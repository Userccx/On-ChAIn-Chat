# Chat functionality
from flask import Blueprint, request, jsonify

from ..config import settings
from ..middleware.auth_middleware import verify_wallet_token
from ..models.chat_models import ChatRequest, ChatResponse
from ..services import get_llm_service, get_storage_service
from ..utils.validation import ValidationError, ensure_messages

bp = Blueprint("chat", __name__, url_prefix=f"{settings.API_PREFIX}/chat")


@bp.route("", methods=["POST"])
@verify_wallet_token
def get_chat_response():
    """
    Get AI chat response with model flexibility.
    每次对话后自动将用户请求和模型回复存储到 IPFS。
    """
    data = request.get_json()
    if not data:
        return jsonify({"detail": "Request body is required"}), 400

    try:
        chat_request = ChatRequest(**data)
    except Exception as e:
        return jsonify({"detail": f"Invalid request: {str(e)}"}), 400

    try:
        trimmed_messages = ensure_messages(
            chat_request.messages, settings.MAX_HISTORY_MESSAGES
        )
        
        # 获取用户最后一条消息（用于存储）
        user_message = ""
        if trimmed_messages:
            # 找到最后一条用户消息
            for msg in reversed(trimmed_messages):
                if msg.role == "user":
                    user_message = msg.content
                    break
        
        # 获取 LLM 回复
        llm_service = get_llm_service()
        response = llm_service.get_response(
            messages=trimmed_messages,
            model=chat_request.model,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens,
        )
        
        # 存储对话到 IPFS
        storage_service = get_storage_service()
        storage_result = storage_service.save_chat_turn(
            wallet_address=request.wallet_address,
            user_message=user_message,
            assistant_reply=response.get("reply", ""),
            model_used=response.get("model_used"),
        )
        
        # 在响应中包含存储信息
        result = ChatResponse(
            wallet_address=request.wallet_address,
            **response,
            ipfs_hash=storage_result.get("ipfs_hash"),
            stored_at=storage_result.get("timestamp"),
        )
        return jsonify(result.dict())
    except ValidationError as ve:
        return jsonify({"detail": str(ve)}), 422
    except ValueError as ve:
        return jsonify({"detail": str(ve)}), 400
    except Exception as e:
        return jsonify(
            {"detail": f"Failed to get response from AI service: {str(e)}"}
        ), 500


@bp.route("/history", methods=["GET"])
@verify_wallet_token
def get_chat_history():
    """
    获取用户的所有历史对话记录（从 IPFS 检索）
    前端可以在用户登录后调用此接口加载历史对话。
    """
    try:
        storage_service = get_storage_service()
        chat_history = storage_service.get_user_chat_history(
            wallet_address=request.wallet_address
        )
        
        return jsonify({
            "wallet_address": request.wallet_address,
            "total_turns": len(chat_history),
            "history": chat_history,
        })
    except Exception as e:
        return jsonify(
            {"detail": f"Failed to retrieve chat history: {str(e)}"}
        ), 500


@bp.route("/unpin/<ipfs_hash>", methods=["DELETE"])
@verify_wallet_token
def unpin_chat_turn(ipfs_hash: str):
    """
    取消固定（删除）指定的对话记录
    
    注意：取消固定后，数据可能仍会在 IPFS 网络中保留一段时间
    直到所有节点都进行垃圾回收。这是 IPFS 的去中心化特性。
    """
    try:
        storage_service = get_storage_service()
        result = storage_service.unpin_content(
            ipfs_hash=ipfs_hash,
            wallet_address=request.wallet_address
        )
        
        if result.get("unpinned"):
            return jsonify({
                "message": result.get("message", "Content unpinned successfully"),
                "ipfs_hash": ipfs_hash,
                "service": result.get("service"),
            })
        else:
            return jsonify({
                "detail": result.get("message", "Failed to unpin content"),
                "error": result.get("error"),
            }), 400
    except Exception as e:
        return jsonify(
            {"detail": f"Failed to unpin content: {str(e)}"}
        ), 500


@bp.route("/pinned", methods=["GET"])
@verify_wallet_token
def get_pinned_content():
    """
    获取当前钱包地址的所有已固定内容列表
    """
    try:
        storage_service = get_storage_service()
        pinned_content = storage_service.get_pinned_content(
            wallet_address=request.wallet_address
        )
        
        return jsonify({
            "wallet_address": request.wallet_address,
            "total_pinned": len(pinned_content),
            "pinned_content": pinned_content,
        })
    except Exception as e:
        return jsonify(
            {"detail": f"Failed to retrieve pinned content: {str(e)}"}
        ), 500


@bp.route("/index-hash", methods=["GET"])
@verify_wallet_token
def get_index_hash():
    """
    获取当前钱包地址的索引文件 IPFS 哈希
    
    这个哈希可以存储到智能合约中，用于在完全去中心化的场景中检索历史记录
    """
    try:
        storage_service = get_storage_service()
        index_hash = storage_service.get_wallet_index_hash(
            wallet_address=request.wallet_address
        )
        
        return jsonify({
            "wallet_address": request.wallet_address,
            "index_hash": index_hash,
            "has_index": index_hash is not None,
        })
    except Exception as e:
        return jsonify(
            {"detail": f"Failed to retrieve index hash: {str(e)}"}
        ), 500


@bp.route("/index-hash", methods=["POST"])
@verify_wallet_token
def set_index_hash():
    """
    设置钱包地址的索引文件 IPFS 哈希
    
    用于从链上或其他来源恢复索引（例如从智能合约读取）
    """
    data = request.get_json()
    if not data or "index_hash" not in data:
        return jsonify({"detail": "index_hash is required"}), 400
    
    try:
        storage_service = get_storage_service()
        success = storage_service.set_wallet_index_hash(
            wallet_address=request.wallet_address,
            index_hash=data["index_hash"]
        )
        
        if success:
            return jsonify({
                "message": "Index hash set successfully",
                "wallet_address": request.wallet_address,
                "index_hash": data["index_hash"],
            })
        else:
            return jsonify({
                "detail": "Failed to set index hash"
            }), 400
    except Exception as e:
        return jsonify(
            {"detail": f"Failed to set index hash: {str(e)}"}
        ), 500


# Chat functionality
from flask import Blueprint, request, jsonify

from ..config import settings
from ..middleware.auth_middleware import verify_wallet_token
from ..models.chat_models import ChatRequest, ChatResponse
from ..services import get_llm_service, get_storage_service
from ..utils.validation import ValidationError, ensure_messages
from ..utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint("chat", __name__, url_prefix=f"{settings.API_PREFIX}/chat")


@bp.route("", methods=["POST"])
@verify_wallet_token
def get_chat_response():
    """
    Get AI chat response with model flexibility.
    每次对话后自动将用户请求和模型回复存储到 IPFS。
    
    请求体:
    {
        "messages": [...],
        "conversation_id": "可选，如果为空则创建新对话",
        "model": "可选",
        "temperature": 0.7,
        "max_tokens": 2000
    }
    """
    logger.info(f"Getting chat response for wallet: {request.wallet_address}")
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
        
        # 获取用户最后一条消息
        user_message_content = ""
        if trimmed_messages:
            for msg in reversed(trimmed_messages):
                if msg.role == "user":
                    user_message_content = msg.content
                    break
        
        # 获取 LLM 回复
        llm_service = get_llm_service()
        response = llm_service.get_response(
            messages=trimmed_messages,
            model=chat_request.model,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens,
        )
        
        # 存储对话
        storage_service = get_storage_service()
        
        # 确定对话 ID
        conversation_id = chat_request.conversation_id
        if not conversation_id:
            # 创建新对话
            import uuid
            conversation_id = str(uuid.uuid4())
        
        # 添加用户消息
        user_msg = storage_service.add_message_to_conversation(
            conversation_id=conversation_id,
            wallet_address=request.wallet_address,
            role="user",
            content=user_message_content,
        )
        
        # 添加助手回复
        assistant_msg = storage_service.add_message_to_conversation(
            conversation_id=conversation_id,
            wallet_address=request.wallet_address,
            role="assistant",
            content=response.get("reply", ""),
        )
        
        # 获取更新后的对话
        conversation = storage_service.get_conversation(
            conversation_id, request.wallet_address
        )
        
        result = ChatResponse(
            wallet_address=request.wallet_address,
            conversation_id=conversation_id,
            message_id=assistant_msg.id,
            **response,
            ipfs_hash=conversation.ipfs_hash if conversation else None,
            stored_at=assistant_msg.timestamp.isoformat() if assistant_msg.timestamp else None,
        )
        return jsonify(result.dict())
    except ValidationError as ve:
        return jsonify({"detail": str(ve)}), 422
    except ValueError as ve:
        return jsonify({"detail": str(ve)}), 400
    except Exception as e:
        logger.error(f"Failed to get chat response: {e}")
        return jsonify(
            {"detail": f"Failed to get response from AI service: {str(e)}"}
        ), 500


@bp.route("/conversations", methods=["GET"])
@verify_wallet_token
def get_conversations():
    """
    获取用户的所有对话列表
    
    返回简化的对话列表，不包含完整消息内容
    """
    try:
        storage_service = get_storage_service()
        conversations = storage_service.get_user_conversations(
            wallet_address=request.wallet_address
        )
        
        # 转换为列表项格式
        items = []
        for convo in conversations:
            # 统计铸造状态
            minted_count = sum(1 for msg in convo.messages if msg.is_minted)
            unminted_count = len(convo.messages) - minted_count
            
            # 获取最后一条消息预览
            last_message = convo.messages[-1] if convo.messages else None
            preview = last_message.content[:50] + "..." if last_message and len(last_message.content) > 50 else (last_message.content if last_message else None)
            
            items.append({
                "id": convo.id,
                "title": convo.title,
                "wallet_address": convo.wallet_address,
                "message_count": len(convo.messages),
                "last_message_preview": preview,
                "has_minted_messages": minted_count > 0,
                "minted_count": minted_count,
                "unminted_count": unminted_count,
                "can_mint": unminted_count > 0,
                "created_at": convo.created_at.isoformat(),
                "updated_at": convo.updated_at.isoformat(),
            })
        
        return jsonify({
            "wallet_address": request.wallet_address,
            "total": len(items),
            "conversations": items,
        })
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        return jsonify(
            {"detail": f"Failed to retrieve conversations: {str(e)}"}
        ), 500


@bp.route("/conversations/<conversation_id>", methods=["GET"])
@verify_wallet_token
def get_conversation(conversation_id: str):
    """
    获取指定对话的完整内容（包含所有消息）
    """
    try:
        storage_service = get_storage_service()
        conversation = storage_service.get_conversation(
            conversation_id=conversation_id,
            wallet_address=request.wallet_address
        )
        
        if not conversation:
            return jsonify({"detail": "Conversation not found"}), 404
        
        # 统计铸造状态
        minted_count = sum(1 for msg in conversation.messages if msg.is_minted)
        unminted_count = len(conversation.messages) - minted_count
        
        return jsonify({
            "id": conversation.id,
            "title": conversation.title,
            "wallet_address": conversation.wallet_address,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "is_minted": msg.is_minted,
                }
                for msg in conversation.messages
            ],
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "ipfs_hash": conversation.ipfs_hash,
            # 铸造统计
            "minted_count": minted_count,
            "unminted_count": unminted_count,
            "can_mint": unminted_count > 0,  # 是否还有可铸造的消息
        })
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        return jsonify(
            {"detail": f"Failed to retrieve conversation: {str(e)}"}
        ), 500


@bp.route("/conversations", methods=["POST"])
@verify_wallet_token
def create_conversation():
    """
    创建新对话
    """
    data = request.get_json() or {}
    title = data.get("title", "New Conversation")
    
    try:
        storage_service = get_storage_service()
        conversation = storage_service.create_conversation(
            wallet_address=request.wallet_address,
            title=title
        )
        
        return jsonify({
            "id": conversation.id,
            "title": conversation.title,
            "wallet_address": conversation.wallet_address,
            "created_at": conversation.created_at.isoformat(),
        }), 201
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        return jsonify(
            {"detail": f"Failed to create conversation: {str(e)}"}
        ), 500


@bp.route("/history", methods=["GET"])
@verify_wallet_token
def get_chat_history():
    """
    获取用户的所有历史对话记录（兼容旧接口）
    
    返回扁平化的消息列表
    """
    try:
        storage_service = get_storage_service()
        conversations = storage_service.get_user_conversations(
            wallet_address=request.wallet_address
        )
        
        # 扁平化所有消息
        all_messages = []
        for convo in conversations:
            for msg in convo.messages:
                all_messages.append({
                    "conversation_id": convo.id,
                    "conversation_title": convo.title,
                    "message_id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "is_minted": msg.is_minted,
                })
        
        # 按时间排序
        all_messages.sort(key=lambda x: x.get("timestamp", ""))
        
        return jsonify({
            "wallet_address": request.wallet_address,
            "total_messages": len(all_messages),
            "history": all_messages,
        })
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        return jsonify(
            {"detail": f"Failed to retrieve chat history: {str(e)}"}
        ), 500


@bp.route("/minted", methods=["GET"])
@verify_wallet_token
def get_minted_records():
    """
    获取用户的所有 NFT 铸造记录
    """
    try:
        storage_service = get_storage_service()
        records = storage_service.get_mint_records(
            wallet_address=request.wallet_address
        )
        
        return jsonify({
            "wallet_address": request.wallet_address,
            "total": len(records),
            "minted_records": [
                {
                    "id": record.id,
                    "conversation_id": record.conversation_id,
                    "message_ids": record.message_ids,
                    "ipfs_hash": record.ipfs_hash,
                    "metadata_url": record.metadata_url,
                    "gateway_url": record.gateway_url,
                    "tx_hash": record.tx_hash,
                    "token_id": record.token_id,
                    "listing_id": record.listing_id,
                    "price": record.price,
                    "is_listed": record.is_listed,
                    "owner_address": record.owner_address,
                    "minted_at": record.minted_at.isoformat(),
                }
                for record in records
            ],
        })
    except Exception as e:
        logger.error(f"Failed to get minted records: {e}")
        return jsonify(
            {"detail": f"Failed to retrieve minted records: {str(e)}"}
        ), 500


@bp.route("/unpin/<ipfs_hash>", methods=["DELETE"])
@verify_wallet_token
def unpin_content(ipfs_hash: str):
    """
    取消固定指定的 IPFS 内容
    """
    try:
        storage_service = get_storage_service()
        success = storage_service.unpin_content(ipfs_hash=ipfs_hash)
        
        if success:
            return jsonify({
                "message": "Content unpinned successfully",
                "ipfs_hash": ipfs_hash,
            })
        else:
            return jsonify({
                "detail": "Failed to unpin content",
            }), 400
    except Exception as e:
        logger.error(f"Failed to unpin content: {e}")
        return jsonify(
            {"detail": f"Failed to unpin content: {str(e)}"}
        ), 500


@bp.route("/status", methods=["GET"])
@verify_wallet_token
def get_storage_status():
    """
    获取存储服务状态
    """
    try:
        storage_service = get_storage_service()
        status = storage_service.get_service_status()
        
        return jsonify({
            "wallet_address": request.wallet_address,
            **status,
        })
    except Exception as e:
        return jsonify(
            {"detail": f"Failed to get status: {str(e)}"}
        ), 500

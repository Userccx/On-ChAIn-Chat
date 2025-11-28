# NFT minting endpoints
from flask import Blueprint, request, jsonify

from ..config import settings
from ..middleware.auth_middleware import verify_wallet_token
from ..models.chat_models import MintRequest, MintResponse
from ..services import get_blockchain_service, get_storage_service
from ..utils.validation import ValidationError, ensure_title
from ..utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint("mint", __name__, url_prefix=f"{settings.API_PREFIX}/mints")


@bp.route("", methods=["POST"])
@verify_wallet_token
def mint_conversation_nft():
    """
    Mint conversation as NFT.
    
    请求体:
    {
        "conversation_id": "对话 ID（必需）",
        "message_ids": ["可选：指定要铸造的消息 ID，默认全部"],
        "conversationTitle": "NFT 标题",
        "description": "NFT 描述",
        "userAddress": "可选：用户地址"
    }
    """
    logger.info(f"Minting conversation NFT for wallet: {request.wallet_address}")
    data = request.get_json()
    if not data:
        return jsonify({"detail": "Request body is required"}), 400

    try:
        mint_request = MintRequest(**data)
    except Exception as e:
        return jsonify({"detail": f"Invalid request: {str(e)}"}), 400

    try:
        storage_service = get_storage_service()
        
        # 获取对话
        conversation = storage_service.get_conversation(
            conversation_id=mint_request.conversation_id,
            wallet_address=request.wallet_address
        )
        
        if not conversation:
            return jsonify({"detail": "Conversation not found"}), 404
        
        # 检查对话是否已被铸造
        existing_record = storage_service.get_mint_record_by_conversation(
            conversation_id=mint_request.conversation_id,
            wallet_address=request.wallet_address
        )
        
        if existing_record:
            return jsonify({
                "detail": "This conversation has already been minted",
                "existing_mint_id": existing_record.id,
                "metadata_url": existing_record.metadata_url,
            }), 400
        
        # 确定要铸造的消息
        message_ids = mint_request.message_ids
        if not message_ids:
            # 默认铸造所有未铸造的消息
            message_ids = [msg.id for msg in conversation.messages if not msg.is_minted]
        else:
            # 验证消息 ID 存在
            valid_message_ids = {msg.id for msg in conversation.messages}
            invalid_ids = set(message_ids) - valid_message_ids
            if invalid_ids:
                return jsonify({
                    "detail": f"Invalid message IDs: {list(invalid_ids)}"
                }), 400
            
            # 自动过滤已铸造的消息
            already_minted = [
                msg.id for msg in conversation.messages 
                if msg.id in message_ids and msg.is_minted
            ]
            if already_minted:
                logger.info(f"Filtering out already minted messages: {already_minted}")
            
            message_ids = [
                msg_id for msg_id in message_ids 
                if msg_id not in already_minted
            ]
        
        # 检查是否还有未铸造的消息
        if not message_ids:
            return jsonify({
                "detail": "No unminted messages to mint. All selected messages have already been minted.",
                "already_minted_count": len([m for m in conversation.messages if m.is_minted]),
            }), 400
        
        # 获取标题
        title = ensure_title(mint_request.conversation_title) or conversation.title
        
        # 上传 NFT 元数据到 IPFS
        storage_result = storage_service.upload_nft_metadata(
            conversation=conversation,
            message_ids=message_ids,
            title=title,
            description=mint_request.description,
        )

        # 调用区块链服务
        blockchain_service = get_blockchain_service()
        mint_result = blockchain_service.mint_context_nft(
            user_address=request.wallet_address,
            metadata_url=storage_result["metadataUrl"],
        )
        
        # 检查 mint 结果
        if not mint_result.get("success", True):
            error_msg = mint_result.get("error") or mint_result.get("message", "Unknown error")
            return jsonify({"detail": f"Failed to mint NFT: {error_msg}"}), 500

        # 创建铸造记录
        mint_record = storage_service.create_mint_record(
            conversation=conversation,
            message_ids=message_ids,
            ipfs_hash=storage_result["ipfs_hash"],
            metadata_url=storage_result["metadataUrl"],
            gateway_url=storage_result["gatewayUrl"],
            tx_hash=mint_result.get("tx_hash"),
            token_id=mint_result.get("token_id"),
            listing_id=mint_result.get("listing_id"),
        )

        result = MintResponse(
            mint_id=mint_record.id,
            conversation_id=conversation.id,
            message_ids=message_ids,
            metadataUrl=storage_result["metadataUrl"],
            ipfs_hash=storage_result["ipfs_hash"],
            gatewayUrl=storage_result["gatewayUrl"],
            token_id=mint_result.get("token_id"),
            tx_hash=mint_result.get("tx_hash"),
            listing_id=mint_result.get("listing_id"),
            message=mint_result.get("message", "NFT minted successfully"),
        )
        return jsonify(result.dict())

    except ValidationError as ve:
        return jsonify({"detail": str(ve)}), 422
    except Exception as e:
        logger.error(f"Failed to mint NFT: {e}")
        return jsonify(
            {"detail": f"Failed to mint conversation NFT: {str(e)}"}
        ), 500


@bp.route("/<mint_id>", methods=["GET"])
@verify_wallet_token
def get_mint_record(mint_id: str):
    """
    获取指定的铸造记录
    """
    try:
        storage_service = get_storage_service()
        records = storage_service.get_mint_records(request.wallet_address)
        
        record = next((r for r in records if r.id == mint_id), None)
        if not record:
            return jsonify({"detail": "Mint record not found"}), 404
        
        return jsonify({
            "id": record.id,
            "conversation_id": record.conversation_id,
            "message_ids": record.message_ids,
            "wallet_address": record.wallet_address,
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
        })
    except Exception as e:
        logger.error(f"Failed to get mint record: {e}")
        return jsonify(
            {"detail": f"Failed to get mint record: {str(e)}"}
        ), 500


@bp.route("/<mint_id>/list", methods=["POST"])
@verify_wallet_token
def list_mint_on_market(mint_id: str):
    """
    将铸造的 NFT 上架到市场
    
    请求体:
    {
        "price": 100
    }
    """
    data = request.get_json() or {}
    price = data.get("price", 0)
    
    if price <= 0:
        return jsonify({"detail": "Price must be greater than 0"}), 400
    
    try:
        storage_service = get_storage_service()
        records = storage_service.get_mint_records(request.wallet_address)
        
        record = next((r for r in records if r.id == mint_id), None)
        if not record:
            return jsonify({"detail": "Mint record not found"}), 404
        
        if record.is_listed:
            return jsonify({
                "detail": "Already listed on market",
                "listing_id": record.listing_id,
            }), 400
        
        # 调用区块链服务上架
        blockchain_service = get_blockchain_service()
        list_result = blockchain_service.list_data(
            data_hash=record.metadata_url,
            price=int(price)
        )
        
        if not list_result.get("success"):
            return jsonify({
                "detail": f"Failed to list on market: {list_result.get('error')}"
            }), 500
        
        # 更新铸造记录
        storage_service.update_mint_record_listing(
            mint_id=mint_id,
            wallet_address=request.wallet_address,
            listing_id=list_result.get("listing_id"),
            price=price,
            is_listed=True
        )
        
        return jsonify({
            "message": "Listed on market successfully",
            "mint_id": mint_id,
            "listing_id": list_result.get("listing_id"),
            "price": price,
            "tx_hash": list_result.get("tx_hash"),
        })
    except Exception as e:
        logger.error(f"Failed to list on market: {e}")
        return jsonify(
            {"detail": f"Failed to list on market: {str(e)}"}
        ), 500


@bp.route("/<mint_id>/unlist", methods=["POST"])
@verify_wallet_token
def unlist_from_market(mint_id: str):
    """
    将 NFT 从市场下架
    """
    try:
        storage_service = get_storage_service()
        records = storage_service.get_mint_records(request.wallet_address)
        
        record = next((r for r in records if r.id == mint_id), None)
        if not record:
            return jsonify({"detail": "Mint record not found"}), 404
        
        if not record.is_listed:
            return jsonify({"detail": "Not listed on market"}), 400
        
        # 调用区块链服务下架
        blockchain_service = get_blockchain_service()
        result = blockchain_service.remove_listing(record.listing_id)
        
        if not result.get("success"):
            return jsonify({
                "detail": f"Failed to unlist: {result.get('error')}"
            }), 500
        
        # 更新铸造记录
        storage_service.update_mint_record_listing(
            mint_id=mint_id,
            wallet_address=request.wallet_address,
            listing_id=None,
            price=0,
            is_listed=False
        )
        
        return jsonify({
            "message": "Unlisted from market successfully",
            "mint_id": mint_id,
            "tx_hash": result.get("tx_hash"),
        })
    except Exception as e:
        logger.error(f"Failed to unlist: {e}")
        return jsonify(
            {"detail": f"Failed to unlist: {str(e)}"}
        ), 500

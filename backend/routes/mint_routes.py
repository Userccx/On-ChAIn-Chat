# NFT minting endpoints
from flask import Blueprint, request, jsonify

from ..config import settings
from ..middleware.auth_middleware import verify_wallet_token
from ..models.chat_models import MintRequest, MintResponse
from ..services import get_blockchain_service, get_storage_service
from ..utils.validation import (
    ValidationError,
    ensure_messages,
    ensure_same_wallet,
    ensure_title,
)

bp = Blueprint("mint", __name__, url_prefix=f"{settings.API_PREFIX}/mints")


@bp.route("", methods=["POST"])
@verify_wallet_token
def mint_conversation_nft():
    """Mint conversation as NFT."""
    data = request.get_json()
    if not data:
        return jsonify({"detail": "Request body is required"}), 400

    try:
        mint_request = MintRequest(**data)
    except Exception as e:
        return jsonify({"detail": f"Invalid request: {str(e)}"}), 400

    try:
        trimmed_messages = ensure_messages(
            mint_request.messages, settings.MAX_HISTORY_MESSAGES
        )
        wallet_address = ensure_same_wallet(
            request.wallet_address, mint_request.user_address
        )
        title = ensure_title(mint_request.conversation_title)

        storage_service = get_storage_service()
        storage_result = storage_service.upload_conversation_metadata(
            messages=trimmed_messages,
            user_address=wallet_address,
            title=title,
            description=mint_request.description,
        )

        blockchain_service = get_blockchain_service()
        mint_result = blockchain_service.mint_context_nft(
            user_address=wallet_address,
            metadata_url=storage_result["metadataUrl"],
        )

        result = MintResponse(
            **storage_result,
            token_id=mint_result.get("token_id"),
            tx_hash=mint_result.get("tx_hash"),
            message=mint_result.get("message"),
        )
        return jsonify(result.dict())

    except ValidationError as ve:
        return jsonify({"detail": str(ve)}), 422
    except Exception as e:
        return jsonify(
            {"detail": f"Failed to mint conversation NFT: {str(e)}"}
        ), 500


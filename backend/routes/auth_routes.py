# Wallet authentication
from flask import Blueprint, request, jsonify

from ..config import settings
from ..models.user_models import (
    NonceResponse,
    WalletAuthRequest,
    WalletAuthResponse,
)
from ..services import get_wallet_service
from ..utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint("auth", __name__, url_prefix=f"{settings.API_PREFIX}/auth")


@bp.route("/nonce/<address>", methods=["GET"])
def get_nonce(address: str):
    """Get nonce for wallet signature."""
    logger.info(f"Getting nonce for wallet: {address}")
    wallet_service = get_wallet_service()
    result = wallet_service.generate_nonce(address)
    return jsonify(result)


@bp.route("/verify", methods=["POST"])
def verify_wallet():
    """Verify wallet signature and return JWT token."""
    data = request.get_json()
    if not data:
        return jsonify({"detail": "Request body is required"}), 400

    try:
        auth_request = WalletAuthRequest(**data)
    except Exception as e:
        return jsonify({"detail": f"Invalid request: {str(e)}"}), 400

    wallet_service = get_wallet_service()
    is_valid, normalized_address, error = wallet_service.verify_signature(
        address=auth_request.address,
        message=auth_request.message,
        signature=auth_request.signature,
    )

    if not is_valid or not normalized_address:
        return jsonify({"detail": error or "Invalid signature"}), 401

    token = wallet_service.issue_access_token(normalized_address)
    return jsonify(WalletAuthResponse(access_token=token).dict())


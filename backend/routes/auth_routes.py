# Wallet authentication
from fastapi import APIRouter, Depends, HTTPException

from config import settings
from models.user_models import (
    NonceResponse,
    WalletAuthRequest,
    WalletAuthResponse,
)
from services import get_wallet_service
from services.wallet_service import WalletService

router = APIRouter(prefix=f"{settings.API_PREFIX}/auth", tags=["authentication"])


@router.get("/nonce/{address}", response_model=NonceResponse)
async def get_nonce(
    address: str,
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """Get nonce for wallet signature."""
    return wallet_service.generate_nonce(address)


@router.post("/verify", response_model=WalletAuthResponse)
async def verify_wallet(
    request: WalletAuthRequest,
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """Verify wallet signature and return JWT token."""
    is_valid, normalized_address, error = wallet_service.verify_signature(
        address=request.address,
        message=request.message,
        signature=request.signature,
    )

    if not is_valid or not normalized_address:
        raise HTTPException(status_code=401, detail=error or "Invalid signature")

    token = wallet_service.issue_access_token(normalized_address)
    return WalletAuthResponse(access_token=token)


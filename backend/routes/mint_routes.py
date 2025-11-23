# NFT minting endpoints
from fastapi import APIRouter, Depends, HTTPException

from ..config import settings
from ..middleware.auth_middleware import verify_wallet_token
from ..models.chat_models import MintRequest, MintResponse
from ..services import get_blockchain_service, get_storage_service
from ..services.blockchain_service import BlockchainService
from ..services.storage_service import StorageService
from ..utils.validation import (
    ValidationError,
    ensure_messages,
    ensure_same_wallet,
    ensure_title,
)

router = APIRouter(prefix=f"{settings.API_PREFIX}/mints", tags=["mint"])


@router.post("", response_model=MintResponse)
async def mint_conversation_nft(
    request: MintRequest,
    user_address: str = Depends(verify_wallet_token),
    storage_service: StorageService = Depends(get_storage_service),
    blockchain_service: BlockchainService = Depends(get_blockchain_service),
):
    """Mint conversation as NFT."""
    try:
        trimmed_messages = ensure_messages(
            request.messages, settings.MAX_HISTORY_MESSAGES
        )
        wallet_address = ensure_same_wallet(user_address, request.user_address)
        title = ensure_title(request.conversation_title)

        storage_result = await storage_service.upload_conversation_metadata(
            messages=trimmed_messages,
            user_address=wallet_address,
            title=title,
            description=request.description,
        )

        mint_result = await blockchain_service.mint_context_nft(
            user_address=wallet_address,
            metadata_url=storage_result["metadataUrl"],
        )

        return MintResponse(
            **storage_result,
            token_id=mint_result.get("token_id"),
            tx_hash=mint_result.get("tx_hash"),
            message=mint_result.get("message"),
        )

    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to mint conversation NFT: {str(e)}"
        ) from e


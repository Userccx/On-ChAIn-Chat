# Chat functionality
from fastapi import APIRouter, Depends, HTTPException

from config import settings
from middleware.auth_middleware import verify_wallet_token
from models.chat_models import ChatRequest, ChatResponse
from services import get_llm_service
from services.llm_service import LLMService
from utils.validation import ValidationError, ensure_messages

router = APIRouter(prefix=f"{settings.API_PREFIX}/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def get_chat_response(
    request: ChatRequest,
    user_address: str = Depends(verify_wallet_token),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Get AI chat response with model flexibility."""
    try:
        trimmed_messages = ensure_messages(
            request.messages, settings.MAX_HISTORY_MESSAGES
        )
        response = await llm_service.get_response(
            messages=trimmed_messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return ChatResponse(wallet_address=user_address, **response)
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=str(ve)) from ve
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get response from AI service: {str(e)}",
        ) from e


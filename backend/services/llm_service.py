# Mockable LLM service for local testing
from typing import Dict, List, Optional

from ..config import settings
from ..models.chat_models import ChatMessage


class LLMService:
    """Very lightweight LLM proxy returning mock data for smoke tests."""

    async def get_response(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        """Return canned response when running in mock mode."""
        reply = settings.MOCK_LLM_REPLY or "Hello world"
        return {
            "reply": reply,
            "model_used": model or settings.DEFAULT_LLM_MODEL,
            "tokens_used": len(reply.split()),
            "provider": "mock",
            "latency_ms": 0,
        }



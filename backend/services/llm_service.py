# Multi-model LLM integration
import asyncio
import time
from typing import Dict, List, Optional

import google.generativeai as genai
from anthropic import Anthropic
from openai import OpenAI

from config import settings
from models.chat_models import ChatMessage


class LLMService:
    def __init__(self):
        self.openai_client = (
            OpenAI(api_key=settings.OPENAI_API_KEY)
            if settings.OPENAI_API_KEY
            else None
        )
        self.anthropic_client = (
            Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            if settings.ANTHROPIC_API_KEY
            else None
        )
        self.google_enabled = False
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.google_enabled = True

    async def get_response(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        """Route request to appropriate LLM provider."""

        target_model = model or settings.DEFAULT_LLM_MODEL
        provider = self._detect_provider(target_model)
        handler_map = {
            "openai": self._openai_chat,
            "anthropic": self._anthropic_chat,
            "google": self._google_chat,
        }
        handler = handler_map.get(provider)
        if not handler:
            raise ValueError(f"Unsupported model provider for: {target_model}")

        start = time.perf_counter()
        response = await handler(messages, target_model, **kwargs)
        response["provider"] = provider
        response["latency_ms"] = int((time.perf_counter() - start) * 1000)
        return response

    def _detect_provider(self, model: str) -> str:
        model_lower = model.lower()
        if model_lower.startswith("gpt"):
            if not self.openai_client:
                raise ValueError("未配置 OpenAI API Key。")
            return "openai"
        if model_lower.startswith("claude"):
            if not self.anthropic_client:
                raise ValueError("未配置 Anthropic API Key。")
            return "anthropic"
        if model_lower.startswith("gemini"):
            if not self.google_enabled:
                raise ValueError("未配置 Google Generative AI API Key。")
            return "google"
        raise ValueError(f"Unsupported model: {model}")

    async def _openai_chat(
        self,
        messages: List[ChatMessage],
        model: str,
        **kwargs,
    ):
        """OpenAI API integration."""
        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        response = await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model=model,
            messages=formatted_messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )

        return {
            "reply": response.choices[0].message.content,
            "model_used": model,
            "tokens_used": response.usage.total_tokens,
        }

    async def _anthropic_chat(
        self,
        messages: List[ChatMessage],
        model: str,
        **kwargs,
    ):
        """Anthropic Claude API integration."""
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.role != "system"
        ]

        response = await asyncio.to_thread(
            self.anthropic_client.messages.create,
            model=model,
            messages=formatted_messages,
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=kwargs.get("temperature", 0.7),
        )

        usage = getattr(response, "usage", None)
        tokens_used = None
        if usage:
            tokens_used = getattr(usage, "input_tokens", 0) + getattr(
                usage, "output_tokens", 0
            )

        return {
            "reply": response.content[0].text,
            "model_used": model,
            "tokens_used": tokens_used,
        }

    async def _google_chat(
        self,
        messages: List[ChatMessage],
        model: str,
        **kwargs,
    ):
        """Google Gemini API integration."""
        genai_model = genai.GenerativeModel(model)

        prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])

        response = await asyncio.to_thread(
            genai_model.generate_content,
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=kwargs.get("temperature", 0.7),
                max_output_tokens=kwargs.get("max_tokens", 2000),
            ),
        )

        return {
            "reply": response.text,
            "model_used": model,
            "tokens_used": None,  # Gemini doesn't always return token count
        }


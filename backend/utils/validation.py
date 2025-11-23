# Input validation helpers
from typing import List, Optional, Sequence

from ..models.chat_models import ChatMessage


class ValidationError(ValueError):
    """Lightweight validation error used across the backend."""


def ensure_messages(
    messages: Sequence[ChatMessage],
    max_length: int,
) -> List[ChatMessage]:
    if not messages:
        raise ValidationError("对话消息不能为空。")
    if len(messages) > max_length:
        # 保留最新的 max_length 条消息，避免上下文过长
        return list(messages)[-max_length:]
    return list(messages)


def ensure_same_wallet(authenticated: str, claimed: Optional[str]) -> str:
    """确保请求体中的地址（若提供）与 JWT 中一致。"""
    if claimed and claimed.lower() != authenticated.lower():
        raise ValidationError("会话钱包地址与认证地址不一致。")
    return authenticated


def ensure_title(title: Optional[str], fallback: str = "Untitled Conversation") -> str:
    cleaned = (title or fallback).strip()
    if not cleaned:
        cleaned = fallback
    if len(cleaned) > 120:
        raise ValidationError("标题长度不得超过 120 个字符。")
    return cleaned


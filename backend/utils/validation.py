# Input validation helpers
from typing import List, Optional, Sequence

from ..models.chat_models import ChatMessage
from ..utils.crypto_utils import normalize_address


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
    # 验证认证地址格式
    try:
        normalized_authenticated = normalize_address(authenticated)
    except ValueError as e:
        raise ValidationError(f"认证钱包地址格式无效: {str(e)}")
    
    # 如果提供了 claimed 地址，验证格式并比较
    if claimed:
        try:
            normalized_claimed = normalize_address(claimed)
        except ValueError as e:
            raise ValidationError(f"请求中的钱包地址格式无效: {str(e)}")
        
        if normalized_claimed.lower() != normalized_authenticated.lower():
            raise ValidationError("会话钱包地址与认证地址不一致。")
    
    return normalized_authenticated


def ensure_title(title: Optional[str], fallback: str = "Untitled Conversation") -> str:
    cleaned = (title or fallback).strip()
    if not cleaned:
        cleaned = fallback
    if len(cleaned) > 120:
        raise ValidationError("标题长度不得超过 120 个字符。")
    return cleaned


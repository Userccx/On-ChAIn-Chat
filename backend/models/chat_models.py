# Chat message schemas
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None  # Allow backend default
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=2000, ge=64, le=4096)


class ChatResponse(BaseModel):
    reply: str
    model_used: str
    tokens_used: Optional[int] = None
    provider: Optional[str] = None
    latency_ms: Optional[int] = None
    wallet_address: Optional[str] = None
    ipfs_hash: Optional[str] = None  # 本次对话存储的 IPFS 哈希
    stored_at: Optional[str] = None  # 存储时间戳


class MintRequest(BaseModel):
    messages: List[ChatMessage]
    conversation_title: Optional[str] = Field(
        default="Untitled Conversation", alias="conversationTitle"
    )
    description: Optional[str] = Field(default=None, max_length=280)
    user_address: Optional[str] = Field(default=None, alias="userAddress")

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class MintResponse(BaseModel):
    metadataUrl: str
    ipfs_hash: str
    gatewayUrl: str
    token_id: Optional[int] = None
    tx_hash: Optional[str] = None
    message: Optional[str] = None


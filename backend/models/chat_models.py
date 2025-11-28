# Chat message schemas
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """单条消息"""
    id: Optional[str] = None  # 消息唯一标识
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    is_minted: bool = False  # 是否已被铸造为 NFT


class Conversation(BaseModel):
    """完整对话"""
    id: str  # 对话唯一标识
    wallet_address: str  # 所属钱包地址
    title: str = "New Conversation"
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # IPFS 存储信息
    ipfs_hash: Optional[str] = None  # 最新版本的 IPFS 哈希


class MintRecord(BaseModel):
    """NFT 铸造记录"""
    id: str  # 铸造记录唯一标识
    conversation_id: str  # 关联的对话 ID
    message_ids: List[str] = []  # 被铸造的消息 ID 列表
    wallet_address: str  # 铸造者钱包地址
    
    # IPFS 信息
    ipfs_hash: str
    metadata_url: str  # ipfs://Qm...
    gateway_url: str  # https://gateway.pinata.cloud/ipfs/Qm...
    
    # 区块链信息
    tx_hash: Optional[str] = None
    token_id: Optional[int] = None
    listing_id: Optional[int] = None
    
    # 市场信息
    price: float = 0
    is_listed: bool = False
    owner_address: Optional[str] = None
    
    # 时间戳
    minted_at: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[ChatMessage]
    conversation_id: Optional[str] = None  # 对话 ID，如果为空则创建新对话
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=2000, ge=64, le=4096)


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    model_used: str
    tokens_used: Optional[int] = None
    provider: Optional[str] = None
    latency_ms: Optional[int] = None
    
    # 对话信息
    conversation_id: str
    message_id: str  # 新消息的 ID
    
    # 存储信息
    wallet_address: Optional[str] = None
    ipfs_hash: Optional[str] = None
    stored_at: Optional[str] = None


class MintRequest(BaseModel):
    """铸造请求"""
    conversation_id: str  # 要铸造的对话 ID
    message_ids: Optional[List[str]] = None  # 可选：指定要铸造的消息，默认全部
    conversation_title: Optional[str] = Field(
        default="Untitled Conversation", alias="conversationTitle"
    )
    description: Optional[str] = Field(default=None, max_length=280)
    user_address: Optional[str] = Field(default=None, alias="userAddress")

    class Config:
        populate_by_name = True


class MintResponse(BaseModel):
    """铸造响应"""
    mint_id: str  # 铸造记录 ID
    conversation_id: str
    message_ids: List[str]
    
    # IPFS 信息
    metadataUrl: str
    ipfs_hash: str
    gatewayUrl: str
    
    # 区块链信息
    token_id: Optional[int] = None
    tx_hash: Optional[str] = None
    listing_id: Optional[int] = None
    
    message: Optional[str] = None


class ConversationListItem(BaseModel):
    """对话列表项（不包含完整消息）"""
    id: str
    title: str
    wallet_address: str
    message_count: int
    last_message_preview: Optional[str] = None
    has_minted_messages: bool = False
    created_at: datetime
    updated_at: datetime

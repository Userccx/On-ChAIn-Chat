# Configuration and environment variables
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized application configuration."""

    # App meta
    APP_NAME: str = "Tokenized LLM Interaction Platform"
    API_PREFIX: str = "/api"
    API_VERSION: str = "v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: List[str] = ["*"]

    # LLM defaults
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    FALLBACK_LLM_MODEL: str = "gpt-3.5-turbo"
    MAX_HISTORY_MESSAGES: int = 30
    MOCK_LLM_REPLY: str = "Hello world"

    # API Keys for different LLM providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # IPFS Configuration
    IPFS_API_URL: str = "http://127.0.0.1:5001"
    IPFS_GATEWAY: str = "https://ipfs.io/ipfs/"
    
    # IPFS Pinning Service Configuration
    # 选项：'local' (本地节点), 'pinata' (Pinata 服务), 'none' (不 pinning)
    IPFS_PINNING_SERVICE: str = "pinata"
    PINATA_API_KEY: Optional[str] = None
    PINATA_SECRET_KEY: Optional[str] = None
    PINATA_JWT: Optional[str] = None  # Pinata JWT token (推荐使用，替代 API Key + Secret)

    # Blockchain Configuration (Pseudo for now)
    BLOCKCHAIN_NETWORK: str = "polygon-mumbai"
    CONTRACT_ADDRESS: Optional[str] = None
    PAYMENT_TOKEN_ADDRESS: Optional[str] = None  # 如果使用 ERC20 版本
    WEB3_RPC_URL: Optional[str] = "https://eth-mainnet.g.alchemy.com/v2/9m2L_-2aXz8zn881udhPC"
    PRIVATE_KEY: Optional[str] = None  # 后端签名交易的私钥
    CHAIN_ID: int = 1  # 主网=1, Sepolia=11155111, Polygon Mumbai=80001

    # Security
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # Database (Optional - for caching)
    DATABASE_URL: str = "sqlite:///./chat_history.db"
    USE_MOCK_SERVICES: bool = True
    MOCK_WALLET_ADDRESS: str = "0xMockWallet000000000000000000000000000000"

    class Config:
        env_file = ".env"



@lru_cache
def get_settings() -> "Settings":
    """Return cached settings instance to reuse across imports."""
    return Settings()


settings = get_settings()


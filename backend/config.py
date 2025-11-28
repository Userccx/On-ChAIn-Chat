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
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: List[str] = ["*"]

    # LLM defaults
    DEFAULT_LLM_MODEL: str = "gpt-4"
    FALLBACK_LLM_MODEL: str = "gpt-3.5-turbo"
    MAX_HISTORY_MESSAGES: int = 30
    MOCK_LLM_REPLY: str = "Hello world"

    # API Keys for different LLM providers
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://chatapi.onechats.top/v1/"
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # IPFS Configuration
    # Pinning 服务类型：'pinata' (推荐生产环境), 'local' (本地节点), 'none' (Mock 模式)
    IPFS_PINNING_SERVICE: str = "pinata"
    IPFS_API_URL: str = "http://127.0.0.1:5001"  # 仅 local 模式使用
    IPFS_GATEWAY: str = "https://gateway.pinata.cloud/ipfs/"  # Pinata 专用网关
    
    # Pinata 配置（推荐使用 JWT）
    PINATA_JWT: Optional[str] = None  # 从 https://app.pinata.cloud/developers/api-keys 获取
    PINATA_API_KEY: Optional[str] = None  # 备选：API Key + Secret
    PINATA_SECRET_KEY: Optional[str] = None

    # ============ Blockchain Configuration ============
    # 通用配置
    BLOCKCHAIN_NETWORK: str = "sepolia"
    WEB3_RPC_URL: Optional[str] = None
    PRIVATE_KEY: Optional[str] = None  # 后端签名交易的私钥
    CHAIN_ID: int = 11155111  # Sepolia=11155111, Polygon Mumbai=80001, Mainnet=1
    
    # 市场类型：'token' (使用 DTK 代币) 或 'eth' (使用 ETH)
    MARKET_TYPE: str = "token"
    
    # DataToken (DTK) / Payment Token 合约配置
    DATA_TOKEN_ADDRESS: Optional[str] = None
    PAYMENT_TOKEN_ADDRESS: Optional[str] = None  # 别名，与 DATA_TOKEN_ADDRESS 相同用途
    DATA_TOKEN_DECIMALS: int = 18
    
    # Market / Contract 合约配置
    MARKET_CONTRACT_ADDRESS: Optional[str] = None
    CONTRACT_ADDRESS: Optional[str] = None  # 别名，与 MARKET_CONTRACT_ADDRESS 相同用途
    
    # ETH Market 合约配置（使用原生 ETH）
    ETH_MARKET_CONTRACT_ADDRESS: Optional[str] = None
    
    # 默认价格（用于上架时的默认价格，单位：最小单位）
    DEFAULT_LISTING_PRICE: int = 1  # 1 wei 或 1 最小单位代币

    # Security
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # Database (Optional - for caching)
    DATABASE_URL: str = "sqlite:///./chat_history.db"
    USE_MOCK_SERVICES: bool = False
    MOCK_WALLET_ADDRESS: str = "0xMockWallet000000000000000000000000000000"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> "Settings":
    """Return cached settings instance to reuse across imports."""
    return Settings()


settings = get_settings()
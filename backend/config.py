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

    # Blockchain Configuration (Pseudo for now)
    BLOCKCHAIN_NETWORK: str = "polygon-mumbai"
    CONTRACT_ADDRESS: Optional[str] = None

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


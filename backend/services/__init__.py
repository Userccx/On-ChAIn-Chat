# Business logic layer
from functools import lru_cache

from .blockchain_service import BlockchainService
from .llm_service import LLMService
from .storage_service import StorageService
from .wallet_service import WalletService


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()


@lru_cache
def get_storage_service() -> StorageService:
    return StorageService()


@lru_cache
def get_blockchain_service() -> BlockchainService:
    return BlockchainService()


@lru_cache
def get_wallet_service() -> WalletService:
    return WalletService()


__all__ = [
    "get_llm_service",
    "get_storage_service",
    "get_blockchain_service",
    "get_wallet_service",
]


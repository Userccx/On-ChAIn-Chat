# Wallet authentication
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

# 使用 PyJWT
import jwt

from ..config import settings
from ..utils.crypto_utils import (
    format_auth_message,
    is_valid_signature,
    normalize_address,
)

from ..utils.logger import get_logger

logger = get_logger(__name__)

class WalletService:
    def __init__(self):
        # In production consider Redis or DB to persist nonces
        self.active_nonces: Dict[str, str] = {}
        self.mock_mode = settings.USE_MOCK_SERVICES

    def _store_nonce(self, address: str, nonce: str) -> None:
        logger.info(f"Storing nonce for address: {address}")
        self.active_nonces[address.lower()] = nonce

    def _pop_nonce(self, address: str) -> Optional[str]:
        logger.info(f"Popping nonce for address: {address}")
        return self.active_nonces.pop(address.lower(), None)

    def generate_nonce(self, address: str) -> Dict[str, str]:
        """Generate unique nonce for signature verification."""
        logger.info(f"Generating nonce for address: {address}")
        normalized = normalize_address(address)
        nonce = secrets.token_hex(16) if not self.mock_mode else "mock-nonce"
        self._store_nonce(normalized, nonce)
        return {
            "nonce": nonce,
            "message": format_auth_message(nonce),
            "wallet": normalized,
        }

    def verify_signature(
        self,
        address: str,
        message: str,
        signature: str,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Verify wallet signature and consume nonce once validated."""
        normalized = normalize_address(address or settings.MOCK_WALLET_ADDRESS)
        expected_nonce = self.active_nonces.get(normalized.lower())

        if not expected_nonce:
            return False, None, "鉴权 nonce 已失效或不存在，请重新获取。"

        expected_message = format_auth_message(expected_nonce)
        if not self.mock_mode and message != expected_message:
            return False, None, "签名消息与服务器下发的 nonce 不一致。"

        if not self.mock_mode:
            if not is_valid_signature(normalized, message, signature or ""):
                logger.error(f"Signature verification failed for address: {normalized}")
                return False, None, "签名校验失败，请确认钱包地址与签名内容。"
        else:
            # 在 mock 模式下自动通过验证
            if not message:
                message = expected_message

        self._pop_nonce(normalized)
        return True, normalized, None

    def issue_access_token(self, wallet_address: str) -> str:
        """Create a short-lived JWT for authenticated wallets."""
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_EXPIRATION_MINUTES
        )
        payload = {
            "wallet_address": wallet_address,
            "exp": int(expires_at.timestamp()),
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


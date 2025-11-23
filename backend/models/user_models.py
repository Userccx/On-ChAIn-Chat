# User and wallet schemas
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WalletAuthRequest(BaseModel):
    address: str
    signature: Optional[str] = None
    message: Optional[str] = None


class WalletTokenPayload(BaseModel):
    wallet_address: str
    exp: int


class NonceResponse(BaseModel):
    nonce: str
    message: str


class WalletAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    wallet_address: str
    nonce: str  # For signature verification
    created_at: Optional[datetime] = None


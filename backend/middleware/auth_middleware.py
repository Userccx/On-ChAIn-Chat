# Wallet verification
from fastapi import Header, HTTPException
import jwt

from config import settings


async def verify_wallet_token(authorization: str = Header(None, alias="Authorization")) -> str:
    """Verify JWT token from wallet authentication."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        wallet_address = payload.get("wallet_address")
        if not wallet_address:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return wallet_address
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


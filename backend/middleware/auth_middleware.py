# Wallet verification
from functools import wraps
from flask import request, jsonify

# 使用 PyJWT
import jwt

from ..config import settings


def verify_wallet_token(f):
    """Decorator to verify JWT token from wallet authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authorization = request.headers.get("Authorization")
        if not authorization:
            return jsonify({"detail": "Authorization header missing"}), 401

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return jsonify({"detail": "Invalid authorization scheme"}), 401

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            wallet_address = payload.get("wallet_address")
            if not wallet_address:
                return jsonify({"detail": "Invalid token payload"}), 401
            # Store wallet address in request context for use in route handlers
            request.wallet_address = wallet_address
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"detail": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"detail": "Invalid token"}), 401

    return decorated_function


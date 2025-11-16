# Signature utilities
from eth_account.messages import encode_defunct
from web3 import Web3

AUTH_MESSAGE_TEMPLATE = "Sign this message to authenticate: {nonce}"

_w3 = Web3()


def format_auth_message(nonce: str) -> str:
    """Return the canonical message the client must sign."""
    return AUTH_MESSAGE_TEMPLATE.format(nonce=nonce)


def normalize_address(address: str) -> str:
    """Return the lowercase checksum version of a wallet address."""
    try:
        return _w3.to_checksum_address(address)
    except Exception:
        # Fall back to lowercase if checksum conversion fails
        return address.lower()


def recover_address_from_signature(message: str, signature: str) -> str:
    """Recover the wallet address that produced the provided signature."""
    message_hash = encode_defunct(text=message)
    return _w3.eth.account.recover_message(message_hash, signature=signature)


def is_valid_signature(address: str, message: str, signature: str) -> bool:
    """Check whether `signature` was produced by `address` for `message`."""
    try:
        recovered = recover_address_from_signature(message, signature)
        return recovered.lower() == address.lower()
    except Exception:
        return False


# Signature utilities
from eth_account.messages import encode_defunct
from web3 import Web3

from .logger import get_logger

AUTH_MESSAGE_TEMPLATE = "Sign this message to authenticate: {nonce}"

_w3 = Web3()
logger = get_logger(__name__)


def format_auth_message(nonce: str) -> str:
    """Return the canonical message the client must sign."""
    return AUTH_MESSAGE_TEMPLATE.format(nonce=nonce)


def normalize_address(address: str) -> str:
    """Return the lowercase checksum version of a wallet address."""
    if not address:
        raise ValueError("Address cannot be empty")
    
    # 移除前后空格
    address = address.strip()
    
    # 检查基本格式
    if not address.startswith("0x"):
        raise ValueError(f"Invalid address format: must start with '0x'. Got: {address}")
    
    # 检查长度（应该是 0x + 40 个十六进制字符 = 42 个字符）
    if len(address) != 42:
        raise ValueError(
            f"Invalid address length: expected 42 characters (0x + 40 hex), got {len(address)}. "
            f"Address: {address}"
        )
    
    # 检查是否为有效的十六进制
    hex_part = address[2:]
    try:
        int(hex_part, 16)
    except ValueError:
        raise ValueError(f"Invalid address format: contains non-hexadecimal characters. Address: {address}")
    
    try:
        return _w3.to_checksum_address(address)
    except Exception as e:
        # Fall back to lowercase if checksum conversion fails
        logger.warning(f"⚠️ Warning: Failed to convert address to checksum format: {e}")
        return address.lower()


def recover_address_from_signature(message: str, signature: str) -> str:
    """Recover the wallet address that produced the provided signature."""
    message_hash = encode_defunct(text=message)
    return _w3.eth.account.recover_message(message_hash, signature=signature)


def is_valid_signature(address: str, message: str, signature: str) -> bool:
    """Check whether `signature` was produced by `address` for `message`."""
    logger.info(f"Checking signature for address: {address}, message: {message}, signature: {signature}")
    try:
        recovered = recover_address_from_signature(message, signature)
        logger.info(f"Signature verification - recovered address: {recovered}, expected: {address}")
        is_valid = recovered.lower() == address.lower()
        if not is_valid:
            logger.warning(f"Signature mismatch - recovered: {recovered}, expected: {address}")
        return is_valid
    except Exception as e:
        logger.error(f"Signature verification failed with exception: {e}")
        return False


from eth_account import Account
from eth_account.messages import encode_defunct

# 创建测试账户（或使用现有私钥）
#account = Account.create()  # 或 
account = Account.from_key("51580ac6b35bcc19d40547311543ba04f834c763e0c9a989a9016e4e9833f530")
print(f"地址: {account.address}")

# 假设从后端获取的 nonce
nonce = "ead49f1531756dc1dc901d80e320c237"
message = f"Sign this message to authenticate: {nonce}"

# 签名
message_hash = encode_defunct(text=message)
signed = Account.sign_message(message_hash, account.key)
signature = signed.signature.hex()

print(f"签名: {signature}")
# 然后在 Postman 中使用这个签名
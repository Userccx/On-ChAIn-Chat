# 钱包验证逻辑说明

## 📋 当前实现状态

### ✅ **已经支持真实钱包验证！**

代码已经实现了完整的钱包签名验证功能。是否启用真实验证取决于 `USE_MOCK_SERVICES` 配置。

---

## 🔄 钱包验证工作流程

### 完整流程

```
1. 前端请求 nonce
   ↓
2. 后端生成 nonce 并返回
   ↓
3. 前端使用钱包签名消息
   ↓
4. 前端发送签名到后端验证
   ↓
5. 后端验证签名
   ↓
6. 后端返回 JWT token
```

---

## 🔍 详细逻辑分析

### 1. 获取 Nonce (`GET /api/auth/nonce/<address>`)

**代码位置**: `backend/services/wallet_service.py` - `generate_nonce()`

**逻辑**:
```python
def generate_nonce(self, address: str) -> Dict[str, str]:
    normalized = normalize_address(address)
    
    # Mock 模式：固定 nonce
    # 真实模式：随机 nonce
    nonce = secrets.token_hex(16) if not self.mock_mode else "mock-nonce"
    
    self._store_nonce(normalized, nonce)
    return {
        "nonce": nonce,
        "message": format_auth_message(nonce),  # "Sign this message to authenticate: {nonce}"
        "wallet": normalized,
    }
```

**返回示例**:
```json
{
  "nonce": "a1b2c3d4e5f6...",  // Mock: "mock-nonce", 真实: 随机32字符
  "message": "Sign this message to authenticate: a1b2c3d4e5f6...",
  "wallet": "0x1234..."
}
```

### 2. 验证签名 (`POST /api/auth/verify`)

**代码位置**: `backend/services/wallet_service.py` - `verify_signature()`

**逻辑流程**:

```python
def verify_signature(self, address, message, signature):
    # 1. 规范化地址
    normalized = normalize_address(address)
    
    # 2. 检查 nonce 是否存在
    expected_nonce = self.active_nonces.get(normalized.lower())
    if not expected_nonce:
        return False, None, "鉴权 nonce 已失效或不存在，请重新获取。"
    
    # 3. 验证消息是否匹配
    expected_message = format_auth_message(expected_nonce)
    if not self.mock_mode and message != expected_message:
        return False, None, "签名消息与服务器下发的 nonce 不一致。"
    
    # 4. 验证签名（真实模式）
    if not self.mock_mode:
        if not is_valid_signature(normalized, message, signature or ""):
            return False, None, "签名校验失败，请确认钱包地址与签名内容。"
    else:
        # Mock 模式：自动通过
        if not message:
            message = expected_message
    
    # 5. 消耗 nonce（一次性使用）
    self._pop_nonce(normalized)
    
    # 6. 返回成功
    return True, normalized, None
```

### 3. 签名验证函数 (`is_valid_signature`)

**代码位置**: `backend/utils/crypto_utils.py`

**逻辑**:
```python
def is_valid_signature(address: str, message: str, signature: str) -> bool:
    """验证签名是否由指定地址产生"""
    try:
        # 1. 从签名恢复地址
        recovered = recover_address_from_signature(message, signature)
        
        # 2. 比较恢复的地址和提供的地址
        return recovered.lower() == address.lower()
    except Exception:
        return False

def recover_address_from_signature(message: str, signature: str) -> str:
    """从签名恢复钱包地址"""
    # 使用 Ethereum 消息格式
    message_hash = encode_defunct(text=message)
    # 恢复地址
    return _w3.eth.account.recover_message(message_hash, signature=signature)
```

---

## ⚙️ 两种模式对比

### Mock 模式 (`USE_MOCK_SERVICES=True`)

**特点**:
- ✅ 不需要真实钱包
- ✅ 不需要签名
- ✅ 用于开发和测试
- ❌ 不安全，不应该用于生产环境

**工作方式**:
1. Nonce 固定为 `"mock-nonce"`
2. 签名验证被跳过
3. 只要消息格式正确就通过

**请求示例**:
```json
{
  "address": "0x1234...",
  "message": "Sign this message to authenticate: mock-nonce",
  "signature": ""  // 可以为空
}
```

### 真实模式 (`USE_MOCK_SERVICES=False`) ✅

**特点**:
- ✅ 完整的签名验证
- ✅ 安全的身份验证
- ✅ 适合生产环境
- ⚠️ 需要前端正确实现签名

**工作方式**:
1. 生成随机 nonce（32 个十六进制字符）
2. 验证消息是否匹配服务器下发的 nonce
3. 使用 `eth_account.recover_message` 恢复地址
4. 比较恢复的地址和提供的地址
5. 只有签名有效才通过

**前端需要做的事情**:
```javascript
// 1. 获取 nonce
const response = await fetch('/api/auth/nonce/0xYourAddress');
const { nonce, message } = await response.json();

// 2. 使用钱包签名消息
const signature = await window.ethereum.request({
  method: 'personal_sign',
  params: [message, '0xYourAddress']
});

// 3. 发送验证请求
const verifyResponse = await fetch('/api/auth/verify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    address: '0xYourAddress',
    message: message,
    signature: signature
  })
});

// 4. 获取 JWT token
const { access_token } = await verifyResponse.json();
```

---

## 🔧 配置方式

### 启用真实钱包验证

在 `.env` 文件中：

```env
# 禁用 Mock 模式，启用真实验证
USE_MOCK_SERVICES=False
```

### 使用 Mock 模式（仅测试）

```env
# 启用 Mock 模式，跳过签名验证
USE_MOCK_SERVICES=True
```

---

## 📝 前端集成示例

### 使用 MetaMask 签名

```javascript
async function authenticateWallet() {
  try {
    // 1. 检查 MetaMask 是否安装
    if (!window.ethereum) {
      throw new Error('请安装 MetaMask');
    }
    
    // 2. 请求账户访问
    const accounts = await window.ethereum.request({
      method: 'eth_requestAccounts'
    });
    const address = accounts[0];
    
    // 3. 获取 nonce
    const nonceResponse = await fetch(
      `http://localhost:5000/api/auth/nonce/${address}`
    );
    const { nonce, message } = await nonceResponse.json();
    
    // 4. 使用 MetaMask 签名消息
    const signature = await window.ethereum.request({
      method: 'personal_sign',
      params: [message, address]
    });
    
    // 5. 验证签名
    const verifyResponse = await fetch(
      'http://localhost:5000/api/auth/verify',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address: address,
          message: message,
          signature: signature
        })
      }
    );
    
    if (!verifyResponse.ok) {
      throw new Error('验证失败');
    }
    
    const { access_token } = await verifyResponse.json();
    
    // 6. 保存 token
    localStorage.setItem('access_token', access_token);
    
    console.log('✅ 认证成功！');
    return access_token;
    
  } catch (error) {
    console.error('❌ 认证失败:', error);
    throw error;
  }
}
```

### 使用 ethers.js

```javascript
import { ethers } from 'ethers';

async function authenticateWithEthers() {
  // 1. 连接钱包
  const provider = new ethers.BrowserProvider(window.ethereum);
  const signer = await provider.getSigner();
  const address = await signer.getAddress();
  
  // 2. 获取 nonce
  const nonceResponse = await fetch(
    `http://localhost:5000/api/auth/nonce/${address}`
  );
  const { message } = await nonceResponse.json();
  
  // 3. 签名消息
  const signature = await signer.signMessage(message);
  
  // 4. 验证
  const verifyResponse = await fetch(
    'http://localhost:5000/api/auth/verify',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        address: address,
        message: message,
        signature: signature
      })
    }
  );
  
  const { access_token } = await verifyResponse.json();
  return access_token;
}
```

---

## ⚠️ 常见问题

### Q1: 为什么验证总是失败？

**可能原因**:
1. **消息不匹配**：前端签名的消息必须与后端返回的 `message` 完全一致
2. **签名格式错误**：签名必须是 0x 开头的 132 个字符（0x + 130 个十六进制字符）
3. **地址不匹配**：签名的地址必须与提供的地址一致
4. **Nonce 已过期**：nonce 是一次性的，验证后会被消耗

**解决方案**:
- 确保前端使用后端返回的 `message` 进行签名
- 检查签名格式是否正确
- 确保地址格式正确（42 个字符）

### Q2: Mock 模式和真实模式有什么区别？

**Mock 模式**:
- Nonce 固定为 `"mock-nonce"`
- 跳过签名验证
- 用于快速测试

**真实模式**:
- Nonce 是随机生成的
- 进行完整的签名验证
- 安全的身份验证

### Q3: 如何测试真实钱包验证？

**步骤**:
1. 设置 `USE_MOCK_SERVICES=False`
2. 使用 MetaMask 或其他钱包
3. 前端实现签名逻辑
4. 发送验证请求

### Q4: Nonce 会过期吗？

**当前实现**:
- Nonce 存储在内存中（`self.active_nonces`）
- 验证后立即删除（一次性使用）
- 服务重启后所有 nonce 失效

**生产环境建议**:
- 使用 Redis 或数据库存储 nonce
- 设置过期时间（如 5 分钟）
- 支持 nonce 重用（在一定时间内）

### Q5: 签名验证安全吗？

**安全性**:
- ✅ 使用标准的 Ethereum 消息签名格式
- ✅ 使用 `personal_sign` 或 `eth_sign` 方法
- ✅ 签名只能由私钥持有者产生
- ✅ 无法伪造签名

**注意事项**:
- 确保消息包含 nonce，防止重放攻击
- Nonce 应该是一次性的
- 建议添加时间戳验证

---

## 🔒 安全建议

### 1. Nonce 管理

**当前实现**（内存存储）:
```python
self.active_nonces: Dict[str, str] = {}
```

**生产环境建议**:
```python
# 使用 Redis 存储，设置过期时间
import redis
r = redis.Redis()
r.setex(f"nonce:{address}", 300, nonce)  # 5分钟过期
```

### 2. 消息格式

**当前格式**:
```
Sign this message to authenticate: {nonce}
```

**建议增强**:
```
Sign this message to authenticate: {nonce}
Timestamp: {timestamp}
Domain: {domain}
```

### 3. 速率限制

建议添加速率限制，防止暴力攻击：
- 每个 IP 地址每分钟最多 5 次 nonce 请求
- 每个地址每分钟最多 10 次验证尝试

---

## ✅ 验证检查清单

### 后端配置
- [ ] `USE_MOCK_SERVICES=False`（真实模式）
- [ ] 地址验证正常工作
- [ ] Nonce 生成和验证正常

### 前端实现
- [ ] 正确获取 nonce
- [ ] 使用正确的消息进行签名
- [ ] 签名格式正确（0x + 130 个字符）
- [ ] 正确发送验证请求

### 测试
- [ ] Mock 模式可以正常工作
- [ ] 真实模式可以正常验证
- [ ] 错误的签名会被拒绝
- [ ] Nonce 一次性使用正常

---

## 📚 相关代码文件

- `backend/services/wallet_service.py` - 钱包服务主逻辑
- `backend/utils/crypto_utils.py` - 签名验证工具
- `backend/routes/auth_routes.py` - 认证路由
- `backend/middleware/auth_middleware.py` - JWT 验证中间件

---

## 🎯 总结

**当前状态**:
- ✅ **已经支持真实钱包验证**
- ✅ 代码实现完整
- ✅ 签名验证逻辑正确

**使用方法**:
1. 设置 `USE_MOCK_SERVICES=False`
2. 前端实现钱包签名逻辑
3. 发送正确的签名进行验证

**下一步**:
- 实现前端签名逻辑
- 测试真实钱包验证
- 考虑添加 nonce 过期时间
- 考虑使用 Redis 存储 nonce（生产环境）


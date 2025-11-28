# Postman 环境变量配置指南

## 📋 重要区分

### Postman 环境变量 vs Pinata 配置

这是**两个完全不同的配置**：

1. **Postman 环境变量** (`wallet_address`)
   - 用于 API 测试
   - 是**钱包的公钥地址**（以太坊地址）
   - 格式：`0x` 开头，42 个字符

2. **Pinata 配置** (`.env` 文件中的 `PINATA_JWT`)
   - 用于 IPFS pinning 服务
   - 是 **Pinata API 的认证令牌**
   - 格式：JWT Token（很长的字符串）

---

## 🔑 Postman 环境变量配置

### `wallet_address` - 钱包公钥地址

**是的，应该配置你的钱包公钥地址！**

#### 格式要求

- ✅ 以太坊地址格式
- ✅ 以 `0x` 开头
- ✅ 总共 42 个字符
- ✅ 不区分大小写（系统会自动转换为小写）

#### 示例

```javascript
// ✅ 正确格式
0x1234567890abcdef1234567890abcdef12345678
0xAbCdEf1234567890AbCdEf1234567890AbCdEf12
0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb  // 真实地址示例

// ❌ 错误格式
1234567890abcdef1234567890abcdef12345678  // 缺少 0x
0x123  // 太短
wallet_address  // 不是地址格式
```

#### 在 Postman 中设置

1. 打开 Postman
2. 点击右上角的 **Environments** 图标
3. 选择或创建环境（例如：`Local Development`）
4. 添加变量：
   - **Variable**: `wallet_address`
   - **Initial Value**: `0x你的钱包地址`
   - **Current Value**: `0x你的钱包地址`

#### 使用场景

这个地址用于：

1. **获取 Nonce**
   ```
   GET /api/auth/nonce/{{wallet_address}}
   ```

2. **验证签名**
   ```json
   {
     "address": "{{wallet_address}}",
     "message": "...",
     "signature": "..."
   }
   ```

3. **NFT 铸造**
   ```json
   {
     "userAddress": "{{wallet_address}}",
     ...
   }
   ```

#### Mock 模式 vs 真实模式

**Mock 模式** (`USE_MOCK_SERVICES=True`):
- 可以使用**任何有效的以太坊地址格式**
- 不需要真实钱包
- 例如：`0x1234567890abcdef1234567890abcdef12345678`

**真实模式** (`USE_MOCK_SERVICES=False`):
- 需要使用**真实钱包地址**
- 需要该钱包的私钥进行签名
- 例如：你的 MetaMask 钱包地址

---

## 🔐 Pinata 配置（.env 文件）

### `PINATA_JWT` - Pinata API 认证令牌

**这不是钱包地址！** 这是 Pinata 服务的 API 凭证。

#### 配置位置

在项目根目录的 `.env` 文件中：

```env
# IPFS Pinning Service
IPFS_PINNING_SERVICE=pinata
PINATA_JWT=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # 这是 JWT Token，不是钱包地址
```

#### 如何获取

1. 访问 https://app.pinata.cloud/developers/api-keys
2. 创建新的 API Key
3. 复制 **JWT Token**（很长的字符串）
4. 粘贴到 `.env` 文件中

#### 格式示例

```env
PINATA_JWT=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

---

## 📝 完整配置示例

### Postman 环境变量

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `base_url` | `http://127.0.0.1:5000` | API 基础地址 |
| `wallet_address` | `0x1234567890abcdef1234567890abcdef12345678` | **钱包公钥地址** |
| `access_token` | (自动设置) | JWT 访问令牌 |
| `nonce` | (自动设置) | 认证 nonce |
| `auth_message` | (自动设置) | 认证消息 |
| `first_chat_hash` | (自动设置) | 第一条消息的 IPFS 哈希 |
| `index_hash` | (自动设置) | 索引文件的 IPFS 哈希 |

### .env 文件配置

```env
# App Configuration
USE_MOCK_SERVICES=True
DEBUG=True

# IPFS Configuration
IPFS_PINNING_SERVICE=pinata
PINATA_JWT=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Pinata JWT Token

# Blockchain Configuration
WEB3_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/...
CONTRACT_ADDRESS=0x...
PRIVATE_KEY=0x...  # 后端私钥（不是用户钱包私钥）
```

---

## ❓ 常见问题

### Q1: Postman 中的 `wallet_address` 应该填什么？

**A**: 填你的**钱包公钥地址**（以太坊地址），格式：`0x` 开头，42 个字符。

### Q2: 可以使用测试地址吗？

**A**: 
- **Mock 模式**：可以，使用任何有效的以太坊地址格式
- **真实模式**：需要使用真实钱包地址，并且需要该钱包的私钥进行签名

### Q3: 如何获取我的钱包地址？

**A**: 
- **MetaMask**: 点击账户名称，复制地址
- **其他钱包**: 查看账户信息，复制公钥地址

### Q4: Pinata 配置中的 `PINATA_JWT` 是钱包地址吗？

**A**: **不是！** `PINATA_JWT` 是 Pinata API 的认证令牌，不是钱包地址。从 Pinata Dashboard 获取。

### Q5: 为什么需要两个不同的配置？

**A**: 
- **Postman `wallet_address`**: 用于 API 测试，标识用户身份
- **Pinata `PINATA_JWT`**: 用于 IPFS pinning 服务，认证 Pinata API

### Q6: Mock 模式下可以使用真实钱包地址吗？

**A**: 可以，但不必要。Mock 模式下可以使用任何有效的以太坊地址格式。

---

## ✅ 配置检查清单

### Postman 环境变量
- [ ] `base_url` 已设置
- [ ] `wallet_address` 已设置（以太坊地址格式）
- [ ] `wallet_address` 以 `0x` 开头
- [ ] `wallet_address` 长度为 42 个字符

### .env 文件
- [ ] `IPFS_PINNING_SERVICE=pinata`（如果使用 Pinata）
- [ ] `PINATA_JWT` 已设置（如果使用 Pinata）
- [ ] `PINATA_JWT` 不是钱包地址，而是 JWT Token
- [ ] `USE_MOCK_SERVICES` 已设置

---

## 🚀 快速开始

### 步骤 1: 配置 Postman 环境变量

1. 打开 Postman
2. 创建新环境：`Local Development`
3. 添加变量：
   ```
   wallet_address = 0x1234567890abcdef1234567890abcdef12345678
   base_url = http://127.0.0.1:5000
   ```

### 步骤 2: 配置 .env 文件（如果需要 Pinata）

1. 在项目根目录创建或编辑 `.env` 文件
2. 添加：
   ```env
   IPFS_PINNING_SERVICE=pinata
   PINATA_JWT=你的_Pinata_JWT_Token
   ```

### 步骤 3: 测试

1. 在 Postman 中选择环境：`Local Development`
2. 执行测试：`Get Nonce`
3. 检查响应是否正常

---

## 📚 相关文档

- [Postman 测试计划](./POSTMAN_TEST_PLAN.md)
- [Pinata 配置指南](./PINATA_SETUP.md)
- [项目 README](./README.md)


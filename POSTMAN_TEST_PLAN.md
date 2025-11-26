# Postman 完整测试计划 v2.0

## 📋 目录

1. [测试环境配置](#测试环境配置)
2. [测试集合结构](#测试集合结构)
3. [详细测试用例](#详细测试用例)
4. [测试执行顺序](#测试执行顺序)
5. [自动化测试脚本](#自动化测试脚本)
6. [性能测试建议](#性能测试建议)

---

## 测试环境配置

### Base URL
```
http://127.0.0.1:5000
```
或使用 ngrok 暴露的公网地址：
```
https://your-ngrok-url.ngrok-free.app
```

### 环境变量（在 Postman 中设置）

| 变量名 | 初始值 | 说明 |
|--------|--------|------|
| `base_url` | `http://127.0.0.1:5000` | API 基础地址 |
| `wallet_address` | `0x1234567890abcdef1234567890abcdef12345678` | 测试钱包地址 |
| `access_token` | (自动设置) | JWT 访问令牌 |
| `nonce` | (自动设置) | 认证 nonce |
| `auth_message` | (自动设置) | 认证消息 |
| `first_chat_hash` | (自动设置) | 第一条消息的 IPFS 哈希 |
| `second_chat_hash` | (自动设置) | 第二条消息的 IPFS 哈希 |
| `index_hash` | (自动设置) | 钱包索引文件的 IPFS 哈希 |

---

## 测试集合结构

### 1. 健康检查 (2 个用例)
### 2. 钱包认证流程 (3 个用例)
### 3. 聊天功能测试 (5 个用例)
### 4. IPFS 存储与历史记录 (3 个用例)
### 5. 索引哈希管理 (3 个用例)
### 6. Pinning 管理 (3 个用例)
### 7. NFT 铸造功能 (4 个用例)
### 8. 错误场景测试 (6 个用例)

**总计：29 个测试用例**

---

## 详细测试用例

### 1. 健康检查

#### 1.1 根路径检查
- **Method**: `GET`
- **URL**: `{{base_url}}/`
- **Headers**: 无
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "message": "Tokenized LLM Interaction Platform API"
}
```

#### 1.2 健康检查
- **Method**: `GET`
- **URL**: `{{base_url}}/health`
- **Headers**: 无
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "status": "healthy",
  "environment": "development"
}
```

---

### 2. 钱包认证流程

#### 2.1 获取 Nonce
- **Method**: `GET`
- **URL**: `{{base_url}}/api/auth/nonce/{{wallet_address}}`
- **Headers**: 无
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "nonce": "mock-nonce",
  "message": "Sign this message to authenticate: mock-nonce",
  "wallet": "0x1234567890abcdef1234567890abcdef12345678"
}
```
- **Post-request Script**:
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("nonce", response.nonce);
    pm.environment.set("auth_message", response.message);
}
```

#### 2.2 验证签名（Mock 模式）
- **Method**: `POST`
- **URL**: `{{base_url}}/api/auth/verify`
- **Headers**: 
  - `Content-Type: application/json`
- **Body** (raw JSON):
```json
{
  "address": "{{wallet_address}}",
  "message": "{{auth_message}}",
  "signature": ""
}
```
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
- **Post-request Script**:
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("access_token", response.access_token);
    pm.test("Token received", function () {
        pm.expect(response.access_token).to.be.a('string');
    });
}
```

#### 2.3 验证签名失败（错误场景）
- **Method**: `POST`
- **URL**: `{{base_url}}/api/auth/verify`
- **Headers**: 
  - `Content-Type: application/json`
- **Body** (raw JSON):
```json
{
  "address": "{{wallet_address}}",
  "message": "wrong message",
  "signature": ""
}
```
- **Expected Status**: `401`
- **Expected Response**:
```json
{
  "detail": "签名消息与服务器下发的 nonce 不一致。"
}
```

---

### 3. 聊天功能测试

#### 3.1 发送第一条消息
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body** (raw JSON):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, what is blockchain?",
      "timestamp": null
    }
  ],
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 2000
}
```
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "reply": "Hello world",
  "model_used": "gpt-4o-mini",
  "tokens_used": 2,
  "provider": "mock",
  "latency_ms": 0,
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "ipfs_hash": "Qm...",
  "stored_at": "2025-11-26T15:30:00.123456"
}
```
- **Post-request Script**:
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    if (response.ipfs_hash) {
        pm.environment.set("first_chat_hash", response.ipfs_hash);
    }
    pm.test("Response has IPFS hash", function () {
        pm.expect(response).to.have.property('ipfs_hash');
        pm.expect(response).to.have.property('stored_at');
    });
}
```

#### 3.2 发送第二条消息（带上下文）
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body** (raw JSON):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, what is blockchain?",
      "timestamp": null
    },
    {
      "role": "assistant",
      "content": "Hello world",
      "timestamp": null
    },
    {
      "role": "user",
      "content": "Can you explain more?",
      "timestamp": null
    }
  ],
  "model": "gpt-4o-mini"
}
```
- **Expected Status**: `200`
- **Post-request Script**:
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    if (response.ipfs_hash) {
        pm.environment.set("second_chat_hash", response.ipfs_hash);
    }
}
```

#### 3.3 发送第三条消息（测试历史记录累积）
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body** (raw JSON):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What are the benefits?",
      "timestamp": null
    }
  ],
  "model": "gpt-4o-mini"
}
```
- **Expected Status**: `200`

#### 3.4 聊天 - 缺少 Authorization
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Content-Type: application/json`
- **Body** (raw JSON):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Test message"
    }
  ]
}
```
- **Expected Status**: `401`
- **Expected Response**:
```json
{
  "detail": "Authorization header missing"
}
```

#### 3.5 聊天 - 空消息列表
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body** (raw JSON):
```json
{
  "messages": []
}
```
- **Expected Status**: `422`
- **Expected Response**:
```json
{
  "detail": "对话消息不能为空。"
}
```

---

### 4. IPFS 存储与历史记录

#### 4.1 获取历史对话记录
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/history`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "total_turns": 3,
  "history": [
    {
      "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
      "user_message": "Hello, what is blockchain?",
      "assistant_reply": "Hello world",
      "model_used": "gpt-4o-mini",
      "timestamp": "2025-11-26T15:30:00"
    },
    {
      "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
      "user_message": "Can you explain more?",
      "assistant_reply": "Hello world",
      "model_used": "gpt-4o-mini",
      "timestamp": "2025-11-26T15:31:00"
    }
  ]
}
```
- **Tests Script**:
```javascript
pm.test("History retrieved successfully", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response).to.have.property('wallet_address');
    pm.expect(response).to.have.property('total_turns');
    pm.expect(response).to.have.property('history');
    pm.expect(response.history).to.be.an('array');
    pm.expect(response.total_turns).to.be.at.least(1);
});
```

#### 4.2 获取已固定内容列表
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/pinned`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "total_pinned": 3,
  "pinned_content": [
    {
      "ipfs_hash": "Qm...",
      "service": "pinata",
      "pin_id": "...",
      "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
      "pinned_at": "2025-11-26T15:30:00"
    }
  ]
}
```

#### 4.3 获取历史记录 - 新钱包（空历史）
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/history`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Note**: 使用一个新的钱包地址（未发送过消息）
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "wallet_address": "0xNewWalletAddress...",
  "total_turns": 0,
  "history": []
}
```

---

### 5. 索引哈希管理（新增）

#### 5.1 获取索引哈希
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/index-hash`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "index_hash": "Qm...",
  "has_index": true
}
```
- **Post-request Script**:
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    if (response.index_hash) {
        pm.environment.set("index_hash", response.index_hash);
    }
    pm.test("Index hash retrieved", function () {
        pm.expect(response).to.have.property('index_hash');
        pm.expect(response).to.have.property('has_index');
    });
}
```

#### 5.2 设置索引哈希（恢复索引）
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat/index-hash`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body** (raw JSON):
```json
{
  "index_hash": "{{index_hash}}"
}
```
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "message": "Index hash set successfully",
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "index_hash": "Qm..."
}
```

#### 5.3 设置索引哈希 - 缺少参数
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat/index-hash`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body** (raw JSON):
```json
{}
```
- **Expected Status**: `400`
- **Expected Response**:
```json
{
  "detail": "index_hash is required"
}
```

---

### 6. Pinning 管理

#### 6.1 取消固定对话记录
- **Method**: `DELETE`
- **URL**: `{{base_url}}/api/chat/unpin/{{first_chat_hash}}`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "message": "Successfully unpinned from Pinata",
  "ipfs_hash": "Qm...",
  "service": "pinata"
}
```

#### 6.2 取消固定 - 无效哈希
- **Method**: `DELETE`
- **URL**: `{{base_url}}/api/chat/unpin/QmInvalidHash123456789`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `400` 或 `500`
- **Expected Response**:
```json
{
  "detail": "Failed to unpin content: ..."
}
```

#### 6.3 取消固定 - 缺少 Authorization
- **Method**: `DELETE`
- **URL**: `{{base_url}}/api/chat/unpin/{{first_chat_hash}}`
- **Headers**: 无
- **Expected Status**: `401`

---

### 7. NFT 铸造功能

#### 7.1 铸造对话 NFT
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body** (raw JSON):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, what is blockchain?",
      "timestamp": null
    },
    {
      "role": "assistant",
      "content": "Hello world",
      "timestamp": null
    }
  ],
  "conversationTitle": "My First NFT Conversation",
  "description": "A conversation about blockchain technology",
  "userAddress": "{{wallet_address}}"
}
```
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "metadataUrl": "ipfs://Qm...",
  "ipfs_hash": "Qm...",
  "gatewayUrl": "https://ipfs.io/ipfs/Qm...",
  "token_id": 1,
  "tx_hash": "0xaaaaaaaa...",
  "message": "NFT minted successfully (pseudo mode)"
}
```

#### 7.2 铸造 NFT - 钱包地址不匹配
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body** (raw JSON):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Test"
    }
  ],
  "conversationTitle": "Test",
  "userAddress": "0xDifferentAddress123456789012345678901234567890"
}
```
- **Expected Status**: `422`
- **Expected Response**:
```json
{
  "detail": "会话钱包地址与认证地址不一致。"
}
```

#### 7.3 铸造 NFT - 标题过长
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body** (raw JSON):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Test"
    }
  ],
  "conversationTitle": "A very long title that exceeds the maximum allowed length of 120 characters and should trigger a validation error",
  "userAddress": "{{wallet_address}}"
}
```
- **Expected Status**: `422`
- **Expected Response**:
```json
{
  "detail": "标题长度不得超过 120 个字符。"
}
```

#### 7.4 铸造 NFT - 空消息
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body** (raw JSON):
```json
{
  "messages": [],
  "conversationTitle": "Empty Conversation",
  "userAddress": "{{wallet_address}}"
}
```
- **Expected Status**: `422`
- **Expected Response**:
```json
{
  "detail": "对话消息不能为空。"
}
```

---

### 8. 错误场景测试

#### 8.1 无效的请求体
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body** (raw JSON):
```json
{
  "invalid_field": "test"
}
```
- **Expected Status**: `400`
- **Expected Response**:
```json
{
  "detail": "Invalid request: ..."
}
```

#### 8.2 Token 过期测试
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/history`
- **Headers**: 
  - `Authorization: Bearer expired_token_here`
- **Expected Status**: `401`
- **Expected Response**:
```json
{
  "detail": "Token expired"
}
```

#### 8.3 无效 Token
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/history`
- **Headers**: 
  - `Authorization: Bearer invalid_token_here`
- **Expected Status**: `401`
- **Expected Response**:
```json
{
  "detail": "Invalid token"
}
```

#### 8.4 错误的 HTTP 方法
- **Method**: `PUT`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `405` (Method Not Allowed)

#### 8.5 无效的 IPFS 哈希格式
- **Method**: `DELETE`
- **URL**: `{{base_url}}/api/chat/unpin/invalid-hash-format`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `400` 或 `500`

#### 8.6 缺少请求体
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body**: (空)
- **Expected Status**: `400`
- **Expected Response**:
```json
{
  "detail": "Request body is required"
}
```

---

## 测试执行顺序

### 🔄 完整流程测试（Happy Path）

1. ✅ **健康检查** (1.1, 1.2)
2. ✅ **获取 Nonce** (2.1)
3. ✅ **验证签名** (2.2)
4. ✅ **发送第一条消息** (3.1)
5. ✅ **发送第二条消息** (3.2)
6. ✅ **发送第三条消息** (3.3)
7. ✅ **获取历史记录** (4.1) - **验证修复后的历史记录功能**
8. ✅ **获取索引哈希** (5.1) - **验证索引管理**
9. ✅ **获取已固定内容** (4.2)
10. ✅ **铸造 NFT** (7.1)

### ❌ 错误场景测试

11. ✅ **认证失败** (2.3)
12. ✅ **缺少 Authorization** (3.4, 6.3)
13. ✅ **空消息** (3.5, 7.4)
14. ✅ **钱包地址不匹配** (7.2)
15. ✅ **标题过长** (7.3)
16. ✅ **取消固定测试** (6.1, 6.2)
17. ✅ **索引哈希管理** (5.2, 5.3)
18. ✅ **其他错误场景** (8.1-8.6)

---

## 自动化测试脚本

### Collection 级别的 Pre-request Script

在 Postman Collection 设置中添加：

```javascript
// 自动设置时间戳
pm.environment.set("timestamp", new Date().toISOString());

// 检查 base_url 是否设置
if (!pm.environment.get("base_url")) {
    console.warn("⚠️ base_url not set, using default");
    pm.environment.set("base_url", "http://127.0.0.1:5000");
}
```

### Collection 级别的 Tests

```javascript
// 全局测试：检查响应时间
pm.test("Response time is less than 5000ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(5000);
});

// 全局测试：检查响应格式
if (pm.response.code < 400) {
    pm.test("Response is valid JSON", function () {
        pm.response.to.be.json;
    });
}
```

### 常用测试脚本模板

#### 验证响应结构
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has required fields", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('field_name');
});
```

#### 保存变量供后续使用
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    if (response.access_token) {
        pm.environment.set("access_token", response.access_token);
    }
    if (response.ipfs_hash) {
        pm.collectionVariables.set("last_ipfs_hash", response.ipfs_hash);
    }
}
```

#### 验证 IPFS 哈希格式
```javascript
pm.test("IPFS hash is valid format", function () {
    const jsonData = pm.response.json();
    if (jsonData.ipfs_hash) {
        // IPFS 哈希通常以 Qm 开头，长度为 46 字符
        pm.expect(jsonData.ipfs_hash).to.match(/^Qm[a-zA-Z0-9]{44}$/);
    }
});
```

---

## 性能测试建议

### 并发测试

使用 Postman Runner 执行并发请求：

1. **多用户同时发送消息**
   - 创建多个环境，每个环境使用不同的钱包地址
   - 同时发送多条消息
   - 监控响应时间和错误率

2. **历史记录查询性能**
   - 发送大量消息（10+ 条）
   - 测试获取历史记录的性能
   - 验证数据完整性

### 负载测试

1. **大量消息测试**
   - 连续发送 50+ 条消息
   - 测试 IPFS 存储性能
   - 验证索引更新性能

2. **历史记录查询（大数据量）**
   - 在发送大量消息后
   - 测试历史记录查询性能
   - 验证分页或限制功能（如果实现）

---

## 测试检查清单

### ✅ 功能测试
- [ ] 所有 API 端点都能正常响应
- [ ] 认证流程完整（nonce → verify → token）
- [ ] 聊天功能正常（发送消息、获取回复）
- [ ] 历史记录能正确返回（修复后）
- [ ] IPFS 存储正常工作
- [ ] Pinning 功能正常
- [ ] 索引哈希管理正常
- [ ] NFT 铸造功能正常

### ✅ 错误处理
- [ ] 认证失败正确处理
- [ ] 缺少 token 时返回 401
- [ ] 无效请求体返回 400
- [ ] 验证错误返回 422
- [ ] 服务器错误返回 500

### ✅ 数据完整性
- [ ] 历史记录包含所有发送的消息
- [ ] 历史记录按时间排序
- [ ] IPFS 哈希格式正确
- [ ] 钱包地址正确关联

### ✅ 边界情况
- [ ] 空消息列表处理
- [ ] 标题长度限制
- [ ] 钱包地址不匹配
- [ ] 无效 IPFS 哈希
- [ ] Token 过期处理

---

## 注意事项

1. **Mock 模式 vs 真实模式**
   - 如果 `USE_MOCK_SERVICES=True`，某些功能会返回模拟数据
   - 真实 IPFS 模式需要配置 IPFS 节点或 Pinata

2. **Token 有效期**
   - JWT token 默认 60 分钟
   - 过期后需要重新认证

3. **环境变量**
   - 确保 `.env` 文件配置正确
   - 测试前检查所有必要的配置项

4. **IPFS 连接**
   - 真实模式需要 IPFS 节点运行
   - 或配置 Pinata 服务

5. **CORS 配置**
   - 如果从浏览器测试，确保 CORS 配置允许你的域名

6. **数据持久性**
   - Mock 模式：数据存储在内存，服务重启后丢失
   - 真实模式：数据存储在 IPFS，持久化

---

## 快速开始

1. **导入 Collection**
   - 打开 Postman
   - 点击 "Import"
   - 选择 `Tokenized_LLM_Platform_API.postman_collection.json`

2. **创建环境**
   - 创建新环境 "Local Development"
   - 设置所有必要的环境变量

3. **执行测试**
   - 按照测试执行顺序逐个运行
   - 或使用 Postman Runner 批量执行

4. **查看结果**
   - 检查每个请求的响应
   - 查看测试脚本的执行结果
   - 检查控制台日志

5. **调试问题**
   - 查看响应详情
   - 检查服务器日志
   - 验证环境变量设置

---

## 更新日志

### v2.0 (2025-11-26)
- ✅ 添加索引哈希管理 API 测试用例
- ✅ 更新历史记录测试（修复后）
- ✅ 添加更详细的测试脚本
- ✅ 优化测试执行顺序
- ✅ 添加性能测试建议
- ✅ 完善错误场景测试

### v1.0 (2025-11-25)
- ✅ 初始版本
- ✅ 基础 API 测试用例

# Postman 完整测试计划 v3.0

## 📋 目录

1. [测试环境配置](#测试环境配置)
2. [测试集合结构](#测试集合结构)
3. [详细测试用例](#详细测试用例)
4. [测试执行顺序](#测试执行顺序)
5. [自动化测试脚本](#自动化测试脚本)

---

## 测试环境配置

### Base URL
```
http://127.0.0.1:5000
```

### 环境变量（在 Postman 中设置）

| 变量名 | 初始值 | 说明 |
|--------|--------|------|
| `base_url` | `http://127.0.0.1:5000` | API 基础地址 |
| `wallet_address` | `0x1234567890abcdef1234567890abcdef12345678` | 测试钱包地址 |
| `access_token` | (自动设置) | JWT 访问令牌 |
| `nonce` | (自动设置) | 认证 nonce |
| `auth_message` | (自动设置) | 认证消息 |
| `conversation_id` | (自动设置) | 当前对话 ID |
| `message_id` | (自动设置) | 消息 ID |
| `mint_id` | (自动设置) | 铸造记录 ID |
| `ipfs_hash` | (自动设置) | IPFS 哈希 |

---

## 测试集合结构

### 1. 健康检查 (2 个用例)
### 2. 钱包认证流程 (3 个用例)
### 3. 对话管理 (6 个用例) ⭐ 新增
### 4. 聊天功能 (5 个用例)
### 5. NFT 铸造功能 (7 个用例) ⭐ 更新
### 6. 市场功能 (4 个用例) ⭐ 新增
### 7. 存储服务 (3 个用例)
### 8. 错误场景测试 (6 个用例)

**总计：36 个测试用例**

---

## 详细测试用例

### 1. 健康检查

#### 1.1 根路径检查
- **Method**: `GET`
- **URL**: `{{base_url}}/`
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
- **Body**:
```json
{
  "address": "{{wallet_address}}",
  "message": "{{auth_message}}",
  "signature": ""
}
```
- **Expected Status**: `200`
- **Post-request Script**:
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("access_token", response.access_token);
}
```

#### 2.3 验证签名失败
- **Method**: `POST`
- **URL**: `{{base_url}}/api/auth/verify`
- **Body**:
```json
{
  "address": "{{wallet_address}}",
  "message": "wrong message",
  "signature": ""
}
```
- **Expected Status**: `401`

---

### 3. 对话管理 ⭐ 新增

#### 3.1 创建新对话
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat/conversations`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body**:
```json
{
  "title": "My First Conversation"
}
```
- **Expected Status**: `201`
- **Expected Response**:
```json
{
  "id": "uuid-string",
  "title": "My First Conversation",
  "wallet_address": "0x1234...",
  "created_at": "2025-11-28T12:00:00"
}
```
- **Post-request Script**:
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("conversation_id", response.id);
}
```

#### 3.2 获取对话列表
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/conversations`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "wallet_address": "0x1234...",
  "total": 1,
  "conversations": [
    {
      "id": "uuid-string",
      "title": "My First Conversation",
      "wallet_address": "0x1234...",
      "message_count": 0,
      "last_message_preview": null,
      "has_minted_messages": false,
      "minted_count": 0,
      "unminted_count": 0,
      "can_mint": false,
      "created_at": "2025-11-28T12:00:00",
      "updated_at": "2025-11-28T12:00:00"
    }
  ]
}
```

#### 3.3 获取对话详情
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/conversations/{{conversation_id}}`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "id": "uuid-string",
  "title": "My First Conversation",
  "wallet_address": "0x1234...",
  "messages": [],
  "created_at": "2025-11-28T12:00:00",
  "updated_at": "2025-11-28T12:00:00",
  "ipfs_hash": "Qm...",
  "minted_count": 0,
  "unminted_count": 0,
  "can_mint": false
}
```

#### 3.4 获取对话详情 - 不存在
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/conversations/non-existent-id`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `404`
- **Expected Response**:
```json
{
  "detail": "Conversation not found"
}
```

#### 3.5 获取历史消息（扁平化）
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/history`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "wallet_address": "0x1234...",
  "total_messages": 0,
  "history": []
}
```

#### 3.6 获取铸造记录列表
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/minted`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "wallet_address": "0x1234...",
  "total": 0,
  "minted_records": []
}
```

---

### 4. 聊天功能

#### 4.1 发送第一条消息（创建新对话）
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, what is blockchain?"
    }
  ],
  "model": "gpt-4"
}
```
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "reply": "Hello world",
  "model_used": "gpt-4",
  "tokens_used": 2,
  "provider": "mock",
  "latency_ms": 0,
  "conversation_id": "uuid-string",
  "message_id": "uuid-string",
  "wallet_address": "0x1234...",
  "ipfs_hash": "Qm...",
  "stored_at": "2025-11-28T12:00:00"
}
```
- **Post-request Script**:
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("conversation_id", response.conversation_id);
    pm.environment.set("message_id", response.message_id);
    pm.environment.set("ipfs_hash", response.ipfs_hash);
}
```

#### 4.2 在现有对话中发送消息
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Can you explain more about smart contracts?"
    }
  ],
  "conversation_id": "{{conversation_id}}",
  "model": "gpt-4"
}
```
- **Expected Status**: `200`
- **Post-request Script**:
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("second_message_id", response.message_id);
}
```

#### 4.3 验证对话已更新
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/conversations/{{conversation_id}}`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Tests Script**:
```javascript
pm.test("Conversation has messages", function () {
    const response = pm.response.json();
    pm.expect(response.messages.length).to.be.at.least(2);
    pm.expect(response.unminted_count).to.be.at.least(2);
    pm.expect(response.can_mint).to.be.true;
});
```

#### 4.4 聊天 - 缺少 Authorization
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Body**:
```json
{
  "messages": [{"role": "user", "content": "Test"}]
}
```
- **Expected Status**: `401`

#### 4.5 聊天 - 空消息列表
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Body**:
```json
{
  "messages": []
}
```
- **Expected Status**: `422`

---

### 5. NFT 铸造功能 ⭐ 更新

#### 5.1 铸造对话为 NFT
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body**:
```json
{
  "conversation_id": "{{conversation_id}}",
  "conversationTitle": "My First NFT Conversation",
  "description": "A conversation about blockchain technology"
}
```
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "mint_id": "uuid-string",
  "conversation_id": "uuid-string",
  "message_ids": ["msg-1", "msg-2"],
  "metadataUrl": "ipfs://Qm...",
  "ipfs_hash": "Qm...",
  "gatewayUrl": "https://gateway.pinata.cloud/ipfs/Qm...",
  "token_id": 1,
  "tx_hash": "0xaaa...",
  "listing_id": null,
  "message": "NFT minted successfully"
}
```
- **Post-request Script**:
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("mint_id", response.mint_id);
    pm.environment.set("minted_message_ids", JSON.stringify(response.message_ids));
}
```

#### 5.2 验证消息已标记为铸造
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/conversations/{{conversation_id}}`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Tests Script**:
```javascript
pm.test("Messages are marked as minted", function () {
    const response = pm.response.json();
    const mintedMessages = response.messages.filter(m => m.is_minted);
    pm.expect(mintedMessages.length).to.be.at.least(1);
    pm.expect(response.minted_count).to.be.at.least(1);
});
```

#### 5.3 重复铸造同一对话（应失败或自动过滤）
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body**:
```json
{
  "conversation_id": "{{conversation_id}}",
  "conversationTitle": "Duplicate Mint Attempt"
}
```
- **Expected Status**: `400`
- **Expected Response**:
```json
{
  "detail": "No unminted messages to mint. All selected messages have already been minted.",
  "already_minted_count": 4
}
```

#### 5.4 添加新消息后再次铸造（仅铸造新消息）
- **先发送新消息**:
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Body**:
```json
{
  "messages": [{"role": "user", "content": "What about DeFi?"}],
  "conversation_id": "{{conversation_id}}"
}
```

- **然后铸造**:
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints`
- **Body**:
```json
{
  "conversation_id": "{{conversation_id}}",
  "conversationTitle": "Extended NFT Conversation"
}
```
- **Expected Status**: `200`
- **Tests Script**:
```javascript
pm.test("Only new messages are minted", function () {
    const response = pm.response.json();
    pm.expect(response.message_ids.length).to.equal(2); // 只有新的 user + assistant 消息
});
```

#### 5.5 获取铸造记录详情
- **Method**: `GET`
- **URL**: `{{base_url}}/api/mints/{{mint_id}}`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "id": "uuid-string",
  "conversation_id": "uuid-string",
  "message_ids": ["msg-1", "msg-2"],
  "wallet_address": "0x1234...",
  "ipfs_hash": "Qm...",
  "metadata_url": "ipfs://Qm...",
  "gateway_url": "https://gateway.pinata.cloud/ipfs/Qm...",
  "tx_hash": "0xaaa...",
  "token_id": 1,
  "listing_id": null,
  "price": 0,
  "is_listed": false,
  "owner_address": "0x1234...",
  "minted_at": "2025-11-28T12:00:00"
}
```

#### 5.6 铸造 - 对话不存在
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints`
- **Body**:
```json
{
  "conversation_id": "non-existent-id",
  "conversationTitle": "Test"
}
```
- **Expected Status**: `404`
- **Expected Response**:
```json
{
  "detail": "Conversation not found"
}
```

#### 5.7 铸造 - 指定不存在的消息 ID
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints`
- **Body**:
```json
{
  "conversation_id": "{{conversation_id}}",
  "message_ids": ["invalid-msg-id"],
  "conversationTitle": "Test"
}
```
- **Expected Status**: `400`
- **Expected Response**:
```json
{
  "detail": "Invalid message IDs: ['invalid-msg-id']"
}
```

---

### 6. 市场功能 ⭐ 新增

#### 6.1 上架 NFT 到市场
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints/{{mint_id}}/list`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- **Body**:
```json
{
  "price": 100
}
```
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "message": "Listed on market successfully",
  "mint_id": "uuid-string",
  "listing_id": 1,
  "price": 100,
  "tx_hash": "0xaaa..."
}
```

#### 6.2 验证 NFT 已上架
- **Method**: `GET`
- **URL**: `{{base_url}}/api/mints/{{mint_id}}`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Tests Script**:
```javascript
pm.test("NFT is listed", function () {
    const response = pm.response.json();
    pm.expect(response.is_listed).to.be.true;
    pm.expect(response.price).to.equal(100);
    pm.expect(response.listing_id).to.not.be.null;
});
```

#### 6.3 从市场下架 NFT
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints/{{mint_id}}/unlist`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "message": "Unlisted from market successfully",
  "mint_id": "uuid-string",
  "tx_hash": "0xaaa..."
}
```

#### 6.4 上架 - 无效价格
- **Method**: `POST`
- **URL**: `{{base_url}}/api/mints/{{mint_id}}/list`
- **Body**:
```json
{
  "price": 0
}
```
- **Expected Status**: `400`
- **Expected Response**:
```json
{
  "detail": "Price must be greater than 0"
}
```

---

### 7. 存储服务

#### 7.1 获取存储服务状态
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/status`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "wallet_address": "0x1234...",
  "service": "pinata",
  "available": true,
  "gateway": "https://gateway.pinata.cloud/ipfs/",
  "app_identifier": "tokenized_llm_platform",
  "cached_conversations": 1,
  "cached_mint_records": 1
}
```

#### 7.2 取消固定 IPFS 内容
- **Method**: `DELETE`
- **URL**: `{{base_url}}/api/chat/unpin/{{ipfs_hash}}`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `200`
- **Expected Response**:
```json
{
  "message": "Content unpinned successfully",
  "ipfs_hash": "Qm..."
}
```

#### 7.3 取消固定 - 无效哈希
- **Method**: `DELETE`
- **URL**: `{{base_url}}/api/chat/unpin/QmInvalidHash123`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `400`

---

### 8. 错误场景测试

#### 8.1 无效的请求体
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Body**:
```json
{
  "invalid_field": "test"
}
```
- **Expected Status**: `400`

#### 8.2 Token 过期测试
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/history`
- **Headers**: 
  - `Authorization: Bearer expired_token_here`
- **Expected Status**: `401`

#### 8.3 无效 Token
- **Method**: `GET`
- **URL**: `{{base_url}}/api/chat/history`
- **Headers**: 
  - `Authorization: Bearer invalid_token`
- **Expected Status**: `401`

#### 8.4 错误的 HTTP 方法
- **Method**: `PUT`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `405`

#### 8.5 缺少请求体
- **Method**: `POST`
- **URL**: `{{base_url}}/api/chat`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Body**: (空)
- **Expected Status**: `400`

#### 8.6 获取不存在的铸造记录
- **Method**: `GET`
- **URL**: `{{base_url}}/api/mints/non-existent-id`
- **Headers**: 
  - `Authorization: Bearer {{access_token}}`
- **Expected Status**: `404`

---

## 测试执行顺序

### 🔄 完整流程测试（Happy Path）

```
1. 健康检查 (1.1, 1.2)
         ↓
2. 获取 Nonce (2.1)
         ↓
3. 验证签名 (2.2) → 获取 access_token
         ↓
4. 创建对话 (3.1) → 获取 conversation_id
         ↓
5. 发送消息 (4.1, 4.2) → 对话中累积消息
         ↓
6. 验证对话 (4.3) → 确认 can_mint=true
         ↓
7. 铸造 NFT (5.1) → 获取 mint_id
         ↓
8. 验证铸造状态 (5.2) → is_minted=true
         ↓
9. 上架到市场 (6.1)
         ↓
10. 验证上架 (6.2) → is_listed=true
         ↓
11. 下架 (6.3)
         ↓
12. 添加新消息并再次铸造 (5.4) → 只铸造新消息
```

### ❌ 错误场景测试

```
- 认证失败 (2.3)
- 缺少 Authorization (4.4)
- 空消息 (4.5)
- 对话不存在 (3.4, 5.6)
- 重复铸造 (5.3)
- 无效消息 ID (5.7)
- 无效价格 (6.4)
- 其他错误 (8.1-8.6)
```

---

## 自动化测试脚本

### Collection Pre-request Script

```javascript
// 自动设置时间戳
pm.environment.set("timestamp", new Date().toISOString());

// 检查 base_url
if (!pm.environment.get("base_url")) {
    pm.environment.set("base_url", "http://127.0.0.1:5000");
}
```

### Collection Tests

```javascript
// 响应时间检查
pm.test("Response time < 5s", function () {
    pm.expect(pm.response.responseTime).to.be.below(5000);
});

// JSON 格式检查
if (pm.response.code < 400) {
    pm.test("Response is valid JSON", function () {
        pm.response.to.be.json;
    });
}
```

---

## API 端点汇总

| 端点 | 方法 | 说明 | 需要认证 |
|------|------|------|----------|
| `/` | GET | 根路径 | ❌ |
| `/health` | GET | 健康检查 | ❌ |
| `/api/auth/nonce/{address}` | GET | 获取 Nonce | ❌ |
| `/api/auth/verify` | POST | 验证签名 | ❌ |
| `/api/chat` | POST | 发送消息 | ✅ |
| `/api/chat/conversations` | GET | 获取对话列表 | ✅ |
| `/api/chat/conversations` | POST | 创建对话 | ✅ |
| `/api/chat/conversations/{id}` | GET | 获取对话详情 | ✅ |
| `/api/chat/history` | GET | 获取历史消息 | ✅ |
| `/api/chat/minted` | GET | 获取铸造记录 | ✅ |
| `/api/chat/status` | GET | 存储服务状态 | ✅ |
| `/api/chat/unpin/{hash}` | DELETE | 取消固定 | ✅ |
| `/api/mints` | POST | 铸造 NFT | ✅ |
| `/api/mints/{id}` | GET | 获取铸造详情 | ✅ |
| `/api/mints/{id}/list` | POST | 上架到市场 | ✅ |
| `/api/mints/{id}/unlist` | POST | 从市场下架 | ✅ |

---

## 更新日志

### v3.0 (2025-11-28)
- ✅ 新增对话管理 API (conversations)
- ✅ 更新聊天 API 支持 conversation_id
- ✅ 重构铸造 API 基于 conversation_id
- ✅ 新增铸造防重复功能（自动过滤已铸造消息）
- ✅ 新增市场上架/下架功能
- ✅ 新增存储服务状态接口
- ✅ 新增铸造统计字段 (minted_count, unminted_count, can_mint)
- ✅ 优化测试执行流程

### v2.0 (2025-11-26)
- ✅ 添加索引哈希管理 API
- ✅ 添加 IPFS 存储功能

### v1.0 (2025-11-25)
- ✅ 初始版本

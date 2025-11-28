# 前端 API 接口指南

> 后端 API 设计文档，供前端开发参考

## 📋 目录

1. [基础信息](#基础信息)
2. [认证流程](#认证流程)
3. [对话管理](#对话管理)
4. [聊天功能](#聊天功能)
5. [NFT 铸造](#nft-铸造)
6. [市场功能](#市场功能)
7. [数据结构](#数据结构)
8. [错误处理](#错误处理)

---

## 基础信息

### Base URL
```
开发环境: http://127.0.0.1:5000
生产环境: https://your-domain.com
```

### 通用请求头
```
Content-Type: application/json
Authorization: Bearer <access_token>  // 需要认证的接口
```

### 响应格式
所有响应均为 JSON 格式。

---

## 认证流程

### 流程图

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  1. 获取    │      │  2. 钱包    │      │  3. 获取    │
│    Nonce    │ ───► │   签名     │ ───► │   Token    │
└─────────────┘      └─────────────┘      └─────────────┘
     │                     │                    │
     ▼                     ▼                    ▼
  GET /nonce         前端调用钱包           POST /verify
                     signMessage
```

### 1. 获取 Nonce

```http
GET /api/auth/nonce/{wallet_address}
```

**请求示例:**
```
GET /api/auth/nonce/0x1234567890abcdef1234567890abcdef12345678
```

**响应:**
```json
{
  "nonce": "abc123xyz",
  "message": "Sign this message to authenticate: abc123xyz",
  "wallet": "0x1234567890abcdef1234567890abcdef12345678"
}
```

**前端使用:**
```typescript
const { nonce, message, wallet } = await fetch(`/api/auth/nonce/${address}`).then(r => r.json());
```

### 2. 前端签名（使用钱包）

```typescript
// 使用 ethers.js
const signature = await signer.signMessage(message);

// 使用 wagmi
const signature = await signMessageAsync({ message });
```

### 3. 验证签名获取 Token

```http
POST /api/auth/verify
```

**请求体:**
```json
{
  "address": "0x1234567890abcdef1234567890abcdef12345678",
  "message": "Sign this message to authenticate: abc123xyz",
  "signature": "0x..."
}
```

**响应:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**前端使用:**
```typescript
// 保存 token
localStorage.setItem('access_token', response.access_token);

// 后续请求添加 header
headers: {
  'Authorization': `Bearer ${token}`
}
```

---

## 对话管理

### 获取对话列表

```http
GET /api/chat/conversations
Authorization: Bearer <token>
```

**响应:**
```json
{
  "wallet_address": "0x1234...",
  "total": 3,
  "conversations": [
    {
      "id": "conv-uuid-1",
      "title": "Exploring RWA",
      "wallet_address": "0x1234...",
      "message_count": 4,
      "last_message_preview": "RWA stands for Real-World...",
      "has_minted_messages": true,
      "minted_count": 2,
      "unminted_count": 2,
      "can_mint": true,
      "created_at": "2025-11-28T10:00:00",
      "updated_at": "2025-11-28T12:30:00"
    }
  ]
}
```

**前端使用:**
```typescript
interface ConversationListItem {
  id: string;
  title: string;
  message_count: number;
  last_message_preview: string | null;
  has_minted_messages: boolean;
  minted_count: number;      // 已铸造消息数
  unminted_count: number;    // 未铸造消息数
  can_mint: boolean;         // 是否还能铸造
  created_at: string;
  updated_at: string;
}
```

### 创建新对话

```http
POST /api/chat/conversations
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "title": "New Conversation"  // 可选，默认 "New Conversation"
}
```

**响应:**
```json
{
  "id": "conv-uuid-new",
  "title": "New Conversation",
  "wallet_address": "0x1234...",
  "created_at": "2025-11-28T12:00:00"
}
```

### 获取对话详情

```http
GET /api/chat/conversations/{conversation_id}
Authorization: Bearer <token>
```

**响应:**
```json
{
  "id": "conv-uuid-1",
  "title": "Exploring RWA",
  "wallet_address": "0x1234...",
  "messages": [
    {
      "id": "msg-uuid-1",
      "role": "user",
      "content": "What is RWA?",
      "timestamp": "2025-11-28T10:00:00",
      "is_minted": true
    },
    {
      "id": "msg-uuid-2",
      "role": "assistant",
      "content": "RWA stands for Real-World Asset...",
      "timestamp": "2025-11-28T10:00:05",
      "is_minted": true
    },
    {
      "id": "msg-uuid-3",
      "role": "user",
      "content": "Can you explain more?",
      "timestamp": "2025-11-28T10:01:00",
      "is_minted": false
    }
  ],
  "created_at": "2025-11-28T10:00:00",
  "updated_at": "2025-11-28T10:01:00",
  "ipfs_hash": "QmXxx...",
  "minted_count": 2,
  "unminted_count": 2,
  "can_mint": true
}
```

**前端类型定义:**
```typescript
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  is_minted: boolean;  // 是否已铸造为 NFT
}

interface Conversation {
  id: string;
  title: string;
  wallet_address: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
  ipfs_hash: string | null;
  minted_count: number;
  unminted_count: number;
  can_mint: boolean;
}
```

---

## 聊天功能

### 发送消息

```http
POST /api/chat
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is blockchain?"
    }
  ],
  "conversation_id": "conv-uuid-1",  // 可选，不传则创建新对话
  "model": "gpt-4",                   // 可选，默认 gpt-4
  "temperature": 0.7,                 // 可选，0-1
  "max_tokens": 2000                  // 可选，64-4096
}
```

**响应:**
```json
{
  "reply": "Blockchain is a distributed ledger technology...",
  "model_used": "gpt-4",
  "tokens_used": 150,
  "provider": "openai",
  "latency_ms": 1200,
  "conversation_id": "conv-uuid-1",
  "message_id": "msg-uuid-new",
  "wallet_address": "0x1234...",
  "ipfs_hash": "QmXxx...",
  "stored_at": "2025-11-28T12:00:00"
}
```

**前端使用示例:**
```typescript
// 在现有对话中发送消息
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    messages: [{ role: 'user', content: userInput }],
    conversation_id: currentConversationId
  })
});

const { reply, conversation_id, message_id } = await response.json();

// 如果是新对话，保存 conversation_id
if (!currentConversationId) {
  setCurrentConversationId(conversation_id);
}
```

### 获取历史消息（扁平化）

```http
GET /api/chat/history
Authorization: Bearer <token>
```

**响应:**
```json
{
  "wallet_address": "0x1234...",
  "total_messages": 10,
  "history": [
    {
      "conversation_id": "conv-1",
      "conversation_title": "RWA Discussion",
      "message_id": "msg-1",
      "role": "user",
      "content": "What is RWA?",
      "timestamp": "2025-11-28T10:00:00",
      "is_minted": true
    }
  ]
}
```

---

## NFT 铸造

### 铸造对话为 NFT

```http
POST /api/mints
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "conversation_id": "conv-uuid-1",
  "message_ids": ["msg-1", "msg-2"],  // 可选，不传则铸造所有未铸造的消息
  "conversationTitle": "My NFT Title",
  "description": "A valuable conversation about blockchain"
}
```

**响应:**
```json
{
  "mint_id": "mint-uuid-1",
  "conversation_id": "conv-uuid-1",
  "message_ids": ["msg-1", "msg-2"],
  "metadataUrl": "ipfs://QmXxx...",
  "ipfs_hash": "QmXxx...",
  "gatewayUrl": "https://gateway.pinata.cloud/ipfs/QmXxx...",
  "token_id": 1,
  "tx_hash": "0xabc...",
  "listing_id": null,
  "message": "NFT minted successfully"
}
```

**重要说明:**
- ⚠️ **已铸造的消息不能重复铸造**
- 如果不传 `message_ids`，自动选择所有 `is_minted=false` 的消息
- 如果所有消息都已铸造，返回错误

**错误响应（所有消息已铸造）:**
```json
{
  "detail": "No unminted messages to mint. All selected messages have already been minted.",
  "already_minted_count": 4
}
```

### 获取铸造记录列表

```http
GET /api/chat/minted
Authorization: Bearer <token>
```

**响应:**
```json
{
  "wallet_address": "0x1234...",
  "total": 2,
  "minted_records": [
    {
      "id": "mint-uuid-1",
      "conversation_id": "conv-uuid-1",
      "message_ids": ["msg-1", "msg-2"],
      "ipfs_hash": "QmXxx...",
      "metadata_url": "ipfs://QmXxx...",
      "gateway_url": "https://gateway.pinata.cloud/ipfs/QmXxx...",
      "tx_hash": "0xabc...",
      "token_id": 1,
      "listing_id": null,
      "price": 0,
      "is_listed": false,
      "owner_address": "0x1234...",
      "minted_at": "2025-11-28T12:00:00"
    }
  ]
}
```

### 获取铸造记录详情

```http
GET /api/mints/{mint_id}
Authorization: Bearer <token>
```

**响应:** 同上单条记录

---

## 市场功能

### 上架 NFT

```http
POST /api/mints/{mint_id}/list
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "price": 100  // 价格必须大于 0
}
```

**响应:**
```json
{
  "message": "Listed on market successfully",
  "mint_id": "mint-uuid-1",
  "listing_id": 1,
  "price": 100,
  "tx_hash": "0xabc..."
}
```

### 下架 NFT

```http
POST /api/mints/{mint_id}/unlist
Authorization: Bearer <token>
```

**响应:**
```json
{
  "message": "Unlisted from market successfully",
  "mint_id": "mint-uuid-1",
  "tx_hash": "0xabc..."
}
```

---

## 数据结构

### 前端 TypeScript 类型定义

```typescript
// ==================== 认证相关 ====================

interface NonceResponse {
  nonce: string;
  message: string;
  wallet: string;
}

interface AuthRequest {
  address: string;
  message: string;
  signature: string;
}

interface AuthResponse {
  access_token: string;
}

// ==================== 消息相关 ====================

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  is_minted: boolean;
}

interface ChatRequest {
  messages: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;
  conversation_id?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

interface ChatResponse {
  reply: string;
  model_used: string;
  tokens_used: number;
  provider: string;
  latency_ms: number;
  conversation_id: string;
  message_id: string;
  wallet_address: string;
  ipfs_hash: string;
  stored_at: string;
}

// ==================== 对话相关 ====================

interface Conversation {
  id: string;
  title: string;
  wallet_address: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
  ipfs_hash: string | null;
  minted_count: number;
  unminted_count: number;
  can_mint: boolean;
}

interface ConversationListItem {
  id: string;
  title: string;
  wallet_address: string;
  message_count: number;
  last_message_preview: string | null;
  has_minted_messages: boolean;
  minted_count: number;
  unminted_count: number;
  can_mint: boolean;
  created_at: string;
  updated_at: string;
}

// ==================== 铸造相关 ====================

interface MintRequest {
  conversation_id: string;
  message_ids?: string[];
  conversationTitle?: string;
  description?: string;
}

interface MintResponse {
  mint_id: string;
  conversation_id: string;
  message_ids: string[];
  metadataUrl: string;
  ipfs_hash: string;
  gatewayUrl: string;
  token_id: number | null;
  tx_hash: string | null;
  listing_id: number | null;
  message: string;
}

interface MintRecord {
  id: string;
  conversation_id: string;
  message_ids: string[];
  wallet_address: string;
  ipfs_hash: string;
  metadata_url: string;
  gateway_url: string;
  tx_hash: string | null;
  token_id: number | null;
  listing_id: number | null;
  price: number;
  is_listed: boolean;
  owner_address: string;
  minted_at: string;
}

// ==================== 市场相关 ====================

interface ListRequest {
  price: number;
}

interface ListResponse {
  message: string;
  mint_id: string;
  listing_id: number;
  price: number;
  tx_hash: string;
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码

| HTTP 状态码 | 说明 | 示例 |
|------------|------|------|
| `400` | 请求参数错误 | 缺少必填字段、格式错误 |
| `401` | 认证失败 | Token 无效/过期、签名错误 |
| `404` | 资源不存在 | 对话/铸造记录不存在 |
| `422` | 验证错误 | 消息为空、标题过长 |
| `500` | 服务器错误 | 内部错误 |

### 错误处理示例

```typescript
async function apiRequest(url: string, options: RequestInit) {
  const response = await fetch(url, options);
  
  if (!response.ok) {
    const error = await response.json();
    
    switch (response.status) {
      case 401:
        // Token 过期，重新登录
        logout();
        throw new Error('请重新登录');
      case 404:
        throw new Error(error.detail || '资源不存在');
      case 422:
        throw new Error(error.detail || '输入验证失败');
      default:
        throw new Error(error.detail || '请求失败');
    }
  }
  
  return response.json();
}
```

---

## API 端点汇总

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/auth/nonce/{address}` | GET | 获取认证 Nonce | ❌ |
| `/api/auth/verify` | POST | 验证签名 | ❌ |
| `/api/chat` | POST | 发送消息 | ✅ |
| `/api/chat/conversations` | GET | 获取对话列表 | ✅ |
| `/api/chat/conversations` | POST | 创建对话 | ✅ |
| `/api/chat/conversations/{id}` | GET | 获取对话详情 | ✅ |
| `/api/chat/history` | GET | 获取历史消息 | ✅ |
| `/api/chat/minted` | GET | 获取铸造记录 | ✅ |
| `/api/chat/status` | GET | 存储服务状态 | ✅ |
| `/api/chat/unpin/{hash}` | DELETE | 取消 IPFS 固定 | ✅ |
| `/api/mints` | POST | 铸造 NFT | ✅ |
| `/api/mints/{id}` | GET | 获取铸造详情 | ✅ |
| `/api/mints/{id}/list` | POST | 上架到市场 | ✅ |
| `/api/mints/{id}/unlist` | POST | 从市场下架 | ✅ |

---

## 前端集成示例

### API 服务封装

```typescript
// api/index.ts
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:5000';

class ApiService {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: { ...headers, ...options.headers },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  // 认证
  async getNonce(address: string) {
    return this.request<NonceResponse>(`/api/auth/nonce/${address}`);
  }

  async verify(address: string, message: string, signature: string) {
    return this.request<AuthResponse>('/api/auth/verify', {
      method: 'POST',
      body: JSON.stringify({ address, message, signature }),
    });
  }

  // 对话
  async getConversations() {
    return this.request<{ conversations: ConversationListItem[] }>('/api/chat/conversations');
  }

  async getConversation(id: string) {
    return this.request<Conversation>(`/api/chat/conversations/${id}`);
  }

  async createConversation(title?: string) {
    return this.request('/api/chat/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  }

  // 聊天
  async sendMessage(content: string, conversationId?: string) {
    return this.request<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        messages: [{ role: 'user', content }],
        conversation_id: conversationId,
      }),
    });
  }

  // 铸造
  async mintConversation(conversationId: string, title?: string, messageIds?: string[]) {
    return this.request<MintResponse>('/api/mints', {
      method: 'POST',
      body: JSON.stringify({
        conversation_id: conversationId,
        message_ids: messageIds,
        conversationTitle: title,
      }),
    });
  }

  async getMintedRecords() {
    return this.request<{ minted_records: MintRecord[] }>('/api/chat/minted');
  }

  // 市场
  async listOnMarket(mintId: string, price: number) {
    return this.request<ListResponse>(`/api/mints/${mintId}/list`, {
      method: 'POST',
      body: JSON.stringify({ price }),
    });
  }

  async unlistFromMarket(mintId: string) {
    return this.request(`/api/mints/${mintId}/unlist`, {
      method: 'POST',
    });
  }
}

export const api = new ApiService();
```

### 使用示例

```typescript
// 登录流程
async function login(address: string, signMessage: (msg: string) => Promise<string>) {
  // 1. 获取 nonce
  const { message } = await api.getNonce(address);
  
  // 2. 钱包签名
  const signature = await signMessage(message);
  
  // 3. 验证并获取 token
  const { access_token } = await api.verify(address, message, signature);
  api.setToken(access_token);
}

// 发送消息
async function sendMessage(content: string, conversationId?: string) {
  const response = await api.sendMessage(content, conversationId);
  return {
    reply: response.reply,
    conversationId: response.conversation_id,
    messageId: response.message_id,
  };
}

// 铸造对话
async function mintConversation(conversationId: string) {
  const conversation = await api.getConversation(conversationId);
  
  if (!conversation.can_mint) {
    throw new Error('没有可铸造的消息');
  }
  
  return api.mintConversation(conversationId, conversation.title);
}
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v3.0 | 2025-11-28 | 新增对话管理、铸造防重复、市场功能 |
| v2.0 | 2025-11-26 | 新增 IPFS 存储、索引管理 |
| v1.0 | 2025-11-25 | 初始版本 |


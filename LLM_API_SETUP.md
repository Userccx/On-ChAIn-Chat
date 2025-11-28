# LLM API 配置指南

## 📋 概述

已更新 LLM 服务以支持自定义 OpenAI API 端点（`https://chatapi.onechats.top/v1/`）。

## 🔧 配置步骤

### 1. 安装依赖

```bash
pip install openai>=1.0.0
```

或者重新安装所有依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```env
# LLM Configuration
OPENAI_API_KEY=sk-xxx  # 你的 API Key
OPENAI_BASE_URL=https://chatapi.onechats.top/v1/  # 自定义 API 端点（可选，已有默认值）
DEFAULT_LLM_MODEL=gpt-4  # 使用的模型

# 启用真实 LLM（关闭 Mock 模式）
USE_MOCK_SERVICES=False
```

### 3. 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API Key | `None` |
| `OPENAI_BASE_URL` | API 端点地址 | `https://chatapi.onechats.top/v1/` |
| `DEFAULT_LLM_MODEL` | 默认使用的模型 | `gpt-4` |
| `USE_MOCK_SERVICES` | 是否使用 Mock 模式 | `False` |

## 🎯 工作模式

### Mock 模式

当以下任一条件满足时，会使用 Mock 模式：
- `USE_MOCK_SERVICES=True`
- `OPENAI_API_KEY` 未配置
- OpenAI 包未安装

Mock 模式会返回固定的回复（`MOCK_LLM_REPLY`，默认为 "Hello world"）。

### 真实 API 模式

当配置了 `OPENAI_API_KEY` 且 `USE_MOCK_SERVICES=False` 时，会调用真实的 OpenAI API。

## 📝 代码示例

更新后的 LLM 服务会自动：

1. **初始化 OpenAI 客户端**：
   ```python
   client = OpenAI(
       api_key=settings.OPENAI_API_KEY,
       base_url=settings.OPENAI_BASE_URL,
   )
   ```

2. **调用 API**：
   ```python
   response = client.chat.completions.create(
       model="gpt-4",
       messages=[
           {"role": "system", "content": "You are a helpful assistant."},
           {"role": "user", "content": "..."}
       ]
   )
   ```

3. **返回格式化的响应**：
   ```python
   {
       "reply": "AI 回复内容",
       "model_used": "gpt-4",
       "tokens_used": 150,
       "provider": "openai",
       "latency_ms": 1200
   }
   ```

## 🔍 日志查看

所有 LLM 调用都会记录到日志文件中：

```bash
# 查看日志
tail -f logs/app_$(date +%Y%m%d).log | grep -i "llm\|openai"
```

日志会显示：
- ✅ API 初始化成功
- ✅ API 调用成功（包含 tokens 和延迟）
- ❌ API 调用失败（会自动回退到 Mock 模式）

## 🐛 故障排查

### 问题 1: 仍然使用 Mock 模式

**检查**：
1. `.env` 文件中是否设置了 `OPENAI_API_KEY`
2. `USE_MOCK_SERVICES` 是否为 `False`
3. 是否安装了 `openai` 包

**解决**：
```bash
# 检查配置
grep OPENAI .env

# 安装依赖
pip install openai>=1.0.0
```

### 问题 2: API 调用失败

**检查日志**：
```bash
tail -f logs/app_*.log | grep -i error
```

**常见原因**：
- API Key 无效
- API 端点不可访问
- 网络连接问题

**解决**：
- 验证 API Key 是否正确
- 检查网络连接
- 确认 API 端点地址正确

### 问题 3: 模型不存在

如果指定的模型不可用，API 会返回错误。检查：
- 模型名称是否正确（如 `gpt-4`）
- API 端点是否支持该模型

## ✅ 测试

启动后端后，发送聊天请求：

```bash
# 启动后端
python -m flask --app backend.main:app run --reload

# 在另一个终端测试（需要先获取 JWT token）
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  }'
```

## 📚 相关文件

- `backend/services/llm_service.py` - LLM 服务实现
- `backend/config.py` - 配置管理
- `backend/routes/chat_routes.py` - 聊天路由


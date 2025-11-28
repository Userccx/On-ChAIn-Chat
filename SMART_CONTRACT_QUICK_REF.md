# 智能合约配置快速参考

## 🎯 从 Remix 获取的信息

部署合约后，从 Remix 控制台复制以下信息：

```
✅ 合约地址: 0x1234567890abcdef1234567890abcdef12345678
✅ 交易哈希: 0xabcdef...
✅ 网络: Sepolia / Mumbai / Mainnet
```

## 📋 配置步骤

### 1. 更新 ABI

**文件**: `backend/services/blockchain_service.py`

**位置**: 第 10-21 行

**操作**: 
1. 在 Remix 中点击 "Solidity Compiler" → "ABI" 按钮
2. 复制完整 ABI JSON
3. 替换 `ETH_MARKETPLACE_ABI = [...]` 中的内容

### 2. 配置 .env 文件

在项目根目录的 `.env` 文件中添加：

```env
# ============================================
# 智能合约配置
# ============================================

# 从 Remix 部署输出复制
CONTRACT_ADDRESS=0x你的合约地址

# 从 Alchemy/Infura 获取
WEB3_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY

# 根据网络选择
CHAIN_ID=11155111  # Sepolia: 11155111, Mumbai: 80001, Mainnet: 1
BLOCKCHAIN_NETWORK=sepolia

# 后端账户私钥（用于发送交易）
PRIVATE_KEY=0x你的后端账户私钥（64个十六进制字符）

# 禁用 Mock 模式
USE_MOCK_SERVICES=False
```

## 🔑 获取 RPC 端点

### Alchemy（推荐）

1. 访问 https://www.alchemy.com/
2. 创建应用 → 选择网络
3. 复制 HTTP URL

**格式**: `https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY`

### Infura

1. 访问 https://www.infura.io/
2. 创建项目 → 选择网络
3. 复制 Endpoint URL

**格式**: `https://sepolia.infura.io/v3/YOUR_PROJECT_ID`

## 🌐 常见网络配置

| 网络 | Chain ID | RPC URL 示例 |
|------|----------|--------------|
| **Sepolia** (推荐测试) | 11155111 | `https://eth-sepolia.g.alchemy.com/v2/...` |
| **Mumbai** (Polygon) | 80001 | `https://polygon-mumbai.g.alchemy.com/v2/...` |
| **Mainnet** | 1 | `https://eth-mainnet.g.alchemy.com/v2/...` |
| **本地** (Hardhat) | 1337 | `http://127.0.0.1:8545` |

## ✅ 验证配置

启动后端后，应该看到：

```
✅ 成功连接到 sepolia
   最新区块: 12345678
```

## ⚠️ 重要提示

1. **合约地址**: 42 个字符，以 `0x` 开头
2. **私钥**: 0x + 64 个十六进制字符（不要包含空格）
3. **ABI**: 必须是完整的 JSON 数组
4. **安全**: 不要将 `.env` 文件提交到 Git

## 🔧 如果合约函数不同

如果你的合约函数名不是 `listData`，需要修改：

**文件**: `backend/services/blockchain_service.py` 第 88 行

**示例**（如果你的函数是 `mintNFT`）:
```python
tx = self.contract.functions.mintNFT(
    user_address,
    metadata_url
).build_transaction({...})
```

## 📚 详细文档

查看 `SMART_CONTRACT_SETUP.md` 获取完整配置指南。


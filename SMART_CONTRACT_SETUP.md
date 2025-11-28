# 智能合约配置指南（基于 Remix 部署）

## 📋 概述

本指南将帮助你将从 Remix IDE 部署的智能合约配置到后端系统中。

---

## 🔍 第一步：在 Remix 中部署合约

### 1.1 部署步骤

1. **打开 Remix IDE**
   - 访问：https://remix.ethereum.org/
   - 创建或打开你的智能合约文件（`.sol`）

2. **编译合约**
   - 在 "Solidity Compiler" 标签页
   - 选择编译器版本（通常与合约兼容）
   - 点击 "Compile [合约名].sol"

3. **部署合约**
   - 切换到 "Deploy & Run Transactions" 标签页
   - 选择环境：
     - **Injected Provider** (MetaMask) - 用于真实网络
     - **Remix VM** - 用于本地测试
   - 选择要部署的合约
   - 点击 "Deploy"

4. **记录部署信息**
   - 部署成功后，在控制台会显示部署信息
   - **重要**：记录以下信息（见下方）

---

## 📝 第二步：从 Remix 获取必要信息

### 2.1 Remix 部署后的输出信息

部署成功后，Remix 会显示类似以下的信息：

```
[block:12345678] Transaction hash: 0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
[block:12345678] Contract deployed at: 0x1234567890abcdef1234567890abcdef12345678
[block:12345678] Gas used: 234567
```

**你需要记录的信息：**

| 信息 | 说明 | 示例 |
|------|------|------|
| **合约地址** | 部署后的合约地址 | `0x1234567890abcdef1234567890abcdef12345678` |
| **交易哈希** | 部署交易的哈希 | `0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890` |
| **网络** | 部署到的网络 | `Sepolia`, `Mumbai`, `Mainnet` 等 |
| **Chain ID** | 链 ID | `11155111` (Sepolia), `80001` (Mumbai), `1` (Mainnet) |

### 2.2 获取合约 ABI

**方法 1：从 Remix 复制（推荐）**

1. 在 Remix 中，点击 "Solidity Compiler" 标签页
2. 找到 "Compilation Details" 或 "ABI" 按钮
3. 点击 "ABI" 按钮
4. 复制完整的 ABI JSON（这是一个数组）

**方法 2：从编译输出获取**

1. 在 "Solidity Compiler" 标签页
2. 展开 "Compilation Details"
3. 找到 `contracts/[合约名].sol/[合约名].json`
4. 复制其中的 `abi` 字段

**ABI 示例格式：**
```json
[
  {
    "inputs": [
      {"internalType": "string", "name": "_dataHash", "type": "string"},
      {"internalType": "uint256", "name": "_price", "type": "uint256"}
    ],
    "name": "listData",
    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "anonymous": false,
    "inputs": [
      {"indexed": true, "internalType": "uint256", "name": "listingId", "type": "uint256"},
      {"indexed": false, "internalType": "string", "name": "dataHash", "type": "string"}
    ],
    "name": "DataListed",
    "type": "event"
  }
]
```

---

## ⚙️ 第三步：配置后端

### 3.1 更新 ABI 文件

1. **打开文件**：`backend/services/blockchain_service.py`

2. **找到 ABI 定义**（大约在第 10-21 行）：
   ```python
   ETH_MARKETPLACE_ABI = [
       {
           "inputs": [...],
           "name": "listData",
           ...
       },
       # ... 其他函数定义
   ]
   ```

3. **替换为你的完整 ABI**：
   - 将从 Remix 复制的完整 ABI JSON 粘贴到这里
   - 确保格式正确（Python 列表格式）

**示例：**
```python
ETH_MARKETPLACE_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "_dataHash", "type": "string"},
            {"internalType": "uint256", "name": "_price", "type": "uint256"}
        ],
        "name": "listData",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # ... 添加你的合约的所有函数和事件
]
```

### 3.2 配置 .env 文件

在项目根目录的 `.env` 文件中添加以下配置：

```env
# ============================================
# 智能合约配置（从 Remix 部署信息获取）
# ============================================

# 合约地址（从 Remix 部署输出中复制）
CONTRACT_ADDRESS=0x1234567890abcdef1234567890abcdef12345678

# RPC 端点（根据你部署的网络选择）
# 主网 (Ethereum Mainnet)
WEB3_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
CHAIN_ID=1

# Sepolia 测试网
# WEB3_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY
# CHAIN_ID=11155111

# Polygon Mumbai 测试网
# WEB3_RPC_URL=https://polygon-mumbai.g.alchemy.com/v2/YOUR_API_KEY
# CHAIN_ID=80001

# 后端账户私钥（用于发送交易）
# ⚠️ 重要：这是后端服务的私钥，不是用户钱包私钥
# 格式：0x + 64 个十六进制字符
PRIVATE_KEY=0x你的后端账户私钥（64个十六进制字符，不含0x前缀）

# 网络名称（用于显示）
BLOCKCHAIN_NETWORK=sepolia

# 如果使用 ERC20 代币支付，配置代币合约地址
PAYMENT_TOKEN_ADDRESS=0x...  # 可选，如果使用 ERC20 版本

# 禁用 Mock 模式（使用真实智能合约）
USE_MOCK_SERVICES=False
```

---

## 🔑 第四步：获取 RPC 端点

### 4.1 使用 Alchemy（推荐）

1. **注册/登录 Alchemy**
   - 访问：https://www.alchemy.com/
   - 创建账户或登录

2. **创建应用**
   - 点击 "Create App"
   - 填写应用名称
   - 选择网络（Mainnet, Sepolia, Mumbai 等）
   - 点击 "Create"

3. **获取 API Key**
   - 在应用详情页，找到 "HTTP" 或 "API Key"
   - 复制完整的 RPC URL
   - 格式：`https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY`

### 4.2 使用 Infura

1. **注册/登录 Infura**
   - 访问：https://www.infura.io/
   - 创建账户或登录

2. **创建项目**
   - 点击 "Create New Key"
   - 选择网络
   - 复制 Endpoint URL
   - 格式：`https://sepolia.infura.io/v3/YOUR_PROJECT_ID`

### 4.3 使用公共 RPC（不推荐，仅用于测试）

```env
# Sepolia 测试网（公共，可能不稳定）
WEB3_RPC_URL=https://rpc.sepolia.org
CHAIN_ID=11155111

# Polygon Mumbai（公共，可能不稳定）
WEB3_RPC_URL=https://rpc-mumbai.maticvigil.com
CHAIN_ID=80001
```

---

## 🔐 第五步：配置后端账户私钥

### 5.1 创建后端账户

**重要**：后端需要一个独立的账户来发送交易，这个账户的私钥需要配置在 `.env` 文件中。

**方法 1：使用 MetaMask 创建新账户**

1. 打开 MetaMask
2. 创建新账户（仅用于后端）
3. 导出私钥：
   - 点击账户名称 → "Account details"
   - 点击 "Export Private Key"
   - 输入密码
   - 复制私钥

**方法 2：使用 Python 生成（仅用于测试）**

```python
from eth_account import Account
account = Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
```

### 5.2 配置私钥

在 `.env` 文件中：

```env
# 格式：0x + 64 个十六进制字符
PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

**⚠️ 安全提示：**
- 不要将 `.env` 文件提交到 Git
- 确保 `.env` 在 `.gitignore` 中
- 生产环境使用环境变量或密钥管理服务

---

## 📊 第六步：常见网络配置

### 6.1 Ethereum Mainnet（主网）

```env
BLOCKCHAIN_NETWORK=ethereum-mainnet
WEB3_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
CHAIN_ID=1
```

### 6.2 Sepolia Testnet（推荐测试）

```env
BLOCKCHAIN_NETWORK=sepolia
WEB3_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY
CHAIN_ID=11155111
```

### 6.3 Polygon Mumbai Testnet

```env
BLOCKCHAIN_NETWORK=polygon-mumbai
WEB3_RPC_URL=https://polygon-mumbai.g.alchemy.com/v2/YOUR_API_KEY
CHAIN_ID=80001
```

### 6.4 本地 Hardhat/Ganache

```env
BLOCKCHAIN_NETWORK=local
WEB3_RPC_URL=http://127.0.0.1:8545
CHAIN_ID=1337  # 或你的本地链 ID
```

---

## ✅ 第七步：验证配置

### 7.1 检查清单

- [ ] 合约地址已配置（42 个字符，以 0x 开头）
- [ ] RPC URL 已配置（包含 API Key）
- [ ] Chain ID 已配置（与网络匹配）
- [ ] 后端私钥已配置（0x + 64 个十六进制字符）
- [ ] ABI 已更新到 `blockchain_service.py`
- [ ] `USE_MOCK_SERVICES=False`（如果使用真实合约）

### 7.2 测试连接

启动后端服务，应该看到：

```
✅ 成功连接到 sepolia
   最新区块: 12345678
```

如果看到错误，检查：
- RPC URL 是否正确
- API Key 是否有效
- 网络是否可访问

---

## 🔧 第八步：更新合约函数调用

### 8.1 检查合约函数

根据你的智能合约，可能需要更新 `blockchain_service.py` 中的函数调用。

**当前实现调用 `listData` 函数：**

```python
tx = self.contract.functions.listData(metadata_url, price_wei).build_transaction({
    'from': self.account.address,
    'nonce': nonce,
    'gas': 200000,  # 根据实际情况调整
    'gasPrice': self.w3.eth.gas_price,
    'chainId': settings.CHAIN_ID,
})
```

**如果你的合约函数不同，需要修改：**

例如，如果你的合约有 `mintNFT` 函数：
```python
tx = self.contract.functions.mintNFT(
    user_address,  # 接收者地址
    metadata_url   # IPFS 元数据 URL
).build_transaction({
    'from': self.account.address,
    'nonce': nonce,
    'gas': 200000,
    'gasPrice': self.w3.eth.gas_price,
    'chainId': settings.CHAIN_ID,
})
```

### 8.2 更新事件解析

如果你的合约有不同的事件，需要更新事件解析：

```python
# 当前实现解析 DataListed 事件
event = self.contract.events.DataListed().process_receipt(receipt)

# 如果你的合约有 NFTMinted 事件
event = self.contract.events.NFTMinted().process_receipt(receipt)
if event:
    token_id = event[0]['args']['tokenId']
```

---

## 📝 完整配置示例

### .env 文件完整示例

```env
# ============================================
# 应用配置
# ============================================
APP_NAME=Tokenized LLM Interaction Platform
DEBUG=True
ENVIRONMENT=development

# ============================================
# 智能合约配置（从 Remix 获取）
# ============================================
USE_MOCK_SERVICES=False

# 合约地址（从 Remix 部署输出复制）
CONTRACT_ADDRESS=0x1234567890abcdef1234567890abcdef12345678

# RPC 端点（从 Alchemy/Infura 获取）
WEB3_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY_HERE

# Chain ID（根据网络选择）
CHAIN_ID=11155111  # Sepolia

# 网络名称
BLOCKCHAIN_NETWORK=sepolia

# 后端账户私钥（用于发送交易）
PRIVATE_KEY=0x你的后端账户私钥（64个十六进制字符）

# 可选：ERC20 代币地址（如果使用）
PAYMENT_TOKEN_ADDRESS=

# ============================================
# IPFS 配置
# ============================================
IPFS_PINNING_SERVICE=pinata
PINATA_JWT=你的_Pinata_JWT_Token

# ============================================
# 安全配置
# ============================================
JWT_SECRET=your-secret-key-change-in-production
```

---

## ❓ 常见问题

### Q1: 如何知道我的合约部署在哪个网络？

**A**: 在 Remix 的 "Deploy & Run Transactions" 标签页，查看 "Environment" 下拉菜单。或者在 MetaMask 中查看当前连接的网络。

### Q2: 如何获取完整的 ABI？

**A**: 
1. 在 Remix 中，点击 "Solidity Compiler" 标签页
2. 找到 "ABI" 按钮并点击
3. 复制完整的 JSON 数组

### Q3: 后端私钥和用户钱包私钥有什么区别？

**A**:
- **后端私钥**：后端服务用于发送交易的账户私钥，配置在 `.env` 文件中
- **用户钱包私钥**：用户的钱包私钥，**永远不要**配置在后端

### Q4: 如何测试配置是否正确？

**A**:
1. 启动后端服务
2. 查看启动日志，应该看到 "✅ 成功连接到 [网络]"
3. 尝试发送一条消息并铸造 NFT
4. 检查交易是否成功

### Q5: Gas 费用如何计算？

**A**: 
- 代码中会自动获取当前网络的 gas price
- 你可以设置 `gas` 限制（当前代码中设置为 200000，可根据实际情况调整）
- 实际费用 = gas_used × gas_price

### Q6: 如何在不同网络之间切换？

**A**: 修改 `.env` 文件中的：
- `WEB3_RPC_URL`（对应网络的 RPC 端点）
- `CHAIN_ID`（对应网络的 Chain ID）
- `BLOCKCHAIN_NETWORK`（网络名称）

---

## 🚨 故障排除

### 错误 1: "无法连接到区块链节点"

**原因**：
- RPC URL 不正确
- API Key 无效
- 网络不可访问

**解决**：
1. 检查 RPC URL 格式
2. 验证 API Key 是否有效
3. 尝试在浏览器中访问 RPC URL（应该返回 JSON）

### 错误 2: "CONTRACT_ADDRESS 必须配置"

**原因**：`.env` 文件中没有设置 `CONTRACT_ADDRESS`

**解决**：添加 `CONTRACT_ADDRESS=你的合约地址`

### 错误 3: "需要配置 PRIVATE_KEY 以发送交易"

**原因**：`.env` 文件中没有设置 `PRIVATE_KEY`

**解决**：添加 `PRIVATE_KEY=0x你的私钥`

### 错误 4: "ENS name: 'xxx' is invalid"

**原因**：地址格式不正确（长度不对或包含无效字符）

**解决**：
1. 确保地址是 42 个字符（0x + 40 个十六进制字符）
2. 检查地址是否包含空格或特殊字符

### 错误 5: 交易失败（revert）

**原因**：
- Gas 不足
- 合约函数参数错误
- 合约状态不允许该操作

**解决**：
1. 增加 gas 限制
2. 检查合约函数签名和参数
3. 查看合约代码确认调用条件

---

## 📚 相关资源

- [Remix IDE 文档](https://remix-ide.readthedocs.io/)
- [Web3.py 文档](https://web3py.readthedocs.io/)
- [Alchemy 文档](https://docs.alchemy.com/)
- [Ethereum Chain IDs](https://chainlist.org/)

---

## ✅ 配置完成检查清单

完成以下所有步骤后，你的智能合约应该可以正常工作了：

- [ ] 在 Remix 中成功部署合约
- [ ] 记录了合约地址
- [ ] 复制了完整的 ABI
- [ ] 更新了 `blockchain_service.py` 中的 ABI
- [ ] 配置了 RPC 端点（Alchemy/Infura）
- [ ] 配置了 Chain ID
- [ ] 配置了后端私钥
- [ ] 设置了 `USE_MOCK_SERVICES=False`
- [ ] 后端服务启动成功，显示 "✅ 成功连接到 [网络]"
- [ ] 测试 NFT 铸造功能

---

**配置完成后，重启后端服务，你的智能合约就可以正常工作了！** 🎉


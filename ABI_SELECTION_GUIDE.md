# ABI 选择指南

## 📋 你的合约结构

根据你的 Solidity 文件，你有以下合约：

1. **`ETHUserDataMarketplace`** (`test_ETH.sol`)
   - 使用 **ETH** 支付
   - 有 `listData` 函数 ✅
   - 适合：直接使用 ETH 进行交易

2. **`UserDataMarketplace`** (`test.sol`)
   - 使用 **ERC20 代币** 支付
   - 有 `listData` 函数 ✅
   - 需要：先部署 `DataToken` 合约，然后传入代币地址

3. **`DataToken`** (`DataToken.sol`)
   - ERC20 代币合约
   - 用于支付（如果使用 `UserDataMarketplace`）

## ❌ 你提供的 ABI 文件

### `DataToken_ABI.json`
- **用途**：这是 `DataToken` 代币合约的 ABI
- **问题**：❌ **不包含 `listData` 函数**
- **使用场景**：仅当你需要与代币合约交互时使用（如 mint、transfer）

### `test_ABI.json`
- **用途**：不完整的 ERC20 ABI
- **问题**：❌ **不包含 `listData` 函数**
- **使用场景**：不适用

## ✅ 正确的做法

### 你需要的是 Marketplace 合约的 ABI

根据你部署的合约，你需要：

#### 选项 1：如果部署了 `ETHUserDataMarketplace`（推荐，更简单）

**从 Remix 获取 ABI：**
1. 在 Remix 中打开 `test_ETH.sol`
2. 编译合约
3. 点击 "Solidity Compiler" → "ABI" 按钮
4. 复制完整的 ABI

**这个 ABI 应该包含：**
- ✅ `listData` 函数
- ✅ `purchaseAccess` 函数
- ✅ `removeListing` 函数
- ✅ `DataListed` 事件
- ✅ 其他 view 函数

#### 选项 2：如果部署了 `UserDataMarketplace`（需要代币）

**从 Remix 获取 ABI：**
1. 在 Remix 中打开 `test.sol`
2. 编译合约
3. 点击 "Solidity Compiler" → "ABI" 按钮
4. 复制完整的 ABI

**还需要配置：**
- `PAYMENT_TOKEN_ADDRESS`：`DataToken` 合约地址

## 🔧 如何获取正确的 ABI

### 方法 1：从 Remix 获取（推荐）

1. **打开 Remix IDE**
   - 访问：https://remix.ethereum.org/

2. **打开你的合约文件**
   - 如果是 ETH 版本：打开 `test_ETH.sol`
   - 如果是 ERC20 版本：打开 `test.sol`

3. **编译合约**
   - 切换到 "Solidity Compiler" 标签页
   - 选择编译器版本
   - 点击 "Compile [合约名].sol"

4. **获取 ABI**
   - 在编译成功后，找到 "ABI" 按钮
   - 点击 "ABI" 按钮
   - 复制完整的 JSON 数组

5. **更新代码**
   - 打开 `backend/services/blockchain_service.py`
   - 找到 `ETH_MARKETPLACE_ABI = [...]`（第 11-21 行）
   - 替换为从 Remix 复制的完整 ABI

### 方法 2：从编译输出获取

1. 在 Remix 的 "Solidity Compiler" 标签页
2. 展开 "Compilation Details"
3. 找到 `contracts/test_ETH.sol/ETHUserDataMarketplace.json`（或对应的文件）
4. 复制其中的 `abi` 字段

## ⚠️ 重要注意事项

### 1. 价格参数问题

**当前代码问题：**
```python
mint_result = blockchain_service.mint_context_nft(
    user_address=wallet_address,
    metadata_url=storage_result["metadataUrl"],
    price_wei=0  # ⚠️ 这里传入的是 0
)
```

**合约要求：**
```solidity
require(_price > 0, "Price must be greater than 0");
```

**解决方案：**
- 修改代码，传入一个大于 0 的价格
- 或者修改合约，允许价格为 0（不推荐）

### 2. 合约地址配置

在 `.env` 文件中：

```env
# 如果使用 ETHUserDataMarketplace
CONTRACT_ADDRESS=0x你的Marketplace合约地址
# PAYMENT_TOKEN_ADDRESS 不需要配置

# 如果使用 UserDataMarketplace
CONTRACT_ADDRESS=0x你的Marketplace合约地址
PAYMENT_TOKEN_ADDRESS=0x你的DataToken合约地址
```

## 📝 配置步骤总结

### 步骤 1：确定你部署的合约

- [ ] 我部署了 `ETHUserDataMarketplace`（ETH 支付）
- [ ] 我部署了 `UserDataMarketplace`（ERC20 代币支付）

### 步骤 2：获取 Marketplace 合约的 ABI

- [ ] 在 Remix 中编译对应的合约
- [ ] 复制完整的 ABI JSON
- [ ] 更新 `backend/services/blockchain_service.py` 中的 `ETH_MARKETPLACE_ABI`

### 步骤 3：配置 .env 文件

- [ ] 设置 `CONTRACT_ADDRESS`（Marketplace 合约地址）
- [ ] 如果使用 ERC20 版本，设置 `PAYMENT_TOKEN_ADDRESS`
- [ ] 配置其他必要的参数

### 步骤 4：修复价格问题

- [ ] 修改代码，确保传入的价格 > 0
- [ ] 或者修改合约允许价格为 0

## 🎯 推荐方案

**推荐使用 `ETHUserDataMarketplace`（ETH 支付版本）**，因为：
- ✅ 更简单，不需要额外的代币合约
- ✅ 直接使用 ETH，用户更容易理解
- ✅ 减少配置复杂度

**配置示例：**
```env
# 使用 ETH 支付版本
CONTRACT_ADDRESS=0x你的ETHUserDataMarketplace合约地址
# 不需要 PAYMENT_TOKEN_ADDRESS
```

## ❓ 常见问题

### Q1: 我应该使用哪个 ABI？

**A**: 使用你**实际部署的 Marketplace 合约**的 ABI：
- 如果部署了 `ETHUserDataMarketplace` → 使用它的 ABI
- 如果部署了 `UserDataMarketplace` → 使用它的 ABI
- **不要使用** `DataToken_ABI.json`（那是代币合约，不是 Marketplace）

### Q2: 如何知道我在 Remix 中部署了哪个合约？

**A**: 
1. 查看 Remix 的 "Deploy & Run Transactions" 标签页
2. 查看 "Deployed Contracts" 列表
3. 查看合约名称

### Q3: 我可以同时使用两个 ABI 吗？

**A**: 不需要。后端只需要 Marketplace 合约的 ABI。代币合约的 ABI 只在需要直接与代币交互时使用（通常不需要）。

### Q4: 如果我没有从 Remix 获取 ABI，可以手动创建吗？

**A**: 可以，但不推荐。最好从 Remix 获取，因为：
- 确保 ABI 完整且正确
- 包含所有函数和事件
- 避免手动输入错误

---

## ✅ 下一步

1. **确定你部署的合约类型**
2. **从 Remix 获取对应的完整 ABI**
3. **更新 `blockchain_service.py` 中的 ABI**
4. **配置 `.env` 文件**
5. **修复价格参数问题**
6. **测试连接**




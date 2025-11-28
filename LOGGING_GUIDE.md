# 日志系统使用指南

## 📋 概述

所有应用的输出（包括之前的 `print` 语句）现在都会记录到日志文件中，方便调试和问题排查。

## 📁 日志文件位置

日志文件存储在项目根目录的 `logs/` 文件夹中：

```
Project/
  logs/
    app_20251128.log  # 按日期命名的日志文件
```

日志文件命名格式：`app_YYYYMMDD.log`（例如：`app_20251128.log`）

## 🔍 查看日志

### 方法 1: 直接查看文件

```bash
# 查看最新的日志文件
cat logs/app_$(date +%Y%m%d).log

# 或者使用 tail 实时查看（推荐）
tail -f logs/app_$(date +%Y%m%d).log
```

### 方法 2: 使用文本编辑器

直接用你喜欢的编辑器打开日志文件：
- VS Code: `code logs/app_20251128.log`
- Vim: `vim logs/app_20251128.log`
- 其他编辑器...

### 方法 3: 搜索特定内容

```bash
# 搜索包含 "error" 的行
grep -i error logs/app_*.log

# 搜索钱包验证相关的日志
grep -i "signature\|nonce\|wallet" logs/app_*.log

# 搜索 IPFS 相关的日志
grep -i "ipfs\|pinata" logs/app_*.log
```

## 📝 日志格式

每条日志包含以下信息：

```
2025-11-28 10:30:45 - crypto_utils - DEBUG - crypto_utils.py:59 - Signature verification - recovered address: 0x1234..., expected: 0x1234...
```

格式说明：
- `2025-11-28 10:30:45` - 时间戳
- `crypto_utils` - 模块名称
- `DEBUG` - 日志级别（DEBUG, INFO, WARNING, ERROR）
- `crypto_utils.py:59` - 文件名和行号
- `Signature verification...` - 日志消息

## 🎯 日志级别

系统使用以下日志级别：

- **DEBUG**: 详细的调试信息（如签名验证的恢复地址）
- **INFO**: 一般信息（如连接成功、操作完成）
- **WARNING**: 警告信息（如连接失败但使用备用方案）
- **ERROR**: 错误信息（如认证失败、操作失败）

## 🔧 调试钱包验证问题

当钱包验证失败时，可以查看日志文件中的以下信息：

1. **Nonce 生成**：
   ```
   INFO - Generated nonce for wallet: 0x...
   ```

2. **签名验证**：
   ```
   DEBUG - Signature verification - recovered address: 0x..., expected: 0x...
   ```

3. **错误信息**：
   ```
   ERROR - Signature verification failed with exception: ...
   WARNING - 鉴权 nonce 已失效或不存在，请重新获取。
   ```

## 📊 日志文件管理

- 日志文件按日期自动创建
- 每天会生成新的日志文件
- 旧的日志文件会保留在 `logs/` 目录中
- 建议定期清理旧的日志文件以节省空间

## 💡 提示

1. **实时监控**：使用 `tail -f` 可以实时查看日志输出
2. **过滤日志**：使用 `grep` 可以快速找到相关的日志条目
3. **日志级别**：在开发环境中，所有级别的日志都会记录；生产环境可以调整日志级别以减少日志量

## 🚀 快速开始

启动应用后，日志会自动写入到日志文件。无需额外配置！

```bash
# 启动应用
python -m flask --app backend.main:app run --reload

# 在另一个终端实时查看日志
tail -f logs/app_$(date +%Y%m%d).log
```


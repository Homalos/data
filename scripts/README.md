# Scripts 目录说明

本目录包含各种实用脚本，用于系统的初始化、测试、维护和监控。

---

## 📁 脚本分类

### 🚀 启动和登录脚本

#### `auto_login_td.py`
**自动登录交易服务**

自动连接WebSocket并登录交易服务，登录成功后自动查询合约信息。

```bash
# 使用 .env 文件配置（推荐）
python scripts/auto_login_td.py

# 使用环境变量
set CTP_USER_ID=your_account
set CTP_PASSWORD=your_password
python scripts/auto_login_td.py
```

**功能**：
- ✅ 自动连接WebSocket
- ✅ 自动登录
- ✅ 自动查询合约
- ✅ 保存合约信息到JSON

**相关文档**：`HOW_TO_USE_AUTO_LOGIN.md`

#### `start_and_login.bat`
**一键启动脚本（Windows）**

自动启动交易服务并执行登录流程。

```bash
scripts\start_and_login.bat
```

---

### 📊 K线数据管理脚本（CSV）

#### `query_kline_csv.py`
**查询CSV格式的K线数据**

查询、列出和浏览CSV格式存储的K线数据。

```bash
# 查询特定合约的K线（显示最后10根）
python scripts/query_kline_csv.py query 20251224 1m zc601

# 查询并显示所有K线
python scripts/query_kline_csv.py query 20251224 1m zc601 --limit 0

# 列出指定交易日和周期的所有合约
python scripts/query_kline_csv.py list 20251224 1m

# 列出所有交易日
python scripts/query_kline_csv.py days
```

**功能**：
- ✅ 查询特定合约的K线数据
- ✅ 列出所有合约
- ✅ 列出所有交易日
- ✅ 显示文件大小和K线数量

#### `check_kline_disk_usage.py`
**检查K线数据磁盘使用情况**

统计K线数据的磁盘使用情况，按交易日和周期分类。

```bash
python scripts/check_kline_disk_usage.py
```

**功能**：
- ✅ 按交易日统计文件数和大小
- ✅ 按周期统计文件数和大小
- ✅ 显示总计和平均每日增长
- ✅ 预估一年数据量

#### `cleanup_old_klines.py`
**清理旧的K线数据**

删除指定天数之前的K线数据，释放磁盘空间。

```bash
# 模拟运行（不实际删除）
python scripts/cleanup_old_klines.py --days 30

# 实际删除
python scripts/cleanup_old_klines.py --days 30 --execute
```

**功能**：
- ✅ 按天数清理旧数据
- ✅ 模拟运行模式（安全）
- ✅ 显示删除统计
- ✅ 计算释放空间

---

### 🧪 测试脚本

#### `test_storage_client.py`
**测试存储系统客户端**

测试行情订阅和存储功能，从配置文件加载参数。

```bash
python scripts/test_storage_client.py
```

**功能**：
- ✅ 从 `.env` 读取账号密码
- ✅ 从 `instruments.json` 加载合约
- ✅ 从配置文件读取测试参数
- ✅ 自动订阅和监听行情

**相关文档**：`scripts/TEST_STORAGE_CLIENT_GUIDE.md`

#### `test_auto_query_instruments.py`
**测试自动查询合约功能**

验证合约自动查询和保存功能。

```bash
python scripts/test_auto_query_instruments.py
```

#### `test_futures_filter.py`
**测试期货过滤功能**

测试期货识别逻辑，验证期权过滤。

```bash
python scripts/test_futures_filter.py
```

#### `test_new_storage_structure.py`
**测试新存储结构**

测试按合约分表的存储结构。

```bash
python scripts/test_new_storage_structure.py
```

#### `test_server_validation.py`
**测试服务器验证**

验证服务器配置和连接。

```bash
python scripts/test_server_validation.py
```

#### `run_tests.py` / `run_tests.bat`
**运行测试套件**

运行所有单元测试，可选生成覆盖率报告。

```bash
# Python脚本（跨平台）
python scripts/run_tests.py
python scripts/run_tests.py --cov  # 生成覆盖率报告
python scripts/run_tests.py --file instrument_manager  # 运行特定测试

# Windows批处理
scripts\run_tests.bat
```

---

### 🔧 初始化和配置脚本

#### `init_influxdb.py`
**初始化InfluxDB**

初始化InfluxDB数据库和配置。

```bash
python scripts/init_influxdb.py
```

#### `check_config.py`
**检查配置文件**

验证配置文件格式和字段。

```bash
python scripts/check_config.py
```

#### `check_dependencies.py`
**检查依赖**

检查Python依赖是否安装。

```bash
python scripts/check_dependencies.py
```

#### `load_env.py`
**加载环境变量**

从 `.env` 文件加载环境变量的工具模块。

```python
from scripts.load_env import load_env
load_env()
```

---

### 📊 数据检查和验证脚本

#### `check_influx_final.py`
**检查InfluxDB数据（最终版）**

检查InfluxDB中的Tick和K线数据。

```bash
python scripts/check_influx_final.py
```

**功能**：
- ✅ 查询所有表
- ✅ 统计数据量
- ✅ 显示样本数据
- ✅ 使用pandas格式化输出

#### `check_tables.py`
**检查数据库表**

列出InfluxDB中的所有表。

```bash
python scripts/check_tables.py
```

#### `verify_data.py`
**验证数据存储**

验证数据是否正确存储到InfluxDB。

```bash
python scripts/verify_data.py
```

---

### 🔄 数据维护脚本

#### `retry_failed_data.py`
**重试失败数据**

重试之前写入失败并保存到本地文件的数据。

```bash
python scripts/retry_failed_data.py
```

**功能**：
- ✅ 扫描 `data/failures/` 目录
- ✅ 读取失败数据文件
- ✅ 重新尝试写入InfluxDB
- ✅ 成功后自动删除文件
- ✅ 显示详细统计信息

**使用场景**：
- InfluxDB故障恢复后
- 网络问题解决后
- 定期清理失败数据

#### `reset_influxdb.py`
**重置InfluxDB**

清空InfluxDB数据库（谨慎使用）。

```bash
python scripts/reset_influxdb.py
```

⚠️ **警告**：此操作会删除所有数据，不可恢复！

---

## 📝 使用指南

### 快速开始

1. **首次使用**：
```bash
# 1. 检查依赖
python scripts/check_dependencies.py

# 2. 配置环境变量
copy .env.example .env
# 编辑 .env 填入账号密码

# 3. 初始化InfluxDB
python scripts/init_influxdb.py

# 4. 检查配置
python scripts/check_config.py
```

2. **自动登录和查询合约**：
```bash
# 启动交易服务（终端1）
python -m uvicorn src.apps.td_app:app --host 0.0.0.0 --port 8081

# 自动登录（终端2）
python scripts/auto_login_td.py
```

3. **测试存储系统**：
```bash
# 启动行情服务（终端1）
python -m uvicorn src.apps.md_app:app --host 0.0.0.0 --port 8080

# 测试存储客户端（终端2）
python scripts/test_storage_client.py
```

4. **检查数据**：
```bash
# 检查InfluxDB数据
python scripts/check_influx_final.py

# 检查表结构
python scripts/check_tables.py
```

5. **运行测试**：
```bash
# 运行所有测试
python scripts/run_tests.py

# 生成覆盖率报告
python scripts/run_tests.py --cov
```

---

## 🔍 故障排查

### 问题1：连接失败

```bash
# 检查服务是否启动
# 检查端口是否正确
# 检查防火墙设置
```

### 问题2：登录失败

```bash
# 检查账号密码
# 检查配置文件
python scripts/check_config.py
```

### 问题3：数据写入失败

```bash
# 检查InfluxDB连接
python scripts/check_influx_final.py

# 重试失败数据
python scripts/retry_failed_data.py
```

### 问题4：依赖缺失

```bash
# 检查依赖
python scripts/check_dependencies.py

# 安装依赖
pip install -r requirements.txt
```

---

## 📚 相关文档

- `HOW_TO_USE_AUTO_LOGIN.md` - 自动登录详细指南
- `TEST_STORAGE_CLIENT_GUIDE.md` - 存储客户端测试指南
- `STORAGE_IMPROVEMENT_COMPLETE.md` - 存储改进完成报告
- `DATA_LOSS_RISK_ANALYSIS.md` - 数据丢失风险分析
- `TESTS_UPDATE_COMPLETE.md` - 测试更新完成报告

---

## 🗂️ 脚本列表

### 核心脚本（17个）

| 脚本名 | 用途 | 状态 |
|--------|------|------|
| `auto_login_td.py` | 自动登录交易服务 | ✅ 活跃 |
| `start_and_login.bat` | 一键启动（Windows） | ✅ 活跃 |
| `test_storage_client.py` | 测试存储客户端 | ✅ 活跃 |
| `test_auto_query_instruments.py` | 测试合约查询 | ✅ 活跃 |
| `test_futures_filter.py` | 测试期货过滤 | ✅ 活跃 |
| `test_new_storage_structure.py` | 测试新存储结构 | ✅ 活跃 |
| `test_server_validation.py` | 测试服务器验证 | ✅ 活跃 |
| `run_tests.py` | 运行测试套件 | ✅ 活跃 |
| `run_tests.bat` | 运行测试（Windows） | ✅ 活跃 |
| `init_influxdb.py` | 初始化InfluxDB | ✅ 活跃 |
| `check_config.py` | 检查配置 | ✅ 活跃 |
| `check_dependencies.py` | 检查依赖 | ✅ 活跃 |
| `load_env.py` | 加载环境变量 | ✅ 活跃 |
| `check_influx_final.py` | 检查InfluxDB数据 | ✅ 活跃 |
| `check_tables.py` | 检查数据库表 | ✅ 活跃 |
| `verify_data.py` | 验证数据存储 | ✅ 活跃 |
| `retry_failed_data.py` | 重试失败数据 | ✅ 活跃 |
| `reset_influxdb.py` | 重置数据库 | ⚠️ 谨慎使用 |

### 已删除的过时脚本（10个）

| 脚本名 | 删除原因 |
|--------|---------|
| `verify_strategy_removal.py` | 策略移除已完成 |
| `query_influxdb_direct.py` | 被更好的版本替代 |
| `test_websocket_path.py` | 调试用途已完成 |
| `debug_login.py` | 已有auto_login_td.py |
| `test_direct_write.py` | 调试用途已完成 |
| `check_influxdb_simple.py` | 被更好的版本替代 |
| `test_ws_connection.py` | 调试用途已完成 |
| `check_influxdb_data.py` | 被更好的版本替代 |
| `test_simple_login.py` | 已有auto_login_td.py |
| `verify_fix.py` | 修复已完成 |

---

## 🔄 更新日志

### 2025-12-23
- ✅ 删除10个过时/重复脚本
- ✅ 新增 `retry_failed_data.py` - 重试失败数据
- ✅ 新增 `run_tests.py/bat` - 运行测试套件
- ✅ 更新 `README.md` - 完整的脚本文档

### 之前版本
- ✅ 创建 `auto_login_td.py`
- ✅ 创建 `test_storage_client.py`
- ✅ 创建各种测试和验证脚本

---

## 💡 最佳实践

1. **使用 .env 文件**：避免在代码中硬编码敏感信息
2. **定期检查数据**：使用 `check_influx_final.py` 监控数据
3. **重试失败数据**：定期运行 `retry_failed_data.py`
4. **运行测试**：修改代码后运行 `run_tests.py`
5. **备份数据**：重要操作前备份InfluxDB数据

---

**最后更新**: 2025-12-23  
**维护者**: Kiro AI Assistant

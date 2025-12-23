# 测试文档

## 测试文件列表

### 1. test_instrument_manager.py
**测试合约管理器**

测试内容：
- ✅ 初始化
- ✅ 保存和加载缓存
- ✅ 期货识别（过滤期权）
- ✅ 按交易所查询合约
- ✅ 按品种查询合约

**更新说明**（2025-12-23）：
- 更新为简化的数据结构（移除了 `instrument_name`, `create_date`, `expire_date`, `is_trading` 字段）
- 添加期货识别测试（`is_futures` 方法）
- 移除了 `get_trading_instruments` 测试（已删除该方法）

运行测试：
```bash
pytest tests/test_instrument_manager.py -v
```

---

### 2. test_tick_storage.py
**测试Tick存储模块**

测试内容：
- ✅ Tick缓冲器初始化
- ✅ 添加数据和大小检查
- ✅ 缓冲区满判断（新版本：不丢弃数据）
- ✅ 获取批次
- ✅ 统计信息
- ✅ 清空缓冲区
- ✅ 数据点转换（按合约分表）
- ✅ 时间戳解析
- ✅ 统计信息（包含失败处理器）

**更新说明**（2025-12-23）：
- 更新缓冲区测试：新版本移除了 `maxlen` 限制，不会丢弃数据
- 更新数据点转换测试：新版本按合约分表（`tick_rb2505` 而非 `market_tick`）
- 更新统计信息测试：包含失败处理器统计

运行测试：
```bash
pytest tests/test_tick_storage.py -v
```

---

### 3. test_kline_builder.py
**测试K线合成模块**

测试内容：
- ✅ K线周期定义
- ✅ K线数据结构
- ✅ K线合成器初始化
- ✅ 时间对齐算法
- ✅ K线完成判断
- ✅ 处理tick数据
- ✅ 统计信息

**状态**：无需更新，与最新代码兼容

运行测试：
```bash
pytest tests/test_kline_builder.py -v
```

---

### 4. test_failure_handler.py
**测试失败数据处理器**（新增）

测试内容：
- ✅ 初始化
- ✅ 保存失败批次
- ✅ 重试成功场景
- ✅ 重试失败场景
- ✅ 按数据类型重试
- ✅ 统计信息
- ✅ 保存空批次
- ✅ 清理旧文件

**新增说明**（2025-12-23）：
- 测试失败数据持久化功能
- 测试重试机制
- 测试文件管理

运行测试：
```bash
pytest tests/test_failure_handler.py -v
```

---

## 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_instrument_manager.py -v

# 运行特定测试类
pytest tests/test_tick_storage.py::TestTickBuffer -v

# 运行特定测试方法
pytest tests/test_tick_storage.py::TestTickBuffer::test_init -v

# 显示详细输出
pytest tests/ -v -s

# 生成覆盖率报告
pytest tests/ --cov=src/storage --cov-report=html
```

---

## 测试覆盖范围

### 合约管理模块
- ✅ InstrumentManager
- ✅ InstrumentInfo
- ✅ 期货识别逻辑
- ✅ 缓存管理

### Tick存储模块
- ✅ TickBuffer（无容量限制）
- ✅ TickStorage
- ✅ 数据点转换（按合约分表）
- ✅ 时间戳解析

### K线合成模块
- ✅ KLinePeriod
- ✅ KLineBar
- ✅ KLineBuilder
- ✅ 时间对齐
- ✅ K线完成判断

### 失败处理模块
- ✅ FailureHandler
- ✅ 失败数据保存
- ✅ 重试机制
- ✅ 文件管理

---

## 测试环境要求

### Python依赖
```bash
pip install pytest pytest-asyncio pytest-cov
```

### 配置文件
测试会使用临时配置，不需要真实的InfluxDB连接。

---

## 测试数据

测试使用模拟数据，不会影响生产环境：
- 临时缓存文件：`data/test_instruments.json`
- 临时失败数据目录：由 pytest 的 `tmp_path` fixture 提供

---

## 已知问题

### 1. 异步测试
某些测试需要 `pytest-asyncio` 插件：
```bash
pip install pytest-asyncio
```

### 2. 临时文件清理
测试会自动清理临时文件，但如果测试中断，可能需要手动清理：
```bash
rm -f data/test_instruments.json
```

---

## 测试统计

| 模块 | 测试文件 | 测试用例数 | 状态 |
|------|---------|-----------|------|
| 合约管理 | test_instrument_manager.py | 4 | ✅ 通过 |
| Tick存储 | test_tick_storage.py | 9 | ✅ 通过 |
| K线合成 | test_kline_builder.py | 11 | ✅ 通过 |
| 失败处理 | test_failure_handler.py | 9 | ✅ 通过 |
| **总计** | **4个文件** | **33个用例** | **✅ 全部通过** |

---

## 更新日志

### 2025-12-23
- ✅ 更新 `test_instrument_manager.py` - 适配简化的数据结构
- ✅ 更新 `test_tick_storage.py` - 适配无容量限制和按合约分表
- ✅ 新增 `test_failure_handler.py` - 测试失败数据处理器
- ✅ 创建测试文档 `tests/README.md`

### 之前版本
- ✅ 创建 `test_instrument_manager.py`
- ✅ 创建 `test_tick_storage.py`
- ✅ 创建 `test_kline_builder.py`

---

## 贡献指南

### 添加新测试

1. 在 `tests/` 目录创建新的测试文件：`test_<module_name>.py`
2. 导入必要的模块和 pytest
3. 创建测试类：`class Test<ModuleName>`
4. 编写测试方法：`def test_<feature_name>(self)`
5. 运行测试验证

### 测试命名规范

- 测试文件：`test_<module_name>.py`
- 测试类：`Test<ModuleName>`
- 测试方法：`test_<feature_name>`
- 使用描述性名称，清楚表达测试意图

### 测试最佳实践

1. **独立性**：每个测试应该独立运行，不依赖其他测试
2. **清理**：测试后清理临时文件和数据
3. **断言**：使用清晰的断言消息
4. **覆盖率**：尽量覆盖正常和异常情况
5. **文档**：添加测试说明文档字符串

---

**最后更新**: 2025-12-23  
**维护者**: Kiro AI Assistant

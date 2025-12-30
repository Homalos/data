# 日志工具使用指南

## 概述

homalos-data 项目使用基于 `loguru` 的日志工具类 `Logger`，提供强大的日志记录功能。

### 主要特性

- ✅ **标签分类**：使用 `tag` 参数对日志进行分类
- ✅ **默认 Tag**：支持类级别默认标签，减少重复代码
- ✅ **Trace ID 追踪**：支持请求级别的追踪 ID
- ✅ **YAML 配置**：支持从配置文件加载日志配置
- ✅ **多输出目标**：同时输出到控制台和文件
- ✅ **自动轮转**：日志文件自动轮转和压缩
- ✅ **线程安全**：支持多线程和异步操作
- ✅ **详细堆栈**：异常时包含完整堆栈跟踪

## 快速开始

### 基础使用

```python
from src.utils.log import logger

# 不指定 tag - 日志不带标签
logger.debug("调试信息")
logger.info("普通信息")
logger.success("成功信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")

# 指定 tag - 日志带标签
logger.info("普通信息", tag="auth")
logger.error("错误信息", tag="database")
logger.success("成功信息", tag="payment")
```

### 异常记录

```python
from src.utils.log import logger

try:
    result = 1 / 0
except Exception as e:
    logger.exception("发生异常", tag="error")
    # 自动记录完整的堆栈跟踪
```

---

## 配置文件

日志配置存储在 `config/logger.yaml` 文件中，支持自定义各项配置。

### 配置文件位置

```
config/logger.yaml
```

### 配置文件结构

```yaml
# 日志配置文件

# 日志目录
log_dir: logs

# 控制台输出配置
console:
  enabled: true
  level: DEBUG
  colorize: true
  format: "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"

# 主日志文件配置
main_log:
  enabled: true
  filename: webctp.log
  level: DEBUG
  rotation: "500 MB"      # 单文件大小限制
  retention: "7 days"     # 保留时间
  compression: zip        # 压缩格式
  format: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"

# 错误日志文件配置
error_log:
  enabled: true
  filename: webctp_error.log
  level: ERROR
  rotation: "500 MB"
  retention: "30 days"
  compression: zip
  format: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"

# 通用配置
common:
  backtrace: true         # 是否显示完整堆栈
  diagnose: true          # 是否显示诊断信息
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `log_dir` | 日志文件目录 | `logs` |
| `console.enabled` | 是否启用控制台输出 | `true` |
| `console.level` | 控制台日志级别 | `DEBUG` |
| `console.colorize` | 是否启用颜色 | `true` |
| `main_log.enabled` | 是否启用主日志文件 | `true` |
| `main_log.filename` | 主日志文件名 | `webctp.log` |
| `main_log.level` | 主日志级别 | `DEBUG` |
| `main_log.rotation` | 日志轮转大小 | `500 MB` |
| `main_log.retention` | 日志保留时间 | `7 days` |
| `error_log.enabled` | 是否启用错误日志文件 | `true` |
| `error_log.filename` | 错误日志文件名 | `webctp_error.log` |
| `error_log.level` | 错误日志级别 | `ERROR` |
| `error_log.retention` | 错误日志保留时间 | `30 days` |
| `common.backtrace` | 是否显示完整堆栈 | `true` |
| `common.diagnose` | 是否显示诊断信息 | `true` |

### 日志级别

支持的日志级别（从低到高）：
- `DEBUG` - 调试信息
- `INFO` - 一般信息
- `SUCCESS` - 成功信息
- `WARNING` - 警告信息
- `ERROR` - 错误信息
- `CRITICAL` - 严重错误

### 格式模板变量

| 变量 | 说明 |
|------|------|
| `{time}` | 时间戳 |
| `{level}` | 日志级别 |
| `{name}` | 模块名 |
| `{function}` | 函数名 |
| `{line}` | 行号 |
| `{message}` | 日志消息 |

### 生产环境配置示例

```yaml
# 生产环境配置
log_dir: /var/log/webctp

console:
  enabled: false          # 生产环境关闭控制台输出

main_log:
  enabled: true
  filename: webctp.log
  level: INFO             # 生产环境使用 INFO 级别
  rotation: "100 MB"
  retention: "30 days"

error_log:
  enabled: true
  filename: webctp_error.log
  level: ERROR
  rotation: "100 MB"
  retention: "90 days"

common:
  backtrace: true
  diagnose: false         # 生产环境关闭诊断信息
```

---

## Tag 标签系统

### 什么是 Tag？

`tag` 是日志的**分类标签**，用于：

- **日志分类** - 快速识别日志来自哪个模块或功能
- **日志过滤** - 在日志文件中快速查找特定类型的日志
- **问题追踪** - 通过 tag 追踪特定功能的执行流程
- **性能分析** - 统计不同模块的日志数量和性能指标

### 常见 Tag 使用场景

| Tag | 使用场景 | 示例 |
|-----|---------|------|
| `auth` | 认证和授权相关 | 登录、权限验证 |
| `database` | 数据库操作 | 查询、插入、更新、删除 |
| `websocket` | WebSocket 通信 | 连接、断开、消息收发 |
| `payment` | 支付相关 | 支付处理、退款 |
| `order` | 订单相关 | 订单创建、更新、取消 |
| `cache` | 缓存操作 | 缓存命中、缓存更新 |
| `connection` | 连接管理 | 连接建立、断开 |

### Tag 命名规范

1. **使用小写字母** - `auth`, `database`, `websocket`
2. **使用下划线分隔** - `user_auth`, `db_query`, `ws_connect`
3. **保持简洁** - 通常 1-2 个单词
4. **表示功能/模块** - 而不是日志级别
5. **保持一致性** - 同一功能使用相同的 tag

---

## 默认 Tag 功能

### 功能说明

默认 Tag 功能允许在类初始化时设置一个默认标签，这样在该类中记录日志时就不需要每次都传入 `tag` 参数。

### API 方法

```python
# 设置默认 tag
logger.set_default_tag(tag: Optional[str] = None) -> None

# 清除默认 tag
logger.clear_default_tag() -> None

# 获取默认 tag
logger.get_default_tag() -> Optional[str]
```

### 基础用法

```python
from src.utils.log import logger

class PaymentService:
    """支付服务"""
    
    def __init__(self):
        # 设置类级别的默认 tag
        logger.set_default_tag("payment")
        logger.info("支付服务初始化")
    
    def process_payment(self, order_id: str):
        # 不需要传入 tag，自动使用 "payment"
        logger.info(f"开始处理支付: {order_id}")
        logger.debug("验证订单")
        logger.success("支付成功")
    
    def __del__(self):
        # 清理时清除默认 tag
        logger.clear_default_tag()
```

**输出：**
```
INFO     | [payment] 支付服务初始化
INFO     | [payment] 开始处理支付: ORD-123
DEBUG    | [payment] 验证订单
SUCCESS  | [payment] 支付成功
```

### 覆盖默认 Tag

```python
class OrderService:
    def __init__(self):
        logger.set_default_tag("order")
    
    def create_order(self, user_id: int):
        logger.info("创建订单")  # 使用默认 tag "order"
        
        # 覆盖默认 tag
        logger.debug("查询用户", tag="database")  # 使用 "database"
        logger.info("处理支付", tag="payment")    # 使用 "payment"
        
        logger.success("订单完成")  # 又回到默认 tag "order"
```

### 优先级规则

```python
# 优先级：传入的 tag > 默认 tag > 无 tag
logger.set_default_tag("default")

logger.info("使用默认")           # [default]
logger.info("覆盖", tag="custom") # [custom]
logger.info("又回到默认")         # [default]
```

---

## Trace ID 追踪

Logger 支持三种方式使用 trace_id：

### 方式 1：为单条日志添加 trace_id

```python
from src.utils.log import logger

# 自动生成 UUID 作为 trace_id
logger.info("处理请求", trace_id=True)
logger.info("查询数据库", tag="database", trace_id=True)

# 指定 trace_id
logger.info("处理请求", trace_id="req-12345")
logger.error("数据库错误", tag="database", trace_id="req-12345")
```

### 方式 2：全局设置 trace_id

```python
from src.utils.log import logger

# 设置全局 trace_id
logger.set_trace_id("req-12345")
logger.info("处理请求", tag="request")
logger.info("查询数据库", tag="database")

# 清除 trace_id
logger.clear_trace_id()
```

### 方式 3：自动生成全局 trace_id

```python
from src.utils.log import logger

# 自动生成 UUID 作为全局 trace_id
trace_id = logger.set_trace_id()
logger.info("处理请求", tag="request")
logger.info("查询数据库", tag="database")

# 清除 trace_id
logger.clear_trace_id()
```

### 与默认 Tag 结合

```python
class PaymentService:
    def __init__(self):
        logger.set_default_tag("payment")
    
    def process_payment(self, order_id: str):
        trace_id = logger.set_trace_id()
        
        try:
            # 所有日志都会带上 [payment] tag 和 trace_id
            logger.info(f"开始处理: {order_id}")
            logger.debug("调用 API")
            logger.success("处理完成")
        finally:
            logger.clear_trace_id()
```

**输出：**
```
INFO     | [trace_id=abc-123] [payment] 开始处理: ORD-456
DEBUG    | [trace_id=abc-123] [payment] 调用 API
SUCCESS  | [trace_id=abc-123] [payment] 处理完成
```

---

## 实际应用场景

### 1. 服务类

```python
class DatabaseService:
    def __init__(self):
        logger.set_default_tag("database")
        logger.info("数据库服务初始化")
    
    def query(self, sql: str):
        logger.debug(f"执行查询: {sql}")
        return []
    
    def insert(self, table: str, data: dict):
        logger.info(f"插入数据到表 {table}")
        logger.success("数据插入成功")
    
    def __del__(self):
        logger.clear_default_tag()
```

### 2. WebSocket 连接

```python
class WebSocketConnection:
    def __init__(self, client_id: str):
        logger.set_default_tag("websocket")
        logger.info(f"连接建立: {client_id}")
    
    async def send(self, message: str):
        logger.debug("发送消息")
    
    async def receive(self) -> str:
        logger.debug("接收消息")
```

### 3. 认证服务

```python
class AuthService:
    def __init__(self):
        logger.set_default_tag("auth")
    
    def login(self, username: str):
        logger.info(f"用户登录: {username}")
    
    def logout(self, token: str):
        logger.info("用户登出")
```

---

## 日志输出

### 控制台输出

```
2025-12-30 14:30:45.123 | DEBUG    | [trace_id=req-12345] [database] 查询用户: 123
2025-12-30 14:30:46.456 | INFO     | [trace_id=req-12345] [request] 处理请求
2025-12-30 14:30:47.789 | SUCCESS  | [trace_id=req-12345] [request] 订单处理完成
```

### 文件输出

日志文件位置：`logs/` 目录

- `webctp.log` - 所有日志（DEBUG 及以上）
- `webctp_error.log` - 仅错误日志（ERROR 及以上）

---

## API 参考

### 日志方法

```python
logger.debug(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None) -> None
logger.info(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None) -> None
logger.success(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None) -> None
logger.warning(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None) -> None
logger.error(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None) -> None
logger.critical(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None) -> None
logger.exception(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None) -> None

# trace_id 参数说明：
# - True: 自动生成 UUID
# - str: 使用指定的 trace_id
# - None/False: 不添加 trace_id
```

### Trace ID 方法

```python
logger.set_trace_id(trace_id: Optional[str] = None) -> str
logger.get_trace_id() -> Optional[str]
logger.clear_trace_id() -> None
```

### 默认 Tag 方法

```python
logger.set_default_tag(tag: Optional[str] = None) -> None
logger.get_default_tag() -> Optional[str]
logger.clear_default_tag() -> None
```

### 配置方法

```python
logger.get_config() -> dict  # 获取当前日志配置
```

---

## 日志查询

使用 `grep` 命令查询日志文件：

```bash
# 查看所有支付相关的日志
grep "\[payment\]" logs/webctp.log

# 查看特定请求的所有日志
grep "trace_id=req-123" logs/webctp.log

# 结合 tag 和 trace_id 查看
grep "trace_id=req-123" logs/webctp.log | grep "\[payment\]"

# 统计某个 tag 的日志数量
grep -c "\[database\]" logs/webctp.log

# 查看最近的 100 条支付日志
grep "\[payment\]" logs/webctp.log | tail -100
```

---

## 最佳实践

### 1. 在 `__init__` 中设置默认 Tag

```python
class MyService:
    def __init__(self):
        logger.set_default_tag("my_service")
        logger.info("服务初始化")
```

### 2. 使用有意义的 Tag

```python
# ✅ 好的做法
logger.set_default_tag("payment")
logger.set_default_tag("database")

# ❌ 不好的做法
logger.set_default_tag("service")  # 太泛化
```

### 3. 使用适当的日志级别

```python
logger.debug("详细调试信息", tag="database")  # DEBUG
logger.info("一般信息", tag="auth")           # INFO
logger.success("操作成功", tag="order")       # SUCCESS
logger.warning("警告信息", tag="retry")       # WARNING
logger.error("错误信息", tag="payment")       # ERROR
logger.critical("严重错误", tag="system")     # CRITICAL
```

### 4. 异常处理

```python
# ✅ 好的做法
try:
    result = risky_operation()
except Exception as e:
    logger.exception("操作失败", tag="operation")
    raise
```

---

## 常见问题

### Q: 如何修改日志级别？

A: 编辑 `config/logger.yaml` 中的 `level` 配置项。

### Q: 日志文件会无限增长吗？

A: 不会。日志文件设置了自动轮转和压缩，可在配置文件中调整 `rotation` 和 `retention`。

### Q: 如何在异步代码中使用？

A: `contextvars` 自动支持异步上下文，无需特殊处理。

### Q: 默认 Tag 是线程安全的吗？

A: 是的，使用 `contextvars.ContextVar` 实现，确保多线程和异步协程安全。

### Q: 配置文件不存在会怎样？

A: Logger 会使用内置的默认配置，不会报错。

---

## 相关文件

- `src/utils/log/logger.py` - 日志工具类实现
- `src/utils/log/__init__.py` - 日志模块导出
- `config/logger.yaml` - 日志配置文件
- `logs/` - 日志文件目录（自动创建）

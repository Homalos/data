# Logger 默认 Tag 使用指南

## 概述

Logger 现在支持**类级别的默认 tag**，可以在类初始化时设置一个默认标签，这样在该类中记录日志时就不需要每次都传入 `tag` 参数了。

## 功能特性

- ✅ **类级别默认 tag** - 在类中设置一次，所有日志自动使用
- ✅ **可覆盖** - 仍然可以为单条日志指定不同的 tag
- ✅ **上下文安全** - 使用 `contextvars`，支持多线程和异步
- ✅ **灵活控制** - 可以随时设置、清除或修改默认 tag

## 使用方法

### 方式 1: 在类的 `__init__` 中设置默认 tag

这是**最推荐**的方式，适合大多数场景。

```python
from src.utils.log import logger

class PaymentService:
    """支付服务"""
    
    def __init__(self):
        # 设置类级别的默认 tag
        logger.set_default_tag("payment")
    
    def process_payment(self, order_id: str, amount: float):
        # 不需要传入 tag，自动使用 "payment"
        logger.info(f"开始处理支付: {order_id}")
        
        try:
            # 验证金额
            if amount <= 0:
                logger.warning(f"无效金额: {amount}")
                raise ValueError("金额必须大于 0")
            
            # 调用支付接口
            result = self._call_payment_api(order_id, amount)
            logger.success(f"支付成功: {order_id}")
            return result
            
        except Exception as e:
            logger.exception(f"支付失败: {e}")
            raise
    
    def _call_payment_api(self, order_id: str, amount: float):
        logger.debug(f"调用支付 API: order={order_id}, amount={amount}")
        # 实际的支付逻辑
        return {"status": "success"}
    
    def __del__(self):
        # 清理时清除默认 tag（可选）
        logger.clear_default_tag()
```

**输出示例：**
```
INFO     | [payment] 开始处理支付: ORD-123
DEBUG    | [payment] 调用支付 API: order=ORD-123, amount=100.0
SUCCESS  | [payment] 支付成功: ORD-123
```

### 方式 2: 使用上下文管理器（临时设置）

适合需要临时设置默认 tag 的场景。

```python
from src.utils.log import logger
from contextlib import contextmanager

@contextmanager
def with_default_tag(tag: str):
    """临时设置默认 tag 的上下文管理器"""
    previous_tag = logger.get_default_tag()
    logger.set_default_tag(tag)
    try:
        yield
    finally:
        if previous_tag:
            logger.set_default_tag(previous_tag)
        else:
            logger.clear_default_tag()

# 使用示例
def process_order(order_id: str):
    with with_default_tag("order"):
        logger.info(f"开始处理订单: {order_id}")
        logger.debug("验证订单信息")
        logger.success("订单处理完成")
```

### 方式 3: 在方法级别设置（不推荐）

```python
from src.utils.log import logger

class DatabaseService:
    """数据库服务"""
    
    def query_user(self, user_id: int):
        # 方法开始时设置
        logger.set_default_tag("database")
        
        logger.info(f"查询用户: {user_id}")
        # ... 查询逻辑
        
        # 方法结束时清除（重要！）
        logger.clear_default_tag()
```

**注意**: 这种方式容易忘记清除，不推荐使用。

## 完整示例

### 示例 1: 数据库服务类

```python
from src.utils.log import logger

class DatabaseService:
    """数据库服务类"""
    
    def __init__(self, connection_string: str):
        # 设置类级别的默认 tag
        logger.set_default_tag("database")
        
        self.connection_string = connection_string
        logger.info("数据库服务初始化")
    
    def connect(self):
        logger.info("正在连接数据库...")
        try:
            # 连接逻辑
            logger.success("数据库连接成功")
        except Exception as e:
            logger.exception("数据库连接失败")
            raise
    
    def query(self, sql: str):
        logger.debug(f"执行查询: {sql}")
        # 查询逻辑
        return []
    
    def insert(self, table: str, data: dict):
        logger.info(f"插入数据到表 {table}")
        # 插入逻辑
        logger.success("数据插入成功")
    
    def close(self):
        logger.info("关闭数据库连接")
        logger.clear_default_tag()
```

**使用：**
```python
db = DatabaseService("postgresql://localhost/mydb")
db.connect()
db.query("SELECT * FROM users")
db.insert("users", {"name": "Alice"})
db.close()
```

**输出：**
```
INFO     | [database] 数据库服务初始化
INFO     | [database] 正在连接数据库...
SUCCESS  | [database] 数据库连接成功
DEBUG    | [database] 执行查询: SELECT * FROM users
INFO     | [database] 插入数据到表 users
SUCCESS  | [database] 数据插入成功
INFO     | [database] 关闭数据库连接
```

### 示例 2: WebSocket 连接类

```python
from src.utils.log import logger
from fastapi import WebSocket

class WebSocketConnection:
    """WebSocket 连接管理类"""
    
    def __init__(self, websocket: WebSocket, client_id: str):
        # 设置默认 tag
        logger.set_default_tag("websocket")
        
        self.websocket = websocket
        self.client_id = client_id
        logger.info(f"创建 WebSocket 连接: {client_id}")
    
    async def accept(self):
        await self.websocket.accept()
        logger.success(f"WebSocket 连接已建立: {self.client_id}")
    
    async def send(self, message: str):
        logger.debug(f"发送消息: {message[:50]}...")
        await self.websocket.send_text(message)
    
    async def receive(self) -> str:
        message = await self.websocket.receive_text()
        logger.debug(f"接收消息: {message[:50]}...")
        return message
    
    async def close(self):
        await self.websocket.close()
        logger.info(f"WebSocket 连接已关闭: {self.client_id}")
        logger.clear_default_tag()
```

### 示例 3: 认证服务类

```python
from src.utils.log import logger

class AuthService:
    """认证服务类"""
    
    def __init__(self):
        logger.set_default_tag("auth")
        logger.info("认证服务初始化")
    
    def login(self, username: str, password: str):
        logger.info(f"用户登录: {username}")
        
        try:
            # 验证用户
            user = self._validate_credentials(username, password)
            
            if user:
                logger.success(f"登录成功: {username}")
                return self._generate_token(user)
            else:
                logger.warning(f"登录失败: 用户名或密码错误 ({username})")
                return None
                
        except Exception as e:
            logger.exception(f"登录异常: {username}")
            raise
    
    def _validate_credentials(self, username: str, password: str):
        logger.debug(f"验证凭证: {username}")
        # 验证逻辑
        return {"id": 1, "username": username}
    
    def _generate_token(self, user: dict):
        logger.debug(f"生成令牌: {user['username']}")
        # 生成令牌逻辑
        return "token-123456"
    
    def logout(self, token: str):
        logger.info("用户登出")
        # 登出逻辑
        logger.success("登出成功")
```

## 覆盖默认 Tag

即使设置了默认 tag，仍然可以为单条日志指定不同的 tag：

```python
from src.utils.log import logger

class OrderService:
    """订单服务类"""
    
    def __init__(self):
        # 设置默认 tag 为 "order"
        logger.set_default_tag("order")
    
    def create_order(self, user_id: int, items: list):
        # 使用默认 tag "order"
        logger.info(f"创建订单: user={user_id}")
        
        # 覆盖默认 tag，使用 "database"
        logger.debug("查询用户信息", tag="database")
        
        # 覆盖默认 tag，使用 "payment"
        logger.info("处理支付", tag="payment")
        
        # 又回到默认 tag "order"
        logger.success("订单创建成功")
```

**输出：**
```
INFO     | [order] 创建订单: user=123
DEBUG    | [database] 查询用户信息
INFO     | [payment] 处理支付
SUCCESS  | [order] 订单创建成功
```

## 与 trace_id 结合使用

默认 tag 和 trace_id 可以完美配合：

```python
from src.utils.log import logger

class PaymentService:
    """支付服务类"""
    
    def __init__(self):
        logger.set_default_tag("payment")
    
    def process_payment(self, order_id: str, amount: float):
        # 为这次支付生成 trace_id
        trace_id = logger.set_trace_id()
        
        try:
            # 所有日志都会带上 [payment] tag 和 trace_id
            logger.info(f"开始处理支付: {order_id}")
            logger.debug(f"金额: {amount}")
            
            result = self._call_payment_api(order_id, amount)
            
            logger.success("支付成功")
            return result
            
        except Exception as e:
            logger.exception("支付失败")
            raise
        finally:
            logger.clear_trace_id()
    
    def _call_payment_api(self, order_id: str, amount: float):
        # 自动继承 trace_id 和默认 tag
        logger.debug("调用支付 API")
        return {"status": "success"}
```

**输出：**
```
INFO     | [trace_id=abc-123] [payment] 开始处理支付: ORD-456
DEBUG    | [trace_id=abc-123] [payment] 金额: 100.0
DEBUG    | [trace_id=abc-123] [payment] 调用支付 API
SUCCESS  | [trace_id=abc-123] [payment] 支付成功
```

## API 参考

### 设置默认 Tag

```python
logger.set_default_tag(tag: Optional[str] = None) -> None
```

设置默认 tag，用于类级别的日志标签。

**参数：**
- `tag`: 默认标签，如果为 `None` 则清除默认标签

**示例：**
```python
logger.set_default_tag("payment")  # 设置默认 tag
logger.set_default_tag(None)       # 清除默认 tag
```

### 清除默认 Tag

```python
logger.clear_default_tag() -> None
```

清除默认 tag。

**示例：**
```python
logger.clear_default_tag()
```

### 获取默认 Tag

```python
logger.get_default_tag() -> Optional[str]
```

获取当前的默认 tag。

**返回：**
- 当前的默认 tag，如果没有设置则返回 `None`

**示例：**
```python
current_tag = logger.get_default_tag()
print(f"当前默认 tag: {current_tag}")
```

## 最佳实践

### 1. 在 `__init__` 中设置，在 `__del__` 中清除

```python
class MyService:
    def __init__(self):
        logger.set_default_tag("my_service")
        logger.info("服务初始化")
    
    def __del__(self):
        logger.clear_default_tag()
```

### 2. 使用有意义的 tag 名称

```python
# ✅ 好的做法
logger.set_default_tag("payment")
logger.set_default_tag("database")
logger.set_default_tag("websocket")

# ❌ 不好的做法
logger.set_default_tag("service")  # 太泛化
logger.set_default_tag("class1")   # 无意义
```

### 3. 保持 tag 的一致性

在同一个类中，使用统一的 tag：

```python
class PaymentService:
    def __init__(self):
        # 统一使用 "payment"
        logger.set_default_tag("payment")
    
    def process_payment(self, order_id: str):
        logger.info("处理支付")  # [payment]
    
    def refund(self, order_id: str):
        logger.info("处理退款")  # [payment]
```

### 4. 需要时可以覆盖

```python
class OrderService:
    def __init__(self):
        logger.set_default_tag("order")
    
    def create_order(self, user_id: int):
        logger.info("创建订单")  # [order]
        
        # 数据库操作使用不同的 tag
        logger.debug("查询用户", tag="database")  # [database]
        
        # 支付操作使用不同的 tag
        logger.info("处理支付", tag="payment")  # [payment]
        
        logger.success("订单创建成功")  # [order]
```

### 5. 多线程/异步安全

`contextvars` 确保了默认 tag 在多线程和异步环境中的安全性：

```python
import asyncio
from src.utils.log import logger

class AsyncService:
    def __init__(self):
        logger.set_default_tag("async_service")
    
    async def task1(self):
        logger.info("任务 1 开始")
        await asyncio.sleep(1)
        logger.info("任务 1 完成")
    
    async def task2(self):
        logger.info("任务 2 开始")
        await asyncio.sleep(1)
        logger.info("任务 2 完成")

# 并发执行，每个任务都会正确使用默认 tag
service = AsyncService()
await asyncio.gather(service.task1(), service.task2())
```

## 常见问题

### Q: 默认 tag 会影响其他类吗？

A: 不会。`contextvars` 确保了每个上下文（线程/协程）都有独立的默认 tag。

### Q: 可以嵌套设置默认 tag 吗？

A: 可以，但新的设置会覆盖旧的。建议在需要时保存旧值：

```python
# 保存旧的默认 tag
old_tag = logger.get_default_tag()

# 设置新的默认 tag
logger.set_default_tag("new_tag")

# 使用新 tag 记录日志
logger.info("使用新 tag")

# 恢复旧的默认 tag
if old_tag:
    logger.set_default_tag(old_tag)
else:
    logger.clear_default_tag()
```

### Q: 忘记清除默认 tag 会怎样？

A: 默认 tag 会一直生效，直到被清除或覆盖。建议在类的 `__del__` 方法中清除。

### Q: 默认 tag 和传入的 tag 哪个优先？

A: 传入的 tag 优先。如果同时设置了默认 tag 和传入 tag，会使用传入的 tag。

```python
logger.set_default_tag("default")
logger.info("使用默认 tag")        # [default]
logger.info("覆盖", tag="custom")  # [custom]
```

## 迁移指南

### 从旧代码迁移

**之前：**
```python
class PaymentService:
    def process_payment(self, order_id: str):
        logger.info("开始处理", tag="payment")
        logger.debug("验证订单", tag="payment")
        logger.success("处理完成", tag="payment")
```

**现在：**
```python
class PaymentService:
    def __init__(self):
        logger.set_default_tag("payment")
    
    def process_payment(self, order_id: str):
        logger.info("开始处理")      # 自动使用 "payment"
        logger.debug("验证订单")     # 自动使用 "payment"
        logger.success("处理完成")   # 自动使用 "payment"
```

## 总结

✅ **优点：**
- 减少重复代码
- 提高代码可读性
- 保持日志一致性
- 支持多线程/异步

✅ **适用场景：**
- 类中有大量日志记录
- 所有日志使用相同的 tag
- 需要保持日志分类一致性

✅ **注意事项：**
- 记得在适当时候清除默认 tag
- 可以随时覆盖默认 tag
- 与 trace_id 完美配合

---

**更新日期**: 2025-12-26
**版本**: 1.0

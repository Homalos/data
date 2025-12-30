# 开发文档

## 目录

- [项目概述](#项目概述)
- [架构设计](#架构设计)
- [开发环境搭建](#开发环境搭建)
- [代码结构](#代码结构)
- [开发指南](#开发指南)
- [测试指南](#测试指南)
- [常见问题](#常见问题)

## 项目概述

homalos-webctp 是一个基于 FastAPI 和 WebSocket 的 CTP 接口服务，将传统的 CTP API 封装为 WebSocket 接口，方便 Web 应用接入期货交易系统。

### 技术栈

- **Python 3.10+**: 编程语言
- **FastAPI**: Web 框架
- **WebSocket**: 实时通信协议
- **anyio**: 异步 I/O 库
- **openctp-ctp**: CTP Python 绑定
- **PyYAML**: 配置文件解析
- **CSV**: 数据存储格式

### 主要功能

- 行情服务（端口 8080）
- 交易服务（端口 8081）
- Tick 数据存储（CSV 格式）
- K线数据生成和存储
- 合约信息管理

## 架构设计

### 整体架构

```
┌─────────────┐
│   Client    │ (浏览器/应用)
└──────┬──────┘
       │ WebSocket
┌──────▼──────────────────────┐
│   FastAPI Application       │
│  (apps/md_app.py|td_app.py) │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│   Service Layer             │
│  (services/base_client.py)  │
│  - 异步/同步边界处理           │
│  - 消息队列管理               │
│  - 请求路由                  │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│   CTP Client Layer          │
│  (clients/md|td_client.py)  │
│  - CTP API 封装              │
│  - 回调处理                  │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│   Storage Layer             │
│  (storage/csv_*.py)         │
│  - CSV Tick 存储             │
│  - CSV K线 存储              │
│  - 合约信息管理              │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│   CTP API (openctp-ctp)     │
└─────────────────────────────┘
```

### 数据存储架构

```
data/
├── ticks/                    # Tick 数据目录
│   └── {YYYYMMDD}/          # 按日期分目录
│       └── {instrument}.csv  # 按合约分文件
├── klines/                   # K线数据目录
│   └── {period}/            # 按周期分目录
│       └── {instrument}.csv  # 按合约分文件
└── instruments.json          # 合约信息缓存
```

### 核心设计模式

#### 1. 模板方法模式 (BaseClient)

`BaseClient` 定义了客户端的通用流程，子类实现特定的 CTP 客户端创建逻辑：

```python
class BaseClient(ABC):
    async def start(self, user_id, password):
        # 通用启动流程
        self._client = self._create_ctp_client(user_id, password)
        # ...
    
    @abstractmethod
    def _create_ctp_client(self, user_id, password):
        # 子类实现具体的客户端创建
        pass
```

#### 2. 异步/同步边界处理

CTP API 是同步的，WebSocket 是异步的，通过 `anyio.to_thread.run_sync` 处理边界：

```python
# 在异步上下文中调用同步的 CTP API
await anyio.to_thread.run_sync(self._client.connect)
```

#### 3. 消息队列模式

使用队列解耦 CTP 回调和 WebSocket 发送：

```
CTP Callback → Queue → Background Task → WebSocket Send
```

## 开发环境搭建

### 1. 克隆项目

```bash
git clone https://github.com/Homalos/homalos-webctp.git
cd homalos-webctp
```

### 2. 安装依赖

**使用 uv (推荐)**

```bash
# 同步依赖
uv sync
```

**使用 pip**

```bash
pip install -e .
```

### 3. 配置文件

复制示例配置并修改：

```bash
cp config/config.sample.yaml config/config_md.yaml
cp config/config.sample.yaml config/config_td.yaml
```

编辑配置文件，填入正确的信息：

```yaml
# config/config_md.yaml
MdFrontAddress: tcp://182.254.243.31:40011
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
Port: 8080
Host: 127.0.0.1
LogLevel: INFO

# 存储配置
Storage:
  Enabled: true
  Type: csv
  CSV:
    BasePath: ./data/ticks
    FlushInterval: 0.5
    BatchSize: 100
```

### 4. 环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

填入账号信息：

```bash
CTP_USER_ID=你的账号
CTP_PASSWORD=你的密码
```

### 5. 启动服务

```bash
# 行情服务
python main.py --config=./config/config_md.yaml --app_type=md

# 交易服务
python main.py --config=./config/config_td.yaml --app_type=td
```

## 代码结构

### 目录说明

```
homalos-webctp/
├── src/
│   ├── apps/                   # 应用入口
│   │   ├── __init__.py
│   │   ├── md_app.py          # 行情服务 FastAPI 应用
│   │   └── td_app.py          # 交易服务 FastAPI 应用
│   │
│   ├── clients/                # CTP 客户端封装
│   │   ├── __init__.py
│   │   ├── md_client.py       # 行情客户端 (继承 CThostFtdcMdSpi)
│   │   └── td_client.py       # 交易客户端 (继承 CThostFtdcTraderSpi)
│   │
│   ├── services/               # 服务层
│   │   ├── __init__.py
│   │   ├── base_client.py     # 客户端基类 (抽象类)
│   │   ├── md_client.py       # 行情服务 (继承 BaseClient)
│   │   ├── td_client.py       # 交易服务 (继承 BaseClient)
│   │   └── connection.py      # WebSocket 连接管理
│   │
│   ├── storage/                # 存储层
│   │   ├── __init__.py
│   │   ├── csv_tick_storage.py    # CSV Tick 存储
│   │   ├── csv_kline_storage.py   # CSV K线 存储
│   │   ├── kline_builder.py       # K线生成器
│   │   ├── kline_period.py        # K线周期定义
│   │   ├── instrument_manager.py  # 合约管理器
│   │   └── storage_helper.py      # 存储辅助函数
│   │
│   ├── constants/              # 常量定义
│   │   ├── __init__.py
│   │   ├── call_errors.py     # 错误码定义
│   │   └── constant.py        # 消息类型常量
│   │
│   ├── model/                  # 数据模型
│   │   ├── __init__.py
│   │   └── request.py         # 请求数据模型
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── config.py          # 配置管理
│       ├── ctp_object_helper.py  # CTP 对象辅助函数
│       └── math_helper.py     # 数学辅助函数
│
├── config/                     # 配置文件目录
│   ├── config.sample.yaml     # 示例配置
│   ├── config_md.yaml         # 行情服务配置
│   └── config_td.yaml         # 交易服务配置
│
├── data/                       # 数据目录
│   ├── ticks/                 # Tick 数据
│   ├── klines/                # K线数据
│   └── instruments.json       # 合约信息
│
├── docs/                       # 文档
│   ├── QUICK_START.md         # 快速开始
│   ├── development_CN.md      # 开发文档 (本文件)
│   └── troubleshooting_CN.md  # 故障排查
│
├── scripts/                    # 脚本
│   ├── auto_login_td.py       # 自动登录脚本
│   ├── query_tick_csv.py      # 查询 Tick 数据
│   └── query_kline_csv.py     # 查询 K线 数据
│
├── tests/                      # 测试
├── main.py                     # 主入口
├── pyproject.toml              # 项目配置和依赖
└── README.md                   # 项目说明
```

### 关键文件说明

#### `src/services/base_client.py`

抽象基类，提供：
- 客户端生命周期管理 (start/stop/run)
- 消息队列处理
- 异步/同步边界处理
- 公共属性和方法

#### `src/services/td_client.py` & `src/services/md_client.py`

具体的服务实现：
- 继承 `BaseClient`
- 实现抽象方法
- 处理特定的业务逻辑
- 请求验证和路由

#### `src/clients/td_client.py` & `src/clients/md_client.py`

CTP API 封装：
- 继承 CTP Spi 类
- 实现回调方法
- 封装 API 调用
- 数据转换

#### `src/storage/csv_tick_storage.py`

CSV Tick 存储：
- 按日期和合约分文件存储
- 批量写入优化
- 自动刷新机制

#### `src/storage/kline_builder.py`

K线生成器：
- 从 Tick 数据生成 K线
- 支持多周期（1m, 5m, 15m, 30m, 60m, 1d）
- 实时更新

## 开发指南

### 添加新的 API 接口

以添加一个新的查询接口为例：

#### 1. 在 `constants/constant.py` 添加常量

```python
class TdConstant(CommonConstant):
    # Request Method
    ReqQryNewApi = "ReqQryNewApi"
    
    # Response Type
    OnRspQryNewApi = "RspQryNewApi"
    
    # Request/Response Field
    QryNewApi = "QryNewApi"
    NewApiData = "NewApiData"
```

#### 2. 在 `clients/td_client.py` 添加 API 封装

```python
def reqQryNewApi(self, request: dict[str, Any]) -> None:
    req, requestId = CTPObjectHelper.extract_request(
        request, 
        Constant.QryNewApi, 
        tdapi.CThostFtdcQryNewApiField
    )
    ret = self._api.ReqQryNewApi(req, requestId)
    self.method_called(Constant.OnRspQryNewApi, ret)

def OnRspQryNewApi(self, pData, pRspInfo, nRequestID, bIsLast):
    response = CTPObjectHelper.build_response_dict(
        Constant.OnRspQryNewApi, 
        pRspInfo, 
        nRequestID, 
        bIsLast
    )
    if pData:
        response[Constant.NewApiData] = {
            "Field1": pData.Field1,
            "Field2": pData.Field2,
        }
    self.rsp_callback(response)
```

#### 3. 在 `services/td_client.py` 注册方法

```python
def _init_call_map(self):
    # ... 其他映射
    self._call_map[Constant.ReqQryNewApi] = self._client.reqQryNewApi
```

### 错误处理最佳实践

#### 1. 使用统一的错误码

```python
from constants import CallError

# 返回错误
response = {
    "MsgType": message_type,
    "RspInfo": CallError.get_rsp_info(404)
}
```

#### 2. 记录详细日志

```python
import logging

# 使用合适的日志级别
logging.debug("详细的调试信息")
logging.info("一般信息")
logging.warning("警告信息")
logging.error("错误信息")
logging.exception("异常信息，包含堆栈")
```

### 数据存储

#### CSV 存储格式

**Tick 数据** (`data/ticks/{YYYYMMDD}/{instrument}.csv`):
```csv
datetime,last_price,volume,open_interest,bid_price1,ask_price1,bid_volume1,ask_volume1
2025-12-30T09:00:00.500+08:00,4500.0,100,50000,4499.0,4501.0,10,15
```

**K线数据** (`data/klines/{period}/{instrument}.csv`):
```csv
datetime,open,high,low,close,volume,open_interest
2025-12-30T09:00:00+08:00,4500.0,4510.0,4495.0,4505.0,1000,50000
```

#### 时间格式

统一使用 ISO 8601 东八区格式：`YYYY-MM-DDTHH:mm:ss.sss+08:00`

#### 浮点数精度

使用 `repr()` 保持原始精度：

```python
# 正确
price_str = repr(tick.last_price)  # "4500.5"

# 错误（可能丢失精度）
price_str = str(tick.last_price)   # "4500.5"
```

## 测试指南

### 单元测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_storage.py

# 显示详细输出
pytest -v
```

### 集成测试

使用 SimNow 仿真环境进行测试：

1. 注册 SimNow 账号
2. 配置测试环境
3. 运行服务
4. 使用 WebSocket 客户端测试

### 测试工具

- **pytest**: 单元测试框架
- **wscat**: WebSocket 命令行工具
- **浏览器开发者工具**: WebSocket 调试

## 常见问题

### Q: 如何处理 CTP 的流控限制？

A: CTP 有请求频率限制，建议：
- 控制请求频率
- 实现请求队列
- 处理流控错误码 (-2, -3)

### Q: WebSocket 断开后如何处理？

A: 
- 客户端实现自动重连
- 服务端在 `connection.py` 中处理 `WebSocketDisconnect`
- 清理资源，释放 CTP 连接

### Q: 如何调试 CTP 回调？

A:
- 设置日志级别为 DEBUG
- 在回调方法中添加日志
- 使用 CTP 的流文件查看详细信息

### Q: 生产环境部署注意事项？

A:
- 充分测试后再部署
- 配置合适的日志级别
- 监控服务状态
- 实现故障恢复机制
- 注意 CTP 的连接数限制

## 贡献指南

欢迎贡献代码！请遵循以下流程：

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

### 代码审查要点

- 代码风格符合 PEP 8
- 添加必要的类型注解
- 包含适当的错误处理
- 更新相关文档
- 通过测试

## 许可证

请参考项目根目录的 LICENSE 文件。

## 联系方式

- 项目主页: https://github.com/Homalos/homalos-webctp
- 邮箱: donnymoving@gmail.com
- QQ群: 446042777

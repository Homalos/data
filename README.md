# Homalos Data

期货行情数据采集与存储系统，基于CTP接口实现实时行情订阅、Tick数据存储和K线合成。

## 功能特性

- 连接SimNow等CTP行情服务器
- 订阅全市场期货合约行情
- 实时存储Tick数据到CSV文件
- 实时合成多周期K线（1m, 3m, 5m, 10m, 15m, 30m, 60m, 日线）
- WebSocket服务端，支持多客户端连接

## 项目结构

```
homalos-data/
├── config/                 # 配置文件
│   ├── config_md.yaml      # 行情服务配置
│   └── config_td.yaml      # 交易服务配置
├── data/                   # 数据存储目录
│   ├── instruments.json    # 合约信息缓存
│   ├── ticks/              # Tick数据 (按交易日/合约)
│   └── klines/             # K线数据 (按交易日/周期/合约)
├── scripts/                # 脚本工具
├── src/                    # 源代码
│   ├── apps/               # FastAPI应用
│   ├── gateway/            # CTP网关
│   ├── services/           # 服务层
│   ├── storage/            # 存储引擎
│   └── utils/              # 工具类
└── tests/                  # 测试代码
```

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
CTP_USER_ID=你的账号
CTP_PASSWORD=你的密码
```

### 3. 运行更新合约信息脚本和订阅存储行情脚本

```bash
python scripts/start_update_instruments
python scripts/store_market_data.py
```

## 数据存储格式

### Tick数据

存储路径: `data/ticks/{交易日}/{合约代码}.csv`

| 字段 | 说明 |
|------|------|
| timestamp | ISO 8601时间戳 |
| trading_day | 交易日 |
| instrument_id | 合约代码 |
| last_price | 最新价 |
| volume | 成交量 |
| turnover | 成交额 |
| open_interest | 持仓量 |
| bid_price1~5 | 买一~买五价 |
| bid_volume1~5 | 买一~买五量 |
| ask_price1~5 | 卖一~卖五价 |
| ask_volume1~5 | 卖一~卖五量 |
| ... | 其他字段 |

### K线数据

存储路径: `data/klines/{交易日}/{周期}/{合约代码}.csv`

| 字段 | 说明 |
|------|------|
| timestamp | ISO 8601时间戳 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 成交量 |
| turnover | 成交额 |
| open_interest | 持仓量 |
| tick_count | Tick数量 |

### 时间格式

所有时间字段统一使用 **ISO 8601** 国际标准格式：

```
YYYY-MM-DDTHH:mm:ss.sssZ
```

示例：
- Tick时间: `2025-12-27T09:30:15.500Z`（毫秒精度）
- K线时间: `2025-12-27T09:30:00.000Z`（秒精度）

## 配置说明

### config_md.yaml

```yaml
# CTP前置地址
# TdFrontAddress: tcp://182.254.243.31:40001 # 7x24交易前置地址
# MdFrontAddress: tcp://182.254.243.31:40011 # 7x24行情前置地址
TdFrontAddress: tcp://182.254.243.31:30001 # 交易前置地址
MdFrontAddress: tcp://182.254.243.31:30012 # 行情前置地址
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
UserProductInfo: ""

# WebSocket服务
Host: 127.0.0.1      # the bind ip address, default 127.0.0.1
Port: 8080         # the listening port, default 8081
LogLevel: INFO     # NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL
HeartbeatInterval: 30.0  # WebSocket heartbeat interval in seconds, default 30.0
HeartbeatTimeout: 60.0   # WebSocket heartbeat timeout in seconds, default 60.0

# 存储配置
Storage:
  Enabled: true
  Type: csv  # 存储类型: csv

  # CSV配置
  CSV:
    BasePath: ./data/ticks  # 基础存储路径
    FlushInterval: 1.0      # 刷新间隔（秒）
    BatchSize: 100          # 批量写入大小
  
  # 合约管理配置
  Instruments:
    CachePath: ./data/instruments.json
    AutoUpdate: true
    UpdateInterval: 86400  # 每天更新一次（秒）
  
  # K线配置
  KLine:
    Enabled: true
    Periods: ["1m", "3m", "5m", "10m", "15m", "30m", "60m", "1d"]

# Redis缓存配置
Cache:
  Enabled: false

# 性能监控配置
Metrics:
  Enabled: true
  ReportInterval: 60
  LatencyBuckets: [10, 50, 100, 200, 500, 1000]
  SampleRate: 1.0
  LatencyWarningThresholdMs: 100.0
  CacheHitRateWarningThreshold: 50.0
  CpuWarningThreshold: 80.0
  MemoryWarningThreshold: 80.0

# 测试配置
Test:
  SubscribeLimit: 50  # 订阅合约数量，0表示订阅所有
  ListenDuration: 0   # 监听时长（秒），0表示持续监听直到Ctrl+C
```

### config_td.yaml

```yaml
# CTP前置地址
# TdFrontAddress: tcp://182.254.243.31:40001 # 7x24交易前置地址
# MdFrontAddress: tcp://182.254.243.31:40011 # 7x24行情前置地址
TdFrontAddress: tcp://182.254.243.31:30001 # 交易前置地址
MdFrontAddress: tcp://182.254.243.31:30012 # 行情前置地址
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
UserProductInfo: ""

# WebSocket服务
Host: 127.0.0.1      # the bind ip address, default 127.0.0.1
Port: 8081         # the listening port, default 8080
LogLevel: INFO     # NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL
HeartbeatInterval: 30.0  # WebSocket heartbeat interval in seconds, default 30.0
HeartbeatTimeout: 60.0   # WebSocket heartbeat timeout in seconds, default 60.0

# 存储配置
Storage:
  Enabled: true
  Instruments:
    CachePath: data/instruments.json

# 测试配置
Test:
  SubscribeLimit: 50  # 订阅合约数量，0表示订阅所有
  ListenDuration: 0   # 监听时长（秒），0表示持续监听直到Ctrl+C
```

## 脚本说明

### store_market_data.py

订阅并存储期货合约的Tick数据和K线数据。

功能：
1. 从 `data/instruments.json` 加载合约列表
2. 连接行情WebSocket服务
3. 订阅所有期货合约
4. 实时存储Tick数据到CSV
5. 实时合成K线并存储到CSV

运行：
```bash
python scripts/store_market_data.py
```

或使用批处理：
```bash
start_store_market_data.bat
```

## License

BSD 3-Clause License
# WebSocket消息格式参考

## 重要提示

⚠️ **消息类型字段名是 `MsgType` 而不是 `MessageType`**

这是系统内部使用的字段名，所有WebSocket消息都必须使用 `MsgType`。

---

## 登录请求

### 请求格式

```json
{
  "MsgType": "ReqUserLogin",
  "RequestID": 0,
  "ReqUserLogin": {
    "UserID": "your_user_id",
    "Password": "your_password"
  }
}
```

**重要说明：**
- ✅ `MsgType` 必须在顶层
- ✅ `RequestID` 必须在顶层（通常设为 0）
- ✅ `ReqUserLogin` 对象包含用户名和密码

### 响应格式

**成功：**
```json
{
  "MsgType": "OnRspUserLogin",
  "RspInfo": {
    "ErrorID": 0,
    "ErrorMsg": ""
  },
  "RspUserLogin": {
    "TradingDay": "20251223",
    "LoginTime": "09:30:00",
    "FrontID": 1,
    "SessionID": 12345678,
    "MaxOrderRef": "1",
    "BrokerID": "9999",
    "UserID": "160219"
  },
  "RequestID": 0,
  "IsLast": true
}
```

**失败：**
```json
{
  "MsgType": "OnRspUserLogin",
  "RspInfo": {
    "ErrorID": 3,
    "ErrorMsg": "CTP:不合法的登录"
  },
  "RspUserLogin": {},
  "RequestID": 0,
  "IsLast": true
}
```

---

## 查询合约请求

### 请求格式

```json
{
  "MsgType": "ReqQryInstrument",
  "ReqQryInstrument": {
    "InstrumentID": "",
    "RequestID": 0
  }
}
```

**说明：**
- `InstrumentID` 为空表示查询所有合约
- 指定合约代码可查询单个合约，如 `"rb2505"`
- `RequestID` 通常设为 0

### 响应格式

```json
{
  "MsgType": "OnRspQryInstrument",
  "RspInfo": {
    "ErrorID": 0,
    "ErrorMsg": ""
  },
  "Instrument": {
    "InstrumentID": "rb2505",
    "InstrumentName": "螺纹钢2505",
    "ExchangeID": "SHFE",
    "ProductID": "rb",
    "VolumeMultiple": 10,
    "PriceTick": 1.0,
    "CreateDate": "20240101",
    "ExpireDate": "20250515",
    "IsTrading": 1
  },
  "RequestID": 0,
  "IsLast": false
}
```

**说明：**
- `IsLast` 为 `true` 表示这是最后一条响应
- 查询所有合约时会收到多条响应

---

## 心跳消息

系统会自动发送心跳消息来保持连接活跃。

### Ping消息

```json
{
  "MsgType": "Ping"
}
```

### Pong消息

```json
{
  "MsgType": "Pong"
}
```

**说明：**
- 心跳消息由系统自动处理
- 客户端应该忽略这些消息
- 不需要手动回复心跳

---

## 订阅行情请求

### 请求格式

```json
{
  "MsgType": "ReqSubMarketData",
  "ReqSubMarketData": {
    "InstrumentID": ["rb2505", "au2506"]
  }
}
```

### 响应格式

```json
{
  "MsgType": "OnRspSubMarketData",
  "RspInfo": {
    "ErrorID": 0,
    "ErrorMsg": ""
  },
  "SpecificInstrument": {
    "InstrumentID": "rb2505"
  },
  "RequestID": 0,
  "IsLast": true
}
```

---

## 行情推送

### 推送格式

```json
{
  "MsgType": "OnRtnDepthMarketData",
  "DepthMarketData": {
    "InstrumentID": "rb2505",
    "LastPrice": 3500.0,
    "Volume": 12345,
    "Turnover": 43212500.0,
    "OpenInterest": 234567.0,
    "UpdateTime": "09:30:15",
    "UpdateMillisec": 500,
    "BidPrice1": 3499.0,
    "BidVolume1": 100,
    "AskPrice1": 3501.0,
    "AskVolume1": 150,
    "TradingDay": "20251223"
  }
}
```

---

## 常见错误

### 错误1：使用了错误的字段名

❌ **错误：**
```json
{
  "MessageType": "ReqUserLogin",  // 错误！
  ...
}
```

✅ **正确：**
```json
{
  "MsgType": "ReqUserLogin",  // 正确！
  ...
}
```

### 错误2：缺少必需字段

❌ **错误：**
```json
{
  "MsgType": "ReqUserLogin"
  // 缺少 ReqUserLogin 字段
}
```

✅ **正确：**
```json
{
  "MsgType": "ReqUserLogin",
  "ReqUserLogin": {
    "UserID": "160219",
    "Password": "password",
    "BrokerID": "9999"
  }
}
```

---

## 字段名对照表

| 显示名称 | 实际字段名 | 说明 |
|---------|-----------|------|
| MessageType | `MsgType` | 消息类型 |
| ResponseInfo | `RspInfo` | 响应信息 |
| RequestID | `RequestID` | 请求ID |
| IsLast | `IsLast` | 是否最后一条 |

---

## 调试技巧

### 1. 打印发送的消息

```python
import json

message = {
    "MsgType": "ReqUserLogin",
    "ReqUserLogin": {...}
}

print("发送消息:")
print(json.dumps(message, indent=2, ensure_ascii=False))
```

### 2. 打印接收的消息

```python
response = await websocket.recv()
response_data = json.loads(response)

print("接收消息:")
print(json.dumps(response_data, indent=2, ensure_ascii=False))
```

### 3. 检查字段名

```python
# 检查是否使用了正确的字段名
if "MsgType" in response_data:
    print("✅ 使用了正确的字段名")
else:
    print("❌ 字段名错误")
    print(f"可用字段: {list(response_data.keys())}")
```

---

## 参考代码

### Python WebSocket客户端示例

```python
import asyncio
import json
import websockets

async def login_example():
    """登录示例"""
    url = "ws://127.0.0.1:8081/"
    
    async with websockets.connect(url) as ws:
        # 发送登录请求
        login_request = {
            "MsgType": "ReqUserLogin",  # 顶层字段
            "RequestID": 0,              # 顶层字段
            "ReqUserLogin": {
                "UserID": "160219",
                "Password": "your_password"
            }
        }
        
        await ws.send(json.dumps(login_request))
        
        # 接收响应
        response = await ws.recv()
        response_data = json.loads(response)
        
        # 检查响应
        if response_data.get("MsgType") == "OnRspUserLogin":
            rsp_info = response_data.get("RspInfo", {})
            if rsp_info.get("ErrorID") == 0:
                print("✅ 登录成功")
            else:
                print(f"❌ 登录失败: {rsp_info.get('ErrorMsg')}")

if __name__ == "__main__":
    asyncio.run(login_example())
```

---

**更新时间**: 2025-12-23  
**维护者**: Kiro AI Assistant

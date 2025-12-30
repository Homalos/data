# 故障排查指南

**版本**: 2.0  
**更新日期**: 2025-12-30

## 目录

- [概述](#概述)
- [故障排查流程](#故障排查流程)
- [连接问题](#连接问题)
- [性能问题](#性能问题)
- [配置问题](#配置问题)
- [日志分析](#日志分析)
- [错误代码参考](#错误代码参考)
- [获取帮助](#获取帮助)

## 概述

本指南帮助您快速诊断和解决 homalos-webctp 系统中的常见问题。

### 故障分类

**连接问题**:
- WebSocket 连接失败
- CTP 连接失败

**性能问题**:
- 延迟过高
- 吞吐量低
- 系统资源占用高

**配置问题**:
- 配置文件错误
- 环境变量问题
- 权限问题

### 诊断原则

1. **查看日志**: 首先查看错误日志
2. **检查配置**: 确认配置文件正确
3. **验证连接**: 测试各个连接是否正常
4. **监控指标**: 查看性能报告和告警
5. **隔离问题**: 逐个排查可能的原因
6. **记录过程**: 记录排查步骤和结果

### 常用工具

- **日志文件**: `logs/webctp.log`, `logs/webctp_error.log`
- **性能报告**: 日志中的性能指标报告
- **系统监控**: Windows 性能监视器 / Linux top/htop
- **网络工具**: ping, telnet, curl


## 故障排查流程

### 快速诊断流程

```
1. 服务是否启动？
   ├─ 否 → 检查启动错误
   └─ 是 → 继续

2. 能否连接 WebSocket？
   ├─ 否 → 检查网络和端口
   └─ 是 → 继续

3. 能否登录？
   ├─ 否 → 检查账号和 CTP 连接
   └─ 是 → 继续

4. 功能是否正常？
   ├─ 否 → 检查具体功能错误
   └─ 是 → 检查性能问题

5. 性能是否达标？
   ├─ 否 → 查看性能报告和告警
   └─ 是 → 系统正常
```

### 详细排查步骤

#### 步骤 1: 检查服务状态

**检查服务是否运行**:
```bash
# Windows
tasklist | findstr python

# Linux
ps aux | grep python
```

**检查端口是否监听**:
```bash
# Windows
netstat -ano | findstr :8080
netstat -ano | findstr :8081

# Linux
netstat -tlnp | grep 8080
netstat -tlnp | grep 8081
```

**预期结果**:
- 应该看到 python 进程
- 端口 8080 (MD) 和 8081 (TD) 应该在监听状态

#### 步骤 2: 检查日志

**查看最新日志**:
```bash
# Windows PowerShell
Get-Content logs\webctp.log -Tail 50

# Linux
tail -50 logs/webctp.log
```

**查看错误日志**:
```bash
# Windows PowerShell
Get-Content logs\webctp_error.log -Tail 50

# Linux
tail -50 logs/webctp_error.log
```

**关注关键信息**:
- 启动信息
- 连接状态
- 错误消息
- 告警信息

#### 步骤 3: 测试连接

**测试 WebSocket 连接**:
```python
import asyncio
import websockets

async def test_connection():
    try:
        async with websockets.connect("ws://localhost:8080/ws") as ws:
            print("WebSocket 连接成功")
    except Exception as e:
        print(f"WebSocket 连接失败: {e}")

asyncio.run(test_connection())
```

**测试 CTP 连接**:
- 查看日志中的 CTP 连接状态
- 确认前置地址可访问

#### 步骤 4: 检查配置

**验证配置文件**:
```bash
# 检查配置文件语法
python -c "import yaml; yaml.safe_load(open('config/config_md.yaml'))"
```

**检查关键配置项**:
- 前置地址是否正确
- 端口是否冲突
- 日志级别是否合适

#### 步骤 5: 查看性能指标

**查看性能报告**:
```bash
# 查看最近的性能报告
grep "性能指标报告" logs/webctp.log -A 30 | tail -35
```

**查看告警**:
```bash
# 查看所有告警
grep "⚠️" logs/webctp.log
```


## 连接问题

### 问题 1: WebSocket 连接失败

#### 症状
- 客户端无法连接到 WebSocket
- 连接超时或被拒绝
- 浏览器显示 "WebSocket connection failed"

#### 可能原因

**1. 服务未启动**
```bash
# 检查服务是否运行
tasklist | findstr python
```

**解决方案**: 启动服务
```bash
.venv\Scripts\activate
python main.py --config=./config/config_md.yaml --app_type=md
```

**2. 端口被占用**
```bash
# 检查端口占用
netstat -ano | findstr :8080
```

**解决方案**: 
- 终止占用端口的进程
- 或修改配置文件中的端口号

**3. 防火墙阻止**

**解决方案**: 
```bash
# Windows 防火墙添加规则
netsh advfirewall firewall add rule name="WebCTP MD" dir=in action=allow protocol=TCP localport=8080
netsh advfirewall firewall add rule name="WebCTP TD" dir=in action=allow protocol=TCP localport=8081
```

**4. 绑定地址错误**

**检查配置**:
```yaml
Host: 127.0.0.1  # 只允许本地连接
# 或
Host: 0.0.0.0    # 允许所有网络接口
```

#### 日志示例

**正常启动**:
```
INFO | Application startup complete
INFO | Uvicorn running on http://127.0.0.1:8080
```

**端口占用**:
```
ERROR | [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8080): 通常每个套接字地址(协议/网络地址/端口)只允许使用一次。
```

### 问题 2: CTP 连接失败

#### 症状
- 登录失败
- 无法订阅行情
- 无法提交订单
- 日志显示 CTP 连接错误

#### 可能原因

**1. 前置地址错误**

**检查配置**:
```yaml
TdFrontAddress: tcp://182.254.243.31:40001
MdFrontAddress: tcp://182.254.243.31:40011
```

**解决方案**: 
- 确认前置地址正确
- SimNow 7x24: tcp://182.254.243.31:40001 (交易), tcp://182.254.243.31:40011 (行情)
- SimNow 标准: tcp://180.168.146.187:10130 (交易), tcp://180.168.146.187:10131 (行情)

**2. 账号密码错误**

**检查配置**:
```yaml
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
```

**解决方案**: 
- 确认 BrokerID 正确（SimNow 为 "9999"）
- 确认 AuthCode 和 AppID 正确
- 检查用户名和密码

**3. 网络连接问题**

**测试连接**:
```bash
# Windows
telnet 182.254.243.31 40001

# 或使用 PowerShell
Test-NetConnection -ComputerName 182.254.243.31 -Port 40001
```

**4. CTP 服务器维护**

**解决方案**: 
- 查看 SimNow 官网公告
- 等待服务器恢复
- 尝试使用备用前置地址

#### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 3 | CTP:不合法的登录 | 检查用户名密码 |
| 7 | CTP:还没有初始化 | 等待初始化完成 |
| 63 | CTP:网络连接失败 | 检查网络和前置地址 |
| 90 | CTP:认证失败 | 检查 AuthCode 和 AppID |

#### 日志示例

**连接成功**:
```
INFO | CTP 前置连接成功
INFO | 用户登录成功: UserID=123456
```

**连接失败**:
```
ERROR | CTP 前置连接失败: 网络连接失败
ERROR | 用户登录失败: ErrorID=3, ErrorMsg=CTP:不合法的登录
```

### 问题 3: 心跳超时

#### 症状
- WebSocket 连接频繁断开
- 日志显示 "心跳超时"
- 客户端需要频繁重连

#### 可能原因

**1. 网络不稳定**

**解决方案**: 
- 使用更稳定的网络
- 缩短心跳间隔

**配置调整**:
```yaml
HeartbeatInterval: 15.0  # 从 30 秒缩短到 15 秒
HeartbeatTimeout: 30.0   # 从 60 秒缩短到 30 秒
```

**2. 客户端未响应心跳**

**解决方案**: 
- 确保客户端正确处理心跳消息
- 客户端应该响应 ping 消息

**3. 服务器负载过高**

**解决方案**: 
- 检查系统资源使用
- 优化性能
- 增加服务器资源


## 性能问题

### 问题 4: 延迟过高

#### 症状
- 订单延迟 P95 > 200 ms
- 行情延迟 > 100 ms
- 频繁收到延迟告警

#### 可能原因和解决方案

**1. 系统资源不足**

**检查**:
```bash
# 查看系统资源
grep "系统资源" logs/webctp.log | tail -5
```

**解决方案**:
- CPU > 80%: 优化代码、增加 CPU 资源
- 内存 > 80%: 清理缓存、增加内存
- 降低采样率减少监控开销

**2. 网络延迟高**

**检查**:
```bash
# 测试网络延迟
ping 182.254.243.31
```

**解决方案**:
- 使用更快的网络连接
- 选择地理位置近的前置服务器
- 考虑使用专线

**3. CTP API 响应慢**

**特征**:
- 延迟主要来自 CTP 回调
- 其他操作正常

**解决方案**:
- 这是外部因素，难以优化
- 考虑使用生产环境（比 SimNow 快）
- 实施请求合并策略

**4. 序列化开销大**

**检查**:
- 确认使用 orjson（不是标准 json）
- 查看日志中的序列化错误

**解决方案**:
```bash
# 确认 orjson 已安装
uv pip list | grep orjson
```

### 问题 5: 吞吐量低

#### 症状
- 订单吞吐量 < 10 单/秒
- 系统无法处理高频交易
- 请求排队严重

#### 可能原因和解决方案

**1. 同步阻塞**

**检查日志**:
- 查找 "blocking" 或 "waiting" 相关日志

**解决方案**:
- 确保所有 I/O 操作都是异步的
- 检查是否有同步调用阻塞事件循环

**2. 消息队列积压**

**特征**:
- 内存持续增长
- 延迟持续上升

**解决方案**:
- 增加处理速度
- 限制队列大小
- 实施背压机制

### 问题 6: 系统资源占用高

#### CPU 使用率过高

**症状**:
- CPU > 80%
- 频繁收到 CPU 告警

**可能原因**:

**1. 采样率过高**
```yaml
Metrics:
  SampleRate: 0.2  # 降低到 20%
```

**2. 日志级别过低**
```yaml
LogLevel: INFO  # 不要使用 DEBUG
```

#### 内存使用率过高

**症状**:
- 内存 > 80%
- 频繁收到内存告警
- 可能出现 OOM

**可能原因**:

**1. 内存泄漏**

**诊断**:
```python
# 使用 memory_profiler
from memory_profiler import profile

@profile
def your_function():
    pass
```


## 配置问题

### 问题 7: 配置文件错误

#### 症状
- 服务启动失败
- 日志显示配置解析错误
- 功能异常

#### 常见配置错误

**1. YAML 语法错误**

**错误示例**:
```yaml
Storage:
  Enabled: true
  Type csv  # 缺少冒号
```

**正确格式**:
```yaml
Storage:
  Enabled: true
  Type: csv  # 添加冒号
```

**验证语法**:
```bash
python -c "import yaml; yaml.safe_load(open('config/config_md.yaml'))"
```

**2. 缩进错误**

**错误示例**:
```yaml
Storage:
  Enabled: true
Type: csv  # 缩进错误
```

**正确格式**:
```yaml
Storage:
  Enabled: true
  Type: csv  # 正确缩进
```

**3. 数据类型错误**

**错误示例**:
```yaml
Port: "8080"  # 字符串，应该是数字
Enabled: "true"  # 字符串，应该是布尔值
```

**正确格式**:
```yaml
Port: 8080  # 数字
Enabled: true  # 布尔值
```

#### 配置验证清单

- [ ] YAML 语法正确
- [ ] 缩进一致（使用空格，不用 Tab）
- [ ] 数据类型正确
- [ ] 所有必需字段存在
- [ ] 端口号未被占用
- [ ] 前置地址正确

### 问题 8: 环境变量问题

#### 症状
- 配置未生效
- 使用了错误的配置值
- 环境变量覆盖了配置文件

#### 环境变量优先级

```
环境变量 > 配置文件 > 默认值
```

#### 常见问题

**1. 环境变量未设置**

**检查**:
```bash
# Windows CMD
echo %CTP_USER_ID%

# Windows PowerShell
$env:CTP_USER_ID

# Linux
echo $CTP_USER_ID
```

**设置**:
```bash
# Windows CMD
set CTP_USER_ID=your_user_id

# Windows PowerShell
$env:CTP_USER_ID="your_user_id"

# Linux
export CTP_USER_ID=your_user_id
```

### 问题 9: 权限问题

#### 症状
- 无法创建日志文件
- 无法写入数据目录
- 无法读取配置文件

#### 常见权限问题

**1. 日志目录权限不足**

**错误日志**:
```
PermissionError: [Errno 13] Permission denied: 'logs/webctp.log'
```

**解决方案**:
```bash
# Windows
icacls logs /grant Users:F

# Linux
chmod 755 logs
```

**2. 数据目录权限不足**

**解决方案**:
```bash
# Windows
icacls data /grant Users:F

# Linux
chmod 755 data
```

### 问题 10: 端口冲突

#### 症状
- 服务启动失败
- 错误信息: "Address already in use"
- 端口被占用

#### 诊断和解决

**1. 查找占用端口的进程**

```bash
# Windows
netstat -ano | findstr :8080
tasklist | findstr <PID>

# Linux
lsof -i :8080
```

**2. 终止占用进程**

```bash
# Windows
taskkill /PID <PID> /F

# Linux
kill -9 <PID>
```

**3. 修改配置使用其他端口**

```yaml
# config_md.yaml
Port: 8082  # 改为其他端口

# config_td.yaml
Port: 8083  # 改为其他端口
```


## 日志分析

### 日志文件位置

**主日志文件**:
- `logs/webctp.log` - 所有日志（INFO 及以上）
- `logs/webctp_error.log` - 错误日志（ERROR 及以上）

### 日志级别

| 级别 | 说明 | 用途 |
|------|------|------|
| DEBUG | 调试信息 | 开发调试 |
| INFO | 一般信息 | 正常运行日志 |
| WARNING | 警告信息 | 潜在问题 |
| ERROR | 错误信息 | 错误和异常 |
| CRITICAL | 严重错误 | 系统崩溃 |

### 日志格式

```
2025-12-30 10:30:45 | INFO | src.apps.md_app:startup:45 | 行情服务启动成功
```

**格式说明**:
- `2025-12-30 10:30:45` - 时间戳
- `INFO` - 日志级别
- `src.apps.md_app:startup:45` - 模块:函数:行号
- `行情服务启动成功` - 日志消息

### 常用日志查询

#### 查看最新日志

```bash
# Windows PowerShell
Get-Content logs\webctp.log -Tail 50

# Linux
tail -50 logs/webctp.log
```

#### 实时监控日志

```bash
# Windows PowerShell
Get-Content logs\webctp.log -Wait -Tail 50

# Linux
tail -f logs/webctp.log
```

#### 查找错误日志

```bash
# Windows PowerShell
Select-String -Path logs\webctp.log -Pattern "ERROR"

# Linux
grep "ERROR" logs/webctp.log
```

#### 查找性能报告

```bash
# 查看最近的性能报告
grep "性能指标报告" logs/webctp.log -A 30 | tail -35
```

#### 查找告警

```bash
# 查看所有告警
grep "⚠️" logs/webctp.log
```


## 错误代码参考

### CTP 错误代码

#### 常见错误码

| 错误码 | 说明 | 可能原因 | 解决方案 |
|--------|------|----------|----------|
| 0 | 正确 | - | - |
| 3 | 不合法的登录 | 用户名或密码错误 | 检查账号密码 |
| 4 | 用户不活跃 | 账号被冻结 | 联系券商 |
| 7 | 还没有初始化 | CTP 未初始化完成 | 等待初始化 |
| 22 | 重复的报单 | 订单重复提交 | 检查订单逻辑 |
| 31 | 报单不存在 | 订单号不存在 | 检查订单号 |
| 36 | 超过最大报单数 | 报单数量超限 | 减少报单频率 |
| 50 | 资金不足 | 账户资金不足 | 充值或减少订单量 |
| 63 | 网络连接失败 | 网络问题 | 检查网络连接 |
| 90 | 认证失败 | AuthCode 或 AppID 错误 | 检查认证信息 |

### WebSocket 错误

| 状态码 | 说明 | 原因 |
|--------|------|------|
| 1000 | 正常关闭 | 正常断开连接 |
| 1001 | 端点离开 | 服务器关闭 |
| 1002 | 协议错误 | WebSocket 协议错误 |
| 1003 | 不支持的数据 | 数据类型错误 |
| 1006 | 异常关闭 | 连接异常断开 |
| 1011 | 服务器错误 | 服务器内部错误 |


## 获取帮助

### 自助资源

**文档**:
- [README](../README.md) - 项目概述和快速开始
- [开发文档](./development_CN.md) - 开发指南和架构说明
- [快速开始](./QUICK_START.md) - 快速入门指南

**日志分析**:
```bash
# 查看错误日志
grep "ERROR" logs/webctp.log | tail -50

# 查看告警
grep "⚠️" logs/webctp.log

# 查看性能报告
grep "性能指标报告" logs/webctp.log -A 30 | tail -35
```

### 社区支持

**QQ 群**: 446042777

**GitHub Issues**: 
- 报告 Bug
- 功能请求
- 技术讨论

### 技术支持联系方式

**邮箱**: donnymoving@gmail.com

---

## 附录

### A. 故障排查清单

**启动问题**:
- [ ] 检查 Python 版本（3.10+）
- [ ] 检查虚拟环境已激活
- [ ] 检查依赖已安装（uv sync）
- [ ] 检查配置文件语法
- [ ] 检查端口未被占用
- [ ] 检查日志目录权限

**连接问题**:
- [ ] 检查服务已启动
- [ ] 检查端口监听状态
- [ ] 检查防火墙设置
- [ ] 检查网络连接
- [ ] 检查前置地址正确
- [ ] 检查账号密码正确

**性能问题**:
- [ ] 查看性能报告
- [ ] 检查系统资源
- [ ] 检查网络延迟
- [ ] 检查配置是否优化
- [ ] 查看告警日志

### B. 常用命令速查

```bash
# 服务管理
python main.py --config=./config/config_md.yaml --app_type=md
python main.py --config=./config/config_td.yaml --app_type=td

# 日志查看
tail -f logs/webctp.log
grep "ERROR" logs/webctp.log
grep "⚠️" logs/webctp.log

# 端口检查
netstat -ano | findstr :8080
netstat -ano | findstr :8081
```

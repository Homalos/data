# 故障排查指南

## 常见问题和解决方案

### 问题1：HTTP 403 错误

**错误信息：**
```
❌ 连接失败: server rejected WebSocket connection: HTTP 403
```

**原因分析：**
1. WebSocket路径不正确
2. 需要Token认证但未提供
3. Token不正确

**解决方案：**

#### 方案1：检查WebSocket路径
确保连接的URL是正确的：
- ✅ 正确：`ws://127.0.0.1:8081/`
- ❌ 错误：`ws://127.0.0.1:8081/td/`

#### 方案2：检查Token配置
查看配置文件中是否配置了Token：

```yaml
# config/config_td.yaml
Token: your_token_here  # 如果有这一行，需要在连接时提供Token
```

如果配置了Token，需要在 `.env` 文件中添加：
```bash
TD_TOKEN=your_token_here
```

#### 方案3：测试连接
使用测试脚本验证连接：
```bash
python scripts/test_ws_connection.py
```

---

### 问题2：连接被拒绝

**错误信息：**
```
❌ 连接被拒绝: [Errno 10061] No connection could be made...
```

**原因分析：**
1. 交易服务未启动
2. 端口不正确
3. 防火墙阻止连接

**解决方案：**

#### 方案1：启动交易服务
```bash
# 检查服务是否运行
netstat -ano | findstr :8081

# 如果没有运行，启动服务
python -m uvicorn src.apps.td_app:app --host 0.0.0.0 --port 8081
```

#### 方案2：检查端口配置
确保 `.env` 文件中的端口与配置文件一致：

```bash
# .env
TD_PORT=8081  # 必须与 config/config_td.yaml 中的 Port 一致
```

#### 方案3：检查防火墙
```bash
# Windows防火墙
# 控制面板 -> Windows Defender 防火墙 -> 允许应用通过防火墙
# 添加Python到允许列表
```

---

### 问题3：登录失败

**错误信息：**
```
❌ 登录失败: [3] CTP:不合法的登录
```

**原因分析：**
1. 账号密码错误
2. 经纪商ID不正确
3. 不在交易时间
4. 账号被锁定

**解决方案：**

#### 方案1：检查账号密码
确认 `.env` 文件中的账号密码正确：
```bash
CTP_USER_ID=your_correct_user_id
CTP_PASSWORD=your_correct_password
```

#### 方案2：检查经纪商ID
查看配置文件中的经纪商ID：
```yaml
# config/config_td.yaml
BrokerID: "9999"  # SimNow模拟环境
```

#### 方案3：检查交易时间
CTP服务器只在交易时间可用：
- 周一至周五：09:00-15:00, 21:00-02:30
- SimNow 7x24环境除外

#### 方案4：检查前置地址
确认前置地址可用：
```yaml
# config/config_td.yaml
TdFrontAddress: tcp://182.254.243.31:30001  # 标准环境
# TdFrontAddress: tcp://182.254.243.31:40001  # 7x24环境
```

---

### 问题4：合约查询超时

**错误信息：**
```
⚠️  等待超时，已接收 0 个合约
```

**原因分析：**
1. 网络连接不稳定
2. CTP服务器响应慢
3. 超时时间设置太短

**解决方案：**

#### 方案1：检查网络连接
```bash
# 测试到CTP服务器的连接
ping 182.254.243.31
```

#### 方案2：增加超时时间
修改 `scripts/auto_login_td.py`：
```python
# 将超时时间从120秒增加到300秒
await self.wait_for_instruments_query(timeout=300.0)
```

#### 方案3：手动查询合约
登录成功后，可以手动发送查询请求：
```python
# 使用WebSocket客户端发送
{
    "MessageType": "ReqQryInstrument",
    "ReqQryInstrument": {
        "InstrumentID": ""
    }
}
```

---

### 问题5：找不到配置文件

**错误信息：**
```
未找到配置文件
```

**解决方案：**

#### 创建配置文件
```bash
# 从示例文件复制
copy config\config.sample.yaml config\config_td.yaml

# 或使用通用配置
copy config\config.sample.yaml config\config.yaml
```

---

### 问题6：缺少依赖

**错误信息：**
```
ModuleNotFoundError: No module named 'websockets'
```

**解决方案：**

#### 检查依赖
```bash
python scripts/check_dependencies.py
```

#### 安装依赖
```bash
# 使用pip
pip install websockets pyyaml loguru

# 或使用uv
uv add websockets pyyaml loguru
```

---

## 调试技巧

### 1. 启用详细日志

修改配置文件：
```yaml
# config/config_td.yaml
LogLevel: DEBUG  # 改为DEBUG级别
```

### 2. 查看服务日志

启动服务时查看输出：
```bash
python -m uvicorn src.apps.td_app:app --host 0.0.0.0 --port 8081 --log-level debug
```

### 3. 使用测试脚本

按顺序运行测试脚本：
```bash
# 1. 检查依赖
python scripts/check_dependencies.py

# 2. 测试WebSocket连接
python scripts/test_ws_connection.py

# 3. 执行自动登录
python scripts/auto_login_td.py

# 4. 查看合约信息
python scripts/test_auto_query_instruments.py
```

### 4. 检查端口占用

```bash
# Windows
netstat -ano | findstr :8081

# 如果端口被占用，找到进程ID并结束
taskkill /PID <进程ID> /F
```

---

## 完整的故障排查流程

### 步骤1：检查环境

```bash
# 检查Python版本
python --version

# 检查依赖
python scripts/check_dependencies.py
```

### 步骤2：检查配置

```bash
# 确认配置文件存在
dir config\config_td.yaml

# 确认 .env 文件存在
dir .env

# 查看配置内容
type config\config_td.yaml
type .env
```

### 步骤3：启动服务

```bash
# 启动交易服务
python -m uvicorn src.apps.td_app:app --host 0.0.0.0 --port 8081

# 等待看到 "Application startup complete" 消息
```

### 步骤4：测试连接

```bash
# 在新终端测试连接
python scripts/test_ws_connection.py
```

### 步骤5：执行登录

```bash
# 如果连接测试通过，执行自动登录
python scripts/auto_login_td.py
```

---

## 获取帮助

如果以上方法都无法解决问题，请提供以下信息：

1. **错误日志**：完整的错误信息
2. **配置信息**：
   - config/config_td.yaml 内容（隐藏敏感信息）
   - .env 文件内容（隐藏密码）
3. **环境信息**：
   - Python版本
   - 操作系统版本
   - 依赖版本
4. **测试结果**：
   - check_dependencies.py 输出
   - test_ws_connection.py 输出

---

**更新时间**: 2025-12-23  
**维护者**: Kiro AI Assistant

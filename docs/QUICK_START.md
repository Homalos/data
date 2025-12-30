# 🚀 快速开始

## 一分钟快速开始

### Windows用户

```bash
# 1. 创建配置文件
copy .env.example .env
notepad .env  # 填入你的CTP账号和密码

# 2. 启动行情服务
start_md_server.bat

# 3. 启动交易服务（另一个终端）
start_td_server.bat
```

服务启动后：
- ✅ 行情服务运行在 8080 端口
- ✅ 交易服务运行在 8081 端口
- ✅ 数据存储到 `data/ticks/` 和 `data/klines/` 目录（CSV格式）

---

## 详细步骤

### 步骤1：准备配置文件

创建 `.env` 文件：

```bash
# Windows
copy .env.example .env
notepad .env

# Linux/Mac
cp .env.example .env
nano .env
```

填入你的账号信息：

```bash
# CTP账号
CTP_USER_ID=你的账号
CTP_PASSWORD=你的密码
```

### 步骤2：安装依赖

```bash
# 使用 uv 安装依赖
uv sync
```

### 步骤3：启动服务

#### 方式A：使用启动脚本（Windows）

```bash
# 启动行情服务
start_md_server.bat

# 启动交易服务（另一个终端）
start_td_server.bat
```

#### 方式B：手动启动

```bash
# 终端1：启动行情服务
python main.py --config=./config/config_md.yaml --app_type=md

# 终端2：启动交易服务
python main.py --config=./config/config_td.yaml --app_type=td
```

### 步骤4：查看数据

```bash
# 查看Tick数据
python scripts/query_tick_csv.py list

# 查看K线数据
python scripts/query_kline_csv.py list
```

---

## 运行效果

### 行情服务启动成功：

```
INFO | 行情服务启动成功
INFO | Uvicorn running on http://127.0.0.1:8080
INFO | CTP 前置连接成功
INFO | 用户登录成功
```

### 交易服务启动成功：

```
INFO | 交易服务启动成功
INFO | Uvicorn running on http://127.0.0.1:8081
INFO | CTP 前置连接成功
INFO | 用户登录成功
INFO | 合约查询完成，共 500 个合约
```

---

## 常见问题

### Q1: 连接失败？

检查：
1. 服务是否已启动
2. 端口是否正确（行情8080，交易8081）
3. 防火墙设置

### Q2: 登录失败？

检查：
1. 账号密码是否正确
2. 是否在交易时间
3. 经纪商ID是否正确（SimNow为9999）

### Q3: 找不到 .env 文件？

解决：
1. 确保在项目根目录
2. 从 .env.example 复制
3. 填入真实账号密码

### Q4: 缺少依赖？

```bash
# 使用 uv 安装
uv sync

# 或使用 pip
pip install -r requirements.txt
```

---

## 下一步

登录成功后，你可以：

1. **查看合约信息**
   ```bash
   python scripts/test_auto_query_instruments.py
   ```

2. **订阅行情数据**
   - 使用WebSocket客户端连接到行情服务
   - 订阅感兴趣的合约
   - 实时接收tick数据

3. **查看存储的数据**
   - Tick数据：`data/ticks/` 目录
   - K线数据：`data/klines/` 目录

---

## 完整文档

- [详细使用指南](HOW_TO_USE_AUTO_LOGIN.md)
- [故障排查指南](TROUBLESHOOTING.md)
- [开发文档](development_CN.md)

---

## 安全提示

⚠️ **重要**：
- `.env` 文件包含敏感信息，不要提交到版本控制
- `.env` 已添加到 `.gitignore`
- 不要分享包含真实账号密码的配置文件

---

**祝使用愉快！** 🎉

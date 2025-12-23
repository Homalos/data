@echo off
REM 启动行情存储服务
echo ========================================
echo 行情存储系统启动脚本
echo ========================================
echo.

REM 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo 错误: 虚拟环境不存在
    echo 请先运行: uv sync
    pause
    exit /b 1
)

REM 激活虚拟环境
echo [1/3] 激活虚拟环境...
call .venv\Scripts\activate.bat

REM 检查InfluxDB连接
echo.
echo [2/3] 检查InfluxDB连接...
python scripts/init_influxdb.py
if errorlevel 1 (
    echo.
    echo 错误: InfluxDB连接失败
    echo 请确保InfluxDB 3.x已启动
    pause
    exit /b 1
)

REM 启动行情服务
echo.
echo [3/3] 启动行情存储服务...
echo.
echo ========================================
echo 服务信息:
echo - 配置文件: config/config_md.yaml
echo - WebSocket端口: 8080
echo - 存储: InfluxDB 3.x (localhost:8181)
echo - 数据库: tick_data
echo ========================================
echo.
echo 按 Ctrl+C 停止服务
echo.

python main.py --config=./config/config_md.yaml --app_type=md

pause

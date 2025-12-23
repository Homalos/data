@echo off
chcp 65001 >nul
echo ========================================
echo 交易服务自动启动和登录脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
python -c "import websockets" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装websockets依赖...
    pip install websockets
)

echo.
echo [2/3] 启动交易服务...
echo [提示] 交易服务将在新窗口中启动
echo.

REM 在新窗口中启动交易服务
start "交易服务" cmd /k "python -m uvicorn src.apps.td_app:app --host 0.0.0.0 --port 8001"

REM 等待服务启动
echo [等待] 等待交易服务启动（5秒）...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] 执行自动登录...
echo.

REM 执行自动登录脚本
python scripts/auto_login_td.py

echo.
echo ========================================
echo 完成
echo ========================================
pause

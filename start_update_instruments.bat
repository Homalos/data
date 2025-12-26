@echo off
title 登录交易服务更新全市场合约信息
echo ========================================
echo 登录交易服务更新全市场合约信息
echo ========================================
echo.

REM 检查Python虚拟环境是否安装
echo [1/3] 检查Python虚拟环境...
if not exist ".venv\Scripts\activate.bat" (
    echo 错误: 虚拟环境不存在
    echo 请先运行: uv sync
    pause
    exit /b 1
)

echo.
echo [2/3] 启动交易服务...
echo [提示] 交易服务将在新窗口中启动
echo.

REM 在新窗口中启动交易服务
start start_td_server.bat

REM 等待服务启动
echo [等待] 等待交易服务启动（5秒）...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] 执行自动登录交易服务器...
echo.

REM 执行登录和更新合约脚本
call .venv\Scripts\activate
python scripts/update_instruments.py

echo.
echo ========================================
echo 停止
echo ========================================
pause

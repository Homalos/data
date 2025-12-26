@echo off
title 启动存储期货行情数据存储系统
REM 启动存储期货行情数据存储系统
REM 持续监听行情数据，按 Ctrl+C 停止

echo ============================================================
echo 行情存储系统
echo ============================================================
echo.
echo 此脚本将持续监听行情数据，直到您按 Ctrl+C 停止
echo.

REM 检查 .env 文件
if exist .env (
    echo [提示] 发现 .env 文件，将自动加载账号密码
    echo.
) else (
    echo [提示] 未发现 .env 文件，需要手动输入账号密码
    echo [提示] 建议创建 .env 文件以避免每次输入
    echo.
    echo 创建方法:
    echo   1. 复制 .env.example 为 .env
    echo   2. 编辑 .env 文件，填入您的账号密码
    echo.
)

REM 检查Python虚拟环境是否安装
echo [1/3] 检查Python虚拟环境...
if not exist ".venv\Scripts\activate.bat" (
    echo 错误: 虚拟环境不存在
    echo 请先运行: uv sync
    pause
    exit /b 1
)

echo.
echo [2/3] 启动行情服务...
echo [提示] 行情服务将在新窗口中启动
echo.

REM 在新窗口中启动交易服务
start start_md_server.bat

REM 等待服务启动
echo [等待] 等待交易服务启动（5秒）...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] 执行订阅并存储期货行情数据...
echo.
REM 执行订阅并存储期货行情数据
call .venv\Scripts\activate
python scripts\store_market_data.py

echo.
echo ============================================================
echo 停止
echo ============================================================
pause

@echo off
REM 启动定时任务调度器
title 定时任务调度器
echo ========================================
echo 定时任务调度器
echo ========================================
echo.
call .venv\Scripts\activate
python scripts\scheduler.py

pause

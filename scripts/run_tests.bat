@echo off
REM 运行所有测试脚本
REM 使用方法: scripts\run_tests.bat

echo ============================================================
echo 运行测试套件
echo ============================================================
echo.

REM 检查pytest是否安装
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo [错误] pytest未安装
    echo 请运行: pip install pytest pytest-asyncio
    pause
    exit /b 1
)

echo [1/5] 运行所有测试...
echo.
pytest tests/ -v

echo.
echo ============================================================
echo 测试完成
echo ============================================================
echo.

REM 询问是否生成覆盖率报告
set /p generate_coverage="是否生成覆盖率报告? (y/n): "
if /i "%generate_coverage%"=="y" (
    echo.
    echo [2/5] 生成覆盖率报告...
    pytest tests/ --cov=src/storage --cov-report=html --cov-report=term
    echo.
    echo 覆盖率报告已生成到: htmlcov/index.html
    echo.
    
    set /p open_report="是否打开覆盖率报告? (y/n): "
    if /i "%open_report%"=="y" (
        start htmlcov\index.html
    )
)

echo.
pause

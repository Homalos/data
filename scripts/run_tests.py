#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行测试套件脚本（跨平台）

使用方法:
    python scripts/run_tests.py              # 运行所有测试
    python scripts/run_tests.py --cov        # 运行测试并生成覆盖率报告
    python scripts/run_tests.py --file test_instrument_manager  # 运行特定测试文件
"""
import sys
import subprocess
from pathlib import Path


def check_pytest():
    """检查pytest是否安装"""
    try:
        import pytest
        import pytest_asyncio
        return True
    except ImportError:
        print("❌ pytest或pytest-asyncio未安装")
        print("请运行: pip install pytest pytest-asyncio")
        return False


def run_tests(args):
    """运行测试"""
    if not check_pytest():
        return 1
    
    print("=" * 60)
    print("运行测试套件")
    print("=" * 60)
    print()
    
    # 构建pytest命令
    cmd = ["pytest", "tests/", "-v"]
    
    # 解析参数
    if "--cov" in args:
        cmd.extend(["--cov=src/storage", "--cov-report=html", "--cov-report=term"])
        print("📊 将生成覆盖率报告")
    
    if "--file" in args:
        file_idx = args.index("--file")
        if file_idx + 1 < len(args):
            test_file = args[file_idx + 1]
            if not test_file.startswith("test_"):
                test_file = f"test_{test_file}"
            if not test_file.endswith(".py"):
                test_file = f"{test_file}.py"
            cmd[1] = f"tests/{test_file}"
            print(f"🎯 只运行测试文件: {test_file}")
    
    print()
    print("执行命令:", " ".join(cmd))
    print()
    
    # 运行测试
    result = subprocess.run(cmd)
    
    print()
    print("=" * 60)
    if result.returncode == 0:
        print("✅ 测试完成 - 全部通过")
    else:
        print("❌ 测试完成 - 有失败")
    print("=" * 60)
    
    # 如果生成了覆盖率报告，提示打开
    if "--cov" in args and result.returncode == 0:
        print()
        print("📊 覆盖率报告已生成到: htmlcov/index.html")
        
        # 询问是否打开报告
        try:
            response = input("是否打开覆盖率报告? (y/n): ").strip().lower()
            if response == 'y':
                import webbrowser
                report_path = Path("htmlcov/index.html").absolute()
                webbrowser.open(f"file://{report_path}")
        except KeyboardInterrupt:
            print()
    
    return result.returncode


def main():
    """主函数"""
    args = sys.argv[1:]
    
    # 显示帮助
    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0
    
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())

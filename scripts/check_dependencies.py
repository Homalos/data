#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查自动登录脚本所需的依赖
"""
import sys


def check_dependency(module_name: str, package_name: str = None) -> bool:
    """
    检查依赖是否已安装
    
    Args:
        module_name: 模块名称
        package_name: 包名称（用于安装提示）
    
    Returns:
        是否已安装
    """
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✅ {module_name:20s} 已安装")
        return True
    except ImportError:
        print(f"❌ {module_name:20s} 未安装 - 运行: pip install {package_name}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("检查自动登录脚本依赖")
    print("=" * 60)
    print()
    
    dependencies = [
        ("websockets", "websockets"),
        ("yaml", "pyyaml"),
        ("loguru", "loguru"),
    ]
    
    all_installed = True
    
    for module_name, package_name in dependencies:
        if not check_dependency(module_name, package_name):
            all_installed = False
    
    print()
    print("=" * 60)
    
    if all_installed:
        print("✅ 所有依赖已安装，可以运行自动登录脚本")
        print()
        print("运行命令:")
        print("  python scripts/auto_login_td.py")
    else:
        print("❌ 部分依赖未安装，请先安装依赖")
        print()
        print("安装命令:")
        print("  pip install websockets pyyaml loguru")
        print()
        print("或使用 uv:")
        print("  uv add websockets pyyaml loguru")
    
    print("=" * 60)
    
    return 0 if all_installed else 1


if __name__ == "__main__":
    sys.exit(main())

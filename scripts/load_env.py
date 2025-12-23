#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境变量加载工具

从 .env 文件加载环境变量
"""
import os
from pathlib import Path


def load_env(env_file: str = ".env"):
    """
    从文件加载环境变量
    
    Args:
        env_file: 环境变量文件路径
    """
    env_path = Path(env_file)
    
    if not env_path.exists():
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            
            # 解析键值对
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 设置环境变量
                os.environ[key] = value
    
    return True


if __name__ == "__main__":
    if load_env():
        print("✅ 环境变量加载成功")
    else:
        print("⚠️  未找到 .env 文件")

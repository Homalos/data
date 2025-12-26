#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试服务端验证逻辑

直接测试 validate_request 方法
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.td_client import TdClient
from src.constants import TdConstant as Constant


def test_validation():
    """测试验证逻辑"""
    print("=" * 60)
    print("测试服务端验证逻辑")
    print("=" * 60)
    
    # 创建TdClient实例
    client = TdClient()
    
    # 测试请求
    request = {
        "MsgType": "ReqUserLogin",
        "RequestID": 0,
        "ReqUserLogin": {
            "UserID": "xxx",
            "Password": "xxx"
        }
    }
    
    print("\n测试请求:")
    print(request)
    
    # 获取消息类型
    message_type = request[Constant.MessageType]
    print(f"\n消息类型: {message_type}")
    
    # 验证请求
    print("\n执行验证...")
    result = client.validate_request(message_type, request)
    
    if result is None:
        print("✅ 验证通过")
    else:
        print("❌ 验证失败")
        print(f"错误信息: {result}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_validation()

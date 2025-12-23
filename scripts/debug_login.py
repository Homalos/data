#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试登录流程 - 打印所有收到的消息
"""
import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import websockets
except ImportError:
    print("❌ 缺少 websockets 库")
    print("安装命令: pip install websockets")
    sys.exit(1)

from loguru import logger
from src.utils.config import GlobalConfig


async def debug_login():
    """调试登录流程"""
    # 加载配置
    config_path = project_root / "config/config_td.yaml"
    GlobalConfig.load_config(str(config_path))
    
    # 连接参数
    url = "ws://127.0.0.1:8081/"
    user_id = "160219"
    password = "1"  # 使用测试密码
    
    logger.info(f"连接到: {url}")
    
    async with websockets.connect(url, ping_interval=30, ping_timeout=60) as ws:
        logger.info("✅ 连接成功")
        
        # 构建登录请求
        login_request = {
            "MsgType": "ReqUserLogin",
            "RequestID": 0,
            "ReqUserLogin": {
                "UserID": user_id,
                "Password": password
            }
        }
        
        logger.info(f"发送登录请求:")
        logger.info(json.dumps(login_request, indent=2, ensure_ascii=False))
        
        # 发送请求
        await ws.send(json.dumps(login_request))
        logger.info("✅ 请求已发送")
        
        # 接收所有消息（最多10条或30秒）
        logger.info("\n开始接收消息...")
        logger.info("=" * 60)
        
        count = 0
        start_time = asyncio.get_event_loop().time()
        
        while count < 10 and (asyncio.get_event_loop().time() - start_time) < 30:
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                count += 1
                
                logger.info(f"\n消息 #{count}:")
                logger.info("-" * 60)
                
                try:
                    response_data = json.loads(response)
                    logger.info(json.dumps(response_data, indent=2, ensure_ascii=False))
                    
                    # 检查消息类型
                    msg_type = response_data.get("MsgType")
                    logger.info(f"\nMsgType: {msg_type}")
                    
                    if msg_type == "OnRspUserLogin":
                        logger.info("✅ 收到登录响应！")
                        rsp_info = response_data.get("RspInfo", {})
                        logger.info(f"ErrorID: {rsp_info.get('ErrorID')}")
                        logger.info(f"ErrorMsg: {rsp_info.get('ErrorMsg')}")
                        break
                        
                except json.JSONDecodeError:
                    logger.warning(f"非JSON消息: {response}")
                    
            except asyncio.TimeoutError:
                logger.info("5秒内没有新消息")
                break
        
        logger.info("\n" + "=" * 60)
        logger.info(f"共接收 {count} 条消息")


if __name__ == "__main__":
    try:
        asyncio.run(debug_login())
    except KeyboardInterrupt:
        logger.info("\n用户中断")
    except Exception as e:
        logger.error(f"错误: {e}", exc_info=True)

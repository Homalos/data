#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的登录测试脚本
用于诊断登录超时问题
"""
import asyncio
import websockets
import json
import sys
from pathlib import Path
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_login():
    """测试登录"""
    url = "ws://127.0.0.1:8080/"
    
    logger.info(f"连接到 {url}")
    
    try:
        async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
            logger.info("✅ WebSocket连接成功")
            
            # 发送登录请求
            login_request = {
                "MsgType": "ReqUserLogin",
                "RequestID": 1,
                "ReqUserLogin": {
                    "UserID": "160219",
                    "Password": "Aa123456"
                }
            }
            
            logger.info("发送登录请求...")
            await ws.send(json.dumps(login_request))
            logger.info("✅ 登录请求已发送")
            
            # 等待响应（增加超时时间）
            logger.info("等待响应（60秒超时）...")
            
            try:
                # 循环接收消息
                timeout_count = 0
                while timeout_count < 6:  # 最多等待60秒
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=10.0)
                        logger.info(f"收到消息: {message[:200]}...")
                        
                        response = json.loads(message)
                        msg_type = response.get("MsgType")
                        
                        logger.info(f"消息类型: {msg_type}")
                        
                        if msg_type == "Ping":
                            # 响应Ping
                            pong = {"MsgType": "Pong", "Timestamp": response.get("Timestamp")}
                            await ws.send(json.dumps(pong))
                            logger.debug("已响应Pong")
                            continue
                        
                        if msg_type in ["OnRspUserLogin", "RspUserLogin"]:
                            logger.info("✅ 收到登录响应")
                            logger.info(f"响应内容: {json.dumps(response, indent=2, ensure_ascii=False)}")
                            
                            rsp_info = response.get("RspInfo", {})
                            if rsp_info.get("ErrorID") == 0:
                                logger.info("✅ 登录成功！")
                                return True
                            else:
                                logger.error(f"❌ 登录失败: {rsp_info.get('ErrorMsg')}")
                                return False
                        
                        # 其他消息
                        logger.info(f"收到其他消息: {msg_type}")
                        
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        logger.warning(f"等待超时 ({timeout_count * 10}秒)，继续等待...")
                        continue
                
                logger.error("❌ 等待响应超时（60秒）")
                return False
                
            except Exception as e:
                logger.error(f"❌ 接收响应失败: {e}", exc_info=True)
                return False
            
    except Exception as e:
        logger.error(f"❌ 连接失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("简单登录测试")
    logger.info("=" * 60)
    
    success = await test_login()
    
    logger.info("=" * 60)
    if success:
        logger.info("✅ 测试通过")
    else:
        logger.info("❌ 测试失败")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n测试被中断")
    except Exception as e:
        logger.error(f"测试异常: {e}", exc_info=True)

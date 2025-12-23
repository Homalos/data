#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试WebSocket连接

快速测试WebSocket服务是否可以连接
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import websockets
except ImportError:
    print("❌ 缺少 websockets 库")
    print("安装命令: pip install websockets")
    sys.exit(1)

from loguru import logger


async def test_connection(host: str = "127.0.0.1", port: int = 8081, token: str = None):
    """
    测试WebSocket连接
    
    Args:
        host: 服务器地址
        port: 服务器端口
        token: 认证令牌（可选）
    """
    # 构建URL
    url = f"ws://{host}:{port}/"
    if token:
        url += f"?token={token}"
    
    logger.info(f"测试连接: {url}")
    
    try:
        # 尝试连接
        async with websockets.connect(url, ping_interval=30, ping_timeout=60) as ws:
            logger.info("✅ 连接成功")
            
            # 尝试接收欢迎消息（如果有）
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"收到消息: {message}")
            except asyncio.TimeoutError:
                logger.info("未收到欢迎消息（正常）")
            
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        logger.error(f"❌ 连接失败: HTTP {e.status_code}")
        if e.status_code == 403:
            logger.error("可能原因:")
            logger.error("1. 需要Token认证但未提供")
            logger.error("2. Token不正确")
            logger.error("3. WebSocket路径不正确")
        return False
        
    except ConnectionRefusedError:
        logger.error("❌ 连接被拒绝")
        logger.error("可能原因:")
        logger.error("1. 服务未启动")
        logger.error("2. 端口不正确")
        logger.error("3. 防火墙阻止")
        return False
        
    except Exception as e:
        logger.error(f"❌ 连接失败: {e}")
        return False


async def main():
    """主函数"""
    import os
    
    logger.info("=" * 60)
    logger.info("WebSocket连接测试")
    logger.info("=" * 60)
    
    # 从环境变量获取配置
    host = os.getenv("TD_HOST", "127.0.0.1")
    port = int(os.getenv("TD_PORT", "8081"))
    token = os.getenv("TD_TOKEN", None)
    
    logger.info(f"配置:")
    logger.info(f"  地址: {host}")
    logger.info(f"  端口: {port}")
    logger.info(f"  Token: {'已配置' if token else '未配置'}")
    logger.info("")
    
    # 测试连接
    success = await test_connection(host, port, token)
    
    logger.info("")
    logger.info("=" * 60)
    if success:
        logger.info("✅ 测试通过")
        logger.info("")
        logger.info("下一步:")
        logger.info("  运行自动登录脚本:")
        logger.info("  python scripts/auto_login_td.py")
    else:
        logger.info("❌ 测试失败")
        logger.info("")
        logger.info("请检查:")
        logger.info("1. 交易服务是否已启动")
        logger.info("   启动命令: python -m uvicorn src.apps.td_app:app --host 0.0.0.0 --port 8081")
        logger.info("2. 端口是否正确（默认8081）")
        logger.info("3. 是否需要Token认证")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n用户中断")

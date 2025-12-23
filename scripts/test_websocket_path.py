#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试WebSocket路径
"""
import asyncio
import websockets
from loguru import logger


async def test_paths():
    """测试不同的WebSocket路径"""
    
    paths = [
        "ws://127.0.0.1:8080/",
        "ws://127.0.0.1:8080/md",
        "ws://127.0.0.1:8080/md/",
    ]
    
    logger.info("=" * 60)
    logger.info("测试WebSocket路径")
    logger.info("=" * 60)
    
    for path in paths:
        logger.info(f"\n尝试连接: {path}")
        try:
            ws = await websockets.connect(path, open_timeout=2)
            logger.info(f"✅ 成功连接到: {path}")
            await ws.close()
            return path
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
    
    logger.error("\n所有路径都连接失败！")
    return None


if __name__ == "__main__":
    result = asyncio.run(test_paths())
    if result:
        logger.info(f"\n正确的WebSocket路径是: {result}")

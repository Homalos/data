#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : heartbeat.py
@Date       : 2025/12/10 17:42
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: WebSocket 心跳管理器
"""
import time
import asyncio
from typing import Callable, Awaitable
from ..utils import logger


class HeartbeatManager:
    """WebSocket 心跳管理器"""
    
    def __init__(self, interval: float = 30.0, timeout: float = 60.0):
        """
        初始化心跳管理器
        
        Args:
            interval: 心跳间隔（秒）
            timeout: 心跳超时时间（秒）
        """
        self.interval = interval
        self.timeout = timeout
        self.last_pong_time = time.time()
        self.is_running = False
        self._task = None
    
    async def start(self, 
                   send_callback: Callable[[dict], Awaitable[None]], 
                   disconnect_callback: Callable[[], Awaitable[None]]):
        """
        启动心跳检测
        
        Args:
            send_callback: 发送消息的回调函数
            disconnect_callback: 断开连接的回调函数
        """
        self.is_running = True
        self.last_pong_time = time.time()
        
        async def heartbeat_loop():
            while self.is_running:
                try:
                    # 检查超时（在发送前检查）
                    if self.is_timeout():
                        logger.warning(f"Heartbeat timeout ({self.timeout}s), disconnecting...")
                        self.is_running = False
                        try:
                            await disconnect_callback()
                        except Exception:
                            pass  # 忽略断开连接时的错误
                        break
                    
                    # 发送 Ping
                    await send_callback({
                        "MsgType": "Ping",
                        "Timestamp": int(time.time() * 1000)
                    })
                    logger.debug(f"Sent Ping, last pong: {time.time() - self.last_pong_time:.1f}s ago")
                    
                    # 等待心跳间隔
                    await asyncio.sleep(self.interval)
                        
                except asyncio.CancelledError:
                    logger.debug("Heartbeat task cancelled")
                    break
                except Exception as e:
                    # 连接已关闭，静默退出
                    if "websocket.close" in str(e) or "response already completed" in str(e):
                        logger.debug("Connection closed, stopping heartbeat")
                    else:
                        logger.error(f"Heartbeat error: {e}")
                    self.is_running = False
                    break
        
        self._task = asyncio.create_task(heartbeat_loop())
    
    async def stop(self):
        """停止心跳检测"""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    def on_pong_received(self):
        """收到 Pong 响应时调用"""
        self.last_pong_time = time.time()
        logger.debug("Received Pong, heartbeat updated")
    
    def is_timeout(self) -> bool:
        """检查是否超时"""
        return (time.time() - self.last_pong_time) > self.timeout

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tick数据缓冲器 - 用于批量写入优化
"""
import asyncio
from typing import List, Dict
from collections import deque
from loguru import logger


class TickBuffer:
    """
    Tick数据缓冲器
    
    用于批量写入优化，减少数据库写入次数，提高性能
    """
    
    def __init__(self, max_size: int = 1000, flush_interval: float = 5.0):
        """
        初始化缓冲器
        
        Args:
            max_size: 最大缓冲数量
            flush_interval: 刷新间隔（秒）
        """
        self.max_size = max_size
        self.flush_interval = flush_interval
        self._buffer: deque = deque(maxlen=max_size)
        self._lock = asyncio.Lock()
        self._total_received = 0
        self._total_flushed = 0
    
    def add(self, tick_data: Dict):
        """
        添加tick数据（非阻塞）
        
        Args:
            tick_data: tick数据字典
        """
        self._buffer.append(tick_data)
        self._total_received += 1
    
    def is_full(self) -> bool:
        """
        检查缓冲区是否已满
        
        Returns:
            是否已满
        """
        return len(self._buffer) >= self.max_size
    
    def size(self) -> int:
        """
        获取当前缓冲区大小
        
        Returns:
            当前缓冲数量
        """
        return len(self._buffer)
    
    async def get_batch(self) -> List[Dict]:
        """
        获取一批数据并清空缓冲区（线程安全）
        
        Returns:
            tick数据列表
        """
        async with self._lock:
            if not self._buffer:
                return []
            
            batch = list(self._buffer)
            self._buffer.clear()
            self._total_flushed += len(batch)
            
            return batch
    
    def get_all(self) -> List[Dict]:
        """
        获取所有数据（用于关闭时刷新）
        
        Returns:
            所有tick数据
        """
        if not self._buffer:
            return []
        
        batch = list(self._buffer)
        self._buffer.clear()
        self._total_flushed += len(batch)
        
        return batch
    
    def get_stats(self) -> Dict:
        """
        获取缓冲区统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "current_size": len(self._buffer),
            "max_size": self.max_size,
            "usage_percent": (len(self._buffer) / self.max_size * 100) if self.max_size > 0 else 0,
            "total_received": self._total_received,
            "total_flushed": self._total_flushed,
            "pending": self._total_received - self._total_flushed,
        }
    
    def clear(self):
        """清空缓冲区"""
        self._buffer.clear()
        logger.warning("缓冲区已清空")

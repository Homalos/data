#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
存储辅助工具类
提供CSV存储的公共方法
"""
import asyncio
import math
from pathlib import Path
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

import aiofiles
import aiofiles.os
from loguru import logger


class BaseCSVStorage(ABC):
    """CSV存储基类"""
    
    def __init__(self, base_path: str, flush_interval: float = 1.0):
        """
        初始化CSV存储基类
        
        Args:
            base_path: 基础存储路径
            flush_interval: 刷新间隔（秒）
        """
        self.base_path = Path(base_path)
        self._write_buffers: Dict[str, list] = {}
        self._buffer_locks: Dict[str, asyncio.Lock] = {}
        self._flush_interval = flush_interval
        self._running = False
        self._background_task: Optional[asyncio.Task] = None
    
    @property
    @abstractmethod
    def csv_fields(self) -> List[str]:
        """CSV字段列表"""
        pass
    
    @property
    @abstractmethod
    def storage_name(self) -> str:
        """存储类型名称"""
        pass
    
    async def initialize(self) -> None:
        """初始化存储引擎"""
        await aiofiles.os.makedirs(self.base_path, exist_ok=True)
        self._running = True
        self._background_task = asyncio.create_task(self._background_writer())
        logger.info(f"{self.storage_name}存储引擎初始化成功，存储路径: {self.base_path}")
    
    async def close(self) -> None:
        """关闭存储引擎"""
        self._running = False
        if self._background_task:
            await self._background_task
        await self._flush_all_buffers()
        logger.info(f"{self.storage_name}存储引擎已关闭")
    
    async def _add_to_buffer(self, file_key: str, csv_row: Dict[str, Any]) -> None:
        """
        添加数据到缓冲区
        
        Args:
            file_key: 文件key
            csv_row: CSV行数据
        """
        if file_key not in self._buffer_locks:
            self._buffer_locks[file_key] = asyncio.Lock()
        
        async with self._buffer_locks[file_key]:
            if file_key not in self._write_buffers:
                self._write_buffers[file_key] = []
            self._write_buffers[file_key].append(csv_row)
    
    async def _background_writer(self) -> None:
        """后台写入任务"""
        logger.info(f"{self.storage_name}后台写入任务启动")
        
        while self._running:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_all_buffers()
            except Exception as e:
                logger.error(f"{self.storage_name}后台写入任务异常: {e}", exc_info=True)
        
        logger.info(f"{self.storage_name}后台写入任务停止")
    
    async def _flush_all_buffers(self) -> None:
        """刷新所有缓冲区"""
        if not self._write_buffers:
            return
        
        file_keys = list(self._write_buffers.keys())
        for file_key in file_keys:
            try:
                await self._flush_buffer(file_key)
            except Exception as e:
                logger.error(f"刷新{self.storage_name}缓冲区失败: {file_key}, {e}")
    
    @abstractmethod
    async def _flush_buffer(self, file_key: str) -> None:
        """刷新单个缓冲区（子类实现）"""
        pass
    
    @staticmethod
    def _format_value(value: Any) -> str:
        """
        格式化值为CSV字符串，保证数值精度
        
        Args:
            value: 原始值
            
        Returns:
            格式化后的字符串
        """
        if value is None:
            return ''
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return ''  # NaN和Inf存为空值
            # 使用repr保持原始精度，1084.0 -> '1084.0'
            return repr(value)
        if isinstance(value, int):
            return str(value)
        return str(value)

    async def _write_csv_file(
        self, 
        file_path: Path, 
        data_to_write: List[Dict[str, Any]],
        file_key: str
    ) -> None:
        """
        写入CSV文件
        
        Args:
            file_path: 文件路径
            data_to_write: 要写入的数据列表
            file_key: 文件key（用于失败时放回缓冲区）
        """
        file_exists = file_path.exists()
        
        try:
            async with aiofiles.open(file_path, mode='a', newline='', encoding='utf-8') as f:
                if not file_exists:
                    header_line = ','.join(self.csv_fields) + '\n'
                    await f.write(header_line)
                
                for row in data_to_write:
                    values = [self._format_value(row.get(field, '')) for field in self.csv_fields]
                    line = ','.join(values) + '\n'
                    await f.write(line)
            
            logger.debug(f"写入{self.storage_name} CSV成功: {file_path}, {len(data_to_write)}条")
            
        except Exception as e:
            logger.error(f"写入{self.storage_name} CSV失败: {file_path}, {e}")
            async with self._buffer_locks[file_key]:
                self._write_buffers[file_key].extend(data_to_write)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_buffered = sum(len(buffer) for buffer in self._write_buffers.values())
        return {
            "storage_type": self.storage_name,
            "base_path": str(self.base_path),
            "buffered_files": len(self._write_buffers),
            "buffered_records": total_buffered,
            "running": self._running,
        }

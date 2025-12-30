#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
存储辅助工具类
提供CSV存储的公共方法
"""
import asyncio
import math
from io import StringIO
from pathlib import Path
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

import aiofiles
import aiofiles.os
from loguru import logger


class BaseCSVStorage(ABC):
    """CSV存储基类"""
    
    def __init__(self, base_path: str, flush_interval: float = 1.0, buffer_size: int = 1000):
        """
        初始化CSV存储基类
        
        Args:
            base_path: 基础存储路径
            flush_interval: 刷新间隔（秒）
            buffer_size: 缓冲区大小，达到此大小时触发写入
        """
        self.base_path = Path(base_path)
        self._write_buffers: Dict[str, List[Dict[str, Any]]] = {}
        self._buffer_lock = asyncio.Lock()  # 单一锁，减少锁对象数量
        self._flush_interval = flush_interval
        self._buffer_size = buffer_size
        self._running = False
        self._background_task: Optional[asyncio.Task] = None
        
        # 预构建CSV表头字符串
        self._header_line: Optional[str] = None
    
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
    
    def _get_header_line(self) -> str:
        """获取CSV表头行（缓存）"""
        if self._header_line is None:
            self._header_line = ','.join(self.csv_fields) + '\n'
        return self._header_line
    
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
        async with self._buffer_lock:
            if file_key not in self._write_buffers:
                self._write_buffers[file_key] = []
            self._write_buffers[file_key].append(csv_row)
            
            # 缓冲区满时立即触发写入
            if len(self._write_buffers[file_key]) >= self._buffer_size:
                data_to_write = self._write_buffers[file_key]
                self._write_buffers[file_key] = []
                # 释放锁后再写入
                asyncio.create_task(self._flush_buffer_data(file_key, data_to_write))
    
    async def _background_writer(self) -> None:
        """后台写入任务"""
        logger.info(f"{self.storage_name}后台写入任务启动")
        
        while self._running:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_all_buffers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{self.storage_name}后台写入任务异常: {e}", exc_info=True)
        
        logger.info(f"{self.storage_name}后台写入任务停止")
    
    async def _flush_all_buffers(self) -> None:
        """刷新所有缓冲区"""
        # 快速获取所有待写入数据
        async with self._buffer_lock:
            if not self._write_buffers:
                return
            buffers_to_flush = self._write_buffers
            self._write_buffers = {}
        
        # 并发写入所有文件
        tasks = []
        for file_key, data in buffers_to_flush.items():
            if data:
                tasks.append(self._flush_buffer_data(file_key, data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _flush_buffer_data(self, file_key: str, data_to_write: List[Dict[str, Any]]) -> None:
        """
        刷新缓冲区数据到文件
        
        Args:
            file_key: 文件key
            data_to_write: 要写入的数据
        """
        try:
            await self._flush_buffer(file_key, data_to_write)
        except Exception as e:
            logger.error(f"刷新{self.storage_name}缓冲区失败: {file_key}, {e}")
            # 写入失败时放回缓冲区
            async with self._buffer_lock:
                if file_key not in self._write_buffers:
                    self._write_buffers[file_key] = []
                self._write_buffers[file_key].extend(data_to_write)
    
    @abstractmethod
    async def _flush_buffer(self, file_key: str, data_to_write: List[Dict[str, Any]]) -> None:
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
                return ''
            return repr(value)
        if isinstance(value, int):
            return str(value)
        return str(value)

    def _build_csv_content(self, data_to_write: List[Dict[str, Any]], include_header: bool) -> str:
        """
        批量构建CSV内容
        
        Args:
            data_to_write: 要写入的数据列表
            include_header: 是否包含表头
            
        Returns:
            CSV内容字符串
        """
        buffer = StringIO()
        
        if include_header:
            buffer.write(self._get_header_line())
        
        fields = self.csv_fields
        for row in data_to_write:
            line = ','.join(self._format_value(row.get(field, '')) for field in fields)
            buffer.write(line)
            buffer.write('\n')
        
        return buffer.getvalue()

    async def _write_csv_file(
        self, 
        file_path: Path, 
        data_to_write: List[Dict[str, Any]]
    ) -> None:
        """
        写入CSV文件
        
        Args:
            file_path: 文件路径
            data_to_write: 要写入的数据列表
        """
        file_exists = file_path.exists()
        
        # 批量构建CSV内容
        content = self._build_csv_content(data_to_write, include_header=not file_exists)
        
        # 一次性写入
        async with aiofiles.open(file_path, mode='a', encoding='utf-8') as f:
            await f.write(content)
        
        logger.debug(f"写入{self.storage_name} CSV成功: {file_path}, {len(data_to_write)}条")
    
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

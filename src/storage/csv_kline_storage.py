#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV K线数据存储引擎
按交易日、周期、合约分文件存储
存储路径: data/klines/{交易日}/{周期}/{合约代码}.csv
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
import aiofiles
import aiofiles.os

from .kline_period import KLineBar


class CSVKLineStorage:
    """CSV K线存储引擎"""
    
    def __init__(self, base_path: str = "./data/klines"):
        """
        初始化CSV K线存储引擎
        
        Args:
            base_path: 基础存储路径
        """
        self.base_path = Path(base_path)
        self._write_buffers: Dict[str, list] = {}  # {file_key: [kline_data]}
        self._buffer_locks: Dict[str, asyncio.Lock] = {}
        self._flush_interval = 5.0  # K线刷新间隔（秒），比tick长
        self._running = False
        self._background_task: Optional[asyncio.Task] = None
        
        # CSV字段顺序（与现有格式保持一致）
        self._csv_fields = [
            'datetime',
            'open',
            'high',
            'low',
            'close',
            'volume',
            'turnover',
            'open_interest',
            'tick_count',
        ]
    
    async def initialize(self):
        """初始化存储引擎"""
        # 创建基础目录
        await aiofiles.os.makedirs(self.base_path, exist_ok=True)
        
        # 启动后台写入任务
        self._running = True
        self._background_task = asyncio.create_task(self._background_writer())
        
        logger.info(f"CSV K线存储引擎初始化成功，存储路径: {self.base_path}")
    
    async def close(self):
        """关闭存储引擎"""
        self._running = False
        
        if self._background_task:
            await self._background_task
        
        # 刷新所有缓冲区
        await self._flush_all_buffers()
        
        logger.info("CSV K线存储引擎已关闭")
    
    async def store_kline(self, kline_bar: KLineBar):
        """
        存储K线数据
        
        Args:
            kline_bar: K线数据对象
        """
        try:
            trading_day = kline_bar.trading_day
            instrument_id = kline_bar.instrument_id
            period = kline_bar.period.value
            
            if not trading_day or not instrument_id:
                logger.warning(f"K线数据缺少交易日或合约代码")
                return
            
            # 生成文件key: trading_day/period/instrument_id
            file_key = f"{trading_day}_{period}_{instrument_id}"
            
            # 获取或创建锁
            if file_key not in self._buffer_locks:
                self._buffer_locks[file_key] = asyncio.Lock()
            
            # 转换数据格式
            csv_row = self._convert_to_csv_row(kline_bar)
            
            # 添加到缓冲区
            async with self._buffer_locks[file_key]:
                if file_key not in self._write_buffers:
                    self._write_buffers[file_key] = []
                self._write_buffers[file_key].append(csv_row)
            
            logger.debug(f"K线数据已缓冲: {instrument_id} {period}, 交易日: {trading_day}")
            
        except Exception as e:
            logger.error(f"存储K线数据失败: {e}", exc_info=True)
    
    def _convert_to_csv_row(self, kline_bar: KLineBar) -> Dict[str, Any]:
        """
        转换K线数据为CSV行格式
        
        Args:
            kline_bar: K线数据对象
            
        Returns:
            CSV行数据字典
        """
        # 生成时间戳（与现有格式保持一致）
        if kline_bar.start_time:
            datetime_str = kline_bar.start_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            datetime_str = ""
        
        csv_row = {
            'datetime': datetime_str,
            'open': kline_bar.open,
            'high': kline_bar.high,
            'low': kline_bar.low,
            'close': kline_bar.close,
            'volume': kline_bar.volume,
            'turnover': kline_bar.turnover,
            'open_interest': kline_bar.open_interest,
            'tick_count': kline_bar.tick_count,
        }
        
        return csv_row
    
    async def _background_writer(self):
        """后台写入任务"""
        logger.info("CSV K线后台写入任务启动")
        
        while self._running:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_all_buffers()
            except Exception as e:
                logger.error(f"K线后台写入任务异常: {e}", exc_info=True)
        
        logger.info("CSV K线后台写入任务停止")
    
    async def _flush_all_buffers(self):
        """刷新所有缓冲区"""
        if not self._write_buffers:
            return
        
        # 获取所有需要刷新的文件
        file_keys = list(self._write_buffers.keys())
        
        for file_key in file_keys:
            try:
                await self._flush_buffer(file_key)
            except Exception as e:
                logger.error(f"刷新K线缓冲区失败: {file_key}, {e}")
    
    async def _flush_buffer(self, file_key: str):
        """
        刷新单个缓冲区
        
        Args:
            file_key: 文件key (格式: trading_day_period_instrument_id)
        """
        async with self._buffer_locks[file_key]:
            if file_key not in self._write_buffers or not self._write_buffers[file_key]:
                return
            
            # 获取数据
            data_to_write = self._write_buffers[file_key]
            self._write_buffers[file_key] = []
        
        # 解析文件key
        parts = file_key.split('_', 2)
        if len(parts) != 3:
            logger.error(f"无效的K线文件key: {file_key}")
            return
        
        trading_day, period, instrument_id = parts
        
        # 构建文件路径: data/klines/{交易日}/{周期}/{合约代码}.csv
        period_dir = self.base_path / trading_day / period
        await aiofiles.os.makedirs(period_dir, exist_ok=True)
        
        file_path = period_dir / f"{instrument_id}.csv"
        
        # 检查文件是否存在（决定是否写入表头）
        file_exists = file_path.exists()
        
        # 写入数据
        try:
            async with aiofiles.open(file_path, mode='a', newline='', encoding='utf-8') as f:
                # 如果文件不存在，先写入表头
                if not file_exists:
                    header_line = ','.join(self._csv_fields) + '\n'
                    await f.write(header_line)
                
                # 写入数据行
                for row in data_to_write:
                    values = [str(row.get(field, '')) for field in self._csv_fields]
                    line = ','.join(values) + '\n'
                    await f.write(line)
            
            logger.debug(f"写入K线CSV成功: {file_path}, {len(data_to_write)}条")
            
        except Exception as e:
            logger.error(f"写入K线CSV失败: {file_path}, {e}")
            # 将数据放回缓冲区
            async with self._buffer_locks[file_key]:
                self._write_buffers[file_key].extend(data_to_write)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        total_buffered = sum(len(buffer) for buffer in self._write_buffers.values())
        
        return {
            "storage_type": "CSV_KLine",
            "base_path": str(self.base_path),
            "buffered_files": len(self._write_buffers),
            "buffered_records": total_buffered,
            "running": self._running,
        }

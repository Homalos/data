#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV Tick数据存储引擎
按交易日和合约分文件存储
"""
import asyncio
import csv
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
import aiofiles
import aiofiles.os


class CSVTickStorage:
    """CSV Tick存储引擎"""
    
    def __init__(self, base_path: str = "./data/ticks"):
        """
        初始化CSV存储引擎
        
        Args:
            base_path: 基础存储路径
        """
        self.base_path = Path(base_path)
        self._write_buffers: Dict[str, list] = {}  # {file_key: [tick_data]}
        self._buffer_locks: Dict[str, asyncio.Lock] = {}
        self._flush_interval = 1.0  # 刷新间隔（秒）
        self._batch_size = 100  # 批量写入大小
        self._running = False
        self._background_task: Optional[asyncio.Task] = None
        
        # CSV字段顺序
        self._csv_fields = [
            'Timestamp',
            'TradingDay',
            'InstrumentID',
            'ExchangeID',
            'ExchangeInstID',
            'LastPrice',
            'PreSettlementPrice',
            'PreClosePrice',
            'PreOpenInterest',
            'OpenPrice',
            'HighestPrice',
            'LowestPrice',
            'Volume',
            'Turnover',
            'OpenInterest',
            'ClosePrice',
            'SettlementPrice',
            'UpperLimitPrice',
            'LowerLimitPrice',
            'PreDelta',
            'CurrDelta',
            'UpdateTime',
            'UpdateMillisec',
            'BidPrice1', 'BidVolume1', 'AskPrice1', 'AskVolume1',
            'BidPrice2', 'BidVolume2', 'AskPrice2', 'AskVolume2',
            'BidPrice3', 'BidVolume3', 'AskPrice3', 'AskVolume3',
            'BidPrice4', 'BidVolume4', 'AskPrice4', 'AskVolume4',
            'BidPrice5', 'BidVolume5', 'AskPrice5', 'AskVolume5',
            'AveragePrice',
            'ActionDay',
            'BandingUpperPrice',
            'BandingLowerPrice'
        ]
    
    async def initialize(self):
        """初始化存储引擎"""
        # 创建基础目录
        await aiofiles.os.makedirs(self.base_path, exist_ok=True)
        
        # 启动后台写入任务
        self._running = True
        self._background_task = asyncio.create_task(self._background_writer())
        
        logger.info(f"CSV Tick存储引擎初始化成功，存储路径: {self.base_path}")
    
    async def close(self):
        """关闭存储引擎"""
        self._running = False
        
        if self._background_task:
            await self._background_task
        
        # 刷新所有缓冲区
        await self._flush_all_buffers()
        
        logger.info("CSV Tick存储引擎已关闭")
    
    async def store_tick(self, tick_data: Dict[str, Any]):
        """
        存储单条tick数据
        
        Args:
            tick_data: tick数据字典
        """
        try:
            # 提取关键信息
            trading_day = tick_data.get('TradingDay', '')
            instrument_id = tick_data.get('InstrumentID', '')
            
            if not trading_day or not instrument_id:
                logger.warning(f"Tick数据缺少交易日或合约代码: {tick_data}")
                return
            
            # 生成文件key
            file_key = f"{trading_day}_{instrument_id}"
            
            # 获取或创建锁
            if file_key not in self._buffer_locks:
                self._buffer_locks[file_key] = asyncio.Lock()
            
            # 转换数据格式
            csv_row = self._convert_to_csv_row(tick_data)
            
            # 添加到缓冲区
            async with self._buffer_locks[file_key]:
                if file_key not in self._write_buffers:
                    self._write_buffers[file_key] = []
                self._write_buffers[file_key].append(csv_row)
            
            logger.debug(f"Tick数据已缓冲: {instrument_id}, 交易日: {trading_day}")
            
        except Exception as e:
            logger.error(f"存储tick数据失败: {e}", exc_info=True)
    
    def _convert_to_csv_row(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换tick数据为CSV行格式
        
        Args:
            tick_data: 原始tick数据
            
        Returns:
            CSV行数据字典
        """
        # 生成ISO 8601标准时间戳 (YYYY-MM-DDTHH:mm:ss.sssZ)
        update_time = tick_data.get('UpdateTime', '')
        update_millisec = tick_data.get('UpdateMillisec', 0)
        trading_day = tick_data.get('TradingDay', '')
        
        # 构建ISO 8601时间戳
        if update_time and trading_day:
            # 格式: 2025-12-27T09:30:15.500Z
            timestamp = f"{trading_day[:4]}-{trading_day[4:6]}-{trading_day[6:8]}T{update_time}.{update_millisec:03d}Z"
        else:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            logger.warning(f"Tick数据缺少交易日或更新时间: {tick_data}，使用当前时间戳代替")

        # 映射字段
        csv_row = {
            'Timestamp': timestamp,
            'TradingDay': tick_data.get('TradingDay', ''),
            'InstrumentID': tick_data.get('InstrumentID', ''),
            'ExchangeID': tick_data.get('ExchangeID', ''),
            'ExchangeInstID': tick_data.get('ExchangeInstID', ''),
            'LastPrice': tick_data.get('LastPrice', 0.0),
            'PreSettlementPrice': tick_data.get('PreSettlementPrice', 0.0),
            'PreClosePrice': tick_data.get('PreClosePrice', 0.0),
            'PreOpenInterest': tick_data.get('PreOpenInterest', 0),
            'OpenPrice': tick_data.get('OpenPrice', 0.0),
            'HighestPrice': tick_data.get('HighestPrice', 0.0),
            'LowestPrice': tick_data.get('LowestPrice', 0.0),
            'Volume': tick_data.get('Volume', 0),
            'Turnover': tick_data.get('Turnover', 0.0),
            'OpenInterest': tick_data.get('OpenInterest', 0),
            'ClosePrice': tick_data.get('ClosePrice', 0.0),
            'SettlementPrice': tick_data.get('SettlementPrice', 0.0),
            'UpperLimitPrice': tick_data.get('UpperLimitPrice', 0.0),
            'LowerLimitPrice': tick_data.get('LowerLimitPrice', 0.0),
            'PreDelta': tick_data.get('PreDelta', 0.0),
            'CurrDelta': tick_data.get('CurrDelta', 0.0),
            'UpdateTime': update_time,
            'UpdateMillisec': update_millisec,
            'BidPrice1': tick_data.get('BidPrice1', 0.0),
            'BidVolume1': tick_data.get('BidVolume1', 0),
            'AskPrice1': tick_data.get('AskPrice1', 0.0),
            'AskVolume1': tick_data.get('AskVolume1', 0),
            'BidPrice2': tick_data.get('BidPrice2', 0.0),
            'BidVolume2': tick_data.get('BidVolume2', 0),
            'AskPrice2': tick_data.get('AskPrice2', 0.0),
            'AskVolume2': tick_data.get('AskVolume2', 0),
            'BidPrice3': tick_data.get('BidPrice3', 0.0),
            'BidVolume3': tick_data.get('BidVolume3', 0),
            'AskPrice3': tick_data.get('AskPrice3', 0.0),
            'AskVolume3': tick_data.get('AskVolume3', 0),
            'BidPrice4': tick_data.get('BidPrice4', 0.0),
            'BidVolume4': tick_data.get('BidVolume4', 0),
            'AskPrice4': tick_data.get('AskPrice4', 0.0),
            'AskVolume4': tick_data.get('AskVolume4', 0),
            'BidPrice5': tick_data.get('BidPrice5', 0.0),
            'BidVolume5': tick_data.get('BidVolume5', 0),
            'AskPrice5': tick_data.get('AskPrice5', 0.0),
            'AskVolume5': tick_data.get('AskVolume5', 0),
            'AveragePrice': tick_data.get('AveragePrice', 0.0),
            'ActionDay': tick_data.get('ActionDay', ''),
            'BandingUpperPrice': tick_data.get('BandingUpperPrice', 0.0),
            'BandingLowerPrice': tick_data.get('BandingLowerPrice', 0.0)
        }
        
        return csv_row
    
    async def _background_writer(self):
        """后台写入任务"""
        logger.info("CSV后台写入任务启动")
        
        while self._running:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_all_buffers()
            except Exception as e:
                logger.error(f"后台写入任务异常: {e}", exc_info=True)
        
        logger.info("CSV后台写入任务停止")
    
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
                logger.error(f"刷新缓冲区失败: {file_key}, {e}")
    
    async def _flush_buffer(self, file_key: str):
        """
        刷新单个缓冲区
        
        Args:
            file_key: 文件key (格式: trading_day_instrument_id)
        """
        async with self._buffer_locks[file_key]:
            if file_key not in self._write_buffers or not self._write_buffers[file_key]:
                return
            
            # 获取数据
            data_to_write = self._write_buffers[file_key]
            self._write_buffers[file_key] = []
        
        # 解析文件key
        parts = file_key.split('_', 1)
        if len(parts) != 2:
            logger.error(f"无效的文件key: {file_key}")
            return
        
        trading_day, instrument_id = parts
        
        # 构建文件路径
        day_dir = self.base_path / trading_day
        await aiofiles.os.makedirs(day_dir, exist_ok=True)
        
        file_path = day_dir / f"{instrument_id}.csv"
        
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
            
            logger.debug(f"写入CSV成功: {file_path}, {len(data_to_write)}条")
            
        except Exception as e:
            logger.error(f"写入CSV失败: {file_path}, {e}")
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
            "storage_type": "CSV",
            "base_path": str(self.base_path),
            "buffered_files": len(self._write_buffers),
            "buffered_records": total_buffered,
            "running": self._running,
        }

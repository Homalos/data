#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tick数据存储引擎
"""
import asyncio
from typing import Optional, Dict, List
from datetime import datetime
from loguru import logger

from .influxdb_client import InfluxDBClientWrapper
from .tick_buffer import TickBuffer


class TickStorage:
    """
    Tick数据存储引擎
    
    负责接收tick数据并持久化到InfluxDB，支持批量写入和异步处理
    """
    
    def __init__(self, influxdb_config):
        """
        初始化Tick存储引擎
        
        Args:
            influxdb_config: InfluxDB配置对象
        """
        self.config = influxdb_config
        self._influxdb: Optional[InfluxDBClientWrapper] = None
        self._buffer: Optional[TickBuffer] = None
        self._write_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._write_count: int = 0
        self._error_count: int = 0
    
    async def initialize(self):
        """初始化存储引擎"""
        try:
            # 初始化InfluxDB客户端
            self._influxdb = InfluxDBClientWrapper(
                host=self.config.host,
                token=self.config.token,
                database=self.config.database
            )
            await self._influxdb.connect()
            
            # 初始化缓冲区
            self._buffer = TickBuffer(
                max_size=self.config.batch_size,
                flush_interval=self.config.flush_interval
            )
            
            # 启动后台写入任务
            self._running = True
            self._write_task = asyncio.create_task(self._background_writer())
            
            logger.info("Tick存储引擎初始化成功")
            logger.info(f"批量大小: {self.config.batch_size}, 刷新间隔: {self.config.flush_interval}秒")
            
        except Exception as e:
            logger.error(f"Tick存储引擎初始化失败: {e}", exc_info=True)
            raise
    
    async def store_tick(self, tick_data: Dict):
        """
        存储单条tick数据（非阻塞）
        
        Args:
            tick_data: tick数据字典
        """
        if not self._buffer:
            logger.warning("存储引擎未初始化，忽略tick数据")
            return
        
        # 添加到缓冲区（非阻塞）
        self._buffer.add(tick_data)
        logger.debug(f"添加tick到缓冲区: {tick_data.get('InstrumentID')}, 当前缓冲: {self._buffer.size()}/{self._buffer.max_size}")
        
        # 如果缓冲区满了，立即触发写入
        if self._buffer.is_full():
            logger.info(f"缓冲区已满({self._buffer.size()}条)，触发立即写入")
    
    async def _background_writer(self):
        """后台批量写入任务"""
        logger.info("后台写入任务启动")
        
        while self._running:
            try:
                # 等待刷新间隔
                await asyncio.sleep(self._buffer.flush_interval)
                
                logger.debug(f"后台写入任务唤醒，检查缓冲区（当前: {self._buffer.size()}条）")
                
                # 获取待写入数据
                batch = await self._buffer.get_batch()
                
                if batch:
                    logger.info(f"准备写入 {len(batch)} 条tick数据到InfluxDB")
                    # 批量写入InfluxDB
                    await self._write_batch(batch)
                else:
                    logger.debug("缓冲区为空，跳过写入")
                
            except asyncio.CancelledError:
                logger.info("后台写入任务被取消")
                break
            except Exception as e:
                logger.error(f"后台写入失败: {e}", exc_info=True)
                self._error_count += 1
        
        logger.info("后台写入任务停止")
    
    async def _write_batch(self, batch: List[Dict]):
        """
        批量写入tick数据到InfluxDB
        
        Args:
            batch: tick数据列表
        """
        if not batch:
            return
        
        try:
            logger.info(f"开始转换 {len(batch)} 条tick数据为InfluxDB格式")
            
            # 转换为InfluxDB数据点格式
            points = []
            for tick in batch:
                point = self._convert_to_point(tick)
                if point:
                    points.append(point)
            
            if not points:
                logger.warning("没有有效的数据点可写入")
                return
            
            logger.info(f"准备写入 {len(points)} 个数据点到InfluxDB")
            
            # 写入InfluxDB
            await self._influxdb.write_points(points)
            
            self._write_count += len(points)
            logger.info(f"✅ 成功写入 {len(points)} 条tick数据（累计: {self._write_count}）")
            
        except Exception as e:
            logger.error(f"❌ 批量写入失败: {e}", exc_info=True)
            self._error_count += 1
            raise
    
    def _convert_to_point(self, tick_data: Dict) -> Optional[Dict]:
        """
        将tick数据转换为InfluxDB数据点格式
        
        Args:
            tick_data: tick数据字典
            
        Returns:
            InfluxDB数据点字典，格式错误返回None
        """
        try:
            instrument_id = tick_data.get("InstrumentID")
            if not instrument_id:
                logger.warning("tick数据缺少InstrumentID")
                return None
            
            # 解析时间戳
            timestamp = self._parse_timestamp(tick_data)
            
            # 使用合约ID作为measurement名称（按合约分表）
            measurement = f"tick_{instrument_id}"
            
            # 构建数据点（InfluxDB 3.x格式）
            point = {
                "measurement": measurement,
                "tags": {
                    "exchange_id": tick_data.get("ExchangeID", ""),
                    "trading_day": tick_data.get("TradingDay", ""),
                },
                "fields": {
                    "last_price": float(tick_data.get("LastPrice", 0)),
                    "volume": int(tick_data.get("Volume", 0)),
                    "turnover": float(tick_data.get("Turnover", 0)),
                    "open_interest": float(tick_data.get("OpenInterest", 0)),
                    "bid_price1": float(tick_data.get("BidPrice1", 0)),
                    "bid_volume1": int(tick_data.get("BidVolume1", 0)),
                    "ask_price1": float(tick_data.get("AskPrice1", 0)),
                    "ask_volume1": int(tick_data.get("AskVolume1", 0)),
                    "open_price": float(tick_data.get("OpenPrice", 0)),
                    "high_price": float(tick_data.get("HighestPrice", 0)),
                    "low_price": float(tick_data.get("LowestPrice", 0)),
                    "close_price": float(tick_data.get("ClosePrice", 0)),
                },
                "time": timestamp,
            }
            
            return point
            
        except Exception as e:
            logger.error(f"转换数据点失败: {e}", exc_info=True)
            return None
    
    def _parse_timestamp(self, tick_data: Dict) -> datetime:
        """
        解析tick时间戳
        
        Args:
            tick_data: tick数据字典
            
        Returns:
            Python datetime对象
        """
        try:
            # 获取交易日和更新时间
            trading_day = tick_data.get("TradingDay", "")
            update_time = tick_data.get("UpdateTime", "")
            update_millisec = tick_data.get("UpdateMillisec", 0)
            
            # 解析时间
            if trading_day and update_time:
                # 格式: TradingDay="20251223", UpdateTime="09:30:15"
                datetime_str = f"{trading_day} {update_time}"
                dt = datetime.strptime(datetime_str, "%Y%m%d %H:%M:%S")
                
                # 添加毫秒
                if update_millisec:
                    from datetime import timedelta
                    dt = dt + timedelta(milliseconds=update_millisec)
                
                return dt
            else:
                # 如果没有时间信息，使用当前时间
                return datetime.now()
                
        except Exception as e:
            logger.warning(f"解析时间戳失败: {e}，使用当前时间")
            return datetime.now()
    
    def get_stats(self) -> Dict:
        """
        获取存储统计信息
        
        Returns:
            统计信息字典
        """
        buffer_stats = self._buffer.get_stats() if self._buffer else {}
        
        return {
            "write_count": self._write_count,
            "error_count": self._error_count,
            "buffer": buffer_stats,
            "running": self._running,
        }
    
    async def close(self):
        """关闭存储引擎"""
        if not self._running:
            return
        
        logger.info("正在关闭Tick存储引擎...")
        
        # 停止后台任务
        self._running = False
        if self._write_task:
            self._write_task.cancel()
            try:
                await self._write_task
            except asyncio.CancelledError:
                pass
        
        # 刷新剩余数据
        if self._buffer:
            remaining = self._buffer.get_all()
            if remaining:
                logger.info(f"刷新剩余 {len(remaining)} 条数据")
                await self._write_batch(remaining)
        
        # 关闭InfluxDB连接
        if self._influxdb:
            self._influxdb.close()
        
        # 打印统计信息
        stats = self.get_stats()
        logger.info(f"Tick存储引擎已关闭 - 总写入: {stats['write_count']}, 错误: {stats['error_count']}")

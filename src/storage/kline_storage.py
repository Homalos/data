#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
K线存储引擎
"""
import asyncio
from typing import Optional, Dict, List
from datetime import datetime
from loguru import logger

from .influxdb_client import InfluxDBClientWrapper
from .kline_period import KLineBar


class KLineStorage:
    """
    K线存储引擎
    
    负责将K线数据持久化到InfluxDB
    """
    
    def __init__(self, influxdb_config):
        """
        初始化K线存储引擎
        
        Args:
            influxdb_config: InfluxDB配置对象
        """
        self.config = influxdb_config
        self._influxdb: Optional[InfluxDBClientWrapper] = None
        self._write_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
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
            
            # 启动后台写入任务
            self._running = True
            self._write_task = asyncio.create_task(self._background_writer())
            
            logger.info("K线存储引擎初始化成功")
            
        except Exception as e:
            logger.error(f"K线存储引擎初始化失败: {e}", exc_info=True)
            raise
    
    async def store_kline(self, kline_bar: KLineBar):
        """
        存储单根K线（非阻塞）
        
        Args:
            kline_bar: K线对象
        """
        if not self._running:
            logger.warning("存储引擎未运行，忽略K线数据")
            return
        
        try:
            # 添加到写入队列
            await self._write_queue.put(kline_bar)
        except asyncio.QueueFull:
            logger.error("K线写入队列已满，丢弃数据")
            self._error_count += 1
    
    async def _background_writer(self):
        """后台写入任务"""
        logger.info("K线后台写入任务启动")
        
        while self._running:
            try:
                # 从队列获取K线（超时1秒）
                try:
                    kline_bar = await asyncio.wait_for(
                        self._write_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 写入InfluxDB
                await self._write_kline(kline_bar)
                
            except asyncio.CancelledError:
                logger.info("K线后台写入任务被取消")
                break
            except Exception as e:
                logger.error(f"K线后台写入失败: {e}", exc_info=True)
                self._error_count += 1
        
        logger.info("K线后台写入任务停止")
    
    async def _write_kline(self, kline_bar: KLineBar):
        """
        写入单根K线到InfluxDB
        
        Args:
            kline_bar: K线对象
        """
        try:
            # 转换为InfluxDB数据点格式
            point = self._convert_to_point(kline_bar)
            if not point:
                logger.warning("K线数据转换失败")
                return
            
            # 写入InfluxDB
            await self._influxdb.write_points([point])
            
            self._write_count += 1
            logger.debug(
                f"K线写入成功: {kline_bar.instrument_id} {kline_bar.period.value} "
                f"(累计: {self._write_count})"
            )
            
        except Exception as e:
            logger.error(f"K线写入失败: {e}", exc_info=True)
            self._error_count += 1
            raise
    
    def _convert_to_point(self, kline_bar: KLineBar) -> Optional[Dict]:
        """
        将K线转换为InfluxDB数据点格式
        
        Args:
            kline_bar: K线对象
            
        Returns:
            InfluxDB数据点字典，格式错误返回None
        """
        try:
            if not kline_bar.start_time:
                logger.warning("K线缺少开始时间")
                return None
            
            # 使用"周期_合约ID"作为measurement名称（按合约分表）
            measurement = f"{kline_bar.period.measurement_name}_{kline_bar.instrument_id}"
            
            # 构建数据点（InfluxDB 3.x格式）
            point = {
                "measurement": measurement,
                "tags": {
                    "trading_day": kline_bar.trading_day,
                    "period": kline_bar.period.value,
                },
                "fields": {
                    "open": float(kline_bar.open),
                    "high": float(kline_bar.high),
                    "low": float(kline_bar.low),
                    "close": float(kline_bar.close),
                    "volume": int(kline_bar.volume),
                    "turnover": float(kline_bar.turnover),
                    "open_interest": float(kline_bar.open_interest),
                    "tick_count": int(kline_bar.tick_count),
                },
                "time": kline_bar.start_time,
            }
            
            return point
            
        except Exception as e:
            logger.error(f"转换K线数据点失败: {e}", exc_info=True)
            return None
    
    def get_stats(self) -> Dict:
        """
        获取存储统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "write_count": self._write_count,
            "error_count": self._error_count,
            "queue_size": self._write_queue.qsize(),
            "running": self._running,
        }
    
    async def close(self):
        """关闭存储引擎"""
        if not self._running:
            return
        
        logger.info("正在关闭K线存储引擎...")
        
        # 停止后台任务
        self._running = False
        if self._write_task:
            self._write_task.cancel()
            try:
                await self._write_task
            except asyncio.CancelledError:
                pass
        
        # 刷新队列中剩余的K线
        remaining_count = 0
        while not self._write_queue.empty():
            try:
                kline_bar = self._write_queue.get_nowait()
                await self._write_kline(kline_bar)
                remaining_count += 1
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                logger.error(f"刷新剩余K线失败: {e}")
        
        if remaining_count > 0:
            logger.info(f"刷新了 {remaining_count} 根剩余K线")
        
        # 关闭InfluxDB连接
        if self._influxdb:
            self._influxdb.close()
        
        # 打印统计信息
        stats = self.get_stats()
        logger.info(
            f"K线存储引擎已关闭 - "
            f"总写入: {stats['write_count']}, 错误: {stats['error_count']}"
        )

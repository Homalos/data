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
from .failure_handler import FailureHandler


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
        self._write_queue: asyncio.Queue = asyncio.Queue()  # 移除maxsize限制，不丢弃任何数据
        self._write_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._write_count: int = 0
        self._error_count: int = 0
        self._batch_size: int = 100  # K线批量写入大小
        self._failure_handler: Optional[FailureHandler] = None
        self._max_retries: int = 3  # 最大重试次数
    
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
            
            # 初始化失败数据处理器
            self._failure_handler = FailureHandler(failure_dir="data/failures")
            
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
        
        # 添加到写入队列（无容量限制，不会丢弃数据）
        await self._write_queue.put(kline_bar)
        
        # 背压警告：当队列积压过多时发出警告
        queue_size = self._write_queue.qsize()
        if queue_size > 5000:
            logger.warning(f"⚠️ K线队列积压严重: {queue_size}条，写入速度可能跟不上接收速度")
        elif queue_size > 2000:
            logger.info(f"K线队列积压: {queue_size}条")
    
    async def _background_writer(self):
        """后台批量写入任务"""
        logger.info("K线后台写入任务启动（批量模式）")
        batch = []
        
        while self._running:
            try:
                # 从队列获取K线（超时1秒）
                try:
                    kline_bar = await asyncio.wait_for(
                        self._write_queue.get(),
                        timeout=1.0
                    )
                    batch.append(kline_bar)
                except asyncio.TimeoutError:
                    pass
                
                # 达到批量大小或队列为空时，执行批量写入
                if len(batch) >= self._batch_size or (batch and self._write_queue.empty()):
                    await self._write_kline_batch(batch)
                    batch.clear()
                
            except asyncio.CancelledError:
                logger.info("K线后台写入任务被取消")
                break
            except Exception as e:
                logger.error(f"K线后台写入失败: {e}", exc_info=True)
                self._error_count += 1
        
        # 刷新剩余数据
        if batch:
            logger.info(f"刷新剩余 {len(batch)} 根K线")
            await self._write_kline_batch(batch)
        
        logger.info("K线后台写入任务停止")
    
    async def _write_kline_batch(self, batch: List[KLineBar]):
        """
        批量写入K线到InfluxDB（带重试机制）
        
        Args:
            batch: K线对象列表
        """
        if not batch:
            return
        
        try:
            # 转换为InfluxDB数据点格式
            points = []
            for kline_bar in batch:
                point = self._convert_to_point(kline_bar)
                if point:
                    points.append(point)
            
            if not points:
                logger.warning("没有有效的K线数据点可写入")
                return
            
            # 带重试的写入
            success = await self._write_with_retry(points)
            
            if success:
                self._write_count += len(points)
                logger.info(
                    f"✅ 批量写入 {len(points)} 根K线（累计: {self._write_count}）"
                )
            else:
                # 保存失败数据到本地文件
                logger.error(f"❌ 写入失败，保存到本地文件")
                await self._failure_handler.save_failed_batch(points, "kline")
            
        except Exception as e:
            logger.error(f"❌ K线批量写入异常: {e}", exc_info=True)
            self._error_count += 1
    
    async def _write_with_retry(self, points: List[Dict]) -> bool:
        """
        带重试机制的写入
        
        Args:
            points: 数据点列表
            
        Returns:
            是否写入成功
        """
        for attempt in range(self._max_retries):
            try:
                await self._influxdb.write_points(points)
                return True
                
            except Exception as e:
                if attempt < self._max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                    logger.warning(
                        f"⚠️ K线写入失败，{wait_time}秒后重试 "
                        f"({attempt + 1}/{self._max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ K线写入失败，已达最大重试次数 ({self._max_retries}): {e}")
                    self._error_count += 1
                    return False
        
        return False
    
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
            # 统一转换为小写，避免大小写不一致问题
            measurement = f"{kline_bar.period.measurement_name}_{kline_bar.instrument_id.lower()}"
            
            # 构建数据点（InfluxDB 3.x格式）
            point = {
                "measurement": measurement,
                "tags": {
                    "instrument_id": kline_bar.instrument_id,  # 保留原始大小写用于查询
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
        failure_stats = self._failure_handler.get_stats() if self._failure_handler else {}
        
        return {
            "write_count": self._write_count,
            "error_count": self._error_count,
            "queue_size": self._write_queue.qsize(),
            "failure": failure_stats,
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
        
        # 刷新队列中剩余的K线（批量处理）
        remaining_batch = []
        while not self._write_queue.empty():
            try:
                kline_bar = self._write_queue.get_nowait()
                remaining_batch.append(kline_bar)
            except asyncio.QueueEmpty:
                break
        
        if remaining_batch:
            logger.info(f"刷新剩余 {len(remaining_batch)} 根K线")
            try:
                await self._write_kline_batch(remaining_batch)
            except Exception as e:
                logger.error(f"刷新剩余K线失败: {e}")
        
        # 关闭InfluxDB连接
        if self._influxdb:
            self._influxdb.close()
        
        # 打印统计信息
        stats = self.get_stats()
        logger.info(
            f"K线存储引擎已关闭 - "
            f"总写入: {stats['write_count']}, 错误: {stats['error_count']}"
        )

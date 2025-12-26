#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
K线合成器 - 实时合成多周期K线
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, List

from loguru import logger

from .kline_period import KLinePeriod, KLineBar


class KLineBuilder:
    """
    K线合成器
    
    负责从tick数据实时合成多周期K线
    """
    
    def __init__(self, kline_storage, enabled_periods: List[str] = None):
        """
        初始化K线合成器
        
        Args:
            kline_storage: K线存储引擎实例
            enabled_periods: 启用的周期列表，如 ["1m", "5m", "1d"]
        """
        self.kline_storage = kline_storage
        
        # 解析启用的周期
        if enabled_periods:
            self.enabled_periods = [
                KLinePeriod.from_string(p) for p in enabled_periods
            ]
        else:
            # 默认启用所有周期
            self.enabled_periods = KLinePeriod.get_all_periods()
        
        # 为每个合约的每个周期维护当前K线
        # 结构: {instrument_id: {period: KLineBar}}
        self.current_bars: Dict[str, Dict[KLinePeriod, KLineBar]] = {}
        
        # 统计信息
        self._total_ticks = 0
        self._total_bars = 0
        
        logger.info(f"K线合成器初始化成功，启用周期: {[p.value for p in self.enabled_periods]}")
    
    async def on_tick(self, tick_data: Dict):
        """
        处理tick数据，更新所有周期K线
        
        Args:
            tick_data: tick数据字典
        """
        instrument_id = tick_data.get("InstrumentID")
        if not instrument_id:
            logger.warning("tick数据缺少InstrumentID")
            return
        
        # 解析tick时间
        current_time = self._parse_tick_time(tick_data)
        if not current_time:
            logger.warning(f"无法解析tick时间: {instrument_id}")
            return
        
        # 确保该合约的K线字典存在
        if instrument_id not in self.current_bars:
            self.current_bars[instrument_id] = {}
        
        # 更新所有启用周期的K线
        for period in self.enabled_periods:
            await self._update_kline(instrument_id, period, tick_data, current_time)
        
        self._total_ticks += 1
    
    async def _update_kline(
        self,
        instrument_id: str,
        period: KLinePeriod,
        tick_data: Dict,
        current_time: datetime
    ):
        """
        更新指定周期的K线
        
        Args:
            instrument_id: 合约代码
            period: K线周期
            tick_data: tick数据
            current_time: 当前时间
        """
        bars = self.current_bars[instrument_id]
        
        # 获取或创建当前K线
        if period not in bars:
            bars[period] = self._create_new_bar(
                instrument_id, period, current_time
            )
        
        current_bar = bars[period]
        
        # 检查是否需要完成当前K线并开始新K线
        if self._should_finish_bar(current_bar, current_time):
            # 标记K线完成
            current_bar.is_finished = True
            current_bar.end_time = current_time
            
            # 保存完成的K线
            await self.kline_storage.store_kline(current_bar)
            self._total_bars += 1
            
            logger.debug(
                f"K线完成: {instrument_id} {period.value} "
                f"O:{current_bar.open} H:{current_bar.high} "
                f"L:{current_bar.low} C:{current_bar.close} "
                f"V:{current_bar.volume}"
            )
            
            # 创建新K线
            bars[period] = self._create_new_bar(
                instrument_id, period, current_time
            )
            current_bar = bars[period]
        
        # 更新K线数据
        current_bar.update(tick_data)
    
    def _create_new_bar(
        self,
        instrument_id: str,
        period: KLinePeriod,
        current_time: datetime
    ) -> KLineBar:
        """
        创建新K线
        
        Args:
            instrument_id: 合约代码
            period: K线周期
            current_time: 当前时间
            
        Returns:
            新创建的K线
        """
        bar = KLineBar(instrument_id, period)
        bar.start_time = self._align_time(current_time, period)
        return bar
    
    def _should_finish_bar(self, bar: KLineBar, current_time: datetime) -> bool:
        """
        判断K线是否应该完成
        
        Args:
            bar: K线对象
            current_time: 当前时间
            
        Returns:
            是否应该完成
        """
        if not bar.start_time:
            return False
        
        period = bar.period
        
        # 日K线特殊处理
        if period == KLinePeriod.DAY_1:
            # 日K线在15:00收盘后完成
            # 或者跨日时完成
            if current_time.hour >= 15 and bar.start_time.day != current_time.day:
                return True
            # 夜盘结束（凌晨2:30后）且是新的交易日
            if current_time.hour >= 3 and bar.start_time.day != current_time.day:
                return True
            return False
        
        # 分钟K线根据周期判断
        minutes = period.minutes
        elapsed = (current_time - bar.start_time).total_seconds() / 60
        
        # 如果经过的时间超过周期，则完成
        return elapsed >= minutes
    
    def _align_time(self, dt: datetime, period: KLinePeriod) -> datetime:
        """
        对齐K线开始时间
        
        Args:
            dt: 当前时间
            period: K线周期
            
        Returns:
            对齐后的时间
        """
        if period == KLinePeriod.DAY_1:
            # 日K线对齐到当天9:00
            return dt.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # 分钟K线对齐
        minutes = period.minutes
        aligned_minute = (dt.minute // minutes) * minutes
        return dt.replace(minute=aligned_minute, second=0, microsecond=0)
    
    def _parse_tick_time(self, tick_data: Dict) -> Optional[datetime]:
        """
        解析tick时间戳
        
        Args:
            tick_data: tick数据字典
            
        Returns:
            Python datetime对象，解析失败返回None
        """
        try:
            trading_day = tick_data.get("TradingDay", "")
            update_time = tick_data.get("UpdateTime", "")
            update_millisec = tick_data.get("UpdateMillisec", 0)
            
            if trading_day and update_time:
                # 格式: TradingDay="20251223", UpdateTime="09:30:15"
                datetime_str = f"{trading_day} {update_time}"
                dt = datetime.strptime(datetime_str, "%Y%m%d %H:%M:%S")
                
                # 添加毫秒
                if update_millisec:
                    dt = dt + timedelta(milliseconds=update_millisec)
                
                # 处理夜盘跨日情况
                # 如果时间在21:00-23:59或00:00-02:30，可能是夜盘
                hour = dt.hour
                if hour >= 21 or hour <= 2:
                    # 夜盘时间，可能需要调整日期
                    # 这里简化处理，实际应根据交易所规则
                    pass
                
                return dt
            else:
                # 如果没有时间信息，使用当前时间
                return datetime.now()
                
        except Exception as e:
            logger.warning(f"解析tick时间失败: {e}")
            return datetime.now()
    
    def get_current_bar(
        self,
        instrument_id: str,
        period: KLinePeriod
    ) -> Optional[KLineBar]:
        """
        获取指定合约和周期的当前K线
        
        Args:
            instrument_id: 合约代码
            period: K线周期
            
        Returns:
            当前K线，不存在返回None
        """
        if instrument_id not in self.current_bars:
            return None
        
        return self.current_bars[instrument_id].get(period)
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        # 统计各周期的K线数量
        period_counts = {period.value: 0 for period in self.enabled_periods}
        
        for instrument_bars in self.current_bars.values():
            for period, bar in instrument_bars.items():
                if bar.tick_count > 0:
                    period_counts[period.value] += 1
        
        return {
            "total_ticks": self._total_ticks,
            "total_bars": self._total_bars,
            "active_instruments": len(self.current_bars),
            "period_counts": period_counts,
            "enabled_periods": [p.value for p in self.enabled_periods],
        }
    
    async def close(self):
        """关闭K线合成器，保存所有未完成的K线"""
        logger.info("正在关闭K线合成器...")
        
        # 保存所有未完成的K线
        saved_count = 0
        for instrument_id, bars in self.current_bars.items():
            for period, bar in bars.items():
                if bar.tick_count > 0:
                    bar.is_finished = True
                    bar.end_time = datetime.now()
                    await self.kline_storage.store_kline(bar)
                    saved_count += 1
        
        if saved_count > 0:
            logger.info(f"保存了 {saved_count} 根未完成的K线")
        
        # 打印统计信息
        stats = self.get_stats()
        logger.info(f"K线合成器统计 - 总tick: {stats['total_ticks']}, 总K线: {stats['total_bars']}")
        logger.info("K线合成器已关闭")

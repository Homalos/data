#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试K线合成模块
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from src.storage.kline_period import KLinePeriod, KLineBar
from src.storage.kline_builder import KLineBuilder


class MockKLineStorage:
    """模拟K线存储"""
    
    def __init__(self):
        self.stored_klines = []
    
    async def store_kline(self, kline_bar: KLineBar):
        """存储K线"""
        self.stored_klines.append(kline_bar)


class TestKLinePeriod:
    """测试K线周期"""
    
    def test_period_minutes(self):
        """测试周期分钟数"""
        assert KLinePeriod.MIN_1.minutes == 1
        assert KLinePeriod.MIN_5.minutes == 5
        assert KLinePeriod.MIN_15.minutes == 15
        assert KLinePeriod.MIN_60.minutes == 60
        assert KLinePeriod.DAY_1.minutes == 1440
    
    def test_measurement_name(self):
        """测试measurement名称"""
        assert KLinePeriod.MIN_1.measurement_name == "kline_1m"
        assert KLinePeriod.MIN_5.measurement_name == "kline_5m"
        assert KLinePeriod.DAY_1.measurement_name == "kline_1d"
    
    def test_from_string(self):
        """测试从字符串创建"""
        period = KLinePeriod.from_string("5m")
        assert period == KLinePeriod.MIN_5
        
        with pytest.raises(ValueError):
            KLinePeriod.from_string("invalid")


class TestKLineBar:
    """测试K线数据结构"""
    
    def test_init(self):
        """测试初始化"""
        bar = KLineBar("rb2505", KLinePeriod.MIN_1)
        assert bar.instrument_id == "rb2505"
        assert bar.period == KLinePeriod.MIN_1
        assert bar.open == 0
        assert bar.tick_count == 0
    
    def test_update(self):
        """测试更新K线"""
        bar = KLineBar("rb2505", KLinePeriod.MIN_1)
        
        # 第一个tick
        tick1 = {
            "LastPrice": 3500.0,
            "Volume": 100,
            "Turnover": 350000.0,
            "OpenInterest": 1000.0,
            "TradingDay": "20251223",
        }
        bar.update(tick1)
        
        assert bar.open == 3500.0
        assert bar.high == 3500.0
        assert bar.low == 3500.0
        assert bar.close == 3500.0
        assert bar.tick_count == 1
        
        # 第二个tick（更高价格）
        tick2 = {
            "LastPrice": 3510.0,
            "Volume": 150,
            "Turnover": 526500.0,
            "OpenInterest": 1050.0,
            "TradingDay": "20251223",
        }
        bar.update(tick2)
        
        assert bar.open == 3500.0  # 开盘价不变
        assert bar.high == 3510.0  # 最高价更新
        assert bar.low == 3500.0   # 最低价不变
        assert bar.close == 3510.0  # 收盘价更新
        assert bar.tick_count == 2
        
        # 第三个tick（更低价格）
        tick3 = {
            "LastPrice": 3490.0,
            "Volume": 200,
            "Turnover": 698000.0,
            "OpenInterest": 1100.0,
            "TradingDay": "20251223",
        }
        bar.update(tick3)
        
        assert bar.open == 3500.0
        assert bar.high == 3510.0
        assert bar.low == 3490.0   # 最低价更新
        assert bar.close == 3490.0  # 收盘价更新
        assert bar.tick_count == 3
    
    def test_to_dict(self):
        """测试转换为字典"""
        bar = KLineBar("rb2505", KLinePeriod.MIN_5)
        bar.start_time = datetime(2025, 12, 23, 9, 30, 0)
        bar.open = 3500.0
        bar.high = 3510.0
        bar.low = 3490.0
        bar.close = 3505.0
        bar.volume = 1000
        
        data = bar.to_dict()
        
        assert data["instrument_id"] == "rb2505"
        assert data["period"] == "5m"
        assert data["open"] == 3500.0
        assert data["high"] == 3510.0
        assert data["low"] == 3490.0
        assert data["close"] == 3505.0
        assert data["volume"] == 1000


class TestKLineBuilder:
    """测试K线合成器"""
    
    @pytest.mark.asyncio
    async def test_init(self):
        """测试初始化"""
        storage = MockKLineStorage()
        builder = KLineBuilder(storage, enabled_periods=["1m", "5m"])
        
        assert len(builder.enabled_periods) == 2
        assert KLinePeriod.MIN_1 in builder.enabled_periods
        assert KLinePeriod.MIN_5 in builder.enabled_periods
    
    @pytest.mark.asyncio
    async def test_align_time(self):
        """测试时间对齐"""
        storage = MockKLineStorage()
        builder = KLineBuilder(storage)
        
        # 1分钟对齐
        dt = datetime(2025, 12, 23, 9, 37, 25)
        aligned = builder._align_time(dt, KLinePeriod.MIN_1)
        assert aligned.minute == 37
        assert aligned.second == 0
        
        # 5分钟对齐
        aligned = builder._align_time(dt, KLinePeriod.MIN_5)
        assert aligned.minute == 35
        assert aligned.second == 0
        
        # 15分钟对齐
        aligned = builder._align_time(dt, KLinePeriod.MIN_15)
        assert aligned.minute == 30
        assert aligned.second == 0
        
        # 日K线对齐
        aligned = builder._align_time(dt, KLinePeriod.DAY_1)
        assert aligned.hour == 9
        assert aligned.minute == 0
        assert aligned.second == 0
    
    @pytest.mark.asyncio
    async def test_should_finish_bar(self):
        """测试K线完成判断"""
        storage = MockKLineStorage()
        builder = KLineBuilder(storage)
        
        # 1分钟K线
        bar = KLineBar("rb2505", KLinePeriod.MIN_1)
        bar.start_time = datetime(2025, 12, 23, 9, 30, 0)
        
        # 30秒后，不应完成
        current_time = datetime(2025, 12, 23, 9, 30, 30)
        assert not builder._should_finish_bar(bar, current_time)
        
        # 1分钟后，应该完成
        current_time = datetime(2025, 12, 23, 9, 31, 0)
        assert builder._should_finish_bar(bar, current_time)
        
        # 5分钟K线
        bar5 = KLineBar("rb2505", KLinePeriod.MIN_5)
        bar5.start_time = datetime(2025, 12, 23, 9, 30, 0)
        
        # 3分钟后，不应完成
        current_time = datetime(2025, 12, 23, 9, 33, 0)
        assert not builder._should_finish_bar(bar5, current_time)
        
        # 5分钟后，应该完成
        current_time = datetime(2025, 12, 23, 9, 35, 0)
        assert builder._should_finish_bar(bar5, current_time)
    
    @pytest.mark.asyncio
    async def test_on_tick(self):
        """测试处理tick数据"""
        storage = MockKLineStorage()
        builder = KLineBuilder(storage, enabled_periods=["1m"])
        
        # 第一个tick
        tick1 = {
            "InstrumentID": "rb2505",
            "TradingDay": "20251223",
            "UpdateTime": "09:30:15",
            "UpdateMillisec": 0,
            "LastPrice": 3500.0,
            "Volume": 100,
            "Turnover": 350000.0,
            "OpenInterest": 1000.0,
        }
        
        await builder.on_tick(tick1)
        
        # 检查是否创建了K线
        assert "rb2505" in builder.current_bars
        assert KLinePeriod.MIN_1 in builder.current_bars["rb2505"]
        
        bar = builder.current_bars["rb2505"][KLinePeriod.MIN_1]
        assert bar.open == 3500.0
        assert bar.tick_count == 1
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试统计信息"""
        storage = MockKLineStorage()
        builder = KLineBuilder(storage, enabled_periods=["1m", "5m"])
        
        stats = builder.get_stats()
        
        assert "total_ticks" in stats
        assert "total_bars" in stats
        assert "enabled_periods" in stats
        assert len(stats["enabled_periods"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

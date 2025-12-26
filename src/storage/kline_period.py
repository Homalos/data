#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
K线周期定义
"""
from enum import Enum
from typing import Dict


class KLinePeriod(Enum):
    """K线周期枚举"""
    MIN_1 = "1m"      # 1分钟
    MIN_3 = "3m"      # 3分钟
    MIN_5 = "5m"      # 5分钟
    MIN_10 = "10m"    # 10分钟
    MIN_15 = "15m"    # 15分钟
    MIN_30 = "30m"    # 30分钟
    MIN_60 = "60m"    # 60分钟（1小时）
    DAY_1 = "1d"      # 日线
    
    @property
    def minutes(self) -> int:
        """
        获取周期对应的分钟数
        
        Returns:
            分钟数，日线返回1440（24小时）
        """
        period_minutes = {
            "1m": 1,
            "3m": 3,
            "5m": 5,
            "10m": 10,
            "15m": 15,
            "30m": 30,
            "60m": 60,
            "1d": 1440,  # 24小时
        }
        return period_minutes.get(self.value, 1)
    
    @property
    def measurement_name(self) -> str:
        """
        获取K线表名称
        
        Returns:
            表名称，如 "kline_1m"
        """
        return f"kline_{self.value}"
    
    @classmethod
    def from_string(cls, period_str: str) -> 'KLinePeriod':
        """
        从字符串创建周期枚举
        
        Args:
            period_str: 周期字符串，如 "1m", "5m", "1d"
            
        Returns:
            KLinePeriod枚举
            
        Raises:
            ValueError: 无效的周期字符串
        """
        for period in cls:
            if period.value == period_str:
                return period
        raise ValueError(f"无效的K线周期: {period_str}")
    
    @classmethod
    def get_all_periods(cls) -> list['KLinePeriod']:
        """
        获取所有周期
        
        Returns:
            所有周期列表
        """
        return list(cls)
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"KLinePeriod.{self.name}"


class KLineBar:
    """
    K线数据结构
    
    表示一根K线的完整信息
    """
    
    def __init__(self, instrument_id: str, period: KLinePeriod):
        """
        初始化K线
        
        Args:
            instrument_id: 合约代码
            period: K线周期
        """
        self.instrument_id = instrument_id
        self.period = period
        
        # 时间信息
        self.start_time = None      # K线开始时间
        self.end_time = None        # K线结束时间
        self.trading_day = ""       # 交易日
        
        # OHLC数据
        self.open = 0.0             # 开盘价
        self.high = 0.0             # 最高价
        self.low = 0.0              # 最低价
        self.close = 0.0            # 收盘价
        
        # 成交数据
        self.volume = 0             # 成交量
        self.turnover = 0.0         # 成交额
        self.open_interest = 0.0    # 持仓量
        
        # 统计信息
        self.tick_count = 0         # tick数量
        self.is_finished = False    # 是否完成
    
    def update(self, tick_data: Dict):
        """
        用tick数据更新K线
        
        Args:
            tick_data: tick数据字典
        """
        price = tick_data.get("LastPrice", 0)
        
        # 初始化开盘价
        if self.open == 0:
            self.open = price
            self.high = price
            self.low = price
        else:
            # 更新最高最低价
            self.high = max(self.high, price)
            self.low = min(self.low, price) if self.low > 0 else price
        
        # 更新收盘价
        self.close = price
        
        # 更新成交数据（使用当前累计值）
        self.volume = tick_data.get("Volume", 0)
        self.turnover = tick_data.get("Turnover", 0)
        self.open_interest = tick_data.get("OpenInterest", 0)
        
        # 更新交易日
        if not self.trading_day:
            self.trading_day = tick_data.get("TradingDay", "")
        
        # 增加tick计数
        self.tick_count += 1
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式
        
        Returns:
            K线数据字典
        """
        return {
            "instrument_id": self.instrument_id,
            "period": self.period.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "trading_day": self.trading_day,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "turnover": self.turnover,
            "open_interest": self.open_interest,
            "tick_count": self.tick_count,
            "is_finished": self.is_finished,
        }
    
    def __repr__(self) -> str:
        return (
            f"KLineBar({self.instrument_id}, {self.period.value}, "
            f"O:{self.open}, H:{self.high}, L:{self.low}, C:{self.close}, "
            f"V:{self.volume}, ticks:{self.tick_count})"
        )

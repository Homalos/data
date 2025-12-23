#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Tick存储模块
"""
import pytest
import asyncio
from datetime import datetime
from src.storage.tick_buffer import TickBuffer
from src.storage.tick_storage import TickStorage
from src.utils.config import InfluxDBConfig


class TestTickBuffer:
    """测试Tick缓冲器"""
    
    def test_init(self):
        """测试初始化"""
        buffer = TickBuffer(max_size=100, flush_interval=5.0)
        assert buffer.max_size == 100
        assert buffer.flush_interval == 5.0
        assert buffer.size() == 0
    
    def test_add_and_size(self):
        """测试添加数据"""
        buffer = TickBuffer(max_size=10)
        
        # 添加数据
        for i in range(5):
            buffer.add({"id": i, "price": 100 + i})
        
        assert buffer.size() == 5
        assert not buffer.is_full()
    
    def test_is_full(self):
        """测试缓冲区满"""
        buffer = TickBuffer(max_size=3)
        
        buffer.add({"id": 1})
        buffer.add({"id": 2})
        assert not buffer.is_full()
        
        buffer.add({"id": 3})
        assert buffer.is_full()
    
    @pytest.mark.asyncio
    async def test_get_batch(self):
        """测试获取批次"""
        buffer = TickBuffer(max_size=10)
        
        # 添加数据
        for i in range(5):
            buffer.add({"id": i})
        
        # 获取批次
        batch = await buffer.get_batch()
        
        assert len(batch) == 5
        assert buffer.size() == 0
        assert batch[0]["id"] == 0
        assert batch[4]["id"] == 4
    
    def test_get_stats(self):
        """测试统计信息"""
        buffer = TickBuffer(max_size=10)
        
        # 添加数据
        for i in range(5):
            buffer.add({"id": i})
        
        stats = buffer.get_stats()
        
        assert stats["current_size"] == 5
        assert stats["max_size"] == 10
        assert stats["usage_percent"] == 50.0
        assert stats["total_received"] == 5
        assert stats["total_flushed"] == 0
    
    def test_clear(self):
        """测试清空"""
        buffer = TickBuffer(max_size=10)
        
        for i in range(5):
            buffer.add({"id": i})
        
        buffer.clear()
        assert buffer.size() == 0


class TestTickStorage:
    """测试Tick存储引擎"""
    
    def test_convert_to_point(self):
        """测试数据点转换"""
        config = InfluxDBConfig(
            host="http://localhost:8181",
            token="test-token",
            database="test_db"
        )
        
        storage = TickStorage(config)
        
        # 测试数据
        tick_data = {
            "InstrumentID": "rb2505",
            "ExchangeID": "SHFE",
            "TradingDay": "20251223",
            "UpdateTime": "09:30:15",
            "UpdateMillisec": 500,
            "LastPrice": 3500.0,
            "Volume": 1000,
            "Turnover": 3500000.0,
            "OpenInterest": 50000.0,
            "BidPrice1": 3499.0,
            "BidVolume1": 100,
            "AskPrice1": 3501.0,
            "AskVolume1": 100,
            "OpenPrice": 3480.0,
            "HighestPrice": 3510.0,
            "LowestPrice": 3475.0,
            "ClosePrice": 3500.0,
        }
        
        point = storage._convert_to_point(tick_data)
        
        assert point is not None
        assert point["measurement"] == "market_tick"
        assert point["tags"]["instrument_id"] == "rb2505"
        assert point["tags"]["exchange_id"] == "SHFE"
        assert point["fields"]["last_price"] == 3500.0
        assert point["fields"]["volume"] == 1000
        assert isinstance(point["time"], datetime)
    
    def test_parse_timestamp(self):
        """测试时间戳解析"""
        config = InfluxDBConfig(
            host="http://localhost:8181",
            token="test-token",
            database="test_db"
        )
        
        storage = TickStorage(config)
        
        tick_data = {
            "TradingDay": "20251223",
            "UpdateTime": "09:30:15",
            "UpdateMillisec": 500,
        }
        
        timestamp = storage._parse_timestamp(tick_data)
        
        assert isinstance(timestamp, datetime)
        assert timestamp.year == 2025
        assert timestamp.month == 12
        assert timestamp.day == 23
        assert timestamp.hour == 9
        assert timestamp.minute == 30
        assert timestamp.second == 15
    
    def test_get_stats(self):
        """测试统计信息"""
        config = InfluxDBConfig(
            host="http://localhost:8181",
            token="test-token",
            database="test_db"
        )
        
        storage = TickStorage(config)
        stats = storage.get_stats()
        
        assert "write_count" in stats
        assert "error_count" in stats
        assert "running" in stats
        assert stats["write_count"] == 0
        assert stats["error_count"] == 0
        assert stats["running"] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

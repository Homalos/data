#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试合约管理器
"""
import pytest
import asyncio
from pathlib import Path
from src.storage.instrument_manager import InstrumentManager, InstrumentInfo


class TestInstrumentManager:
    """测试合约管理器"""
    
    def test_init(self):
        """测试初始化"""
        manager = InstrumentManager()
        assert manager.cache_path == Path("data/instruments.json")
        assert len(manager.instruments) == 0
    
    def test_save_and_load_cache(self):
        """测试保存和加载缓存"""
        # 创建测试数据
        manager = InstrumentManager(cache_path="data/test_instruments.json")
        
        # 添加测试合约（使用简化的数据结构）
        test_instrument = InstrumentInfo(
            instrument_id="rb2505",
            exchange_id="SHFE",
            product_id="rb",
            volume_multiple=10,
            price_tick=1.0
        )
        
        manager.instruments["rb2505"] = test_instrument
        
        # 保存到缓存
        manager.save_to_cache()
        
        # 创建新的管理器并加载
        manager2 = InstrumentManager(cache_path="data/test_instruments.json")
        success = manager2.load_from_cache()
        
        assert success
        assert len(manager2.instruments) == 1
        assert "rb2505" in manager2.instruments
        assert manager2.instruments["rb2505"].exchange_id == "SHFE"
        
        # 清理测试文件
        Path("data/test_instruments.json").unlink(missing_ok=True)
    
    def test_is_futures(self):
        """测试期货识别"""
        # 期货合约
        assert InstrumentInfo.is_futures("rb2505")
        assert InstrumentInfo.is_futures("ag2602")
        assert InstrumentInfo.is_futures("IC2501")
        
        # 期权合约（应该被过滤）
        assert not InstrumentInfo.is_futures("rb2505-C-4000")
        assert not InstrumentInfo.is_futures("ag2602-P-5000")
        
        # 无效合约
        assert not InstrumentInfo.is_futures("")
        assert not InstrumentInfo.is_futures("123")
    
    def test_get_instruments_by_exchange(self):
        """测试按交易所获取合约"""
        manager = InstrumentManager()
        
        # 添加不同交易所的合约（使用简化的数据结构）
        manager.instruments["rb2505"] = InstrumentInfo(
            instrument_id="rb2505",
            exchange_id="SHFE",
            product_id="rb",
            volume_multiple=10,
            price_tick=1.0
        )
        
        manager.instruments["IF2501"] = InstrumentInfo(
            instrument_id="IF2501",
            exchange_id="CFFEX",
            product_id="IF",
            volume_multiple=300,
            price_tick=0.2
        )
        
        shfe_instruments = manager.get_instruments_by_exchange("SHFE")
        cffex_instruments = manager.get_instruments_by_exchange("CFFEX")
        
        assert len(shfe_instruments) == 1
        assert len(cffex_instruments) == 1
        assert shfe_instruments[0].instrument_id == "rb2505"
        assert cffex_instruments[0].instrument_id == "IF2501"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

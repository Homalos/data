#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试新的存储结构（按合约分表）
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.storage import TickStorage, KLineBuilder, KLineStorage
from src.storage.kline_period import KLinePeriod
from src.utils.config import InfluxDBConfig


async def test_new_structure():
    """测试新的存储结构"""
    logger.info("=" * 60)
    logger.info("测试新的存储结构（按合约分表）")
    logger.info("=" * 60)
    
    # 配置
    influxdb_config = InfluxDBConfig(
        host="http://localhost:8181",
        token="apiv3_ml78EtzEVhJV4478mH4DMVPKpXCxskkODLUVkB7ENXkft9wKGz-1p4esG7lNLn5m3PCqSk1rbSeuL1A_Hnrt7g",
        database="tick_data",
        batch_size=10,
        flush_interval=2.0
    )
    
    # 初始化存储引擎
    logger.info("\n[1] 初始化存储引擎...")
    tick_storage = TickStorage(influxdb_config)
    await tick_storage.initialize()
    
    kline_storage = KLineStorage(influxdb_config)
    await kline_storage.initialize()
    
    kline_builder = KLineBuilder(
        kline_storage=kline_storage,
        enabled_periods=["1m", "5m"]
    )
    
    logger.info("✅ 存储引擎初始化成功")
    
    # 模拟写入tick数据（3个合约）
    logger.info("\n[2] 写入测试tick数据...")
    instruments = ["rb2605", "au2602", "ag2602"]
    
    for i in range(15):
        for instrument in instruments:
            tick_data = {
                "InstrumentID": instrument,
                "ExchangeID": "SHFE" if instrument.startswith(("rb", "au", "ag")) else "DCE",
                "TradingDay": "20251223",
                "UpdateTime": f"20:05:{i:02d}",
                "UpdateMillisec": 0,
                "LastPrice": 3500.0 + i,
                "Volume": 1000 + i * 10,
                "Turnover": 3500000.0 + i * 1000,
                "OpenInterest": 50000.0,
                "BidPrice1": 3499.0 + i,
                "BidVolume1": 100,
                "AskPrice1": 3501.0 + i,
                "AskVolume1": 100,
                "OpenPrice": 3500.0,
                "HighestPrice": 3510.0 + i,
                "LowestPrice": 3490.0,
                "ClosePrice": 3500.0 + i,
            }
            
            # 存储tick
            await tick_storage.store_tick(tick_data)
            
            # 合成K线
            await kline_builder.on_tick(tick_data)
        
        # 每5个tick等待一下
        if (i + 1) % 5 == 0:
            logger.info(f"已写入 {(i + 1) * len(instruments)} 条tick数据")
            await asyncio.sleep(0.5)
    
    logger.info(f"✅ 共写入 {15 * len(instruments)} 条tick数据")
    
    # 等待数据写入完成
    logger.info("\n[3] 等待数据写入完成...")
    await asyncio.sleep(5)
    
    # 关闭存储引擎
    logger.info("\n[4] 关闭存储引擎...")
    await kline_builder.close()
    await kline_storage.close()
    await tick_storage.close()
    
    # 打印统计信息
    tick_stats = tick_storage.get_stats()
    kline_stats = kline_storage.get_stats()
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成！")
    logger.info(f"Tick写入: {tick_stats['write_count']} 条")
    logger.info(f"K线写入: {kline_stats['write_count']} 条")
    logger.info("=" * 60)
    logger.info("\n现在运行 python scripts/verify_data.py 查看结果")


if __name__ == "__main__":
    asyncio.run(test_new_structure())

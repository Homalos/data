#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试CSV存储功能
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.storage.csv_tick_storage import CSVTickStorage


async def test_csv_storage():
    """测试CSV存储"""
    logger.info("=" * 60)
    logger.info("CSV存储功能测试")
    logger.info("=" * 60)
    logger.info("")
    
    # 创建存储引擎
    storage = CSVTickStorage(base_path="./data/test_ticks")
    await storage.initialize()
    
    # 模拟tick数据
    test_ticks = [
        {
            'TradingDay': '20251226',
            'InstrumentID': 'ag2501',
            'ExchangeID': 'SHFE',
            'LastPrice': 5234.0,
            'Volume': 1000,
            'Turnover': 52340000.0,
            'OpenInterest': 50000,
            'BidPrice1': 5233.0,
            'BidVolume1': 10,
            'AskPrice1': 5235.0,
            'AskVolume1': 5,
            'BidPrice2': 0.0,
            'BidVolume2': 0,
            'AskPrice2': 0.0,
            'AskVolume2': 0,
            'BidPrice3': 0.0,
            'BidVolume3': 0,
            'AskPrice3': 0.0,
            'AskVolume3': 0,
            'BidPrice4': 0.0,
            'BidVolume4': 0,
            'AskPrice4': 0.0,
            'AskVolume4': 0,
            'BidPrice5': 0.0,
            'BidVolume5': 0,
            'AskPrice5': 0.0,
            'AskVolume5': 0,
            'OpenPrice': 5230.0,
            'HighestPrice': 5240.0,
            'LowestPrice': 5220.0,
            'ClosePrice': 0.0,
            'PreSettlementPrice': 5200.0,
            'PreClosePrice': 5210.0,
            'PreOpenInterest': 49000,
            'SettlementPrice': 0.0,
            'UpperLimitPrice': 5460.0,
            'LowerLimitPrice': 4940.0,
            'AveragePrice': 5232.5,
            'UpdateTime': '09:00:00',
            'UpdateMillisec': 0,
            'ActionDay': '20251226',
        },
        {
            'TradingDay': '20251226',
            'InstrumentID': 'ag2501',
            'ExchangeID': 'SHFE',
            'LastPrice': 5235.0,
            'Volume': 1010,
            'Turnover': 52865000.0,
            'OpenInterest': 50010,
            'BidPrice1': 5234.0,
            'BidVolume1': 8,
            'AskPrice1': 5236.0,
            'AskVolume1': 6,
            'BidPrice2': 0.0,
            'BidVolume2': 0,
            'AskPrice2': 0.0,
            'AskVolume2': 0,
            'BidPrice3': 0.0,
            'BidVolume3': 0,
            'AskPrice3': 0.0,
            'AskVolume3': 0,
            'BidPrice4': 0.0,
            'BidVolume4': 0,
            'AskPrice4': 0.0,
            'AskVolume4': 0,
            'BidPrice5': 0.0,
            'BidVolume5': 0,
            'AskPrice5': 0.0,
            'AskVolume5': 0,
            'OpenPrice': 5230.0,
            'HighestPrice': 5240.0,
            'LowestPrice': 5220.0,
            'ClosePrice': 0.0,
            'PreSettlementPrice': 5200.0,
            'PreClosePrice': 5210.0,
            'PreOpenInterest': 49000,
            'SettlementPrice': 0.0,
            'UpperLimitPrice': 5460.0,
            'LowerLimitPrice': 4940.0,
            'AveragePrice': 5233.0,
            'UpdateTime': '09:00:01',
            'UpdateMillisec': 500,
            'ActionDay': '20251226',
        },
        {
            'TradingDay': '20251226',
            'InstrumentID': 'au2501',
            'ExchangeID': 'SHFE',
            'LastPrice': 480.5,
            'Volume': 500,
            'Turnover': 24025000.0,
            'OpenInterest': 30000,
            'BidPrice1': 480.4,
            'BidVolume1': 15,
            'AskPrice1': 480.6,
            'AskVolume1': 10,
            'BidPrice2': 0.0,
            'BidVolume2': 0,
            'AskPrice2': 0.0,
            'AskVolume2': 0,
            'BidPrice3': 0.0,
            'BidVolume3': 0,
            'AskPrice3': 0.0,
            'AskVolume3': 0,
            'BidPrice4': 0.0,
            'BidVolume4': 0,
            'AskPrice4': 0.0,
            'AskVolume4': 0,
            'BidPrice5': 0.0,
            'BidVolume5': 0,
            'AskPrice5': 0.0,
            'AskVolume5': 0,
            'OpenPrice': 480.0,
            'HighestPrice': 481.0,
            'LowestPrice': 479.5,
            'ClosePrice': 0.0,
            'PreSettlementPrice': 479.0,
            'PreClosePrice': 479.5,
            'PreOpenInterest': 29500,
            'SettlementPrice': 0.0,
            'UpperLimitPrice': 502.95,
            'LowerLimitPrice': 455.05,
            'AveragePrice': 480.25,
            'UpdateTime': '09:00:00',
            'UpdateMillisec': 0,
            'ActionDay': '20251226',
        },
    ]
    
    # 存储测试数据
    logger.info("开始存储测试数据...")
    for i, tick in enumerate(test_ticks, 1):
        await storage.store_tick(tick)
        logger.info(f"已存储 {i}/{len(test_ticks)}: {tick['InstrumentID']}")
    
    # 等待后台写入
    logger.info("")
    logger.info("等待后台写入完成...")
    await asyncio.sleep(2)
    
    # 获取统计信息
    stats = storage.get_stats()
    logger.info("")
    logger.info("存储统计:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    # 关闭存储
    await storage.close()
    
    # 检查文件
    logger.info("")
    logger.info("检查生成的文件:")
    base_path = Path("./data/test_ticks")
    if base_path.exists():
        for day_dir in sorted(base_path.iterdir()):
            if day_dir.is_dir():
                logger.info(f"  交易日: {day_dir.name}")
                for csv_file in sorted(day_dir.glob('*.csv')):
                    file_size = csv_file.stat().st_size
                    logger.info(f"    - {csv_file.name} ({file_size} 字节)")
                    
                    # 读取并显示前几行
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        logger.info(f"      记录数: {len(lines) - 1} (不含表头)")
                        if len(lines) > 1:
                            logger.info(f"      表头: {lines[0].strip()[:100]}...")
                            logger.info(f"      第1行: {lines[1].strip()[:100]}...")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ 测试完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_csv_storage())

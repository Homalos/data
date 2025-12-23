#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试InfluxDB写入
"""
import asyncio
from datetime import datetime
from loguru import logger

# InfluxDB配置
HOST = "http://localhost:8181"
TOKEN = "apiv3_ml78EtzEVhJV4478mH4DMVPKpXCxskkODLUVkB7ENXkft9wKGz-1p4esG7lNLn5m3PCqSk1rbSeuL1A_Hnrt7g"
DATABASE = "tick_data"


async def test_write():
    """测试直接写入"""
    logger.info("=" * 60)
    logger.info("测试直接写入InfluxDB")
    logger.info("=" * 60)
    
    try:
        # 导入存储模块
        import sys
        sys.path.insert(0, '.')
        from src.storage.influxdb_client import InfluxDBClientWrapper
        
        # 创建客户端
        logger.info("创建InfluxDB客户端...")
        client = InfluxDBClientWrapper(
            host=HOST,
            token=TOKEN,
            database=DATABASE
        )
        
        # 连接
        logger.info("连接到InfluxDB...")
        await client.connect()
        logger.info("✅ 连接成功")
        
        # 创建测试数据点
        logger.info("创建测试数据点...")
        test_points = [
            {
                "measurement": "market_tick",
                "tags": {
                    "instrument_id": "TEST001",
                    "exchange_id": "TEST",
                    "trading_day": "20251223",
                },
                "fields": {
                    "last_price": 3500.0,
                    "volume": 1000,
                    "turnover": 3500000.0,
                    "open_interest": 50000.0,
                    "bid_price1": 3499.0,
                    "bid_volume1": 100,
                    "ask_price1": 3501.0,
                    "ask_volume1": 100,
                    "open_price": 3480.0,
                    "high_price": 3520.0,
                    "low_price": 3470.0,
                    "close_price": 3500.0,
                },
                "time": datetime.now(),
            }
        ]
        
        logger.info(f"准备写入 {len(test_points)} 个数据点...")
        logger.info(f"数据点内容: {test_points[0]}")
        
        # 写入
        logger.info("开始写入...")
        await client.write_points(test_points)
        logger.info("✅ 写入成功！")
        
        # 等待一下让数据落盘
        logger.info("等待2秒让数据落盘...")
        await asyncio.sleep(2)
        
        # 查询验证
        logger.info("查询验证...")
        query = """
        SELECT * FROM market_tick 
        WHERE instrument_id = 'TEST001'
        ORDER BY time DESC
        LIMIT 10
        """
        
        result = await client.query(query)
        logger.info(f"查询结果: {result}")
        
        if result:
            logger.info("✅ 数据写入并查询成功！")
        else:
            logger.warning("⚠️  查询结果为空")
        
        # 关闭
        client.close()
        logger.info("=" * 60)
        logger.info("测试完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_write())

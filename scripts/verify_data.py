#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证InfluxDB数据存储（按合约分表）
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from influxdb_client_3 import InfluxDBClient3
from loguru import logger


def verify_data():
    """验证数据"""
    logger.info("=" * 60)
    logger.info("验证InfluxDB数据存储（按合约分表）")
    logger.info("=" * 60)
    
    # InfluxDB配置
    host = "http://localhost:8181"
    token = "apiv3_ml78EtzEVhJV4478mH4DMVPKpXCxskkODLUVkB7ENXkft9wKGz-1p4esG7lNLn5m3PCqSk1rbSeuL1A_Hnrt7g"
    database = "tick_data"
    
    try:
        # 连接InfluxDB
        client = InfluxDBClient3(
            host=host,
            token=token,
            database=database
        )
        logger.info("✅ InfluxDB连接成功")
        
        # 查询所有表
        logger.info("\n[1] 查询所有表...")
        query = "SHOW TABLES"
        tables = client.query(query=query)
        
        if tables is None or len(tables) == 0:
            logger.warning("没有找到任何表")
            return
        
        # 分类表
        tick_tables = []
        kline_tables = []
        
        for row in tables.to_pydict()['table_name']:
            if row.startswith('tick_'):
                tick_tables.append(row)
            elif row.startswith('kline_'):
                kline_tables.append(row)
        
        logger.info(f"找到 {len(tick_tables)} 个Tick表:")
        for table in sorted(tick_tables):
            logger.info(f"  - {table}")
        
        logger.info(f"\n找到 {len(kline_tables)} 个K线表:")
        for table in sorted(kline_tables):
            logger.info(f"  - {table}")
        
        # 查询每个Tick表的数据量
        if tick_tables:
            logger.info("\n[2] 查询Tick数据量...")
            total_ticks = 0
            for table in sorted(tick_tables):
                try:
                    query = f"SELECT COUNT(*) as count FROM {table}"
                    result = client.query(query=query)
                    if result is not None and len(result) > 0:
                        count = result.to_pydict()['count'][0]
                        total_ticks += count
                        logger.info(f"  - {table}: {count} 条")
                except Exception as e:
                    logger.warning(f"  - {table}: 查询失败 ({e})")
            
            logger.info(f"\n  总计: {total_ticks} 条tick数据")
        
        # 查询每个K线表的数据量
        if kline_tables:
            logger.info("\n[3] 查询K线数据量...")
            total_klines = 0
            for table in sorted(kline_tables):
                try:
                    query = f"SELECT COUNT(*) as count FROM {table}"
                    result = client.query(query=query)
                    if result is not None and len(result) > 0:
                        count = result.to_pydict()['count'][0]
                        total_klines += count
                        logger.info(f"  - {table}: {count} 条")
                except Exception as e:
                    logger.warning(f"  - {table}: 查询失败 ({e})")
            
            logger.info(f"\n  总计: {total_klines} 条K线数据")
        
        # 查询示例数据（第一个tick表）
        if tick_tables:
            logger.info("\n[4] 查询示例Tick数据...")
            first_tick_table = sorted(tick_tables)[0]
            instrument_id = first_tick_table.replace('tick_', '')
            
            query = f"""
                SELECT time, last_price, volume, open_interest
                FROM {first_tick_table}
                ORDER BY time DESC
                LIMIT 5
            """
            result = client.query(query=query)
            
            if result is not None and len(result) > 0:
                logger.info(f"\n{instrument_id} 最新5条tick:")
                logger.info(result)
        
        # 查询示例K线数据（第一个1分钟K线表）
        kline_1m_tables = [t for t in kline_tables if t.startswith('kline_1m_')]
        if kline_1m_tables:
            logger.info("\n[5] 查询示例K线数据...")
            first_kline_table = sorted(kline_1m_tables)[0]
            instrument_id = first_kline_table.replace('kline_1m_', '')
            
            query = f"""
                SELECT time, open, high, low, close, volume
                FROM {first_kline_table}
                ORDER BY time DESC
                LIMIT 5
            """
            result = client.query(query=query)
            
            if result is not None and len(result) > 0:
                logger.info(f"\n{instrument_id} 最新5根1分钟K线:")
                logger.info(result)
        
        logger.info("\n" + "=" * 60)
        logger.info("验证完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 验证失败: {e}", exc_info=True)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    verify_data()

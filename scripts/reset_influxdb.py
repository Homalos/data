#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重置InfluxDB数据库
清除所有旧表，准备重新开始
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from influxdb_client_3 import InfluxDBClient3
from loguru import logger


def reset_database():
    """重置数据库"""
    logger.info("=" * 60)
    logger.info("重置InfluxDB数据库")
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
        logger.info("\n[1] 查询现有表...")
        query = "SHOW TABLES"
        tables = client.query(query=query)
        
        if tables is None or len(tables) == 0:
            logger.info("没有找到任何表")
            return
        
        # 过滤出我们创建的表（tick_*, kline_*, market_tick）
        our_tables = []
        for row in tables.to_pydict()['table_name']:
            if (row.startswith('tick_') or 
                row.startswith('kline_') or 
                row == 'market_tick' or
                row == 'test'):
                our_tables.append(row)
        
        if not our_tables:
            logger.info("没有找到需要删除的表")
            return
        
        logger.info(f"找到 {len(our_tables)} 个表需要删除:")
        for table in our_tables:
            logger.info(f"  - {table}")
        
        # 删除表
        logger.info("\n[2] 删除表数据...")
        deleted_count = 0
        for table in our_tables:
            try:
                # InfluxDB 3.x 使用 DELETE 语句删除数据
                # 注意：InfluxDB 3.x 不支持 DROP TABLE，只能删除数据
                delete_query = f"DELETE FROM {table}"
                client.query(query=delete_query)
                logger.info(f"  ✅ 已清空表: {table}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"  ❌ 删除表失败 {table}: {e}")
        
        logger.info(f"\n✅ 成功清空 {deleted_count} 个表")
        logger.info("=" * 60)
        logger.info("重置完成！现在可以重新运行测试")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 重置失败: {e}", exc_info=True)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    reset_database()

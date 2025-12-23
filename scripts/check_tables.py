#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查InfluxDB中的所有表
"""
from influxdb_client_3 import InfluxDBClient3
from loguru import logger

# InfluxDB配置
HOST = "http://localhost:8181"
TOKEN = "apiv3_ml78EtzEVhJV4478mH4DMVPKpXCxskkODLUVkB7ENXkft9wKGz-1p4esG7lNLn5m3PCqSk1rbSeuL1A_Hnrt7g"
DATABASE = "tick_data"


def check_tables():
    """检查所有表"""
    try:
        client = InfluxDBClient3(
            host=HOST,
            token=TOKEN,
            database=DATABASE
        )
        
        logger.info("=" * 60)
        logger.info("检查InfluxDB中的表")
        logger.info("=" * 60)
        
        # 查询所有表
        query = """
        SHOW TABLES
        """
        
        try:
            result = client.query(query)
            df = result.to_pandas()
            
            if len(df) > 0:
                logger.info(f"\n找到 {len(df)} 个表:")
                for idx, row in df.iterrows():
                    logger.info(f"  - {row['table_name']}")
            else:
                logger.warning("⚠️  数据库中没有表")
                
        except Exception as e:
            logger.warning(f"SHOW TABLES 失败: {e}")
            logger.info("尝试使用information_schema查询...")
            
            # 尝试另一种方式
            query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            """
            
            try:
                result = client.query(query)
                df = result.to_pandas()
                
                if len(df) > 0:
                    logger.info(f"\n找到 {len(df)} 个表:")
                    for idx, row in df.iterrows():
                        logger.info(f"  - {row['table_name']}")
                else:
                    logger.warning("⚠️  数据库中没有表")
            except Exception as e2:
                logger.error(f"查询表失败: {e2}")
        
        logger.info("=" * 60)
        
        client.close()
        
    except Exception as e:
        logger.error(f"连接失败: {e}")


if __name__ == "__main__":
    check_tables()

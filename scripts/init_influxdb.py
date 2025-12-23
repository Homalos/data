#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化InfluxDB 3.x - 测试连接并创建数据库
"""
from influxdb_client_3 import InfluxDBClient3, write_client_options, WriteOptions
from loguru import logger
import sys


def test_influxdb3_connection(host: str, token: str, database: str):
    """
    测试InfluxDB 3.x连接并创建数据库
    
    Args:
        host: InfluxDB地址（如 http://localhost:8181）
        token: 访问Token
        database: 数据库名称
    """
    try:
        logger.info(f"正在连接InfluxDB 3.x: {host}")
        
        # InfluxDB 3.x 使用不同的客户端
        client = InfluxDBClient3(
            host=host,
            token=token,
            database=database
        )
        
        logger.info(f"✅ InfluxDB 3.x 连接成功！")
        logger.info(f"数据库: {database}")
        
        # 测试写入一条数据
        logger.info("正在测试写入功能...")
        test_data = {
            "measurement": "test",
            "tags": {"test_tag": "init"},
            "fields": {"test_field": 1},
        }
        
        try:
            client.write(record=test_data)
            logger.info("✅ 写入测试成功！")
        except Exception as e:
            logger.warning(f"写入测试失败（这是正常的，数据库可能需要先创建）: {e}")
        
        # 验证配置
        logger.info("\n" + "="*50)
        logger.info("InfluxDB 3.x 配置信息")
        logger.info("="*50)
        logger.info(f"Host: {host}")
        logger.info(f"Database: {database}")
        logger.info(f"Token: {token[:20]}...")
        logger.info("="*50 + "\n")
        
        client.close()
        logger.info("InfluxDB 3.x 初始化完成！")
        return True
        
    except Exception as e:
        logger.error(f"InfluxDB 3.x 连接失败: {e}", exc_info=True)
        logger.error("\n请检查：")
        logger.error("1. InfluxDB 3.x 是否已启动")
        logger.error("2. 地址是否正确（默认端口8181）")
        logger.error("3. Token是否有效")
        return False


if __name__ == "__main__":
    # InfluxDB 3.x 配置参数
    INFLUXDB_HOST = "http://localhost:8181"
    INFLUXDB_TOKEN = "apiv3_ml78EtzEVhJV4478mH4DMVPKpXCxskkODLUVkB7ENXkft9wKGz-1p4esG7lNLn5m3PCqSk1rbSeuL1A_Hnrt7g"
    DATABASE_NAME = "tick_data"
    
    print("="*60)
    print("InfluxDB 3.x 初始化脚本")
    print("="*60)
    
    # 执行初始化
    success = test_influxdb3_connection(INFLUXDB_HOST, INFLUXDB_TOKEN, DATABASE_NAME)
    
    if success:
        print("\n" + "="*60)
        print("✅ InfluxDB 3.x 初始化成功！")
        print("="*60)
        print("\n请将以下配置添加到 config/config.sample.yaml:")
        print(f"""
Storage:
  Enabled: true
  
  InfluxDB:
    Host: {INFLUXDB_HOST}
    Token: {INFLUXDB_TOKEN}
    Database: {DATABASE_NAME}
    BatchSize: 1000
    FlushInterval: 5
""")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ InfluxDB 3.x 初始化失败")
        print("="*60)
        print("\n请确保：")
        print("1. InfluxDB 3.x 服务已启动")
        print("2. 访问地址正确（默认 http://localhost:8181）")
        print("3. Token有效")
        sys.exit(1)

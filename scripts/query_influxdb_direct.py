#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接查询 InfluxDB 数据
"""

import sys
from pathlib import Path
from datetime import datetime
import yaml

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

try:
    from influxdb_client_3 import InfluxDBClient3
except ImportError:
    logger.error("请安装 influxdb3-python: pip install influxdb3-python")
    sys.exit(1)


def load_config():
    """加载配置文件"""
    config_path = project_root / "config" / "config_md.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    storage_config = config.get('Storage', {})
    influxdb_config = storage_config.get('InfluxDB', {})
    
    return {
        'host': influxdb_config.get('Host', 'http://localhost:8181'),
        'token': influxdb_config.get('Token', ''),
        'database': influxdb_config.get('Database', 'tick_data'),
    }


def main():
    """主函数"""
    config = load_config()
    
    logger.info("连接 InfluxDB...")
    client = InfluxDBClient3(
        host=config['host'],
        token=config['token'],
        database=config['database']
    )
    
    # 查询所有表
    logger.info("\n查询所有表...")
    tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'iox'"
    tables_result = client.query(tables_query, language="sql")
    
    tables = []
    for row in tables_result:
        table_name = str(row[0])
        tables.append(table_name)
        logger.info(f"  - {table_name}")
    
    # 查询每个表的数据
    for table_name in tables:
        logger.info(f"\n{'='*60}")
        logger.info(f"表: {table_name}")
        logger.info(f"{'='*60}")
        
        try:
            # 查询记录数
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            count_result = client.query(count_query, language="sql")
            
            count = 0
            for row in count_result:
                count = int(row[0])
            
            logger.info(f"记录数: {count}")
            
            if count > 0:
                # 查询前5条记录
                data_query = f"SELECT * FROM {table_name} ORDER BY time DESC LIMIT 5"
                data_result = client.query(data_query, language="sql")
                
                logger.info(f"\n列名: {data_result.schema.names}")
                logger.info(f"\n最新的 5 条记录:")
                
                for i, row in enumerate(data_result, 1):
                    logger.info(f"\n  记录 {i}:")
                    for j, col_name in enumerate(data_result.schema.names):
                        value = row[j]
                        
                        # 格式化时间
                        if col_name == 'time' and value:
                            try:
                                dt = datetime.fromtimestamp(value.timestamp())
                                value = dt.strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                pass
                        
                        logger.info(f"    {col_name}: {value}")
        
        except Exception as e:
            logger.error(f"查询失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    client.close()
    logger.info("\n完成")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
InfluxDB 数据检查工具（最终版）
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
    import pyarrow
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


def format_time(value):
    """格式化时间"""
    if value is None:
        return 'N/A'
    try:
        if hasattr(value, 'timestamp'):
            dt = datetime.fromtimestamp(value.timestamp())
        else:
            dt = datetime.fromtimestamp(value / 1e9)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(value)


def main():
    """主函数"""
    logger.info("=" * 70)
    logger.info("InfluxDB 数据检查工具")
    logger.info("=" * 70)
    
    config = load_config()
    
    logger.info(f"\n连接信息:")
    logger.info(f"  Host: {config['host']}")
    logger.info(f"  Database: {config['database']}")
    
    # 连接
    try:
        client = InfluxDBClient3(
            host=config['host'],
            token=config['token'],
            database=config['database']
        )
        logger.info("\n✅ 连接成功")
    except Exception as e:
        logger.error(f"\n❌ 连接失败: {e}")
        return
    
    # 查询所有表
    logger.info("\n" + "=" * 70)
    logger.info("数据库中的表")
    logger.info("=" * 70)
    
    try:
        tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'iox'"
        tables_result = client.query(tables_query, language="sql")
        
        # 转换为 pandas DataFrame 更容易处理
        tables_df = tables_result.to_pandas()
        tables = tables_df['table_name'].tolist()
        
        tick_tables = [t for t in tables if t.startswith('tick_')]
        kline_tables = [t for t in tables if t.startswith('kline_')]
        
        logger.info(f"\n找到 {len(tables)} 个表:")
        for table in sorted(tables):
            logger.info(f"  - {table}")
        
        logger.info(f"\n分类统计:")
        logger.info(f"  Tick 表: {len(tick_tables)} 个")
        logger.info(f"  K线 表: {len(kline_tables)} 个")
        logger.info(f"  其他表: {len(tables) - len(tick_tables) - len(kline_tables)} 个")
        
    except Exception as e:
        logger.error(f"❌ 查询表失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        client.close()
        return
    
    # 检查每个表的数据
    for table_name in sorted(tables):
        logger.info(f"\n" + "=" * 70)
        logger.info(f"表: {table_name}")
        logger.info(f"=" * 70)
        
        try:
            # 查询记录数
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_result = client.query(count_query, language="sql")
            count_df = count_result.to_pandas()
            count = int(count_df['count'].iloc[0]) if not count_df.empty else 0
            
            logger.info(f"\n记录数: {count}")
            
            if count > 0:
                # 查询表结构
                schema_query = f"SELECT * FROM {table_name} LIMIT 1"
                schema_result = client.query(schema_query, language="sql")
                columns = schema_result.schema.names
                
                logger.info(f"列: {', '.join(columns)}")
                
                # 查询最新的 5 条记录
                data_query = f"SELECT * FROM {table_name} ORDER BY time DESC LIMIT 5"
                data_result = client.query(data_query, language="sql")
                data_df = data_result.to_pandas()
                
                logger.info(f"\n最新的 {len(data_df)} 条记录:")
                
                for idx, row in data_df.iterrows():
                    logger.info(f"\n  记录 {idx + 1}:")
                    for col in columns:
                        value = row[col]
                        
                        # 格式化时间列
                        if col == 'time':
                            value = format_time(value)
                        # 格式化浮点数
                        elif isinstance(value, float):
                            value = f"{value:.2f}"
                        
                        logger.info(f"    {col:20s}: {value}")
                
                # 如果是 K 线表，显示统计信息
                if table_name.startswith('kline_'):
                    logger.info(f"\n  📊 统计信息:")
                    
                    # 按合约分组统计
                    if 'instrument_id' in columns:
                        stats_query = f"""
                        SELECT instrument_id, COUNT(*) as count
                        FROM {table_name}
                        GROUP BY instrument_id
                        ORDER BY count DESC
                        """
                        stats_result = client.query(stats_query, language="sql")
                        stats_df = stats_result.to_pandas()
                        
                        logger.info(f"    按合约统计:")
                        for _, stat_row in stats_df.iterrows():
                            inst_id = stat_row['instrument_id']
                            inst_count = stat_row['count']
                            logger.info(f"      {inst_id}: {inst_count} 条")
                
                # 如果是 Tick 表，显示时间范围
                if table_name.startswith('tick_'):
                    time_query = f"""
                    SELECT MIN(time) as min_time, MAX(time) as max_time
                    FROM {table_name}
                    """
                    time_result = client.query(time_query, language="sql")
                    time_df = time_result.to_pandas()
                    
                    if not time_df.empty:
                        min_time = format_time(time_df['min_time'].iloc[0])
                        max_time = format_time(time_df['max_time'].iloc[0])
                        
                        logger.info(f"\n  ⏰ 时间范围:")
                        logger.info(f"    最早: {min_time}")
                        logger.info(f"    最晚: {max_time}")
            
            else:
                logger.warning("  ⚠️  表为空")
        
        except Exception as e:
            logger.error(f"  ❌ 查询失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    client.close()
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ 检查完成")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()

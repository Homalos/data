#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的 InfluxDB 数据检查脚本

使用 InfluxDB 3.x Flight SQL API 查询数据
"""

import sys
from pathlib import Path
from datetime import datetime
import yaml

# 添加项目根目录到 Python 路径
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
    logger.info("=" * 60)
    logger.info("InfluxDB 数据检查工具（简化版）")
    logger.info("=" * 60)
    
    # 加载配置
    config = load_config()
    
    logger.info(f"\n连接信息:")
    logger.info(f"  Host: {config['host']}")
    logger.info(f"  Database: {config['database']}")
    
    # 创建客户端
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
    
    # 1. 查询所有表
    logger.info("\n" + "=" * 60)
    logger.info("查询所有表")
    logger.info("=" * 60)
    
    try:
        # 使用 information_schema 查询表
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'iox'
        """
        
        tables_result = client.query(tables_query, language="sql")
        
        tick_tables = []
        kline_tables = []
        
        logger.info("\n所有表:")
        for row in tables_result:
            # row 是 pyarrow.Table 的一行
            table_name = str(row[0])
            logger.info(f"  - {table_name}")
            
            if table_name.startswith('tick_'):
                tick_tables.append(table_name)
            elif table_name.startswith('kline_'):
                kline_tables.append(table_name)
        
        logger.info(f"\n统计:")
        logger.info(f"  Tick 表: {len(tick_tables)} 个")
        logger.info(f"  K线 表: {len(kline_tables)} 个")
        
    except Exception as e:
        logger.error(f"❌ 查询表失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return
    
    # 2. 检查 Tick 数据
    if tick_tables:
        logger.info("\n" + "=" * 60)
        logger.info("Tick 数据详情")
        logger.info("=" * 60)
        
        total_tick_records = 0
        
        for table_name in sorted(tick_tables)[:5]:  # 只显示前5个
            instrument_id = table_name.replace('tick_', '')
            
            try:
                # 查询记录数
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                count_result = client.query(count_query, language="sql")
                
                count = 0
                for row in count_result:
                    count = int(row[0])
                
                total_tick_records += count
                
                if count > 0:
                    # 查询最新记录
                    latest_query = f"SELECT * FROM {table_name} ORDER BY time DESC LIMIT 1"
                    latest_result = client.query(latest_query, language="sql")
                    
                    logger.info(f"\n  📊 {instrument_id}:")
                    logger.info(f"    记录数: {count}")
                    
                    for row in latest_result:
                        # 转换为字典以便访问
                        row_dict = {}
                        for i, col_name in enumerate(latest_result.schema.names):
                            row_dict[col_name] = row[i]
                        
                        # 格式化时间
                        time_val = row_dict.get('time')
                        if time_val:
                            dt = datetime.fromtimestamp(time_val.timestamp())
                            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            time_str = 'N/A'
                        
                        logger.info(f"    最新时间: {time_str}")
                        logger.info(f"    最新价格: {row_dict.get('last_price', 'N/A')}")
                        logger.info(f"    成交量: {row_dict.get('volume', 'N/A')}")
                        logger.info(f"    持仓量: {row_dict.get('open_interest', 'N/A')}")
                
            except Exception as e:
                logger.error(f"  ❌ 查询 {table_name} 失败: {e}")
        
        if len(tick_tables) > 5:
            logger.info(f"\n  ... 还有 {len(tick_tables) - 5} 个表未显示")
        
        logger.info(f"\n✅ Tick 数据总计: {total_tick_records} 条记录（已统计的表）")
    
    # 3. 检查 K 线数据
    if kline_tables:
        logger.info("\n" + "=" * 60)
        logger.info("K 线数据详情")
        logger.info("=" * 60)
        
        # 按周期分组
        period_stats = {}
        total_kline_records = 0
        
        for table_name in sorted(kline_tables)[:10]:  # 只显示前10个
            # 解析表名: kline_{period}_{instrument_id}
            parts = table_name.replace('kline_', '').split('_', 1)
            if len(parts) != 2:
                continue
            
            period, instrument_id = parts
            
            try:
                # 查询记录数
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                count_result = client.query(count_query, language="sql")
                
                count = 0
                for row in count_result:
                    count = int(row[0])
                
                total_kline_records += count
                
                if period not in period_stats:
                    period_stats[period] = {'count': 0, 'tables': 0}
                
                period_stats[period]['count'] += count
                period_stats[period]['tables'] += 1
                
                if count > 0:
                    # 查询最新记录
                    latest_query = f"SELECT * FROM {table_name} ORDER BY time DESC LIMIT 1"
                    latest_result = client.query(latest_query, language="sql")
                    
                    logger.info(f"\n  📈 {period} - {instrument_id}:")
                    logger.info(f"    记录数: {count}")
                    
                    for row in latest_result:
                        # 转换为字典
                        row_dict = {}
                        for i, col_name in enumerate(latest_result.schema.names):
                            row_dict[col_name] = row[i]
                        
                        # 格式化时间
                        time_val = row_dict.get('time')
                        if time_val:
                            dt = datetime.fromtimestamp(time_val.timestamp())
                            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            time_str = 'N/A'
                        
                        logger.info(f"    最新时间: {time_str}")
                        logger.info(f"    开盘价: {row_dict.get('open', 'N/A')}")
                        logger.info(f"    最高价: {row_dict.get('high', 'N/A')}")
                        logger.info(f"    最低价: {row_dict.get('low', 'N/A')}")
                        logger.info(f"    收盘价: {row_dict.get('close', 'N/A')}")
                        logger.info(f"    成交量: {row_dict.get('volume', 'N/A')}")
                
            except Exception as e:
                logger.error(f"  ❌ 查询 {table_name} 失败: {e}")
        
        if len(kline_tables) > 10:
            logger.info(f"\n  ... 还有 {len(kline_tables) - 10} 个表未显示")
        
        # 打印周期统计
        logger.info("\n📊 K 线周期统计:")
        for period in sorted(period_stats.keys()):
            stats = period_stats[period]
            logger.info(f"  {period:5s}: {stats['count']:6d} 条记录, {stats['tables']} 个表")
        
        logger.info(f"\n✅ K 线数据总计: {total_kline_records} 条记录（已统计的表）")
    
    # 关闭客户端
    client.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("检查完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

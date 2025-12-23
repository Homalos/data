#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查 InfluxDB 中的 Tick 数据和 K 线数据

使用 InfluxDB 3.x Flight SQL API 查询数据
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
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


def format_timestamp(ts):
    """格式化时间戳"""
    if ts is None:
        return "N/A"
    try:
        # InfluxDB 返回的时间戳是纳秒
        dt = datetime.fromtimestamp(ts / 1e9)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(ts)


def check_tick_data(client, database):
    """检查 Tick 数据"""
    logger.info("=" * 60)
    logger.info("检查 Tick 数据")
    logger.info("=" * 60)
    
    try:
        # 查询所有 tick 表
        query = """
        SHOW TABLES
        """
        
        tables = client.query(query=query, database=database, language="sql")
        
        # 过滤出 tick 表
        tick_tables = []
        for row in tables:
            table_name = row[0] if isinstance(row, (list, tuple)) else row.get('table_name', row.get('Table', ''))
            if table_name and table_name.startswith('tick_'):
                tick_tables.append(table_name)
        
        if not tick_tables:
            logger.warning("⚠️  未找到任何 Tick 数据表")
            return
        
        logger.info(f"找到 {len(tick_tables)} 个 Tick 数据表:")
        
        total_records = 0
        
        for table_name in sorted(tick_tables):
            instrument_id = table_name.replace('tick_', '')
            
            # 查询该表的记录数
            count_query = f"""
            SELECT COUNT(*) as count FROM {table_name}
            """
            
            count_result = client.query(query=count_query, database=database, language="sql")
            count = 0
            for row in count_result:
                count = row[0] if isinstance(row, (list, tuple)) else row.get('count', 0)
            
            if count == 0:
                continue
            
            total_records += count
            
            # 查询最新的一条记录
            latest_query = f"""
            SELECT * FROM {table_name}
            ORDER BY time DESC
            LIMIT 1
            """
            
            latest_result = client.query(query=latest_query, database=database, language="sql")
            
            for row in latest_result:
                # 处理不同的返回格式
                if isinstance(row, dict):
                    time_val = row.get('time')
                    last_price = row.get('last_price', 'N/A')
                    volume = row.get('volume', 'N/A')
                    open_interest = row.get('open_interest', 'N/A')
                else:
                    # 如果是 tuple/list，需要知道列的顺序
                    time_val = row[0] if len(row) > 0 else None
                    last_price = 'N/A'
                    volume = 'N/A'
                    open_interest = 'N/A'
                
                logger.info(f"\n  📊 {instrument_id}:")
                logger.info(f"    记录数: {count}")
                logger.info(f"    最新时间: {format_timestamp(time_val)}")
                logger.info(f"    最新价格: {last_price}")
                logger.info(f"    成交量: {volume}")
                logger.info(f"    持仓量: {open_interest}")
        
        logger.info(f"\n✅ Tick 数据总计: {total_records} 条记录")
        
    except Exception as e:
        logger.error(f"❌ 查询 Tick 数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


def check_kline_data(client, database):
    """检查 K 线数据"""
    logger.info("\n" + "=" * 60)
    logger.info("检查 K 线数据")
    logger.info("=" * 60)
    
    try:
        # 查询所有 kline 表
        query = """
        SHOW TABLES
        """
        
        tables = client.query(query=query, database=database, language="sql")
        
        # 过滤出 kline 表
        kline_tables = []
        for row in tables:
            table_name = row['table_name']
            if table_name.startswith('kline_'):
                kline_tables.append(table_name)
        
        if not kline_tables:
            logger.warning("⚠️  未找到任何 K 线数据表")
            return
        
        logger.info(f"找到 {len(kline_tables)} 个 K 线数据表:")
        
        # 按周期分组统计
        period_stats = {}
        total_records = 0
        
        for table_name in sorted(kline_tables):
            # 解析表名: kline_{period}_{instrument_id}
            parts = table_name.replace('kline_', '').split('_', 1)
            if len(parts) != 2:
                continue
            
            period, instrument_id = parts
            
            # 查询该表的记录数
            count_query = f"""
            SELECT COUNT(*) as count FROM "{table_name}"
            """
            
            count_result = client.query(query=count_query, database=database, language="sql")
            count = 0
            for row in count_result:
                count = row['count']
            
            if count == 0:
                continue
            
            total_records += count
            
            if period not in period_stats:
                period_stats[period] = {'count': 0, 'instruments': []}
            
            period_stats[period]['count'] += count
            period_stats[period]['instruments'].append(instrument_id)
            
            # 查询最新的一条记录
            latest_query = f"""
            SELECT * FROM "{table_name}"
            ORDER BY time DESC
            LIMIT 1
            """
            
            latest_result = client.query(query=latest_query, database=database, language="sql")
            
            for row in latest_result:
                logger.info(f"\n  📈 {period} - {instrument_id}:")
                logger.info(f"    记录数: {count}")
                logger.info(f"    最新时间: {format_timestamp(row.get('time'))}")
                logger.info(f"    开盘价: {row.get('open', 'N/A')}")
                logger.info(f"    最高价: {row.get('high', 'N/A')}")
                logger.info(f"    最低价: {row.get('low', 'N/A')}")
                logger.info(f"    收盘价: {row.get('close', 'N/A')}")
                logger.info(f"    成交量: {row.get('volume', 'N/A')}")
        
        # 打印周期统计
        logger.info("\n📊 K 线周期统计:")
        for period in sorted(period_stats.keys()):
            stats = period_stats[period]
            logger.info(f"  {period:5s}: {stats['count']:6d} 条记录, {len(stats['instruments'])} 个合约")
        
        logger.info(f"\n✅ K 线数据总计: {total_records} 条记录")
        
    except Exception as e:
        logger.error(f"❌ 查询 K 线数据失败: {e}")


def check_recent_data(client, database, minutes=10):
    """检查最近 N 分钟的数据"""
    logger.info("\n" + "=" * 60)
    logger.info(f"检查最近 {minutes} 分钟的数据")
    logger.info("=" * 60)
    
    try:
        # 计算时间范围
        now = datetime.now()
        start_time = now - timedelta(minutes=minutes)
        
        # 查询最近的 tick 数据
        tick_query = f"""
        SELECT * FROM (
            SELECT * FROM "tick_ZC610"
            WHERE time >= {int(start_time.timestamp() * 1e9)}
            ORDER BY time DESC
            LIMIT 10
        )
        ORDER BY time ASC
        """
        
        logger.info(f"\n最近 {minutes} 分钟的 Tick 数据 (ZC610):")
        
        tick_result = client.query(query=tick_query, database=database, language="sql")
        tick_count = 0
        
        for row in tick_result:
            tick_count += 1
            logger.info(
                f"  {format_timestamp(row.get('time'))} | "
                f"价格: {row.get('last_price'):8.2f} | "
                f"成交量: {row.get('volume'):8d} | "
                f"持仓量: {row.get('open_interest'):8d}"
            )
        
        if tick_count == 0:
            logger.warning(f"  ⚠️  最近 {minutes} 分钟无 Tick 数据")
        else:
            logger.info(f"  ✅ 共 {tick_count} 条记录")
        
    except Exception as e:
        logger.error(f"❌ 查询最近数据失败: {e}")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("InfluxDB 数据检查工具")
    logger.info("=" * 60)
    
    # 加载配置
    config = load_config()
    
    logger.info(f"\n连接信息:")
    logger.info(f"  Host: {config['host']}")
    logger.info(f"  Database: {config['database']}")
    logger.info(f"  Token: {'*' * 20}...{config['token'][-10:]}")
    
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
    
    # 检查数据
    check_tick_data(client, config['database'])
    check_kline_data(client, config['database'])
    check_recent_data(client, config['database'], minutes=10)
    
    # 关闭客户端
    client.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("检查完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

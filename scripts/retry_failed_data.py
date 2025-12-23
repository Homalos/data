#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重试失败数据脚本

用于重试之前写入失败并保存到本地文件的数据
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.utils.config import GlobalConfig
from src.storage.influxdb_client import InfluxDBClientWrapper
from src.storage.failure_handler import FailureHandler


async def main():
    """主函数"""
    try:
        # 加载配置
        config_path = project_root / "config" / "config_md.yaml"
        GlobalConfig.load_config(str(config_path))
        
        logger.info("=" * 60)
        logger.info("重试失败数据脚本")
        logger.info("=" * 60)
        
        # 初始化InfluxDB客户端
        influxdb_config = GlobalConfig.InfluxDB
        influxdb_client = InfluxDBClientWrapper(
            host=influxdb_config.host,
            token=influxdb_config.token,
            database=influxdb_config.database
        )
        await influxdb_client.connect()
        logger.info("✅ InfluxDB连接成功")
        
        # 初始化失败数据处理器
        failure_handler = FailureHandler(failure_dir="data/failures")
        
        # 获取当前失败数据统计
        stats_before = failure_handler.get_stats()
        logger.info(f"当前失败数据统计:")
        logger.info(f"  - Tick文件: {stats_before['pending_tick_files']}个")
        logger.info(f"  - K线文件: {stats_before['pending_kline_files']}个")
        logger.info(f"  - 总计: {stats_before['total_pending_files']}个")
        
        if stats_before['total_pending_files'] == 0:
            logger.info("没有需要重试的失败数据")
            return
        
        # 重试Tick数据
        logger.info("\n开始重试Tick失败数据...")
        tick_result = await failure_handler.retry_failed_batches(influxdb_client, "tick")
        logger.info(
            f"Tick重试结果: 总计{tick_result['total']}, "
            f"成功{tick_result['success']}, 失败{tick_result['failed']}"
        )
        
        # 重试K线数据
        logger.info("\n开始重试K线失败数据...")
        kline_result = await failure_handler.retry_failed_batches(influxdb_client, "kline")
        logger.info(
            f"K线重试结果: 总计{kline_result['total']}, "
            f"成功{kline_result['success']}, 失败{kline_result['failed']}"
        )
        
        # 获取重试后的统计
        stats_after = failure_handler.get_stats()
        logger.info(f"\n重试后失败数据统计:")
        logger.info(f"  - Tick文件: {stats_after['pending_tick_files']}个")
        logger.info(f"  - K线文件: {stats_after['pending_kline_files']}个")
        logger.info(f"  - 总计: {stats_after['total_pending_files']}个")
        
        # 关闭连接
        influxdb_client.close()
        logger.info("\n✅ 重试完成")
        
    except Exception as e:
        logger.error(f"❌ 重试失败数据出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

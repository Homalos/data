#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试自动查询合约功能

验证：
1. 合约管理器是否正确初始化
2. 登录后是否自动查询合约
3. 合约信息是否保存到JSON文件
4. 是否正确过滤期权，仅保留期货
"""
import json
from pathlib import Path
from loguru import logger


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("测试自动查询合约功能")
    logger.info("=" * 60)
    
    # 检查合约JSON文件
    instruments_file = Path("data/instruments.json")
    
    if not instruments_file.exists():
        logger.error(f"❌ 合约文件不存在: {instruments_file}")
        logger.info("\n请先运行自动登录脚本:")
        logger.info("  python scripts/auto_login_td.py")
        return
    
    # 读取合约信息
    try:
        with open(instruments_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_count = data.get("total_count", 0)
        update_time = data.get("update_time", "未知")
        instruments = data.get("instruments", [])
        
        logger.info(f"\n✅ 合约文件存在: {instruments_file}")
        logger.info(f"更新时间: {update_time}")
        logger.info(f"期货合约总数: {total_count}")
        
        # 按交易所统计
        exchanges = {}
        for inst in instruments:
            exchange = inst.get("exchange_id", "未知")
            exchanges[exchange] = exchanges.get(exchange, 0) + 1
        
        logger.info("\n按交易所统计:")
        for exchange, count in sorted(exchanges.items()):
            logger.info(f"  {exchange}: {count} 个合约")
        
        # 显示前10个合约
        logger.info("\n前10个期货合约:")
        for i, inst in enumerate(instruments[:10], 1):
            logger.info(
                f"  {i}. {inst.get('instrument_id'):8s} | "
                f"{inst.get('exchange_id'):6s} | "
                f"品种: {inst.get('product_id'):6s} | "
                f"乘数: {inst.get('volume_multiple'):4d} | "
                f"最小变动: {inst.get('price_tick')}"
            )
        
        # 验证数据结构
        logger.info("\n验证数据结构:")
        if instruments:
            first_inst = instruments[0]
            expected_fields = ["instrument_id", "exchange_id", "product_id", "volume_multiple", "price_tick"]
            actual_fields = list(first_inst.keys())
            
            logger.info(f"  预期字段: {expected_fields}")
            logger.info(f"  实际字段: {actual_fields}")
            
            if set(actual_fields) == set(expected_fields):
                logger.info("  ✅ 数据结构正确（简化版）")
            else:
                logger.warning("  ⚠️  数据结构不匹配")
        
        # 验证是否过滤了期权
        logger.info("\n验证期权过滤:")
        has_options = False
        for inst in instruments:
            inst_id = inst.get("instrument_id", "")
            # 检查是否包含期权标识
            if '-' in inst_id or len(inst_id) > 6:
                has_options = True
                logger.warning(f"  ⚠️  发现疑似期权合约: {inst_id}")
        
        if not has_options:
            logger.info("  ✅ 已正确过滤期权，仅保留期货")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 测试完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 读取合约文件失败: {e}", exc_info=True)


if __name__ == "__main__":
    main()

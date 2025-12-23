#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试期货合约识别逻辑

验证 is_futures() 方法是否正确识别期货和期权
"""
import sys
from pathlib import Path
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.instrument_manager import InstrumentInfo


def test_futures_filter():
    """测试期货过滤逻辑"""
    logger.info("=" * 60)
    logger.info("测试期货合约识别逻辑")
    logger.info("=" * 60)
    
    # 测试用例：期货合约（应该返回 True）
    futures_cases = [
        "ag2506",    # 白银
        "rb2505",    # 螺纹钢
        "au2506",    # 黄金
        "cu2505",    # 铜
        "al2506",    # 铝
        "zn2505",    # 锌
        "pb2506",    # 铅
        "ni2505",    # 镍
        "sn2506",    # 锡
        "ps2606",    # 棕榈油（6位）
        "IF2501",    # 股指期货
        "IC2501",    # 中证500
        "IH2501",    # 上证50
        "TS2503",    # 2年期国债
        "TF2503",    # 5年期国债
        "T2503",     # 10年期国债
    ]
    
    # 测试用例：期权合约（应该返回 False）
    options_cases = [
        "ag2506C5000",     # 白银看涨期权（长度>6）
        "ag2506P5000",     # 白银看跌期权（长度>6）
        "m2505-C-3000",    # 豆粕看涨期权（包含-）
        "m2505-P-3000",    # 豆粕看跌期权（包含-）
        "SR505C6000",      # 白糖看涨期权（包含C）
        "SR505P6000",      # 白糖看跌期权（包含P）
        "IO2501-C-4000",   # 股指期权（包含-和C）
        "IO2501-P-4000",   # 股指期权（包含-和P）
    ]
    
    # 测试用例：其他（应该返回 False）
    other_cases = [
        "",              # 空字符串
        "ABC",           # 纯字母
        "123",           # 纯数字
        "1234567",       # 长度>6
    ]
    
    logger.info("\n测试期货合约识别:")
    futures_passed = 0
    for case in futures_cases:
        result = InstrumentInfo.is_futures(case)
        status = "✅" if result else "❌"
        logger.info(f"  {status} {case:15s} -> {result} (预期: True)")
        if result:
            futures_passed += 1
    
    logger.info(f"\n期货识别通过率: {futures_passed}/{len(futures_cases)}")
    
    logger.info("\n测试期权合约过滤:")
    options_passed = 0
    for case in options_cases:
        result = InstrumentInfo.is_futures(case)
        status = "✅" if not result else "❌"
        logger.info(f"  {status} {case:15s} -> {result} (预期: False)")
        if not result:
            options_passed += 1
    
    logger.info(f"\n期权过滤通过率: {options_passed}/{len(options_cases)}")
    
    logger.info("\n测试其他情况:")
    other_passed = 0
    for case in other_cases:
        result = InstrumentInfo.is_futures(case)
        status = "✅" if not result else "❌"
        display_case = case if case else "(空字符串)"
        logger.info(f"  {status} {display_case:15s} -> {result} (预期: False)")
        if not result:
            other_passed += 1
    
    logger.info(f"\n其他情况通过率: {other_passed}/{len(other_cases)}")
    
    # 总结
    total_passed = futures_passed + options_passed + other_passed
    total_cases = len(futures_cases) + len(options_cases) + len(other_cases)
    
    logger.info("\n" + "=" * 60)
    logger.info(f"总通过率: {total_passed}/{total_cases}")
    
    if total_passed == total_cases:
        logger.info("✅ 所有测试通过")
    else:
        logger.warning(f"⚠️  有 {total_cases - total_passed} 个测试失败")
    
    logger.info("=" * 60)
    
    return total_passed == total_cases


if __name__ == "__main__":
    try:
        success = test_futures_filter()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)

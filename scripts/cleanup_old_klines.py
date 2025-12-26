#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理旧的K线数据
"""
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timedelta


def cleanup_old_klines(days: int, dry_run: bool = True):
    """
    清理指定天数之前的K线数据
    
    Args:
        days: 保留天数，超过此天数的数据将被删除
        dry_run: 是否为模拟运行（不实际删除）
    """
    base_dir = Path("data/klines")
    
    if not base_dir.exists():
        print(f"❌ 目录不存在: {base_dir}")
        return
    
    # 计算截止日期
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff_date.strftime("%Y%m%d")
    
    print("="*80)
    print(f"清理K线数据 (保留最近 {days} 天)")
    print("="*80)
    print(f"截止日期: {cutoff_str}")
    print(f"模式: {'模拟运行' if dry_run else '实际删除'}")
    print()
    
    # 查找所有交易日目录
    trading_days = [d for d in base_dir.iterdir() if d.is_dir()]
    
    deleted_count = 0
    deleted_size = 0
    kept_count = 0
    
    for day_dir in sorted(trading_days):
        trading_day = day_dir.name
        
        # 检查是否为有效的日期格式
        try:
            day_date = datetime.strptime(trading_day, "%Y%m%d")
        except ValueError:
            print(f"⚠️  跳过无效目录: {trading_day}")
            continue
        
        # 计算目录大小
        dir_size = sum(f.stat().st_size for f in day_dir.rglob("*.csv"))
        file_count = len(list(day_dir.rglob("*.csv")))
        
        # 判断是否需要删除
        if day_date < cutoff_date:
            if dry_run:
                print(f"🗑️  [模拟] 将删除: {trading_day} ({file_count} 文件, {dir_size/1024/1024:.2f} MB)")
            else:
                print(f"🗑️  删除: {trading_day} ({file_count} 文件, {dir_size/1024/1024:.2f} MB)")
                shutil.rmtree(day_dir)
            
            deleted_count += 1
            deleted_size += dir_size
        else:
            print(f"✅ 保留: {trading_day} ({file_count} 文件, {dir_size/1024/1024:.2f} MB)")
            kept_count += 1
    
    print()
    print("="*80)
    print(f"统计:")
    print(f"  保留: {kept_count} 个交易日")
    print(f"  删除: {deleted_count} 个交易日")
    print(f"  释放空间: {deleted_size/1024/1024:.2f} MB")
    
    if dry_run:
        print()
        print("⚠️  这是模拟运行，没有实际删除文件")
        print("⚠️  要实际删除，请使用 --execute 参数")
    
    print("="*80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="清理旧的K线数据")
    parser.add_argument('--days', type=int, default=30, help='保留天数（默认30天）')
    parser.add_argument('--execute', action='store_true', help='实际执行删除（默认为模拟运行）')
    
    args = parser.parse_args()
    
    cleanup_old_klines(args.days, dry_run=not args.execute)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查K线数据磁盘使用情况
"""
from pathlib import Path
from collections import defaultdict


def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def check_disk_usage():
    """检查K线数据磁盘使用情况"""
    base_dir = Path("data/klines")
    
    if not base_dir.exists():
        print(f"❌ 目录不存在: {base_dir}")
        return
    
    print("="*80)
    print("K线数据磁盘使用情况")
    print("="*80)
    
    # 按交易日统计
    trading_day_stats = defaultdict(lambda: {'files': 0, 'size': 0})
    
    # 按周期统计
    period_stats = defaultdict(lambda: {'files': 0, 'size': 0})
    
    # 总计
    total_files = 0
    total_size = 0
    
    # 遍历所有CSV文件
    for csv_file in base_dir.rglob("*.csv"):
        file_size = csv_file.stat().st_size
        
        # 解析路径：data/klines/{trading_day}/{period}/{instrument_id}.csv
        parts = csv_file.relative_to(base_dir).parts
        if len(parts) >= 3:
            trading_day = parts[0]
            period = parts[1]
            
            trading_day_stats[trading_day]['files'] += 1
            trading_day_stats[trading_day]['size'] += file_size
            
            period_stats[period]['files'] += 1
            period_stats[period]['size'] += file_size
        
        total_files += 1
        total_size += file_size
    
    # 打印按交易日统计
    print("\n📅 按交易日统计:")
    print("-" * 80)
    print(f"{'交易日':<15} {'文件数':>10} {'大小':>15}")
    print("-" * 80)
    
    for trading_day in sorted(trading_day_stats.keys()):
        stats = trading_day_stats[trading_day]
        print(f"{trading_day:<15} {stats['files']:>10} {format_size(stats['size']):>15}")
    
    # 打印按周期统计
    print("\n⏱️  按周期统计:")
    print("-" * 80)
    print(f"{'周期':<15} {'文件数':>10} {'大小':>15}")
    print("-" * 80)
    
    for period in sorted(period_stats.keys()):
        stats = period_stats[period]
        print(f"{period:<15} {stats['files']:>10} {format_size(stats['size']):>15}")
    
    # 打印总计
    print("\n📊 总计:")
    print("-" * 80)
    print(f"交易日数量: {len(trading_day_stats)}")
    print(f"周期数量: {len(period_stats)}")
    print(f"文件总数: {total_files}")
    print(f"总大小: {format_size(total_size)}")
    print("="*80)
    
    # 估算增长速度
    if len(trading_day_stats) > 0:
        avg_size_per_day = total_size / len(trading_day_stats)
        print(f"\n📈 平均每日增长: {format_size(avg_size_per_day)}")
        print(f"预计一年数据量: {format_size(avg_size_per_day * 250)} (按250个交易日计算)")
        print("="*80)


if __name__ == "__main__":
    check_disk_usage()

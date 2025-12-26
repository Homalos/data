#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询CSV格式的K线数据
"""
import csv
import argparse
from pathlib import Path
from datetime import datetime


def query_kline(trading_day: str, period: str, instrument_id: str, limit: int = 10):
    """
    查询K线数据
    
    Args:
        trading_day: 交易日，格式：YYYYMMDD
        period: 周期，如：1m, 5m, 15m, 30m, 60m, 1d
        instrument_id: 合约代码
        limit: 显示行数，0表示全部
    """
    file_path = Path(f"data/klines/{trading_day}/{period}/{instrument_id}.csv")
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📊 查询K线数据: {file_path}")
    print("="*80)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        rows = list(reader)
        total = len(rows)
        
        if limit > 0:
            rows = rows[-limit:]  # 显示最后N行
        
        # 打印表头
        if rows:
            headers = rows[0].keys()
            print(" | ".join(f"{h:>15}" for h in headers))
            print("-" * 80)
            
            # 打印数据
            for row in rows:
                print(" | ".join(f"{row[h]:>15}" for h in headers))
        
        print("="*80)
        print(f"总计: {total} 根K线")
        if limit > 0 and total > limit:
            print(f"显示: 最后 {limit} 根")


def list_contracts(trading_day: str, period: str):
    """
    列出指定交易日和周期的所有合约
    
    Args:
        trading_day: 交易日
        period: 周期
    """
    base_dir = Path(f"data/klines/{trading_day}/{period}")
    
    if not base_dir.exists():
        print(f"❌ 目录不存在: {base_dir}")
        return
    
    csv_files = list(base_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"❌ 没有找到CSV文件: {base_dir}")
        return
    
    print(f"📁 {trading_day} / {period}")
    print("="*60)
    
    for csv_file in sorted(csv_files):
        # 统计行数
        with open(csv_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f) - 1  # 减去表头
        
        file_size = csv_file.stat().st_size / 1024  # KB
        print(f"  {csv_file.stem:15s}  {line_count:5d} 根K线  {file_size:8.2f} KB")
    
    print("="*60)
    print(f"总计: {len(csv_files)} 个合约")


def list_trading_days():
    """列出所有交易日"""
    base_dir = Path("data/klines")
    
    if not base_dir.exists():
        print(f"❌ 目录不存在: {base_dir}")
        return
    
    trading_days = [d.name for d in base_dir.iterdir() if d.is_dir()]
    
    if not trading_days:
        print("❌ 没有找到交易日数据")
        return
    
    print("📅 可用的交易日:")
    print("="*60)
    
    for day in sorted(trading_days):
        # 统计该交易日的文件数
        day_dir = base_dir / day
        csv_count = len(list(day_dir.rglob("*.csv")))
        
        # 计算总大小
        total_size = sum(f.stat().st_size for f in day_dir.rglob("*.csv")) / 1024 / 1024  # MB
        
        print(f"  {day}  {csv_count:5d} 个文件  {total_size:8.2f} MB")
    
    print("="*60)
    print(f"总计: {len(trading_days)} 个交易日")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="查询CSV格式的K线数据")
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # query命令
    query_parser = subparsers.add_parser('query', help='查询K线数据')
    query_parser.add_argument('trading_day', help='交易日，格式：YYYYMMDD')
    query_parser.add_argument('period', help='周期，如：1m, 5m, 15m')
    query_parser.add_argument('instrument_id', help='合约代码')
    query_parser.add_argument('--limit', type=int, default=10, help='显示行数，0表示全部')
    
    # list命令
    list_parser = subparsers.add_parser('list', help='列出合约')
    list_parser.add_argument('trading_day', help='交易日，格式：YYYYMMDD')
    list_parser.add_argument('period', help='周期，如：1m, 5m, 15m')
    
    # days命令
    days_parser = subparsers.add_parser('days', help='列出所有交易日')
    
    args = parser.parse_args()
    
    if args.command == 'query':
        query_kline(args.trading_day, args.period, args.instrument_id, args.limit)
    elif args.command == 'list':
        list_contracts(args.trading_day, args.period)
    elif args.command == 'days':
        list_trading_days()
    else:
        parser.print_help()

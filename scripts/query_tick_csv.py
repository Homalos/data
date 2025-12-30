#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询CSV格式的Tick数据

用法：
python scripts\query_tick_csv.py <command> <trading_day> <instrument_id> [--limit <limit>] [--fields <fields>]

查询Tick数据（显示最后10条）
python scripts\query_tick_csv.py query 20251230 FG605

查询更多条数
python scripts\query_tick_csv.py query 20251230 FG605 --limit 50

指定显示字段
python scripts\query_tick_csv.py query 20251230 FG605 --fields "Timestamp,LastPrice,Volume"

列出某交易日所有合约
python scripts\query_tick_csv.py list 20251230

列出所有交易日
python scripts\query_tick_csv.py days

显示CSV所有字段
python scripts\query_tick_csv.py fields 20251230 FG605

"""
import csv
import argparse
from pathlib import Path


def query_tick(trading_day: str, instrument_id: str, limit: int = 10, fields: str = None):
    """
    查询Tick数据
    
    Args:
        trading_day: 交易日，格式：YYYYMMDD
        instrument_id: 合约代码
        limit: 显示行数，0表示全部
        fields: 显示的字段，逗号分隔，默认显示核心字段
    """
    file_path = Path(f"data/ticks/{trading_day}/{instrument_id}.csv")
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return
    
    # 默认显示的核心字段
    default_fields = [
        'Timestamp', 'LastPrice', 'Volume', 'Turnover', 'OpenInterest',
        'BidPrice1', 'BidVolume1', 'AskPrice1', 'AskVolume1'
    ]
    
    if fields:
        display_fields = [f.strip() for f in fields.split(',')]
    else:
        display_fields = default_fields
    
    print(f"查询Tick数据: {file_path}")
    print("="*120)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        rows = list(reader)
        total = len(rows)
        
        if limit > 0:
            rows = rows[-limit:]  # 显示最后N行
        
        if rows:
            # 过滤存在的字段
            available_fields = [f for f in display_fields if f in rows[0]]
            
            # 打印表头
            print(" | ".join(f"{h:>15}" for h in available_fields))
            print("-" * 120)
            
            # 打印数据
            for row in rows:
                values = []
                for h in available_fields:
                    v = row.get(h, '')
                    # 截断过长的时间戳
                    if h == 'Timestamp' and len(v) > 15:
                        v = v[11:23]  # 只显示时间部分
                    values.append(f"{v:>15}")
                print(" | ".join(values))
        
        print("="*120)
        print(f"总计: {total} 条Tick")
        if limit > 0 and total > limit:
            print(f"显示: 最后 {limit} 条")


def list_contracts(trading_day: str):
    """
    列出指定交易日的所有合约
    
    Args:
        trading_day: 交易日
    """
    base_dir = Path(f"data/ticks/{trading_day}")
    
    if not base_dir.exists():
        print(f"目录不存在: {base_dir}")
        return
    
    csv_files = list(base_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"没有找到CSV文件: {base_dir}")
        return
    
    print(f"交易日: {trading_day}")
    print("="*60)
    
    for csv_file in sorted(csv_files):
        # 统计行数
        with open(csv_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f) - 1  # 减去表头
        
        file_size = csv_file.stat().st_size / 1024  # KB
        print(f"  {csv_file.stem:15s}  {line_count:6d} 条Tick  {file_size:8.2f} KB")
    
    print("="*60)
    print(f"总计: {len(csv_files)} 个合约")


def list_trading_days():
    """列出所有交易日"""
    base_dir = Path("data/ticks")
    
    if not base_dir.exists():
        print(f"目录不存在: {base_dir}")
        return
    
    trading_days = [d.name for d in base_dir.iterdir() if d.is_dir()]
    
    if not trading_days:
        print("没有找到交易日数据")
        return
    
    print("可用的交易日:")
    print("="*60)
    
    for day in sorted(trading_days):
        day_dir = base_dir / day
        csv_files = list(day_dir.glob("*.csv"))
        csv_count = len(csv_files)
        
        # 计算总大小
        total_size = sum(f.stat().st_size for f in csv_files) / 1024 / 1024  # MB
        
        print(f"  {day}  {csv_count:5d} 个合约  {total_size:8.2f} MB")
    
    print("="*60)
    print(f"总计: {len(trading_days)} 个交易日")


def show_fields(trading_day: str, instrument_id: str):
    """显示CSV文件的所有字段"""
    file_path = Path(f"data/ticks/{trading_day}/{instrument_id}.csv")
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
    
    print(f"文件: {file_path}")
    print(f"字段数: {len(headers)}")
    print("="*60)
    
    for i, h in enumerate(headers, 1):
        print(f"  {i:2d}. {h}")
    
    print("="*60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="查询CSV格式的Tick数据")
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # query命令
    query_parser = subparsers.add_parser('query', help='查询Tick数据')
    query_parser.add_argument('trading_day', help='交易日，格式：YYYYMMDD')
    query_parser.add_argument('instrument_id', help='合约代码')
    query_parser.add_argument('--limit', type=int, default=10, help='显示行数，0表示全部')
    query_parser.add_argument('--fields', type=str, help='显示的字段，逗号分隔')
    
    # list命令
    list_parser = subparsers.add_parser('list', help='列出合约')
    list_parser.add_argument('trading_day', help='交易日，格式：YYYYMMDD')
    
    # days命令
    subparsers.add_parser('days', help='列出所有交易日')
    
    # fields命令
    fields_parser = subparsers.add_parser('fields', help='显示所有字段')
    fields_parser.add_argument('trading_day', help='交易日，格式：YYYYMMDD')
    fields_parser.add_argument('instrument_id', help='合约代码')
    
    args = parser.parse_args()
    
    if args.command == 'query':
        query_tick(args.trading_day, args.instrument_id, args.limit, args.fields)
    elif args.command == 'list':
        list_contracts(args.trading_day)
    elif args.command == 'days':
        list_trading_days()
    elif args.command == 'fields':
        show_fields(args.trading_day, args.instrument_id)
    else:
        parser.print_help()

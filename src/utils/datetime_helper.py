#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日期时间工具
"""
import zoneinfo
from datetime import datetime, time
from typing import List, Tuple


class DateTimeHelper(object):

    @staticmethod
    def get_now_iso_datetime_ms() -> str:
        """
        获取当前日期时间字符串（上海时区，精确到毫秒）

        Returns:
            str: ISO格式的日期时间字符串，精确到毫秒，如 '2025-12-30T10:15:02.123+08:00'
        """
        return datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai")).isoformat(timespec='milliseconds')

    @staticmethod
    def get_expire_date(date_str: str) -> int:
        """
        计算从今天到未来指定日期的天数差

        Args:
            date_str: 字符串格式的日期，如'20260519'

        Returns:
            剩余天数（如果未来日期在今天之前则返回负数）
        """
        today = datetime.now().date()
        future_date = datetime.strptime(date_str, "%Y%m%d").date()
        delta = future_date - today
        return delta.days

    @staticmethod
    def is_trading_time(
        day_sessions: List[List[str]] = None,
        night_sessions: List[List[str]] = None
    ) -> bool:
        """
        判断当前时间是否在交易时段内
        
        Args:
            day_sessions: 日盘交易时段列表，如 [["09:00:00", "10:15:00"], ["10:30:00", "11:30:00"]]
            night_sessions: 夜盘交易时段列表，如 [["21:00:00", "23:00:00"], ["23:00:00", "02:30:00"]]
        
        Returns:
            bool: 是否在交易时段内
        """
        if day_sessions is None:
            day_sessions = [["09:00:00", "10:15:00"], ["10:30:00", "11:30:00"], ["13:30:00", "15:00:00"]]
        if night_sessions is None:
            night_sessions = [["21:00:00", "23:00:00"], ["23:00:00", "02:30:00"]]
        
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()  # 0=周一, 6=周日
        
        # 周六周日不交易（但周五夜盘可能跨到周六凌晨）
        if weekday == 6:  # 周日
            return False
        if weekday == 5:  # 周六，只有凌晨时段可能有（周五夜盘延续）
            # 检查是否在夜盘跨日时段（00:00-02:30）
            for session in night_sessions:
                start_str, end_str = session
                end_time = DateTimeHelper._parse_time(end_str)
                # 只检查跨日的夜盘（结束时间小于开始时间）
                if DateTimeHelper._parse_time(start_str) > end_time:
                    if current_time <= end_time:
                        return True
            return False
        
        # 检查日盘时段（周一到周五）
        for session in day_sessions:
            start_str, end_str = session
            start_time = DateTimeHelper._parse_time(start_str)
            end_time = DateTimeHelper._parse_time(end_str)
            if start_time <= current_time <= end_time:
                return True
        
        # 检查夜盘时段（周一到周五晚上，以及周二到周六凌晨）
        for session in night_sessions:
            start_str, end_str = session
            start_time = DateTimeHelper._parse_time(start_str)
            end_time = DateTimeHelper._parse_time(end_str)
            
            if start_time > end_time:
                # 跨日时段，如 21:00 - 02:30
                if current_time >= start_time or current_time <= end_time:
                    # 周五晚上21:00后或周六凌晨02:30前
                    if weekday == 4 and current_time >= start_time:  # 周五晚上
                        return True
                    if weekday < 5 and current_time >= start_time:  # 周一到周四晚上
                        return True
                    if weekday > 0 and current_time <= end_time:  # 周二到周六凌晨
                        return True
            else:
                # 不跨日时段
                if start_time <= current_time <= end_time:
                    if weekday < 5:  # 周一到周五
                        return True
        
        return False

    @staticmethod
    def _parse_time(time_str: str) -> time:
        """解析时间字符串为time对象，支持HH:MM和HH:MM:SS格式"""
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) > 2 else 0
        return time(hour, minute, second)


if __name__ == '__main__':
    from datetime import datetime, timezone

    # 获取当前时间（本地时间）
    dt_now = datetime.now()
    iso_local = dt_now.isoformat()
    print(f"本地时间: {iso_local}")

    # 获取当前 UTC 时间
    dt_utc = datetime.now(timezone.utc)
    iso_utc = dt_utc.isoformat()
    print(f"UTC 时间: {iso_utc}")

    import zoneinfo

    # 获取特定时区的当前时间, 带3位毫秒的ISO字符串
    now = datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai")).isoformat(timespec='milliseconds')
    print(f"上海时间: {now}")
    # 列出可用时区（Python 3.11+）
    print(zoneinfo.available_timezones())

    # 解析带时区的时间字符串
    # iso_str = "2024-01-15T14:30:45+09:00"
    # dt = datetime.fromisoformat(now)
    # print(f"原始: {dt} (时区: {dt.tzinfo})")

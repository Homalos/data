#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-data
@FileName   : datetime_helper.py
@Date       : 2025/12/27 22:29
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 日期时间工具
"""
from datetime import datetime


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
        # 1. 获取当前日期（不含时间部分）
        today = datetime.now().date()

        # 2. 将字符串转换为日期对象
        # 注意：字符串格式必须与指定的格式完全匹配
        future_date = datetime.strptime(date_str, "%Y%m%d").date()

        # 3. 计算天数差
        delta = future_date - today
        days_diff = delta.days

        return days_diff


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

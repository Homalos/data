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
    d = DateTimeHelper.expire_date("20260519")
    print(d)

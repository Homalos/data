#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-data
@FileName   : time_test.py
@Date       : 2025/12/24 16:24
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: description
"""
from datetime import datetime
from zoneinfo import ZoneInfo

# 1. 定义时区
beijing_tz = ZoneInfo("Asia/Shanghai")  # 代表东八区
utc_tz = ZoneInfo("UTC")

# 2. 将北京时间字符串解析为带时区的datetime对象
beijing_time_str = "2025-12-24T16:40:00+08:00"
beijing_time = datetime.fromisoformat(beijing_time_str)  # Python 3.11+ 支持直接解析时区

# 3. 转换为UTC时区
utc_time = beijing_time.astimezone(utc_tz)
print(utc_time)
# 4. 格式化为以'Z'结尾的ISO 8601字符串
utc_str = utc_time.isoformat().replace("+00:00", "Z")
print(utc_str)

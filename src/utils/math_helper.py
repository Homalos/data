#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : math_helper.py
@Date       : 2025/12/3 14:40
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 数学辅助函数
"""
import re
import sys


class MathHelper(object):

    @staticmethod
    def adjust_price(price: float) -> float:
        """
        调整价格值，将最大浮点数值转换为0

        当价格值为系统的最大浮点数值时，将其转换为0。
        这通常用于处理CTP API中特殊的价格标记值。

        Args:
            price (float): 需要调整的价格值

        Returns:
            float: 调整后的价格值，最大浮点数值会被转换为0，其他值保持不变
        """
        if price is not None and price == sys.float_info.max:
            price = 0.0

        return price

    @staticmethod
    def del_num(content: str) -> str:
        """
        从字符串中删除所有数字字符

        使用正则表达式移除字符串中的所有数字字符，保留非数字字符。

        Args:
            content (str): 需要处理的字符串内容

        Returns:
            str: 删除所有数字字符后的新字符串
        """
        return re.sub(r'\d', '', content)


if __name__ == '__main__':
    ret = 1.7976931348623157e+308
    print(ret, type(ret))
    s = 1159659.0
    print(MathHelper.adjust_price(s))

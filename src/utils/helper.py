#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-data
@FileName   : helper.py
@Date       : 2025/12/27 22:57
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 业务相关的辅助方法
"""
class Helper(object):

    @staticmethod
    def _is_futures(instrument_id: str) -> bool:
        """
        判断是否为期货合约（过滤期权）

        期货合约代码规则：
        - 以字母开头
        - 最长6位字符
        - 格式：产品代码(1-2位字母) + 合约月份(3-4位数字)
        - 例如：ru2501, IF2501, a2501

        期权合约代码规则：
        - 超过6位字符
        - 包含 C 或 P（看涨/看跌）
        - 例如：ru2605P14000, m2501-C-2700

        Args:
            instrument_id: 合约代码

        Returns:
            是否为期货合约
        """
        if not instrument_id:
            return False

        if '-' in instrument_id:
            return False

        # 必须以字母开头
        if not instrument_id[0].isalpha():
            return False

        # 期货合约代码最长6位
        if len(instrument_id) > 6:
            return False

        return True

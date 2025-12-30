#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV K线数据存储引擎
按交易日、周期、合约分文件存储
存储路径: data/klines/{交易日}/{周期}/{合约代码}.csv
"""
from typing import Dict, Any, List

import aiofiles.os
from loguru import logger

from .storage_helper import BaseCSVStorage
from .kline_period import KLineBar


class CSVKLineStorage(BaseCSVStorage):
    """CSV K线存储引擎"""

    # CSV字段顺序（使用ISO 8601标准时间格式）
    _CSV_FIELDS = [
        'Timestamp',
        'Open',
        'High',
        'Low',
        'Close',
        'Volume',
        'Turnover',
        'OpenInterest'
    ]

    def __init__(self, base_path: str = "./data/klines"):
        super().__init__(base_path, flush_interval=5.0)

    @property
    def csv_fields(self) -> List[str]:
        return self._CSV_FIELDS

    @property
    def storage_name(self) -> str:
        return "CSV K线"

    async def store_kline(self, kline_bar: KLineBar) -> None:
        """存储K线数据"""
        try:
            trading_day = kline_bar.trading_day
            instrument_id = kline_bar.instrument_id
            period = kline_bar.period.value

            if not trading_day or not instrument_id:
                logger.warning(f"K线数据缺少交易日或合约代码")
                return

            # 生成文件key: trading_day_period_instrument_id
            file_key = f"{trading_day}_{period}_{instrument_id}"
            csv_row = self._convert_to_csv_row(kline_bar)
            await self._add_to_buffer(file_key, csv_row)

            logger.debug(f"K线数据已缓冲: {instrument_id} {period}")

        except Exception as e:
            logger.error(f"存储K线数据失败: {e}", exc_info=True)

    @staticmethod
    def _convert_to_csv_row(kline_bar: KLineBar) -> Dict[str, Any]:
        """转换K线数据为CSV行格式"""
        # 生成ISO 8601标准时间戳 (YYYY-MM-DDTHH:mm:ss.000+08:00)
        if kline_bar.start_time:
            timestamp = kline_bar.start_time.strftime("%Y-%m-%dT%H:%M:%S.000+08:00")
        else:
            timestamp = ""

        return {
            'Timestamp': timestamp,
            'Open': kline_bar.open,
            'High': kline_bar.high,
            'Low': kline_bar.low,
            'Close': kline_bar.close,
            'Volume': kline_bar.volume,
            'Turnover': kline_bar.turnover,
            'OpenInterest': kline_bar.open_interest
        }

    async def _flush_buffer(self, file_key: str) -> None:
        """刷新单个缓冲区"""
        async with self._buffer_locks[file_key]:
            if file_key not in self._write_buffers or not self._write_buffers[file_key]:
                return
            data_to_write = self._write_buffers[file_key]
            self._write_buffers[file_key] = []

        # 解析文件key: trading_day_period_instrument_id
        parts = file_key.split('_', 2)
        if len(parts) != 3:
            logger.error(f"无效的K线文件key: {file_key}")
            return

        trading_day, period, instrument_id = parts

        # 构建文件路径: data/klines/{交易日}/{周期}/{合约代码}.csv
        period_dir = self.base_path / trading_day / period
        await aiofiles.os.makedirs(period_dir, exist_ok=True)

        file_path = period_dir / f"{instrument_id}.csv"
        await self._write_csv_file(file_path, data_to_write, file_key)

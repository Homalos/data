#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV Tick数据存储引擎
按交易日和合约分文件存储
存储路径: data/ticks/{交易日}/{合约代码}.csv
"""
from typing import Dict, Any, List

import aiofiles.os
from loguru import logger

from .storage_helper import BaseCSVStorage
from ..utils import DateTimeHelper


class CSVTickStorage(BaseCSVStorage):
    """CSV Tick存储引擎"""

    # CSV字段顺序
    _CSV_FIELDS = [
        'Timestamp',
        'TradingDay',
        'InstrumentID',
        'ExchangeID',
        'ExchangeInstID',
        'LastPrice',
        'PreSettlementPrice',
        'PreClosePrice',
        'PreOpenInterest',
        'OpenPrice',
        'HighestPrice',
        'LowestPrice',
        'Volume',
        'Turnover',
        'OpenInterest',
        'ClosePrice',
        'SettlementPrice',
        'UpperLimitPrice',
        'LowerLimitPrice',
        'PreDelta',
        'CurrDelta',
        'UpdateTime',
        'UpdateMillisec',
        'BidPrice1', 'BidVolume1', 'AskPrice1', 'AskVolume1',
        'BidPrice2', 'BidVolume2', 'AskPrice2', 'AskVolume2',
        'BidPrice3', 'BidVolume3', 'AskPrice3', 'AskVolume3',
        'BidPrice4', 'BidVolume4', 'AskPrice4', 'AskVolume4',
        'BidPrice5', 'BidVolume5', 'AskPrice5', 'AskVolume5',
        'AveragePrice',
        'ActionDay',
        'BandingUpperPrice',
        'BandingLowerPrice'
    ]

    def __init__(self, base_path: str = "./data/ticks"):
        super().__init__(base_path, flush_interval=1.0)

    @property
    def csv_fields(self) -> List[str]:
        return self._CSV_FIELDS

    @property
    def storage_name(self) -> str:
        return "CSV Tick"

    async def store_tick(self, tick_data: Dict[str, Any]) -> None:
        """存储单条tick数据"""
        try:
            trading_day = tick_data.get('TradingDay', '')
            instrument_id = tick_data.get('InstrumentID', '')

            if not trading_day or not instrument_id:
                logger.warning(f"Tick数据缺少交易日或合约代码: {tick_data}")
                return

            file_key = f"{trading_day}_{instrument_id}"
            csv_row: dict[str, Any] = self._convert_to_csv_row(tick_data)
            await self._add_to_buffer(file_key, csv_row)

            logger.debug(f"Tick数据已缓冲: {instrument_id}")

        except Exception as e:
            logger.error(f"存储tick数据失败: {e}", exc_info=True)

    @staticmethod
    def _convert_to_csv_row(tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换tick数据为CSV行格式"""
        update_time = tick_data.get('UpdateTime', '')
        update_millisec = tick_data.get('UpdateMillisec', 0)
        trading_day = tick_data.get('TradingDay', '')

        # 构建ISO 8601时间戳(使用东八区时区存储tick行情)
        if update_time and trading_day:
            timestamp = f"{trading_day[:4]}-{trading_day[4:6]}-{trading_day[6:8]}T{update_time}.{update_millisec:03d}+08:00"
        else:
            timestamp = DateTimeHelper.get_now_iso_datetime_ms()
            logger.warning(f"Tick数据缺少交易日或更新时间，使用当前时间戳代替 {timestamp}")

        return {
            'Timestamp': timestamp,
            'TradingDay': tick_data.get('TradingDay', ''),
            'InstrumentID': tick_data.get('InstrumentID', ''),
            'ExchangeID': tick_data.get('ExchangeID', ''),
            'ExchangeInstID': tick_data.get('ExchangeInstID', ''),
            'LastPrice': tick_data.get('LastPrice', 0.0),
            'PreSettlementPrice': tick_data.get('PreSettlementPrice', 0.0),
            'PreClosePrice': tick_data.get('PreClosePrice', 0.0),
            'PreOpenInterest': tick_data.get('PreOpenInterest', 0.0),
            'OpenPrice': tick_data.get('OpenPrice', 0.0),
            'HighestPrice': tick_data.get('HighestPrice', 0.0),
            'LowestPrice': tick_data.get('LowestPrice', 0.0),
            'Volume': tick_data.get('Volume', 0),
            'Turnover': tick_data.get('Turnover', 0.0),
            'OpenInterest': tick_data.get('OpenInterest', 0.0),
            'ClosePrice': tick_data.get('ClosePrice', 0.0),
            'SettlementPrice': tick_data.get('SettlementPrice', 0.0),
            'UpperLimitPrice': tick_data.get('UpperLimitPrice', 0.0),
            'LowerLimitPrice': tick_data.get('LowerLimitPrice', 0.0),
            'PreDelta': tick_data.get('PreDelta', 0.0),
            'CurrDelta': tick_data.get('CurrDelta', 0.0),
            'UpdateTime': update_time,
            'UpdateMillisec': update_millisec,
            'BidPrice1': tick_data.get('BidPrice1', 0.0),
            'BidVolume1': tick_data.get('BidVolume1', 0),
            'AskPrice1': tick_data.get('AskPrice1', 0.0),
            'AskVolume1': tick_data.get('AskVolume1', 0),
            'BidPrice2': tick_data.get('BidPrice2', 0.0),
            'BidVolume2': tick_data.get('BidVolume2', 0),
            'AskPrice2': tick_data.get('AskPrice2', 0.0),
            'AskVolume2': tick_data.get('AskVolume2', 0),
            'BidPrice3': tick_data.get('BidPrice3', 0.0),
            'BidVolume3': tick_data.get('BidVolume3', 0),
            'AskPrice3': tick_data.get('AskPrice3', 0.0),
            'AskVolume3': tick_data.get('AskVolume3', 0),
            'BidPrice4': tick_data.get('BidPrice4', 0.0),
            'BidVolume4': tick_data.get('BidVolume4', 0),
            'AskPrice4': tick_data.get('AskPrice4', 0.0),
            'AskVolume4': tick_data.get('AskVolume4', 0),
            'BidPrice5': tick_data.get('BidPrice5', 0.0),
            'BidVolume5': tick_data.get('BidVolume5', 0),
            'AskPrice5': tick_data.get('AskPrice5', 0.0),
            'AskVolume5': tick_data.get('AskVolume5', 0),
            'AveragePrice': tick_data.get('AveragePrice', 0.0),
            'ActionDay': tick_data.get('ActionDay', ''),
            'BandingUpperPrice': tick_data.get('BandingUpperPrice', 0.0),
            'BandingLowerPrice': tick_data.get('BandingLowerPrice', 0.0)
        }

    async def _flush_buffer(self, file_key: str) -> None:
        """刷新单个缓冲区"""
        async with self._buffer_locks[file_key]:
            if file_key not in self._write_buffers or not self._write_buffers[file_key]:
                return
            data_to_write = self._write_buffers[file_key]
            self._write_buffers[file_key] = []

        # 解析文件key: trading_day_instrument_id
        parts = file_key.split('_', 1)
        if len(parts) != 2:
            logger.error(f"无效的文件key: {file_key}")
            return

        trading_day, instrument_id = parts

        # 构建文件路径: data/ticks/{交易日}/{合约代码}.csv
        day_dir = self.base_path / trading_day
        await aiofiles.os.makedirs(day_dir, exist_ok=True)

        file_path = day_dir / f"{instrument_id}.csv"
        await self._write_csv_file(file_path, data_to_write, file_key)

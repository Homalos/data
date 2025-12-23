#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
合约管理器 - 查询并缓存全市场合约信息
"""
import json
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from loguru import logger


@dataclass
class InstrumentInfo:
    """合约信息（简化版，仅期货）"""
    instrument_id: str          # 合约代码
    exchange_id: str            # 交易所代码
    product_id: str             # 品种代码
    volume_multiple: int        # 合约乘数
    price_tick: float           # 最小变动价位
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @staticmethod
    def is_futures(instrument_id: str) -> bool:
        """
        判断是否为期货合约
        
        期货合约特征：
        1. 代码长度 <= 6
        2. 以字母开头，后跟数字（如 ag2506, rb2505, ps2606）
        3. 不包含 '-'（期权标识）
        4. 如果包含 'C' 或 'P'，必须在前2个字符内（如 IC, IH 是股指期货）
        
        Args:
            instrument_id: 合约代码
            
        Returns:
            是否为期货合约
        """
        if not instrument_id:
            return False
        
        # 长度检查：期货代码最长6位
        if len(instrument_id) > 6:
            return False
        
        # 期权标识检查：包含 '-' 的通常是期权
        if '-' in instrument_id:
            return False
        
        # 必须以字母开头
        if not instrument_id[0].isalpha():
            return False
        
        # 必须包含数字
        if not any(c.isdigit() for c in instrument_id):
            return False
        
        # 如果包含 'C' 或 'P'，检查位置
        # 股指期货如 IC2501, IH2501 的 C 和 H 在前2个字符
        # 期权如 SR505C6000 的 C 在后面
        for i, c in enumerate(instrument_id):
            if c in ['C', 'P']:
                # 如果 C 或 P 在第3个字符之后，很可能是期权
                if i >= 2:
                    return False
        
        return True


class InstrumentManager:
    """合约管理器 - 查询并缓存全市场合约"""
    
    def __init__(self, cache_path: str = "data/instruments.json"):
        """
        初始化合约管理器
        
        Args:
            cache_path: 缓存文件路径
        """
        self.cache_path = Path(cache_path)
        self.instruments: Dict[str, InstrumentInfo] = {}
        self.update_time: Optional[datetime] = None
        
        # 确保数据目录存在
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def query_all_instruments(self, td_client) -> List[InstrumentInfo]:
        """
        通过CTP查询全市场合约
        
        Args:
            td_client: 交易客户端实例
            
        Returns:
            合约信息列表
        """
        logger.info("开始查询全市场合约...")
        
        # 创建一个Future用于等待查询完成
        query_future = asyncio.Future()
        instruments_list = []
        
        # 定义回调函数
        def on_rsp_qry_instrument(instrument_dict: Dict, is_last: bool):
            """合约查询响应回调"""
            if instrument_dict:
                try:
                    # 解析合约信息
                    info = InstrumentInfo(
                        instrument_id=instrument_dict.get("InstrumentID", ""),
                        instrument_name=instrument_dict.get("InstrumentName", ""),
                        exchange_id=instrument_dict.get("ExchangeID", ""),
                        product_id=instrument_dict.get("ProductID", ""),
                        volume_multiple=instrument_dict.get("VolumeMultiple", 1),
                        price_tick=instrument_dict.get("PriceTick", 0.01),
                        create_date=instrument_dict.get("CreateDate", ""),
                        expire_date=instrument_dict.get("ExpireDate", ""),
                        is_trading=instrument_dict.get("IsTrading", 0) == 1
                    )
                    instruments_list.append(info)
                    
                    # 每100个合约打印一次进度
                    if len(instruments_list) % 100 == 0:
                        logger.info(f"已查询 {len(instruments_list)} 个合约...")
                        
                except Exception as err:
                    logger.error(f"解析合约信息失败: {err}")
            
            # 查询完成
            if is_last:
                query_future.set_result(instruments_list)
        
        # 注册临时回调
        original_callback = td_client.rsp_callback
        
        def temp_callback(response: Dict):
            """临时回调函数"""
            msg_type = response.get("MessageType")
            
            if msg_type == "OnRspQryInstrument":
                instrument = response.get("Instrument")
                is_last = response.get("IsLast", False)
                on_rsp_qry_instrument(instrument, is_last)
            
            # 调用原始回调
            if original_callback:
                original_callback(response)
        
        td_client.rsp_callback = temp_callback
        
        try:
            # 发起查询请求
            logger.info("发送合约查询请求...")
            td_client.query_instrument({})
            
            # 等待查询完成（最多等待60秒）
            instruments_list = await asyncio.wait_for(query_future, timeout=60.0)
            
            logger.info(f"合约查询完成，共 {len(instruments_list)} 个合约")
            
            # 更新内存缓存
            self.instruments = {
                inst.instrument_id: inst 
                for inst in instruments_list
            }
            self.update_time = datetime.now()
            
            return instruments_list
            
        except asyncio.TimeoutError:
            logger.error("合约查询超时")
            raise
        except Exception as e:
            logger.error(f"合约查询失败: {e}", exc_info=True)
            raise
        finally:
            # 恢复原始回调
            td_client.rsp_callback = original_callback
    
    def save_to_cache(self):
        """保存合约信息到JSON文件（仅期货）"""
        try:
            # 过滤出期货合约
            futures_instruments = [
                inst.to_dict() 
                for inst in self.instruments.values()
                if InstrumentInfo.is_futures(inst.instrument_id)
            ]
            
            cache_data = {
                "update_time": self.update_time.isoformat() if self.update_time else None,
                "total_count": len(futures_instruments),
                "instruments": futures_instruments
            }
            
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"合约信息已保存到: {self.cache_path}")
            logger.info(f"共 {len(futures_instruments)} 个期货合约（已过滤期权）")
            
        except Exception as e:
            logger.error(f"保存合约缓存失败: {e}", exc_info=True)
            raise
    
    def load_from_cache(self) -> bool:
        """
        从JSON文件加载合约信息
        
        Returns:
            是否加载成功
        """
        if not self.cache_path.exists():
            logger.warning(f"缓存文件不存在: {self.cache_path}")
            return False
        
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 解析合约信息
            self.instruments = {}
            for inst_dict in cache_data.get("instruments", []):
                # 兼容旧格式和新格式
                info = InstrumentInfo(
                    instrument_id=inst_dict["instrument_id"],
                    exchange_id=inst_dict["exchange_id"],
                    product_id=inst_dict["product_id"],
                    volume_multiple=inst_dict["volume_multiple"],
                    price_tick=inst_dict["price_tick"]
                )
                self.instruments[info.instrument_id] = info
            
            # 解析更新时间
            update_time_str = cache_data.get("update_time")
            if update_time_str:
                self.update_time = datetime.fromisoformat(update_time_str)
            
            logger.info(f"从缓存加载 {len(self.instruments)} 个期货合约")
            logger.info(f"缓存更新时间: {self.update_time}")
            
            return True
            
        except Exception as e:
            logger.error(f"加载合约缓存失败: {e}", exc_info=True)
            return False
    
    def get_instrument(self, instrument_id: str) -> Optional[InstrumentInfo]:
        """
        获取指定合约信息
        
        Args:
            instrument_id: 合约代码
            
        Returns:
            合约信息，不存在返回None
        """
        return self.instruments.get(instrument_id)
    
    def get_instruments_by_exchange(self, exchange_id: str) -> List[InstrumentInfo]:
        """
        获取指定交易所的合约
        
        Args:
            exchange_id: 交易所代码
            
        Returns:
            合约信息列表
        """
        return [
            inst 
            for inst in self.instruments.values()
            if inst.exchange_id == exchange_id
        ]
    
    def get_instruments_by_product(self, product_id: str) -> List[InstrumentInfo]:
        """
        获取指定品种的合约
        
        Args:
            product_id: 品种代码
            
        Returns:
            合约信息列表
        """
        return [
            inst 
            for inst in self.instruments.values()
            if inst.product_id == product_id
        ]

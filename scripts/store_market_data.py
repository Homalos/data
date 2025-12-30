#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
订阅并存储所有期货合约的tick数据和K线数据

此脚本会：
1. 从 data/instruments.json 加载所有期货合约
2. 连接到行情服务
3. 订阅所有期货合约
4. 接收tick数据并使用CSV存储引擎保存到 data/ticks/{交易日}/{合约代码}.csv
5. 实时合成K线并保存到 data/klines/{交易日}/{周期}/{合约代码}.csv
"""
import asyncio
import websockets
import json
import sys
import os
from pathlib import Path
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import GlobalConfig
from src.storage.csv_tick_storage import CSVTickStorage
from src.storage.csv_kline_storage import CSVKLineStorage
from src.storage.kline_builder import KLineBuilder


class DataSubscriber(object):
    """行情数据订阅存储客户端"""
    
    def __init__(self, url: str = "ws://127.0.0.1:8080/"):
        self.url: str = url
        self.ws = None
        self.request_id: int = 0
        self.tick_count: int = 0
        self.last_log_time = 0
        self.start_time: float = 0
        
        # CSV存储引擎
        self.tick_storage = None
        
        # K线相关
        self.kline_storage = None
        self.kline_builder = None
    
    async def initialize_storage(
        self, 
        tick_base_path: str = "./data/ticks",
        kline_base_path: str = "./data/klines",
        kline_periods: list = None
    ) -> None:
        """
        初始化存储引擎
        
        Args:
            tick_base_path: Tick数据存储路径
            kline_base_path: K线数据存储路径
            kline_periods: K线周期列表
        """
        # 初始化Tick存储
        try:
            self.tick_storage = CSVTickStorage(base_path=tick_base_path)
            await self.tick_storage.initialize()
            logger.info(f"CSV Tick存储引擎初始化成功，路径: {tick_base_path}")
        except Exception as err:
            logger.error(f"初始化Tick存储引擎失败: {err}")
            raise
        
        # 初始化K线存储
        try:
            self.kline_storage = CSVKLineStorage(base_path=kline_base_path)
            await self.kline_storage.initialize()
            logger.info(f"CSV K线存储引擎初始化成功，路径: {kline_base_path}")
        except Exception as err:
            logger.error(f"初始化K线存储引擎失败: {err}")
            raise
        
        # 初始化K线合成器
        try:
            if kline_periods is None:
                kline_periods = ["1m", "3m", "5m", "10m", "15m", "30m", "60m", "1d"]
            self.kline_builder = KLineBuilder(self.kline_storage, enabled_periods=kline_periods)
            logger.info(f"K线合成器初始化成功，周期: {kline_periods}")
        except Exception as err:
            logger.error(f"初始化K线合成器失败: {err}")
            raise
    
    async def close_storage(self) -> None:
        """关闭存储引擎"""
        # 关闭K线合成器（会保存未完成的K线）
        if self.kline_builder:
            try:
                await self.kline_builder.close()
                logger.info("K线合成器已关闭")
            except Exception as err:
                logger.error(f"关闭K线合成器失败: {err}")
        
        # 关闭K线存储
        if self.kline_storage:
            try:
                await self.kline_storage.close()
                logger.info("CSV K线存储引擎已关闭")
            except Exception as err:
                logger.error(f"关闭K线存储引擎失败: {err}")
        
        # 关闭Tick存储
        if self.tick_storage:
            try:
                await self.tick_storage.close()
                logger.info("CSV Tick存储引擎已关闭")
            except Exception as err:
                logger.error(f"关闭Tick存储引擎失败: {err}")
    
    async def connect(self) -> bool:
        """连接到WebSocket服务"""
        try:
            logger.info(f"正在连接到行情服务: {self.url}")
            
            # 禁用自动 ping/pong，使用应用层心跳
            self.ws = await websockets.connect(
                self.url,
                max_size=10 * 1024 * 1024,  # 10MB
                ping_interval=None,         # 禁用 websockets 库的自动 ping
                ping_timeout=None           # 禁用 websockets 库的 ping 超时
            )
            
            logger.info("连接成功")
            return True
            
        except Exception as err:
            logger.error(f"连接失败: {err}")
            return False
    
    async def send_request(self, request: dict) -> None:
        """发送请求"""
        try:
            request["RequestID"] = self.request_id
            self.request_id += 1
            
            message = json.dumps(request)
            await self.ws.send(message)
            logger.debug(f"发送请求: {request.get('MsgType')}")
            
        except Exception as err:
            logger.error(f"发送请求失败: {err}")
    
    async def receive_response(self, timeout: float = 30.0) -> json:
        """接收响应（跳过Ping消息）"""
        try:
            while True:
                message = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
                response = json.loads(message)
                
                msg_type = response.get("MsgType")
                
                # 处理心跳消息
                if msg_type == "Ping":
                    await self.ws.send(json.dumps({"MsgType": "Pong"}))
                    logger.debug("已响应心跳 Pong")
                    continue
                
                return response
                
        except asyncio.TimeoutError:
            logger.error(f"接收响应超时（{timeout}秒）")
            return None
        except Exception as err:
            logger.error(f"接收响应失败: {err}")
            return None
    
    async def login(self, user_id: str = "", password: str = "") -> bool:
        """登录"""
        logger.info(f"正在登录，账号: {user_id}")
        
        request = {
            "MsgType": "ReqUserLogin",
            "ReqUserLogin": {
                "UserID": user_id,
                "Password": password,
            }
        }
        
        await self.send_request(request)
        
        # 等待登录响应
        response = await self.receive_response()
        
        if response:
            msg_type = response.get("MsgType")
            if msg_type in ["OnRspUserLogin", "RspUserLogin"]:
                rsp_info = response.get("RspInfo", {})
                if rsp_info.get("ErrorID") == 0:
                    logger.info("登录成功")
                    
                    # 显示登录信息
                    rsp_user_login = response.get("RspUserLogin", {})
                    logger.info(f"交易日: {rsp_user_login.get('TradingDay', 'N/A')}")
                    logger.info(f"登录时间: {rsp_user_login.get('LoginTime', 'N/A')}")
                    
                    return True
                else:
                    logger.error(f"登录失败: {rsp_info.get('ErrorMsg')}")
                    return False
        
        return False
    
    async def subscribe_market_data(self, instruments: list) -> bool:
        """订阅行情"""
        logger.info(f"正在订阅 {len(instruments)} 个期货合约...")
        
        request = {
            "MsgType": "SubscribeMarketData",
            "InstrumentID": instruments,
        }
        
        await self.send_request(request)
        
        # 等待订阅响应
        response = await self.receive_response()
        
        if response:
            msg_type = response.get("MsgType")
            if msg_type in ["OnRspSubMarketData", "RspSubMarketData"]:
                logger.info("订阅成功")
                return True
        
        return False
    
    async def listen_and_store(self) -> int:
        """
        监听并存储行情数据
        """
        logger.info("开始监听并存储行情数据（按 Ctrl+C 停止）...")
        logger.info("=" * 60)
        
        self.tick_count = 0
        self.start_time = asyncio.get_event_loop().time()
        self.last_log_time = self.start_time
        
        try:
            while True:
                try:
                    message = await self.ws.recv()
                    response = json.loads(message)
                    
                    msg_type = response.get("MsgType")
                    
                    # 响应Ping消息
                    if msg_type == "Ping":
                        await self.ws.send(json.dumps({"MsgType": "Pong"}))
                        logger.debug("已响应心跳 Pong")
                        continue
                    
                    # 处理tick数据
                    if msg_type in ["OnRtnDepthMarketData", "RtnDepthMarketData"]:
                        self.tick_count += 1
                        depth_data = response.get("DepthMarketData", {})
                        
                        # 存储tick数据
                        if self.tick_storage:
                            try:
                                await self.tick_storage.store_tick(depth_data)
                            except Exception as err:
                                logger.error(f"存储tick数据失败: {err}")
                        
                        # 合成K线
                        if self.kline_builder:
                            try:
                                await self.kline_builder.on_tick(depth_data)
                            except Exception as err:
                                logger.error(f"合成K线失败: {err}")
                        
                        # 每100个tick打印一次
                        if self.tick_count % 100 == 0:
                            logger.info(
                                f"[{self.tick_count:6d}] {depth_data.get('InstrumentID'):8s} "
                                f"价格: {depth_data.get('LastPrice'):8.2f} "
                                f"成交量: {depth_data.get('Volume'):8d} "
                                f"时间: {depth_data.get('UpdateTime')}"
                            )
                        
                        # 每30秒打印一次进度
                        current_time = asyncio.get_event_loop().time()
                        if current_time - self.last_log_time >= 30:
                            elapsed = current_time - self.start_time
                            rate = self.tick_count / elapsed if elapsed > 0 else 0
                            
                            # 获取存储统计
                            tick_stats = self.tick_storage.get_stats() if self.tick_storage else {}
                            tick_buffered = tick_stats.get("buffered_records", 0)
                            
                            kline_stats = self.kline_builder.get_stats() if self.kline_builder else {}
                            kline_bars = kline_stats.get("total_bars", 0)
                            
                            logger.info(
                                f"运行 {int(elapsed)}秒，接收 {self.tick_count} 个tick "
                                f"({rate:.1f} tick/秒)，缓冲 {tick_buffered} 条，K线 {kline_bars} 根"
                            )
                            self.last_log_time = current_time
                
                except Exception as err:
                    logger.error(f"接收数据失败: {err}")
                    break
        
        except KeyboardInterrupt:
            logger.info("\n用户中断")
        
        elapsed = asyncio.get_event_loop().time() - self.start_time
        rate = self.tick_count / elapsed if elapsed > 0 else 0
        
        logger.info("=" * 60)
        logger.info(f"共接收 {self.tick_count} 个tick数据")
        logger.info(f"运行时长: {int(elapsed)} 秒")
        logger.info(f"平均速率: {rate:.1f} tick/秒")
        
        return self.tick_count
    
    async def close(self) -> None:
        """关闭连接"""
        if self.ws:
            await self.ws.close()
            logger.info("连接已关闭")


def load_instruments_from_json() -> list:
    """
    从 instruments.json 加载所有期货合约
    
    Returns:
        合约代码列表
    """
    instruments_file = project_root / "data" / "instruments.json"
    
    if not instruments_file.exists():
        logger.error(f"合约文件不存在: {instruments_file}")
        logger.info("\n请先运行自动登录脚本生成合约文件:")
        logger.info("  python scripts/update_instruments.py")
        return []
    
    try:
        with open(instruments_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        instruments_dict = data.get("instruments", {})
        
        if not instruments_dict:
            logger.warning("合约文件中没有合约数据")
            return []
        
        # 提取所有合约代码
        instrument_ids = list(instruments_dict.keys())
        
        logger.info(f"从 {instruments_file.name} 加载了 {len(instrument_ids)} 个期货合约")
        logger.info(f"更新时间: {data.get('update_time', 'N/A')}")
        
        return instrument_ids
        
    except Exception as err:
        logger.error(f"加载合约文件失败: {err}")
        return []


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("期货合约行情数据订阅与存储")
    logger.info("=" * 60)
    
    # 尝试加载 .env 文件
    env_file = project_root / ".env"
    if env_file.exists():
        logger.info("发现 .env 文件，正在加载环境变量...")
        try:
            from scripts.load_env import load_env
            if load_env(str(env_file)):
                logger.info("环境变量加载成功")
        except Exception as err:
            logger.warning(f"加载 .env 文件失败: {err}")
    
    # 加载配置
    try:
        config_path = project_root / "config" / "config_md.yaml"
        if not config_path.exists():
            logger.error(f"配置文件不存在: {config_path}")
            return
        
        logger.info(f"加载配置文件: config/config_md.yaml")
        GlobalConfig.load_config(str(config_path))
            
    except Exception as err:
        logger.error(f"加载配置失败: {err}")
        return
    
    # 加载合约列表
    logger.info("\n加载合约列表:")
    instruments = load_instruments_from_json()
    
    if not instruments:
        logger.error("没有可订阅的合约")
        return
    
    logger.info(f"\n将订阅以下合约（前10个）:")
    for i, inst in enumerate(instruments[:10], 1):
        logger.info(f"  {i}. {inst}")
    if len(instruments) > 10:
        logger.info(f"  ... 还有 {len(instruments) - 10} 个合约")
    
    # 获取登录信息
    logger.info("\n请输入登录信息:")
    
    user_id = os.getenv("CTP_USER_ID")
    password = os.getenv("CTP_PASSWORD")
    
    if not user_id:
        user_id = input("行情账号: ").strip()
    else:
        logger.info(f"行情账号: {user_id} (从环境变量读取)")
    
    if not password:
        password = input("行情密码: ").strip()
    else:
        logger.info("行情密码: ****** (从环境变量读取)")
    
    if not user_id or not password:
        logger.error("账号或密码不能为空")
        return
    
    # 获取服务器配置
    host = os.getenv("MD_HOST", "127.0.0.1")
    port = int(os.getenv("MD_PORT", "8080"))
    
    logger.info(f"\n服务器配置:")
    logger.info(f"  地址: {host}:{port}")
    logger.info(f"  经纪商: {GlobalConfig.BrokerID}")
    logger.info(f"  前置地址: {GlobalConfig.MdFrontAddress}")
    
    # 获取存储配置
    csv_config = GlobalConfig.Storage.csv
    kline_config = GlobalConfig.Storage.kline
    
    logger.info(f"\n存储配置:")
    logger.info(f"  Tick存储:")
    logger.info(f"    路径: {csv_config.base_path}")
    logger.info(f"    刷新间隔: {csv_config.flush_interval}秒")
    logger.info(f"  K线存储:")
    logger.info(f"    路径: ./data/klines")
    logger.info(f"    周期: {kline_config.periods}")
    
    logger.info("\n开始订阅流程...\n")
    
    # 创建客户端
    url = f"ws://{host}:{port}/"
    client = DataSubscriber(url)
    
    try:
        # 初始化存储引擎
        await client.initialize_storage(
            tick_base_path=csv_config.base_path,
            kline_base_path="./data/klines",
            kline_periods=kline_config.periods
        )
        
        # 连接
        if not await client.connect():
            return
        
        # 登录
        if not await client.login(user_id=user_id, password=password):
            return
        
        # 订阅合约
        if not await client.subscribe_market_data(instruments):
            return

        # 监听并存储行情数据
        tick_count = await client.listen_and_store()
        
        # 关闭连接
        await client.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("订阅流程完成！")
        logger.info("=" * 60)
        logger.info(f"接收到 {tick_count} 个tick数据")
        
        # 打印K线统计
        if client.kline_builder:
            kline_stats = client.kline_builder.get_stats()
            logger.info(f"合成K线 {kline_stats.get('total_bars', 0)} 根")
        
        logger.info("\n数据已存储到CSV文件:")
        logger.info("  - Tick: data/ticks/{交易日}/{合约代码}.csv")
        logger.info("  - K线: data/klines/{交易日}/{周期}/{合约代码}.csv")
        logger.info("=" * 60)
        
    finally:
        # 确保关闭存储引擎
        await client.close_storage()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n程序被中断")
    except Exception as e:
        logger.error(f"程序异常: {e}", exc_info=True)

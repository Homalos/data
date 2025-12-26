#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试存储系统的客户端
连接到行情服务并订阅合约
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


class TestStorageClient:
    """测试存储系统的客户端"""
    
    def __init__(self, url: str = "ws://127.0.0.1:8080/"):
        self.url = url
        self.ws = None
        self.request_id = 0
    
    async def connect(self):
        """连接到WebSocket服务"""
        try:
            logger.info(f"正在连接到 {self.url}")
            # 添加额外的连接选项，防止重定向问题
            self.ws = await websockets.connect(
                self.url,
                max_size=10 * 1024 * 1024,  # 10MB
                ping_interval=20,
                ping_timeout=20
            )
            logger.info("✅ 连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False
    
    async def send_request(self, request: dict):
        """发送请求"""
        try:
            request["RequestID"] = self.request_id
            self.request_id += 1
            
            message = json.dumps(request)
            await self.ws.send(message)
            logger.debug(f"发送请求: {request.get('MsgType')}")
            
        except Exception as e:
            logger.error(f"发送请求失败: {e}")
    
    async def receive_response(self, timeout: float = 30.0):
        """接收响应（跳过Ping消息）"""
        try:
            while True:
                message = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
                response = json.loads(message)
                
                # 跳过Ping消息
                if response.get("MsgType") == "Ping":
                    continue
                
                return response
        except asyncio.TimeoutError:
            logger.error(f"接收响应超时（{timeout}秒）")
            return None
        except Exception as e:
            logger.error(f"接收响应失败: {e}")
            return None
    
    async def login(self, user_id: str = "", password: str = ""):
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
            # 兼容两种消息类型
            if msg_type in ["OnRspUserLogin", "RspUserLogin"]:
                rsp_info = response.get("RspInfo", {})
                if rsp_info.get("ErrorID") == 0:
                    logger.info("✅ 登录成功")
                    
                    # 显示登录信息
                    rsp_user_login = response.get("RspUserLogin", {})
                    logger.info(f"交易日: {rsp_user_login.get('TradingDay', 'N/A')}")
                    logger.info(f"登录时间: {rsp_user_login.get('LoginTime', 'N/A')}")
                    
                    return True
                else:
                    logger.error(f"❌ 登录失败: {rsp_info.get('ErrorMsg')}")
                    return False
        
        return False
    
    async def subscribe_market_data(self, instruments: list):
        """订阅行情"""
        logger.info(f"正在订阅 {len(instruments)} 个合约...")
        
        request = {
            "MsgType": "SubscribeMarketData",
            "InstrumentID": instruments,
        }
        
        await self.send_request(request)
        
        # 等待订阅响应
        response = await self.receive_response()
        
        if response:
            msg_type = response.get("MsgType")
            # 兼容多种消息类型
            if msg_type in ["OnRspSubMarketData", "RspSubMarketData"]:
                logger.info("✅ 订阅成功")
                return True
        
        return False
    
    async def listen_market_data(self, duration: int = 0):
        """
        监听行情数据
        
        Args:
            duration: 监听时长（秒），0表示持续监听直到Ctrl+C
        """
        if duration == 0:
            logger.info("开始持续监听行情数据（按 Ctrl+C 停止）...")
        else:
            logger.info(f"开始监听行情数据（{duration}秒）...")
        logger.info("=" * 60)
        
        tick_count = 0
        start_time = asyncio.get_event_loop().time()
        last_log_time = start_time
        
        try:
            while True:
                # 检查是否超时（如果设置了时长）
                if duration > 0:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= duration:
                        break
                
                # 接收消息（不设置超时，让它一直等待）
                try:
                    message = await self.ws.recv()
                    response = json.loads(message)
                    
                    msg_type = response.get("MsgType")
                    
                    # 响应Ping消息
                    if msg_type == "Ping":
                        pong = {"MsgType": "Pong", "Timestamp": response.get("Timestamp")}
                        await self.ws.send(json.dumps(pong))
                        logger.debug("已响应心跳 Pong")
                        continue
                    
                    # 处理tick数据
                    if msg_type in ["OnRtnDepthMarketData", "RtnDepthMarketData"]:
                        tick_count += 1
                        depth_data = response.get("DepthMarketData", {})
                        
                        # 每10个tick打印一次
                        if tick_count % 10 == 0:
                            logger.info(
                                f"[{tick_count:4d}] {depth_data.get('InstrumentID'):8s} "
                                f"价格: {depth_data.get('LastPrice'):8.2f} "
                                f"成交量: {depth_data.get('Volume'):8d} "
                                f"时间: {depth_data.get('UpdateTime')}"
                            )
                        
                        # 每30秒打印一次进度
                        current_time = asyncio.get_event_loop().time()
                        if current_time - last_log_time >= 30:
                            elapsed = current_time - start_time
                            logger.info(f"已运行 {int(elapsed)}秒，接收 {tick_count} 个tick")
                            last_log_time = current_time
                
                except Exception as e:
                    logger.error(f"接收数据失败: {e}")
                    break
        
        except KeyboardInterrupt:
            logger.info("\n用户中断")
        
        logger.info("=" * 60)
        logger.info(f"✅ 共接收 {tick_count} 个tick数据")
        
        return tick_count
    
    async def close(self):
        """关闭连接"""
        if self.ws:
            await self.ws.close()
            logger.info("连接已关闭")


def load_instruments_from_json(limit: int = 10) -> list:
    """
    从 instruments.json 加载合约列表
    
    Args:
        limit: 最多加载多少个合约（0表示加载所有）
        
    Returns:
        合约代码列表
    """
    instruments_file = project_root / "data" / "instruments.json"
    
    if not instruments_file.exists():
        logger.warning(f"合约文件不存在: {instruments_file}")
        logger.info("请先运行自动登录脚本生成合约文件:")
        logger.info("  python scripts/auto_login_td.py")
        return []
    
    try:
        with open(instruments_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        instruments = data.get("instruments", [])
        
        if not instruments:
            logger.warning("合约文件中没有合约数据")
            return []
        
        # 提取合约代码
        if limit == 0:
            # 订阅所有合约
            instrument_ids = [inst["instrument_id"] for inst in instruments]
            logger.info(f"从 {instruments_file.name} 加载了所有 {len(instrument_ids)} 个合约")
        else:
            # 订阅指定数量的合约
            instrument_ids = [inst["instrument_id"] for inst in instruments[:limit]]
            logger.info(f"从 {instruments_file.name} 加载了 {len(instrument_ids)} 个合约（限制: {limit}）")
        
        return instrument_ids
        
    except Exception as e:
        logger.error(f"加载合约文件失败: {e}")
        return []


def load_test_config(config_path: Path) -> dict:
    """
    从配置文件加载测试配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        测试配置字典
    """
    import yaml
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        test_config = config.get("Test", {})
        
        return {
            "subscribe_limit": test_config.get("SubscribeLimit", 10),
            "listen_duration": test_config.get("ListenDuration", 0)  # 默认0表示持续监听
        }
        
    except Exception as e:
        logger.warning(f"加载测试配置失败: {e}，使用默认值")
        return {
            "subscribe_limit": 10,
            "listen_duration": 0  # 默认持续监听
        }


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("行情存储系统测试客户端")
    logger.info("=" * 60)
    
    # 尝试加载 .env 文件
    env_file = project_root / ".env"
    if env_file.exists():
        logger.info("发现 .env 文件，正在加载环境变量...")
        try:
            from scripts.load_env import load_env
            if load_env(str(env_file)):
                logger.info("✅ 环境变量加载成功")
        except Exception as e:
            logger.warning(f"加载 .env 文件失败: {e}")
    
    # 加载配置
    config_path = None
    try:
        # 尝试加载配置文件
        config_files = [
            "config/config_md.yaml",
            "config/config.yaml",
            "config/config.sample.yaml"
        ]
        
        config_loaded = False
        for config_file in config_files:
            config_path = project_root / config_file
            if config_path.exists():
                logger.info(f"加载配置文件: {config_file}")
                GlobalConfig.load_config(str(config_path))
                config_loaded = True
                break
        
        if not config_loaded:
            logger.error("未找到配置文件")
            return
            
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return
    
    # 加载测试配置
    test_config = load_test_config(config_path)
    subscribe_limit = test_config["subscribe_limit"]
    listen_duration = test_config.get("listen_duration", 0)  # 默认0表示持续监听
    
    logger.info(f"\n测试配置:")
    logger.info(f"  订阅合约数量: {'所有' if subscribe_limit == 0 else subscribe_limit}")
    if listen_duration == 0:
        logger.info(f"  监听模式: 持续监听（按 Ctrl+C 停止）")
    else:
        logger.info(f"  监听时长: {listen_duration} 秒")
    
    # 获取登录信息
    logger.info("\n请输入登录信息:")
    
    # 从环境变量或用户输入获取账号密码
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
    
    # 加载合约列表
    logger.info("\n加载合约列表:")
    
    instruments = load_instruments_from_json(limit=subscribe_limit)
    
    if not instruments:
        logger.error("没有可订阅的合约")
        return
    
    logger.info(f"\n将订阅以下合约:")
    for i, inst in enumerate(instruments[:10], 1):
        logger.info(f"  {i}. {inst}")
    if len(instruments) > 10:
        logger.info(f"  ... 还有 {len(instruments) - 10} 个合约")
    
    logger.info("\n开始测试流程...\n")
    
    # 创建客户端
    url = f"ws://{host}:{port}/"
    client = TestStorageClient(url)
    
    # 连接
    if not await client.connect():
        return
    
    # 登录
    if not await client.login(user_id=user_id, password=password):
        return
    
    # 订阅合约
    if not await client.subscribe_market_data(instruments):
        return
    
    # 监听行情数据
    tick_count = await client.listen_market_data(duration=listen_duration)
    
    # 关闭连接
    await client.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 测试完成！")
    logger.info("=" * 60)
    logger.info(f"接收到 {tick_count} 个tick数据")
    logger.info("\n数据已存储到CSV文件:")
    logger.info("  - 路径: data/ticks/{交易日}/{合约代码}.csv")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n程序被中断")
    except Exception as e:
        logger.error(f"程序异常: {e}", exc_info=True)

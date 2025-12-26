#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动连接并登录交易服务，更新全市场期货合约信息

此脚本用于自动连接到交易WebSocket服务并执行登录操作
登录成功后会自动查询全市场合约并保存到JSON文件
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import websockets
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import GlobalConfig


class TdAutoLogin:
    """交易服务自动登录客户端"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8001,
        token: Optional[str] = None,
        user_id: str = "",
        password: str = ""
    ):
        """
        初始化自动登录客户端

        Args:
            host: 服务器地址
            port: 服务器端口
            token: 认证令牌（如果配置了）
            user_id: 交易账号
            password: 交易密码
        """
        self.host = host
        self.port = port
        self.token = token
        self.user_id = user_id
        self.password = password
        self.websocket = None   # websocket连接对象
        self.connected = False  # 是否已连接
        self.logged_in = False  # 是否已登录
        self.query_symbols = False  # 是否已查询合约
        self._ws_timeout = 10.0  # 单次WebSocket超时时间，单位秒
        self._login_timeout = 30.0  # 登录超时时间，单位秒
        self._symbol_query_timeout = 120.0  # 查询合约超时时间，单位秒
        self._request_id = 0  # 请求ID计数器
        self._instruments_cache = []  # 临时缓存查询到的合约

    def _get_next_request_id(self) -> int:
        """
        获取下一个请求ID

        Returns:
            int: 递增后的请求ID
        """
        self._request_id += 1
        return self._request_id

    def _build_ws_url(self) -> str:
        """构建WebSocket URL"""
        url = f"ws://{self.host}:{self.port}/"
        if self.token:
            url += f"?token={self.token}"
        return url

    async def connect(self) -> bool:
        """
        连接到WebSocket服务

        Returns:
            是否连接成功
        """
        try:
            url = self._build_ws_url()
            logger.info(f"正在连接到交易服务: {url}")

            # 禁用自动 ping/pong，使用应用层心跳
            self.websocket = await websockets.connect(
                url,
                ping_interval=None,  # 禁用 websockets 库的自动 ping
                ping_timeout=None    # 禁用 websockets 库的 ping 超时
            )

            self.connected = True
            logger.info("连接成功")
            return True

        except Exception as err:
            self.connected = False
            logger.error(f"连接失败: {err}")
            return False

    async def login(self) -> bool:
        """
        发送登录请求

        Returns:
            是否登录成功
        """
        if not self.connected:
            self.logged_in = False
            logger.error("未连接到服务器，无法登录")
            return False

        try:
            # 构建登录请求
            login_request = {
                "MsgType": "ReqUserLogin",
                "RequestID": self._get_next_request_id(),  # 请求ID
                "ReqUserLogin": {
                    "UserID": self.user_id,
                    "Password": self.password
                }
            }

            logger.info(f"正在登录，账号: {self.user_id}")
            # 发送登录请求
            logger.info(f"发送登录请求: {json.dumps(login_request, ensure_ascii=False)}")

            await self.websocket.send(json.dumps(login_request))

            # 等待登录完成
            return await self.wait_for_login()

        except Exception as err:
            self.logged_in = False
            logger.error(f"登录异常: {err}")
            return False

    async def wait_for_login(self) -> bool:
        """
        等待用户登录响应。

        该方法通过WebSocket连接循环接收消息，等待登录响应。会忽略心跳消息，
        处理登录成功和失败的情况，并在超时后返回相应结果。

        Returns:
            bool: 登录成功返回True，登录失败或超时返回False
        """
        logger.info(f"等待登录响应（{self._login_timeout}秒超时）...")
        start_time = asyncio.get_event_loop().time()

        try:
            while True:
                # 检查总超时
                if asyncio.get_event_loop().time() - start_time > self._login_timeout:
                    self.logged_in = False
                    logger.error("登录超时")
                    return False

                try:
                    response = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=self._ws_timeout
                    )

                    response_data = json.loads(response)
                    msg_type = response_data.get("MsgType")

                    logger.debug(f"收到消息: MsgType={msg_type}")

                    # 处理心跳消息
                    if msg_type == "Ping":
                        logger.debug("收到Ping，回复Pong")
                        await self.websocket.send(json.dumps({"MsgType": "Pong"}))
                        continue
                    elif msg_type == "Pong":
                        logger.debug("收到Pong")
                        continue

                    # 检查是否是登录响应
                    if msg_type in ["OnRspUserLogin", "RspUserLogin"]:
                        rsp_info = response_data.get("RspInfo", {})
                        error_id = rsp_info.get("ErrorID", -1)

                        if error_id == 0:
                            self.logged_in = True
                            logger.info("登录成功")

                            # 显示登录信息
                            rsp_user_login = response_data.get("RspUserLogin", {})
                            logger.info(f"交易日: {rsp_user_login.get('TradingDay', 'N/A')}")
                            logger.info(f"登录时间: {rsp_user_login.get('LoginTime', 'N/A')}")
                            logger.info(f"前置编号: {rsp_user_login.get('FrontID', 'N/A')}")
                            logger.info(f"会话编号: {rsp_user_login.get('SessionID', 'N/A')}")

                            return True
                        else:
                            self.logged_in = False
                            error_msg = rsp_info.get("ErrorMsg", "未知错误")
                            logger.error(f"登录失败: [{error_id}] {error_msg}")
                            return False
                    else:
                        logger.warning(f"收到意外消息类型: {msg_type}")
                        continue

                except asyncio.TimeoutError:
                    # 单次接收超时，继续等待
                    logger.debug(f"等待中...")
                    continue
                except json.JSONDecodeError as err:
                    logger.warning(f"JSON解析失败: {err}")
                    continue

            return False
        except Exception as err:
            self.logged_in = False
            logger.error(f"等待登录响应时出错: {err}")
            return False

    async def query_instruments(self) -> bool:
        """
        主动查询全市场合约

        Returns:
            是否查询成功
        """
        if not self.logged_in:
            logger.error("未登录，无法查询合约")
            return False

        try:
            # 构建查询合约请求
            query_request = {
                "MsgType": "ReqQryInstrument",
                "RequestID": self._get_next_request_id(),
                "ReqQryInstrument": {
                    "InstrumentID": ""  # 空表示查询所有合约
                }
            }

            logger.info("正在查询全市场合约...")
            # 发送查询请求
            await self.websocket.send(json.dumps(query_request))

            # 等待合约查询完成
            return await self.wait_for_instruments_query(timeout=self._symbol_query_timeout)

        except Exception as err:
            logger.error(f"查询合约异常: {err}")
            return False

    async def wait_for_instruments_query(self, timeout: float = 60.0) -> bool:
        """
        等待合约查询完成并保存到JSON文件

        Args:
            timeout: 超时时间（秒）
        """
        logger.info("等待合约查询完成...")

        start_time = asyncio.get_event_loop().time()
        instrument_count = 0

        try:
            while True:
                # 检查总超时
                if asyncio.get_event_loop().time() - start_time > timeout:
                    self.query_symbols = False
                    logger.warning(f"等待超时，已接收 {instrument_count} 个合约")
                    return False

                try:
                    response = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=self._ws_timeout
                    )

                    response_data = json.loads(response)
                    msg_type = response_data.get("MsgType")

                    # 处理心跳消息
                    if msg_type == "Ping":
                        logger.debug("收到Ping，回复Pong")
                        await self.websocket.send(json.dumps({"MsgType": "Pong"}))
                        continue
                    elif msg_type == "Pong":
                        logger.debug("收到Pong")
                        continue

                    # 检查是否是合约查询响应
                    if msg_type in ["OnRspQryInstrument", "RspQryInstrument"]:
                        instrument = response_data.get("Instrument", {})
                        is_last = response_data.get("IsLast", False)

                        if instrument.get("InstrumentID"):
                            # 收集合约信息
                            self._collect_instrument(instrument)
                            instrument_count += 1

                            # 每100个打印一次进度
                            if instrument_count % 100 == 0:
                                logger.info(f"已接收 {instrument_count} 个合约...")

                        # 查询完成，保存到文件
                        if is_last:
                            self.query_symbols = True
                            logger.info(f"合约查询完成，共接收 {instrument_count} 个合约")
                            
                            # 保存到JSON文件
                            if self._save_instruments_to_file():
                                logger.info("✅ 合约信息已保存到 data/instruments.json")
                            else:
                                logger.warning("⚠️ 合约信息保存失败")
                            
                            return True

                except asyncio.TimeoutError:
                    # 接收超时，继续等待
                    logger.debug("等待中...")
                    continue
                except json.JSONDecodeError as err:
                    logger.warning(f"JSON解析失败: {err}")
                    continue

            return False
        except Exception as err:
            self.query_symbols = False
            logger.error(f"等待合约查询时出错: {err}")
            return False

    def _collect_instrument(self, instrument: dict) -> None:
        """
        收集合约信息（只收集期货合约，过滤期权）

        Args:
            instrument: 合约信息字典
        """
        try:
            instrument_id = instrument.get("InstrumentID", "")
            
            # 只收集期货合约，过滤期权
            if self._is_futures(instrument_id):
                # 提取关键字段
                instrument_info = {
                    "instrument_id": instrument_id,
                    "exchange_id": instrument.get("ExchangeID", ""),
                    "product_id": instrument.get("ProductID", ""),
                    "product_class": instrument.get("ProductClass", ""),
                    "delivery_year": instrument.get("DeliveryYear", 0),
                    "delivery_month": instrument.get("DeliveryMonth", 0),
                    "max_market_order_volume": instrument.get("MaxMarketOrderVolume", 0),
                    "min_market_order_volume": instrument.get("MinMarketOrderVolume", 0),
                    "max_limit_order_volume": instrument.get("MaxLimitOrderVolume", 0),
                    "min_limit_order_volume": instrument.get("MinLimitOrderVolume", 0),
                    "volume_multiple": instrument.get("VolumeMultiple", 0),
                    "price_tick": instrument.get("PriceTick", 0.0),
                    "create_date": instrument.get("CreateDate", ""),
                    "open_date": instrument.get("OpenDate", ""),
                    "expire_date": instrument.get("ExpireDate", ""),
                    "is_trading": instrument.get("IsTrading", 0),
                }
                
                self._instruments_cache.append(instrument_info)
                
        except Exception as e:
            logger.error(f"收集合约信息失败: {e}")

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
        
        # 必须以字母开头
        if not instrument_id[0].isalpha():
            return False
        
        # 期货合约代码最长6位
        if len(instrument_id) > 6:
            return False
        
        return True

    def _save_instruments_to_file(self) -> bool:
        """
        保存合约信息到JSON文件

        Returns:
            是否保存成功
        """
        try:
            if not self._instruments_cache:
                logger.warning("没有合约信息需要保存")
                return False
            
            # 确保data目录存在
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            
            # 构建保存数据
            from datetime import datetime
            save_data = {
                "update_time": datetime.now().isoformat(),
                "total_count": len(self._instruments_cache),
                "instruments": {
                    inst["instrument_id"]: inst 
                    for inst in self._instruments_cache
                }
            }
            
            # 保存到JSON文件
            json_file = data_dir / "instruments.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已保存 {len(self._instruments_cache)} 个期货合约（已过滤期权）")
            
            # 清空缓存
            self._instruments_cache = []
            
            return True
            
        except Exception as err:
            logger.error(f"保存合约信息失败: {err}", exc_info=True)
            return False

    async def close(self) -> None:
        """关闭WebSocket连接。

        执行清理操作，确保连接资源被正确释放。
        如果存在活跃的WebSocket连接，则关闭连接并记录日志。
        """
        if self.websocket:
            await self.websocket.close()
            logger.info("连接已关闭")

    async def run(self) -> bool:
        """运行自动登录流程"""
        try:
            # 1. 连接
            if not await self.connect():
                return False

            # 2. 登录
            if not await self.login():
                return False

            # 3. 主动查询全市场合约
            if not await self.query_instruments():
                return False

            return True
        finally:
            await self.close()


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("交易服务自动登录脚本")
    logger.info("=" * 60)

    # 尝试加载 .env 文件
    import os
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
        # 尝试加载配置文件
        config_files = [
            "config/config_td.yaml"
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

    # 获取登录信息
    logger.info("\n请输入登录信息:")

    # 从环境变量或用户输入获取账号密码
    user_id = os.getenv("CTP_USER_ID")
    password = os.getenv("CTP_PASSWORD")

    if not user_id:
        user_id = input("交易账号: ").strip()
    else:
        logger.info(f"交易账号: {user_id} (从环境变量读取)")

    if not password:
        password = input("交易密码: ").strip()
    else:
        logger.info("交易密码: ****** (从环境变量读取)")

    if not user_id or not password:
        logger.error("账号或密码不能为空")
        return

    # 获取服务器配置
    host = os.getenv("TD_HOST", "127.0.0.1")
    port = int(os.getenv("TD_PORT", "8081"))
    token = os.getenv("TD_TOKEN", getattr(GlobalConfig, "Token", None))

    logger.info(f"\n服务器配置:")
    logger.info(f"  地址: {host}:{port}")
    logger.info(f"  Token: {'已配置' if token else '未配置'}")
    logger.info(f"  经纪商: {GlobalConfig.BrokerID}")
    logger.info(f"  前置地址: {GlobalConfig.TdFrontAddress}")

    # 创建客户端并运行
    client = TdAutoLogin(
        host=host,
        port=port,
        token=token,
        user_id=user_id,
        password=password
    )

    logger.info("\n开始自动登录流程...\n")

    success = await client.run()

    if success:
        logger.info("\n" + "=" * 60)
        logger.info("自动登录流程完成")
        logger.info("=" * 60)
        logger.info("\n下一步:")
        logger.info("1. 运行测试脚本查看合约信息:")
        logger.info("   python scripts/test_auto_query_instruments.py")
        logger.info("\n2. 查看合约JSON文件:")
        logger.info("   data/instruments.json")
    else:
        logger.error("\n" + "=" * 60)
        logger.error("自动登录流程失败")
        logger.error("=" * 60)
        logger.info("\n请检查:")
        logger.info("1. 交易服务是否已启动")
        logger.info("2. 账号密码是否正确")
        logger.info("3. 网络连接是否正常")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n用户中断")
    except Exception as e:
        logger.error(f"程序异常: {e}", exc_info=True)

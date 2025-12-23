#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动连接并登录交易服务

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
        self.websocket = None
        self.connected = False
        self.logged_in = False
        
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
            
            self.websocket = await websockets.connect(
                url,
                ping_interval=30,
                ping_timeout=60
            )
            
            self.connected = True
            logger.info("✅ 连接成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False
    
    async def login(self) -> bool:
        """
        发送登录请求
        
        Returns:
            是否登录成功
        """
        if not self.connected:
            logger.error("未连接到服务器，无法登录")
            return False
        
        try:
            # 构建登录请求
            login_request = {
                "MsgType": "ReqUserLogin",
                "RequestID": 0,
                "ReqUserLogin": {
                    "UserID": self.user_id,
                    "Password": self.password
                }
            }
            
            logger.info(f"正在登录，账号: {self.user_id}")
            
            # 发送登录请求
            logger.info(f"发送登录请求: {json.dumps(login_request, ensure_ascii=False)}")
            await self.websocket.send(json.dumps(login_request))
            
            # 等待登录响应（循环接收，忽略心跳消息）
            start_time = asyncio.get_event_loop().time()
            timeout = 30.0
            
            while True:
                # 检查超时
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.error("❌ 登录超时")
                    return False
                
                try:
                    response = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=5.0
                    )
                    
                    response_data = json.loads(response)
                    msg_type = response_data.get("MsgType")
                    
                    # 调试：打印收到的消息
                    logger.debug(f"收到消息: MsgType={msg_type}")
                    
                    # 忽略心跳消息
                    if msg_type in ["Ping", "Pong"]:
                        logger.debug(f"收到心跳消息: {msg_type}")
                        continue
                    
                    # 检查是否是登录响应
                    if msg_type in ["OnRspUserLogin", "RspUserLogin"]:
                        rsp_info = response_data.get("RspInfo", {})
                        error_id = rsp_info.get("ErrorID", -1)
                        
                        if error_id == 0:
                            self.logged_in = True
                            logger.info("✅ 登录成功")
                            
                            # 显示登录信息
                            rsp_user_login = response_data.get("RspUserLogin", {})
                            logger.info(f"交易日: {rsp_user_login.get('TradingDay', 'N/A')}")
                            logger.info(f"登录时间: {rsp_user_login.get('LoginTime', 'N/A')}")
                            logger.info(f"前置编号: {rsp_user_login.get('FrontID', 'N/A')}")
                            logger.info(f"会话编号: {rsp_user_login.get('SessionID', 'N/A')}")
                            
                            return True
                        else:
                            error_msg = rsp_info.get("ErrorMsg", "未知错误")
                            logger.error(f"❌ 登录失败: [{error_id}] {error_msg}")
                            return False
                    else:
                        logger.warning(f"收到意外消息类型: {msg_type}")
                        # 继续等待登录响应
                        continue
                        
                except asyncio.TimeoutError:
                    # 5秒内没有消息，继续等待
                    continue
                
        except Exception as e:
            logger.error(f"❌ 登录异常: {e}")
            return False
    
    async def wait_for_instruments_query(self, timeout: float = 60.0):
        """
        等待合约查询完成
        
        Args:
            timeout: 超时时间（秒）
        """
        logger.info("等待合约查询完成...")
        
        start_time = asyncio.get_event_loop().time()
        instrument_count = 0
        
        try:
            while True:
                # 检查超时
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.warning(f"⚠️  等待超时，已接收 {instrument_count} 个合约")
                    break
                
                # 接收消息
                try:
                    response = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=5.0
                    )
                    
                    response_data = json.loads(response)
                    msg_type = response_data.get("MsgType")
                    
                    # 忽略心跳消息
                    if msg_type in ["Ping", "Pong"]:
                        continue
                    
                    # 检查是否是合约查询响应
                    if msg_type in ["OnRspQryInstrument", "RspQryInstrument"]:
                        instrument = response_data.get("Instrument", {})
                        is_last = response_data.get("IsLast", False)
                        
                        if instrument.get("InstrumentID"):
                            instrument_count += 1
                            
                            # 每100个打印一次进度
                            if instrument_count % 100 == 0:
                                logger.info(f"已接收 {instrument_count} 个合约...")
                        
                        # 查询完成
                        if is_last:
                            logger.info(f"✅ 合约查询完成，共 {instrument_count} 个合约")
                            logger.info("合约信息已保存到 data/instruments.json")
                            break
                    
                except asyncio.TimeoutError:
                    # 5秒内没有消息，继续等待
                    continue
                    
        except Exception as e:
            logger.error(f"等待合约查询时出错: {e}")
    
    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()
            logger.info("连接已关闭")
    
    async def run(self):
        """运行自动登录流程"""
        try:
            # 1. 连接
            if not await self.connect():
                return False
            
            # 2. 登录
            if not await self.login():
                return False
            
            # 3. 等待合约查询完成
            await self.wait_for_instruments_query(timeout=120.0)
            
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
                logger.info("✅ 环境变量加载成功")
        except Exception as e:
            logger.warning(f"加载 .env 文件失败: {e}")
    
    # 加载配置
    try:
        # 尝试加载配置文件
        config_files = [
            "config/config_td.yaml",
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
        logger.info("✅ 自动登录流程完成")
        logger.info("=" * 60)
        logger.info("\n下一步:")
        logger.info("1. 运行测试脚本查看合约信息:")
        logger.info("   python scripts/test_auto_query_instruments.py")
        logger.info("\n2. 查看合约JSON文件:")
        logger.info("   data/instruments.json")
    else:
        logger.error("\n" + "=" * 60)
        logger.error("❌ 自动登录流程失败")
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试CTP API连接的简单脚本
"""
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ctp import thostmduserapi as mdapi
from loguru import logger


class SimpleMdSpi(mdapi.CThostFtdcMdSpi):
    """简单的行情SPI，用于测试连接"""
    
    def __init__(self):
        super().__init__()
        self.connected = False
        self.login_success = False
    
    def OnFrontConnected(self):
        logger.info("✅ CTP前置连接成功！")
        self.connected = True
    
    def OnFrontDisconnected(self, reason):
        logger.warning(f"❌ CTP前置断开连接，原因: {reason}")
        self.connected = False
    
    def OnRspUserLogin(self, rsp_user_login, rsp_info, request_id, is_last):
        if rsp_info and rsp_info.ErrorID != 0:
            logger.error(f"❌ 登录失败: {rsp_info.ErrorMsg}")
        else:
            logger.info("✅ 登录成功！")
            self.login_success = True


def test_connection():
    """测试CTP连接"""
    logger.info("=" * 60)
    logger.info("CTP连接测试")
    logger.info("=" * 60)
    
    # 配置
    front_address = "tcp://182.254.243.31:30012"
    broker_id = "9999"
    user_id = "160219"
    password = "Aa123456"
    con_file_path = "./con_file/test_md"
    
    logger.info(f"前置地址: {front_address}")
    logger.info(f"经纪商ID: {broker_id}")
    logger.info(f"用户ID: {user_id}")
    logger.info(f"连接文件路径: {con_file_path}")
    logger.info("")
    
    # 创建API
    logger.info("步骤1: 创建CTP API...")
    api = mdapi.CThostFtdcMdApi.CreateFtdcMdApi(con_file_path)
    logger.info("✅ API创建成功")
    
    # 创建SPI
    logger.info("步骤2: 创建SPI回调...")
    spi = SimpleMdSpi()
    logger.info("✅ SPI创建成功")
    
    # 注册SPI
    logger.info("步骤3: 注册SPI...")
    api.RegisterSpi(spi)
    logger.info("✅ SPI注册成功")
    
    # 注册前置
    logger.info("步骤4: 注册前置地址...")
    api.RegisterFront(front_address)
    logger.info("✅ 前置地址注册成功")
    
    # 初始化
    logger.info("步骤5: 初始化API（开始连接）...")
    api.Init()
    logger.info("✅ Init()调用成功（非阻塞）")
    logger.info("")
    
    # 等待连接
    logger.info("等待CTP前置连接...")
    max_wait = 30
    for i in range(max_wait):
        if spi.connected:
            logger.info(f"✅ 连接成功！耗时: {i+1}秒")
            break
        time.sleep(1)
        if (i + 1) % 5 == 0:
            logger.info(f"  等待中... ({i+1}/{max_wait}秒)")
    else:
        logger.error(f"❌ 连接超时！等待了{max_wait}秒仍未连接")
        logger.error("可能的原因:")
        logger.error("  1. 网络问题（防火墙、代理等）")
        logger.error("  2. CTP服务器地址错误")
        logger.error("  3. CTP服务器维护中")
        api.Release()
        return False
    
    # 登录
    logger.info("")
    logger.info("步骤6: 发送登录请求...")
    req = mdapi.CThostFtdcReqUserLoginField()
    req.BrokerID = broker_id
    req.UserID = user_id
    req.Password = password
    ret = api.ReqUserLogin(req, 0)
    if ret != 0:
        logger.error(f"❌ 登录请求发送失败，返回码: {ret}")
        api.Release()
        return False
    logger.info("✅ 登录请求已发送")
    
    # 等待登录响应
    logger.info("等待登录响应...")
    for i in range(10):
        if spi.login_success:
            logger.info(f"✅ 登录成功！耗时: {i+1}秒")
            break
        time.sleep(1)
        if (i + 1) % 3 == 0:
            logger.info(f"  等待中... ({i+1}/10秒)")
    else:
        logger.error("❌ 登录超时！")
        api.Release()
        return False
    
    # 清理
    logger.info("")
    logger.info("步骤7: 释放资源...")
    api.Release()
    logger.info("✅ 资源释放成功")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ 测试完成！CTP连接正常")
    logger.info("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception(f"测试过程中发生异常: {e}")
        sys.exit(1)

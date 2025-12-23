#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : md_app.py
@Date       : 2025/12/3 13:20
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 行情服务 FastAPI 应用
"""
import time
from typing import Any, Optional
from fastapi import FastAPI, WebSocket
from loguru import logger

from ..services.connection import MdConnection
from ..services.cache_manager import CacheManager
from ..services.strategy_manager import StrategyManager
from ..utils import GlobalConfig
from ..utils.metrics import MetricsCollector


# 全局实例
_cache_manager: Optional[CacheManager] = None
_metrics_collector: Optional[MetricsCollector] = None
_strategy_manager: Optional[StrategyManager] = None
_tick_storage: Optional[Any] = None  # 新增：Tick存储
_instrument_manager: Optional[Any] = None  # 新增：合约管理器
_kline_builder: Optional[Any] = None  # 新增：K线合成器
_kline_storage: Optional[Any] = None  # 新增：K线存储
_initialized: bool = False


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """
    应用启动事件处理器
    
    初始化 CacheManager、MetricsCollector、StrategyManager 和存储服务
    """
    global _cache_manager, _metrics_collector, _strategy_manager, _tick_storage, _instrument_manager, _kline_builder, _kline_storage, _initialized
    
    if _initialized:
        return
    
    logger.info("正在初始化行情服务...")
    
    # 初始化 MetricsCollector（先初始化，以便注入到其他组件）
    try:
        _metrics_collector = MetricsCollector(GlobalConfig.Metrics)
        if GlobalConfig.Metrics.enabled:
            # 启动定期报告
            await _metrics_collector.start_reporting()
            logger.info("MetricsCollector 初始化成功")
        else:
            logger.info("性能指标收集未启用")
    except Exception as e:
        logger.warning(f"MetricsCollector 初始化失败: {e}")
        _metrics_collector = None
    
    # 初始化 CacheManager
    try:
        _cache_manager = CacheManager()
        if GlobalConfig.Cache.enabled:
            await _cache_manager.initialize(GlobalConfig.Cache)
            # 注入 MetricsCollector
            if _metrics_collector:
                _cache_manager.set_metrics_collector(_metrics_collector)
            logger.info("CacheManager 初始化成功")
        else:
            logger.info("Redis 缓存未启用")
    except Exception as e:
        logger.warning(f"CacheManager 初始化失败，将在无缓存模式下运行: {e}")
        _cache_manager = None
    
    # 初始化 StrategyManager
    try:
        _strategy_manager = StrategyManager(
            cache_manager=_cache_manager,
            max_strategies=GlobalConfig.Strategy.max_strategies if hasattr(GlobalConfig, 'Strategy') else None
        )
        logger.info("StrategyManager 初始化成功")
    except Exception as e:
        logger.warning(f"StrategyManager 初始化失败: {e}")
        _strategy_manager = None
    
    # 【新增】初始化存储服务
    if hasattr(GlobalConfig, 'Storage') and GlobalConfig.Storage.enabled:
        try:
            from ..storage import InstrumentManager, TickStorage, KLineBuilder, KLineStorage
            
            # 初始化合约管理器
            _instrument_manager = InstrumentManager(
                cache_path=GlobalConfig.Storage.instruments.cache_path
            )
            # 尝试从缓存加载
            if not _instrument_manager.load_from_cache():
                logger.info("合约缓存不存在，将在首次连接后查询")
            else:
                logger.info(f"从缓存加载 {len(_instrument_manager.instruments)} 个合约")
            
            # 初始化Tick存储
            _tick_storage = TickStorage(GlobalConfig.Storage.influxdb)
            await _tick_storage.initialize()
            logger.info("Tick存储引擎初始化成功")
            
            # 初始化K线存储
            if GlobalConfig.Storage.kline.enabled:
                _kline_storage = KLineStorage(GlobalConfig.Storage.influxdb)
                await _kline_storage.initialize()
                logger.info("K线存储引擎初始化成功")
                
                # 初始化K线合成器
                _kline_builder = KLineBuilder(
                    kline_storage=_kline_storage,
                    enabled_periods=GlobalConfig.Storage.kline.periods
                )
                logger.info("K线合成器初始化成功")
            else:
                logger.info("K线合成未启用")
            
        except Exception as e:
            logger.error(f"存储服务初始化失败: {e}", exc_info=True)
            _tick_storage = None
            _instrument_manager = None
            _kline_builder = None
            _kline_storage = None
    else:
        logger.info("存储服务未启用")
    
    _initialized = True
    logger.info("行情服务初始化完成")


@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭事件处理器
    
    清理 CacheManager、MetricsCollector、StrategyManager 和存储服务资源
    """
    global _cache_manager, _metrics_collector, _strategy_manager, _tick_storage, _kline_builder, _kline_storage, _initialized
    
    logger.info("正在关闭行情服务...")
    
    # 停止所有策略
    if _strategy_manager:
        try:
            # 停止所有运行中的策略
            strategies = _strategy_manager.list_strategies()
            for strategy_info in strategies:
                if strategy_info.status.value == "running":
                    await _strategy_manager.stop_strategy(strategy_info.strategy_id)
            logger.info("所有策略已停止")
        except Exception as e:
            logger.error(f"停止策略失败: {e}")
    
    # 【新增】关闭存储服务
    if _kline_builder:
        try:
            await _kline_builder.close()
            logger.info("K线合成器已关闭")
        except Exception as e:
            logger.error(f"关闭K线合成器失败: {e}")
    
    if _kline_storage:
        try:
            await _kline_storage.close()
            logger.info("K线存储引擎已关闭")
        except Exception as e:
            logger.error(f"关闭K线存储失败: {e}")
    
    if _tick_storage:
        try:
            await _tick_storage.close()
            logger.info("Tick存储引擎已关闭")
        except Exception as e:
            logger.error(f"关闭Tick存储失败: {e}")
    
    # 停止 MetricsCollector
    if _metrics_collector:
        try:
            await _metrics_collector.stop_reporting()
            logger.info("MetricsCollector 已停止")
        except Exception as e:
            logger.error(f"停止 MetricsCollector 失败: {e}")
    
    # 关闭 CacheManager
    if _cache_manager:
        try:
            await _cache_manager.close()
            logger.info("CacheManager 已关闭")
        except Exception as e:
            logger.error(f"关闭 CacheManager 失败: {e}")
    
    _initialized = False
    logger.info("行情服务已关闭")


class MdConnectionWithMetrics(MdConnection):
    """
    扩展的 MdConnection，支持性能指标记录和缓存管理
    
    在原有 MdConnection 基础上添加：
    - CacheManager 和 MetricsCollector 依赖注入
    - 消息延迟记录
    - 保持 JSON 协议向后兼容
    """
    
    def __init__(self, websocket: WebSocket):
        """
        初始化连接
        
        Args:
            websocket: WebSocket 连接对象
        """
        super().__init__(websocket)
        self._message_start_time: Optional[float] = None
    
    def create_client(self):
        """
        创建行情客户端实例并注入依赖
        
        Returns:
            MdClient: 配置好的行情客户端实例
        """
        # 调用父类方法创建客户端
        client = super().create_client()
        
        # 注入 CacheManager
        if _cache_manager:
            client.set_cache_manager(_cache_manager)
        
        # 注入 MetricsCollector
        if _metrics_collector:
            client.set_metrics_collector(_metrics_collector)
        
        # 注入 StrategyManager
        if _strategy_manager:
            client.set_strategy_manager(_strategy_manager)
        
        # 【新增】注入存储服务
        if _tick_storage:
            client.set_tick_storage(_tick_storage)
        
        if _instrument_manager:
            client.set_instrument_manager(_instrument_manager)
        
        if _kline_builder:
            client.set_kline_builder(_kline_builder)
        
        return client
    
    async def recv(self) -> dict[str, Any]:
        """
        接收消息并记录开始时间
        
        Returns:
            dict[str, Any]: 接收到的消息
        """
        # 记录消息接收时间
        self._message_start_time = time.time()
        
        # 调用父类方法接收消息
        return await super().recv()
    
    async def send(self, data: dict[str, Any]) -> None:
        """
        发送消息并记录延迟指标
        
        Args:
            data: 要发送的消息数据
        """
        # 调用父类方法发送消息
        await super().send(data)
        
        # 记录消息延迟（从接收到发送的时间）
        if self._message_start_time and _metrics_collector:
            latency_ms = (time.time() - self._message_start_time) * 1000
            _metrics_collector.record_latency("md_message_latency", latency_ms)
            self._message_start_time = None


@app.websocket("/")
async def md_websocket(websocket: WebSocket, token: str | None = None):
    """
    WebSocket端点，用于处理CTP行情数据连接
    
    集成了性能监控和缓存管理功能，同时保持 JSON 协议向后兼容

    Args:
        websocket: FastAPI WebSocket连接对象
        token: 可选的认证令牌

    Returns:
        None: 无返回值，通过WebSocket持续发送和接收数据
    """
    # Token 验证
    if GlobalConfig.Token and token != GlobalConfig.Token:
        await websocket.close(code=1008)
        return

    # 使用扩展的连接类（支持指标记录和缓存）
    connection = MdConnectionWithMetrics(websocket)
    
    # 记录活跃连接数
    if _metrics_collector:
        _metrics_collector.record_gauge("md_active_connections", 1)

    try:
        await connection.run()
    finally:
        # 连接关闭时更新指标
        if _metrics_collector:
            _metrics_collector.record_gauge("md_active_connections", 0)

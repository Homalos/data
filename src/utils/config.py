#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class MetricsConfig:
    """性能指标配置"""

    enabled: bool = True
    report_interval: int = 60  # 报告间隔（秒）
    latency_buckets: List[float] = field(
        default_factory=lambda: [10, 50, 100, 200, 500, 1000]
    )  # 延迟桶（毫秒）
    sample_rate: float = 1.0  # 采样率（0.0-1.0）
    
    # 告警阈值配置
    latency_warning_threshold_ms: float = 100.0  # 延迟告警阈值（毫秒）
    cpu_warning_threshold: float = 80.0  # CPU 使用率告警阈值（百分比）
    memory_warning_threshold: float = 80.0  # 内存使用率告警阈值（百分比）


@dataclass
class InstrumentsConfig:
    """合约管理配置"""
    cache_path: str = "./data/instruments.json"
    auto_update: bool = True
    update_interval: int = 86400  # 每天更新一次


@dataclass
class KLineConfig:
    """K线配置"""
    enabled: bool = True
    periods: List[str] = field(
        default_factory=lambda: ["1m", "3m", "5m", "10m", "15m", "30m", "60m", "1d"]
    )


@dataclass
class CSVConfig:
    """CSV存储配置"""
    base_path: str = "./data/ticks"
    flush_interval: float = 1.0
    batch_size: int = 100


@dataclass
class StorageConfig:
    """存储配置"""
    enabled: bool = False
    type: str = "csv"
    csv: CSVConfig = field(default_factory=CSVConfig)
    instruments: InstrumentsConfig = field(default_factory=InstrumentsConfig)
    kline: KLineConfig = field(default_factory=KLineConfig)


class GlobalConfig(object):
    TdFrontAddress: str
    MdFrontAddress: str
    BrokerID: str
    AuthCode: str
    UserProductInfo: str
    AppID: str
    Host: str
    Port: int
    LogLevel: str
    ConFilePath: str
    Token: str
    HeartbeatInterval: float
    HeartbeatTimeout: float

    # 配置对象
    Metrics: MetricsConfig
    Storage: StorageConfig

    @classmethod
    def load_config(cls, config_file_path: str):
        """
        加载并解析 YAML 配置文件，设置类属性
        """
        with open(config_file_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
            cls.TdFrontAddress = os.environ.get(
                "WEBCTP_TD_ADDRESS", config.get("TdFrontAddress", "")
            )
            cls.MdFrontAddress = os.environ.get(
                "WEBCTP_MD_ADDRESS", config.get("MdFrontAddress", "")
            )
            cls.BrokerID = os.environ.get(
                "WEBCTP_BROKER_ID", config.get("BrokerID", "")
            )
            cls.AuthCode = os.environ.get(
                "WEBCTP_AUTH_CODE", config.get("AuthCode", "")
            )
            cls.AppID = os.environ.get("WEBCTP_APP_ID", config.get("AppID", ""))
            cls.UserProductInfo = os.environ.get("WEBCTP_USER_PRODUCT_INFO", config.get("UserProductInfo", ""))
            cls.Host = os.environ.get("WEBCTP_HOST", config.get("Host", "0.0.0.0"))

            cls.Port = config.get("Port", 8080)
            cls.LogLevel = config.get("LogLevel", "INFO")
            cls.ConFilePath = config.get("ConFilePath", "./con_file/")
            cls.Token = os.environ.get("WEBCTP_TOKEN", config.get("Token", ""))
            
            # Heartbeat configuration
            cls.HeartbeatInterval = float(
                os.environ.get(
                    "WEBCTP_HEARTBEAT_INTERVAL", config.get("HeartbeatInterval", 30.0)
                )
            )
            cls.HeartbeatTimeout = float(
                os.environ.get(
                    "WEBCTP_HEARTBEAT_TIMEOUT", config.get("HeartbeatTimeout", 60.0)
                )
            )

            # 加载性能监控配置
            metrics_config = config.get("Metrics", {})
            cls.Metrics = MetricsConfig(
                enabled=bool(
                    os.environ.get(
                        "WEBCTP_METRICS_ENABLED", metrics_config.get("Enabled", True)
                    )
                ),
                report_interval=int(
                    os.environ.get(
                        "WEBCTP_METRICS_INTERVAL",
                        metrics_config.get("ReportInterval", 60),
                    )
                ),
                sample_rate=float(metrics_config.get("SampleRate", 1.0)),
                latency_warning_threshold_ms=float(
                    os.environ.get(
                        "WEBCTP_METRICS_LATENCY_WARNING_THRESHOLD",
                        metrics_config.get("LatencyWarningThresholdMs", 100.0),
                    )
                ),
                cpu_warning_threshold=float(
                    os.environ.get(
                        "WEBCTP_METRICS_CPU_WARNING_THRESHOLD",
                        metrics_config.get("CpuWarningThreshold", 80.0),
                    )
                ),
                memory_warning_threshold=float(
                    os.environ.get(
                        "WEBCTP_METRICS_MEMORY_WARNING_THRESHOLD",
                        metrics_config.get("MemoryWarningThreshold", 80.0),
                    )
                ),
            )

            # 加载存储配置
            storage_config = config.get("Storage", {})
            csv_config = storage_config.get("CSV", {})
            instruments_config = storage_config.get("Instruments", {})
            kline_config = storage_config.get("KLine", {})
            
            cls.Storage = StorageConfig(
                enabled=bool(storage_config.get("Enabled", False)),
                type=storage_config.get("Type", "csv"),
                csv=CSVConfig(
                    base_path=csv_config.get("BasePath", "./data/ticks"),
                    flush_interval=float(csv_config.get("FlushInterval", 1.0)),
                    batch_size=int(csv_config.get("BatchSize", 100)),
                ),
                instruments=InstrumentsConfig(
                    cache_path=instruments_config.get("CachePath", "./data/instruments.json"),
                    auto_update=bool(instruments_config.get("AutoUpdate", True)),
                    update_interval=int(instruments_config.get("UpdateInterval", 86400)),
                ),
                kline=KLineConfig(
                    enabled=bool(kline_config.get("Enabled", True)),
                    periods=kline_config.get("Periods", ["1m", "3m", "5m", "10m", "15m", "30m", "60m", "1d"]),
                ),
            )

        if not cls.ConFilePath.endswith("/"):
            cls.ConFilePath = cls.ConFilePath + "/"

        if not os.path.exists(cls.ConFilePath):
            os.makedirs(cls.ConFilePath)

    @classmethod
    def get_con_file_path(cls, name: str) -> str:
        """
        获取连接文件的完整路径
        """
        path = os.path.join(cls.ConFilePath, name)
        return path


if __name__ == "__main__":
    config_path = Path(__file__).parent.parent.parent / "config" / "config.sample.yaml"
    GlobalConfig.load_config(str(config_path))
    print(f"TdFrontAddress: {GlobalConfig.TdFrontAddress}")
    print(f"MdFrontAddress: {GlobalConfig.MdFrontAddress}")
    print(f"BrokerID: {GlobalConfig.BrokerID}")
    print(f"Storage: {GlobalConfig.Storage}")

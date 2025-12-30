#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: webctp
@FileName   : logger.py
@Date       : 2025/12/3 13:55
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 基于 loguru 的日志工具类，支持标签分类和 trace_id 追踪
"""

import contextvars
import sys
import uuid
from pathlib import Path
from typing import Any, Optional

import yaml
from loguru import logger as _logger

# 创建 trace_id 上下文变量，用于追踪请求
_trace_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'trace_id', default=None
)

# 创建默认 tag 上下文变量，用于设置日志上下文
_default_tag_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'default_tag', default=None
)

# 默认配置
DEFAULT_CONFIG = {
    'log_dir': 'logs',
    'console': {
        'enabled': True,
        'level': 'DEBUG',
        'colorize': True,
        'format': '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>'
    },
    'main_log': {
        'enabled': True,
        'filename': 'webctp.log',
        'level': 'DEBUG',
        'rotation': '500 MB',
        'retention': '7 days',
        'compression': 'zip',
        'format': '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}'
    },
    'error_log': {
        'enabled': True,
        'filename': 'webctp_error.log',
        'level': 'ERROR',
        'rotation': '500 MB',
        'retention': '30 days',
        'compression': 'zip',
        'format': '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}'
    },
    'common': {
        'backtrace': True,
        'diagnose': True
    }
}


def _load_config() -> dict[str, Any]:
    """
    加载日志配置文件
    
    按以下顺序查找配置文件：
    1. config/logger.yaml
    2. 使用默认配置
    
    Returns:
        配置字典
    """
    config_paths = [
        Path('config/logger.yaml'),
        Path(__file__).parent.parent.parent.parent / 'config' / 'logger.yaml',
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if config:
                        # 合并默认配置和文件配置
                        return _merge_config(DEFAULT_CONFIG, config)
            except Exception:
                pass
    
    return DEFAULT_CONFIG


def _merge_config(default: dict, override: dict) -> dict:
    """
    递归合并配置字典
    
    Args:
        default: 默认配置
        override: 覆盖配置
        
    Returns:
        合并后的配置
    """
    result = default.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result


class Logger:
    """
    日志工具类，基于 loguru 库实现。
    
    特性：
    - 支持标签分类日志
    - 支持 trace_id 追踪
    - 支持控制台和文件输出
    - 支持自定义日志格式
    - 支持从 YAML 配置文件加载配置
    - 线程安全和异步安全
    
    使用示例：
        # 基础使用
        logger = Logger()
        logger.info("这是一条信息", tag="auth")
        logger.error("这是一条错误", tag="database")
        
        # 使用 trace_id
        logger.set_trace_id("req-123456")
        logger.info("处理请求", tag="request")
        logger.clear_trace_id()
    """
    
    _instance = None
    _initialized = False
    _config: dict[str, Any] = {}
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志工具"""
        if Logger._initialized:
            return
        
        # 加载配置
        Logger._config = _load_config()
        
        # 移除默认的处理器
        _logger.remove()
        
        # 获取通用配置
        common = Logger._config.get('common', {})
        backtrace = common.get('backtrace', True)
        diagnose = common.get('diagnose', True)
        
        # 添加控制台处理器
        console_config = Logger._config.get('console', {})
        if console_config.get('enabled', True):
            _logger.add(
                sys.stdout,
                format=console_config.get('format', DEFAULT_CONFIG['console']['format']),
                level=console_config.get('level', 'DEBUG'),
                colorize=console_config.get('colorize', True),
                backtrace=backtrace,
                diagnose=diagnose,
            )
        
        # 创建日志目录
        log_dir = Path(Logger._config.get('log_dir', 'logs'))
        log_dir.mkdir(exist_ok=True)
        
        # 添加主日志文件处理器
        main_log_config = Logger._config.get('main_log', {})
        if main_log_config.get('enabled', True):
            _logger.add(
                log_dir / main_log_config.get('filename', 'webctp.log'),
                format=main_log_config.get('format', DEFAULT_CONFIG['main_log']['format']),
                level=main_log_config.get('level', 'DEBUG'),
                rotation=main_log_config.get('rotation', '500 MB'),
                retention=main_log_config.get('retention', '7 days'),
                compression=main_log_config.get('compression', 'zip'),
                backtrace=backtrace,
                diagnose=diagnose,
            )
        
        # 添加错误日志文件处理器
        error_log_config = Logger._config.get('error_log', {})
        if error_log_config.get('enabled', True):
            _logger.add(
                log_dir / error_log_config.get('filename', 'webctp_error.log'),
                format=error_log_config.get('format', DEFAULT_CONFIG['error_log']['format']),
                level=error_log_config.get('level', 'ERROR'),
                rotation=error_log_config.get('rotation', '500 MB'),
                retention=error_log_config.get('retention', '30 days'),
                compression=error_log_config.get('compression', 'zip'),
                backtrace=backtrace,
                diagnose=diagnose,
            )
        
        Logger._initialized = True
    
    @staticmethod
    def get_config() -> dict[str, Any]:
        """获取当前日志配置"""
        return Logger._config.copy()
    
    @staticmethod
    def _get_trace_id() -> Optional[str]:
        """获取当前的 trace_id"""
        return _trace_id_context.get()
    
    @staticmethod
    def _generate_trace_id() -> str:
        """
        生成唯一的 trace_id
        
        Returns:
            生成的 trace_id（UUID 格式）
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def set_trace_id(trace_id: Optional[str] = None) -> str:
        """
        设置 trace_id，用于追踪请求
        
        如果不指定 trace_id，将自动生成一个 UUID
        
        Args:
            trace_id: 追踪 ID，如果为 None 则自动生成
            
        Returns:
            设置的 trace_id
        """
        if trace_id is None:
            trace_id = Logger._generate_trace_id()
        _trace_id_context.set(trace_id)
        return trace_id
    
    @staticmethod
    def clear_trace_id() -> None:
        """清除 trace_id"""
        _trace_id_context.set(None)
    
    @staticmethod
    def get_trace_id() -> Optional[str]:
        """获取当前的 trace_id"""
        return Logger._get_trace_id()
    
    @staticmethod
    def set_default_tag(tag: Optional[str] = None) -> None:
        """
        设置默认 tag，用于类级别的日志标签
        
        Args:
            tag: 默认标签，如果为 None 则清除默认标签
        """
        _default_tag_context.set(tag)
    
    @staticmethod
    def clear_default_tag() -> None:
        """清除默认 tag"""
        _default_tag_context.set(None)
    
    @staticmethod
    def get_default_tag() -> Optional[str]:
        """获取当前的默认 tag"""
        return _default_tag_context.get()
    
    def _log_with_trace(self, message: str, tag: Optional[str], trace_id, log_func, **kwargs) -> None:
        """
        使用 trace_id 记录日志的辅助方法
        
        Args:
            message: 日志消息
            tag: 日志标签
            trace_id: 追踪 ID（True/str/None）
            log_func: 日志函数（_logger.debug/info/error 等）
            **kwargs: 其他参数
        """
        # 处理 trace_id 参数
        if trace_id is True:
            # 自动生成 UUID
            trace_id = self._generate_trace_id()
        
        # 如果指定了 trace_id，临时设置
        if trace_id:
            previous_trace_id = self._get_trace_id()
            self.set_trace_id(trace_id)
            try:
                formatted_message = self._format_message(message, tag)
                _logger.opt(depth=2).log(log_func.__name__.upper(), formatted_message, **kwargs)
            finally:
                if previous_trace_id:
                    self.set_trace_id(previous_trace_id)
                else:
                    self.clear_trace_id()
        else:
            formatted_message = self._format_message(message, tag)
            _logger.opt(depth=2).log(log_func.__name__.upper(), formatted_message, **kwargs)
    
    def _format_message(self, message: str, tag: Optional[str] = None) -> str:
        """
        格式化日志消息，添加 trace_id 和标签
        
        Args:
            message: 原始消息
            tag: 日志标签（可选）
            
        Returns:
            格式化后的消息
        """
        parts = []
        
        # 添加 trace_id
        trace_id = self._get_trace_id()
        if trace_id:
            parts.append(f"[trace_id={trace_id}]")
        
        # 添加标签（优先使用传入的tag，否则使用默认tag）
        final_tag = tag if tag is not None else _default_tag_context.get()
        if final_tag:
            parts.append(f"[{final_tag}]")
        
        # 添加消息
        parts.append(message)
        
        return " ".join(parts)
    
    def debug(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 DEBUG 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.debug, **kwargs)
    
    def info(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 INFO 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.info, **kwargs)
    
    def success(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 SUCCESS 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.success, **kwargs)
    
    def warning(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 WARNING 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.warning, **kwargs)
    
    def error(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 ERROR 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.error, **kwargs)
    
    def critical(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 CRITICAL 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.critical, **kwargs)
    
    def exception(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录异常日志（包含堆栈跟踪）
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.exception, **kwargs)


# 创建全局日志实例
logger = Logger()

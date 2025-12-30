#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
定时任务调度器

支持配置多个定时任务，在指定时间执行命令或脚本
"""
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


def cron_to_chinese(cron_expr: str) -> str:
    """
    将cron表达式转换为易读的中文描述
    
    Args:
        cron_expr: cron表达式，格式：分 时 日 月 周
        
    Returns:
        中文描述字符串
    """
    parts = cron_expr.split()
    if len(parts) != 5:
        return cron_expr
    
    minute, hour, day, month, weekday = parts
    
    # 解析周几
    weekday_map = {
        '0': '周日', '1': '周一', '2': '周二', '3': '周三',
        '4': '周四', '5': '周五', '6': '周六', '7': '周日',
        'sun': '周日', 'mon': '周一', 'tue': '周二', 'wed': '周三',
        'thu': '周四', 'fri': '周五', 'sat': '周六'
    }
    
    result_parts = []
    
    # 解析周
    if weekday == '*':
        result_parts.append("每天")
    elif '-' in weekday:
        start, end = weekday.split('-')
        start_cn = weekday_map.get(start.lower(), start)
        end_cn = weekday_map.get(end.lower(), end)
        result_parts.append(f"{start_cn}至{end_cn}")
    elif ',' in weekday:
        days = [weekday_map.get(d.lower(), d) for d in weekday.split(',')]
        result_parts.append('、'.join(days))
    else:
        result_parts.append(weekday_map.get(weekday.lower(), f"周{weekday}"))
    
    # 解析时间
    if minute == '*' and hour == '*':
        result_parts.append("每分钟")
    elif minute.startswith('*/'):
        interval = minute[2:]
        result_parts.append(f"每{interval}分钟")
    elif hour == '*':
        result_parts.append(f"每小时的第{minute}分")
    else:
        result_parts.append(f"{hour.zfill(2)}:{minute.zfill(2)}")
    
    return ' '.join(result_parts)


def run_command(command: str, name: str = "task"):
    """
    执行命令
    
    Args:
        command: 要执行的命令
        name: 任务名称（用于日志）
    """
    logger.info(f"[{name}] 开始执行: {command}")
    start_time = datetime.now()
    
    try:
        # 在项目根目录执行命令
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            logger.info(f"[{name}] 执行成功，耗时 {elapsed:.1f}秒")
            if result.stdout:
                logger.debug(f"[{name}] 输出: {result.stdout[:500]}")
        else:
            logger.error(f"[{name}] 执行失败，返回码: {result.returncode}")
            if result.stderr:
                logger.error(f"[{name}] 错误: {result.stderr[:500]}")
                
    except subprocess.TimeoutExpired:
        logger.error(f"[{name}] 执行超时")
    except Exception as e:
        logger.error(f"[{name}] 执行异常: {e}")


def start_service(config_file: str, app_type: str, name: str = "service"):
    """
    启动服务（在新终端窗口中运行）
    
    Args:
        config_file: 配置文件路径
        app_type: 应用类型 (td/md)
        name: 任务名称
    """
    command = f"python main.py --config={config_file} --app_type={app_type}"
    logger.info(f"[{name}] 启动服务: {command}")
    
    try:
        if sys.platform == 'win32':
            # Windows: 在新的CMD窗口中启动，窗口标题为任务名称
            process = subprocess.Popen(
                f'start "{name}" cmd /k {command}',
                shell=True,
                cwd=str(PROJECT_ROOT)
            )
        else:
            # Linux/Mac: 后台运行
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        logger.info(f"[{name}] 服务已启动")
        return process
    except Exception as e:
        logger.error(f"[{name}] 启动服务失败: {e}")
        return None


def load_schedule_config(config_path: str = None) -> dict:
    """
    加载调度配置
    
    Args:
        config_path: 配置文件路径，默认为 config/scheduler.yaml
    """
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "scheduler.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        return get_default_config()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"加载配置文件: {config_path}")
        return config
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return get_default_config()


def get_default_config() -> dict:
    """获取默认配置"""
    return {
        "tasks": [
            {
                "name": "启动交易服务",
                "type": "service",
                "config_file": "./config/config_td.yaml",
                "app_type": "td",
                "cron": "30 8 * * 1-5",  # 周一到周五 08:30
                "enabled": True
            },
            {
                "name": "启动行情服务",
                "type": "service", 
                "config_file": "./config/config_md.yaml",
                "app_type": "md",
                "cron": "30 8 * * 1-5",  # 周一到周五 08:30
                "enabled": True
            }
        ]
    }


def setup_scheduler(config: dict) -> BackgroundScheduler:
    """
    设置调度器
    
    Args:
        config: 调度配置
    """
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    
    tasks = config.get("tasks", [])
    
    for task in tasks:
        if not task.get("enabled", True):
            logger.info(f"任务已禁用: {task.get('name')}")
            continue
        
        name = task.get("name", "unnamed")
        cron_expr = task.get("cron", "")
        task_type = task.get("type", "command")
        
        if not cron_expr:
            logger.warning(f"任务 [{name}] 缺少 cron 表达式，跳过")
            continue
        
        try:
            # 解析 cron 表达式
            cron_parts = cron_expr.split()
            if len(cron_parts) == 5:
                trigger = CronTrigger(
                    minute=cron_parts[0],
                    hour=cron_parts[1],
                    day=cron_parts[2],
                    month=cron_parts[3],
                    day_of_week=cron_parts[4],
                    timezone="Asia/Shanghai"
                )
            else:
                logger.error(f"任务 [{name}] cron 表达式格式错误: {cron_expr}")
                continue
            
            # 根据任务类型添加任务
            if task_type == "service":
                scheduler.add_job(
                    start_service,
                    trigger=trigger,
                    args=[task.get("config_file"), task.get("app_type"), name],
                    id=name,
                    name=name
                )
            elif task_type == "command":
                command = task.get("command", "")
                if command:
                    scheduler.add_job(
                        run_command,
                        trigger=trigger,
                        args=[command, name],
                        id=name,
                        name=name
                    )
            
            logger.info(f"已添加任务: [{name}] {cron_to_chinese(cron_expr)} (cron={cron_expr})")
            
        except Exception as e:
            logger.error(f"添加任务 [{name}] 失败: {e}")
    
    return scheduler


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="定时任务调度器")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--list", action="store_true", help="列出所有任务")
    parser.add_argument("--run", type=str, help="立即执行指定任务")
    args = parser.parse_args()
    
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )
    logger.add(
        PROJECT_ROOT / "logs" / "scheduler.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG"
    )
    
    logger.info("=" * 60)
    logger.info("定时任务调度器")
    logger.info("=" * 60)
    
    # 加载配置
    config = load_schedule_config(args.config)
    
    # 列出任务
    if args.list:
        logger.info("\n已配置的任务:")
        for task in config.get("tasks", []):
            status = "启用" if task.get("enabled", True) else "禁用"
            cron_expr = task.get('cron', '')
            cron_desc = cron_to_chinese(cron_expr) if cron_expr else "未配置"
            logger.info(f"  - {task.get('name')}: {cron_desc} (cron={cron_expr}) [{status}]")
        return
    
    # 立即执行指定任务
    if args.run:
        for task in config.get("tasks", []):
            if task.get("name") == args.run:
                logger.info(f"立即执行任务: {args.run}")
                if task.get("type") == "service":
                    start_service(task.get("config_file"), task.get("app_type"), task.get("name"))
                elif task.get("type") == "command":
                    run_command(task.get("command"), task.get("name"))
                return
        logger.error(f"未找到任务: {args.run}")
        return
    
    # 设置调度器
    scheduler = setup_scheduler(config)
    
    # 显示已添加的任务
    logger.info("\n任务调度:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name}: 已就绪")
    
    logger.info("\n调度器已启动，按 Ctrl+C 停止...")
    
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n正在关闭调度器...")
        scheduler.shutdown(wait=False)
        logger.info("调度器已停止")


if __name__ == "__main__":
    main()

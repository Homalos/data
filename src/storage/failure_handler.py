#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
失败数据处理器 - 用于持久化和重试写入失败的数据
"""
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger


class FailureHandler:
    """
    失败数据处理器
    
    负责将写入失败的数据持久化到本地文件，并支持后续重试
    """
    
    def __init__(self, failure_dir: str = "data/failures"):
        """
        初始化失败数据处理器
        
        Args:
            failure_dir: 失败数据保存目录
        """
        self.failure_dir = Path(failure_dir)
        self.failure_dir.mkdir(parents=True, exist_ok=True)
        self._save_count = 0
        self._retry_success_count = 0
        self._retry_fail_count = 0
        
        logger.info(f"失败数据处理器初始化完成，保存目录: {self.failure_dir}")
    
    async def save_failed_batch(self, batch: List[Dict], data_type: str) -> bool:
        """
        保存失败的批次到本地文件
        
        Args:
            batch: 失败的数据批次
            data_type: 数据类型（tick/kline）
            
        Returns:
            是否保存成功
        """
        if not batch:
            return True
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = self.failure_dir / f"{data_type}_{timestamp}.json"
            
            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(batch, f, ensure_ascii=False, indent=2)
            
            self._save_count += 1
            logger.warning(f"⚠️ 已保存 {len(batch)} 条失败数据到: {filename.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存失败数据出错: {e}", exc_info=True)
            return False
    
    async def retry_failed_batches(self, influxdb_client, data_type: Optional[str] = None) -> Dict:
        """
        重试失败的批次
        
        Args:
            influxdb_client: InfluxDB客户端
            data_type: 数据类型过滤（tick/kline），None表示重试所有
            
        Returns:
            重试统计信息
        """
        pattern = f"{data_type}_*.json" if data_type else "*.json"
        failure_files = list(self.failure_dir.glob(pattern))
        
        if not failure_files:
            logger.info("没有需要重试的失败数据")
            return {
                "total": 0,
                "success": 0,
                "failed": 0
            }
        
        logger.info(f"发现 {len(failure_files)} 个失败数据文件，开始重试...")
        
        success_count = 0
        fail_count = 0
        
        for file in failure_files:
            try:
                # 读取失败数据
                with open(file, 'r', encoding='utf-8') as f:
                    batch = json.load(f)
                
                # 重试写入
                await influxdb_client.write_points(batch)
                
                # 删除成功重试的文件
                file.unlink()
                success_count += 1
                self._retry_success_count += 1
                
                logger.info(f"✅ 成功重试失败数据: {file.name} ({len(batch)}条)")
                
            except Exception as e:
                fail_count += 1
                self._retry_fail_count += 1
                logger.error(f"❌ 重试失败数据出错: {file.name}, {e}")
        
        result = {
            "total": len(failure_files),
            "success": success_count,
            "failed": fail_count
        }
        
        logger.info(
            f"重试完成 - 总计: {result['total']}, "
            f"成功: {result['success']}, 失败: {result['failed']}"
        )
        
        return result
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        # 统计当前失败文件数量
        tick_files = list(self.failure_dir.glob("tick_*.json"))
        kline_files = list(self.failure_dir.glob("kline_*.json"))
        
        return {
            "save_count": self._save_count,
            "retry_success_count": self._retry_success_count,
            "retry_fail_count": self._retry_fail_count,
            "pending_tick_files": len(tick_files),
            "pending_kline_files": len(kline_files),
            "total_pending_files": len(tick_files) + len(kline_files),
        }
    
    def clear_old_failures(self, days: int = 7):
        """
        清理旧的失败数据文件
        
        Args:
            days: 保留天数，超过此天数的文件将被删除
        """
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days)
            
            deleted_count = 0
            for file in self.failure_dir.glob("*.json"):
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                if file_time < cutoff_time:
                    file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 个超过 {days} 天的失败数据文件")
                
        except Exception as e:
            logger.error(f"清理旧失败数据文件出错: {e}")

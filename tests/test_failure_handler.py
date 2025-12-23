#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试失败数据处理器
"""
import pytest
import asyncio
import json
from pathlib import Path
from src.storage.failure_handler import FailureHandler


class MockInfluxDBClient:
    """模拟InfluxDB客户端"""
    
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.written_points = []
    
    async def write_points(self, points):
        """模拟写入"""
        if self.should_fail:
            raise Exception("Mock write failure")
        self.written_points.extend(points)


class TestFailureHandler:
    """测试失败数据处理器"""
    
    @pytest.fixture
    def test_dir(self, tmp_path):
        """创建临时测试目录"""
        return str(tmp_path / "test_failures")
    
    def test_init(self, test_dir):
        """测试初始化"""
        handler = FailureHandler(failure_dir=test_dir)
        
        assert handler.failure_dir == Path(test_dir)
        assert handler.failure_dir.exists()
        assert handler._save_count == 0
        assert handler._retry_success_count == 0
        assert handler._retry_fail_count == 0
    
    @pytest.mark.asyncio
    async def test_save_failed_batch(self, test_dir):
        """测试保存失败批次"""
        handler = FailureHandler(failure_dir=test_dir)
        
        # 测试数据
        batch = [
            {"measurement": "tick_rb2505", "fields": {"price": 3500.0}},
            {"measurement": "tick_rb2505", "fields": {"price": 3510.0}},
        ]
        
        # 保存失败数据
        success = await handler.save_failed_batch(batch, "tick")
        
        assert success
        assert handler._save_count == 1
        
        # 检查文件是否创建
        files = list(Path(test_dir).glob("tick_*.json"))
        assert len(files) == 1
        
        # 检查文件内容
        with open(files[0], 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 2
        assert saved_data[0]["fields"]["price"] == 3500.0
    
    @pytest.mark.asyncio
    async def test_retry_failed_batches_success(self, test_dir):
        """测试重试成功"""
        handler = FailureHandler(failure_dir=test_dir)
        
        # 先保存一些失败数据
        batch1 = [{"measurement": "tick_rb2505", "fields": {"price": 3500.0}}]
        batch2 = [{"measurement": "kline_1m_rb2505", "fields": {"open": 3500.0}}]
        
        await handler.save_failed_batch(batch1, "tick")
        await handler.save_failed_batch(batch2, "kline")
        
        # 创建模拟客户端（成功）
        mock_client = MockInfluxDBClient(should_fail=False)
        
        # 重试所有失败数据
        result = await handler.retry_failed_batches(mock_client)
        
        assert result["total"] == 2
        assert result["success"] == 2
        assert result["failed"] == 0
        assert handler._retry_success_count == 2
        
        # 检查文件是否被删除
        files = list(Path(test_dir).glob("*.json"))
        assert len(files) == 0
        
        # 检查数据是否写入
        assert len(mock_client.written_points) == 2
    
    @pytest.mark.asyncio
    async def test_retry_failed_batches_failure(self, test_dir):
        """测试重试失败"""
        handler = FailureHandler(failure_dir=test_dir)
        
        # 保存失败数据
        batch = [{"measurement": "tick_rb2505", "fields": {"price": 3500.0}}]
        await handler.save_failed_batch(batch, "tick")
        
        # 创建模拟客户端（失败）
        mock_client = MockInfluxDBClient(should_fail=True)
        
        # 重试失败数据
        result = await handler.retry_failed_batches(mock_client)
        
        assert result["total"] == 1
        assert result["success"] == 0
        assert result["failed"] == 1
        assert handler._retry_fail_count == 1
        
        # 检查文件是否仍然存在
        files = list(Path(test_dir).glob("*.json"))
        assert len(files) == 1
    
    @pytest.mark.asyncio
    async def test_retry_by_data_type(self, test_dir):
        """测试按数据类型重试"""
        handler = FailureHandler(failure_dir=test_dir)
        
        # 保存不同类型的失败数据
        tick_batch = [{"measurement": "tick_rb2505"}]
        kline_batch = [{"measurement": "kline_1m_rb2505"}]
        
        await handler.save_failed_batch(tick_batch, "tick")
        await handler.save_failed_batch(kline_batch, "kline")
        
        # 创建模拟客户端
        mock_client = MockInfluxDBClient(should_fail=False)
        
        # 只重试tick数据
        result = await handler.retry_failed_batches(mock_client, "tick")
        
        assert result["total"] == 1
        assert result["success"] == 1
        
        # 检查只有tick文件被删除
        tick_files = list(Path(test_dir).glob("tick_*.json"))
        kline_files = list(Path(test_dir).glob("kline_*.json"))
        
        assert len(tick_files) == 0
        assert len(kline_files) == 1
    
    def test_get_stats(self, test_dir):
        """测试统计信息"""
        handler = FailureHandler(failure_dir=test_dir)
        
        stats = handler.get_stats()
        
        assert "save_count" in stats
        assert "retry_success_count" in stats
        assert "retry_fail_count" in stats
        assert "pending_tick_files" in stats
        assert "pending_kline_files" in stats
        assert "total_pending_files" in stats
        
        assert stats["save_count"] == 0
        assert stats["total_pending_files"] == 0
    
    @pytest.mark.asyncio
    async def test_save_empty_batch(self, test_dir):
        """测试保存空批次"""
        handler = FailureHandler(failure_dir=test_dir)
        
        # 保存空批次
        success = await handler.save_failed_batch([], "tick")
        
        assert success
        assert handler._save_count == 0  # 不应该增加计数
        
        # 不应该创建文件
        files = list(Path(test_dir).glob("*.json"))
        assert len(files) == 0
    
    def test_clear_old_failures(self, test_dir):
        """测试清理旧文件"""
        handler = FailureHandler(failure_dir=test_dir)
        
        # 创建一些测试文件
        test_file = Path(test_dir) / "tick_old.json"
        test_file.write_text("[]")
        
        # 修改文件时间（模拟旧文件）
        import time
        old_time = time.time() - (8 * 24 * 3600)  # 8天前
        import os
        os.utime(test_file, (old_time, old_time))
        
        # 清理超过7天的文件
        handler.clear_old_failures(days=7)
        
        # 检查文件是否被删除
        assert not test_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

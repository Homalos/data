#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
InfluxDB 3.x 客户端封装
"""
from typing import List, Dict, Optional
from influxdb_client_3 import InfluxDBClient3, Point
from loguru import logger
from datetime import datetime


class InfluxDBClientWrapper:
    """InfluxDB 3.x 客户端封装"""
    
    def __init__(self, host: str, token: str, database: str):
        """
        初始化InfluxDB客户端
        
        Args:
            host: InfluxDB地址（如 http://localhost:8181）
            token: 访问Token
            database: 数据库名称
        """
        self.host = host
        self.token = token
        self.database = database
        self._client: Optional[InfluxDBClient3] = None
    
    async def connect(self):
        """连接InfluxDB"""
        try:
            self._client = InfluxDBClient3(
                host=self.host,
                token=self.token,
                database=self.database
            )
            logger.info(f"InfluxDB 3.x 连接成功: {self.host}, 数据库: {self.database}")
        except Exception as e:
            logger.error(f"InfluxDB 3.x 连接失败: {e}", exc_info=True)
            raise
    
    async def write_points(self, points: List[Dict]):
        """
        批量写入数据点
        
        Args:
            points: 数据点列表，每个点包含 measurement, tags, fields, time
        """
        if not self._client:
            raise RuntimeError("InfluxDB客户端未连接")
        
        try:
            # InfluxDB 3.x 使用字典格式写入
            self._client.write(record=points)
            logger.debug(f"成功写入 {len(points)} 条数据到InfluxDB")
        except Exception as e:
            logger.error(f"InfluxDB写入失败: {e}", exc_info=True)
            raise
    
    async def query(self, sql: str) -> List[Dict]:
        """
        执行SQL查询（InfluxDB 3.x 使用SQL而非Flux）
        
        Args:
            sql: SQL查询语句
            
        Returns:
            查询结果列表
        """
        if not self._client:
            raise RuntimeError("InfluxDB客户端未连接")
        
        try:
            # InfluxDB 3.x 使用SQL查询
            table = self._client.query(query=sql)
            
            # 转换为字典列表
            results = []
            if table is not None:
                results = table.to_pydict()
                # 转换为行格式
                if results:
                    num_rows = len(next(iter(results.values())))
                    rows = []
                    for i in range(num_rows):
                        row = {key: values[i] for key, values in results.items()}
                        rows.append(row)
                    return rows
            
            return []
            
        except Exception as e:
            logger.error(f"InfluxDB查询失败: {e}", exc_info=True)
            raise
    
    def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            logger.info("InfluxDB连接已关闭")

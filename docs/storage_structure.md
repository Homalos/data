# 行情存储结构设计

## 概述

本系统采用**按合约分表**的存储策略，将每个合约的tick数据和K线数据分别存储在独立的表中，优化回测性能。

## 存储结构

### Tick数据表

**命名规则**: `tick_{instrument_id}`

**示例**:
- `tick_rb2605` - 螺纹钢2605合约
- `tick_au2602` - 黄金2602合约
- `tick_ag2602` - 白银2602合约

**字段**:
- `time` (timestamp): 时间戳
- `last_price` (double): 最新价
- `volume` (int64): 成交量
- `turnover` (double): 成交额
- `open_interest` (double): 持仓量
- `bid_price1` (double): 买一价
- `bid_volume1` (int64): 买一量
- `ask_price1` (double): 卖一价
- `ask_volume1` (int64): 卖一量
- `open_price` (double): 开盘价
- `high_price` (double): 最高价
- `low_price` (double): 最低价
- `close_price` (double): 收盘价

**标签 (Tags)**:
- `exchange_id`: 交易所代码
- `trading_day`: 交易日

### K线数据表

**命名规则**: `kline_{period}_{instrument_id}`

**示例**:
- `kline_1m_rb2605` - 螺纹钢2605合约1分钟K线
- `kline_5m_au2602` - 黄金2602合约5分钟K线
- `kline_1d_ag2602` - 白银2602合约日K线

**支持周期**:
- `1m` - 1分钟
- `3m` - 3分钟
- `5m` - 5分钟
- `10m` - 10分钟
- `15m` - 15分钟
- `30m` - 30分钟
- `60m` - 60分钟
- `1d` - 日线

**字段**:
- `time` (timestamp): K线开始时间
- `open` (double): 开盘价
- `high` (double): 最高价
- `low` (double): 最低价
- `close` (double): 收盘价
- `volume` (int64): 成交量
- `turnover` (double): 成交额
- `open_interest` (double): 持仓量
- `tick_count` (int64): tick数量

**标签 (Tags)**:
- `trading_day`: 交易日
- `period`: 周期

## 查询示例

### 查询单个合约的Tick数据

```sql
SELECT time, last_price, volume, open_interest
FROM tick_rb2605
WHERE time >= '2025-12-23 09:00:00'
  AND time <= '2025-12-23 15:00:00'
ORDER BY time ASC
```

### 查询单个合约的K线数据

```sql
SELECT time, open, high, low, close, volume
FROM kline_1m_rb2605
WHERE time >= '2025-12-23 09:00:00'
  AND time <= '2025-12-23 15:00:00'
ORDER BY time ASC
```

### 查询所有合约的表

```sql
SHOW TABLES
```

### 统计单个合约的数据量

```sql
SELECT COUNT(*) as count FROM tick_rb2605
```

## 优势

### 1. 回测性能优化
- 查询单个合约时不需要扫描其他合约的数据
- 减少数据过滤开销
- 提高查询速度

### 2. 数据管理
- 可以独立管理每个合约的数据
- 方便清理过期合约数据
- 便于数据备份和恢复

### 3. 索引优化
- 可以针对单个合约优化索引
- 减少索引大小
- 提高写入性能

### 4. 扩展性
- 支持大量合约并发写入
- 避免单表过大问题
- 便于分布式部署

## 注意事项

### 1. 表数量
- 每个合约会创建1个tick表和N个K线表（N为启用的周期数）
- 例如：100个合约 × (1 + 8) = 900个表
- InfluxDB 3.x可以很好地处理大量表

### 2. 合约命名
- 合约代码必须符合InfluxDB表名规则
- 建议使用小写字母和数字
- 避免特殊字符

### 3. 数据清理
- 定期清理过期合约的表
- 可以使用脚本批量删除
- 建议保留最近3个月的数据

## 迁移指南

### 从旧结构迁移

如果之前使用的是单表结构（`market_tick`, `kline_1m`等），可以：

1. **保留旧数据**：旧表不影响新表的使用
2. **重新采集**：从当前时间开始使用新结构
3. **数据迁移**：编写脚本将旧表数据迁移到新表（可选）

### 验证新结构

运行验证脚本：
```bash
python scripts/verify_data.py
```

## 相关脚本

- `scripts/test_new_storage_structure.py` - 测试新存储结构
- `scripts/verify_data.py` - 验证数据存储
- `scripts/reset_influxdb.py` - 重置数据库（清空表）
- `scripts/check_tables.py` - 检查所有表

## 更新日志

- **2025-12-23**: 初始版本，采用按合约分表策略

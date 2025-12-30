# Changelog

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

## [Unreleased]

### Added
- 新增 `scripts/query_tick_csv.py` - Tick数据查询工具
- 新增 `scripts/scheduler.py` - 定时任务调度器，支持cron表达式
- 新增 `config/scheduler.yaml` - 调度器配置文件

### Changed
- 优化CSV存储引擎性能 (`src/storage/storage_helper.py`)
  - 使用单一锁替代多锁，减少锁对象开销
  - 添加缓冲区大小阈值，达到阈值时立即触发写入
  - 使用StringIO批量构建CSV内容，减少字符串拼接
  - 使用asyncio.gather并发写入多个文件
  - 缓存CSV表头字符串，避免重复拼接
  - 一次性写入整个内容，减少IO次数
  - 写入失败时数据放回缓冲区重试
- 优化浮点数存储精度，使用repr()保持原始精度（如1084.0存储为1084.0）
- 简化 `src/utils/config.py`，移除策略相关配置（CacheConfig保留但默认禁用）
- 时间格式统一使用ISO 8601标准（东八区）：`YYYY-MM-DDTHH:mm:ss.sss+08:00`

### Fixed
- 修复 `_format_value` 方法中None判断逻辑错误
- 修复 `sm4.py` 解密时PKCS7填充去除逻辑
- 修复调度器在Windows下Ctrl+C无法退出的问题（改用BackgroundScheduler）
- 修复调度器启动服务时无法看到终端输出的问题（使用新CMD窗口启动）

### Removed
- 移除QuestDB和InfluxDB相关代码，只保留CSV存储
- 移除 `config/config_csv.yaml`，统一使用 `config/config_md.yaml`

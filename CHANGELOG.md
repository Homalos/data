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

### Changed (Documentation)
- 更新 `docs/QUICK_START.md` - 简化快速开始指南，移除过时的自动登录流程描述
- 更新 `docs/troubleshooting_CN.md` - 移除Redis相关故障排查内容，精简文档结构
- 更新 `docs/development_CN.md` - 更新架构描述，添加CSV存储层说明
- 更新 `docs/TROUBLESHOOTING.md` - 精简英文版故障排查指南
- 更新 `docs/HOW_TO_USE_AUTO_LOGIN.md` - 简化自动登录使用指南

### Removed
- 移除QuestDB和InfluxDB相关代码，只保留CSV存储
- 移除 `config/config_csv.yaml`，统一使用 `config/config_md.yaml`
- 清理docs目录中过时的文档（共删除22个文件）：
  - 删除InfluxDB相关文档：`data_storage_design.md`, `storage_implementation_plan.md`, `storage_structure.md`, `implementation_progress.md`
  - 删除Redis相关文档：`redis_setup_CN.md`, `monitoring_guide_CN.md`, `migration_guide_CN.md`, `performance_tuning_guide_CN.md`, `performance_report_CN.md`, `performance_baseline_report.md`
  - 删除旧版本修复文档：`FIX_SUMMARY.md`, `FIX_SUMMARY_V2.md`, `DEBUG_GUIDE.md`, `HEARTBEAT_FIX.md`, `CTP_CONNECTION_ISSUE_RESOLVED.md`
  - 删除过时的存储文档：`CSV_STORAGE_IMPLEMENTATION.md`, `CSV_STORAGE_READY.md`, `TEST_STORAGE_CLIENT_GUIDE.md`
  - 删除过时的合约文档：`SIMNOW_SETUP_COMPLETE.md`, `FETCH_INSTRUMENTS_UPDATE.md`, `INSTRUMENTS_SIMPLIFICATION.md`
  - 删除其他过时文档：`现在请这样做.md`

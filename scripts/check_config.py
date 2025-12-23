#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查配置文件是否正确

验证：
1. 配置文件是否存在
2. Storage 配置是否正确
3. 字段名大小写是否正确
"""
import sys
from pathlib import Path
import yaml
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_config():
    """检查配置文件"""
    logger.info("=" * 60)
    logger.info("检查配置文件")
    logger.info("=" * 60)
    
    # 检查配置文件是否存在
    config_file = project_root / "config" / "config_td.yaml"
    
    if not config_file.exists():
        logger.error(f"❌ 配置文件不存在: {config_file}")
        return False
    
    logger.info(f"✅ 配置文件存在: {config_file}")
    
    # 读取配置文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"❌ 读取配置文件失败: {e}")
        return False
    
    logger.info("✅ 配置文件读取成功")
    
    # 检查 Storage 配置
    if "Storage" not in config:
        logger.error("❌ 配置文件中没有 Storage 配置")
        logger.info("\n请添加以下配置到 config/config_td.yaml:")
        logger.info("""
Storage:
  Enabled: true
  Instruments:
    CachePath: data/instruments.json
""")
        return False
    
    logger.info("✅ 找到 Storage 配置")
    
    storage_config = config["Storage"]
    
    # 检查 Enabled 字段
    if "Enabled" not in storage_config:
        if "enabled" in storage_config:
            logger.error("❌ 字段名错误: 应该是 'Enabled' (大写 E)，不是 'enabled' (小写 e)")
            logger.info("\n请修改配置文件，将 'enabled' 改为 'Enabled'")
            return False
        else:
            logger.error("❌ Storage 配置中没有 Enabled 字段")
            return False
    
    enabled = storage_config["Enabled"]
    if not enabled:
        logger.warning("⚠️  Storage.Enabled 为 false，存储服务未启用")
        logger.info("\n请将 Enabled 设置为 true")
        return False
    
    logger.info("✅ Storage.Enabled = true")
    
    # 检查 Instruments 配置
    if "Instruments" not in storage_config:
        if "instruments" in storage_config:
            logger.error("❌ 字段名错误: 应该是 'Instruments' (大写 I)，不是 'instruments' (小写 i)")
            logger.info("\n请修改配置文件，将 'instruments' 改为 'Instruments'")
            return False
        else:
            logger.warning("⚠️  Storage 配置中没有 Instruments 字段，将使用默认值")
    else:
        instruments_config = storage_config["Instruments"]
        
        # 检查 CachePath 字段
        if "CachePath" not in instruments_config:
            if "cache_path" in instruments_config:
                logger.error("❌ 字段名错误: 应该是 'CachePath' (大写 C 和 P)，不是 'cache_path' (小写)")
                logger.info("\n请修改配置文件，将 'cache_path' 改为 'CachePath'")
                return False
            else:
                logger.warning("⚠️  Instruments 配置中没有 CachePath 字段，将使用默认值")
        else:
            cache_path = instruments_config["CachePath"]
            logger.info(f"✅ Instruments.CachePath = {cache_path}")
    
    # 显示完整的 Storage 配置
    logger.info("\n当前 Storage 配置:")
    logger.info(yaml.dump({"Storage": storage_config}, default_flow_style=False, allow_unicode=True))
    
    logger.info("=" * 60)
    logger.info("✅ 配置检查通过")
    logger.info("=" * 60)
    logger.info("\n下一步:")
    logger.info("1. 重启交易服务")
    logger.info("2. 运行自动登录脚本: python scripts/auto_login_td.py")
    
    return True


if __name__ == "__main__":
    try:
        success = check_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"检查配置时出错: {e}", exc_info=True)
        sys.exit(1)

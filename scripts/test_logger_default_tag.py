#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Logger 默认 tag 功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.log import logger


class PaymentService:
    """支付服务示例类"""
    
    def __init__(self):
        # 设置类级别的默认 tag
        logger.set_default_tag("payment")
        logger.info("支付服务初始化")
    
    def process_payment(self, order_id: str, amount: float):
        # 不需要传入 tag，自动使用 "payment"
        logger.info(f"开始处理支付: {order_id}")
        
        try:
            # 验证金额
            if amount <= 0:
                logger.warning(f"无效金额: {amount}")
                raise ValueError("金额必须大于 0")
            
            # 调用支付接口
            logger.debug(f"调用支付 API: order={order_id}, amount={amount}")
            
            # 模拟支付成功
            logger.success(f"支付成功: {order_id}")
            return {"status": "success", "order_id": order_id}
            
        except Exception as e:
            logger.exception(f"支付失败: {e}")
            raise
    
    def refund(self, order_id: str):
        logger.info(f"处理退款: {order_id}")
        logger.success(f"退款成功: {order_id}")
    
    def __del__(self):
        # 清理时清除默认 tag
        logger.clear_default_tag()


class DatabaseService:
    """数据库服务示例类"""
    
    def __init__(self):
        logger.set_default_tag("database")
        logger.info("数据库服务初始化")
    
    def query(self, sql: str):
        logger.debug(f"执行查询: {sql}")
        return []
    
    def insert(self, table: str, data: dict):
        logger.info(f"插入数据到表 {table}")
        logger.success("数据插入成功")
    
    def __del__(self):
        logger.clear_default_tag()


class OrderService:
    """订单服务示例类 - 演示覆盖默认 tag"""
    
    def __init__(self):
        logger.set_default_tag("order")
        logger.info("订单服务初始化")
    
    def create_order(self, user_id: int, items: list):
        # 使用默认 tag "order"
        logger.info(f"创建订单: user={user_id}")
        
        # 覆盖默认 tag，使用 "database"
        logger.debug("查询用户信息", tag="database")
        
        # 覆盖默认 tag，使用 "payment"
        logger.info("处理支付", tag="payment")
        
        # 又回到默认 tag "order"
        logger.success("订单创建成功")
    
    def __del__(self):
        logger.clear_default_tag()


def test_basic_usage():
    """测试基础使用"""
    print("\n" + "=" * 60)
    print("测试 1: 基础使用 - PaymentService")
    print("=" * 60)
    
    payment_service = PaymentService()
    payment_service.process_payment("ORD-123", 100.0)
    payment_service.refund("ORD-123")


def test_multiple_services():
    """测试多个服务"""
    print("\n" + "=" * 60)
    print("测试 2: 多个服务 - 不同的默认 tag")
    print("=" * 60)
    
    payment = PaymentService()
    database = DatabaseService()
    
    payment.process_payment("ORD-456", 200.0)
    database.query("SELECT * FROM users")
    database.insert("orders", {"id": 1, "amount": 200.0})


def test_tag_override():
    """测试覆盖默认 tag"""
    print("\n" + "=" * 60)
    print("测试 3: 覆盖默认 tag")
    print("=" * 60)
    
    order_service = OrderService()
    order_service.create_order(123, ["item1", "item2"])


def test_with_trace_id():
    """测试与 trace_id 结合使用"""
    print("\n" + "=" * 60)
    print("测试 4: 与 trace_id 结合使用")
    print("=" * 60)
    
    payment = PaymentService()
    
    # 设置 trace_id
    trace_id = logger.set_trace_id("req-789")
    
    try:
        payment.process_payment("ORD-789", 300.0)
    finally:
        logger.clear_trace_id()


def test_without_default_tag():
    """测试不设置默认 tag"""
    print("\n" + "=" * 60)
    print("测试 5: 不设置默认 tag（对比）")
    print("=" * 60)
    
    logger.info("普通日志，无 tag")
    logger.info("指定 tag", tag="custom")
    logger.info("又回到无 tag")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Logger 默认 Tag 功能测试")
    print("=" * 60)
    
    # 运行所有测试
    test_basic_usage()
    test_multiple_services()
    test_tag_override()
    test_with_trace_id()
    test_without_default_tag()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    print("\n提示：")
    print("  - 查看控制台输出，观察不同的 tag 标签")
    print("  - 查看 logs/webctp.log 文件，查看完整日志")
    print("  - 注意默认 tag 如何自动应用到所有日志")
    print("  - 注意如何覆盖默认 tag")
    print("")


if __name__ == "__main__":
    main()

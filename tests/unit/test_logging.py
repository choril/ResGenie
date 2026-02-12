"""测试日志系统功能"""
# python -m tests.unit.test_logging
from src.core.logging import get_logger, init_logging, set_log_level, LogContext, log_function_call, log_exception

logger = get_logger("test")

def test_basic_logging():
    """测试基本日志功能"""

    print("=== 测试基本日志功能 ===")
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.critical("这是一条严重错误信息")
    print()


def test_log_level():
    """测试日志级别设置"""
    
    print("=== 测试日志级别设置 ===")
    
    print("当前日志级别: ", logger.level)
    logger.debug("debug日志--不会显示")
    logger.info("info日志--会显示")
    
    print("\n切换到 DEBUG 级别")
    set_log_level("DEBUG")
    print("当前日志级别: ", logger.level)
    logger.debug("debug日志--会显示")
    
    print("\n切换回 INFO 级别")
    set_log_level("INFO")
    logger.debug("debug日志--不会显示")
    print()


def test_log_context():
    """测试日志上下文管理器"""
    
    print("=== 测试日志上下文管理器 ===")
    
    print("当前日志级别: ", logger.level)
    logger.debug("debug日志--不会显示")
    
    print("\n进入 DEBUG 上下文")
    with LogContext(logger, "DEBUG"):
        logger.debug("在上下文中，debug调试信息会显示")
    
    print("\n退出上下文")
    logger.debug("退出上下文后，debug调试信息又不会显示了")
    print()


def test_function_decorator():
    """测试函数调用日志装饰器"""
    
    print("=== 测试函数调用日志装饰器 ===")
    logger.setLevel("DEBUG")
    
    @log_function_call(logger)
    def add(a, b):
        return a + b
    
    @log_function_call(logger)
    def multiply(a, b):
        return a * b
    
    result1 = add(3, 5)
    result2 = multiply(4, 7)
    print()


def test_exception_decorator():
    """测试异常日志装饰器"""
    
    print("=== 测试异常日志装饰器 ===")
    
    @log_exception(logger)
    def divide(a, b):
        return a / b
    
    try:
        result = divide(10, 2)
        print(f"divide(10, 2) = {result}")
    except Exception as e:
        print(f"捕获到异常: {e}")
    
    try:
        result = divide(10, 0)
        print(f"divide(10, 0) = {result}")
    except Exception as e:
        pass
    print()


def test_multiple_loggers():
    """测试多个日志器"""
    print("=== 测试多个日志器 ===")
    
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")
    logger3 = get_logger("module3")
    
    logger1.info("来自模块1的信息")
    logger2.info("来自模块2的信息")
    logger3.info("来自模块3的信息")
    print()


def test_custom_init():
    """测试自定义初始化"""
    print("=== 测试自定义初始化 ===")
    
    custom_logger = init_logging(
        name="custom_app",
        level="DEBUG",
        log_to_console=True,
        log_to_file=True
    )
    
    custom_logger.debug("自定义日志器的调试信息")
    custom_logger.info("自定义日志器的普通信息")
    custom_logger.warning("自定义日志器的警告信息")
    print()


if __name__ == "__main__":
    print("ResGenie 日志系统测试\n")
    print("=" * 50)
    print()
    
    test_basic_logging()
    test_log_level()
    test_log_context()
    test_function_decorator()
    test_exception_decorator()
    test_multiple_loggers()
    test_custom_init()
    
    print("=" * 50)
    print("所有测试完成！")
    print("\n请检查 logs/ 目录中的日志文件")

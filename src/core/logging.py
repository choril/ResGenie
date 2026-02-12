"""ResGenie 日志系统模块"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional

from .config import settings

class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[1;36m',      # 青色
        'INFO': '\033[1;32m',       # 绿色
        'WARNING': '\033[1;33m',    # 黄色
        'ERROR': '\033[1;31m',      # 红色
        'CRITICAL': '\033[1;35m',   # 紫色
    }
    RESET = '\033[0m'   # 重置颜色
    
    def format(self, record):
        original_levelname = record.levelname
        
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        
        formatted = super().format(record)
        # 恢复原始 levelname，确保只在终端输出时生效
        record.levelname = original_levelname
        
        return formatted

class ResGenieLogger:
    """ResGenie 日志管理器"""
    
    def __init__(self):
        self.logger = None
        self.log_dir = Path(settings.log_dir)
    
    def init_logger(
        self,
        name: str = "resgenie",
        level: Optional[str] = None,
        log_to_file: bool = True,
        log_to_console: bool = True
    ) -> logging.Logger:
        """初始化日志系统
        
        Args:
            name: 日志器名称
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: 是否记录到文件
            log_to_console: 是否输出到控制台
            
        Returns:
            logging.Logger: 配置好的日志器
        """
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(name)
        
        log_level = level or settings.log_level
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # 防止重复添加处理器
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 防止日志传播到父级
        self.logger.propagate = False
        
        # 详细格式化器
        detailed_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 简单格式化器
        simple_formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            colored_formatter = ColoredFormatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(colored_formatter)
            self.logger.addHandler(console_handler)
        
        # 文件处理器
        if log_to_file:
            # 主日志文件（按大小轮转）
            main_log_file = self.log_dir / f"{name}.log"
            file_handler = RotatingFileHandler(
                main_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,  # 保留5个备份文件
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)
            
            # 错误日志文件（单独记录错误和严重错误）
            error_log_file = self.log_dir / f"{name}_error.log"
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(error_handler)
            
            # 按日期轮转的日志文件
            daily_log_file = self.log_dir / f"{name}_daily.log"
            daily_handler = TimedRotatingFileHandler(
                daily_log_file,
                when='midnight',
                interval=1,  # 每天轮转一次
                backupCount=30,
                encoding='utf-8'
            )
            daily_handler.suffix = "%Y-%m-%d"  # 每天的日志文件名后缀
            daily_handler.setLevel(logging.DEBUG)
            daily_handler.setFormatter(simple_formatter)
            self.logger.addHandler(daily_handler)
        
        return self.logger
    
    def get_logger(self, name: str = "resgenie") -> logging.Logger:
        """获取日志器
        
        Args:
            name: 日志器名称
            
        Returns:
            logging.Logger: 日志器实例
        """
        if not self.logger or self.logger.name != name:
            self.logger = self.init_logger(name)
        
        return self.logger
    
    def set_level(self, level: str):
        """设置日志级别
        
        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    def clear_handlers(self):
        """清除所有处理器"""
        self.logger.handlers.clear()

# 创建全局日志管理器实例
_logger_manager = ResGenieLogger()

def get_logger(name: str = "resgenie") -> logging.Logger:
    """获取日志器的便捷函数
    
    Args:
        name: 日志器名称，默认为 'resgenie'
        
    Returns:
        logging.Logger: 日志器实例
        
    Example:
        >>> from src.core.logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息")
    """
    return _logger_manager.get_logger(name)

def init_logging(
    name: str = "resgenie",
    level: Optional[str] = None,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """初始化日志系统的便捷函数
    
    Args:
        name: 日志器名称
        level: 日志级别
        log_to_file: 是否记录到文件
        log_to_console: 是否输出到控制台
        
    Returns:
        logging.Logger: 配置好的日志器
        
    Example:
        >>> from src.core.logging import init_logging
        >>> logger = init_logging("myapp", level="DEBUG")
        >>> logger.debug("调试信息")
    """
    return _logger_manager.init_logger(name, level, log_to_file, log_to_console)

def set_log_level(level: str) -> None:
    """设置日志级别的便捷函数
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Example:
        >>> from src.core.logging import set_log_level
        >>> set_log_level("DEBUG")
    """
    _logger_manager.set_level(level)

class LogContext:
    """日志上下文管理器，用于临时修改日志级别"""
    
    def __init__(self, logger: logging.Logger, level: str):
        self.logger = logger
        self.level = level
        self.original_level = None
    
    def __enter__(self):
        self.original_level = self.logger.level
        self.logger.setLevel(getattr(logging, self.level.upper(), logging.INFO))
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)

def log_function_call(logger: logging.Logger):
    """函数调用日志装饰器
    
    Args:
        logger: 日志器实例
        
    Example:
        >>> from src.core.logging import get_logger, log_function_call
        >>> logger = get_logger(__name__)
        >>> 
        >>> @log_function_call(logger)
        >>> def my_function(x, y):
        ...     return x + y
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"调用函数: {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {str(e)}")
                raise
        return wrapper
    return decorator


def log_exception(logger: logging.Logger):
    """异常日志装饰器
    
    Args:
        logger: 日志器实例
        
    Example:
        >>> from src.core.logging import get_logger, log_exception
        >>> logger = get_logger(__name__)
        >>> 
        >>> @log_exception(logger)
        >>> def risky_function():
        ...     raise ValueError("出错了")
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"函数 {func.__name__} 发生异常: {str(e)}")
                raise
        return wrapper
    return decorator
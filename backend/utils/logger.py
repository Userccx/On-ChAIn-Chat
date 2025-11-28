# Logging configuration
import logging
import os
from datetime import datetime
from pathlib import Path

# 日志文件目录
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志文件名（带时间戳）
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"

# 全局日志级别（从配置中读取，默认为 DEBUG）
_global_log_level = logging.DEBUG


def set_global_log_level(level: int):
    """设置全局日志级别"""
    global _global_log_level
    _global_log_level = level


def setup_logger(name: str = "app", level: int = None) -> logging.Logger:
    """
    设置并返回配置好的 logger 实例
    
    Args:
        name: logger 名称
        level: 日志级别，如果为 None 则使用全局日志级别
        
    Returns:
        配置好的 logger 实例
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 如果没有指定级别，使用全局日志级别
    if level is None:
        level = _global_log_level
    
    logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件 handler（写入日志文件）
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台 handler（同时输出到控制台，方便开发时查看）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取 logger 实例
    
    Args:
        name: logger 名称，如果为 None 则使用调用模块的名称
        
    Returns:
        logger 实例
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'app')
    
    return setup_logger(name)


# 默认 logger（用于直接导入使用）
default_logger = setup_logger("app")


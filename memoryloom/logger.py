import logging
import sys
from pathlib import Path

def get_logger(name: str = "loom", log_file: str = "log/main.log") -> logging.Logger:
    """创建并配置日志记录器
    
    Args:
        name: 记录器名称（默认：my_logger）
        log_file: 日志文件路径（默认：当前目录下的app.log）
        
    Returns:
        配置好的logging.Logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 捕获所有级别日志
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 创建日志格式
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # 文件处理器（追加模式）
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)  # 控制台只显示INFO及以上级别

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# ===== 使用示例 =====
if __name__ == "__main__":
    logger = get_logger("my_logger", "log/my_app.log")
    
    logger.debug("这是一条debug信息（仅写入文件）")
    logger.info("程序启动")
    logger.warning("磁盘空间不足")
    logger.error("文件读取失败")
    logger.critical("系统崩溃")

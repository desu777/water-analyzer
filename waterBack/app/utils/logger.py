import logging
import os
from datetime import datetime
from app.config import settings

def setup_logger(name: str) -> logging.Logger:
    """Setup logger with consistent formatting"""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    # Set logging level
    level = logging.DEBUG if settings.DEBUG_MODE else logging.INFO
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = logging.FileHandler(
        f'logs/water_analyzer_{datetime.now().strftime("%Y%m%d")}.log'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create default logger
logger = setup_logger(__name__)

def log_debug(message: str, component: str = "SYSTEM"):
    """Log debug message if DEBUG_MODE is enabled"""
    if settings.DEBUG_MODE:
        logger.debug(f"[{component}] {message}")

def log_info(message: str, component: str = "SYSTEM"):
    """Log info message"""
    logger.info(f"[{component}] {message}")

def log_warning(message: str, component: str = "SYSTEM"):
    """Log warning message"""
    logger.warning(f"[{component}] {message}")

def log_error(message: str, component: str = "SYSTEM"):
    """Log error message"""
    logger.error(f"[{component}] {message}")

def log_critical(message: str, component: str = "SYSTEM"):
    """Log critical message"""
    logger.critical(f"[{component}] {message}") 
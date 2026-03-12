"""
Logger Module - Compatibility Wrapper
Provides unified logging interface using loguru
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional
import logging


def setup_logger(log_file: Optional[str] = None, 
                level: str = "INFO",
                rotation: str = "100 MB",
                retention: str = "30 days"):
    """
    Setup logger with file and console output
    
    Args:
        log_file: Path to log file (default: logs/trading_bot.log)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: When to rotate log file
        retention: How long to keep old logs
        
    Returns:
        Configured logger instance
    """
    # Remove default handler
    try:
        logger.remove()
    
        # Add console handler with colors
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=level,
            colorize=True
        )
    
        # Add file handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=level,
                rotation=rotation,
                retention=retention,
                compression="zip"
            )
        else:
            # Default log file
            default_log = Path("logs/trading_bot.log")
            default_log.parent.mkdir(parents=True, exist_ok=True)
        
            logger.add(
                str(default_log),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=level,
                rotation=rotation,
                retention=retention,
                compression="zip"
            )
    
        return logger
    except Exception as e:
        logger.error(f"Error in setup_logger: {e}")
        raise

# Create default logger instance
default_logger = setup_logger()

# Export for compatibility
__all__ = ['setup_logger', 'logger', 'default_logger']

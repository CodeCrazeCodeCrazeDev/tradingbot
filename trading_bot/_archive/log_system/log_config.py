"""
Advanced logging configuration with rotation and structured logging.
Implements production-grade logging with Loguru.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional
import logging
logger = logging.getLogger(__name__)
import json


class LogConfig:
    """Centralized logging configuration."""
    
    def __init__(self, log_dir: str = "logs", rotation: str = "100 MB", 
                 retention: str = "30 days", compression: str = "zip"):
        """
        Initialize logging configuration.
        
        Args:
            log_dir: Directory for log files
            rotation: When to rotate logs (size or time)
            retention: How long to keep logs
            compression: Compression format for rotated logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.rotation = rotation
        self.retention = retention
        self.compression = compression
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup Loguru logging with rotation and formatting."""
        
        # Remove default handler
        logger.remove()
        
        # Console handler with color
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO",
            colorize=True
        )
        
        # File handler for all logs
        logger.add(
            self.log_dir / "alphaalgo_{time:YYYY-MM-DD}.log",
            rotation=self.rotation,
            retention=self.retention,
            compression=self.compression,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG"
        )
        
        # Separate file for errors
        logger.add(
            self.log_dir / "errors_{time:YYYY-MM-DD}.log",
            rotation=self.rotation,
            retention=self.retention,
            compression=self.compression,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR"
        )
        
        # JSON structured logging for production
        logger.add(
            self.log_dir / "structured_{time:YYYY-MM-DD}.json",
            rotation=self.rotation,
            retention=self.retention,
            compression=self.compression,
            serialize=True,
            level="INFO"
        )
        
        logger.info("Logging system initialized")
        logger.info(f"Log directory: {self.log_dir.absolute()}")
        logger.info(f"Rotation: {self.rotation}, Retention: {self.retention}")
    
    def log_trade(self, symbol: str, action: str, lot: float, price: float, 
                  sl: float, tp: float, **kwargs):
        """Structured logging for trades."""
        logger.bind(
            event_type="trade",
            symbol=symbol,
            action=action,
            lot=lot,
            price=price,
            sl=sl,
            tp=tp,
            **kwargs
        ).info(f"Trade executed: {action} {lot} {symbol} @ {price}")
    
    def log_signal(self, symbol: str, signal: str, confidence: float, **kwargs):
        """Structured logging for signals."""
        logger.bind(
            event_type="signal",
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            **kwargs
        ).info(f"Signal generated: {signal} for {symbol} (confidence: {confidence:.2%})")
    
    def log_error(self, error_type: str, message: str, **kwargs):
        """Structured logging for errors."""
        logger.bind(
            event_type="error",
            error_type=error_type,
            **kwargs
        ).error(f"{error_type}: {message}")
    
    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """Structured logging for performance metrics."""
        logger.bind(
            event_type="performance",
            operation=operation,
            duration_ms=duration_ms,
            **kwargs
        ).debug(f"Performance: {operation} took {duration_ms:.2f}ms")


# Global log config instance
_log_config: Optional[LogConfig] = None


def setup_logging(log_dir: str = "logs", **kwargs) -> LogConfig:
    """Setup global logging configuration."""
    global _log_config
    _log_config = LogConfig(log_dir, **kwargs)
    return _log_config


def get_logger():
    """Get configured logger instance."""
    return logger

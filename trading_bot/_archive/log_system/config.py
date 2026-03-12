"""
import asyncio
Centralized Logging Configuration
=================================

This module provides a unified logging configuration for the entire trading bot.

Usage:
    from trading_bot.log_system.config import setup_logging, get_logger
    
    # Setup at application start
    setup_logging(level='INFO', log_file='logs/trading.log')
    
    # Get a logger for your module
    logger = get_logger(__name__)
    logger.info("Starting trading...")
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json

try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        
        return json.dumps(log_entry)


class TradingFormatter(logging.Formatter):
    """Custom formatter for trading logs with color support."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, use_colors: bool = True):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.use_colors = use_colors
    
    def format(self, record):
        if self.use_colors and record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    json_format: bool = False,
    use_colors: bool = True,
    rotation: str = '10 MB',
    retention: str = '7 days'
) -> None:
    """
    Setup centralized logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        json_format: Use JSON format for logs
        use_colors: Use colored output in console
        rotation: Log file rotation size
        retention: Log file retention period
    """
    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(TradingFormatter(use_colors=use_colors))
    
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('tensorflow').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    
    # Setup loguru if available
    if LOGURU_AVAILABLE:
        loguru_logger.remove()
        loguru_logger.add(
            sys.stdout,
            level=level.upper(),
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        if log_file:
            loguru_logger.add(
                log_file,
                level='DEBUG',
                rotation=rotation,
                retention=retention,
                compression='zip'
            )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class TradingLogger:
    """
    Specialized logger for trading operations.
    
    Provides structured logging for trades, signals, and risk events.
    """
    
    def __init__(self, name: str = 'trading'):
        self.logger = get_logger(name)
    
    def trade_opened(self, symbol: str, direction: str, size: float, price: float, **kwargs):
        """Log trade opened event."""
        self.logger.info(
            f"TRADE OPENED: {symbol} {direction} {size} lots @ {price}",
            extra={'event': 'trade_opened', 'symbol': symbol, 'direction': direction, 
                   'size': size, 'price': price, **kwargs}
        )
    
    def trade_closed(self, symbol: str, profit: float, pips: float, **kwargs):
        """Log trade closed event."""
        level = logging.INFO if profit >= 0 else logging.WARNING
        self.logger.log(
            level,
            f"TRADE CLOSED: {symbol} P/L: {profit:.2f} ({pips:.1f} pips)",
            extra={'event': 'trade_closed', 'symbol': symbol, 'profit': profit, 
                   'pips': pips, **kwargs}
        )
    
    def signal_generated(self, symbol: str, direction: str, confidence: float, **kwargs):
        """Log signal generated event."""
        self.logger.info(
            f"SIGNAL: {symbol} {direction} (confidence: {confidence:.2%})",
            extra={'event': 'signal', 'symbol': symbol, 'direction': direction,
                   'confidence': confidence, **kwargs}
        )
    
    def risk_alert(self, message: str, level: str = 'WARNING', **kwargs):
        """Log risk alert."""
        log_level = getattr(logging, level.upper(), logging.WARNING)
        self.logger.log(
            log_level,
            f"RISK ALERT: {message}",
            extra={'event': 'risk_alert', **kwargs}
        )
    
    def system_event(self, event: str, message: str, **kwargs):
        """Log system event."""
        self.logger.info(
            f"SYSTEM [{event}]: {message}",
            extra={'event': event, **kwargs}
        )


# Default trading logger instance
trading_logger = TradingLogger()


__all__ = [
    'setup_logging',
    'get_logger',
    'TradingLogger',
    'trading_logger',
    'JSONFormatter',
    'TradingFormatter',
]

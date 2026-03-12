"""
AlphaAlgo Logging Configuration - Structured Logging

This module provides structured logging configuration.

Version: 1.0.0
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
from pathlib import Path


class LogLevel(Enum):
    """Log levels"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data['data'] = record.extra_data
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class StructuredLogger:
    """Structured logger with extra data support"""
    
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
    
    def _log(self, level: int, message: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        extra = {'extra_data': data} if data else {}
        self._logger.log(level, message, extra=extra, **kwargs)
    
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.DEBUG, message, data, **kwargs)
    
    def info(self, message: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.INFO, message, data, **kwargs)
    
    def warning(self, message: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.WARNING, message, data, **kwargs)
    
    def error(self, message: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.ERROR, message, data, **kwargs)
    
    def critical(self, message: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.CRITICAL, message, data, **kwargs)
    
    def exception(self, message: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.ERROR, message, data, exc_info=True, **kwargs)


def setup_logging(
    level: LogLevel = LogLevel.INFO,
    log_dir: Optional[str] = None,
    console: bool = True,
    file: bool = True,
    structured: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Log level
        log_dir: Directory for log files
        console: Enable console logging
        file: Enable file logging
        structured: Use JSON structured logging
        max_bytes: Max size per log file
        backup_count: Number of backup files to keep
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level.value)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level.value)
        
        if structured:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(ColoredFormatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
        
        root_logger.addHandler(console_handler)
    
    # File handler
    if file and log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Main log file
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / 'alphaalgo.log',
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level.value)
        
        if structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
        
        root_logger.addHandler(file_handler)
        
        # Error log file
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / 'alphaalgo_error.log',
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s\n%(exc_info)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        
        root_logger.addHandler(error_handler)
    
    logging.info(f"Logging configured: level={level.name}, console={console}, file={file}")


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger"""
    return StructuredLogger(name)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def log_trade(
    action: str,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    **kwargs
) -> None:
    """Log a trade event"""
    logger = get_logger('trading')
    logger.info(
        f"Trade: {action} {side} {quantity} {symbol} @ {price}",
        data={
            'action': action,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            **kwargs
        }
    )


def log_signal(
    signal_type: str,
    symbol: str,
    confidence: float,
    source: str,
    **kwargs
) -> None:
    """Log a signal event"""
    logger = get_logger('signals')
    logger.info(
        f"Signal: {signal_type} {symbol} (confidence={confidence:.2%})",
        data={
            'signal_type': signal_type,
            'symbol': symbol,
            'confidence': confidence,
            'source': source,
            **kwargs
        }
    )


def log_risk_event(
    event_type: str,
    current_value: float,
    limit_value: float,
    **kwargs
) -> None:
    """Log a risk event"""
    logger = get_logger('risk')
    logger.warning(
        f"Risk Event: {event_type} (current={current_value:.2%}, limit={limit_value:.2%})",
        data={
            'event_type': event_type,
            'current_value': current_value,
            'limit_value': limit_value,
            **kwargs
        }
    )

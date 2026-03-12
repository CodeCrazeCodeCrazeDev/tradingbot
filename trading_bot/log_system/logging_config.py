"""
Centralized Logging Configuration
Provides consistent logging across all modules.

Usage:
    from trading_bot.log_system.logging_config import setup_logging, get_logger
    
    # At application startup
    setup_logging(level='INFO', log_file='trading.log')
    
    # In each module
    logger = get_logger(__name__)
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class LogConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_dir: str = "logs"
    log_file: str = "trading_bot.log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True
    file_output: bool = True
    json_output: bool = False
    sensitive_fields: list = None
    
    def __post_init__(self):
        if self.sensitive_fields is None:
            self.sensitive_fields = [
                'password', 'api_key', 'secret', 'token', 
                'credential', 'auth', 'key'
            ]


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in logs"""
    
    def __init__(self, sensitive_fields: list):
        super().__init__()
        self.sensitive_fields = [f.lower() for f in sensitive_fields]
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Mask sensitive data in the message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._mask_sensitive(record.msg)
        
        # Mask in args
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._mask_value(k, v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._mask_sensitive(str(a)) if isinstance(a, str) else a 
                                   for a in record.args)
        
        return True
    
    def _mask_sensitive(self, text: str) -> str:
        """Mask sensitive patterns in text"""
        import re
        
        # Mask API keys (common patterns)
        patterns = [
            (r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', 
             r'api_key=***MASKED***'),
            (r'secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', 
             r'secret=***MASKED***'),
            (r'password["\']?\s*[:=]\s*["\']?([^\s"\']+)["\']?', 
             r'password=***MASKED***'),
            (r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_.-]{20,})["\']?', 
             r'token=***MASKED***'),
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _mask_value(self, key: str, value: Any) -> Any:
        """Mask value if key is sensitive"""
        if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
            if isinstance(value, str) and len(value) > 4:
                return value[:4] + '*' * (len(value) - 4)
            return '***MASKED***'
        return value


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
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
        for key, value in record.__dict__.items():
            if key not in ['msg', 'args', 'created', 'filename', 'funcName', 
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'name', 'pathname', 'process', 'processName', 
                          'relativeCreated', 'stack_info', 'thread', 'threadName',
                          'exc_info', 'exc_text', 'message']:
                log_data[key] = value
        
        return json.dumps(log_data)


class TradingBotLogger:
    """
    Centralized logger for the trading bot.
    Ensures consistent logging configuration across all modules.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if TradingBotLogger._initialized:
            return
        
        self.config = LogConfig()
        self.root_logger = logging.getLogger('trading_bot')
        TradingBotLogger._initialized = True
    
    def setup(self, config: Optional[LogConfig] = None):
        """Setup logging with configuration"""
        if config:
            self.config = config
        
        # Create log directory
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set root logger level
        level = getattr(logging, self.config.level.upper(), logging.INFO)
        self.root_logger.setLevel(level)
        
        # Remove existing handlers
        self.root_logger.handlers.clear()
        
        # Create formatters
        standard_formatter = logging.Formatter(
            self.config.format,
            datefmt=self.config.date_format
        )
        json_formatter = JSONFormatter()
        
        # Create sensitive data filter
        sensitive_filter = SensitiveDataFilter(self.config.sensitive_fields)
        
        # Console handler
        if self.config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(standard_formatter)
            console_handler.addFilter(sensitive_filter)
            self.root_logger.addHandler(console_handler)
        
        # File handler (rotating)
        if self.config.file_output:
            log_file = log_dir / self.config.log_file
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(standard_formatter)
            file_handler.addFilter(sensitive_filter)
            self.root_logger.addHandler(file_handler)
        
        # JSON file handler (for structured logging)
        if self.config.json_output:
            json_file = log_dir / f"{self.config.log_file.replace('.log', '')}_json.log"
            json_handler = logging.handlers.RotatingFileHandler(
                json_file,
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            json_handler.setLevel(level)
            json_handler.setFormatter(json_formatter)
            json_handler.addFilter(sensitive_filter)
            self.root_logger.addHandler(json_handler)
        
        # Prevent propagation to root logger
        self.root_logger.propagate = False
        
        self.root_logger.info(f"Logging initialized at {self.config.level} level")
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger for a specific module"""
        if name.startswith('trading_bot.'):
            return logging.getLogger(name)
        return logging.getLogger(f'trading_bot.{name}')


# Global instance
_logger_instance: Optional[TradingBotLogger] = None


def setup_logging(
    level: str = "INFO",
    log_file: str = "trading_bot.log",
    log_dir: str = "logs",
    console: bool = True,
    file: bool = True,
    json: bool = False
):
    """
    Setup logging for the trading bot.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file name
        log_dir: Log directory
        console: Enable console output
        file: Enable file output
        json: Enable JSON structured logging
    """
    global _logger_instance
    
    config = LogConfig(
        level=level,
        log_file=log_file,
        log_dir=log_dir,
        console_output=console,
        file_output=file,
        json_output=json,
    )
    
    _logger_instance = TradingBotLogger()
    _logger_instance.setup(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Logger instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = TradingBotLogger()
        _logger_instance.setup()
    
    return _logger_instance.get_logger(name)


# Convenience function to replace print statements
def log_print(message: str, level: str = "INFO"):
    """
    Replacement for print statements.
    Use this during migration from print to logging.
    """
    logger = get_logger('print_migration')
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)


# Context manager for temporary log level changes
class LogLevelContext:
    """Context manager to temporarily change log level"""
    
    def __init__(self, logger_name: str, level: str):
        self.logger = logging.getLogger(logger_name)
        self.new_level = getattr(logging, level.upper(), logging.INFO)
        self.old_level = None
    
    def __enter__(self):
        self.old_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)
        return False


# Performance logging decorator
def log_performance(logger: Optional[logging.Logger] = None):
    """Decorator to log function execution time"""
    import functools
    import time
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"{func.__name__} completed in {elapsed:.4f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed:.4f}s: {e}")
                raise
        
        return wrapper
    return decorator


# Async performance logging decorator
def log_performance_async(logger: Optional[logging.Logger] = None):
    """Decorator to log async function execution time"""
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"{func.__name__} completed in {elapsed:.4f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed:.4f}s: {e}")
                raise
        
        return wrapper
    return decorator

from typing import Set
import asyncio

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator

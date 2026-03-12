"""
Layer 7: Infrastructure & Orchestration - Logging System
Centralized logging with structured output and performance monitoring.
"""

import logging
import logging.handlers
import sys
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import traceback


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
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
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        return json.dumps(log_entry, ensure_ascii=False)


class TradingLogFilter(logging.Filter):
    """Filter for trading-specific log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records based on trading context."""
        # Always allow ERROR and CRITICAL
        if record.levelno >= logging.ERROR:
            return True
            
        # Filter out noisy third-party libraries in production
        noisy_loggers = [
            'urllib3.connectionpool',
            'requests.packages.urllib3',
            'matplotlib',
            'PIL',
        ]
        
        for noisy in noisy_loggers:
            if record.name.startswith(noisy):
                return record.levelno >= logging.WARNING
                
        return True


class PerformanceLogger:
    """Logger for performance metrics and trading events."""
    
    def __init__(self, name: str = "trading.performance"):
        self.logger = logging.getLogger(name)
        
    def log_trade(self, symbol: str, action: str, quantity: float, 
                  price: float, **kwargs) -> None:
        """Log trading event."""
        extra_fields = {
            'event_type': 'trade',
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            **kwargs
        }
        
        self.logger.info(
            f"Trade executed: {action} {quantity} {symbol} @ {price}",
            extra={'extra_fields': extra_fields}
        )
        
    def log_signal(self, symbol: str, signal_type: str, confidence: float,
                   **kwargs) -> None:
        """Log trading signal."""
        extra_fields = {
            'event_type': 'signal',
            'symbol': symbol,
            'signal_type': signal_type,
            'confidence': confidence,
            **kwargs
        }
        
        self.logger.info(
            f"Signal generated: {signal_type} for {symbol} (confidence: {confidence:.2f})",
            extra={'extra_fields': extra_fields}
        )
        
    def log_performance(self, metric_name: str, value: float, **kwargs) -> None:
        """Log performance metric."""
        extra_fields = {
            'event_type': 'performance',
            'metric': metric_name,
            'value': value,
            **kwargs
        }
        
        self.logger.info(
            f"Performance metric: {metric_name} = {value}",
            extra={'extra_fields': extra_fields}
        )


def setup_logging(level: str = "INFO", 
                  log_dir: Optional[Path] = None,
                  structured: bool = True,
                  console_output: bool = True) -> None:
    """
    Setup centralized logging for the trading system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (None = logs/ in current dir)
        structured: Use structured JSON logging
        console_output: Enable console output
    """
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create log directory
    if log_dir is None:
        log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set root level
    root_logger.setLevel(numeric_level)
    
    # Create formatters
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(TradingLogFilter())
        root_logger.addHandler(console_handler)
    
    # File handlers
    
    # Main application log (rotating)
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "alphaalgo.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    app_handler.setLevel(numeric_level)
    app_handler.setFormatter(formatter)
    app_handler.addFilter(TradingLogFilter())
    root_logger.addHandler(app_handler)
    
    # Error log (separate file for errors)
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Trading events log (structured for analysis)
    trading_handler = logging.handlers.RotatingFileHandler(
        log_dir / "trading_events.log",
        maxBytes=20 * 1024 * 1024,  # 20MB
        backupCount=10
    )
    trading_handler.setLevel(logging.INFO)
    trading_handler.setFormatter(StructuredFormatter())
    
    # Only add trading events to this handler
    trading_logger = logging.getLogger("trading")
    trading_logger.addHandler(trading_handler)
    trading_logger.propagate = False  # Don't propagate to root
    
    # Performance log
    perf_handler = logging.handlers.RotatingFileHandler(
        log_dir / "performance.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(StructuredFormatter())
    
    perf_logger = logging.getLogger("trading.performance")
    perf_logger.addHandler(perf_handler)
    perf_logger.propagate = False
    
    # Set specific logger levels
    logging.getLogger("trading_bot").setLevel(numeric_level)
    logging.getLogger("trading").setLevel(logging.INFO)
    logging.getLogger("trading.performance").setLevel(logging.INFO)
    
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: level={level}, structured={structured}, dir={log_dir}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration."""
    return logging.getLogger(name)


def get_performance_logger() -> PerformanceLogger:
    """Get performance logger instance."""
    return PerformanceLogger()


class LogContext:
    """Context manager for adding context to log messages."""
    
    def __init__(self, **context):
        self.context = context
        self.old_factory = logging.getLogRecordFactory()
        
    def __enter__(self):
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            if not hasattr(record, 'extra_fields'):
                record.extra_fields = {}
            record.extra_fields.update(self.context)
            return record
            
        logging.setLogRecordFactory(record_factory)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


# Convenience function for trading context
def trading_context(**context):
    """Create logging context for trading operations."""
    return LogContext(**context)

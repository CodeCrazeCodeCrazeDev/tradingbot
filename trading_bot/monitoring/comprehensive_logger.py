"""
Comprehensive Logging and Monitoring System
===========================================
Centralized logging with structured output, metrics collection,
and real-time monitoring capabilities.
"""

import logging
import logging.handlers
import json
import sys
import os
import time
import asyncio
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque
import traceback
import uuid


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class LogLevel(Enum):
    """Log levels with numeric values."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    TRADE = 25  # Custom level for trade events
    SIGNAL = 22  # Custom level for signal events
    RISK = 35   # Custom level for risk events


class MetricType(Enum):
    """Types of metrics to collect."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: str
    logger_name: str
    message: str
    module: str
    function: str
    line: int
    extra: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    exception: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class Metric:
    """Metric data point."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags
        }


@dataclass
class Alert:
    """Alert notification."""
    alert_id: str
    severity: str
    title: str
    message: str
    timestamp: datetime
    source: str
    tags: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


# ============================================================================
# CUSTOM LOG FORMATTER
# ============================================================================

class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs."""
    
    def __init__(self, include_trace: bool = True):
        super().__init__()
        self.include_trace = include_trace
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line=record.lineno,
            extra=getattr(record, 'extra', {}),
            trace_id=getattr(record, 'trace_id', None),
            span_id=getattr(record, 'span_id', None),
        )
        
        if record.exc_info:
            entry.exception = self.formatException(record.exc_info)
        
        return entry.to_json()


class ColoredFormatter(logging.Formatter):
    """Formatter with colored output for console."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'TRADE': '\033[34m',     # Blue
        'SIGNAL': '\033[96m',    # Light Cyan
        'RISK': '\033[91m',      # Light Red
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors."""
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# ============================================================================
# METRICS COLLECTOR
# ============================================================================

class MetricsCollector:
    """Collects and aggregates metrics."""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._timers: Dict[str, List[float]] = {}
        self._history: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()
    
    def increment(self, name: str, value: float = 1, tags: Dict[str, str] = None):
        """Increment a counter."""
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] = self._counters.get(key, 0) + value
            self._record_metric(name, self._counters[key], MetricType.COUNTER, tags)
    
    def gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge value."""
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value
            self._record_metric(name, value, MetricType.GAUGE, tags)
    
    def histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value."""
        with self._lock:
            key = self._make_key(name, tags)
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
            # Keep only last 1000 values
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
            self._record_metric(name, value, MetricType.HISTOGRAM, tags)
    
    def timer(self, name: str, duration: float, tags: Dict[str, str] = None):
        """Record a timer value."""
        with self._lock:
            key = self._make_key(name, tags)
            if key not in self._timers:
                self._timers[key] = []
            self._timers[key].append(duration)
            if len(self._timers[key]) > 1000:
                self._timers[key] = self._timers[key][-1000:]
            self._record_metric(name, duration, MetricType.TIMER, tags)
    
    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create a unique key for a metric."""
        if tags:
            tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{name}:{tag_str}"
        return name
    
    def _record_metric(self, name: str, value: float, 
                       metric_type: MetricType, tags: Dict[str, str] = None):
        """Record metric to history."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        self._history.append(metric)
    
    def get_counter(self, name: str, tags: Dict[str, str] = None) -> float:
        """Get counter value."""
        key = self._make_key(name, tags)
        return self._counters.get(key, 0)
    
    def get_gauge(self, name: str, tags: Dict[str, str] = None) -> float:
        """Get gauge value."""
        key = self._make_key(name, tags)
        return self._gauges.get(key, 0)
    
    def get_histogram_stats(self, name: str, tags: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics."""
        import statistics
        key = self._make_key(name, tags)
        values = self._histograms.get(key, [])
        if not values:
            return {'count': 0, 'min': 0, 'max': 0, 'mean': 0, 'p50': 0, 'p95': 0, 'p99': 0}
        
        sorted_values = sorted(values)
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'p50': sorted_values[int(len(sorted_values) * 0.5)],
            'p95': sorted_values[int(len(sorted_values) * 0.95)],
            'p99': sorted_values[int(len(sorted_values) * 0.99)]
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        return {
            'counters': dict(self._counters),
            'gauges': dict(self._gauges),
            'histogram_stats': {k: self.get_histogram_stats(k) for k in self._histograms},
            'timer_stats': {k: self.get_histogram_stats(k) for k in self._timers}
        }


# ============================================================================
# COMPREHENSIVE LOGGER
# ============================================================================

class ComprehensiveLogger:
    """
    Comprehensive logging system with:
    - Structured JSON logging
    - Console output with colors
    - File rotation
    - Metrics collection
    - Alert management
    - Trace context propagation
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        log_dir: str = "logs",
        log_level: str = "INFO",
        enable_console: bool = True,
        enable_file: bool = True,
        enable_json: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 10,
        enable_metrics: bool = True
    ):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_json = enable_json
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        # Add custom log levels
        self._add_custom_levels()
        
        # Initialize metrics collector
        self.metrics = MetricsCollector() if enable_metrics else None
        
        # Alert storage
        self._alerts: List[Alert] = []
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        
        # Trace context
        self._trace_context = threading.local()
        
        # Configure root logger
        self._configure_logging()
        
        # Start background tasks
        self._running = True
        self._background_thread = threading.Thread(target=self._background_tasks, daemon=True)
        self._background_thread.start()
    
    def _add_custom_levels(self):
        """Add custom log levels."""
        logging.addLevelName(LogLevel.TRADE.value, 'TRADE')
        logging.addLevelName(LogLevel.SIGNAL.value, 'SIGNAL')
        logging.addLevelName(LogLevel.RISK.value, 'RISK')
    
    def _configure_logging(self):
        """Configure logging handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Remove existing handlers
        root_logger.handlers = []
        
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
            console_handler.setFormatter(ColoredFormatter(console_format))
            root_logger.addHandler(console_handler)
        
        # File handler (human readable)
        if self.enable_file:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / 'alphaalgo.log',
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            file_handler.setLevel(self.log_level)
            file_format = '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
            file_handler.setFormatter(logging.Formatter(file_format))
            root_logger.addHandler(file_handler)
        
        # JSON file handler
        if self.enable_json:
            json_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / 'alphaalgo.json',
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            json_handler.setLevel(self.log_level)
            json_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(json_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'errors.log',
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s:%(lineno)d\n%(message)s\n'
        ))
        root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance."""
        return logging.getLogger(name)
    
    def set_trace_context(self, trace_id: str = None, span_id: str = None):
        """Set trace context for current thread."""
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        if span_id is None:
            span_id = str(uuid.uuid4())[:8]
        
        self._trace_context.trace_id = trace_id
        self._trace_context.span_id = span_id
    
    def get_trace_context(self) -> Dict[str, str]:
        """Get current trace context."""
        return {
            'trace_id': getattr(self._trace_context, 'trace_id', None),
            'span_id': getattr(self._trace_context, 'span_id', None)
        }
    
    # ========================================================================
    # TRADE LOGGING
    # ========================================================================
    
    def log_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_id: str = None,
        profit: float = None,
        **extra
    ):
        """Log a trade event."""
        logger = self.get_logger('trading.trades')
        
        message = f"TRADE: {side} {quantity} {symbol} @ {price}"
        if profit is not None:
            message += f" | P/L: {profit:.2f}"
        
        extra_data = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'order_id': order_id,
            'profit': profit,
            **extra
        }
        
        logger.log(LogLevel.TRADE.value, message, extra={'extra': extra_data})
        
        # Record metrics
        if self.metrics:
            self.metrics.increment('trades_total', tags={'symbol': symbol, 'side': side})
            if profit is not None:
                self.metrics.histogram('trade_profit', profit, tags={'symbol': symbol})
    
    def log_signal(
        self,
        symbol: str,
        direction: str,
        confidence: float,
        source: str,
        **extra
    ):
        """Log a signal event."""
        logger = self.get_logger('trading.signals')
        
        message = f"SIGNAL: {direction} {symbol} | Confidence: {confidence:.2%} | Source: {source}"
        
        extra_data = {
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'source': source,
            **extra
        }
        
        logger.log(LogLevel.SIGNAL.value, message, extra={'extra': extra_data})
        
        # Record metrics
        if self.metrics:
            self.metrics.increment('signals_total', tags={'symbol': symbol, 'source': source})
            self.metrics.histogram('signal_confidence', confidence, tags={'source': source})
    
    def log_risk_event(
        self,
        event_type: str,
        message: str,
        severity: str = "WARNING",
        **extra
    ):
        """Log a risk event."""
        logger = self.get_logger('trading.risk')
        
        full_message = f"RISK [{event_type}]: {message}"
        
        extra_data = {
            'event_type': event_type,
            'severity': severity,
            **extra
        }
        
        logger.log(LogLevel.RISK.value, full_message, extra={'extra': extra_data})
        
        # Record metrics
        if self.metrics:
            self.metrics.increment('risk_events', tags={'type': event_type, 'severity': severity})
    
    # ========================================================================
    # PERFORMANCE LOGGING
    # ========================================================================
    
    def log_latency(self, operation: str, duration: float, **tags):
        """Log operation latency."""
        logger = self.get_logger('performance.latency')
        logger.debug(f"Latency: {operation} = {duration*1000:.2f}ms")
        
        if self.metrics:
            self.metrics.timer(f'latency_{operation}', duration, tags)
    
    def log_throughput(self, operation: str, count: int, duration: float, **tags):
        """Log operation throughput."""
        logger = self.get_logger('performance.throughput')
        rate = count / duration if duration > 0 else 0
        logger.debug(f"Throughput: {operation} = {rate:.2f}/s")
        
        if self.metrics:
            self.metrics.gauge(f'throughput_{operation}', rate, tags)
    
    # ========================================================================
    # ALERTING
    # ========================================================================
    
    def create_alert(
        self,
        severity: str,
        title: str,
        message: str,
        source: str,
        **tags
    ) -> Alert:
        """Create and store an alert."""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source,
            tags=tags
        )
        
        self._alerts.append(alert)
        
        # Log the alert
        logger = self.get_logger('alerts')
        log_level = {
            'CRITICAL': logging.CRITICAL,
            'ERROR': logging.ERROR,
            'WARNING': logging.WARNING,
            'INFO': logging.INFO
        }.get(severity.upper(), logging.WARNING)
        
        logger.log(log_level, f"ALERT [{severity}] {title}: {message}")
        
        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logging.error(f"Alert callback error: {e}")
        
        return alert
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                break
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [a for a in self._alerts if not a.resolved]
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add callback for new alerts."""
        self._alert_callbacks.append(callback)
    
    # ========================================================================
    # BACKGROUND TASKS
    # ========================================================================
    
    def _background_tasks(self):
        """Run background maintenance tasks."""
        while self._running:
            try:
                # Clean up old alerts (keep last 1000)
                if len(self._alerts) > 1000:
                    self._alerts = self._alerts[-1000:]
                
                # Flush metrics periodically
                if self.metrics:
                    self._flush_metrics()
                
            except Exception as e:
                logging.error(f"Background task error: {e}")
            
            time.sleep(60)  # Run every minute
    
    def _flush_metrics(self):
        """Flush metrics to file."""
        try:
            metrics_file = self.log_dir / 'metrics.json'
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics.get_all_metrics(), f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Failed to flush metrics: {e}")
    
    def shutdown(self):
        """Shutdown the logger."""
        self._running = False
        if self._background_thread.is_alive():
            self._background_thread.join(timeout=5)
        
        # Final metrics flush
        if self.metrics:
            self._flush_metrics()
        
        logging.shutdown()


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

class TimedOperation:
    """Context manager for timing operations."""
    
    def __init__(self, logger: ComprehensiveLogger, operation: str, **tags):
        self.logger = logger
        self.operation = operation
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        self.logger.log_latency(self.operation, duration, **self.tags)
        return False


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_logger_instance: Optional[ComprehensiveLogger] = None


def get_logger() -> ComprehensiveLogger:
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ComprehensiveLogger()
    return _logger_instance


def configure_logging(**kwargs) -> ComprehensiveLogger:
    """Configure and get the global logger."""
    global _logger_instance
    _logger_instance = ComprehensiveLogger(**kwargs)
    return _logger_instance

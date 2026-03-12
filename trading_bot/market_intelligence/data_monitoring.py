import logging
from collections import defaultdict
logger = logging.getLogger(__name__)
from datetime import timedelta
"""Real-Time Data Monitoring components for the Market Intelligence System.

This module provides classes for monitoring various types of market data:
- Market data streams (price, volume, order book, etc.)
- Economic indicators
- News and sentiment analysis
"""

# Standard library imports
import datetime
import sys
import threading
import time
import traceback
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# Third-party imports
import numpy as np
import pandas as pd
import psutil
from loguru import logger

from trading_bot.data import MT5Interface
from typing import Set
import numpy
import pandas


class DebugLevel(Enum):
    """Debug severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DebugEvent:
    """Debug event data structure."""
    timestamp: datetime.datetime
    level: DebugLevel
    component: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    performance_metrics: Optional[Dict[str, float]] = None


class SelfDebugger:
    """Comprehensive self-debugging system for data monitoring components."""
    
    def __init__(self, max_events: int = 1000, enable_performance_monitoring: bool = True):
        """Initialize the self-debugger.
        
        Args:
            max_events: Maximum number of debug events to store
            enable_performance_monitoring: Whether to enable performance monitoring
        """
        self.max_events = max_events
        self.enable_performance_monitoring = enable_performance_monitoring
        
        # Debug event storage
        self.debug_events = deque(maxlen=max_events)
        
        # Performance metrics
        self.performance_metrics = {
            'cpu_usage': deque(maxlen=100),
            'memory_usage': deque(maxlen=100),
            'execution_times': {},
            'error_counts': {},
            'data_quality_metrics': {}
        }
        
        # System health indicators
        self.health_status = {
            'overall_health': 'healthy',
            'component_health': {},
            'last_health_check': None,
            'alerts': []
        }
        
        # Monitoring flags
        self.is_monitoring = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        logger.info("Initialized SelfDebugger with comprehensive monitoring capabilities")
    
    def log_event(self, level: DebugLevel, component: str, message: str, 
                  details: Dict[str, Any] = None, include_stack: bool = False):
        """Log a debug event.
        
        Args:
            level: Debug level
            component: Component name
            message: Debug message
            details: Additional details
            include_stack: Whether to include stack trace
        """
        event = DebugEvent(
            timestamp=datetime.datetime.now(),
            level=level,
            component=component,
            message=message,
            details=details or {},
            stack_trace=traceback.format_stack() if include_stack else None
        )
        
        # Add performance metrics if enabled
        if self.enable_performance_monitoring:
            event.performance_metrics = self._get_current_performance_metrics()
        
        self.debug_events.append(event)
        
        # Log to standard logger as well
        log_msg = f"[{component}] {message}"
        if details:
            log_msg += f" | Details: {details}"
        
        if level == DebugLevel.INFO:
            logger.info(log_msg)
        elif level == DebugLevel.WARNING:
            logger.warning(log_msg)
        elif level == DebugLevel.ERROR:
            logger.error(log_msg)
        elif level == DebugLevel.CRITICAL:
            logger.critical(log_msg)
        
        # Update error counts
        if level in [DebugLevel.ERROR, DebugLevel.CRITICAL]:
            self.performance_metrics['error_counts'][component] = \
                self.performance_metrics['error_counts'].get(component, 0) + 1
    
    def monitor_execution_time(self, component: str, function_name: str):
        """Decorator to monitor execution time of functions.
        
        Args:
            component: Component name
            function_name: Function name
            
        Returns:
            Decorator function that wraps the target function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                """Wrapper function that monitors execution time.
                
                Args:
                    *args: Arguments to pass to the wrapped function
                    **kwargs: Keyword arguments to pass to the wrapped function
                    
                Returns:
                    Result of the wrapped function
                """
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Store execution time with thread safety
                    key = f"{component}.{function_name}"
                    try:
                        if key not in self.performance_metrics['execution_times']:
                            self.performance_metrics['execution_times'][key] = deque(maxlen=100)
                        
                        self.performance_metrics['execution_times'][key].append(execution_time)
                    except Exception as e:
                        logger.warning(f"Failed to store execution time: {str(e)}")
                    
                    # Log slow executions
                    if execution_time > 5.0:  # 5 seconds threshold
                        self.log_event(
                            DebugLevel.WARNING,
                            component,
                            f"Slow execution detected in {function_name}",
                            {'execution_time': execution_time, 'threshold': 5.0}
                        )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.log_event(
                        DebugLevel.ERROR,
                        component,
                        f"Exception in {function_name}: {str(e)}",
                        {
                            'exception_type': type(e).__name__,
                            'execution_time': execution_time,
                            'args': str(args)[:200],
                            'kwargs': str(kwargs)[:200]
                        },
                        include_stack=True
                    )
                    raise
            return wrapper
        return decorator
    
    def _get_current_performance_metrics(self) -> Dict[str, float]:
        """Get current system performance metrics.
        
        Returns:
            Dictionary with performance metrics or empty dict on error
        """
        try:
            # CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            try:
                # Store for trending with thread safety
                self.performance_metrics['cpu_usage'].append(cpu_percent)
                self.performance_metrics['memory_usage'].append(memory.percent)
            except Exception as e:
                logger.debug(f"Failed to store trending metrics: {str(e)}")
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'thread_count': threading.active_count(),
                'process_memory_mb': psutil.Process().memory_info().rss / (1024**2)
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    def start_health_monitoring(self, check_interval: float = 30.0):
        """Start continuous health monitoring.
        
        Args:
            check_interval: Time between health checks in seconds
        """
        if self.is_monitoring:
            logger.warning("Health monitoring is already running")
            return
        
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(
            target=self._health_monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.is_monitoring = True
        
        logger.info(f"Started health monitoring with {check_interval}s interval")
    
    def stop_health_monitoring(self):
        """Stop health monitoring."""
        if not self.is_monitoring:
            return
        
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        self.is_monitoring = False
        logger.info("Stopped health monitoring")
    
    def _health_monitoring_loop(self, check_interval: float):
        """Main health monitoring loop."""
        while not self.stop_event.is_set():
            try:
                self._perform_health_check()
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(check_interval * 2)
    
    def _perform_health_check(self):
        """Perform comprehensive health check."""
        try:
            current_time = datetime.datetime.now()
            alerts = []
            
            # Check system resources
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            if cpu_usage > 80:
                alerts.append({
                    'type': 'high_cpu',
                    'message': f'High CPU usage: {cpu_usage:.1f}%',
                    'severity': 'warning' if cpu_usage < 90 else 'critical'
                })
            
            if memory.percent > 85:
                alerts.append({
                    'type': 'high_memory',
                    'message': f'High memory usage: {memory.percent:.1f}%',
                    'severity': 'warning' if memory.percent < 95 else 'critical'
                })
            
            # Check error rates
            recent_errors = [
                event for event in self.debug_events
                if event.level in [DebugLevel.ERROR, DebugLevel.CRITICAL]
                and (current_time - event.timestamp).total_seconds() < 300  # Last 5 minutes
            ]
            
            if len(recent_errors) > 10:
                alerts.append({
                    'type': 'high_error_rate',
                    'message': f'High error rate: {len(recent_errors)} errors in last 5 minutes',
                    'severity': 'critical'
                })
            
            # Check data quality
            self._check_data_quality(alerts)
            
            # Update health status
            if any(alert['severity'] == 'critical' for alert in alerts):
                self.health_status['overall_health'] = 'critical'
            elif any(alert['severity'] == 'warning' for alert in alerts):
                self.health_status['overall_health'] = 'warning'
            else:
                self.health_status['overall_health'] = 'healthy'
            
            self.health_status['alerts'] = alerts
            self.health_status['last_health_check'] = current_time
            
            # Log health status
            if alerts:
                self.log_event(
                    DebugLevel.WARNING if self.health_status['overall_health'] == 'warning' else DebugLevel.CRITICAL,
                    'HealthMonitor',
                    f"Health check completed with {len(alerts)} alerts",
                    {'alerts': alerts, 'overall_health': self.health_status['overall_health']}
                )
            
        except Exception as e:
            self.log_event(
                DebugLevel.ERROR,
                'HealthMonitor',
                f"Error performing health check: {str(e)}",
                include_stack=True
            )
    
    def _check_data_quality(self, alerts: List[Dict]):
        """Check data quality metrics.
        
        Args:
            alerts: List to append alerts to
        """
        try:
            # This would be implemented based on specific data quality requirements
            # For now, we'll add placeholder checks
            
            # Check for data staleness
            current_time = datetime.datetime.now()
            
            try:
                # Make a thread-safe copy of debug events
                # Use a list comprehension with a safe copy to avoid race conditions
                debug_events_copy = list(self.debug_events)
                
                # Example: Check if we have recent data updates
                recent_data_events = [
                    event for event in debug_events_copy
                    if event.message and 'data_update' in event.message.lower()
                    and (current_time - event.timestamp).total_seconds() < 120  # Last 2 minutes
                ]
                
                if len(recent_data_events) == 0:
                    alerts.append({
                        'type': 'stale_data',
                        'message': 'No recent data updates detected',
                        'severity': 'warning'
                    })
            except Exception as e:
                logger.warning(f"Error during data events processing: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error checking data quality: {e}")
    
    def get_debug_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get debug summary for the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with debug summary information
            
        Returns:
            Dictionary with debug summary
        """
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
        recent_events = [
            event for event in self.debug_events
            if event.timestamp >= cutoff_time
        ]
        
        # Count events by level
        level_counts = {}
        for level in DebugLevel:
            level_counts[level.value] = sum(1 for event in recent_events if event.level == level)
        
        # Count events by component
        component_counts = {}
        for event in recent_events:
            component_counts[event.component] = component_counts.get(event.component, 0) + 1
        
        # Get performance statistics
        performance_stats = {}
        if self.performance_metrics['cpu_usage']:
            performance_stats['avg_cpu_usage'] = sum(self.performance_metrics['cpu_usage']) / len(self.performance_metrics['cpu_usage'])
            performance_stats['max_cpu_usage'] = max(self.performance_metrics['cpu_usage'])
        
        if self.performance_metrics['memory_usage']:
            performance_stats['avg_memory_usage'] = sum(self.performance_metrics['memory_usage']) / len(self.performance_metrics['memory_usage'])
            performance_stats['max_memory_usage'] = max(self.performance_metrics['memory_usage'])
        
        # Get execution time statistics
        execution_stats = {}
        for func_name, times in self.performance_metrics['execution_times'].items():
            if times:
                execution_stats[func_name] = {
                    'avg_time': sum(times) / len(times),
                    'max_time': max(times),
                    'min_time': min(times),
                    'call_count': len(times)
                }
        
        return {
            'time_period_hours': hours,
            'total_events': len(recent_events),
            'events_by_level': level_counts,
            'events_by_component': component_counts,
            'performance_stats': performance_stats,
            'execution_stats': execution_stats,
            'error_counts': dict(self.performance_metrics['error_counts']),
            'health_status': self.health_status,
            'generated_at': datetime.datetime.now()
        }
    
    def get_recent_errors(self, count: int = 10) -> List[DebugEvent]:
        """Get recent error and critical events.
        
        Args:
            count: Maximum number of errors to return
            
        Returns:
            List of recent error events
        """
        try:
            # Make a thread-safe copy of debug events
            debug_events_copy = list(self.debug_events)
            
            error_events = [
                event for event in debug_events_copy
                if event.level in [DebugLevel.ERROR, DebugLevel.CRITICAL]
            ]
            
            # Sort by timestamp (most recent first)
            error_events.sort(key=lambda x: x.timestamp, reverse=True)
            
            return error_events[:count]
        except Exception as e:
            logger.error(f"Error getting recent errors: {str(e)}")
            return []
    
    def diagnose_performance_issues(self) -> Dict[str, List[str]]:
        """Diagnose performance issues based on collected metrics.
        
        Returns:
            Dictionary with performance diagnosis
        """
        diagnosis = {
            'cpu_issues': [],
            'memory_issues': [],
            'execution_issues': [],
            'error_rate_issues': [],
            'recommendations': [],
            'slow_functions': []
        }
        
        try:
            # Check CPU usage trends
            cpu_data = list(self.performance_metrics['cpu_usage'])
            if cpu_data and len(cpu_data) > 0:
                avg_cpu = sum(cpu_data) / len(cpu_data)
                max_cpu = max(cpu_data)
                
                if avg_cpu > 70:
                    diagnosis['cpu_issues'].append(f"High average CPU usage: {avg_cpu:.1f}%")
                    diagnosis['recommendations'].append("Consider optimizing CPU-intensive operations")
                
                if max_cpu > 90:
                    diagnosis['cpu_issues'].append(f"CPU usage spikes detected: {max_cpu:.1f}%")
                    diagnosis['recommendations'].append("Investigate CPU usage spikes")
            
            # Check memory usage trends
            memory_data = list(self.performance_metrics['memory_usage'])
            if memory_data and len(memory_data) > 0:
                avg_memory = sum(memory_data) / len(memory_data)
                max_memory = max(memory_data)
                
                if avg_memory > 80:
                    diagnosis['memory_issues'].append(f"High average memory usage: {avg_memory:.1f}%")
                    diagnosis['recommendations'].append("Consider memory optimization")
                
                if max_memory > 95:
                    diagnosis['memory_issues'].append(f"Memory usage spikes detected: {max_memory:.1f}%")
                    diagnosis['recommendations'].append("Investigate memory leaks")
            
            # Check execution times
            slow_functions = []
            for func_name, times in self.performance_metrics['execution_times'].items():
                times_list = list(times) if times else []
                if times_list and len(times_list) > 0:
                    avg_time = sum(times_list) / len(times_list)
                    max_time = max(times_list)
                    
                    if avg_time > 2.0:  # 2 seconds threshold
                        slow_functions.append({
                            'function': func_name,
                            'avg_time': avg_time,
                            'max_time': max_time
                        })
            
            if slow_functions:
                diagnosis['execution_issues'].append(f"Slow functions detected: {len(slow_functions)}")
                diagnosis['recommendations'].append("Optimize slow-running functions")
                diagnosis['slow_functions'] = slow_functions
            
            # Check error rates
            try:
                total_errors = sum(self.performance_metrics['error_counts'].values())
                if total_errors > 50:  # Arbitrary threshold
                    diagnosis['error_rate_issues'].append(f"High error count: {total_errors}")
                    diagnosis['recommendations'].append("Investigate and fix recurring errors")
            except (KeyError, TypeError):
                # Handle case where error_counts doesn't exist or isn't iterable
                pass
            
        except Exception as e:
            logger.error(f"Error diagnosing performance issues: {e}")
        
        return diagnosis


class MarketDataMonitor:
    """Monitor real-time market data across multiple timeframes."""
    
    def __init__(self, mt5_interface: Optional[MT5Interface] = None, 
                 symbols: List[str] = None, 
                 timeframes: List[str] = None,
                 max_history: int = 1000,
                 enable_debugging: bool = True):
        """Initialize the market data monitor.
        
        Args:
            mt5_interface: MT5 interface for data retrieval
            symbols: List of symbols to monitor
            timeframes: List of timeframes to monitor
            max_history: Maximum number of data points to store per symbol/timeframe
            enable_debugging: Whether to enable self-debugging capabilities
        """
        self.mt5 = mt5_interface or MT5Interface()
        self.symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
        self.timeframes = timeframes or ["M1", "M5", "M15", "H1", "H4", "D1"]
        self.max_history = max_history
        
        # Initialize self-debugger
        self.debugger = SelfDebugger(enable_performance_monitoring=enable_debugging) if enable_debugging else None
        
        # Data storage: symbol -> timeframe -> deque of data
        self.price_data = {}
        self.volume_data = {}
        self.order_book_data = {}
        
        # Initialize data structures
        self._initialize_data_structures()
        
        # Monitoring flags and threads
        self.is_monitoring = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # Data quality metrics
        self.data_quality_metrics = {
            'total_updates': 0,
            'failed_updates': 0,
            'last_successful_update': None,
            'symbols_with_issues': set(),
            'connection_issues': 0
        }
        
        if self.debugger:
            self.debugger.log_event(
                DebugLevel.INFO,
                'MarketDataMonitor',
                f"Initialized with {len(self.symbols)} symbols and {len(self.timeframes)} timeframes",
                {'symbols': self.symbols, 'timeframes': self.timeframes, 'max_history': max_history}
            )
        
        logger.info(f"Initialized MarketDataMonitor with {len(self.symbols)} symbols and {len(self.timeframes)} timeframes")
    
    def _initialize_data_structures(self):
        """Initialize data storage structures."""
        for symbol in self.symbols:
            self.price_data[symbol] = {}
            self.volume_data[symbol] = {}
            self.order_book_data[symbol] = {}
            
            for timeframe in self.timeframes:
                self.price_data[symbol][timeframe] = deque(maxlen=self.max_history)
                self.volume_data[symbol][timeframe] = deque(maxlen=self.max_history)
            
            # Order book is not timeframe-specific
            self.order_book_data[symbol] = deque(maxlen=self.max_history)
    
    def start_monitoring(self, update_interval: float = 1.0):
        """Start monitoring market data.
        
        Args:
            update_interval: Time between updates in seconds
        """
        if self.is_monitoring:
            if self.debugger:
                self.debugger.log_event(
                    DebugLevel.WARNING,
                    'MarketDataMonitor',
                    "Attempted to start monitoring when already running"
                )
            logger.warning("Market data monitoring is already running")
            return
        
        # Reset stop event
        self.stop_event.clear()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(update_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.is_monitoring = True
        
        if self.debugger:
            self.debugger.log_event(
                DebugLevel.INFO,
                'MarketDataMonitor',
                f"Started monitoring with {update_interval}s interval",
                {'update_interval': update_interval, 'thread_id': self.monitor_thread.ident}
            )
            # Start health monitoring for the debugger
            self.debugger.start_health_monitoring()
        
        logger.info(f"Started market data monitoring with {update_interval}s interval")
    
    def stop_monitoring(self):
        """Stop monitoring market data."""
        if not self.is_monitoring:
            logger.warning("Market data monitoring is not running")
            return
        
        # Set stop event
        self.stop_event.set()
        
        # Wait for thread to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
            
            if self.monitor_thread.is_alive():
                logger.warning("Market data monitoring thread did not stop gracefully")
            else:
                logger.info("Stopped market data monitoring")
        
        self.is_monitoring = False
    
    @property
    def monitoring_loop_decorated(self):
        """Get decorated monitoring loop with performance monitoring."""
        if self.debugger:
            return self.debugger.monitor_execution_time('MarketDataMonitor', '_monitoring_loop')(self._monitoring_loop_impl)
        return self._monitoring_loop_impl
    
    def _monitoring_loop(self, update_interval: float):
        """Main monitoring loop wrapper."""
        return self.monitoring_loop_decorated(update_interval)
    
    def _monitoring_loop_impl(self, update_interval: float):
        """Main monitoring loop implementation.
        
        Args:
            update_interval: Time between updates in seconds
        """
        if self.debugger:
            self.debugger.log_event(
                DebugLevel.INFO,
                'MarketDataMonitor',
                "Market data monitoring loop started",
                {'update_interval': update_interval}
            )
        
        logger.info("Market data monitoring loop started")
        
        while not self.stop_event.is_set():
            try:
                # Update price and volume data
                self._update_price_and_volume()
                
                # Update order book data
                self._update_order_book()
                
                # Update data quality metrics
                self.data_quality_metrics['total_updates'] += 1
                self.data_quality_metrics['last_successful_update'] = datetime.datetime.now()
                
                if self.debugger:
                    self.debugger.log_event(
                        DebugLevel.INFO,
                        'MarketDataMonitor',
                        "Completed data update cycle",
                        {
                            'total_updates': self.data_quality_metrics['total_updates'],
                            'symbols_count': len(self.symbols),
                            'timeframes_count': len(self.timeframes)
                        }
                    )
                
                # Wait for next update
                time.sleep(update_interval)
                
            except Exception as e:
                self.data_quality_metrics['failed_updates'] += 1
                
                if self.debugger:
                    self.debugger.log_event(
                        DebugLevel.ERROR,
                        'MarketDataMonitor',
                        f"Error in monitoring loop: {str(e)}",
                        {
                            'exception_type': type(e).__name__,
                            'failed_updates': self.data_quality_metrics['failed_updates'],
                            'total_updates': self.data_quality_metrics['total_updates']
                        },
                        include_stack=True
                    )
                
                logger.error(f"Error in market data monitoring loop: {e}")
                time.sleep(update_interval * 2)  # Wait longer on error
    
    def _update_price_and_volume(self):
        """Update price and volume data for all symbols and timeframes."""
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                try:
                    # Get latest data from MT5
                    df = self.mt5.get_ohlc(symbol, timeframe, 10)  # Get last 10 candles
                    
                    if df is not None and not df.empty:
                        new_data_count = 0
                        # Add new data to price and volume deques
                        for _, row in df.iterrows():
                            # Check if this is new data
                            if (len(self.price_data[symbol][timeframe]) == 0 or 
                                row.name > self.price_data[symbol][timeframe][-1]['timestamp']):
                                
                                price_data = {
                                    'timestamp': row.name,
                                    'open': row['open'],
                                    'high': row['high'],
                                    'low': row['low'],
                                    'close': row['close']
                                }
                                
                                volume_data = {
                                    'timestamp': row.name,
                                    'volume': row['tick_volume'],
                                    'real_volume': row.get('real_volume', row['tick_volume'])
                                }
                                
                                self.price_data[symbol][timeframe].append(price_data)
                                self.volume_data[symbol][timeframe].append(volume_data)
                                new_data_count += 1
                        
                        if self.debugger and new_data_count > 0:
                            self.debugger.log_event(
                                DebugLevel.INFO,
                                'MarketDataMonitor',
                                f"Updated price and volume data for {symbol} {timeframe}",
                                {
                                    'symbol': symbol,
                                    'timeframe': timeframe,
                                    'new_data_points': new_data_count,
                                    'total_data_points': len(self.price_data[symbol][timeframe])
                                }
                            )
                        
                        logger.debug(f"Updated price and volume data for {symbol} {timeframe}")
                    else:
                        # No data received - potential connection issue
                        if self.debugger:
                            self.debugger.log_event(
                                DebugLevel.WARNING,
                                'MarketDataMonitor',
                                f"No data received for {symbol} {timeframe}",
                                {'symbol': symbol, 'timeframe': timeframe}
                            )
                        
                        self.data_quality_metrics['symbols_with_issues'].add(symbol)
                    
                except Exception as e:
                    self.data_quality_metrics['connection_issues'] += 1
                    self.data_quality_metrics['symbols_with_issues'].add(symbol)
                    
                    if self.debugger:
                        self.debugger.log_event(
                            DebugLevel.ERROR,
                            'MarketDataMonitor',
                            f"Error updating price and volume data for {symbol} {timeframe}: {str(e)}",
                            {
                                'symbol': symbol,
                                'timeframe': timeframe,
                                'exception_type': type(e).__name__,
                                'connection_issues': self.data_quality_metrics['connection_issues']
                            },
                            include_stack=True
                        )
                    
                    logger.error(f"Error updating price and volume data for {symbol} {timeframe}: {e}")
    
    def _update_order_book(self):
        """Update order book data for all symbols."""
        for symbol in self.symbols:
            try:
                # Get order book data from MT5
                order_book = self.mt5.get_order_book(symbol)
                
                if order_book is not None:
                    # Process order book data
                    processed_data = {
                        'timestamp': datetime.datetime.now(),
                        'bids': order_book.get('bids', []),
                        'asks': order_book.get('asks', []),
                        'bid_volume': sum(bid[1] for bid in order_book.get('bids', [])),
                        'ask_volume': sum(ask[1] for ask in order_book.get('asks', [])),
                        'spread': order_book.get('spread', 0)
                    }
                    
                    # Add to order book deque
                    self.order_book_data[symbol].append(processed_data)
                    
                    logger.debug(f"Updated order book data for {symbol}")
                
            except Exception as e:
                logger.error(f"Error updating order book data for {symbol}: {e}")
    
    def detect_volume_spikes(self, symbol: str, timeframe: str, 
                            threshold: float = 2.0, lookback: int = 20) -> List[Dict]:
        """Detect unusual volume spikes.
        
        Args:
            symbol: Symbol to check
            timeframe: Timeframe to check
            threshold: Volume threshold as multiple of average volume
            lookback: Number of periods to look back for average calculation
            
        Returns:
            List of volume spike events
        """
        if symbol not in self.volume_data or timeframe not in self.volume_data[symbol]:
            return []
        
        volume_data = list(self.volume_data[symbol][timeframe])
        if len(volume_data) < lookback:
            return []
        
        # Calculate average volume
        recent_volumes = [v['volume'] for v in volume_data[-lookback:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        
        # Detect spikes
        spikes = []
        for _, data in enumerate(volume_data[-lookback:]):
            if data['volume'] > avg_volume * threshold:
                spikes.append({
                    'timestamp': data['timestamp'],
                    'volume': data['volume'],
                    'avg_volume': avg_volume,
                    'ratio': data['volume'] / avg_volume
                })
        
        return spikes
    
    def detect_order_book_imbalances(self, symbol: str, threshold: float = 2.0) -> List[Dict]:
        """Detect significant order book imbalances.
        
        Args:
            symbol: Symbol to check
            threshold: Imbalance threshold as bid/ask ratio
            
        Returns:
            List of order book imbalance events
        """
        if symbol not in self.order_book_data:
            return []
        
        order_book_data = list(self.order_book_data[symbol])
        if not order_book_data:
            return []
        
        # Detect imbalances
        imbalances = []
        for data in order_book_data:
            bid_volume = data['bid_volume']
            ask_volume = data['ask_volume']
            
            if bid_volume > 0 and ask_volume > 0:
                ratio = bid_volume / ask_volume
                
                if ratio > threshold or ratio < 1/threshold:
                    imbalances.append({
                        'timestamp': data['timestamp'],
                        'bid_volume': bid_volume,
                        'ask_volume': ask_volume,
                        'ratio': ratio,
                        'imbalance_direction': 'buy' if ratio > threshold else 'sell'
                    })
        
        return imbalances
    
    def get_price_action_summary(self, symbol: str, timeframe: str, lookback: int = 10) -> Dict:
        """Get a summary of recent price action.
        
        Args:
            symbol: Symbol to check
            timeframe: Timeframe to check
            lookback: Number of periods to look back
            
        Returns:
            Dictionary with price action summary
        """
        if symbol not in self.price_data or timeframe not in self.price_data[symbol]:
            return {}
        
        price_data = list(self.price_data[symbol][timeframe])
        if len(price_data) < lookback:
            return {}
        
        # Get recent price data
        recent_data = price_data[-lookback:]
        
        # Calculate price change
        start_price = recent_data[0]['close']
        end_price = recent_data[-1]['close']
        price_change = end_price - start_price
        price_change_pct = (price_change / start_price) * 100
        
        # Calculate high and low
        high = max(data['high'] for data in recent_data)
        low = min(data['low'] for data in recent_data)
        
        # Calculate average range
        ranges = [data['high'] - data['low'] for data in recent_data]
        avg_range = sum(ranges) / len(ranges)
        
        # Determine trend
        if price_change_pct > 0.5:
            trend = "bullish"
        elif price_change_pct < -0.5:
            trend = "bearish"
        else:
            trend = "sideways"
        
        summary = {
            'symbol': symbol,
            'timeframe': timeframe,
            'start_time': recent_data[0]['timestamp'],
            'end_time': recent_data[-1]['timestamp'],
            'start_price': start_price,
            'end_price': end_price,
            'high': high,
            'low': low,
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'avg_range': avg_range,
            'trend': trend
        }
        
        if self.debugger:
            self.debugger.log_event(
                DebugLevel.INFO,
                'MarketDataMonitor',
                f"Generated price action summary for {symbol} {timeframe}",
                {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'trend': trend,
                    'price_change_pct': price_change_pct,
                    'lookback': lookback
                }
            )
        
        return summary
    
    def get_debug_status(self) -> Dict[str, Any]:
        """Get comprehensive debug status for the monitor.
        
        Returns:
            Dictionary with debug status information
        """
        if not self.debugger:
            return {'debugging_enabled': False}
        
        # Get debug summary
        debug_summary = self.debugger.get_debug_summary(hours=1)
        
        # Get recent errors
        recent_errors = self.debugger.get_recent_errors(count=5)
        
        # Get performance diagnosis
        performance_diagnosis = self.debugger.diagnose_performance_issues()
        
        # Calculate data quality score
        total_updates = self.data_quality_metrics['total_updates']
        failed_updates = self.data_quality_metrics['failed_updates']
        success_rate = ((total_updates - failed_updates) / total_updates * 100) if total_updates > 0 else 0
        
        return {
            'debugging_enabled': True,
            'monitor_status': {
                'is_monitoring': self.is_monitoring,
                'symbols_count': len(self.symbols),
                'timeframes_count': len(self.timeframes),
                'thread_active': self.monitor_thread.is_alive() if self.monitor_thread else False
            },
            'data_quality': {
                'total_updates': total_updates,
                'failed_updates': failed_updates,
                'success_rate': success_rate,
                'connection_issues': self.data_quality_metrics['connection_issues'],
                'symbols_with_issues': list(self.data_quality_metrics['symbols_with_issues']),
                'last_successful_update': self.data_quality_metrics['last_successful_update']
            },
            'debug_summary': debug_summary,
            'recent_errors': [
                {
                    'timestamp': error.timestamp,
                    'level': error.level.value,
                    'component': error.component,
                    'message': error.message,
                    'details': error.details
                } for error in recent_errors
            ],
            'performance_diagnosis': performance_diagnosis,
            'health_status': self.debugger.health_status
        }
    
    def run_diagnostic_check(self) -> Dict[str, Any]:
        """Run comprehensive diagnostic check.
        
        Returns:
            Dictionary with diagnostic results
        """
        if not self.debugger:
            return {'error': 'Debugging not enabled'}
        
        diagnostic_results = {
            'timestamp': datetime.datetime.now(),
            'checks_performed': [],
            'issues_found': [],
            'recommendations': []
        }
        
        try:
            # Check 1: Data freshness
            diagnostic_results['checks_performed'].append('data_freshness')
            current_time = datetime.datetime.now()
            
            if self.data_quality_metrics['last_successful_update']:
                time_since_update = (current_time - self.data_quality_metrics['last_successful_update']).total_seconds()
                if time_since_update > 300:  # 5 minutes
                    diagnostic_results['issues_found'].append({
                        'type': 'stale_data',
                        'severity': 'warning',
                        'message': f'Data not updated for {time_since_update:.0f} seconds',
                        'recommendation': 'Check MT5 connection and data feed'
                    })
            
            # Check 2: Error rates
            diagnostic_results['checks_performed'].append('error_rates')
            total_updates = self.data_quality_metrics['total_updates']
            failed_updates = self.data_quality_metrics['failed_updates']
            
            if total_updates > 0:
                error_rate = (failed_updates / total_updates) * 100
                if error_rate > 10:  # 10% error rate threshold
                    diagnostic_results['issues_found'].append({
                        'type': 'high_error_rate',
                        'severity': 'critical' if error_rate > 25 else 'warning',
                        'message': f'High error rate: {error_rate:.1f}%',
                        'recommendation': 'Investigate connection stability and error patterns'
                    })
            
            # Check 3: Symbol coverage
            diagnostic_results['checks_performed'].append('symbol_coverage')
            problematic_symbols = len(self.data_quality_metrics['symbols_with_issues'])
            total_symbols = len(self.symbols)
            
            if problematic_symbols > 0:
                coverage_rate = ((total_symbols - problematic_symbols) / total_symbols) * 100
                if coverage_rate < 80:  # 80% coverage threshold
                    diagnostic_results['issues_found'].append({
                        'type': 'poor_symbol_coverage',
                        'severity': 'warning',
                        'message': f'Only {coverage_rate:.1f}% symbol coverage',
                        'recommendation': 'Check specific symbol data feeds'
                    })
            
            # Check 4: Memory usage
            diagnostic_results['checks_performed'].append('memory_usage')
            if self.debugger.performance_metrics['memory_usage']:
                current_memory = self.debugger.performance_metrics['memory_usage'][-1]
                if current_memory > 85:
                    diagnostic_results['issues_found'].append({
                        'type': 'high_memory_usage',
                        'severity': 'critical' if current_memory > 95 else 'warning',
                        'message': f'High memory usage: {current_memory:.1f}%',
                        'recommendation': 'Consider reducing max_history or optimizing data structures'
                    })
            
            # Log diagnostic results
            self.debugger.log_event(
                DebugLevel.INFO,
                'MarketDataMonitor',
                f"Diagnostic check completed: {len(diagnostic_results['issues_found'])} issues found",
                {
                    'checks_performed': len(diagnostic_results['checks_performed']),
                    'issues_found': len(diagnostic_results['issues_found']),
                    'issues': diagnostic_results['issues_found']
                }
            )
            
        except Exception as e:
            diagnostic_results['error'] = str(e)
            if self.debugger:
                self.debugger.log_event(
                    DebugLevel.ERROR,
                    'MarketDataMonitor',
                    f"Error during diagnostic check: {str(e)}",
                    include_stack=True
                )
        
        return diagnostic_results
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.debugger:
            return {'error': 'Debugging not enabled'}
        
        metrics = {
            'timestamp': datetime.datetime.now(),
            'system_metrics': {},
            'execution_metrics': {},
            'data_metrics': self.data_quality_metrics.copy()
        }
        
        # Convert set to list for JSON serialization
        metrics['data_metrics']['symbols_with_issues'] = list(metrics['data_metrics']['symbols_with_issues'])
        
        # System metrics
        if self.debugger.performance_metrics['cpu_usage']:
            cpu_data = list(self.debugger.performance_metrics['cpu_usage'])
            metrics['system_metrics']['cpu'] = {
                'current': cpu_data[-1] if cpu_data else 0,
                'average': sum(cpu_data) / len(cpu_data) if cpu_data else 0,
                'max': max(cpu_data) if cpu_data else 0,
                'samples': len(cpu_data)
            }
        
        if self.debugger.performance_metrics['memory_usage']:
            memory_data = list(self.debugger.performance_metrics['memory_usage'])
            metrics['system_metrics']['memory'] = {
                'current': memory_data[-1] if memory_data else 0,
                'average': sum(memory_data) / len(memory_data) if memory_data else 0,
                'max': max(memory_data) if memory_data else 0,
                'samples': len(memory_data)
            }
        
        # Execution metrics
        for func_name, times in self.debugger.performance_metrics['execution_times'].items():
            if times:
                times_list = list(times)
                metrics['execution_metrics'][func_name] = {
                    'average_time': sum(times_list) / len(times_list),
                    'max_time': max(times_list),
                    'min_time': min(times_list),
                    'call_count': len(times_list),
                    'total_time': sum(times_list)
                }
        
        return metrics


class EconomicIndicatorMonitor:
    """Monitor economic indicators and central bank announcements."""
    
    def __init__(self, api_key: Optional[str] = None, enable_debugging: bool = True):
        """Initialize the economic indicator monitor.
        
        Args:
            api_key: API key for economic data provider
            enable_debugging: Enable self-debugging capabilities
        """
        self.api_key = api_key
        self.indicators_data = defaultdict(deque)
        self.is_monitoring = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # Initialize self-debugger
        self.debugger = SelfDebugger() if enable_debugging else None
        
        # Data quality metrics
        self.data_quality_metrics = {
            'total_requests': 0,
            'failed_requests': 0,
            'api_errors': 0,
            'last_successful_update': None,
            'indicators_with_issues': set(),
            'rate_limit_hits': 0
        }
        
        # Economic indicators to monitor
        self.indicators = [
            'interest_rates',
            'inflation_rate',
            'unemployment_rate',
            'gdp_growth',
            'retail_sales',
            'manufacturing_pmi',
            'services_pmi',
            'consumer_confidence'
        ]
        
        if self.debugger:
            self.debugger.log_event(
                DebugLevel.INFO,
                'EconomicIndicatorMonitor',
                "Economic indicator monitor initialized",
                {
                    'api_key_provided': bool(api_key),
                    'indicators_count': len(self.indicators),
                    'debugging_enabled': enable_debugging
                }
            )
        logger.info("Initialized EconomicIndicatorMonitor")
    
    def update_economic_calendar(self, days_ahead: int = 7, days_behind: int = 1):
        """Update the economic calendar.
        
        Args:
            days_ahead: Number of days ahead to fetch
            days_behind: Number of days behind to fetch
        """
        try:
            self.data_quality_metrics['total_requests'] += 1
            
            if self.debugger:
                self.debugger.log_event(
                    DebugLevel.INFO,
                    'EconomicIndicatorMonitor',
                    f"Updating economic calendar: {days_behind} days behind, {days_ahead} days ahead",
                    {'days_ahead': days_ahead, 'days_behind': days_behind}
                )
            
            # In a real implementation, this would call an API
            # For now, we'll simulate the data
            today = datetime.datetime.now().date()
            start_date = today - datetime.timedelta(days=days_behind)
            end_date = today + datetime.timedelta(days=days_ahead)
            
            # Simulated economic calendar data
            self.economic_calendar = [
                {
                    'date': today + datetime.timedelta(days=1),
                    'time': '14:30',
                    'country': 'US',
                    'indicator': 'Non-Farm Payrolls',
                    'importance': 'high',
                    'forecast': '200K',
                    'previous': '187K'
                },
                {
                    'date': today + datetime.timedelta(days=2),
                    'time': '20:00',
                    'country': 'US',
                    'indicator': 'FOMC Statement',
                    'importance': 'high',
                    'forecast': '',
                    'previous': ''
                },
                {
                    'date': today + datetime.timedelta(days=3),
                    'time': '10:00',
                    'country': 'EUR',
                    'indicator': 'CPI y/y',
                    'importance': 'high',
                    'forecast': '2.5%',
                    'previous': '2.6%'
                }
            ]
            
            self.data_quality_metrics['last_successful_update'] = datetime.datetime.now()
            
            if self.debugger:
                self.debugger.log_event(
                    DebugLevel.INFO,
                    'EconomicIndicatorMonitor',
                    f"Successfully updated economic calendar with {len(self.economic_calendar)} events",
                    {
                        'events_count': len(self.economic_calendar),
                        'date_range': f"{start_date} to {end_date}",
                        'high_importance_events': len([e for e in self.economic_calendar if e['importance'] == 'high'])
                    }
                )
            
            logger.info(f"Updated economic calendar with {len(self.economic_calendar)} events")
            
        except Exception as e:
            self.data_quality_metrics['failed_requests'] += 1
            self.data_quality_metrics['api_errors'] += 1
            
            if self.debugger:
                self.debugger.log_event(
                    DebugLevel.ERROR,
                    'EconomicIndicatorMonitor',
                    f"Error updating economic calendar: {str(e)}",
                    {
                        'exception_type': type(e).__name__,
                        'failed_requests': self.data_quality_metrics['failed_requests'],
                        'total_requests': self.data_quality_metrics['total_requests']
                    },
                    include_stack=True
                )
            
            logger.error(f"Error updating economic calendar: {e}")
    
    def update_interest_rates(self):
        """Update central bank interest rates."""
        try:
            self.data_quality_metrics['total_requests'] += 1
            
            if self.debugger:
                self.debugger.log_event(
                    DebugLevel.INFO,
                    'EconomicIndicatorMonitor',
                    "Updating central bank interest rates"
                )
            
            # Simulated interest rate data
            self.interest_rates = {
                'USD': {
                    'current_rate': 5.25,
                    'previous_rate': 5.00,
                    'next_meeting': datetime.datetime.now().date() + datetime.timedelta(days=15),
                    'expectation': 'hold',
                    'last_change': datetime.datetime.now().date() - datetime.timedelta(days=45)
                },
                'EUR': {
                    'current_rate': 3.75,
                    'previous_rate': 3.50,
                    'next_meeting': datetime.datetime.now().date() + datetime.timedelta(days=22),
                    'expectation': 'hike',
                    'last_change': datetime.datetime.now().date() - datetime.timedelta(days=30)
                },
                'GBP': {
                    'current_rate': 4.50,
                    'previous_rate': 4.25,
                    'next_meeting': datetime.datetime.now().date() + datetime.timedelta(days=8),
                    'expectation': 'hold',
                    'last_change': datetime.datetime.now().date() - datetime.timedelta(days=60)
                }
            }
            
            self.data_quality_metrics['last_successful_update'] = datetime.datetime.now()
            
            if self.debugger:
                rate_changes = sum(1 for curr_data in self.interest_rates.values() 
                                 if curr_data['current_rate'] != curr_data['previous_rate'])
                self.debugger.log_event(
                    DebugLevel.INFO,
                    'EconomicIndicatorMonitor',
                    f"Successfully updated interest rates for {len(self.interest_rates)} currencies",
                    {
                        'currencies_count': len(self.interest_rates),
                        'rate_changes': rate_changes,
                        'currencies': list(self.interest_rates.keys())
                    }
                )
            
            logger.info(f"Updated interest rates for {len(self.interest_rates)} currencies")
            
        except Exception as e:
            self.data_quality_metrics['failed_requests'] += 1
            self.data_quality_metrics['api_errors'] += 1
            
            if self.debugger:
                self.debugger.log_event(
                    DebugLevel.ERROR,
                    'EconomicIndicatorMonitor',
                    f"Error updating interest rates: {str(e)}",
                    {
                        'exception_type': type(e).__name__,
                        'failed_requests': self.data_quality_metrics['failed_requests']
                    },
                    include_stack=True
                )
            
            logger.error(f"Error updating interest rates: {e}")
    
    def update_inflation_data(self):
        """Update inflation data and forecasts."""
        try:
            # Simulated inflation data
            self.inflation_data = {
                'USD': {
                    'current': 3.2,
                    'previous': 3.3,
                    'forecast': 3.1,
                    'core': 2.8,
                    'trend': 'decreasing'
                },
                'EUR': {
                    'current': 2.6,
                    'previous': 2.8,
                    'forecast': 2.5,
                    'core': 2.3,
                    'trend': 'decreasing'
                },
                'GBP': {
                    'current': 4.1,
                    'previous': 4.3,
                    'forecast': 3.9,
                    'core': 3.8,
                    'trend': 'decreasing'
                }
            }
            
            self.last_update['inflation'] = datetime.datetime.now()
            logger.info(f"Updated inflation data for {len(self.inflation_data)} currencies")
            
        except Exception as e:
            logger.error(f"Error updating inflation data: {e}")
    
    def get_high_impact_events(self, days: int = 7) -> List[Dict]:
        """Get high impact economic events.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of high impact events
        """
        if not self.economic_calendar:
            self.update_economic_calendar(days_ahead=days)
        
        today = datetime.datetime.now().date()
        end_date = today + datetime.timedelta(days=days)
        
        high_impact_events = [
            event for event in self.economic_calendar
            if event['importance'] == 'high' and today <= event['date'] <= end_date
        ]
        
        return high_impact_events
    
    def get_rate_expectations(self) -> Dict:
        """Get interest rate expectations.
        
        Returns:
            Dictionary with rate expectations by currency
        """
        if not self.interest_rates:
            self.update_interest_rates()
        
        expectations = {}
        for currency, data in self.interest_rates.items():
            expectations[currency] = {
                'current_rate': data['current_rate'],
                'expectation': data['expectation'],
                'next_meeting': data['next_meeting']
            }
        
        return expectations


class NewsAndSentimentMonitor:
    """Monitor financial news and social media sentiment."""
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None, enable_debugging: bool = True):
        """Initialize the news and sentiment monitor.
        
        Args:
            api_keys: Dictionary of API keys for different data sources
            enable_debugging: Enable self-debugging capabilities
        """
        self.api_keys = api_keys or {}
        self.news_data = []
        self.social_sentiment = {}
        self.analyst_recommendations = {}
        self.institutional_positions = {}
        self.market_sentiment_indicators = {}
        
        # Initialize self-debugger
        self.debugger = SelfDebugger() if enable_debugging else None
        
        # Data quality metrics
        self.data_quality_metrics = {
            'total_requests': 0,
            'failed_requests': 0,
            'api_errors': 0,
            'rate_limit_hits': 0,
            'sentiment_analysis_errors': 0,
            'last_successful_update': None,
            'sources_with_issues': set(),
            'cached_sentiment_hits': 0
        }
        
        # Last update timestamps
        self.last_update = {
            'news': None,
            'social': None,
            'analyst': None,
            'institutional': None,
            'sentiment': None
        }
        
        # Sentiment analysis cache
        self.sentiment_cache = {}
        
        if self.debugger:
            self.debugger.log_event(
                DebugLevel.INFO,
                'NewsAndSentimentMonitor',
                "News and sentiment monitor initialized",
                {
                    'api_keys_provided': len(self.api_keys),
                    'debugging_enabled': enable_debugging,
                    'available_sources': list(self.api_keys.keys()) if self.api_keys else []
                }
            )
        
        logger.info("Initialized NewsAndSentimentMonitor")
    
    def update_financial_news(self, symbols: List[str] = None, max_articles: int = 50):
        """Update financial news data.
        
        Args:
            symbols: List of symbols to get news for
            max_articles: Maximum number of articles to fetch
        """
        try:
            self.data_quality_metrics['total_requests'] += 1
            symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
            
            if self.debugger:
                self.debugger.log_event(
                    DebugLevel.INFO,
                    'NewsAndSentimentMonitor',
                    f"Updating financial news for {len(symbols)} symbols",
                    {'symbols': symbols, 'max_articles': max_articles}
                )
            
            # In a real implementation, this would call a news API
            # For now, we'll simulate the data
            
            # Simulated news data
            self.news_data = [
                {
                    'timestamp': datetime.datetime.now() - datetime.timedelta(hours=2),
                    'headline': 'Fed signals potential rate cut in upcoming meeting',
                    'source': 'Bloomberg',
                    'url': 'https://bloomberg.com/news/123',
                    'symbols': ['USD', 'EURUSD', 'GBPUSD'],
                    'sentiment': 'positive',
                    'importance': 'high'
                },
                {
                    'timestamp': datetime.datetime.now() - datetime.timedelta(hours=4),
                    'headline': 'ECB maintains hawkish stance on inflation',
                    'source': 'Reuters',
                    'url': 'https://reuters.com/news/456',
                    'symbols': ['EUR', 'EURUSD'],
                    'sentiment': 'negative',
                    'importance': 'medium'
                },
                {
                    'timestamp': datetime.datetime.now() - datetime.timedelta(hours=6),
                    'headline': 'Gold prices surge amid geopolitical tensions',
                    'source': 'Financial Times',
                    'url': 'https://ft.com/news/789',
                    'symbols': ['XAUUSD', 'USD'],
                    'sentiment': 'positive',
                    'importance': 'high'
                }
            ]
            
            self.data_quality_metrics['last_successful_update'] = datetime.datetime.now()
            self.last_update['news'] = datetime.datetime.now()
            
            if self.debugger:
                high_importance_count = len([n for n in self.news_data if n['importance'] == 'high'])
                sentiment_distribution = {}
                for article in self.news_data:
                    sentiment = article['sentiment']
                    sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
                
                self.debugger.log_event(
                    DebugLevel.INFO,
                    'NewsAndSentimentMonitor',
                    f"Successfully updated financial news with {len(self.news_data)} articles",
                    {
                        'articles_count': len(self.news_data),
                        'high_importance_count': high_importance_count,
                        'sentiment_distribution': sentiment_distribution,
                        'sources': list(set(article['source'] for article in self.news_data))
                    }
                )
            
            logger.info(f"Updated financial news with {len(self.news_data)} articles")
            
        except Exception as e:
            self.data_quality_metrics['failed_requests'] += 1
            self.data_quality_metrics['api_errors'] += 1
            
            if self.debugger:
                self.debugger.log_event(
                    DebugLevel.ERROR,
                    'NewsAndSentimentMonitor',
                    f"Error updating financial news: {str(e)}",
                    {
                        'exception_type': type(e).__name__,
                        'failed_requests': self.data_quality_metrics['failed_requests'],
                        'symbols': symbols
                    },
                    include_stack=True
                )
            
            logger.error(f"Error updating financial news: {e}")
    
    def update_social_sentiment(self, symbols: List[str] = None):
        """Update social media sentiment data.
        
        Args:
            symbols: List of symbols to get sentiment for
        """
        try:
            # In a real implementation, this would call a social sentiment API
            # For now, we'll simulate the data
            symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
            
            # Simulated social sentiment data
            self.social_sentiment = {
                'EURUSD': {
                    'bullish_percentage': 45,
                    'bearish_percentage': 55,
                    'neutral_percentage': 0,
                    'total_mentions': 1250,
                    'sentiment_score': -0.1,
                    'trending': True
                },
                'GBPUSD': {
                    'bullish_percentage': 60,
                    'bearish_percentage': 30,
                    'neutral_percentage': 10,
                    'total_mentions': 850,
                    'sentiment_score': 0.3,
                    'trending': False
                },
                'USDJPY': {
                    'bullish_percentage': 70,
                    'bearish_percentage': 20,
                    'neutral_percentage': 10,
                    'total_mentions': 950,
                    'sentiment_score': 0.5,
                    'trending': True
                },
                'XAUUSD': {
                    'bullish_percentage': 80,
                    'bearish_percentage': 15,
                    'neutral_percentage': 5,
                    'total_mentions': 1500,
                    'sentiment_score': 0.65,
                    'trending': True
                }
            }
            
            self.data_quality_metrics['last_successful_update'] = datetime.datetime.now()
            self.last_update['social'] = datetime.datetime.now()
            
            if self.debugger:
                avg_sentiment = sum(data['sentiment_score'] for data in self.social_sentiment.values()) / len(self.social_sentiment)
                total_mentions = sum(data['total_mentions'] for data in self.social_sentiment.values())
                
                self.debugger.log_event(
                    DebugLevel.INFO,
                    'NewsAndSentimentMonitor',
                    f"Successfully updated social sentiment for {len(self.social_sentiment)} symbols",
                    {
                        'symbols_count': len(self.social_sentiment),
                        'average_sentiment': avg_sentiment,
                        'total_mentions': total_mentions,
                        'symbols': list(self.social_sentiment.keys())
                    }
                )
            
            logger.info(f"Updated social sentiment for {len(self.social_sentiment)} symbols")
            
        except Exception as e:
            self.data_quality_metrics['failed_requests'] += 1
            self.data_quality_metrics['api_errors'] += 1
            
            if self.debugger:
                self.debugger.log_event(
                    DebugLevel.ERROR,
                    'NewsAndSentimentMonitor',
                    f"Error updating social sentiment: {str(e)}",
                    {
                        'exception_type': type(e).__name__,
                        'failed_requests': self.data_quality_metrics['failed_requests'],
                        'symbols': symbols
                    },
                    include_stack=True
                )
            
            logger.error(f"Error updating social sentiment: {e}")
    
    def update_analyst_recommendations(self, symbols: List[str] = None):
        """Update analyst recommendations.
        
        Args:
            symbols: List of symbols to get recommendations for
        """
        try:
            # In a real implementation, this would call an API
            # For now, we'll simulate the data
            symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
            
            # Simulated analyst recommendations
            self.analyst_recommendations = {
                'EURUSD': {
                    'buy': 8,
                    'hold': 5,
                    'sell': 7,
                    'consensus': 'neutral',
                    'price_target': 1.0850,
                    'current_price': 1.0820
                },
                'GBPUSD': {
                    'buy': 12,
                    'hold': 3,
                    'sell': 5,
                    'consensus': 'buy',
                    'price_target': 1.2750,
                    'current_price': 1.2680
                },
                'USDJPY': {
                    'buy': 6,
                    'hold': 8,
                    'sell': 6,
                    'consensus': 'hold',
                    'price_target': 148.50,
                    'current_price': 149.20
                },
                'XAUUSD': {
                    'buy': 15,
                    'hold': 4,
                    'sell': 1,
                    'consensus': 'strong buy',
                    'price_target': 2100.00,
                    'current_price': 2050.00
                }
            }
            
            self.last_update['analyst'] = datetime.datetime.now()
            logger.info(f"Updated analyst recommendations for {len(self.analyst_recommendations)} symbols")
            
        except Exception as e:
            logger.error(f"Error updating analyst recommendations: {e}")
    
    def get_sentiment_summary(self, symbol: str) -> Dict:
        """Get a comprehensive sentiment summary for a symbol.
        
        Args:
            symbol: Symbol to get sentiment for
            
        Returns:
            Dictionary with sentiment summary
        """
        # Update data if needed
        if self.last_update['news'] is None:
            self.update_financial_news([symbol])
        
        if self.last_update['social'] is None:
            self.update_social_sentiment([symbol])
        
        if self.last_update['analyst'] is None:
            self.update_analyst_recommendations([symbol])
        
        # Get news sentiment
        news_sentiment = 0
        news_count = 0
        for article in self.news_data:
            if symbol in article['symbols']:
                if article['sentiment'] == 'positive':
                    news_sentiment += 1
                elif article['sentiment'] == 'negative':
                    news_sentiment -= 1
                news_count += 1
        
        news_score = news_sentiment / news_count if news_count > 0 else 0
        
        # Get social sentiment
        social_score = self.social_sentiment.get(symbol, {}).get('sentiment_score', 0)
        
        # Get analyst sentiment
        analyst_data = self.analyst_recommendations.get(symbol, {})
        buy_count = analyst_data.get('buy', 0)
        hold_count = analyst_data.get('hold', 0)
        sell_count = analyst_data.get('sell', 0)
        total_count = buy_count + hold_count + sell_count
        
        if total_count > 0:
            analyst_score = (buy_count - sell_count) / total_count
        else:
            analyst_score = 0
        
        # Calculate overall sentiment
        overall_sentiment = (news_score * 0.3) + (social_score * 0.3) + (analyst_score * 0.4)
        
        # Determine sentiment category
        if overall_sentiment > 0.5:
            sentiment_category = "very bullish"
        elif overall_sentiment > 0.2:
            sentiment_category = "bullish"
        elif overall_sentiment > -0.2:
            sentiment_category = "neutral"
        elif overall_sentiment > -0.5:
            sentiment_category = "bearish"
        else:
            sentiment_category = "very bearish"
        
        sentiment_summary = {
            'symbol': symbol,
            'overall_sentiment': overall_sentiment,
            'sentiment_category': sentiment_category,
            'news_sentiment': news_score,
            'social_sentiment': social_score,
            'analyst_sentiment': analyst_score,
            'news_count': news_count,
            'social_mentions': self.social_sentiment.get(symbol, {}).get('total_mentions', 0),
            'analyst_consensus': analyst_data.get('consensus', 'unknown'),
            'last_updated': datetime.datetime.now()
        }
        
        if self.debugger:
            self.debugger.log_event(
                DebugLevel.INFO,
                'NewsAndSentimentMonitor',
                f"Generated sentiment summary for {symbol}",
                {
                    'symbol': symbol,
                    'sentiment_category': sentiment_category,
                    'overall_sentiment': overall_sentiment,
                    'news_count': news_count
                }
            )
        
        return sentiment_summary
    
    def get_debug_status(self) -> Dict[str, Any]:
        """Get comprehensive debug status for the news and sentiment monitor.
        
        Returns:
            Dictionary with debug status information
        """
        if not self.debugger:
            return {'debugging_enabled': False}
        
        # Get debug summary
        debug_summary = self.debugger.get_debug_summary(hours=1)
        
        # Get recent errors
        recent_errors = self.debugger.get_recent_errors(count=5)
        
        # Calculate data quality metrics
        total_requests = self.data_quality_metrics['total_requests']
        failed_requests = self.data_quality_metrics['failed_requests']
        success_rate = ((total_requests - failed_requests) / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'debugging_enabled': True,
            'monitor_status': {
                'news_articles': len(self.news_data),
                'social_symbols': len(self.social_sentiment),
                'analyst_recommendations': len(self.analyst_recommendations),
                'api_keys_configured': len(self.api_keys)
            },
            'data_quality': {
                'total_requests': total_requests,
                'failed_requests': failed_requests,
                'success_rate': success_rate,
                'api_errors': self.data_quality_metrics['api_errors'],
                'rate_limit_hits': self.data_quality_metrics['rate_limit_hits'],
                'sentiment_analysis_errors': self.data_quality_metrics['sentiment_analysis_errors'],
                'sources_with_issues': list(self.data_quality_metrics['sources_with_issues']),
                'cached_sentiment_hits': self.data_quality_metrics['cached_sentiment_hits'],
                'last_successful_update': self.data_quality_metrics['last_successful_update']
            },
            'debug_summary': debug_summary,
            'recent_errors': [
                {
                    'timestamp': error.timestamp,
                    'level': error.level.value,
                    'component': error.component,
                    'message': error.message,
                    'details': error.details
                } for error in recent_errors
            ],
            'health_status': self.debugger.health_status
        }
    
    def run_diagnostic_check(self) -> Dict[str, Any]:
        """Run comprehensive diagnostic check for news and sentiment monitoring.
        
        Returns:
            Dictionary with diagnostic results
        """
        if not self.debugger:
            return {'error': 'Debugging not enabled'}
        
        diagnostic_results = {
            'timestamp': datetime.datetime.now(),
            'checks_performed': [],
            'issues_found': [],
            'recommendations': []
        }
        
        try:
            # Check 1: Data freshness
            diagnostic_results['checks_performed'].append('data_freshness')
            current_time = datetime.datetime.now()
            
            if self.data_quality_metrics['last_successful_update']:
                time_since_update = (current_time - self.data_quality_metrics['last_successful_update']).total_seconds()
                if time_since_update > 1800:  # 30 minutes
                    diagnostic_results['issues_found'].append({
                        'type': 'stale_news_data',
                        'severity': 'warning',
                        'message': f'News data not updated for {time_since_update/60:.0f} minutes',
                        'recommendation': 'Check news API connections and rate limits'
                    })
            
            # Check 2: API error rates
            diagnostic_results['checks_performed'].append('api_error_rates')
            total_requests = self.data_quality_metrics['total_requests']
            api_errors = self.data_quality_metrics['api_errors']
            
            if total_requests > 0:
                error_rate = (api_errors / total_requests) * 100
                if error_rate > 15:  # 15% error rate threshold
                    diagnostic_results['issues_found'].append({
                        'type': 'high_api_error_rate',
                        'severity': 'critical' if error_rate > 30 else 'warning',
                        'message': f'High API error rate: {error_rate:.1f}%',
                        'recommendation': 'Check API keys, rate limits, and service availability'
                    })
            
            # Check 3: Rate limiting
            diagnostic_results['checks_performed'].append('rate_limiting')
            rate_limit_hits = self.data_quality_metrics['rate_limit_hits']
            
            if rate_limit_hits > 5:
                diagnostic_results['issues_found'].append({
                    'type': 'frequent_rate_limiting',
                    'severity': 'warning',
                    'message': f'Rate limit hit {rate_limit_hits} times',
                    'recommendation': 'Implement request throttling or upgrade API plan'
                })
            
            # Check 4: Sentiment analysis errors
            diagnostic_results['checks_performed'].append('sentiment_analysis')
            sentiment_errors = self.data_quality_metrics['sentiment_analysis_errors']
            
            if sentiment_errors > 10:
                diagnostic_results['issues_found'].append({
                    'type': 'sentiment_analysis_issues',
                    'severity': 'warning',
                    'message': f'Sentiment analysis failed {sentiment_errors} times',
                    'recommendation': 'Check sentiment analysis model and text preprocessing'
                })
            
            # Check 5: Data coverage
            diagnostic_results['checks_performed'].append('data_coverage')
            if len(self.news_data) < 5:
                diagnostic_results['issues_found'].append({
                    'type': 'low_news_coverage',
                    'severity': 'warning',
                    'message': f'Only {len(self.news_data)} news articles available',
                    'recommendation': 'Expand news sources or check API configurations'
                })
            
            # Log diagnostic results
            self.debugger.log_event(
                DebugLevel.INFO,
                'NewsAndSentimentMonitor',
                f"Diagnostic check completed: {len(diagnostic_results['issues_found'])} issues found",
                {
                    'checks_performed': len(diagnostic_results['checks_performed']),
                    'issues_found': len(diagnostic_results['issues_found']),
                    'issues': diagnostic_results['issues_found']
                }
            )
            
        except Exception as e:
            diagnostic_results['error'] = str(e)
            if self.debugger:
                self.debugger.log_event(
                    DebugLevel.ERROR,
                    'NewsAndSentimentMonitor',
                    f"Error during diagnostic check: {str(e)}",
                    include_stack=True
                )
        
        return diagnostic_results

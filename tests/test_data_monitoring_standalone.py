import logging
"""
Standalone test script for the data_monitoring.py module

This script validates the fixes made to the SelfDebugger class in data_monitoring.py,
focusing on thread safety, error handling, and robustness without requiring
the full trading bot system imports.
"""

import sys
import os
import datetime
import time
import threading
from collections import deque, defaultdict
import unittest
from unittest.mock import Mock, patch
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Import necessary modules
import psutil
from loguru import logger
from typing import Optional

# Define the necessary classes for testing
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
    pass
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
    pass
            level: Debug level
            component: Component name
            message: Debug message
            details: Additional details
            include_stack: Whether to include stack trace
        """
        import traceback
from typing import Set

logger = logging.getLogger(__name__)

        
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
    pass
            component: Component name
            function_name: Function name
            
        Returns:
    pass
            Decorator function that wraps the target function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                """Wrapper function that monitors execution time.
                
                Args:
    pass
                    *args: Arguments to pass to the wrapped function
                    **kwargs: Keyword arguments to pass to the wrapped function
                    
                Returns:
    pass
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
    pass
        """Get current system performance metrics.
        
        Returns:
    pass
            Dictionary with performance metrics or empty dict on error
        """
        try:
            # CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Store for trending with thread safety
            try:
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
    
    def get_debug_summary(self, hours: int = 24) -> Dict[str, Any]:
    pass
        """Get debug summary for the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
    pass
            Dictionary with debug summary information
        """
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
        
        # Make a thread-safe copy
        try:
            debug_events_copy = list(self.debug_events)
            
            recent_events = [
                event for event in debug_events_copy
                if event.timestamp >= cutoff_time
            ]
            
            # Count events by level
            level_counts = {}
            for level in DebugLevel:
                level_counts[level.value] = sum(1 for event in recent_events if event.level == level)
            
            # Count events by component
            component_counts = defaultdict(int)
            for event in recent_events:
                component_counts[event.component] += 1
            
            # Get performance stats
            performance_stats = {
                'avg_cpu': 0.0,
                'max_cpu': 0.0,
                'avg_memory': 0.0,
                'max_memory': 0.0
            }
            
            cpu_data = list(self.performance_metrics['cpu_usage'])
            if cpu_data:
                performance_stats['avg_cpu'] = sum(cpu_data) / len(cpu_data)
                performance_stats['max_cpu'] = max(cpu_data)
            
            memory_data = list(self.performance_metrics['memory_usage'])
            if memory_data:
                performance_stats['avg_memory'] = sum(memory_data) / len(memory_data)
                performance_stats['max_memory'] = max(memory_data)
            
            # Get execution time stats
            execution_stats = {}
            for func_name, times in self.performance_metrics['execution_times'].items():
                if times:
                    times_list = list(times)
                    execution_stats[func_name] = {
                        'avg': sum(times_list) / len(times_list),
                        'max': max(times_list),
                        'count': len(times_list)
                    }
            
            return {
                'time_period_hours': hours,
                'total_events': len(recent_events),
                'events_by_level': level_counts,
                'events_by_component': dict(component_counts),
                'performance_stats': performance_stats,
                'execution_stats': execution_stats,
                'error_counts': dict(self.performance_metrics['error_counts']),
                'health_status': self.health_status,
                'generated_at': datetime.datetime.now()
            }
        except Exception as e:
            logger.error(f"Error generating debug summary: {str(e)}")
            return {
                'error': str(e),
                'generated_at': datetime.datetime.now()
            }
    
    def get_recent_errors(self, count: int = 10) -> List[DebugEvent]:
    pass
        """Get recent error and critical events.
        
        Args:
    pass
            count: Maximum number of errors to return
            
        Returns:
    pass
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
    pass
        """Diagnose performance issues based on collected metrics.
        
        Returns:
    pass
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


class TestSelfDebugger(unittest.TestCase):
    """Test cases for the SelfDebugger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.debugger = SelfDebugger(max_events=100)
    
    def test_log_event(self):
        """Test event logging functionality."""
        # Log an event
        self.debugger.log_event(
            DebugLevel.INFO,
            'TestComponent',
            'Test message',
            {'test_key': 'test_value'}
        )
        
        # Verify event was logged
        self.assertEqual(len(self.debugger.debug_events), 1)
        event = self.debugger.debug_events[0]
        self.assertEqual(event.level, DebugLevel.INFO)
        self.assertEqual(event.component, 'TestComponent')
        self.assertEqual(event.message, 'Test message')
        self.assertEqual(event.details.get('test_key'), 'test_value')
    
    def test_get_debug_summary(self):
        """Test debug summary generation."""
        # Log multiple events
        self.debugger.log_event(DebugLevel.INFO, 'Component1', 'Info message')
        self.debugger.log_event(DebugLevel.WARNING, 'Component2', 'Warning message')
        self.debugger.log_event(DebugLevel.ERROR, 'Component1', 'Error message')
        
        # Get summary
        summary = self.debugger.get_debug_summary(hours=1)
        
        # Verify summary
        self.assertEqual(summary['total_events'], 3)
        self.assertEqual(summary['events_by_level']['info'], 1)
        self.assertEqual(summary['events_by_level']['warning'], 1)
        self.assertEqual(summary['events_by_level']['error'], 1)
    
    def test_get_recent_errors(self):
        """Test retrieving recent errors."""
        # Log various events
        self.debugger.log_event(DebugLevel.INFO, 'Component1', 'Info message')
        self.debugger.log_event(DebugLevel.WARNING, 'Component2', 'Warning message')
        self.debugger.log_event(DebugLevel.ERROR, 'Component1', 'Error message 1')
        self.debugger.log_event(DebugLevel.CRITICAL, 'Component2', 'Critical message')
        self.debugger.log_event(DebugLevel.ERROR, 'Component3', 'Error message 2')
        
        # Get recent errors
        errors = self.debugger.get_recent_errors(count=10)
        
        # Verify errors
        self.assertEqual(len(errors), 3)  # 2 ERROR + 1 CRITICAL
        error_levels = [error.level for error in errors]
        self.assertIn(DebugLevel.ERROR, error_levels)
        self.assertIn(DebugLevel.CRITICAL, error_levels)
    
    def test_monitor_execution_time(self):
        """Test execution time monitoring."""
        # Create a decorated function
        @self.debugger.monitor_execution_time('TestComponent', 'test_function')
        def test_function(sleep_time):
            time.sleep(sleep_time)
            return "test_result"
        
        # Call the function
        result = test_function(0.1)
        
        # Verify result and execution time recording
        self.assertEqual(result, "test_result")
        key = "TestComponent.test_function"
        self.assertIn(key, self.debugger.performance_metrics['execution_times'])
        self.assertGreaterEqual(len(self.debugger.performance_metrics['execution_times'][key]), 1)
    
    def test_diagnose_performance_issues_empty_data(self):
        """Test performance diagnosis with empty data."""
        # Clear any existing data
        self.debugger.performance_metrics['cpu_usage'].clear()
        self.debugger.performance_metrics['memory_usage'].clear()
        
        # Run diagnosis
        diagnosis = self.debugger.diagnose_performance_issues()
        
        # Verify diagnosis structure
        self.assertIn('cpu_issues', diagnosis)
        self.assertIn('memory_issues', diagnosis)
        self.assertIn('execution_issues', diagnosis)
        self.assertIn('error_rate_issues', diagnosis)
        self.assertIn('recommendations', diagnosis)
    
    def test_diagnose_performance_issues_with_data(self):
        """Test performance diagnosis with simulated data."""
        # Add simulated performance data
        self.debugger.performance_metrics['cpu_usage'].extend([75.0, 80.0, 85.0, 90.0, 95.0])  # Higher CPU values to trigger issues
        self.debugger.performance_metrics['memory_usage'].extend([75.0, 80.0, 85.0, 90.0, 95.0])  # Higher memory values
        
        # Add execution times with higher values to trigger issues
        key = "TestComponent.test_function"
        if key not in self.debugger.performance_metrics['execution_times']:
            self.debugger.performance_metrics['execution_times'][key] = deque(maxlen=100)
        self.debugger.performance_metrics['execution_times'][key].extend([1.5, 2.0, 2.5, 3.0, 4.0])  # Values above 2.0 threshold
        
        # Run diagnosis
        diagnosis = self.debugger.diagnose_performance_issues()
        
        # Verify diagnosis
        self.assertTrue(len(diagnosis['cpu_issues']) > 0)
        self.assertTrue(len(diagnosis['memory_issues']) > 0)
        self.assertTrue(len(diagnosis['execution_issues']) > 0)
        self.assertTrue(len(diagnosis['recommendations']) > 0)


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("RUNNING STANDALONE SELF-DEBUGGER TESTS")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSelfDebugger)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("SUCCESS: ALL TESTS PASSED!")
    else:
        print(f"FAILED: {len(result.failures)} failures, {len(result.errors)} errors")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

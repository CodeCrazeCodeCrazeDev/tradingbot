"""
from pathlib import Path
Latency Budget Tracking System
Monitors and enforces latency budgets for critical trading paths
"""

import asyncio
import time
import logging
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime, timedelta
from collections import deque
import json
import threading
import functools
import uuid
import traceback

from trading_bot.monitoring.performance_tracker import get_performance_tracker
import pathlib
import numpy

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



logger = logging.getLogger(__name__)


class LatencyBudget:
    """
    Defines a latency budget for a critical path
    """
    
    def __init__(self, 
                name: str, 
                total_budget_ms: float,
                component_budgets: Dict[str, float]):
        self.name = name
        self.total_budget_ms = total_budget_ms
        self.component_budgets = component_budgets
        
        # Validate component budgets
        total_component_budget = sum(component_budgets.values())
        if total_component_budget > total_budget_ms:
            logger.warning(
                f"Component budgets ({total_component_budget}ms) exceed total budget "
                f"({total_budget_ms}ms) for {name}"
            )
    
    def get_component_budget(self, component: str) -> float:
        """Get budget for a specific component"""
        return self.component_budgets.get(component, 0)


class LatencyBudgetTracker:
    """
    Tracks and enforces latency budgets for critical paths
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Performance tracker
        self.performance_tracker = get_performance_tracker()
        
        # Latency budgets
        self.budgets = {}
        self._initialize_budgets()
        
        # Tracking state
        self.active_traces = {}
        self.completed_traces = deque(maxlen=1000)
        self.lock = threading.RLock()
        
        logger.info("Latency budget tracker initialized")
    
    def _initialize_budgets(self):
        """Initialize default latency budgets"""
        # Opportunity to trade path
        self.budgets['opportunity_to_trade'] = LatencyBudget(
            name='opportunity_to_trade',
            total_budget_ms=100,  # 100ms total budget
            component_budgets={
                'opportunity_detection': 20,  # 20ms for detection
                'signal_generation': 20,     # 20ms for signal generation
                'risk_assessment': 10,       # 10ms for risk assessment
                'decision_making': 20,       # 20ms for decision making
                'order_creation': 10,        # 10ms for order creation
                'execution': 20              # 20ms for execution
            }
        )
        
        # Data processing path
        self.budgets['data_processing'] = LatencyBudget(
            name='data_processing',
            total_budget_ms=50,  # 50ms total budget
            component_budgets={
                'data_reception': 5,         # 5ms for receiving data
                'normalization': 5,          # 5ms for normalization
                'validation': 5,             # 5ms for validation
                'enrichment': 10,            # 10ms for enrichment
                'storage': 10,               # 10ms for storage
                'distribution': 15           # 15ms for distribution
            }
        )
        
        # Signal generation path
        self.budgets['signal_generation'] = LatencyBudget(
            name='signal_generation',
            total_budget_ms=50,  # 50ms total budget
            component_budgets={
                'data_retrieval': 10,        # 10ms for data retrieval
                'indicator_calculation': 15, # 15ms for indicator calculation
                'signal_evaluation': 15,     # 15ms for signal evaluation
                'signal_filtering': 10       # 10ms for signal filtering
            }
        )
        
        # Add custom budgets from config
        for name, budget in self.config.get('budgets', {}).items():
            self.budgets[name] = LatencyBudget(
                name=name,
                total_budget_ms=budget['total_budget_ms'],
                component_budgets=budget['component_budgets']
            )
    
    def start_trace(self, path: str) -> str:
        """
        Start tracing a critical path
        
        Args:
            path: Name of the critical path
            
        Returns:
            Trace ID for the path
        """
        with self.lock:
            trace_id = str(uuid.uuid4())
            
            self.active_traces[trace_id] = {
                'path': path,
                'start_time': time.time(),
                'components': {},
                'current_component': None,
                'current_component_start': None
            }
            
            return trace_id
    
    def start_component(self, trace_id: str, component: str) -> bool:
        """
        Start timing a component within a trace
        
        Args:
            trace_id: Trace ID
            component: Component name
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            if trace_id not in self.active_traces:
                logger.warning(f"Trace {trace_id} not found")
                return False
            
            trace = self.active_traces[trace_id]
            
            # End current component if any
            if trace['current_component'] is not None:
                self.end_component(trace_id)
            
            # Start new component
            trace['current_component'] = component
            trace['current_component_start'] = time.time()
            
            return True
    
    def end_component(self, trace_id: str) -> bool:
        """
        End timing the current component within a trace
        
        Args:
            trace_id: Trace ID
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            if trace_id not in self.active_traces:
                logger.warning(f"Trace {trace_id} not found")
                return False
            
            trace = self.active_traces[trace_id]
            
            if trace['current_component'] is None:
                logger.warning(f"No active component in trace {trace_id}")
                return False
            
            # Calculate component latency
            component = trace['current_component']
            start_time = trace['current_component_start']
            latency_ms = (time.time() - start_time) * 1000
            
            # Store component latency
            trace['components'][component] = latency_ms
            
            # Check component budget
            path = trace['path']
            if path in self.budgets:
                budget = self.budgets[path]
                component_budget = budget.get_component_budget(component)
                
                if latency_ms > component_budget:
                    logger.warning(
                        f"Component {component} in {path} exceeded budget: "
                        f"{latency_ms:.2f}ms > {component_budget}ms"
                    )
            
            # Reset current component
            trace['current_component'] = None
            trace['current_component_start'] = None
            
            return True
    
    def end_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        End a trace and get results
        
        Args:
            trace_id: Trace ID
            
        Returns:
            Trace results or None if trace not found
        """
        with self.lock:
            if trace_id not in self.active_traces:
                logger.warning(f"Trace {trace_id} not found")
                return None
            
            # End current component if any
            if self.active_traces[trace_id]['current_component'] is not None:
                self.end_component(trace_id)
            
            # Calculate total latency
            trace = self.active_traces[trace_id]
            path = trace['path']
            start_time = trace['start_time']
            total_latency_ms = (time.time() - start_time) * 1000
            
            # Create result
            result = {
                'trace_id': trace_id,
                'path': path,
                'total_latency_ms': total_latency_ms,
                'components': trace['components'],
                'timestamp': datetime.now()
            }
            
            # Check total budget
            if path in self.budgets:
                budget = self.budgets[path]
                result['budget_ms'] = budget.total_budget_ms
                result['budget_exceeded'] = total_latency_ms > budget.total_budget_ms
                
                if result['budget_exceeded']:
                    logger.warning(
                        f"Path {path} exceeded total budget: "
                        f"{total_latency_ms:.2f}ms > {budget.total_budget_ms}ms"
                    )
            
            # Store result
            self.completed_traces.append(result)
            
            # Remove from active traces
            del self.active_traces[trace_id]
            
            return result
    
    def trace_path(self, path: str):
        """
        Decorator to trace a critical path
        
        Usage:
            @latency_budget_tracker.trace_path("opportunity_to_trade")
            async def process_opportunity(opportunity):
                ...
        """
        def decorator(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                trace_id = self.start_trace(path)
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    self.end_trace(trace_id)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                trace_id = self.start_trace(path)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    self.end_trace(trace_id)
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    def trace_component(self, component: str):
        """
        Decorator to trace a component within a critical path
        
        Usage:
            @latency_budget_tracker.trace_component("signal_generation")
            async def generate_signal(data):
                ...
        """
        def decorator(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Try to find trace ID in context
                trace_id = asyncio.current_task().get_name() if asyncio.current_task() else None
                
                if trace_id and trace_id in self.active_traces:
                    self.start_component(trace_id, component)
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    finally:
                        self.end_component(trace_id)
                else:
                    # No active trace, just call the function
                    return await func(*args, **kwargs)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Try to find trace ID in thread local storage
                trace_id = threading.current_thread().name
                
                if trace_id and trace_id in self.active_traces:
                    self.start_component(trace_id, component)
                    try:
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        self.end_component(trace_id)
                else:
                    # No active trace, just call the function
                    return func(*args, **kwargs)
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get latency budget metrics"""
        with self.lock:
            # Calculate statistics for each path
            path_metrics = {}
            
            for trace in self.completed_traces:
                path = trace['path']
                
                if path not in path_metrics:
                    path_metrics[path] = {
                        'count': 0,
                        'latencies': [],
                        'budget_exceeded_count': 0,
                        'component_latencies': {}
                    }
                
                metrics = path_metrics[path]
                metrics['count'] += 1
                metrics['latencies'].append(trace['total_latency_ms'])
                
                if trace.get('budget_exceeded', False):
                    metrics['budget_exceeded_count'] += 1
                
                # Aggregate component latencies
                for component, latency in trace['components'].items():
                    if component not in metrics['component_latencies']:
                        metrics['component_latencies'][component] = []
                    
                    metrics['component_latencies'][component].append(latency)
            
            # Calculate statistics
            result = {}
            
            for path, metrics in path_metrics.items():
                latencies = metrics['latencies']
                
                result[path] = {
                    'count': metrics['count'],
                    'avg_latency_ms': np.mean(latencies) if latencies else 0,
                    'min_latency_ms': np.min(latencies) if latencies else 0,
                    'max_latency_ms': np.max(latencies) if latencies else 0,
                    'p50_latency_ms': np.percentile(latencies, 50) if latencies else 0,
                    'p95_latency_ms': np.percentile(latencies, 95) if latencies else 0,
                    'p99_latency_ms': np.percentile(latencies, 99) if latencies else 0,
                    'budget_exceeded_rate': metrics['budget_exceeded_count'] / metrics['count'] if metrics['count'] > 0 else 0,
                    'components': {}
                }
                
                # Component statistics
                for component, latencies in metrics['component_latencies'].items():
                    result[path]['components'][component] = {
                        'avg_latency_ms': np.mean(latencies) if latencies else 0,
                        'min_latency_ms': np.min(latencies) if latencies else 0,
                        'max_latency_ms': np.max(latencies) if latencies else 0,
                        'p95_latency_ms': np.percentile(latencies, 95) if latencies else 0
                    }
            
            return result


# Global latency budget tracker instance
_latency_budget_tracker = None


def get_latency_budget_tracker(config: Optional[Dict[str, Any]] = None) -> LatencyBudgetTracker:
    """Get the global latency budget tracker instance"""
    global _latency_budget_tracker
    if _latency_budget_tracker is None:
        _latency_budget_tracker = LatencyBudgetTracker(config)
    return _latency_budget_tracker

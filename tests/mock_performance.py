"""
Mock implementations of performance optimization modules for testing and demonstration.
"""

import time
import threading
from typing import Any, Callable, Dict, List
from enum import Enum
import numpy as np
import pandas as pd
import numpy
import pandas


class TaskType(Enum):
    """Types of tasks for parallel processing."""
    DATA_LOADING = "data_loading"
    DATA_PROCESSING = "data_processing"
    MARKET_ANALYSIS = "market_analysis"
    SIGNAL_GENERATION = "signal_generation"
    RISK_CALCULATION = "risk_calculation"
    ORDER_EXECUTION = "order_execution"
    CUSTOM = "custom"


class DataStructureType(Enum):
    """Types of data structures for optimization."""
    OHLCV = "ohlcv"
    PRICE_SERIES = "price_series"
    ORDER_BOOK = "order_book"
    INDICATOR = "indicator"
    TIME_SERIES = "time_series"
    CUSTOM = "custom"


class ParallelProcessor:
    """Mock parallel processor."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize the processor."""
        self.max_workers = max_workers
        self.metrics = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'total_execution_time': 0,
            'avg_execution_time': 0
        }
    
    def map_tasks(self, task_type: TaskType, func: Callable, tasks: List[Any]) -> List[Any]:
        """Process tasks in parallel (mock implementation)."""
        results = []
        
        for task in tasks:
            start_time = time.time()
            result = func(task)
            execution_time = time.time() - start_time
            
            self.metrics['tasks_submitted'] += 1
            self.metrics['tasks_completed'] += 1
            self.metrics['total_execution_time'] += execution_time
            self.metrics['avg_execution_time'] = (
                self.metrics['total_execution_time'] / self.metrics['tasks_completed']
            )
            
            results.append(result)
        
        return results
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics."""
        return self.metrics


class MemoryOptimizer:
    """Mock memory optimizer."""
    
    def optimize_dataframe(self, df: pd.DataFrame,
                         data_type: DataStructureType) -> tuple[pd.DataFrame, Any]:
        """Optimize a DataFrame."""
        # Create a copy of the DataFrame
        optimized_df = df.copy()
        
        # Calculate original size
        original_size = df.memory_usage(deep=True).sum()
        
        # Convert float64 to float32
        float_cols = optimized_df.select_dtypes(include=['float64']).columns
        for col in float_cols:
            optimized_df[col] = optimized_df[col].astype('float32')
        
        # Convert int64 to int32
        int_cols = optimized_df.select_dtypes(include=['int64']).columns
        for col in int_cols:
            optimized_df[col] = optimized_df[col].astype('int32')
        
        # Calculate optimized size
        optimized_size = optimized_df.memory_usage(deep=True).sum()
        
        # Create optimization result
        class OptimizationResult:
            def __init__(self, original: int, optimized: int):
                self.original_size = original
                self.optimized_size = optimized
                self.reduction_percent = (
                    (original - optimized) / original * 100
                    if original > 0 else 0
                )
        
        result = OptimizationResult(original_size, optimized_size)
        return optimized_df, result


def profile(name: str, metric_type: str = "execution_time"):
    """Mock profiling decorator."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            return result
        return wrapper
    return decorator


class PerformanceMonitor:
    """Mock performance monitor."""
    
    def __init__(self):
        """Initialize the monitor."""
        self.metrics = {}
    
    def record_metric(self, name: str, metric_type: str, value: float) -> None:
        """Record a performance metric."""
        key = f"{name}_{metric_type}"
        if key not in self.metrics:
            self.metrics[key] = []
        self.metrics[key].append(value)
    
    def get_metrics(self) -> Dict[str, List[float]]:
        """Get all recorded metrics."""
        return self.metrics
    
    def get_metric_statistics(self, name: str, metric_type: str) -> Dict[str, float]:
        """Get statistics for a specific metric."""
        key = f"{name}_{metric_type}"
        if key not in self.metrics or not self.metrics[key]:
            return {}
        
        values = self.metrics[key]
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / len(values),
            'total': sum(values)
        }


def get_default_processor() -> ParallelProcessor:
    """Get the default parallel processor."""
    return ParallelProcessor()


def get_default_optimizer() -> MemoryOptimizer:
    """Get the default memory optimizer."""
    return MemoryOptimizer()

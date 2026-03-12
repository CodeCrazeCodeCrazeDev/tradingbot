"""
Elite Trading Bot - Parallel Processing Module

This module provides parallel processing capabilities for computationally intensive
market analysis tasks, optimizing performance through multi-threading and multi-processing.
"""

import os
import time
import logging
import threading
import multiprocessing
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, as_completed
from dataclasses import dataclass
import queue

import numpy as np
import pandas as pd
from typing import Set
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks that can be parallelized."""
    MARKET_ANALYSIS = "market_analysis"
    ORDER_FLOW = "order_flow"
    LIQUIDITY_DETECTION = "liquidity_detection"
    MICROSTRUCTURE = "microstructure"
    RISK_CALCULATION = "risk_calculation"
    BACKTEST = "backtest"
    OPTIMIZATION = "optimization"
    DATA_PROCESSING = "data_processing"
    CUSTOM = "custom"


@dataclass
class ProcessingResult:
    """Result of a parallel processing task."""
    task_id: str
    task_type: TaskType
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    resource_usage: Dict[str, float] = None


class ParallelProcessor:
    """
    Handles parallel processing for the Elite Trading Bot.
    
    This class provides optimized parallel execution capabilities for
    computationally intensive tasks using both multi-threading (for I/O-bound tasks)
    and multi-processing (for CPU-bound tasks).
    """
    
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = True):
        """
        Initialize the parallel processor.
        
        Args:
            max_workers: Maximum number of worker threads/processes.
                         If None, defaults to CPU count for processes or CPU count * 5 for threads.
            use_processes: If True, use multiprocessing, otherwise use threading.
        """
        self.use_processes = use_processes
        
        # Determine optimal number of workers based on system capabilities
        if max_workers is None:
            cpu_count = os.cpu_count() or 4
            self.max_workers = cpu_count if use_processes else cpu_count * 5
        else:
            self.max_workers = max_workers
            
        # Initialize executor
        self._executor = None
        self._active_tasks: Dict[str, Future] = {}
        self._results_queue = queue.Queue()
        
        # Performance metrics
        self._task_timings: Dict[str, List[float]] = {}
        self._resource_usage: Dict[str, List[Dict[str, float]]] = {}
        
        logger.info(f"Initialized ParallelProcessor with {self.max_workers} workers "
                   f"using {'processes' if use_processes else 'threads'}")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
    
    def start(self):
        """Start the executor."""
        if self._executor is None:
            if self.use_processes:
                self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
            else:
                self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
            logger.debug(f"Started executor with {self.max_workers} workers")
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown the executor.
        
        Args:
            wait: If True, wait for pending tasks to complete.
        """
        if self._executor is not None:
            self._executor.shutdown(wait=wait)
            self._executor = None
            logger.debug("Executor shutdown complete")
    
    def submit_task(self, task_id: str, task_type: TaskType, func: Callable, *args, **kwargs) -> str:
        """
        Submit a task for parallel execution.
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of task being submitted
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            task_id: The task identifier
        """
        if self._executor is None:
            self.start()
        
        # Wrap the function to capture execution time and results
        def wrapped_func(*args, **kwargs):
            start_time = time.time()
            try:
                # Execute the function
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = e
                logger.error(f"Task {task_id} failed with error: {str(e)}")
            
            execution_time = time.time() - start_time
            
            # Capture resource usage
            resource_usage = {
                'cpu_percent': 0.0,  # Would require psutil in real implementation
                'memory_mb': 0.0,    # Would require psutil in real implementation
                'execution_time': execution_time
            }
            
            # Create and return the result
            return ProcessingResult(
                task_id=task_id,
                task_type=task_type,
                success=success,
                result=result,
                error=error,
                execution_time=execution_time,
                resource_usage=resource_usage
            )
        
        # Submit the wrapped function
        future = self._executor.submit(wrapped_func, *args, **kwargs)
        self._active_tasks[task_id] = future
        
        # Set up callback to handle task completion
        def task_done_callback(future):
            try:
                result = future.result()
                # Store performance metrics
                if task_type.value not in self._task_timings:
                    self._task_timings[task_type.value] = []
                self._task_timings[task_type.value].append(result.execution_time)
                
                if task_type.value not in self._resource_usage:
                    self._resource_usage[task_type.value] = []
                self._resource_usage[task_type.value].append(result.resource_usage)
                
                # Put result in queue
                self._results_queue.put(result)
            except Exception as e:
                logger.error(f"Error processing task {task_id} result: {str(e)}")
            finally:
                # Remove from active tasks
                if task_id in self._active_tasks:
                    del self._active_tasks[task_id]
        
        future.add_done_callback(task_done_callback)
        logger.debug(f"Submitted task {task_id} of type {task_type.value}")
        
        return task_id
    
    def map_tasks(self, task_type: TaskType, func: Callable, items: List[Any],
                 **kwargs) -> List[ProcessingResult]:
        """
        Map a function over a list of items in parallel.
        
        Args:
            task_type: Type of tasks being submitted
            func: Function to execute for each item
            items: List of items to process
            **kwargs: Additional keyword arguments for the function
            
        Returns:
            List of processing results
        """
        task_ids = []
        for i, item in enumerate(items):
            task_id = f"{task_type.value}_{i}"
            self.submit_task(task_id, task_type, func, item, **kwargs)
            task_ids.append(task_id)
        
        return self.get_results(task_ids)
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> ProcessingResult:
        """
        Get the result of a specific task.
        
        Args:
            task_id: The task identifier
            timeout: Maximum time to wait for the result (in seconds)
            
        Returns:
            The processing result
            
        Raises:
            TimeoutError: If the result is not available within the timeout
            KeyError: If the task_id is not found
        """
        if task_id not in self._active_tasks:
            try:
                # Check if result is in the queue
                # Non-blocking check of all items in queue
                results = []
                while not self._results_queue.empty():
                    results.append(self._results_queue.get_nowait())
                
                for result in results:
                    if result.task_id == task_id:
                        return result
                    # Put back other results
                    self._results_queue.put(result)
                
                raise KeyError(f"Task {task_id} not found")
            except queue.Empty:
                raise KeyError(f"Task {task_id} not found")
        
        # Wait for the future to complete
        future = self._active_tasks[task_id]
        result = future.result(timeout=timeout)
        return result
    
    def get_results(self, task_ids: List[str], timeout: Optional[float] = None) -> List[ProcessingResult]:
        """
        Get results for multiple tasks.
        
        Args:
            task_ids: List of task identifiers
            timeout: Maximum time to wait for all results (in seconds)
            
        Returns:
            List of processing results in the same order as task_ids
        """
        results = []
        start_time = time.time()
        
        for task_id in task_ids:
            remaining_time = None
            if timeout is not None:
                try:
                    elapsed = time.time() - start_time
                    remaining_time = max(0, timeout - elapsed)
                    if remaining_time <= 0:
                        raise TimeoutError(f"Timeout waiting for results after {timeout} seconds")

                    result = self.get_result(task_id, timeout=remaining_time)
                    results.append(result)
                except (KeyError, TimeoutError) as e:
                    logger.warning(f"Could not get result for task {task_id}: {str(e)}")
                    # Create a placeholder failed result
                    results.append(ProcessingResult(
                        task_id=task_id,
                        task_type=TaskType.CUSTOM,  # Default as we don't know the actual type
                        success=False,
                        error=e,
                        execution_time=0.0
                    ))

        return results
    
    def wait_for_tasks(self, task_ids: Optional[List[str]] = None, 
                      timeout: Optional[float] = None) -> Dict[str, bool]:
        """
        Wait for specific tasks or all tasks to complete.
        
        Args:
            task_ids: List of task identifiers to wait for, or None for all active tasks
            timeout: Maximum time to wait (in seconds)
            
        Returns:
            Dictionary mapping task_ids to completion status (True if completed)
        """
        if task_ids is None:
            task_ids = list(self._active_tasks.keys())
        
        futures_to_ids = {self._active_tasks[task_id]: task_id 
                         for task_id in task_ids if task_id in self._active_tasks}
        
        completion_status = {task_id: False for task_id in task_ids}
        
        # Wait for futures to complete
        done_futures = set()
        try:
            for future in as_completed(futures_to_ids.keys(), timeout=timeout):
                task_id = futures_to_ids[future]
                completion_status[task_id] = True
                done_futures.add(future)
        except TimeoutError:
            # Mark only the completed futures
            for future in done_futures:
                task_id = futures_to_ids[future]
                completion_status[task_id] = True
        
        return completion_status
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a specific task if it's still running.
        
        Args:
            task_id: The task identifier
            
        Returns:
            True if the task was cancelled, False otherwise
        """
        if task_id in self._active_tasks:
            future = self._active_tasks[task_id]
            cancelled = future.cancel()
            if cancelled:
                del self._active_tasks[task_id]
                logger.debug(f"Task {task_id} cancelled successfully")
            else:
                logger.debug(f"Could not cancel task {task_id}, it may have already completed")
            return cancelled
        return False
    
    def cancel_all_tasks(self) -> Dict[str, bool]:
        """
        Cancel all active tasks.
        
        Returns:
            Dictionary mapping task_ids to cancellation status (True if cancelled)
        """
        cancellation_status = {}
        for task_id in list(self._active_tasks.keys()):
            cancellation_status[task_id] = self.cancel_task(task_id)
        return cancellation_status
    
    def get_active_task_count(self) -> int:
        """Get the number of active tasks."""
        return len(self._active_tasks)
    
    def get_performance_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance metrics for completed tasks.
        
        Returns:
            Dictionary with task types as keys and performance metrics as values
        """
        metrics = {}
        
        for task_type, timings in self._task_timings.items():
            if not timings:
                continue
                
            metrics[task_type] = {
                'count': len(timings),
                'avg_execution_time': np.mean(timings),
                'min_execution_time': np.min(timings),
                'max_execution_time': np.max(timings),
                'median_execution_time': np.median(timings),
                'total_execution_time': np.sum(timings)
            }
            
            # Add resource usage metrics if available
            if task_type in self._resource_usage and self._resource_usage[task_type]:
                resource_metrics = {}
                for metric in self._resource_usage[task_type][0].keys():
                    values = [usage[metric] for usage in self._resource_usage[task_type] if metric in usage]
                    if values:
                        resource_metrics[f'avg_{metric}'] = np.mean(values)
                        resource_metrics[f'max_{metric}'] = np.max(values)
                
                metrics[task_type].update(resource_metrics)
        
        return metrics
    
    def optimize_workload(self, task_type: TaskType, data_size: int) -> Tuple[int, bool]:
        """
        Optimize the workload distribution based on task type and data size.
        
        Args:
            task_type: Type of task to optimize for
            data_size: Size of the data to process
            
        Returns:
            Tuple of (optimal_chunk_size, use_processes)
        """
        cpu_count = os.cpu_count() or 4
        
        # Default optimization strategy based on task type
        if task_type == TaskType.MARKET_ANALYSIS:
            # Market analysis is often CPU-bound
            return max(1, data_size // (cpu_count * 2)), True
        
        elif task_type == TaskType.DATA_PROCESSING:
            # Data processing can be I/O bound or CPU bound depending on operation
            if data_size > 100000:  # Large dataset
                return max(1, data_size // cpu_count), True
            else:
                return max(1, data_size // (cpu_count * 2)), False
        
        elif task_type == TaskType.BACKTEST:
            # Backtesting is CPU-intensive
            return max(1, data_size // cpu_count), True
        
        elif task_type == TaskType.OPTIMIZATION:
            # Optimization tasks are CPU-intensive
            return max(1, data_size // cpu_count), True
        
        else:
            # Default strategy
            if data_size > 50000:
                return max(1, data_size // (cpu_count * 2)), True
            else:
                return max(1, data_size // (cpu_count * 4)), False
    
    def parallel_apply_to_dataframe(self, df: pd.DataFrame, func: Callable,
                                   task_type: TaskType = TaskType.DATA_PROCESSING,
                                   axis: int = 0, **kwargs) -> pd.DataFrame:
        """
        Apply a function to a DataFrame in parallel.
        
        Args:
            df: Input DataFrame
            func: Function to apply
            task_type: Type of task
            axis: 0 for rows, 1 for columns
            **kwargs: Additional arguments for the function
            
        Returns:
            DataFrame with function applied
        """
        # Determine optimal chunk size
        chunk_size, use_processes = self.optimize_workload(task_type, len(df))
        
        # Split DataFrame into chunks
        chunks = [df.iloc[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
        
        # Process each chunk in parallel
        original_use_processes = self.use_processes
        try:
            # Set process mode based on optimization
            if self.use_processes != use_processes:
                self.shutdown()
                self.use_processes = use_processes
                self.start()
            
            # Define wrapper function for processing chunks
            def process_chunk(chunk_df):
                return chunk_df.apply(func, axis=axis, **kwargs)
            
            # Submit tasks
            results = self.map_tasks(task_type, process_chunk, chunks)
            
            # Combine results
            processed_chunks = []
            for result in results:
                if result.success:
                    processed_chunks.append(result.result)
                else:
                    logger.error(f"Error processing chunk: {result.error}")
                    # Use original chunk as fallback
                    idx = int(result.task_id.split('_')[-1])
                    if idx < len(chunks):
                        processed_chunks.append(chunks[idx])
            
            # Concatenate results
            if processed_chunks:
                return pd.concat(processed_chunks)
            else:
                return df  # Return original if all failed
            
        finally:
            # Restore original process mode if changed
            if self.use_processes != original_use_processes:
                self.shutdown()
                self.use_processes = original_use_processes
                self.start()
    
    def parallel_map(self, func: Callable, items: List[Any], 
                    task_type: TaskType = TaskType.CUSTOM,
                    **kwargs) -> List[Any]:
        """
        Map a function over a list of items in parallel and return just the results.
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            task_type: Type of task
            **kwargs: Additional arguments for the function
            
        Returns:
            List of results
        """
        processing_results = self.map_tasks(task_type, func, items, **kwargs)
        
        # Extract just the result values
        results = []
        for pr in processing_results:
            if pr.success:
                results.append(pr.result)
            else:
                results.append(None)
                logger.warning(f"Task {pr.task_id} failed: {pr.error}")
        
        return results


# Singleton instance for easy access
_default_processor = None

def get_default_processor() -> ParallelProcessor:
    """Get or create the default parallel processor instance."""
    global _default_processor
    if _default_processor is None:
        _default_processor = ParallelProcessor()
    return _default_processor


# Example usage functions
def parallel_market_analysis(symbols: List[str], timeframes: List[str], 
                           analysis_func: Callable, **kwargs) -> Dict[str, Dict[str, Any]]:
    """
    Run market analysis in parallel for multiple symbols and timeframes.
    
    Args:
        symbols: List of symbols to analyze
        timeframes: List of timeframes to analyze
        analysis_func: Analysis function to apply
        **kwargs: Additional arguments for the analysis function
        
    Returns:
        Nested dictionary with results: {symbol: {timeframe: result}}
    """
    processor = get_default_processor()
    
    # Create tasks for each symbol-timeframe combination
    tasks = []
    task_mapping = {}
    
    for symbol in symbols:
        for timeframe in timeframes:
            task_id = f"analysis_{symbol}_{timeframe}"
            processor.submit_task(
                task_id, 
                TaskType.MARKET_ANALYSIS,
                analysis_func,
                symbol=symbol,
                timeframe=timeframe,
                **kwargs
            )
            tasks.append(task_id)
            task_mapping[task_id] = (symbol, timeframe)
    
    # Wait for all tasks to complete
    results = processor.get_results(tasks)
    
    # Organize results by symbol and timeframe
    organized_results = {}
    for result in results:
        if result.success:
            symbol, timeframe = task_mapping[result.task_id]
            if symbol not in organized_results:
                organized_results[symbol] = {}
            organized_results[symbol][timeframe] = result.result
    
    return organized_results

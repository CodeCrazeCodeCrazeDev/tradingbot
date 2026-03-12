from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
"""Performance profiling utilities for CPU usage optimization.

This module provides decorators and context managers to measure execution time
and memory usage of functions and code blocks. Results are logged and can be
used to identify bottlenecks.
"""

import cProfile
import functools
import pstats
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from loguru import logger

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class ProfileStats:
    """Container for profiling statistics."""

    function_name: str
    calls: int
    execution_time: float  # seconds
    cpu_percent: float


def profile_function(log_level: str = "DEBUG") -> Callable[[F], F]:
    """Decorator to profile a function's execution time and CPU usage.
    
    Args:
        log_level: Loguru log level to use for output
        
    Example:
        @profile_function()
        def my_function():
            # code to profile
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create profiler
            try:
                profiler = cProfile.Profile()
            
                # Start timing
                start_time = time.time()
            
                # Start profiling
                profiler.enable()
            
                # Call the function
                result = func(*args, **kwargs)
            
                # Stop profiling
                profiler.disable()
            
                # Calculate execution time
                execution_time = time.time() - start_time
            
                # Get stats
                stats = pstats.Stats(profiler)
            
                # Extract function stats
                func_stats = _extract_function_stats(stats, func.__name__)
            
                # Log the results
                getattr(logger, log_level.lower())(
                    "PROFILE: {}: {:.4f}s, CPU: {:.1f}%, Calls: {}",
                    func.__name__,
                    execution_time,
                    func_stats.cpu_percent,
                    func_stats.calls
                )
            
                return result
            except Exception as e:
                logger.error(f"Error in wrapper: {e}")
                raise
        return cast(F, wrapper)
    return decorator


class ProfileBlock:
    """Context manager for profiling a block of code.
    
    Example:
        with ProfileBlock("my_operation"):
            # code to profile
    """
    
    def __init__(self, name: str, log_level: str = "DEBUG") -> None:
        try:
            self.name = name
            self.log_level = log_level
            self.start_time: float = 0
            self.profiler = cProfile.Profile()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def __enter__(self) -> ProfileBlock:
        try:
            self.start_time = time.time()
            self.profiler.enable()
            return self
        except Exception as e:
            logger.error(f"Error in __enter__: {e}")
            raise
        
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            self.profiler.disable()
            execution_time = time.time() - self.start_time
        
            # Get stats
            stats = pstats.Stats(self.profiler)
        
            # Log the results
            getattr(logger, self.log_level.lower())(
                "PROFILE BLOCK: {}: {:.4f}s",
                self.name,
                execution_time
            )
        
            # If detailed logging is desired
            if self.log_level == "DEBUG":
                top_funcs = _get_top_functions(stats, 5)
                for i, func in enumerate(top_funcs):
                    logger.debug(
                        "  Top #{}: {} - {:.4f}s ({:.1f}%)",
                        i + 1,
                        func.function_name,
                        func.execution_time,
                        func.cpu_percent
                    )
        except Exception as e:
            logger.error(f"Error in __exit__: {e}")
            raise


def _extract_function_stats(stats: pstats.Stats, func_name: str) -> ProfileStats:
    """Extract statistics for a specific function."""
    # Get the stats dictionary
    try:
        stats_dict = stats.stats
    
        # Find the function entry
        func_entry = None
        for key, value in stats_dict.items():
            if func_name in str(key):
                func_entry = (key, value)
                break
    
        if func_entry is None:
            # Return default stats if function not found
            return ProfileStats(func_name, 0, 0.0, 0.0)
    
        # Extract stats
        _, (calls, _, cumtime, _, _) = func_entry
    
        # Calculate CPU percentage (approximate)
        total_time = sum(entry[2] for entry in stats_dict.values())
        cpu_percent = (cumtime / total_time * 100) if total_time > 0 else 0
    
        return ProfileStats(func_name, calls, cumtime, cpu_percent)
    except Exception as e:
        logger.error(f"Error in _extract_function_stats: {e}")
        raise


def _get_top_functions(stats: pstats.Stats, n: int = 5) -> List[ProfileStats]:
    """Get the top N functions by cumulative time."""
    # Get the stats dictionary
    try:
        stats_dict = stats.stats
    
        # Calculate total time
        total_time = sum(entry[2] for entry in stats_dict.values())
    
        # Create ProfileStats for each function
        all_stats = []
        for (file, line, name), (calls, _, cumtime, _, _) in stats_dict.items():
            func_name = f"{name} ({file}:{line})"
            cpu_percent = (cumtime / total_time * 100) if total_time > 0 else 0
            all_stats.append(ProfileStats(func_name, calls, cumtime, cpu_percent))
    
        # Sort by execution time (descending)
        all_stats.sort(key=lambda x: x.execution_time, reverse=True)
    
        # Return top N
        return all_stats[:n]
    except Exception as e:
        logger.error(f"Error in _get_top_functions: {e}")
        raise

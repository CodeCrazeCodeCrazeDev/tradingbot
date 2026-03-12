"""
Async/Sync Method Validation Module
Ensures correct usage of async/sync methods and provides runtime validation
"""

import asyncio
import inspect
import logging
import functools
import time
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
from datetime import datetime

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


class AsyncMismatchError(Exception):
    """Exception raised when async/sync methods are mismatched"""
    pass


def validate_async(func=None, *, expected_async=True):
    """
    Decorator to validate that a function is correctly defined as async or sync
    
    Args:
        func: The function to decorate
        expected_async: Whether the function should be async (True) or sync (False)
    """
    def decorator(func):
        is_async = asyncio.iscoroutinefunction(func)
        
        if expected_async and not is_async:
            raise AsyncMismatchError(
                f"Function {func.__name__} should be async but is defined as sync"
            )
        elif not expected_async and is_async:
            raise AsyncMismatchError(
                f"Function {func.__name__} should be sync but is defined as async"
            )
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return async_wrapper if is_async else wrapper
    
    if func is None:
        return decorator
    return decorator(func)


def validate_async_call(func=None, *, expected_await=True):
    """
    Decorator to validate that a function is correctly called with or without await
    
    Args:
        func: The function to decorate
        expected_await: Whether the function should be called with await (True) or not (False)
    """
    def decorator(func):
        is_async = asyncio.iscoroutinefunction(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Check if we're in an async context
                asyncio.get_running_loop()
                in_async_context = True
            except RuntimeError:
                in_async_context = False
            
            # For sync functions, just call normally
            if not is_async:
                return func(*args, **kwargs)
            
            # For async functions, warn if called without await
            result = func(*args, **kwargs)
            
            # Check if result is a coroutine (indicating it wasn't awaited)
            if inspect.iscoroutine(result):
                caller_frame = inspect.currentframe().f_back
                caller_info = inspect.getframeinfo(caller_frame)
                logger.warning(
                    f"Async function {func.__name__} called without await at "
                    f"{caller_info.filename}:{caller_info.lineno}"
                )
                
                # If we're in an async context, we can await it for them
                if in_async_context and expected_await:
                    logger.warning(f"Auto-awaiting {func.__name__} call")
                    return asyncio.ensure_future(result)
            
            return result
        
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)


def async_safe(func):
    """
    Decorator to make a function safe to call in both async and sync contexts
    
    If the function is async and called from a sync context, it will run the event loop.
    If the function is sync and called with await, it will be wrapped in asyncio.to_thread.
    """
    is_async = asyncio.iscoroutinefunction(func)
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if is_async:
            try:
                # If we're in an async context, return the coroutine
                asyncio.get_running_loop()
                return func(*args, **kwargs)
            except RuntimeError:
                # We're in a sync context, run the event loop
                return asyncio.run(func(*args, **kwargs))
        else:
            # Sync function, just call it
            return func(*args, **kwargs)
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        if is_async:
            # Async function, await it
            return await func(*args, **kwargs)
        else:
            # Sync function, run in thread pool
            return await asyncio.to_thread(func, *args, **kwargs)
    
    return async_wrapper if is_async else wrapper


def measure_latency(func=None, *, threshold_ms=100, log_all=False):
    """
    Decorator to measure and log function execution latency
    
    Args:
        func: The function to decorate
        threshold_ms: Log warning if execution time exceeds this threshold (in ms)
        log_all: Whether to log all executions or only those exceeding threshold
    """
    def decorator(func):
        is_async = asyncio.iscoroutinefunction(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # ms
            
            if log_all or execution_time > threshold_ms:
                level = logging.WARNING if execution_time > threshold_ms else logging.DEBUG
                logger.log(
                    level,
                    f"{func.__name__} took {execution_time:.2f}ms "
                    f"(threshold: {threshold_ms}ms)"
                )
            
            return result
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # ms
            
            if log_all or execution_time > threshold_ms:
                level = logging.WARNING if execution_time > threshold_ms else logging.DEBUG
                logger.log(
                    level,
                    f"{func.__name__} took {execution_time:.2f}ms "
                    f"(threshold: {threshold_ms}ms)"
                )
            
            return result
        
        return async_wrapper if is_async else wrapper
    
    if func is None:
        return decorator
    return decorator(func)


class AsyncValidator:
    """
    Utility class to validate async/sync method usage in a class
    """
    
    @staticmethod
    def validate_class(cls: Type, async_methods: Set[str], sync_methods: Set[str]) -> List[str]:
        """
        Validate that methods in a class are correctly defined as async or sync
        
        Args:
            cls: The class to validate
            async_methods: Set of method names that should be async
            sync_methods: Set of method names that should be sync
            
        Returns:
            List of error messages, empty if no errors
        """
        errors = []
        
        for method_name in async_methods:
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                if callable(method) and not asyncio.iscoroutinefunction(method):
                    errors.append(f"Method {cls.__name__}.{method_name} should be async but is sync")
        
        for method_name in sync_methods:
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                if callable(method) and asyncio.iscoroutinefunction(method):
                    errors.append(f"Method {cls.__name__}.{method_name} should be sync but is async")
        
        return errors
    
    @staticmethod
    def patch_class(cls: Type, async_methods: Set[str], sync_methods: Set[str]) -> Type:
        """
        Patch a class to ensure methods are correctly defined as async or sync
        
        Args:
            cls: The class to patch
            async_methods: Set of method names that should be async
            sync_methods: Set of method names that should be sync
            
        Returns:
            Patched class
        """
        for method_name in async_methods:
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                if callable(method) and not asyncio.iscoroutinefunction(method):
                    logger.warning(f"Patching {cls.__name__}.{method_name} to be async")
                    
                    @functools.wraps(method)
                    async def async_wrapper(self, *args, **kwargs):
                        return method(self, *args, **kwargs)
                    
                    setattr(cls, method_name, async_wrapper)
        
        for method_name in sync_methods:
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                if callable(method) and asyncio.iscoroutinefunction(method):
                    logger.warning(f"Patching {cls.__name__}.{method_name} to be sync")
                    
                    @functools.wraps(method)
                    def sync_wrapper(self, *args, **kwargs):
                        return asyncio.run(method(self, *args, **kwargs))
                    
                    setattr(cls, method_name, sync_wrapper)
        
        return cls

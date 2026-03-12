"""
profiling package
"""

try:
    from .async_profiler import (
        AsyncProfileBlock,
        AsyncProfiler,
        HotspotReport,
        ProfileBlock,
        ProfileResult,
        T,
        get_profiler,
        profile_async,
        profile_sync,
        reset_profiler,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in profiling: {e}')

__all__ = [
    'AsyncProfileBlock',
    'AsyncProfiler',
    'HotspotReport',
    'ProfileBlock',
    'ProfileResult',
    'T',
    'get_profiler',
    'profile_async',
    'profile_sync',
    'reset_profiler',
    'retry',
]
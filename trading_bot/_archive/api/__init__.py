"""
api package
"""

try:
    from .rate_limiter import (
        BROKER_RATE_LIMITS,
        MultiRateLimiter,
        RateLimitConfig,
        RateLimitStats,
        RateLimitStrategy,
        RateLimiter,
        create_broker_limiter,
        rate_limited,
        retry
    )
    from .rest_api import TradingAPIServer
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in api: {e}')

__all__ = [
    'BROKER_RATE_LIMITS',
    'MultiRateLimiter',
    'RateLimitConfig',
    'RateLimitStats',
    'RateLimitStrategy',
    'RateLimiter',
    'TradingAPIServer',
    'create_broker_limiter',
    'rate_limited',
    'retry',
]
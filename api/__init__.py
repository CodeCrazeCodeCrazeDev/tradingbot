"""
API package for AlphaAlgo 2.0
"""

from .api_server import APIServer

try:
    from .rate_limiter import RateLimiter, RateLimitMiddleware
    from .authentication import JWTAuthenticator, APIKeyAuthenticator
    __all__ = [
        'APIServer',
        'RateLimiter',
        'RateLimitMiddleware',
        'JWTAuthenticator',
        'APIKeyAuthenticator'
    ]
except ImportError:
    __all__ = ['APIServer']

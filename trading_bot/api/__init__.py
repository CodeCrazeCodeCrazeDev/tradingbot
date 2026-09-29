"""API compatibility layer over the modular-monolith read models."""

import warnings

from trading_bot.foundation.runtime import ModularMonolithRuntime
from trading_bot.interfaces.read_models import ModularMonolithReadModel

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
    'APIOrchestrator',
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

class APIManager:
    """Auto-generated stub orchestrator for module integration."""
    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
        self._initialized = True
    
    async def start(self):
        """Start the orchestrator."""
        self.running = True
    
    async def stop(self):
        """Stop the orchestrator."""
        self.running = False
    
    def get_status(self):
        """Get orchestrator status."""
        return {"running": self.running, "initialized": self._initialized}



class APIOrchestrator:
    """One-wave read-only compatibility facade over the runtime boundary."""

    def __init__(self, *args, **kwargs):
        self.config = kwargs.get("config", {})
        warnings.warn(
            "APIOrchestrator is a compatibility facade; use ModularMonolithRuntime and read models.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.runtime = ModularMonolithRuntime(self.config)
        self.read_model = ModularMonolithReadModel(self.runtime)
        self.running = False

    async def start(self):
        await self.runtime.start()
        self.running = True

    async def stop(self):
        await self.runtime.stop()
        self.running = False

    def get_status(self):
        return {**self.read_model.status(), "running": self.running}

    async def health(self):
        return await self.read_model.health()

    async def portfolio(self, account_id: str = "runtime"):
        return await self.read_model.portfolio(account_id)

    async def dashboard_snapshot(self, account_id: str = "runtime"):
        return await self.read_model.dashboard_snapshot(account_id)

    async def report_snapshot(self, account_id: str = "runtime"):
        return await self.read_model.report_snapshot(account_id)

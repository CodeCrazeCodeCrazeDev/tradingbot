"""
crypto package
"""

try:
    from .defi_module import (
        Chain,
        CrossChainBridge,
        CryptoDeFiModule,
        CryptoExchangeConnector,
        DeFiPool,
        DeFiProtocolConnector,
        YieldOpportunity,
        YieldOptimizer,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in crypto: {e}')

__all__ = [
    'Chain',
    'CrossChainBridge',
    'CryptoDeFiModule',
    'CryptoExchangeConnector',
    'DeFiPool',
    'DeFiProtocolConnector',
    'YieldOpportunity',
    'YieldOptimizer',
    'retry',
]

class CryptoOrchestrator:
    """Auto-generated stub orchestrator for module integration."""
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "CryptoOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
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


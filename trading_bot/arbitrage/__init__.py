"""
arbitrage package
"""

try:
    from .arbitrage_network import (
        ArbitrageNetwork,
        ArbitrageOpportunity,
        ArbitrageType,
        CrossExchangeArbitrage,
        ETFArbitrage,
        TriangularArbitrage,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in arbitrage: {e}')

__all__ = [
    'ArbitrageScanner',
    'ArbitrageNetwork',
    'ArbitrageOpportunity',
    'ArbitrageType',
    'CrossExchangeArbitrage',
    'ETFArbitrage',
    'TriangularArbitrage',
    'retry',
]

class ArbitrageScanner:
    """Stub for ArbitrageScanner."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}

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
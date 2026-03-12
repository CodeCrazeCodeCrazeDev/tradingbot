"""
integrations package
"""

try:
    from .real_alternative_data import (
        EconomicIndicator,
        NewsItem,
        RealAlternativeDataProvider,
        SentimentData,
        get_real_alternative_data
    )
    from .real_defi_integration import (
        CHAIN_CONFIGS,
        Chain,
        ChainConfig,
        DeFiProtocol,
        ERC20_ABI,
        PoolInfo,
        RealDeFiIntegration,
        SUSHISWAP_ROUTER,
        TokenInfo,
        UNISWAP_V2_ROUTER,
        UNISWAP_V3_ROUTER,
        YieldOpportunity,
        get_real_defi_integration
    )
    from .real_market_data import (
        DataProvider,
        MarketDataConfig,
        RealMarketDataProvider,
        get_real_market_data
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in integrations: {e}')

__all__ = [
    'CHAIN_CONFIGS',
    'Chain',
    'ChainConfig',
    'DataProvider',
    'DeFiProtocol',
    'ERC20_ABI',
    'EconomicIndicator',
    'MarketDataConfig',
    'NewsItem',
    'PoolInfo',
    'RealAlternativeDataProvider',
    'RealDeFiIntegration',
    'RealMarketDataProvider',
    'SUSHISWAP_ROUTER',
    'SentimentData',
    'TokenInfo',
    'UNISWAP_V2_ROUTER',
    'UNISWAP_V3_ROUTER',
    'YieldOpportunity',
    'get_real_alternative_data',
    'get_real_defi_integration',
    'get_real_market_data',
]
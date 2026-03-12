"""
blockchain package
"""

try:
    from .defi_integration import (
        ArbitrageOpportunity,
        Chain,
        CrossChainArbitrage,
        DeFiProtocol,
        DeFiYieldOptimizer,
        LiquidityMiningOptimizer,
        YieldOpportunity,
        retry
    )
    from .real_defi_integration import (
        CHAIN_CONFIGS,
        Chain,
        ChainConfig,
        CrossChainBridge,
        DEXProtocol,
        ERC20_ABI,
        PoolInfo,
        RealDeFiClient,
        SwapQuote,
        TokenInfo,
        UNISWAP_V2_PAIR_ABI,
        UNISWAP_V2_ROUTER_ABI
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in blockchain: {e}')

__all__ = [
    'BlockchainValidator',
    'ArbitrageOpportunity',
    'CHAIN_CONFIGS',
    'Chain',
    'ChainConfig',
    'CrossChainArbitrage',
    'CrossChainBridge',
    'DEXProtocol',
    'DeFiProtocol',
    'DeFiYieldOptimizer',
    'ERC20_ABI',
    'LiquidityMiningOptimizer',
    'PoolInfo',
    'RealDeFiClient',
    'SwapQuote',
    'TokenInfo',
    'UNISWAP_V2_PAIR_ABI',
    'UNISWAP_V2_ROUTER_ABI',
    'YieldOpportunity',
    'retry',
]

class BlockchainValidator:
    """Stub for BlockchainValidator."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}

"""
Blockchain & DeFi Integration Module (Ideas 181-210)
======================================================
On-chain analytics and DeFi protocol integration.

Most submodules were removed in the repo merge; imports are
guarded so the package stays importable with partial contents.
"""

import importlib as _il
import logging as _logging

_logger = _logging.getLogger(__name__)

_EXPORTS = {
    "on_chain_analytics": ["OnChainAnalytics"],
    "whale_tracker": ["WhaleTracker"],
    "defi_integration": ["DeFiIntegration"],
    "yield_farming": ["YieldFarmingOptimizer"],
    "liquidity_pool": ["LiquidityPoolManager"],
    "mev_protection": ["MEVProtection"],
    "cross_chain_arbitrage": ["CrossChainArbitrage"],
    "nft_analyzer": ["NFTAnalyzer"],
    "token_launch_detector": ["TokenLaunchDetector"],
    "smart_contract_risk": ["SmartContractRiskAnalyzer"],
    "governance_token": ["GovernanceTokenVoter"],
    "staking_optimizer": ["StakingOptimizer"],
    "bridge_monitor": ["BridgeMonitor"],
    "dex_aggregator": ["DEXAggregator"],
    "perpetual_arbitrage": ["PerpetualArbitrage"],
    "funding_rate_trader": ["FundingRateTrader"],
    "liquidation_detector": ["LiquidationDetector"],
    "token_unlock_tracker": ["TokenUnlockTracker"],
    "airdrop_farming": ["AirdropFarming"],
    "dao_treasury": ["DAOTreasuryAnalyzer"],
    "stablecoin_monitor": ["StablecoinMonitor"],
    "layer2_analytics": ["Layer2Analytics"],
    "oracle_monitor": ["OracleMonitor"],
    "flash_loan_detector": ["FlashLoanDetector"],
    "token_burn_tracker": ["TokenBurnTracker"],
    "protocol_revenue": ["ProtocolRevenueAnalyzer"],
    "tvl_monitor": ["TVLMonitor"],
    "validator_tracker": ["ValidatorTracker"],
    "gas_optimizer": ["GasOptimizer"],
    "cross_chain_identity": ["CrossChainIdentity"],
}

for _mod, _names in _EXPORTS.items():
    try:
        _m = _il.import_module(f".{_mod}", __name__)
        for _n in _names:
            globals()[_n] = getattr(_m, _n)
    except Exception as _e:
        _logger.debug(f"blockchain_defi.{_mod} unavailable: {_e}")
        for _n in _names:
            globals()[_n] = None

__all__ = [n for names in _EXPORTS.values() for n in names]

"""
Skill #84: Crypto On-Chain Analyzer
===================================

Analyzes on-chain metrics for crypto trading signals.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class OnChainResult:
    """On-chain analysis result."""
    active_addresses: int
    transaction_volume: float
    whale_movements: List[Dict]
    exchange_flow: float
    trading_signal: str


class CryptoOnChainAnalyzer:
    """Analyzes crypto on-chain data."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("CryptoOnChainAnalyzer initialized")
    
    def analyze(self, onchain_data: Dict) -> OnChainResult:
        """Analyze on-chain metrics."""
        if not onchain_data:
            return OnChainResult(0, 0, [], 0, "No on-chain data")
        
        addresses = onchain_data.get('active_addresses', 0)
        tx_volume = onchain_data.get('transaction_volume', 0)
        whales = onchain_data.get('whale_transactions', [])
        
        # Exchange flow (negative = outflow = bullish)
        inflow = onchain_data.get('exchange_inflow', 0)
        outflow = onchain_data.get('exchange_outflow', 0)
        net_flow = inflow - outflow
        
        signal = "BULLISH" if net_flow < 0 else "BEARISH" if net_flow > 0 else "NEUTRAL"
        
        return OnChainResult(
            active_addresses=addresses, transaction_volume=tx_volume,
            whale_movements=whales[:5], exchange_flow=net_flow,
            trading_signal=f"ON-CHAIN {signal}: Net exchange flow {net_flow:,.0f}"
        )

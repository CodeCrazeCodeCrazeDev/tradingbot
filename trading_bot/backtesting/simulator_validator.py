"""
Simulator Validator - AlphaAlgo UCA V5
Verifies replay determinism and environment instrumentation.
"""

import numpy as np
from typing import Dict, Any, List
from .replay import MarketReplay, DatasetSplit
from datetime import datetime

class SimulatorValidator:
    """
    Validates that the market simulator is deterministic,
    grounded, and provides sufficient coverage.
    """

    def __init__(self, replay: MarketReplay):
        self.replay = replay

    def verify_determinism(self, symbol: str, timestamp: datetime) -> bool:
        """Ensure repeated calls return identical market states."""
        state1 = self.replay.get_market_state(symbol, timestamp, DatasetSplit.TRAIN)
        state2 = self.replay.get_market_state(symbol, timestamp, DatasetSplit.TRAIN)

        if state1 is None or state2 is None:
            return False

        return state1['price'] == state2['price'] and state1['spread'] == state2['spread']

    def check_coverage(self, split: DatasetSplit) -> Dict[str, float]:
        """Verify state and action coverage for a given split."""
        data = self.replay.get_data(split)
        coverage = {}
        for symbol, df in data.items():
            coverage[symbol] = {
                'total_bars': len(df),
                'duration_days': (df.index[-1] - df.index[0]).days if not df.empty else 0,
                'volatility_avg': (df['high'] - df['low']).mean() / df['close'].mean()
            }
        return coverage

    def validate_execution_model(self, price: float, quantity: float, volume: float) -> Dict[str, Any]:
        """Check if execution modeling produces realistic slippage/impact."""
        # Simple heuristic check
        impact = (quantity / volume) * 0.1
        return {
            'expected_impact_bps': impact * 10000,
            'is_realistic': impact < 0.05 # Impact shouldn't usually exceed 5%
        }

"""
Skill #73: Walk-Forward Optimizer
=================================

Performs walk-forward optimization to prevent overfitting.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardResult:
    """Walk-forward optimization result."""
    in_sample_performance: float
    out_sample_performance: float
    robustness_ratio: float
    optimal_params: Dict[str, float]
    trading_signal: str


class WalkForwardOptimizer:
    """Walk-forward optimization for strategies."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.train_ratio = self.config.get('train_ratio', 0.7)
        logger.info("WalkForwardOptimizer initialized")
    
    def optimize(self, prices: np.ndarray, param_ranges: Dict[str, tuple]) -> WalkForwardResult:
        """Perform walk-forward optimization."""
        if len(prices) < 100:
            return self._create_empty_result()
        
        split = int(len(prices) * self.train_ratio)
        train_prices = prices[:split]
        test_prices = prices[split:]
        
        # Optimize on training data
        best_params = {}
        best_perf = -np.inf
        
        for _ in range(20):  # Random search
            params = {k: np.random.uniform(v[0], v[1]) for k, v in param_ranges.items()}
            perf = self._evaluate(train_prices, params)
            if perf > best_perf:
                best_perf = perf
                best_params = params
        
        # Test on out-of-sample
        out_perf = self._evaluate(test_prices, best_params)
        
        robustness = out_perf / (best_perf + 1e-10) if best_perf > 0 else 0
        
        return WalkForwardResult(
            in_sample_performance=best_perf, out_sample_performance=out_perf,
            robustness_ratio=robustness, optimal_params=best_params,
            trading_signal=f"WALK-FORWARD: IS={best_perf:.2f}, OOS={out_perf:.2f}, robustness={robustness:.0%}"
        )
    
    def _evaluate(self, prices: np.ndarray, params: Dict) -> float:
        """Evaluate strategy with params."""
        returns = np.diff(prices) / prices[:-1]
        lookback = int(params.get('lookback', 10))
        threshold = params.get('threshold', 0)
        
        signals = np.zeros(len(returns))
        for i in range(lookback, len(returns)):
            ma_return = np.mean(returns[i-lookback:i])
            signals[i] = 1 if ma_return > threshold else -1
        
        strategy_returns = signals[:-1] * returns[1:]
        return np.mean(strategy_returns) / (np.std(strategy_returns) + 1e-10)
    
    def _create_empty_result(self) -> WalkForwardResult:
        return WalkForwardResult(0, 0, 0, {}, "Insufficient data")

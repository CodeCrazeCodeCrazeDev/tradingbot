"""
Performance Benchmarks - AlphaAlgo Production Readiness
Enforces no-regression policy for institutional metrics.
"""

from typing import Dict, Any, List
import numpy as np

class PerformanceBenchmarks:
    """
    Measures and validates system performance against production thresholds.
    """

    THRESHOLDS = {
        'sharpe_ratio': 1.5,
        'sortino_ratio': 1.8,
        'max_drawdown': 0.15,
        'profit_factor': 1.4,
        'win_rate': 0.52,
        'slippage_bps': 2.0,
        'execution_latency_ms': 500
    }

    @staticmethod
    def validate_metrics(metrics: Dict[str, float]) -> Dict[str, Any]:
        """Verify metrics against institutional thresholds."""
        results = {}
        for key, threshold in PerformanceBenchmarks.THRESHOLDS.items():
            if key in metrics:
                if 'drawdown' in key or 'latency' in key or 'slippage' in key:
                    passed = metrics[key] <= threshold
                else:
                    passed = metrics[key] >= threshold
                results[key] = {
                    'value': metrics[key],
                    'threshold': threshold,
                    'passed': passed
                }
        return results

    @staticmethod
    def check_oos_decay(is_sharpe: float, oos_sharpe: float) -> bool:
        """Enforce that OOS performance doesn't decay more than 50%."""
        if is_sharpe <= 0: return False
        return (oos_sharpe / is_sharpe) >= 0.5

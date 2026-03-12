"""
Skill #60: Portfolio Stress Tester
==================================

Comprehensive stress testing for portfolio risk assessment.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class StressTestResult:
    """Stress test result."""
    scenario_results: Dict[str, float]
    worst_scenario: str
    worst_loss: float
    avg_stress_loss: float
    passes_stress_test: bool
    trading_signal: str


class PortfolioStressTester:
    """Comprehensive portfolio stress testing."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.max_acceptable_loss = self.config.get('max_acceptable_loss', 0.2)
            logger.info("PortfolioStressTester initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def test(self, portfolio_value: float, positions: Dict[str, float], sensitivities: Dict[str, float]) -> StressTestResult:
        """Run stress tests on portfolio."""
        try:
            scenarios = {
                '2008_crisis': {'equity': -0.50, 'vol': 0.80, 'rates': -0.02},
                'covid_crash': {'equity': -0.35, 'vol': 0.60, 'rates': -0.01},
                'rate_shock': {'equity': -0.10, 'vol': 0.20, 'rates': 0.02},
                'flash_crash': {'equity': -0.10, 'vol': 1.00, 'rates': 0},
                'gradual_bear': {'equity': -0.25, 'vol': 0.30, 'rates': 0},
            }
        
            results = {}
            for name, shocks in scenarios.items():
                loss = 0
                for factor, shock in shocks.items():
                    sens = sensitivities.get(factor, 0)
                    loss += sens * shock * portfolio_value
                results[name] = loss
        
            worst = min(results, key=results.get)
            worst_loss = results[worst]
            avg_loss = np.mean(list(results.values()))
            passes = abs(worst_loss) < portfolio_value * self.max_acceptable_loss
        
            signal = self._generate_signal(worst, worst_loss, passes, portfolio_value)
        
            return StressTestResult(
                scenario_results=results, worst_scenario=worst,
                worst_loss=worst_loss, avg_stress_loss=avg_loss,
                passes_stress_test=passes, trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in test: {e}")
            raise
    
    def _generate_signal(self, worst: str, loss: float, passes: bool, value: float) -> str:
        try:
            pct = loss / value if value > 0 else 0
            if not passes:
                return f"FAILS STRESS TEST: {worst} causes {pct:.0%} loss"
            return f"PASSES: Worst case {worst} = {pct:.0%} loss"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise

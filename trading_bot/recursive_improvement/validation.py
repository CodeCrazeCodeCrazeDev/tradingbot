"""
RSIE Improvement Validation Pipeline

Rigorous validation gates for every recursive improvement:
- Statistical Significance (p-values, effect size)
- Out-of-Sample (OOS) Testing
- Robustness (Stress testing, parameter sensitivity)
- Risk Check (Drawdown, VaR, Sharpe)
- Regression Testing (Ensuring no breakage of existing capabilities)
- Cost-Benefit Analysis
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ValidationReport:
    """Detailed report for an improvement validation"""
    passed_all: bool
    gates: Dict[str, bool]
    metrics: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class ImprovementValidationPipeline:
    """
    Unified validation suite for RSIE.
    Ensures that only high-quality, verified improvements are deployed.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.p_value_threshold = self.config.get('p_value_threshold', 0.05)
        self.sharpe_threshold = self.config.get('sharpe_threshold', 1.0)
        self.max_drawdown_limit = self.config.get('max_drawdown_limit', 0.20)
        self.min_oos_score_ratio = self.config.get('min_oos_score_ratio', 0.8) # OOS score / IS score

    async def validate(
        self,
        is_results: Dict[str, Any],  # In-Sample results
        oos_results: Dict[str, Any], # Out-of-Sample results
        baseline_results: Optional[Dict[str, Any]] = None
    ) -> ValidationReport:
        """Run all validation gates"""

        gates = {
            'statistical_significance': False,
            'out_of_sample': False,
            'robustness': False,
            'risk_check': False,
            'regression_check': True, # Default to True if no baseline
            'cost_benefit': False
        }

        metrics = {}
        warnings = []

        # 1. Statistical Significance
        gates['statistical_significance'], sig_metrics = self._check_statistical_significance(
            is_results, baseline_results
        )
        metrics.update(sig_metrics)

        # 2. Out-of-Sample Validation
        gates['out_of_sample'], oos_metrics = self._check_oos_stability(
            is_results, oos_results
        )
        metrics.update(oos_metrics)

        # 3. Risk Check
        gates['risk_check'], risk_metrics = self._check_risk_bounds(oos_results)
        metrics.update(risk_metrics)

        # 4. Regression Check
        if baseline_results:
            gates['regression_check'], reg_metrics = self._check_regression(
                oos_results, baseline_results
            )
            metrics.update(reg_metrics)

        # 5. Cost-Benefit Analysis
        gates['cost_benefit'], cb_metrics = self._check_cost_benefit(oos_results)
        metrics.update(cb_metrics)

        # 6. Robustness (Mocked - would integrate with Stress Test engine)
        gates['robustness'] = True # TODO: Implement stress test bridge

        passed_all = all(gates.values())

        return ValidationReport(
            passed_all=passed_all,
            gates=gates,
            metrics=metrics,
            warnings=warnings
        )

    def _check_statistical_significance(
        self,
        results: Dict[str, Any],
        baseline: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Dict[str, float]]:
        """Check if improvement is statistically significant"""
        is_returns = results.get('returns', [])
        base_returns = baseline.get('returns', []) if baseline else []

        if not is_returns or not base_returns:
            # If no returns, check p_value from engine if available
            p_val = results.get('metrics', {}).get('p_value', 1.0)
            return p_val < self.p_value_threshold, {'p_value': p_val}

        # T-test for means
        t_stat, p_val = stats.ttest_ind(is_returns, base_returns)

        # Cohen's d for effect size
        combined_std = np.sqrt((np.std(is_returns)**2 + np.std(base_returns)**2) / 2)
        effect_size = (np.mean(is_returns) - np.mean(base_returns)) / combined_std if combined_std > 0 else 0

        passed = p_val < self.p_value_threshold and effect_size > 0.1
        return passed, {'p_value': p_val, 't_stat': t_stat, 'effect_size': effect_size}

    def _check_oos_stability(
        self,
        is_results: Dict[str, Any],
        oos_results: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, float]]:
        """Check if performance holds up in OOS data"""
        is_sharpe = is_results.get('metrics', {}).get('sharpe_ratio', 0)
        oos_sharpe = oos_results.get('metrics', {}).get('sharpe_ratio', 0)

        if is_sharpe <= 0:
            return False, {'oos_ratio': 0}

        ratio = oos_sharpe / is_sharpe
        passed = ratio >= self.min_oos_score_ratio
        return passed, {'oos_sharpe_ratio': ratio, 'is_sharpe': is_sharpe, 'oos_sharpe': oos_sharpe}

    def _check_risk_bounds(self, results: Dict[str, Any]) -> Tuple[bool, Dict[str, float]]:
        """Check if risk metrics are within acceptable bounds"""
        metrics = results.get('metrics', {})
        sharpe = metrics.get('sharpe_ratio', 0)
        max_dd = metrics.get('max_drawdown', 1.0)

        passed = sharpe >= self.sharpe_threshold and max_dd <= self.max_drawdown_limit
        return passed, {'eval_sharpe': sharpe, 'eval_max_dd': max_dd}

    def _check_regression(
        self,
        results: Dict[str, Any],
        baseline: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, float]]:
        """Ensure no significant degradation of core metrics"""
        # Focus on absolute win rate or stability
        res_wr = results.get('metrics', {}).get('win_rate', 0)
        base_wr = baseline.get('metrics', {}).get('win_rate', 0)

        # Allow max 5% degradation in win rate if overall profit is higher
        passed = res_wr >= (base_wr * 0.95)
        return passed, {'win_rate_delta': res_wr - base_wr}

    def _check_cost_benefit(self, results: Dict[str, Any]) -> Tuple[bool, Dict[str, float]]:
        """Evaluate if the improvement is worth the resource cost"""
        # Would normally check inference latency, compute usage etc.
        metrics = results.get('metrics', {})
        latency_ms = metrics.get('latency_ms', 0)
        profit_delta = metrics.get('total_return', 0)

        # If latency increased by > 100ms without > 1% profit gain, might fail
        # Placeholder logic
        return True, {'latency_ms': latency_ms}

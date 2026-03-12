"""
Promotion System for Adversarial Curriculum Learning

Implements rigorous statistical validation for level advancement.
No shortcuts. No vanity metrics. Statistical dominance required.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from .core_types import (
    CurriculumLevel,
    EpisodeResult,
    FailureMode,
    LevelConfig,
    MarketRegime,
    PromotionGate,
    PromotionResult,
    get_level_config,
    get_promotion_gate,
)

logger = logging.getLogger(__name__)


# =============================================================================
# STATISTICAL VALIDATOR
# =============================================================================

class StatisticalValidator:
    """
    Validates performance metrics with statistical rigor.
    No 100% accuracy criteria - only statistical confidence.
    """
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
    
    def test_positive_expectancy(
        self,
        returns: List[float],
        min_samples: int = 30
    ) -> Tuple[bool, float, str]:
        """
        Test if returns have statistically significant positive expectancy.
        
        Returns:
            Tuple of (passed, p_value, explanation)
        """
        if len(returns) < min_samples:
            return False, 1.0, f"Insufficient samples: {len(returns)} < {min_samples}"
        
        # One-sample t-test against zero
        t_stat, p_value = stats.ttest_1samp(returns, 0)
        
        # We want positive expectancy, so check if mean > 0 and significant
        mean_return = np.mean(returns)
        
        if mean_return <= 0:
            return False, p_value, f"Negative expectancy: mean={mean_return:.4f}"
        
        # One-tailed test
        p_value_one_tailed = p_value / 2 if t_stat > 0 else 1 - p_value / 2
        
        passed = p_value_one_tailed < (1 - self.confidence_level)
        
        explanation = (
            f"Mean return: {mean_return:.4f}, "
            f"t-stat: {t_stat:.2f}, "
            f"p-value (one-tailed): {p_value_one_tailed:.4f}"
        )
        
        return passed, p_value_one_tailed, explanation
    
    def test_sharpe_significance(
        self,
        sharpe_ratios: List[float],
        min_sharpe: float,
        min_samples: int = 10
    ) -> Tuple[bool, float, str]:
        """
        Test if Sharpe ratio is significantly above threshold.
        """
        if len(sharpe_ratios) < min_samples:
            return False, 1.0, f"Insufficient samples: {len(sharpe_ratios)} < {min_samples}"
        
        mean_sharpe = np.mean(sharpe_ratios)
        std_sharpe = np.std(sharpe_ratios)
        
        if std_sharpe == 0:
            passed = mean_sharpe >= min_sharpe
            return passed, 0.0 if passed else 1.0, f"Zero variance, mean={mean_sharpe:.3f}"
        
        # t-test against threshold
        t_stat = (mean_sharpe - min_sharpe) / (std_sharpe / np.sqrt(len(sharpe_ratios)))
        p_value = 1 - stats.t.cdf(t_stat, len(sharpe_ratios) - 1)
        
        passed = p_value < (1 - self.confidence_level) and mean_sharpe >= min_sharpe
        
        explanation = (
            f"Mean Sharpe: {mean_sharpe:.3f} (threshold: {min_sharpe}), "
            f"std: {std_sharpe:.3f}, p-value: {p_value:.4f}"
        )
        
        return passed, p_value, explanation
    
    def test_drawdown_bound(
        self,
        drawdowns: List[float],
        max_allowed: float,
        confidence: float = 0.95
    ) -> Tuple[bool, float, str]:
        """
        Test if drawdowns are bounded with high confidence.
        Uses bootstrap to estimate upper confidence bound.
        """
        if len(drawdowns) < 10:
            return False, 1.0, f"Insufficient samples: {len(drawdowns)}"
        
        # Bootstrap confidence interval for max drawdown
        n_bootstrap = 1000
        bootstrap_maxes = []
        
        for _ in range(n_bootstrap):
            sample = np.random.choice(drawdowns, size=len(drawdowns), replace=True)
            bootstrap_maxes.append(np.max(sample))
        
        upper_bound = np.percentile(bootstrap_maxes, confidence * 100)
        
        passed = upper_bound <= max_allowed
        
        explanation = (
            f"Max observed: {np.max(drawdowns):.3f}, "
            f"{confidence:.0%} upper bound: {upper_bound:.3f}, "
            f"threshold: {max_allowed:.3f}"
        )
        
        return passed, upper_bound, explanation
    
    def test_consistency_across_seeds(
        self,
        seed_results: Dict[int, List[float]],
        max_variance_ratio: float = 0.3
    ) -> Tuple[bool, float, str]:
        """
        Test if performance is consistent across random seeds.
        """
        if len(seed_results) < 3:
            return False, 1.0, f"Insufficient seeds: {len(seed_results)} < 3"
        
        seed_means = [np.mean(results) for results in seed_results.values()]
        
        overall_mean = np.mean(seed_means)
        overall_std = np.std(seed_means)
        
        if overall_mean == 0:
            variance_ratio = float('inf') if overall_std > 0 else 0
        else:
            variance_ratio = overall_std / abs(overall_mean)
        
        passed = variance_ratio <= max_variance_ratio
        
        explanation = (
            f"Seed means: {[f'{m:.3f}' for m in seed_means]}, "
            f"variance ratio: {variance_ratio:.3f} (max: {max_variance_ratio})"
        )
        
        return passed, variance_ratio, explanation
    
    def test_no_regime_dependence(
        self,
        regime_results: Dict[MarketRegime, List[float]],
        min_regimes: int = 3
    ) -> Tuple[bool, float, str]:
        """
        Test if performance doesn't depend on a single regime.
        Uses ANOVA to check for significant regime effects.
        """
        valid_regimes = {k: v for k, v in regime_results.items() if len(v) >= 5}
        
        if len(valid_regimes) < min_regimes:
            return False, 1.0, f"Insufficient regimes with data: {len(valid_regimes)} < {min_regimes}"
        
        # ANOVA test
        groups = list(valid_regimes.values())
        f_stat, p_value = stats.f_oneway(*groups)
        
        # We want NO significant difference between regimes
        # So we want p_value > 0.05 (fail to reject null hypothesis)
        passed = p_value > 0.05
        
        regime_means = {k.name: np.mean(v) for k, v in valid_regimes.items()}
        
        explanation = (
            f"Regime means: {regime_means}, "
            f"F-stat: {f_stat:.2f}, p-value: {p_value:.4f} "
            f"({'No' if passed else 'Significant'} regime dependence)"
        )
        
        return passed, p_value, explanation


# =============================================================================
# OUT-OF-DISTRIBUTION TESTER
# =============================================================================

class OODTester:
    """
    Tests agent performance on out-of-distribution scenarios.
    Promotion is invalid without passing OOD tests.
    """
    
    def __init__(self, degradation_threshold: float = 0.25):
        self.degradation_threshold = degradation_threshold
    
    def generate_ood_scenarios(self, level: CurriculumLevel) -> List[Dict[str, Any]]:
        """
        Generate OOD test scenarios for a given level.
        """
        scenarios = []
        
        # Scenario 1: Inverted regime patterns
        scenarios.append({
            'name': 'inverted_regimes',
            'description': 'Regime patterns are inverted from training',
            'modifications': {
                'regime_inversion': True,
                'volatility_multiplier': 1.5,
            }
        })
        
        # Scenario 2: Extreme volatility
        scenarios.append({
            'name': 'extreme_volatility',
            'description': '3x normal volatility',
            'modifications': {
                'volatility_multiplier': 3.0,
                'spread_multiplier': 2.0,
            }
        })
        
        # Scenario 3: Liquidity drought
        scenarios.append({
            'name': 'liquidity_drought',
            'description': '80% reduction in liquidity',
            'modifications': {
                'liquidity_multiplier': 0.2,
                'slippage_multiplier': 5.0,
            }
        })
        
        # Scenario 4: Correlation breakdown
        if level.value >= 6:
            scenarios.append({
                'name': 'correlation_flip',
                'description': 'All correlations flip sign',
                'modifications': {
                    'correlation_flip': True,
                }
            })
        
        # Scenario 5: Adversarial patterns
        if level.value >= 5:
            scenarios.append({
                'name': 'adversarial_patterns',
                'description': 'Increased fake signals and stop hunting',
                'modifications': {
                    'fake_signal_multiplier': 3.0,
                    'stop_hunt_multiplier': 3.0,
                }
            })
        
        # Scenario 6: Non-stationary dynamics
        if level.value >= 8:
            scenarios.append({
                'name': 'non_stationary',
                'description': 'Market dynamics change mid-episode',
                'modifications': {
                    'mid_episode_regime_change': True,
                    'rule_change_probability': 0.1,
                }
            })
        
        return scenarios
    
    def evaluate_ood_performance(
        self,
        in_distribution_results: List[EpisodeResult],
        ood_results: List[EpisodeResult],
        scenario_name: str
    ) -> Tuple[bool, float, str]:
        """
        Evaluate if OOD performance degradation is acceptable.
        """
        if not in_distribution_results or not ood_results:
            return False, 1.0, "Missing results for comparison"
        
        # Compare key metrics
        id_sharpe = np.mean([r.sharpe_ratio for r in in_distribution_results])
        ood_sharpe = np.mean([r.sharpe_ratio for r in ood_results])
        
        id_return = np.mean([r.total_return for r in in_distribution_results])
        ood_return = np.mean([r.total_return for r in ood_results])
        
        id_drawdown = np.mean([r.max_drawdown for r in in_distribution_results])
        ood_drawdown = np.mean([r.max_drawdown for r in ood_results])
        
        # Calculate degradation
        sharpe_degradation = (id_sharpe - ood_sharpe) / (abs(id_sharpe) + 1e-8)
        return_degradation = (id_return - ood_return) / (abs(id_return) + 1e-8)
        drawdown_increase = (ood_drawdown - id_drawdown) / (id_drawdown + 1e-8)
        
        # Composite degradation score
        degradation = max(sharpe_degradation, return_degradation, drawdown_increase)
        
        passed = degradation <= self.degradation_threshold
        
        explanation = (
            f"Scenario: {scenario_name}, "
            f"Sharpe: {id_sharpe:.3f} -> {ood_sharpe:.3f} ({sharpe_degradation:+.1%}), "
            f"Return: {id_return:.3f} -> {ood_return:.3f} ({return_degradation:+.1%}), "
            f"Drawdown: {id_drawdown:.3f} -> {ood_drawdown:.3f} ({drawdown_increase:+.1%})"
        )
        
        return passed, degradation, explanation


# =============================================================================
# ROBUSTNESS CHECKER
# =============================================================================

class RobustnessChecker:
    """
    Checks for various robustness criteria.
    """
    
    def check_no_martingale(
        self,
        results: List[EpisodeResult],
        threshold: float = 0.3
    ) -> Tuple[bool, str]:
        """
        Check if agent exhibits martingale-like behavior (doubling down on losses).
        """
        violations = 0
        total_checked = 0
        
        for result in results:
            trades = result.winning_trades + result.losing_trades
            if trades < 10:
                continue
            
            total_checked += 1
            
            # Check for increasing position sizes after losses
            # This is a simplified check - in practice would analyze trade history
            if result.max_leverage_used > 3.0 and result.losing_trades > result.winning_trades:
                violations += 1
        
        if total_checked == 0:
            return True, "No episodes with sufficient trades to check"
        
        violation_rate = violations / total_checked
        passed = violation_rate < threshold
        
        return passed, f"Martingale violation rate: {violation_rate:.1%} (threshold: {threshold:.1%})"
    
    def check_no_leverage_abuse(
        self,
        results: List[EpisodeResult],
        max_leverage: float = 3.0
    ) -> Tuple[bool, str]:
        """
        Check if agent abuses leverage.
        """
        violations = sum(1 for r in results if r.max_leverage_used > max_leverage)
        violation_rate = violations / len(results) if results else 0
        
        passed = violation_rate < 0.1  # Allow 10% of episodes with high leverage
        
        return passed, f"Leverage violations: {violations}/{len(results)} ({violation_rate:.1%})"
    
    def check_no_tail_risk_hiding(
        self,
        results: List[EpisodeResult],
        max_tail_ratio: float = 2.0
    ) -> Tuple[bool, str]:
        """
        Check if agent is hiding tail risk (large CVaR relative to VaR).
        """
        tail_ratios = [r.tail_ratio for r in results if r.var_95 != 0]
        
        if not tail_ratios:
            return True, "No tail ratio data available"
        
        avg_tail_ratio = np.mean(tail_ratios)
        max_observed = np.max(tail_ratios)
        
        passed = avg_tail_ratio <= max_tail_ratio and max_observed <= max_tail_ratio * 1.5
        
        return passed, f"Avg tail ratio: {avg_tail_ratio:.2f}, max: {max_observed:.2f} (threshold: {max_tail_ratio})"
    
    def check_trade_frequency(
        self,
        results: List[EpisodeResult],
        max_frequency: float = 0.5
    ) -> Tuple[bool, str]:
        """
        Check if agent trades excessively (potential overfit to noise).
        """
        frequencies = [r.trade_frequency for r in results]
        avg_frequency = np.mean(frequencies)
        
        passed = avg_frequency <= max_frequency
        
        return passed, f"Avg trade frequency: {avg_frequency:.3f} (max: {max_frequency})"


# =============================================================================
# PROMOTION EVALUATOR
# =============================================================================

class PromotionEvaluator:
    """
    Main evaluator for level promotion decisions.
    Combines all validation components.
    """
    
    def __init__(self):
        self.statistical_validator = StatisticalValidator()
        self.ood_tester = OODTester()
        self.robustness_checker = RobustnessChecker()
    
    def evaluate_promotion(
        self,
        level: CurriculumLevel,
        results: List[EpisodeResult],
        ood_results: Optional[Dict[str, List[EpisodeResult]]] = None
    ) -> PromotionResult:
        """
        Evaluate if agent should be promoted to next level.
        
        Args:
            level: Current level
            results: Episode results from current level
            ood_results: OOD test results by scenario name
            
        Returns:
            PromotionResult with decision and details
        """
        gate = get_promotion_gate(level)
        failure_reasons = []
        recommendations = []
        
        # 1. Check minimum episodes
        if len(results) < gate.min_episodes:
            failure_reasons.append(f"Insufficient episodes: {len(results)} < {gate.min_episodes}")
        
        # 2. Statistical validation of positive expectancy
        returns = [r.total_return for r in results]
        passed, p_value, explanation = self.statistical_validator.test_positive_expectancy(returns)
        if not passed:
            failure_reasons.append(f"Failed positive expectancy test: {explanation}")
        
        # 3. Sharpe ratio validation
        sharpes = [r.sharpe_ratio for r in results]
        passed, p_value, explanation = self.statistical_validator.test_sharpe_significance(
            sharpes, gate.min_sharpe
        )
        if not passed:
            failure_reasons.append(f"Failed Sharpe test: {explanation}")
        
        # 4. Drawdown bound validation
        drawdowns = [r.max_drawdown for r in results]
        passed, upper_bound, explanation = self.statistical_validator.test_drawdown_bound(
            drawdowns, gate.max_drawdown
        )
        if not passed:
            failure_reasons.append(f"Failed drawdown test: {explanation}")
        
        # 5. Seed consistency validation
        seed_results = {}
        for r in results:
            if r.seed not in seed_results:
                seed_results[r.seed] = []
            seed_results[r.seed].append(r.sharpe_ratio)
        
        passed, variance_ratio, explanation = self.statistical_validator.test_consistency_across_seeds(
            seed_results, gate.max_seed_variance
        )
        if not passed:
            failure_reasons.append(f"Failed seed consistency: {explanation}")
            recommendations.append("Train with more diverse random seeds")
        
        # 6. Regime independence validation
        regime_results = {}
        for r in results:
            for regime in r.regimes_encountered:
                if regime not in regime_results:
                    regime_results[regime] = []
                regime_results[regime].append(r.sharpe_ratio)
        
        passed, p_value, explanation = self.statistical_validator.test_no_regime_dependence(regime_results)
        if not passed:
            failure_reasons.append(f"Failed regime independence: {explanation}")
            recommendations.append("Improve adaptation to different market regimes")
        
        # 7. OOD validation
        if ood_results:
            ood_failures = 0
            for scenario_name, scenario_results in ood_results.items():
                passed, degradation, explanation = self.ood_tester.evaluate_ood_performance(
                    results, scenario_results, scenario_name
                )
                if not passed:
                    ood_failures += 1
                    failure_reasons.append(f"Failed OOD test ({scenario_name}): {explanation}")
            
            if ood_failures > 0:
                recommendations.append(f"Improve generalization - failed {ood_failures} OOD tests")
        else:
            failure_reasons.append("No OOD tests performed - promotion invalid")
        
        # 8. Robustness checks
        passed, explanation = self.robustness_checker.check_no_martingale(results)
        if not passed:
            failure_reasons.append(f"Martingale behavior detected: {explanation}")
            recommendations.append("Implement proper position sizing without doubling down")
        
        passed, explanation = self.robustness_checker.check_no_leverage_abuse(results, gate.max_leverage)
        if not passed:
            failure_reasons.append(f"Leverage abuse detected: {explanation}")
            recommendations.append("Reduce maximum leverage usage")
        
        passed, explanation = self.robustness_checker.check_no_tail_risk_hiding(results)
        if not passed:
            failure_reasons.append(f"Tail risk hiding detected: {explanation}")
            recommendations.append("Improve tail risk management")
        
        passed, explanation = self.robustness_checker.check_trade_frequency(results, gate.max_trade_frequency)
        if not passed:
            failure_reasons.append(f"Excessive trading detected: {explanation}")
            recommendations.append("Reduce trade frequency - may be overfitting to noise")
        
        # 9. Check for rule violations
        total_violations = sum(len(r.rule_violations) + len(r.anti_cheat_flags) for r in results)
        if total_violations > 0:
            failure_reasons.append(f"Rule violations detected: {total_violations}")
            recommendations.append("Review and fix rule violations before promotion")
        
        # Calculate aggregate metrics
        avg_sharpe = np.mean(sharpes)
        avg_sortino = np.mean([r.sortino_ratio for r in results])
        avg_drawdown = np.mean(drawdowns)
        avg_win_rate = np.mean([r.win_rate for r in results])
        avg_profit_factor = np.mean([r.profit_factor for r in results])
        
        # Determine promotion
        promoted = len(failure_reasons) == 0
        next_level = CurriculumLevel(level.value + 1) if promoted and level.value < 10 else None
        
        if promoted:
            logger.info(f"PROMOTION APPROVED: Level {level.value} -> {next_level.value if next_level else 'MAX'}")
        else:
            logger.warning(f"PROMOTION DENIED: Level {level.value}, {len(failure_reasons)} failures")
        
        return PromotionResult(
            level=level,
            promoted=promoted,
            next_level=next_level,
            episodes_evaluated=len(results),
            seeds_tested=len(seed_results),
            ood_tests_passed=len(ood_results) - sum(1 for r in failure_reasons if 'OOD' in r) if ood_results else 0,
            avg_sharpe=avg_sharpe,
            avg_sortino=avg_sortino,
            avg_drawdown=avg_drawdown,
            avg_win_rate=avg_win_rate,
            avg_profit_factor=avg_profit_factor,
            failure_reasons=failure_reasons,
            recommendations=recommendations,
        )
    
    def generate_promotion_report(self, result: PromotionResult) -> str:
        """Generate a detailed promotion report."""
        lines = [
            "=" * 70,
            f"PROMOTION EVALUATION REPORT - Level {result.level.value}",
            "=" * 70,
            "",
            f"Decision: {'✅ PROMOTED' if result.promoted else '❌ NOT PROMOTED'}",
            f"Next Level: {result.next_level.value if result.next_level else 'N/A'}",
            "",
            "EVALUATION METRICS:",
            f"  Episodes Evaluated: {result.episodes_evaluated}",
            f"  Seeds Tested: {result.seeds_tested}",
            f"  OOD Tests Passed: {result.ood_tests_passed}",
            "",
            "PERFORMANCE METRICS:",
            f"  Average Sharpe Ratio: {result.avg_sharpe:.3f}",
            f"  Average Sortino Ratio: {result.avg_sortino:.3f}",
            f"  Average Max Drawdown: {result.avg_drawdown:.3f}",
            f"  Average Win Rate: {result.avg_win_rate:.3f}",
            f"  Average Profit Factor: {result.avg_profit_factor:.3f}",
            "",
        ]
        
        if result.failure_reasons:
            lines.append("FAILURE REASONS:")
            for i, reason in enumerate(result.failure_reasons, 1):
                lines.append(f"  {i}. {reason}")
            lines.append("")
        
        if result.recommendations:
            lines.append("RECOMMENDATIONS:")
            for i, rec in enumerate(result.recommendations, 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)

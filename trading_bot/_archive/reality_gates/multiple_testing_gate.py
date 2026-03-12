"""
Multiple Testing Correction Gate - Preventing P-Hacking and Data Snooping

This gate prevents the classic mistake of testing many strategies and
picking the one that "worked" without accounting for multiple comparisons.

THE PROBLEM:
- Test 100 strategies
- 5 show "significant" results (p < 0.05)
- But with 100 tests, we EXPECT 5 false positives!
- Deploy the "best" one -> It was just luck

THE SOLUTION:
- Track all strategies/parameters tested
- Apply Bonferroni, Holm, or FDR corrections
- Require much higher significance for approval
- Penalize strategies from large search spaces

RULE: "If you tested 1000 things, you need 1000x more evidence."

Author: AlphaAlgo Reality Check System
"""

import logging
import math
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from collections import deque

logger = logging.getLogger(__name__)


class CorrectionMethod(Enum):
    """Multiple testing correction methods"""
    NONE = "none"  # No correction (dangerous!)
    BONFERRONI = "bonferroni"  # Most conservative
    HOLM = "holm"  # Step-down procedure
    BH_FDR = "benjamini_hochberg"  # False Discovery Rate
    BY_FDR = "benjamini_yekutieli"  # FDR under dependency
    DEFLATED_SHARPE = "deflated_sharpe"  # Bailey & Lopez de Prado


class OverfitRisk(Enum):
    """Risk level of overfitting"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class TestingCorrection:
    """Result of multiple testing correction"""
    original_pvalue: float
    corrected_pvalue: float
    original_sharpe: float
    deflated_sharpe: float
    
    num_tests: int
    correction_method: CorrectionMethod
    
    is_significant: bool
    overfit_risk: OverfitRisk
    
    # Probability this is a false discovery
    false_discovery_prob: float
    
    # Minimum required Sharpe given tests performed
    min_required_sharpe: float
    
    warnings: List[str] = field(default_factory=list)


@dataclass
class OverfitScore:
    """Comprehensive overfitting assessment"""
    score: float  # 0-1, higher = more likely overfit
    
    # Components
    search_space_penalty: float  # Penalty for large parameter space
    data_reuse_penalty: float  # Penalty for reusing same data
    complexity_penalty: float  # Penalty for model complexity
    selection_bias_penalty: float  # Penalty for cherry-picking
    
    # Risk assessment
    risk_level: OverfitRisk
    is_acceptable: bool
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)


class MultipleTestingGate:
    """
    HARD GATE: Multiple Testing Correction
    
    This gate BLOCKS strategies that haven't properly accounted for
    the multiple testing problem. No data snooping allowed.
    
    Tracks:
    1. Number of strategies tested
    2. Number of parameter combinations tried
    3. Number of times data was reused
    4. Selection process used
    
    Applies:
    1. P-value corrections (Bonferroni, Holm, FDR)
    2. Deflated Sharpe ratio (Bailey & Lopez de Prado)
    3. Overfit probability estimation
    4. Minimum significance thresholds
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Default correction method
        self.default_method = CorrectionMethod(
            self.config.get('correction_method', 'deflated_sharpe')
        )
        
        # Significance thresholds
        self.base_alpha = self.config.get('base_alpha', 0.05)
        self.min_deflated_sharpe = self.config.get('min_deflated_sharpe', 1.0)
        
        # Testing history
        self.test_registry: Dict[str, Dict] = {}  # strategy_id -> test info
        self.total_tests_performed = 0
        self.parameter_combinations_tried = 0
        
        # Data usage tracking
        self.data_usage: Dict[str, int] = {}  # data_hash -> times used
        
        # Statistics
        self.strategies_corrected = 0
        self.strategies_blocked = 0
        
        logger.info("MultipleTestingGate initialized - NO P-HACKING SHALL PASS")
    
    def register_test(
        self,
        strategy_id: str,
        num_parameters: int,
        parameter_ranges: Dict[str, Tuple[float, float]],
        data_hash: str,
        optimization_method: str = "grid_search"
    ):
        """
        Register a strategy test for tracking.
        
        Call this BEFORE running any backtest to properly track
        the multiple testing burden.
        """
        # Calculate search space size
        search_space_size = 1
        for param, (low, high) in parameter_ranges.items():
            # Estimate number of values tested
            if isinstance(low, int) and isinstance(high, int):
                search_space_size *= (high - low + 1)
            else:
                search_space_size *= 10  # Assume 10 values for continuous
        
        # Track data reuse
        self.data_usage[data_hash] = self.data_usage.get(data_hash, 0) + 1
        
        self.test_registry[strategy_id] = {
            'registered_at': datetime.utcnow(),
            'num_parameters': num_parameters,
            'parameter_ranges': parameter_ranges,
            'search_space_size': search_space_size,
            'data_hash': data_hash,
            'data_reuse_count': self.data_usage[data_hash],
            'optimization_method': optimization_method
        }
        
        self.total_tests_performed += 1
        self.parameter_combinations_tried += search_space_size
        
        logger.info(
            f"Registered test for {strategy_id}: "
            f"search_space={search_space_size}, data_reuse={self.data_usage[data_hash]}"
        )
    
    def correct_results(
        self,
        strategy_id: str,
        observed_sharpe: float,
        observed_pvalue: float,
        num_trades: int,
        backtest_years: float,
        method: Optional[CorrectionMethod] = None
    ) -> TestingCorrection:
        """
        Apply multiple testing correction to strategy results.
        
        Args:
            strategy_id: Strategy identifier (must be registered)
            observed_sharpe: Observed Sharpe ratio from backtest
            observed_pvalue: P-value of strategy performance
            num_trades: Number of trades in backtest
            backtest_years: Years of backtest data
            method: Correction method to use
            
        Returns:
            TestingCorrection with adjusted significance
        """
        self.strategies_corrected += 1
        method = method or self.default_method
        warnings = []
        
        # Get test info
        test_info = self.test_registry.get(strategy_id, {})
        search_space = test_info.get('search_space_size', self.total_tests_performed)
        data_reuse = test_info.get('data_reuse_count', 1)
        
        # Effective number of tests
        # Account for correlation between tests (not fully independent)
        independence_factor = 0.5  # Assume 50% correlation
        effective_tests = max(1, search_space * independence_factor * data_reuse)
        
        # 1. Correct p-value
        if method == CorrectionMethod.BONFERRONI:
            corrected_pvalue = min(1.0, observed_pvalue * effective_tests)
        elif method == CorrectionMethod.HOLM:
            corrected_pvalue = min(1.0, observed_pvalue * effective_tests)  # Simplified
        elif method in [CorrectionMethod.BH_FDR, CorrectionMethod.BY_FDR]:
            # FDR correction
            corrected_pvalue = min(1.0, observed_pvalue * effective_tests / math.log(effective_tests + 1))
        else:
            corrected_pvalue = observed_pvalue
        
        # 2. Calculate Deflated Sharpe Ratio (Bailey & Lopez de Prado)
        deflated_sharpe = self._calculate_deflated_sharpe(
            observed_sharpe=observed_sharpe,
            num_trials=effective_tests,
            backtest_years=backtest_years,
            num_trades=num_trades
        )
        
        # 3. Calculate minimum required Sharpe
        min_required_sharpe = self._min_sharpe_for_significance(
            num_trials=effective_tests,
            backtest_years=backtest_years
        )
        
        # 4. Estimate false discovery probability
        # Using Bayesian approach
        prior_prob_true = 0.01  # Only 1% of strategies are truly profitable
        false_discovery_prob = self._estimate_false_discovery(
            pvalue=corrected_pvalue,
            prior_prob=prior_prob_true
        )
        
        # 5. Determine significance
        is_significant = (
            corrected_pvalue < self.base_alpha and
            deflated_sharpe > self.min_deflated_sharpe and
            false_discovery_prob < 0.5
        )
        
        # 6. Assess overfit risk
        if effective_tests > 1000:
            overfit_risk = OverfitRisk.EXTREME
            warnings.append(f"Extreme search space: {effective_tests:.0f} effective tests")
        elif effective_tests > 100:
            overfit_risk = OverfitRisk.HIGH
            warnings.append(f"Large search space: {effective_tests:.0f} effective tests")
        elif effective_tests > 10:
            overfit_risk = OverfitRisk.MODERATE
        else:
            overfit_risk = OverfitRisk.LOW
        
        # Additional warnings
        if data_reuse > 3:
            warnings.append(f"Data reused {data_reuse} times - high snooping risk")
        
        if observed_sharpe > 3.0:
            warnings.append(f"Suspiciously high Sharpe ({observed_sharpe:.2f}) - likely overfit")
        
        if deflated_sharpe < observed_sharpe * 0.3:
            warnings.append(f"Sharpe deflated by {(1 - deflated_sharpe/observed_sharpe)*100:.0f}%")
        
        if not is_significant:
            self.strategies_blocked += 1
        
        result = TestingCorrection(
            original_pvalue=observed_pvalue,
            corrected_pvalue=corrected_pvalue,
            original_sharpe=observed_sharpe,
            deflated_sharpe=deflated_sharpe,
            num_tests=int(effective_tests),
            correction_method=method,
            is_significant=is_significant,
            overfit_risk=overfit_risk,
            false_discovery_prob=false_discovery_prob,
            min_required_sharpe=min_required_sharpe,
            warnings=warnings
        )
        
        if not is_significant:
            logger.warning(
                f"MULTIPLE TESTING GATE BLOCKED {strategy_id}: "
                f"Original Sharpe={observed_sharpe:.2f}, Deflated={deflated_sharpe:.2f}, "
                f"Tests={effective_tests:.0f}, FDP={false_discovery_prob:.1%}"
            )
        
        return result
    
    def _calculate_deflated_sharpe(
        self,
        observed_sharpe: float,
        num_trials: float,
        backtest_years: float,
        num_trades: int
    ) -> float:
        """
        Calculate Deflated Sharpe Ratio (DSR).
        
        Based on Bailey & Lopez de Prado (2014):
        "The Deflated Sharpe Ratio: Correcting for Selection Bias,
        Backtest Overfitting and Non-Normality"
        """
        if num_trials <= 1:
            return observed_sharpe
        
        # Expected maximum Sharpe under null hypothesis
        # E[max(SR)] ≈ sqrt(2 * log(N)) for N trials
        expected_max_sharpe = math.sqrt(2 * math.log(num_trials))
        
        # Standard error of Sharpe ratio
        # SE(SR) ≈ sqrt((1 + SR^2/2) / T)
        if backtest_years > 0:
            se_sharpe = math.sqrt((1 + observed_sharpe**2 / 2) / backtest_years)
        else:
            se_sharpe = 1.0
        
        # Deflated Sharpe
        # DSR = (SR - E[max(SR)]) / SE(SR)
        deflated = observed_sharpe - expected_max_sharpe * se_sharpe
        
        # Ensure non-negative
        return max(0, deflated)
    
    def _min_sharpe_for_significance(
        self,
        num_trials: float,
        backtest_years: float
    ) -> float:
        """Calculate minimum Sharpe needed for significance given trials"""
        if num_trials <= 1:
            return 0.5
        
        # From DSR formula, solve for SR where DSR > threshold
        expected_max = math.sqrt(2 * math.log(num_trials))
        
        # Add buffer for standard error
        se_factor = math.sqrt(1 / max(backtest_years, 1))
        
        return expected_max * se_factor + self.min_deflated_sharpe
    
    def _estimate_false_discovery(
        self,
        pvalue: float,
        prior_prob: float
    ) -> float:
        """
        Estimate probability that a significant result is a false discovery.
        
        Using Bayesian approach:
        P(H0|significant) = P(significant|H0) * P(H0) / P(significant)
        """
        if pvalue >= 1:
            return 1.0
        
        # P(significant | H0) = alpha (type I error rate)
        alpha = self.base_alpha
        
        # P(significant | H1) = power (assume 0.8)
        power = 0.8
        
        # P(H0) = 1 - prior_prob
        p_h0 = 1 - prior_prob
        
        # P(significant) = P(sig|H0)*P(H0) + P(sig|H1)*P(H1)
        p_significant = alpha * p_h0 + power * prior_prob
        
        if p_significant <= 0:
            return 1.0
        
        # P(H0 | significant) = false discovery probability
        fdp = (pvalue * p_h0) / p_significant
        
        return min(1.0, fdp)
    
    def calculate_overfit_score(
        self,
        strategy_id: str,
        model_complexity: int,  # Number of parameters
        in_sample_sharpe: float,
        out_of_sample_sharpe: float
    ) -> OverfitScore:
        """
        Calculate comprehensive overfitting score.
        
        Args:
            strategy_id: Strategy identifier
            model_complexity: Number of free parameters
            in_sample_sharpe: In-sample Sharpe ratio
            out_of_sample_sharpe: Out-of-sample Sharpe ratio
        """
        recommendations = []
        
        # Get test info
        test_info = self.test_registry.get(strategy_id, {})
        search_space = test_info.get('search_space_size', 1)
        data_reuse = test_info.get('data_reuse_count', 1)
        
        # 1. Search space penalty
        # More tests = higher chance of finding spurious patterns
        search_space_penalty = min(1.0, math.log10(search_space + 1) / 4)
        if search_space_penalty > 0.5:
            recommendations.append(f"Reduce search space from {search_space} combinations")
        
        # 2. Data reuse penalty
        # Using same data multiple times increases snooping
        data_reuse_penalty = min(1.0, (data_reuse - 1) * 0.2)
        if data_reuse_penalty > 0.3:
            recommendations.append(f"Use fresh data - current data used {data_reuse} times")
        
        # 3. Complexity penalty
        # More parameters = more degrees of freedom to overfit
        complexity_penalty = min(1.0, model_complexity / 20)
        if complexity_penalty > 0.5:
            recommendations.append(f"Reduce model complexity from {model_complexity} parameters")
        
        # 4. Selection bias penalty
        # Large gap between IS and OOS indicates overfitting
        if in_sample_sharpe > 0:
            performance_decay = 1 - (out_of_sample_sharpe / in_sample_sharpe)
            selection_bias_penalty = max(0, min(1.0, performance_decay))
        else:
            selection_bias_penalty = 1.0
        
        if selection_bias_penalty > 0.3:
            recommendations.append(
                f"IS/OOS gap too large: {in_sample_sharpe:.2f} vs {out_of_sample_sharpe:.2f}"
            )
        
        # Overall score (weighted average)
        score = (
            search_space_penalty * 0.3 +
            data_reuse_penalty * 0.2 +
            complexity_penalty * 0.2 +
            selection_bias_penalty * 0.3
        )
        
        # Determine risk level
        if score > 0.7:
            risk_level = OverfitRisk.EXTREME
        elif score > 0.5:
            risk_level = OverfitRisk.HIGH
        elif score > 0.3:
            risk_level = OverfitRisk.MODERATE
        else:
            risk_level = OverfitRisk.LOW
        
        is_acceptable = score < 0.5 and risk_level not in [OverfitRisk.EXTREME, OverfitRisk.HIGH]
        
        if not is_acceptable:
            logger.warning(f"High overfit score for {strategy_id}: {score:.2f}")
        
        return OverfitScore(
            score=score,
            search_space_penalty=search_space_penalty,
            data_reuse_penalty=data_reuse_penalty,
            complexity_penalty=complexity_penalty,
            selection_bias_penalty=selection_bias_penalty,
            risk_level=risk_level,
            is_acceptable=is_acceptable,
            recommendations=recommendations
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gate statistics"""
        return {
            'total_tests_performed': self.total_tests_performed,
            'parameter_combinations_tried': self.parameter_combinations_tried,
            'strategies_corrected': self.strategies_corrected,
            'strategies_blocked': self.strategies_blocked,
            'block_rate': self.strategies_blocked / max(self.strategies_corrected, 1),
            'unique_datasets_used': len(self.data_usage),
            'avg_data_reuse': statistics.mean(self.data_usage.values()) if self.data_usage else 1
        }
    
    def generate_report(self, strategy_id: str, correction: TestingCorrection) -> str:
        """Generate detailed multiple testing report"""
        test_info = self.test_registry.get(strategy_id, {})
        
        report = [
            "=== Multiple Testing Correction Report ===",
            f"Strategy: {strategy_id}",
            f"",
            f"=== Test Registry ===",
            f"Search Space Size: {test_info.get('search_space_size', 'Unknown')}",
            f"Data Reuse Count: {test_info.get('data_reuse_count', 'Unknown')}",
            f"Optimization Method: {test_info.get('optimization_method', 'Unknown')}",
            f"",
            f"=== Correction Results ===",
            f"Correction Method: {correction.correction_method.value}",
            f"Effective Tests: {correction.num_tests}",
            f"",
            f"Original P-value: {correction.original_pvalue:.4f}",
            f"Corrected P-value: {correction.corrected_pvalue:.4f}",
            f"",
            f"Original Sharpe: {correction.original_sharpe:.2f}",
            f"Deflated Sharpe: {correction.deflated_sharpe:.2f}",
            f"Min Required Sharpe: {correction.min_required_sharpe:.2f}",
            f"",
            f"=== Risk Assessment ===",
            f"Is Significant: {'YES' if correction.is_significant else 'NO'}",
            f"Overfit Risk: {correction.overfit_risk.value.upper()}",
            f"False Discovery Probability: {correction.false_discovery_prob:.1%}",
            f"",
        ]
        
        if correction.warnings:
            report.append("=== Warnings ===")
            for warning in correction.warnings:
                report.append(f"  - {warning}")
        
        return "\n".join(report)

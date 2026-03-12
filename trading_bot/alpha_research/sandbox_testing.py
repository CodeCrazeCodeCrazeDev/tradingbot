"""
Automated Sandbox Testing Module
================================
Every candidate feature must undergo automated testing:
- Out-of-sample testing
- Cross-regime testing
- Cost-adjusted testing (transaction costs, slippage, impact)
- Parameter stability testing
- Robustness to data errors

Reject any candidate that fails any test.

Author: AlphaAlgo Research Team
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from .rdaos_core import (
    AlphaHorizon,
    FeatureDefinition,
    FeatureFamily,
    HARD_LIMITS,
    ProductionStatus,
    RegimeType,
    TestingMetrics,
    TestingResult,
    generate_id
)

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of tests"""
    OUT_OF_SAMPLE = "out_of_sample"
    CROSS_REGIME = "cross_regime"
    COST_ADJUSTED = "cost_adjusted"
    PARAMETER_STABILITY = "parameter_stability"
    DATA_ROBUSTNESS = "data_robustness"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class TestConfig:
    """Configuration for a test"""
    test_type: TestType
    
    # Out-of-sample config
    oos_ratio: float = 0.3  # 30% out-of-sample
    min_oos_periods: int = 3
    
    # Cross-regime config
    min_regimes: int = 4
    regime_min_samples: int = 50
    
    # Cost config
    transaction_cost_bps: float = 10.0
    slippage_bps: float = 5.0
    market_impact_bps: float = 5.0
    
    # Parameter stability config
    param_perturbation: float = 0.1  # 10% perturbation
    min_stability_score: float = 0.7
    
    # Data robustness config
    missing_data_ratio: float = 0.05
    noise_std: float = 0.01
    min_robustness_score: float = 0.7


@dataclass
class TestResult:
    """Result of a single test"""
    test_type: TestType
    status: TestStatus
    
    metrics: TestingMetrics = field(default_factory=TestingMetrics)
    
    passed: bool = False
    failure_reason: str = ""
    
    details: Dict[str, Any] = field(default_factory=dict)
    
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "test_type": self.test_type.value,
            "status": self.status.value,
            "metrics": self.metrics.to_dict(),
            "passed": self.passed,
            "failure_reason": self.failure_reason,
            "details": self.details
        }


class BaseTest(ABC):
    """Abstract base class for tests"""
    
    def __init__(self, config: TestConfig):
        self.config = config
    
    @abstractmethod
    def run(
        self,
        feature: FeatureDefinition,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> TestResult:
        """Run the test"""
        pass
    
    def _compute_metrics(
        self,
        returns: pd.Series,
        positions: pd.Series,
        costs: float = 0.0
    ) -> TestingMetrics:
        """Compute performance metrics"""
        # Strategy returns
        strategy_returns = returns * positions.shift(1)
        strategy_returns = strategy_returns.dropna()
        
        if len(strategy_returns) == 0:
            return TestingMetrics()
        
        # Apply costs
        trades = positions.diff().abs()
        cost_drag = trades * costs / 10000  # Convert bps to decimal
        net_returns = strategy_returns - cost_drag
        
        # Compute metrics
        total_return = (1 + net_returns).prod() - 1
        
        # Annualized metrics
        n_years = len(net_returns) / 252
        if n_years > 0:
            annualized_return = (1 + total_return) ** (1 / n_years) - 1
        else:
            annualized_return = 0.0
        
        volatility = net_returns.std() * np.sqrt(252)
        
        # Sharpe ratio
        if volatility > 0:
            sharpe_ratio = annualized_return / volatility
        else:
            sharpe_ratio = 0.0
        
        # Sortino ratio
        downside_returns = net_returns[net_returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.0
        if downside_vol > 0:
            sortino_ratio = annualized_return / downside_vol
        else:
            sortino_ratio = 0.0
        
        # Drawdown
        cumulative = (1 + net_returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = abs(drawdown.min()) * 100  # As percentage
        
        # Calmar ratio
        if max_drawdown > 0:
            calmar_ratio = annualized_return / (max_drawdown / 100)
        else:
            calmar_ratio = 0.0
        
        # Win rate
        winning_trades = (strategy_returns > 0).sum()
        total_trades = (positions.diff() != 0).sum()
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Profit factor
        gross_profit = strategy_returns[strategy_returns > 0].sum()
        gross_loss = abs(strategy_returns[strategy_returns < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        # VaR and CVaR
        var_95 = np.percentile(net_returns, 5) * 100
        cvar_95 = net_returns[net_returns <= np.percentile(net_returns, 5)].mean() * 100
        
        return TestingMetrics(
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            total_return=total_return * 100,
            annualized_return=annualized_return * 100,
            max_drawdown=max_drawdown,
            avg_drawdown=abs(drawdown.mean()) * 100,
            volatility=volatility * 100,
            downside_volatility=downside_vol * 100,
            win_rate=win_rate,
            profit_factor=profit_factor,
            var_95=var_95,
            cvar_95=cvar_95 if not np.isnan(cvar_95) else 0.0,
            total_trades=int(total_trades),
            transaction_costs=costs
        )


class OutOfSampleTest(BaseTest):
    """Out-of-sample testing"""
    
    def run(
        self,
        feature: FeatureDefinition,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> TestResult:
        """Run out-of-sample test"""
        result = TestResult(test_type=TestType.OUT_OF_SAMPLE, status=TestStatus.RUNNING)
        
        try:
            n = len(data)
            split_idx = int(n * (1 - self.config.oos_ratio))
            
            # In-sample and out-of-sample splits
            is_data = data.iloc[:split_idx]
            oos_data = data.iloc[split_idx:]
            oos_returns = returns.iloc[split_idx:]
            
            if len(oos_data) < self.config.min_oos_periods * 20:
                result.status = TestStatus.FAILED
                result.failure_reason = "Insufficient out-of-sample data"
                return result
            
            # Generate positions from feature (simple signal)
            feature_values = self._compute_feature(feature, oos_data)
            positions = np.sign(feature_values)
            
            # Compute metrics
            metrics = self._compute_metrics(oos_returns, positions)
            result.metrics = metrics
            
            # Check against hard limits
            passed, violations = HARD_LIMITS.validate_feature(metrics)
            
            if passed and metrics.sharpe_ratio >= HARD_LIMITS.MIN_SHARPE_AFTER_COSTS:
                result.status = TestStatus.PASSED
                result.passed = True
            else:
                result.status = TestStatus.FAILED
                result.passed = False
                result.failure_reason = "; ".join(violations) if violations else "Sharpe below threshold"
            
            result.details = {
                "oos_samples": len(oos_data),
                "is_samples": len(is_data),
                "oos_ratio": self.config.oos_ratio
            }
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.failure_reason = str(e)
        
        result.completed_at = datetime.utcnow()
        return result
    
    def _compute_feature(self, feature: FeatureDefinition, data: pd.DataFrame) -> pd.Series:
        """Compute feature values from data"""
        # Simple momentum feature as default
        if "close" in data.columns:
            lookback = feature.lookback_period
            return data["close"].pct_change(lookback)
        return pd.Series(0, index=data.index)


class CrossRegimeTest(BaseTest):
    """Cross-regime testing"""
    
    REGIME_DEFINITIONS = {
        RegimeType.NORMAL: {"vol_percentile": (25, 75), "trend": None},
        RegimeType.HIGH_VOLATILITY: {"vol_percentile": (75, 100), "trend": None},
        RegimeType.LOW_VOLATILITY: {"vol_percentile": (0, 25), "trend": None},
        RegimeType.TRENDING_UP: {"vol_percentile": None, "trend": "up"},
        RegimeType.TRENDING_DOWN: {"vol_percentile": None, "trend": "down"},
        RegimeType.CRISIS: {"vol_percentile": (90, 100), "trend": "down"},
    }
    
    def run(
        self,
        feature: FeatureDefinition,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> TestResult:
        """Run cross-regime test"""
        result = TestResult(test_type=TestType.CROSS_REGIME, status=TestStatus.RUNNING)
        
        try:
            # Classify regimes
            regimes = self._classify_regimes(data, returns)
            
            # Test in each regime
            regime_metrics = {}
            regimes_passed = 0
            
            for regime_type, regime_mask in regimes.items():
                if regime_mask.sum() < self.config.regime_min_samples:
                    continue
                
                regime_data = data[regime_mask]
                regime_returns = returns[regime_mask]
                
                # Compute feature and positions
                feature_values = self._compute_feature(feature, regime_data)
                positions = np.sign(feature_values)
                
                # Compute metrics
                metrics = self._compute_metrics(regime_returns, positions)
                regime_metrics[regime_type.value] = metrics
                
                # Check if passed in this regime
                if metrics.sharpe_ratio > 0:  # Positive Sharpe in regime
                    regimes_passed += 1
            
            result.details["regime_metrics"] = {k: v.to_dict() for k, v in regime_metrics.items()}
            result.details["regimes_tested"] = len(regime_metrics)
            result.details["regimes_passed"] = regimes_passed
            
            # Need to pass in minimum number of regimes
            if regimes_passed >= self.config.min_regimes:
                result.status = TestStatus.PASSED
                result.passed = True
            else:
                result.status = TestStatus.FAILED
                result.passed = False
                result.failure_reason = f"Only passed in {regimes_passed}/{self.config.min_regimes} regimes"
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.failure_reason = str(e)
        
        result.completed_at = datetime.utcnow()
        return result
    
    def _classify_regimes(
        self,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> Dict[RegimeType, pd.Series]:
        """Classify data into regimes"""
        regimes = {}
        
        # Compute volatility
        vol = returns.rolling(20).std() * np.sqrt(252)
        vol_percentile = vol.rank(pct=True) * 100
        
        # Compute trend
        sma_50 = data["close"].rolling(50).mean() if "close" in data.columns else None
        sma_200 = data["close"].rolling(200).mean() if "close" in data.columns else None
        
        for regime_type, definition in self.REGIME_DEFINITIONS.items():
            mask = pd.Series(True, index=data.index)
            
            if definition["vol_percentile"]:
                low, high = definition["vol_percentile"]
                mask &= (vol_percentile >= low) & (vol_percentile < high)
            
            if definition["trend"] and sma_50 is not None and sma_200 is not None:
                if definition["trend"] == "up":
                    mask &= sma_50 > sma_200
                elif definition["trend"] == "down":
                    mask &= sma_50 < sma_200
            
            regimes[regime_type] = mask
        
        return regimes
    
    def _compute_feature(self, feature: FeatureDefinition, data: pd.DataFrame) -> pd.Series:
        """Compute feature values"""
        if "close" in data.columns:
            lookback = feature.lookback_period
            return data["close"].pct_change(lookback)
        return pd.Series(0, index=data.index)


class CostAdjustedTest(BaseTest):
    """Cost-adjusted testing"""
    
    def run(
        self,
        feature: FeatureDefinition,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> TestResult:
        """Run cost-adjusted test"""
        result = TestResult(test_type=TestType.COST_ADJUSTED, status=TestStatus.RUNNING)
        
        try:
            # Compute feature and positions
            feature_values = self._compute_feature(feature, data)
            positions = np.sign(feature_values)
            
            # Total costs
            total_costs = (
                self.config.transaction_cost_bps +
                self.config.slippage_bps +
                self.config.market_impact_bps
            )
            
            # Compute metrics with costs
            metrics = self._compute_metrics(returns, positions, costs=total_costs)
            result.metrics = metrics
            
            result.details = {
                "transaction_costs_bps": self.config.transaction_cost_bps,
                "slippage_bps": self.config.slippage_bps,
                "market_impact_bps": self.config.market_impact_bps,
                "total_costs_bps": total_costs
            }
            
            # Check against hard limits
            passed, violations = HARD_LIMITS.validate_feature(metrics)
            
            if passed:
                result.status = TestStatus.PASSED
                result.passed = True
            else:
                result.status = TestStatus.FAILED
                result.passed = False
                result.failure_reason = "; ".join(violations)
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.failure_reason = str(e)
        
        result.completed_at = datetime.utcnow()
        return result
    
    def _compute_feature(self, feature: FeatureDefinition, data: pd.DataFrame) -> pd.Series:
        """Compute feature values"""
        if "close" in data.columns:
            lookback = feature.lookback_period
            return data["close"].pct_change(lookback)
        return pd.Series(0, index=data.index)


class ParameterStabilityTest(BaseTest):
    """Parameter stability testing"""
    
    def run(
        self,
        feature: FeatureDefinition,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> TestResult:
        """Run parameter stability test"""
        result = TestResult(test_type=TestType.PARAMETER_STABILITY, status=TestStatus.RUNNING)
        
        try:
            # Get base parameters
            base_params = feature.parameters.copy()
            
            # Test with perturbed parameters
            sharpe_ratios = []
            
            # Base case
            base_sharpe = self._test_with_params(feature, data, returns, base_params)
            sharpe_ratios.append(base_sharpe)
            
            # Perturbed cases
            for param_name, param_value in base_params.items():
                if isinstance(param_value, (int, float)):
                    # Perturb up
                    perturbed_up = base_params.copy()
                    perturbed_up[param_name] = param_value * (1 + self.config.param_perturbation)
                    sharpe_up = self._test_with_params(feature, data, returns, perturbed_up)
                    sharpe_ratios.append(sharpe_up)
                    
                    # Perturb down
                    perturbed_down = base_params.copy()
                    perturbed_down[param_name] = param_value * (1 - self.config.param_perturbation)
                    sharpe_down = self._test_with_params(feature, data, returns, perturbed_down)
                    sharpe_ratios.append(sharpe_down)
            
            # Compute stability score
            if len(sharpe_ratios) > 1 and np.std(sharpe_ratios) > 0:
                stability_score = 1 - (np.std(sharpe_ratios) / (np.mean(sharpe_ratios) + 1e-10))
                stability_score = max(0, min(1, stability_score))
            else:
                stability_score = 1.0
            
            result.details = {
                "base_sharpe": base_sharpe,
                "sharpe_ratios": sharpe_ratios,
                "stability_score": stability_score,
                "perturbation": self.config.param_perturbation
            }
            
            if stability_score >= self.config.min_stability_score:
                result.status = TestStatus.PASSED
                result.passed = True
            else:
                result.status = TestStatus.FAILED
                result.passed = False
                result.failure_reason = f"Stability score {stability_score:.2f} < {self.config.min_stability_score}"
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.failure_reason = str(e)
        
        result.completed_at = datetime.utcnow()
        return result
    
    def _test_with_params(
        self,
        feature: FeatureDefinition,
        data: pd.DataFrame,
        returns: pd.Series,
        params: Dict
    ) -> float:
        """Test feature with specific parameters"""
        # Create modified feature
        modified_feature = FeatureDefinition(
            feature_id=feature.feature_id,
            name=feature.name,
            formula=feature.formula,
            parameters=params,
            time_horizon=feature.time_horizon,
            lookback_period=params.get("lookback", feature.lookback_period)
        )
        
        # Compute feature and positions
        feature_values = self._compute_feature(modified_feature, data)
        positions = np.sign(feature_values)
        
        # Compute metrics
        metrics = self._compute_metrics(returns, positions)
        return metrics.sharpe_ratio
    
    def _compute_feature(self, feature: FeatureDefinition, data: pd.DataFrame) -> pd.Series:
        """Compute feature values"""
        if "close" in data.columns:
            lookback = feature.lookback_period
            return data["close"].pct_change(lookback)
        return pd.Series(0, index=data.index)


class DataRobustnessTest(BaseTest):
    """Data robustness testing"""
    
    def run(
        self,
        feature: FeatureDefinition,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> TestResult:
        """Run data robustness test"""
        result = TestResult(test_type=TestType.DATA_ROBUSTNESS, status=TestStatus.RUNNING)
        
        try:
            # Base case
            base_sharpe = self._test_with_data(feature, data, returns)
            
            # Test with missing data
            missing_data = self._add_missing_data(data)
            missing_sharpe = self._test_with_data(feature, missing_data, returns)
            
            # Test with noisy data
            noisy_data = self._add_noise(data)
            noisy_sharpe = self._test_with_data(feature, noisy_data, returns)
            
            # Compute robustness score
            sharpe_ratios = [base_sharpe, missing_sharpe, noisy_sharpe]
            if base_sharpe > 0:
                robustness_score = min(missing_sharpe / base_sharpe, noisy_sharpe / base_sharpe)
                robustness_score = max(0, min(1, robustness_score))
            else:
                robustness_score = 0.0
            
            result.details = {
                "base_sharpe": base_sharpe,
                "missing_data_sharpe": missing_sharpe,
                "noisy_data_sharpe": noisy_sharpe,
                "robustness_score": robustness_score,
                "missing_ratio": self.config.missing_data_ratio,
                "noise_std": self.config.noise_std
            }
            
            if robustness_score >= self.config.min_robustness_score:
                result.status = TestStatus.PASSED
                result.passed = True
            else:
                result.status = TestStatus.FAILED
                result.passed = False
                result.failure_reason = f"Robustness score {robustness_score:.2f} < {self.config.min_robustness_score}"
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.failure_reason = str(e)
        
        result.completed_at = datetime.utcnow()
        return result
    
    def _test_with_data(
        self,
        feature: FeatureDefinition,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> float:
        """Test feature with specific data"""
        feature_values = self._compute_feature(feature, data)
        positions = np.sign(feature_values)
        metrics = self._compute_metrics(returns, positions)
        return metrics.sharpe_ratio
    
    def _add_missing_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add missing data to test robustness"""
        modified = data.copy()
        n = len(modified)
        n_missing = int(n * self.config.missing_data_ratio)
        
        missing_idx = np.random.choice(n, n_missing, replace=False)
        for col in modified.columns:
            modified.iloc[missing_idx, modified.columns.get_loc(col)] = np.nan
        
        # Forward fill missing values
        modified = modified.ffill()
        return modified
    
    def _add_noise(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add noise to test robustness"""
        modified = data.copy()
        
        for col in modified.columns:
            if modified[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
                noise = np.random.normal(0, self.config.noise_std * modified[col].std(), len(modified))
                modified[col] = modified[col] + noise
        
        return modified
    
    def _compute_feature(self, feature: FeatureDefinition, data: pd.DataFrame) -> pd.Series:
        """Compute feature values"""
        if "close" in data.columns:
            lookback = feature.lookback_period
            return data["close"].pct_change(lookback)
        return pd.Series(0, index=data.index)


class SandboxTestingEngine:
    """
    Main engine for automated sandbox testing.
    
    Coordinates all tests:
    - Out-of-sample testing
    - Cross-regime testing
    - Cost-adjusted testing
    - Parameter stability testing
    - Data robustness testing
    
    Rejects any candidate that fails any test.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Test configuration
        self.test_config = TestConfig(
            test_type=TestType.OUT_OF_SAMPLE,
            oos_ratio=self.config.get("oos_ratio", 0.3),
            min_oos_periods=self.config.get("min_oos_periods", 3),
            min_regimes=self.config.get("min_regimes", 4),
            transaction_cost_bps=self.config.get("transaction_cost_bps", 10.0),
            slippage_bps=self.config.get("slippage_bps", 5.0),
            market_impact_bps=self.config.get("market_impact_bps", 5.0),
            param_perturbation=self.config.get("param_perturbation", 0.1),
            min_stability_score=self.config.get("min_stability_score", 0.7),
            min_robustness_score=self.config.get("min_robustness_score", 0.7)
        )
        
        # Initialize tests
        self.tests = {
            TestType.OUT_OF_SAMPLE: OutOfSampleTest(self.test_config),
            TestType.CROSS_REGIME: CrossRegimeTest(self.test_config),
            TestType.COST_ADJUSTED: CostAdjustedTest(self.test_config),
            TestType.PARAMETER_STABILITY: ParameterStabilityTest(self.test_config),
            TestType.DATA_ROBUSTNESS: DataRobustnessTest(self.test_config)
        }
        
        logger.info("Sandbox Testing Engine initialized")
    
    def test_feature_family(
        self,
        family: FeatureFamily,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> TestingResult:
        """Test a complete feature family"""
        
        test_id = generate_id("test")
        
        # Test each feature in the family
        all_results = []
        
        for feature in family.features:
            feature_results = self._test_feature(feature, data, returns)
            all_results.append(feature_results)
        
        # Aggregate results
        testing_result = self._aggregate_results(test_id, family.family_id, all_results)
        
        return testing_result
    
    def _test_feature(
        self,
        feature: FeatureDefinition,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> Dict[TestType, TestResult]:
        """Run all tests on a single feature"""
        results = {}
        
        for test_type, test in self.tests.items():
            try:
                result = test.run(feature, data, returns)
                results[test_type] = result
                
                logger.info(
                    f"Feature {feature.feature_id} - {test_type.value}: "
                    f"{'PASSED' if result.passed else 'FAILED'}"
                )
                
            except Exception as e:
                logger.error(f"Error running {test_type.value} on {feature.feature_id}: {e}")
                results[test_type] = TestResult(
                    test_type=test_type,
                    status=TestStatus.ERROR,
                    failure_reason=str(e)
                )
        
        return results
    
    def _aggregate_results(
        self,
        test_id: str,
        family_id: str,
        all_results: List[Dict[TestType, TestResult]]
    ) -> TestingResult:
        """Aggregate results from all features"""
        
        # Check if all tests passed for at least one feature
        any_feature_passed_all = False
        rejection_reasons = []
        
        for feature_results in all_results:
            all_passed = all(r.passed for r in feature_results.values())
            if all_passed:
                any_feature_passed_all = True
            else:
                for test_type, result in feature_results.items():
                    if not result.passed:
                        rejection_reasons.append(f"{test_type.value}: {result.failure_reason}")
        
        # Get best OOS metrics
        best_oos_metrics = TestingMetrics()
        best_sharpe = -float("inf")
        
        for feature_results in all_results:
            oos_result = feature_results.get(TestType.OUT_OF_SAMPLE)
            if oos_result and oos_result.metrics.sharpe_ratio > best_sharpe:
                best_sharpe = oos_result.metrics.sharpe_ratio
                best_oos_metrics = oos_result.metrics
        
        # Get best cost-adjusted metrics
        best_cost_metrics = TestingMetrics()
        best_cost_sharpe = -float("inf")
        
        for feature_results in all_results:
            cost_result = feature_results.get(TestType.COST_ADJUSTED)
            if cost_result and cost_result.metrics.sharpe_ratio > best_cost_sharpe:
                best_cost_sharpe = cost_result.metrics.sharpe_ratio
                best_cost_metrics = cost_result.metrics
        
        # Compute average stability and robustness scores
        stability_scores = []
        robustness_scores = []
        
        for feature_results in all_results:
            stability_result = feature_results.get(TestType.PARAMETER_STABILITY)
            if stability_result and "stability_score" in stability_result.details:
                stability_scores.append(stability_result.details["stability_score"])
            
            robustness_result = feature_results.get(TestType.DATA_ROBUSTNESS)
            if robustness_result and "robustness_score" in robustness_result.details:
                robustness_scores.append(robustness_result.details["robustness_score"])
        
        avg_stability = np.mean(stability_scores) if stability_scores else 0.0
        avg_robustness = np.mean(robustness_scores) if robustness_scores else 0.0
        
        # Build regime metrics
        regime_metrics = {}
        for feature_results in all_results:
            regime_result = feature_results.get(TestType.CROSS_REGIME)
            if regime_result and "regime_metrics" in regime_result.details:
                for regime, metrics_dict in regime_result.details["regime_metrics"].items():
                    if regime not in regime_metrics:
                        regime_metrics[regime] = TestingMetrics(**metrics_dict)
        
        return TestingResult(
            test_id=test_id,
            family_id=family_id,
            oos_metrics=best_oos_metrics,
            oos_passed=any(
                r.get(TestType.OUT_OF_SAMPLE, TestResult(TestType.OUT_OF_SAMPLE, TestStatus.FAILED)).passed
                for r in all_results
            ),
            regime_metrics=regime_metrics,
            regime_passed=any(
                r.get(TestType.CROSS_REGIME, TestResult(TestType.CROSS_REGIME, TestStatus.FAILED)).passed
                for r in all_results
            ),
            cost_adjusted_metrics=best_cost_metrics,
            cost_adjusted_passed=any(
                r.get(TestType.COST_ADJUSTED, TestResult(TestType.COST_ADJUSTED, TestStatus.FAILED)).passed
                for r in all_results
            ),
            parameter_stability_score=avg_stability,
            parameter_stability_passed=avg_stability >= self.test_config.min_stability_score,
            data_robustness_score=avg_robustness,
            data_robustness_passed=avg_robustness >= self.test_config.min_robustness_score,
            all_tests_passed=any_feature_passed_all,
            rejection_reasons=list(set(rejection_reasons))
        )
    
    def test_batch(
        self,
        families: List[FeatureFamily],
        data: pd.DataFrame,
        returns: pd.Series
    ) -> Dict[str, TestingResult]:
        """Test multiple feature families"""
        results = {}
        
        for family in families:
            try:
                result = self.test_feature_family(family, data, returns)
                results[family.family_id] = result
                
                status = "PASSED" if result.all_tests_passed else "FAILED"
                logger.info(f"Family {family.family_id}: {status}")
                
            except Exception as e:
                logger.error(f"Error testing family {family.family_id}: {e}")
        
        return results


def create_testing_engine(config: Optional[Dict] = None) -> SandboxTestingEngine:
    """Factory function to create testing engine"""
    return SandboxTestingEngine(config)

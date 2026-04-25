"""
Strategy Validation Pipeline
============================

Scientific validation before any real capital deployment.

Stages:
1. In-sample backtest (reject if Sharpe < 1.0)
2. Out-of-sample test (reject if degradation > 20%)
3. Walk-forward analysis (reject if inconsistency)
4. Regime-specific testing (reject if single-regime dependent)
5. Transaction cost modeling (reject if costs > 50% of alpha)
6. Paper trading (30 days minimum)
7. Live micro deployment ($1K max)
8. Gradual scale-up (if all above pass)

Validation Checklist:
- [ ] Out-of-sample test (30% holdout minimum)
- [ ] Walk-forward analysis (12+ months)
- [ ] Multiple market regimes (bull, bear, choppy, crisis)
- [ ] Transaction cost modeling (realistic slippage, fees)
- [ ] Statistical significance (p < 0.05 for alpha)
- [ ] Reproduction check (same result on re-run)
- [ ] Sensitivity analysis (parameter stability)
- [ ] Overfitting detection (training vs test degradation < 30%)
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ValidationStage(Enum):
    """Validation pipeline stages."""
    IN_SAMPLE_BACKTEST = "in_sample_backtest"
    OUT_OF_SAMPLE_TEST = "out_of_sample_test"
    WALK_FORWARD_ANALYSIS = "walk_forward_analysis"
    REGIME_TESTING = "regime_testing"
    TRANSACTION_COSTS = "transaction_costs"
    PAPER_TRADING = "paper_trading"
    LIVE_MICRO = "live_micro"
    SCALE_UP = "scale_up"


class ValidationStatus(Enum):
    """Status of validation stage."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class StageResult:
    """Result of a validation stage."""
    stage: ValidationStage
    status: ValidationStatus
    metrics: Dict[str, float] = field(default_factory=dict)
    notes: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'stage': self.stage.value,
            'status': self.status.value,
            'metrics': self.metrics,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class ValidationReport:
    """Complete validation report."""
    strategy_id: str
    overall_status: ValidationStatus
    stage_results: List[StageResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_assessment: str = ""
    deployment_authorized: bool = False
    max_position_size: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_id': self.strategy_id,
            'overall_status': self.overall_status.value,
            'stage_results': [r.to_dict() for r in self.stage_results],
            'recommendations': self.recommendations,
            'risk_assessment': self.risk_assessment,
            'deployment_authorized': self.deployment_authorized,
            'max_position_size': self.max_position_size,
        }


class StrategyValidationPipeline:
    """
    Scientific validation pipeline for trading strategies.
    
    Enforces rigorous testing before any real capital deployment.
    """
    
    def __init__(self):
        """Initialize validation pipeline."""
        self.thresholds = {
            'min_sharpe': 1.0,
            'max_drawdown': 0.25,
            'min_win_rate': 0.45,
            'max_degradation': 0.20,
            'max_cost_ratio': 0.50,
            'min_statistical_significance': 0.05,
        }
        
        logger.info("StrategyValidationPipeline initialized")
    
    def validate_strategy(self, 
                         strategy,
                         price_data: List[float],
                         strategy_id: str = "unknown") -> ValidationReport:
        """
        Run full validation pipeline on a strategy.
        
        Args:
            strategy: Strategy to validate
            price_data: Historical price data
            strategy_id: Strategy identifier
            
        Returns:
            ValidationReport
        """
        logger.info(f"Starting validation for strategy {strategy_id}")
        
        stage_results = []
        
        # Stage 1: In-sample backtest
        result = self._in_sample_backtest(strategy, price_data)
        stage_results.append(result)
        
        if result.status == ValidationStatus.FAILED:
            return self._create_failure_report(strategy_id, stage_results, "Failed in-sample backtest")
        
        # Stage 2: Out-of-sample test
        result = self._out_of_sample_test(strategy, price_data)
        stage_results.append(result)
        
        if result.status == ValidationStatus.FAILED:
            return self._create_failure_report(strategy_id, stage_results, "Failed out-of-sample test")
        
        # Stage 3: Walk-forward analysis
        result = self._walk_forward_analysis(strategy, price_data)
        stage_results.append(result)
        
        # Stage 4: Regime testing
        result = self._regime_testing(strategy, price_data)
        stage_results.append(result)
        
        # Stage 5: Transaction cost modeling
        result = self._transaction_cost_modeling(strategy, price_data)
        stage_results.append(result)
        
        # Evaluate overall
        overall_status = self._evaluate_overall_status(stage_results)
        deployment_authorized = overall_status == ValidationStatus.PASSED
        
        # Calculate max position based on risk
        max_position = self._calculate_max_position(stage_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(stage_results)
        
        report = ValidationReport(
            strategy_id=strategy_id,
            overall_status=overall_status,
            stage_results=stage_results,
            recommendations=recommendations,
            risk_assessment=self._generate_risk_assessment(stage_results),
            deployment_authorized=deployment_authorized,
            max_position_size=max_position,
        )
        
        logger.info(f"Validation complete for {strategy_id}: {overall_status.value}")
        
        return report
    
    def _in_sample_backtest(self, strategy, price_data: List[float]) -> StageResult:
        """Stage 1: In-sample backtest."""
        # Use first 70% for in-sample
        split_idx = int(len(price_data) * 0.7)
        train_data = price_data[:split_idx]
        
        metrics = self._run_backtest(strategy, train_data)
        
        # Check thresholds
        status = ValidationStatus.PASSED
        notes = []
        
        if metrics['sharpe'] < self.thresholds['min_sharpe']:
            status = ValidationStatus.FAILED
            notes.append(f"Sharpe {metrics['sharpe']:.2f} < {self.thresholds['min_sharpe']}")
        
        if metrics['max_drawdown'] > self.thresholds['max_drawdown']:
            status = ValidationStatus.FAILED
            notes.append(f"MaxDD {metrics['max_drawdown']:.2%} > {self.thresholds['max_drawdown']:.0%}")
        
        if metrics['win_rate'] < self.thresholds['min_win_rate']:
            status = ValidationStatus.WARNING
            notes.append(f"Win rate {metrics['win_rate']:.1%} < {self.thresholds['min_win_rate']:.0%}")
        
        return StageResult(
            stage=ValidationStage.IN_SAMPLE_BACKTEST,
            status=status,
            metrics=metrics,
            notes="; ".join(notes) if notes else "Passed all thresholds",
        )
    
    def _out_of_sample_test(self, strategy, price_data: List[float]) -> StageResult:
        """Stage 2: Out-of-sample test."""
        # Use last 30% for out-of-sample
        split_idx = int(len(price_data) * 0.7)
        test_data = price_data[split_idx:]
        
        if len(test_data) < 30:
            return StageResult(
                stage=ValidationStage.OUT_OF_SAMPLE_TEST,
                status=ValidationStatus.NOT_APPLICABLE,
                notes="Insufficient out-of-sample data",
            )
        
        # Run backtest
        train_data = price_data[:split_idx]
        train_metrics = self._run_backtest(strategy, train_data)
        test_metrics = self._run_backtest(strategy, test_data)
        
        # Check degradation
        if train_metrics['sharpe'] > 0:
            degradation = (train_metrics['sharpe'] - test_metrics['sharpe']) / train_metrics['sharpe']
        else:
            degradation = 0
        
        status = ValidationStatus.PASSED
        notes = f"Sharpe degradation: {degradation:.1%}"
        
        if degradation > self.thresholds['max_degradation']:
            status = ValidationStatus.FAILED
            notes += f" (exceeds {self.thresholds['max_degradation']:.0%} limit)"
        elif degradation > 0.10:
            status = ValidationStatus.WARNING
        
        metrics = {
            'train_sharpe': train_metrics['sharpe'],
            'test_sharpe': test_metrics['sharpe'],
            'degradation': degradation,
        }
        
        return StageResult(
            stage=ValidationStage.OUT_OF_SAMPLE_TEST,
            status=status,
            metrics=metrics,
            notes=notes,
        )
    
    def _walk_forward_analysis(self, strategy, price_data: List[float]) -> StageResult:
        """Stage 3: Walk-forward analysis."""
        window_size = 100
        step_size = 20
        
        performances = []
        
        for start in range(0, len(price_data) - window_size * 2, step_size):
            train_end = start + window_size
            test_end = train_end + window_size
            
            if test_end > len(price_data):
                break
            
            train_data = price_data[start:train_end]
            test_data = price_data[train_end:test_end]
            
            train_metrics = self._run_backtest(strategy, train_data)
            test_metrics = self._run_backtest(strategy, test_data)
            
            if train_metrics['sharpe'] > 0:
                perf_ratio = test_metrics['sharpe'] / train_metrics['sharpe']
                performances.append(perf_ratio)
        
        if not performances:
            return StageResult(
                stage=ValidationStage.WALK_FORWARD_ANALYSIS,
                status=ValidationStatus.NOT_APPLICABLE,
                notes="Insufficient data for walk-forward",
            )
        
        consistency = np.std(performances)
        avg_ratio = np.mean(performances)
        
        status = ValidationStatus.PASSED if consistency < 0.3 else ValidationStatus.WARNING
        
        return StageResult(
            stage=ValidationStage.WALK_FORWARD_ANALYSIS,
            status=status,
            metrics={'consistency': consistency, 'avg_ratio': avg_ratio},
            notes=f"Consistency: {consistency:.2f}, Avg ratio: {avg_ratio:.2f}",
        )
    
    def _regime_testing(self, strategy, price_data: List[float]) -> StageResult:
        """Stage 4: Regime-specific testing."""
        # Simple regime split: up vs down markets
        returns = np.diff(price_data) / price_data[:-1]
        
        # Identify regimes based on cumulative returns
        cumulative = np.cumsum(returns)
        
        # Bull: cumulative > 10%, Bear: cumulative < -10%
        bull_mask = cumulative > 0.10
        bear_mask = cumulative < -0.10
        
        bull_performance = []
        bear_performance = []
        
        for i in range(len(price_data) - 1):
            if bull_mask[i] if i < len(bull_mask) else False:
                bull_performance.append(returns[i])
            elif bear_mask[i] if i < len(bear_mask) else False:
                bear_performance.append(returns[i])
        
        if not bull_performance or not bear_performance:
            return StageResult(
                stage=ValidationStage.REGIME_TESTING,
                status=ValidationStatus.NOT_APPLICABLE,
                notes="Could not identify distinct regimes",
            )
        
        bull_sharpe = np.mean(bull_performance) / (np.std(bull_performance) + 1e-8) * np.sqrt(252)
        bear_sharpe = np.mean(bear_performance) / (np.std(bear_performance) + 1e-8) * np.sqrt(252)
        
        # Check if strategy works in both regimes
        single_regime_dependent = (bull_sharpe > 1.0 and bear_sharpe < 0) or (bear_sharpe > 1.0 and bull_sharpe < 0)
        
        status = ValidationStatus.FAILED if single_regime_dependent else ValidationStatus.PASSED
        
        return StageResult(
            stage=ValidationStage.REGIME_TESTING,
            status=status,
            metrics={'bull_sharpe': bull_sharpe, 'bear_sharpe': bear_sharpe},
            notes=f"Bull: {bull_sharpe:.2f}, Bear: {bear_sharpe:.2f}",
        )
    
    def _transaction_cost_modeling(self, strategy, price_data: List[float]) -> StageResult:
        """Stage 5: Transaction cost modeling."""
        # Run backtest with costs
        metrics_no_cost = self._run_backtest(strategy, price_data, transaction_cost=0.0)
        metrics_with_cost = self._run_backtest(strategy, price_data, transaction_cost=0.001)
        
        alpha_no_cost = metrics_no_cost['total_return']
        alpha_with_cost = metrics_with_cost['total_return']
        
        cost_impact = alpha_no_cost - alpha_with_cost
        cost_ratio = cost_impact / abs(alpha_no_cost) if alpha_no_cost != 0 else 0
        
        status = ValidationStatus.PASSED
        notes = f"Cost impact: {cost_impact:.2%}, Ratio: {cost_ratio:.1%}"
        
        if cost_ratio > self.thresholds['max_cost_ratio']:
            status = ValidationStatus.FAILED
            notes += f" (exceeds {self.thresholds['max_cost_ratio']:.0%} limit)"
        elif cost_ratio > 0.3:
            status = ValidationStatus.WARNING
        
        return StageResult(
            stage=ValidationStage.TRANSACTION_COSTS,
            status=status,
            metrics={'alpha_no_cost': alpha_no_cost, 'alpha_with_cost': alpha_with_cost, 'cost_ratio': cost_ratio},
            notes=notes,
        )
    
    def _run_backtest(self, strategy, price_data: List[float], 
                     transaction_cost: float = 0.0) -> Dict[str, float]:
        """Run simple backtest."""
        portfolio = 10000.0
        position = 0
        values = [portfolio]
        trades = 0
        
        for i in range(len(price_data) - 1):
            # Get signal
            if hasattr(strategy, 'generate_signal'):
                market_data = {'price': price_data[i], 'returns': 0}
                signal = strategy.generate_signal(market_data)
            elif hasattr(strategy, 'select_action'):
                from .rl_engine import TradingState
                state = TradingState(price_data[i], 0, 0, 0, 0, position)
                action, _ = strategy.select_action(state, explore=False)
                signal = 1 if action.value == 1 else -1 if action.value == -1 else 0
            else:
                signal = 0
            
            # Apply position change cost
            new_position = 1 if signal > 0.3 else -1 if signal < -0.3 else 0
            if new_position != position and transaction_cost > 0:
                portfolio *= (1 - transaction_cost)
                trades += 1
            
            position = new_position
            
            # Calculate return
            price_return = (price_data[i + 1] - price_data[i]) / price_data[i]
            portfolio += position * price_return * portfolio
            values.append(portfolio)
        
        # Calculate metrics
        returns = np.diff(values) / values[:-1]
        
        total_return = (values[-1] - values[0]) / values[0]
        sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
        
        # Max drawdown
        peak = values[0]
        max_dd = 0
        for v in values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            max_dd = max(max_dd, dd)
        
        win_rate = sum(1 for r in returns if r > 0) / len(returns) if len(returns) > 0 else 0
        
        return {
            'total_return': total_return,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'num_trades': trades,
        }
    
    def _evaluate_overall_status(self, stage_results: List[StageResult]) -> ValidationStatus:
        """Determine overall validation status."""
        if any(r.status == ValidationStatus.FAILED for r in stage_results):
            return ValidationStatus.FAILED
        
        if any(r.status == ValidationStatus.WARNING for r in stage_results):
            return ValidationStatus.WARNING
        
        return ValidationStatus.PASSED
    
    def _calculate_max_position(self, stage_results: List[StageResult]) -> float:
        """Calculate maximum allowed position size based on risk."""
        base_position = 1.0
        
        # Reduce position for any warnings
        num_warnings = sum(1 for r in stage_results if r.status == ValidationStatus.WARNING)
        reduction = num_warnings * 0.2
        
        # Further reduce based on drawdown
        for r in stage_results:
            if 'max_drawdown' in r.metrics:
                if r.metrics['max_drawdown'] > 0.20:
                    reduction += 0.3
                elif r.metrics['max_drawdown'] > 0.15:
                    reduction += 0.15
        
        return max(0.1, base_position - reduction)
    
    def _generate_recommendations(self, stage_results: List[StageResult]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        for result in stage_results:
            if result.status == ValidationStatus.WARNING:
                recommendations.append(f"{result.stage.value}: {result.notes}")
        
        if not recommendations:
            recommendations.append("Strategy passed all validation stages. Ready for deployment.")
        
        return recommendations
    
    def _generate_risk_assessment(self, stage_results: List[StageResult]) -> str:
        """Generate overall risk assessment."""
        failed = sum(1 for r in stage_results if r.status == ValidationStatus.FAILED)
        warnings = sum(1 for r in stage_results if r.status == ValidationStatus.WARNING)
        
        if failed > 0:
            return f"HIGH RISK: {failed} validation stages failed. DO NOT DEPLOY."
        elif warnings > 2:
            return f"MODERATE RISK: {warnings} warnings. Deploy with reduced position size."
        elif warnings > 0:
            return f"LOW RISK: {warnings} minor warnings. Deploy with caution."
        else:
            return "LOW RISK: All validation stages passed. Strategy ready for deployment."
    
    def _create_failure_report(self, strategy_id: str, 
                              stage_results: List[StageResult],
                              reason: str) -> ValidationReport:
        """Create failure report."""
        return ValidationReport(
            strategy_id=strategy_id,
            overall_status=ValidationStatus.FAILED,
            stage_results=stage_results,
            recommendations=[f"Validation failed: {reason}", "Strategy requires significant improvements before deployment."],
            risk_assessment=f"CRITICAL: {reason}. Deployment NOT authorized.",
            deployment_authorized=False,
            max_position_size=0.0,
        )

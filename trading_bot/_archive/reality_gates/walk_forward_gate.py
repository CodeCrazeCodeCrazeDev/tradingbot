"""
Walk-Forward Validation Gate - Preventing Overfitting Delusions

This gate ensures that any strategy or model has been properly validated
using walk-forward analysis, not just in-sample backtesting.

THE PROBLEM:
- Backtest looks amazing: 500% returns!
- Live trading: -50% in first month
- Why? Overfitting to historical data

THE SOLUTION:
- Require walk-forward validation before any strategy goes live
- Track out-of-sample performance vs in-sample
- Detect when a strategy is likely overfit
- Block strategies that haven't proven themselves OOS

RULE: "If it only works in backtest, it doesn't work."

Author: AlphaAlgo Reality Check System
"""

import logging
import statistics
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from collections import deque

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Status of walk-forward validation"""
    NOT_VALIDATED = "not_validated"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    DEGRADED = "degraded"  # Was passing, now failing


@dataclass
class WalkForwardConfig:
    """Configuration for walk-forward validation"""
    # Window sizes
    in_sample_periods: int = 12  # e.g., 12 months
    out_of_sample_periods: int = 3  # e.g., 3 months
    min_walks: int = 4  # Minimum number of walk-forward periods
    
    # Performance thresholds
    min_oos_sharpe: float = 0.5  # Minimum out-of-sample Sharpe
    max_oos_drawdown: float = 0.20  # Maximum OOS drawdown
    min_oos_win_rate: float = 0.45  # Minimum OOS win rate
    
    # Degradation thresholds
    max_is_oos_sharpe_ratio: float = 2.0  # IS Sharpe / OOS Sharpe
    max_performance_decay: float = 0.50  # Max decay from IS to OOS
    
    # Statistical requirements
    min_trades_per_period: int = 30  # Minimum trades for significance
    confidence_level: float = 0.95  # Statistical confidence


@dataclass
class WalkPeriodResult:
    """Results from a single walk-forward period"""
    period_id: int
    start_date: datetime
    end_date: datetime
    
    # In-sample metrics
    is_sharpe: float
    is_returns: float
    is_drawdown: float
    is_win_rate: float
    is_trades: int
    
    # Out-of-sample metrics
    oos_sharpe: float
    oos_returns: float
    oos_drawdown: float
    oos_win_rate: float
    oos_trades: int
    
    @property
    def performance_decay(self) -> float:
        """How much performance decayed from IS to OOS"""
        if self.is_sharpe <= 0:
            return 1.0
        return 1.0 - (self.oos_sharpe / self.is_sharpe)
    
    @property
    def is_overfit(self) -> bool:
        """Is this period showing signs of overfitting?"""
        if self.is_sharpe <= 0:
            return True
        ratio = self.is_sharpe / max(self.oos_sharpe, 0.01)
        return ratio > 2.0 or self.performance_decay > 0.5


@dataclass
class ValidationResult:
    """Complete validation result for a strategy"""
    strategy_id: str
    status: ValidationStatus
    is_approved: bool
    
    # Aggregate metrics
    avg_oos_sharpe: float
    avg_oos_returns: float
    avg_oos_drawdown: float
    avg_oos_win_rate: float
    
    # Consistency metrics
    sharpe_consistency: float  # Std dev of OOS Sharpe across walks
    overfit_score: float  # 0-1, higher = more overfit
    
    # Details
    walk_results: List[WalkPeriodResult]
    failure_reasons: List[str]
    
    # Timestamps
    validated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    @property
    def confidence_multiplier(self) -> float:
        """How much to trust this strategy"""
        if not self.is_approved:
            return 0.0
        return max(0.3, 1.0 - self.overfit_score)


class WalkForwardGate:
    """
    HARD GATE: Walk-Forward Validation
    
    This gate BLOCKS any strategy that hasn't been properly validated
    using walk-forward analysis. No exceptions.
    
    Process:
    1. Strategy is trained on in-sample data
    2. Tested on out-of-sample data
    3. Window rolls forward
    4. Repeat multiple times
    5. Aggregate OOS performance determines approval
    
    A strategy must:
    - Have positive OOS Sharpe ratio
    - Show consistent OOS performance
    - Not show excessive IS/OOS performance gap (overfitting)
    - Have sufficient trades for statistical significance
    """
    
    def __init__(self, config: Optional[WalkForwardConfig] = None):
        self.config = config or WalkForwardConfig()
        
        # Validation results cache
        self.validation_cache: Dict[str, ValidationResult] = {}
        
        # Live performance tracking
        self.live_performance: Dict[str, deque] = {}
        
        # Statistics
        self.strategies_validated = 0
        self.strategies_approved = 0
        self.strategies_blocked = 0
        
        logger.info("WalkForwardGate initialized - NO UNVALIDATED STRATEGIES SHALL PASS")
    
    def validate_strategy(
        self,
        strategy_id: str,
        walk_results: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate a strategy using walk-forward results.
        
        Args:
            strategy_id: Unique identifier for the strategy
            walk_results: List of walk-forward period results
            
        Returns:
            ValidationResult with approval status
        """
        self.strategies_validated += 1
        failure_reasons = []
        
        # Parse walk results
        parsed_walks = []
        for i, wr in enumerate(walk_results):
            try:
                parsed = WalkPeriodResult(
                    period_id=i,
                    start_date=wr.get('start_date', datetime.utcnow()),
                    end_date=wr.get('end_date', datetime.utcnow()),
                    is_sharpe=wr.get('is_sharpe', 0),
                    is_returns=wr.get('is_returns', 0),
                    is_drawdown=wr.get('is_drawdown', 0),
                    is_win_rate=wr.get('is_win_rate', 0),
                    is_trades=wr.get('is_trades', 0),
                    oos_sharpe=wr.get('oos_sharpe', 0),
                    oos_returns=wr.get('oos_returns', 0),
                    oos_drawdown=wr.get('oos_drawdown', 0),
                    oos_win_rate=wr.get('oos_win_rate', 0),
                    oos_trades=wr.get('oos_trades', 0),
                )
                parsed_walks.append(parsed)
            except Exception as e:
                logger.warning(f"Failed to parse walk result {i}: {e}")
        
        # Check minimum walks
        if len(parsed_walks) < self.config.min_walks:
            failure_reasons.append(
                f"Insufficient walks: {len(parsed_walks)} < {self.config.min_walks}"
            )
        
        # Calculate aggregate metrics
        if parsed_walks:
            oos_sharpes = [w.oos_sharpe for w in parsed_walks]
            oos_returns = [w.oos_returns for w in parsed_walks]
            oos_drawdowns = [w.oos_drawdown for w in parsed_walks]
            oos_win_rates = [w.oos_win_rate for w in parsed_walks]
            oos_trades = [w.oos_trades for w in parsed_walks]
            
            avg_oos_sharpe = statistics.mean(oos_sharpes)
            avg_oos_returns = statistics.mean(oos_returns)
            avg_oos_drawdown = statistics.mean(oos_drawdowns)
            avg_oos_win_rate = statistics.mean(oos_win_rates)
            
            # Sharpe consistency (lower is better)
            sharpe_consistency = statistics.stdev(oos_sharpes) if len(oos_sharpes) > 1 else 0
            
            # Overfit score
            overfit_scores = []
            for w in parsed_walks:
                if w.is_sharpe > 0:
                    ratio = w.is_sharpe / max(w.oos_sharpe, 0.01)
                    overfit_scores.append(min(ratio / 3.0, 1.0))  # Normalize to 0-1
                else:
                    overfit_scores.append(0.5)
            overfit_score = statistics.mean(overfit_scores) if overfit_scores else 1.0
        else:
            avg_oos_sharpe = 0
            avg_oos_returns = 0
            avg_oos_drawdown = 1.0
            avg_oos_win_rate = 0
            sharpe_consistency = 1.0
            overfit_score = 1.0
        
        # Validation checks
        
        # 1. Minimum OOS Sharpe
        if avg_oos_sharpe < self.config.min_oos_sharpe:
            failure_reasons.append(
                f"OOS Sharpe too low: {avg_oos_sharpe:.2f} < {self.config.min_oos_sharpe}"
            )
        
        # 2. Maximum OOS drawdown
        if avg_oos_drawdown > self.config.max_oos_drawdown:
            failure_reasons.append(
                f"OOS drawdown too high: {avg_oos_drawdown:.1%} > {self.config.max_oos_drawdown:.1%}"
            )
        
        # 3. Minimum win rate
        if avg_oos_win_rate < self.config.min_oos_win_rate:
            failure_reasons.append(
                f"OOS win rate too low: {avg_oos_win_rate:.1%} < {self.config.min_oos_win_rate:.1%}"
            )
        
        # 4. Check for overfitting
        if overfit_score > 0.7:
            failure_reasons.append(
                f"High overfit score: {overfit_score:.2f} (IS >> OOS performance)"
            )
        
        # 5. Check trade count
        if parsed_walks:
            total_oos_trades = sum(w.oos_trades for w in parsed_walks)
            min_required = self.config.min_trades_per_period * len(parsed_walks)
            if total_oos_trades < min_required:
                failure_reasons.append(
                    f"Insufficient OOS trades: {total_oos_trades} < {min_required}"
                )
        
        # 6. Check consistency
        if sharpe_consistency > 1.0:
            failure_reasons.append(
                f"Inconsistent OOS performance: Sharpe std = {sharpe_consistency:.2f}"
            )
        
        # 7. Check for any negative OOS periods
        negative_periods = sum(1 for w in parsed_walks if w.oos_sharpe < 0)
        if negative_periods > len(parsed_walks) * 0.5:
            failure_reasons.append(
                f"Too many negative OOS periods: {negative_periods}/{len(parsed_walks)}"
            )
        
        # Determine status
        is_approved = len(failure_reasons) == 0
        
        if is_approved:
            status = ValidationStatus.PASSED
            self.strategies_approved += 1
        else:
            status = ValidationStatus.FAILED
            self.strategies_blocked += 1
        
        result = ValidationResult(
            strategy_id=strategy_id,
            status=status,
            is_approved=is_approved,
            avg_oos_sharpe=avg_oos_sharpe,
            avg_oos_returns=avg_oos_returns,
            avg_oos_drawdown=avg_oos_drawdown,
            avg_oos_win_rate=avg_oos_win_rate,
            sharpe_consistency=sharpe_consistency,
            overfit_score=overfit_score,
            walk_results=parsed_walks,
            failure_reasons=failure_reasons,
            expires_at=datetime.utcnow() + timedelta(days=90)  # Re-validate every 90 days
        )
        
        # Cache result
        self.validation_cache[strategy_id] = result
        
        if is_approved:
            logger.info(f"Strategy {strategy_id} APPROVED: OOS Sharpe={avg_oos_sharpe:.2f}")
        else:
            logger.warning(f"Strategy {strategy_id} BLOCKED: {failure_reasons}")
        
        return result
    
    def is_strategy_approved(self, strategy_id: str) -> Tuple[bool, str]:
        """
        Check if a strategy is approved for live trading.
        
        Returns:
            Tuple of (is_approved, reason)
        """
        if strategy_id not in self.validation_cache:
            return False, "Strategy not validated - run walk-forward validation first"
        
        result = self.validation_cache[strategy_id]
        
        # Check expiration
        if result.expires_at and datetime.utcnow() > result.expires_at:
            return False, "Validation expired - re-run walk-forward validation"
        
        # Check for degradation
        if result.status == ValidationStatus.DEGRADED:
            return False, "Strategy performance has degraded - re-validate"
        
        if not result.is_approved:
            return False, f"Strategy failed validation: {result.failure_reasons}"
        
        return True, "Strategy approved"
    
    def update_live_performance(
        self,
        strategy_id: str,
        trade_result: Dict[str, Any]
    ):
        """
        Track live performance to detect degradation.
        
        Args:
            strategy_id: Strategy identifier
            trade_result: Result of a live trade
        """
        if strategy_id not in self.live_performance:
            self.live_performance[strategy_id] = deque(maxlen=100)
        
        self.live_performance[strategy_id].append(trade_result)
        
        # Check for degradation
        if len(self.live_performance[strategy_id]) >= 30:
            self._check_degradation(strategy_id)
    
    def _check_degradation(self, strategy_id: str):
        """Check if live performance has degraded from validation"""
        if strategy_id not in self.validation_cache:
            return
        
        validation = self.validation_cache[strategy_id]
        live_trades = list(self.live_performance[strategy_id])
        
        # Calculate live metrics
        returns = [t.get('return', 0) for t in live_trades]
        if not returns:
            return
        
        live_sharpe = self._calculate_sharpe(returns)
        live_win_rate = sum(1 for r in returns if r > 0) / len(returns)
        
        # Compare to validation
        sharpe_decay = 1.0 - (live_sharpe / max(validation.avg_oos_sharpe, 0.01))
        win_rate_decay = 1.0 - (live_win_rate / max(validation.avg_oos_win_rate, 0.01))
        
        if sharpe_decay > 0.5 or win_rate_decay > 0.3:
            validation.status = ValidationStatus.DEGRADED
            logger.warning(
                f"Strategy {strategy_id} DEGRADED: "
                f"Live Sharpe={live_sharpe:.2f} vs OOS={validation.avg_oos_sharpe:.2f}"
            )
    
    def _calculate_sharpe(self, returns: List[float], risk_free: float = 0.0) -> float:
        """Calculate Sharpe ratio from returns"""
        if len(returns) < 2:
            return 0.0
        
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        
        if std_return == 0:
            return 0.0
        
        return (mean_return - risk_free) / std_return * math.sqrt(252)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gate statistics"""
        return {
            'strategies_validated': self.strategies_validated,
            'strategies_approved': self.strategies_approved,
            'strategies_blocked': self.strategies_blocked,
            'approval_rate': self.strategies_approved / max(self.strategies_validated, 1),
            'cached_validations': len(self.validation_cache),
            'degraded_strategies': sum(
                1 for v in self.validation_cache.values()
                if v.status == ValidationStatus.DEGRADED
            )
        }
    
    def generate_validation_report(self, strategy_id: str) -> str:
        """Generate detailed validation report"""
        if strategy_id not in self.validation_cache:
            return f"No validation found for strategy {strategy_id}"
        
        v = self.validation_cache[strategy_id]
        
        report = [
            f"=== Walk-Forward Validation Report ===",
            f"Strategy: {strategy_id}",
            f"Status: {v.status.value.upper()}",
            f"Approved: {'YES' if v.is_approved else 'NO'}",
            f"",
            f"=== Aggregate OOS Metrics ===",
            f"Sharpe Ratio: {v.avg_oos_sharpe:.2f}",
            f"Returns: {v.avg_oos_returns:.2%}",
            f"Max Drawdown: {v.avg_oos_drawdown:.2%}",
            f"Win Rate: {v.avg_oos_win_rate:.2%}",
            f"",
            f"=== Quality Metrics ===",
            f"Sharpe Consistency: {v.sharpe_consistency:.2f}",
            f"Overfit Score: {v.overfit_score:.2f}",
            f"Confidence Multiplier: {v.confidence_multiplier:.2f}",
            f"",
        ]
        
        if v.failure_reasons:
            report.append("=== Failure Reasons ===")
            for reason in v.failure_reasons:
                report.append(f"  - {reason}")
            report.append("")
        
        report.append(f"=== Walk Period Details ===")
        for w in v.walk_results:
            report.append(
                f"Period {w.period_id}: IS Sharpe={w.is_sharpe:.2f}, "
                f"OOS Sharpe={w.oos_sharpe:.2f}, Decay={w.performance_decay:.1%}"
            )
        
        return "\n".join(report)

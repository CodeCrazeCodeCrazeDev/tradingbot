"""
Post-Trade Self-Fixing System - Stage 7 Fix

Addresses violations:
- Claim failure rates not tracked
- Confidence calibration curves basic
- Regime misclassification penalties missing
- Strategy half-life decay not systematic
- No automatic disabling

Tracks performance and AUTOMATICALLY disables failing strategies.

Author: AlphaAlgo Core
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Deque
from collections import deque, defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class StrategyStatus(Enum):
    """Strategy status"""
    ACTIVE = "active"
    WARNING = "warning"
    QUARANTINED = "quarantined"
    DISABLED = "disabled"


@dataclass
class ClaimFailureRecord:
    """Record of a claim failure"""
    claim_id: str
    claim_type: str
    predicted_pass: bool
    actual_pass: bool
    conditions: Dict
    timestamp: datetime


@dataclass
class TradeOutcome:
    """Outcome of a trade"""
    trade_id: str
    signal_id: str
    strategy_id: str
    symbol: str
    direction: str
    
    # Predictions
    predicted_regime: str
    predicted_confidence: float
    predicted_pnl: float
    
    # Actuals
    actual_regime: str
    actual_pnl: float
    won: bool
    
    # Claims
    claim_failures: List[str]
    
    timestamp: datetime


@dataclass
class StrategyHealthMetrics:
    """Health metrics for a strategy"""
    strategy_id: str
    status: StrategyStatus
    
    # Performance
    total_trades: int
    win_rate: float
    recent_win_rate: float
    sharpe_ratio: float
    
    # Claim accuracy
    claim_accuracy: float
    claim_failure_rate: float
    
    # Regime accuracy
    regime_accuracy: float
    regime_misclassification_rate: float
    
    # Confidence calibration
    confidence_calibration_error: float
    overconfidence_rate: float
    
    # Alpha decay
    alpha_half_life_days: float
    days_since_last_win: int
    
    # Quarantine info
    quarantine_reason: Optional[str] = None
    quarantine_date: Optional[datetime] = None
    
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ClaimFailureTracker:
    """
    Tracks claim-level failure rates.
    
    Which claims fail most often? Under what conditions?
    """
    
    def __init__(self, max_history: int = 10000):
        try:
            self.max_history = max_history
            self.claim_failures: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_claim_outcome(
        self,
        claim_id: str,
        claim_type: str,
        predicted_pass: bool,
        actual_pass: bool,
        conditions: Dict
    ):
        """Record claim outcome"""
        try:
            record = ClaimFailureRecord(
                claim_id=claim_id,
                claim_type=claim_type,
                predicted_pass=predicted_pass,
                actual_pass=actual_pass,
                conditions=conditions,
                timestamp=datetime.utcnow()
            )
        
            self.claim_failures[claim_type].append(record)
        except Exception as e:
            logger.error(f"Error in record_claim_outcome: {e}")
            raise
    
    def get_claim_failure_rate(self, claim_type: str, window: int = 100) -> float:
        """Get failure rate for claim type"""
        try:
            if claim_type not in self.claim_failures:
                return 0.0
        
            recent = list(self.claim_failures[claim_type])[-window:]
            if not recent:
                return 0.0
        
            failures = sum(1 for r in recent if r.predicted_pass and not r.actual_pass)
            return failures / len(recent)
        except Exception as e:
            logger.error(f"Error in get_claim_failure_rate: {e}")
            raise
    
    def get_claim_accuracy(self, claim_type: str, window: int = 100) -> float:
        """Get accuracy for claim type"""
        try:
            if claim_type not in self.claim_failures:
                return 0.5
        
            recent = list(self.claim_failures[claim_type])[-window:]
            if not recent:
                return 0.5
        
            correct = sum(1 for r in recent if r.predicted_pass == r.actual_pass)
            return correct / len(recent)
        except Exception as e:
            logger.error(f"Error in get_claim_accuracy: {e}")
            raise


class ConfidenceCalibrator:
    """
    Per-claim confidence calibration.
    
    Are we overconfident? Underconfident?
    """
    
    def __init__(self):
        try:
            self.calibration_data: Dict[str, List] = defaultdict(list)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_prediction(
        self,
        claim_type: str,
        predicted_confidence: float,
        actual_outcome: bool
    ):
        """Record prediction for calibration"""
        try:
            self.calibration_data[claim_type].append({
                'confidence': predicted_confidence,
                'outcome': 1.0 if actual_outcome else 0.0,
                'timestamp': datetime.utcnow()
            })
        except Exception as e:
            logger.error(f"Error in record_prediction: {e}")
            raise
    
    def get_calibration_error(self, claim_type: str, window: int = 100) -> float:
        """
        Get calibration error.
        
        Returns:
            Calibration error (0.0 = perfect, 1.0 = terrible)
        """
        try:
            if claim_type not in self.calibration_data:
                return 0.5
        
            recent = self.calibration_data[claim_type][-window:]
            if len(recent) < 10:
                return 0.5
        
            # Bin by confidence
            bins = np.linspace(0, 1, 11)  # 10 bins
            bin_errors = []
        
            for i in range(len(bins) - 1):
                bin_min, bin_max = bins[i], bins[i + 1]
                bin_data = [d for d in recent if bin_min <= d['confidence'] < bin_max]
            
                if len(bin_data) >= 5:
                    avg_confidence = np.mean([d['confidence'] for d in bin_data])
                    avg_outcome = np.mean([d['outcome'] for d in bin_data])
                    bin_error = abs(avg_confidence - avg_outcome)
                    bin_errors.append(bin_error)
        
            if not bin_errors:
                return 0.5
        
            return np.mean(bin_errors)
        except Exception as e:
            logger.error(f"Error in get_calibration_error: {e}")
            raise
    
    def is_overconfident(self, claim_type: str, window: int = 100) -> bool:
        """Check if overconfident"""
        try:
            if claim_type not in self.calibration_data:
                return False
        
            recent = self.calibration_data[claim_type][-window:]
            if len(recent) < 10:
                return False
        
            avg_confidence = np.mean([d['confidence'] for d in recent])
            avg_outcome = np.mean([d['outcome'] for d in recent])
        
            # Overconfident if confidence > outcome by more than 10%
            return (avg_confidence - avg_outcome) > 0.1
        except Exception as e:
            logger.error(f"Error in is_overconfident: {e}")
            raise


class RegimeMisclassificationTracker:
    """
    Tracks regime misclassification.
    
    Heavily penalizes wrong regime predictions.
    """
    
    def __init__(self):
        try:
            self.regime_predictions: deque = deque(maxlen=1000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_regime_prediction(
        self,
        predicted_regime: str,
        actual_regime: str,
        strategy_id: str
    ):
        """Record regime prediction"""
        try:
            self.regime_predictions.append({
                'predicted': predicted_regime,
                'actual': actual_regime,
                'strategy_id': strategy_id,
                'correct': predicted_regime == actual_regime,
                'timestamp': datetime.utcnow()
            })
        except Exception as e:
            logger.error(f"Error in record_regime_prediction: {e}")
            raise
    
    def get_regime_accuracy(self, strategy_id: str, window: int = 50) -> float:
        """Get regime accuracy for strategy"""
        try:
            strategy_predictions = [
                p for p in list(self.regime_predictions)[-window:]
                if p['strategy_id'] == strategy_id
            ]
        
            if not strategy_predictions:
                return 0.5
        
            correct = sum(1 for p in strategy_predictions if p['correct'])
            return correct / len(strategy_predictions)
        except Exception as e:
            logger.error(f"Error in get_regime_accuracy: {e}")
            raise
    
    def get_misclassification_rate(self, strategy_id: str, window: int = 50) -> float:
        """Get misclassification rate"""
        return 1.0 - self.get_regime_accuracy(strategy_id, window)


class StrategyHalfLifeMonitor:
    """
    Monitors strategy half-life.
    
    Tracks how long strategies maintain their edge.
    """
    
    def __init__(self):
        try:
            self.strategy_performance: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_trade(self, strategy_id: str, pnl: float, timestamp: datetime):
        """Record trade"""
        try:
            self.strategy_performance[strategy_id].append({
                'pnl': pnl,
                'timestamp': timestamp
            })
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def estimate_half_life(self, strategy_id: str) -> float:
        """
        Estimate alpha half-life in days.
        
        Returns:
            Days until performance decays to 50%
        """
        try:
            if strategy_id not in self.strategy_performance:
                return 90.0  # Default
        
            trades = list(self.strategy_performance[strategy_id])
            if len(trades) < 50:
                return 90.0
        
            # Split into older and recent
            mid = len(trades) // 2
            older_trades = trades[:mid]
            recent_trades = trades[mid:]
        
            older_avg = np.mean([t['pnl'] for t in older_trades])
            recent_avg = np.mean([t['pnl'] for t in recent_trades])
        
            if older_avg <= 0:
                return 30.0  # Fast decay
        
            # Calculate decay rate
            performance_ratio = recent_avg / older_avg if older_avg > 0 else 0.0
        
            if performance_ratio >= 1.0:
                return 180.0  # No decay, long half-life
            elif performance_ratio >= 0.75:
                return 120.0
            elif performance_ratio >= 0.5:
                return 90.0
            elif performance_ratio >= 0.25:
                return 60.0
            else:
                return 30.0  # Fast decay
        except Exception as e:
            logger.error(f"Error in estimate_half_life: {e}")
            raise
    
    def days_since_last_win(self, strategy_id: str) -> int:
        """Days since last winning trade"""
        try:
            if strategy_id not in self.strategy_performance:
                return 0
        
            trades = list(self.strategy_performance[strategy_id])
        
            # Find last winning trade
            for trade in reversed(trades):
                if trade['pnl'] > 0:
                    days = (datetime.utcnow() - trade['timestamp']).days
                    return days
        
            return 999  # No wins
        except Exception as e:
            logger.error(f"Error in days_since_last_win: {e}")
            raise


class AutomaticStrategyDisabler:
    """
    Automatically disables failing strategies.
    
    NO HUMAN INTERVENTION REQUIRED.
    """
    
    def __init__(self):
        try:
            self.strategy_status: Dict[str, StrategyStatus] = defaultdict(lambda: StrategyStatus.ACTIVE)
            self.quarantine_reasons: Dict[str, str] = {}
            self.quarantine_dates: Dict[str, datetime] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def evaluate_strategy_health(
        self,
        strategy_id: str,
        metrics: StrategyHealthMetrics
    ) -> StrategyStatus:
        """
        Evaluate strategy health and update status.
        
        Automatic quarantine/disable rules:
        1. Win rate < 45% → WARNING
        2. Win rate < 40% → QUARANTINED
        3. Win rate < 35% → DISABLED
        4. Claim failure rate > 30% → QUARANTINED
        5. Regime misclassification > 40% → QUARANTINED
        6. Overconfidence rate > 50% → WARNING
        7. Days since last win > 30 → QUARANTINED
        8. Days since last win > 60 → DISABLED
        """
        try:
            current_status = self.strategy_status[strategy_id]
            new_status = StrategyStatus.ACTIVE
            reason = None
        
            # Rule 1-3: Win rate
            if metrics.recent_win_rate < 0.35:
                new_status = StrategyStatus.DISABLED
                reason = f"Win rate {metrics.recent_win_rate:.2%} < 35%"
            elif metrics.recent_win_rate < 0.40:
                new_status = StrategyStatus.QUARANTINED
                reason = f"Win rate {metrics.recent_win_rate:.2%} < 40%"
            elif metrics.recent_win_rate < 0.45:
                new_status = StrategyStatus.WARNING
                reason = f"Win rate {metrics.recent_win_rate:.2%} < 45%"
        
            # Rule 4: Claim failure rate
            if metrics.claim_failure_rate > 0.30:
                if new_status == StrategyStatus.ACTIVE:
                    new_status = StrategyStatus.QUARANTINED
                    reason = f"Claim failure rate {metrics.claim_failure_rate:.2%} > 30%"
        
            # Rule 5: Regime misclassification
            if metrics.regime_misclassification_rate > 0.40:
                if new_status == StrategyStatus.ACTIVE:
                    new_status = StrategyStatus.QUARANTINED
                    reason = f"Regime misclassification {metrics.regime_misclassification_rate:.2%} > 40%"
        
            # Rule 6: Overconfidence
            if metrics.overconfidence_rate > 0.50:
                if new_status == StrategyStatus.ACTIVE:
                    new_status = StrategyStatus.WARNING
                    reason = f"Overconfidence rate {metrics.overconfidence_rate:.2%} > 50%"
        
            # Rule 7-8: Days since last win
            if metrics.days_since_last_win > 60:
                new_status = StrategyStatus.DISABLED
                reason = f"No wins in {metrics.days_since_last_win} days"
            elif metrics.days_since_last_win > 30:
                if new_status == StrategyStatus.ACTIVE:
                    new_status = StrategyStatus.QUARANTINED
                    reason = f"No wins in {metrics.days_since_last_win} days"
        
            # Update status
            if new_status != current_status:
                self.strategy_status[strategy_id] = new_status
            
                if new_status in [StrategyStatus.QUARANTINED, StrategyStatus.DISABLED]:
                    self.quarantine_reasons[strategy_id] = reason
                    self.quarantine_dates[strategy_id] = datetime.utcnow()
                
                    logger.warning(
                        f"Strategy {strategy_id} status changed: {current_status.value} → {new_status.value}\n"
                        f"  Reason: {reason}"
                    )
        
            return new_status
        except Exception as e:
            logger.error(f"Error in evaluate_strategy_health: {e}")
            raise
    
    def is_strategy_allowed(self, strategy_id: str) -> bool:
        """Check if strategy is allowed to trade"""
        try:
            status = self.strategy_status[strategy_id]
            return status in [StrategyStatus.ACTIVE, StrategyStatus.WARNING]
        except Exception as e:
            logger.error(f"Error in is_strategy_allowed: {e}")
            raise
    
    def get_quarantine_info(self, strategy_id: str) -> Optional[Dict]:
        """Get quarantine info"""
        try:
            if strategy_id not in self.quarantine_reasons:
                return None
        
            return {
                'status': self.strategy_status[strategy_id].value,
                'reason': self.quarantine_reasons[strategy_id],
                'date': self.quarantine_dates[strategy_id],
                'days_quarantined': (datetime.utcnow() - self.quarantine_dates[strategy_id]).days
            }
        except Exception as e:
            logger.error(f"Error in get_quarantine_info: {e}")
            raise


class PostTradeSelfFixingSystem:
    """
    Master post-trade self-fixing system.
    
    Tracks everything and automatically disables failing strategies.
    """
    
    def __init__(self):
        try:
            self.claim_tracker = ClaimFailureTracker()
            self.confidence_calibrator = ConfidenceCalibrator()
            self.regime_tracker = RegimeMisclassificationTracker()
            self.halflife_monitor = StrategyHalfLifeMonitor()
            self.auto_disabler = AutomaticStrategyDisabler()
        
            self.trade_outcomes: deque = deque(maxlen=10000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_trade_outcome(self, outcome: TradeOutcome):
        """Record complete trade outcome"""
        try:
            self.trade_outcomes.append(outcome)
        
            # Update all trackers
            self.halflife_monitor.record_trade(
                outcome.strategy_id,
                outcome.actual_pnl,
                outcome.timestamp
            )
        
            self.regime_tracker.record_regime_prediction(
                outcome.predicted_regime,
                outcome.actual_regime,
                outcome.strategy_id
            )
        
            # Update strategy health
            metrics = self.calculate_strategy_health(outcome.strategy_id)
            status = self.auto_disabler.evaluate_strategy_health(outcome.strategy_id, metrics)
        
            if status in [StrategyStatus.QUARANTINED, StrategyStatus.DISABLED]:
                logger.warning(
                    f"Strategy {outcome.strategy_id} is {status.value}:\n"
                    f"  Win rate: {metrics.recent_win_rate:.2%}\n"
                    f"  Claim failure rate: {metrics.claim_failure_rate:.2%}\n"
                    f"  Regime accuracy: {metrics.regime_accuracy:.2%}\n"
                    f"  Days since last win: {metrics.days_since_last_win}"
                )
        except Exception as e:
            logger.error(f"Error in record_trade_outcome: {e}")
            raise
    
    def calculate_strategy_health(self, strategy_id: str) -> StrategyHealthMetrics:
        """Calculate complete strategy health metrics"""
        try:
            strategy_trades = [
                t for t in self.trade_outcomes
                if t.strategy_id == strategy_id
            ]
        
            if not strategy_trades:
                return StrategyHealthMetrics(
                    strategy_id=strategy_id,
                    status=StrategyStatus.ACTIVE,
                    total_trades=0,
                    win_rate=0.5,
                    recent_win_rate=0.5,
                    sharpe_ratio=0.0,
                    claim_accuracy=0.5,
                    claim_failure_rate=0.0,
                    regime_accuracy=0.5,
                    regime_misclassification_rate=0.5,
                    confidence_calibration_error=0.5,
                    overconfidence_rate=0.0,
                    alpha_half_life_days=90.0,
                    days_since_last_win=0
                )
        
            # Performance metrics
            total_trades = len(strategy_trades)
            wins = sum(1 for t in strategy_trades if t.won)
            win_rate = wins / total_trades if total_trades > 0 else 0.5
        
            recent_trades = strategy_trades[-50:]
            recent_wins = sum(1 for t in recent_trades if t.won)
            recent_win_rate = recent_wins / len(recent_trades) if recent_trades else 0.5
        
            pnls = [t.actual_pnl for t in strategy_trades]
            sharpe = np.mean(pnls) / np.std(pnls) if len(pnls) > 1 and np.std(pnls) > 0 else 0.0
        
            # Claim metrics
            claim_accuracy = self.claim_tracker.get_claim_accuracy('all', window=100)
            claim_failure_rate = self.claim_tracker.get_claim_failure_rate('all', window=100)
        
            # Regime metrics
            regime_accuracy = self.regime_tracker.get_regime_accuracy(strategy_id, window=50)
            regime_misclassification_rate = self.regime_tracker.get_misclassification_rate(strategy_id, window=50)
        
            # Confidence metrics
            confidence_calibration_error = self.confidence_calibrator.get_calibration_error('all', window=100)
            overconfidence_rate = 1.0 if self.confidence_calibrator.is_overconfident('all', window=100) else 0.0
        
            # Alpha decay
            alpha_half_life = self.halflife_monitor.estimate_half_life(strategy_id)
            days_since_win = self.halflife_monitor.days_since_last_win(strategy_id)
        
            # Status
            status = self.auto_disabler.strategy_status[strategy_id]
        
            return StrategyHealthMetrics(
                strategy_id=strategy_id,
                status=status,
                total_trades=total_trades,
                win_rate=win_rate,
                recent_win_rate=recent_win_rate,
                sharpe_ratio=sharpe,
                claim_accuracy=claim_accuracy,
                claim_failure_rate=claim_failure_rate,
                regime_accuracy=regime_accuracy,
                regime_misclassification_rate=regime_misclassification_rate,
                confidence_calibration_error=confidence_calibration_error,
                overconfidence_rate=overconfidence_rate,
                alpha_half_life_days=alpha_half_life,
                days_since_last_win=days_since_win
            )
        except Exception as e:
            logger.error(f"Error in calculate_strategy_health: {e}")
            raise
    
    def is_strategy_allowed(self, strategy_id: str) -> bool:
        """Check if strategy is allowed to trade"""
        return self.auto_disabler.is_strategy_allowed(strategy_id)
    
    def get_all_strategy_health(self) -> Dict[str, StrategyHealthMetrics]:
        """Get health metrics for all strategies"""
        try:
            strategy_ids = set(t.strategy_id for t in self.trade_outcomes)
        
            return {
                strategy_id: self.calculate_strategy_health(strategy_id)
                for strategy_id in strategy_ids
            }
        except Exception as e:
            logger.error(f"Error in get_all_strategy_health: {e}")
            raise


# Global singleton
_global_self_fixer: Optional[PostTradeSelfFixingSystem] = None


def get_global_self_fixer() -> PostTradeSelfFixingSystem:
    """Get global self-fixer singleton"""
    try:
        global _global_self_fixer
        if _global_self_fixer is None:
            _global_self_fixer = PostTradeSelfFixingSystem()
        return _global_self_fixer
    except Exception as e:
        logger.error(f"Error in get_global_self_fixer: {e}")
        raise


def record_trade_outcome(outcome: TradeOutcome):
    """Record trade outcome using global self-fixer"""
    try:
        get_global_self_fixer().record_trade_outcome(outcome)
    except Exception as e:
        logger.error(f"Error in record_trade_outcome: {e}")
        raise


def is_strategy_allowed(strategy_id: str) -> bool:
    """Check if strategy is allowed"""
    return get_global_self_fixer().is_strategy_allowed(strategy_id)

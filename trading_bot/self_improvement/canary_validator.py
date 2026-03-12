"""
Canary Validator
Tests fixes in paper/canary mode before promotion to live.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import numpy as np

from .fix_generator import ProposedFix
import numpy

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Status of canary validation."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class CanaryMetrics:
    """Metrics collected during canary run."""
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: float
    
    # Trading metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Performance metrics
    total_pnl: float
    avg_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    
    # Execution metrics
    avg_slippage: float
    avg_latency_ms: float
    fill_rate: float
    
    # Signal metrics
    signal_count: int
    signal_rate_per_hour: float
    avg_confidence: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        try:
            data = asdict(self)
            data['start_time'] = self.start_time.isoformat()
            data['end_time'] = self.end_time.isoformat() if self.end_time else None
            return data
        except Exception as e:
            logger.error(f"Error in to_dict: {e}")
            raise


@dataclass
class ValidationResult:
    """Result of canary validation."""
    fix_id: str
    status: ValidationStatus
    start_time: datetime
    end_time: Optional[datetime]
    
    canary_metrics: CanaryMetrics
    baseline_metrics: Optional[CanaryMetrics]
    
    comparison: Dict[str, Any]  # Comparison vs baseline
    passed_criteria: List[str]
    failed_criteria: List[str]
    
    recommendation: str  # 'promote', 'reject', 'extend_testing'
    confidence: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'fix_id': self.fix_id,
            'status': self.status.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'canary_metrics': self.canary_metrics.to_dict(),
            'baseline_metrics': self.baseline_metrics.to_dict() if self.baseline_metrics else None,
            'comparison': self.comparison,
            'passed_criteria': self.passed_criteria,
            'failed_criteria': self.failed_criteria,
            'recommendation': self.recommendation,
            'confidence': self.confidence
        }


class CanaryValidator:
    """
    Validates fixes in paper/canary mode before live deployment.
    Compares canary performance against baseline metrics.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize canary validator.
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config
        
            # Canary configuration
            self.canary_duration_minutes = config.get('canary_duration_minutes', 60)
            self.canary_min_trades = config.get('canary_min_trades', 100)
            self.canary_instruments = config.get('canary_instruments', ['EURUSD', 'GBPUSD'])
        
            # Validation thresholds
            self.max_win_rate_degradation = config.get('max_win_rate_degradation', 0.10)  # 10%
            self.max_drawdown_increase = config.get('max_drawdown_increase', 0.05)  # 5%
            self.min_trade_count = config.get('min_trade_count', 30)
            self.max_slippage_increase = config.get('max_slippage_increase', 0.002)  # 0.2%
        
            # Active canary runs
            self.active_canaries = {}
        
            logger.info("CanaryValidator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def start_canary(self, fix: ProposedFix, baseline_metrics: Optional[CanaryMetrics] = None) -> str:
        """
        Start a canary validation run for a fix.
        
        Args:
            fix: Proposed fix to validate
            baseline_metrics: Optional baseline metrics for comparison
            
        Returns:
            Canary run ID
        """
        try:
            canary_id = f"canary_{fix.fix_id}_{int(datetime.now().timestamp())}"
        
            self.active_canaries[canary_id] = {
                'fix': fix,
                'baseline_metrics': baseline_metrics,
                'start_time': datetime.now(),
                'status': ValidationStatus.RUNNING,
                'trades': [],
                'signals': []
            }
        
            logger.info(f"Started canary {canary_id} for fix {fix.fix_id}")
            logger.info(f"  Duration: {self.canary_duration_minutes} minutes")
            logger.info(f"  Min trades: {self.canary_min_trades}")
            logger.info(f"  Instruments: {self.canary_instruments}")
        
            return canary_id
        except Exception as e:
            logger.error(f"Error in start_canary: {e}")
            raise
    
    def record_trade(self, canary_id: str, trade: Dict[str, Any]):
        """
        Record a trade during canary run.
        
        Args:
            canary_id: Canary run ID
            trade: Trade data
        """
        try:
            if canary_id not in self.active_canaries:
                logger.warning(f"Unknown canary ID: {canary_id}")
                return
        
            self.active_canaries[canary_id]['trades'].append(trade)
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def record_signal(self, canary_id: str, signal: Dict[str, Any]):
        """
        Record a signal during canary run.
        
        Args:
            canary_id: Canary run ID
            signal: Signal data
        """
        try:
            if canary_id not in self.active_canaries:
                logger.warning(f"Unknown canary ID: {canary_id}")
                return
        
            self.active_canaries[canary_id]['signals'].append(signal)
        except Exception as e:
            logger.error(f"Error in record_signal: {e}")
            raise
    
    def check_canary_completion(self, canary_id: str) -> bool:
        """
        Check if canary run is complete.
        
        Args:
            canary_id: Canary run ID
            
        Returns:
            True if complete, False otherwise
        """
        try:
            if canary_id not in self.active_canaries:
                return False
        
            canary = self.active_canaries[canary_id]
        
            # Check duration
            elapsed = (datetime.now() - canary['start_time']).total_seconds() / 60
            duration_met = elapsed >= self.canary_duration_minutes
        
            # Check trade count
            trade_count_met = len(canary['trades']) >= self.canary_min_trades
        
            return duration_met or trade_count_met
        except Exception as e:
            logger.error(f"Error in check_canary_completion: {e}")
            raise
    
    def finalize_canary(self, canary_id: str) -> ValidationResult:
        """
        Finalize canary run and generate validation result.
        
        Args:
            canary_id: Canary run ID
            
        Returns:
            ValidationResult with pass/fail decision
        """
        try:
            if canary_id not in self.active_canaries:
                raise ValueError(f"Unknown canary ID: {canary_id}")
        
            canary = self.active_canaries[canary_id]
            fix = canary['fix']
            baseline = canary['baseline_metrics']
        
            # Calculate canary metrics
            canary_metrics = self._calculate_metrics(
                canary['trades'],
                canary['signals'],
                canary['start_time'],
                datetime.now()
            )
        
            # Compare against baseline
            comparison = self._compare_metrics(canary_metrics, baseline)
        
            # Evaluate validation criteria
            passed_criteria, failed_criteria = self._evaluate_criteria(
                canary_metrics,
                baseline,
                fix.validation_criteria
            )
        
            # Determine status and recommendation
            if failed_criteria:
                status = ValidationStatus.FAILED
                recommendation = 'reject'
                confidence = 0.0
            elif len(canary['trades']) < self.min_trade_count:
                status = ValidationStatus.TIMEOUT
                recommendation = 'extend_testing'
                confidence = 0.5
            else:
                status = ValidationStatus.PASSED
                recommendation = 'promote'
                confidence = self._calculate_confidence(passed_criteria, canary_metrics)
        
            result = ValidationResult(
                fix_id=fix.fix_id,
                status=status,
                start_time=canary['start_time'],
                end_time=datetime.now(),
                canary_metrics=canary_metrics,
                baseline_metrics=baseline,
                comparison=comparison,
                passed_criteria=passed_criteria,
                failed_criteria=failed_criteria,
                recommendation=recommendation,
                confidence=confidence
            )
        
            # Clean up
            del self.active_canaries[canary_id]
        
            logger.info(f"Canary {canary_id} finalized: {status.value}")
            logger.info(f"  Recommendation: {recommendation}")
            logger.info(f"  Passed criteria: {len(passed_criteria)}")
            logger.info(f"  Failed criteria: {len(failed_criteria)}")
        
            return result
        except Exception as e:
            logger.error(f"Error in finalize_canary: {e}")
            raise
    
    def _calculate_metrics(self, trades: List[Dict], signals: List[Dict],
                          start_time: datetime, end_time: datetime) -> CanaryMetrics:
        """Calculate metrics from trades and signals."""
        try:
            if not trades:
                # No trades - return zero metrics
                duration = (end_time - start_time).total_seconds() / 60
                return CanaryMetrics(
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=duration,
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0.0,
                    total_pnl=0.0,
                    avg_pnl=0.0,
                    max_drawdown=0.0,
                    sharpe_ratio=0.0,
                    avg_slippage=0.0,
                    avg_latency_ms=0.0,
                    fill_rate=0.0,
                    signal_count=len(signals),
                    signal_rate_per_hour=len(signals) / (duration / 60) if duration > 0 else 0,
                    avg_confidence=np.mean([s.get('confidence', 0) for s in signals]) if signals else 0
                )
        
            # Calculate trading metrics
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
            losing_trades = sum(1 for t in trades if t.get('pnl', 0) < 0)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
            # Performance metrics
            pnls = [t.get('pnl', 0) for t in trades]
            total_pnl = sum(pnls)
            avg_pnl = np.mean(pnls)
        
            # Calculate drawdown
            cumulative_pnl = np.cumsum(pnls)
            running_max = np.maximum.accumulate(cumulative_pnl)
            drawdowns = running_max - cumulative_pnl
            max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
            # Sharpe ratio (simplified)
            sharpe_ratio = (np.mean(pnls) / np.std(pnls)) if np.std(pnls) > 0 else 0
        
            # Execution metrics
            avg_slippage = np.mean([t.get('slippage', 0) for t in trades])
            avg_latency_ms = np.mean([t.get('execution_latency_ms', 0) for t in trades])
        
            # Fill rate (assume full fills if not specified)
            full_fills = sum(1 for t in trades if t.get('fill_type', 'full') == 'full')
            fill_rate = full_fills / total_trades if total_trades > 0 else 1.0
        
            # Signal metrics
            duration = (end_time - start_time).total_seconds() / 60
            signal_rate = len(signals) / (duration / 60) if duration > 0 else 0
            avg_confidence = np.mean([s.get('confidence', 0) for s in signals]) if signals else 0
        
            return CanaryMetrics(
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_pnl=total_pnl,
                avg_pnl=avg_pnl,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                avg_slippage=avg_slippage,
                avg_latency_ms=avg_latency_ms,
                fill_rate=fill_rate,
                signal_count=len(signals),
                signal_rate_per_hour=signal_rate,
                avg_confidence=avg_confidence
            )
        except Exception as e:
            logger.error(f"Error in _calculate_metrics: {e}")
            raise
    
    def _compare_metrics(self, canary: CanaryMetrics, 
                        baseline: Optional[CanaryMetrics]) -> Dict[str, Any]:
        """Compare canary metrics against baseline."""
        try:
            if not baseline:
                return {'note': 'No baseline available for comparison'}
        
            comparison = {}
        
            # Win rate comparison
            if baseline.win_rate > 0:
                win_rate_change = (canary.win_rate - baseline.win_rate) / baseline.win_rate
                comparison['win_rate_change_pct'] = win_rate_change * 100
        
            # Drawdown comparison
            drawdown_change = canary.max_drawdown - baseline.max_drawdown
            comparison['drawdown_change'] = drawdown_change
        
            # PnL comparison
            if baseline.avg_pnl != 0:
                pnl_change = (canary.avg_pnl - baseline.avg_pnl) / abs(baseline.avg_pnl)
                comparison['avg_pnl_change_pct'] = pnl_change * 100
        
            # Slippage comparison
            slippage_change = canary.avg_slippage - baseline.avg_slippage
            comparison['slippage_change'] = slippage_change
        
            # Signal rate comparison
            if baseline.signal_rate_per_hour > 0:
                signal_rate_change = (canary.signal_rate_per_hour - baseline.signal_rate_per_hour) / baseline.signal_rate_per_hour
                comparison['signal_rate_change_pct'] = signal_rate_change * 100
        
            return comparison
        except Exception as e:
            logger.error(f"Error in _compare_metrics: {e}")
            raise
    
    def _evaluate_criteria(self, canary: CanaryMetrics, baseline: Optional[CanaryMetrics],
                          validation_criteria: Dict[str, Any]) -> tuple:
        """Evaluate validation criteria."""
        try:
            passed = []
            failed = []
        
            # Minimum trade count
            if canary.total_trades >= self.min_trade_count:
                passed.append(f"Minimum trade count met: {canary.total_trades}")
            else:
                failed.append(f"Insufficient trades: {canary.total_trades} < {self.min_trade_count}")
        
            if baseline:
                # Win rate degradation check
                if baseline.win_rate > 0:
                    win_rate_change = (canary.win_rate - baseline.win_rate) / baseline.win_rate
                    if win_rate_change >= -self.max_win_rate_degradation:
                        passed.append(f"Win rate acceptable: {win_rate_change*100:.1f}% change")
                    else:
                        failed.append(f"Win rate degraded: {win_rate_change*100:.1f}% < -{self.max_win_rate_degradation*100}%")
            
                # Drawdown increase check
                drawdown_increase = canary.max_drawdown - baseline.max_drawdown
                if drawdown_increase <= self.max_drawdown_increase:
                    passed.append(f"Drawdown acceptable: +{drawdown_increase:.4f}")
                else:
                    failed.append(f"Drawdown increased: +{drawdown_increase:.4f} > {self.max_drawdown_increase}")
            
                # Slippage increase check
                slippage_increase = canary.avg_slippage - baseline.avg_slippage
                if slippage_increase <= self.max_slippage_increase:
                    passed.append(f"Slippage acceptable: +{slippage_increase:.4f}")
                else:
                    failed.append(f"Slippage increased: +{slippage_increase:.4f} > {self.max_slippage_increase}")
        
            # Custom validation criteria from fix
            if 'win_rate_improvement' in validation_criteria:
                target = validation_criteria['win_rate_improvement']
                if baseline and baseline.win_rate > 0:
                    improvement = canary.win_rate - baseline.win_rate
                    if improvement >= target:
                        passed.append(f"Win rate improved: +{improvement:.2%}")
                    else:
                        failed.append(f"Win rate improvement insufficient: +{improvement:.2%} < {target:.2%}")
        
            if 'max_drawdown_reduction' in validation_criteria:
                target = validation_criteria['max_drawdown_reduction']
                if baseline:
                    reduction = baseline.max_drawdown - canary.max_drawdown
                    if reduction >= target:
                        passed.append(f"Drawdown reduced: -{reduction:.4f}")
                    # Note: Not failing if reduction target not met, as long as it didn't increase
        
            return passed, failed
        except Exception as e:
            logger.error(f"Error in _evaluate_criteria: {e}")
            raise
    
    def _calculate_confidence(self, passed_criteria: List[str], 
                            metrics: CanaryMetrics) -> float:
        """Calculate confidence in validation result."""
        try:
            confidence = 0.5  # Base confidence
        
            # Increase confidence based on trade count
            if metrics.total_trades >= 100:
                confidence += 0.2
            elif metrics.total_trades >= 50:
                confidence += 0.1
        
            # Increase confidence based on passed criteria
            confidence += min(0.3, len(passed_criteria) * 0.05)
        
            return min(1.0, confidence)
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise

"""
Drift Detection Gate - Detecting When the World Has Changed

This gate detects when market conditions have changed enough that
our models/strategies may no longer be valid.

THE PROBLEM:
- Strategy trained on 2020-2022 data
- Works great in backtest
- 2023: Market regime completely different
- Strategy fails catastrophically

TYPES OF DRIFT:
1. Concept Drift - Relationship between features and target changes
2. Data Drift - Distribution of input features changes
3. Regime Drift - Market regime (trending/ranging/volatile) changes
4. Correlation Drift - Asset correlations change
5. Volatility Drift - Volatility regime changes

RULE: "Yesterday's model may not work today. Detect change before it kills you."

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


class DriftType(Enum):
    """Types of drift we detect"""
    CONCEPT_DRIFT = "concept_drift"  # Feature-target relationship changed
    DATA_DRIFT = "data_drift"  # Input distribution changed
    REGIME_DRIFT = "regime_drift"  # Market regime changed
    CORRELATION_DRIFT = "correlation_drift"  # Correlations changed
    VOLATILITY_DRIFT = "volatility_drift"  # Volatility regime changed
    PERFORMANCE_DRIFT = "performance_drift"  # Strategy performance degraded
    LIQUIDITY_DRIFT = "liquidity_drift"  # Liquidity conditions changed


class DriftSeverity(Enum):
    """Severity of detected drift"""
    NONE = "none"
    MINOR = "minor"  # Monitor closely
    MODERATE = "moderate"  # Reduce position sizes
    SEVERE = "severe"  # Halt new trades
    CRITICAL = "critical"  # Close all positions


@dataclass
class DriftAlert:
    """Alert for detected drift"""
    drift_type: DriftType
    severity: DriftSeverity
    
    # Metrics
    drift_score: float  # 0-1, higher = more drift
    confidence: float  # Confidence in detection
    
    # Details
    baseline_value: float
    current_value: float
    threshold: float
    
    # Timing
    detected_at: datetime = field(default_factory=datetime.utcnow)
    drift_started: Optional[datetime] = None
    
    # Recommendations
    recommended_action: str = ""
    
    def __str__(self):
        return (
            f"[{self.severity.value.upper()}] {self.drift_type.value}: "
            f"score={self.drift_score:.2f}, baseline={self.baseline_value:.3f}, "
            f"current={self.current_value:.3f}"
        )


@dataclass
class DriftStatus:
    """Overall drift status"""
    is_stable: bool
    overall_drift_score: float
    active_alerts: List[DriftAlert]
    
    # Recommended actions
    should_halt_trading: bool
    should_reduce_size: bool
    position_size_multiplier: float
    
    # Time since last stable
    time_in_drift: Optional[timedelta] = None


class DriftDetectionGate:
    """
    HARD GATE: Drift Detection
    
    This gate continuously monitors for drift and BLOCKS trading
    when significant drift is detected.
    
    Monitors:
    1. Feature distributions (data drift)
    2. Model predictions vs actuals (concept drift)
    3. Market regime indicators (regime drift)
    4. Asset correlations (correlation drift)
    5. Volatility levels (volatility drift)
    6. Strategy performance (performance drift)
    
    Actions:
    - Minor drift: Log and monitor
    - Moderate drift: Reduce position sizes
    - Severe drift: Halt new trades
    - Critical drift: Close all positions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Detection thresholds
            self.data_drift_threshold = self.config.get('data_drift_threshold', 0.3)
            self.concept_drift_threshold = self.config.get('concept_drift_threshold', 0.25)
            self.regime_drift_threshold = self.config.get('regime_drift_threshold', 0.4)
            self.correlation_drift_threshold = self.config.get('correlation_drift_threshold', 0.3)
            self.volatility_drift_threshold = self.config.get('volatility_drift_threshold', 0.5)
            self.performance_drift_threshold = self.config.get('performance_drift_threshold', 0.3)
        
            # Baseline windows
            self.baseline_window = self.config.get('baseline_window', 100)  # Data points
            self.detection_window = self.config.get('detection_window', 20)  # Recent data points
        
            # Historical data for baseline
            self.feature_history: Dict[str, deque] = {}
            self.prediction_history: deque = deque(maxlen=500)
            self.actual_history: deque = deque(maxlen=500)
            self.return_history: deque = deque(maxlen=500)
            self.volatility_history: deque = deque(maxlen=500)
            self.correlation_history: deque = deque(maxlen=100)
        
            # Regime tracking
            self.regime_history: deque = deque(maxlen=100)
            self.current_regime: Optional[str] = None
        
            # Alert history
            self.alert_history: List[DriftAlert] = []
            self.drift_start_time: Optional[datetime] = None
        
            # Statistics
            self.checks_performed = 0
            self.drifts_detected = 0
            self.trading_halted_count = 0
        
            logger.info("DriftDetectionGate initialized - MONITORING FOR REGIME CHANGE")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check_drift(
        self,
        features: Dict[str, float],
        prediction: Optional[float] = None,
        actual: Optional[float] = None,
        current_return: Optional[float] = None,
        current_volatility: Optional[float] = None,
        current_regime: Optional[str] = None,
        correlations: Optional[Dict[str, float]] = None
    ) -> DriftStatus:
        """
        Check for all types of drift.
        
        Args:
            features: Current feature values
            prediction: Model's prediction (if available)
            actual: Actual outcome (if available)
            current_return: Current period return
            current_volatility: Current volatility
            current_regime: Current market regime
            correlations: Current asset correlations
            
        Returns:
            DriftStatus with alerts and recommendations
        """
        try:
            self.checks_performed += 1
            alerts = []
        
            # Update histories
            self._update_histories(
                features, prediction, actual, current_return,
                current_volatility, current_regime, correlations
            )
        
            # 1. Check data drift (feature distribution changes)
            data_drift_alert = self._check_data_drift(features)
            if data_drift_alert:
                alerts.append(data_drift_alert)
        
            # 2. Check concept drift (prediction accuracy changes)
            if len(self.prediction_history) >= self.detection_window:
                concept_drift_alert = self._check_concept_drift()
                if concept_drift_alert:
                    alerts.append(concept_drift_alert)
        
            # 3. Check regime drift
            if current_regime:
                regime_drift_alert = self._check_regime_drift(current_regime)
                if regime_drift_alert:
                    alerts.append(regime_drift_alert)
        
            # 4. Check volatility drift
            if current_volatility is not None:
                vol_drift_alert = self._check_volatility_drift(current_volatility)
                if vol_drift_alert:
                    alerts.append(vol_drift_alert)
        
            # 5. Check correlation drift
            if correlations:
                corr_drift_alert = self._check_correlation_drift(correlations)
                if corr_drift_alert:
                    alerts.append(corr_drift_alert)
        
            # 6. Check performance drift
            if len(self.return_history) >= self.detection_window:
                perf_drift_alert = self._check_performance_drift()
                if perf_drift_alert:
                    alerts.append(perf_drift_alert)
        
            # Calculate overall drift score
            if alerts:
                overall_drift = max(a.drift_score for a in alerts)
                max_severity = max(a.severity.value for a in alerts)
                self.drifts_detected += 1
            else:
                overall_drift = 0.0
                max_severity = DriftSeverity.NONE.value
        
            # Determine actions
            should_halt = any(
                a.severity in [DriftSeverity.SEVERE, DriftSeverity.CRITICAL]
                for a in alerts
            )
            should_reduce = any(
                a.severity == DriftSeverity.MODERATE
                for a in alerts
            )
        
            if should_halt:
                position_multiplier = 0.0
                self.trading_halted_count += 1
            elif should_reduce:
                position_multiplier = 0.5
            elif alerts:
                position_multiplier = 0.8
            else:
                position_multiplier = 1.0
        
            # Track drift duration
            if alerts and self.drift_start_time is None:
                self.drift_start_time = datetime.utcnow()
            elif not alerts:
                self.drift_start_time = None
        
            time_in_drift = None
            if self.drift_start_time:
                time_in_drift = datetime.utcnow() - self.drift_start_time
        
            # Store alerts
            self.alert_history.extend(alerts)
            if len(self.alert_history) > 1000:
                self.alert_history = self.alert_history[-500:]
        
            status = DriftStatus(
                is_stable=len(alerts) == 0,
                overall_drift_score=overall_drift,
                active_alerts=alerts,
                should_halt_trading=should_halt,
                should_reduce_size=should_reduce,
                position_size_multiplier=position_multiplier,
                time_in_drift=time_in_drift
            )
        
            if should_halt:
                logger.error(f"DRIFT DETECTION GATE: TRADING HALTED - {len(alerts)} alerts")
                for alert in alerts:
                    logger.error(f"  {alert}")
            elif alerts:
                logger.warning(f"Drift detected: {len(alerts)} alerts, multiplier={position_multiplier}")
        
            return status
        except Exception as e:
            logger.error(f"Error in check_drift: {e}")
            raise
    
    def _update_histories(
        self,
        features: Dict[str, float],
        prediction: Optional[float],
        actual: Optional[float],
        current_return: Optional[float],
        current_volatility: Optional[float],
        current_regime: Optional[str],
        correlations: Optional[Dict[str, float]]
    ):
        """Update historical data"""
        # Features
        try:
            for name, value in features.items():
                if name not in self.feature_history:
                    self.feature_history[name] = deque(maxlen=self.baseline_window)
                if value is not None and not math.isnan(value):
                    self.feature_history[name].append(value)
        
            # Predictions and actuals
            if prediction is not None:
                self.prediction_history.append(prediction)
            if actual is not None:
                self.actual_history.append(actual)
        
            # Returns
            if current_return is not None:
                self.return_history.append(current_return)
        
            # Volatility
            if current_volatility is not None:
                self.volatility_history.append(current_volatility)
        
            # Regime
            if current_regime:
                self.regime_history.append(current_regime)
                self.current_regime = current_regime
        
            # Correlations
            if correlations:
                self.correlation_history.append(correlations)
        except Exception as e:
            logger.error(f"Error in _update_histories: {e}")
            raise
    
    def _check_data_drift(self, features: Dict[str, float]) -> Optional[DriftAlert]:
        """Check for data drift using PSI (Population Stability Index)"""
        try:
            drift_scores = []
        
            for name, current_value in features.items():
                if name not in self.feature_history:
                    continue
            
                history = list(self.feature_history[name])
                if len(history) < self.baseline_window // 2:
                    continue
            
                # Calculate PSI-like metric
                baseline = history[:len(history)//2]
                recent = history[-self.detection_window:]
            
                if len(baseline) < 5 or len(recent) < 5:
                    continue
            
                baseline_mean = statistics.mean(baseline)
                baseline_std = statistics.stdev(baseline) if len(baseline) > 1 else 1
                recent_mean = statistics.mean(recent)
            
                if baseline_std > 0:
                    z_score = abs(recent_mean - baseline_mean) / baseline_std
                    drift_score = min(1.0, z_score / 3)  # Normalize
                    drift_scores.append((name, drift_score, baseline_mean, recent_mean))
        
            if not drift_scores:
                return None
        
            # Use max drift across features
            max_drift = max(drift_scores, key=lambda x: x[1])
        
            if max_drift[1] > self.data_drift_threshold:
                severity = self._score_to_severity(max_drift[1])
            
                return DriftAlert(
                    drift_type=DriftType.DATA_DRIFT,
                    severity=severity,
                    drift_score=max_drift[1],
                    confidence=0.8,
                    baseline_value=max_drift[2],
                    current_value=max_drift[3],
                    threshold=self.data_drift_threshold,
                    recommended_action=f"Feature '{max_drift[0]}' distribution changed significantly"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _check_data_drift: {e}")
            raise
    
    def _check_concept_drift(self) -> Optional[DriftAlert]:
        """Check for concept drift (prediction accuracy degradation)"""
        try:
            if len(self.prediction_history) < self.baseline_window // 2:
                return None
            if len(self.actual_history) < self.baseline_window // 2:
                return None
        
            predictions = list(self.prediction_history)
            actuals = list(self.actual_history)
        
            min_len = min(len(predictions), len(actuals))
            predictions = predictions[-min_len:]
            actuals = actuals[-min_len:]
        
            # Calculate baseline accuracy (first half)
            mid = len(predictions) // 2
            baseline_errors = [
                abs(p - a) for p, a in zip(predictions[:mid], actuals[:mid])
            ]
            recent_errors = [
                abs(p - a) for p, a in zip(predictions[-self.detection_window:], actuals[-self.detection_window:])
            ]
        
            if not baseline_errors or not recent_errors:
                return None
        
            baseline_mae = statistics.mean(baseline_errors)
            recent_mae = statistics.mean(recent_errors)
        
            if baseline_mae > 0:
                drift_score = (recent_mae - baseline_mae) / baseline_mae
                drift_score = max(0, min(1, drift_score))
            else:
                drift_score = 0
        
            if drift_score > self.concept_drift_threshold:
                severity = self._score_to_severity(drift_score)
            
                return DriftAlert(
                    drift_type=DriftType.CONCEPT_DRIFT,
                    severity=severity,
                    drift_score=drift_score,
                    confidence=0.7,
                    baseline_value=baseline_mae,
                    current_value=recent_mae,
                    threshold=self.concept_drift_threshold,
                    recommended_action="Model predictions degraded - consider retraining"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _check_concept_drift: {e}")
            raise
    
    def _check_regime_drift(self, current_regime: str) -> Optional[DriftAlert]:
        """Check for market regime changes"""
        try:
            if len(self.regime_history) < 10:
                return None
        
            recent_regimes = list(self.regime_history)[-20:]
        
            # Count regime distribution
            regime_counts = {}
            for r in recent_regimes:
                regime_counts[r] = regime_counts.get(r, 0) + 1
        
            # Check if current regime is different from dominant
            dominant_regime = max(regime_counts, key=regime_counts.get)
            dominant_pct = regime_counts[dominant_regime] / len(recent_regimes)
        
            # Check for regime instability
            num_changes = sum(
                1 for i in range(1, len(recent_regimes))
                if recent_regimes[i] != recent_regimes[i-1]
            )
            change_rate = num_changes / len(recent_regimes)
        
            drift_score = change_rate  # High change rate = drift
        
            if drift_score > self.regime_drift_threshold or dominant_pct < 0.5:
                severity = self._score_to_severity(drift_score)
            
                return DriftAlert(
                    drift_type=DriftType.REGIME_DRIFT,
                    severity=severity,
                    drift_score=drift_score,
                    confidence=0.75,
                    baseline_value=0.1,  # Expected change rate
                    current_value=change_rate,
                    threshold=self.regime_drift_threshold,
                    recommended_action=f"Regime unstable: {num_changes} changes in {len(recent_regimes)} periods"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _check_regime_drift: {e}")
            raise
    
    def _check_volatility_drift(self, current_volatility: float) -> Optional[DriftAlert]:
        """Check for volatility regime changes"""
        try:
            if len(self.volatility_history) < self.baseline_window // 2:
                return None
        
            history = list(self.volatility_history)
            baseline = history[:len(history)//2]
        
            baseline_mean = statistics.mean(baseline)
            baseline_std = statistics.stdev(baseline) if len(baseline) > 1 else baseline_mean * 0.2
        
            if baseline_std > 0:
                z_score = abs(current_volatility - baseline_mean) / baseline_std
                drift_score = min(1.0, z_score / 3)
            else:
                drift_score = 0
        
            if drift_score > self.volatility_drift_threshold:
                severity = self._score_to_severity(drift_score)
            
                direction = "increased" if current_volatility > baseline_mean else "decreased"
            
                return DriftAlert(
                    drift_type=DriftType.VOLATILITY_DRIFT,
                    severity=severity,
                    drift_score=drift_score,
                    confidence=0.85,
                    baseline_value=baseline_mean,
                    current_value=current_volatility,
                    threshold=self.volatility_drift_threshold,
                    recommended_action=f"Volatility {direction} significantly - adjust position sizes"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _check_volatility_drift: {e}")
            raise
    
    def _check_correlation_drift(self, correlations: Dict[str, float]) -> Optional[DriftAlert]:
        """Check for correlation structure changes"""
        try:
            if len(self.correlation_history) < 10:
                return None
        
            # Get baseline correlations
            baseline_corrs = list(self.correlation_history)[:len(self.correlation_history)//2]
        
            # Average baseline
            baseline_avg = {}
            for corr_dict in baseline_corrs:
                for pair, value in corr_dict.items():
                    if pair not in baseline_avg:
                        baseline_avg[pair] = []
                    baseline_avg[pair].append(value)
        
            baseline_avg = {k: statistics.mean(v) for k, v in baseline_avg.items()}
        
            # Compare current to baseline
            drift_scores = []
            for pair, current_corr in correlations.items():
                if pair in baseline_avg:
                    diff = abs(current_corr - baseline_avg[pair])
                    drift_scores.append(diff)
        
            if not drift_scores:
                return None
        
            avg_drift = statistics.mean(drift_scores)
            drift_score = min(1.0, avg_drift / 0.5)  # 0.5 correlation change = max drift
        
            if drift_score > self.correlation_drift_threshold:
                severity = self._score_to_severity(drift_score)
            
                return DriftAlert(
                    drift_type=DriftType.CORRELATION_DRIFT,
                    severity=severity,
                    drift_score=drift_score,
                    confidence=0.7,
                    baseline_value=0,
                    current_value=avg_drift,
                    threshold=self.correlation_drift_threshold,
                    recommended_action="Correlation structure changed - review portfolio hedges"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _check_correlation_drift: {e}")
            raise
    
    def _check_performance_drift(self) -> Optional[DriftAlert]:
        """Check for strategy performance degradation"""
        try:
            if len(self.return_history) < self.baseline_window // 2:
                return None
        
            returns = list(self.return_history)
            baseline = returns[:len(returns)//2]
            recent = returns[-self.detection_window:]
        
            baseline_sharpe = self._calculate_sharpe(baseline)
            recent_sharpe = self._calculate_sharpe(recent)
        
            if baseline_sharpe > 0:
                drift_score = max(0, (baseline_sharpe - recent_sharpe) / baseline_sharpe)
                drift_score = min(1.0, drift_score)
            else:
                drift_score = 0 if recent_sharpe >= 0 else 0.5
        
            if drift_score > self.performance_drift_threshold:
                severity = self._score_to_severity(drift_score)
            
                return DriftAlert(
                    drift_type=DriftType.PERFORMANCE_DRIFT,
                    severity=severity,
                    drift_score=drift_score,
                    confidence=0.8,
                    baseline_value=baseline_sharpe,
                    current_value=recent_sharpe,
                    threshold=self.performance_drift_threshold,
                    recommended_action=f"Performance degraded: Sharpe {baseline_sharpe:.2f} -> {recent_sharpe:.2f}"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _check_performance_drift: {e}")
            raise
    
    def _calculate_sharpe(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio from returns"""
        try:
            if len(returns) < 2:
                return 0.0
        
            mean_ret = statistics.mean(returns)
            std_ret = statistics.stdev(returns)
        
            if std_ret == 0:
                return 0.0
        
            return mean_ret / std_ret * math.sqrt(252)
        except Exception as e:
            logger.error(f"Error in _calculate_sharpe: {e}")
            raise
    
    def _score_to_severity(self, score: float) -> DriftSeverity:
        """Convert drift score to severity level"""
        try:
            if score > 0.8:
                return DriftSeverity.CRITICAL
            elif score > 0.6:
                return DriftSeverity.SEVERE
            elif score > 0.4:
                return DriftSeverity.MODERATE
            elif score > 0.2:
                return DriftSeverity.MINOR
            else:
                return DriftSeverity.NONE
        except Exception as e:
            logger.error(f"Error in _score_to_severity: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gate statistics"""
        return {
            'checks_performed': self.checks_performed,
            'drifts_detected': self.drifts_detected,
            'trading_halted_count': self.trading_halted_count,
            'drift_rate': self.drifts_detected / max(self.checks_performed, 1),
            'current_regime': self.current_regime,
            'time_in_drift': str(datetime.utcnow() - self.drift_start_time) if self.drift_start_time else None,
            'recent_alerts': len([a for a in self.alert_history if (datetime.utcnow() - a.detected_at).total_seconds() < 3600])
        }
    
    def reset_baseline(self):
        """Reset baseline data (use after confirmed regime change)"""
        try:
            for history in self.feature_history.values():
                history.clear()
            self.prediction_history.clear()
            self.actual_history.clear()
            self.return_history.clear()
            self.volatility_history.clear()
            self.correlation_history.clear()
            self.drift_start_time = None
            logger.info("Drift detection baseline reset")
        except Exception as e:
            logger.error(f"Error in reset_baseline: {e}")
            raise

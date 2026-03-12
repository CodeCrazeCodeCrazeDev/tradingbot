"""
AlphaAlgo MSOS - Loss Shape & Damage Monitoring

Monitor not just drawdown, but:
- Loss clustering
- Drawdown acceleration
- Asymmetric tail exposure
- Recovery degradation

If loss shape deteriorates:
- Size is throttled
- Strategy suspended
- Post-mortem required

Author: AlphaAlgo MSOS
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class LossShape(Enum):
    """Loss shape classifications"""
    NORMAL = auto()           # Expected loss distribution
    CLUSTERED = auto()        # Losses are bunched together
    ACCELERATING = auto()     # Losses are getting worse
    ASYMMETRIC = auto()       # Tail losses dominate
    DEGRADING = auto()        # Recovery is getting harder
    CATASTROPHIC = auto()     # Multiple issues present


class DamageLevel(Enum):
    """Damage severity levels"""
    NONE = auto()
    MINOR = auto()
    MODERATE = auto()
    SEVERE = auto()
    CRITICAL = auto()


@dataclass
class DrawdownAcceleration:
    """Drawdown acceleration metrics"""
    current_drawdown: float = 0.0
    drawdown_velocity: float = 0.0  # Rate of change
    drawdown_acceleration: float = 0.0  # Second derivative
    time_in_drawdown: float = 0.0  # Days
    is_accelerating: bool = False
    
    def calculate_severity(self) -> float:
        """Calculate severity score (0-1)"""
        try:
            velocity_score = min(1.0, abs(self.drawdown_velocity) * 10)
            accel_score = min(1.0, abs(self.drawdown_acceleration) * 20)
            time_score = min(1.0, self.time_in_drawdown / 30)  # 30 days = max
        
            return (velocity_score * 0.4 + accel_score * 0.4 + time_score * 0.2)
        except Exception as e:
            logger.error(f"Error in calculate_severity: {e}")
            raise


@dataclass
class TailExposure:
    """Tail exposure metrics"""
    left_tail_ratio: float = 0.0  # Ratio of extreme losses to normal
    var_95: float = 0.0  # Value at Risk 95%
    var_99: float = 0.0  # Value at Risk 99%
    cvar_95: float = 0.0  # Conditional VaR 95%
    tail_asymmetry: float = 0.0  # Difference between left and right tails
    is_asymmetric: bool = False
    
    def calculate_severity(self) -> float:
        """Calculate severity score (0-1)"""
        try:
            ratio_score = min(1.0, self.left_tail_ratio / 3)
            asymmetry_score = min(1.0, abs(self.tail_asymmetry) * 2)
            var_score = min(1.0, abs(self.var_99) / 0.05)  # 5% = max
        
            return (ratio_score * 0.4 + asymmetry_score * 0.3 + var_score * 0.3)
        except Exception as e:
            logger.error(f"Error in calculate_severity: {e}")
            raise


@dataclass
class LossClustering:
    """Loss clustering metrics"""
    cluster_count: int = 0
    average_cluster_size: float = 0.0
    max_cluster_size: int = 0
    clustering_coefficient: float = 0.0  # Autocorrelation of losses
    is_clustered: bool = False
    
    def calculate_severity(self) -> float:
        """Calculate severity score (0-1)"""
        try:
            coef_score = self.clustering_coefficient
            size_score = min(1.0, self.max_cluster_size / 10)
        
            return (coef_score * 0.6 + size_score * 0.4)
        except Exception as e:
            logger.error(f"Error in calculate_severity: {e}")
            raise


@dataclass
class RecoveryDegradation:
    """Recovery degradation metrics"""
    average_recovery_time: float = 0.0  # Days
    recovery_trend: float = 0.0  # Positive = getting slower
    failed_recoveries: int = 0
    recovery_efficiency: float = 1.0  # How much of drawdown is recovered
    is_degrading: bool = False
    
    def calculate_severity(self) -> float:
        """Calculate severity score (0-1)"""
        try:
            time_score = min(1.0, self.average_recovery_time / 60)  # 60 days = max
            trend_score = min(1.0, max(0, self.recovery_trend) * 5)
            efficiency_score = 1 - self.recovery_efficiency
        
            return (time_score * 0.3 + trend_score * 0.4 + efficiency_score * 0.3)
        except Exception as e:
            logger.error(f"Error in calculate_severity: {e}")
            raise


@dataclass
class LossResult:
    """Result from loss monitoring"""
    shape: LossShape
    damage_level: DamageLevel
    overall_severity: float  # 0-1
    exposure_multiplier: float  # 0-1
    drawdown: DrawdownAcceleration
    tail: TailExposure
    clustering: LossClustering
    recovery: RecoveryDegradation
    warnings: List[str]
    action_required: str
    post_mortem_required: bool
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'shape': self.shape.name,
            'damage_level': self.damage_level.name,
            'overall_severity': self.overall_severity,
            'exposure_multiplier': self.exposure_multiplier,
            'drawdown_severity': self.drawdown.calculate_severity(),
            'tail_severity': self.tail.calculate_severity(),
            'clustering_severity': self.clustering.calculate_severity(),
            'recovery_severity': self.recovery.calculate_severity(),
            'warnings': self.warnings,
            'action_required': self.action_required,
            'post_mortem_required': self.post_mortem_required,
            'timestamp': self.timestamp
        }


class DrawdownTracker:
    """Tracks drawdown and its derivatives"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._equity: Deque[float] = deque(maxlen=window_size)
            self._drawdown: Deque[float] = deque(maxlen=window_size)
            self._peak: float = 0.0
            self._drawdown_start: Optional[float] = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, equity: float) -> DrawdownAcceleration:
        """Update with new equity value"""
        try:
            self._equity.append(equity)
        
            result = DrawdownAcceleration()
        
            # Update peak
            if equity > self._peak:
                self._peak = equity
                self._drawdown_start = None
        
            # Calculate drawdown
            if self._peak > 0:
                result.current_drawdown = (self._peak - equity) / self._peak
        
            self._drawdown.append(result.current_drawdown)
        
            # Track drawdown start
            if result.current_drawdown > 0.01 and self._drawdown_start is None:
                self._drawdown_start = time.time()
        
            if self._drawdown_start:
                result.time_in_drawdown = (time.time() - self._drawdown_start) / 86400
        
            # Calculate velocity and acceleration
            if len(self._drawdown) >= 5:
                recent = list(self._drawdown)[-5:]
                result.drawdown_velocity = (recent[-1] - recent[0]) / 5
            
                if len(self._drawdown) >= 10:
                    older = list(self._drawdown)[-10:-5]
                    older_velocity = (older[-1] - older[0]) / 5
                    result.drawdown_acceleration = result.drawdown_velocity - older_velocity
        
            result.is_accelerating = result.drawdown_acceleration > 0.001
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class TailAnalyzer:
    """Analyzes tail exposure"""
    
    def __init__(self, window_size: int = 252):
        try:
            self.window_size = window_size
            self._returns: Deque[float] = deque(maxlen=window_size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, return_value: float) -> TailExposure:
        """Update with new return"""
        try:
            self._returns.append(return_value)
        
            result = TailExposure()
        
            if len(self._returns) < 30:
                return result
        
            returns = np.array(list(self._returns))
        
            # Calculate VaR
            result.var_95 = np.percentile(returns, 5)
            result.var_99 = np.percentile(returns, 1)
        
            # Calculate CVaR (Expected Shortfall)
            tail_returns = returns[returns <= result.var_95]
            if len(tail_returns) > 0:
                result.cvar_95 = np.mean(tail_returns)
        
            # Calculate tail ratio
            left_tail = returns[returns < np.percentile(returns, 10)]
            body = returns[(returns >= np.percentile(returns, 10)) & 
                           (returns <= np.percentile(returns, 90))]
        
            if len(body) > 0 and np.mean(np.abs(body)) > 0:
                result.left_tail_ratio = np.mean(np.abs(left_tail)) / np.mean(np.abs(body))
        
            # Calculate asymmetry
            right_tail = returns[returns > np.percentile(returns, 90)]
            if len(left_tail) > 0 and len(right_tail) > 0:
                result.tail_asymmetry = np.mean(np.abs(left_tail)) - np.mean(np.abs(right_tail))
        
            result.is_asymmetric = abs(result.tail_asymmetry) > 0.01
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class ClusteringAnalyzer:
    """Analyzes loss clustering"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._returns: Deque[float] = deque(maxlen=window_size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, return_value: float) -> LossClustering:
        """Update with new return"""
        try:
            self._returns.append(return_value)
        
            result = LossClustering()
        
            if len(self._returns) < 20:
                return result
        
            returns = np.array(list(self._returns))
            loss_indicator = (returns < 0).astype(int)
        
            # Calculate clustering coefficient (autocorrelation)
            if len(loss_indicator) > 1:
                result.clustering_coefficient = np.corrcoef(
                    loss_indicator[:-1], loss_indicator[1:]
                )[0, 1]
                result.clustering_coefficient = max(0, result.clustering_coefficient)
        
            # Count clusters
            clusters = []
            current_cluster = 0
            for is_loss in loss_indicator:
                if is_loss:
                    current_cluster += 1
                elif current_cluster > 0:
                    clusters.append(current_cluster)
                    current_cluster = 0
            if current_cluster > 0:
                clusters.append(current_cluster)
        
            if clusters:
                result.cluster_count = len(clusters)
                result.average_cluster_size = np.mean(clusters)
                result.max_cluster_size = max(clusters)
        
            result.is_clustered = result.clustering_coefficient > 0.3
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class RecoveryAnalyzer:
    """Analyzes recovery patterns"""
    
    def __init__(self):
        try:
            self._equity: Deque[float] = deque(maxlen=1000)
            self._peak: float = 0.0
            self._recovery_times: List[float] = []
            self._drawdown_start: Optional[float] = None
            self._drawdown_depth: float = 0.0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, equity: float) -> RecoveryDegradation:
        """Update with new equity"""
        try:
            self._equity.append(equity)
        
            result = RecoveryDegradation()
        
            # Track peak and recovery
            if equity >= self._peak:
                if self._drawdown_start is not None:
                    # Recovery completed
                    recovery_time = (time.time() - self._drawdown_start) / 86400
                    self._recovery_times.append(recovery_time)
                    self._drawdown_start = None
                self._peak = equity
            elif self._drawdown_start is None and equity < self._peak * 0.99:
                # New drawdown started
                self._drawdown_start = time.time()
                self._drawdown_depth = (self._peak - equity) / self._peak
        
            # Calculate metrics
            if self._recovery_times:
                result.average_recovery_time = np.mean(self._recovery_times)
            
                # Calculate trend (are recoveries getting slower?)
                if len(self._recovery_times) >= 3:
                    recent = self._recovery_times[-3:]
                    older = self._recovery_times[:-3] if len(self._recovery_times) > 3 else [recent[0]]
                    result.recovery_trend = np.mean(recent) - np.mean(older)
            
                # Count failed recoveries (took > 60 days)
                result.failed_recoveries = sum(1 for t in self._recovery_times if t > 60)
            
                # Recovery efficiency
                if len(self._equity) > 1:
                    max_equity = max(self._equity)
                    current_equity = self._equity[-1]
                    if max_equity > 0:
                        result.recovery_efficiency = current_equity / max_equity
        
            result.is_degrading = result.recovery_trend > 5  # 5 days slower
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class LossShapeMonitor:
    """
    Main Loss Shape Monitor
    
    RULES:
    1. Monitor loss SHAPE, not just magnitude
    2. Detect clustering, acceleration, asymmetry
    3. Throttle size when shape deteriorates
    4. Require post-mortem for severe damage
    """
    
    # Thresholds
    CLUSTERING_THRESHOLD = 0.4
    ACCELERATION_THRESHOLD = 0.002
    TAIL_RATIO_THRESHOLD = 2.0
    RECOVERY_TREND_THRESHOLD = 10  # Days
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.loss")
        
            # Analyzers
            self._drawdown = DrawdownTracker()
            self._tail = TailAnalyzer()
            self._clustering = ClusteringAnalyzer()
            self._recovery = RecoveryAnalyzer()
        
            # State
            self._last_result: Optional[LossResult] = None
            self._post_mortems_pending: List[str] = []
        
            self.logger.info("Loss Shape Monitor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(
        self,
        equity: float,
        return_value: float
    ) -> LossResult:
        """
        Update with new data and analyze loss shape.
        """
        # Update all analyzers
        try:
            drawdown = self._drawdown.update(equity)
            tail = self._tail.update(return_value)
            clustering = self._clustering.update(return_value)
            recovery = self._recovery.update(equity)
        
            # Calculate severities
            drawdown_severity = drawdown.calculate_severity()
            tail_severity = tail.calculate_severity()
            clustering_severity = clustering.calculate_severity()
            recovery_severity = recovery.calculate_severity()
        
            # Overall severity
            overall_severity = (
                drawdown_severity * 0.3 +
                tail_severity * 0.25 +
                clustering_severity * 0.25 +
                recovery_severity * 0.2
            )
        
            # Determine loss shape
            warnings = []
            shape_issues = []
        
            if clustering.is_clustered:
                warnings.append(f"Loss clustering detected: {clustering.clustering_coefficient:.2f}")
                shape_issues.append(LossShape.CLUSTERED)
        
            if drawdown.is_accelerating:
                warnings.append(f"Drawdown accelerating: {drawdown.drawdown_acceleration:.4f}")
                shape_issues.append(LossShape.ACCELERATING)
        
            if tail.is_asymmetric:
                warnings.append(f"Asymmetric tail exposure: {tail.tail_asymmetry:.4f}")
                shape_issues.append(LossShape.ASYMMETRIC)
        
            if recovery.is_degrading:
                warnings.append(f"Recovery degrading: +{recovery.recovery_trend:.1f} days")
                shape_issues.append(LossShape.DEGRADING)
        
            # Determine final shape
            if len(shape_issues) >= 2:
                shape = LossShape.CATASTROPHIC
            elif shape_issues:
                shape = shape_issues[0]
            else:
                shape = LossShape.NORMAL
        
            # Determine damage level
            if overall_severity >= 0.8:
                damage_level = DamageLevel.CRITICAL
            elif overall_severity >= 0.6:
                damage_level = DamageLevel.SEVERE
            elif overall_severity >= 0.4:
                damage_level = DamageLevel.MODERATE
            elif overall_severity >= 0.2:
                damage_level = DamageLevel.MINOR
            else:
                damage_level = DamageLevel.NONE
        
            # Calculate exposure multiplier
            exposure_multiplier = max(0.1, 1 - overall_severity)
        
            # Determine action
            action_required, post_mortem = self._determine_action(
                damage_level, shape, overall_severity
            )
        
            result = LossResult(
                shape=shape,
                damage_level=damage_level,
                overall_severity=overall_severity,
                exposure_multiplier=exposure_multiplier,
                drawdown=drawdown,
                tail=tail,
                clustering=clustering,
                recovery=recovery,
                warnings=warnings,
                action_required=action_required,
                post_mortem_required=post_mortem
            )
        
            self._last_result = result
        
            if warnings:
                self.logger.warning(
                    f"Loss shape: {shape.name} | Damage: {damage_level.name} | "
                    f"Severity: {overall_severity:.2f} | Exposure: {exposure_multiplier:.1%}"
                )
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _determine_action(
        self,
        damage: DamageLevel,
        shape: LossShape,
        severity: float
    ) -> Tuple[str, bool]:
        """Determine required action and post-mortem need"""
        try:
            if damage == DamageLevel.CRITICAL:
                return "SUSPEND STRATEGY. Immediate post-mortem required.", True
            elif damage == DamageLevel.SEVERE:
                return "THROTTLE SIZE to 20%. Post-mortem required.", True
            elif damage == DamageLevel.MODERATE:
                return "REDUCE SIZE to 50%. Monitor closely.", False
            elif damage == DamageLevel.MINOR:
                return "MONITOR. Consider reducing size.", False
            else:
                return "Normal operations.", False
        except Exception as e:
            logger.error(f"Error in _determine_action: {e}")
            raise
    
    def get_exposure_multiplier(self) -> float:
        """Get current exposure multiplier"""
        try:
            if self._last_result:
                return self._last_result.exposure_multiplier
            return 1.0
        except Exception as e:
            logger.error(f"Error in get_exposure_multiplier: {e}")
            raise
    
    def is_shape_healthy(self) -> bool:
        """Check if loss shape is healthy"""
        try:
            if self._last_result:
                return self._last_result.shape == LossShape.NORMAL
            return True
        except Exception as e:
            logger.error(f"Error in is_shape_healthy: {e}")
            raise
    
    def get_pending_post_mortems(self) -> List[str]:
        """Get list of pending post-mortems"""
        return self._post_mortems_pending.copy()

"""
Anomaly Detector - Multi-Dimensional Anomaly Detection
=======================================================

Implements comprehensive anomaly detection for markets:
1. Statistical Anomalies: Z-score, IQR, Grubbs test
2. Temporal Anomalies: Regime changes, trend breaks
3. Correlation Anomalies: Correlation breakdowns
4. Volume Anomalies: Unusual trading activity
5. Pattern Anomalies: Unexpected pattern formations

Based on the Foundation Agents paper (arXiv:2504.01990) curiosity systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import deque
import hashlib

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies"""
    STATISTICAL = "statistical"          # Statistical outliers
    TEMPORAL = "temporal"                # Time-based anomalies
    CORRELATION = "correlation"          # Correlation breakdowns
    VOLUME = "volume"                    # Volume anomalies
    PATTERN = "pattern"                  # Pattern anomalies
    REGIME = "regime"                    # Regime change
    VOLATILITY = "volatility"            # Volatility anomalies
    LIQUIDITY = "liquidity"              # Liquidity anomalies
    CROSS_ASSET = "cross_asset"          # Cross-asset anomalies
    MICROSTRUCTURE = "microstructure"    # Market microstructure anomalies


class AnomalySeverity(Enum):
    """Severity levels for anomalies"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Anomaly:
    """Detected anomaly"""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    
    # Description
    description: str
    asset: Optional[str] = None
    
    # Metrics
    score: float = 0.0  # Anomaly score (higher = more anomalous)
    z_score: Optional[float] = None
    probability: Optional[float] = None  # P(normal) - lower = more anomalous
    
    # Values
    observed_value: Optional[float] = None
    expected_value: Optional[float] = None
    deviation: Optional[float] = None
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    related_anomalies: List[str] = field(default_factory=list)
    
    # Timing
    detected_at: datetime = field(default_factory=datetime.utcnow)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Status
    acknowledged: bool = False
    investigated: bool = False
    resolution: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'anomaly_id': self.anomaly_id,
            'anomaly_type': self.anomaly_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'asset': self.asset,
            'score': self.score,
            'z_score': self.z_score,
            'probability': self.probability,
            'observed_value': self.observed_value,
            'expected_value': self.expected_value,
            'detected_at': self.detected_at.isoformat()
        }


class StatisticalAnomalyDetector:
    """Statistical anomaly detection methods"""
    
    def __init__(self, z_threshold: float = 3.0, iqr_multiplier: float = 1.5):
        self.z_threshold = z_threshold
        self.iqr_multiplier = iqr_multiplier
    
    def detect_zscore(
        self,
        values: np.ndarray,
        current_value: float
    ) -> Tuple[bool, float, float]:
        """Detect anomaly using z-score"""
        if len(values) < 10:
            return False, 0.0, 0.5
        
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return False, 0.0, 0.5
        
        z_score = (current_value - mean) / std
        is_anomaly = abs(z_score) > self.z_threshold
        
        # Probability of being normal (using normal distribution)
        from scipy import stats
        probability = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        return is_anomaly, z_score, probability
    
    def detect_iqr(
        self,
        values: np.ndarray,
        current_value: float
    ) -> Tuple[bool, float]:
        """Detect anomaly using IQR method"""
        if len(values) < 10:
            return False, 0.0
        
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - self.iqr_multiplier * iqr
        upper_bound = q3 + self.iqr_multiplier * iqr
        
        is_anomaly = current_value < lower_bound or current_value > upper_bound
        
        # Score based on distance from bounds
        if current_value < lower_bound:
            score = (lower_bound - current_value) / (iqr + 1e-10)
        elif current_value > upper_bound:
            score = (current_value - upper_bound) / (iqr + 1e-10)
        else:
            score = 0.0
        
        return is_anomaly, score
    
    def detect_mad(
        self,
        values: np.ndarray,
        current_value: float,
        threshold: float = 3.5
    ) -> Tuple[bool, float]:
        """Detect anomaly using Median Absolute Deviation"""
        if len(values) < 10:
            return False, 0.0
        
        median = np.median(values)
        mad = np.median(np.abs(values - median))
        
        if mad == 0:
            return False, 0.0
        
        modified_z = 0.6745 * (current_value - median) / mad
        is_anomaly = abs(modified_z) > threshold
        
        return is_anomaly, modified_z


class TemporalAnomalyDetector:
    """Temporal/time-series anomaly detection"""
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
    
    def detect_trend_break(
        self,
        values: np.ndarray,
        current_value: float
    ) -> Tuple[bool, float, str]:
        """Detect trend breaks"""
        if len(values) < self.window_size:
            return False, 0.0, ""
        
        recent = values[-self.window_size:]
        
        # Calculate trend
        x = np.arange(len(recent))
        slope, intercept = np.polyfit(x, recent, 1)
        
        # Predict next value
        predicted = slope * len(recent) + intercept
        
        # Calculate residuals
        residuals = recent - (slope * x + intercept)
        residual_std = np.std(residuals)
        
        if residual_std == 0:
            return False, 0.0, ""
        
        # Check if current value breaks trend
        deviation = (current_value - predicted) / residual_std
        is_anomaly = abs(deviation) > 2.5
        
        direction = "above" if deviation > 0 else "below"
        
        return is_anomaly, deviation, direction
    
    def detect_regime_change(
        self,
        values: np.ndarray,
        lookback: int = 50
    ) -> Tuple[bool, float, Dict]:
        """Detect regime changes using variance ratio"""
        if len(values) < lookback * 2:
            return False, 0.0, {}
        
        recent = values[-lookback:]
        previous = values[-lookback*2:-lookback]
        
        # Compare statistics
        recent_mean = np.mean(recent)
        previous_mean = np.mean(previous)
        recent_std = np.std(recent)
        previous_std = np.std(previous)
        
        # Mean shift
        pooled_std = np.sqrt((recent_std**2 + previous_std**2) / 2)
        if pooled_std > 0:
            mean_shift = abs(recent_mean - previous_mean) / pooled_std
        else:
            mean_shift = 0
        
        # Variance ratio
        if previous_std > 0:
            variance_ratio = recent_std / previous_std
        else:
            variance_ratio = 1.0
        
        # Detect regime change
        is_regime_change = mean_shift > 1.5 or variance_ratio > 2.0 or variance_ratio < 0.5
        
        score = max(mean_shift / 2, abs(np.log(variance_ratio + 0.01)))
        
        details = {
            'mean_shift': mean_shift,
            'variance_ratio': variance_ratio,
            'recent_mean': recent_mean,
            'previous_mean': previous_mean
        }
        
        return is_regime_change, score, details


class CorrelationAnomalyDetector:
    """Correlation breakdown detection"""
    
    def __init__(self, correlation_threshold: float = 0.3):
        self.correlation_threshold = correlation_threshold
        self.historical_correlations: Dict[Tuple[str, str], deque] = {}
    
    def update_correlation(
        self,
        asset1: str,
        asset2: str,
        correlation: float
    ):
        """Update historical correlation"""
        key = tuple(sorted([asset1, asset2]))
        if key not in self.historical_correlations:
            self.historical_correlations[key] = deque(maxlen=100)
        self.historical_correlations[key].append(correlation)
    
    def detect_correlation_break(
        self,
        asset1: str,
        asset2: str,
        current_correlation: float
    ) -> Tuple[bool, float, Dict]:
        """Detect correlation breakdown"""
        key = tuple(sorted([asset1, asset2]))
        
        if key not in self.historical_correlations:
            return False, 0.0, {}
        
        history = list(self.historical_correlations[key])
        if len(history) < 20:
            return False, 0.0, {}
        
        historical_mean = np.mean(history)
        historical_std = np.std(history)
        
        if historical_std == 0:
            return False, 0.0, {}
        
        # Z-score of current correlation
        z_score = (current_correlation - historical_mean) / historical_std
        
        # Detect significant change
        is_anomaly = abs(z_score) > 2.0
        
        # Also check for sign change
        sign_change = (current_correlation * historical_mean) < 0
        
        details = {
            'historical_mean': historical_mean,
            'current': current_correlation,
            'z_score': z_score,
            'sign_change': sign_change
        }
        
        return is_anomaly or sign_change, abs(z_score), details


class VolumeAnomalyDetector:
    """Volume anomaly detection"""
    
    def __init__(self, volume_threshold: float = 3.0):
        self.volume_threshold = volume_threshold
    
    def detect_volume_spike(
        self,
        volumes: np.ndarray,
        current_volume: float
    ) -> Tuple[bool, float, str]:
        """Detect unusual volume"""
        if len(volumes) < 20:
            return False, 0.0, ""
        
        mean_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        
        if std_volume == 0 or mean_volume == 0:
            return False, 0.0, ""
        
        z_score = (current_volume - mean_volume) / std_volume
        volume_ratio = current_volume / mean_volume
        
        is_anomaly = abs(z_score) > self.volume_threshold
        
        if z_score > 0:
            description = f"Volume spike: {volume_ratio:.1f}x average"
        else:
            description = f"Volume drought: {volume_ratio:.1f}x average"
        
        return is_anomaly, z_score, description


class AnomalyDetector:
    """
    Anomaly Detector
    
    Central system for detecting all types of market anomalies.
    Feeds into the curiosity engine for hypothesis generation.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Sub-detectors
        self.statistical = StatisticalAnomalyDetector(
            z_threshold=self.config.get('z_threshold', 3.0)
        )
        self.temporal = TemporalAnomalyDetector(
            window_size=self.config.get('window_size', 20)
        )
        self.correlation = CorrelationAnomalyDetector()
        self.volume = VolumeAnomalyDetector()
        
        # Data storage
        self.price_history: Dict[str, deque] = {}
        self.volume_history: Dict[str, deque] = {}
        self.return_history: Dict[str, deque] = {}
        
        # Detected anomalies
        self.anomalies: List[Anomaly] = []
        self.anomaly_history: deque = deque(maxlen=10000)
        
        # Statistics
        self.stats = {
            'total_detected': 0,
            'by_type': {at.value: 0 for at in AnomalyType},
            'by_severity': {s.value: 0 for s in AnomalySeverity}
        }
        
        logger.info("Anomaly Detector initialized")
    
    def update_data(
        self,
        asset: str,
        price: float,
        volume: Optional[float] = None,
        return_value: Optional[float] = None
    ):
        """Update historical data for an asset"""
        max_history = self.config.get('max_history', 1000)
        
        if asset not in self.price_history:
            self.price_history[asset] = deque(maxlen=max_history)
            self.volume_history[asset] = deque(maxlen=max_history)
            self.return_history[asset] = deque(maxlen=max_history)
        
        self.price_history[asset].append(price)
        
        if volume is not None:
            self.volume_history[asset].append(volume)
        
        if return_value is not None:
            self.return_history[asset].append(return_value)
    
    def detect_all(
        self,
        asset: str,
        current_price: float,
        current_volume: Optional[float] = None,
        current_return: Optional[float] = None,
        correlations: Optional[Dict[str, float]] = None
    ) -> List[Anomaly]:
        """Run all anomaly detection methods"""
        detected = []
        
        # Update data
        self.update_data(asset, current_price, current_volume, current_return)
        
        # Get historical data
        prices = np.array(list(self.price_history.get(asset, [])))
        volumes = np.array(list(self.volume_history.get(asset, [])))
        returns = np.array(list(self.return_history.get(asset, [])))
        
        # 1. Statistical anomalies on returns
        if len(returns) > 20 and current_return is not None:
            is_anomaly, z_score, prob = self.statistical.detect_zscore(returns[:-1], current_return)
            if is_anomaly:
                anomaly = self._create_anomaly(
                    anomaly_type=AnomalyType.STATISTICAL,
                    description=f"Statistical outlier in {asset} returns",
                    asset=asset,
                    score=abs(z_score),
                    z_score=z_score,
                    probability=prob,
                    observed_value=current_return,
                    expected_value=np.mean(returns[:-1])
                )
                detected.append(anomaly)
        
        # 2. Trend break detection
        if len(prices) > 30:
            is_anomaly, deviation, direction = self.temporal.detect_trend_break(
                prices[:-1], current_price
            )
            if is_anomaly:
                anomaly = self._create_anomaly(
                    anomaly_type=AnomalyType.TEMPORAL,
                    description=f"Trend break in {asset}: price {direction} trend",
                    asset=asset,
                    score=abs(deviation),
                    z_score=deviation,
                    observed_value=current_price,
                    context={'direction': direction}
                )
                detected.append(anomaly)
        
        # 3. Regime change detection
        if len(returns) > 100:
            is_regime_change, score, details = self.temporal.detect_regime_change(returns)
            if is_regime_change:
                anomaly = self._create_anomaly(
                    anomaly_type=AnomalyType.REGIME,
                    description=f"Regime change detected in {asset}",
                    asset=asset,
                    score=score,
                    context=details
                )
                detected.append(anomaly)
        
        # 4. Volume anomalies
        if len(volumes) > 20 and current_volume is not None:
            is_anomaly, z_score, desc = self.volume.detect_volume_spike(
                volumes[:-1], current_volume
            )
            if is_anomaly:
                anomaly = self._create_anomaly(
                    anomaly_type=AnomalyType.VOLUME,
                    description=f"{desc} for {asset}",
                    asset=asset,
                    score=abs(z_score),
                    z_score=z_score,
                    observed_value=current_volume,
                    expected_value=np.mean(volumes[:-1])
                )
                detected.append(anomaly)
        
        # 5. Volatility anomalies
        if len(returns) > 30:
            recent_vol = np.std(returns[-20:])
            historical_vol = np.std(returns[:-20])
            
            if historical_vol > 0:
                vol_ratio = recent_vol / historical_vol
                if vol_ratio > 2.0 or vol_ratio < 0.5:
                    anomaly = self._create_anomaly(
                        anomaly_type=AnomalyType.VOLATILITY,
                        description=f"Volatility anomaly in {asset}: {vol_ratio:.1f}x normal",
                        asset=asset,
                        score=abs(np.log(vol_ratio)),
                        observed_value=recent_vol,
                        expected_value=historical_vol,
                        context={'volatility_ratio': vol_ratio}
                    )
                    detected.append(anomaly)
        
        # 6. Correlation anomalies
        if correlations:
            for other_asset, corr in correlations.items():
                self.correlation.update_correlation(asset, other_asset, corr)
                is_anomaly, score, details = self.correlation.detect_correlation_break(
                    asset, other_asset, corr
                )
                if is_anomaly:
                    anomaly = self._create_anomaly(
                        anomaly_type=AnomalyType.CORRELATION,
                        description=f"Correlation breakdown between {asset} and {other_asset}",
                        asset=asset,
                        score=score,
                        observed_value=corr,
                        expected_value=details.get('historical_mean'),
                        context=details
                    )
                    detected.append(anomaly)
        
        # Store detected anomalies
        for anomaly in detected:
            self.anomalies.append(anomaly)
            self.anomaly_history.append(anomaly)
            self.stats['total_detected'] += 1
            self.stats['by_type'][anomaly.anomaly_type.value] += 1
            self.stats['by_severity'][anomaly.severity.value] += 1
        
        return detected
    
    def _create_anomaly(
        self,
        anomaly_type: AnomalyType,
        description: str,
        asset: Optional[str] = None,
        score: float = 0.0,
        z_score: Optional[float] = None,
        probability: Optional[float] = None,
        observed_value: Optional[float] = None,
        expected_value: Optional[float] = None,
        context: Optional[Dict] = None
    ) -> Anomaly:
        """Create an anomaly object"""
        # Determine severity based on score
        if score > 5.0:
            severity = AnomalySeverity.CRITICAL
        elif score > 3.5:
            severity = AnomalySeverity.HIGH
        elif score > 2.5:
            severity = AnomalySeverity.MEDIUM
        else:
            severity = AnomalySeverity.LOW
        
        anomaly_id = f"anom_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(description.encode()).hexdigest()[:8]}"
        
        deviation = None
        if observed_value is not None and expected_value is not None:
            deviation = observed_value - expected_value
        
        return Anomaly(
            anomaly_id=anomaly_id,
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            asset=asset,
            score=score,
            z_score=z_score,
            probability=probability,
            observed_value=observed_value,
            expected_value=expected_value,
            deviation=deviation,
            context=context or {}
        )
    
    def get_recent_anomalies(
        self,
        limit: int = 10,
        anomaly_type: Optional[AnomalyType] = None,
        min_severity: Optional[AnomalySeverity] = None,
        asset: Optional[str] = None
    ) -> List[Anomaly]:
        """Get recent anomalies with optional filtering"""
        candidates = list(self.anomaly_history)
        
        if anomaly_type:
            candidates = [a for a in candidates if a.anomaly_type == anomaly_type]
        
        if min_severity:
            candidates = [a for a in candidates if a.severity.value >= min_severity.value]
        
        if asset:
            candidates = [a for a in candidates if a.asset == asset]
        
        # Sort by detection time (most recent first)
        candidates.sort(key=lambda a: a.detected_at, reverse=True)
        
        return candidates[:limit]
    
    def get_anomaly_summary(self) -> Dict[str, Any]:
        """Get summary of detected anomalies"""
        recent = list(self.anomaly_history)[-100:]
        
        return {
            'total_detected': self.stats['total_detected'],
            'recent_count': len(recent),
            'by_type': self.stats['by_type'],
            'by_severity': self.stats['by_severity'],
            'unacknowledged': len([a for a in self.anomalies if not a.acknowledged]),
            'uninvestigated': len([a for a in self.anomalies if not a.investigated]),
            'assets_with_anomalies': list(set(a.asset for a in recent if a.asset))
        }
    
    def acknowledge_anomaly(self, anomaly_id: str):
        """Acknowledge an anomaly"""
        for anomaly in self.anomalies:
            if anomaly.anomaly_id == anomaly_id:
                anomaly.acknowledged = True
                return True
        return False
    
    def mark_investigated(self, anomaly_id: str, resolution: Optional[str] = None):
        """Mark an anomaly as investigated"""
        for anomaly in self.anomalies:
            if anomaly.anomaly_id == anomaly_id:
                anomaly.investigated = True
                anomaly.resolution = resolution
                return True
        return False
    
    def clear_old_anomalies(self, max_age_hours: int = 24):
        """Clear anomalies older than specified age"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        self.anomalies = [a for a in self.anomalies if a.detected_at > cutoff]

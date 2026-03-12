"""
Correlation Breakdown Detector
==============================

Detects when historical correlations between assets break down.
Critical for portfolio risk management and pairs trading strategies.

Features:
- Rolling correlation monitoring
- Breakdown detection with multiple methods
- Regime-aware correlation tracking
- Alert generation on significant changes
- Historical correlation analysis
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import deque
import threading
import logging
import math
import statistics

logger = logging.getLogger(__name__)


class BreakdownType(Enum):
    """Types of correlation breakdown."""
    DECORRELATION = auto()      # Correlation dropped significantly
    CORRELATION_FLIP = auto()   # Correlation changed sign
    VOLATILITY_SPIKE = auto()   # Correlation unstable due to volatility
    REGIME_CHANGE = auto()      # Correlation changed due to regime shift
    STRUCTURAL_BREAK = auto()   # Permanent structural change detected
    TEMPORARY_DIVERGENCE = auto()  # Short-term divergence


class BreakdownSeverity(Enum):
    """Severity of correlation breakdown."""
    CRITICAL = auto()   # Immediate action required
    HIGH = auto()       # Significant risk
    MEDIUM = auto()     # Monitor closely
    LOW = auto()        # Minor deviation
    INFO = auto()       # Informational only


@dataclass
class PairCorrelation:
    """Correlation data for an asset pair."""
    asset1: str
    asset2: str
    current_correlation: float
    rolling_correlation: float
    historical_correlation: float
    correlation_std: float
    z_score: float
    last_updated: datetime
    sample_count: int
    is_stable: bool
    
    @property
    def pair_id(self) -> str:
        return f"{min(self.asset1, self.asset2)}:{max(self.asset1, self.asset2)}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset1": self.asset1,
            "asset2": self.asset2,
            "current_correlation": self.current_correlation,
            "rolling_correlation": self.rolling_correlation,
            "historical_correlation": self.historical_correlation,
            "correlation_std": self.correlation_std,
            "z_score": self.z_score,
            "last_updated": self.last_updated.isoformat(),
            "sample_count": self.sample_count,
            "is_stable": self.is_stable,
        }


@dataclass
class CorrelationAlert:
    """Alert for correlation breakdown."""
    alert_id: str
    pair_id: str
    asset1: str
    asset2: str
    breakdown_type: BreakdownType
    severity: BreakdownSeverity
    current_correlation: float
    expected_correlation: float
    deviation: float
    z_score: float
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "pair_id": self.pair_id,
            "asset1": self.asset1,
            "asset2": self.asset2,
            "breakdown_type": self.breakdown_type.name,
            "severity": self.severity.name,
            "current_correlation": self.current_correlation,
            "expected_correlation": self.expected_correlation,
            "deviation": self.deviation,
            "z_score": self.z_score,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
        }


@dataclass
class BreakdownConfig:
    """Configuration for correlation breakdown detection."""
    # Rolling windows
    short_window: int = 20       # Short-term correlation window
    long_window: int = 60        # Long-term correlation window
    historical_window: int = 252  # Historical baseline window
    
    # Thresholds
    z_score_threshold: float = 2.0      # Z-score for breakdown detection
    critical_z_score: float = 3.0       # Z-score for critical alert
    min_correlation_change: float = 0.2  # Minimum change to trigger alert
    flip_threshold: float = 0.1         # Threshold for correlation flip
    
    # Stability
    stability_window: int = 10          # Window for stability check
    stability_threshold: float = 0.1    # Max std for stable correlation
    
    # Monitoring
    update_frequency_seconds: int = 60
    max_pairs: int = 1000
    min_samples: int = 30


class CorrelationCalculator:
    """Calculates rolling correlations between asset pairs."""
    
    def __init__(self, window: int = 60):
        self.window = window
        self._returns: Dict[str, deque] = {}
        self._lock = threading.Lock()
    
    def add_return(self, asset: str, return_value: float, timestamp: datetime) -> None:
        """Add a return observation."""
        with self._lock:
            if asset not in self._returns:
                self._returns[asset] = deque(maxlen=self.window * 2)
            self._returns[asset].append((timestamp, return_value))
    
    def calculate_correlation(self, asset1: str, asset2: str) -> Optional[float]:
        """Calculate correlation between two assets."""
        with self._lock:
            if asset1 not in self._returns or asset2 not in self._returns:
                return None
            
            returns1 = [r[1] for r in list(self._returns[asset1])[-self.window:]]
            returns2 = [r[1] for r in list(self._returns[asset2])[-self.window:]]
            
            # Align by taking minimum length
            min_len = min(len(returns1), len(returns2))
            if min_len < 10:
                return None
            
            returns1 = returns1[-min_len:]
            returns2 = returns2[-min_len:]
            
            return self._pearson_correlation(returns1, returns2)
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = len(x)
        if n == 0:
            return 0.0
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        
        std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
        
        if std_x == 0 or std_y == 0:
            return 0.0
        
        return numerator / (std_x * std_y)
    
    def get_sample_count(self, asset: str) -> int:
        """Get number of samples for an asset."""
        with self._lock:
            if asset in self._returns:
                return len(self._returns[asset])
            return 0


class CorrelationBreakdownDetector:
    """
    Detects correlation breakdowns between asset pairs.
    
    Monitors rolling correlations and alerts when significant
    deviations from historical patterns are detected.
    """
    
    def __init__(self, config: Optional[BreakdownConfig] = None):
        self.config = config or BreakdownConfig()
        
        # Calculators for different windows
        self._short_calc = CorrelationCalculator(self.config.short_window)
        self._long_calc = CorrelationCalculator(self.config.long_window)
        self._historical_calc = CorrelationCalculator(self.config.historical_window)
        
        # Pair tracking
        self._monitored_pairs: Set[str] = set()
        self._pair_history: Dict[str, deque] = {}
        self._pair_baselines: Dict[str, Dict[str, float]] = {}
        
        # Alerts
        self._active_alerts: Dict[str, CorrelationAlert] = {}
        self._alert_history: deque = deque(maxlen=10000)
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Statistics
        self._breakdown_counts: Dict[BreakdownType, int] = {t: 0 for t in BreakdownType}
        
        logger.info("CorrelationBreakdownDetector initialized")
    
    def add_pair(self, asset1: str, asset2: str, expected_correlation: Optional[float] = None) -> str:
        """Add a pair to monitor."""
        pair_id = self._make_pair_id(asset1, asset2)
        
        with self._lock:
            if len(self._monitored_pairs) >= self.config.max_pairs:
                raise ValueError(f"Maximum pairs ({self.config.max_pairs}) reached")
            
            self._monitored_pairs.add(pair_id)
            self._pair_history[pair_id] = deque(maxlen=1000)
            
            if expected_correlation is not None:
                self._pair_baselines[pair_id] = {
                    "expected": expected_correlation,
                    "std": 0.1,  # Default std
                }
        
        logger.info(f"Added pair for monitoring: {pair_id}")
        return pair_id
    
    def remove_pair(self, asset1: str, asset2: str) -> bool:
        """Remove a pair from monitoring."""
        pair_id = self._make_pair_id(asset1, asset2)
        
        with self._lock:
            if pair_id in self._monitored_pairs:
                self._monitored_pairs.discard(pair_id)
                if pair_id in self._pair_history:
                    del self._pair_history[pair_id]
                if pair_id in self._pair_baselines:
                    del self._pair_baselines[pair_id]
                return True
        return False
    
    def update(self, asset: str, return_value: float, timestamp: Optional[datetime] = None) -> List[CorrelationAlert]:
        """
        Update with new return data and check for breakdowns.
        
        Returns list of new alerts generated.
        """
        timestamp = timestamp or datetime.utcnow()
        
        # Update all calculators
        self._short_calc.add_return(asset, return_value, timestamp)
        self._long_calc.add_return(asset, return_value, timestamp)
        self._historical_calc.add_return(asset, return_value, timestamp)
        
        # Check all pairs involving this asset
        new_alerts = []
        
        with self._lock:
            for pair_id in self._monitored_pairs:
                asset1, asset2 = pair_id.split(":")
                if asset not in (asset1, asset2):
                    continue
                
                # Calculate correlations
                pair_corr = self._calculate_pair_correlation(asset1, asset2)
                if pair_corr is None:
                    continue
                
                # Store in history
                self._pair_history[pair_id].append({
                    "timestamp": timestamp,
                    "correlation": pair_corr.current_correlation,
                })
                
                # Check for breakdown
                alert = self._check_breakdown(pair_corr)
                if alert:
                    self._active_alerts[alert.alert_id] = alert
                    self._alert_history.append(alert)
                    self._breakdown_counts[alert.breakdown_type] += 1
                    new_alerts.append(alert)
        
        return new_alerts
    
    def _calculate_pair_correlation(self, asset1: str, asset2: str) -> Optional[PairCorrelation]:
        """Calculate correlation metrics for a pair."""
        short_corr = self._short_calc.calculate_correlation(asset1, asset2)
        long_corr = self._long_calc.calculate_correlation(asset1, asset2)
        hist_corr = self._historical_calc.calculate_correlation(asset1, asset2)
        
        if short_corr is None or long_corr is None:
            return None
        
        pair_id = self._make_pair_id(asset1, asset2)
        
        # Get baseline or use historical
        if pair_id in self._pair_baselines:
            baseline = self._pair_baselines[pair_id]
            expected = baseline["expected"]
            std = baseline["std"]
        else:
            expected = hist_corr if hist_corr is not None else long_corr
            std = 0.1  # Default
        
        # Calculate z-score
        if std > 0:
            z_score = (short_corr - expected) / std
        else:
            z_score = 0.0
        
        # Check stability
        history = self._pair_history.get(pair_id, deque())
        recent = [h["correlation"] for h in list(history)[-self.config.stability_window:]]
        is_stable = len(recent) >= 5 and statistics.stdev(recent) < self.config.stability_threshold if len(recent) > 1 else True
        
        return PairCorrelation(
            asset1=asset1,
            asset2=asset2,
            current_correlation=short_corr,
            rolling_correlation=long_corr,
            historical_correlation=hist_corr if hist_corr is not None else long_corr,
            correlation_std=std,
            z_score=z_score,
            last_updated=datetime.utcnow(),
            sample_count=min(
                self._short_calc.get_sample_count(asset1),
                self._short_calc.get_sample_count(asset2)
            ),
            is_stable=is_stable,
        )
    
    def _check_breakdown(self, pair_corr: PairCorrelation) -> Optional[CorrelationAlert]:
        """Check if correlation has broken down."""
        pair_id = pair_corr.pair_id
        
        # Skip if not enough samples
        if pair_corr.sample_count < self.config.min_samples:
            return None
        
        # Check for existing unresolved alert
        for alert in self._active_alerts.values():
            if alert.pair_id == pair_id and not alert.resolved:
                return None  # Already alerted
        
        deviation = abs(pair_corr.current_correlation - pair_corr.historical_correlation)
        z_score = abs(pair_corr.z_score)
        
        # Determine breakdown type and severity
        breakdown_type = None
        severity = None
        message = ""
        
        # Check for correlation flip
        if (pair_corr.current_correlation * pair_corr.historical_correlation < 0 and
            abs(pair_corr.current_correlation) > self.config.flip_threshold and
            abs(pair_corr.historical_correlation) > self.config.flip_threshold):
            breakdown_type = BreakdownType.CORRELATION_FLIP
            severity = BreakdownSeverity.CRITICAL
            message = f"Correlation flipped from {pair_corr.historical_correlation:.2f} to {pair_corr.current_correlation:.2f}"
        
        # Check for significant decorrelation
        elif z_score >= self.config.critical_z_score:
            breakdown_type = BreakdownType.DECORRELATION
            severity = BreakdownSeverity.CRITICAL
            message = f"Critical decorrelation: z-score = {z_score:.2f}"
        
        elif z_score >= self.config.z_score_threshold and deviation >= self.config.min_correlation_change:
            breakdown_type = BreakdownType.DECORRELATION
            severity = BreakdownSeverity.HIGH
            message = f"Significant decorrelation: {pair_corr.historical_correlation:.2f} -> {pair_corr.current_correlation:.2f}"
        
        # Check for instability
        elif not pair_corr.is_stable and z_score >= self.config.z_score_threshold * 0.7:
            breakdown_type = BreakdownType.VOLATILITY_SPIKE
            severity = BreakdownSeverity.MEDIUM
            message = f"Correlation unstable with high volatility"
        
        # Check for temporary divergence
        elif deviation >= self.config.min_correlation_change * 0.5:
            breakdown_type = BreakdownType.TEMPORARY_DIVERGENCE
            severity = BreakdownSeverity.LOW
            message = f"Temporary divergence detected"
        
        if breakdown_type is None:
            return None
        
        # Create alert
        import hashlib
        alert_id = hashlib.sha256(
            f"{pair_id}:{breakdown_type.name}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        alert = CorrelationAlert(
            alert_id=alert_id,
            pair_id=pair_id,
            asset1=pair_corr.asset1,
            asset2=pair_corr.asset2,
            breakdown_type=breakdown_type,
            severity=severity,
            current_correlation=pair_corr.current_correlation,
            expected_correlation=pair_corr.historical_correlation,
            deviation=deviation,
            z_score=pair_corr.z_score,
            message=message,
        )
        
        logger.warning(f"Correlation breakdown: {pair_id} - {message}")
        return alert
    
    def get_pair_correlation(self, asset1: str, asset2: str) -> Optional[PairCorrelation]:
        """Get current correlation data for a pair."""
        pair_id = self._make_pair_id(asset1, asset2)
        
        with self._lock:
            if pair_id not in self._monitored_pairs:
                return None
            
            return self._calculate_pair_correlation(asset1, asset2)
    
    def get_all_correlations(self) -> List[PairCorrelation]:
        """Get correlations for all monitored pairs."""
        correlations = []
        
        with self._lock:
            for pair_id in self._monitored_pairs:
                asset1, asset2 = pair_id.split(":")
                corr = self._calculate_pair_correlation(asset1, asset2)
                if corr:
                    correlations.append(corr)
        
        return correlations
    
    def get_active_alerts(self, severity: Optional[BreakdownSeverity] = None) -> List[CorrelationAlert]:
        """Get active (unresolved) alerts."""
        with self._lock:
            alerts = [a for a in self._active_alerts.values() if not a.resolved]
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        with self._lock:
            if alert_id in self._active_alerts:
                self._active_alerts[alert_id].acknowledged = True
                return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        with self._lock:
            if alert_id in self._active_alerts:
                self._active_alerts[alert_id].resolved = True
                return True
        return False
    
    def set_baseline(self, asset1: str, asset2: str, expected_correlation: float, std: float = 0.1) -> None:
        """Set baseline correlation for a pair."""
        pair_id = self._make_pair_id(asset1, asset2)
        
        with self._lock:
            self._pair_baselines[pair_id] = {
                "expected": expected_correlation,
                "std": std,
            }
    
    def get_correlation_matrix(self, assets: List[str]) -> Dict[str, Dict[str, float]]:
        """Get correlation matrix for a list of assets."""
        matrix: Dict[str, Dict[str, float]] = {}
        
        for asset1 in assets:
            matrix[asset1] = {}
            for asset2 in assets:
                if asset1 == asset2:
                    matrix[asset1][asset2] = 1.0
                else:
                    corr = self._short_calc.calculate_correlation(asset1, asset2)
                    matrix[asset1][asset2] = corr if corr is not None else 0.0
        
        return matrix
    
    def get_breakdown_summary(self) -> Dict[str, Any]:
        """Get summary of correlation breakdowns."""
        with self._lock:
            active_alerts = [a for a in self._active_alerts.values() if not a.resolved]
            
            return {
                "monitored_pairs": len(self._monitored_pairs),
                "active_alerts": len(active_alerts),
                "breakdown_counts": {t.name: c for t, c in self._breakdown_counts.items()},
                "alerts_by_severity": {
                    s.name: len([a for a in active_alerts if a.severity == s])
                    for s in BreakdownSeverity
                },
                "most_unstable_pairs": self._get_most_unstable_pairs(5),
            }
    
    def _get_most_unstable_pairs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get pairs with highest correlation instability."""
        unstable = []
        
        for pair_id in self._monitored_pairs:
            asset1, asset2 = pair_id.split(":")
            corr = self._calculate_pair_correlation(asset1, asset2)
            if corr:
                unstable.append({
                    "pair_id": pair_id,
                    "z_score": abs(corr.z_score),
                    "current": corr.current_correlation,
                    "historical": corr.historical_correlation,
                    "is_stable": corr.is_stable,
                })
        
        return sorted(unstable, key=lambda x: x["z_score"], reverse=True)[:limit]
    
    def get_pair_history(self, asset1: str, asset2: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get correlation history for a pair."""
        pair_id = self._make_pair_id(asset1, asset2)
        
        with self._lock:
            if pair_id in self._pair_history:
                history = list(self._pair_history[pair_id])[-limit:]
                return [
                    {"timestamp": h["timestamp"].isoformat(), "correlation": h["correlation"]}
                    for h in history
                ]
        return []
    
    def _make_pair_id(self, asset1: str, asset2: str) -> str:
        """Create consistent pair ID."""
        return f"{min(asset1, asset2)}:{max(asset1, asset2)}"

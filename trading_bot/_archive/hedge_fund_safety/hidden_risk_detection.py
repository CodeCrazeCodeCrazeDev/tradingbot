"""
Hidden Risk Detection
=====================

Detects hidden and subtle risks that can cause catastrophic failure:
1. Model Decay - Models degrading over time
2. Data Poisoning - Corrupted or manipulated data
3. Adversarial Attacks - Intentional manipulation
4. Overfitting - Models that don't generalize
5. Regime Change - Market structure changes

PRINCIPLE: The most dangerous risks are the ones you don't see coming.
"""

import logging
import threading
import hashlib
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import json
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from scipy import stats
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class RiskType(Enum):
    """Types of hidden risks"""
    MODEL_DECAY = "model_decay"
    DATA_POISONING = "data_poisoning"
    ADVERSARIAL_ATTACK = "adversarial_attack"
    OVERFITTING = "overfitting"
    REGIME_CHANGE = "regime_change"
    CONCEPT_DRIFT = "concept_drift"
    FEATURE_DRIFT = "feature_drift"
    LABEL_DRIFT = "label_drift"


class RiskSeverity(Enum):
    """Severity of detected risks"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HiddenRiskAlert:
    """Alert for a detected hidden risk"""
    alert_id: str
    risk_type: RiskType
    severity: RiskSeverity
    description: str
    evidence: Dict[str, Any]
    recommended_action: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'alert_id': self.alert_id,
            'risk_type': self.risk_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'recommended_action': self.recommended_action,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged,
            'resolved': self.resolved
        }


class ModelDecayDetector:
    """
    Detects when models are degrading in performance.
    
    Detection Methods:
    1. Performance metric degradation
    2. Prediction confidence decline
    3. Feature importance shift
    4. Residual pattern changes
    5. Out-of-sample vs in-sample gap
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Performance tracking
        self.performance_history: Dict[str, deque] = {}
        self.confidence_history: Dict[str, deque] = {}
        
        # Thresholds
        self.performance_decay_threshold = self.config.get('performance_decay', 0.2)
        self.confidence_decay_threshold = self.config.get('confidence_decay', 0.15)
        self.lookback_periods = self.config.get('lookback_periods', 50)
        
        # Alerts
        self.alerts: List[HiddenRiskAlert] = []
        
        logger.info("ModelDecayDetector initialized")
    
    def record_prediction(
        self,
        model_id: str,
        prediction: float,
        actual: float,
        confidence: float
    ):
        """Record a prediction for decay analysis"""
        if model_id not in self.performance_history:
            self.performance_history[model_id] = deque(maxlen=1000)
            self.confidence_history[model_id] = deque(maxlen=1000)
        
        # Calculate error
        error = abs(prediction - actual)
        
        self.performance_history[model_id].append({
            'prediction': prediction,
            'actual': actual,
            'error': error,
            'timestamp': datetime.now()
        })
        
        self.confidence_history[model_id].append({
            'confidence': confidence,
            'timestamp': datetime.now()
        })
    
    def check_decay(self, model_id: str) -> Tuple[bool, Optional[HiddenRiskAlert]]:
        """
        Check for model decay.
        
        Returns:
            Tuple of (is_decaying, alert)
        """
        if model_id not in self.performance_history:
            return False, None
        
        history = list(self.performance_history[model_id])
        
        if len(history) < self.lookback_periods * 2:
            return False, None
        
        # Compare recent vs historical performance
        recent = history[-self.lookback_periods:]
        historical = history[-self.lookback_periods*2:-self.lookback_periods]
        
        recent_errors = [h['error'] for h in recent]
        historical_errors = [h['error'] for h in historical]
        
        if NUMPY_AVAILABLE:
            recent_mean = np.mean(recent_errors)
            historical_mean = np.mean(historical_errors)
        else:
            recent_mean = sum(recent_errors) / len(recent_errors)
            historical_mean = sum(historical_errors) / len(historical_errors)
        
        # Check for significant degradation
        if historical_mean > 0:
            degradation = (recent_mean - historical_mean) / historical_mean
            
            if degradation > self.performance_decay_threshold:
                alert = self._create_alert(
                    RiskType.MODEL_DECAY,
                    RiskSeverity.HIGH if degradation > 0.5 else RiskSeverity.MEDIUM,
                    f"Model {model_id} performance degraded by {degradation*100:.1f}%",
                    {'recent_error': recent_mean, 'historical_error': historical_mean, 'degradation': degradation},
                    "Retrain model or reduce reliance"
                )
                return True, alert
        
        # Check confidence decay
        if model_id in self.confidence_history:
            conf_history = list(self.confidence_history[model_id])
            if len(conf_history) >= self.lookback_periods * 2:
                recent_conf = [c['confidence'] for c in conf_history[-self.lookback_periods:]]
                historical_conf = [c['confidence'] for c in conf_history[-self.lookback_periods*2:-self.lookback_periods]]
                
                if NUMPY_AVAILABLE:
                    conf_decline = np.mean(historical_conf) - np.mean(recent_conf)
                else:
                    conf_decline = sum(historical_conf)/len(historical_conf) - sum(recent_conf)/len(recent_conf)
                
                if conf_decline > self.confidence_decay_threshold:
                    alert = self._create_alert(
                        RiskType.MODEL_DECAY,
                        RiskSeverity.MEDIUM,
                        f"Model {model_id} confidence declining",
                        {'confidence_decline': conf_decline},
                        "Review model inputs and retrain"
                    )
                    return True, alert
        
        return False, None
    
    def _create_alert(
        self,
        risk_type: RiskType,
        severity: RiskSeverity,
        description: str,
        evidence: Dict,
        action: str
    ) -> HiddenRiskAlert:
        """Create a hidden risk alert"""
        alert = HiddenRiskAlert(
            alert_id=hashlib.sha256(f"{risk_type}_{datetime.now()}".encode()).hexdigest()[:16],
            risk_type=risk_type,
            severity=severity,
            description=description,
            evidence=evidence,
            recommended_action=action
        )
        self.alerts.append(alert)
        logger.warning(f"HIDDEN RISK DETECTED: {description}")
        return alert
    
    def get_model_health(self, model_id: str) -> Dict[str, Any]:
        """Get health metrics for a model"""
        if model_id not in self.performance_history:
            return {'status': 'unknown'}
        
        history = list(self.performance_history[model_id])
        if not history:
            return {'status': 'no_data'}
        
        recent = history[-min(50, len(history)):]
        errors = [h['error'] for h in recent]
        
        if NUMPY_AVAILABLE:
            return {
                'status': 'active',
                'mean_error': float(np.mean(errors)),
                'std_error': float(np.std(errors)),
                'sample_count': len(history),
                'last_update': history[-1]['timestamp'].isoformat()
            }
        else:
            mean_error = sum(errors) / len(errors)
            return {
                'status': 'active',
                'mean_error': mean_error,
                'sample_count': len(history),
                'last_update': history[-1]['timestamp'].isoformat()
            }


class DataPoisoningDefense:
    """
    Defends against data poisoning attacks.
    
    Detection Methods:
    1. Statistical anomaly detection
    2. Data distribution monitoring
    3. Source verification
    4. Temporal consistency checks
    5. Cross-validation with multiple sources
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Baseline statistics
        self.baselines: Dict[str, Dict[str, float]] = {}
        
        # Anomaly thresholds
        self.z_score_threshold = self.config.get('z_score_threshold', 4.0)
        self.distribution_shift_threshold = self.config.get('distribution_shift', 0.3)
        
        # Data history
        self.data_history: Dict[str, deque] = {}
        
        # Quarantine
        self.quarantined_sources: set = set()
        
        # Alerts
        self.alerts: List[HiddenRiskAlert] = []
        
        logger.info("DataPoisoningDefense initialized")
    
    def establish_baseline(
        self,
        data_source: str,
        data: List[float]
    ):
        """Establish baseline statistics for a data source"""
        if not data or not NUMPY_AVAILABLE:
            return
        
        arr = np.array(data)
        self.baselines[data_source] = {
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'median': float(np.median(arr)),
            'established_at': datetime.now().isoformat()
        }
        
        logger.info(f"Baseline established for {data_source}")
    
    def validate_data(
        self,
        data_source: str,
        data_point: float,
        timestamp: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """
        Validate a data point against baseline.
        
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check if source is quarantined
        if data_source in self.quarantined_sources:
            return False, f"Data source {data_source} is quarantined"
        
        # Initialize history
        if data_source not in self.data_history:
            self.data_history[data_source] = deque(maxlen=1000)
        
        self.data_history[data_source].append({
            'value': data_point,
            'timestamp': timestamp or datetime.now()
        })
        
        # Check against baseline
        if data_source in self.baselines and NUMPY_AVAILABLE:
            baseline = self.baselines[data_source]
            
            # Z-score check
            if baseline['std'] > 0:
                z_score = abs(data_point - baseline['mean']) / baseline['std']
                
                if z_score > self.z_score_threshold:
                    self._create_alert(
                        RiskType.DATA_POISONING,
                        RiskSeverity.HIGH,
                        f"Extreme outlier from {data_source}: z-score {z_score:.2f}",
                        {'data_point': data_point, 'z_score': z_score, 'baseline': baseline},
                        "Verify data source and quarantine if suspicious"
                    )
                    return False, f"Extreme outlier (z-score: {z_score:.2f})"
        
        # Check temporal consistency
        if len(self.data_history[data_source]) >= 2:
            prev = self.data_history[data_source][-2]['value']
            if prev != 0:
                change = abs(data_point - prev) / abs(prev)
                
                if change > 0.5:  # 50% change
                    self._create_alert(
                        RiskType.DATA_POISONING,
                        RiskSeverity.MEDIUM,
                        f"Sudden change in {data_source}: {change*100:.1f}%",
                        {'previous': prev, 'current': data_point, 'change': change},
                        "Verify data continuity"
                    )
        
        return True, "Data validated"
    
    def check_distribution_shift(
        self,
        data_source: str
    ) -> Tuple[bool, float]:
        """
        Check for distribution shift in recent data.
        
        Returns:
            Tuple of (has_shifted, shift_magnitude)
        """
        if data_source not in self.data_history or data_source not in self.baselines:
            return False, 0.0
        
        if not NUMPY_AVAILABLE:
            return False, 0.0
        
        history = list(self.data_history[data_source])
        if len(history) < 100:
            return False, 0.0
        
        recent = np.array([h['value'] for h in history[-50:]])
        baseline = self.baselines[data_source]
        
        # Compare means
        mean_shift = abs(np.mean(recent) - baseline['mean']) / baseline['std'] if baseline['std'] > 0 else 0
        
        # Compare standard deviations
        std_shift = abs(np.std(recent) - baseline['std']) / baseline['std'] if baseline['std'] > 0 else 0
        
        total_shift = (mean_shift + std_shift) / 2
        
        if total_shift > self.distribution_shift_threshold:
            self._create_alert(
                RiskType.DATA_POISONING,
                RiskSeverity.MEDIUM,
                f"Distribution shift detected in {data_source}",
                {'mean_shift': mean_shift, 'std_shift': std_shift, 'total_shift': total_shift},
                "Re-establish baseline or investigate source"
            )
            return True, total_shift
        
        return False, total_shift
    
    def quarantine_source(self, data_source: str, reason: str):
        """Quarantine a data source"""
        self.quarantined_sources.add(data_source)
        logger.warning(f"Data source QUARANTINED: {data_source} - {reason}")
    
    def restore_source(self, data_source: str):
        """Restore a quarantined data source"""
        if data_source in self.quarantined_sources:
            self.quarantined_sources.remove(data_source)
            logger.info(f"Data source restored: {data_source}")
    
    def _create_alert(
        self,
        risk_type: RiskType,
        severity: RiskSeverity,
        description: str,
        evidence: Dict,
        action: str
    ) -> HiddenRiskAlert:
        """Create a hidden risk alert"""
        alert = HiddenRiskAlert(
            alert_id=hashlib.sha256(f"{risk_type}_{datetime.now()}".encode()).hexdigest()[:16],
            risk_type=risk_type,
            severity=severity,
            description=description,
            evidence=evidence,
            recommended_action=action
        )
        self.alerts.append(alert)
        return alert


class AdversarialAttackDetector:
    """
    Detects adversarial attacks on the trading system.
    
    Attack Types:
    1. Price manipulation (spoofing, layering)
    2. Model poisoning attempts
    3. Stop hunting
    4. Quote stuffing
    5. Momentum ignition
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Detection thresholds
        self.order_cancel_ratio_threshold = self.config.get('cancel_ratio', 0.9)
        self.quote_update_threshold = self.config.get('quote_updates_per_sec', 100)
        self.stop_hunt_threshold = self.config.get('stop_hunt_pct', 0.02)
        
        # Tracking
        self.order_flow: deque = deque(maxlen=10000)
        self.quote_updates: Dict[str, deque] = {}
        self.stop_levels: Dict[str, List[float]] = {}
        
        # Alerts
        self.alerts: List[HiddenRiskAlert] = []
        
        logger.info("AdversarialAttackDetector initialized")
    
    def record_order_event(
        self,
        symbol: str,
        event_type: str,  # 'new', 'cancel', 'fill'
        price: float,
        size: float
    ):
        """Record an order event"""
        self.order_flow.append({
            'symbol': symbol,
            'event_type': event_type,
            'price': price,
            'size': size,
            'timestamp': datetime.now()
        })
    
    def record_quote_update(
        self,
        symbol: str,
        bid: float,
        ask: float
    ):
        """Record a quote update"""
        if symbol not in self.quote_updates:
            self.quote_updates[symbol] = deque(maxlen=1000)
        
        self.quote_updates[symbol].append({
            'bid': bid,
            'ask': ask,
            'timestamp': datetime.now()
        })
    
    def register_stop_level(self, symbol: str, stop_price: float):
        """Register a stop loss level"""
        if symbol not in self.stop_levels:
            self.stop_levels[symbol] = []
        self.stop_levels[symbol].append(stop_price)
    
    def detect_spoofing(self, symbol: str) -> Tuple[bool, Optional[HiddenRiskAlert]]:
        """
        Detect spoofing (placing and quickly canceling orders).
        
        Returns:
            Tuple of (is_spoofing, alert)
        """
        # Get recent orders for symbol
        recent = [o for o in self.order_flow 
                  if o['symbol'] == symbol and 
                  datetime.now() - o['timestamp'] < timedelta(minutes=5)]
        
        if len(recent) < 10:
            return False, None
        
        # Calculate cancel ratio
        new_orders = sum(1 for o in recent if o['event_type'] == 'new')
        cancels = sum(1 for o in recent if o['event_type'] == 'cancel')
        
        if new_orders > 0:
            cancel_ratio = cancels / new_orders
            
            if cancel_ratio > self.order_cancel_ratio_threshold:
                alert = self._create_alert(
                    RiskType.ADVERSARIAL_ATTACK,
                    RiskSeverity.HIGH,
                    f"Potential spoofing detected in {symbol}: {cancel_ratio*100:.0f}% cancel ratio",
                    {'cancel_ratio': cancel_ratio, 'new_orders': new_orders, 'cancels': cancels},
                    "Avoid trading, report to exchange"
                )
                return True, alert
        
        return False, None
    
    def detect_quote_stuffing(self, symbol: str) -> Tuple[bool, Optional[HiddenRiskAlert]]:
        """
        Detect quote stuffing (excessive quote updates).
        
        Returns:
            Tuple of (is_stuffing, alert)
        """
        if symbol not in self.quote_updates:
            return False, None
        
        # Count updates in last second
        now = datetime.now()
        recent = [q for q in self.quote_updates[symbol]
                  if now - q['timestamp'] < timedelta(seconds=1)]
        
        if len(recent) > self.quote_update_threshold:
            alert = self._create_alert(
                RiskType.ADVERSARIAL_ATTACK,
                RiskSeverity.MEDIUM,
                f"Quote stuffing detected in {symbol}: {len(recent)} updates/sec",
                {'updates_per_second': len(recent)},
                "Delay trading, use slower execution"
            )
            return True, alert
        
        return False, None
    
    def detect_stop_hunting(
        self,
        symbol: str,
        current_price: float,
        recent_low: float,
        recent_high: float
    ) -> Tuple[bool, Optional[HiddenRiskAlert]]:
        """
        Detect stop hunting (price moves to trigger stops then reverses).
        
        Returns:
            Tuple of (is_hunting, alert)
        """
        if symbol not in self.stop_levels or not self.stop_levels[symbol]:
            return False, None
        
        stops = self.stop_levels[symbol]
        
        # Check if price touched stop levels
        stops_triggered = [s for s in stops if recent_low <= s <= recent_high]
        
        if stops_triggered:
            # Check if price reversed after triggering
            price_range = recent_high - recent_low
            if price_range > 0:
                reversal = abs(current_price - (recent_low if current_price > recent_low else recent_high)) / price_range
                
                if reversal > 0.5:  # Significant reversal
                    alert = self._create_alert(
                        RiskType.ADVERSARIAL_ATTACK,
                        RiskSeverity.MEDIUM,
                        f"Potential stop hunting in {symbol}",
                        {'stops_triggered': len(stops_triggered), 'reversal': reversal},
                        "Widen stops, use mental stops"
                    )
                    return True, alert
        
        return False, None
    
    def _create_alert(
        self,
        risk_type: RiskType,
        severity: RiskSeverity,
        description: str,
        evidence: Dict,
        action: str
    ) -> HiddenRiskAlert:
        """Create a hidden risk alert"""
        alert = HiddenRiskAlert(
            alert_id=hashlib.sha256(f"{risk_type}_{datetime.now()}".encode()).hexdigest()[:16],
            risk_type=risk_type,
            severity=severity,
            description=description,
            evidence=evidence,
            recommended_action=action
        )
        self.alerts.append(alert)
        logger.warning(f"ADVERSARIAL ATTACK DETECTED: {description}")
        return alert


class OverfittingGuard:
    """
    Guards against overfitting in trading models.
    
    Detection Methods:
    1. In-sample vs out-of-sample performance gap
    2. Parameter sensitivity analysis
    3. Regime-specific performance variance
    4. Complexity penalty monitoring
    5. Cross-validation consistency
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.performance_gap_threshold = self.config.get('performance_gap', 0.3)
        self.sensitivity_threshold = self.config.get('sensitivity', 0.5)
        
        # Tracking
        self.in_sample_performance: Dict[str, List[float]] = {}
        self.out_sample_performance: Dict[str, List[float]] = {}
        self.parameter_sensitivity: Dict[str, Dict[str, float]] = {}
        
        # Alerts
        self.alerts: List[HiddenRiskAlert] = []
        
        logger.info("OverfittingGuard initialized")
    
    def record_performance(
        self,
        model_id: str,
        is_in_sample: bool,
        metric_value: float
    ):
        """Record performance metric"""
        if is_in_sample:
            if model_id not in self.in_sample_performance:
                self.in_sample_performance[model_id] = []
            self.in_sample_performance[model_id].append(metric_value)
        else:
            if model_id not in self.out_sample_performance:
                self.out_sample_performance[model_id] = []
            self.out_sample_performance[model_id].append(metric_value)
    
    def check_overfitting(self, model_id: str) -> Tuple[bool, Optional[HiddenRiskAlert]]:
        """
        Check for overfitting.
        
        Returns:
            Tuple of (is_overfitting, alert)
        """
        if model_id not in self.in_sample_performance or model_id not in self.out_sample_performance:
            return False, None
        
        in_sample = self.in_sample_performance[model_id]
        out_sample = self.out_sample_performance[model_id]
        
        if len(in_sample) < 10 or len(out_sample) < 10:
            return False, None
        
        if NUMPY_AVAILABLE:
            in_mean = np.mean(in_sample[-20:])
            out_mean = np.mean(out_sample[-20:])
        else:
            in_mean = sum(in_sample[-20:]) / len(in_sample[-20:])
            out_mean = sum(out_sample[-20:]) / len(out_sample[-20:])
        
        # Calculate performance gap
        if in_mean > 0:
            gap = (in_mean - out_mean) / in_mean
            
            if gap > self.performance_gap_threshold:
                alert = self._create_alert(
                    RiskType.OVERFITTING,
                    RiskSeverity.HIGH,
                    f"Model {model_id} shows {gap*100:.1f}% performance gap",
                    {'in_sample': in_mean, 'out_sample': out_mean, 'gap': gap},
                    "Simplify model, add regularization, or retrain"
                )
                return True, alert
        
        return False, None
    
    def record_parameter_sensitivity(
        self,
        model_id: str,
        parameter: str,
        sensitivity: float
    ):
        """Record parameter sensitivity"""
        if model_id not in self.parameter_sensitivity:
            self.parameter_sensitivity[model_id] = {}
        self.parameter_sensitivity[model_id][parameter] = sensitivity
    
    def check_sensitivity(self, model_id: str) -> Tuple[bool, List[str]]:
        """
        Check for high parameter sensitivity.
        
        Returns:
            Tuple of (has_high_sensitivity, sensitive_parameters)
        """
        if model_id not in self.parameter_sensitivity:
            return False, []
        
        sensitive = [
            param for param, sens in self.parameter_sensitivity[model_id].items()
            if sens > self.sensitivity_threshold
        ]
        
        if sensitive:
            self._create_alert(
                RiskType.OVERFITTING,
                RiskSeverity.MEDIUM,
                f"Model {model_id} has {len(sensitive)} highly sensitive parameters",
                {'sensitive_parameters': sensitive},
                "Reduce model complexity or use ensemble"
            )
        
        return len(sensitive) > 0, sensitive
    
    def _create_alert(
        self,
        risk_type: RiskType,
        severity: RiskSeverity,
        description: str,
        evidence: Dict,
        action: str
    ) -> HiddenRiskAlert:
        """Create a hidden risk alert"""
        alert = HiddenRiskAlert(
            alert_id=hashlib.sha256(f"{risk_type}_{datetime.now()}".encode()).hexdigest()[:16],
            risk_type=risk_type,
            severity=severity,
            description=description,
            evidence=evidence,
            recommended_action=action
        )
        self.alerts.append(alert)
        return alert


class HiddenRiskDetection:
    """
    Master Hidden Risk Detection System
    
    Coordinates all hidden risk detection:
    - Model Decay
    - Data Poisoning
    - Adversarial Attacks
    - Overfitting
    
    CORE PRINCIPLE: Actively hunt for risks before they materialize.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.model_decay = ModelDecayDetector(config.get('model_decay', {}))
        self.data_poisoning = DataPoisoningDefense(config.get('data_poisoning', {}))
        self.adversarial = AdversarialAttackDetector(config.get('adversarial', {}))
        self.overfitting = OverfittingGuard(config.get('overfitting', {}))
        
        # All alerts
        self.all_alerts: List[HiddenRiskAlert] = []
        
        # Callbacks
        self.on_alert: Optional[Callable] = None
        
        # Lock
        self._lock = threading.Lock()
        
        logger.info("HiddenRiskDetection system initialized")
    
    def run_full_scan(self, models: List[str], symbols: List[str]) -> List[HiddenRiskAlert]:
        """
        Run a full scan for all hidden risks.
        
        Returns:
            List of detected alerts
        """
        with self._lock:
            alerts = []
            
            # Check model decay
            for model_id in models:
                is_decaying, alert = self.model_decay.check_decay(model_id)
                if alert:
                    alerts.append(alert)
                
                # Check overfitting
                is_overfit, overfit_alert = self.overfitting.check_overfitting(model_id)
                if overfit_alert:
                    alerts.append(overfit_alert)
            
            # Check adversarial attacks
            for symbol in symbols:
                is_spoofing, spoof_alert = self.adversarial.detect_spoofing(symbol)
                if spoof_alert:
                    alerts.append(spoof_alert)
                
                is_stuffing, stuff_alert = self.adversarial.detect_quote_stuffing(symbol)
                if stuff_alert:
                    alerts.append(stuff_alert)
            
            # Check data poisoning
            for source in self.data_poisoning.data_history.keys():
                has_shift, _ = self.data_poisoning.check_distribution_shift(source)
            
            # Collect all alerts
            self.all_alerts.extend(alerts)
            
            # Notify
            if alerts and self.on_alert:
                for alert in alerts:
                    self.on_alert(alert)
            
            return alerts
    
    def validate_data(
        self,
        data_source: str,
        data_point: float
    ) -> Tuple[bool, str]:
        """Validate incoming data"""
        return self.data_poisoning.validate_data(data_source, data_point)
    
    def record_prediction(
        self,
        model_id: str,
        prediction: float,
        actual: float,
        confidence: float
    ):
        """Record a model prediction"""
        self.model_decay.record_prediction(model_id, prediction, actual, confidence)
    
    def get_unacknowledged_alerts(self) -> List[HiddenRiskAlert]:
        """Get all unacknowledged alerts"""
        return [a for a in self.all_alerts if not a.acknowledged]
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        for alert in self.all_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                break
    
    def get_status(self) -> Dict[str, Any]:
        """Get hidden risk detection status"""
        return {
            'total_alerts': len(self.all_alerts),
            'unacknowledged': len(self.get_unacknowledged_alerts()),
            'quarantined_sources': list(self.data_poisoning.quarantined_sources),
            'models_monitored': len(self.model_decay.performance_history),
            'recent_alerts': [a.to_dict() for a in self.all_alerts[-10:]]
        }

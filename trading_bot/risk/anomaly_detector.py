"""
Anomaly Detection System ($0 Budget)
Statistical outlier detection
Machine learning-based anomaly alerts
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import deque
try:
    from scipy import stats
except ImportError:
    scipy = None
import numpy

import logging
logger = logging.getLogger(__name__)



@dataclass
class Anomaly:
    """Detected anomaly"""
    timestamp: datetime
    type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    value: float
    expected_range: Tuple[float, float]
    deviation: float
    description: str


class StatisticalAnomalyDetector:
    """Statistical anomaly detection (free)"""
    
    def __init__(self, window_size: int = 100, threshold: float = 3.0):
        self.window_size = window_size
        self.threshold = threshold  # Standard deviations
        self.data_buffer = deque(maxlen=window_size)
        
    def detect(self, value: float) -> Tuple[bool, Anomaly]:
        """Detect if value is anomalous"""
        
        self.data_buffer.append(value)
        
        if len(self.data_buffer) < 10:
            return False, None
        
        # Calculate statistics
        data_array = np.array(self.data_buffer)
        mean = np.mean(data_array)
        std = np.std(data_array)
        
        # Z-score
        z_score = (value - mean) / std if std > 0 else 0
        
        # Check if anomalous
        is_anomaly = abs(z_score) > self.threshold
        
        if is_anomaly:
            # Determine severity
            if abs(z_score) > 5:
                severity = 'critical'
            elif abs(z_score) > 4:
                severity = 'high'
            elif abs(z_score) > 3:
                severity = 'medium'
            else:
                severity = 'low'
            
            anomaly = Anomaly(
                timestamp=datetime.now(),
                type='statistical',
                severity=severity,
                value=value,
                expected_range=(mean - self.threshold * std, mean + self.threshold * std),
                deviation=abs(z_score),
                description=f"Value {value:.2f} is {abs(z_score):.1f}σ from mean {mean:.2f}"
            )
            
            return True, anomaly
        
        return False, None


class IQRAnomalyDetector:
    """Interquartile Range (IQR) anomaly detection (free)"""
    
    def __init__(self, window_size: int = 100, multiplier: float = 1.5):
        self.window_size = window_size
        self.multiplier = multiplier
        self.data_buffer = deque(maxlen=window_size)
        
    def detect(self, value: float) -> Tuple[bool, Anomaly]:
        """Detect using IQR method"""
        
        self.data_buffer.append(value)
        
        if len(self.data_buffer) < 10:
            return False, None
        
        # Calculate IQR
        data_array = np.array(self.data_buffer)
        q1 = np.percentile(data_array, 25)
        q3 = np.percentile(data_array, 75)
        iqr = q3 - q1
        
        # Bounds
        lower_bound = q1 - self.multiplier * iqr
        upper_bound = q3 + self.multiplier * iqr
        
        # Check if anomalous
        is_anomaly = value < lower_bound or value > upper_bound
        
        if is_anomaly:
            deviation = min(abs(value - lower_bound), abs(value - upper_bound)) / iqr if iqr > 0 else 0
            
            if deviation > 3:
                severity = 'critical'
            elif deviation > 2:
                severity = 'high'
            elif deviation > 1:
                severity = 'medium'
            else:
                severity = 'low'
            
            anomaly = Anomaly(
                timestamp=datetime.now(),
                type='iqr',
                severity=severity,
                value=value,
                expected_range=(lower_bound, upper_bound),
                deviation=deviation,
                description=f"Value {value:.2f} outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]"
            )
            
            return True, anomaly
        
        return False, None


class MADAnomalyDetector:
    """Median Absolute Deviation (MAD) anomaly detection (free)"""
    
    def __init__(self, window_size: int = 100, threshold: float = 3.5):
        self.window_size = window_size
        self.threshold = threshold
        self.data_buffer = deque(maxlen=window_size)
        
    def detect(self, value: float) -> Tuple[bool, Anomaly]:
        """Detect using MAD method"""
        
        self.data_buffer.append(value)
        
        if len(self.data_buffer) < 10:
            return False, None
        
        # Calculate MAD
        data_array = np.array(self.data_buffer)
        median = np.median(data_array)
        mad = np.median(np.abs(data_array - median))
        
        # Modified Z-score
        if mad > 0:
            modified_z = 0.6745 * (value - median) / mad
        else:
            modified_z = 0
        
        # Check if anomalous
        is_anomaly = abs(modified_z) > self.threshold
        
        if is_anomaly:
            if abs(modified_z) > 5:
                severity = 'critical'
            elif abs(modified_z) > 4:
                severity = 'high'
            else:
                severity = 'medium'
            
            anomaly = Anomaly(
                timestamp=datetime.now(),
                type='mad',
                severity=severity,
                value=value,
                expected_range=(median - self.threshold * mad, median + self.threshold * mad),
                deviation=abs(modified_z),
                description=f"Value {value:.2f} has modified Z-score of {abs(modified_z):.1f}"
            )
            
            return True, anomaly
        
        return False, None


class IsolationForestDetector:
    """Simplified Isolation Forest (free, no sklearn needed)"""
    
    def __init__(self, window_size: int = 100, contamination: float = 0.1):
        self.window_size = window_size
        self.contamination = contamination
        self.data_buffer = deque(maxlen=window_size)
        
    def detect(self, value: float) -> Tuple[bool, Anomaly]:
        """Detect using simplified isolation approach"""
        
        self.data_buffer.append(value)
        
        if len(self.data_buffer) < 20:
            return False, None
        
        # Calculate isolation score (simplified)
        data_array = np.array(self.data_buffer)
        
        # Count how many points are between value and median
        median = np.median(data_array)
        distances = np.abs(data_array - median)
        value_distance = abs(value - median)
        
        # Isolation score: how far from the crowd
        isolation_score = np.sum(distances < value_distance) / len(distances)
        
        # Anomaly if very isolated (far from most points)
        threshold = 1 - self.contamination
        is_anomaly = isolation_score > threshold
        
        if is_anomaly:
            if isolation_score > 0.95:
                severity = 'critical'
            elif isolation_score > 0.90:
                severity = 'high'
            else:
                severity = 'medium'
            
            anomaly = Anomaly(
                timestamp=datetime.now(),
                type='isolation',
                severity=severity,
                value=value,
                expected_range=(np.min(data_array), np.max(data_array)),
                deviation=isolation_score,
                description=f"Value {value:.2f} is isolated (score: {isolation_score:.2f})"
            )
            
            return True, anomaly
        
        return False, None


class ChangePointDetector:
    """Change point detection (free)"""
    
    def __init__(self, window_size: int = 50, threshold: float = 2.0):
        self.window_size = window_size
        self.threshold = threshold
        self.data_buffer = deque(maxlen=window_size * 2)
        
    def detect(self, value: float) -> Tuple[bool, Anomaly]:
        """Detect change points"""
        
        self.data_buffer.append(value)
        
        if len(self.data_buffer) < self.window_size * 2:
            return False, None
        
        # Split into two windows
        data_array = np.array(self.data_buffer)
        first_half = data_array[:self.window_size]
        second_half = data_array[self.window_size:]
        
        # Test for change in mean
        mean1 = np.mean(first_half)
        mean2 = np.mean(second_half)
        std1 = np.std(first_half)
        std2 = np.std(second_half)
        
        # T-test
        pooled_std = np.sqrt((std1**2 + std2**2) / 2)
        if pooled_std > 0:
            t_stat = abs(mean2 - mean1) / (pooled_std * np.sqrt(2 / self.window_size))
        else:
            t_stat = 0
        
        # Check if significant change
        is_change_point = t_stat > self.threshold
        
        if is_change_point:
            if t_stat > 4:
                severity = 'critical'
            elif t_stat > 3:
                severity = 'high'
            else:
                severity = 'medium'
            
            anomaly = Anomaly(
                timestamp=datetime.now(),
                type='change_point',
                severity=severity,
                value=value,
                expected_range=(mean1 - 2*std1, mean1 + 2*std1),
                deviation=t_stat,
                description=f"Change point detected: mean shifted from {mean1:.2f} to {mean2:.2f}"
            )
            
            return True, anomaly
        
        return False, None


class AnomalyDetectionSystem:
    """Unified anomaly detection system"""
    
    def __init__(self):
        self.statistical_detector = StatisticalAnomalyDetector()
        self.iqr_detector = IQRAnomalyDetector()
        self.mad_detector = MADAnomalyDetector()
        self.isolation_detector = IsolationForestDetector()
        self.change_point_detector = ChangePointDetector()
        
        self.anomalies: List[Anomaly] = []
        self.alert_callbacks: List[callable] = []
        
    def detect_anomalies(self, value: float, use_ensemble: bool = True) -> List[Anomaly]:
        """Detect anomalies using multiple methods"""
        
        detected_anomalies = []
        
        # Run all detectors
        detectors = [
            ('statistical', self.statistical_detector),
            ('iqr', self.iqr_detector),
            ('mad', self.mad_detector),
            ('isolation', self.isolation_detector),
            ('change_point', self.change_point_detector)
        ]
        
        for name, detector in detectors:
            is_anomaly, anomaly = detector.detect(value)
            if is_anomaly and anomaly:
                detected_anomalies.append(anomaly)
        
        # Ensemble voting (if multiple detectors agree, increase confidence)
        if use_ensemble and len(detected_anomalies) >= 2:
            # Upgrade severity if multiple detectors agree
            for anomaly in detected_anomalies:
                if len(detected_anomalies) >= 3:
                    if anomaly.severity == 'medium':
                        anomaly.severity = 'high'
                    elif anomaly.severity == 'high':
                        anomaly.severity = 'critical'
        
        # Store anomalies
        self.anomalies.extend(detected_anomalies)
        
        # Trigger alerts
        for anomaly in detected_anomalies:
            self._trigger_alerts(anomaly)
        
        return detected_anomalies
    
    def register_alert_callback(self, callback: callable):
        """Register callback for anomaly alerts"""
        self.alert_callbacks.append(callback)
    
    def _trigger_alerts(self, anomaly: Anomaly):
        """Trigger alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(anomaly)
            except Exception as e:
                logger.info(f"Alert callback error: {e}")
    
    def get_anomaly_summary(self) -> Dict:
        """Get summary of detected anomalies"""
        
        if not self.anomalies:
            return {'total': 0, 'by_severity': {}, 'by_type': {}}
        
        by_severity = {}
        by_type = {}
        
        for anomaly in self.anomalies:
            # Count by severity
            by_severity[anomaly.severity] = by_severity.get(anomaly.severity, 0) + 1
            
            # Count by type
            by_type[anomaly.type] = by_type.get(anomaly.type, 0) + 1
        
        return {
            'total': len(self.anomalies),
            'by_severity': by_severity,
            'by_type': by_type,
            'recent': self.anomalies[-10:] if len(self.anomalies) > 10 else self.anomalies,
            'cost': 0  # Free
        }


# Example usage
if __name__ == '__main__':
    # Initialize system
    system = AnomalyDetectionSystem()
    
    # Register alert callback
    def alert_handler(anomaly: Anomaly):
        logger.info(f"\n🚨 ANOMALY ALERT!")
        logger.info(f"   Type: {anomaly.type}")
        logger.info(f"   Severity: {anomaly.severity.upper()}")
        logger.info(f"   {anomaly.description}")
    
    system.register_alert_callback(alert_handler)
    
    logger.info("Anomaly Detection System")
    print("="*60)
    
    # Generate test data with anomalies
    np.random.seed(42)
    normal_data = np.random.randn(100) * 10 + 100
    
    # Add some anomalies
    anomalous_values = [150, 50, 180, 30]  # Outliers
    
    logger.info("\nProcessing normal data...")
    for value in normal_data[:50]:
        anomalies = system.detect_anomalies(value)
    
    logger.info("\nInjecting anomalies...")
    for value in anomalous_values:
        anomalies = system.detect_anomalies(value)
    
    # Get summary
    summary = system.get_anomaly_summary()
    
    print("\n" + "="*60)
    logger.info("ANOMALY SUMMARY")
    print("="*60)
    logger.info(f"Total Anomalies: {summary['total']}")
    logger.info(f"\nBy Severity:")
    for severity, count in summary['by_severity'].items():
        logger.info(f"  {severity.upper()}: {count}")
    logger.info(f"\nBy Type:")
    for type_name, count in summary['by_type'].items():
        logger.info(f"  {type_name}: {count}")
    logger.info(f"\nCost: ${summary['cost']}")

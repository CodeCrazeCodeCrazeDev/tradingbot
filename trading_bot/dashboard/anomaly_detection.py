"""
from pathlib import Path
Advanced Anomaly Detection for Trading Performance Metrics
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Result of anomaly detection"""
    is_anomaly: bool
    anomaly_score: float
    expected_range: Tuple[float, float]
    detection_method: str
    description: str


class AdvancedAnomalyDetector:
    """
    Advanced anomaly detection for trading performance metrics
    
    Features:
    - Multiple detection algorithms
    - Ensemble approach
    - Adaptive thresholds
    - Contextual anomaly detection
    - Trend-aware detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Statistical parameters
        self.z_score_threshold = self.config.get('z_score_threshold', 3.0)
        self.iqr_multiplier = self.config.get('iqr_multiplier', 1.5)
        self.min_history_points = self.config.get('min_history_points', 20)
        
        # Moving window parameters
        self.window_size = self.config.get('window_size', 20)
        self.window_std_threshold = self.config.get('window_std_threshold', 2.5)
        
        # Machine learning parameters
        self.isolation_forest_contamination = self.config.get('isolation_forest_contamination', 0.05)
        self.dbscan_eps = self.config.get('dbscan_eps', 0.5)
        self.dbscan_min_samples = self.config.get('dbscan_min_samples', 5)
        
        # Ensemble parameters
        self.min_detectors_agreement = self.config.get('min_detectors_agreement', 2)
        
        # Metric-specific parameters
        self.metric_params = self.config.get('metric_params', {})
        
        # Models
        self.isolation_forest = None
        self.pca = None
        
        # Metric history
        self.history = {}
        self.seasonal_patterns = {}
        
        logger.info("Advanced Anomaly Detector initialized")
    
    def detect_anomaly(self, metric_name: str, value: float, 
                     timestamp: datetime = None) -> AnomalyResult:
        """
        Detect if a metric value is anomalous
        
        Args:
            metric_name: Name of the metric
            value: Current value of the metric
            timestamp: Timestamp of the measurement (default: now)
            
        Returns:
            AnomalyResult with detection information
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Initialize history if needed
        if metric_name not in self.history:
            self.history[metric_name] = []
        
        # Get history
        history = self.history[metric_name]
        
        # Not enough history
        if len(history) < self.min_history_points:
            # Add to history
            history.append((timestamp, value))
            
            # Return non-anomalous result
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                expected_range=(0.0, 0.0),
                detection_method="insufficient_data",
                description="Insufficient historical data for anomaly detection"
            )
        
        # Get metric-specific parameters
        params = self.metric_params.get(metric_name, {})
        z_score_threshold = params.get('z_score_threshold', self.z_score_threshold)
        window_std_threshold = params.get('window_std_threshold', self.window_std_threshold)
        
        # Extract values from history
        timestamps = [h[0] for h in history]
        values = [h[1] for h in history]
        
        # Run multiple detection methods
        detectors = []
        
        # 1. Z-score method
        z_score_result = self._detect_z_score_anomaly(value, values, z_score_threshold)
        detectors.append(z_score_result)
        
        # 2. IQR method
        iqr_result = self._detect_iqr_anomaly(value, values)
        detectors.append(iqr_result)
        
        # 3. Moving window method
        window_result = self._detect_window_anomaly(value, values, window_std_threshold)
        detectors.append(window_result)
        
        # 4. Seasonal decomposition (if enough data)
        if len(history) >= 2 * self.window_size:
            seasonal_result = self._detect_seasonal_anomaly(metric_name, value, timestamps, values)
            detectors.append(seasonal_result)
        
        # 5. Machine learning methods (if enough data)
        if len(history) >= 50:
            # Isolation Forest
            if_result = self._detect_isolation_forest_anomaly(metric_name, value, values)
            detectors.append(if_result)
        
        # Ensemble decision
        anomaly_count = sum(1 for d in detectors if d.is_anomaly)
        is_anomaly = anomaly_count >= self.min_detectors_agreement
        
        # Calculate overall anomaly score (average of all methods)
        anomaly_score = sum(d.anomaly_score for d in detectors) / len(detectors)
        
        # Get expected range (from z-score method)
        expected_range = z_score_result.expected_range
        
        # Determine primary detection method
        if is_anomaly:
            # Find method with highest score
            primary_method = max(detectors, key=lambda d: d.anomaly_score if d.is_anomaly else 0)
            detection_method = primary_method.detection_method
            description = primary_method.description
        else:
            detection_method = "ensemble"
            description = "No anomaly detected"
        
        # Add to history
        history.append((timestamp, value))
        
        # Limit history size
        if len(history) > 1000:
            history = history[-1000:]
        self.history[metric_name] = history
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            expected_range=expected_range,
            detection_method=detection_method,
            description=description
        )
    
    def _detect_z_score_anomaly(self, value: float, history: List[float], 
                              threshold: float) -> AnomalyResult:
        """Detect anomaly using Z-score method"""
        mean = np.mean(history)
        std = np.std(history)
        
        if std > 0:
            z_score = abs((value - mean) / std)
            is_anomaly = z_score > threshold
            anomaly_score = z_score / threshold
        else:
            z_score = 0
            is_anomaly = False
            anomaly_score = 0
        
        expected_range = (mean - threshold * std, mean + threshold * std)
        
        description = f"Z-score: {z_score:.2f} (threshold: {threshold:.2f})"
        if is_anomaly:
            description += f", value {value:.2f} outside expected range [{expected_range[0]:.2f}, {expected_range[1]:.2f}]"
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            expected_range=expected_range,
            detection_method="z_score",
            description=description
        )
    
    def _detect_iqr_anomaly(self, value: float, history: List[float]) -> AnomalyResult:
        """Detect anomaly using IQR method"""
        q1 = np.percentile(history, 25)
        q3 = np.percentile(history, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - self.iqr_multiplier * iqr
        upper_bound = q3 + self.iqr_multiplier * iqr
        
        is_anomaly = value < lower_bound or value > upper_bound
        
        if is_anomaly:
            if value < lower_bound:
                distance = (lower_bound - value) / iqr if iqr > 0 else 0
            else:
                distance = (value - upper_bound) / iqr if iqr > 0 else 0
            anomaly_score = min(1.0, distance)
        else:
            anomaly_score = 0.0
        
        description = f"IQR bounds: [{lower_bound:.2f}, {upper_bound:.2f}]"
        if is_anomaly:
            description += f", value {value:.2f} outside bounds"
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            expected_range=(lower_bound, upper_bound),
            detection_method="iqr",
            description=description
        )
    
    def _detect_window_anomaly(self, value: float, history: List[float], 
                             threshold: float) -> AnomalyResult:
        """Detect anomaly using moving window method"""
        if len(history) < self.window_size:
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                expected_range=(0.0, 0.0),
                detection_method="window",
                description="Insufficient data for window method"
            )
        
        # Get recent window
        recent = history[-self.window_size:]
        
        # Calculate statistics
        mean = np.mean(recent)
        std = np.std(recent)
        
        if std > 0:
            z_score = abs((value - mean) / std)
            is_anomaly = z_score > threshold
            anomaly_score = z_score / threshold
        else:
            z_score = 0
            is_anomaly = False
            anomaly_score = 0
        
        expected_range = (mean - threshold * std, mean + threshold * std)
        
        description = f"Window Z-score: {z_score:.2f} (threshold: {threshold:.2f})"
        if is_anomaly:
            description += f", value {value:.2f} outside recent window range"
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            expected_range=expected_range,
            detection_method="window",
            description=description
        )
    
    def _detect_seasonal_anomaly(self, metric_name: str, value: float, 
                               timestamps: List[datetime], 
                               values: List[float]) -> AnomalyResult:
        """Detect anomaly using seasonal decomposition"""
        try:
            # Check if we have a seasonal pattern
            if metric_name not in self.seasonal_patterns:
                # Try to detect seasonality
                self._detect_seasonality(metric_name, timestamps, values)
            
            # Get seasonal pattern
            pattern = self.seasonal_patterns.get(metric_name, {})
            
            if not pattern:
                return AnomalyResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    expected_range=(0.0, 0.0),
                    detection_method="seasonal",
                    description="No seasonal pattern detected"
                )
            
            # Get current position in pattern
            current_time = timestamps[-1]
            position = self._get_seasonal_position(current_time, pattern.get('period', 24))
            
            # Get expected value and range
            expected = pattern.get('values', {}).get(position, {})
            if not expected:
                return AnomalyResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    expected_range=(0.0, 0.0),
                    detection_method="seasonal",
                    description="No seasonal data for current position"
                )
            
            expected_value = expected.get('mean', 0)
            expected_std = expected.get('std', 0)
            
            # Calculate deviation
            if expected_std > 0:
                deviation = abs((value - expected_value) / expected_std)
                is_anomaly = deviation > self.z_score_threshold
                anomaly_score = deviation / self.z_score_threshold
            else:
                deviation = 0
                is_anomaly = False
                anomaly_score = 0
            
            expected_range = (
                expected_value - self.z_score_threshold * expected_std,
                expected_value + self.z_score_threshold * expected_std
            )
            
            description = f"Seasonal deviation: {deviation:.2f} (threshold: {self.z_score_threshold:.2f})"
            if is_anomaly:
                description += f", value {value:.2f} outside seasonal range"
            
            return AnomalyResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                expected_range=expected_range,
                detection_method="seasonal",
                description=description
            )
            
        except Exception as e:
            logger.warning(f"Error in seasonal anomaly detection: {e}")
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                expected_range=(0.0, 0.0),
                detection_method="seasonal",
                description="Error in seasonal analysis"
            )
    
    def _detect_isolation_forest_anomaly(self, metric_name: str, value: float, 
                                       values: List[float]) -> AnomalyResult:
        """Detect anomaly using Isolation Forest"""
        try:
            # Create model if needed
            if self.isolation_forest is None:
                self.isolation_forest = IsolationForest(
                    contamination=self.isolation_forest_contamination,
                    random_state=42
                )
                # Fit on historical data
                X = np.array(values[:-1]).reshape(-1, 1)
                self.isolation_forest.fit(X)
            
            # Predict
            X_new = np.array([value]).reshape(1, -1)
            prediction = self.isolation_forest.predict(X_new)[0]
            score = self.isolation_forest.score_samples(X_new)[0]
            
            # Convert score to anomaly score (higher is more anomalous)
            # Isolation Forest returns negative scores, lower is more anomalous
            anomaly_score = max(0, min(1, -score / 0.5))
            
            is_anomaly = prediction == -1
            
            # Calculate expected range (approximate)
            mean = np.mean(values)
            std = np.std(values)
            expected_range = (mean - 3 * std, mean + 3 * std)
            
            description = f"Isolation Forest score: {score:.2f}"
            if is_anomaly:
                description += ", value identified as outlier"
            
            return AnomalyResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                expected_range=expected_range,
                detection_method="isolation_forest",
                description=description
            )
            
        except Exception as e:
            logger.warning(f"Error in Isolation Forest anomaly detection: {e}")
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                expected_range=(0.0, 0.0),
                detection_method="isolation_forest",
                description="Error in Isolation Forest analysis"
            )
    
    def _detect_seasonality(self, metric_name: str, timestamps: List[datetime], 
                          values: List[float]):
        """Detect seasonality in time series data"""
        try:
            # Check for daily pattern (24 hours)
            period = 24
            
            # Group by hour of day
            hour_groups = {}
            for i, (ts, val) in enumerate(zip(timestamps, values)):
                hour = ts.hour
                if hour not in hour_groups:
                    hour_groups[hour] = []
                hour_groups[hour].append(val)
            
            # Calculate statistics for each hour
            hour_stats = {}
            for hour, vals in hour_groups.items():
                if len(vals) >= 3:  # Need at least 3 points for statistics
                    hour_stats[hour] = {
                        'mean': np.mean(vals),
                        'std': np.std(vals),
                        'count': len(vals)
                    }
            
            # Store pattern
            self.seasonal_patterns[metric_name] = {
                'period': period,
                'values': hour_stats
            }
            
            logger.info(f"Detected daily seasonality for {metric_name}")
            
        except Exception as e:
            logger.warning(f"Error detecting seasonality: {e}")
    
    def _get_seasonal_position(self, timestamp: datetime, period: int) -> int:
        """Get position in seasonal pattern"""
        if period == 24:  # Daily pattern
            return timestamp.hour
        elif period == 7:  # Weekly pattern
            return timestamp.weekday()
        else:
            return 0
    
    def plot_metric_history(self, metric_name: str, save_path: Optional[str] = None):
        """
        Plot metric history with anomaly detection
        
        Args:
            metric_name: Name of the metric
            save_path: Path to save plot, if None, plot is displayed
        """
        if metric_name not in self.history:
            logger.warning(f"No history for metric {metric_name}")
            return
        
        history = self.history[metric_name]
        
        if not history:
            logger.warning(f"Empty history for metric {metric_name}")
            return
        
        # Extract data
        timestamps = [h[0] for h in history]
        values = [h[1] for h in history]
        
        # Detect anomalies
        anomalies = []
        for i, (ts, val) in enumerate(history):
            # Skip first few points (not enough history)
            if i < self.min_history_points:
                continue
            
            # Use previous history for detection
            prev_history = history[:i]
            prev_values = [h[1] for h in prev_history]
            
            # Detect anomaly
            result = self._detect_z_score_anomaly(val, prev_values, self.z_score_threshold)
            
            if result.is_anomaly:
                anomalies.append((ts, val))
        
        # Create plot
        plt.figure(figsize=(12, 6))
        
        # Plot metric values
        plt.plot(timestamps, values, 'b-', label=metric_name)
        
        # Plot anomalies
        if anomalies:
            anomaly_timestamps = [a[0] for a in anomalies]
            anomaly_values = [a[1] for a in anomalies]
            plt.scatter(anomaly_timestamps, anomaly_values, color='red', s=50, label='Anomalies')
        
        # Add labels and title
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.title(f'{metric_name} with Anomaly Detection')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Format x-axis
        plt.gcf().autofmt_xdate()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved plot to {save_path}")
        else:
            plt.show()
        
        plt.close()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create detector
    detector = AdvancedAnomalyDetector()
    
    # Simulate metric data
    import random
    
    # Start time
    start_time = datetime.now() - timedelta(hours=100)
    
    # Generate normal data with occasional anomalies
    for i in range(100):
        timestamp = start_time + timedelta(hours=i)
        
        # Normal value with daily pattern
        hour = timestamp.hour
        base_value = 100 + 10 * np.sin(hour * np.pi / 12)
        
        # Add noise
        noise = random.normalvariate(0, 5)
        value = base_value + noise
        
        # Add occasional anomalies
        if random.random() < 0.05:
            value += random.choice([-1, 1]) * random.uniform(20, 50)
        
        # Detect anomaly
        result = detector.detect_anomaly('test_metric', value, timestamp)
        
        # Print result
        if result.is_anomaly:
            logger.info(f"Anomaly detected at {timestamp}: {value:.2f}, {result.description}")
    
    # Plot results
    detector.plot_metric_history('test_metric')

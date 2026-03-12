"""
ADWIN (Adaptive Windowing) Drift Detector

Paper: "Learning from Time-Changing Data with Adaptive Windowing"
Bifet & Gavaldà (2007)

Detects concept drift in data streams without requiring parameters.
Automatically adjusts window size based on detected changes.
"""

import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import logging
import numpy

logger = logging.getLogger(__name__)


@dataclass
class DriftDetection:
    """Drift detection result."""
    drift_detected: bool
    timestamp: int
    window_size: int
    mean_before: float
    mean_after: float
    change_magnitude: float


class ADWINDetector:
    """
    ADWIN drift detector for trading signals.
    
    Maintains adaptive window and detects when distribution changes.
    No parameters to tune - automatically adapts.
    """
    
    def __init__(self, delta: float = 0.002):
        """
        Initialize ADWIN detector.
        
        Args:
            delta: Confidence parameter (smaller = more sensitive)
        """
        self.delta = delta
        self.window = deque()
        self.total = 0.0
        self.variance = 0.0
        self.width = 0
        
        # Detection history
        self.drift_points = []
        self.total_drifts = 0
        
        logger.info(f"ADWIN detector initialized: delta={delta}")
    
    def add_element(self, value: float) -> bool:
        """
        Add new element and check for drift.
        
        Args:
            value: New data point
        
        Returns:
            True if drift detected
        """
        # Add to window
        self.window.append(value)
        self.width += 1
        self.total += value
        
        # Update variance incrementally
        if self.width > 1:
            mean = self.total / self.width
            self.variance += (value - mean) ** 2
        
        # Check for drift
        drift_detected = self._detect_change()
        
        if drift_detected:
            self.total_drifts += 1
            self.drift_points.append(len(self.window))
            logger.info(f"Drift detected at position {len(self.window)}")
        
        return drift_detected
    
    def _detect_change(self) -> bool:
        """Detect if distribution has changed."""
        if self.width < 2:
            return False
        
        # Try different split points
        n = self.width
        
        for i in range(1, n):
            # Split window at position i
            n0 = i
            n1 = n - i
            
            if n0 < 5 or n1 < 5:  # Minimum window size
                continue
            
            # Compute means
            window_list = list(self.window)
            mean0 = np.mean(window_list[:i])
            mean1 = np.mean(window_list[i:])
            
            # Compute cut value
            m = 1.0 / (1.0 / n0 + 1.0 / n1)
            
            # Hoeffding bound
            epsilon = np.sqrt((1.0 / (2.0 * m)) * np.log(4.0 / self.delta))
            
            # Check if difference is significant
            if abs(mean0 - mean1) > epsilon:
                # Drift detected - remove old data
                change_magnitude = abs(mean0 - mean1)
                
                # Store detection info
                detection = DriftDetection(
                    drift_detected=True,
                    timestamp=len(self.window),
                    window_size=self.width,
                    mean_before=mean0,
                    mean_after=mean1,
                    change_magnitude=change_magnitude
                )
                
                # Shrink window
                for _ in range(i):
                    removed = self.window.popleft()
                    self.total -= removed
                    self.width -= 1
                
                # Recalculate variance
                if self.width > 0:
                    window_list = list(self.window)
                    mean = np.mean(window_list)
                    self.variance = np.sum((np.array(window_list) - mean) ** 2)
                
                return True
        
        return False
    
    def get_window_mean(self) -> float:
        """Get current window mean."""
        if self.width == 0:
            return 0.0
        return self.total / self.width
    
    def get_window_variance(self) -> float:
        """Get current window variance."""
        if self.width <= 1:
            return 0.0
        return self.variance / (self.width - 1)
    
    def reset(self):
        """Reset detector."""
        self.window.clear()
        self.total = 0.0
        self.variance = 0.0
        self.width = 0
        logger.info("ADWIN detector reset")


class PageHinkleyDetector:
    """
    Page-Hinkley Test for drift detection.
    
    Sequential change detection with low latency.
    Good for detecting gradual drifts.
    """
    
    def __init__(
        self,
        delta: float = 0.005,
        threshold: float = 50.0,
        alpha: float = 0.9999
    ):
        """
        Initialize Page-Hinkley detector.
        
        Args:
            delta: Magnitude of changes to detect
            threshold: Detection threshold
            alpha: Forgetting factor
        """
        self.delta = delta
        self.threshold = threshold
        self.alpha = alpha
        
        # State
        self.sum = 0.0
        self.min_sum = 0.0
        self.mean = 0.0
        self.n = 0
        
        # Detection history
        self.drift_points = []
        self.total_drifts = 0
        
        logger.info(f"Page-Hinkley detector initialized: delta={delta}, threshold={threshold}")
    
    def add_element(self, value: float) -> bool:
        """
        Add new element and check for drift.
        
        Args:
            value: New data point
        
        Returns:
            True if drift detected
        """
        # Update mean
        self.n += 1
        self.mean = self.alpha * self.mean + (1 - self.alpha) * value
        
        # Update cumulative sum
        self.sum += value - self.mean - self.delta
        
        # Update minimum
        if self.sum < self.min_sum:
            self.min_sum = self.sum
        
        # Check for drift
        drift_detected = (self.sum - self.min_sum) > self.threshold
        
        if drift_detected:
            self.total_drifts += 1
            self.drift_points.append(self.n)
            
            # Reset
            self.sum = 0.0
            self.min_sum = 0.0
            
            logger.info(f"Drift detected at position {self.n}")
        
        return drift_detected
    
    def reset(self):
        """Reset detector."""
        self.sum = 0.0
        self.min_sum = 0.0
        self.mean = 0.0
        self.n = 0
        logger.info("Page-Hinkley detector reset")


class ConceptDriftMonitor:
    """
    Comprehensive concept drift monitoring for trading systems.
    
    Monitors multiple metrics and triggers retraining when drift detected.
    """
    
    def __init__(
        self,
        metrics: List[str] = None,
        use_adwin: bool = True,
        use_page_hinkley: bool = True
    ):
        """
        Initialize drift monitor.
        
        Args:
            metrics: List of metrics to monitor
            use_adwin: Use ADWIN detector
            use_page_hinkley: Use Page-Hinkley detector
        """
        if metrics is None:
            metrics = ['returns', 'sharpe', 'win_rate', 'drawdown']
        
        self.metrics = metrics
        
        # Create detectors for each metric
        self.adwin_detectors = {}
        self.ph_detectors = {}
        
        if use_adwin:
            for metric in metrics:
                self.adwin_detectors[metric] = ADWINDetector(delta=0.002)
        
        if use_page_hinkley:
            for metric in metrics:
                self.ph_detectors[metric] = PageHinkleyDetector(
                    delta=0.005,
                    threshold=50.0
                )
        
        # Drift history
        self.drift_history = []
        
        logger.info(f"Concept drift monitor initialized: {len(metrics)} metrics")
    
    def update(self, metrics_dict: dict) -> dict:
        """
        Update with new metrics and check for drift.
        
        Args:
            metrics_dict: Dictionary of metric values
        
        Returns:
            Dictionary with drift detection results
        """
        results = {
            'drift_detected': False,
            'drifted_metrics': [],
            'detector_results': {}
        }
        
        for metric in self.metrics:
            if metric not in metrics_dict:
                continue
            
            value = metrics_dict[metric]
            metric_drift = False
            
            # Check ADWIN
            if metric in self.adwin_detectors:
                adwin_drift = self.adwin_detectors[metric].add_element(value)
                if adwin_drift:
                    metric_drift = True
                    results['drifted_metrics'].append(f"{metric}_adwin")
            
            # Check Page-Hinkley
            if metric in self.ph_detectors:
                ph_drift = self.ph_detectors[metric].add_element(value)
                if ph_drift:
                    metric_drift = True
                    results['drifted_metrics'].append(f"{metric}_ph")
            
            if metric_drift:
                results['drift_detected'] = True
        
        # Store in history
        if results['drift_detected']:
            self.drift_history.append({
                'timestamp': len(self.drift_history),
                'metrics': results['drifted_metrics']
            })
            
            logger.warning(
                f"Drift detected in metrics: {results['drifted_metrics']}"
            )
        
        return results
    
    def should_retrain(self, window: int = 5) -> bool:
        """
        Check if retraining should be triggered.
        
        Args:
            window: Number of recent updates to check
        
        Returns:
            True if retraining recommended
        """
        if len(self.drift_history) < 2:
            return False
        
        # Check if multiple drifts in recent window
        recent_drifts = [
            d for d in self.drift_history[-window:]
        ]
        
        return len(recent_drifts) >= 2
    
    def get_drift_summary(self) -> dict:
        """Get summary of drift detections."""
        total_drifts = len(self.drift_history)
        
        if total_drifts == 0:
            return {
                'total_drifts': 0,
                'most_unstable_metric': None,
                'drift_rate': 0.0
            }
        
        # Count drifts per metric
        metric_counts = {}
        for drift in self.drift_history:
            for metric in drift['metrics']:
                metric_counts[metric] = metric_counts.get(metric, 0) + 1
        
        most_unstable = max(metric_counts.items(), key=lambda x: x[1]) if metric_counts else (None, 0)
        
        return {
            'total_drifts': total_drifts,
            'most_unstable_metric': most_unstable[0],
            'drift_rate': total_drifts / max(1, len(self.drift_history)),
            'metric_counts': metric_counts
        }
    
    def reset(self):
        """Reset all detectors."""
        for detector in self.adwin_detectors.values():
            detector.reset()
        for detector in self.ph_detectors.values():
            detector.reset()
        self.drift_history.clear()
        logger.info("Drift monitor reset")


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    logger.info("DRIFT DETECTION DEMO")
    print("="*80)
    
    # Test ADWIN
    logger.info("\n[1] Testing ADWIN detector...")
    adwin = ADWINDetector(delta=0.002)
    
    # Generate data with drift
    np.random.seed(42)
    data = np.concatenate([
        np.random.normal(0, 1, 100),  # Normal
        np.random.normal(2, 1, 100)   # Drift
    ])
    
    drifts = []
    for i, value in enumerate(data):
        if adwin.add_element(value):
            drifts.append(i)
    
    logger.info(f"  Detected {len(drifts)} drifts at positions: {drifts}")
    
    # Test Page-Hinkley
    logger.info("\n[2] Testing Page-Hinkley detector...")
    ph = PageHinkleyDetector(delta=0.005, threshold=50.0)
    
    drifts = []
    for i, value in enumerate(data):
        if ph.add_element(value):
            drifts.append(i)
    
    logger.info(f"  Detected {len(drifts)} drifts at positions: {drifts}")
    
    # Test Concept Drift Monitor
    logger.info("\n[3] Testing Concept Drift Monitor...")
    monitor = ConceptDriftMonitor(
        metrics=['returns', 'sharpe'],
        use_adwin=True,
        use_page_hinkley=True
    )
    
    # Simulate trading metrics
    for i in range(200):
        if i < 100:
            metrics = {
                'returns': np.random.normal(0.001, 0.01),
                'sharpe': np.random.normal(1.0, 0.2)
            }
        else:
            # Drift
            metrics = {
                'returns': np.random.normal(-0.002, 0.015),
                'sharpe': np.random.normal(0.5, 0.3)
            }
        
        result = monitor.update(metrics)
        
        if result['drift_detected']:
            logger.info(f"  Step {i}: Drift in {result['drifted_metrics']}")
    
    # Summary
    summary = monitor.get_drift_summary()
    logger.info(f"\nDrift Summary:")
    logger.info(f"  Total drifts: {summary['total_drifts']}")
    logger.info(f"  Most unstable: {summary['most_unstable_metric']}")
    logger.info(f"  Should retrain: {monitor.should_retrain()}")
    
    print("\n" + "="*80)
    logger.info("DEMO COMPLETE")
    print("="*80)

"""
Statistical Outlier Detection
=============================

Algorithms for detecting statistical outliers in market data.

Methods:
- Z-score based detection
- Modified Z-score (MAD-based)
- IQR (Interquartile Range) method
- Grubbs' test
"""

from typing import List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from enum import Enum


class OutlierMethod(Enum):
    """Statistical methods for outlier detection."""
    Z_SCORE = "z_score"
    MODIFIED_Z_SCORE = "modified_z_score"
    IQR = "iqr"
    GRUBBS = "grubbs"


@dataclass
class OutlierResult:
    """Result of outlier detection."""
    index: int
    value: float
    score: float
    is_outlier: bool
    method: OutlierMethod


class StatisticalOutlierDetector:
    """
    Detects statistical outliers in time series data.
    
    Useful for identifying:
    - Price spikes/crashes
    - Unusual volume
    - Extreme volatility moves
    """
    
    def __init__(self, method: OutlierMethod = OutlierMethod.Z_SCORE, 
                 threshold: float = 2.5):
        """
        Initialize detector.
        
        Args:
            method: Statistical method to use
            threshold: Threshold for outlier detection
        """
        self.method = method
        self.threshold = threshold
    
    def detect(self, data: List[float]) -> List[OutlierResult]:
        """
        Detect outliers in data.
        
        Args:
            data: List of values to check
            
        Returns:
            List of OutlierResult for each point
        """
        if len(data) < 10:
            return []
        
        if self.method == OutlierMethod.Z_SCORE:
            return self._z_score_detection(data)
        elif self.method == OutlierMethod.MODIFIED_Z_SCORE:
            return self._modified_z_score_detection(data)
        elif self.method == OutlierMethod.IQR:
            return self._iqr_detection(data)
        elif self.method == OutlierMethod.GRUBBS:
            return self._grubbs_detection(data)
        else:
            return []
    
    def _z_score_detection(self, data: List[float]) -> List[OutlierResult]:
        """Detect outliers using Z-score."""
        mean = np.mean(data)
        std = np.std(data)
        
        results = []
        for i, value in enumerate(data):
            if std == 0:
                z_score = 0
            else:
                z_score = abs((value - mean) / std)
            
            results.append(OutlierResult(
                index=i,
                value=value,
                score=z_score,
                is_outlier=z_score > self.threshold,
                method=OutlierMethod.Z_SCORE
            ))
        
        return results
    
    def _modified_z_score_detection(self, data: List[float]) -> List[OutlierResult]:
        """Detect outliers using modified Z-score (MAD-based)."""
        median = np.median(data)
        mad = np.median([abs(x - median) for x in data])
        
        results = []
        for i, value in enumerate(data):
            if mad == 0:
                modified_z = 0
            else:
                modified_z = 0.6745 * (value - median) / mad
            
            results.append(OutlierResult(
                index=i,
                value=value,
                score=abs(modified_z),
                is_outlier=abs(modified_z) > self.threshold,
                method=OutlierMethod.MODIFIED_Z_SCORE
            ))
        
        return results
    
    def _iqr_detection(self, data: List[float]) -> List[OutlierResult]:
        """Detect outliers using IQR method."""
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        results = []
        for i, value in enumerate(data):
            is_outlier = value < lower_bound or value > upper_bound
            distance = 0
            if value < lower_bound:
                distance = (lower_bound - value) / iqr if iqr > 0 else 0
            elif value > upper_bound:
                distance = (value - upper_bound) / iqr if iqr > 0 else 0
            
            results.append(OutlierResult(
                index=i,
                value=value,
                score=distance,
                is_outlier=is_outlier,
                method=OutlierMethod.IQR
            ))
        
        return results
    
    def _grubbs_detection(self, data: List[float]) -> List[OutlierResult]:
        """Detect outliers using Grubbs' test."""
        # Grubbs' test detects one outlier at a time
        # This is a simplified implementation
        mean = np.mean(data)
        std = np.std(data)
        n = len(data)
        
        # Critical value approximation for alpha=0.05
        critical = 1.96  # Simplified
        
        results = []
        for i, value in enumerate(data):
            if std == 0:
                g_stat = 0
            else:
                g_stat = abs(value - mean) / std
            
            results.append(OutlierResult(
                index=i,
                value=value,
                score=g_stat,
                is_outlier=g_stat > critical,
                method=OutlierMethod.GRUBBS
            ))
        
        return results
    
    def get_outliers(self, data: List[float]) -> List[OutlierResult]:
        """Get only the outliers (not all results)."""
        results = self.detect(data)
        return [r for r in results if r.is_outlier]

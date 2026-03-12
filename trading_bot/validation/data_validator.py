"""Data quality validation module for OHLCV data."""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import field
import numpy

logger = logging.getLogger(__name__)


class DataQualityValidator:
    """Validate OHLCV data quality."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize validator with configuration."""
        try:
            self.config = config or {}
            self.max_price_change_percent = self.config.get('max_price_change_percent', 10)
            self.max_volume_change_percent = self.config.get('max_volume_change_percent', 500)
            self.max_outlier_std = self.config.get('max_outlier_std', 3.0)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate_ohlcv(self, ohlcv: Dict) -> Tuple[bool, List[str]]:
        """Validate OHLCV data structure and values."""
        try:
            issues = []
        
            # Check required fields
            required = ['open', 'high', 'low', 'close', 'volume', 'time']
            for field in required:
                if field not in ohlcv:
                    issues.append(f"Missing field: {field}")
        
            if issues:
                return False, issues
        
            # Check OHLC relationships
            if ohlcv['high'] < ohlcv['low']:
                issues.append(f"High ({ohlcv['high']}) < Low ({ohlcv['low']})")
        
            if ohlcv['high'] < ohlcv['open']:
                issues.append(f"High ({ohlcv['high']}) < Open ({ohlcv['open']})")
        
            if ohlcv['high'] < ohlcv['close']:
                issues.append(f"High ({ohlcv['high']}) < Close ({ohlcv['close']})")
        
            if ohlcv['low'] > ohlcv['open']:
                issues.append(f"Low ({ohlcv['low']}) > Open ({ohlcv['open']})")
        
            if ohlcv['low'] > ohlcv['close']:
                issues.append(f"Low ({ohlcv['low']}) > Close ({ohlcv['close']})")
        
            # Check for negative values
            if ohlcv['open'] <= 0 or ohlcv['high'] <= 0 or ohlcv['low'] <= 0 or ohlcv['close'] <= 0:
                issues.append("Negative or zero prices")
        
            if ohlcv['volume'] < 0:
                issues.append("Negative volume")
        
            # Check for extreme price changes
            if ohlcv['open'] > 0:
                change_percent = abs(ohlcv['close'] - ohlcv['open']) / ohlcv['open'] * 100
                if change_percent > self.max_price_change_percent:
                    issues.append(f"Extreme price change: {change_percent:.2f}%")
        
            return len(issues) == 0, issues
        except Exception as e:
            logger.error(f"Error in validate_ohlcv: {e}")
            raise
    
    def detect_staleness(self, current_time: datetime, last_data_time: datetime, 
                        max_age_seconds: int = 60) -> Tuple[bool, Optional[str]]:
        """Detect if data is stale."""
        try:
            age = (current_time - last_data_time).total_seconds()
            if age > max_age_seconds:
                return True, f"Data is {age:.0f}s old (max {max_age_seconds}s)"
            return False, None
        except Exception as e:
            logger.error(f"Error in detect_staleness: {e}")
            raise
    
    def detect_gaps(self, timestamps: List[datetime], 
                   expected_interval_seconds: int) -> Tuple[bool, List[str]]:
        """Detect missing candles."""
        try:
            issues = []
        
            for i in range(1, len(timestamps)):
                actual_gap = (timestamps[i] - timestamps[i-1]).total_seconds()
                if actual_gap > expected_interval_seconds * 1.5:
                    issues.append(f"Gap detected: {actual_gap}s (expected {expected_interval_seconds}s)")
        
            return len(issues) == 0, issues
        except Exception as e:
            logger.error(f"Error in detect_gaps: {e}")
            raise
    
    def detect_outliers(self, prices: List[float], 
                       threshold_std: Optional[float] = None) -> Tuple[bool, List[int]]:
        """Detect outlier prices using Z-score."""
        try:
            if threshold_std is None:
                threshold_std = self.max_outlier_std
        
            if len(prices) < 2:
                return True, []
        
            mean = np.mean(prices)
            std = np.std(prices)
        
            outliers = []
            for i, price in enumerate(prices):
                z_score = abs((price - mean) / std) if std > 0 else 0
                if z_score > threshold_std:
                    outliers.append(i)
        
            return len(outliers) == 0, outliers
        except Exception as e:
            logger.error(f"Error in detect_outliers: {e}")
            raise
    
    def detect_duplicates(self, timestamps: List[datetime]) -> Tuple[bool, List[int]]:
        """Detect duplicate timestamps."""
        try:
            duplicates = []
            seen = set()
        
            for i, ts in enumerate(timestamps):
                if ts in seen:
                    duplicates.append(i)
                seen.add(ts)
        
            return len(duplicates) == 0, duplicates
        except Exception as e:
            logger.error(f"Error in detect_duplicates: {e}")
            raise
    
    def validate_batch(self, ohlcv_list: List[Dict]) -> Dict:
        """Validate a batch of OHLCV data."""
        try:
            results = {
                'total': len(ohlcv_list),
                'valid': 0,
                'invalid': 0,
                'issues': [],
                'outliers': [],
                'gaps': [],
                'duplicates': []
            }
        
            for i, ohlcv in enumerate(ohlcv_list):
                is_valid, issues = self.validate_ohlcv(ohlcv)
                if is_valid:
                    results['valid'] += 1
                else:
                    results['invalid'] += 1
                    results['issues'].append({'index': i, 'issues': issues})
        
            # Check for gaps
            if len(ohlcv_list) > 1:
                timestamps = [ohlcv.get('time') for ohlcv in ohlcv_list if 'time' in ohlcv]
                if timestamps:
                    is_valid, gap_issues = self.detect_gaps(timestamps, 60)
                    if not is_valid:
                        results['gaps'] = gap_issues
        
            # Check for outliers
            closes = [ohlcv.get('close', 0) for ohlcv in ohlcv_list if 'close' in ohlcv]
            if closes:
                is_valid, outlier_indices = self.detect_outliers(closes)
                if not is_valid:
                    results['outliers'] = outlier_indices
        
            return results
        except Exception as e:
            logger.error(f"Error in validate_batch: {e}")
            raise


class DataQualityMonitor:
    """Monitor data quality in real-time."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize monitor."""
        try:
            self.validator = DataQualityValidator(config)
            self.last_data_time = None
            self.data_history = []
            self.max_history = config.get('max_history', 1000) if config else 1000
            self.quality_score = 100.0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def process_data(self, ohlcv: Dict) -> Dict:
        """Process and validate incoming data."""
        try:
            result = {
                'timestamp': datetime.now(),
                'valid': False,
                'quality_score': 0,
                'issues': [],
                'warnings': []
            }
        
            # Validate OHLCV
            is_valid, issues = self.validator.validate_ohlcv(ohlcv)
            result['valid'] = is_valid
            result['issues'] = issues
        
            # Check staleness
            if self.last_data_time:
                is_stale, stale_msg = self.validator.detect_staleness(
                    datetime.now(), self.last_data_time, 60
                )
                if is_stale:
                    result['warnings'].append(stale_msg)
        
            # Update history
            self.data_history.append(ohlcv)
            if len(self.data_history) > self.max_history:
                self.data_history.pop(0)
        
            # Calculate quality score
            self.quality_score = 100.0 - (len(issues) * 10) - (len(result['warnings']) * 5)
            self.quality_score = max(0, min(100, self.quality_score))
            result['quality_score'] = self.quality_score
        
            self.last_data_time = datetime.now()
        
            return result
        except Exception as e:
            logger.error(f"Error in process_data: {e}")
            raise
    
    def get_quality_report(self) -> Dict:
        """Get data quality report."""
        try:
            if not self.data_history:
                return {'status': 'no_data', 'quality_score': 0}
        
            batch_result = self.validator.validate_batch(self.data_history[-100:])
        
            return {
                'status': 'ok' if self.quality_score > 80 else 'degraded',
                'quality_score': self.quality_score,
                'valid_records': batch_result['valid'],
                'invalid_records': batch_result['invalid'],
                'total_records': batch_result['total'],
                'issues': batch_result['issues'][:5],  # Last 5 issues
                'gaps': len(batch_result['gaps']),
                'outliers': len(batch_result['outliers'])
            }
        except Exception as e:
            logger.error(f"Error in get_quality_report: {e}")
            raise

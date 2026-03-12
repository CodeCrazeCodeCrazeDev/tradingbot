"""
Data quality validation system
Ensures data integrity before trading decisions
"""

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy
import pandas

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""
    CRITICAL = "critical"  # Trading must stop
    WARNING = "warning"    # Log but continue
    INFO = "info"          # Informational only


class DataQualityIssue(Enum):
    """Types of data quality issues"""
    MISSING_DATA = "missing_data"
    STALE_DATA = "stale_data"
    OUTLIER = "outlier"
    INCONSISTENT = "inconsistent"
    DUPLICATE = "duplicate"
    INVALID_RANGE = "invalid_range"
    SEQUENCE_GAP = "sequence_gap"


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    level: ValidationLevel
    issues: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_issue(self, issue_type: DataQualityIssue, description: str, 
                  level: ValidationLevel = ValidationLevel.WARNING, **kwargs):
        """Add validation issue"""
        self.issues.append({
            'type': issue_type.value,
            'description': description,
            'level': level.value,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        })
        
        if level == ValidationLevel.CRITICAL:
            self.is_valid = False


class DataQualityValidator:
    """
    Comprehensive data quality validation
    Checks for missing data, outliers, staleness, consistency
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Validation thresholds
        self.max_staleness_seconds = self.config.get('max_staleness_seconds', 60)
        self.outlier_std_threshold = self.config.get('outlier_std_threshold', 5.0)
        self.max_missing_pct = self.config.get('max_missing_pct', 5.0)
        self.price_change_threshold = self.config.get('price_change_threshold', 0.1)  # 10%
        
        self.stats = {
            'validations_performed': 0,
            'critical_issues': 0,
            'warnings': 0,
            'last_validation': None
        }
    
    def validate_market_data(self, data: pd.DataFrame, symbol: str) -> ValidationResult:
        """
        Validate market data DataFrame
        
        Args:
            data: DataFrame with OHLCV data
            symbol: Trading symbol
            
        Returns:
            ValidationResult with issues found
        """
        result = ValidationResult(is_valid=True, level=ValidationLevel.INFO)
        self.stats['validations_performed'] += 1
        
        # Check for empty data
        if data is None or len(data) == 0:
            result.add_issue(
                DataQualityIssue.MISSING_DATA,
                f"No data available for {symbol}",
                ValidationLevel.CRITICAL
            )
            self.stats['critical_issues'] += 1
            return result
        
        # Check required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            result.add_issue(
                DataQualityIssue.MISSING_DATA,
                f"Missing required columns: {missing_cols}",
                ValidationLevel.CRITICAL,
                missing_columns=missing_cols
            )
            self.stats['critical_issues'] += 1
            return result
        
        # Check for missing values
        missing_pct = (data[required_cols].isnull().sum() / len(data) * 100)
        for col, pct in missing_pct.items():
            if pct > self.max_missing_pct:
                result.add_issue(
                    DataQualityIssue.MISSING_DATA,
                    f"{col} has {pct:.2f}% missing values",
                    ValidationLevel.CRITICAL if pct > 20 else ValidationLevel.WARNING,
                    column=col,
                    missing_percentage=pct
                )
                if pct > 20:
                    self.stats['critical_issues'] += 1
                else:
                    self.stats['warnings'] += 1
        
        # Check data staleness
        if 'timestamp' in data.columns or isinstance(data.index, pd.DatetimeIndex):
            latest_time = data.index[-1] if isinstance(data.index, pd.DatetimeIndex) else pd.to_datetime(data['timestamp'].iloc[-1])
            staleness = (datetime.now() - latest_time).total_seconds()
            
            if staleness > self.max_staleness_seconds:
                result.add_issue(
                    DataQualityIssue.STALE_DATA,
                    f"Data is {staleness:.0f} seconds old",
                    ValidationLevel.CRITICAL if staleness > 300 else ValidationLevel.WARNING,
                    staleness_seconds=staleness
                )
                if staleness > 300:
                    self.stats['critical_issues'] += 1
                else:
                    self.stats['warnings'] += 1
        
        # Check for outliers in prices
        for col in ['open', 'high', 'low', 'close']:
            if col in data.columns:
                outliers = self._detect_outliers(data[col])
                if len(outliers) > 0:
                    result.add_issue(
                        DataQualityIssue.OUTLIER,
                        f"{col} has {len(outliers)} outliers",
                        ValidationLevel.WARNING,
                        column=col,
                        outlier_count=len(outliers),
                        outlier_indices=outliers.tolist()
                    )
                    self.stats['warnings'] += 1
        
        # Check OHLC consistency
        inconsistent = self._check_ohlc_consistency(data)
        if len(inconsistent) > 0:
            result.add_issue(
                DataQualityIssue.INCONSISTENT,
                f"Found {len(inconsistent)} OHLC inconsistencies",
                ValidationLevel.WARNING,
                inconsistent_rows=inconsistent
            )
            self.stats['warnings'] += 1
        
        # Check for duplicates
        if 'timestamp' in data.columns:
            duplicates = data['timestamp'].duplicated().sum()
            if duplicates > 0:
                result.add_issue(
                    DataQualityIssue.DUPLICATE,
                    f"Found {duplicates} duplicate timestamps",
                    ValidationLevel.WARNING,
                    duplicate_count=duplicates
                )
                self.stats['warnings'] += 1
        
        # Check for extreme price changes
        if 'close' in data.columns and len(data) > 1:
            price_changes = data['close'].pct_change().abs()
            extreme_changes = price_changes[price_changes > self.price_change_threshold]
            
            if len(extreme_changes) > 0:
                result.add_issue(
                    DataQualityIssue.OUTLIER,
                    f"Found {len(extreme_changes)} extreme price changes",
                    ValidationLevel.WARNING,
                    max_change=extreme_changes.max(),
                    extreme_indices=extreme_changes.index.tolist()
                )
                self.stats['warnings'] += 1
        
        # Check volume validity
        if 'volume' in data.columns:
            if (data['volume'] < 0).any():
                result.add_issue(
                    DataQualityIssue.INVALID_RANGE,
                    "Negative volume detected",
                    ValidationLevel.CRITICAL
                )
                self.stats['critical_issues'] += 1
            
            if (data['volume'] == 0).sum() / len(data) > 0.5:
                result.add_issue(
                    DataQualityIssue.MISSING_DATA,
                    "More than 50% of volume data is zero",
                    ValidationLevel.WARNING
                )
                self.stats['warnings'] += 1
        
        self.stats['last_validation'] = datetime.now()
        return result
    
    def _detect_outliers(self, series: pd.Series) -> np.ndarray:
        """Detect outliers using z-score method"""
        if len(series) < 3:
            return np.array([])
        
        z_scores = np.abs((series - series.mean()) / series.std())
        return np.where(z_scores > self.outlier_std_threshold)[0]
    
    def _check_ohlc_consistency(self, data: pd.DataFrame) -> List[int]:
        """Check OHLC relationships (high >= low, etc.)"""
        inconsistent = []
        
        if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
            # High should be >= Low
            mask1 = data['high'] < data['low']
            
            # High should be >= Open and Close
            mask2 = (data['high'] < data['open']) | (data['high'] < data['close'])
            
            # Low should be <= Open and Close
            mask3 = (data['low'] > data['open']) | (data['low'] > data['close'])
            
            inconsistent = data[mask1 | mask2 | mask3].index.tolist()
        
        return inconsistent
    
    def validate_signal(self, signal: Dict[str, Any]) -> ValidationResult:
        """
        Validate trading signal
        
        Args:
            signal: Trading signal dictionary
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, level=ValidationLevel.INFO)
        
        # Check required fields
        required_fields = ['symbol', 'direction', 'confidence', 'timestamp']
        missing = [f for f in required_fields if f not in signal]
        
        if missing:
            result.add_issue(
                DataQualityIssue.MISSING_DATA,
                f"Signal missing required fields: {missing}",
                ValidationLevel.CRITICAL,
                missing_fields=missing
            )
            self.stats['critical_issues'] += 1
            return result
        
        # Validate confidence range
        confidence = signal.get('confidence', 0)
        if not 0 <= confidence <= 1:
            result.add_issue(
                DataQualityIssue.INVALID_RANGE,
                f"Confidence {confidence} outside valid range [0, 1]",
                ValidationLevel.CRITICAL,
                confidence=confidence
            )
            self.stats['critical_issues'] += 1
        
        # Validate direction
        direction = signal.get('direction', '').upper()
        if direction not in ['BUY', 'SELL', 'LONG', 'SHORT']:
            result.add_issue(
                DataQualityIssue.INVALID_RANGE,
                f"Invalid direction: {direction}",
                ValidationLevel.CRITICAL,
                direction=direction
            )
            self.stats['critical_issues'] += 1
        
        # Check signal staleness
        if 'timestamp' in signal:
            try:
                signal_time = pd.to_datetime(signal['timestamp'])
                staleness = (datetime.now() - signal_time).total_seconds()
                
                if staleness > 60:  # Signal older than 1 minute
                    result.add_issue(
                        DataQualityIssue.STALE_DATA,
                        f"Signal is {staleness:.0f} seconds old",
                        ValidationLevel.WARNING,
                        staleness_seconds=staleness
                    )
                    self.stats['warnings'] += 1
            except Exception:
                result.add_issue(
                    DataQualityIssue.INVALID_RANGE,
                    "Invalid timestamp format",
                    ValidationLevel.WARNING
                )
                self.stats['warnings'] += 1
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            **self.stats,
            'config': {
                'max_staleness_seconds': self.max_staleness_seconds,
                'outlier_std_threshold': self.outlier_std_threshold,
                'max_missing_pct': self.max_missing_pct,
                'price_change_threshold': self.price_change_threshold
            }
        }


class DataQualityMonitor:
    """
    Continuous data quality monitoring
    Tracks quality metrics over time
    """
    
    def __init__(self, validator: DataQualityValidator):
        self.validator = validator
        self.history: List[ValidationResult] = []
        self.max_history = 1000
        
    def monitor(self, data: pd.DataFrame, symbol: str) -> ValidationResult:
        """Monitor data quality and track history"""
        result = self.validator.validate_market_data(data, symbol)
        
        self.history.append(result)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        return result
    
    def get_quality_score(self) -> float:
        """
        Calculate overall data quality score (0-100)
        Based on recent validation history
        """
        if not self.history:
            return 100.0
        
        recent = self.history[-100:]  # Last 100 validations
        
        total_issues = sum(len(r.issues) for r in recent)
        critical_issues = sum(
            len([i for i in r.issues if i['level'] == ValidationLevel.CRITICAL.value])
            for r in recent
        )
        
        # Score calculation
        score = 100.0
        score -= (critical_issues * 10)  # -10 per critical issue
        score -= (total_issues * 2)      # -2 per any issue
        
        return max(0.0, min(100.0, score))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get quality monitoring summary"""
        if not self.history:
            return {'quality_score': 100.0, 'total_validations': 0}
        
        recent = self.history[-100:]
        
        return {
            'quality_score': self.get_quality_score(),
            'total_validations': len(self.history),
            'recent_validations': len(recent),
            'total_issues': sum(len(r.issues) for r in recent),
            'critical_issues': sum(
                len([i for i in r.issues if i['level'] == ValidationLevel.CRITICAL.value])
                for r in recent
            ),
            'warnings': sum(
                len([i for i in r.issues if i['level'] == ValidationLevel.WARNING.value])
                for r in recent
            ),
            'validator_stats': self.validator.get_stats()
        }

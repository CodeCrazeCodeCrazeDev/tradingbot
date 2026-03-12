"""
Data Validation Pipeline

Comprehensive data validation for trading systems:
- OHLCV validation
- Staleness detection
- Gap handling
- Outlier detection
- Data quality scoring
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import deque
import numpy

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation issue severity"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DataQuality(Enum):
    """Data quality classification"""
    EXCELLENT = "EXCELLENT"  # 95-100%
    GOOD = "GOOD"  # 80-95%
    ACCEPTABLE = "ACCEPTABLE"  # 60-80%
    POOR = "POOR"  # 40-60%
    UNUSABLE = "UNUSABLE"  # <40%


@dataclass
class ValidationIssue:
    """Single validation issue"""
    field: str
    message: str
    severity: ValidationSeverity
    value: Any = None
    expected: Any = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationResult:
    """Result of data validation"""
    valid: bool
    quality: DataQuality
    score: float  # 0-100
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)
        # Recalculate validity
        self.valid = not any(i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] for i in self.issues)


@dataclass
class OHLCVData:
    """OHLCV data structure"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str = "1H"


class OHLCVValidator:
    """
    OHLCV data validator with comprehensive checks.
    """
    
    def __init__(
        self,
        max_price_change: float = 0.10,  # 10% max single bar change
        min_volume: float = 0,
        max_staleness_seconds: int = 300,
        outlier_std_threshold: float = 4.0
    ):
        self.max_price_change = max_price_change
        self.min_volume = min_volume
        self.max_staleness_seconds = max_staleness_seconds
        self.outlier_std_threshold = outlier_std_threshold
        
        # Historical data for outlier detection
        self.price_history: Dict[str, deque] = {}
        self.volume_history: Dict[str, deque] = {}
    
    def validate(self, data: Union[OHLCVData, Dict]) -> ValidationResult:
        """
        Validate OHLCV data.
        
        Args:
            data: OHLCV data to validate
        
        Returns:
            ValidationResult with issues and quality score
        """
        result = ValidationResult(valid=True, quality=DataQuality.EXCELLENT, score=100.0)
        
        # Convert dict to OHLCVData if needed
        if isinstance(data, dict):
            try:
                data = OHLCVData(
                    symbol=data.get('symbol', 'UNKNOWN'),
                    timestamp=data.get('timestamp', datetime.now()),
                    open=float(data.get('open', 0)),
                    high=float(data.get('high', 0)),
                    low=float(data.get('low', 0)),
                    close=float(data.get('close', 0)),
                    volume=float(data.get('volume', 0)),
                    timeframe=data.get('timeframe', '1H')
                )
            except (ValueError, TypeError) as e:
                result.add_issue(ValidationIssue(
                    field='data',
                    message=f"Invalid data format: {e}",
                    severity=ValidationSeverity.CRITICAL
                ))
                result.score = 0
                result.quality = DataQuality.UNUSABLE
                return result
        
        # Run all validations
        self._validate_completeness(data, result)
        self._validate_ohlc_relationships(data, result)
        self._validate_price_range(data, result)
        self._validate_volume(data, result)
        self._validate_staleness(data, result)
        self._validate_outliers(data, result)
        
        # Calculate final score
        result.score = self._calculate_score(result)
        result.quality = self._score_to_quality(result.score)
        result.valid = result.score >= 40  # Minimum acceptable
        
        # Update history
        self._update_history(data)
        
        return result
    
    def _validate_completeness(self, data: OHLCVData, result: ValidationResult):
        """Check for missing or zero values"""
        if data.open <= 0:
            result.add_issue(ValidationIssue(
                field='open',
                message="Open price is zero or negative",
                severity=ValidationSeverity.ERROR,
                value=data.open
            ))
        
        if data.high <= 0:
            result.add_issue(ValidationIssue(
                field='high',
                message="High price is zero or negative",
                severity=ValidationSeverity.ERROR,
                value=data.high
            ))
        
        if data.low <= 0:
            result.add_issue(ValidationIssue(
                field='low',
                message="Low price is zero or negative",
                severity=ValidationSeverity.ERROR,
                value=data.low
            ))
        
        if data.close <= 0:
            result.add_issue(ValidationIssue(
                field='close',
                message="Close price is zero or negative",
                severity=ValidationSeverity.ERROR,
                value=data.close
            ))
    
    def _validate_ohlc_relationships(self, data: OHLCVData, result: ValidationResult):
        """Validate OHLC price relationships"""
        # High must be highest
        if data.high < data.open:
            result.add_issue(ValidationIssue(
                field='high',
                message="High is less than Open",
                severity=ValidationSeverity.ERROR,
                value=data.high,
                expected=f">= {data.open}"
            ))
        
        if data.high < data.close:
            result.add_issue(ValidationIssue(
                field='high',
                message="High is less than Close",
                severity=ValidationSeverity.ERROR,
                value=data.high,
                expected=f">= {data.close}"
            ))
        
        if data.high < data.low:
            result.add_issue(ValidationIssue(
                field='high',
                message="High is less than Low",
                severity=ValidationSeverity.CRITICAL,
                value=data.high,
                expected=f">= {data.low}"
            ))
        
        # Low must be lowest
        if data.low > data.open:
            result.add_issue(ValidationIssue(
                field='low',
                message="Low is greater than Open",
                severity=ValidationSeverity.ERROR,
                value=data.low,
                expected=f"<= {data.open}"
            ))
        
        if data.low > data.close:
            result.add_issue(ValidationIssue(
                field='low',
                message="Low is greater than Close",
                severity=ValidationSeverity.ERROR,
                value=data.low,
                expected=f"<= {data.close}"
            ))
    
    def _validate_price_range(self, data: OHLCVData, result: ValidationResult):
        """Validate price change is within acceptable range"""
        if data.open > 0:
            # Check high-low range
            range_pct = (data.high - data.low) / data.open
            if range_pct > self.max_price_change * 2:
                result.add_issue(ValidationIssue(
                    field='range',
                    message=f"Price range ({range_pct:.2%}) exceeds maximum ({self.max_price_change * 2:.2%})",
                    severity=ValidationSeverity.WARNING,
                    value=range_pct
                ))
            
            # Check open-close change
            change_pct = abs(data.close - data.open) / data.open
            if change_pct > self.max_price_change:
                result.add_issue(ValidationIssue(
                    field='change',
                    message=f"Price change ({change_pct:.2%}) exceeds maximum ({self.max_price_change:.2%})",
                    severity=ValidationSeverity.WARNING,
                    value=change_pct
                ))
    
    def _validate_volume(self, data: OHLCVData, result: ValidationResult):
        """Validate volume"""
        if data.volume < 0:
            result.add_issue(ValidationIssue(
                field='volume',
                message="Negative volume",
                severity=ValidationSeverity.CRITICAL,
                value=data.volume
            ))
        elif data.volume < self.min_volume:
            result.add_issue(ValidationIssue(
                field='volume',
                message=f"Volume ({data.volume}) below minimum ({self.min_volume})",
                severity=ValidationSeverity.WARNING,
                value=data.volume
            ))
        elif data.volume == 0:
            result.add_issue(ValidationIssue(
                field='volume',
                message="Zero volume",
                severity=ValidationSeverity.INFO,
                value=data.volume
            ))
    
    def _validate_staleness(self, data: OHLCVData, result: ValidationResult):
        """Check data freshness"""
        age = (datetime.now() - data.timestamp).total_seconds()
        
        if age > self.max_staleness_seconds:
            severity = ValidationSeverity.WARNING
            if age > self.max_staleness_seconds * 2:
                severity = ValidationSeverity.ERROR
            if age > self.max_staleness_seconds * 4:
                severity = ValidationSeverity.CRITICAL
            
            result.add_issue(ValidationIssue(
                field='timestamp',
                message=f"Data is {age:.0f}s old (max: {self.max_staleness_seconds}s)",
                severity=severity,
                value=age
            ))
        
        # Check for future timestamps
        if data.timestamp > datetime.now() + timedelta(seconds=60):
            result.add_issue(ValidationIssue(
                field='timestamp',
                message="Timestamp is in the future",
                severity=ValidationSeverity.ERROR,
                value=data.timestamp
            ))
    
    def _validate_outliers(self, data: OHLCVData, result: ValidationResult):
        """Detect statistical outliers"""
        symbol = data.symbol
        
        # Initialize history if needed
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=100)
            self.volume_history[symbol] = deque(maxlen=100)
        
        # Check price outlier
        if len(self.price_history[symbol]) >= 10:
            prices = list(self.price_history[symbol])
            mean_price = np.mean(prices)
            std_price = np.std(prices)
            
            if std_price > 0:
                z_score = abs(data.close - mean_price) / std_price
                if z_score > self.outlier_std_threshold:
                    result.add_issue(ValidationIssue(
                        field='close',
                        message=f"Price outlier detected (z-score: {z_score:.2f})",
                        severity=ValidationSeverity.WARNING,
                        value=data.close,
                        expected=f"~{mean_price:.5f}"
                    ))
        
        # Check volume outlier
        if len(self.volume_history[symbol]) >= 10:
            volumes = list(self.volume_history[symbol])
            mean_vol = np.mean(volumes)
            std_vol = np.std(volumes)
            
            if std_vol > 0 and data.volume > 0:
                z_score = abs(data.volume - mean_vol) / std_vol
                if z_score > self.outlier_std_threshold:
                    result.add_issue(ValidationIssue(
                        field='volume',
                        message=f"Volume outlier detected (z-score: {z_score:.2f})",
                        severity=ValidationSeverity.INFO,
                        value=data.volume,
                        expected=f"~{mean_vol:.0f}"
                    ))
    
    def _update_history(self, data: OHLCVData):
        """Update historical data for outlier detection"""
        symbol = data.symbol
        
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=100)
            self.volume_history[symbol] = deque(maxlen=100)
        
        self.price_history[symbol].append(data.close)
        self.volume_history[symbol].append(data.volume)
    
    def _calculate_score(self, result: ValidationResult) -> float:
        """Calculate quality score based on issues"""
        score = 100.0
        
        for issue in result.issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                score -= 40
            elif issue.severity == ValidationSeverity.ERROR:
                score -= 20
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 10
            elif issue.severity == ValidationSeverity.INFO:
                score -= 2
        
        return max(0, score)
    
    def _score_to_quality(self, score: float) -> DataQuality:
        """Convert score to quality classification"""
        if score >= 95:
            return DataQuality.EXCELLENT
        elif score >= 80:
            return DataQuality.GOOD
        elif score >= 60:
            return DataQuality.ACCEPTABLE
        elif score >= 40:
            return DataQuality.POOR
        else:
            return DataQuality.UNUSABLE


class GapDetector:
    """
    Detect and handle gaps in time series data.
    """
    
    def __init__(self, expected_interval_seconds: int = 3600):
        """
        Args:
            expected_interval_seconds: Expected time between data points
        """
        self.expected_interval = expected_interval_seconds
        self.last_timestamp: Dict[str, datetime] = {}
    
    def check_gap(self, symbol: str, timestamp: datetime) -> Optional[Dict]:
        """
        Check for gap since last data point.
        
        Returns:
            Gap info dict or None if no gap
        """
        if symbol not in self.last_timestamp:
            self.last_timestamp[symbol] = timestamp
            return None
        
        last = self.last_timestamp[symbol]
        gap_seconds = (timestamp - last).total_seconds()
        
        # Allow 10% tolerance
        if gap_seconds > self.expected_interval * 1.1:
            gap_info = {
                'symbol': symbol,
                'start': last,
                'end': timestamp,
                'gap_seconds': gap_seconds,
                'expected_seconds': self.expected_interval,
                'missing_bars': int(gap_seconds / self.expected_interval) - 1
            }
            
            self.last_timestamp[symbol] = timestamp
            return gap_info
        
        self.last_timestamp[symbol] = timestamp
        return None
    
    def fill_gap(self, gap_info: Dict, fill_method: str = 'forward') -> List[OHLCVData]:
        """
        Generate fill data for gap.
        
        Args:
            gap_info: Gap information from check_gap
            fill_method: 'forward', 'backward', 'interpolate'
        
        Returns:
            List of fill data points
        """
        fills = []
        
        # This is a placeholder - in production, you'd fetch historical data
        # or use proper interpolation
        
        return fills


class DataQuarantineManager:
    """
    Quarantine suspicious data for review.
    """
    
    def __init__(self, max_quarantine_size: int = 1000):
        self.quarantine: deque = deque(maxlen=max_quarantine_size)
        self.quarantine_stats = {
            'total_quarantined': 0,
            'by_reason': {}
        }
    
    def quarantine_data(self, data: Any, reason: str, validation_result: ValidationResult):
        """Add data to quarantine"""
        entry = {
            'data': data,
            'reason': reason,
            'validation_result': validation_result,
            'timestamp': datetime.now()
        }
        
        self.quarantine.append(entry)
        self.quarantine_stats['total_quarantined'] += 1
        self.quarantine_stats['by_reason'][reason] = self.quarantine_stats['by_reason'].get(reason, 0) + 1
        
        logger.warning(f"Data quarantined: {reason}")
    
    def get_quarantine_summary(self) -> Dict:
        """Get quarantine statistics"""
        return {
            'current_size': len(self.quarantine),
            'total_quarantined': self.quarantine_stats['total_quarantined'],
            'by_reason': self.quarantine_stats['by_reason']
        }
    
    def review_quarantine(self) -> List[Dict]:
        """Get quarantined items for review"""
        return list(self.quarantine)
    
    def release_from_quarantine(self, index: int) -> Optional[Dict]:
        """Release item from quarantine"""
        if 0 <= index < len(self.quarantine):
            # Convert deque to list, remove item, convert back
            items = list(self.quarantine)
            released = items.pop(index)
            self.quarantine = deque(items, maxlen=self.quarantine.maxlen)
            return released
        return None


class DataValidationPipeline:
    """
    Complete data validation pipeline.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        
        self.ohlcv_validator = OHLCVValidator(
            max_price_change=config.get('max_price_change', 0.10),
            min_volume=config.get('min_volume', 0),
            max_staleness_seconds=config.get('max_staleness_seconds', 300),
            outlier_std_threshold=config.get('outlier_std_threshold', 4.0)
        )
        
        self.gap_detector = GapDetector(
            expected_interval_seconds=config.get('expected_interval_seconds', 3600)
        )
        
        self.quarantine = DataQuarantineManager(
            max_quarantine_size=config.get('max_quarantine_size', 1000)
        )
        
        # Statistics
        self.stats = {
            'total_validated': 0,
            'passed': 0,
            'failed': 0,
            'quarantined': 0,
            'gaps_detected': 0
        }
    
    def validate(self, data: Union[OHLCVData, Dict]) -> Tuple[bool, ValidationResult]:
        """
        Run complete validation pipeline.
        
        Returns:
            (is_valid, validation_result)
        """
        self.stats['total_validated'] += 1
        
        # OHLCV validation
        result = self.ohlcv_validator.validate(data)
        
        # Gap detection
        symbol = data.symbol if isinstance(data, OHLCVData) else data.get('symbol', 'UNKNOWN')
        timestamp = data.timestamp if isinstance(data, OHLCVData) else data.get('timestamp', datetime.now())
        
        gap = self.gap_detector.check_gap(symbol, timestamp)
        if gap:
            self.stats['gaps_detected'] += 1
            result.add_issue(ValidationIssue(
                field='timestamp',
                message=f"Gap detected: {gap['missing_bars']} missing bars",
                severity=ValidationSeverity.WARNING,
                value=gap
            ))
            result.metadata['gap'] = gap
        
        # Quarantine if needed
        if result.quality == DataQuality.UNUSABLE:
            self.quarantine.quarantine_data(data, "Unusable quality", result)
            self.stats['quarantined'] += 1
        
        # Update stats
        if result.valid:
            self.stats['passed'] += 1
        else:
            self.stats['failed'] += 1
        
        return result.valid, result
    
    def get_stats(self) -> Dict:
        """Get pipeline statistics"""
        return {
            **self.stats,
            'pass_rate': self.stats['passed'] / self.stats['total_validated'] if self.stats['total_validated'] > 0 else 0,
            'quarantine': self.quarantine.get_quarantine_summary()
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create pipeline
    pipeline = DataValidationPipeline({
        'max_price_change': 0.05,
        'max_staleness_seconds': 60
    })
    
    # Test data
    test_cases = [
        # Good data
        {
            'symbol': 'EURUSD',
            'timestamp': datetime.now(),
            'open': 1.1000,
            'high': 1.1010,
            'low': 1.0990,
            'close': 1.1005,
            'volume': 10000
        },
        # Bad: High < Low
        {
            'symbol': 'EURUSD',
            'timestamp': datetime.now(),
            'open': 1.1000,
            'high': 1.0980,  # Wrong!
            'low': 1.1020,   # Wrong!
            'close': 1.1005,
            'volume': 10000
        },
        # Stale data
        {
            'symbol': 'EURUSD',
            'timestamp': datetime.now() - timedelta(minutes=10),
            'open': 1.1000,
            'high': 1.1010,
            'low': 1.0990,
            'close': 1.1005,
            'volume': 10000
        }
    ]
    
    print("\n" + "="*60)
    logger.info("DATA VALIDATION PIPELINE TEST")
    print("="*60)
    
    for i, data in enumerate(test_cases):
        valid, result = pipeline.validate(data)
        logger.info(f"\nTest Case {i+1}:")
        logger.info(f"  Valid: {valid}")
        logger.info(f"  Quality: {result.quality.value}")
        logger.info(f"  Score: {result.score:.1f}")
        if result.issues:
            logger.info(f"  Issues:")
            for issue in result.issues:
                logger.info(f"    - [{issue.severity.value}] {issue.field}: {issue.message}")
    
    logger.info(f"\n\nPipeline Stats: {pipeline.get_stats()}")
    print("="*60)

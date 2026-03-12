"""
Data Validator - Answers Q71-Q80, Q62, Q91-Q100
===============================================

Critical Question Q71: How do you detect price spikes that are data errors vs. real market events?
Critical Question Q62: How do you detect when a data source is delivering stale data?
Critical Question Q91: How do you detect bit-level corruption in stored data?

This module provides:
1. Real-time data validation
2. Price spike detection (error vs. real)
3. Staleness detection
4. Data corruption detection
5. Quality scoring
6. Automatic quarantine of bad data
"""

import logging
import threading
import hashlib
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class DataQualityLevel(Enum):
    """Data quality classification"""
    EXCELLENT = "excellent"    # All checks pass
    GOOD = "good"              # Minor issues
    ACCEPTABLE = "acceptable"  # Some issues but usable
    POOR = "poor"              # Significant issues
    UNUSABLE = "unusable"      # Do not use
    QUARANTINED = "quarantined"  # Isolated for review


class DataIssueType(Enum):
    """Types of data issues"""
    STALE = "stale"
    PRICE_SPIKE = "price_spike"
    VOLUME_ANOMALY = "volume_anomaly"
    SPREAD_INVERTED = "spread_inverted"
    SPREAD_EXCESSIVE = "spread_excessive"
    TIMESTAMP_INVALID = "timestamp_invalid"
    TIMESTAMP_FUTURE = "timestamp_future"
    TIMESTAMP_OLD = "timestamp_old"
    MISSING_FIELD = "missing_field"
    INVALID_VALUE = "invalid_value"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    SEQUENCE_GAP = "sequence_gap"
    DUPLICATE = "duplicate"
    ECONOMICALLY_IMPOSSIBLE = "economically_impossible"


@dataclass
class DataIssue:
    """Detected data issue"""
    issue_type: DataIssueType
    severity: str  # 'critical', 'warning', 'info'
    field: str
    expected: Any
    actual: Any
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'issue_type': self.issue_type.value,
            'severity': self.severity,
            'field': self.field,
            'expected': str(self.expected),
            'actual': str(self.actual),
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class DataQualityReport:
    """Comprehensive data quality report"""
    timestamp: datetime
    symbol: str
    data_type: str  # 'tick', 'bar', 'orderbook'
    quality_level: DataQualityLevel
    quality_score: float  # 0-100
    issues: List[DataIssue]
    is_usable: bool
    quarantined: bool
    validation_time_ms: float
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'data_type': self.data_type,
            'quality_level': self.quality_level.value,
            'quality_score': self.quality_score,
            'issues': [i.to_dict() for i in self.issues],
            'is_usable': self.is_usable,
            'quarantined': self.quarantined,
            'validation_time_ms': self.validation_time_ms
        }


class DataValidator:
    """
    Comprehensive data validation system.
    
    Addresses critical questions:
    - Q71: Price spike detection (error vs. real)
    - Q62: Staleness detection
    - Q91-Q100: Corruption detection
    
    Features:
    - Real-time validation
    - Historical context for anomaly detection
    - Automatic quarantine
    - Quality scoring
    - Configurable thresholds
    """
    
    # Default thresholds
    DEFAULT_MAX_PRICE_CHANGE_PCT = 0.10  # 10% max single tick change
    DEFAULT_MAX_STALENESS_SECONDS = 5
    DEFAULT_MAX_SPREAD_PCT = 0.05  # 5% max spread
    DEFAULT_MIN_VOLUME = 0
    
    def __init__(
        self,
        max_price_change_pct: float = DEFAULT_MAX_PRICE_CHANGE_PCT,
        max_staleness_seconds: float = DEFAULT_MAX_STALENESS_SECONDS,
        max_spread_pct: float = DEFAULT_MAX_SPREAD_PCT,
        history_size: int = 1000,
        on_issue_detected: Optional[callable] = None,
        on_data_quarantined: Optional[callable] = None
    ):
        """
        Initialize data validator.
        
        Args:
            max_price_change_pct: Max allowed price change per tick
            max_staleness_seconds: Max allowed data age
            max_spread_pct: Max allowed bid-ask spread
            history_size: Number of data points to keep for context
            on_issue_detected: Callback when issue detected
            on_data_quarantined: Callback when data quarantined
        """
        self.max_price_change_pct = max_price_change_pct
        self.max_staleness_seconds = max_staleness_seconds
        self.max_spread_pct = max_spread_pct
        self.history_size = history_size
        self.on_issue_detected = on_issue_detected
        self.on_data_quarantined = on_data_quarantined
        
        # Price history per symbol
        self._price_history: Dict[str, deque] = {}
        self._volume_history: Dict[str, deque] = {}
        self._last_data: Dict[str, Dict] = {}
        self._sequence_numbers: Dict[str, int] = {}
        
        # Quarantine
        self._quarantine: List[Dict] = []
        self._quarantine_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'total_validated': 0,
            'total_issues': 0,
            'total_quarantined': 0,
            'issues_by_type': {},
            'quality_scores': deque(maxlen=1000)
        }
        
        logger.info("DataValidator initialized")
    
    def validate_tick(
        self,
        symbol: str,
        bid: float,
        ask: float,
        timestamp: datetime,
        volume: Optional[float] = None,
        sequence: Optional[int] = None,
        checksum: Optional[str] = None
    ) -> DataQualityReport:
        """
        Validate a tick data point.
        
        This is the answer to Q71: How do you detect price spikes that are
        data errors vs. real market events?
        
        Args:
            symbol: Trading symbol
            bid: Bid price
            ask: Ask price
            timestamp: Data timestamp
            volume: Optional volume
            sequence: Optional sequence number
            checksum: Optional data checksum
            
        Returns:
            DataQualityReport with validation results
        """
        start_time = datetime.now()
        issues = []
        
        # Initialize history if needed
        if symbol not in self._price_history:
            self._price_history[symbol] = deque(maxlen=self.history_size)
            self._volume_history[symbol] = deque(maxlen=self.history_size)
        
        mid_price = (bid + ask) / 2 if bid > 0 and ask > 0 else 0
        
        # 1. Basic validation
        issues.extend(self._validate_basic(symbol, bid, ask, timestamp, volume))
        
        # 2. Spread validation
        issues.extend(self._validate_spread(symbol, bid, ask))
        
        # 3. Staleness check (Q62)
        issues.extend(self._validate_staleness(symbol, timestamp))
        
        # 4. Price spike detection (Q71)
        issues.extend(self._validate_price_change(symbol, mid_price))
        
        # 5. Volume anomaly detection
        if volume is not None:
            issues.extend(self._validate_volume(symbol, volume))
        
        # 6. Sequence validation
        if sequence is not None:
            issues.extend(self._validate_sequence(symbol, sequence))
        
        # 7. Checksum validation (Q91)
        if checksum is not None:
            issues.extend(self._validate_checksum(symbol, bid, ask, timestamp, checksum))
        
        # 8. Economic validity
        issues.extend(self._validate_economic(symbol, bid, ask, mid_price))
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(issues)
        quality_level = self._classify_quality(quality_score)
        
        # Determine if usable
        critical_issues = [i for i in issues if i.severity == 'critical']
        is_usable = len(critical_issues) == 0 and quality_score >= 50
        
        # Quarantine if needed
        quarantined = False
        if not is_usable or quality_level == DataQualityLevel.UNUSABLE:
            quarantined = self._quarantine_data({
                'symbol': symbol,
                'bid': bid,
                'ask': ask,
                'timestamp': timestamp,
                'volume': volume,
                'issues': [i.to_dict() for i in issues]
            })
        
        # Update history (only if not quarantined)
        if not quarantined:
            self._price_history[symbol].append(mid_price)
            if volume is not None:
                self._volume_history[symbol].append(volume)
            self._last_data[symbol] = {
                'bid': bid,
                'ask': ask,
                'mid': mid_price,
                'timestamp': timestamp,
                'volume': volume
            }
            if sequence is not None:
                self._sequence_numbers[symbol] = sequence
        
        # Update statistics
        self.stats['total_validated'] += 1
        self.stats['total_issues'] += len(issues)
        self.stats['quality_scores'].append(quality_score)
        for issue in issues:
            issue_type = issue.issue_type.value
            self.stats['issues_by_type'][issue_type] = \
                self.stats['issues_by_type'].get(issue_type, 0) + 1
        
        # Callbacks
        if issues and self.on_issue_detected:
            for issue in issues:
                try:
                    self.on_issue_detected(symbol, issue)
                except Exception as e:
                    logger.error(f"Issue callback error: {e}")
        
        validation_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return DataQualityReport(
            timestamp=datetime.now(),
            symbol=symbol,
            data_type='tick',
            quality_level=quality_level,
            quality_score=quality_score,
            issues=issues,
            is_usable=is_usable,
            quarantined=quarantined,
            validation_time_ms=validation_time_ms
        )
    
    def validate_bar(
        self,
        symbol: str,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        timestamp: datetime
    ) -> DataQualityReport:
        """Validate OHLCV bar data"""
        start_time = datetime.now()
        issues = []
        
        # Basic validation
        if open_price <= 0:
            issues.append(DataIssue(
                DataIssueType.INVALID_VALUE, 'critical', 'open',
                '>0', open_price, "Open price must be positive"
            ))
        
        if high <= 0:
            issues.append(DataIssue(
                DataIssueType.INVALID_VALUE, 'critical', 'high',
                '>0', high, "High price must be positive"
            ))
        
        if low <= 0:
            issues.append(DataIssue(
                DataIssueType.INVALID_VALUE, 'critical', 'low',
                '>0', low, "Low price must be positive"
            ))
        
        if close <= 0:
            issues.append(DataIssue(
                DataIssueType.INVALID_VALUE, 'critical', 'close',
                '>0', close, "Close price must be positive"
            ))
        
        # OHLC relationship validation
        if high < low:
            issues.append(DataIssue(
                DataIssueType.ECONOMICALLY_IMPOSSIBLE, 'critical', 'high/low',
                'high >= low', f"high={high}, low={low}",
                "High must be >= Low"
            ))
        
        if high < open_price or high < close:
            issues.append(DataIssue(
                DataIssueType.ECONOMICALLY_IMPOSSIBLE, 'critical', 'high',
                'high >= open,close', high,
                "High must be >= Open and Close"
            ))
        
        if low > open_price or low > close:
            issues.append(DataIssue(
                DataIssueType.ECONOMICALLY_IMPOSSIBLE, 'critical', 'low',
                'low <= open,close', low,
                "Low must be <= Open and Close"
            ))
        
        # Volume validation
        if volume < 0:
            issues.append(DataIssue(
                DataIssueType.INVALID_VALUE, 'critical', 'volume',
                '>=0', volume, "Volume cannot be negative"
            ))
        
        # Staleness
        issues.extend(self._validate_staleness(symbol, timestamp))
        
        # Price change from previous bar
        if symbol in self._last_data:
            last_close = self._last_data[symbol].get('close', close)
            if last_close > 0:
                change_pct = abs(open_price - last_close) / last_close
                if change_pct > self.max_price_change_pct * 2:  # Allow larger gaps for bars
                    issues.append(DataIssue(
                        DataIssueType.PRICE_SPIKE, 'warning', 'open',
                        f'<{self.max_price_change_pct*200:.1f}%', f'{change_pct*100:.1f}%',
                        f"Large gap from previous close: {change_pct*100:.1f}%"
                    ))
        
        # Calculate quality
        quality_score = self._calculate_quality_score(issues)
        quality_level = self._classify_quality(quality_score)
        critical_issues = [i for i in issues if i.severity == 'critical']
        is_usable = len(critical_issues) == 0
        
        # Update last data
        if is_usable:
            self._last_data[symbol] = {
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'timestamp': timestamp
            }
        
        validation_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return DataQualityReport(
            timestamp=datetime.now(),
            symbol=symbol,
            data_type='bar',
            quality_level=quality_level,
            quality_score=quality_score,
            issues=issues,
            is_usable=is_usable,
            quarantined=not is_usable,
            validation_time_ms=validation_time_ms
        )
    
    def _validate_basic(
        self,
        symbol: str,
        bid: float,
        ask: float,
        timestamp: datetime,
        volume: Optional[float]
    ) -> List[DataIssue]:
        """Basic field validation"""
        issues = []
        
        if not symbol:
            issues.append(DataIssue(
                DataIssueType.MISSING_FIELD, 'critical', 'symbol',
                'non-empty', symbol, "Symbol is required"
            ))
        
        if bid <= 0:
            issues.append(DataIssue(
                DataIssueType.INVALID_VALUE, 'critical', 'bid',
                '>0', bid, "Bid must be positive"
            ))
        
        if ask <= 0:
            issues.append(DataIssue(
                DataIssueType.INVALID_VALUE, 'critical', 'ask',
                '>0', ask, "Ask must be positive"
            ))
        
        if timestamp is None:
            issues.append(DataIssue(
                DataIssueType.MISSING_FIELD, 'critical', 'timestamp',
                'non-null', None, "Timestamp is required"
            ))
        elif timestamp > datetime.now() + timedelta(seconds=5):
            issues.append(DataIssue(
                DataIssueType.TIMESTAMP_FUTURE, 'warning', 'timestamp',
                '<=now', timestamp.isoformat(), "Timestamp is in the future"
            ))
        
        if volume is not None and volume < 0:
            issues.append(DataIssue(
                DataIssueType.INVALID_VALUE, 'critical', 'volume',
                '>=0', volume, "Volume cannot be negative"
            ))
        
        return issues
    
    def _validate_spread(self, symbol: str, bid: float, ask: float) -> List[DataIssue]:
        """Validate bid-ask spread"""
        issues = []
        
        if bid > 0 and ask > 0:
            if bid > ask:
                issues.append(DataIssue(
                    DataIssueType.SPREAD_INVERTED, 'critical', 'spread',
                    'bid <= ask', f'bid={bid}, ask={ask}',
                    "Inverted spread: bid > ask"
                ))
            else:
                spread_pct = (ask - bid) / bid
                if spread_pct > self.max_spread_pct:
                    issues.append(DataIssue(
                        DataIssueType.SPREAD_EXCESSIVE, 'warning', 'spread',
                        f'<{self.max_spread_pct*100:.1f}%', f'{spread_pct*100:.1f}%',
                        f"Excessive spread: {spread_pct*100:.2f}%"
                    ))
        
        return issues
    
    def _validate_staleness(self, symbol: str, timestamp: datetime) -> List[DataIssue]:
        """
        Validate data freshness.
        
        This is the answer to Q62: How do you detect when a data source
        is delivering stale data?
        """
        issues = []
        
        if timestamp is None:
            return issues
        
        age_seconds = (datetime.now() - timestamp).total_seconds()
        
        if age_seconds > self.max_staleness_seconds:
            severity = 'critical' if age_seconds > self.max_staleness_seconds * 2 else 'warning'
            issues.append(DataIssue(
                DataIssueType.STALE, severity, 'timestamp',
                f'<{self.max_staleness_seconds}s', f'{age_seconds:.1f}s',
                f"Data is {age_seconds:.1f}s old (max: {self.max_staleness_seconds}s)"
            ))
        
        return issues
    
    def _validate_price_change(self, symbol: str, price: float) -> List[DataIssue]:
        """
        Validate price change from previous tick.
        
        This is the answer to Q71: How do you detect price spikes that are
        data errors vs. real market events?
        
        Uses statistical analysis of recent price history to distinguish
        between real market moves and data errors.
        """
        issues = []
        
        if symbol not in self._price_history or len(self._price_history[symbol]) < 2:
            return issues
        
        history = list(self._price_history[symbol])
        last_price = history[-1]
        
        if last_price <= 0 or price <= 0:
            return issues
        
        # Calculate change
        change_pct = abs(price - last_price) / last_price
        
        # Simple threshold check
        if change_pct > self.max_price_change_pct:
            # Check if this is likely a real move or error
            is_likely_error = self._is_likely_price_error(symbol, price, history)
            
            if is_likely_error:
                issues.append(DataIssue(
                    DataIssueType.PRICE_SPIKE, 'critical', 'price',
                    f'<{self.max_price_change_pct*100:.1f}%', f'{change_pct*100:.1f}%',
                    f"Likely data error: {change_pct*100:.2f}% change"
                ))
            else:
                issues.append(DataIssue(
                    DataIssueType.PRICE_SPIKE, 'warning', 'price',
                    f'<{self.max_price_change_pct*100:.1f}%', f'{change_pct*100:.1f}%',
                    f"Large price move: {change_pct*100:.2f}% (may be real)"
                ))
        
        return issues
    
    def _is_likely_price_error(
        self,
        symbol: str,
        price: float,
        history: List[float]
    ) -> bool:
        """
        Determine if a price spike is likely a data error.
        
        Criteria for likely error:
        1. Change is > 3 standard deviations from recent changes
        2. Price would immediately revert (if we had next tick)
        3. No corresponding volume spike
        """
        if len(history) < 10:
            return False
        
        # Calculate recent price changes
        changes = []
        for i in range(1, len(history)):
            if history[i-1] > 0:
                changes.append(abs(history[i] - history[i-1]) / history[i-1])
        
        if not changes:
            return False
        
        # Statistical analysis
        mean_change = np.mean(changes)
        std_change = np.std(changes)
        
        current_change = abs(price - history[-1]) / history[-1] if history[-1] > 0 else 0
        
        # If change is > 5 standard deviations, likely error
        if std_change > 0 and current_change > mean_change + 5 * std_change:
            return True
        
        # Check if price is far from recent range
        recent_high = max(history[-20:]) if len(history) >= 20 else max(history)
        recent_low = min(history[-20:]) if len(history) >= 20 else min(history)
        recent_range = recent_high - recent_low
        
        if recent_range > 0:
            distance_from_range = 0
            if price > recent_high:
                distance_from_range = (price - recent_high) / recent_range
            elif price < recent_low:
                distance_from_range = (recent_low - price) / recent_range
            
            # If price is > 3x the recent range away, likely error
            if distance_from_range > 3:
                return True
        
        return False
    
    def _validate_volume(self, symbol: str, volume: float) -> List[DataIssue]:
        """Validate volume for anomalies"""
        issues = []
        
        if symbol not in self._volume_history or len(self._volume_history[symbol]) < 10:
            return issues
        
        history = list(self._volume_history[symbol])
        mean_volume = np.mean(history)
        std_volume = np.std(history)
        
        if std_volume > 0 and mean_volume > 0:
            z_score = (volume - mean_volume) / std_volume
            
            if z_score > 5:  # 5 standard deviations
                issues.append(DataIssue(
                    DataIssueType.VOLUME_ANOMALY, 'warning', 'volume',
                    f'<{mean_volume + 3*std_volume:.0f}', f'{volume:.0f}',
                    f"Unusually high volume: {z_score:.1f} std devs"
                ))
        
        return issues
    
    def _validate_sequence(self, symbol: str, sequence: int) -> List[DataIssue]:
        """Validate sequence numbers for gaps"""
        issues = []
        
        if symbol in self._sequence_numbers:
            expected = self._sequence_numbers[symbol] + 1
            if sequence != expected:
                gap = sequence - expected
                if gap > 0:
                    issues.append(DataIssue(
                        DataIssueType.SEQUENCE_GAP, 'warning', 'sequence',
                        expected, sequence, f"Sequence gap: missing {gap} messages"
                    ))
                elif gap < 0:
                    issues.append(DataIssue(
                        DataIssueType.DUPLICATE, 'warning', 'sequence',
                        f'>{self._sequence_numbers[symbol]}', sequence,
                        "Possible duplicate or out-of-order message"
                    ))
        
        return issues
    
    def _validate_checksum(
        self,
        symbol: str,
        bid: float,
        ask: float,
        timestamp: datetime,
        checksum: str
    ) -> List[DataIssue]:
        """
        Validate data checksum.
        
        This is the answer to Q91: How do you detect bit-level corruption?
        """
        issues = []
        
        # Calculate expected checksum
        data = f"{symbol}:{bid}:{ask}:{timestamp.isoformat()}"
        expected = hashlib.md5(data.encode()).hexdigest()[:8]
        
        if checksum != expected:
            issues.append(DataIssue(
                DataIssueType.CHECKSUM_MISMATCH, 'critical', 'checksum',
                expected, checksum, "Data checksum mismatch - possible corruption"
            ))
        
        return issues
    
    def _validate_economic(
        self,
        symbol: str,
        bid: float,
        ask: float,
        mid: float
    ) -> List[DataIssue]:
        """Validate economic plausibility"""
        issues = []
        
        # Check for obviously wrong prices (e.g., forex pair at 0.0001 or 10000)
        # This is symbol-specific, using general heuristics
        
        if 'USD' in symbol or 'EUR' in symbol or 'GBP' in symbol:
            # Major forex pairs typically between 0.5 and 2.0
            if mid < 0.1 or mid > 200:
                issues.append(DataIssue(
                    DataIssueType.ECONOMICALLY_IMPOSSIBLE, 'warning', 'price',
                    '0.1-200', mid, f"Price {mid} seems implausible for {symbol}"
                ))
        
        return issues
    
    def _calculate_quality_score(self, issues: List[DataIssue]) -> float:
        """Calculate quality score from 0-100"""
        if not issues:
            return 100.0
        
        # Deduct points based on issue severity
        deductions = {
            'critical': 40,
            'warning': 15,
            'info': 5
        }
        
        total_deduction = sum(deductions.get(i.severity, 10) for i in issues)
        return max(0, 100 - total_deduction)
    
    def _classify_quality(self, score: float) -> DataQualityLevel:
        """Classify quality level from score"""
        if score >= 95:
            return DataQualityLevel.EXCELLENT
        elif score >= 80:
            return DataQualityLevel.GOOD
        elif score >= 60:
            return DataQualityLevel.ACCEPTABLE
        elif score >= 40:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.UNUSABLE
    
    def _quarantine_data(self, data: Dict) -> bool:
        """Quarantine bad data for review"""
        with self._quarantine_lock:
            data['quarantined_at'] = datetime.now().isoformat()
            self._quarantine.append(data)
            self.stats['total_quarantined'] += 1
            
            # Limit quarantine size
            if len(self._quarantine) > 10000:
                self._quarantine = self._quarantine[-5000:]
        
        if self.on_data_quarantined:
            try:
                self.on_data_quarantined(data)
            except Exception as e:
                logger.error(f"Quarantine callback error: {e}")
        
        logger.warning(f"Data quarantined: {data.get('symbol')} - {len(data.get('issues', []))} issues")
        return True
    
    def get_quarantined_data(self, limit: int = 100) -> List[Dict]:
        """Get quarantined data for review"""
        with self._quarantine_lock:
            return self._quarantine[-limit:]
    
    def clear_quarantine(self, before: Optional[datetime] = None) -> int:
        """Clear quarantined data"""
        with self._quarantine_lock:
            if before is None:
                count = len(self._quarantine)
                self._quarantine = []
            else:
                before_iso = before.isoformat()
                original = len(self._quarantine)
                self._quarantine = [
                    d for d in self._quarantine
                    if d.get('quarantined_at', '') > before_iso
                ]
                count = original - len(self._quarantine)
        
        return count
    
    def get_statistics(self) -> Dict:
        """Get validation statistics"""
        avg_quality = np.mean(list(self.stats['quality_scores'])) if self.stats['quality_scores'] else 100
        
        return {
            'total_validated': self.stats['total_validated'],
            'total_issues': self.stats['total_issues'],
            'total_quarantined': self.stats['total_quarantined'],
            'average_quality_score': avg_quality,
            'issues_by_type': self.stats['issues_by_type'],
            'quarantine_size': len(self._quarantine),
            'symbols_tracked': len(self._price_history)
        }

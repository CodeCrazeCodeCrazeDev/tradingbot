"""
Data Integrity Gate - The First Line of Defense Against AI Stupidity

This gate ensures that all data entering the decision pipeline is:
1. Complete - No missing values that could cause NaN propagation
2. Fresh - Not stale data that could lead to outdated decisions
3. Consistent - No impossible values or logical contradictions
4. Verified - Cross-checked against multiple sources when possible

RULE: "Garbage in, garbage out. We refuse garbage."

Author: AlphaAlgo Reality Check System
"""

import logging
import statistics
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
import math

logger = logging.getLogger(__name__)


class DataAnomalyType(Enum):
    """Types of data anomalies we detect"""
    MISSING_VALUES = "missing_values"
    STALE_DATA = "stale_data"
    IMPOSSIBLE_VALUES = "impossible_values"
    EXTREME_OUTLIERS = "extreme_outliers"
    TIMESTAMP_GAPS = "timestamp_gaps"
    PRICE_JUMPS = "price_jumps"
    VOLUME_ANOMALY = "volume_anomaly"
    BID_ASK_CROSSED = "bid_ask_crossed"
    NEGATIVE_PRICES = "negative_prices"
    ZERO_VOLUME = "zero_volume"
    DUPLICATE_DATA = "duplicate_data"
    SOURCE_MISMATCH = "source_mismatch"
    CHECKSUM_FAILURE = "checksum_failure"
    SEQUENCE_BREAK = "sequence_break"


class DataSeverity(Enum):
    """Severity levels for data issues"""
    INFO = "info"           # Log but continue
    WARNING = "warning"     # Reduce confidence
    ERROR = "error"         # Block this data point
    CRITICAL = "critical"   # Halt all trading


@dataclass
class DataAnomaly:
    """Represents a detected data anomaly"""
    anomaly_type: DataAnomalyType
    severity: DataSeverity
    field: str
    value: Any
    expected_range: Optional[Tuple[float, float]] = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __str__(self):
        return f"[{self.severity.value.upper()}] {self.anomaly_type.value}: {self.message}"


@dataclass
class DataQualityScore:
    """Overall data quality assessment"""
    score: float  # 0-1, where 1 is perfect
    is_usable: bool
    anomalies: List[DataAnomaly]
    completeness: float  # % of non-missing values
    freshness: float  # 0-1 based on data age
    consistency: float  # 0-1 based on logical checks
    reliability: float  # 0-1 based on source verification
    
    @property
    def should_block(self) -> bool:
        """Should we block trading based on this data?"""
        return not self.is_usable or self.score < 0.5
    
    @property
    def confidence_multiplier(self) -> float:
        """How much to reduce confidence based on data quality"""
        return max(0.1, self.score)


class DataIntegrityGate:
    """
    HARD GATE: Data Integrity Validation
    
    This gate BLOCKS all trading decisions if data quality is insufficient.
    No exceptions. No overrides. Bad data = No trade.
    
    Checks:
    1. Completeness - All required fields present
    2. Freshness - Data is recent enough
    3. Validity - Values are within possible ranges
    4. Consistency - No logical contradictions
    5. Outliers - Extreme values are flagged
    6. Source verification - Cross-check when possible
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Staleness thresholds (seconds)
        self.max_price_age = self.config.get('max_price_age', 60)  # 1 minute
        self.max_indicator_age = self.config.get('max_indicator_age', 300)  # 5 minutes
        
        # Price validity ranges (percentage from last known good)
        self.max_price_change_pct = self.config.get('max_price_change_pct', 0.10)  # 10%
        self.max_spread_pct = self.config.get('max_spread_pct', 0.02)  # 2%
        
        # Outlier detection
        self.outlier_std_threshold = self.config.get('outlier_std_threshold', 4.0)
        
        # Historical data for validation
        self.price_history: Dict[str, deque] = {}
        self.volume_history: Dict[str, deque] = {}
        self.last_valid_data: Dict[str, Dict] = {}
        
        # Anomaly tracking
        self.anomaly_history: deque = deque(maxlen=1000)
        self.blocked_count = 0
        self.passed_count = 0
        
        # Required fields for different data types
        self.required_ohlcv_fields = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        self.required_tick_fields = ['bid', 'ask', 'last', 'timestamp']
        
        logger.info("DataIntegrityGate initialized - NO BAD DATA SHALL PASS")
    
    def validate(self, data: Dict[str, Any], data_type: str = 'ohlcv') -> DataQualityScore:
        """
        Validate incoming data and return quality score.
        
        Args:
            data: The data to validate
            data_type: Type of data ('ohlcv', 'tick', 'indicator')
            
        Returns:
            DataQualityScore with detailed assessment
        """
        anomalies = []
        
        # 1. Check completeness
        completeness, missing_anomalies = self._check_completeness(data, data_type)
        anomalies.extend(missing_anomalies)
        
        # 2. Check freshness
        freshness, stale_anomalies = self._check_freshness(data)
        anomalies.extend(stale_anomalies)
        
        # 3. Check validity (impossible values)
        validity, invalid_anomalies = self._check_validity(data, data_type)
        anomalies.extend(invalid_anomalies)
        
        # 4. Check consistency (logical contradictions)
        consistency, inconsistent_anomalies = self._check_consistency(data, data_type)
        anomalies.extend(inconsistent_anomalies)
        
        # 5. Check for outliers
        outlier_score, outlier_anomalies = self._check_outliers(data)
        anomalies.extend(outlier_anomalies)
        
        # 6. Check for duplicates
        duplicate_anomalies = self._check_duplicates(data)
        anomalies.extend(duplicate_anomalies)
        
        # Calculate overall score
        reliability = 1.0 - (len([a for a in anomalies if a.severity in [DataSeverity.ERROR, DataSeverity.CRITICAL]]) * 0.2)
        reliability = max(0, reliability)
        
        overall_score = (
            completeness * 0.25 +
            freshness * 0.25 +
            validity * 0.20 +
            consistency * 0.15 +
            outlier_score * 0.10 +
            reliability * 0.05
        )
        
        # Determine if usable
        has_critical = any(a.severity == DataSeverity.CRITICAL for a in anomalies)
        has_errors = sum(1 for a in anomalies if a.severity == DataSeverity.ERROR) >= 2
        is_usable = not has_critical and not has_errors and overall_score >= 0.5
        
        # Track statistics
        if is_usable:
            self.passed_count += 1
            self._update_history(data)
        else:
            self.blocked_count += 1
        
        # Log anomalies
        for anomaly in anomalies:
            self.anomaly_history.append(anomaly)
            if anomaly.severity in [DataSeverity.ERROR, DataSeverity.CRITICAL]:
                logger.warning(f"Data anomaly: {anomaly}")
        
        result = DataQualityScore(
            score=overall_score,
            is_usable=is_usable,
            anomalies=anomalies,
            completeness=completeness,
            freshness=freshness,
            consistency=consistency,
            reliability=reliability
        )
        
        if not is_usable:
            logger.error(f"DATA INTEGRITY GATE BLOCKED: score={overall_score:.2f}, "
                        f"anomalies={len(anomalies)}, critical={has_critical}")
        
        return result
    
    def _check_completeness(self, data: Dict, data_type: str) -> Tuple[float, List[DataAnomaly]]:
        """Check for missing required fields"""
        anomalies = []
        
        if data_type == 'ohlcv':
            required = self.required_ohlcv_fields
        elif data_type == 'tick':
            required = self.required_tick_fields
        else:
            required = ['value', 'timestamp']
        
        missing = []
        for field in required:
            if field not in data or data[field] is None:
                missing.append(field)
                anomalies.append(DataAnomaly(
                    anomaly_type=DataAnomalyType.MISSING_VALUES,
                    severity=DataSeverity.ERROR,
                    field=field,
                    value=None,
                    message=f"Required field '{field}' is missing"
                ))
            elif isinstance(data[field], float) and math.isnan(data[field]):
                missing.append(field)
                anomalies.append(DataAnomaly(
                    anomaly_type=DataAnomalyType.MISSING_VALUES,
                    severity=DataSeverity.ERROR,
                    field=field,
                    value=float('nan'),
                    message=f"Field '{field}' is NaN"
                ))
        
        completeness = 1.0 - (len(missing) / len(required)) if required else 1.0
        return completeness, anomalies
    
    def _check_freshness(self, data: Dict) -> Tuple[float, List[DataAnomaly]]:
        """Check if data is stale"""
        anomalies = []
        
        timestamp = data.get('timestamp')
        if timestamp is None:
            return 0.5, anomalies  # Can't check without timestamp
        
        if isinstance(timestamp, (int, float)):
            data_time = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, datetime):
            data_time = timestamp
        else:
            try:
                data_time = datetime.fromisoformat(str(timestamp))
            except Exception as e:
                logger.error(f"Error: {e}")
                return 0.5, anomalies
        
        age_seconds = (datetime.utcnow() - data_time).total_seconds()
        
        if age_seconds > self.max_price_age * 10:  # Very stale
            anomalies.append(DataAnomaly(
                anomaly_type=DataAnomalyType.STALE_DATA,
                severity=DataSeverity.CRITICAL,
                field='timestamp',
                value=age_seconds,
                message=f"Data is {age_seconds:.0f}s old (max: {self.max_price_age}s)"
            ))
            return 0.0, anomalies
        elif age_seconds > self.max_price_age:
            anomalies.append(DataAnomaly(
                anomaly_type=DataAnomalyType.STALE_DATA,
                severity=DataSeverity.WARNING,
                field='timestamp',
                value=age_seconds,
                message=f"Data is {age_seconds:.0f}s old"
            ))
            freshness = max(0, 1.0 - (age_seconds / (self.max_price_age * 10)))
        else:
            freshness = 1.0
        
        return freshness, anomalies
    
    def _check_validity(self, data: Dict, data_type: str) -> Tuple[float, List[DataAnomaly]]:
        """Check for impossible values"""
        anomalies = []
        validity_score = 1.0
        
        # Check for negative prices
        price_fields = ['open', 'high', 'low', 'close', 'bid', 'ask', 'last', 'price']
        for field in price_fields:
            if field in data and data[field] is not None:
                if data[field] < 0:
                    anomalies.append(DataAnomaly(
                        anomaly_type=DataAnomalyType.NEGATIVE_PRICES,
                        severity=DataSeverity.CRITICAL,
                        field=field,
                        value=data[field],
                        expected_range=(0, float('inf')),
                        message=f"Negative price: {field}={data[field]}"
                    ))
                    validity_score -= 0.3
                elif data[field] == 0:
                    anomalies.append(DataAnomaly(
                        anomaly_type=DataAnomalyType.IMPOSSIBLE_VALUES,
                        severity=DataSeverity.ERROR,
                        field=field,
                        value=data[field],
                        message=f"Zero price: {field}={data[field]}"
                    ))
                    validity_score -= 0.2
        
        # Check for negative volume
        if 'volume' in data and data['volume'] is not None:
            if data['volume'] < 0:
                anomalies.append(DataAnomaly(
                    anomaly_type=DataAnomalyType.IMPOSSIBLE_VALUES,
                    severity=DataSeverity.CRITICAL,
                    field='volume',
                    value=data['volume'],
                    message=f"Negative volume: {data['volume']}"
                ))
                validity_score -= 0.3
        
        # Check OHLC logic: High >= Low, High >= Open/Close, Low <= Open/Close
        if data_type == 'ohlcv':
            o, h, l, c = data.get('open'), data.get('high'), data.get('low'), data.get('close')
            if all(v is not None for v in [o, h, l, c]):
                if h < l:
                    anomalies.append(DataAnomaly(
                        anomaly_type=DataAnomalyType.IMPOSSIBLE_VALUES,
                        severity=DataSeverity.CRITICAL,
                        field='high/low',
                        value=(h, l),
                        message=f"High ({h}) < Low ({l})"
                    ))
                    validity_score -= 0.4
                if h < max(o, c):
                    anomalies.append(DataAnomaly(
                        anomaly_type=DataAnomalyType.IMPOSSIBLE_VALUES,
                        severity=DataSeverity.ERROR,
                        field='high',
                        value=h,
                        message=f"High ({h}) < max(Open, Close) ({max(o, c)})"
                    ))
                    validity_score -= 0.2
                if l > min(o, c):
                    anomalies.append(DataAnomaly(
                        anomaly_type=DataAnomalyType.IMPOSSIBLE_VALUES,
                        severity=DataSeverity.ERROR,
                        field='low',
                        value=l,
                        message=f"Low ({l}) > min(Open, Close) ({min(o, c)})"
                    ))
                    validity_score -= 0.2
        
        # Check bid/ask logic
        if data_type == 'tick':
            bid, ask = data.get('bid'), data.get('ask')
            if bid is not None and ask is not None:
                if bid > ask:
                    anomalies.append(DataAnomaly(
                        anomaly_type=DataAnomalyType.BID_ASK_CROSSED,
                        severity=DataSeverity.CRITICAL,
                        field='bid/ask',
                        value=(bid, ask),
                        message=f"Bid ({bid}) > Ask ({ask}) - crossed market"
                    ))
                    validity_score -= 0.5
                elif (ask - bid) / bid > self.max_spread_pct:
                    anomalies.append(DataAnomaly(
                        anomaly_type=DataAnomalyType.EXTREME_OUTLIERS,
                        severity=DataSeverity.WARNING,
                        field='spread',
                        value=(ask - bid) / bid,
                        message=f"Extreme spread: {((ask - bid) / bid * 100):.2f}%"
                    ))
                    validity_score -= 0.1
        
        return max(0, validity_score), anomalies
    
    def _check_consistency(self, data: Dict, data_type: str) -> Tuple[float, List[DataAnomaly]]:
        """Check for logical inconsistencies with historical data"""
        anomalies = []
        consistency_score = 1.0
        
        symbol = data.get('symbol', 'unknown')
        
        # Check price jumps against history
        if symbol in self.last_valid_data:
            last = self.last_valid_data[symbol]
            
            # Price jump check
            current_price = data.get('close') or data.get('last') or data.get('price')
            last_price = last.get('close') or last.get('last') or last.get('price')
            
            if current_price and last_price and last_price > 0:
                change_pct = abs(current_price - last_price) / last_price
                
                if change_pct > self.max_price_change_pct:
                    severity = DataSeverity.CRITICAL if change_pct > 0.5 else DataSeverity.WARNING
                    anomalies.append(DataAnomaly(
                        anomaly_type=DataAnomalyType.PRICE_JUMPS,
                        severity=severity,
                        field='price',
                        value=change_pct,
                        expected_range=(0, self.max_price_change_pct),
                        message=f"Price jumped {change_pct*100:.1f}% from {last_price} to {current_price}"
                    ))
                    consistency_score -= 0.3 if severity == DataSeverity.CRITICAL else 0.1
            
            # Volume anomaly check
            current_vol = data.get('volume')
            last_vol = last.get('volume')
            
            if current_vol and last_vol and last_vol > 0:
                vol_ratio = current_vol / last_vol
                if vol_ratio > 100 or vol_ratio < 0.01:
                    anomalies.append(DataAnomaly(
                        anomaly_type=DataAnomalyType.VOLUME_ANOMALY,
                        severity=DataSeverity.WARNING,
                        field='volume',
                        value=vol_ratio,
                        message=f"Volume changed {vol_ratio:.1f}x from last"
                    ))
                    consistency_score -= 0.1
        
        return max(0, consistency_score), anomalies
    
    def _check_outliers(self, data: Dict) -> Tuple[float, List[DataAnomaly]]:
        """Check for statistical outliers"""
        anomalies = []
        outlier_score = 1.0
        
        symbol = data.get('symbol', 'unknown')
        
        # Check price outliers
        if symbol in self.price_history and len(self.price_history[symbol]) >= 10:
            prices = list(self.price_history[symbol])
            current_price = data.get('close') or data.get('last') or data.get('price')
            
            if current_price and len(prices) >= 2:
                mean = statistics.mean(prices)
                std = statistics.stdev(prices)
                
                if std > 0:
                    z_score = abs(current_price - mean) / std
                    
                    if z_score > self.outlier_std_threshold:
                        anomalies.append(DataAnomaly(
                            anomaly_type=DataAnomalyType.EXTREME_OUTLIERS,
                            severity=DataSeverity.WARNING,
                            field='price',
                            value=z_score,
                            message=f"Price is {z_score:.1f} std devs from mean"
                        ))
                        outlier_score -= 0.2
        
        return max(0, outlier_score), anomalies
    
    def _check_duplicates(self, data: Dict) -> List[DataAnomaly]:
        """Check for duplicate data"""
        anomalies = []
        
        symbol = data.get('symbol', 'unknown')
        
        if symbol in self.last_valid_data:
            last = self.last_valid_data[symbol]
            
            # Check if this is exact duplicate
            if (data.get('timestamp') == last.get('timestamp') and
                data.get('close') == last.get('close') and
                data.get('volume') == last.get('volume')):
                anomalies.append(DataAnomaly(
                    anomaly_type=DataAnomalyType.DUPLICATE_DATA,
                    severity=DataSeverity.WARNING,
                    field='all',
                    value=None,
                    message="Duplicate data point detected"
                ))
        
        return anomalies
    
    def _update_history(self, data: Dict):
        """Update historical data for future validation"""
        symbol = data.get('symbol', 'unknown')
        
        # Update price history
        price = data.get('close') or data.get('last') or data.get('price')
        if price:
            if symbol not in self.price_history:
                self.price_history[symbol] = deque(maxlen=100)
            self.price_history[symbol].append(price)
        
        # Update volume history
        volume = data.get('volume')
        if volume:
            if symbol not in self.volume_history:
                self.volume_history[symbol] = deque(maxlen=100)
            self.volume_history[symbol].append(volume)
        
        # Update last valid data
        self.last_valid_data[symbol] = data.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gate statistics"""
        total = self.passed_count + self.blocked_count
        return {
            'total_checks': total,
            'passed': self.passed_count,
            'blocked': self.blocked_count,
            'block_rate': self.blocked_count / total if total > 0 else 0,
            'recent_anomalies': len(self.anomaly_history),
            'anomaly_breakdown': self._get_anomaly_breakdown()
        }
    
    def _get_anomaly_breakdown(self) -> Dict[str, int]:
        """Get breakdown of anomaly types"""
        breakdown = {}
        for anomaly in self.anomaly_history:
            key = anomaly.anomaly_type.value
            breakdown[key] = breakdown.get(key, 0) + 1
        return breakdown
    
    def reset_history(self):
        """Reset all historical data"""
        self.price_history.clear()
        self.volume_history.clear()
        self.last_valid_data.clear()
        self.anomaly_history.clear()
        self.blocked_count = 0
        self.passed_count = 0
        logger.info("DataIntegrityGate history reset")

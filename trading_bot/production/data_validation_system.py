"""
Production Data Validation System

Implements:
- Timestamp synchronization with NTP
- Sequence number checking and gap detection
- Cross-venue consistency checks
- Outlier detection with forensics
- Data quality scoring
- Anomaly alerting

This is critical infrastructure - bad data = bad trades = lost money.
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import logging
import hashlib
import json
import time
import threading
import socket

logger = logging.getLogger(__name__)


# =============================================================================
# DATA QUALITY ENUMS
# =============================================================================

class DataQuality(Enum):
    """Data quality levels"""
    EXCELLENT = "EXCELLENT"  # All checks pass
    GOOD = "GOOD"  # Minor warnings
    DEGRADED = "DEGRADED"  # Some issues, usable with caution
    POOR = "POOR"  # Significant issues
    UNUSABLE = "UNUSABLE"  # Do not use


class AnomalyType(Enum):
    """Types of data anomalies"""
    TIMESTAMP_DRIFT = "TIMESTAMP_DRIFT"
    TIMESTAMP_GAP = "TIMESTAMP_GAP"
    TIMESTAMP_DUPLICATE = "TIMESTAMP_DUPLICATE"
    TIMESTAMP_OUT_OF_ORDER = "TIMESTAMP_OUT_OF_ORDER"
    SEQUENCE_GAP = "SEQUENCE_GAP"
    SEQUENCE_DUPLICATE = "SEQUENCE_DUPLICATE"
    PRICE_SPIKE = "PRICE_SPIKE"
    PRICE_ZERO = "PRICE_ZERO"
    PRICE_NEGATIVE = "PRICE_NEGATIVE"
    VOLUME_SPIKE = "VOLUME_SPIKE"
    SPREAD_ANOMALY = "SPREAD_ANOMALY"
    CROSS_VENUE_DIVERGENCE = "CROSS_VENUE_DIVERGENCE"
    STALE_DATA = "STALE_DATA"
    MISSING_FIELD = "MISSING_FIELD"


class DataSource(Enum):
    """Data source types"""
    EXCHANGE_DIRECT = "EXCHANGE_DIRECT"
    EXCHANGE_WEBSOCKET = "EXCHANGE_WEBSOCKET"
    BROKER_FEED = "BROKER_FEED"
    AGGREGATOR = "AGGREGATOR"
    HISTORICAL = "HISTORICAL"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Anomaly:
    """Detected data anomaly"""
    anomaly_type: AnomalyType
    symbol: str
    timestamp: datetime
    severity: float  # 0.0 to 1.0
    description: str
    raw_data: Dict[str, Any]
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.anomaly_type.value,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity,
            'description': self.description,
            'source': self.source
        }


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    quality: DataQuality
    score: float  # 0.0 to 1.0
    anomalies: List[Anomaly]
    warnings: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'quality': self.quality.value,
            'score': round(self.score, 4),
            'anomaly_count': len(self.anomalies),
            'anomalies': [a.to_dict() for a in self.anomalies],
            'warnings': self.warnings,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TickData:
    """Normalized tick data"""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    bid_size: float
    ask_size: float
    last_price: float
    last_size: float
    volume: float
    sequence: Optional[int] = None
    source: str = "unknown"
    exchange: str = "unknown"
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def spread_bps(self) -> float:
        return (self.spread / self.mid) * 10000 if self.mid > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'bid': self.bid,
            'ask': self.ask,
            'bid_size': self.bid_size,
            'ask_size': self.ask_size,
            'last_price': self.last_price,
            'last_size': self.last_size,
            'volume': self.volume,
            'sequence': self.sequence,
            'source': self.source,
            'exchange': self.exchange
        }


@dataclass
class DataQualityMetrics:
    """Aggregated data quality metrics"""
    symbol: str
    period_start: datetime
    period_end: datetime
    
    # Counts
    total_ticks: int = 0
    valid_ticks: int = 0
    invalid_ticks: int = 0
    
    # Anomaly counts by type
    anomaly_counts: Dict[str, int] = field(default_factory=dict)
    
    # Quality scores
    timestamp_quality: float = 1.0
    price_quality: float = 1.0
    volume_quality: float = 1.0
    sequence_quality: float = 1.0
    overall_quality: float = 1.0
    
    # Latency stats
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    # Gap stats
    total_gaps: int = 0
    max_gap_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'period': f"{self.period_start.isoformat()} to {self.period_end.isoformat()}",
            'total_ticks': self.total_ticks,
            'valid_ticks': self.valid_ticks,
            'invalid_ticks': self.invalid_ticks,
            'validity_rate': self.valid_ticks / self.total_ticks if self.total_ticks > 0 else 0,
            'anomaly_counts': self.anomaly_counts,
            'timestamp_quality': round(self.timestamp_quality, 4),
            'price_quality': round(self.price_quality, 4),
            'volume_quality': round(self.volume_quality, 4),
            'sequence_quality': round(self.sequence_quality, 4),
            'overall_quality': round(self.overall_quality, 4),
            'avg_latency_ms': round(self.avg_latency_ms, 2),
            'max_latency_ms': round(self.max_latency_ms, 2),
            'p99_latency_ms': round(self.p99_latency_ms, 2)
        }


# =============================================================================
# TIMESTAMP SYNCHRONIZATION
# =============================================================================

class TimestampSynchronizer:
    """
    Synchronizes timestamps with NTP servers
    
    Ensures all data timestamps are accurate relative to true time.
    Critical for:
    - Order sequencing
    - Latency measurement
    - Cross-venue comparison
    """
    
    NTP_SERVERS = [
        'pool.ntp.org',
        'time.google.com',
        'time.cloudflare.com',
        'time.windows.com'
    ]
    
    def __init__(self):
        self.offset_ms: float = 0.0
        self.last_sync: Optional[datetime] = None
        self.sync_interval_seconds: int = 300  # 5 minutes
        self._lock = threading.Lock()
        
    def sync(self) -> bool:
        """Synchronize with NTP server"""
        try:
            import ntplib
            client = ntplib.NTPClient()
            
            for server in self.NTP_SERVERS:
                try:
                    response = client.request(server, version=3, timeout=2)
                    
                    with self._lock:
                        self.offset_ms = response.offset * 1000
                        self.last_sync = datetime.utcnow()
                    
                    logger.info(f"NTP sync successful: offset={self.offset_ms:.2f}ms (server={server})")
                    return True
                    
                except Exception as e:
                    logger.debug(f"NTP server {server} failed: {e}")
                    continue
            
            logger.warning("All NTP servers failed")
            return False
            
        except ImportError:
            logger.warning("ntplib not installed, using system time")
            self.offset_ms = 0.0
            self.last_sync = datetime.utcnow()
            return True
    
    def get_true_time(self) -> datetime:
        """Get current time adjusted for NTP offset"""
        now = datetime.utcnow()
        
        # Check if sync needed
        if self.last_sync is None or \
           (now - self.last_sync).total_seconds() > self.sync_interval_seconds:
            self.sync()
        
        # Apply offset
        offset_delta = timedelta(milliseconds=self.offset_ms)
        return now + offset_delta
    
    def validate_timestamp(self, timestamp: datetime, max_drift_ms: float = 5000) -> Tuple[bool, float]:
        """
        Validate timestamp against true time
        
        Returns: (is_valid, drift_ms)
        """
        true_time = self.get_true_time()
        drift_ms = abs((timestamp - true_time).total_seconds() * 1000)
        
        return drift_ms <= max_drift_ms, drift_ms


# =============================================================================
# SEQUENCE VALIDATOR
# =============================================================================

class SequenceValidator:
    """
    Validates sequence numbers for gap and duplicate detection
    
    Tracks:
    - Expected next sequence
    - Gap history
    - Duplicate detection
    """
    
    def __init__(self, max_history: int = 10000):
        self.sequences: Dict[str, int] = {}  # symbol -> last sequence
        self.gaps: Dict[str, List[Tuple[int, int]]] = {}  # symbol -> [(start, end)]
        self.duplicates: Dict[str, Set[int]] = {}  # symbol -> set of duplicate sequences
        self.history: Dict[str, deque] = {}  # symbol -> recent sequences
        self.max_history = max_history
    
    def validate(self, symbol: str, sequence: int) -> Tuple[bool, List[Anomaly]]:
        """
        Validate sequence number
        
        Returns: (is_valid, anomalies)
        """
        anomalies = []
        
        # Initialize if needed
        if symbol not in self.sequences:
            self.sequences[symbol] = sequence
            self.gaps[symbol] = []
            self.duplicates[symbol] = set()
            self.history[symbol] = deque(maxlen=self.max_history)
            self.history[symbol].append(sequence)
            return True, []
        
        last_seq = self.sequences[symbol]
        expected = last_seq + 1
        
        # Check for gap
        if sequence > expected:
            gap_size = sequence - expected
            self.gaps[symbol].append((expected, sequence - 1))
            
            anomaly = Anomaly(
                anomaly_type=AnomalyType.SEQUENCE_GAP,
                symbol=symbol,
                timestamp=datetime.utcnow(),
                severity=min(1.0, gap_size / 100),  # Scale by gap size
                description=f"Sequence gap: expected {expected}, got {sequence} (gap={gap_size})",
                raw_data={'expected': expected, 'received': sequence, 'gap_size': gap_size},
                source="sequence_validator"
            )
            anomalies.append(anomaly)
            logger.warning(f"Sequence gap for {symbol}: {expected} -> {sequence}")
        
        # Check for duplicate
        elif sequence <= last_seq:
            if sequence in self.history[symbol]:
                self.duplicates[symbol].add(sequence)
                
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.SEQUENCE_DUPLICATE,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    severity=0.5,
                    description=f"Duplicate sequence: {sequence}",
                    raw_data={'sequence': sequence, 'last_sequence': last_seq},
                    source="sequence_validator"
                )
                anomalies.append(anomaly)
                logger.warning(f"Duplicate sequence for {symbol}: {sequence}")
                
                return False, anomalies
        
        # Update state
        self.sequences[symbol] = sequence
        self.history[symbol].append(sequence)
        
        return len(anomalies) == 0, anomalies
    
    def get_gap_count(self, symbol: str) -> int:
        """Get total number of gaps for symbol"""
        return len(self.gaps.get(symbol, []))
    
    def get_total_missing(self, symbol: str) -> int:
        """Get total number of missing sequences"""
        total = 0
        for start, end in self.gaps.get(symbol, []):
            total += end - start + 1
        return total


# =============================================================================
# PRICE VALIDATOR
# =============================================================================

class PriceValidator:
    """
    Validates price data for anomalies
    
    Checks:
    - Zero/negative prices
    - Price spikes
    - Spread anomalies
    - Statistical outliers
    """
    
    def __init__(
        self,
        max_price_change_pct: float = 0.10,  # 10% max single-tick change
        max_spread_bps: float = 100,  # 1% max spread
        outlier_std_threshold: float = 4.0  # 4 standard deviations
    ):
        self.max_price_change_pct = max_price_change_pct
        self.max_spread_bps = max_spread_bps
        self.outlier_std_threshold = outlier_std_threshold
        
        # Price history for outlier detection
        self.price_history: Dict[str, deque] = {}
        self.history_size = 1000
    
    def validate(self, tick: TickData) -> Tuple[bool, List[Anomaly]]:
        """
        Validate tick price data
        
        Returns: (is_valid, anomalies)
        """
        anomalies = []
        symbol = tick.symbol
        
        # Initialize history
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.history_size)
        
        # Check for zero/negative prices
        if tick.bid <= 0 or tick.ask <= 0:
            anomaly = Anomaly(
                anomaly_type=AnomalyType.PRICE_ZERO if tick.bid == 0 or tick.ask == 0 else AnomalyType.PRICE_NEGATIVE,
                symbol=symbol,
                timestamp=tick.timestamp,
                severity=1.0,
                description=f"Invalid price: bid={tick.bid}, ask={tick.ask}",
                raw_data=tick.to_dict(),
                source="price_validator"
            )
            anomalies.append(anomaly)
            return False, anomalies
        
        # Check spread
        if tick.spread_bps > self.max_spread_bps:
            anomaly = Anomaly(
                anomaly_type=AnomalyType.SPREAD_ANOMALY,
                symbol=symbol,
                timestamp=tick.timestamp,
                severity=min(1.0, tick.spread_bps / (self.max_spread_bps * 2)),
                description=f"Wide spread: {tick.spread_bps:.1f} bps",
                raw_data=tick.to_dict(),
                source="price_validator"
            )
            anomalies.append(anomaly)
        
        # Check for price spike
        if self.price_history[symbol]:
            last_price = self.price_history[symbol][-1]
            pct_change = abs(tick.mid - last_price) / last_price
            
            if pct_change > self.max_price_change_pct:
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.PRICE_SPIKE,
                    symbol=symbol,
                    timestamp=tick.timestamp,
                    severity=min(1.0, pct_change / (self.max_price_change_pct * 2)),
                    description=f"Price spike: {pct_change:.2%} change",
                    raw_data={'last_price': last_price, 'current_price': tick.mid, 'change_pct': pct_change},
                    source="price_validator"
                )
                anomalies.append(anomaly)
        
        # Check for statistical outlier
        if len(self.price_history[symbol]) >= 30:
            prices = list(self.price_history[symbol])
            mean = np.mean(prices)
            std = np.std(prices)
            
            if std > 0:
                z_score = abs(tick.mid - mean) / std
                if z_score > self.outlier_std_threshold:
                    anomaly = Anomaly(
                        anomaly_type=AnomalyType.PRICE_SPIKE,
                        symbol=symbol,
                        timestamp=tick.timestamp,
                        severity=min(1.0, z_score / (self.outlier_std_threshold * 2)),
                        description=f"Statistical outlier: z-score={z_score:.2f}",
                        raw_data={'price': tick.mid, 'mean': mean, 'std': std, 'z_score': z_score},
                        source="price_validator"
                    )
                    anomalies.append(anomaly)
        
        # Update history
        self.price_history[symbol].append(tick.mid)
        
        # Determine validity (critical anomalies make it invalid)
        critical_types = {AnomalyType.PRICE_ZERO, AnomalyType.PRICE_NEGATIVE}
        is_valid = not any(a.anomaly_type in critical_types for a in anomalies)
        
        return is_valid, anomalies


# =============================================================================
# CROSS-VENUE VALIDATOR
# =============================================================================

class CrossVenueValidator:
    """
    Validates price consistency across multiple venues
    
    Detects:
    - Price divergence between exchanges
    - Arbitrage opportunities (which may indicate stale data)
    - Venue-specific anomalies
    """
    
    def __init__(
        self,
        max_divergence_bps: float = 10,  # 0.1% max divergence
        min_venues: int = 2
    ):
        self.max_divergence_bps = max_divergence_bps
        self.min_venues = min_venues
        
        # Latest prices by venue
        self.venue_prices: Dict[str, Dict[str, Tuple[float, datetime]]] = {}  # symbol -> {venue -> (price, timestamp)}
    
    def update_price(self, symbol: str, venue: str, price: float, timestamp: datetime):
        """Update price for venue"""
        if symbol not in self.venue_prices:
            self.venue_prices[symbol] = {}
        
        self.venue_prices[symbol][venue] = (price, timestamp)
    
    def validate(self, symbol: str, max_age_seconds: float = 5.0) -> Tuple[bool, List[Anomaly]]:
        """
        Validate cross-venue consistency
        
        Returns: (is_valid, anomalies)
        """
        anomalies = []
        
        if symbol not in self.venue_prices:
            return True, []
        
        now = datetime.utcnow()
        venue_data = self.venue_prices[symbol]
        
        # Filter to recent prices
        recent_prices = {}
        for venue, (price, timestamp) in venue_data.items():
            age = (now - timestamp).total_seconds()
            if age <= max_age_seconds:
                recent_prices[venue] = price
        
        if len(recent_prices) < self.min_venues:
            return True, []  # Not enough venues to compare
        
        # Calculate reference price (median)
        prices = list(recent_prices.values())
        reference = np.median(prices)
        
        # Check each venue
        for venue, price in recent_prices.items():
            divergence_bps = abs(price - reference) / reference * 10000
            
            if divergence_bps > self.max_divergence_bps:
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.CROSS_VENUE_DIVERGENCE,
                    symbol=symbol,
                    timestamp=now,
                    severity=min(1.0, divergence_bps / (self.max_divergence_bps * 2)),
                    description=f"{venue} price divergence: {divergence_bps:.1f} bps from median",
                    raw_data={
                        'venue': venue,
                        'price': price,
                        'reference': reference,
                        'divergence_bps': divergence_bps,
                        'all_prices': recent_prices
                    },
                    source="cross_venue_validator"
                )
                anomalies.append(anomaly)
        
        return len(anomalies) == 0, anomalies


# =============================================================================
# STALENESS DETECTOR
# =============================================================================

class StalenessDetector:
    """
    Detects stale data
    
    Tracks:
    - Time since last update
    - Expected update frequency
    - Gap patterns
    """
    
    def __init__(
        self,
        stale_threshold_seconds: float = 60.0,
        expected_frequency_hz: float = 1.0  # Expected updates per second
    ):
        self.stale_threshold_seconds = stale_threshold_seconds
        self.expected_frequency_hz = expected_frequency_hz
        
        # Last update times
        self.last_updates: Dict[str, datetime] = {}
        
        # Update frequency tracking
        self.update_counts: Dict[str, int] = {}
        self.frequency_window_start: Dict[str, datetime] = {}
    
    def record_update(self, symbol: str, timestamp: datetime):
        """Record data update"""
        self.last_updates[symbol] = timestamp
        
        # Track frequency
        if symbol not in self.frequency_window_start:
            self.frequency_window_start[symbol] = timestamp
            self.update_counts[symbol] = 0
        
        self.update_counts[symbol] += 1
        
        # Reset window every minute
        window_duration = (timestamp - self.frequency_window_start[symbol]).total_seconds()
        if window_duration >= 60:
            self.frequency_window_start[symbol] = timestamp
            self.update_counts[symbol] = 1
    
    def check_staleness(self, symbol: str) -> Tuple[bool, Optional[Anomaly]]:
        """
        Check if data is stale
        
        Returns: (is_stale, anomaly if stale)
        """
        if symbol not in self.last_updates:
            return False, None
        
        now = datetime.utcnow()
        age = (now - self.last_updates[symbol]).total_seconds()
        
        if age > self.stale_threshold_seconds:
            anomaly = Anomaly(
                anomaly_type=AnomalyType.STALE_DATA,
                symbol=symbol,
                timestamp=now,
                severity=min(1.0, age / (self.stale_threshold_seconds * 2)),
                description=f"Stale data: {age:.1f}s since last update",
                raw_data={
                    'last_update': self.last_updates[symbol].isoformat(),
                    'age_seconds': age,
                    'threshold_seconds': self.stale_threshold_seconds
                },
                source="staleness_detector"
            )
            return True, anomaly
        
        return False, None
    
    def get_frequency(self, symbol: str) -> float:
        """Get current update frequency in Hz"""
        if symbol not in self.frequency_window_start:
            return 0.0
        
        now = datetime.utcnow()
        window_duration = (now - self.frequency_window_start[symbol]).total_seconds()
        
        if window_duration <= 0:
            return 0.0
        
        return self.update_counts.get(symbol, 0) / window_duration


# =============================================================================
# MASTER DATA VALIDATOR
# =============================================================================

class DataValidationSystem:
    """
    Master data validation system
    
    Coordinates all validators and provides unified interface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # Initialize components
        self.timestamp_sync = TimestampSynchronizer()
        self.sequence_validator = SequenceValidator()
        self.price_validator = PriceValidator(
            max_price_change_pct=config.get('max_price_change_pct', 0.10),
            max_spread_bps=config.get('max_spread_bps', 100)
        )
        self.cross_venue_validator = CrossVenueValidator(
            max_divergence_bps=config.get('max_divergence_bps', 10)
        )
        self.staleness_detector = StalenessDetector(
            stale_threshold_seconds=config.get('stale_threshold_seconds', 60)
        )
        
        # Metrics tracking
        self.metrics: Dict[str, DataQualityMetrics] = {}
        self.all_anomalies: List[Anomaly] = []
        self.max_anomaly_history = 10000
        
        # Callbacks
        self.on_anomaly: Optional[Callable[[Anomaly], None]] = None
        self.on_quality_change: Optional[Callable[[str, DataQuality], None]] = None
        
        # Initial NTP sync
        self.timestamp_sync.sync()
        
        logger.info("DataValidationSystem initialized")
    
    def validate_tick(self, tick: TickData) -> ValidationResult:
        """
        Validate a single tick
        
        Returns comprehensive validation result
        """
        anomalies = []
        warnings = []
        
        symbol = tick.symbol
        
        # Initialize metrics if needed
        if symbol not in self.metrics:
            self.metrics[symbol] = DataQualityMetrics(
                symbol=symbol,
                period_start=tick.timestamp,
                period_end=tick.timestamp
            )
        
        metrics = self.metrics[symbol]
        metrics.total_ticks += 1
        metrics.period_end = tick.timestamp
        
        # 1. Timestamp validation
        ts_valid, drift_ms = self.timestamp_sync.validate_timestamp(tick.timestamp)
        if not ts_valid:
            anomaly = Anomaly(
                anomaly_type=AnomalyType.TIMESTAMP_DRIFT,
                symbol=symbol,
                timestamp=tick.timestamp,
                severity=min(1.0, drift_ms / 10000),
                description=f"Timestamp drift: {drift_ms:.0f}ms",
                raw_data={'drift_ms': drift_ms},
                source="timestamp_sync"
            )
            anomalies.append(anomaly)
        
        # 2. Sequence validation
        if tick.sequence is not None:
            seq_valid, seq_anomalies = self.sequence_validator.validate(symbol, tick.sequence)
            anomalies.extend(seq_anomalies)
        
        # 3. Price validation
        price_valid, price_anomalies = self.price_validator.validate(tick)
        anomalies.extend(price_anomalies)
        
        # 4. Cross-venue update and validation
        self.cross_venue_validator.update_price(symbol, tick.exchange, tick.mid, tick.timestamp)
        cv_valid, cv_anomalies = self.cross_venue_validator.validate(symbol)
        anomalies.extend(cv_anomalies)
        
        # 5. Staleness tracking
        self.staleness_detector.record_update(symbol, tick.timestamp)
        
        # Update metrics
        for anomaly in anomalies:
            anomaly_type = anomaly.anomaly_type.value
            metrics.anomaly_counts[anomaly_type] = metrics.anomaly_counts.get(anomaly_type, 0) + 1
            
            # Trigger callback
            if self.on_anomaly:
                self.on_anomaly(anomaly)
        
        # Store anomalies
        self.all_anomalies.extend(anomalies)
        if len(self.all_anomalies) > self.max_anomaly_history:
            self.all_anomalies = self.all_anomalies[-self.max_anomaly_history:]
        
        # Calculate quality score
        score = self._calculate_quality_score(anomalies)
        quality = self._score_to_quality(score)
        
        # Update metrics
        if score >= 0.9:
            metrics.valid_ticks += 1
        else:
            metrics.invalid_ticks += 1
        
        # Determine validity
        critical_types = {
            AnomalyType.PRICE_ZERO,
            AnomalyType.PRICE_NEGATIVE,
            AnomalyType.STALE_DATA
        }
        is_valid = not any(a.anomaly_type in critical_types for a in anomalies)
        
        return ValidationResult(
            is_valid=is_valid,
            quality=quality,
            score=score,
            anomalies=anomalies,
            warnings=warnings
        )
    
    def check_staleness(self, symbol: str) -> Tuple[bool, Optional[Anomaly]]:
        """Check if symbol data is stale"""
        return self.staleness_detector.check_staleness(symbol)
    
    def get_metrics(self, symbol: str) -> Optional[DataQualityMetrics]:
        """Get quality metrics for symbol"""
        return self.metrics.get(symbol)
    
    def get_all_metrics(self) -> Dict[str, DataQualityMetrics]:
        """Get all quality metrics"""
        return self.metrics.copy()
    
    def get_recent_anomalies(self, limit: int = 100) -> List[Anomaly]:
        """Get recent anomalies"""
        return self.all_anomalies[-limit:]
    
    def get_anomalies_by_type(self, anomaly_type: AnomalyType) -> List[Anomaly]:
        """Get anomalies of specific type"""
        return [a for a in self.all_anomalies if a.anomaly_type == anomaly_type]
    
    def _calculate_quality_score(self, anomalies: List[Anomaly]) -> float:
        """Calculate quality score from anomalies"""
        if not anomalies:
            return 1.0
        
        # Weight anomalies by severity
        total_penalty = sum(a.severity for a in anomalies)
        
        # Score decreases with more/worse anomalies
        score = max(0.0, 1.0 - total_penalty * 0.2)
        
        return score
    
    def _score_to_quality(self, score: float) -> DataQuality:
        """Convert score to quality level"""
        if score >= 0.95:
            return DataQuality.EXCELLENT
        elif score >= 0.85:
            return DataQuality.GOOD
        elif score >= 0.70:
            return DataQuality.DEGRADED
        elif score >= 0.50:
            return DataQuality.POOR
        else:
            return DataQuality.UNUSABLE


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_validation_system(config: Optional[Dict[str, Any]] = None) -> DataValidationSystem:
    """Create data validation system"""
    return DataValidationSystem(config)


def validate_ohlcv_bar(
    symbol: str,
    timestamp: datetime,
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: float
) -> ValidationResult:
    """
    Validate OHLCV bar data
    
    Checks:
    - High >= Low
    - High >= Open, Close
    - Low <= Open, Close
    - All prices positive
    - Volume non-negative
    """
    anomalies = []
    warnings = []
    
    # Basic price checks
    if high < low:
        anomalies.append(Anomaly(
            anomaly_type=AnomalyType.PRICE_SPIKE,
            symbol=symbol,
            timestamp=timestamp,
            severity=1.0,
            description=f"High ({high}) < Low ({low})",
            raw_data={'high': high, 'low': low},
            source="ohlcv_validator"
        ))
    
    if high < open_price or high < close:
        anomalies.append(Anomaly(
            anomaly_type=AnomalyType.PRICE_SPIKE,
            symbol=symbol,
            timestamp=timestamp,
            severity=0.8,
            description=f"High ({high}) < Open ({open_price}) or Close ({close})",
            raw_data={'high': high, 'open': open_price, 'close': close},
            source="ohlcv_validator"
        ))
    
    if low > open_price or low > close:
        anomalies.append(Anomaly(
            anomaly_type=AnomalyType.PRICE_SPIKE,
            symbol=symbol,
            timestamp=timestamp,
            severity=0.8,
            description=f"Low ({low}) > Open ({open_price}) or Close ({close})",
            raw_data={'low': low, 'open': open_price, 'close': close},
            source="ohlcv_validator"
        ))
    
    # Zero/negative checks
    for name, value in [('open', open_price), ('high', high), ('low', low), ('close', close)]:
        if value <= 0:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.PRICE_ZERO if value == 0 else AnomalyType.PRICE_NEGATIVE,
                symbol=symbol,
                timestamp=timestamp,
                severity=1.0,
                description=f"{name} price is {value}",
                raw_data={name: value},
                source="ohlcv_validator"
            ))
    
    if volume < 0:
        anomalies.append(Anomaly(
            anomaly_type=AnomalyType.VOLUME_SPIKE,
            symbol=symbol,
            timestamp=timestamp,
            severity=1.0,
            description=f"Negative volume: {volume}",
            raw_data={'volume': volume},
            source="ohlcv_validator"
        ))
    
    # Calculate score
    score = 1.0 - len(anomalies) * 0.2
    score = max(0.0, score)
    
    quality = DataQuality.EXCELLENT if score >= 0.95 else \
              DataQuality.GOOD if score >= 0.85 else \
              DataQuality.DEGRADED if score >= 0.70 else \
              DataQuality.POOR if score >= 0.50 else \
              DataQuality.UNUSABLE
    
    return ValidationResult(
        is_valid=len(anomalies) == 0,
        quality=quality,
        score=score,
        anomalies=anomalies,
        warnings=warnings
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create validation system
    validator = create_validation_system()
    
    # Test with sample tick
    tick = TickData(
        symbol="AAPL",
        timestamp=datetime.utcnow(),
        bid=150.00,
        ask=150.05,
        bid_size=100,
        ask_size=100,
        last_price=150.02,
        last_size=10,
        volume=1000000,
        sequence=1,
        source="test",
        exchange="NASDAQ"
    )
    
    result = validator.validate_tick(tick)
    print(f"Validation result: {result.to_dict()}")
    
    # Test OHLCV validation
    ohlcv_result = validate_ohlcv_bar(
        symbol="AAPL",
        timestamp=datetime.utcnow(),
        open_price=150.00,
        high=152.00,
        low=149.00,
        close=151.50,
        volume=5000000
    )
    print(f"OHLCV validation: {ohlcv_result.to_dict()}")

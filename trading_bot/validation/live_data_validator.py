"""
Live Data Validation System
============================
Real-time validation of live market data feeds.
Ensures data quality before use in trading decisions.
"""

import asyncio
import logging
import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
import numpy

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class ValidationResult(Enum):
    """Validation result."""
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"
    STALE = "stale"
    ANOMALY = "anomaly"


class DataQuality(Enum):
    """Data quality levels."""
    EXCELLENT = "excellent"  # 95%+
    GOOD = "good"           # 80-95%
    ACCEPTABLE = "acceptable"  # 60-80%
    POOR = "poor"           # 40-60%
    UNUSABLE = "unusable"   # <40%


@dataclass
class ValidationConfig:
    """Validation configuration."""
    staleness_threshold_seconds: float = 30.0
    price_change_threshold: float = 0.05  # 5% max change
    volume_spike_threshold: float = 10.0  # 10x average
    spread_threshold: float = 0.01  # 1% max spread
    z_score_threshold: float = 3.0  # Standard deviations
    min_tick_interval_ms: float = 10.0
    max_tick_interval_ms: float = 60000.0
    history_size: int = 1000
    enable_anomaly_detection: bool = True
    enable_sequence_check: bool = True


@dataclass
class ValidationReport:
    """Validation report for a data point."""
    result: ValidationResult
    quality_score: float
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OHLCVData:
    """OHLCV data point."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    def validate_basic(self) -> Tuple[bool, List[str]]:
        """Basic OHLCV validation."""
        try:
            issues = []
        
            if self.high < self.low:
                issues.append("High < Low")
            if self.high < self.open:
                issues.append("High < Open")
            if self.high < self.close:
                issues.append("High < Close")
            if self.low > self.open:
                issues.append("Low > Open")
            if self.low > self.close:
                issues.append("Low > Close")
            if self.volume < 0:
                issues.append("Negative volume")
            if any(v <= 0 for v in [self.open, self.high, self.low, self.close]):
                issues.append("Non-positive price")
        
            return len(issues) == 0, issues
        except Exception as e:
            logger.error(f"Error in validate_basic: {e}")
            raise


@dataclass
class TickData:
    """Tick data point."""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    last: float
    volume: float
    
    def validate_basic(self) -> Tuple[bool, List[str]]:
        """Basic tick validation."""
        try:
            issues = []
        
            if self.bid <= 0:
                issues.append("Non-positive bid")
            if self.ask <= 0:
                issues.append("Non-positive ask")
            if self.bid > self.ask:
                issues.append("Bid > Ask (crossed market)")
            if self.volume < 0:
                issues.append("Negative volume")
        
            return len(issues) == 0, issues
        except Exception as e:
            logger.error(f"Error in validate_basic: {e}")
            raise


# ============================================================================
# VALIDATORS
# ============================================================================

class PriceValidator:
    """Validates price data."""
    
    def __init__(self, config: ValidationConfig):
        try:
            self.config = config
            self._price_history: Dict[str, deque] = {}
            self._lock = threading.Lock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _get_history(self, symbol: str) -> deque:
        """Get price history for symbol."""
        try:
            if symbol not in self._price_history:
                self._price_history[symbol] = deque(maxlen=self.config.history_size)
            return self._price_history[symbol]
        except Exception as e:
            logger.error(f"Error in _get_history: {e}")
            raise
    
    def validate(self, symbol: str, price: float) -> ValidationReport:
        """Validate a price."""
        try:
            issues = []
            warnings = []
        
            with self._lock:
                history = self._get_history(symbol)
            
                # Basic validation
                if price <= 0:
                    return ValidationReport(
                        result=ValidationResult.INVALID,
                        quality_score=0.0,
                        issues=["Non-positive price"],
                    )
            
                if len(history) > 0:
                    # Check price change
                    last_price = history[-1]
                    change = abs(price - last_price) / last_price
                
                    if change > self.config.price_change_threshold:
                        issues.append(f"Large price change: {change:.2%}")
                    elif change > self.config.price_change_threshold * 0.5:
                        warnings.append(f"Significant price change: {change:.2%}")
                
                    # Z-score check
                    if len(history) >= 20:
                        prices = list(history)
                        mean = statistics.mean(prices)
                        std = statistics.stdev(prices) if len(prices) > 1 else 0
                    
                        if std > 0:
                            z_score = abs(price - mean) / std
                            if z_score > self.config.z_score_threshold:
                                warnings.append(f"High z-score: {z_score:.2f}")
            
                # Add to history
                history.append(price)
        
            # Calculate quality score
            quality_score = 1.0
            quality_score -= len(issues) * 0.3
            quality_score -= len(warnings) * 0.1
            quality_score = max(0.0, min(1.0, quality_score))
        
            if issues:
                result = ValidationResult.INVALID
            elif warnings:
                result = ValidationResult.WARNING
            else:
                result = ValidationResult.VALID
        
            return ValidationReport(
                result=result,
                quality_score=quality_score,
                issues=issues,
                warnings=warnings,
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class VolumeValidator:
    """Validates volume data."""
    
    def __init__(self, config: ValidationConfig):
        try:
            self.config = config
            self._volume_history: Dict[str, deque] = {}
            self._lock = threading.Lock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _get_history(self, symbol: str) -> deque:
        """Get volume history for symbol."""
        try:
            if symbol not in self._volume_history:
                self._volume_history[symbol] = deque(maxlen=self.config.history_size)
            return self._volume_history[symbol]
        except Exception as e:
            logger.error(f"Error in _get_history: {e}")
            raise
    
    def validate(self, symbol: str, volume: float) -> ValidationReport:
        """Validate volume."""
        try:
            issues = []
            warnings = []
        
            with self._lock:
                history = self._get_history(symbol)
            
                # Basic validation
                if volume < 0:
                    return ValidationReport(
                        result=ValidationResult.INVALID,
                        quality_score=0.0,
                        issues=["Negative volume"],
                    )
            
                if len(history) >= 10:
                    avg_volume = statistics.mean(history)
                
                    if avg_volume > 0:
                        ratio = volume / avg_volume
                    
                        if ratio > self.config.volume_spike_threshold:
                            warnings.append(f"Volume spike: {ratio:.1f}x average")
                        elif volume == 0 and avg_volume > 0:
                            warnings.append("Zero volume")
            
                # Add to history
                history.append(volume)
        
            quality_score = 1.0 - len(warnings) * 0.1
        
            return ValidationReport(
                result=ValidationResult.WARNING if warnings else ValidationResult.VALID,
                quality_score=max(0.0, quality_score),
                warnings=warnings,
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class SpreadValidator:
    """Validates bid-ask spread."""
    
    def __init__(self, config: ValidationConfig):
        try:
            self.config = config
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(self, bid: float, ask: float) -> ValidationReport:
        """Validate spread."""
        try:
            issues = []
            warnings = []
        
            if bid <= 0 or ask <= 0:
                return ValidationReport(
                    result=ValidationResult.INVALID,
                    quality_score=0.0,
                    issues=["Non-positive bid/ask"],
                )
        
            if bid > ask:
                return ValidationReport(
                    result=ValidationResult.INVALID,
                    quality_score=0.0,
                    issues=["Crossed market (bid > ask)"],
                )
        
            mid = (bid + ask) / 2
            spread = (ask - bid) / mid
        
            if spread > self.config.spread_threshold:
                warnings.append(f"Wide spread: {spread:.4%}")
        
            quality_score = 1.0 - (spread / self.config.spread_threshold) * 0.5
        
            return ValidationReport(
                result=ValidationResult.WARNING if warnings else ValidationResult.VALID,
                quality_score=max(0.0, min(1.0, quality_score)),
                warnings=warnings,
                metadata={'spread': spread},
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class StalenessValidator:
    """Validates data freshness."""
    
    def __init__(self, config: ValidationConfig):
        try:
            self.config = config
            self._last_update: Dict[str, datetime] = {}
            self._lock = threading.Lock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(self, symbol: str, data_timestamp: datetime) -> ValidationReport:
        """Validate data freshness."""
        try:
            now = datetime.utcnow()
        
            # Check data timestamp
            age = (now - data_timestamp).total_seconds()
        
            if age > self.config.staleness_threshold_seconds:
                return ValidationReport(
                    result=ValidationResult.STALE,
                    quality_score=0.0,
                    issues=[f"Data is {age:.1f}s old (threshold: {self.config.staleness_threshold_seconds}s)"],
                    latency_ms=age * 1000,
                )
        
            with self._lock:
                # Check update interval
                if symbol in self._last_update:
                    interval = (data_timestamp - self._last_update[symbol]).total_seconds() * 1000
                
                    if interval < self.config.min_tick_interval_ms:
                        return ValidationReport(
                            result=ValidationResult.WARNING,
                            quality_score=0.8,
                            warnings=[f"Very fast updates: {interval:.1f}ms"],
                            latency_ms=age * 1000,
                        )
                
                    if interval > self.config.max_tick_interval_ms:
                        return ValidationReport(
                            result=ValidationResult.WARNING,
                            quality_score=0.7,
                            warnings=[f"Slow updates: {interval/1000:.1f}s"],
                            latency_ms=age * 1000,
                        )
            
                self._last_update[symbol] = data_timestamp
        
            quality_score = 1.0 - (age / self.config.staleness_threshold_seconds) * 0.5
        
            return ValidationReport(
                result=ValidationResult.VALID,
                quality_score=max(0.0, quality_score),
                latency_ms=age * 1000,
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class SequenceValidator:
    """Validates data sequence."""
    
    def __init__(self, config: ValidationConfig):
        try:
            self.config = config
            self._last_sequence: Dict[str, int] = {}
            self._lock = threading.Lock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(self, symbol: str, sequence: int) -> ValidationReport:
        """Validate sequence number."""
        try:
            with self._lock:
                if symbol in self._last_sequence:
                    expected = self._last_sequence[symbol] + 1
                
                    if sequence < self._last_sequence[symbol]:
                        return ValidationReport(
                            result=ValidationResult.INVALID,
                            quality_score=0.0,
                            issues=[f"Out of order: got {sequence}, expected >= {expected}"],
                        )
                
                    if sequence > expected:
                        gap = sequence - expected
                        return ValidationReport(
                            result=ValidationResult.WARNING,
                            quality_score=0.8,
                            warnings=[f"Sequence gap: {gap} messages missed"],
                        )
            
                self._last_sequence[symbol] = sequence
        
            return ValidationReport(
                result=ValidationResult.VALID,
                quality_score=1.0,
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class AnomalyDetector:
    """Detects anomalies in data."""
    
    def __init__(self, config: ValidationConfig):
        try:
            self.config = config
            self._data_history: Dict[str, deque] = {}
            self._lock = threading.Lock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _get_history(self, key: str) -> deque:
        """Get data history."""
        try:
            if key not in self._data_history:
                self._data_history[key] = deque(maxlen=self.config.history_size)
            return self._data_history[key]
        except Exception as e:
            logger.error(f"Error in _get_history: {e}")
            raise
    
    def detect(self, symbol: str, field: str, value: float) -> ValidationReport:
        """Detect anomalies."""
        try:
            key = f"{symbol}:{field}"
        
            with self._lock:
                history = self._get_history(key)
            
                if len(history) < 30:
                    history.append(value)
                    return ValidationReport(
                        result=ValidationResult.VALID,
                        quality_score=1.0,
                        metadata={'status': 'warming_up'},
                    )
            
                # Calculate statistics
                data = np.array(history)
                mean = np.mean(data)
                std = np.std(data)
            
                if std > 0:
                    z_score = abs(value - mean) / std
                
                    if z_score > self.config.z_score_threshold:
                        history.append(value)
                        return ValidationReport(
                            result=ValidationResult.ANOMALY,
                            quality_score=0.5,
                            warnings=[f"Anomaly detected: z-score={z_score:.2f}"],
                            metadata={'z_score': z_score, 'mean': mean, 'std': std},
                        )
            
                history.append(value)
        
            return ValidationReport(
                result=ValidationResult.VALID,
                quality_score=1.0,
            )
        except Exception as e:
            logger.error(f"Error in detect: {e}")
            raise


# ============================================================================
# LIVE DATA VALIDATOR
# ============================================================================

class LiveDataValidator:
    """
    Comprehensive live data validator.
    Combines all validators for complete data validation.
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        try:
            self.config = config or ValidationConfig()
        
            self.price_validator = PriceValidator(self.config)
            self.volume_validator = VolumeValidator(self.config)
            self.spread_validator = SpreadValidator(self.config)
            self.staleness_validator = StalenessValidator(self.config)
            self.sequence_validator = SequenceValidator(self.config)
            self.anomaly_detector = AnomalyDetector(self.config)
        
            self._stats: Dict[str, Dict] = {}
            self._lock = threading.Lock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate_ohlcv(self, data: OHLCVData) -> ValidationReport:
        """Validate OHLCV data."""
        try:
            all_issues = []
            all_warnings = []
            quality_scores = []
        
            # Basic OHLCV validation
            is_valid, issues = data.validate_basic()
            if not is_valid:
                all_issues.extend(issues)
        
            # Price validation
            price_report = self.price_validator.validate(data.symbol, data.close)
            all_issues.extend(price_report.issues)
            all_warnings.extend(price_report.warnings)
            quality_scores.append(price_report.quality_score)
        
            # Volume validation
            volume_report = self.volume_validator.validate(data.symbol, data.volume)
            all_warnings.extend(volume_report.warnings)
            quality_scores.append(volume_report.quality_score)
        
            # Staleness validation
            staleness_report = self.staleness_validator.validate(data.symbol, data.timestamp)
            all_issues.extend(staleness_report.issues)
            all_warnings.extend(staleness_report.warnings)
            quality_scores.append(staleness_report.quality_score)
        
            # Anomaly detection
            if self.config.enable_anomaly_detection:
                anomaly_report = self.anomaly_detector.detect(data.symbol, "close", data.close)
                all_warnings.extend(anomaly_report.warnings)
                quality_scores.append(anomaly_report.quality_score)
        
            # Calculate overall quality
            quality_score = statistics.mean(quality_scores) if quality_scores else 0.0
        
            # Determine result
            if all_issues:
                result = ValidationResult.INVALID
            elif any(r.result == ValidationResult.STALE for r in [staleness_report]):
                result = ValidationResult.STALE
            elif all_warnings:
                result = ValidationResult.WARNING
            else:
                result = ValidationResult.VALID
        
            # Update stats
            self._update_stats(data.symbol, result)
        
            return ValidationReport(
                result=result,
                quality_score=quality_score,
                issues=all_issues,
                warnings=all_warnings,
                latency_ms=staleness_report.latency_ms,
            )
        except Exception as e:
            logger.error(f"Error in validate_ohlcv: {e}")
            raise
    
    def validate_tick(self, data: TickData) -> ValidationReport:
        """Validate tick data."""
        try:
            all_issues = []
            all_warnings = []
            quality_scores = []
        
            # Basic tick validation
            is_valid, issues = data.validate_basic()
            if not is_valid:
                all_issues.extend(issues)
        
            # Spread validation
            spread_report = self.spread_validator.validate(data.bid, data.ask)
            all_issues.extend(spread_report.issues)
            all_warnings.extend(spread_report.warnings)
            quality_scores.append(spread_report.quality_score)
        
            # Price validation
            price_report = self.price_validator.validate(data.symbol, data.last)
            all_issues.extend(price_report.issues)
            all_warnings.extend(price_report.warnings)
            quality_scores.append(price_report.quality_score)
        
            # Staleness validation
            staleness_report = self.staleness_validator.validate(data.symbol, data.timestamp)
            all_issues.extend(staleness_report.issues)
            all_warnings.extend(staleness_report.warnings)
            quality_scores.append(staleness_report.quality_score)
        
            # Calculate overall quality
            quality_score = statistics.mean(quality_scores) if quality_scores else 0.0
        
            # Determine result
            if all_issues:
                result = ValidationResult.INVALID
            elif staleness_report.result == ValidationResult.STALE:
                result = ValidationResult.STALE
            elif all_warnings:
                result = ValidationResult.WARNING
            else:
                result = ValidationResult.VALID
        
            # Update stats
            self._update_stats(data.symbol, result)
        
            return ValidationReport(
                result=result,
                quality_score=quality_score,
                issues=all_issues,
                warnings=all_warnings,
                latency_ms=staleness_report.latency_ms,
            )
        except Exception as e:
            logger.error(f"Error in validate_tick: {e}")
            raise
    
    def _update_stats(self, symbol: str, result: ValidationResult):
        """Update validation statistics."""
        try:
            with self._lock:
                if symbol not in self._stats:
                    self._stats[symbol] = {
                        'total': 0,
                        'valid': 0,
                        'warning': 0,
                        'invalid': 0,
                        'stale': 0,
                        'anomaly': 0,
                    }
            
                self._stats[symbol]['total'] += 1
                self._stats[symbol][result.value] += 1
        except Exception as e:
            logger.error(f"Error in _update_stats: {e}")
            raise
    
    def get_quality(self, symbol: str) -> DataQuality:
        """Get data quality for symbol."""
        try:
            with self._lock:
                if symbol not in self._stats:
                    return DataQuality.ACCEPTABLE
            
                stats = self._stats[symbol]
                if stats['total'] == 0:
                    return DataQuality.ACCEPTABLE
            
                valid_rate = stats['valid'] / stats['total']
            
                if valid_rate >= 0.95:
                    return DataQuality.EXCELLENT
                elif valid_rate >= 0.80:
                    return DataQuality.GOOD
                elif valid_rate >= 0.60:
                    return DataQuality.ACCEPTABLE
                elif valid_rate >= 0.40:
                    return DataQuality.POOR
                else:
                    return DataQuality.UNUSABLE
        except Exception as e:
            logger.error(f"Error in get_quality: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """Get validation statistics."""
        try:
            with self._lock:
                return {
                    symbol: {
                        **stats,
                        'valid_rate': stats['valid'] / stats['total'] if stats['total'] > 0 else 0,
                        'quality': self.get_quality(symbol).value,
                    }
                    for symbol, stats in self._stats.items()
                }
        except Exception as e:
            logger.error(f"Error in get_stats: {e}")
            raise
    
    def reset_stats(self, symbol: Optional[str] = None):
        """Reset statistics."""
        try:
            with self._lock:
                if symbol:
                    self._stats.pop(symbol, None)
                else:
                    self._stats.clear()
        except Exception as e:
            logger.error(f"Error in reset_stats: {e}")
            raise


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_live_validator: Optional[LiveDataValidator] = None


def get_live_validator() -> LiveDataValidator:
    """Get global live data validator."""
    try:
        global _live_validator
        if _live_validator is None:
            _live_validator = LiveDataValidator()
        return _live_validator
    except Exception as e:
        logger.error(f"Error in get_live_validator: {e}")
        raise


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'ValidationResult', 'DataQuality', 'ValidationConfig', 'ValidationReport',
    'OHLCVData', 'TickData', 'PriceValidator', 'VolumeValidator',
    'SpreadValidator', 'StalenessValidator', 'SequenceValidator',
    'AnomalyDetector', 'LiveDataValidator', 'get_live_validator',
]

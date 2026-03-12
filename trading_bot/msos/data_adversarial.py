"""
AlphaAlgo MSOS - Data Adversarial Defense Module

DATA ADVERSARIAL DEFENSE:
- Cross-validate all external data against independent vendors
- Detect fake news injection, coordinated manipulation, spoofed data
- Assign trust scores to every data source
- Auto-disable any source whose trust score degrades

Your data lies to you. Most systems don't check.

Author: AlphaAlgo MSOS
"""

import hashlib
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class DataTrustLevel(Enum):
    """Data trust levels"""
    VERIFIED = auto()      # Cross-validated, high confidence
    TRUSTED = auto()       # Single source, historically reliable
    UNCERTAIN = auto()     # Some discrepancies detected
    SUSPICIOUS = auto()    # Significant issues detected
    UNTRUSTED = auto()     # Known bad data
    QUARANTINED = auto()   # Isolated for investigation


class ContaminationType(Enum):
    """Types of data contamination"""
    NONE = auto()
    STALE_DATA = auto()
    MISSING_DATA = auto()
    OUTLIER = auto()
    VENDOR_BIAS = auto()
    MANIPULATION = auto()
    SPOOFING = auto()
    FAKE_NEWS = auto()
    COORDINATED_ATTACK = auto()
    STRUCTURAL_CHANGE = auto()


@dataclass
class DataTrustScore:
    """Trust score for a data source"""
    source_id: str
    trust_level: DataTrustLevel
    score: float  # 0-1
    reliability_history: float = 1.0
    latency_score: float = 1.0
    accuracy_score: float = 1.0
    consistency_score: float = 1.0
    validation_count: int = 0
    failure_count: int = 0
    last_validated: float = 0.0
    is_disabled: bool = False
    disable_reason: str = ""
    
    def calculate_score(self) -> float:
        """Calculate overall trust score"""
        try:
            self.score = (
                self.reliability_history * 0.3 +
                self.latency_score * 0.2 +
                self.accuracy_score * 0.3 +
                self.consistency_score * 0.2
            )
        
            # Determine trust level
            if self.score >= 0.9:
                self.trust_level = DataTrustLevel.VERIFIED
            elif self.score >= 0.7:
                self.trust_level = DataTrustLevel.TRUSTED
            elif self.score >= 0.5:
                self.trust_level = DataTrustLevel.UNCERTAIN
            elif self.score >= 0.3:
                self.trust_level = DataTrustLevel.SUSPICIOUS
            else:
                self.trust_level = DataTrustLevel.UNTRUSTED
        
            return self.score
        except Exception as e:
            logger.error(f"Error in calculate_score: {e}")
            raise


@dataclass
class VendorBias:
    """Vendor bias detection"""
    vendor_id: str
    bias_direction: float = 0.0  # Positive = bullish bias, negative = bearish
    bias_magnitude: float = 0.0
    systematic_error: float = 0.0
    is_biased: bool = False
    
    def detect_bias(self, vendor_data: List[float], reference_data: List[float]) -> bool:
        """Detect systematic bias in vendor data"""
        try:
            if len(vendor_data) != len(reference_data) or len(vendor_data) < 20:
                return False
        
            errors = np.array(vendor_data) - np.array(reference_data)
        
            self.bias_direction = np.mean(errors)
            self.bias_magnitude = abs(self.bias_direction)
            self.systematic_error = np.std(errors)
        
            # Bias if mean error is significantly non-zero
            self.is_biased = self.bias_magnitude > 0.001  # 0.1% threshold
        
            return self.is_biased
        except Exception as e:
            logger.error(f"Error in detect_bias: {e}")
            raise


@dataclass
class DataContamination:
    """Data contamination detection result"""
    contamination_type: ContaminationType
    severity: float  # 0-1
    affected_fields: List[str]
    detection_method: str
    confidence: float
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.contamination_type.name,
            'severity': self.severity,
            'affected_fields': self.affected_fields,
            'detection_method': self.detection_method,
            'confidence': self.confidence,
            'timestamp': self.timestamp
        }


@dataclass
class DataDefenseResult:
    """Result from data adversarial defense"""
    is_clean: bool
    can_use: bool
    trust_score: float
    contaminations: List[DataContamination]
    source_scores: Dict[str, DataTrustScore]
    vendor_biases: Dict[str, VendorBias]
    warnings: List[str]
    reason: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_clean': self.is_clean,
            'can_use': self.can_use,
            'trust_score': self.trust_score,
            'contamination_count': len(self.contaminations),
            'warnings': self.warnings,
            'reason': self.reason,
            'timestamp': self.timestamp
        }


class CrossValidator:
    """Cross-validates data across multiple sources"""
    
    def __init__(self, tolerance: float = 0.001):
        try:
            self.tolerance = tolerance
            self._source_data: Dict[str, Deque[Tuple[float, float]]] = {}  # source -> [(timestamp, value)]
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_data(self, source_id: str, timestamp: float, value: float):
        """Add data point from a source"""
        try:
            if source_id not in self._source_data:
                self._source_data[source_id] = deque(maxlen=1000)
            self._source_data[source_id].append((timestamp, value))
        except Exception as e:
            logger.error(f"Error in add_data: {e}")
            raise
    
    def validate(self, timestamp: float, tolerance_seconds: float = 1.0) -> Tuple[bool, float, List[str]]:
        """
        Cross-validate data at a timestamp.
        
        Returns: (is_valid, consensus_value, discrepant_sources)
        """
        try:
            if len(self._source_data) < 2:
                return True, 0.0, []
        
            # Get values near timestamp from all sources
            values = {}
            for source_id, data in self._source_data.items():
                for ts, val in data:
                    if abs(ts - timestamp) <= tolerance_seconds:
                        values[source_id] = val
                        break
        
            if len(values) < 2:
                return True, 0.0, []
        
            # Calculate consensus (median)
            value_list = list(values.values())
            consensus = np.median(value_list)
        
            # Find discrepancies
            discrepant = []
            for source_id, val in values.items():
                if abs(val - consensus) / (abs(consensus) + 1e-10) > self.tolerance:
                    discrepant.append(source_id)
        
            is_valid = len(discrepant) == 0
            return is_valid, consensus, discrepant
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class ManipulationDetector:
    """Detects market manipulation patterns"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._prices: Deque[float] = deque(maxlen=window_size)
            self._volumes: Deque[float] = deque(maxlen=window_size)
            self._order_imbalances: Deque[float] = deque(maxlen=window_size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, price: float, volume: float, order_imbalance: float = 0.0):
        """Update with new market data"""
        try:
            self._prices.append(price)
            self._volumes.append(volume)
            self._order_imbalances.append(order_imbalance)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def detect_spoofing(self) -> Optional[DataContamination]:
        """Detect spoofing patterns (large orders that disappear)"""
        try:
            if len(self._order_imbalances) < 20:
                return None
        
            imbalances = np.array(list(self._order_imbalances))
        
            # Spoofing: large imbalances that quickly reverse
            changes = np.diff(imbalances)
            reversals = np.sum(np.abs(changes) > np.std(imbalances) * 2)
        
            if reversals > len(imbalances) * 0.2:  # 20% reversal rate
                return DataContamination(
                    contamination_type=ContaminationType.SPOOFING,
                    severity=min(1.0, reversals / len(imbalances)),
                    affected_fields=['order_book', 'order_imbalance'],
                    detection_method='reversal_rate',
                    confidence=0.7
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in detect_spoofing: {e}")
            raise
    
    def detect_wash_trading(self) -> Optional[DataContamination]:
        """Detect wash trading patterns"""
        try:
            if len(self._volumes) < 20:
                return None
        
            volumes = np.array(list(self._volumes))
            prices = np.array(list(self._prices))
        
            # Wash trading: high volume with no price impact
            if np.std(prices) > 0:
                volume_price_corr = np.corrcoef(volumes, np.abs(np.diff(np.append(prices, prices[-1]))))[0, 1]
            
                if abs(volume_price_corr) < 0.1 and np.mean(volumes) > np.median(volumes) * 2:
                    return DataContamination(
                        contamination_type=ContaminationType.MANIPULATION,
                        severity=0.6,
                        affected_fields=['volume', 'trades'],
                        detection_method='volume_price_decorrelation',
                        confidence=0.6
                    )
        
            return None
        except Exception as e:
            logger.error(f"Error in detect_wash_trading: {e}")
            raise
    
    def detect_coordinated_attack(self) -> Optional[DataContamination]:
        """Detect coordinated manipulation"""
        try:
            if len(self._prices) < 50:
                return None
        
            prices = np.array(list(self._prices))
        
            # Sudden, large moves followed by reversal
            returns = np.diff(prices) / prices[:-1]
        
            # Find extreme moves
            extreme_threshold = np.std(returns) * 3
            extreme_moves = np.abs(returns) > extreme_threshold
        
            if np.sum(extreme_moves) >= 3:
                # Check if moves are clustered
                extreme_indices = np.where(extreme_moves)[0]
                if len(extreme_indices) >= 2:
                    gaps = np.diff(extreme_indices)
                    if np.mean(gaps) < 5:  # Clustered within 5 periods
                        return DataContamination(
                            contamination_type=ContaminationType.COORDINATED_ATTACK,
                            severity=0.8,
                            affected_fields=['price', 'returns'],
                            detection_method='clustered_extremes',
                            confidence=0.7
                        )
        
            return None
        except Exception as e:
            logger.error(f"Error in detect_coordinated_attack: {e}")
            raise


class NewsValidator:
    """Validates news and sentiment data"""
    
    def __init__(self):
        try:
            self._news_hashes: Set[str] = set()
            self._sentiment_history: Deque[Tuple[float, float]] = deque(maxlen=1000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate_news(self, news_item: Dict[str, Any]) -> Optional[DataContamination]:
        """Validate a news item for manipulation"""
        # Check for duplicate/recycled news
        try:
            content_hash = hashlib.md5(
                str(news_item.get('content', '')).encode()
            ).hexdigest()
        
            if content_hash in self._news_hashes:
                return DataContamination(
                    contamination_type=ContaminationType.FAKE_NEWS,
                    severity=0.5,
                    affected_fields=['news'],
                    detection_method='duplicate_detection',
                    confidence=0.9
                )
        
            self._news_hashes.add(content_hash)
        
            # Check for suspicious patterns
            content = news_item.get('content', '').lower()
        
            # Pump and dump keywords
            pump_keywords = ['guaranteed', 'moon', '1000%', 'insider', 'secret']
            if any(kw in content for kw in pump_keywords):
                return DataContamination(
                    contamination_type=ContaminationType.FAKE_NEWS,
                    severity=0.7,
                    affected_fields=['news', 'sentiment'],
                    detection_method='keyword_detection',
                    confidence=0.6
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in validate_news: {e}")
            raise
    
    def detect_sentiment_manipulation(
        self,
        current_sentiment: float,
        price_change: float
    ) -> Optional[DataContamination]:
        """Detect sentiment manipulation"""
        try:
            self._sentiment_history.append((current_sentiment, price_change))
        
            if len(self._sentiment_history) < 20:
                return None
        
            sentiments = np.array([s[0] for s in self._sentiment_history])
            price_changes = np.array([s[1] for s in self._sentiment_history])
        
            # Check for sentiment-price divergence
            if np.std(sentiments) > 0 and np.std(price_changes) > 0:
                correlation = np.corrcoef(sentiments, price_changes)[0, 1]
            
                # Extreme sentiment with opposite price action
                if correlation < -0.5:
                    return DataContamination(
                        contamination_type=ContaminationType.MANIPULATION,
                        severity=0.6,
                        affected_fields=['sentiment'],
                        detection_method='sentiment_price_divergence',
                        confidence=0.5
                    )
        
            return None
        except Exception as e:
            logger.error(f"Error in detect_sentiment_manipulation: {e}")
            raise


class DataAdversarialDefense:
    """
    Main Data Adversarial Defense Module
    
    RULES:
    1. Cross-validate ALL external data
    2. Detect manipulation, spoofing, fake news
    3. Assign trust scores to every source
    4. Auto-disable degraded sources
    5. Your data lies to you - verify everything
    """
    
    # Thresholds
    MIN_TRUST_SCORE = 0.5
    MAX_CONTAMINATION_SEVERITY = 0.7
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.data_defense")
        
            # Components
            self._cross_validator = CrossValidator()
            self._manipulation_detector = ManipulationDetector()
            self._news_validator = NewsValidator()
        
            # Source tracking
            self._source_scores: Dict[str, DataTrustScore] = {}
            self._vendor_biases: Dict[str, VendorBias] = {}
            self._disabled_sources: Dict[str, str] = {}
        
            # Contamination history
            self._contamination_history: Deque[DataContamination] = deque(maxlen=1000)
        
            self.logger.info("Data Adversarial Defense initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def register_source(self, source_id: str, initial_trust: float = 0.7):
        """Register a data source"""
        try:
            self._source_scores[source_id] = DataTrustScore(
                source_id=source_id,
                trust_level=DataTrustLevel.TRUSTED,
                score=initial_trust,
                reliability_history=initial_trust
            )
            self.logger.info(f"Data source registered: {source_id}")
        except Exception as e:
            logger.error(f"Error in register_source: {e}")
            raise
    
    def validate(
        self,
        source_id: str,
        data: Dict[str, Any],
        reference_data: Optional[Dict[str, Any]] = None
    ) -> DataDefenseResult:
        """
        Validate data from a source.
        
        Cross-validates, checks for manipulation, updates trust scores.
        """
        try:
            warnings = []
            contaminations = []
        
            # Check if source is disabled
            if source_id in self._disabled_sources:
                return DataDefenseResult(
                    is_clean=False,
                    can_use=False,
                    trust_score=0.0,
                    contaminations=[],
                    source_scores=self._source_scores,
                    vendor_biases=self._vendor_biases,
                    warnings=[f"Source disabled: {self._disabled_sources[source_id]}"],
                    reason="Source is disabled"
                )
        
            # Ensure source is registered
            if source_id not in self._source_scores:
                self.register_source(source_id)
        
            source_score = self._source_scores[source_id]
        
            # Check for stale data
            data_age = data.get('age_seconds', 0)
            if data_age > 60:
                contaminations.append(DataContamination(
                    contamination_type=ContaminationType.STALE_DATA,
                    severity=min(1.0, data_age / 300),
                    affected_fields=['all'],
                    detection_method='age_check',
                    confidence=1.0
                ))
                warnings.append(f"Stale data: {data_age}s old")
        
            # Check for missing data
            required_fields = ['price', 'volume', 'timestamp']
            missing = [f for f in required_fields if f not in data or data[f] is None]
            if missing:
                contaminations.append(DataContamination(
                    contamination_type=ContaminationType.MISSING_DATA,
                    severity=len(missing) / len(required_fields),
                    affected_fields=missing,
                    detection_method='field_check',
                    confidence=1.0
                ))
                warnings.append(f"Missing fields: {missing}")
        
            # Check for outliers
            price = data.get('price', 0)
            if price > 0:
                self._manipulation_detector.update(
                    price=price,
                    volume=data.get('volume', 0),
                    order_imbalance=data.get('order_imbalance', 0)
                )
            
                # Detect manipulation
                spoofing = self._manipulation_detector.detect_spoofing()
                if spoofing:
                    contaminations.append(spoofing)
                    warnings.append("Spoofing detected")
            
                wash = self._manipulation_detector.detect_wash_trading()
                if wash:
                    contaminations.append(wash)
                    warnings.append("Wash trading suspected")
            
                attack = self._manipulation_detector.detect_coordinated_attack()
                if attack:
                    contaminations.append(attack)
                    warnings.append("Coordinated attack detected")
        
            # Validate news if present
            if 'news' in data:
                news_contamination = self._news_validator.validate_news(data['news'])
                if news_contamination:
                    contaminations.append(news_contamination)
                    warnings.append("Suspicious news detected")
        
            # Cross-validate if reference data available
            if reference_data:
                for field in ['price', 'volume']:
                    if field in data and field in reference_data:
                        self._cross_validator.add_data(
                            source_id, time.time(), data[field]
                        )
                        self._cross_validator.add_data(
                            'reference', time.time(), reference_data[field]
                        )
            
                is_valid, consensus, discrepant = self._cross_validator.validate(time.time())
                if not is_valid and source_id in discrepant:
                    contaminations.append(DataContamination(
                        contamination_type=ContaminationType.VENDOR_BIAS,
                        severity=0.5,
                        affected_fields=['price'],
                        detection_method='cross_validation',
                        confidence=0.8
                    ))
                    warnings.append(f"Cross-validation failed: discrepancy with reference")
        
            # Update source score
            self._update_source_score(source_id, contaminations)
        
            # Store contaminations
            for c in contaminations:
                self._contamination_history.append(c)
        
            # Determine if data can be used
            max_severity = max([c.severity for c in contaminations], default=0)
            trust_score = source_score.score
        
            is_clean = len(contaminations) == 0
            can_use = (
                trust_score >= self.MIN_TRUST_SCORE and
                max_severity < self.MAX_CONTAMINATION_SEVERITY
            )
        
            # Auto-disable if trust too low
            if trust_score < 0.3:
                self._disable_source(source_id, "Trust score too low")
                can_use = False
        
            reason = self._generate_reason(is_clean, can_use, contaminations, trust_score)
        
            if warnings:
                self.logger.warning(
                    f"[{source_id}] Data validation: {len(contaminations)} issues | "
                    f"Trust: {trust_score:.2f} | Can use: {can_use}"
                )
        
            return DataDefenseResult(
                is_clean=is_clean,
                can_use=can_use,
                trust_score=trust_score,
                contaminations=contaminations,
                source_scores=self._source_scores,
                vendor_biases=self._vendor_biases,
                warnings=warnings,
                reason=reason
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise
    
    def _update_source_score(
        self,
        source_id: str,
        contaminations: List[DataContamination]
    ):
        """Update source trust score based on validation results"""
        try:
            score = self._source_scores[source_id]
            score.validation_count += 1
            score.last_validated = time.time()
        
            if contaminations:
                score.failure_count += 1
            
                # Reduce scores based on contamination severity
                max_severity = max(c.severity for c in contaminations)
                score.accuracy_score *= (1 - max_severity * 0.1)
                score.reliability_history *= 0.99
            else:
                # Slowly improve scores
                score.accuracy_score = min(1.0, score.accuracy_score * 1.01)
                score.reliability_history = min(1.0, score.reliability_history * 1.001)
        
            score.calculate_score()
        except Exception as e:
            logger.error(f"Error in _update_source_score: {e}")
            raise
    
    def _disable_source(self, source_id: str, reason: str):
        """Disable a data source"""
        try:
            self._disabled_sources[source_id] = reason
            if source_id in self._source_scores:
                self._source_scores[source_id].is_disabled = True
                self._source_scores[source_id].disable_reason = reason
            self.logger.critical(f"Data source DISABLED: {source_id} - {reason}")
        except Exception as e:
            logger.error(f"Error in _disable_source: {e}")
            raise
    
    def enable_source(self, source_id: str):
        """Re-enable a data source"""
        try:
            if source_id in self._disabled_sources:
                del self._disabled_sources[source_id]
            if source_id in self._source_scores:
                self._source_scores[source_id].is_disabled = False
                self._source_scores[source_id].disable_reason = ""
            self.logger.info(f"Data source re-enabled: {source_id}")
        except Exception as e:
            logger.error(f"Error in enable_source: {e}")
            raise
    
    def _generate_reason(
        self,
        is_clean: bool,
        can_use: bool,
        contaminations: List[DataContamination],
        trust_score: float
    ) -> str:
        """Generate explanation"""
        try:
            if is_clean:
                return "Data validated successfully"
            elif can_use:
                types = [c.contamination_type.name for c in contaminations]
                return f"Minor issues detected ({types}), data usable with caution"
            else:
                types = [c.contamination_type.name for c in contaminations]
                return f"Data rejected: {types}, trust={trust_score:.2f}"
        except Exception as e:
            logger.error(f"Error in _generate_reason: {e}")
            raise
    
    def get_source_trust(self, source_id: str) -> float:
        """Get trust score for a source"""
        try:
            if source_id in self._source_scores:
                return self._source_scores[source_id].score
            return 0.0
        except Exception as e:
            logger.error(f"Error in get_source_trust: {e}")
            raise
    
    def get_disabled_sources(self) -> Dict[str, str]:
        """Get all disabled sources"""
        return self._disabled_sources.copy()
    
    def get_contamination_stats(self) -> Dict[str, int]:
        """Get contamination statistics"""
        try:
            stats = {}
            for c in self._contamination_history:
                ctype = c.contamination_type.name
                stats[ctype] = stats.get(ctype, 0) + 1
            return stats
        except Exception as e:
            logger.error(f"Error in get_contamination_stats: {e}")
            raise

"""
Enhanced Signal Validator with ML-Based Anomaly Detection

Advanced signal validation with:
- ML-based anomaly detection
- Historical pattern matching
- Market regime compatibility checks
- Signal decay modeling
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import logging
import numpy as np

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of signal anomalies"""
    STATISTICAL_OUTLIER = "statistical_outlier"
    REGIME_MISMATCH = "regime_mismatch"
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    VOLUME_ANOMALY = "volume_anomaly"
    VOLATILITY_REGIME_SHIFT = "volatility_regime_shift"


@dataclass
class SignalAnomaly:
    """Detected signal anomaly"""
    anomaly_type: AnomalyType
    severity: float  # 0-1
    description: str
    affected_metrics: List[str]
    recommendation: str
    confidence: float


@dataclass
class SignalQualityMetrics:
    """Comprehensive signal quality assessment"""
    freshness_score: float
    source_reliability: float
    evidence_strength: float
    internal_consistency: float
    market_alignment: float
    historical_accuracy: float
    overall_quality: float
    decay_factor: float  # How much signal has decayed
    estimated_half_life_minutes: float


class EnhancedSignalValidator:
    """
    Advanced signal validation with ML-based anomaly detection.
    
    Features:
    - Statistical anomaly detection
    - Market regime compatibility
    - Signal decay modeling
    - Historical pattern matching
    - Cross-asset correlation checks
    """
    
    def __init__(
        self,
        max_signal_age_seconds: float = 300.0,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0,
        enable_ml_anomaly_detection: bool = True,
        anomaly_detection_window: int = 100,
        signal_history_size: int = 1000
    ):
        self.max_signal_age = max_signal_age_seconds
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.enable_ml_anomaly = enable_ml_anomaly_detection
        self.anomaly_window = anomaly_detection_window
        
        # Signal history for pattern learning
        self.signal_history: Dict[str, deque] = {}
        self.outcome_history: Dict[str, deque] = {}
        
        # Anomaly detection models (simplified - would use real ML in production)
        self.baseline_stats: Dict[str, Dict] = {}
        
        # Source reliability tracking
        self.source_reliability: Dict[str, Dict] = {}
        
    def validate_signal_comprehensive(
        self,
        signal: Dict[str, Any],
        symbol: str,
        market_context: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, List[SignalAnomaly], SignalQualityMetrics, Optional[Dict]]:
        """
        Comprehensive signal validation with all checks.
        
        Returns:
            Tuple of (is_valid, anomalies, quality_metrics, enriched_signal)
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        anomalies = []
        
        # Basic validation
        basic_valid, basic_errors = self._basic_validation(signal, symbol, current_time)
        if not basic_valid:
            return False, [], SignalQualityMetrics(0, 0, 0, 0, 0, 0, 0, 1.0, 0), None
        
        # Calculate quality metrics
        quality = self._calculate_quality_metrics(signal, symbol, market_context, current_time)
        
        # ML-based anomaly detection
        if self.enable_ml_anomaly:
            ml_anomalies = self._detect_ml_anomalies(signal, symbol, market_context)
            anomalies.extend(ml_anomalies)
        
        # Regime compatibility check
        regime_anomaly = self._check_regime_compatibility(signal, market_context)
        if regime_anomaly:
            anomalies.append(regime_anomaly)
        
        # Signal decay calculation
        decay_factor = self._calculate_signal_decay(signal, current_time)
        quality.decay_factor = decay_factor
        
        # Historical pattern matching
        pattern_match = self._match_historical_patterns(signal, symbol)
        quality.historical_accuracy = pattern_match['accuracy']
        
        if pattern_match['anomaly_detected']:
            anomalies.append(SignalAnomaly(
                anomaly_type=AnomalyType.TEMPORAL_INCONSISTENCY,
                severity=0.6,
                description=f"Signal diverges from historical pattern: {pattern_match['divergence']:.2f}",
                affected_metrics=['direction', 'timing'],
                recommendation="Review against similar historical setups",
                confidence=pattern_match['confidence']
            ))
        
        # Volume anomaly detection
        volume_anomaly = self._detect_volume_anomaly(signal, market_context)
        if volume_anomaly:
            anomalies.append(volume_anomaly)
        
        # Cross-asset correlation check
        correlation_anomaly = self._check_cross_asset_correlation(symbol, signal, market_context)
        if correlation_anomaly:
            anomalies.append(correlation_anomaly)
        
        # Determine validity based on anomalies
        critical_anomalies = [a for a in anomalies if a.severity > 0.8]
        is_valid = len(critical_anomalies) == 0 and quality.overall_quality > 0.5
        
        # Enrich signal with quality metrics
        enriched_signal = self._enrich_signal(signal, quality, anomalies)
        
        return is_valid, anomalies, quality, enriched_signal
    
    def _basic_validation(
        self,
        signal: Dict[str, Any],
        symbol: str,
        current_time: datetime
    ) -> Tuple[bool, List[str]]:
        """Basic signal validation"""
        errors = []
        
        # Check required fields
        required = ['direction', 'confidence', 'symbol']
        for field in required:
            if field not in signal:
                errors.append(f"Missing required field: {field}")
        
        # Check confidence bounds
        confidence = signal.get('confidence', 0.5)
        if not (self.min_confidence <= confidence <= self.max_confidence):
            errors.append(f"Confidence {confidence} out of bounds")
        
        # Check freshness
        signal_time = signal.get('timestamp', current_time)
        age = (current_time - signal_time).total_seconds()
        if age > self.max_signal_age:
            errors.append(f"Signal stale: {age:.0f}s > {self.max_signal_age:.0f}s")
        
        return len(errors) == 0, errors
    
    def _calculate_quality_metrics(
        self,
        signal: Dict[str, Any],
        symbol: str,
        market_context: Dict[str, Any],
        current_time: datetime
    ) -> SignalQualityMetrics:
        """Calculate comprehensive quality metrics"""
        
        # Freshness score (1 = fresh, 0 = stale)
        signal_time = signal.get('timestamp', current_time)
        age_seconds = (current_time - signal_time).total_seconds()
        freshness = max(0, 1 - age_seconds / self.max_signal_age)
        
        # Source reliability
        source = signal.get('source', 'unknown')
        source_rel = self._get_source_reliability_score(source)
        
        # Evidence strength
        evidence = signal.get('evidence', [])
        evidence_strength = min(1.0, len(evidence) / 5)  # 5+ items = full strength
        
        # Internal consistency
        consistency = self._check_internal_consistency(signal)
        
        # Market alignment
        alignment = self._check_market_alignment(signal, market_context)
        
        # Historical accuracy
        hist_accuracy = self._get_historical_accuracy(symbol, source)
        
        # Calculate overall quality as weighted average
        weights = {
            'freshness': 0.15,
            'source': 0.20,
            'evidence': 0.20,
            'consistency': 0.15,
            'alignment': 0.15,
            'historical': 0.15
        }
        
        overall = (
            freshness * weights['freshness'] +
            source_rel * weights['source'] +
            evidence_strength * weights['evidence'] +
            consistency * weights['consistency'] +
            alignment * weights['alignment'] +
            hist_accuracy * weights['historical']
        )
        
        # Estimate half-life based on asset volatility
        volatility = market_context.get('volatility', 0.2)
        half_life = 30 / (volatility * 10)  # Higher vol = shorter half-life
        
        return SignalQualityMetrics(
            freshness_score=freshness,
            source_reliability=source_rel,
            evidence_strength=evidence_strength,
            internal_consistency=consistency,
            market_alignment=alignment,
            historical_accuracy=hist_accuracy,
            overall_quality=overall,
            decay_factor=1.0,
            estimated_half_life_minutes=half_life
        )
    
    def _detect_ml_anomalies(
        self,
        signal: Dict[str, Any],
        symbol: str,
        market_context: Dict[str, Any]
    ) -> List[SignalAnomaly]:
        """ML-based anomaly detection"""
        anomalies = []
        
        # Statistical outlier detection using Z-score
        features = self._extract_signal_features(signal, market_context)
        
        # Check for statistical outliers
        for feature_name, value in features.items():
            if feature_name in self.baseline_stats:
                stats = self.baseline_stats[feature_name]
                mean = stats['mean']
                std = stats['std']
                
                if std > 0:
                    z_score = abs(value - mean) / std
                    if z_score > 3:  # 3 sigma rule
                        anomalies.append(SignalAnomaly(
                            anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                            severity=min(1.0, z_score / 5),
                            description=f"{feature_name} is {z_score:.1f}σ from mean",
                            affected_metrics=[feature_name],
                            recommendation="Investigate unusual feature value",
                            confidence=min(1.0, z_score / 4)
                        ))
        
        # Volatility regime shift detection
        current_vol = market_context.get('volatility', 0.2)
        hist_vol = self._get_historical_volatility(symbol)
        
        if hist_vol > 0 and abs(current_vol - hist_vol) / hist_vol > 0.5:
            anomalies.append(SignalAnomaly(
                anomaly_type=AnomalyType.VOLATILITY_REGIME_SHIFT,
                severity=0.7,
                description=f"Volatility regime shift: {hist_vol:.1%} → {current_vol:.1%}",
                affected_metrics=['volatility', 'expected_slippage'],
                recommendation="Adjust position size for new volatility regime",
                confidence=0.8
            ))
        
        return anomalies
    
    def _extract_signal_features(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract numerical features from signal"""
        return {
            'confidence': signal.get('confidence', 0.5),
            'size': signal.get('size', 1.0),
            'time_of_day': signal.get('timestamp', datetime.utcnow()).hour / 24,
            'market_volatility': market_context.get('volatility', 0.2),
            'market_volume': market_context.get('volume_ratio', 1.0),
            'price_momentum': market_context.get('momentum', 0),
            'rsi': market_context.get('rsi', 50) / 100,
            'spread': market_context.get('spread_bps', 10) / 100
        }
    
    def _check_regime_compatibility(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> Optional[SignalAnomaly]:
        """Check if signal is compatible with current market regime"""
        
        current_regime = market_context.get('regime', 'normal')
        signal_direction = signal.get('direction', 'hold')
        
        # Define incompatible combinations
        incompatibilities = {
            'high_volatility': {
                'buy': ['mean_reversion_signals'],  # Trend signals risky in high vol
                'sell': ['trend_following_signals']
            },
            'low_liquidity': {
                'buy': ['large_size_signals'],
                'sell': ['large_size_signals']
            }
        }
        
        if current_regime in incompatibilities:
            regime_issues = incompatibilities[current_regime]
            if signal_direction in regime_issues:
                return SignalAnomaly(
                    anomaly_type=AnomalyType.REGIME_MISMATCH,
                    severity=0.6,
                    description=f"Signal type may be incompatible with {current_regime} regime",
                    affected_metrics=['regime_fit', 'execution_probability'],
                    recommendation=f"Verify signal works in {current_regime} conditions",
                    confidence=0.7
                )
        
        return None
    
    def _calculate_signal_decay(
        self,
        signal: Dict[str, Any],
        current_time: datetime
    ) -> float:
        """Calculate how much signal has decayed"""
        
        signal_time = signal.get('timestamp', current_time)
        age_minutes = (current_time - signal_time).total_seconds() / 60
        
        # Get half-life (would be asset-specific)
        half_life = signal.get('half_life_minutes', 30)
        
        # Exponential decay
        decay = 0.5 ** (age_minutes / half_life)
        
        return decay
    
    def _match_historical_patterns(
        self,
        signal: Dict[str, Any],
        symbol: str
    ) -> Dict[str, Any]:
        """Match signal against historical patterns"""
        
        history = self.signal_history.get(symbol, deque(maxlen=100))
        
        if len(history) < 10:
            return {'accuracy': 0.5, 'anomaly_detected': False, 'divergence': 0, 'confidence': 0}
        
        # Find similar signals
        similar_signals = []
        current_features = {
            'direction': signal.get('direction'),
            'confidence': signal.get('confidence'),
            'size': signal.get('size')
        }
        
        for hist_signal in history:
            # Calculate similarity
            hist_features = {
                'direction': hist_signal.get('direction'),
                'confidence': hist_signal.get('confidence'),
                'size': hist_signal.get('size')
            }
            
            similarity = self._calculate_similarity(current_features, hist_features)
            if similarity > 0.8:
                similar_signals.append(hist_signal)
        
        if not similar_signals:
            return {'accuracy': 0.5, 'anomaly_detected': False, 'divergence': 0, 'confidence': 0}
        
        # Calculate historical accuracy
        outcomes = self.outcome_history.get(symbol, deque(maxlen=100))
        if outcomes:
            matching_outcomes = [
                o for o in outcomes
                if any(s['id'] == o.get('signal_id') for s in similar_signals)
            ]
            
            if matching_outcomes:
                wins = sum(1 for o in matching_outcomes if o.get('pnl', 0) > 0)
                accuracy = wins / len(matching_outcomes)
            else:
                accuracy = 0.5
        else:
            accuracy = 0.5
        
        # Detect if current signal diverges from pattern
        avg_conf = sum(s.get('confidence', 0) for s in similar_signals) / len(similar_signals)
        current_conf = signal.get('confidence', 0)
        divergence = abs(current_conf - avg_conf)
        
        return {
            'accuracy': accuracy,
            'anomaly_detected': divergence > 0.2,
            'divergence': divergence,
            'confidence': len(similar_signals) / 10  # More matches = higher confidence
        }
    
    def _calculate_similarity(self, f1: Dict, f2: Dict) -> float:
        """Calculate similarity between two feature sets"""
        if f1['direction'] != f2['direction']:
            return 0.0
        
        # Similarity based on confidence and size
        conf_sim = 1 - abs(f1['confidence'] - f2['confidence'])
        size_sim = 1 - min(1, abs(f1['size'] - f2['size']))
        
        return (conf_sim + size_sim) / 2
    
    def _detect_volume_anomaly(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> Optional[SignalAnomaly]:
        """Detect volume anomalies"""
        
        current_volume = market_context.get('volume', 0)
        avg_volume = market_context.get('avg_volume', current_volume)
        
        if avg_volume > 0:
            volume_ratio = current_volume / avg_volume
            
            if volume_ratio < 0.3:  # Very low volume
                return SignalAnomaly(
                    anomaly_type=AnomalyType.VOLUME_ANOMALY,
                    severity=0.7,
                    description=f"Volume {volume_ratio:.1%} of average - execution risk",
                    affected_metrics=['liquidity', 'slippage', 'fill_probability'],
                    recommendation="Reduce position size or wait for volume",
                    confidence=0.8
                )
            elif volume_ratio > 5:  # Extremely high volume
                return SignalAnomaly(
                    anomaly_type=AnomalyType.VOLUME_ANOMALY,
                    severity=0.5,
                    description=f"Volume spike {volume_ratio:.1f}x - potential news event",
                    affected_metrics=['volatility', 'information_asymmetry'],
                    recommendation="Verify no material news before executing",
                    confidence=0.6
                )
        
        return None
    
    def _check_cross_asset_correlation(
        self,
        symbol: str,
        signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> Optional[SignalAnomaly]:
        """Check for correlation breakdowns across related assets"""
        
        # Get correlations (would come from correlation matrix)
        correlations = market_context.get('correlations', {})
        
        if not correlations:
            return None
        
        # Check if signal contradicts correlated assets
        signal_dir = signal.get('direction')
        contradicting_assets = []
        
        for asset, corr in correlations.items():
            if abs(corr) > 0.7:  # Strong correlation
                asset_signal = market_context.get(f'{asset}_signal')
                if asset_signal:
                    # If highly correlated but opposite signals, that's an anomaly
                    if corr > 0.7 and asset_signal != signal_dir:
                        contradicting_assets.append((asset, corr))
                    elif corr < -0.7 and asset_signal == signal_dir:
                        contradicting_assets.append((asset, corr))
        
        if contradicting_assets:
            return SignalAnomaly(
                anomaly_type=AnomalyType.CORRELATION_BREAKDOWN,
                severity=0.6,
                description=f"Signal contradicts {len(contradicting_assets)} correlated assets",
                affected_metrics=['signal_validity', 'divergence_trade'],
                recommendation="Investigate correlation breakdown or arbitrage opportunity",
                confidence=0.7
            )
        
        return None
    
    def _get_source_reliability_score(self, source: str) -> float:
        """Get reliability score for a source"""
        if source in self.source_reliability:
            return self.source_reliability[source].get('score', 0.7)
        return 0.7  # Default moderate reliability
    
    def _check_internal_consistency(self, signal: Dict[str, Any]) -> float:
        """Check if signal components are internally consistent"""
        
        checks = []
        
        # Check confidence vs evidence alignment
        confidence = signal.get('confidence', 0.5)
        evidence_count = len(signal.get('evidence', []))
        
        # High confidence should have substantial evidence
        if confidence > 0.8 and evidence_count < 3:
            checks.append(0.5)  # Penalty
        else:
            checks.append(1.0)
        
        # Check rationale alignment with direction
        rationale = signal.get('rationale', '').lower()
        direction = signal.get('direction', 'hold')
        
        bullish_terms = ['up', 'bull', 'growth', 'positive', 'strong']
        bearish_terms = ['down', 'bear', 'decline', 'negative', 'weak']
        
        has_bullish = any(t in rationale for t in bullish_terms)
        has_bearish = any(t in rationale for t in bearish_terms)
        
        if direction == 'buy' and has_bearish and not has_bullish:
            checks.append(0.3)
        elif direction == 'sell' and has_bullish and not has_bearish:
            checks.append(0.3)
        else:
            checks.append(1.0)
        
        return sum(checks) / len(checks) if checks else 0.5
    
    def _check_market_alignment(self, signal: Dict[str, Any], market_context: Dict[str, Any]) -> float:
        """Check if signal aligns with market conditions"""
        
        direction = signal.get('direction', 'hold')
        trend = market_context.get('trend', 0)  # -1 to 1
        
        if direction == 'buy' and trend > 0:
            return 1.0
        elif direction == 'sell' and trend < 0:
            return 1.0
        elif direction == 'hold':
            return 0.8
        else:
            return 0.4  # Contrarian signal
    
    def _get_historical_accuracy(self, symbol: str, source: str) -> float:
        """Get historical accuracy for symbol+source combination"""
        key = f"{symbol}_{source}"
        # Would lookup from historical performance database
        return 0.6  # Default
    
    def _get_historical_volatility(self, symbol: str) -> float:
        """Get historical volatility for symbol"""
        # Would lookup from historical data
        return 0.2  # Default
    
    def _enrich_signal(
        self,
        signal: Dict[str, Any],
        quality: SignalQualityMetrics,
        anomalies: List[SignalAnomaly]
    ) -> Dict[str, Any]:
        """Enrich signal with quality metrics"""
        
        enriched = signal.copy()
        enriched['quality_metrics'] = {
            'overall_quality': quality.overall_quality,
            'freshness': quality.freshness_score,
            'source_reliability': quality.source_reliability,
            'decay_factor': quality.decay_factor,
            'estimated_half_life': quality.estimated_half_life_minutes
        }
        enriched['anomaly_count'] = len(anomalies)
        enriched['critical_anomalies'] = len([a for a in anomalies if a.severity > 0.8])
        
        return enriched
    
    def update_signal_history(
        self,
        symbol: str,
        signal: Dict[str, Any],
        outcome: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update signal history for pattern learning"""
        
        if symbol not in self.signal_history:
            self.signal_history[symbol] = deque(maxlen=1000)
        
        self.signal_history[symbol].append({
            **signal,
            'recorded_at': datetime.utcnow()
        })
        
        if outcome:
            if symbol not in self.outcome_history:
                self.outcome_history[symbol] = deque(maxlen=1000)
            self.outcome_history[symbol].append(outcome)
        
        # Update baseline statistics
        self._update_baseline_stats(symbol)
    
    def _update_baseline_stats(self, symbol: str) -> None:
        """Update baseline statistics for anomaly detection"""
        
        history = list(self.signal_history.get(symbol, []))
        
        if len(history) < 10:
            return
        
        # Calculate statistics for each feature
        features_to_track = ['confidence', 'size']
        
        for feature in features_to_track:
            values = [s.get(feature, 0) for s in history if feature in s]
            if values:
                self.baseline_stats[feature] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }
    
    def get_validation_summary(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get validation summary statistics"""
        
        total_signals = sum(len(h) for h in self.signal_history.values())
        
        return {
            'total_signals_validated': total_signals,
            'symbols_tracked': len(self.signal_history),
            'sources_tracked': len(self.source_reliability),
            'baseline_features': list(self.baseline_stats.keys()),
            'average_signal_quality': np.mean([
                s.get('quality_metrics', {}).get('overall_quality', 0.5)
                for h in self.signal_history.values()
                for s in h
            ]) if self.signal_history else 0
        }

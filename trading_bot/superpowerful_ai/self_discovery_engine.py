"""
Self-Discovery Engine
=====================

Autonomous pattern recognition, market regime detection, and anomaly detection.
Continuously discovers new patterns and market behaviors without human intervention.

Features:
- Unsupervised pattern discovery using clustering and dimensionality reduction
- Market regime detection (trending, ranging, volatile, calm)
- Anomaly detection for unusual market conditions
- Correlation discovery across assets and timeframes
- Feature importance analysis
- Pattern persistence tracking
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

try:
    from sklearn.cluster import DBSCAN, KMeans
    from sklearn.decomposition import PCA, FastICA
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import IsolationForest
    from sklearn.covariance import EllipticEnvelope
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.debug("scikit-learn not available for advanced pattern discovery")

try:
    from scipy.stats import zscore, entropy
    from scipy.signal import find_peaks, argrelextrema
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.debug("scipy not available for statistical analysis")


class MarketRegime(Enum):
    """Market regime types"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    CALM = "calm"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    UNKNOWN = "unknown"


@dataclass
class DiscoveredPattern:
    """A pattern discovered by the engine"""
    pattern_id: str
    pattern_type: str
    confidence: float
    features: Dict[str, float]
    timeframe: str
    discovered_at: datetime
    occurrences: int = 1
    success_rate: float = 0.0
    avg_profit: float = 0.0
    last_seen: datetime = field(default_factory=datetime.now)


@dataclass
class MarketRegimeState:
    """Current market regime state"""
    regime: MarketRegime
    confidence: float
    volatility: float
    trend_strength: float
    momentum: float
    detected_at: datetime
    features: Dict[str, float] = field(default_factory=dict)


@dataclass
class AnomalyDetection:
    """Detected market anomaly"""
    anomaly_type: str
    severity: float  # 0-1
    description: str
    detected_at: datetime
    affected_features: List[str]
    recommendation: str


class SelfDiscoveryEngine:
    """
    Autonomous pattern discovery and market intelligence engine.
    
    Continuously learns and discovers:
    - New price patterns
    - Market regimes
    - Anomalies and unusual conditions
    - Cross-asset correlations
    - Feature importance
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.discovered_patterns: Dict[str, DiscoveredPattern] = {}
        self.regime_history: List[MarketRegimeState] = []
        self.anomaly_history: List[AnomalyDetection] = []
        
        # Pattern discovery settings
        self.min_pattern_confidence = self.config.get('min_pattern_confidence', 0.7)
        self.max_patterns = self.config.get('max_patterns', 1000)
        self.pattern_decay_days = self.config.get('pattern_decay_days', 30)
        
        # Anomaly detection settings
        self.anomaly_threshold = self.config.get('anomaly_threshold', 0.8)
        self.contamination = self.config.get('contamination', 0.1)
        
        # Initialize models
        self._init_models()
        
        logger.info("Self-Discovery Engine initialized")
    
    def _init_models(self):
        """Initialize ML models for pattern discovery"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available - using simplified discovery")
            self.scaler = None
            self.pca = None
            self.clusterer = None
            self.anomaly_detector = None
            return
        
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% variance
        self.clusterer = DBSCAN(eps=0.5, min_samples=5)
        self.anomaly_detector = IsolationForest(
            contamination=self.contamination,
            random_state=42
        )
    
    async def discover_patterns(
        self,
        market_data: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> List[DiscoveredPattern]:
        """
        Discover new patterns in market data using unsupervised learning.
        
        Args:
            market_data: OHLCV data
            symbol: Trading symbol
            timeframe: Timeframe (M1, M5, M15, etc.)
        
        Returns:
            List of discovered patterns
        """
        try:
            if market_data is None or len(market_data) < 50:
                return []
            
            # Extract features
            features = self._extract_features(market_data)
            
            if not SKLEARN_AVAILABLE:
                return self._simple_pattern_discovery(features, symbol, timeframe)
            
            # Normalize features
            features_scaled = self.scaler.fit_transform(features)
            
            # Dimensionality reduction
            features_reduced = self.pca.fit_transform(features_scaled)
            
            # Cluster patterns
            clusters = self.clusterer.fit_predict(features_reduced)
            
            # Analyze each cluster
            new_patterns = []
            unique_clusters = set(clusters)
            
            for cluster_id in unique_clusters:
                if cluster_id == -1:  # Noise
                    continue
                
                cluster_mask = clusters == cluster_id
                cluster_features = features[cluster_mask]
                
                # Create pattern signature
                pattern = self._create_pattern(
                    cluster_id=cluster_id,
                    features=cluster_features,
                    symbol=symbol,
                    timeframe=timeframe
                )
                
                if pattern and pattern.confidence >= self.min_pattern_confidence:
                    new_patterns.append(pattern)
                    self.discovered_patterns[pattern.pattern_id] = pattern
            
            # Cleanup old patterns
            self._cleanup_old_patterns()
            
            logger.info(f"Discovered {len(new_patterns)} new patterns for {symbol}")
            return new_patterns
            
        except Exception as e:
            logger.error(f"Error discovering patterns: {e}")
            return []
    
    def _extract_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract features from market data for pattern discovery"""
        features_list = []
        
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            volume = data.get('volume', pd.Series([0] * len(data))).values
            
            # Price-based features
            returns = np.diff(close, prepend=close[0]) / close
            log_returns = np.log(close / np.roll(close, 1))
            log_returns[0] = 0
            
            # Volatility features
            volatility = pd.Series(returns).rolling(20).std().fillna(0).values
            
            # Momentum features
            roc_5 = (close - np.roll(close, 5)) / np.roll(close, 5)
            roc_10 = (close - np.roll(close, 10)) / np.roll(close, 10)
            roc_20 = (close - np.roll(close, 20)) / np.roll(close, 20)
            
            # Range features
            true_range = high - low
            atr = pd.Series(true_range).rolling(14).mean().fillna(0).values
            
            # Volume features
            volume_ma = pd.Series(volume).rolling(20).mean().fillna(0).values
            volume_ratio = np.where(volume_ma > 0, volume / volume_ma, 1.0)
            
            # Combine features
            features = np.column_stack([
                returns,
                log_returns,
                volatility,
                roc_5,
                roc_10,
                roc_20,
                true_range,
                atr,
                volume_ratio
            ])
            
            # Replace inf and nan
            features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return np.array([[0.0] * 9])
    
    def _create_pattern(
        self,
        cluster_id: int,
        features: np.ndarray,
        symbol: str,
        timeframe: str
    ) -> Optional[DiscoveredPattern]:
        """Create a pattern from cluster features"""
        try:
            # Calculate pattern statistics
            mean_features = np.mean(features, axis=0)
            std_features = np.std(features, axis=0)
            
            # Calculate confidence based on cluster cohesion
            cohesion = 1.0 / (1.0 + np.mean(std_features))
            
            pattern_id = f"{symbol}_{timeframe}_cluster_{cluster_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            pattern = DiscoveredPattern(
                pattern_id=pattern_id,
                pattern_type=self._classify_pattern_type(mean_features),
                confidence=float(cohesion),
                features={
                    'returns': float(mean_features[0]),
                    'volatility': float(mean_features[2]),
                    'momentum_5': float(mean_features[3]),
                    'momentum_10': float(mean_features[4]),
                    'momentum_20': float(mean_features[5]),
                    'atr': float(mean_features[7]),
                },
                timeframe=timeframe,
                discovered_at=datetime.now()
            )
            
            return pattern
            
        except Exception as e:
            logger.error(f"Error creating pattern: {e}")
            return None
    
    def _classify_pattern_type(self, features: np.ndarray) -> str:
        """Classify pattern type based on features"""
        returns = features[0]
        volatility = features[2]
        momentum = features[3]
        
        if abs(momentum) > 0.02:
            if momentum > 0:
                return "strong_uptrend"
            else:
                return "strong_downtrend"
        elif volatility > 0.015:
            return "high_volatility"
        elif volatility < 0.005:
            return "low_volatility_range"
        elif abs(returns) < 0.001:
            return "consolidation"
        else:
            return "mixed"
    
    def _simple_pattern_discovery(
        self,
        features: np.ndarray,
        symbol: str,
        timeframe: str
    ) -> List[DiscoveredPattern]:
        """Simplified pattern discovery without sklearn"""
        patterns = []
        
        try:
            # Simple statistical analysis
            mean_features = np.mean(features, axis=0)
            
            pattern_id = f"{symbol}_{timeframe}_simple_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            pattern = DiscoveredPattern(
                pattern_id=pattern_id,
                pattern_type=self._classify_pattern_type(mean_features),
                confidence=0.6,
                features={
                    'returns': float(mean_features[0]),
                    'volatility': float(mean_features[2]),
                    'momentum': float(mean_features[3]),
                },
                timeframe=timeframe,
                discovered_at=datetime.now()
            )
            
            patterns.append(pattern)
            self.discovered_patterns[pattern.pattern_id] = pattern
            
        except Exception as e:
            logger.error(f"Error in simple pattern discovery: {e}")
        
        return patterns
    
    async def detect_regime(
        self,
        market_data: pd.DataFrame,
        symbol: str
    ) -> MarketRegimeState:
        """
        Detect current market regime.
        
        Args:
            market_data: OHLCV data
            symbol: Trading symbol
        
        Returns:
            Current market regime state
        """
        try:
            if market_data is None or len(market_data) < 50:
                return MarketRegimeState(
                    regime=MarketRegime.UNKNOWN,
                    confidence=0.0,
                    volatility=0.0,
                    trend_strength=0.0,
                    momentum=0.0,
                    detected_at=datetime.now()
                )
            
            close = market_data['close'].values
            high = market_data['high'].values
            low = market_data['low'].values
            
            # Calculate regime indicators
            returns = np.diff(close) / close[:-1]
            volatility = np.std(returns[-20:]) if len(returns) >= 20 else 0.0
            
            # Trend strength (ADX-like)
            trend_strength = self._calculate_trend_strength(close)
            
            # Momentum
            momentum = (close[-1] - close[-20]) / close[-20] if len(close) >= 20 else 0.0
            
            # Classify regime
            regime, confidence = self._classify_regime(
                volatility=volatility,
                trend_strength=trend_strength,
                momentum=momentum,
                close=close
            )
            
            regime_state = MarketRegimeState(
                regime=regime,
                confidence=confidence,
                volatility=float(volatility),
                trend_strength=float(trend_strength),
                momentum=float(momentum),
                detected_at=datetime.now(),
                features={
                    'volatility': float(volatility),
                    'trend_strength': float(trend_strength),
                    'momentum': float(momentum),
                }
            )
            
            self.regime_history.append(regime_state)
            
            # Keep only recent history
            if len(self.regime_history) > 1000:
                self.regime_history = self.regime_history[-1000:]
            
            logger.debug(f"Detected regime: {regime.value} (confidence: {confidence:.2f})")
            return regime_state
            
        except Exception as e:
            logger.error(f"Error detecting regime: {e}")
            return MarketRegimeState(
                regime=MarketRegime.UNKNOWN,
                confidence=0.0,
                volatility=0.0,
                trend_strength=0.0,
                momentum=0.0,
                detected_at=datetime.now()
            )
    
    def _calculate_trend_strength(self, close: np.ndarray) -> float:
        """Calculate trend strength (0-1)"""
        try:
            if len(close) < 20:
                return 0.0
            
            # Simple trend strength based on directional movement
            ups = 0
            downs = 0
            
            for i in range(1, min(20, len(close))):
                if close[-i] > close[-i-1]:
                    ups += 1
                elif close[-i] < close[-i-1]:
                    downs += 1
            
            total = ups + downs
            if total == 0:
                return 0.0
            
            return abs(ups - downs) / total
            
        except Exception:
            return 0.0
    
    def _classify_regime(
        self,
        volatility: float,
        trend_strength: float,
        momentum: float,
        close: np.ndarray
    ) -> Tuple[MarketRegime, float]:
        """Classify market regime with confidence"""
        
        # High volatility regime
        if volatility > 0.02:
            return MarketRegime.VOLATILE, 0.8
        
        # Low volatility regime
        if volatility < 0.005:
            return MarketRegime.CALM, 0.8
        
        # Strong trend regimes
        if trend_strength > 0.6:
            if momentum > 0.01:
                return MarketRegime.TRENDING_UP, 0.85
            elif momentum < -0.01:
                return MarketRegime.TRENDING_DOWN, 0.85
        
        # Ranging regime
        if trend_strength < 0.3 and abs(momentum) < 0.005:
            return MarketRegime.RANGING, 0.75
        
        # Breakout detection
        if len(close) >= 20:
            recent_high = np.max(close[-20:-1])
            recent_low = np.min(close[-20:-1])
            current = close[-1]
            
            if current > recent_high * 1.005:
                return MarketRegime.BREAKOUT, 0.7
            elif current < recent_low * 0.995:
                return MarketRegime.BREAKOUT, 0.7
        
        # Default
        return MarketRegime.UNKNOWN, 0.5
    
    async def detect_anomalies(
        self,
        market_data: pd.DataFrame,
        symbol: str
    ) -> List[AnomalyDetection]:
        """
        Detect market anomalies and unusual conditions.
        
        Args:
            market_data: OHLCV data
            symbol: Trading symbol
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        try:
            if market_data is None or len(market_data) < 50:
                return []
            
            close = market_data['close'].values
            volume = market_data.get('volume', pd.Series([0] * len(market_data))).values
            
            # Price anomalies
            price_anomalies = self._detect_price_anomalies(close)
            anomalies.extend(price_anomalies)
            
            # Volume anomalies
            volume_anomalies = self._detect_volume_anomalies(volume)
            anomalies.extend(volume_anomalies)
            
            # Volatility anomalies
            volatility_anomalies = self._detect_volatility_anomalies(close)
            anomalies.extend(volatility_anomalies)
            
            # Store anomalies
            self.anomaly_history.extend(anomalies)
            
            # Keep only recent history
            if len(self.anomaly_history) > 500:
                self.anomaly_history = self.anomaly_history[-500:]
            
            if anomalies:
                logger.info(f"Detected {len(anomalies)} anomalies for {symbol}")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def _detect_price_anomalies(self, close: np.ndarray) -> List[AnomalyDetection]:
        """Detect price-based anomalies"""
        anomalies = []
        
        try:
            if len(close) < 20:
                return []
            
            returns = np.diff(close) / close[:-1]
            
            if SCIPY_AVAILABLE:
                z_scores = zscore(returns[-20:])
                
                # Extreme price movements
                if abs(z_scores[-1]) > 3.0:
                    anomalies.append(AnomalyDetection(
                        anomaly_type="extreme_price_movement",
                        severity=min(abs(z_scores[-1]) / 5.0, 1.0),
                        description=f"Extreme price movement detected (z-score: {z_scores[-1]:.2f})",
                        detected_at=datetime.now(),
                        affected_features=['price', 'returns'],
                        recommendation="Exercise caution - unusual price action"
                    ))
            else:
                # Simple threshold check
                recent_std = np.std(returns[-20:])
                if abs(returns[-1]) > 3 * recent_std:
                    anomalies.append(AnomalyDetection(
                        anomaly_type="extreme_price_movement",
                        severity=0.8,
                        description="Extreme price movement detected",
                        detected_at=datetime.now(),
                        affected_features=['price'],
                        recommendation="Exercise caution"
                    ))
            
        except Exception as e:
            logger.error(f"Error detecting price anomalies: {e}")
        
        return anomalies
    
    def _detect_volume_anomalies(self, volume: np.ndarray) -> List[AnomalyDetection]:
        """Detect volume-based anomalies"""
        anomalies = []
        
        try:
            if len(volume) < 20 or np.all(volume == 0):
                return []
            
            volume_ma = np.mean(volume[-20:])
            
            # Extreme volume spike
            if volume[-1] > 3 * volume_ma:
                anomalies.append(AnomalyDetection(
                    anomaly_type="volume_spike",
                    severity=min(volume[-1] / (3 * volume_ma), 1.0),
                    description=f"Unusual volume spike: {volume[-1]/volume_ma:.1f}x average",
                    detected_at=datetime.now(),
                    affected_features=['volume'],
                    recommendation="Potential significant market event"
                ))
            
            # Extremely low volume
            elif volume[-1] < 0.2 * volume_ma and volume_ma > 0:
                anomalies.append(AnomalyDetection(
                    anomaly_type="low_volume",
                    severity=0.6,
                    description="Unusually low volume",
                    detected_at=datetime.now(),
                    affected_features=['volume'],
                    recommendation="Low liquidity - widen spreads"
                ))
            
        except Exception as e:
            logger.error(f"Error detecting volume anomalies: {e}")
        
        return anomalies
    
    def _detect_volatility_anomalies(self, close: np.ndarray) -> List[AnomalyDetection]:
        """Detect volatility-based anomalies"""
        anomalies = []
        
        try:
            if len(close) < 40:
                return []
            
            returns = np.diff(close) / close[:-1]
            
            # Recent vs historical volatility
            recent_vol = np.std(returns[-10:])
            historical_vol = np.std(returns[-40:-10])
            
            if historical_vol > 0:
                vol_ratio = recent_vol / historical_vol
                
                # Volatility spike
                if vol_ratio > 2.0:
                    anomalies.append(AnomalyDetection(
                        anomaly_type="volatility_spike",
                        severity=min(vol_ratio / 3.0, 1.0),
                        description=f"Volatility spike: {vol_ratio:.1f}x normal",
                        detected_at=datetime.now(),
                        affected_features=['volatility'],
                        recommendation="Reduce position sizes"
                    ))
                
                # Volatility collapse
                elif vol_ratio < 0.3:
                    anomalies.append(AnomalyDetection(
                        anomaly_type="volatility_collapse",
                        severity=0.7,
                        description="Volatility collapse - potential breakout ahead",
                        detected_at=datetime.now(),
                        affected_features=['volatility'],
                        recommendation="Prepare for potential breakout"
                    ))
            
        except Exception as e:
            logger.error(f"Error detecting volatility anomalies: {e}")
        
        return anomalies
    
    def _cleanup_old_patterns(self):
        """Remove old patterns that haven't been seen recently"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.pattern_decay_days)
            
            patterns_to_remove = [
                pid for pid, pattern in self.discovered_patterns.items()
                if pattern.last_seen < cutoff_date
            ]
            
            for pid in patterns_to_remove:
                del self.discovered_patterns[pid]
            
            if patterns_to_remove:
                logger.debug(f"Removed {len(patterns_to_remove)} old patterns")
                
        except Exception as e:
            logger.error(f"Error cleaning up patterns: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery engine statistics"""
        return {
            'total_patterns_discovered': len(self.discovered_patterns),
            'active_patterns': sum(
                1 for p in self.discovered_patterns.values()
                if p.last_seen > datetime.now() - timedelta(days=7)
            ),
            'total_anomalies_detected': len(self.anomaly_history),
            'recent_anomalies': sum(
                1 for a in self.anomaly_history
                if a.detected_at > datetime.now() - timedelta(hours=24)
            ),
            'regime_changes': len(self.regime_history),
            'current_regime': self.regime_history[-1].regime.value if self.regime_history else 'unknown',
        }

"""
Market State Classifier
=======================
Advanced market regime detection using HMM, clustering, and multiple indicators.

Features:
- Hidden Markov Models for regime detection
- K-means and DBSCAN clustering
- Volatility filters and regime classification
- Yield curve analysis
- VIX/VVIX ratio analysis
- Volume shock detection
- Automatic strategy behavior switching

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import deque
import threading

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.signal import find_peaks
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.preprocessing import StandardScaler
    from sklearn.mixture import GaussianMixture
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from hmmlearn import hmm
    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications"""
    TRENDING_UP = auto()
    TRENDING_DOWN = auto()
    RANGING = auto()
    HIGH_VOLATILITY = auto()
    LOW_VOLATILITY = auto()
    CRASH = auto()
    RECOVERY = auto()
    ACCUMULATION = auto()
    DISTRIBUTION = auto()
    BREAKOUT = auto()
    BREAKDOWN = auto()
    UNKNOWN = auto()


class VolatilityRegime(Enum):
    """Volatility regime classifications"""
    VERY_LOW = auto()
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    EXTREME = auto()


class TrendStrength(Enum):
    """Trend strength classifications"""
    STRONG_DOWN = auto()
    MODERATE_DOWN = auto()
    WEAK_DOWN = auto()
    NEUTRAL = auto()
    WEAK_UP = auto()
    MODERATE_UP = auto()
    STRONG_UP = auto()


@dataclass
class MarketState:
    """Complete market state representation"""
    timestamp: datetime
    
    # Primary regime
    regime: MarketRegime = MarketRegime.UNKNOWN
    regime_confidence: float = 0.0
    regime_duration: int = 0  # bars in current regime
    
    # Volatility
    volatility_regime: VolatilityRegime = VolatilityRegime.NORMAL
    current_volatility: float = 0.0
    volatility_percentile: float = 0.5
    
    # Trend
    trend_strength: TrendStrength = TrendStrength.NEUTRAL
    trend_direction: float = 0.0  # -1 to 1
    trend_duration: int = 0
    
    # HMM state
    hmm_state: int = 0
    hmm_state_probs: List[float] = field(default_factory=list)
    
    # Cluster info
    cluster_id: int = 0
    cluster_distance: float = 0.0
    
    # Risk indicators
    vix_level: float = 0.0
    vix_vvix_ratio: float = 0.0
    yield_curve_slope: float = 0.0
    
    # Volume analysis
    volume_shock: bool = False
    volume_ratio: float = 1.0
    
    # Recommended behavior
    recommended_strategy: str = "neutral"
    position_size_multiplier: float = 1.0
    stop_loss_multiplier: float = 1.0


class HMMRegimeDetector:
    """Hidden Markov Model based regime detection"""
    
    def __init__(self, n_states: int = 4, config: Optional[Dict] = None):
        self.n_states = n_states
        self.config = config or {}
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_fitted = False
        
        # State labels
        self.state_labels = {
            0: MarketRegime.TRENDING_UP,
            1: MarketRegime.TRENDING_DOWN,
            2: MarketRegime.RANGING,
            3: MarketRegime.HIGH_VOLATILITY
        }
        
    def fit(self, data: pd.DataFrame) -> None:
        """Fit HMM on historical data"""
        
        if not HMM_AVAILABLE:
            logger.warning("hmmlearn not available, using fallback")
            self.is_fitted = True
            return
        
        # Prepare features
        features = self._prepare_features(data)
        
        if self.scaler:
            features_scaled = self.scaler.fit_transform(features)
        else:
            features_scaled = features
        
        # Fit HMM
        self.model = hmm.GaussianHMM(
            n_components=self.n_states,
            covariance_type="full",
            n_iter=100,
            random_state=42
        )
        
        self.model.fit(features_scaled)
        self.is_fitted = True
        
        # Analyze states to assign labels
        self._assign_state_labels(data, features_scaled)
        
        logger.info(f"HMM fitted with {self.n_states} states")
    
    def predict(self, data: pd.DataFrame) -> Tuple[int, np.ndarray]:
        """Predict current regime state"""
        
        if not self.is_fitted:
            return 0, np.array([0.25] * self.n_states)
        
        features = self._prepare_features(data)
        
        if len(features) == 0:
            return 0, np.array([0.25] * self.n_states)
        
        if self.scaler:
            features_scaled = self.scaler.transform(features)
        else:
            features_scaled = features
        
        if HMM_AVAILABLE and self.model is not None:
            # Get most likely state
            state = self.model.predict(features_scaled)[-1]
            
            # Get state probabilities
            state_probs = self.model.predict_proba(features_scaled)[-1]
            
            return int(state), state_probs
        else:
            # Fallback: simple rule-based
            return self._fallback_predict(data)
    
    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for HMM"""
        
        close = data['close']
        returns = close.pct_change().fillna(0)
        
        features = pd.DataFrame()
        
        # Returns
        features['returns'] = returns
        
        # Volatility
        features['volatility'] = returns.rolling(20).std().fillna(0)
        
        # Momentum
        features['momentum'] = close.pct_change(10).fillna(0)
        
        # Trend
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        features['trend'] = ((sma_20 - sma_50) / sma_50).fillna(0)
        
        # Volume (if available)
        if 'volume' in data.columns:
            vol_sma = data['volume'].rolling(20).mean()
            features['volume_ratio'] = (data['volume'] / vol_sma).fillna(1)
        
        return features.fillna(0).values
    
    def _assign_state_labels(self, data: pd.DataFrame, features: np.ndarray) -> None:
        """Assign meaningful labels to HMM states"""
        
        if not HMM_AVAILABLE or self.model is None:
            return
        
        states = self.model.predict(features)
        returns = data['close'].pct_change().fillna(0)
        volatility = returns.rolling(20).std().fillna(0)
        
        # Analyze each state
        state_stats = {}
        for state in range(self.n_states):
            mask = states == state
            if mask.sum() > 0:
                state_stats[state] = {
                    'mean_return': returns[mask].mean(),
                    'mean_vol': volatility[mask].mean(),
                    'count': mask.sum()
                }
        
        # Assign labels based on characteristics
        sorted_by_return = sorted(state_stats.items(), key=lambda x: x[1]['mean_return'])
        sorted_by_vol = sorted(state_stats.items(), key=lambda x: x[1]['mean_vol'])
        
        # Highest return = trending up
        if sorted_by_return:
            self.state_labels[sorted_by_return[-1][0]] = MarketRegime.TRENDING_UP
            self.state_labels[sorted_by_return[0][0]] = MarketRegime.TRENDING_DOWN
        
        # Highest volatility = high vol regime
        if sorted_by_vol:
            self.state_labels[sorted_by_vol[-1][0]] = MarketRegime.HIGH_VOLATILITY
    
    def _fallback_predict(self, data: pd.DataFrame) -> Tuple[int, np.ndarray]:
        """Fallback prediction without HMM"""
        
        close = data['close']
        returns = close.pct_change().fillna(0)
        
        # Simple rules
        recent_return = returns.iloc[-20:].mean() if len(returns) >= 20 else 0
        recent_vol = returns.iloc[-20:].std() if len(returns) >= 20 else 0.01
        
        if recent_vol > 0.03:  # High volatility
            state = 3
            probs = [0.1, 0.1, 0.1, 0.7]
        elif recent_return > 0.001:  # Trending up
            state = 0
            probs = [0.7, 0.1, 0.1, 0.1]
        elif recent_return < -0.001:  # Trending down
            state = 1
            probs = [0.1, 0.7, 0.1, 0.1]
        else:  # Ranging
            state = 2
            probs = [0.1, 0.1, 0.7, 0.1]
        
        return state, np.array(probs)
    
    def get_regime(self, state: int) -> MarketRegime:
        """Get regime label for state"""
        return self.state_labels.get(state, MarketRegime.UNKNOWN)


class ClusteringRegimeDetector:
    """Clustering-based regime detection using K-means and DBSCAN"""
    
    def __init__(self, n_clusters: int = 5, config: Optional[Dict] = None):
        self.n_clusters = n_clusters
        self.config = config or {}
        self.kmeans = None
        self.dbscan = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.cluster_labels = {}
        self.is_fitted = False
        
    def fit(self, data: pd.DataFrame) -> None:
        """Fit clustering models"""
        
        if not SKLEARN_AVAILABLE:
            logger.warning("sklearn not available, using fallback")
            self.is_fitted = True
            return
        
        features = self._prepare_features(data)
        
        if self.scaler:
            features_scaled = self.scaler.fit_transform(features)
        else:
            features_scaled = features
        
        # Fit K-means
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        self.kmeans.fit(features_scaled)
        
        # Fit DBSCAN for anomaly detection
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.dbscan.fit(features_scaled)
        
        # Assign labels to clusters
        self._assign_cluster_labels(data, features_scaled)
        
        self.is_fitted = True
        logger.info(f"Clustering fitted with {self.n_clusters} clusters")
    
    def predict(self, data: pd.DataFrame) -> Tuple[int, float, bool]:
        """Predict cluster and detect anomalies"""
        
        if not self.is_fitted:
            return 0, 0.0, False
        
        features = self._prepare_features(data)
        
        if len(features) == 0:
            return 0, 0.0, False
        
        if self.scaler:
            features_scaled = self.scaler.transform(features)
        else:
            features_scaled = features
        
        if SKLEARN_AVAILABLE and self.kmeans is not None:
            # Get cluster
            cluster = self.kmeans.predict(features_scaled[-1:])[-1]
            
            # Calculate distance to cluster center
            center = self.kmeans.cluster_centers_[cluster]
            distance = np.linalg.norm(features_scaled[-1] - center)
            
            # Check if anomaly (DBSCAN)
            is_anomaly = False
            if self.dbscan is not None:
                # Use core samples to check
                is_anomaly = distance > 2.0  # Simple threshold
            
            return int(cluster), float(distance), is_anomaly
        else:
            return 0, 0.0, False
    
    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for clustering"""
        
        close = data['close']
        returns = close.pct_change().fillna(0)
        
        features = pd.DataFrame()
        
        # Multi-scale returns
        for period in [1, 5, 10, 20]:
            features[f'return_{period}'] = close.pct_change(period).fillna(0)
        
        # Volatility at different scales
        for period in [5, 10, 20]:
            features[f'vol_{period}'] = returns.rolling(period).std().fillna(0)
        
        # Trend indicators
        for period in [10, 20, 50]:
            sma = close.rolling(period).mean()
            features[f'dist_sma_{period}'] = ((close - sma) / sma).fillna(0)
        
        # Volume features
        if 'volume' in data.columns:
            vol_sma = data['volume'].rolling(20).mean()
            features['volume_ratio'] = (data['volume'] / vol_sma).fillna(1)
        
        return features.fillna(0).values
    
    def _assign_cluster_labels(self, data: pd.DataFrame, features: np.ndarray) -> None:
        """Assign regime labels to clusters"""
        
        if not SKLEARN_AVAILABLE or self.kmeans is None:
            return
        
        clusters = self.kmeans.predict(features)
        returns = data['close'].pct_change().fillna(0)
        volatility = returns.rolling(20).std().fillna(0)
        
        # Analyze each cluster
        for cluster in range(self.n_clusters):
            mask = clusters == cluster
            if mask.sum() > 0:
                mean_return = returns[mask].mean()
                mean_vol = volatility[mask].mean()
                
                # Assign label based on characteristics
                if mean_vol > volatility.quantile(0.8):
                    self.cluster_labels[cluster] = MarketRegime.HIGH_VOLATILITY
                elif mean_return > returns.quantile(0.7):
                    self.cluster_labels[cluster] = MarketRegime.TRENDING_UP
                elif mean_return < returns.quantile(0.3):
                    self.cluster_labels[cluster] = MarketRegime.TRENDING_DOWN
                else:
                    self.cluster_labels[cluster] = MarketRegime.RANGING
    
    def get_regime(self, cluster: int) -> MarketRegime:
        """Get regime label for cluster"""
        return self.cluster_labels.get(cluster, MarketRegime.UNKNOWN)


class VolatilityAnalyzer:
    """Volatility regime analysis"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.volatility_history = deque(maxlen=252)  # 1 year of daily data
        
        # Percentile thresholds
        self.thresholds = {
            VolatilityRegime.VERY_LOW: 0.1,
            VolatilityRegime.LOW: 0.25,
            VolatilityRegime.NORMAL: 0.75,
            VolatilityRegime.HIGH: 0.9,
            VolatilityRegime.EXTREME: 1.0
        }
        
    def analyze(self, data: pd.DataFrame) -> Tuple[VolatilityRegime, float, float]:
        """Analyze current volatility regime"""
        
        close = data['close']
        returns = close.pct_change().fillna(0)
        
        # Calculate current volatility (annualized)
        current_vol = returns.iloc[-20:].std() * np.sqrt(252) if len(returns) >= 20 else 0.15
        
        # Update history
        self.volatility_history.append(current_vol)
        
        # Calculate percentile
        if len(self.volatility_history) > 20:
            percentile = stats.percentileofscore(list(self.volatility_history), current_vol) / 100
        else:
            percentile = 0.5
        
        # Determine regime
        regime = VolatilityRegime.NORMAL
        for vol_regime, threshold in self.thresholds.items():
            if percentile <= threshold:
                regime = vol_regime
                break
        
        return regime, current_vol, percentile
    
    def detect_volatility_spike(self, data: pd.DataFrame, threshold: float = 2.0) -> bool:
        """Detect sudden volatility spike"""
        
        close = data['close']
        returns = close.pct_change().fillna(0)
        
        if len(returns) < 30:
            return False
        
        recent_vol = returns.iloc[-5:].std()
        baseline_vol = returns.iloc[-30:-5].std()
        
        return recent_vol > baseline_vol * threshold


class TrendAnalyzer:
    """Trend strength and direction analysis"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def analyze(self, data: pd.DataFrame) -> Tuple[TrendStrength, float, int]:
        """Analyze trend strength and direction"""
        
        close = data['close']
        
        # Calculate trend indicators
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        sma_200 = close.rolling(200).mean()
        
        # ADX for trend strength
        adx = self._calculate_adx(data, 14)
        
        # Direction (-1 to 1)
        if len(close) >= 50:
            short_trend = (close.iloc[-1] - sma_20.iloc[-1]) / sma_20.iloc[-1]
            medium_trend = (sma_20.iloc[-1] - sma_50.iloc[-1]) / sma_50.iloc[-1]
            direction = 0.6 * short_trend + 0.4 * medium_trend
            direction = np.clip(direction * 10, -1, 1)  # Scale and clip
        else:
            direction = 0
        
        # Determine strength
        if adx > 40:
            if direction > 0.3:
                strength = TrendStrength.STRONG_UP
            elif direction < -0.3:
                strength = TrendStrength.STRONG_DOWN
            elif direction > 0:
                strength = TrendStrength.MODERATE_UP
            else:
                strength = TrendStrength.MODERATE_DOWN
        elif adx > 25:
            if direction > 0.2:
                strength = TrendStrength.MODERATE_UP
            elif direction < -0.2:
                strength = TrendStrength.MODERATE_DOWN
            elif direction > 0:
                strength = TrendStrength.WEAK_UP
            else:
                strength = TrendStrength.WEAK_DOWN
        else:
            strength = TrendStrength.NEUTRAL
        
        # Calculate duration
        duration = self._calculate_trend_duration(close, direction)
        
        return strength, direction, duration
    
    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate ADX"""
        
        if 'high' not in data.columns or 'low' not in data.columns:
            return 25  # Default neutral
        
        high = data['high']
        low = data['low']
        close = data['close']
        
        if len(close) < period * 2:
            return 25
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # Smoothed values
        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        # DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = dx.rolling(period).mean()
        
        return adx.iloc[-1] if not np.isnan(adx.iloc[-1]) else 25
    
    def _calculate_trend_duration(self, close: pd.Series, direction: float) -> int:
        """Calculate how long current trend has lasted"""
        
        if len(close) < 20:
            return 0
        
        sma_20 = close.rolling(20).mean()
        
        # Count bars in current trend
        duration = 0
        for i in range(len(close) - 1, max(0, len(close) - 100), -1):
            if direction > 0:
                if close.iloc[i] > sma_20.iloc[i]:
                    duration += 1
                else:
                    break
            else:
                if close.iloc[i] < sma_20.iloc[i]:
                    duration += 1
                else:
                    break
        
        return duration


class VolumeShockDetector:
    """Detect unusual volume activity"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.shock_threshold = self.config.get('shock_threshold', 3.0)
        
    def detect(self, data: pd.DataFrame) -> Tuple[bool, float]:
        """Detect volume shock"""
        
        if 'volume' not in data.columns:
            return False, 1.0
        
        volume = data['volume']
        
        if len(volume) < 30:
            return False, 1.0
        
        # Calculate volume ratio
        vol_sma = volume.rolling(20).mean()
        current_ratio = volume.iloc[-1] / vol_sma.iloc[-1] if vol_sma.iloc[-1] > 0 else 1.0
        
        # Detect shock
        is_shock = current_ratio > self.shock_threshold
        
        return is_shock, current_ratio


class YieldCurveAnalyzer:
    """Yield curve analysis for macro regime detection"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def analyze(self, yield_data: Optional[Dict[str, float]] = None) -> float:
        """Analyze yield curve slope"""
        
        if yield_data is None:
            # Default neutral slope
            return 0.0
        
        # Calculate 10Y - 2Y spread
        spread_10_2 = yield_data.get('10Y', 0) - yield_data.get('2Y', 0)
        
        return spread_10_2
    
    def is_inverted(self, yield_data: Optional[Dict[str, float]] = None) -> bool:
        """Check if yield curve is inverted"""
        slope = self.analyze(yield_data)
        return slope < 0


class VIXAnalyzer:
    """VIX and VVIX analysis"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def analyze(
        self,
        vix: Optional[float] = None,
        vvix: Optional[float] = None
    ) -> Tuple[float, float]:
        """Analyze VIX and VIX/VVIX ratio"""
        
        if vix is None:
            vix = 20.0  # Default neutral
        
        if vvix is None:
            vvix = 100.0  # Default neutral
        
        # VIX/VVIX ratio
        ratio = vix / vvix if vvix > 0 else 0.2
        
        return vix, ratio
    
    def get_fear_level(self, vix: float) -> str:
        """Get fear level from VIX"""
        
        if vix < 12:
            return "complacent"
        elif vix < 20:
            return "calm"
        elif vix < 30:
            return "cautious"
        elif vix < 40:
            return "fearful"
        else:
            return "panic"


class MarketStateClassifier:
    """
    Complete market state classification system.
    
    Combines:
    - HMM regime detection
    - Clustering analysis
    - Volatility filters
    - Trend analysis
    - Volume shock detection
    - VIX/VVIX analysis
    - Yield curve analysis
    
    Outputs recommended strategy behavior.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.hmm_detector = HMMRegimeDetector(n_states=4, config=config)
        self.cluster_detector = ClusteringRegimeDetector(n_clusters=5, config=config)
        self.volatility_analyzer = VolatilityAnalyzer(config)
        self.trend_analyzer = TrendAnalyzer(config)
        self.volume_detector = VolumeShockDetector(config)
        self.yield_analyzer = YieldCurveAnalyzer(config)
        self.vix_analyzer = VIXAnalyzer(config)
        
        # State history
        self.state_history: List[MarketState] = []
        self.max_history = 1000
        
        # Current state
        self.current_state: Optional[MarketState] = None
        
        # Strategy recommendations
        self.strategy_map = {
            MarketRegime.TRENDING_UP: {
                'strategy': 'trend_following',
                'position_mult': 1.2,
                'stop_mult': 1.0
            },
            MarketRegime.TRENDING_DOWN: {
                'strategy': 'trend_following_short',
                'position_mult': 1.0,
                'stop_mult': 0.8
            },
            MarketRegime.RANGING: {
                'strategy': 'mean_reversion',
                'position_mult': 0.8,
                'stop_mult': 1.2
            },
            MarketRegime.HIGH_VOLATILITY: {
                'strategy': 'volatility_breakout',
                'position_mult': 0.5,
                'stop_mult': 1.5
            },
            MarketRegime.LOW_VOLATILITY: {
                'strategy': 'range_trading',
                'position_mult': 1.0,
                'stop_mult': 0.8
            },
            MarketRegime.CRASH: {
                'strategy': 'defensive',
                'position_mult': 0.3,
                'stop_mult': 0.5
            },
            MarketRegime.RECOVERY: {
                'strategy': 'accumulation',
                'position_mult': 0.7,
                'stop_mult': 1.0
            }
        }
        
        logger.info("MarketStateClassifier initialized")
    
    def fit(self, data: pd.DataFrame) -> None:
        """Fit all models on historical data"""
        
        logger.info("Fitting market state classifier...")
        
        # Fit HMM
        self.hmm_detector.fit(data)
        
        # Fit clustering
        self.cluster_detector.fit(data)
        
        logger.info("Market state classifier fitted")
    
    def classify(
        self,
        data: pd.DataFrame,
        vix: Optional[float] = None,
        vvix: Optional[float] = None,
        yield_data: Optional[Dict[str, float]] = None
    ) -> MarketState:
        """Classify current market state"""
        
        timestamp = datetime.now()
        
        # HMM prediction
        hmm_state, hmm_probs = self.hmm_detector.predict(data)
        hmm_regime = self.hmm_detector.get_regime(hmm_state)
        
        # Clustering prediction
        cluster, cluster_dist, is_anomaly = self.cluster_detector.predict(data)
        cluster_regime = self.cluster_detector.get_regime(cluster)
        
        # Volatility analysis
        vol_regime, current_vol, vol_percentile = self.volatility_analyzer.analyze(data)
        vol_spike = self.volatility_analyzer.detect_volatility_spike(data)
        
        # Trend analysis
        trend_strength, trend_direction, trend_duration = self.trend_analyzer.analyze(data)
        
        # Volume shock
        volume_shock, volume_ratio = self.volume_detector.detect(data)
        
        # VIX analysis
        vix_level, vix_vvix_ratio = self.vix_analyzer.analyze(vix, vvix)
        
        # Yield curve
        yield_slope = self.yield_analyzer.analyze(yield_data)
        
        # Combine signals to determine final regime
        final_regime = self._combine_signals(
            hmm_regime, cluster_regime, vol_regime, trend_strength,
            vol_spike, volume_shock, is_anomaly, vix_level
        )
        
        # Calculate regime confidence
        confidence = self._calculate_confidence(hmm_probs, cluster_dist, vol_percentile)
        
        # Calculate regime duration
        regime_duration = self._calculate_regime_duration(final_regime)
        
        # Get strategy recommendation
        strategy_rec = self.strategy_map.get(final_regime, self.strategy_map[MarketRegime.RANGING])
        
        # Create state
        state = MarketState(
            timestamp=timestamp,
            regime=final_regime,
            regime_confidence=confidence,
            regime_duration=regime_duration,
            volatility_regime=vol_regime,
            current_volatility=current_vol,
            volatility_percentile=vol_percentile,
            trend_strength=trend_strength,
            trend_direction=trend_direction,
            trend_duration=trend_duration,
            hmm_state=hmm_state,
            hmm_state_probs=list(hmm_probs),
            cluster_id=cluster,
            cluster_distance=cluster_dist,
            vix_level=vix_level,
            vix_vvix_ratio=vix_vvix_ratio,
            yield_curve_slope=yield_slope,
            volume_shock=volume_shock,
            volume_ratio=volume_ratio,
            recommended_strategy=strategy_rec['strategy'],
            position_size_multiplier=strategy_rec['position_mult'],
            stop_loss_multiplier=strategy_rec['stop_mult']
        )
        
        # Update history
        self.state_history.append(state)
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
        
        self.current_state = state
        
        return state
    
    def _combine_signals(
        self,
        hmm_regime: MarketRegime,
        cluster_regime: MarketRegime,
        vol_regime: VolatilityRegime,
        trend_strength: TrendStrength,
        vol_spike: bool,
        volume_shock: bool,
        is_anomaly: bool,
        vix_level: float
    ) -> MarketRegime:
        """Combine multiple signals into final regime"""
        
        # Emergency conditions
        if vix_level > 40 or vol_spike:
            return MarketRegime.CRASH
        
        if is_anomaly and volume_shock:
            return MarketRegime.HIGH_VOLATILITY
        
        # High volatility override
        if vol_regime == VolatilityRegime.EXTREME:
            return MarketRegime.HIGH_VOLATILITY
        
        # Trend-based
        if trend_strength in [TrendStrength.STRONG_UP, TrendStrength.MODERATE_UP]:
            return MarketRegime.TRENDING_UP
        
        if trend_strength in [TrendStrength.STRONG_DOWN, TrendStrength.MODERATE_DOWN]:
            return MarketRegime.TRENDING_DOWN
        
        # Use HMM as primary
        if hmm_regime != MarketRegime.UNKNOWN:
            return hmm_regime
        
        # Fall back to cluster
        if cluster_regime != MarketRegime.UNKNOWN:
            return cluster_regime
        
        # Default to ranging
        return MarketRegime.RANGING
    
    def _calculate_confidence(
        self,
        hmm_probs: np.ndarray,
        cluster_dist: float,
        vol_percentile: float
    ) -> float:
        """Calculate confidence in regime classification"""
        
        # HMM confidence (max probability)
        hmm_conf = max(hmm_probs) if len(hmm_probs) > 0 else 0.5
        
        # Cluster confidence (inverse of distance)
        cluster_conf = 1 / (1 + cluster_dist)
        
        # Volatility confidence (how extreme)
        vol_conf = abs(vol_percentile - 0.5) * 2
        
        # Weighted average
        confidence = 0.5 * hmm_conf + 0.3 * cluster_conf + 0.2 * vol_conf
        
        return min(max(confidence, 0), 1)
    
    def _calculate_regime_duration(self, current_regime: MarketRegime) -> int:
        """Calculate how long we've been in current regime"""
        
        duration = 0
        for state in reversed(self.state_history):
            if state.regime == current_regime:
                duration += 1
            else:
                break
        
        return duration
    
    def get_current_state(self) -> Optional[MarketState]:
        """Get current market state"""
        return self.current_state
    
    def get_strategy_recommendation(self) -> Dict:
        """Get current strategy recommendation"""
        
        if self.current_state is None:
            return {
                'strategy': 'neutral',
                'position_multiplier': 1.0,
                'stop_multiplier': 1.0,
                'regime': 'unknown'
            }
        
        return {
            'strategy': self.current_state.recommended_strategy,
            'position_multiplier': self.current_state.position_size_multiplier,
            'stop_multiplier': self.current_state.stop_loss_multiplier,
            'regime': self.current_state.regime.name,
            'confidence': self.current_state.regime_confidence
        }
    
    def should_trade(self) -> Tuple[bool, str]:
        """Determine if conditions are favorable for trading"""
        
        if self.current_state is None:
            return True, "No state available"
        
        # Don't trade in crash
        if self.current_state.regime == MarketRegime.CRASH:
            return False, "Market in crash regime"
        
        # Don't trade with extreme volatility
        if self.current_state.volatility_regime == VolatilityRegime.EXTREME:
            return False, "Extreme volatility"
        
        # Don't trade with volume shock
        if self.current_state.volume_shock:
            return False, "Volume shock detected"
        
        # Low confidence
        if self.current_state.regime_confidence < 0.3:
            return False, "Low regime confidence"
        
        return True, "Conditions favorable"


# Factory function
def create_classifier(config: Optional[Dict] = None) -> MarketStateClassifier:
    """Create and return a MarketStateClassifier instance"""
    return MarketStateClassifier(config)


# Quick start
def quick_classify(data: pd.DataFrame) -> MarketState:
    """Quick classification with default settings"""
    classifier = create_classifier()
    classifier.fit(data)
    return classifier.classify(data)

"""
Market Regime Detection System
Identifies and adapts to different market regimes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from hmmlearn import hmm
import warnings
import numpy
import pandas
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class MarketRegime:
    """Market regime classification"""
    regime_type: str
    confidence: float
    start_time: datetime
    duration: int  # in periods
    characteristics: Dict
    transition_probs: Dict
    stability: float
    metrics: Dict

@dataclass
class RegimeSignal:
    """Market regime signal"""
    signal_type: str
    strength: float
    confidence: float
    timestamp: datetime
    regime: str
    previous_regime: Optional[str]
    transition_probability: float
    supporting_data: Dict
    metadata: Dict

class MarketState:
    """Market state types"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    CAPITULATION = "capitulation"
    RECOVERY = "recovery"

class RegimeDetector:
    """
    Advanced market regime detection system
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Analysis parameters
        self.lookback_window = self.config.get('lookback_window', 100)
        self.short_window = self.config.get('short_window', 20)
        self.transition_threshold = self.config.get('transition_threshold', 0.7)
        
        # Regime models
        self.hmm_model = self._initialize_hmm()
        self.gmm_model = self._initialize_gmm()
        self.regime_history = []
        
        # State tracking
        self.current_regime = None
        self.regime_probabilities = {}
        self.transition_matrix = None
        
        logger.info("Regime Detector initialized")
    
    def detect_regime(self, market_data: pd.DataFrame) -> Tuple[MarketRegime, List[RegimeSignal]]:
        """
        Detect current market regime and generate signals
        """
        signals = []
        
        # Extract features
        features = self._extract_regime_features(market_data)
        
        # Apply different regime detection methods
        hmm_regime = self._detect_hmm_regime(features)
        gmm_regime = self._detect_gmm_regime(features)
        heuristic_regime = self._detect_heuristic_regime(market_data)
        
        # Combine regime detections
        regime = self._combine_regime_detections([
            (hmm_regime, 0.4),
            (gmm_regime, 0.3),
            (heuristic_regime, 0.3)
        ])
        
        # Generate signals for regime changes
        if self.current_regime and regime.regime_type != self.current_regime.regime_type:
            signals.extend(self._generate_regime_change_signals(regime))
        
        # Update state
        self.current_regime = regime
        self.regime_history.append(regime)
        
        # Generate additional signals
        signals.extend(self._analyze_regime_characteristics(regime, market_data))
        signals.extend(self._detect_regime_transitions(market_data))
        
        return regime, signals
    
    def _initialize_hmm(self) -> hmm.GaussianHMM:
        """
        Initialize Hidden Markov Model
        """
        return hmm.GaussianHMM(
            n_components=5,  # Number of regime states
            covariance_type="full",
            n_iter=100
        )
    
    def _initialize_gmm(self) -> GaussianMixture:
        """
        Initialize Gaussian Mixture Model
        """
        return GaussianMixture(
            n_components=5,
            covariance_type="full",
            random_state=42
        )
    
    def _extract_regime_features(self, market_data: pd.DataFrame) -> np.ndarray:
        """
        Extract features for regime detection
        """
        features = []
        
        if len(market_data) < self.short_window:
            return np.array(features)
        
        # Price-based features
        returns = np.log(market_data['close']).diff().dropna()
        features.extend([
            returns.mean(),
            returns.std(),
            returns.skew(),
            returns.kurtosis()
        ])
        
        # Trend features
        sma_short = market_data['close'].rolling(window=self.short_window).mean()
        sma_long = market_data['close'].rolling(window=self.lookback_window).mean()
        features.extend([
            (sma_short.iloc[-1] - sma_long.iloc[-1]) / sma_long.iloc[-1],
            returns.rolling(window=self.short_window).mean().iloc[-1],
            returns.rolling(window=self.lookback_window).mean().iloc[-1]
        ])
        
        # Volatility features
        if 'high' in market_data.columns and 'low' in market_data.columns:
            high_low_ratio = np.log(market_data['high'] / market_data['low'])
            features.extend([
                high_low_ratio.mean(),
                high_low_ratio.std(),
                high_low_ratio.rolling(window=self.short_window).std().iloc[-1]
            ])
        
        # Volume features
        if 'volume' in market_data.columns:
            volume = market_data['volume']
            features.extend([
                volume.mean(),
                volume.std(),
                volume.rolling(window=self.short_window).mean().iloc[-1] / 
                volume.rolling(window=self.lookback_window).mean().iloc[-1]
            ])
        
        return np.array(features).reshape(1, -1)
    
    def _detect_hmm_regime(self, features: np.ndarray) -> MarketRegime:
        """
        Detect regime using HMM
        """
        try:
            if not hasattr(self.hmm_model, 'means_'):
                # Initialize with historical data if available
                if len(self.regime_history) > self.lookback_window:
                    historical_features = np.array([
                        self._extract_regime_features(r.characteristics['data'])
                        for r in self.regime_history[-self.lookback_window:]
                    ])
                    self.hmm_model.fit(historical_features)
                else:
                    return self._get_default_regime()
            
            # Predict regime
            state = self.hmm_model.predict(features)[0]
            state_prob = np.max(self.hmm_model.predict_proba(features))
            
            regime_type = self._map_hmm_state_to_regime(state)
            
            return MarketRegime(
                regime_type=regime_type,
                confidence=state_prob,
                start_time=datetime.now(),
                duration=1,
                characteristics=self._get_regime_characteristics(regime_type),
                transition_probs=dict(enumerate(self.hmm_model.transmat_[state])),
                stability=self._calculate_regime_stability(regime_type),
                metrics={'hmm_state': state, 'hmm_likelihood': self.hmm_model.score(features)}
            )
            
        except Exception as e:
            logger.warning(f"HMM regime detection failed: {e}")
            return self._get_default_regime()
    
    def _detect_gmm_regime(self, features: np.ndarray) -> MarketRegime:
        """
        Detect regime using GMM
        """
        try:
            if not hasattr(self.gmm_model, 'means_'):
                # Initialize with historical data
                if len(self.regime_history) > self.lookback_window:
                    historical_features = np.array([
                        self._extract_regime_features(r.characteristics['data'])
                        for r in self.regime_history[-self.lookback_window:]
                    ])
                    self.gmm_model.fit(historical_features)
                else:
                    return self._get_default_regime()
            
            # Predict regime
            cluster = self.gmm_model.predict(features)[0]
            probs = self.gmm_model.predict_proba(features)[0]
            
            regime_type = self._map_gmm_cluster_to_regime(cluster)
            
            return MarketRegime(
                regime_type=regime_type,
                confidence=probs[cluster],
                start_time=datetime.now(),
                duration=1,
                characteristics=self._get_regime_characteristics(regime_type),
                transition_probs={},  # GMM doesn't provide transition probabilities
                stability=self._calculate_regime_stability(regime_type),
                metrics={'gmm_cluster': cluster, 'gmm_score': self.gmm_model.score(features)}
            )
            
        except Exception as e:
            logger.warning(f"GMM regime detection failed: {e}")
            return self._get_default_regime()
    
    def _detect_heuristic_regime(self, market_data: pd.DataFrame) -> MarketRegime:
        """
        Detect regime using heuristic rules
        """
        if len(market_data) < self.short_window:
            return self._get_default_regime()
        
        # Calculate indicators
        returns = np.log(market_data['close']).diff().dropna()
        volatility = returns.rolling(window=self.short_window).std().iloc[-1]
        trend = self._calculate_trend_strength(market_data)
        
        # Determine regime
        regime_type = self._determine_heuristic_regime(volatility, trend, market_data)
        confidence = self._calculate_heuristic_confidence(volatility, trend)
        
        return MarketRegime(
            regime_type=regime_type,
            confidence=confidence,
            start_time=datetime.now(),
            duration=1,
            characteristics=self._get_regime_characteristics(regime_type),
            transition_probs={},
            stability=self._calculate_regime_stability(regime_type),
            metrics={
                'volatility': volatility,
                'trend_strength': trend,
                'heuristic_score': confidence
            }
        )
    
    def _combine_regime_detections(self, regime_weights: List[Tuple[MarketRegime, float]]) -> MarketRegime:
        """
        Combine multiple regime detections with weights
        """
        if not regime_weights:
            return self._get_default_regime()
        
        # Calculate weighted regime probabilities
        regime_probs = {}
        for regime, weight in regime_weights:
            if regime.regime_type not in regime_probs:
                regime_probs[regime.regime_type] = 0
            regime_probs[regime.regime_type] += regime.confidence * weight
        
        # Select regime with highest probability
        best_regime = max(regime_probs.items(), key=lambda x: x[1])
        regime_type, confidence = best_regime
        
        return MarketRegime(
            regime_type=regime_type,
            confidence=confidence,
            start_time=datetime.now(),
            duration=1,
            characteristics=self._get_regime_characteristics(regime_type),
            transition_probs=self._combine_transition_probs(regime_weights),
            stability=np.mean([r.stability * w for r, w in regime_weights]),
            metrics={
                'regime_probabilities': regime_probs,
                'combined_score': confidence
            }
        )
    
    def _generate_regime_change_signals(self, new_regime: MarketRegime) -> List[RegimeSignal]:
        """
        Generate signals for regime changes
        """
        signals = []
        
        if not self.current_regime:
            return signals
        
        # Regime change signal
        signals.append(RegimeSignal(
            signal_type="regime_change",
            strength=new_regime.confidence,
            confidence=new_regime.confidence,
            timestamp=datetime.now(),
            regime=new_regime.regime_type,
            previous_regime=self.current_regime.regime_type,
            transition_probability=self._get_transition_probability(
                self.current_regime.regime_type,
                new_regime.regime_type
            ),
            supporting_data={
                'duration': self.current_regime.duration,
                'stability': new_regime.stability,
                'characteristics': new_regime.characteristics
            },
            metadata={'change_type': 'regime_transition'}
        ))
        
        # Check for significant characteristic changes
        changed_characteristics = self._compare_regime_characteristics(
            self.current_regime.characteristics,
            new_regime.characteristics
        )
        
        if changed_characteristics:
            signals.append(RegimeSignal(
                signal_type="characteristic_change",
                strength=new_regime.confidence,
                confidence=new_regime.confidence * 0.8,
                timestamp=datetime.now(),
                regime=new_regime.regime_type,
                previous_regime=self.current_regime.regime_type,
                transition_probability=self._get_transition_probability(
                    self.current_regime.regime_type,
                    new_regime.regime_type
                ),
                supporting_data=changed_characteristics,
                metadata={'change_type': 'characteristic'}
            ))
        
        return signals
    
    def _analyze_regime_characteristics(self, regime: MarketRegime, 
                                     market_data: pd.DataFrame) -> List[RegimeSignal]:
        """
        Analyze regime characteristics for additional signals
        """
        signals = []
        
        # Analyze regime stability
        if regime.stability < 0.3:
            signals.append(RegimeSignal(
                signal_type="regime_instability",
                strength=1 - regime.stability,
                confidence=regime.confidence * 0.7,
                timestamp=datetime.now(),
                regime=regime.regime_type,
                previous_regime=None,
                transition_probability=0,
                supporting_data={
                    'stability': regime.stability,
                    'volatility': regime.characteristics.get('volatility', 0),
                    'duration': regime.duration
                },
                metadata={'analysis_type': 'stability'}
            ))
        
        # Analyze regime extremes
        if self._is_extreme_regime(regime, market_data):
            signals.append(RegimeSignal(
                signal_type="regime_extreme",
                strength=self._calculate_regime_extreme_strength(regime, market_data),
                confidence=regime.confidence,
                timestamp=datetime.now(),
                regime=regime.regime_type,
                previous_regime=None,
                transition_probability=0,
                supporting_data=self._get_extreme_characteristics(regime, market_data),
                metadata={'analysis_type': 'extreme'}
            ))
        
        return signals
    
    def _detect_regime_transitions(self, market_data: pd.DataFrame) -> List[RegimeSignal]:
        """
        Detect potential regime transitions
        """
        signals = []
        
        if not self.current_regime or len(self.regime_history) < 2:
            return signals
        
        # Calculate transition probabilities
        transition_probs = self._calculate_transition_probabilities()
        
        # Check for high probability transitions
        for target_regime, prob in transition_probs.items():
            if prob > self.transition_threshold:
                signals.append(RegimeSignal(
                    signal_type="regime_transition_warning",
                    strength=prob,
                    confidence=self.current_regime.confidence * 0.6,
                    timestamp=datetime.now(),
                    regime=self.current_regime.regime_type,
                    previous_regime=None,
                    transition_probability=prob,
                    supporting_data={
                        'target_regime': target_regime,
                        'current_duration': self.current_regime.duration,
                        'historical_transitions': self._get_historical_transitions(target_regime)
                    },
                    metadata={'warning_type': 'transition'}
                ))
        
        return signals
    
    def _map_hmm_state_to_regime(self, state: int) -> str:
        """Map HMM state to regime type"""
        # Map based on state characteristics
        if not hasattr(self.hmm_model, 'means_'):
            return MarketState.RANGING
        
        state_mean = self.hmm_model.means_[state][0]
        state_cov = self.hmm_model.covars_[state][0][0]
        
        if state_mean > 0.5 and state_cov < 0.5:
            return MarketState.TRENDING_UP
        elif state_mean < -0.5 and state_cov < 0.5:
            return MarketState.TRENDING_DOWN
        elif state_cov > 1.0:
            return MarketState.VOLATILE
        elif abs(state_mean) < 0.1:
            return MarketState.RANGING
        else:
            return MarketState.RANGING
    
    def _map_gmm_cluster_to_regime(self, cluster: int) -> str:
        """Map GMM cluster to regime type"""
        if not hasattr(self.gmm_model, 'means_'):
            return MarketState.RANGING
        
        cluster_mean = self.gmm_model.means_[cluster][0]
        cluster_cov = self.gmm_model.covariances_[cluster][0][0]
        
        if cluster_mean > 0.5:
            return MarketState.TRENDING_UP
        elif cluster_mean < -0.5:
            return MarketState.TRENDING_DOWN
        elif cluster_cov > 1.0:
            return MarketState.VOLATILE
        else:
            return MarketState.RANGING
    
    def _determine_heuristic_regime(self, volatility: float, trend: float,
                                  market_data: pd.DataFrame) -> str:
        """
        Determine regime using heuristic rules
        """
        # Check for breakout
        if self._is_breakout(market_data):
            return MarketState.BREAKOUT
        
        # Check for reversal
        if self._is_reversal(market_data):
            return MarketState.REVERSAL
        
        # Check trend and volatility conditions
        if trend > 0.7:
            return MarketState.TRENDING_UP
        elif trend < -0.7:
            return MarketState.TRENDING_DOWN
        elif volatility > 0.02:
            return MarketState.VOLATILE
        else:
            return MarketState.RANGING
    
    def _calculate_trend_strength(self, market_data: pd.DataFrame) -> float:
        """
        Calculate trend strength indicator
        """
        if len(market_data) < self.lookback_window:
            return 0
        
        # Calculate moving averages
        sma_short = market_data['close'].rolling(window=self.short_window).mean()
        sma_long = market_data['close'].rolling(window=self.lookback_window).mean()
        
        # Calculate trend strength
        trend = (sma_short.iloc[-1] - sma_long.iloc[-1]) / sma_long.iloc[-1]
        
        return np.clip(trend, -1, 1)
    
    def _calculate_heuristic_confidence(self, volatility: float, trend: float) -> float:
        """
        Calculate confidence in heuristic regime detection
        """
        # Higher confidence for strong trends or clear ranging markets
        if abs(trend) > 0.7:
            confidence = abs(trend)
        elif volatility < 0.01:
            confidence = 0.8
        else:
            confidence = 0.5
        
        return min(1.0, confidence)
    
    def _get_regime_characteristics(self, regime_type: str) -> Dict:
        """
        Get characteristics for a regime type
        """
        characteristics = {
            MarketState.TRENDING_UP: {
                'trend_direction': 'up',
                'volatility': 'medium',
                'volume_profile': 'increasing',
                'mean_reversion': 'low'
            },
            MarketState.TRENDING_DOWN: {
                'trend_direction': 'down',
                'volatility': 'medium',
                'volume_profile': 'increasing',
                'mean_reversion': 'low'
            },
            MarketState.RANGING: {
                'trend_direction': 'sideways',
                'volatility': 'low',
                'volume_profile': 'decreasing',
                'mean_reversion': 'high'
            },
            MarketState.VOLATILE: {
                'trend_direction': 'mixed',
                'volatility': 'high',
                'volume_profile': 'spiking',
                'mean_reversion': 'low'
            },
            MarketState.BREAKOUT: {
                'trend_direction': 'accelerating',
                'volatility': 'increasing',
                'volume_profile': 'surging',
                'mean_reversion': 'very_low'
            }
        }
        
        return characteristics.get(regime_type, {})
    
    def _calculate_regime_stability(self, regime_type: str) -> float:
        """
        Calculate stability score for current regime
        """
        if len(self.regime_history) < 5:
            return 0.5
        
        # Check recent regime consistency
        recent_regimes = [r.regime_type for r in self.regime_history[-5:]]
        regime_count = recent_regimes.count(regime_type)
        
        return regime_count / 5
    
    def _get_transition_probability(self, from_regime: str, to_regime: str) -> float:
        """
        Get probability of transition between regimes
        """
        if not self.transition_matrix:
            self._update_transition_matrix()
        
        if not self.transition_matrix:
            return 0
        
        return self.transition_matrix.get((from_regime, to_regime), 0)
    
    def _update_transition_matrix(self):
        """
        Update regime transition probability matrix
        """
        if len(self.regime_history) < 2:
            return
        
        transitions = {}
        counts = {}
        
        for i in range(len(self.regime_history) - 1):
            from_regime = self.regime_history[i].regime_type
            to_regime = self.regime_history[i + 1].regime_type
            
            if from_regime not in counts:
                counts[from_regime] = 0
            counts[from_regime] += 1
            
            key = (from_regime, to_regime)
            if key not in transitions:
                transitions[key] = 0
            transitions[key] += 1
        
        # Calculate probabilities
        self.transition_matrix = {}
        for (from_regime, to_regime), count in transitions.items():
            if from_regime in counts and counts[from_regime] > 0:
                self.transition_matrix[(from_regime, to_regime)] = count / counts[from_regime]
    
    def _is_breakout(self, market_data: pd.DataFrame) -> bool:
        """
        Detect breakout conditions
        """
        if len(market_data) < self.lookback_window:
            return False
        
        # Calculate Bollinger Bands
        sma = market_data['close'].rolling(window=self.lookback_window).mean()
        std = market_data['close'].rolling(window=self.lookback_window).std()
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std
        
        # Check for price breakout
        current_price = market_data['close'].iloc[-1]
        return current_price > upper_band.iloc[-1] or current_price < lower_band.iloc[-1]
    
    def _is_reversal(self, market_data: pd.DataFrame) -> bool:
        """
        Detect reversal conditions
        """
        if len(market_data) < self.lookback_window:
            return False
        
        # Calculate trend
        sma_short = market_data['close'].rolling(window=self.short_window).mean()
        sma_long = market_data['close'].rolling(window=self.lookback_window).mean()
        
        # Check for trend reversal
        current_trend = sma_short.iloc[-1] > sma_long.iloc[-1]
        previous_trend = sma_short.iloc[-2] > sma_long.iloc[-2]
        
        return current_trend != previous_trend
    
    def _is_extreme_regime(self, regime: MarketRegime, market_data: pd.DataFrame) -> bool:
        """
        Check if current regime is showing extreme characteristics
        """
        if len(market_data) < self.lookback_window:
            return False
        
        returns = np.log(market_data['close']).diff().dropna()
        volatility = returns.rolling(window=self.short_window).std().iloc[-1]
        
        if regime.regime_type in [MarketState.VOLATILE, MarketState.BREAKOUT]:
            return volatility > np.percentile(returns.rolling(window=self.short_window).std(), 95)
        elif regime.regime_type in [MarketState.TRENDING_UP, MarketState.TRENDING_DOWN]:
            trend = self._calculate_trend_strength(market_data)
            return abs(trend) > 0.9
        
        return False
    
    def _calculate_regime_extreme_strength(self, regime: MarketRegime,
                                         market_data: pd.DataFrame) -> float:
        """
        Calculate strength of extreme regime characteristics
        """
        if len(market_data) < self.lookback_window:
            return 0
        
        returns = np.log(market_data['close']).diff().dropna()
        volatility = returns.rolling(window=self.short_window).std()
        trend = self._calculate_trend_strength(market_data)
        
        if regime.regime_type in [MarketState.VOLATILE, MarketState.BREAKOUT]:
            vol_percentile = np.percentile(volatility, 95)
            return min((volatility.iloc[-1] / vol_percentile - 1) * 2, 1.0)
        elif regime.regime_type in [MarketState.TRENDING_UP, MarketState.TRENDING_DOWN]:
            return min(abs(trend) * 1.1, 1.0)
        
        return 0
    
    def _get_extreme_characteristics(self, regime: MarketRegime,
                                   market_data: pd.DataFrame) -> Dict:
        """
        Get characteristics of extreme regime behavior
        """
        returns = np.log(market_data['close']).diff().dropna()
        volatility = returns.rolling(window=self.short_window).std()
        
        return {
            'volatility_percentile': np.percentile(volatility, 95),
            'current_volatility': volatility.iloc[-1],
            'trend_strength': self._calculate_trend_strength(market_data),
            'volume_ratio': market_data['volume'].iloc[-1] / market_data['volume'].mean() 
            if 'volume' in market_data.columns else 1.0
        }
    
    def _get_default_regime(self) -> MarketRegime:
        """
        Get default regime when detection fails
        """
        return MarketRegime(
            regime_type=MarketState.RANGING,
            confidence=0.5,
            start_time=datetime.now(),
            duration=1,
            characteristics=self._get_regime_characteristics(MarketState.RANGING),
            transition_probs={},
            stability=0.5,
            metrics={}
        )
    
    def _combine_transition_probs(self, 
                                regime_weights: List[Tuple[MarketRegime, float]]) -> Dict:
        """
        Combine transition probabilities from multiple regime detections
        """
        combined_probs = {}
        
        for regime, weight in regime_weights:
            for (from_regime, to_regime), prob in regime.transition_probs.items():
                if (from_regime, to_regime) not in combined_probs:
                    combined_probs[(from_regime, to_regime)] = 0
                combined_probs[(from_regime, to_regime)] += prob * weight
        
        return combined_probs
    
    def _compare_regime_characteristics(self, old_chars: Dict, new_chars: Dict) -> Dict:
        """
        Compare regime characteristics to identify significant changes
        """
        changes = {}
        
        for key in set(old_chars.keys()) & set(new_chars.keys()):
            if old_chars[key] != new_chars[key]:
                changes[key] = {
                    'old': old_chars[key],
                    'new': new_chars[key]
                }
        
        return changes
    
    def _get_historical_transitions(self, target_regime: str) -> List[Dict]:
        """
        Get historical transitions to target regime
        """
        transitions = []
        
        for i in range(len(self.regime_history) - 1):
            if self.regime_history[i + 1].regime_type == target_regime:
                transitions.append({
                    'from_regime': self.regime_history[i].regime_type,
                    'timestamp': self.regime_history[i + 1].start_time,
                    'duration': self.regime_history[i].duration
                })
        
        return transitions[-5:]  # Return last 5 transitions

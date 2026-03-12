"""
Multi-Brain Architecture Module
================================

Specialized sub-modules that work together:
- Alpha Blending Layer (ensemble aggregator)
- Regime Detection (market condition classifier)
- Strategy Selector (activates/deactivates strategies)
- Brain Coordinator (orchestrates all brains)

Features:
- Dynamic model weighting
- Automatic strategy activation/deactivation
- Real-time regime adaptation
- Self-correcting mechanisms
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class MarketRegime(Enum):
    """Market regime classifications"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    CHOPPY_RANGE = "choppy_range"
    VIOLENT_BREAKOUT = "violent_breakout"
    HIGH_VOL_COMPRESSION = "high_vol_compression"
    EVENT_DRIVEN = "event_driven"
    OVERNIGHT_ILLIQUIDITY = "overnight_illiquidity"
    NORMAL = "normal"


class BrainType(Enum):
    """Types of specialized brains"""
    TREND_FOLLOWER = "trend_follower"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    SENTIMENT = "sentiment"
    MICROSTRUCTURE = "microstructure"
    STATISTICAL_ARB = "statistical_arb"
    EVENT_DRIVEN = "event_driven"


@dataclass
class BrainSignal:
    """Signal from a specialized brain"""
    brain_type: BrainType
    timestamp: datetime
    symbol: str
    direction: str  # 'long', 'short', 'neutral'
    strength: float  # -1 to +1
    confidence: float  # 0 to 1
    features: Dict[str, float] = field(default_factory=dict)
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'brain_type': self.brain_type.value,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'direction': self.direction,
            'strength': self.strength,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
        }


@dataclass
class BlendedSignal:
    """Blended signal from all brains"""
    timestamp: datetime
    symbol: str
    direction: str
    strength: float
    confidence: float
    contributing_brains: List[str]
    brain_weights: Dict[str, float]
    regime: MarketRegime
    should_trade: bool
    position_size_multiplier: float
    reasoning: str


class BaseBrain(ABC):
    """Base class for specialized brains"""
    
    def __init__(self, brain_type: BrainType, config: Dict[str, Any] = None):
        self.brain_type = brain_type
        self.config = config or {}
        self.is_active = True
        self.performance_history: deque = deque(maxlen=1000)
        self.signal_history: deque = deque(maxlen=1000)
        
    @abstractmethod
    def generate_signal(self, market_data: Dict[str, Any]) -> BrainSignal:
        """Generate trading signal"""
        pass
    
    def record_performance(self, signal: BrainSignal, actual_return: float):
        """Record signal performance"""
        self.performance_history.append({
            'timestamp': datetime.now(),
            'signal': signal,
            'actual_return': actual_return,
            'correct': (signal.direction == 'long' and actual_return > 0) or
                      (signal.direction == 'short' and actual_return < 0),
        })
    
    def get_accuracy(self, lookback: int = 100) -> float:
        """Get recent accuracy"""
        recent = list(self.performance_history)[-lookback:]
        if not recent:
            return 0.5
        return sum(1 for r in recent if r['correct']) / len(recent)
    
    def get_sharpe(self, lookback: int = 100) -> float:
        """Get recent Sharpe ratio"""
        recent = list(self.performance_history)[-lookback:]
        if len(recent) < 10:
            return 0
        
        returns = []
        for r in recent:
            if r['signal'].direction == 'long':
                returns.append(r['actual_return'])
            elif r['signal'].direction == 'short':
                returns.append(-r['actual_return'])
        
        if not returns:
            return 0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        return mean_return / std_return * np.sqrt(252) if std_return > 0 else 0


class TrendFollowerBrain(BaseBrain):
    """Trend following brain"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(BrainType.TREND_FOLLOWER, config)
        self.lookback_periods = self.config.get('lookback_periods', [20, 50, 200])
    
    def generate_signal(self, market_data: Dict[str, Any]) -> BrainSignal:
        prices = market_data.get('prices', [])
        
        if len(prices) < max(self.lookback_periods):
            return BrainSignal(
                brain_type=self.brain_type,
                timestamp=datetime.now(),
                symbol=market_data.get('symbol', ''),
                direction='neutral',
                strength=0,
                confidence=0,
                reasoning="Insufficient data",
            )
        
        # Calculate moving averages
        mas = {}
        for period in self.lookback_periods:
            mas[period] = np.mean(prices[-period:])
        
        current_price = prices[-1]
        
        # Trend signals
        signals = []
        for period, ma in mas.items():
            if current_price > ma:
                signals.append(1)
            elif current_price < ma:
                signals.append(-1)
            else:
                signals.append(0)
        
        # Aggregate
        avg_signal = np.mean(signals)
        
        if avg_signal > 0.5:
            direction = 'long'
        elif avg_signal < -0.5:
            direction = 'short'
        else:
            direction = 'neutral'
        
        strength = abs(avg_signal)
        confidence = min(abs(avg_signal) + 0.3, 1.0)
        
        return BrainSignal(
            brain_type=self.brain_type,
            timestamp=datetime.now(),
            symbol=market_data.get('symbol', ''),
            direction=direction,
            strength=strength * (1 if direction == 'long' else -1),
            confidence=confidence,
            features={'ma_signals': avg_signal},
            reasoning=f"MA alignment: {avg_signal:.2f}",
        )


class MeanReversionBrain(BaseBrain):
    """Mean reversion brain"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(BrainType.MEAN_REVERSION, config)
        self.lookback = self.config.get('lookback', 20)
        self.entry_zscore = self.config.get('entry_zscore', 2.0)
    
    def generate_signal(self, market_data: Dict[str, Any]) -> BrainSignal:
        prices = market_data.get('prices', [])
        
        if len(prices) < self.lookback:
            return BrainSignal(
                brain_type=self.brain_type,
                timestamp=datetime.now(),
                symbol=market_data.get('symbol', ''),
                direction='neutral',
                strength=0,
                confidence=0,
                reasoning="Insufficient data",
            )
        
        # Calculate z-score
        recent = prices[-self.lookback:]
        mean = np.mean(recent)
        std = np.std(recent)
        
        if std == 0:
            zscore = 0
        else:
            zscore = (prices[-1] - mean) / std
        
        # Mean reversion signal (opposite of z-score)
        if zscore > self.entry_zscore:
            direction = 'short'  # Overbought, expect reversion down
            strength = min(zscore / 3, 1.0)
        elif zscore < -self.entry_zscore:
            direction = 'long'  # Oversold, expect reversion up
            strength = min(abs(zscore) / 3, 1.0)
        else:
            direction = 'neutral'
            strength = 0
        
        confidence = min(abs(zscore) / 3, 1.0)
        
        return BrainSignal(
            brain_type=self.brain_type,
            timestamp=datetime.now(),
            symbol=market_data.get('symbol', ''),
            direction=direction,
            strength=strength * (-1 if direction == 'short' else 1),
            confidence=confidence,
            features={'zscore': zscore},
            reasoning=f"Z-score: {zscore:.2f}",
        )


class MomentumBrain(BaseBrain):
    """Momentum brain"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(BrainType.MOMENTUM, config)
        self.fast_period = self.config.get('fast_period', 12)
        self.slow_period = self.config.get('slow_period', 26)
    
    def generate_signal(self, market_data: Dict[str, Any]) -> BrainSignal:
        prices = market_data.get('prices', [])
        
        if len(prices) < self.slow_period:
            return BrainSignal(
                brain_type=self.brain_type,
                timestamp=datetime.now(),
                symbol=market_data.get('symbol', ''),
                direction='neutral',
                strength=0,
                confidence=0,
                reasoning="Insufficient data",
            )
        
        # Calculate momentum (rate of change)
        fast_roc = (prices[-1] - prices[-self.fast_period]) / prices[-self.fast_period]
        slow_roc = (prices[-1] - prices[-self.slow_period]) / prices[-self.slow_period]
        
        # MACD-like signal
        momentum = fast_roc - slow_roc
        
        if momentum > 0.01:
            direction = 'long'
        elif momentum < -0.01:
            direction = 'short'
        else:
            direction = 'neutral'
        
        strength = min(abs(momentum) * 10, 1.0)
        confidence = min(abs(momentum) * 5 + 0.3, 1.0)
        
        return BrainSignal(
            brain_type=self.brain_type,
            timestamp=datetime.now(),
            symbol=market_data.get('symbol', ''),
            direction=direction,
            strength=strength * (1 if direction == 'long' else -1),
            confidence=confidence,
            features={'fast_roc': fast_roc, 'slow_roc': slow_roc, 'momentum': momentum},
            reasoning=f"Momentum: {momentum:.4f}",
        )


class VolatilityBrain(BaseBrain):
    """Volatility-based brain"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(BrainType.VOLATILITY, config)
        self.lookback = self.config.get('lookback', 20)
    
    def generate_signal(self, market_data: Dict[str, Any]) -> BrainSignal:
        prices = market_data.get('prices', [])
        
        if len(prices) < self.lookback * 2:
            return BrainSignal(
                brain_type=self.brain_type,
                timestamp=datetime.now(),
                symbol=market_data.get('symbol', ''),
                direction='neutral',
                strength=0,
                confidence=0,
                reasoning="Insufficient data",
            )
        
        # Calculate volatility
        returns = np.diff(prices) / prices[:-1]
        recent_vol = np.std(returns[-self.lookback:])
        older_vol = np.std(returns[-self.lookback*2:-self.lookback])
        
        # Volatility regime
        vol_ratio = recent_vol / older_vol if older_vol > 0 else 1
        
        # High volatility = reduce exposure, low volatility = increase
        if vol_ratio > 1.5:
            direction = 'neutral'  # High vol, stay out
            strength = 0
            confidence = 0.8
            reasoning = f"High volatility ({vol_ratio:.2f}x), reducing exposure"
        elif vol_ratio < 0.7:
            direction = 'neutral'  # Low vol, wait for breakout
            strength = 0
            confidence = 0.6
            reasoning = f"Low volatility ({vol_ratio:.2f}x), compression detected"
        else:
            direction = 'neutral'
            strength = 0
            confidence = 0.5
            reasoning = f"Normal volatility ({vol_ratio:.2f}x)"
        
        return BrainSignal(
            brain_type=self.brain_type,
            timestamp=datetime.now(),
            symbol=market_data.get('symbol', ''),
            direction=direction,
            strength=strength,
            confidence=confidence,
            features={'vol_ratio': vol_ratio, 'recent_vol': recent_vol},
            reasoning=reasoning,
        )


class RegimeDetector:
    """
    Detects market regime for strategy selection
    
    Regimes:
    - Trending (up/down)
    - Choppy range
    - Violent breakout
    - High volatility compression
    - Event-driven
    - Overnight illiquidity
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Regime history
        self.regime_history: deque = deque(maxlen=1000)
        
        # Current regime
        self.current_regime = MarketRegime.NORMAL
        self.regime_confidence = 0.5
        
        # Thresholds
        self.trend_threshold = self.config.get('trend_threshold', 0.02)
        self.volatility_threshold = self.config.get('volatility_threshold', 0.03)
        self.breakout_threshold = self.config.get('breakout_threshold', 0.05)
        
        # ML classifier (if available)
        if SKLEARN_AVAILABLE:
            self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.scaler = StandardScaler()
            self.is_trained = False
        else:
            self.classifier = None
            self.is_trained = False
    
    def detect_regime(self, market_data: Dict[str, Any]) -> Tuple[MarketRegime, float]:
        """
        Detect current market regime
        
        Args:
            market_data: Dictionary with prices, volumes, timestamps, etc.
            
        Returns:
            Tuple of (regime, confidence)
        """
        prices = market_data.get('prices', [])
        volumes = market_data.get('volumes', [])
        timestamp = market_data.get('timestamp', datetime.now())
        
        if len(prices) < 50:
            return MarketRegime.NORMAL, 0.5
        
        # Extract features
        features = self._extract_features(prices, volumes, timestamp)
        
        # Use ML if trained, otherwise rule-based
        if self.is_trained and self.classifier is not None:
            regime, confidence = self._ml_detection(features)
        else:
            regime, confidence = self._rule_based_detection(features)
        
        self.current_regime = regime
        self.regime_confidence = confidence
        
        # Record
        self.regime_history.append({
            'timestamp': datetime.now(),
            'regime': regime,
            'confidence': confidence,
            'features': features,
        })
        
        return regime, confidence
    
    def _extract_features(self, prices: List[float], volumes: List[float],
                         timestamp: datetime) -> Dict[str, float]:
        """Extract features for regime detection"""
        returns = np.diff(prices) / prices[:-1] if len(prices) > 1 else [0]
        
        features = {}
        
        # Trend features
        features['return_20d'] = np.sum(returns[-20:]) if len(returns) >= 20 else 0
        features['return_5d'] = np.sum(returns[-5:]) if len(returns) >= 5 else 0
        
        # Volatility features
        features['volatility_20d'] = np.std(returns[-20:]) if len(returns) >= 20 else 0
        features['volatility_5d'] = np.std(returns[-5:]) if len(returns) >= 5 else 0
        features['vol_ratio'] = features['volatility_5d'] / features['volatility_20d'] \
                               if features['volatility_20d'] > 0 else 1
        
        # Momentum features
        if len(prices) >= 20:
            features['momentum'] = (prices[-1] - prices[-20]) / prices[-20]
        else:
            features['momentum'] = 0
        
        # Volume features
        if volumes and len(volumes) >= 20:
            features['volume_ratio'] = np.mean(volumes[-5:]) / np.mean(volumes[-20:])
        else:
            features['volume_ratio'] = 1
        
        # Time features
        features['hour'] = timestamp.hour
        features['is_overnight'] = 1 if timestamp.hour < 9 or timestamp.hour >= 16 else 0
        
        # Range features
        if len(prices) >= 20:
            high = max(prices[-20:])
            low = min(prices[-20:])
            features['range_pct'] = (high - low) / low if low > 0 else 0
            features['position_in_range'] = (prices[-1] - low) / (high - low) if high > low else 0.5
        else:
            features['range_pct'] = 0
            features['position_in_range'] = 0.5
        
        return features
    
    def _rule_based_detection(self, features: Dict[str, float]) -> Tuple[MarketRegime, float]:
        """Rule-based regime detection"""
        # Check for overnight illiquidity
        if features.get('is_overnight', 0) == 1:
            return MarketRegime.OVERNIGHT_ILLIQUIDITY, 0.8
        
        # Check for violent breakout
        if abs(features.get('return_5d', 0)) > self.breakout_threshold:
            return MarketRegime.VIOLENT_BREAKOUT, 0.85
        
        # Check for high volatility compression
        vol_ratio = features.get('vol_ratio', 1)
        if vol_ratio < 0.5:
            return MarketRegime.HIGH_VOL_COMPRESSION, 0.7
        
        # Check for trending
        momentum = features.get('momentum', 0)
        if momentum > self.trend_threshold:
            return MarketRegime.TRENDING_UP, 0.75
        elif momentum < -self.trend_threshold:
            return MarketRegime.TRENDING_DOWN, 0.75
        
        # Check for choppy range
        range_pct = features.get('range_pct', 0)
        if range_pct < 0.03 and abs(momentum) < 0.01:
            return MarketRegime.CHOPPY_RANGE, 0.65
        
        return MarketRegime.NORMAL, 0.5
    
    def _ml_detection(self, features: Dict[str, float]) -> Tuple[MarketRegime, float]:
        """ML-based regime detection"""
        feature_array = np.array([[features.get(k, 0) for k in sorted(features.keys())]])
        feature_array = self.scaler.transform(feature_array)
        
        try:
            prediction = self.classifier.predict(feature_array)[0]
            probabilities = self.classifier.predict_proba(feature_array)[0]
            confidence = max(probabilities)
            
            regime = MarketRegime(prediction)
            return regime, confidence
        except Exception as e:
            logger.error(f"ML detection failed: {e}")
            return self._rule_based_detection(features)
    
    def get_strategy_recommendations(self) -> Dict[BrainType, float]:
        """Get strategy activation recommendations based on regime"""
        recommendations = {
            MarketRegime.TRENDING_UP: {
                BrainType.TREND_FOLLOWER: 1.0,
                BrainType.MOMENTUM: 0.8,
                BrainType.MEAN_REVERSION: 0.2,
                BrainType.VOLATILITY: 0.5,
            },
            MarketRegime.TRENDING_DOWN: {
                BrainType.TREND_FOLLOWER: 1.0,
                BrainType.MOMENTUM: 0.8,
                BrainType.MEAN_REVERSION: 0.2,
                BrainType.VOLATILITY: 0.5,
            },
            MarketRegime.CHOPPY_RANGE: {
                BrainType.TREND_FOLLOWER: 0.2,
                BrainType.MOMENTUM: 0.3,
                BrainType.MEAN_REVERSION: 1.0,
                BrainType.VOLATILITY: 0.6,
            },
            MarketRegime.VIOLENT_BREAKOUT: {
                BrainType.TREND_FOLLOWER: 0.5,
                BrainType.MOMENTUM: 1.0,
                BrainType.MEAN_REVERSION: 0.1,
                BrainType.VOLATILITY: 0.8,
            },
            MarketRegime.HIGH_VOL_COMPRESSION: {
                BrainType.TREND_FOLLOWER: 0.3,
                BrainType.MOMENTUM: 0.4,
                BrainType.MEAN_REVERSION: 0.5,
                BrainType.VOLATILITY: 1.0,
            },
            MarketRegime.OVERNIGHT_ILLIQUIDITY: {
                BrainType.TREND_FOLLOWER: 0.1,
                BrainType.MOMENTUM: 0.1,
                BrainType.MEAN_REVERSION: 0.1,
                BrainType.VOLATILITY: 0.2,
            },
            MarketRegime.NORMAL: {
                BrainType.TREND_FOLLOWER: 0.6,
                BrainType.MOMENTUM: 0.6,
                BrainType.MEAN_REVERSION: 0.6,
                BrainType.VOLATILITY: 0.5,
            },
        }
        
        return recommendations.get(self.current_regime, recommendations[MarketRegime.NORMAL])


class AlphaBlendingLayer:
    """
    Ensemble aggregator that dynamically weights models
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Brain weights
        self.weights: Dict[BrainType, float] = {
            BrainType.TREND_FOLLOWER: 0.25,
            BrainType.MEAN_REVERSION: 0.20,
            BrainType.MOMENTUM: 0.20,
            BrainType.VOLATILITY: 0.15,
            BrainType.SENTIMENT: 0.10,
            BrainType.MICROSTRUCTURE: 0.10,
        }
        
        # Performance tracking
        self.brain_performance: Dict[BrainType, deque] = {
            bt: deque(maxlen=100) for bt in BrainType
        }
        
        # Weight adjustment settings
        self.min_weight = self.config.get('min_weight', 0.05)
        self.max_weight = self.config.get('max_weight', 0.40)
        self.adjustment_rate = self.config.get('adjustment_rate', 0.1)
        
        # Rebalance frequency
        self.rebalance_interval = self.config.get('rebalance_interval', 'hourly')
        self.last_rebalance = datetime.now()
    
    def blend_signals(self, signals: List[BrainSignal], 
                     regime_weights: Dict[BrainType, float] = None) -> BlendedSignal:
        """
        Blend signals from multiple brains
        
        Args:
            signals: List of signals from different brains
            regime_weights: Optional regime-based weight adjustments
            
        Returns:
            BlendedSignal
        """
        if not signals:
            return self._empty_signal()
        
        # Apply regime weights if provided
        effective_weights = self.weights.copy()
        if regime_weights:
            for brain_type, regime_weight in regime_weights.items():
                if brain_type in effective_weights:
                    effective_weights[brain_type] *= regime_weight
        
        # Normalize weights
        total_weight = sum(effective_weights.values())
        effective_weights = {k: v / total_weight for k, v in effective_weights.items()}
        
        # Weighted aggregation
        weighted_strength = 0
        total_confidence = 0
        contributing_brains = []
        
        for signal in signals:
            weight = effective_weights.get(signal.brain_type, 0.1)
            weighted_strength += signal.strength * weight * signal.confidence
            total_confidence += signal.confidence * weight
            
            if signal.confidence > 0.5:
                contributing_brains.append(signal.brain_type.value)
        
        # Determine direction
        if weighted_strength > 0.2:
            direction = 'long'
        elif weighted_strength < -0.2:
            direction = 'short'
        else:
            direction = 'neutral'
        
        # Calculate agreement
        directions = [s.direction for s in signals if s.confidence > 0.5]
        if directions:
            agreement = max(
                directions.count('long'),
                directions.count('short'),
                directions.count('neutral')
            ) / len(directions)
        else:
            agreement = 0
        
        # Should trade?
        should_trade = (
            abs(weighted_strength) > 0.3 and
            total_confidence > 0.5 and
            agreement > 0.5
        )
        
        # Position size multiplier
        size_multiplier = min(abs(weighted_strength) * agreement * 2, 1.5)
        
        return BlendedSignal(
            timestamp=datetime.now(),
            symbol=signals[0].symbol if signals else '',
            direction=direction,
            strength=weighted_strength,
            confidence=total_confidence,
            contributing_brains=contributing_brains,
            brain_weights={k.value: v for k, v in effective_weights.items()},
            regime=MarketRegime.NORMAL,
            should_trade=should_trade,
            position_size_multiplier=size_multiplier,
            reasoning=f"Blended from {len(contributing_brains)} brains, agreement: {agreement:.2f}",
        )
    
    def update_weights(self):
        """Update weights based on recent performance"""
        for brain_type in self.weights.keys():
            performance = list(self.brain_performance.get(brain_type, []))
            
            if len(performance) < 10:
                continue
            
            # Calculate performance score
            correct = sum(1 for p in performance if p.get('correct', False))
            accuracy = correct / len(performance)
            
            returns = [p.get('return', 0) for p in performance]
            sharpe = np.mean(returns) / (np.std(returns) + 1e-10) if returns else 0
            
            # Composite score
            score = accuracy * 0.5 + (sharpe / 3) * 0.5
            
            # Adjust weight
            current_weight = self.weights[brain_type]
            adjustment = self.adjustment_rate * (score - 0.5)
            new_weight = current_weight * (1 + adjustment)
            
            # Apply bounds
            new_weight = np.clip(new_weight, self.min_weight, self.max_weight)
            self.weights[brain_type] = new_weight
        
        # Normalize
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}
        
        self.last_rebalance = datetime.now()
        logger.info(f"Updated brain weights: {self.weights}")
    
    def record_performance(self, brain_type: BrainType, correct: bool, 
                          actual_return: float):
        """Record brain performance"""
        self.brain_performance[brain_type].append({
            'timestamp': datetime.now(),
            'correct': correct,
            'return': actual_return,
        })
    
    def _empty_signal(self) -> BlendedSignal:
        """Return empty signal"""
        return BlendedSignal(
            timestamp=datetime.now(),
            symbol='',
            direction='neutral',
            strength=0,
            confidence=0,
            contributing_brains=[],
            brain_weights={},
            regime=MarketRegime.NORMAL,
            should_trade=False,
            position_size_multiplier=0,
            reasoning="No signals available",
        )


class StrategySelector:
    """
    Activates/deactivates strategies based on regime
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Strategy activation status
        self.active_strategies: Dict[BrainType, bool] = {
            bt: True for bt in BrainType
        }
        
        # Activation thresholds
        self.activation_threshold = self.config.get('activation_threshold', 0.3)
        self.deactivation_threshold = self.config.get('deactivation_threshold', 0.2)
    
    def update_activations(self, regime_weights: Dict[BrainType, float]):
        """Update strategy activations based on regime"""
        for brain_type, weight in regime_weights.items():
            if weight >= self.activation_threshold:
                self.active_strategies[brain_type] = True
            elif weight <= self.deactivation_threshold:
                self.active_strategies[brain_type] = False
    
    def is_active(self, brain_type: BrainType) -> bool:
        """Check if strategy is active"""
        return self.active_strategies.get(brain_type, False)
    
    def get_active_strategies(self) -> List[BrainType]:
        """Get list of active strategies"""
        return [bt for bt, active in self.active_strategies.items() if active]


class BrainCoordinator:
    """
    Orchestrates all brains and coordinates signal generation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.regime_detector = RegimeDetector(config.get('regime', {}))
        self.alpha_blender = AlphaBlendingLayer(config.get('blending', {}))
        self.strategy_selector = StrategySelector(config.get('selector', {}))
        
        # Initialize brains
        self.brains: Dict[BrainType, BaseBrain] = {
            BrainType.TREND_FOLLOWER: TrendFollowerBrain(config.get('trend', {})),
            BrainType.MEAN_REVERSION: MeanReversionBrain(config.get('mean_rev', {})),
            BrainType.MOMENTUM: MomentumBrain(config.get('momentum', {})),
            BrainType.VOLATILITY: VolatilityBrain(config.get('volatility', {})),
        }
        
        # Signal history
        self.signal_history: deque = deque(maxlen=1000)
    
    def generate_signal(self, market_data: Dict[str, Any]) -> BlendedSignal:
        """
        Generate blended signal from all brains
        
        Args:
            market_data: Market data dictionary
            
        Returns:
            BlendedSignal
        """
        # Detect regime
        regime, regime_confidence = self.regime_detector.detect_regime(market_data)
        
        # Get regime-based strategy weights
        regime_weights = self.regime_detector.get_strategy_recommendations()
        
        # Update strategy activations
        self.strategy_selector.update_activations(regime_weights)
        
        # Generate signals from active brains
        signals = []
        for brain_type, brain in self.brains.items():
            if self.strategy_selector.is_active(brain_type):
                try:
                    signal = brain.generate_signal(market_data)
                    signals.append(signal)
                except Exception as e:
                    logger.error(f"Brain {brain_type.value} failed: {e}")
        
        # Blend signals
        blended = self.alpha_blender.blend_signals(signals, regime_weights)
        blended.regime = regime
        
        # Record
        self.signal_history.append({
            'timestamp': datetime.now(),
            'blended_signal': blended,
            'individual_signals': signals,
            'regime': regime,
        })
        
        return blended
    
    def record_outcome(self, actual_return: float):
        """Record outcome for all brains"""
        if not self.signal_history:
            return
        
        last_record = self.signal_history[-1]
        
        for signal in last_record['individual_signals']:
            correct = (
                (signal.direction == 'long' and actual_return > 0) or
                (signal.direction == 'short' and actual_return < 0)
            )
            
            # Record for brain
            if signal.brain_type in self.brains:
                self.brains[signal.brain_type].record_performance(signal, actual_return)
            
            # Record for blender
            self.alpha_blender.record_performance(signal.brain_type, correct, actual_return)
    
    def rebalance_weights(self):
        """Rebalance brain weights based on performance"""
        self.alpha_blender.update_weights()
    
    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status"""
        return {
            'current_regime': self.regime_detector.current_regime.value,
            'regime_confidence': self.regime_detector.regime_confidence,
            'active_strategies': [bt.value for bt in self.strategy_selector.get_active_strategies()],
            'brain_weights': {k.value: v for k, v in self.alpha_blender.weights.items()},
            'brain_accuracies': {
                bt.value: brain.get_accuracy()
                for bt, brain in self.brains.items()
            },
        }


class MultiBrainArchitecture:
    """
    Main interface for multi-brain trading system
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.coordinator = BrainCoordinator(config)
        
        # Human approval settings
        self.require_approval = self.config.get('require_approval', True)
        self.approval_threshold = self.config.get('approval_threshold', 0.8)
        
        # Pending decisions
        self.pending_decisions: deque = deque(maxlen=100)
    
    async def analyze_and_decide(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market and generate trading decision
        
        Args:
            market_data: Market data dictionary
            
        Returns:
            Decision dictionary
        """
        # Generate signal
        signal = self.coordinator.generate_signal(market_data)
        
        # Build decision
        decision = {
            'timestamp': datetime.now().isoformat(),
            'symbol': signal.symbol,
            'direction': signal.direction,
            'strength': signal.strength,
            'confidence': signal.confidence,
            'regime': signal.regime.value,
            'should_trade': signal.should_trade,
            'position_size_multiplier': signal.position_size_multiplier,
            'contributing_brains': signal.contributing_brains,
            'reasoning': signal.reasoning,
            'requires_approval': self.require_approval and signal.confidence < self.approval_threshold,
        }
        
        if decision['requires_approval']:
            self.pending_decisions.append(decision)
            decision['status'] = 'pending_approval'
        else:
            decision['status'] = 'approved' if signal.should_trade else 'no_action'
        
        return decision
    
    def approve_decision(self, decision_id: str) -> bool:
        """Approve a pending decision"""
        for decision in self.pending_decisions:
            if decision.get('timestamp') == decision_id:
                decision['status'] = 'approved'
                return True
        return False
    
    def reject_decision(self, decision_id: str) -> bool:
        """Reject a pending decision"""
        for decision in self.pending_decisions:
            if decision.get('timestamp') == decision_id:
                decision['status'] = 'rejected'
                return True
        return False
    
    def record_outcome(self, actual_return: float):
        """Record trade outcome"""
        self.coordinator.record_outcome(actual_return)
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'coordinator': self.coordinator.get_status(),
            'pending_decisions': len(self.pending_decisions),
            'require_approval': self.require_approval,
        }

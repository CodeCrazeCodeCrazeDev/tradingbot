"""
Hypernetwork-Based Adaptation

Instead of retraining the entire model for new market regimes, uses a smaller
"Hypernetwork" to generate slight adjustments to the main network's weights.

This allows the bot to adapt its personality (e.g., from "trend-following" to
"mean-reverting") much faster and with less data than full retraining.

Features:
- Rapid regime adaptation
- Weight modulation without full retraining
- Strategy personality switching
- Online learning capability
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class TradingPersonality(Enum):
    """Trading strategy personalities"""
    TREND_FOLLOWER = "trend_follower"
    MEAN_REVERTER = "mean_reverter"
    MOMENTUM = "momentum"
    BREAKOUT = "breakout"
    SCALPER = "scalper"
    SWING = "swing"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


class MarketRegime(Enum):
    """Market regime types"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    CONSOLIDATION = "consolidation"


@dataclass
class WeightModulation:
    """Weight adjustment from hypernetwork"""
    layer_name: str
    original_weights: np.ndarray
    modulation: np.ndarray
    modulated_weights: np.ndarray
    modulation_strength: float
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'layer_name': self.layer_name,
            'modulation_strength': self.modulation_strength,
            'weight_change_norm': float(np.linalg.norm(self.modulation))
        }


@dataclass
class AdaptationResult:
    """Result of hypernetwork adaptation"""
    timestamp: datetime
    source_personality: TradingPersonality
    target_personality: TradingPersonality
    regime: MarketRegime
    modulations: List[WeightModulation]
    adaptation_confidence: float
    estimated_performance_change: float
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'source_personality': self.source_personality.value,
            'target_personality': self.target_personality.value,
            'regime': self.regime.value,
            'num_modulations': len(self.modulations),
            'adaptation_confidence': self.adaptation_confidence,
            'estimated_performance_change': self.estimated_performance_change
        }


class SimpleNeuralNetwork:
    """
    Simple neural network for demonstration
    
    In production, this would be replaced with PyTorch/TensorFlow model
    """
    
    def __init__(self, layer_sizes: List[int]):
        try:
            self.layer_sizes = layer_sizes
            self.weights: Dict[str, np.ndarray] = {}
            self.biases: Dict[str, np.ndarray] = {}
        
            # Initialize weights
            for i in range(len(layer_sizes) - 1):
                self.weights[f'layer_{i}'] = np.random.randn(
                    layer_sizes[i], layer_sizes[i+1]
                ) * 0.1
                self.biases[f'layer_{i}'] = np.zeros(layer_sizes[i+1])
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass"""
        try:
            for i in range(len(self.layer_sizes) - 1):
                x = x @ self.weights[f'layer_{i}'] + self.biases[f'layer_{i}']
                if i < len(self.layer_sizes) - 2:
                    x = np.maximum(0, x)  # ReLU
            return x
        except Exception as e:
            logger.error(f"Error in forward: {e}")
            raise
    
    def get_weights(self) -> Dict[str, np.ndarray]:
        """Get all weights"""
        return {**self.weights, **self.biases}
    
    def set_weights(self, weights: Dict[str, np.ndarray]):
        """Set weights"""
        try:
            for key, value in weights.items():
                if key in self.weights:
                    self.weights[key] = value
                elif key in self.biases:
                    self.biases[key] = value
        except Exception as e:
            logger.error(f"Error in set_weights: {e}")
            raise


class Hypernetwork:
    """
    Hypernetwork for generating weight modulations
    
    Takes regime/context as input and outputs weight adjustments
    for the main trading network.
    """
    
    def __init__(
        self,
        context_dim: int,
        target_weight_shapes: Dict[str, Tuple[int, ...]],
        hidden_dim: int = 64
    ):
        try:
            self.context_dim = context_dim
            self.target_weight_shapes = target_weight_shapes
            self.hidden_dim = hidden_dim
        
            # Hypernetwork weights (small network that generates big network weights)
            self.hyper_weights: Dict[str, Dict[str, np.ndarray]] = {}
        
            for layer_name, shape in target_weight_shapes.items():
                output_dim = np.prod(shape)
                self.hyper_weights[layer_name] = {
                    'w1': np.random.randn(context_dim, hidden_dim) * 0.1,
                    'b1': np.zeros(hidden_dim),
                    'w2': np.random.randn(hidden_dim, output_dim) * 0.01,
                    'b2': np.zeros(output_dim)
                }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def generate_modulation(
        self,
        context: np.ndarray,
        layer_name: str,
        modulation_strength: float = 0.1
    ) -> np.ndarray:
        """
        Generate weight modulation for a specific layer
        
        Args:
            context: Context vector (regime, volatility, etc.)
            layer_name: Name of layer to modulate
            modulation_strength: How much to modulate (0-1)
        """
        try:
            if layer_name not in self.hyper_weights:
                raise ValueError(f"Unknown layer: {layer_name}")
        
            hw = self.hyper_weights[layer_name]
        
            # Forward through hypernetwork
            h = context @ hw['w1'] + hw['b1']
            h = np.tanh(h)  # Activation
            output = h @ hw['w2'] + hw['b2']
        
            # Reshape to target shape
            target_shape = self.target_weight_shapes[layer_name]
            modulation = output.reshape(target_shape)
        
            # Scale by modulation strength
            modulation = modulation * modulation_strength
        
            return modulation
        except Exception as e:
            logger.error(f"Error in generate_modulation: {e}")
            raise
    
    def generate_all_modulations(
        self,
        context: np.ndarray,
        modulation_strength: float = 0.1
    ) -> Dict[str, np.ndarray]:
        """Generate modulations for all layers"""
        try:
            modulations = {}
            for layer_name in self.target_weight_shapes:
                modulations[layer_name] = self.generate_modulation(
                    context, layer_name, modulation_strength
                )
            return modulations
        except Exception as e:
            logger.error(f"Error in generate_all_modulations: {e}")
            raise


class HypernetworkAdapter:
    """
    Hypernetwork-Based Adaptation System
    
    Enables rapid adaptation of trading strategy to new market regimes
    without full model retraining.
    """
    
    # Personality embeddings (learned representations)
    PERSONALITY_EMBEDDINGS = {
        TradingPersonality.TREND_FOLLOWER: np.array([1, 0, 0, 0, 0.5, 0.3]),
        TradingPersonality.MEAN_REVERTER: np.array([0, 1, 0, 0, 0.3, 0.5]),
        TradingPersonality.MOMENTUM: np.array([0.8, 0, 0.5, 0, 0.7, 0.2]),
        TradingPersonality.BREAKOUT: np.array([0.5, 0, 0, 1, 0.8, 0.4]),
        TradingPersonality.SCALPER: np.array([0.3, 0.3, 0.8, 0, 0.2, 0.9]),
        TradingPersonality.SWING: np.array([0.6, 0.4, 0, 0, 0.4, 0.3]),
        TradingPersonality.CONSERVATIVE: np.array([0.3, 0.5, 0, 0, 0.2, 0.2]),
        TradingPersonality.AGGRESSIVE: np.array([0.7, 0.2, 0.6, 0.5, 0.9, 0.8]),
    }
    
    # Regime embeddings
    REGIME_EMBEDDINGS = {
        MarketRegime.TRENDING_UP: np.array([1, 0, 0.7, 0.3]),
        MarketRegime.TRENDING_DOWN: np.array([1, 0, 0.3, 0.7]),
        MarketRegime.RANGING: np.array([0, 1, 0.5, 0.5]),
        MarketRegime.HIGH_VOLATILITY: np.array([0.5, 0.5, 0.9, 0.5]),
        MarketRegime.LOW_VOLATILITY: np.array([0.5, 0.5, 0.1, 0.5]),
        MarketRegime.BREAKOUT: np.array([0.7, 0.3, 0.8, 0.5]),
        MarketRegime.CONSOLIDATION: np.array([0.2, 0.8, 0.3, 0.5]),
    }
    
    # Optimal personality for each regime
    REGIME_PERSONALITY_MAP = {
        MarketRegime.TRENDING_UP: TradingPersonality.TREND_FOLLOWER,
        MarketRegime.TRENDING_DOWN: TradingPersonality.TREND_FOLLOWER,
        MarketRegime.RANGING: TradingPersonality.MEAN_REVERTER,
        MarketRegime.HIGH_VOLATILITY: TradingPersonality.CONSERVATIVE,
        MarketRegime.LOW_VOLATILITY: TradingPersonality.SCALPER,
        MarketRegime.BREAKOUT: TradingPersonality.BREAKOUT,
        MarketRegime.CONSOLIDATION: TradingPersonality.MEAN_REVERTER,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Main trading network
            self.main_network = SimpleNeuralNetwork([10, 32, 16, 3])
        
            # Get weight shapes for hypernetwork
            weight_shapes = {}
            for name, weights in self.main_network.get_weights().items():
                weight_shapes[name] = weights.shape
        
            # Context dimension = personality embedding + regime embedding
            context_dim = 6 + 4  # 6 for personality, 4 for regime
        
            # Hypernetwork
            self.hypernetwork = Hypernetwork(context_dim, weight_shapes)
        
            # Current state
            self.current_personality = TradingPersonality.TREND_FOLLOWER
            self.current_regime = MarketRegime.RANGING
        
            # Original weights (for reverting)
            self.original_weights = {k: v.copy() for k, v in self.main_network.get_weights().items()}
        
            # Adaptation history
            self.adaptation_history: deque = deque(maxlen=100)
        
            logger.info("HypernetworkAdapter initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_regime(self, market_data: Dict[str, Any]) -> MarketRegime:
        """Detect current market regime from data"""
        try:
            prices = market_data.get('prices', np.array([]))
            volatility = market_data.get('volatility', 0)
            trend_strength = market_data.get('trend_strength', 0)
        
            if len(prices) < 20:
                return MarketRegime.RANGING
        
            # Calculate metrics
            returns = np.diff(prices) / prices[:-1]
            vol = np.std(returns) * np.sqrt(252)  # Annualized
        
            # Trend detection
            sma20 = np.mean(prices[-20:])
            sma50 = np.mean(prices[-50:]) if len(prices) >= 50 else sma20
        
            price_above_sma = prices[-1] > sma20
            sma_aligned = sma20 > sma50
        
            # Regime classification
            if vol > 0.3:  # High volatility threshold
                return MarketRegime.HIGH_VOLATILITY
            elif vol < 0.1:  # Low volatility threshold
                return MarketRegime.LOW_VOLATILITY
            elif price_above_sma and sma_aligned:
                return MarketRegime.TRENDING_UP
            elif not price_above_sma and not sma_aligned:
                return MarketRegime.TRENDING_DOWN
            elif abs(trend_strength) < 0.2:
                return MarketRegime.CONSOLIDATION
            else:
                return MarketRegime.RANGING
        except Exception as e:
            logger.error(f"Error in detect_regime: {e}")
            raise
    
    def get_optimal_personality(self, regime: MarketRegime) -> TradingPersonality:
        """Get optimal trading personality for regime"""
        return self.REGIME_PERSONALITY_MAP.get(regime, TradingPersonality.CONSERVATIVE)
    
    def adapt_to_regime(
        self,
        regime: MarketRegime,
        modulation_strength: float = 0.1
    ) -> AdaptationResult:
        """
        Adapt the trading network to a new market regime
        
        Uses hypernetwork to generate weight modulations
        """
        # Get optimal personality for regime
        try:
            target_personality = self.get_optimal_personality(regime)
        
            # Build context vector
            personality_emb = self.PERSONALITY_EMBEDDINGS[target_personality]
            regime_emb = self.REGIME_EMBEDDINGS[regime]
            context = np.concatenate([personality_emb, regime_emb])
        
            # Generate modulations
            modulations_dict = self.hypernetwork.generate_all_modulations(
                context, modulation_strength
            )
        
            # Apply modulations
            modulation_results = []
            new_weights = {}
        
            for layer_name, modulation in modulations_dict.items():
                original = self.original_weights[layer_name]
                modulated = original + modulation
                new_weights[layer_name] = modulated
            
                modulation_results.append(WeightModulation(
                    layer_name=layer_name,
                    original_weights=original,
                    modulation=modulation,
                    modulated_weights=modulated,
                    modulation_strength=modulation_strength
                ))
        
            # Update main network
            self.main_network.set_weights(new_weights)
        
            # Update state
            source_personality = self.current_personality
            self.current_personality = target_personality
            self.current_regime = regime
        
            # Estimate performance change (simplified)
            personality_match = 1.0 if target_personality == self.get_optimal_personality(regime) else 0.5
            estimated_change = (personality_match - 0.5) * modulation_strength
        
            result = AdaptationResult(
                timestamp=datetime.now(),
                source_personality=source_personality,
                target_personality=target_personality,
                regime=regime,
                modulations=modulation_results,
                adaptation_confidence=personality_match,
                estimated_performance_change=estimated_change
            )
        
            self.adaptation_history.append(result)
        
            logger.info(
                f"Adapted from {source_personality.value} to {target_personality.value} "
                f"for {regime.value} regime"
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in adapt_to_regime: {e}")
            raise
    
    def adapt_to_market(
        self,
        market_data: Dict[str, Any],
        modulation_strength: float = 0.1
    ) -> AdaptationResult:
        """
        Automatically detect regime and adapt
        """
        try:
            regime = self.detect_regime(market_data)
        
            # Only adapt if regime changed
            if regime != self.current_regime:
                return self.adapt_to_regime(regime, modulation_strength)
        
            # Return current state if no change needed
            return AdaptationResult(
                timestamp=datetime.now(),
                source_personality=self.current_personality,
                target_personality=self.current_personality,
                regime=regime,
                modulations=[],
                adaptation_confidence=1.0,
                estimated_performance_change=0.0
            )
        except Exception as e:
            logger.error(f"Error in adapt_to_market: {e}")
            raise
    
    def force_personality(
        self,
        personality: TradingPersonality,
        modulation_strength: float = 0.1
    ) -> AdaptationResult:
        """Force a specific trading personality"""
        # Build context with forced personality
        try:
            personality_emb = self.PERSONALITY_EMBEDDINGS[personality]
            regime_emb = self.REGIME_EMBEDDINGS[self.current_regime]
            context = np.concatenate([personality_emb, regime_emb])
        
            # Generate and apply modulations
            modulations_dict = self.hypernetwork.generate_all_modulations(
                context, modulation_strength
            )
        
            modulation_results = []
            new_weights = {}
        
            for layer_name, modulation in modulations_dict.items():
                original = self.original_weights[layer_name]
                modulated = original + modulation
                new_weights[layer_name] = modulated
            
                modulation_results.append(WeightModulation(
                    layer_name=layer_name,
                    original_weights=original,
                    modulation=modulation,
                    modulated_weights=modulated,
                    modulation_strength=modulation_strength
                ))
        
            self.main_network.set_weights(new_weights)
        
            source = self.current_personality
            self.current_personality = personality
        
            return AdaptationResult(
                timestamp=datetime.now(),
                source_personality=source,
                target_personality=personality,
                regime=self.current_regime,
                modulations=modulation_results,
                adaptation_confidence=0.8,
                estimated_performance_change=0.0
            )
        except Exception as e:
            logger.error(f"Error in force_personality: {e}")
            raise
    
    def reset_to_original(self):
        """Reset network to original weights"""
        try:
            self.main_network.set_weights(
                {k: v.copy() for k, v in self.original_weights.items()}
            )
            self.current_personality = TradingPersonality.TREND_FOLLOWER
            logger.info("Reset to original weights")
        except Exception as e:
            logger.error(f"Error in reset_to_original: {e}")
            raise
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current adapter state"""
        return {
            'current_personality': self.current_personality.value,
            'current_regime': self.current_regime.value,
            'adaptations_count': len(self.adaptation_history),
            'last_adaptation': self.adaptation_history[-1].to_dict() if self.adaptation_history else None
        }
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Make prediction using adapted network"""
        return self.main_network.forward(features)


# Factory function
def create_hypernetwork_adapter(config: Optional[Dict[str, Any]] = None) -> HypernetworkAdapter:
    """Create hypernetwork adapter"""
    return HypernetworkAdapter(config)

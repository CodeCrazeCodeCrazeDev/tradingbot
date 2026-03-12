"""
Hypernetwork-Based Adaptation

Instead of retraining the entire model for new market regimes, uses a smaller
"Hypernetwork" to generate slight adjustments to the main network's weights.

This allows the bot to adapt its personality (e.g., from "trend-following" to
"mean-reverting") much faster and with less data than full retraining.

Features:
- Dynamic weight generation
- Regime-specific adaptation
- Fast personality switching
- Minimal data requirements
- Continuous adaptation
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics
import math

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class TradingPersonality(Enum):
    """Trading personalities/styles."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    BREAKOUT = "breakout"
    RANGE_TRADING = "range_trading"
    SCALPING = "scalping"
    SWING = "swing"


class MarketRegime(Enum):
    """Market regime types."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    QUIET = "quiet"
    TRANSITIONING = "transitioning"


@dataclass
class RegimeContext:
    """Context for regime detection."""
    prices: List[float]
    volumes: List[float]
    volatility: float
    trend_strength: float  # -1 to +1
    range_bound: bool
    momentum: float
    
    @property
    def regime(self) -> MarketRegime:
        """Detect current regime."""
        if self.volatility > 0.03:
            return MarketRegime.VOLATILE
        elif self.volatility < 0.005:
            return MarketRegime.QUIET
        elif abs(self.trend_strength) > 0.6:
            if self.trend_strength > 0:
                return MarketRegime.TRENDING_UP
            else:
                return MarketRegime.TRENDING_DOWN
        elif self.range_bound:
            return MarketRegime.RANGING
        else:
            return MarketRegime.TRANSITIONING


@dataclass
class WeightAdjustment:
    """Weight adjustment from hypernetwork."""
    layer_name: str
    adjustment_vector: List[float]
    magnitude: float
    personality: TradingPersonality
    regime: MarketRegime
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'layer_name': self.layer_name,
            'magnitude': self.magnitude,
            'personality': self.personality.value,
            'regime': self.regime.value,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class AdaptationResult:
    """Result of adaptation."""
    success: bool
    old_personality: TradingPersonality
    new_personality: TradingPersonality
    regime: MarketRegime
    adjustments: List[WeightAdjustment]
    adaptation_time_ms: float
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'old_personality': self.old_personality.value,
            'new_personality': self.new_personality.value,
            'regime': self.regime.value,
            'adjustments_count': len(self.adjustments),
            'adaptation_time_ms': self.adaptation_time_ms,
            'confidence': self.confidence
        }


class PersonalityProfile:
    """
    Defines weight adjustments for each personality.
    """
    
    # Personality weight profiles
    PROFILES = {
        TradingPersonality.TREND_FOLLOWING: {
            'trend_weight': 1.5,
            'mean_reversion_weight': 0.3,
            'momentum_weight': 1.2,
            'volatility_sensitivity': 0.8,
            'holding_period_mult': 1.5,
            'stop_loss_mult': 1.2,
            'take_profit_mult': 2.0,
        },
        TradingPersonality.MEAN_REVERSION: {
            'trend_weight': 0.3,
            'mean_reversion_weight': 1.5,
            'momentum_weight': 0.5,
            'volatility_sensitivity': 1.2,
            'holding_period_mult': 0.7,
            'stop_loss_mult': 0.8,
            'take_profit_mult': 1.0,
        },
        TradingPersonality.MOMENTUM: {
            'trend_weight': 1.0,
            'mean_reversion_weight': 0.2,
            'momentum_weight': 1.8,
            'volatility_sensitivity': 1.0,
            'holding_period_mult': 0.5,
            'stop_loss_mult': 1.0,
            'take_profit_mult': 1.5,
        },
        TradingPersonality.BREAKOUT: {
            'trend_weight': 0.8,
            'mean_reversion_weight': 0.2,
            'momentum_weight': 1.5,
            'volatility_sensitivity': 1.5,
            'holding_period_mult': 1.0,
            'stop_loss_mult': 1.5,
            'take_profit_mult': 2.5,
        },
        TradingPersonality.RANGE_TRADING: {
            'trend_weight': 0.2,
            'mean_reversion_weight': 1.8,
            'momentum_weight': 0.3,
            'volatility_sensitivity': 0.5,
            'holding_period_mult': 0.8,
            'stop_loss_mult': 0.7,
            'take_profit_mult': 0.8,
        },
        TradingPersonality.SCALPING: {
            'trend_weight': 0.5,
            'mean_reversion_weight': 1.0,
            'momentum_weight': 1.5,
            'volatility_sensitivity': 1.8,
            'holding_period_mult': 0.2,
            'stop_loss_mult': 0.5,
            'take_profit_mult': 0.5,
        },
        TradingPersonality.SWING: {
            'trend_weight': 1.3,
            'mean_reversion_weight': 0.5,
            'momentum_weight': 1.0,
            'volatility_sensitivity': 0.6,
            'holding_period_mult': 2.0,
            'stop_loss_mult': 1.5,
            'take_profit_mult': 2.5,
        },
    }
    
    @classmethod
    def get_profile(cls, personality: TradingPersonality) -> Dict[str, float]:
        """Get weight profile for personality."""
        return cls.PROFILES.get(personality, cls.PROFILES[TradingPersonality.TREND_FOLLOWING])
    
    @classmethod
    def get_adjustment(
        cls,
        from_personality: TradingPersonality,
        to_personality: TradingPersonality
    ) -> Dict[str, float]:
        """Calculate adjustment from one personality to another."""
        from_profile = cls.get_profile(from_personality)
        to_profile = cls.get_profile(to_personality)
        
        adjustment = {}
        for key in from_profile:
            adjustment[key] = to_profile[key] - from_profile[key]
        
        return adjustment


class RegimePersonalityMapper:
    """
    Maps market regimes to optimal personalities.
    """
    
    REGIME_MAPPING = {
        MarketRegime.TRENDING_UP: [
            (TradingPersonality.TREND_FOLLOWING, 0.4),
            (TradingPersonality.MOMENTUM, 0.3),
            (TradingPersonality.SWING, 0.2),
            (TradingPersonality.BREAKOUT, 0.1),
        ],
        MarketRegime.TRENDING_DOWN: [
            (TradingPersonality.TREND_FOLLOWING, 0.4),
            (TradingPersonality.MOMENTUM, 0.3),
            (TradingPersonality.SWING, 0.2),
            (TradingPersonality.BREAKOUT, 0.1),
        ],
        MarketRegime.RANGING: [
            (TradingPersonality.RANGE_TRADING, 0.5),
            (TradingPersonality.MEAN_REVERSION, 0.3),
            (TradingPersonality.SCALPING, 0.2),
        ],
        MarketRegime.VOLATILE: [
            (TradingPersonality.BREAKOUT, 0.4),
            (TradingPersonality.SCALPING, 0.3),
            (TradingPersonality.MOMENTUM, 0.3),
        ],
        MarketRegime.QUIET: [
            (TradingPersonality.RANGE_TRADING, 0.4),
            (TradingPersonality.MEAN_REVERSION, 0.4),
            (TradingPersonality.SCALPING, 0.2),
        ],
        MarketRegime.TRANSITIONING: [
            (TradingPersonality.SWING, 0.3),
            (TradingPersonality.BREAKOUT, 0.3),
            (TradingPersonality.TREND_FOLLOWING, 0.2),
            (TradingPersonality.MEAN_REVERSION, 0.2),
        ],
    }
    
    @classmethod
    def get_optimal_personality(cls, regime: MarketRegime) -> TradingPersonality:
        """Get optimal personality for regime."""
        mapping = cls.REGIME_MAPPING.get(regime, [(TradingPersonality.TREND_FOLLOWING, 1.0)])
        return mapping[0][0]  # Return highest weighted
    
    @classmethod
    def get_personality_weights(cls, regime: MarketRegime) -> Dict[TradingPersonality, float]:
        """Get all personality weights for regime."""
        mapping = cls.REGIME_MAPPING.get(regime, [(TradingPersonality.TREND_FOLLOWING, 1.0)])
        return {p: w for p, w in mapping}


class HypernetworkCore:
    """
    Core hypernetwork that generates weight adjustments.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Hypernetwork parameters
        self.hidden_size = self.config.get('hidden_size', 64)
        self.adaptation_rate = self.config.get('adaptation_rate', 0.1)
        
        # Layer definitions (simplified)
        self.layers = [
            'input_layer',
            'feature_layer',
            'decision_layer',
            'output_layer'
        ]
        
        # Internal state
        self.current_weights: Dict[str, List[float]] = {}
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize base weights."""
        for layer in self.layers:
            # Initialize with ones (neutral)
            self.current_weights[layer] = [1.0] * self.hidden_size
    
    def generate_adjustment(
        self,
        regime: MarketRegime,
        target_personality: TradingPersonality,
        current_personality: TradingPersonality
    ) -> List[WeightAdjustment]:
        """
        Generate weight adjustments for adaptation.
        
        Args:
            regime: Current market regime
            target_personality: Target personality
            current_personality: Current personality
            
        Returns:
            List of weight adjustments
        """
        adjustments = []
        
        # Get personality adjustment
        profile_adj = PersonalityProfile.get_adjustment(
            current_personality, target_personality
        )
        
        # Generate adjustments for each layer
        for layer in self.layers:
            # Calculate adjustment vector
            adj_vector = self._calculate_layer_adjustment(
                layer, profile_adj, regime
            )
            
            # Calculate magnitude
            magnitude = sum(abs(a) for a in adj_vector) / len(adj_vector)
            
            adjustment = WeightAdjustment(
                layer_name=layer,
                adjustment_vector=adj_vector,
                magnitude=magnitude,
                personality=target_personality,
                regime=regime,
                timestamp=datetime.now()
            )
            
            adjustments.append(adjustment)
        
        return adjustments
    
    def _calculate_layer_adjustment(
        self,
        layer: str,
        profile_adj: Dict[str, float],
        regime: MarketRegime
    ) -> List[float]:
        """Calculate adjustment vector for a layer."""
        # Layer-specific sensitivity
        layer_sensitivity = {
            'input_layer': 0.5,
            'feature_layer': 1.0,
            'decision_layer': 1.5,
            'output_layer': 0.8
        }
        
        sensitivity = layer_sensitivity.get(layer, 1.0)
        
        # Generate adjustment vector
        adj_vector = []
        
        for i in range(self.hidden_size):
            # Base adjustment from profile
            base_adj = sum(profile_adj.values()) / len(profile_adj)
            
            # Add some variation based on position
            position_factor = math.sin(i * 0.1) * 0.1
            
            # Apply sensitivity and adaptation rate
            adj = base_adj * sensitivity * self.adaptation_rate + position_factor
            
            adj_vector.append(adj)
        
        return adj_vector
    
    def apply_adjustments(self, adjustments: List[WeightAdjustment]):
        """Apply adjustments to current weights."""
        for adj in adjustments:
            if adj.layer_name in self.current_weights:
                current = self.current_weights[adj.layer_name]
                
                # Apply adjustment
                new_weights = [
                    c + a for c, a in zip(current, adj.adjustment_vector)
                ]
                
                # Clip to reasonable range
                new_weights = [max(0.1, min(3.0, w)) for w in new_weights]
                
                self.current_weights[adj.layer_name] = new_weights


class HypernetworkAdaptation:
    """
    Main hypernetwork adaptation system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.hypernetwork = HypernetworkCore(config)
        self.regime_mapper = RegimePersonalityMapper()
        
        # State
        self.current_personality = TradingPersonality.TREND_FOLLOWING
        self.current_regime: Optional[MarketRegime] = None
        
        # History
        self.adaptation_history: deque = deque(maxlen=100)
        self.regime_history: deque = deque(maxlen=100)
        
        # Performance tracking
        self.personality_performance: Dict[TradingPersonality, List[float]] = {
            p: [] for p in TradingPersonality
        }
        
        logger.info("HypernetworkAdaptation initialized")
    
    def detect_regime(self, context: RegimeContext) -> MarketRegime:
        """
        Detect current market regime.
        
        Args:
            context: Regime context
            
        Returns:
            Detected regime
        """
        regime = context.regime
        
        self.current_regime = regime
        self.regime_history.append((datetime.now(), regime))
        
        return regime
    
    def should_adapt(self, regime: MarketRegime) -> bool:
        """
        Determine if adaptation is needed.
        
        Args:
            regime: Current regime
            
        Returns:
            True if adaptation recommended
        """
        # Get optimal personality for regime
        optimal = self.regime_mapper.get_optimal_personality(regime)
        
        # Check if different from current
        if optimal != self.current_personality:
            return True
        
        # Check regime stability
        if len(self.regime_history) >= 5:
            recent_regimes = [r for _, r in list(self.regime_history)[-5:]]
            regime_stable = all(r == regime for r in recent_regimes)
            
            if not regime_stable:
                return False  # Wait for stability
        
        return False
    
    def adapt(
        self,
        regime: MarketRegime,
        force: bool = False
    ) -> AdaptationResult:
        """
        Adapt to new regime.
        
        Args:
            regime: Target regime
            force: Force adaptation even if not recommended
            
        Returns:
            AdaptationResult
        """
        start_time = datetime.now()
        
        # Check if adaptation needed
        if not force and not self.should_adapt(regime):
            return AdaptationResult(
                success=False,
                old_personality=self.current_personality,
                new_personality=self.current_personality,
                regime=regime,
                adjustments=[],
                adaptation_time_ms=0,
                confidence=0.5
            )
        
        # Get target personality
        target_personality = self.regime_mapper.get_optimal_personality(regime)
        old_personality = self.current_personality
        
        # Generate adjustments
        adjustments = self.hypernetwork.generate_adjustment(
            regime, target_personality, self.current_personality
        )
        
        # Apply adjustments
        self.hypernetwork.apply_adjustments(adjustments)
        
        # Update state
        self.current_personality = target_personality
        
        # Calculate adaptation time
        adaptation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Calculate confidence
        confidence = self._calculate_confidence(regime, target_personality)
        
        result = AdaptationResult(
            success=True,
            old_personality=old_personality,
            new_personality=target_personality,
            regime=regime,
            adjustments=adjustments,
            adaptation_time_ms=adaptation_time,
            confidence=confidence
        )
        
        self.adaptation_history.append(result)
        
        logger.info(
            f"Adapted from {old_personality.value} to {target_personality.value} "
            f"for {regime.value} regime (confidence: {confidence:.0%})"
        )
        
        return result
    
    def _calculate_confidence(
        self,
        regime: MarketRegime,
        personality: TradingPersonality
    ) -> float:
        """Calculate confidence in adaptation."""
        # Base confidence from regime mapping
        weights = self.regime_mapper.get_personality_weights(regime)
        base_confidence = weights.get(personality, 0.5)
        
        # Adjust for historical performance
        perf_history = self.personality_performance.get(personality, [])
        if perf_history:
            avg_perf = statistics.mean(perf_history[-10:])
            perf_adjustment = avg_perf * 0.2
        else:
            perf_adjustment = 0
        
        return min(0.95, base_confidence + perf_adjustment)
    
    def record_performance(self, pnl: float):
        """Record performance for current personality."""
        self.personality_performance[self.current_personality].append(pnl)
        
        # Keep only recent history
        if len(self.personality_performance[self.current_personality]) > 100:
            self.personality_performance[self.current_personality] = \
                self.personality_performance[self.current_personality][-100:]
    
    def get_current_weights(self) -> Dict[str, Any]:
        """Get current weight configuration."""
        profile = PersonalityProfile.get_profile(self.current_personality)
        
        return {
            'personality': self.current_personality.value,
            'regime': self.current_regime.value if self.current_regime else None,
            'profile': profile,
            'layer_weights': {
                layer: statistics.mean(weights)
                for layer, weights in self.hypernetwork.current_weights.items()
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            'current_personality': self.current_personality.value,
            'current_regime': self.current_regime.value if self.current_regime else None,
            'adaptations_count': len(self.adaptation_history),
            'regime_history_length': len(self.regime_history),
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_hypernetwork_adaptation(config: Optional[Dict] = None) -> HypernetworkAdaptation:
    """Create HypernetworkAdaptation instance."""
    return HypernetworkAdaptation(config)


# Example usage
if __name__ == "__main__":
    import random
    
    system = create_hypernetwork_adaptation()
    
    print("=" * 60)
    print("HYPERNETWORK-BASED ADAPTATION")
    print("=" * 60)
    
    print(f"\nInitial Personality: {system.current_personality.value}")
    
    # Simulate different market regimes
    scenarios = [
        ("Trending Market", MarketRegime.TRENDING_UP),
        ("Range-Bound Market", MarketRegime.RANGING),
        ("Volatile Market", MarketRegime.VOLATILE),
        ("Quiet Market", MarketRegime.QUIET),
    ]
    
    for scenario_name, regime in scenarios:
        print("\n" + "=" * 60)
        print(f"SCENARIO: {scenario_name}")
        print("=" * 60)
        
        # Create context
        context = RegimeContext(
            prices=[100 + random.uniform(-1, 1) for _ in range(50)],
            volumes=[1000 + random.randint(-200, 200) for _ in range(50)],
            volatility=0.02 if regime == MarketRegime.VOLATILE else 0.01,
            trend_strength=0.7 if regime == MarketRegime.TRENDING_UP else 0.1,
            range_bound=regime == MarketRegime.RANGING,
            momentum=0.5
        )
        
        # Detect regime
        detected = system.detect_regime(context)
        print(f"\nDetected Regime: {detected.value}")
        
        # Adapt
        result = system.adapt(regime, force=True)
        
        print(f"\nAdaptation Result:")
        print(f"  Success: {result.success}")
        print(f"  Old Personality: {result.old_personality.value}")
        print(f"  New Personality: {result.new_personality.value}")
        print(f"  Confidence: {result.confidence:.0%}")
        print(f"  Adaptation Time: {result.adaptation_time_ms:.2f}ms")
        print(f"  Adjustments: {len(result.adjustments)} layers")
        
        # Show current weights
        weights = system.get_current_weights()
        print(f"\nCurrent Profile:")
        for key, value in weights['profile'].items():
            print(f"  {key}: {value:.2f}")
        
        # Simulate some performance
        for _ in range(5):
            pnl = random.uniform(-0.02, 0.03)
            system.record_performance(pnl)
    
    # Final status
    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)
    
    status = system.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")

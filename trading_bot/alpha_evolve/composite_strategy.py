"""
Composite Strategy Module

Implements hierarchical strategy composition as specified in the Gap Analysis.
Allows combining multiple sub-strategies with different combination logics.
"""

from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import numpy as np
import logging

from .strategy_genome import StrategyGenome, Signal, SignalType 

logger = logging.getLogger(__name__)


class CombinationType(Enum):
    """Types of strategy combination logic"""
    WEIGHTED_SUM = auto()      # Sum of weighted sub-strategy signals
    MAJORITY_VOTE = auto()     # Majority vote of sub-strategies
    UNANIMOUS = auto()         # All sub-strategies must agree
    CONFIDENCE_WEIGHTED = auto()  # Weight by confidence scores
    CASCADE = auto()           # Sequential evaluation, stop on first valid
    PARALLEL = auto()          # All evaluated, combine results


class CombinationLogic:
    """Base class for combination logic"""
    
    def combine(self, 
                signals: List[Optional[float]], 
                confidences: List[float]) -> Optional[float]:
        """
        Combine signals from multiple sub-strategies.
        
        Args:
            signals: List of signals (None if no signal)
            confidences: Confidence scores for each sub-strategy
            
        Returns:
            Combined signal or None
        """
        raise NotImplementedError


class WeightedSumLogic(CombinationLogic):
    """Weighted sum combination"""
    
    def __init__(self, weights: Optional[List[float]] = None):
        self.weights = weights
    
    def combine(self, signals: List[Optional[float]], 
                confidences: List[float]) -> Optional[float]:
        valid_signals = [(s, c) for s, c in zip(signals, confidences) 
                        if s is not None]
        if not valid_signals:
            return None
        
        if self.weights:
            # Use provided weights
            total_weight = sum(self.weights[:len(valid_signals)])
            if total_weight == 0:
                return None
            weighted_sum = sum(s * self.weights[i] * c 
                             for i, (s, c) in enumerate(valid_signals))
            return weighted_sum / total_weight
        else:
            # Equal weights
            return np.mean([s * c for s, c in valid_signals])


class MajorityVoteLogic(CombinationLogic):
    """Majority vote combination"""
    
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
    
    def combine(self, signals: List[Optional[float]], 
                confidences: List[float]) -> Optional[float]:
        valid_signals = [s for s in signals if s is not None]
        if not valid_signals:
            return None
        
        # Count positive and negative
        positive = sum(1 for s in valid_signals if s > 0)
        negative = sum(1 for s in valid_signals if s < 0)
        total = len(valid_signals)
        
        # Majority vote
        if positive / total > self.threshold:
            return 1.0
        elif negative / total > self.threshold:
            return -1.0
        return None


class UnanimousLogic(CombinationLogic):
    """All must agree"""
    
    def combine(self, signals: List[Optional[float]], 
                confidences: List[float]) -> Optional[float]:
        valid_signals = [s for s in signals if s is not None]
        if not valid_signals or len(valid_signals) != len(signals):
            return None
        
        # Check if all positive or all negative
        if all(s > 0 for s in valid_signals):
            return min(valid_signals)  # Most conservative
        elif all(s < 0 for s in valid_signals):
            return max(valid_signals)  # Most conservative (closest to 0)
        return None


class ConfidenceWeightedLogic(CombinationLogic):
    """Weight by confidence scores"""
    
    def combine(self, signals: List[Optional[float]], 
                confidences: List[float]) -> Optional[float]:
        valid_pairs = [(s, c) for s, c in zip(signals, confidences) 
                      if s is not None and c > 0]
        if not valid_pairs:
            return None
        
        total_confidence = sum(c for _, c in valid_pairs)
        if total_confidence == 0:
            return None
        
        weighted_sum = sum(s * c for s, c in valid_pairs)
        return weighted_sum / total_confidence


class CascadeLogic(CombinationLogic):
    """Sequential evaluation, return first valid signal"""
    
    def combine(self, signals: List[Optional[float]], 
                confidences: List[float]) -> Optional[float]:
        for s, c in zip(signals, confidences):
            if s is not None and c > 0.5:  # High confidence threshold
                return s
        return None


@dataclass
class AdaptiveSignal:
    """
    Adaptive signal that adjusts based on performance history.
    
    Features:
    - Dynamic threshold adjustment
    - Performance tracking
    - Self-tuning parameters
    """
    base_signal: Signal
    adaptation_rate: float = 0.1
    performance_history: List[float] = field(default_factory=list)
    current_threshold: float = field(default=0.0)
    generation_created: int = 0
    
    def __post_init__(self):
        if self.current_threshold == 0.0:
            self.current_threshold = self.base_signal.threshold
    
    def adapt(self, performance: float, generation: int) -> None:
        """
        Adapt signal parameters based on performance.
        
        Args:
            performance: Recent performance metric (e.g., Sharpe ratio)
            generation: Current generation
        """
        self.performance_history.append(performance)
        
        # Keep only last 20 performances
        if len(self.performance_history) > 20:
            self.performance_history = self.performance_history[-20:]
        
        # Adjust threshold based on recent performance trend
        if len(self.performance_history) >= 5:
            recent = np.mean(self.performance_history[-5:])
            older = np.mean(self.performance_history[:-5]) if len(self.performance_history) > 5 else recent
            
            # If improving, become more selective (increase threshold)
            # If declining, become more permissive (decrease threshold)
            if recent > older:
                self.current_threshold += self.adaptation_rate * 0.01
            else:
                self.current_threshold -= self.adaptation_rate * 0.01
            
            # Keep threshold in reasonable bounds
            self.current_threshold = max(-2.0, min(2.0, self.current_threshold))
        
        logger.debug(f"Signal adapted: threshold={self.current_threshold:.4f}")
    
    def get_effective_signal(self) -> Signal:
        """Get signal with adapted parameters"""
        # Create signal with adapted threshold
        adapted = Signal(
            signal_type=self.base_signal.signal_type,
            lookback_period=self.base_signal.lookback_period,
            threshold=self.current_threshold,
            weight=self.base_signal.weight
        )
        return adapted


@dataclass
class CompositeStrategy(StrategyGenome):
    """
    Hierarchical strategy combining multiple sub-strategies.
    
    Features:
    - Multiple sub-strategies
    - Configurable combination logic
    - Adaptive signal tuning
    - Performance-based weight adjustment
    """
    # Inherit from StrategyGenome but make fields optional with defaults
    signals: List[Signal] = field(default_factory=list)
    aggregation_type: Any = None
    position_sizing: Any = None
    risk_control: Any = None
    execution_params: Any = None
    
    # Composite-specific fields
    sub_strategies: List[StrategyGenome] = field(default_factory=list)
    combination_type: CombinationType = CombinationType.WEIGHTED_SUM
    combination_weights: Optional[List[float]] = None
    adaptive_signals: List[AdaptiveSignal] = field(default_factory=list)
    
    # Performance tracking for weight adjustment
    strategy_performance: Dict[str, List[float]] = field(default_factory=dict)
    last_rebalance_generation: int = 0
    rebalance_frequency: int = 10
    
    def __post_init__(self):
        # Initialize combination logic
        self._combination_logic = self._create_combination_logic()
        
        # Initialize performance tracking for sub-strategies
        for sub in self.sub_strategies:
            if sub.get_genome_id() not in self.strategy_performance:
                self.strategy_performance[sub.get_genome_id()] = []
        
        logger.info(f"CompositeStrategy initialized with {len(self.sub_strategies)} sub-strategies")
    
    def _create_combination_logic(self) -> CombinationLogic:
        """Create combination logic based on type"""
        if self.combination_type == CombinationType.WEIGHTED_SUM:
            return WeightedSumLogic(self.combination_weights)
        elif self.combination_type == CombinationType.MAJORITY_VOTE:
            return MajorityVoteLogic()
        elif self.combination_type == CombinationType.UNANIMOUS:
            return UnanimousLogic()
        elif self.combination_type == CombinationType.CONFIDENCE_WEIGHTED:
            return ConfidenceWeightedLogic()
        elif self.combination_type == CombinationType.CASCADE:
            return CascadeLogic()
        else:
            return WeightedSumLogic()  # Default
    
    def add_sub_strategy(self, strategy: StrategyGenome, weight: float = 1.0) -> None:
        """Add a sub-strategy"""
        self.sub_strategies.append(strategy)
        self.strategy_performance[strategy.get_genome_id()] = []
        
        # Update weights
        if self.combination_weights is None:
            self.combination_weights = []
        self.combination_weights.append(weight)
        
        logger.info(f"Added sub-strategy {strategy.get_genome_id()} with weight {weight}")
    
    def remove_sub_strategy(self, strategy_id: str) -> bool:
        """Remove a sub-strategy by ID"""
        for i, sub in enumerate(self.sub_strategies):
            if sub.get_genome_id() == strategy_id:
                self.sub_strategies.pop(i)
                if self.combination_weights and i < len(self.combination_weights):
                    self.combination_weights.pop(i)
                del self.strategy_performance[strategy_id]
                logger.info(f"Removed sub-strategy {strategy_id}")
                return True
        return False
    
    def update_performance(self, strategy_id: str, performance: float) -> None:
        """Update performance for a sub-strategy"""
        if strategy_id in self.strategy_performance:
            self.strategy_performance[strategy_id].append(performance)
            
            # Keep only last 50 values
            if len(self.strategy_performance[strategy_id]) > 50:
                self.strategy_performance[strategy_id] = \
                    self.strategy_performance[strategy_id][-50:]
    
    def rebalance_weights(self, generation: int) -> None:
        """
        Dynamically rebalance weights based on performance.
        
        Increases weights for better-performing strategies,
        decreases for worse-performing ones.
        """
        if generation - self.last_rebalance_generation < self.rebalance_frequency:
            return
        
        if not self.combination_weights or len(self.combination_weights) != len(self.sub_strategies):
            return
        
        # Calculate average performance for each strategy
        performances = []
        for sub in self.sub_strategies:
            perf_history = self.strategy_performance.get(sub.get_genome_id(), [])
            if perf_history:
                avg_perf = np.mean(perf_history[-10:])  # Last 10
                performances.append(max(0, avg_perf))  # Non-negative
            else:
                performances.append(0.0)
        
        if sum(performances) == 0:
            return
        
        # Rebalance: weight proportional to performance
        total_perf = sum(performances)
        new_weights = [p / total_perf for p in performances]
        
        # Smooth transition (blend old and new)
        alpha = 0.3  # Adaptation speed
        self.combination_weights = [
            (1 - alpha) * old + alpha * new
            for old, new in zip(self.combination_weights, new_weights)
        ]
        
        self.last_rebalance_generation = generation
        logger.info(f"Rebalanced weights at generation {generation}: {self.combination_weights}")
    
    def combine_signals(self, 
                       sub_signals: List[Optional[float]], 
                       confidences: List[float]) -> Optional[float]:
        """Combine signals from sub-strategies"""
        # Rebalance if needed
        if hasattr(self, '_last_generation'):
            self.rebalance_weights(self._last_generation)
        
        return self._combination_logic.combine(sub_signals, confidences)
    
    def mutate_adaptive_signals(self, generation: int) -> None:
        """Mutate adaptive signals based on their performance"""
        for adaptive_signal in self.adaptive_signals:
            # Find corresponding performance
            perf_history = self.strategy_performance.get(
                adaptive_signal.base_signal.signal_type.name, [0.5]
            )
            recent_perf = np.mean(perf_history[-5:]) if perf_history else 0.5
            
            adaptive_signal.adapt(recent_perf, generation)
    
    def get_complexity_score(self) -> float:
        """Calculate complexity score based on number of sub-strategies"""
        base_complexity = super().get_complexity_score() if hasattr(super(), 'get_complexity_score') else 0.0
        sub_complexity = sum(
            len(sub.signals) for sub in self.sub_strategies
        )
        return base_complexity + sub_complexity * 0.1
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'sub_strategies': [sub.__dict__ for sub in self.sub_strategies],
            'combination_type': self.combination_type.name,
            'combination_weights': self.combination_weights,
            'adaptive_signals': [
                {
                    'base_signal': s.base_signal.__dict__,
                    'adaptation_rate': s.adaptation_rate,
                    'current_threshold': s.current_threshold
                }
                for s in self.adaptive_signals
            ],
            'strategy_performance': self.strategy_performance,
            'rebalance_frequency': self.rebalance_frequency
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompositeStrategy':
        """Deserialize from dictionary"""
        # This is a simplified version - full implementation would
        # need proper StrategyGenome reconstruction
        sub_strategies = [
            StrategyGenome(**sub_data) 
            for sub_data in data.get('sub_strategies', [])
        ]
        
        combination_type = CombinationType[data.get('combination_type', 'WEIGHTED_SUM')]
        
        return cls(
            sub_strategies=sub_strategies,
            combination_type=combination_type,
            combination_weights=data.get('combination_weights'),
            rebalance_frequency=data.get('rebalance_frequency', 10)
        )


def create_composite_strategy(
    strategies: List[StrategyGenome],
    combination_type: CombinationType = CombinationType.WEIGHTED_SUM,
    weights: Optional[List[float]] = None
) -> CompositeStrategy:
    """
    Factory function to create a composite strategy.
    
    Args:
        strategies: List of sub-strategies
        combination_type: How to combine signals
        weights: Optional weights for each strategy
        
    Returns:
        CompositeStrategy instance
    """
    return CompositeStrategy(
        sub_strategies=strategies,
        combination_type=combination_type,
        combination_weights=weights
    )


def create_adaptive_strategy(
    base_signals: List[Signal],
    adaptation_rate: float = 0.1
) -> CompositeStrategy:
    """
    Create a composite strategy with adaptive signals.
    
    Args:
        base_signals: Base signals to make adaptive
        adaptation_rate: Rate of parameter adaptation
        
    Returns:
        CompositeStrategy with adaptive signals
    """
    adaptive_signals = [
        AdaptiveSignal(
            base_signal=signal,
            adaptation_rate=adaptation_rate
        )
        for signal in base_signals
    ]
    
    # Create simple strategy genome with adaptive signals
    genome = StrategyGenome(
        signals=base_signals  # Use base signals initially
    )
    
    return CompositeStrategy(
        sub_strategies=[genome],
        adaptive_signals=adaptive_signals,
        combination_type=CombinationType.WEIGHTED_SUM
    )

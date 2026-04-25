"""
Strategy Genome: Formal representation of trading strategies as evolvable genomes.

Defines the search space and encoding for strategies that can be mutated,
recombined, and evolved through genetic algorithms.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import numpy as np
import json
import hashlib


class SignalType(Enum):
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    MICROSTRUCTURE = "microstructure"
    SENTIMENT = "sentiment"
    CROSS_ASSET = "cross_asset"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"


class AggregationType(Enum):
    LINEAR = "linear"
    RANK = "rank"
    ENSEMBLE = "ensemble"
    NEURAL = "neural"
    DECISION_TREE = "decision_tree"


class PositionSizingType(Enum):
    FIXED = "fixed"
    KELLY = "kelly"
    VOLATILITY_SCALED = "volatility_scaled"
    RISK_PARITY = "risk_parity"
    DYNAMIC = "dynamic"


@dataclass
class Signal:
    """Individual trading signal component"""
    signal_type: SignalType
    lookback_period: int
    threshold: float
    weight: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_type': self.signal_type.value,
            'lookback_period': self.lookback_period,
            'threshold': self.threshold,
            'weight': self.weight,
            'parameters': self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Signal':
        return cls(
            signal_type=SignalType(data['signal_type']),
            lookback_period=data['lookback_period'],
            threshold=data['threshold'],
            weight=data['weight'],
            parameters=data.get('parameters', {})
        )


@dataclass
class RiskControl:
    """Risk management parameters"""
    max_position_size: float = 0.1
    max_leverage: float = 1.0
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04
    max_drawdown_limit: float = 0.15
    max_correlation: float = 0.7
    var_limit: float = 0.05
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_position_size': self.max_position_size,
            'max_leverage': self.max_leverage,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'max_drawdown_limit': self.max_drawdown_limit,
            'max_correlation': self.max_correlation,
            'var_limit': self.var_limit
        }


@dataclass
class ExecutionParams:
    """Execution and transaction cost parameters"""
    slippage_bps: float = 5.0
    commission_bps: float = 1.0
    market_impact_factor: float = 0.1
    min_order_size: float = 100.0
    max_order_size: float = 1000000.0
    execution_delay_ms: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'slippage_bps': self.slippage_bps,
            'commission_bps': self.commission_bps,
            'market_impact_factor': self.market_impact_factor,
            'min_order_size': self.min_order_size,
            'max_order_size': self.max_order_size,
            'execution_delay_ms': self.execution_delay_ms
        }


@dataclass
class StrategyGenome:
    """
    Complete genome representation of a trading strategy.
    
    This is the fundamental unit of evolution - each genome can be:
    - Mutated (parameters changed, signals added/removed)
    - Recombined (crossover with another genome)
    - Evaluated (backtested and scored)
    - Selected (based on fitness)
    """
    signals: List[Signal]
    aggregation_type: AggregationType
    position_sizing: PositionSizingType
    risk_control: RiskControl
    execution_params: ExecutionParams
    rebalance_frequency: int = 1
    universe_size: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if 'generation' not in self.metadata:
            self.metadata['generation'] = 0
        if 'parent_ids' not in self.metadata:
            self.metadata['parent_ids'] = []
        if 'mutation_history' not in self.metadata:
            self.metadata['mutation_history'] = []
    
    def get_genome_id(self) -> str:
        """Generate unique ID for this genome based on its parameters"""
        genome_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(genome_str.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize genome to dictionary"""
        return {
            'signals': [s.to_dict() for s in self.signals],
            'aggregation_type': self.aggregation_type.value,
            'position_sizing': self.position_sizing.value,
            'risk_control': self.risk_control.to_dict(),
            'execution_params': self.execution_params.to_dict(),
            'rebalance_frequency': self.rebalance_frequency,
            'universe_size': self.universe_size,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyGenome':
        """Deserialize genome from dictionary"""
        return cls(
            signals=[Signal.from_dict(s) for s in data['signals']],
            aggregation_type=AggregationType(data['aggregation_type']),
            position_sizing=PositionSizingType(data['position_sizing']),
            risk_control=RiskControl(**data['risk_control']),
            execution_params=ExecutionParams(**data['execution_params']),
            rebalance_frequency=data['rebalance_frequency'],
            universe_size=data['universe_size'],
            metadata=data.get('metadata', {})
        )
    
    def clone(self) -> 'StrategyGenome':
        """Create a deep copy of this genome"""
        return StrategyGenome.from_dict(self.to_dict())
    
    def get_complexity(self) -> int:
        """Calculate genome complexity (for regularization)"""
        return len(self.signals) + sum(len(s.parameters) for s in self.signals)


class SearchSpace:
    """
    Defines the valid search space for strategy evolution.
    
    Specifies bounds and constraints for all evolvable parameters.
    """
    
    def __init__(self):
        self.signal_types = list(SignalType)
        self.aggregation_types = list(AggregationType)
        self.position_sizing_types = list(PositionSizingType)
        
        self.lookback_range = (5, 252)
        self.threshold_range = (-3.0, 3.0)
        self.weight_range = (-1.0, 1.0)
        self.max_signals = 20
        self.min_signals = 1
        
        self.position_size_range = (0.01, 0.25)
        self.leverage_range = (1.0, 3.0)
        self.stop_loss_range = (0.005, 0.10)
        self.take_profit_range = (0.01, 0.20)
        
        self.rebalance_freq_range = (1, 20)
        self.universe_size_range = (20, 500)
    
    def random_signal(self) -> Signal:
        """Generate a random signal within search space"""
        return Signal(
            signal_type=np.random.choice(self.signal_types),
            lookback_period=np.random.randint(*self.lookback_range),
            threshold=np.random.uniform(*self.threshold_range),
            weight=np.random.uniform(*self.weight_range),
            parameters=self._random_signal_params()
        )
    
    def _random_signal_params(self) -> Dict[str, Any]:
        """Generate random parameters for a signal"""
        return {
            'ema_alpha': np.random.uniform(0.01, 0.5),
            'zscore_window': np.random.randint(10, 100),
            'percentile': np.random.uniform(0.1, 0.9),
        }
    
    def random_genome(self) -> StrategyGenome:
        """Generate a completely random genome"""
        num_signals = np.random.randint(self.min_signals, self.max_signals + 1)
        
        return StrategyGenome(
            signals=[self.random_signal() for _ in range(num_signals)],
            aggregation_type=np.random.choice(self.aggregation_types),
            position_sizing=np.random.choice(self.position_sizing_types),
            risk_control=RiskControl(
                max_position_size=np.random.uniform(*self.position_size_range),
                max_leverage=np.random.uniform(*self.leverage_range),
                stop_loss_pct=np.random.uniform(*self.stop_loss_range),
                take_profit_pct=np.random.uniform(*self.take_profit_range),
            ),
            execution_params=ExecutionParams(),
            rebalance_frequency=np.random.randint(*self.rebalance_freq_range),
            universe_size=np.random.randint(*self.universe_size_range)
        )
    
    def validate_genome(self, genome: StrategyGenome) -> Tuple[bool, List[str]]:
        """Validate that a genome is within search space constraints"""
        errors = []
        
        if len(genome.signals) < self.min_signals:
            errors.append(f"Too few signals: {len(genome.signals)} < {self.min_signals}")
        if len(genome.signals) > self.max_signals:
            errors.append(f"Too many signals: {len(genome.signals)} > {self.max_signals}")
        
        for i, signal in enumerate(genome.signals):
            if not (self.lookback_range[0] <= signal.lookback_period <= self.lookback_range[1]):
                errors.append(f"Signal {i} lookback out of range: {signal.lookback_period}")
            if not (self.threshold_range[0] <= signal.threshold <= self.threshold_range[1]):
                errors.append(f"Signal {i} threshold out of range: {signal.threshold}")
            if not (self.weight_range[0] <= signal.weight <= self.weight_range[1]):
                errors.append(f"Signal {i} weight out of range: {signal.weight}")
        
        return len(errors) == 0, errors
    
    def clip_to_bounds(self, genome: StrategyGenome) -> StrategyGenome:
        """Clip genome parameters to valid search space bounds"""
        clipped = genome.clone()
        
        if len(clipped.signals) > self.max_signals:
            clipped.signals = clipped.signals[:self.max_signals]
        
        for signal in clipped.signals:
            signal.lookback_period = np.clip(signal.lookback_period, *self.lookback_range)
            signal.threshold = np.clip(signal.threshold, *self.threshold_range)
            signal.weight = np.clip(signal.weight, *self.weight_range)
        
        clipped.risk_control.max_position_size = np.clip(
            clipped.risk_control.max_position_size, *self.position_size_range
        )
        clipped.risk_control.max_leverage = np.clip(
            clipped.risk_control.max_leverage, *self.leverage_range
        )
        
        return clipped

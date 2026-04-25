"""
AADS Strategy Genome - Sakana-Inspired Evolutionary Strategy Representation

Strategies are represented as genomes that can be:
- Evolved across generations with fitness selection
- Merged using Sakana AI's model merging techniques (SLERP interpolation)
- Mutated with LLM-driven code evolution (AlphaEvolve)

This is the fundamental unit of evolution in AADS.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime
import numpy as np
import json
import hashlib
import uuid


class GenomeStatus(Enum):
    """Strategy genome lifecycle status"""
    CANDIDATE = "candidate"      # Newly generated, not yet validated
    VALIDATED = "validated"      # Passed backtesting gates
    DEPLOYED = "deployed"        # Live with capital allocation
    SHADOW = "shadow"            # Running in shadow mode for comparison
    RETIRED = "retired"          # No longer active, archived for lineage


class SignalGeneType(Enum):
    """Types of signal genes"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY_BREAKOUT = "volatility_breakout"
    VOLUME_ANOMALY = "volume_anomaly"
    EARNINGS_SURPRISE = "earnings_surprise"
    ANALYST_REVISION = "analyst_revision"
    SHORT_SQUEEZE = "short_squeeze"
    YIELD_CURVE = "yield_curve"
    DOLLAR_MOMENTUM = "dollar_momentum"
    VIX_REGIME = "vix_regime"
    SATELLITE = "satellite"
    SENTIMENT = "sentiment"
    OPTIONS_FLOW = "options_flow"
    DARKPOOL = "darkpool"
    POLYMARKET_EDGE = "polymarket_edge"
    CUSTOM_LLM = "custom_llm"


@dataclass
class StrategyGene:
    """
    Individual signal gene within a strategy genome.
    
    Each gene represents a specific alpha signal with its parameters.
    """
    gene_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    signal_type: SignalGeneType = SignalGeneType.MOMENTUM
    weight: float = 1.0
    lookback: int = 20
    threshold: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Performance tracking
    accuracy_30d: float = 0.5
    contribution_pnl: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'gene_id': self.gene_id,
            'signal_type': self.signal_type.value,
            'weight': self.weight,
            'lookback': self.lookback,
            'threshold': self.threshold,
            'parameters': self.parameters,
            'accuracy_30d': self.accuracy_30d,
            'contribution_pnl': self.contribution_pnl,
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyGene':
        return cls(
            gene_id=data.get('gene_id', str(uuid.uuid4())[:8]),
            signal_type=SignalGeneType(data['signal_type']),
            weight=data['weight'],
            lookback=data['lookback'],
            threshold=data['threshold'],
            parameters=data.get('parameters', {}),
            accuracy_30d=data.get('accuracy_30d', 0.5),
            contribution_pnl=data.get('contribution_pnl', 0.0),
            last_updated=datetime.fromisoformat(data['last_updated']) if 'last_updated' in data else datetime.now()
        )


@dataclass
class RiskGene:
    """Risk management parameters as evolvable genes"""
    max_drawdown: float = 0.15          # Maximum allowed drawdown
    kelly_fraction: float = 0.25        # Kelly criterion fraction
    horizon_days: int = 20              # Investment horizon
    var_limit: float = 0.02             # Value at Risk limit (daily)
    max_position_pct: float = 0.02      # Max single position (2% of portfolio)
    max_sector_pct: float = 0.10        # Max sector exposure (10%)
    max_correlation: float = 0.6        # Max correlation for position grouping
    stop_loss_pct: float = 0.05         # Stop loss percentage
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_drawdown': self.max_drawdown,
            'kelly_fraction': self.kelly_fraction,
            'horizon_days': self.horizon_days,
            'var_limit': self.var_limit,
            'max_position_pct': self.max_position_pct,
            'max_sector_pct': self.max_sector_pct,
            'max_correlation': self.max_correlation,
            'stop_loss_pct': self.stop_loss_pct
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskGene':
        return cls(**data)


@dataclass
class FilterGene:
    """Market regime and universe filter genes"""
    regime_filter: str = "all"          # "bull", "bear", "sideways", "all"
    sector_filter: List[str] = field(default_factory=list)  # GICS sectors
    vol_filter: str = "all"             # "low", "medium", "high", "all"
    liquidity_min_adv: float = 1e6      # Minimum average daily volume ($)
    market_cap_min: float = 1e9         # Minimum market cap ($)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'regime_filter': self.regime_filter,
            'sector_filter': self.sector_filter,
            'vol_filter': self.vol_filter,
            'liquidity_min_adv': self.liquidity_min_adv,
            'market_cap_min': self.market_cap_min
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterGene':
        return cls(**data)


@dataclass
class ExecutionGene:
    """Execution algorithm parameters"""
    algo: str = "twap"                  # "twap", "vwap", "is", "adaptive"
    participation_rate: float = 0.05    # Max % of volume
    venue_priority: List[str] = field(default_factory=lambda: ["primary", "dark", "lit"])
    urgency: str = "medium"             # "low", "medium", "high", "critical"
    max_slippage_bps: float = 10.0      # Maximum acceptable slippage
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'algo': self.algo,
            'participation_rate': self.participation_rate,
            'venue_priority': self.venue_priority,
            'urgency': self.urgency,
            'max_slippage_bps': self.max_slippage_bps
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionGene':
        return cls(**data)


@dataclass
class AADSStrategyGenome:
    """
    Complete AADS Strategy Genome - The fundamental unit of evolution.
    
    Inspired by Sakana AI's evolutionary model merging approach.
    Strategies are genomes that evolve across generations with:
    - Signal genes: alpha signals with weights and parameters
    - Risk genes: risk management parameters
    - Filter genes: universe and regime filters
    - Execution genes: order execution parameters
    
    Fitness = Sharpe * (1 - max_dd) * win_rate
    """
    genome_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    
    # Gene components
    signal_genes: List[StrategyGene] = field(default_factory=list)
    risk_genes: RiskGene = field(default_factory=RiskGene)
    filter_genes: FilterGene = field(default_factory=FilterGene)
    execution_genes: ExecutionGene = field(default_factory=ExecutionGene)
    
    # Fitness and performance
    fitness_score: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Lifecycle
    status: GenomeStatus = GenomeStatus.CANDIDATE
    mutation_rate: float = 0.15         # Adapts based on fitness variance
    capital_allocation: float = 0.0     # % of portfolio allocated
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    backtest_results: Dict[str, Any] = field(default_factory=dict)
    live_results: Dict[str, Any] = field(default_factory=dict)
    
    # LLM-evolved code (AlphaEvolve)
    evolved_code: Optional[str] = None
    code_generation: int = 0
    
    def compute_fitness(self) -> float:
        """
        Compute composite fitness score.
        
        Fitness = Sharpe * (1 - max_dd) * win_rate
        
        This is the selection pressure for evolution.
        """
        if self.sharpe_ratio <= 0:
            self.fitness_score = 0.0
        else:
            dd_factor = max(0, 1 - abs(self.max_drawdown))
            self.fitness_score = self.sharpe_ratio * dd_factor * self.win_rate
        
        return self.fitness_score
    
    def get_hash(self) -> str:
        """Generate unique hash for this genome configuration"""
        genome_str = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(genome_str.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize genome to dictionary"""
        return {
            'genome_id': self.genome_id,
            'generation': self.generation,
            'parent_ids': self.parent_ids,
            'signal_genes': [g.to_dict() for g in self.signal_genes],
            'risk_genes': self.risk_genes.to_dict(),
            'filter_genes': self.filter_genes.to_dict(),
            'execution_genes': self.execution_genes.to_dict(),
            'fitness_score': self.fitness_score,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'status': self.status.value,
            'mutation_rate': self.mutation_rate,
            'capital_allocation': self.capital_allocation,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'backtest_results': self.backtest_results,
            'live_results': self.live_results,
            'evolved_code': self.evolved_code,
            'code_generation': self.code_generation
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AADSStrategyGenome':
        """Deserialize genome from dictionary"""
        return cls(
            genome_id=data['genome_id'],
            generation=data['generation'],
            parent_ids=data.get('parent_ids', []),
            signal_genes=[StrategyGene.from_dict(g) for g in data.get('signal_genes', [])],
            risk_genes=RiskGene.from_dict(data.get('risk_genes', {})),
            filter_genes=FilterGene.from_dict(data.get('filter_genes', {})),
            execution_genes=ExecutionGene.from_dict(data.get('execution_genes', {})),
            fitness_score=data.get('fitness_score', 0.0),
            sharpe_ratio=data.get('sharpe_ratio', 0.0),
            max_drawdown=data.get('max_drawdown', 0.0),
            win_rate=data.get('win_rate', 0.0),
            sortino_ratio=data.get('sortino_ratio', 0.0),
            calmar_ratio=data.get('calmar_ratio', 0.0),
            status=GenomeStatus(data.get('status', 'candidate')),
            mutation_rate=data.get('mutation_rate', 0.15),
            capital_allocation=data.get('capital_allocation', 0.0),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            last_updated=datetime.fromisoformat(data['last_updated']) if 'last_updated' in data else datetime.now(),
            backtest_results=data.get('backtest_results', {}),
            live_results=data.get('live_results', {}),
            evolved_code=data.get('evolved_code'),
            code_generation=data.get('code_generation', 0)
        )
    
    def clone(self) -> 'AADSStrategyGenome':
        """Create a deep copy of this genome"""
        cloned = AADSStrategyGenome.from_dict(self.to_dict())
        cloned.genome_id = str(uuid.uuid4())
        cloned.parent_ids = [self.genome_id]
        cloned.generation = self.generation + 1
        cloned.status = GenomeStatus.CANDIDATE
        cloned.fitness_score = 0.0
        cloned.capital_allocation = 0.0
        cloned.created_at = datetime.now()
        cloned.last_updated = datetime.now()
        return cloned


def slerp(v0: float, v1: float, t: float) -> float:
    """
    Spherical linear interpolation for weight merging.
    
    Used in Sakana-style model merging to interpolate between
    parent strategy weights in a geometrically meaningful way.
    """
    # Handle edge cases
    if abs(v0 - v1) < 1e-10:
        return v0
    
    # Normalize to unit vectors (treating as 1D)
    norm0 = abs(v0) if v0 != 0 else 1e-10
    norm1 = abs(v1) if v1 != 0 else 1e-10
    
    # Simple linear interpolation for 1D case
    # (SLERP is more meaningful in higher dimensions)
    return v0 * (1 - t) + v1 * t


def merge_strategies(
    strategy_a: AADSStrategyGenome,
    strategy_b: AADSStrategyGenome,
    merge_ratio: float = 0.5
) -> AADSStrategyGenome:
    """
    Sakana-style model merging: interpolate weights in parameter space.
    
    Produces a child genome that inherits capabilities from both parents.
    Uses SLERP interpolation for smooth blending.
    
    Args:
        strategy_a: First parent genome
        strategy_b: Second parent genome
        merge_ratio: Interpolation factor (0.0 = all A, 1.0 = all B)
    
    Returns:
        Merged child genome
    """
    # Collect all signal types from both parents
    all_signal_types = set()
    a_signals = {g.signal_type: g for g in strategy_a.signal_genes}
    b_signals = {g.signal_type: g for g in strategy_b.signal_genes}
    all_signal_types.update(a_signals.keys())
    all_signal_types.update(b_signals.keys())
    
    # Merge signal genes
    merged_signals = []
    for signal_type in all_signal_types:
        a_gene = a_signals.get(signal_type)
        b_gene = b_signals.get(signal_type)
        
        if a_gene and b_gene:
            # Both parents have this signal - interpolate
            merged_gene = StrategyGene(
                signal_type=signal_type,
                weight=slerp(a_gene.weight, b_gene.weight, merge_ratio),
                lookback=int(slerp(a_gene.lookback, b_gene.lookback, merge_ratio)),
                threshold=slerp(a_gene.threshold, b_gene.threshold, merge_ratio),
                parameters={
                    k: slerp(
                        a_gene.parameters.get(k, 0),
                        b_gene.parameters.get(k, 0),
                        merge_ratio
                    )
                    for k in set(a_gene.parameters.keys()) | set(b_gene.parameters.keys())
                    if isinstance(a_gene.parameters.get(k, 0), (int, float)) and
                       isinstance(b_gene.parameters.get(k, 0), (int, float))
                }
            )
        elif a_gene:
            # Only parent A has this signal - scale by (1 - merge_ratio)
            merged_gene = StrategyGene(
                signal_type=signal_type,
                weight=a_gene.weight * (1 - merge_ratio),
                lookback=a_gene.lookback,
                threshold=a_gene.threshold,
                parameters=a_gene.parameters.copy()
            )
        else:
            # Only parent B has this signal - scale by merge_ratio
            merged_gene = StrategyGene(
                signal_type=signal_type,
                weight=b_gene.weight * merge_ratio,
                lookback=b_gene.lookback,
                threshold=b_gene.threshold,
                parameters=b_gene.parameters.copy()
            )
        
        # Only include if weight is significant
        if abs(merged_gene.weight) > 0.05:
            merged_signals.append(merged_gene)
    
    # Merge risk genes
    merged_risk = RiskGene(
        max_drawdown=slerp(strategy_a.risk_genes.max_drawdown, strategy_b.risk_genes.max_drawdown, merge_ratio),
        kelly_fraction=slerp(strategy_a.risk_genes.kelly_fraction, strategy_b.risk_genes.kelly_fraction, merge_ratio),
        horizon_days=int(slerp(strategy_a.risk_genes.horizon_days, strategy_b.risk_genes.horizon_days, merge_ratio)),
        var_limit=slerp(strategy_a.risk_genes.var_limit, strategy_b.risk_genes.var_limit, merge_ratio),
        max_position_pct=slerp(strategy_a.risk_genes.max_position_pct, strategy_b.risk_genes.max_position_pct, merge_ratio),
        max_sector_pct=slerp(strategy_a.risk_genes.max_sector_pct, strategy_b.risk_genes.max_sector_pct, merge_ratio),
        max_correlation=slerp(strategy_a.risk_genes.max_correlation, strategy_b.risk_genes.max_correlation, merge_ratio),
        stop_loss_pct=slerp(strategy_a.risk_genes.stop_loss_pct, strategy_b.risk_genes.stop_loss_pct, merge_ratio)
    )
    
    # Create merged genome
    merged = AADSStrategyGenome(
        genome_id=str(uuid.uuid4()),
        generation=max(strategy_a.generation, strategy_b.generation) + 1,
        parent_ids=[strategy_a.genome_id, strategy_b.genome_id],
        signal_genes=merged_signals,
        risk_genes=merged_risk,
        filter_genes=strategy_a.filter_genes if merge_ratio < 0.5 else strategy_b.filter_genes,
        execution_genes=strategy_a.execution_genes if merge_ratio < 0.5 else strategy_b.execution_genes,
        status=GenomeStatus.CANDIDATE,
        mutation_rate=(strategy_a.mutation_rate + strategy_b.mutation_rate) / 2
    )
    
    return merged


def create_random_genome(
    num_signals: int = 5,
    signal_types: Optional[List[SignalGeneType]] = None
) -> AADSStrategyGenome:
    """
    Create a random strategy genome for population initialization.
    
    Args:
        num_signals: Number of signal genes to include
        signal_types: Allowed signal types (default: all)
    
    Returns:
        Randomly initialized genome
    """
    if signal_types is None:
        signal_types = list(SignalGeneType)
    
    # Generate random signal genes
    signals = []
    selected_types = np.random.choice(signal_types, size=min(num_signals, len(signal_types)), replace=False)
    
    for sig_type in selected_types:
        gene = StrategyGene(
            signal_type=sig_type,
            weight=np.random.uniform(-1.0, 1.0),
            lookback=np.random.randint(5, 252),
            threshold=np.random.uniform(-2.0, 2.0),
            parameters={
                'ema_alpha': np.random.uniform(0.01, 0.5),
                'zscore_window': np.random.randint(10, 100),
                'percentile': np.random.uniform(0.1, 0.9)
            }
        )
        signals.append(gene)
    
    # Generate random risk genes
    risk = RiskGene(
        max_drawdown=np.random.uniform(0.10, 0.25),
        kelly_fraction=np.random.uniform(0.1, 0.5),
        horizon_days=np.random.randint(5, 60),
        var_limit=np.random.uniform(0.01, 0.05),
        max_position_pct=np.random.uniform(0.01, 0.05),
        max_sector_pct=np.random.uniform(0.05, 0.15),
        max_correlation=np.random.uniform(0.4, 0.8),
        stop_loss_pct=np.random.uniform(0.02, 0.10)
    )
    
    return AADSStrategyGenome(
        signal_genes=signals,
        risk_genes=risk,
        status=GenomeStatus.CANDIDATE
    )

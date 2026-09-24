"""
Self-Replicating Strategy Factory
==================================

A factory that can create, test, evolve, and replicate
trading strategies autonomously:
- Strategy templates and blueprints
- Automatic strategy generation
- Strategy breeding and crossover
- Performance-based selection
- Strategy lifecycle management
- Strategy DNA encoding/decoding

The factory operates like a biological system where
successful strategies reproduce and unsuccessful ones die.
"""

import asyncio
import copy
import hashlib
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type
import json

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Types of trading strategies"""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    SWING = "swing"
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"
    STATISTICAL = "statistical"
    HYBRID = "hybrid"


class StrategyState(Enum):
    """Lifecycle states of a strategy"""
    EMBRYO = "embryo"           # Just created, not tested
    INCUBATING = "incubating"   # Being tested in sandbox
    JUVENILE = "juvenile"       # Passed initial tests, paper trading
    MATURE = "mature"           # Proven, ready for live trading
    REPRODUCING = "reproducing" # Creating offspring
    SENESCENT = "senescent"     # Performance declining
    DEAD = "dead"               # Deactivated


@dataclass
class StrategyGene:
    """A single gene in strategy DNA"""
    name: str
    value: Any
    gene_type: str  # "parameter", "indicator", "rule", "filter"
    mutable: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class StrategyDNA:
    """Complete DNA encoding of a strategy"""
    genes: List[StrategyGene]
    strategy_type: StrategyType
    generation: int = 0
    mutations: int = 0
    
    def encode(self) -> str:
        """Encode DNA as string"""
        data = {
            'genes': [
                {
                    'name': g.name,
                    'value': g.value,
                    'gene_type': g.gene_type,
                    'mutable': g.mutable,
                    'min_value': g.min_value,
                    'max_value': g.max_value,
                }
                for g in self.genes
            ],
            'strategy_type': self.strategy_type.value,
            'generation': self.generation,
            'mutations': self.mutations,
        }
        return json.dumps(data, sort_keys=True)
    
    @classmethod
    def decode(cls, dna_string: str) -> 'StrategyDNA':
        """Decode DNA from string"""
        data = json.loads(dna_string)
        genes = [
            StrategyGene(
                name=g['name'],
                value=g['value'],
                gene_type=g['gene_type'],
                mutable=g.get('mutable', True),
                min_value=g.get('min_value'),
                max_value=g.get('max_value'),
            )
            for g in data['genes']
        ]
        return cls(
            genes=genes,
            strategy_type=StrategyType(data['strategy_type']),
            generation=data['generation'],
            mutations=data['mutations'],
        )
    
    def get_hash(self) -> str:
        """Get unique hash of DNA"""
        return hashlib.sha256(self.encode().encode()).hexdigest()[:16]
    
    def mutate(self, mutation_rate: float = 0.1) -> 'StrategyDNA':
        """Create mutated copy"""
        new_genes = []
        mutations = 0
        
        for gene in self.genes:
            new_gene = copy.deepcopy(gene)
            
            if gene.mutable and random.random() < mutation_rate:
                mutations += 1
                
                if isinstance(gene.value, (int, float)):
                    if gene.min_value is not None and gene.max_value is not None:
                        range_size = gene.max_value - gene.min_value
                        new_gene.value = gene.value + random.gauss(0, range_size * 0.1)
                        new_gene.value = max(gene.min_value, min(gene.max_value, new_gene.value))
                    else:
                        new_gene.value = gene.value * random.uniform(0.8, 1.2)
                
                elif isinstance(gene.value, bool):
                    new_gene.value = not gene.value
                
                elif isinstance(gene.value, list):
                    if len(gene.value) > 0:
                        idx = random.randint(0, len(gene.value) - 1)
                        if isinstance(gene.value[idx], (int, float)):
                            new_gene.value = gene.value.copy()
                            new_gene.value[idx] *= random.uniform(0.8, 1.2)
            
            new_genes.append(new_gene)
        
        return StrategyDNA(
            genes=new_genes,
            strategy_type=self.strategy_type,
            generation=self.generation + 1,
            mutations=self.mutations + mutations,
        )
    
    def crossover(self, other: 'StrategyDNA') -> Tuple['StrategyDNA', 'StrategyDNA']:
        """Crossover with another DNA"""
        if len(self.genes) < 2 or len(other.genes) < 2:
            return self.mutate(), other.mutate()
        
        # Find common genes
        self_gene_names = {g.name for g in self.genes}
        other_gene_names = {g.name for g in other.genes}
        common_names = self_gene_names & other_gene_names
        
        if len(common_names) < 2:
            return self.mutate(), other.mutate()
        
        # Crossover point
        crossover_point = random.randint(1, len(common_names) - 1)
        common_list = sorted(list(common_names))
        
        child1_genes = []
        child2_genes = []
        
        for i, name in enumerate(common_list):
            gene1 = next((g for g in self.genes if g.name == name), None)
            gene2 = next((g for g in other.genes if g.name == name), None)
            
            if gene1 and gene2:
                if i < crossover_point:
                    child1_genes.append(copy.deepcopy(gene1))
                    child2_genes.append(copy.deepcopy(gene2))
                else:
                    child1_genes.append(copy.deepcopy(gene2))
                    child2_genes.append(copy.deepcopy(gene1))
        
        child1 = StrategyDNA(
            genes=child1_genes,
            strategy_type=self.strategy_type,
            generation=max(self.generation, other.generation) + 1,
        )
        
        child2 = StrategyDNA(
            genes=child2_genes,
            strategy_type=other.strategy_type,
            generation=max(self.generation, other.generation) + 1,
        )
        
        return child1, child2


@dataclass
class StrategyBlueprint:
    """Blueprint for creating strategies"""
    blueprint_id: str
    name: str
    strategy_type: StrategyType
    description: str
    
    # Template genes
    template_genes: List[StrategyGene]
    
    # Requirements
    min_data_points: int = 100
    required_indicators: List[str] = field(default_factory=list)
    
    # Performance thresholds
    min_sharpe: float = 0.5
    max_drawdown: float = 0.20
    min_win_rate: float = 0.45
    
    def create_dna(self) -> StrategyDNA:
        """Create DNA from blueprint"""
        return StrategyDNA(
            genes=[copy.deepcopy(g) for g in self.template_genes],
            strategy_type=self.strategy_type,
            generation=0,
        )


@dataclass
class Strategy:
    """A living trading strategy"""
    strategy_id: str
    name: str
    dna: StrategyDNA
    state: StrategyState = StrategyState.EMBRYO
    
    # Lineage
    parent_ids: List[str] = field(default_factory=list)
    children_ids: List[str] = field(default_factory=list)
    
    # Lifecycle
    birth_time: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    age_days: int = 0
    
    # Performance
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    fitness: float = 0.0
    
    # Energy (determines survival)
    energy: float = 100.0
    
    def get_win_rate(self) -> float:
        """Calculate win rate"""
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades
    
    def update_fitness(self) -> None:
        """Update fitness score"""
        # Composite fitness
        win_rate_score = self.get_win_rate() * 30
        sharpe_score = max(0, self.sharpe_ratio) * 20
        drawdown_score = max(0, 1 - self.max_drawdown / 0.3) * 20
        pnl_score = min(30, max(0, self.total_pnl / 1000) * 30)
        
        self.fitness = win_rate_score + sharpe_score + drawdown_score + pnl_score
    
    def consume_energy(self, amount: float) -> None:
        """Consume energy"""
        self.energy = max(0, self.energy - amount)
        if self.energy <= 0:
            self.state = StrategyState.DEAD
    
    def gain_energy(self, amount: float) -> None:
        """Gain energy from successful trades"""
        self.energy = min(200, self.energy + amount)
    
    def can_reproduce(self) -> bool:
        """Check if strategy can reproduce"""
        return (
            self.state == StrategyState.MATURE and
            self.energy >= 120 and
            self.fitness >= 50 and
            self.total_trades >= 20
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'state': self.state.value,
            'strategy_type': self.dna.strategy_type.value,
            'generation': self.dna.generation,
            'parent_ids': self.parent_ids,
            'birth_time': self.birth_time.isoformat(),
            'age_days': self.age_days,
            'total_trades': self.total_trades,
            'win_rate': self.get_win_rate(),
            'total_pnl': self.total_pnl,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'fitness': self.fitness,
            'energy': self.energy,
            'dna_hash': self.dna.get_hash(),
        }


class StrategyFactory:
    """
    Self-Replicating Strategy Factory
    
    Creates, evolves, and manages trading strategies
    as living entities that compete for survival.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Strategy population
        self.strategies: Dict[str, Strategy] = {}
        self.graveyard: List[Strategy] = []  # Dead strategies
        self.hall_of_fame: List[Strategy] = []  # Best ever
        
        # Blueprints
        self.blueprints: Dict[str, StrategyBlueprint] = {}
        self._create_default_blueprints()
        
        # Population limits
        self.max_population = self.config.get('max_population', 50)
        self.min_population = self.config.get('min_population', 10)
        
        # Evolution parameters
        self.mutation_rate = self.config.get('mutation_rate', 0.1)
        self.crossover_rate = self.config.get('crossover_rate', 0.3)
        self.selection_pressure = self.config.get('selection_pressure', 0.5)
        
        # Lifecycle parameters
        self.incubation_trades = self.config.get('incubation_trades', 10)
        self.juvenile_trades = self.config.get('juvenile_trades', 50)
        self.maturity_fitness = self.config.get('maturity_fitness', 40)
        
        self.generation = 0
        self.total_created = 0
        self.total_died = 0
        
        logger.info("StrategyFactory initialized")
    
    def _create_default_blueprints(self) -> None:
        """Create default strategy blueprints"""
        # Trend Following Blueprint
        self.blueprints['trend_following'] = StrategyBlueprint(
            blueprint_id='bp_trend_following',
            name='Trend Following',
            strategy_type=StrategyType.TREND_FOLLOWING,
            description='Follow market trends using moving averages',
            template_genes=[
                StrategyGene('fast_ma_period', 10, 'parameter', True, 5, 50),
                StrategyGene('slow_ma_period', 50, 'parameter', True, 20, 200),
                StrategyGene('atr_period', 14, 'parameter', True, 5, 30),
                StrategyGene('atr_multiplier', 2.0, 'parameter', True, 1.0, 5.0),
                StrategyGene('trend_strength_threshold', 0.5, 'parameter', True, 0.2, 0.8),
                StrategyGene('use_volume_filter', True, 'filter', True),
                StrategyGene('risk_per_trade', 0.02, 'parameter', True, 0.005, 0.05),
            ],
            required_indicators=['SMA', 'ATR'],
        )
        
        # Mean Reversion Blueprint
        self.blueprints['mean_reversion'] = StrategyBlueprint(
            blueprint_id='bp_mean_reversion',
            name='Mean Reversion',
            strategy_type=StrategyType.MEAN_REVERSION,
            description='Trade reversions to mean',
            template_genes=[
                StrategyGene('lookback_period', 20, 'parameter', True, 10, 100),
                StrategyGene('std_dev_threshold', 2.0, 'parameter', True, 1.0, 3.0),
                StrategyGene('rsi_period', 14, 'parameter', True, 5, 30),
                StrategyGene('rsi_oversold', 30, 'parameter', True, 10, 40),
                StrategyGene('rsi_overbought', 70, 'parameter', True, 60, 90),
                StrategyGene('use_bollinger', True, 'indicator', True),
                StrategyGene('risk_per_trade', 0.015, 'parameter', True, 0.005, 0.03),
            ],
            required_indicators=['RSI', 'Bollinger'],
        )
        
        # Momentum Blueprint
        self.blueprints['momentum'] = StrategyBlueprint(
            blueprint_id='bp_momentum',
            name='Momentum',
            strategy_type=StrategyType.MOMENTUM,
            description='Capture momentum moves',
            template_genes=[
                StrategyGene('momentum_period', 14, 'parameter', True, 5, 50),
                StrategyGene('roc_period', 10, 'parameter', True, 5, 30),
                StrategyGene('macd_fast', 12, 'parameter', True, 5, 20),
                StrategyGene('macd_slow', 26, 'parameter', True, 15, 50),
                StrategyGene('macd_signal', 9, 'parameter', True, 5, 15),
                StrategyGene('momentum_threshold', 0.0, 'parameter', True, -0.5, 0.5),
                StrategyGene('risk_per_trade', 0.02, 'parameter', True, 0.005, 0.04),
            ],
            required_indicators=['MACD', 'ROC'],
        )
        
        # Breakout Blueprint
        self.blueprints['breakout'] = StrategyBlueprint(
            blueprint_id='bp_breakout',
            name='Breakout',
            strategy_type=StrategyType.BREAKOUT,
            description='Trade breakouts from ranges',
            template_genes=[
                StrategyGene('lookback_period', 20, 'parameter', True, 10, 50),
                StrategyGene('breakout_threshold', 0.02, 'parameter', True, 0.005, 0.05),
                StrategyGene('volume_multiplier', 1.5, 'parameter', True, 1.0, 3.0),
                StrategyGene('consolidation_bars', 5, 'parameter', True, 3, 20),
                StrategyGene('use_atr_filter', True, 'filter', True),
                StrategyGene('risk_per_trade', 0.025, 'parameter', True, 0.01, 0.05),
            ],
            required_indicators=['ATR', 'Volume'],
        )
    
    def create_strategy(self, blueprint_id: str, name: Optional[str] = None) -> Strategy:
        """Create a new strategy from blueprint"""
        if blueprint_id not in self.blueprints:
            raise ValueError(f"Unknown blueprint: {blueprint_id}")
        
        blueprint = self.blueprints[blueprint_id]
        dna = blueprint.create_dna()
        
        strategy_id = f"strat_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        strategy_name = name or f"{blueprint.name}_{self.total_created}"
        
        strategy = Strategy(
            strategy_id=strategy_id,
            name=strategy_name,
            dna=dna,
            state=StrategyState.EMBRYO,
        )
        
        self.strategies[strategy_id] = strategy
        self.total_created += 1
        
        logger.info(f"Created strategy: {strategy_id} from blueprint {blueprint_id}")
        return strategy
    
    def create_random_strategy(self) -> Strategy:
        """Create a random strategy from random blueprint"""
        blueprint_id = random.choice(list(self.blueprints.keys()))
        strategy = self.create_strategy(blueprint_id)
        
        # Apply random mutations
        strategy.dna = strategy.dna.mutate(mutation_rate=0.3)
        
        return strategy
    
    def breed_strategies(self, parent1_id: str, parent2_id: str) -> Tuple[Strategy, Strategy]:
        """Breed two strategies to create offspring"""
        parent1 = self.strategies.get(parent1_id)
        parent2 = self.strategies.get(parent2_id)
        
        if not parent1 or not parent2:
            raise ValueError("Parent strategies not found")
        
        # Crossover DNA
        child1_dna, child2_dna = parent1.dna.crossover(parent2.dna)
        
        # Apply mutations
        if random.random() < self.mutation_rate:
            child1_dna = child1_dna.mutate(self.mutation_rate)
        if random.random() < self.mutation_rate:
            child2_dna = child2_dna.mutate(self.mutation_rate)
        
        # Create child strategies
        child1 = Strategy(
            strategy_id=f"strat_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            name=f"{parent1.name}_x_{parent2.name}_1",
            dna=child1_dna,
            state=StrategyState.EMBRYO,
            parent_ids=[parent1_id, parent2_id],
        )
        
        child2 = Strategy(
            strategy_id=f"strat_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            name=f"{parent1.name}_x_{parent2.name}_2",
            dna=child2_dna,
            state=StrategyState.EMBRYO,
            parent_ids=[parent1_id, parent2_id],
        )
        
        # Update parent records
        parent1.children_ids.append(child1.strategy_id)
        parent1.children_ids.append(child2.strategy_id)
        parent2.children_ids.append(child1.strategy_id)
        parent2.children_ids.append(child2.strategy_id)
        
        # Consume parent energy
        parent1.consume_energy(30)
        parent2.consume_energy(30)
        
        self.strategies[child1.strategy_id] = child1
        self.strategies[child2.strategy_id] = child2
        self.total_created += 2
        
        logger.info(f"Bred strategies: {child1.strategy_id}, {child2.strategy_id}")
        return child1, child2
    
    def update_strategy_state(self, strategy_id: str, trade_result: Dict[str, Any]) -> None:
        """Update strategy based on trade result"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return
        
        # Update performance
        strategy.total_trades += 1
        pnl = trade_result.get('pnl', 0)
        strategy.total_pnl += pnl
        
        if pnl > 0:
            strategy.winning_trades += 1
            strategy.gain_energy(pnl / 100)  # Gain energy from profits
        else:
            strategy.consume_energy(abs(pnl) / 50)  # Lose energy from losses
        
        # Update drawdown
        drawdown = trade_result.get('drawdown', 0)
        strategy.max_drawdown = max(strategy.max_drawdown, drawdown)
        
        # Update Sharpe (simplified)
        if strategy.total_trades > 5:
            avg_return = strategy.total_pnl / strategy.total_trades
            strategy.sharpe_ratio = avg_return / max(0.01, abs(strategy.max_drawdown))
        
        # Update fitness
        strategy.update_fitness()
        strategy.last_active = datetime.utcnow()
        
        # State transitions
        self._update_lifecycle_state(strategy)
    
    def _update_lifecycle_state(self, strategy: Strategy) -> None:
        """Update strategy lifecycle state"""
        if strategy.state == StrategyState.DEAD:
            return
        
        # Embryo -> Incubating
        if strategy.state == StrategyState.EMBRYO:
            strategy.state = StrategyState.INCUBATING
        
        # Incubating -> Juvenile
        elif strategy.state == StrategyState.INCUBATING:
            if strategy.total_trades >= self.incubation_trades:
                if strategy.fitness >= 20:
                    strategy.state = StrategyState.JUVENILE
                else:
                    strategy.state = StrategyState.DEAD
                    self._kill_strategy(strategy)
        
        # Juvenile -> Mature
        elif strategy.state == StrategyState.JUVENILE:
            if strategy.total_trades >= self.juvenile_trades:
                if strategy.fitness >= self.maturity_fitness:
                    strategy.state = StrategyState.MATURE
                else:
                    strategy.state = StrategyState.SENESCENT
        
        # Mature -> Senescent (performance decline)
        elif strategy.state == StrategyState.MATURE:
            if strategy.fitness < self.maturity_fitness * 0.7:
                strategy.state = StrategyState.SENESCENT
        
        # Senescent -> Dead
        elif strategy.state == StrategyState.SENESCENT:
            if strategy.energy <= 0 or strategy.fitness < 10:
                strategy.state = StrategyState.DEAD
                self._kill_strategy(strategy)
    
    def _kill_strategy(self, strategy: Strategy) -> None:
        """Move strategy to graveyard"""
        if strategy.strategy_id in self.strategies:
            del self.strategies[strategy.strategy_id]
        
        self.graveyard.append(strategy)
        if len(self.graveyard) > 100:
            self.graveyard.pop(0)
        
        self.total_died += 1
        logger.info(f"Strategy died: {strategy.strategy_id}")
    
    def natural_selection(self) -> None:
        """Apply natural selection to population"""
        if len(self.strategies) <= self.min_population:
            return
        
        # Sort by fitness
        sorted_strategies = sorted(
            self.strategies.values(),
            key=lambda s: s.fitness,
            reverse=True
        )
        
        # Update hall of fame
        for strategy in sorted_strategies[:3]:
            if not self.hall_of_fame or strategy.fitness > self.hall_of_fame[0].fitness:
                self.hall_of_fame.insert(0, copy.deepcopy(strategy))
                self.hall_of_fame = self.hall_of_fame[:10]
        
        # Kill weakest if over population
        while len(self.strategies) > self.max_population:
            weakest = min(self.strategies.values(), key=lambda s: s.fitness)
            weakest.state = StrategyState.DEAD
            self._kill_strategy(weakest)
        
        # Breed best performers
        mature_strategies = [s for s in self.strategies.values() if s.can_reproduce()]
        if len(mature_strategies) >= 2 and len(self.strategies) < self.max_population:
            # Select parents
            parent1 = random.choice(mature_strategies[:max(2, len(mature_strategies) // 2)])
            parent2 = random.choice(mature_strategies[:max(2, len(mature_strategies) // 2)])
            
            if parent1.strategy_id != parent2.strategy_id:
                self.breed_strategies(parent1.strategy_id, parent2.strategy_id)
        
        # Ensure minimum population
        while len(self.strategies) < self.min_population:
            self.create_random_strategy()
        
        self.generation += 1
    
    def get_active_strategies(self) -> List[Strategy]:
        """Get all active (non-dead) strategies"""
        return [s for s in self.strategies.values() if s.state != StrategyState.DEAD]
    
    def get_mature_strategies(self) -> List[Strategy]:
        """Get all mature strategies ready for live trading"""
        return [s for s in self.strategies.values() if s.state == StrategyState.MATURE]
    
    def get_best_strategy(self) -> Optional[Strategy]:
        """Get the best performing strategy"""
        active = self.get_active_strategies()
        if not active:
            return None
        return max(active, key=lambda s: s.fitness)
    
    def get_report(self) -> Dict[str, Any]:
        """Get factory status report"""
        strategies_by_state = {}
        for state in StrategyState:
            strategies_by_state[state.value] = len([
                s for s in self.strategies.values() if s.state == state
            ])
        
        strategies_by_type = {}
        for strategy in self.strategies.values():
            stype = strategy.dna.strategy_type.value
            strategies_by_type[stype] = strategies_by_type.get(stype, 0) + 1
        
        return {
            'generation': self.generation,
            'total_created': self.total_created,
            'total_died': self.total_died,
            'current_population': len(self.strategies),
            'strategies_by_state': strategies_by_state,
            'strategies_by_type': strategies_by_type,
            'hall_of_fame_size': len(self.hall_of_fame),
            'best_fitness': max((s.fitness for s in self.strategies.values()), default=0),
            'avg_fitness': sum(s.fitness for s in self.strategies.values()) / len(self.strategies) if self.strategies else 0,
            'graveyard_size': len(self.graveyard),
        }


# Factory function
def create_strategy_factory(config: Optional[Dict[str, Any]] = None) -> StrategyFactory:
    """Create and initialize strategy factory"""
    factory = StrategyFactory(config)
    
    # Create initial population
    for blueprint_id in factory.blueprints:
        for _ in range(3):
            factory.create_strategy(blueprint_id)
    
    return factory

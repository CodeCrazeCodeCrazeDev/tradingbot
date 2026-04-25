"""
Evolutionary Strategy Engine
============================

Genetic programming for discovering novel indicator combinations.

Genome = Tree of indicators and operators
Fitness = Sharpe * (1 - max_drawdown) * win_rate
Selection = Tournament selection
Crossover = Subtree crossover
Mutation = Point/Subtree mutation
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random
import numpy as np
import logging

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of nodes in strategy genome tree."""
    INDICATOR = "indicator"
    OPERATOR = "operator"
    CONSTANT = "constant"
    THRESHOLD = "threshold"


@dataclass
class TreeNode:
    """Node in strategy tree."""
    node_type: NodeType
    value: str
    params: Dict[str, Any] = field(default_factory=dict)
    children: List['TreeNode'] = field(default_factory=list)
    
    def evaluate(self, market_data: Dict[str, Any]) -> float:
        """Evaluate node given market data."""
        if self.node_type == NodeType.CONSTANT:
            return float(self.value)
        
        if self.node_type == NodeType.INDICATOR:
            # Get indicator value from market data
            indicator_name = self.value
            return market_data.get(indicator_name, 0.0)
        
        if self.node_type == NodeType.OPERATOR:
            # Evaluate children
            child_values = [child.evaluate(market_data) for child in self.children]
            
            if self.value == 'ADD':
                return sum(child_values) if child_values else 0.0
            elif self.value == 'SUBTRACT':
                return child_values[0] - child_values[1] if len(child_values) >= 2 else 0.0
            elif self.value == 'MULTIPLY':
                result = 1.0
                for v in child_values:
                    result *= v
                return result
            elif self.value == 'DIVIDE':
                return child_values[0] / child_values[1] if len(child_values) >= 2 and child_values[1] != 0 else 0.0
            elif self.value == 'GT':  # Greater than
                return 1.0 if len(child_values) >= 2 and child_values[0] > child_values[1] else 0.0
            elif self.value == 'LT':  # Less than
                return 1.0 if len(child_values) >= 2 and child_values[0] < child_values[1] else 0.0
            elif self.value == 'AND':
                return 1.0 if all(v > 0.5 for v in child_values) else 0.0
            elif self.value == 'OR':
                return 1.0 if any(v > 0.5 for v in child_values) else 0.0
        
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'node_type': self.node_type.value,
            'value': self.value,
            'params': self.params,
            'children': [child.to_dict() for child in self.children],
        }
    
    def copy(self) -> 'TreeNode':
        """Deep copy of node."""
        return TreeNode(
            node_type=self.node_type,
            value=self.value,
            params=self.params.copy(),
            children=[child.copy() for child in self.children],
        )
    
    def get_depth(self) -> int:
        """Get depth of tree."""
        if not self.children:
            return 1
        return 1 + max(child.get_depth() for child in self.children)
    
    def get_size(self) -> int:
        """Get number of nodes in tree."""
        if not self.children:
            return 1
        return 1 + sum(child.get_size() for child in self.children)


@dataclass
class StrategyGenome:
    """Genetic representation of a trading strategy."""
    genome_id: str
    signal_tree: TreeNode
    entry_threshold: float = 0.5
    exit_threshold: float = 0.3
    position_size: float = 1.0
    
    # Performance metrics
    fitness: float = 0.0
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    
    creation_timestamp: datetime = field(default_factory=datetime.now)
    generation: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'genome_id': self.genome_id,
            'signal_tree': self.signal_tree.to_dict(),
            'entry_threshold': self.entry_threshold,
            'exit_threshold': self.exit_threshold,
            'position_size': self.position_size,
            'fitness': self.fitness,
            'sharpe': self.sharpe,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'generation': self.generation,
        }
    
    def generate_signal(self, market_data: Dict[str, Any]) -> float:
        """
        Generate trading signal from market data.
        
        Returns:
            Signal value between -1 and 1
        """
        raw_signal = self.signal_tree.evaluate(market_data)
        # Normalize to -1 to 1
        return np.tanh(raw_signal)


class EvolutionaryStrategyEngine:
    """
    Genetic programming engine for discovering novel trading strategies.
    
    Evolves populations of strategy genomes over generations to find
    high-performing indicator combinations.
    """
    
    def __init__(self,
                 population_size: int = 100,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.7,
                 max_generations: int = 100,
                 tournament_size: int = 5):
        """
        Initialize evolutionary engine.
        
        Args:
            population_size: Size of population
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
            max_generations: Maximum generations to evolve
            tournament_size: Tournament selection size
        """
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.max_generations = max_generations
        self.tournament_size = tournament_size
        
        self.population: List[StrategyGenome] = []
        self.best_genome: Optional[StrategyGenome] = None
        self.generation_history: List[Dict[str, float]] = []
        
        # Available indicators and operators
        self.indicators = [
            'sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26', 'rsi', 'macd',
            'bb_upper', 'bb_lower', 'volume', 'volatility', 'momentum',
            'price', 'returns', 'atr', 'obv', 'adx', 'stoch_k', 'stoch_d'
        ]
        self.operators = ['ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'GT', 'LT', 'AND', 'OR']
        
        logger.info(f"EvolutionaryStrategyEngine initialized (pop={population_size})")
    
    def evolve_population(self, 
                         market_data: List[Dict[str, Any]],
                         generations: int = 100) -> List[StrategyGenome]:
        """
        Evolve population over generations.
        
        Args:
            market_data: Historical market data for fitness evaluation
            generations: Number of generations to evolve
            
        Returns:
            Final evolved population
        """
        logger.info(f"Evolving population for {generations} generations")
        
        # Initialize population
        self._initialize_population()
        
        for gen in range(generations):
            # Evaluate fitness
            self._evaluate_population(market_data)
            
            # Track best
            gen_best = max(self.population, key=lambda g: g.fitness)
            if self.best_genome is None or gen_best.fitness > self.best_genome.fitness:
                self.best_genome = gen_best
            
            self.generation_history.append({
                'generation': gen,
                'best_fitness': gen_best.fitness,
                'avg_fitness': np.mean([g.fitness for g in self.population]),
            })
            
            if gen % 10 == 0:
                logger.info(f"Generation {gen}: Best fitness = {gen_best.fitness:.4f}")
            
            # Create next generation
            new_population = []
            
            # Elitism: Keep best 10%
            sorted_pop = sorted(self.population, key=lambda g: g.fitness, reverse=True)
            elite_count = max(1, self.population_size // 10)
            new_population.extend(sorted_pop[:elite_count])
            
            # Fill rest with offspring
            while len(new_population) < self.population_size:
                parent1 = self._tournament_selection()
                parent2 = self._tournament_selection()
                
                # Crossover
                if random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                
                # Mutation
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)
                
                child1.generation = gen + 1
                child2.generation = gen + 1
                
                new_population.extend([child1, child2])
            
            self.population = new_population[:self.population_size]
        
        # Final evaluation
        self._evaluate_population(market_data)
        
        logger.info(f"Evolution complete. Best fitness: {self.best_genome.fitness:.4f}")
        
        return sorted(self.population, key=lambda g: g.fitness, reverse=True)
    
    def _initialize_population(self):
        """Create initial random population."""
        self.population = []
        for i in range(self.population_size):
            genome = self._create_random_genome(f"genome_{i}")
            self.population.append(genome)
    
    def _create_random_genome(self, genome_id: str) -> StrategyGenome:
        """Create a random strategy genome."""
        # Create random signal tree
        tree = self._create_random_tree(depth=0, max_depth=3)
        
        return StrategyGenome(
            genome_id=genome_id,
            signal_tree=tree,
            entry_threshold=random.uniform(0.3, 0.7),
            exit_threshold=random.uniform(0.2, 0.4),
            position_size=random.uniform(0.5, 1.0),
        )
    
    def _create_random_tree(self, depth: int, max_depth: int) -> TreeNode:
        """Create a random tree node."""
        if depth >= max_depth:
            # Leaf node: indicator or constant
            if random.random() < 0.7:
                return TreeNode(
                    node_type=NodeType.INDICATOR,
                    value=random.choice(self.indicators),
                )
            else:
                return TreeNode(
                    node_type=NodeType.CONSTANT,
                    value=str(random.uniform(-1, 1)),
                )
        
        # Internal node: operator
        operator = random.choice(self.operators)
        
        # Create children
        num_children = 2 if operator in ['ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'GT', 'LT'] else random.randint(2, 3)
        children = [self._create_random_tree(depth + 1, max_depth) for _ in range(num_children)]
        
        return TreeNode(
            node_type=NodeType.OPERATOR,
            value=operator,
            children=children,
        )
    
    def _evaluate_population(self, market_data: List[Dict[str, Any]]):
        """Evaluate fitness of all genomes."""
        for genome in self.population:
            fitness_metrics = self._fitness_function(genome, market_data)
            genome.fitness = fitness_metrics['fitness']
            genome.sharpe = fitness_metrics['sharpe']
            genome.max_drawdown = fitness_metrics['max_drawdown']
            genome.win_rate = fitness_metrics['win_rate']
    
    def _fitness_function(self, genome: StrategyGenome, 
                         market_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate fitness for a genome.
        
        Fitness = Sharpe * (1 - max_drawdown) * win_rate
        """
        if len(market_data) < 2:
            return {'fitness': 0, 'sharpe': 0, 'max_drawdown': 1, 'win_rate': 0}
        
        # Simulate trading
        signals = [genome.generate_signal(data) for data in market_data]
        
        # Calculate returns (simplified: signal * next return)
        returns = []
        position = 0
        
        for i in range(len(signals) - 1):
            # Entry/exit logic
            if abs(signals[i]) > genome.entry_threshold and position == 0:
                position = 1 if signals[i] > 0 else -1
            elif abs(signals[i]) < genome.exit_threshold and position != 0:
                position = 0
            
            # Calculate return
            next_return = (market_data[i + 1].get('price', 0) - market_data[i].get('price', 0)) / market_data[i].get('price', 1)
            trade_return = position * next_return
            returns.append(trade_return)
        
        if not returns:
            return {'fitness': 0, 'sharpe': 0, 'max_drawdown': 1, 'win_rate': 0}
        
        # Calculate metrics
        total_return = sum(returns)
        sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
        
        # Calculate drawdown
        cumulative = np.cumsum(returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = (peak - cumulative) / (peak + 1e-8)
        max_dd = np.max(drawdown) if len(drawdown) > 0 else 0
        
        win_rate = sum(1 for r in returns if r > 0) / len(returns)
        
        # Combined fitness
        fitness = sharpe * (1 - max_dd) * win_rate
        
        return {
            'fitness': max(0, fitness),
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
        }
    
    def _tournament_selection(self) -> StrategyGenome:
        """Select genome using tournament selection."""
        tournament = random.sample(self.population, min(self.tournament_size, len(self.population)))
        return max(tournament, key=lambda g: g.fitness)
    
    def _crossover(self, parent1: StrategyGenome, parent2: StrategyGenome) -> Tuple[StrategyGenome, StrategyGenome]:
        """Perform subtree crossover between two parents."""
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        # Swap random subtrees
        if random.random() < 0.5:
            # Pick random nodes to swap
            nodes1 = self._get_all_nodes(child1.signal_tree)
            nodes2 = self._get_all_nodes(child2.signal_tree)
            
            if nodes1 and nodes2:
                node1 = random.choice(nodes1)
                node2 = random.choice(nodes2)
                
                # Swap values
                node1.value, node2.value = node2.value, node1.value
                node1.node_type, node2.node_type = node2.node_type, node1.node_type
        
        return child1, child2
    
    def _mutate(self, genome: StrategyGenome) -> StrategyGenome:
        """Mutate a genome."""
        if random.random() > self.mutation_rate:
            return genome
        
        mutated = genome.copy()
        
        # Mutate tree structure
        nodes = self._get_all_nodes(mutated.signal_tree)
        if nodes and random.random() < 0.5:
            node = random.choice(nodes)
            
            if node.node_type == NodeType.INDICATOR:
                node.value = random.choice(self.indicators)
            elif node.node_type == NodeType.CONSTANT:
                node.value = str(random.uniform(-1, 1))
            elif node.node_type == NodeType.OPERATOR:
                node.value = random.choice(self.operators)
        
        # Mutate thresholds
        if random.random() < 0.3:
            mutated.entry_threshold = np.clip(mutated.entry_threshold + random.uniform(-0.1, 0.1), 0.1, 0.9)
        if random.random() < 0.3:
            mutated.exit_threshold = np.clip(mutated.exit_threshold + random.uniform(-0.1, 0.1), 0.1, 0.5)
        
        return mutated
    
    def _get_all_nodes(self, node: TreeNode) -> List[TreeNode]:
        """Get all nodes in tree."""
        nodes = [node]
        for child in node.children:
            nodes.extend(self._get_all_nodes(child))
        return nodes
    
    def get_best_strategies(self, n: int = 10) -> List[StrategyGenome]:
        """Get top N strategies by fitness."""
        sorted_pop = sorted(self.population, key=lambda g: g.fitness, reverse=True)
        return sorted_pop[:n]

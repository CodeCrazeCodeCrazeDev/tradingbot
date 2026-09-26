"""
Self-Evolving Meta-Learning Intelligence
AlphaFold-inspired self-discovery and strategy evolution
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
from collections import deque
import random
import hashlib
import numpy
import pandas

logger = logging.getLogger(__name__)


class EvolutionPhase(Enum):
    """Evolution lifecycle phases"""
    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"
    MUTATION = "mutation"
    SELECTION = "selection"
    CROSSOVER = "crossover"


@dataclass
class AlphaSignal:
    """Novel alpha signal discovered by system"""
    signal_id: str
    formula: str
    features: List[str]
    performance_metrics: Dict[str, float]
    sharpe_ratio: float
    win_rate: float
    regime_validity: Dict[str, float]  # Regime -> performance
    discovery_timestamp: datetime = field(default_factory=datetime.now)
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)


@dataclass
class StrategyGene:
    """Strategy component (gene) for genetic algorithm"""
    gene_id: str
    gene_type: str  # entry, exit, filter, sizing
    code: str
    parameters: Dict[str, Any]
    fitness: float = 0.0
    age: int = 0


@dataclass
class TradingStrategy:
    """Complete trading strategy (organism)"""
    strategy_id: str
    genes: List[StrategyGene]
    performance: Dict[str, float]
    fitness_score: float
    generation: int
    parents: List[str] = field(default_factory=list)
    mutations: int = 0


@dataclass
class EvolutionMetrics:
    """Metrics tracking evolution progress"""
    generation: int
    population_size: int
    best_fitness: float
    avg_fitness: float
    diversity_score: float
    innovation_rate: float
    timestamp: datetime = field(default_factory=datetime.now)


class SymbolicRegressor:
    """Discover mathematical relationships via symbolic regression"""
    
    def __init__(self, max_complexity: int = 10):
        self.max_complexity = max_complexity
        self.operators = ['+', '-', '*', '/', 'log', 'exp', 'sqrt', 'abs']
        self.discovered_formulas: List[str] = []
        
    def discover_relationship(self, X: np.ndarray, y: np.ndarray,
                             feature_names: List[str]) -> Optional[str]:
        """Discover mathematical relationship between X and y"""
        
        best_formula = None
        best_score = float('inf')
        
        # Try random formula combinations
        for _ in range(1000):
            formula = self._generate_random_formula(feature_names)
            
            try:
                # Evaluate formula
                predicted = self._evaluate_formula(formula, X, feature_names)
                
                # Calculate error
                error = np.mean((predicted - y) ** 2)
                
                if error < best_score:
                    best_score = error
                    best_formula = formula
                    
            except Exception:
                continue
        
        if best_formula and best_score < 1.0:  # Threshold for acceptance
            self.discovered_formulas.append(best_formula)
            return best_formula
        
        return None
    
    def _generate_random_formula(self, features: List[str]) -> str:
        """Generate random mathematical formula"""
        
        complexity = random.randint(1, self.max_complexity)
        
        # Start with a feature
        formula = random.choice(features)
        
        for _ in range(complexity):
            op = random.choice(self.operators)
            
            if op in ['+', '-', '*', '/']:
                # Binary operator
                operand = random.choice(features + [str(random.uniform(-10, 10))])
                formula = f"({formula} {op} {operand})"
            else:
                # Unary operator
                formula = f"{op}({formula})"
        
        return formula
    
    def _evaluate_formula(self, formula: str, X: np.ndarray, 
                         feature_names: List[str]) -> np.ndarray:
        """Evaluate formula on data"""
        
        # Create namespace with features
        namespace = {}
        for i, name in enumerate(feature_names):
            namespace[name] = X[:, i]
        
        # Add math functions
        namespace.update({
            'log': np.log,
            'exp': np.exp,
            'sqrt': np.sqrt,
            'abs': np.abs
        })
        
        # Evaluate
        result = eval(formula, {"__builtins__": {}}, namespace)
        
        return np.array(result)


class GeneticAlgorithm:
    """Genetic algorithm for strategy evolution"""
    
    def __init__(self, population_size: int = 100, 
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.7):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        self.population: List[TradingStrategy] = []
        self.generation = 0
        self.evolution_history: List[EvolutionMetrics] = []
        
    def initialize_population(self, gene_pool: List[StrategyGene]):
        """Initialize random population"""
        
        self.population = []
        
        for i in range(self.population_size):
            # Randomly select genes
            n_genes = random.randint(3, 8)
            genes = random.sample(gene_pool, min(n_genes, len(gene_pool)))
            
            strategy = TradingStrategy(
                strategy_id=self._generate_id(),
                genes=genes,
                performance={},
                fitness_score=0.0,
                generation=0
            )
            
            self.population.append(strategy)
    
    def evolve_generation(self, fitness_function: Callable) -> EvolutionMetrics:
        """Evolve one generation"""
        
        # Evaluate fitness
        for strategy in self.population:
            strategy.fitness_score = fitness_function(strategy)
        
        # Sort by fitness
        self.population.sort(key=lambda s: s.fitness_score, reverse=True)
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        # Selection
        survivors = self._selection()
        
        # Crossover
        offspring = self._crossover(survivors)
        
        # Mutation
        mutants = self._mutation(offspring)
        
        # New population
        self.population = survivors + offspring + mutants
        self.population = self.population[:self.population_size]
        
        self.generation += 1
        self.evolution_history.append(metrics)
        
        return metrics
    
    def _selection(self) -> List[TradingStrategy]:
        """Select best strategies (elitism + tournament)"""
        
        # Elitism: Keep top 10%
        elite_count = max(1, self.population_size // 10)
        elite = self.population[:elite_count]
        
        # Tournament selection for rest
        tournament_size = 5
        selected = []
        
        for _ in range(self.population_size // 3):
            tournament = random.sample(self.population, tournament_size)
            winner = max(tournament, key=lambda s: s.fitness_score)
            selected.append(winner)
        
        return elite + selected
    
    def _crossover(self, parents: List[TradingStrategy]) -> List[TradingStrategy]:
        """Create offspring via crossover"""
        
        offspring = []
        
        for _ in range(self.population_size // 3):
            if random.random() < self.crossover_rate and len(parents) >= 2:
                # Select two parents
                parent1, parent2 = random.sample(parents, 2)
                
                # Crossover genes
                crossover_point = random.randint(1, min(len(parent1.genes), len(parent2.genes)) - 1)
                
                child_genes = parent1.genes[:crossover_point] + parent2.genes[crossover_point:]
                
                child = TradingStrategy(
                    strategy_id=self._generate_id(),
                    genes=child_genes,
                    performance={},
                    fitness_score=0.0,
                    generation=self.generation + 1,
                    parents=[parent1.strategy_id, parent2.strategy_id]
                )
                
                offspring.append(child)
        
        return offspring
    
    def _mutation(self, strategies: List[TradingStrategy]) -> List[TradingStrategy]:
        """Mutate strategies"""
        
        mutants = []
        
        for strategy in strategies:
            if random.random() < self.mutation_rate:
                # Create mutant
                mutant_genes = strategy.genes.copy()
                
                # Mutate random gene
                if mutant_genes:
                    gene_idx = random.randint(0, len(mutant_genes) - 1)
                    mutant_genes[gene_idx] = self._mutate_gene(mutant_genes[gene_idx])
                
                mutant = TradingStrategy(
                    strategy_id=self._generate_id(),
                    genes=mutant_genes,
                    performance={},
                    fitness_score=0.0,
                    generation=self.generation + 1,
                    parents=[strategy.strategy_id],
                    mutations=strategy.mutations + 1
                )
                
                mutants.append(mutant)
        
        return mutants
    
    def _mutate_gene(self, gene: StrategyGene) -> StrategyGene:
        """Mutate a single gene"""
        
        mutated = StrategyGene(
            gene_id=self._generate_id(),
            gene_type=gene.gene_type,
            code=gene.code,
            parameters=gene.parameters.copy()
        )
        
        # Mutate parameters
        for param, value in mutated.parameters.items():
            if isinstance(value, (int, float)):
                # Add random noise
                noise = random.gauss(0, abs(value) * 0.1)
                mutated.parameters[param] = value + noise
        
        return mutated
    
    def _calculate_metrics(self) -> EvolutionMetrics:
        """Calculate evolution metrics"""
        
        fitnesses = [s.fitness_score for s in self.population]
        
        # Diversity: Unique gene combinations
        gene_signatures = set()
        for strategy in self.population:
            signature = tuple(sorted(g.gene_id for g in strategy.genes))
            gene_signatures.add(signature)
        
        diversity = len(gene_signatures) / len(self.population)
        
        # Innovation: New strategies this generation
        new_strategies = sum(1 for s in self.population if s.generation == self.generation)
        innovation_rate = new_strategies / len(self.population)
        
        return EvolutionMetrics(
            generation=self.generation,
            population_size=len(self.population),
            best_fitness=max(fitnesses) if fitnesses else 0.0,
            avg_fitness=np.mean(fitnesses) if fitnesses else 0.0,
            diversity_score=diversity,
            innovation_rate=innovation_rate
        )
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        return hashlib.md5(f"{datetime.now()}{random.random()}".encode()).hexdigest()[:12]
    
    def get_best_strategy(self) -> Optional[TradingStrategy]:
        """Get best performing strategy"""
        if self.population:
            return max(self.population, key=lambda s: s.fitness_score)
        return None


class FeatureEngineer:
    """Automated feature engineering"""
    
    def __init__(self):
        self.feature_library: Dict[str, Callable] = {}
        self.performance_tracker: Dict[str, float] = {}
        
    def generate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate engineered features"""
        
        features = data.copy()
        
        # Technical transformations
        for col in data.columns:
            if data[col].dtype in [np.float64, np.int64]:
                # Rolling statistics
                features[f'{col}_ma_10'] = data[col].rolling(10).mean()
                features[f'{col}_ma_50'] = data[col].rolling(50).mean()
                features[f'{col}_std_10'] = data[col].rolling(10).std()
                
                # Momentum
                features[f'{col}_momentum_5'] = data[col].pct_change(5)
                features[f'{col}_momentum_20'] = data[col].pct_change(20)
                
                # Z-score
                mean = data[col].rolling(20).mean()
                std = data[col].rolling(20).std()
                features[f'{col}_zscore'] = (data[col] - mean) / std
        
        # Interaction features
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            col1, col2 = random.sample(list(numeric_cols), 2)
            features[f'{col1}_div_{col2}'] = features[col1] / (features[col2] + 1e-8)
            features[f'{col1}_mul_{col2}'] = features[col1] * features[col2]
        
        return features.fillna(0)
    
    def test_feature_combinations(self, features: pd.DataFrame, 
                                  target: pd.Series,
                                  n_combinations: int = 100) -> List[Tuple[List[str], float]]:
        """Test random feature combinations"""
        
        results = []
        feature_cols = [c for c in features.columns if c != target.name]
        
        for _ in range(n_combinations):
            # Random feature subset
            n_features = random.randint(3, min(10, len(feature_cols)))
            selected = random.sample(feature_cols, n_features)
            
            # Simple correlation-based score
            X = features[selected].values
            y = target.values
            
            # Remove NaN
            mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
            X = X[mask]
            y = y[mask]
            
            if len(X) > 10:
                # Calculate correlation
                correlations = [np.corrcoef(X[:, i], y)[0, 1] for i in range(X.shape[1])]
                score = np.mean(np.abs(correlations))
                
                results.append((selected, score))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:10]  # Top 10


class SelfEvolvingIntelligence:
    """
    Complete self-evolving intelligence system
    """
    
    def __init__(self):
        self.symbolic_regressor = SymbolicRegressor()
        self.genetic_algorithm = GeneticAlgorithm()
        self.feature_engineer = FeatureEngineer()
        
        self.discovered_alphas: List[AlphaSignal] = []
        self.gene_pool: List[StrategyGene] = []
        
    def discover_new_indicators(self, data: pd.DataFrame, 
                               target: pd.Series) -> List[str]:
        """Discover new technical indicators"""
        
        discovered = []
        
        # Generate features
        features = self.feature_engineer.generate_features(data)
        
        # Test combinations
        best_combinations = self.feature_engineer.test_feature_combinations(
            features, target, n_combinations=50
        )
        
        for feature_set, score in best_combinations[:5]:
            if score > 0.3:  # Threshold
                # Try to find formula
                X = features[feature_set].values
                y = target.values
                
                # Remove NaN
                mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
                X = X[mask]
                y = y[mask]
                
                if len(X) > 100:
                    formula = self.symbolic_regressor.discover_relationship(
                        X, y, feature_set
                    )
                    
                    if formula:
                        discovered.append(formula)
                        logger.info(f"Discovered new indicator: {formula}")
        
        return discovered
    
    def evolve_strategies(self, n_generations: int = 10,
                         fitness_function: Optional[Callable] = None) -> List[EvolutionMetrics]:
        """Evolve trading strategies"""
        
        if not self.gene_pool:
            self._initialize_gene_pool()
        
        if not self.genetic_algorithm.population:
            self.genetic_algorithm.initialize_population(self.gene_pool)
        
        if fitness_function is None:
            fitness_function = self._default_fitness_function
        
        metrics_history = []
        
        for gen in range(n_generations):
            metrics = self.genetic_algorithm.evolve_generation(fitness_function)
            metrics_history.append(metrics)
            
            logger.info(f"Generation {gen}: Best fitness = {metrics.best_fitness:.4f}, "
                       f"Diversity = {metrics.diversity_score:.2f}")
        
        return metrics_history
    
    def _initialize_gene_pool(self):
        """Initialize gene pool with basic strategy components"""
        
        # Entry genes
        self.gene_pool.append(StrategyGene(
            gene_id="entry_ma_cross",
            gene_type="entry",
            code="fast_ma > slow_ma",
            parameters={'fast_period': 10, 'slow_period': 50}
        ))
        
        self.gene_pool.append(StrategyGene(
            gene_id="entry_rsi",
            gene_type="entry",
            code="rsi < oversold",
            parameters={'period': 14, 'oversold': 30}
        ))
        
        # Exit genes
        self.gene_pool.append(StrategyGene(
            gene_id="exit_profit_target",
            gene_type="exit",
            code="profit > target",
            parameters={'target': 0.02}
        ))
        
        self.gene_pool.append(StrategyGene(
            gene_id="exit_stop_loss",
            gene_type="exit",
            code="loss > stop",
            parameters={'stop': 0.01}
        ))
        
        # Filter genes
        self.gene_pool.append(StrategyGene(
            gene_id="filter_volatility",
            gene_type="filter",
            code="volatility < threshold",
            parameters={'threshold': 0.02}
        ))
        
        # Sizing genes
        self.gene_pool.append(StrategyGene(
            gene_id="sizing_kelly",
            gene_type="sizing",
            code="kelly_criterion",
            parameters={'fraction': 0.25}
        ))
    
    def _default_fitness_function(self, strategy: TradingStrategy) -> float:
        """Default fitness function (Sharpe ratio)"""
        
        # Simulate performance (in production, backtest the strategy)
        returns = np.random.randn(252) * 0.01  # Simulated daily returns
        
        sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
        
        return max(sharpe, 0.0)
    
    def get_best_strategies(self, n: int = 5) -> List[TradingStrategy]:
        """Get top N strategies"""
        
        if not self.genetic_algorithm.population:
            return []
        
        sorted_pop = sorted(self.genetic_algorithm.population, 
                           key=lambda s: s.fitness_score, 
                           reverse=True)
        
        return sorted_pop[:n]
    
    def continuous_evolution(self, data_stream: Any) -> Dict[str, Any]:
        """Continuous evolution loop"""
        
        # Discover new indicators
        # (In production, this would use real-time data)
        
        # Evolve strategies
        metrics = self.evolve_strategies(n_generations=1)
        
        # Get best strategy
        best = self.genetic_algorithm.get_best_strategy()
        
        return {
            'generation': self.genetic_algorithm.generation,
            'best_strategy': best,
            'metrics': metrics[-1] if metrics else None,
            'population_size': len(self.genetic_algorithm.population)
        }


# Example usage
if __name__ == "__main__":
    # Initialize system
    intelligence = SelfEvolvingIntelligence()
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=500, freq='D')
    data = pd.DataFrame({
        'price': 100 + np.cumsum(np.random.randn(500) * 0.5),
        'volume': np.random.randint(1000, 10000, 500),
        'volatility': np.random.rand(500) * 0.02
    }, index=dates)
    
    target = data['price'].pct_change().shift(-1)  # Next day return
    
    logger.info(f"\n{'='*80}")
    logger.info(f"SELF-EVOLVING INTELLIGENCE SYSTEM")
    logger.info(f"{'='*80}")
    
    # Discover new indicators
    logger.info(f"\nDiscovering new indicators...")
    indicators = intelligence.discover_new_indicators(data, target)
    logger.info(f"Discovered {len(indicators)} new indicators")
    for ind in indicators:
        logger.info(f"  • {ind}")
    
    # Evolve strategies
    logger.info(f"\nEvolving strategies...")
    metrics_history = intelligence.evolve_strategies(n_generations=5)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"EVOLUTION PROGRESS")
    logger.info(f"{'='*80}")
    
    for metrics in metrics_history:
        logger.info(f"\nGeneration {metrics.generation}:")
        logger.info(f"  Best Fitness: {metrics.best_fitness:.4f}")
        logger.info(f"  Avg Fitness: {metrics.avg_fitness:.4f}")
        logger.info(f"  Diversity: {metrics.diversity_score:.2%}")
        logger.info(f"  Innovation Rate: {metrics.innovation_rate:.2%}")
    
    # Get best strategies
    best_strategies = intelligence.get_best_strategies(n=3)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TOP 3 STRATEGIES")
    logger.info(f"{'='*80}")
    
    for i, strategy in enumerate(best_strategies, 1):
        logger.info(f"\n{i}. Strategy {strategy.strategy_id}")
        logger.info(f"   Fitness: {strategy.fitness_score:.4f}")
        logger.info(f"   Generation: {strategy.generation}")
        logger.info(f"   Mutations: {strategy.mutations}")
        logger.info(f"   Genes: {len(strategy.genes)}")
        for gene in strategy.genes:
            logger.info(f"     • {gene.gene_type}: {gene.code}")

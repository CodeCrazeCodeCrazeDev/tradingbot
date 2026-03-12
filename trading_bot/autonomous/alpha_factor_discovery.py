"""
Auto-Generated Alpha Factor Discovery System
Uses genetic programming and ML to discover new trading signals
"""

import numpy as np
import pandas as pd
import copy
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import random
import operator
import math

logger = logging.getLogger(__name__)


@dataclass
class AlphaFactor:
    """Discovered alpha factor"""
    name: str
    expression: str
    function: Callable
    sharpe_ratio: float
    information_coefficient: float
    turnover: float
    fitness_score: float
    generation: int
    timestamp: datetime
    feature_importance: Dict[str, float] = field(default_factory=dict)
    

class GeneticProgramming:
    """
    Genetic programming for alpha factor discovery
    Evolves mathematical expressions that predict returns
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Genetic algorithm parameters
        self.population_size = self.config.get('population_size', 100)
        self.generations = self.config.get('generations', 50)
        self.mutation_rate = self.config.get('mutation_rate', 0.2)
        self.crossover_rate = self.config.get('crossover_rate', 0.7)
        self.tournament_size = self.config.get('tournament_size', 5)
        
        # Function set
        self.functions = {
            'add': operator.add,
            'sub': operator.sub,
            'mul': operator.mul,
            'div': self._protected_div,
            'log': self._protected_log,
            'sqrt': self._protected_sqrt,
            'abs': abs,
            'max': max,
            'min': min,
            'rank': self._rank,
            'ts_mean': self._ts_mean,
            'ts_std': self._ts_std,
            'ts_corr': self._ts_corr,
            'delta': self._delta,
        }
        
        # Terminal set (features)
        self.terminals = [
            'open', 'high', 'low', 'close', 'volume',
            'returns', 'volatility', 'rsi', 'macd', 'bb_upper', 'bb_lower'
        ]
        
        # Population
        self.population: List[Dict] = []
        self.best_factors: List[AlphaFactor] = []
        self.generation = 0
        
        logger.info("Genetic programming initialized")
        
    @staticmethod
    def _protected_div(a, b):
        """Protected division"""
        try:
            return a / b if abs(b) > 1e-10 else 0
        except Exception:
            return 0
            
    @staticmethod
    def _protected_log(x):
        """Protected logarithm"""
        try:
            return math.log(abs(x)) if abs(x) > 1e-10 else 0
        except Exception:
            return 0
            
    @staticmethod
    def _protected_sqrt(x):
        """Protected square root"""
        try:
            return math.sqrt(abs(x))
        except Exception:
            return 0
            
    @staticmethod
    def _rank(x):
        """Rank transformation"""
        if isinstance(x, (list, np.ndarray, pd.Series)):
            return pd.Series(x).rank(pct=True).values
        return 0
        
    @staticmethod
    def _ts_mean(x, window=20):
        """Time series mean"""
        if isinstance(x, (list, np.ndarray, pd.Series)):
            return pd.Series(x).rolling(window).mean().values
        return x
        
    @staticmethod
    def _ts_std(x, window=20):
        """Time series standard deviation"""
        if isinstance(x, (list, np.ndarray, pd.Series)):
            return pd.Series(x).rolling(window).std().values
        return 0
        
    @staticmethod
    def _ts_corr(x, y, window=20):
        """Time series correlation"""
        if isinstance(x, (list, np.ndarray, pd.Series)) and isinstance(y, (list, np.ndarray, pd.Series)):
            return pd.Series(x).rolling(window).corr(pd.Series(y)).values
        return 0
        
    @staticmethod
    def _delta(x, period=1):
        """Delta (difference)"""
        if isinstance(x, (list, np.ndarray, pd.Series)):
            return pd.Series(x).diff(period).values
        return 0
        
    def generate_random_expression(self, max_depth: int = 5) -> Dict:
        """Generate random expression tree"""
        if max_depth == 0 or (max_depth < 5 and random.random() < 0.3):
            # Terminal node
            return {
                'type': 'terminal',
                'value': random.choice(self.terminals)
            }
        else:
            # Function node
            func_name = random.choice(list(self.functions.keys()))
            func = self.functions[func_name]
            
            # Determine number of arguments
            if func_name in ['add', 'sub', 'mul', 'div', 'max', 'min', 'ts_corr']:
                n_args = 2
            else:
                n_args = 1
                
            return {
                'type': 'function',
                'name': func_name,
                'args': [self.generate_random_expression(max_depth - 1) for _ in range(n_args)]
            }
            
    def expression_to_string(self, expr: Dict) -> str:
        """Convert expression tree to string"""
        if expr['type'] == 'terminal':
            return expr['value']
        else:
            args_str = ', '.join([self.expression_to_string(arg) for arg in expr['args']])
            return f"{expr['name']}({args_str})"
            
    def evaluate_expression(self, expr: Dict, data: pd.DataFrame) -> np.ndarray:
        """Evaluate expression on data"""
        try:
            if expr['type'] == 'terminal':
                if expr['value'] in data.columns:
                    return data[expr['value']].values
                else:
                    return np.zeros(len(data))
            else:
                func = self.functions[expr['name']]
                args = [self.evaluate_expression(arg, data) for arg in expr['args']]
                
                # Handle different argument counts
                if len(args) == 1:
                    result = func(args[0])
                elif len(args) == 2:
                    result = func(args[0], args[1])
                else:
                    result = func(*args)
                    
                # Ensure result is array
                if not isinstance(result, np.ndarray):
                    result = np.full(len(data), result)
                    
                return result
        except Exception as e:
            logger.debug(f"Expression evaluation error: {e}")
            return np.zeros(len(data))
            
    def calculate_fitness(self, expr: Dict, data: pd.DataFrame, returns: pd.Series) -> float:
        """
        Calculate fitness of expression
        Higher is better
        """
        try:
            # Evaluate expression
            signal = self.evaluate_expression(expr, data)
            
            # Remove NaN values
            mask = ~(np.isnan(signal) | np.isnan(returns.values))
            signal = signal[mask]
            returns_clean = returns.values[mask]
            
            if len(signal) < 100:
                return 0.0
                
            # Calculate information coefficient (IC)
            ic = np.corrcoef(signal, returns_clean)[0, 1]
            if np.isnan(ic):
                ic = 0
                
            # Calculate Sharpe ratio of signal-weighted returns
            signal_normalized = (signal - np.mean(signal)) / (np.std(signal) + 1e-10)
            strategy_returns = signal_normalized * returns_clean
            
            sharpe = np.mean(strategy_returns) / (np.std(strategy_returns) + 1e-10) * np.sqrt(252)
            
            # Calculate turnover (penalize high turnover)
            turnover = np.mean(np.abs(np.diff(signal_normalized)))
            
            # Composite fitness
            fitness = (
                abs(ic) * 0.4 +
                max(sharpe, 0) * 0.4 -
                turnover * 0.2
            )
            
            return fitness
            
        except Exception as e:
            logger.debug(f"Fitness calculation error: {e}")
            return 0.0
            
    def tournament_selection(self, fitnesses: List[float]) -> int:
        """Tournament selection"""
        tournament = random.sample(range(len(self.population)), self.tournament_size)
        tournament_fitnesses = [fitnesses[i] for i in tournament]
        winner_idx = tournament[np.argmax(tournament_fitnesses)]
        return winner_idx
        
    def crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Crossover two expression trees"""
        # Deep copy
        child = copy.deepcopy(parent1)
        
        # Find random nodes to swap
        def get_random_node(expr, nodes=[]):
            nodes.append(expr)
            if expr['type'] == 'function':
                for arg in expr['args']:
                    get_random_node(arg, nodes)
            return nodes
            
        nodes1 = get_random_node(child)
        nodes2 = get_random_node(parent2)
        
        if len(nodes1) > 0 and len(nodes2) > 0:
            # Swap random nodes
            node1 = random.choice(nodes1)
            node2 = random.choice(nodes2)
            
            # Replace node1 with node2
            for key in list(node1.keys()):
                del node1[key]
            for key, value in copy.deepcopy(node2).items():
                node1[key] = value
                
        return child
        
    def mutate(self, expr: Dict) -> Dict:
        """Mutate expression tree"""
        mutated = copy.deepcopy(expr)
        
        # Random mutation type
        mutation_type = random.choice(['terminal', 'function', 'subtree'])
        
        if mutation_type == 'terminal' and mutated['type'] == 'terminal':
            mutated['value'] = random.choice(self.terminals)
        elif mutation_type == 'function' and mutated['type'] == 'function':
            mutated['name'] = random.choice(list(self.functions.keys()))
        elif mutation_type == 'subtree':
            mutated = self.generate_random_expression()
            
        return mutated
        
    def evolve(self, data: pd.DataFrame, returns: pd.Series) -> AlphaFactor:
        """
        Evolve population to discover alpha factors
        """
        logger.info(f"Starting evolution for {self.generations} generations...")
        
        # Initialize population
        if len(self.population) == 0:
            self.population = [
                self.generate_random_expression() for _ in range(self.population_size)
            ]
            
        best_fitness = 0
        best_expr = None
        
        for gen in range(self.generations):
            # Evaluate fitness
            fitnesses = [
                self.calculate_fitness(expr, data, returns) 
                for expr in self.population
            ]
            
            # Track best
            max_fitness_idx = np.argmax(fitnesses)
            if fitnesses[max_fitness_idx] > best_fitness:
                best_fitness = fitnesses[max_fitness_idx]
                best_expr = self.population[max_fitness_idx]
                logger.info(f"Gen {gen}: New best fitness = {best_fitness:.4f}")
                
            # Create new population
            new_population = []
            
            # Elitism: keep best individuals
            elite_size = int(0.1 * self.population_size)
            elite_indices = np.argsort(fitnesses)[-elite_size:]
            new_population.extend([self.population[i] for i in elite_indices])
            
            # Generate offspring
            while len(new_population) < self.population_size:
                # Selection
                parent1_idx = self.tournament_selection(fitnesses)
                parent2_idx = self.tournament_selection(fitnesses)
                
                # Crossover
                if random.random() < self.crossover_rate:
                    child = self.crossover(
                        self.population[parent1_idx],
                        self.population[parent2_idx]
                    )
                else:
                    child = copy.deepcopy(self.population[parent1_idx])
                    
                # Mutation
                if random.random() < self.mutation_rate:
                    child = self.mutate(child)
                    
                new_population.append(child)
                
            self.population = new_population
            self.generation = gen + 1
            
        # Create alpha factor from best expression
        if best_expr is not None:
            signal = self.evaluate_expression(best_expr, data)
            mask = ~(np.isnan(signal) | np.isnan(returns.values))
            
            ic = np.corrcoef(signal[mask], returns.values[mask])[0, 1] if np.sum(mask) > 0 else 0
            signal_norm = (signal - np.mean(signal)) / (np.std(signal) + 1e-10)
            strategy_returns = signal_norm * returns.values
            sharpe = np.mean(strategy_returns) / (np.std(strategy_returns) + 1e-10) * np.sqrt(252)
            turnover = np.mean(np.abs(np.diff(signal_norm)))
            
            alpha_factor = AlphaFactor(
                name=f"GP_Alpha_{self.generation}",
                expression=self.expression_to_string(best_expr),
                function=lambda df: self.evaluate_expression(best_expr, df),
                sharpe_ratio=sharpe,
                information_coefficient=ic,
                turnover=turnover,
                fitness_score=best_fitness,
                generation=self.generation,
                timestamp=datetime.now()
            )
            
            self.best_factors.append(alpha_factor)
            logger.info(f"Discovered alpha factor: {alpha_factor.expression}")
            logger.info(f"Sharpe: {sharpe:.4f}, IC: {ic:.4f}, Turnover: {turnover:.4f}")
            
            return alpha_factor
            
        return None

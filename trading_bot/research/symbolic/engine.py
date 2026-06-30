"""
Symbolic Equation Discovery - AlphaAlgo Research
Uses genetic programming principles to discover new trading invariants.
"""

import numpy as np
import logging
from typing import List, Dict, Any, Callable, Union, Tuple
import operator
import random
import math

logger = logging.getLogger(__name__)

class Node:
    """A node in the symbolic expression tree."""
    def __init__(self, value: Any, name: str, children: List['Node'] = None):
        self.value = value
        self.name = name
        self.children = children or []

    def evaluate(self, context: Dict[str, np.ndarray]) -> np.ndarray:
        if not self.children:
            # Terminal node (feature or constant)
            if isinstance(self.value, str):
                return context.get(self.value, np.zeros_like(next(iter(context.values()))))
            return np.full_like(next(iter(context.values())), self.value)

        # Function node
        child_results = [child.evaluate(context) for child in self.children]
        return self.value(*child_results)

    def get_complexity(self) -> int:
        return 1 + sum(child.get_complexity() for child in self.children)

    def to_string(self) -> str:
        if not self.children:
            return str(self.value)
        return f"{self.name}({', '.join(c.to_string() for c in self.children)})"

class SymbolicDiscovery:
    """
    Symbolic Regression engine for discovering trading alpha.
    Implements a real Genetic Programming (GP) evolution loop.
    """
    def __init__(self, population_size: int = 50, max_generations: int = 10):
        self.population_size = population_size
        self.max_generations = max_generations

        self.operators = {
            'add': (operator.add, 2),
            'sub': (operator.sub, 2),
            'mul': (operator.mul, 2),
            'div': (lambda x, y: np.divide(x, y, out=np.zeros_like(x), where=y!=0), 2),
            'sin': (np.sin, 1),
            'abs': (np.abs, 1),
            'sqrt': (lambda x: np.sqrt(np.abs(x)), 1),
            'log': (lambda x: np.log(np.abs(x) + 1e-6), 1)
        }

        self.terminals = ['price_change', 'volatility', 'volume_z_score', 'rsi', 'momentum']
        self.population: List[Node] = []
        self.alpha_library: List[Dict[str, Any]] = []

    def _random_tree(self, depth: int) -> Node:
        """Generate a random symbolic tree."""
        if depth <= 0 or random.random() < 0.3:
            # Terminal
            val = random.choice(self.terminals + [random.uniform(-1, 1)])
            return Node(val, str(val))

        op_name = random.choice(list(self.operators.keys()))
        op_func, arity = self.operators[op_name]
        children = [self._random_tree(depth - 1) for _ in range(arity)]

        return Node(op_func, op_name, children)

    async def discover_invariant(self, data: Dict[str, np.ndarray], target: np.ndarray) -> str:
        """
        Main GP loop to evolve alpha equations.
        """
        logger.info("Initializing GP population of size %d", self.population_size)
        self.population = [self._random_tree(3) for _ in range(self.population_size)]

        best_overall = None
        best_fitness = -float('inf')

        for gen in range(self.max_generations):
            fitness_scores = []
            for individual in self.population:
                fitness = self.evaluate_fitness(individual, data, target)
                fitness_scores.append(fitness)

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_overall = individual

            logger.info("Generation %d: Best Fitness = %.4f", gen, best_fitness)

            # Selection and Evolution
            new_population = [best_overall] # Elitism
            while len(new_population) < self.population_size:
                # Tournament Selection
                p1 = self._tournament_selection(self.population, fitness_scores)
                p2 = self._tournament_selection(self.population, fitness_scores)

                # Splicing / Crossover (Advanced Frontier)
                if random.random() < 0.3:
                    child = self._crossover(p1, p2)
                else:
                    # Mutation (Simplified subtree replacement)
                    child = self._mutate(p1)

                new_population.append(child)

            self.population = new_population

        if best_overall:
            equation = best_overall.to_string()
            self.alpha_library.append({
                'equation': equation,
                'fitness': best_fitness,
                'complexity': best_overall.get_complexity()
            })
            return equation

        return "0"

    def _tournament_selection(self, population, scores, k=3) -> Node:
        idx = random.sample(range(len(population)), k)
        best_idx = max(idx, key=lambda i: scores[i])
        return population[best_idx]

    def _mutate(self, node: Node) -> Node:
        """Simple point mutation / subtree replacement."""
        if random.random() < 0.2:
            return self._random_tree(2)

        if not node.children:
            return node

        # Recursive mutation
        new_children = [self._mutate(c) for c in node.children]
        return Node(node.value, node.name, new_children)

    def _crossover(self, p1: Node, p2: Node) -> Node:
        """Crossover / Gene Splicing between two symbolic trees."""
        if not p1.children or not p2.children:
            return p1 # No nodes to swap

        # Swap a random child
        idx = random.randrange(len(p1.children))
        target_idx = random.randrange(len(p2.children))

        new_children = list(p1.children)
        new_children[idx] = p2.children[target_idx]

        return Node(p1.value, p1.name, new_children)

    def evaluate_fitness(self, node: Node, data: Dict[str, np.ndarray], target: np.ndarray) -> float:
        """
        Multi-objective fitness evaluation.
        Fitness = Sharpe - (0.01 * Complexity)
        """
        try:
            prediction = node.evaluate(data)

            # Sharpe proxy: mean / std
            returns = prediction * target
            std = np.std(returns)
            sharpe = np.mean(returns) / (std + 1e-6) * np.sqrt(252)

            complexity = node.get_complexity()
            penalty = 0.05 * complexity # Complexity penalty

            return sharpe - penalty
        except Exception as e:
            return -10.0

    def get_library(self) -> List[Dict[str, Any]]:
        return sorted(self.alpha_library, key=lambda x: x['fitness'], reverse=True)

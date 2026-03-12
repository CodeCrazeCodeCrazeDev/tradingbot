"""
Neural Architecture Search (NAS) for Strategy Evolution
========================================================

Automatically discovers optimal neural network architectures
for trading strategies using evolutionary algorithms.
"""

import asyncio
import hashlib
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable
import numpy as np

logger = logging.getLogger(__name__)


class LayerType(Enum):
    """Types of neural network layers"""
    DENSE = "dense"
    LSTM = "lstm"
    GRU = "gru"
    CONV1D = "conv1d"
    ATTENTION = "attention"
    TRANSFORMER = "transformer"
    DROPOUT = "dropout"
    BATCH_NORM = "batch_norm"
    RESIDUAL = "residual"
    SKIP_CONNECTION = "skip_connection"


class ActivationType(Enum):
    """Activation functions"""
    RELU = "relu"
    LEAKY_RELU = "leaky_relu"
    ELU = "elu"
    SELU = "selu"
    TANH = "tanh"
    SIGMOID = "sigmoid"
    SWISH = "swish"
    GELU = "gelu"
    MISH = "mish"
    SOFTMAX = "softmax"


@dataclass
class LayerConfig:
    """Configuration for a single layer"""
    layer_type: LayerType
    units: int = 64
    activation: ActivationType = ActivationType.RELU
    dropout_rate: float = 0.0
    kernel_size: int = 3
    num_heads: int = 4
    use_bias: bool = True
    regularization: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'layer_type': self.layer_type.value,
            'units': self.units,
            'activation': self.activation.value,
            'dropout_rate': self.dropout_rate,
            'kernel_size': self.kernel_size,
            'num_heads': self.num_heads,
            'use_bias': self.use_bias,
            'regularization': self.regularization
        }


@dataclass
class Architecture:
    """Neural network architecture specification"""
    architecture_id: str
    layers: List[LayerConfig]
    input_shape: Tuple[int, ...]
    output_shape: Tuple[int, ...]
    optimizer: str = "adam"
    learning_rate: float = 0.001
    batch_size: int = 32
    fitness: float = 0.0
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_complexity(self) -> int:
        """Calculate architecture complexity (parameter count estimate)"""
        total_params = 0
        prev_units = self.input_shape[-1] if self.input_shape else 64
        
        for layer in self.layers:
            if layer.layer_type in [LayerType.DENSE, LayerType.LSTM, LayerType.GRU]:
                total_params += prev_units * layer.units
                if layer.layer_type in [LayerType.LSTM, LayerType.GRU]:
                    total_params *= 4 if layer.layer_type == LayerType.LSTM else 3
                prev_units = layer.units
            elif layer.layer_type == LayerType.CONV1D:
                total_params += layer.kernel_size * prev_units * layer.units
                prev_units = layer.units
            elif layer.layer_type == LayerType.ATTENTION:
                total_params += prev_units * prev_units * 3  # Q, K, V
            elif layer.layer_type == LayerType.TRANSFORMER:
                total_params += prev_units * prev_units * 4 * layer.num_heads
        
        return total_params
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'architecture_id': self.architecture_id,
            'layers': [l.to_dict() for l in self.layers],
            'input_shape': self.input_shape,
            'output_shape': self.output_shape,
            'optimizer': self.optimizer,
            'learning_rate': self.learning_rate,
            'batch_size': self.batch_size,
            'fitness': self.fitness,
            'generation': self.generation,
            'complexity': self.get_complexity()
        }


@dataclass
class SearchSpace:
    """Defines the search space for NAS"""
    min_layers: int = 2
    max_layers: int = 10
    layer_types: List[LayerType] = field(default_factory=lambda: list(LayerType))
    min_units: int = 16
    max_units: int = 512
    activations: List[ActivationType] = field(default_factory=lambda: list(ActivationType))
    dropout_range: Tuple[float, float] = (0.0, 0.5)
    learning_rate_range: Tuple[float, float] = (1e-5, 1e-2)
    batch_sizes: List[int] = field(default_factory=lambda: [16, 32, 64, 128, 256])
    optimizers: List[str] = field(default_factory=lambda: ["adam", "sgd", "rmsprop", "adamw"])


class EvolutionaryNAS:
    """
    Evolutionary Neural Architecture Search
    
    Uses genetic algorithms to evolve optimal neural network
    architectures for trading strategies.
    """
    
    def __init__(
        self,
        search_space: Optional[SearchSpace] = None,
        population_size: int = 50,
        elite_ratio: float = 0.1,
        mutation_rate: float = 0.3,
        crossover_rate: float = 0.7,
        tournament_size: int = 5
    ):
        self.search_space = search_space or SearchSpace()
        self.population_size = population_size
        self.elite_ratio = elite_ratio
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        
        self.population: List[Architecture] = []
        self.generation = 0
        self.best_architecture: Optional[Architecture] = None
        self.history: List[Dict[str, Any]] = []
        
        logger.info("EvolutionaryNAS initialized")
    
    def _generate_random_architecture(
        self,
        input_shape: Tuple[int, ...],
        output_shape: Tuple[int, ...]
    ) -> Architecture:
        """Generate a random architecture within search space"""
        
        num_layers = random.randint(
            self.search_space.min_layers,
            self.search_space.max_layers
        )
        
        layers = []
        for i in range(num_layers):
            layer_type = random.choice(self.search_space.layer_types)
            
            # Skip certain layer types for first/last layers
            if i == 0 and layer_type in [LayerType.DROPOUT, LayerType.BATCH_NORM]:
                layer_type = LayerType.DENSE
            
            units = random.randint(
                self.search_space.min_units,
                self.search_space.max_units
            )
            # Round to nearest power of 2 for efficiency
            units = 2 ** round(np.log2(units))
            
            activation = random.choice(self.search_space.activations)
            dropout_rate = random.uniform(*self.search_space.dropout_range)
            
            layer = LayerConfig(
                layer_type=layer_type,
                units=units,
                activation=activation,
                dropout_rate=dropout_rate if layer_type != LayerType.DROPOUT else dropout_rate,
                kernel_size=random.choice([3, 5, 7]),
                num_heads=random.choice([2, 4, 8]),
                regularization=random.uniform(0, 0.01)
            )
            layers.append(layer)
        
        # Generate unique ID
        arch_id = hashlib.sha256(
            f"{datetime.utcnow().isoformat()}:{random.random()}".encode()
        ).hexdigest()[:12]
        
        return Architecture(
            architecture_id=arch_id,
            layers=layers,
            input_shape=input_shape,
            output_shape=output_shape,
            optimizer=random.choice(self.search_space.optimizers),
            learning_rate=10 ** random.uniform(
                np.log10(self.search_space.learning_rate_range[0]),
                np.log10(self.search_space.learning_rate_range[1])
            ),
            batch_size=random.choice(self.search_space.batch_sizes),
            generation=self.generation
        )
    
    def initialize_population(
        self,
        input_shape: Tuple[int, ...],
        output_shape: Tuple[int, ...]
    ):
        """Initialize random population"""
        
        self.population = []
        for _ in range(self.population_size):
            arch = self._generate_random_architecture(input_shape, output_shape)
            self.population.append(arch)
        
        logger.info(f"Initialized population with {len(self.population)} architectures")
    
    def _tournament_selection(self) -> Architecture:
        """Select parent using tournament selection"""
        
        tournament = random.sample(self.population, min(self.tournament_size, len(self.population)))
        return max(tournament, key=lambda x: x.fitness)
    
    def _crossover(self, parent1: Architecture, parent2: Architecture) -> Architecture:
        """Create offspring through crossover"""
        
        if random.random() > self.crossover_rate:
            return self._mutate(parent1 if random.random() > 0.5 else parent2)
        
        # Single-point crossover on layers
        crossover_point = random.randint(1, min(len(parent1.layers), len(parent2.layers)) - 1)
        
        new_layers = parent1.layers[:crossover_point] + parent2.layers[crossover_point:]
        
        # Inherit hyperparameters from random parent
        hp_parent = parent1 if random.random() > 0.5 else parent2
        
        arch_id = hashlib.sha256(
            f"{datetime.utcnow().isoformat()}:{random.random()}".encode()
        ).hexdigest()[:12]
        
        child = Architecture(
            architecture_id=arch_id,
            layers=new_layers,
            input_shape=parent1.input_shape,
            output_shape=parent1.output_shape,
            optimizer=hp_parent.optimizer,
            learning_rate=hp_parent.learning_rate,
            batch_size=hp_parent.batch_size,
            generation=self.generation,
            parent_ids=[parent1.architecture_id, parent2.architecture_id]
        )
        
        return self._mutate(child)
    
    def _mutate(self, architecture: Architecture) -> Architecture:
        """Apply mutations to architecture"""
        
        if random.random() > self.mutation_rate:
            return architecture
        
        # Create a copy
        new_layers = [LayerConfig(**{
            'layer_type': l.layer_type,
            'units': l.units,
            'activation': l.activation,
            'dropout_rate': l.dropout_rate,
            'kernel_size': l.kernel_size,
            'num_heads': l.num_heads,
            'use_bias': l.use_bias,
            'regularization': l.regularization
        }) for l in architecture.layers]
        
        mutation_type = random.choice([
            'add_layer', 'remove_layer', 'modify_layer',
            'change_units', 'change_activation', 'change_hyperparams'
        ])
        
        if mutation_type == 'add_layer' and len(new_layers) < self.search_space.max_layers:
            insert_pos = random.randint(0, len(new_layers))
            new_layer = LayerConfig(
                layer_type=random.choice(self.search_space.layer_types),
                units=2 ** random.randint(4, 9),
                activation=random.choice(self.search_space.activations),
                dropout_rate=random.uniform(*self.search_space.dropout_range)
            )
            new_layers.insert(insert_pos, new_layer)
        
        elif mutation_type == 'remove_layer' and len(new_layers) > self.search_space.min_layers:
            remove_pos = random.randint(0, len(new_layers) - 1)
            new_layers.pop(remove_pos)
        
        elif mutation_type == 'modify_layer' and new_layers:
            idx = random.randint(0, len(new_layers) - 1)
            new_layers[idx] = LayerConfig(
                layer_type=random.choice(self.search_space.layer_types),
                units=new_layers[idx].units,
                activation=new_layers[idx].activation,
                dropout_rate=new_layers[idx].dropout_rate
            )
        
        elif mutation_type == 'change_units' and new_layers:
            idx = random.randint(0, len(new_layers) - 1)
            new_layers[idx].units = 2 ** random.randint(4, 9)
        
        elif mutation_type == 'change_activation' and new_layers:
            idx = random.randint(0, len(new_layers) - 1)
            new_layers[idx].activation = random.choice(self.search_space.activations)
        
        # Create mutated architecture
        new_lr = architecture.learning_rate
        new_bs = architecture.batch_size
        new_opt = architecture.optimizer
        
        if mutation_type == 'change_hyperparams':
            if random.random() > 0.5:
                new_lr = 10 ** random.uniform(
                    np.log10(self.search_space.learning_rate_range[0]),
                    np.log10(self.search_space.learning_rate_range[1])
                )
            if random.random() > 0.5:
                new_bs = random.choice(self.search_space.batch_sizes)
            if random.random() > 0.5:
                new_opt = random.choice(self.search_space.optimizers)
        
        arch_id = hashlib.sha256(
            f"{datetime.utcnow().isoformat()}:{random.random()}".encode()
        ).hexdigest()[:12]
        
        return Architecture(
            architecture_id=arch_id,
            layers=new_layers,
            input_shape=architecture.input_shape,
            output_shape=architecture.output_shape,
            optimizer=new_opt,
            learning_rate=new_lr,
            batch_size=new_bs,
            generation=self.generation,
            parent_ids=[architecture.architecture_id]
        )
    
    async def evaluate_architecture(
        self,
        architecture: Architecture,
        fitness_function: Callable[[Architecture], float]
    ) -> float:
        """Evaluate architecture fitness"""
        
        try:
            fitness = fitness_function(architecture)
            architecture.fitness = fitness
            return fitness
        except Exception as e:
            logger.error(f"Error evaluating architecture {architecture.architecture_id}: {e}")
            architecture.fitness = 0.0
            return 0.0
    
    async def evolve_generation(
        self,
        fitness_function: Callable[[Architecture], float]
    ) -> Architecture:
        """Evolve one generation"""
        
        self.generation += 1
        
        # Evaluate all architectures
        for arch in self.population:
            if arch.fitness == 0.0:
                await self.evaluate_architecture(arch, fitness_function)
        
        # Sort by fitness
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Update best
        if self.population and (
            self.best_architecture is None or
            self.population[0].fitness > self.best_architecture.fitness
        ):
            self.best_architecture = self.population[0]
        
        # Record history
        self.history.append({
            'generation': self.generation,
            'best_fitness': self.population[0].fitness if self.population else 0,
            'avg_fitness': np.mean([a.fitness for a in self.population]) if self.population else 0,
            'best_architecture': self.population[0].architecture_id if self.population else None
        })
        
        # Elite selection
        elite_count = max(1, int(self.population_size * self.elite_ratio))
        new_population = self.population[:elite_count]
        
        # Generate offspring
        while len(new_population) < self.population_size:
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()
            child = self._crossover(parent1, parent2)
            child.generation = self.generation
            new_population.append(child)
        
        self.population = new_population
        
        logger.info(
            f"Generation {self.generation}: "
            f"Best={self.population[0].fitness:.4f}, "
            f"Avg={np.mean([a.fitness for a in self.population]):.4f}"
        )
        
        return self.best_architecture
    
    async def search(
        self,
        input_shape: Tuple[int, ...],
        output_shape: Tuple[int, ...],
        fitness_function: Callable[[Architecture], float],
        num_generations: int = 50,
        early_stopping_patience: int = 10
    ) -> Architecture:
        """
        Run full NAS search
        
        Args:
            input_shape: Input tensor shape
            output_shape: Output tensor shape
            fitness_function: Function to evaluate architecture fitness
            num_generations: Maximum generations to run
            early_stopping_patience: Stop if no improvement for this many generations
        
        Returns:
            Best architecture found
        """
        
        logger.info(f"Starting NAS search for {num_generations} generations")
        
        # Initialize population
        self.initialize_population(input_shape, output_shape)
        
        best_fitness = 0.0
        patience_counter = 0
        
        for gen in range(num_generations):
            best_arch = await self.evolve_generation(fitness_function)
            
            if best_arch.fitness > best_fitness:
                best_fitness = best_arch.fitness
                patience_counter = 0
            else:
                patience_counter += 1
            
            if patience_counter >= early_stopping_patience:
                logger.info(f"Early stopping at generation {gen + 1}")
                break
        
        logger.info(
            f"NAS search complete. Best architecture: {self.best_architecture.architecture_id} "
            f"with fitness {self.best_architecture.fitness:.4f}"
        )
        
        return self.best_architecture
    
    def get_search_report(self) -> Dict[str, Any]:
        """Get comprehensive search report"""
        
        return {
            'generation': self.generation,
            'population_size': len(self.population),
            'best_architecture': self.best_architecture.to_dict() if self.best_architecture else None,
            'history': self.history[-20:],  # Last 20 generations
            'top_architectures': [
                a.to_dict() for a in sorted(
                    self.population, key=lambda x: x.fitness, reverse=True
                )[:5]
            ]
        }


class DARTSSearch:
    """
    Differentiable Architecture Search (DARTS)
    
    Uses gradient-based optimization for architecture search,
    much faster than evolutionary methods.
    """
    
    def __init__(
        self,
        search_space: Optional[SearchSpace] = None,
        architecture_lr: float = 0.001,
        weight_lr: float = 0.01
    ):
        self.search_space = search_space or SearchSpace()
        self.architecture_lr = architecture_lr
        self.weight_lr = weight_lr
        
        # Architecture parameters (alpha)
        self.alpha: Dict[str, np.ndarray] = {}
        
        logger.info("DARTSSearch initialized")
    
    def _initialize_alpha(self, num_layers: int):
        """Initialize architecture parameters"""
        
        num_ops = len(self.search_space.layer_types)
        
        for i in range(num_layers):
            self.alpha[f'layer_{i}'] = np.zeros(num_ops)
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum()
    
    def get_architecture_weights(self) -> Dict[str, np.ndarray]:
        """Get current architecture weights (softmax of alpha)"""
        
        return {
            key: self._softmax(alpha)
            for key, alpha in self.alpha.items()
        }
    
    def derive_architecture(
        self,
        input_shape: Tuple[int, ...],
        output_shape: Tuple[int, ...]
    ) -> Architecture:
        """Derive discrete architecture from continuous relaxation"""
        
        layers = []
        
        for key in sorted(self.alpha.keys()):
            weights = self._softmax(self.alpha[key])
            best_op_idx = np.argmax(weights)
            best_op = list(self.search_space.layer_types)[best_op_idx]
            
            layer = LayerConfig(
                layer_type=best_op,
                units=64,  # Default
                activation=ActivationType.RELU
            )
            layers.append(layer)
        
        arch_id = hashlib.sha256(
            f"darts:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]
        
        return Architecture(
            architecture_id=arch_id,
            layers=layers,
            input_shape=input_shape,
            output_shape=output_shape
        )


class ProgressiveNAS:
    """
    Progressive Neural Architecture Search
    
    Starts with simple architectures and progressively
    increases complexity, more efficient than full search.
    """
    
    def __init__(
        self,
        search_space: Optional[SearchSpace] = None,
        initial_layers: int = 2,
        max_layers: int = 10,
        expansion_rate: int = 2
    ):
        self.search_space = search_space or SearchSpace()
        self.initial_layers = initial_layers
        self.max_layers = max_layers
        self.expansion_rate = expansion_rate
        
        self.current_depth = initial_layers
        self.best_architectures: List[Architecture] = []
        
        logger.info("ProgressiveNAS initialized")
    
    async def search(
        self,
        input_shape: Tuple[int, ...],
        output_shape: Tuple[int, ...],
        fitness_function: Callable[[Architecture], float],
        candidates_per_depth: int = 20
    ) -> Architecture:
        """Run progressive search"""
        
        logger.info("Starting progressive NAS search")
        
        # Start with simple architectures
        current_candidates = []
        
        while self.current_depth <= self.max_layers:
            logger.info(f"Searching at depth {self.current_depth}")
            
            # Generate candidates at current depth
            new_candidates = []
            
            if not current_candidates:
                # Initial candidates
                for _ in range(candidates_per_depth):
                    layers = []
                    for _ in range(self.current_depth):
                        layer = LayerConfig(
                            layer_type=random.choice(self.search_space.layer_types),
                            units=2 ** random.randint(5, 8),
                            activation=random.choice(self.search_space.activations)
                        )
                        layers.append(layer)
                    
                    arch_id = hashlib.sha256(
                        f"prog:{datetime.utcnow().isoformat()}:{random.random()}".encode()
                    ).hexdigest()[:12]
                    
                    arch = Architecture(
                        architecture_id=arch_id,
                        layers=layers,
                        input_shape=input_shape,
                        output_shape=output_shape
                    )
                    new_candidates.append(arch)
            else:
                # Expand best candidates
                for parent in current_candidates[:self.expansion_rate]:
                    for _ in range(candidates_per_depth // self.expansion_rate):
                        new_layers = list(parent.layers)
                        
                        # Add new layer
                        new_layer = LayerConfig(
                            layer_type=random.choice(self.search_space.layer_types),
                            units=2 ** random.randint(5, 8),
                            activation=random.choice(self.search_space.activations)
                        )
                        insert_pos = random.randint(0, len(new_layers))
                        new_layers.insert(insert_pos, new_layer)
                        
                        arch_id = hashlib.sha256(
                            f"prog:{datetime.utcnow().isoformat()}:{random.random()}".encode()
                        ).hexdigest()[:12]
                        
                        arch = Architecture(
                            architecture_id=arch_id,
                            layers=new_layers,
                            input_shape=input_shape,
                            output_shape=output_shape,
                            parent_ids=[parent.architecture_id]
                        )
                        new_candidates.append(arch)
            
            # Evaluate candidates
            for arch in new_candidates:
                try:
                    arch.fitness = fitness_function(arch)
                except Exception as e:
                    logger.error(f"Error evaluating: {e}")
                    arch.fitness = 0.0
            
            # Select best
            new_candidates.sort(key=lambda x: x.fitness, reverse=True)
            current_candidates = new_candidates[:self.expansion_rate]
            self.best_architectures.extend(current_candidates)
            
            logger.info(
                f"Depth {self.current_depth}: Best fitness = {current_candidates[0].fitness:.4f}"
            )
            
            self.current_depth += 1
        
        # Return overall best
        self.best_architectures.sort(key=lambda x: x.fitness, reverse=True)
        return self.best_architectures[0]


# Convenience functions
def create_nas_searcher(
    method: str = "evolutionary",
    **kwargs
) -> Any:
    """Create NAS searcher by method name"""
    
    if method == "evolutionary":
        return EvolutionaryNAS(**kwargs)
    elif method == "darts":
        return DARTSSearch(**kwargs)
    elif method == "progressive":
        return ProgressiveNAS(**kwargs)
    else:
        raise ValueError(f"Unknown NAS method: {method}")


async def quick_nas_search(
    input_shape: Tuple[int, ...],
    output_shape: Tuple[int, ...],
    fitness_function: Callable[[Architecture], float],
    method: str = "evolutionary",
    num_generations: int = 20
) -> Architecture:
    """Quick NAS search with default settings"""
    
    searcher = create_nas_searcher(method)
    
    if method == "evolutionary":
        return await searcher.search(
            input_shape, output_shape, fitness_function,
            num_generations=num_generations
        )
    elif method == "progressive":
        return await searcher.search(
            input_shape, output_shape, fitness_function
        )
    else:
        raise ValueError(f"Quick search not supported for method: {method}")


def create_nas_optimizer(method: str = "evolutionary", **kwargs) -> Any:
    """
    Create a NAS optimizer instance.
    
    Args:
        method: NAS method - "evolutionary", "darts", or "progressive"
        **kwargs: Additional arguments for the optimizer
        
    Returns:
        NAS optimizer instance
    """
    return create_nas_searcher(method, **kwargs)

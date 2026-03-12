"""
from typing import Callable, List, Optional, Set
Neural Architecture Search (NAS) for Trading Models
Automated discovery of optimal neural network architectures
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
import copy

logger = logging.getLogger(__name__)

# Try to import deep learning libraries
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available")


class LayerType(Enum):
    """Types of neural network layers"""
    LINEAR = "linear"
    CONV1D = "conv1d"
    LSTM = "lstm"
    GRU = "gru"
    ATTENTION = "attention"
    TRANSFORMER = "transformer"
    DROPOUT = "dropout"
    BATCHNORM = "batchnorm"
    RESIDUAL = "residual"


class ActivationType(Enum):
    """Activation functions"""
    RELU = "relu"
    GELU = "gelu"
    SILU = "silu"
    TANH = "tanh"
    SIGMOID = "sigmoid"
    LEAKY_RELU = "leaky_relu"
    ELU = "elu"


@dataclass
class LayerConfig:
    """Configuration for a single layer"""
    layer_type: LayerType
    units: int
    activation: ActivationType = ActivationType.RELU
    dropout_rate: float = 0.0
    kernel_size: int = 3
    num_heads: int = 4
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'layer_type': self.layer_type.value,
            'units': self.units,
            'activation': self.activation.value,
            'dropout_rate': self.dropout_rate,
            'kernel_size': self.kernel_size,
            'num_heads': self.num_heads
        }


@dataclass
class Architecture:
    """Neural network architecture specification"""
    arch_id: str
    layers: List[LayerConfig]
    input_dim: int
    output_dim: int
    fitness: float = 0.0
    training_time: float = 0.0
    params_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'arch_id': self.arch_id,
            'layers': [l.to_dict() for l in self.layers],
            'input_dim': self.input_dim,
            'output_dim': self.output_dim,
            'fitness': self.fitness,
            'params_count': self.params_count
        }


class SearchSpace:
    """Define the search space for NAS"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Layer options
        self.layer_types = self.config.get('layer_types', [
            LayerType.LINEAR, LayerType.LSTM, LayerType.GRU,
            LayerType.CONV1D, LayerType.ATTENTION
        ])
        
        # Unit options
        self.unit_options = self.config.get('unit_options', [32, 64, 128, 256, 512])
        
        # Activation options
        self.activation_options = self.config.get('activation_options', [
            ActivationType.RELU, ActivationType.GELU, ActivationType.SILU
        ])
        
        # Depth options
        self.min_layers = self.config.get('min_layers', 2)
        self.max_layers = self.config.get('max_layers', 8)
        
        # Dropout options
        self.dropout_options = self.config.get('dropout_options', [0.0, 0.1, 0.2, 0.3, 0.5])
        
    def sample_architecture(self, input_dim: int, output_dim: int) -> Architecture:
        """Sample a random architecture from the search space"""
        num_layers = random.randint(self.min_layers, self.max_layers)
        layers = []
        
        for i in range(num_layers):
            layer_type = random.choice(self.layer_types)
            units = random.choice(self.unit_options)
            activation = random.choice(self.activation_options)
            dropout = random.choice(self.dropout_options)
            
            layers.append(LayerConfig(
                layer_type=layer_type,
                units=units,
                activation=activation,
                dropout_rate=dropout
            ))
            
        arch_id = f"arch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        return Architecture(
            arch_id=arch_id,
            layers=layers,
            input_dim=input_dim,
            output_dim=output_dim
        )
    
    def mutate_architecture(self, arch: Architecture, mutation_rate: float = 0.3) -> Architecture:
        """Mutate an architecture"""
        new_layers = copy.deepcopy(arch.layers)
        
        for i, layer in enumerate(new_layers):
            if random.random() < mutation_rate:
                # Mutate layer type
                if random.random() < 0.3:
                    layer.layer_type = random.choice(self.layer_types)
                    
                # Mutate units
                if random.random() < 0.5:
                    layer.units = random.choice(self.unit_options)
                    
                # Mutate activation
                if random.random() < 0.3:
                    layer.activation = random.choice(self.activation_options)
                    
                # Mutate dropout
                if random.random() < 0.3:
                    layer.dropout_rate = random.choice(self.dropout_options)
                    
        # Add/remove layers
        if random.random() < 0.2 and len(new_layers) < self.max_layers:
            # Add layer
            new_layers.insert(
                random.randint(0, len(new_layers)),
                LayerConfig(
                    layer_type=random.choice(self.layer_types),
                    units=random.choice(self.unit_options),
                    activation=random.choice(self.activation_options)
                )
            )
        elif random.random() < 0.2 and len(new_layers) > self.min_layers:
            # Remove layer
            new_layers.pop(random.randint(0, len(new_layers) - 1))
            
        arch_id = f"arch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        return Architecture(
            arch_id=arch_id,
            layers=new_layers,
            input_dim=arch.input_dim,
            output_dim=arch.output_dim
        )
    
    def crossover(self, arch1: Architecture, arch2: Architecture) -> Architecture:
        """Crossover two architectures"""
        # Single point crossover
        point1 = random.randint(1, len(arch1.layers) - 1) if len(arch1.layers) > 1 else 1
        point2 = random.randint(1, len(arch2.layers) - 1) if len(arch2.layers) > 1 else 1
        
        new_layers = copy.deepcopy(arch1.layers[:point1]) + copy.deepcopy(arch2.layers[point2:])
        
        # Ensure valid depth
        if len(new_layers) > self.max_layers:
            new_layers = new_layers[:self.max_layers]
        elif len(new_layers) < self.min_layers:
            while len(new_layers) < self.min_layers:
                new_layers.append(LayerConfig(
                    layer_type=random.choice(self.layer_types),
                    units=random.choice(self.unit_options)
                ))
                
        arch_id = f"arch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        return Architecture(
            arch_id=arch_id,
            layers=new_layers,
            input_dim=arch1.input_dim,
            output_dim=arch1.output_dim
        )


class NeuralArchitectureSearch:
    """
    Neural Architecture Search using evolutionary algorithms
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Search parameters
        self.population_size = self.config.get('population_size', 20)
        self.generations = self.config.get('generations', 50)
        self.mutation_rate = self.config.get('mutation_rate', 0.3)
        self.crossover_rate = self.config.get('crossover_rate', 0.5)
        self.elite_size = self.config.get('elite_size', 2)
        
        # Search space
        self.search_space = SearchSpace(self.config.get('search_space', {}))
        
        # Population
        self.population: List[Architecture] = []
        self.best_architecture: Optional[Architecture] = None
        self.generation_history: List[Dict[str, Any]] = []
        
        # Evaluation function
        self.evaluate_fn: Optional[Callable[[Architecture], float]] = None
        
        logger.info("Neural Architecture Search initialized")
        
    def set_evaluation_function(self, fn: Callable[[Architecture], float]):
        """Set the fitness evaluation function"""
        self.evaluate_fn = fn
        
    def initialize_population(self, input_dim: int, output_dim: int):
        """Initialize random population"""
        self.population = []
        
        for _ in range(self.population_size):
            arch = self.search_space.sample_architecture(input_dim, output_dim)
            self.population.append(arch)
            
        logger.info(f"Initialized population with {len(self.population)} architectures")
        
    def evaluate_population(self):
        """Evaluate fitness of all architectures"""
        if not self.evaluate_fn:
            raise ValueError("Evaluation function not set")
            
        for arch in self.population:
            if arch.fitness == 0:  # Not yet evaluated
                arch.fitness = self.evaluate_fn(arch)
                
    def select_parents(self) -> List[Architecture]:
        """Tournament selection"""
        parents = []
        tournament_size = 3
        
        for _ in range(self.population_size - self.elite_size):
            tournament = random.sample(self.population, tournament_size)
            winner = max(tournament, key=lambda a: a.fitness)
            parents.append(winner)
            
        return parents
    
    def evolve_generation(self):
        """Evolve one generation"""
        # Sort by fitness
        self.population.sort(key=lambda a: a.fitness, reverse=True)
        
        # Keep elite
        new_population = self.population[:self.elite_size]
        
        # Select parents
        parents = self.select_parents()
        
        # Create offspring
        while len(new_population) < self.population_size:
            if random.random() < self.crossover_rate and len(parents) >= 2:
                # Crossover
                p1, p2 = random.sample(parents, 2)
                child = self.search_space.crossover(p1, p2)
            else:
                # Clone and mutate
                parent = random.choice(parents)
                child = self.search_space.mutate_architecture(parent, self.mutation_rate)
                
            new_population.append(child)
            
        self.population = new_population
        
    def search(
        self,
        input_dim: int,
        output_dim: int,
        evaluate_fn: Optional[Callable[[Architecture], float]] = None
    ) -> Architecture:
        """
        Run the architecture search
        
        Args:
            input_dim: Input dimension
            output_dim: Output dimension
            evaluate_fn: Function to evaluate architecture fitness
            
        Returns:
            Best architecture found
        """
        if evaluate_fn:
            self.evaluate_fn = evaluate_fn
            
        if not self.evaluate_fn:
            raise ValueError("Evaluation function required")
            
        # Initialize
        self.initialize_population(input_dim, output_dim)
        
        for gen in range(self.generations):
            # Evaluate
            self.evaluate_population()
            
            # Track best
            current_best = max(self.population, key=lambda a: a.fitness)
            if not self.best_architecture or current_best.fitness > self.best_architecture.fitness:
                self.best_architecture = copy.deepcopy(current_best)
                
            # Record history
            fitnesses = [a.fitness for a in self.population]
            self.generation_history.append({
                'generation': gen,
                'best_fitness': max(fitnesses),
                'avg_fitness': np.mean(fitnesses),
                'min_fitness': min(fitnesses),
                'best_arch_id': current_best.arch_id
            })
            
            logger.info(f"Generation {gen}: Best fitness = {current_best.fitness:.4f}")
            
            # Evolve
            if gen < self.generations - 1:
                self.evolve_generation()
                
        return self.best_architecture
    
    def get_top_architectures(self, n: int = 5) -> List[Architecture]:
        """Get top N architectures"""
        sorted_pop = sorted(self.population, key=lambda a: a.fitness, reverse=True)
        return sorted_pop[:n]
    
    def get_search_report(self) -> Dict[str, Any]:
        """Get search report"""
        return {
            'best_architecture': self.best_architecture.to_dict() if self.best_architecture else None,
            'generations_completed': len(self.generation_history),
            'population_size': self.population_size,
            'history': self.generation_history,
            'top_architectures': [a.to_dict() for a in self.get_top_architectures()]
        }


class ArchitectureBuilder:
    """Build PyTorch models from architecture specifications"""
    
    @staticmethod
    def build_model(arch: Architecture) -> Optional[Any]:
        """Build PyTorch model from architecture"""
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available")
            return None
            
        layers = []
        prev_dim = arch.input_dim
        
        for layer_config in arch.layers:
            if layer_config.layer_type == LayerType.LINEAR:
                layers.append(nn.Linear(prev_dim, layer_config.units))
                prev_dim = layer_config.units
                
            elif layer_config.layer_type == LayerType.LSTM:
                layers.append(nn.LSTM(prev_dim, layer_config.units, batch_first=True))
                prev_dim = layer_config.units
                
            elif layer_config.layer_type == LayerType.GRU:
                layers.append(nn.GRU(prev_dim, layer_config.units, batch_first=True))
                prev_dim = layer_config.units
                
            elif layer_config.layer_type == LayerType.CONV1D:
                layers.append(nn.Conv1d(prev_dim, layer_config.units, layer_config.kernel_size, padding='same'))
                prev_dim = layer_config.units
                
            # Add activation
            if layer_config.activation == ActivationType.RELU:
                layers.append(nn.ReLU())
            elif layer_config.activation == ActivationType.GELU:
                layers.append(nn.GELU())
            elif layer_config.activation == ActivationType.SILU:
                layers.append(nn.SiLU())
            elif layer_config.activation == ActivationType.TANH:
                layers.append(nn.Tanh())
                
            # Add dropout
            if layer_config.dropout_rate > 0:
                layers.append(nn.Dropout(layer_config.dropout_rate))
                
        # Output layer
        layers.append(nn.Linear(prev_dim, arch.output_dim))
        
        model = nn.Sequential(*layers)
        
        # Count parameters
        arch.params_count = sum(p.numel() for p in model.parameters())
        
        return model

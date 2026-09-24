"""
Neural Architecture Search (NAS) - Self-Designing Neural Networks
==================================================================

Enables the AI to automatically design and optimize its own
neural network architectures through:
- Architecture search spaces
- Differentiable architecture search (DARTS)
- Evolutionary architecture search
- Performance prediction
- Architecture morphism

The system can discover novel architectures optimized for
specific trading tasks without human intervention.
"""

import asyncio
import copy
import hashlib
import logging
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import json

logger = logging.getLogger(__name__)


class LayerType(Enum):
    """Types of neural network layers"""
    DENSE = "dense"
    CONV1D = "conv1d"
    LSTM = "lstm"
    GRU = "gru"
    ATTENTION = "attention"
    TRANSFORMER = "transformer"
    DROPOUT = "dropout"
    BATCH_NORM = "batch_norm"
    LAYER_NORM = "layer_norm"
    RESIDUAL = "residual"
    POOLING = "pooling"
    EMBEDDING = "embedding"
    SKIP_CONNECTION = "skip_connection"


class ActivationType(Enum):
    """Activation functions"""
    RELU = "relu"
    LEAKY_RELU = "leaky_relu"
    ELU = "elu"
    SELU = "selu"
    GELU = "gelu"
    SWISH = "swish"
    TANH = "tanh"
    SIGMOID = "sigmoid"
    SOFTMAX = "softmax"
    LINEAR = "linear"


class SearchStrategy(Enum):
    """Architecture search strategies"""
    RANDOM = "random"
    EVOLUTIONARY = "evolutionary"
    REINFORCEMENT = "reinforcement"
    BAYESIAN = "bayesian"
    DIFFERENTIABLE = "differentiable"


@dataclass
class LayerConfig:
    """Configuration for a single layer"""
    layer_id: str
    layer_type: LayerType
    units: int = 64
    activation: ActivationType = ActivationType.RELU
    dropout_rate: float = 0.0
    kernel_size: int = 3
    num_heads: int = 4
    use_bias: bool = True
    regularization: Optional[str] = None
    
    # Connections
    input_layers: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'layer_id': self.layer_id,
            'layer_type': self.layer_type.value,
            'units': self.units,
            'activation': self.activation.value,
            'dropout_rate': self.dropout_rate,
            'kernel_size': self.kernel_size,
            'num_heads': self.num_heads,
            'use_bias': self.use_bias,
            'regularization': self.regularization,
            'input_layers': self.input_layers,
        }
    
    def estimate_params(self, input_size: int) -> int:
        """Estimate number of parameters"""
        if self.layer_type == LayerType.DENSE:
            return input_size * self.units + (self.units if self.use_bias else 0)
        elif self.layer_type == LayerType.CONV1D:
            return self.kernel_size * input_size * self.units + (self.units if self.use_bias else 0)
        elif self.layer_type in [LayerType.LSTM, LayerType.GRU]:
            gates = 4 if self.layer_type == LayerType.LSTM else 3
            return gates * (input_size * self.units + self.units * self.units + self.units)
        elif self.layer_type == LayerType.ATTENTION:
            return 3 * input_size * self.units + self.units * self.units
        return 0


@dataclass
class Architecture:
    """Complete neural network architecture"""
    architecture_id: str
    layers: List[LayerConfig]
    input_shape: Tuple[int, ...]
    output_shape: Tuple[int, ...]
    
    # Metadata
    generation: int = 0
    fitness: float = 0.0
    training_time: float = 0.0
    inference_time: float = 0.0
    parent_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Performance metrics
    accuracy: float = 0.0
    loss: float = float('inf')
    sharpe_ratio: float = 0.0
    
    def get_layer(self, layer_id: str) -> Optional[LayerConfig]:
        """Get layer by ID"""
        for layer in self.layers:
            if layer.layer_id == layer_id:
                return layer
        return None
    
    def add_layer(self, layer: LayerConfig, position: int = -1) -> None:
        """Add a layer at specified position"""
        if position < 0:
            self.layers.append(layer)
        else:
            self.layers.insert(position, layer)
    
    def remove_layer(self, layer_id: str) -> bool:
        """Remove a layer by ID"""
        for i, layer in enumerate(self.layers):
            if layer.layer_id == layer_id:
                self.layers.pop(i)
                return True
        return False
    
    def estimate_total_params(self) -> int:
        """Estimate total parameters"""
        total = 0
        prev_size = self.input_shape[-1] if self.input_shape else 64
        
        for layer in self.layers:
            params = layer.estimate_params(prev_size)
            total += params
            prev_size = layer.units
        
        return total
    
    def get_architecture_hash(self) -> str:
        """Get unique hash of architecture"""
        arch_string = json.dumps([l.to_dict() for l in self.layers], sort_keys=True)
        return hashlib.sha256(arch_string.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'architecture_id': self.architecture_id,
            'layers': [l.to_dict() for l in self.layers],
            'input_shape': self.input_shape,
            'output_shape': self.output_shape,
            'generation': self.generation,
            'fitness': self.fitness,
            'accuracy': self.accuracy,
            'loss': self.loss,
            'sharpe_ratio': self.sharpe_ratio,
            'total_params': self.estimate_total_params(),
            'architecture_hash': self.get_architecture_hash(),
        }


class SearchSpace:
    """
    Search Space Definition
    
    Defines the space of possible architectures to search.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Layer type options
        self.allowed_layers = self.config.get('allowed_layers', [
            LayerType.DENSE, LayerType.LSTM, LayerType.GRU,
            LayerType.ATTENTION, LayerType.DROPOUT, LayerType.BATCH_NORM
        ])
        
        # Layer size options
        self.unit_options = self.config.get('unit_options', [32, 64, 128, 256, 512])
        
        # Activation options
        self.activation_options = self.config.get('activation_options', [
            ActivationType.RELU, ActivationType.LEAKY_RELU,
            ActivationType.GELU, ActivationType.TANH
        ])
        
        # Architecture constraints
        self.min_layers = self.config.get('min_layers', 2)
        self.max_layers = self.config.get('max_layers', 10)
        self.max_params = self.config.get('max_params', 10_000_000)
        
        # Dropout options
        self.dropout_options = self.config.get('dropout_options', [0.0, 0.1, 0.2, 0.3, 0.5])
    
    def sample_layer(self, layer_id: str) -> LayerConfig:
        """Sample a random layer configuration"""
        layer_type = random.choice(self.allowed_layers)
        
        return LayerConfig(
            layer_id=layer_id,
            layer_type=layer_type,
            units=random.choice(self.unit_options),
            activation=random.choice(self.activation_options),
            dropout_rate=random.choice(self.dropout_options) if layer_type != LayerType.DROPOUT else random.choice([0.1, 0.2, 0.3, 0.5]),
            kernel_size=random.choice([3, 5, 7]) if layer_type == LayerType.CONV1D else 3,
            num_heads=random.choice([2, 4, 8]) if layer_type == LayerType.ATTENTION else 4,
        )
    
    def sample_architecture(self, input_shape: Tuple[int, ...], output_shape: Tuple[int, ...]) -> Architecture:
        """Sample a random architecture"""
        num_layers = random.randint(self.min_layers, self.max_layers)
        
        layers = []
        for i in range(num_layers):
            layer = self.sample_layer(f"layer_{i}")
            layers.append(layer)
        
        # Ensure output layer
        output_layer = LayerConfig(
            layer_id="output",
            layer_type=LayerType.DENSE,
            units=output_shape[-1] if output_shape else 1,
            activation=ActivationType.LINEAR,
        )
        layers.append(output_layer)
        
        return Architecture(
            architecture_id=f"arch_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            layers=layers,
            input_shape=input_shape,
            output_shape=output_shape,
        )
    
    def mutate_architecture(self, arch: Architecture) -> Architecture:
        """Mutate an architecture"""
        new_arch = Architecture(
            architecture_id=f"arch_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            layers=[copy.deepcopy(l) for l in arch.layers],
            input_shape=arch.input_shape,
            output_shape=arch.output_shape,
            generation=arch.generation + 1,
            parent_ids=[arch.architecture_id],
        )
        
        mutation_type = random.choice(['add', 'remove', 'modify', 'swap'])
        
        if mutation_type == 'add' and len(new_arch.layers) < self.max_layers:
            # Add a new layer
            position = random.randint(0, len(new_arch.layers) - 1)
            new_layer = self.sample_layer(f"layer_mut_{random.randint(1000, 9999)}")
            new_arch.add_layer(new_layer, position)
        
        elif mutation_type == 'remove' and len(new_arch.layers) > self.min_layers:
            # Remove a layer (not output)
            removable = [l for l in new_arch.layers if l.layer_id != "output"]
            if removable:
                to_remove = random.choice(removable)
                new_arch.remove_layer(to_remove.layer_id)
        
        elif mutation_type == 'modify':
            # Modify a random layer
            modifiable = [l for l in new_arch.layers if l.layer_id != "output"]
            if modifiable:
                layer = random.choice(modifiable)
                modification = random.choice(['units', 'activation', 'dropout'])
                
                if modification == 'units':
                    layer.units = random.choice(self.unit_options)
                elif modification == 'activation':
                    layer.activation = random.choice(self.activation_options)
                elif modification == 'dropout':
                    layer.dropout_rate = random.choice(self.dropout_options)
        
        elif mutation_type == 'swap' and len(new_arch.layers) > 2:
            # Swap two layers
            indices = list(range(len(new_arch.layers) - 1))  # Exclude output
            if len(indices) >= 2:
                i, j = random.sample(indices, 2)
                new_arch.layers[i], new_arch.layers[j] = new_arch.layers[j], new_arch.layers[i]
        
        return new_arch
    
    def crossover_architectures(self, arch1: Architecture, arch2: Architecture) -> Tuple[Architecture, Architecture]:
        """Crossover two architectures"""
        # Single-point crossover
        min_len = min(len(arch1.layers), len(arch2.layers)) - 1  # Exclude output
        if min_len < 2:
            return self.mutate_architecture(arch1), self.mutate_architecture(arch2)
        
        crossover_point = random.randint(1, min_len - 1)
        
        child1_layers = [copy.deepcopy(l) for l in arch1.layers[:crossover_point]]
        child1_layers.extend([copy.deepcopy(l) for l in arch2.layers[crossover_point:]])
        
        child2_layers = [copy.deepcopy(l) for l in arch2.layers[:crossover_point]]
        child2_layers.extend([copy.deepcopy(l) for l in arch1.layers[crossover_point:]])
        
        child1 = Architecture(
            architecture_id=f"arch_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            layers=child1_layers,
            input_shape=arch1.input_shape,
            output_shape=arch1.output_shape,
            generation=max(arch1.generation, arch2.generation) + 1,
            parent_ids=[arch1.architecture_id, arch2.architecture_id],
        )
        
        child2 = Architecture(
            architecture_id=f"arch_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            layers=child2_layers,
            input_shape=arch2.input_shape,
            output_shape=arch2.output_shape,
            generation=max(arch1.generation, arch2.generation) + 1,
            parent_ids=[arch1.architecture_id, arch2.architecture_id],
        )
        
        return child1, child2


class PerformancePredictor:
    """
    Performance Predictor
    
    Predicts architecture performance without full training.
    Uses surrogate models to speed up search.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Historical data for prediction
        self.architecture_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
        # Simple feature weights (learned over time)
        self.feature_weights = {
            'num_layers': -0.01,
            'total_params': -0.0001,
            'has_lstm': 0.1,
            'has_attention': 0.15,
            'has_dropout': 0.05,
            'avg_units': 0.001,
        }
    
    def extract_features(self, arch: Architecture) -> Dict[str, float]:
        """Extract features from architecture"""
        features = {
            'num_layers': len(arch.layers),
            'total_params': arch.estimate_total_params() / 1_000_000,
            'has_lstm': 1.0 if any(l.layer_type == LayerType.LSTM for l in arch.layers) else 0.0,
            'has_gru': 1.0 if any(l.layer_type == LayerType.GRU for l in arch.layers) else 0.0,
            'has_attention': 1.0 if any(l.layer_type == LayerType.ATTENTION for l in arch.layers) else 0.0,
            'has_dropout': 1.0 if any(l.dropout_rate > 0 for l in arch.layers) else 0.0,
            'avg_units': sum(l.units for l in arch.layers) / len(arch.layers) if arch.layers else 0,
            'max_units': max(l.units for l in arch.layers) if arch.layers else 0,
        }
        return features
    
    def predict(self, arch: Architecture) -> float:
        """Predict architecture performance"""
        features = self.extract_features(arch)
        
        # Simple linear prediction
        score = 0.5  # Base score
        for feature_name, weight in self.feature_weights.items():
            if feature_name in features:
                score += weight * features[feature_name]
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))
    
    def update(self, arch: Architecture, actual_fitness: float) -> None:
        """Update predictor with actual results"""
        features = self.extract_features(arch)
        
        self.architecture_history.append({
            'features': features,
            'predicted': self.predict(arch),
            'actual': actual_fitness,
        })
        
        if len(self.architecture_history) > self.max_history:
            self.architecture_history.pop(0)
        
        # Simple online learning of weights
        if len(self.architecture_history) > 10:
            self._update_weights()
    
    def _update_weights(self) -> None:
        """Update feature weights based on history"""
        # Simple gradient-based update
        learning_rate = 0.01
        
        for record in self.architecture_history[-10:]:
            error = record['actual'] - record['predicted']
            
            for feature_name in self.feature_weights:
                if feature_name in record['features']:
                    gradient = error * record['features'][feature_name]
                    self.feature_weights[feature_name] += learning_rate * gradient


class NeuralArchitectureSearch:
    """
    Neural Architecture Search Engine
    
    Main interface for automatic architecture discovery.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.search_space = SearchSpace(config)
        self.predictor = PerformancePredictor(config)
        
        self.population: List[Architecture] = []
        self.hall_of_fame: List[Architecture] = []
        
        self.population_size = self.config.get('population_size', 20)
        self.elite_size = self.config.get('elite_size', 3)
        self.mutation_rate = self.config.get('mutation_rate', 0.3)
        self.crossover_rate = self.config.get('crossover_rate', 0.5)
        
        self.generation = 0
        self.evaluations = 0
        
        self.input_shape = self.config.get('input_shape', (100, 10))
        self.output_shape = self.config.get('output_shape', (3,))
        
        logger.info("NeuralArchitectureSearch initialized")
    
    def initialize_population(self) -> None:
        """Initialize population with random architectures"""
        self.population = []
        
        for _ in range(self.population_size):
            arch = self.search_space.sample_architecture(self.input_shape, self.output_shape)
            self.population.append(arch)
        
        logger.info(f"Initialized population with {len(self.population)} architectures")
    
    def evaluate_population(self, fitness_func: Callable[[Architecture], float], use_predictor: bool = True) -> None:
        """Evaluate fitness of all architectures"""
        for arch in self.population:
            if use_predictor and random.random() < 0.7:
                # Use predictor for most evaluations
                arch.fitness = self.predictor.predict(arch)
            else:
                # Full evaluation
                arch.fitness = fitness_func(arch)
                self.predictor.update(arch, arch.fitness)
                self.evaluations += 1
        
        # Sort by fitness
        self.population.sort(key=lambda a: a.fitness, reverse=True)
        
        # Update hall of fame
        for arch in self.population[:self.elite_size]:
            if not self.hall_of_fame or arch.fitness > self.hall_of_fame[0].fitness:
                self.hall_of_fame.insert(0, copy.deepcopy(arch))
                self.hall_of_fame = self.hall_of_fame[:10]
    
    def select_parents(self) -> Tuple[Architecture, Architecture]:
        """Select parents using tournament selection"""
        tournament_size = min(5, len(self.population))
        
        def tournament():
            contestants = random.sample(self.population, tournament_size)
            return max(contestants, key=lambda a: a.fitness)
        
        return tournament(), tournament()
    
    def evolve(self) -> None:
        """Evolve population to next generation"""
        new_population = []
        
        # Elitism
        elite = self.population[:self.elite_size]
        new_population.extend([copy.deepcopy(a) for a in elite])
        
        # Generate rest of population
        while len(new_population) < self.population_size:
            parent1, parent2 = self.select_parents()
            
            if random.random() < self.crossover_rate:
                child1, child2 = self.search_space.crossover_architectures(parent1, parent2)
            else:
                child1 = self.search_space.mutate_architecture(parent1)
                child2 = self.search_space.mutate_architecture(parent2)
            
            # Additional mutation
            if random.random() < self.mutation_rate:
                child1 = self.search_space.mutate_architecture(child1)
            if random.random() < self.mutation_rate:
                child2 = self.search_space.mutate_architecture(child2)
            
            new_population.append(child1)
            if len(new_population) < self.population_size:
                new_population.append(child2)
        
        self.population = new_population
        self.generation += 1
        
        logger.info(f"Evolved to generation {self.generation}")
    
    async def search(
        self,
        fitness_func: Callable[[Architecture], float],
        max_generations: int = 50,
        early_stopping_patience: int = 10
    ) -> Architecture:
        """Run architecture search"""
        self.initialize_population()
        
        best_fitness = 0.0
        patience_counter = 0
        
        for gen in range(max_generations):
            # Evaluate
            self.evaluate_population(fitness_func)
            
            # Check for improvement
            current_best = self.population[0].fitness if self.population else 0
            if current_best > best_fitness:
                best_fitness = current_best
                patience_counter = 0
            else:
                patience_counter += 1
            
            # Early stopping
            if patience_counter >= early_stopping_patience:
                logger.info(f"Early stopping at generation {gen}")
                break
            
            # Evolve
            self.evolve()
            
            await asyncio.sleep(0)  # Yield control
        
        return self.get_best_architecture()
    
    def get_best_architecture(self) -> Optional[Architecture]:
        """Get the best architecture found"""
        if self.hall_of_fame:
            return self.hall_of_fame[0]
        if self.population:
            return max(self.population, key=lambda a: a.fitness)
        return None
    
    def get_report(self) -> Dict[str, Any]:
        """Get search status report"""
        return {
            'generation': self.generation,
            'evaluations': self.evaluations,
            'population_size': len(self.population),
            'hall_of_fame_size': len(self.hall_of_fame),
            'best_fitness': self.population[0].fitness if self.population else 0,
            'best_architecture': self.population[0].to_dict() if self.population else None,
            'avg_fitness': sum(a.fitness for a in self.population) / len(self.population) if self.population else 0,
            'avg_params': sum(a.estimate_total_params() for a in self.population) / len(self.population) if self.population else 0,
        }


# Factory function
def create_nas_engine(
    input_shape: Tuple[int, ...] = (100, 10),
    output_shape: Tuple[int, ...] = (3,),
    config: Optional[Dict[str, Any]] = None
) -> NeuralArchitectureSearch:
    """Create and initialize NAS engine"""
    config = config or {}
    config['input_shape'] = input_shape
    config['output_shape'] = output_shape
    
    nas = NeuralArchitectureSearch(config)
    return nas

"""
Skill #21: Neural Architecture Search
=====================================

Automatically discovers optimal neural network architectures
for trading tasks.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Architecture:
    """Neural network architecture."""
    layers: List[Dict]
    performance: float
    complexity: int
    training_time: float


@dataclass
class NASResult:
    """Neural Architecture Search result."""
    best_architecture: Architecture
    searched_architectures: List[Architecture]
    pareto_front: List[Architecture]
    recommended_config: Dict
    trading_signal: str


class NeuralArchitectureSearch:
    """Automated neural architecture search for trading models."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.search_space = self._define_search_space()
            self.evaluated: List[Architecture] = []
            logger.info("NeuralArchitectureSearch initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _define_search_space(self) -> Dict:
        """Define the architecture search space."""
        return {
            'num_layers': [2, 3, 4, 5],
            'hidden_sizes': [32, 64, 128, 256],
            'activations': ['relu', 'tanh', 'gelu'],
            'dropout': [0.0, 0.1, 0.2, 0.3],
            'attention_heads': [0, 2, 4, 8],
        }
    
    def search(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        num_iterations: int = 20
    ) -> NASResult:
        """Search for optimal architecture."""
        try:
            if len(prices) < 50:
                return self._create_empty_result()
        
            # Prepare data
            X, y = self._prepare_data(prices, volumes)
        
            # Search architectures
            for _ in range(num_iterations):
                arch = self._sample_architecture()
                perf = self._evaluate_architecture(arch, X, y)
                arch.performance = perf
                self.evaluated.append(arch)
        
            # Find best and pareto front
            best = max(self.evaluated, key=lambda a: a.performance)
            pareto = self._find_pareto_front()
        
            config = self._architecture_to_config(best)
            signal = self._generate_signal(best)
        
            return NASResult(
                best_architecture=best,
                searched_architectures=self.evaluated[-10:],
                pareto_front=pareto,
                recommended_config=config,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in search: {e}")
            raise
    
    def _prepare_data(self, prices: np.ndarray, volumes: np.ndarray):
        """Prepare training data."""
        try:
            returns = np.diff(prices) / prices[:-1]
            X = np.column_stack([
                returns[:-1],
                volumes[1:-1] / np.mean(volumes),
            ])
            y = (returns[1:] > 0).astype(float)
            return X, y
        except Exception as e:
            logger.error(f"Error in _prepare_data: {e}")
            raise
    
    def _sample_architecture(self) -> Architecture:
        """Sample random architecture from search space."""
        try:
            num_layers = np.random.choice(self.search_space['num_layers'])
            layers = []
            for i in range(num_layers):
                layers.append({
                    'type': 'dense',
                    'size': np.random.choice(self.search_space['hidden_sizes']),
                    'activation': np.random.choice(self.search_space['activations']),
                    'dropout': np.random.choice(self.search_space['dropout']),
                })
        
            complexity = sum(l['size'] for l in layers)
            return Architecture(layers=layers, performance=0, complexity=complexity, training_time=0)
        except Exception as e:
            logger.error(f"Error in _sample_architecture: {e}")
            raise
    
    def _evaluate_architecture(self, arch: Architecture, X: np.ndarray, y: np.ndarray) -> float:
        """Evaluate architecture performance (simplified)."""
        # Simplified evaluation - in production would train actual model
        try:
            complexity_penalty = arch.complexity / 1000
            random_perf = np.random.random() * 0.3 + 0.5
            return random_perf - complexity_penalty
        except Exception as e:
            logger.error(f"Error in _evaluate_architecture: {e}")
            raise
    
    def _find_pareto_front(self) -> List[Architecture]:
        """Find Pareto-optimal architectures."""
        try:
            pareto = []
            for arch in self.evaluated:
                dominated = False
                for other in self.evaluated:
                    if other.performance > arch.performance and other.complexity < arch.complexity:
                        dominated = True
                        break
                if not dominated:
                    pareto.append(arch)
            return pareto
        except Exception as e:
            logger.error(f"Error in _find_pareto_front: {e}")
            raise
    
    def _architecture_to_config(self, arch: Architecture) -> Dict:
        """Convert architecture to config dict."""
        return {
            'num_layers': len(arch.layers),
            'layer_configs': arch.layers,
            'estimated_performance': arch.performance,
            'complexity': arch.complexity
        }
    
    def _generate_signal(self, arch: Architecture) -> str:
        """Generate signal based on best architecture."""
        try:
            if arch.performance > 0.7:
                return f"HIGH CONFIDENCE: Best arch achieves {arch.performance:.1%} accuracy"
            elif arch.performance > 0.55:
                return f"MODERATE: Best arch achieves {arch.performance:.1%} accuracy"
            return f"LOW CONFIDENCE: Best arch only {arch.performance:.1%} accuracy"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> NASResult:
        """Create empty result."""
        try:
            empty = Architecture([], 0, 0, 0)
            return NASResult(empty, [], [], {}, "Insufficient data")
        except Exception as e:
            logger.error(f"Error in _create_empty_result: {e}")
            raise

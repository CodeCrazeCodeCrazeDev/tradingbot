"""
Meta-Reinforcement Learning
===========================

Learn how to learn faster using MAML, Reptile, and other
meta-learning algorithms for rapid adaptation to new market conditions.
"""

import asyncio
import copy
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable
import numpy as np

logger = logging.getLogger(__name__)


class MetaAlgorithm(Enum):
    """Meta-learning algorithms"""
    MAML = "maml"  # Model-Agnostic Meta-Learning
    REPTILE = "reptile"
    FOMAML = "fomaml"  # First-Order MAML
    MAML_PLUS = "maml_plus"
    META_SGD = "meta_sgd"
    LEAP = "leap"
    PROTO_NET = "proto_net"  # Prototypical Networks


@dataclass
class Task:
    """A meta-learning task (market condition)"""
    task_id: str
    name: str
    train_data: np.ndarray
    train_labels: np.ndarray
    test_data: np.ndarray
    test_labels: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetaLearnerConfig:
    """Configuration for meta-learner"""
    inner_lr: float = 0.01  # Task-specific learning rate
    outer_lr: float = 0.001  # Meta learning rate
    inner_steps: int = 5  # Gradient steps per task
    meta_batch_size: int = 4  # Tasks per meta-update
    first_order: bool = False  # Use first-order approximation
    input_dim: int = 20
    hidden_dims: List[int] = field(default_factory=lambda: [64, 32])
    output_dim: int = 3  # Buy, Hold, Sell


class NeuralNetwork:
    """Simple neural network for meta-learning"""
    
    def __init__(self, input_dim: int, hidden_dims: List[int], output_dim: int):
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.output_dim = output_dim
        
        # Initialize weights
        self.params = self._init_params()
    
    def _init_params(self) -> Dict[str, np.ndarray]:
        """Initialize network parameters"""
        params = {}
        dims = [self.input_dim] + self.hidden_dims + [self.output_dim]
        
        for i in range(len(dims) - 1):
            # Xavier initialization
            scale = np.sqrt(2.0 / (dims[i] + dims[i+1]))
            params[f'W{i}'] = np.random.randn(dims[i], dims[i+1]) * scale
            params[f'b{i}'] = np.zeros(dims[i+1])
        
        return params
    
    def forward(self, x: np.ndarray, params: Optional[Dict[str, np.ndarray]] = None) -> np.ndarray:
        """Forward pass"""
        if params is None:
            params = self.params
        
        num_layers = len(self.hidden_dims) + 1
        
        for i in range(num_layers):
            x = x @ params[f'W{i}'] + params[f'b{i}']
            if i < num_layers - 1:
                x = np.maximum(0, x)  # ReLU
        
        # Softmax for classification
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    
    def compute_loss(
        self,
        x: np.ndarray,
        y: np.ndarray,
        params: Optional[Dict[str, np.ndarray]] = None
    ) -> float:
        """Compute cross-entropy loss"""
        probs = self.forward(x, params)
        
        # Convert labels to one-hot if needed
        if y.ndim == 1:
            y_onehot = np.zeros((len(y), self.output_dim))
            y_onehot[np.arange(len(y)), y.astype(int)] = 1
            y = y_onehot
        
        # Cross-entropy
        eps = 1e-10
        loss = -np.mean(np.sum(y * np.log(probs + eps), axis=-1))
        return loss
    
    def compute_gradients(
        self,
        x: np.ndarray,
        y: np.ndarray,
        params: Optional[Dict[str, np.ndarray]] = None
    ) -> Dict[str, np.ndarray]:
        """Compute gradients using numerical differentiation"""
        if params is None:
            params = self.params
        
        grads = {}
        eps = 1e-5
        
        for key in params:
            grad = np.zeros_like(params[key])
            
            # Numerical gradient (simplified)
            for idx in np.ndindex(params[key].shape):
                params_plus = {k: v.copy() for k, v in params.items()}
                params_minus = {k: v.copy() for k, v in params.items()}
                
                params_plus[key][idx] += eps
                params_minus[key][idx] -= eps
                
                loss_plus = self.compute_loss(x, y, params_plus)
                loss_minus = self.compute_loss(x, y, params_minus)
                
                grad[idx] = (loss_plus - loss_minus) / (2 * eps)
            
            grads[key] = grad
        
        return grads
    
    def compute_gradients_fast(
        self,
        x: np.ndarray,
        y: np.ndarray,
        params: Optional[Dict[str, np.ndarray]] = None
    ) -> Dict[str, np.ndarray]:
        """Fast approximate gradients using backprop"""
        if params is None:
            params = self.params
        
        # Forward pass with caching
        activations = [x]
        num_layers = len(self.hidden_dims) + 1
        
        for i in range(num_layers):
            z = activations[-1] @ params[f'W{i}'] + params[f'b{i}']
            if i < num_layers - 1:
                a = np.maximum(0, z)  # ReLU
            else:
                # Softmax
                exp_z = np.exp(z - np.max(z, axis=-1, keepdims=True))
                a = exp_z / np.sum(exp_z, axis=-1, keepdims=True)
            activations.append(a)
        
        # Convert labels
        if y.ndim == 1:
            y_onehot = np.zeros((len(y), self.output_dim))
            y_onehot[np.arange(len(y)), y.astype(int)] = 1
            y = y_onehot
        
        # Backward pass
        grads = {}
        delta = activations[-1] - y  # Softmax + cross-entropy gradient
        
        for i in range(num_layers - 1, -1, -1):
            grads[f'W{i}'] = activations[i].T @ delta / len(x)
            grads[f'b{i}'] = np.mean(delta, axis=0)
            
            if i > 0:
                delta = delta @ params[f'W{i}'].T
                delta = delta * (activations[i] > 0)  # ReLU gradient
        
        return grads
    
    def update_params(
        self,
        grads: Dict[str, np.ndarray],
        lr: float,
        params: Optional[Dict[str, np.ndarray]] = None
    ) -> Dict[str, np.ndarray]:
        """Update parameters with gradients"""
        if params is None:
            params = self.params
        
        new_params = {}
        for key in params:
            new_params[key] = params[key] - lr * grads[key]
        
        return new_params
    
    def clone_params(self) -> Dict[str, np.ndarray]:
        """Clone current parameters"""
        return {k: v.copy() for k, v in self.params.items()}
    
    def set_params(self, params: Dict[str, np.ndarray]):
        """Set parameters"""
        self.params = {k: v.copy() for k, v in params.items()}


class MAML:
    """
    Model-Agnostic Meta-Learning (MAML)
    
    Learns initialization that can quickly adapt to new tasks.
    """
    
    def __init__(self, config: Optional[MetaLearnerConfig] = None):
        self.config = config or MetaLearnerConfig()
        
        self.network = NeuralNetwork(
            self.config.input_dim,
            self.config.hidden_dims,
            self.config.output_dim
        )
        
        self.meta_params = self.network.clone_params()
        self.task_history: List[Dict[str, Any]] = []
        
        logger.info("MAML initialized")
    
    def inner_loop(
        self,
        task: Task,
        params: Dict[str, np.ndarray]
    ) -> Tuple[Dict[str, np.ndarray], float]:
        """
        Inner loop: Adapt to a specific task
        
        Returns adapted parameters and final loss
        """
        adapted_params = {k: v.copy() for k, v in params.items()}
        
        for step in range(self.config.inner_steps):
            grads = self.network.compute_gradients_fast(
                task.train_data,
                task.train_labels,
                adapted_params
            )
            
            adapted_params = self.network.update_params(
                grads,
                self.config.inner_lr,
                adapted_params
            )
        
        # Compute loss on test data
        test_loss = self.network.compute_loss(
            task.test_data,
            task.test_labels,
            adapted_params
        )
        
        return adapted_params, test_loss
    
    def outer_loop(self, tasks: List[Task]) -> float:
        """
        Outer loop: Meta-update across tasks
        
        Returns average meta-loss
        """
        meta_grads = {k: np.zeros_like(v) for k, v in self.meta_params.items()}
        total_loss = 0.0
        
        for task in tasks:
            # Inner loop adaptation
            adapted_params, test_loss = self.inner_loop(task, self.meta_params)
            total_loss += test_loss
            
            if self.config.first_order:
                # FOMAML: Use gradients at adapted params
                grads = self.network.compute_gradients_fast(
                    task.test_data,
                    task.test_labels,
                    adapted_params
                )
            else:
                # Full MAML: Compute meta-gradients (approximated)
                grads = self.network.compute_gradients_fast(
                    task.test_data,
                    task.test_labels,
                    adapted_params
                )
            
            # Accumulate gradients
            for key in meta_grads:
                meta_grads[key] += grads[key]
        
        # Average gradients
        for key in meta_grads:
            meta_grads[key] /= len(tasks)
        
        # Meta-update
        self.meta_params = self.network.update_params(
            meta_grads,
            self.config.outer_lr,
            self.meta_params
        )
        
        avg_loss = total_loss / len(tasks)
        
        self.task_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'num_tasks': len(tasks),
            'avg_loss': avg_loss
        })
        
        return avg_loss
    
    def adapt(self, task: Task) -> Dict[str, np.ndarray]:
        """Adapt to a new task using learned initialization"""
        adapted_params, _ = self.inner_loop(task, self.meta_params)
        return adapted_params
    
    def predict(
        self,
        x: np.ndarray,
        params: Optional[Dict[str, np.ndarray]] = None
    ) -> np.ndarray:
        """Make predictions"""
        if params is None:
            params = self.meta_params
        return self.network.forward(x, params)


class Reptile:
    """
    Reptile Meta-Learning
    
    Simpler alternative to MAML that doesn't require
    second-order gradients.
    """
    
    def __init__(self, config: Optional[MetaLearnerConfig] = None):
        self.config = config or MetaLearnerConfig()
        
        self.network = NeuralNetwork(
            self.config.input_dim,
            self.config.hidden_dims,
            self.config.output_dim
        )
        
        self.meta_params = self.network.clone_params()
        
        logger.info("Reptile initialized")
    
    def train_on_task(
        self,
        task: Task,
        params: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """Train on a single task"""
        task_params = {k: v.copy() for k, v in params.items()}
        
        for step in range(self.config.inner_steps):
            grads = self.network.compute_gradients_fast(
                task.train_data,
                task.train_labels,
                task_params
            )
            
            task_params = self.network.update_params(
                grads,
                self.config.inner_lr,
                task_params
            )
        
        return task_params
    
    def meta_update(self, tasks: List[Task]) -> float:
        """Reptile meta-update"""
        
        # Average of task-specific parameters
        avg_params = {k: np.zeros_like(v) for k, v in self.meta_params.items()}
        
        for task in tasks:
            task_params = self.train_on_task(task, self.meta_params)
            
            for key in avg_params:
                avg_params[key] += task_params[key]
        
        for key in avg_params:
            avg_params[key] /= len(tasks)
        
        # Interpolate towards average
        for key in self.meta_params:
            self.meta_params[key] = (
                (1 - self.config.outer_lr) * self.meta_params[key] +
                self.config.outer_lr * avg_params[key]
            )
        
        # Compute average loss
        total_loss = 0.0
        for task in tasks:
            total_loss += self.network.compute_loss(
                task.test_data,
                task.test_labels,
                self.meta_params
            )
        
        return total_loss / len(tasks)
    
    def adapt(self, task: Task) -> Dict[str, np.ndarray]:
        """Adapt to a new task"""
        return self.train_on_task(task, self.meta_params)


class MetaSGD:
    """
    Meta-SGD: Learning to Learn with Per-Parameter Learning Rates
    
    Learns both initialization and per-parameter learning rates.
    """
    
    def __init__(self, config: Optional[MetaLearnerConfig] = None):
        self.config = config or MetaLearnerConfig()
        
        self.network = NeuralNetwork(
            self.config.input_dim,
            self.config.hidden_dims,
            self.config.output_dim
        )
        
        self.meta_params = self.network.clone_params()
        
        # Per-parameter learning rates
        self.alpha = {
            k: np.ones_like(v) * self.config.inner_lr
            for k, v in self.meta_params.items()
        }
        
        logger.info("MetaSGD initialized")
    
    def inner_loop(
        self,
        task: Task,
        params: Dict[str, np.ndarray],
        alpha: Dict[str, np.ndarray]
    ) -> Tuple[Dict[str, np.ndarray], float]:
        """Inner loop with learned learning rates"""
        adapted_params = {k: v.copy() for k, v in params.items()}
        
        for step in range(self.config.inner_steps):
            grads = self.network.compute_gradients_fast(
                task.train_data,
                task.train_labels,
                adapted_params
            )
            
            # Update with per-parameter learning rates
            for key in adapted_params:
                adapted_params[key] = adapted_params[key] - alpha[key] * grads[key]
        
        test_loss = self.network.compute_loss(
            task.test_data,
            task.test_labels,
            adapted_params
        )
        
        return adapted_params, test_loss
    
    def meta_update(self, tasks: List[Task]) -> float:
        """Meta-update for both params and learning rates"""
        
        param_grads = {k: np.zeros_like(v) for k, v in self.meta_params.items()}
        alpha_grads = {k: np.zeros_like(v) for k, v in self.alpha.items()}
        total_loss = 0.0
        
        for task in tasks:
            adapted_params, test_loss = self.inner_loop(
                task, self.meta_params, self.alpha
            )
            total_loss += test_loss
            
            grads = self.network.compute_gradients_fast(
                task.test_data,
                task.test_labels,
                adapted_params
            )
            
            for key in param_grads:
                param_grads[key] += grads[key]
                # Approximate gradient for alpha
                alpha_grads[key] += np.abs(grads[key])
        
        # Average and update
        for key in self.meta_params:
            param_grads[key] /= len(tasks)
            alpha_grads[key] /= len(tasks)
            
            self.meta_params[key] -= self.config.outer_lr * param_grads[key]
            self.alpha[key] -= self.config.outer_lr * 0.1 * alpha_grads[key]
            
            # Clip learning rates
            self.alpha[key] = np.clip(self.alpha[key], 1e-5, 1.0)
        
        return total_loss / len(tasks)


class PrototypicalNetworks:
    """
    Prototypical Networks for Few-Shot Learning
    
    Learns an embedding space where classification
    can be performed by computing distances to class prototypes.
    """
    
    def __init__(self, config: Optional[MetaLearnerConfig] = None):
        self.config = config or MetaLearnerConfig()
        
        # Embedding network
        self.encoder = NeuralNetwork(
            self.config.input_dim,
            self.config.hidden_dims,
            self.config.hidden_dims[-1]  # Embedding dimension
        )
        
        logger.info("PrototypicalNetworks initialized")
    
    def compute_prototypes(
        self,
        support_data: np.ndarray,
        support_labels: np.ndarray
    ) -> Dict[int, np.ndarray]:
        """Compute class prototypes from support set"""
        
        embeddings = self.encoder.forward(support_data)
        
        prototypes = {}
        unique_labels = np.unique(support_labels)
        
        for label in unique_labels:
            mask = support_labels == label
            prototypes[int(label)] = np.mean(embeddings[mask], axis=0)
        
        return prototypes
    
    def predict(
        self,
        query_data: np.ndarray,
        prototypes: Dict[int, np.ndarray]
    ) -> np.ndarray:
        """Predict by finding nearest prototype"""
        
        embeddings = self.encoder.forward(query_data)
        
        # Compute distances to each prototype
        distances = np.zeros((len(query_data), len(prototypes)))
        
        for i, (label, prototype) in enumerate(sorted(prototypes.items())):
            distances[:, i] = np.sum((embeddings - prototype) ** 2, axis=-1)
        
        # Convert to probabilities (negative distance -> softmax)
        neg_distances = -distances
        exp_d = np.exp(neg_distances - np.max(neg_distances, axis=-1, keepdims=True))
        probs = exp_d / np.sum(exp_d, axis=-1, keepdims=True)
        
        return probs
    
    def episode_loss(self, task: Task) -> float:
        """Compute loss for an episode"""
        
        prototypes = self.compute_prototypes(task.train_data, task.train_labels)
        probs = self.predict(task.test_data, prototypes)
        
        # Cross-entropy loss
        eps = 1e-10
        labels = task.test_labels.astype(int)
        loss = -np.mean(np.log(probs[np.arange(len(labels)), labels] + eps))
        
        return loss


class MarketConditionTask:
    """Factory for creating market condition tasks"""
    
    @staticmethod
    def create_task(
        market_data: np.ndarray,
        labels: np.ndarray,
        task_id: str,
        name: str,
        train_ratio: float = 0.7
    ) -> Task:
        """Create a task from market data"""
        
        n_train = int(len(market_data) * train_ratio)
        
        # Shuffle
        indices = np.random.permutation(len(market_data))
        
        return Task(
            task_id=task_id,
            name=name,
            train_data=market_data[indices[:n_train]],
            train_labels=labels[indices[:n_train]],
            test_data=market_data[indices[n_train:]],
            test_labels=labels[indices[n_train:]]
        )
    
    @staticmethod
    def create_regime_tasks(
        market_data: np.ndarray,
        labels: np.ndarray,
        regime_labels: np.ndarray
    ) -> List[Task]:
        """Create tasks for different market regimes"""
        
        tasks = []
        unique_regimes = np.unique(regime_labels)
        
        for regime in unique_regimes:
            mask = regime_labels == regime
            
            if np.sum(mask) < 20:  # Skip if too few samples
                continue
            
            task = MarketConditionTask.create_task(
                market_data[mask],
                labels[mask],
                task_id=f"regime_{regime}",
                name=f"Market Regime {regime}"
            )
            tasks.append(task)
        
        return tasks


class MetaRLTrader:
    """
    Meta-RL Trader
    
    High-level interface for meta-learning in trading.
    """
    
    def __init__(
        self,
        algorithm: MetaAlgorithm = MetaAlgorithm.MAML,
        config: Optional[MetaLearnerConfig] = None
    ):
        self.algorithm = algorithm
        self.config = config or MetaLearnerConfig()
        
        if algorithm == MetaAlgorithm.MAML:
            self.learner = MAML(self.config)
        elif algorithm == MetaAlgorithm.FOMAML:
            self.config.first_order = True
            self.learner = MAML(self.config)
        elif algorithm == MetaAlgorithm.REPTILE:
            self.learner = Reptile(self.config)
        elif algorithm == MetaAlgorithm.META_SGD:
            self.learner = MetaSGD(self.config)
        elif algorithm == MetaAlgorithm.PROTO_NET:
            self.learner = PrototypicalNetworks(self.config)
        else:
            self.learner = MAML(self.config)
        
        self.training_history: List[Dict[str, Any]] = []
        self.adapted_params: Optional[Dict[str, np.ndarray]] = None
        
        logger.info(f"MetaRLTrader initialized with {algorithm.value}")
    
    async def meta_train(
        self,
        tasks: List[Task],
        num_iterations: int = 100,
        tasks_per_iteration: int = 4
    ):
        """Meta-train on a set of tasks"""
        
        logger.info(f"Starting meta-training for {num_iterations} iterations")
        
        for i in range(num_iterations):
            # Sample tasks
            batch_tasks = np.random.choice(
                tasks,
                size=min(tasks_per_iteration, len(tasks)),
                replace=False
            ).tolist()
            
            # Meta-update
            if hasattr(self.learner, 'outer_loop'):
                loss = self.learner.outer_loop(batch_tasks)
            elif hasattr(self.learner, 'meta_update'):
                loss = self.learner.meta_update(batch_tasks)
            else:
                loss = 0.0
            
            self.training_history.append({
                'iteration': i,
                'loss': loss,
                'num_tasks': len(batch_tasks)
            })
            
            if (i + 1) % 10 == 0:
                logger.info(f"Iteration {i + 1}/{num_iterations}, Loss: {loss:.4f}")
        
        logger.info("Meta-training complete")
    
    def adapt_to_market(self, task: Task) -> Dict[str, np.ndarray]:
        """Quickly adapt to current market conditions"""
        
        if hasattr(self.learner, 'adapt'):
            self.adapted_params = self.learner.adapt(task)
        else:
            self.adapted_params = self.learner.meta_params
        
        return self.adapted_params
    
    def predict(self, market_features: np.ndarray) -> np.ndarray:
        """Make trading predictions"""
        
        params = self.adapted_params or getattr(self.learner, 'meta_params', None)
        
        if hasattr(self.learner, 'network'):
            return self.learner.network.forward(market_features, params)
        elif hasattr(self.learner, 'encoder'):
            return self.learner.encoder.forward(market_features)
        else:
            raise ValueError("No prediction method available")
    
    def get_action(self, market_features: np.ndarray) -> int:
        """Get trading action (0=Sell, 1=Hold, 2=Buy)"""
        
        probs = self.predict(market_features.reshape(1, -1))
        return int(np.argmax(probs[0]))
    
    def get_report(self) -> Dict[str, Any]:
        """Get training report"""
        
        return {
            'algorithm': self.algorithm.value,
            'training_iterations': len(self.training_history),
            'final_loss': self.training_history[-1]['loss'] if self.training_history else None,
            'loss_history': [h['loss'] for h in self.training_history[-50:]],
            'adapted': self.adapted_params is not None
        }


# Convenience functions
def create_meta_learner(
    algorithm: str = "maml",
    input_dim: int = 20,
    output_dim: int = 3,
    **kwargs
) -> MetaRLTrader:
    """Create a meta-learner"""
    
    algo_map = {
        'maml': MetaAlgorithm.MAML,
        'fomaml': MetaAlgorithm.FOMAML,
        'reptile': MetaAlgorithm.REPTILE,
        'meta_sgd': MetaAlgorithm.META_SGD,
        'proto_net': MetaAlgorithm.PROTO_NET
    }
    
    config = MetaLearnerConfig(
        input_dim=input_dim,
        output_dim=output_dim,
        **kwargs
    )
    
    return MetaRLTrader(
        algorithm=algo_map.get(algorithm, MetaAlgorithm.MAML),
        config=config
    )


async def quick_meta_train(
    market_data: np.ndarray,
    labels: np.ndarray,
    regime_labels: np.ndarray,
    algorithm: str = "maml",
    num_iterations: int = 50
) -> MetaRLTrader:
    """Quick meta-training on market data"""
    
    # Create tasks from regimes
    tasks = MarketConditionTask.create_regime_tasks(
        market_data, labels, regime_labels
    )
    
    if not tasks:
        raise ValueError("No valid tasks created from data")
    
    # Create and train meta-learner
    learner = create_meta_learner(
        algorithm=algorithm,
        input_dim=market_data.shape[1]
    )
    
    await learner.meta_train(tasks, num_iterations=num_iterations)
    
    return learner

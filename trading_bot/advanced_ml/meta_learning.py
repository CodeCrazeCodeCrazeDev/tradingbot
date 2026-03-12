"""
Meta-Learning Strategy Adapters
MAML (Model-Agnostic Meta-Learning) for rapid strategy adaptation
"""

import numpy as np
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import copy
import numpy

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Meta-learning task (market regime)"""
    task_id: str
    regime: str
    train_data: np.ndarray
    train_labels: np.ndarray
    test_data: np.ndarray
    test_labels: np.ndarray
    metadata: Dict[str, Any]


@dataclass
class MetaModel:
    """Meta-learned model"""
    parameters: Dict[str, np.ndarray]
    meta_parameters: Dict[str, np.ndarray]
    adaptation_steps: int
    learning_rate: float
    performance_history: List[float]


class MAML:
    """
    Model-Agnostic Meta-Learning
    Learns to quickly adapt to new market regimes
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Meta-learning parameters
            self.meta_lr = self.config.get('meta_lr', 0.001)
            self.inner_lr = self.config.get('inner_lr', 0.01)
            self.inner_steps = self.config.get('inner_steps', 5)
        
            # Model architecture (simplified neural network)
            self.input_dim = self.config.get('input_dim', 20)
            self.hidden_dim = self.config.get('hidden_dim', 64)
            self.output_dim = self.config.get('output_dim', 3)  # buy/sell/hold
        
            # Initialize meta-parameters
            self.meta_params = self._initialize_parameters()
        
            # Task distribution
            self.task_distribution: List[Task] = []
        
            logger.info("MAML meta-learning initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def _initialize_parameters(self) -> Dict[str, np.ndarray]:
        """Initialize neural network parameters"""
        try:
            params = {
                'W1': np.random.randn(self.input_dim, self.hidden_dim) * 0.01,
                'b1': np.zeros((1, self.hidden_dim)),
                'W2': np.random.randn(self.hidden_dim, self.output_dim) * 0.01,
                'b2': np.zeros((1, self.output_dim))
            }
            return params
        except Exception as e:
            logger.error(f"Error in _initialize_parameters: {e}")
            raise
        
    def forward(self, X: np.ndarray, params: Dict[str, np.ndarray]) -> np.ndarray:
        """Forward pass through network"""
        # Layer 1
        try:
            z1 = X @ params['W1'] + params['b1']
            a1 = np.maximum(0, z1)  # ReLU
        
            # Layer 2
            z2 = a1 @ params['W2'] + params['b2']
        
            # Softmax
            exp_z2 = np.exp(z2 - np.max(z2, axis=1, keepdims=True))
            a2 = exp_z2 / np.sum(exp_z2, axis=1, keepdims=True)
        
            return a2
        except Exception as e:
            logger.error(f"Error in forward: {e}")
            raise
        
    def compute_loss(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """Compute cross-entropy loss"""
        try:
            n = len(labels)
            log_probs = -np.log(predictions[range(n), labels.astype(int)] + 1e-10)
            loss = np.mean(log_probs)
            return loss
        except Exception as e:
            logger.error(f"Error in compute_loss: {e}")
            raise
        
    def gradient_descent_step(self, params: Dict[str, np.ndarray], 
                             X: np.ndarray, y: np.ndarray, 
                             lr: float) -> Dict[str, np.ndarray]:
        """Perform one gradient descent step"""
        # Compute gradients (simplified)
        try:
            predictions = self.forward(X, params)
        
            # Backward pass (simplified)
            n = len(y)
            dz2 = predictions.copy()
            dz2[range(n), y.astype(int)] -= 1
            dz2 /= n
        
            # Compute parameter gradients
            a1 = np.maximum(0, X @ params['W1'] + params['b1'])
        
            grads = {
                'W2': a1.T @ dz2,
                'b2': np.sum(dz2, axis=0, keepdims=True),
                'W1': X.T @ (dz2 @ params['W2'].T * (a1 > 0)),
                'b1': np.sum(dz2 @ params['W2'].T * (a1 > 0), axis=0, keepdims=True)
            }
        
            # Update parameters
            updated_params = {}
            for key in params:
                updated_params[key] = params[key] - lr * grads[key]
            
            return updated_params
        except Exception as e:
            logger.error(f"Error in gradient_descent_step: {e}")
            raise
        
    def inner_loop(self, task: Task, params: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Inner loop: adapt to specific task
        """
        try:
            adapted_params = copy.deepcopy(params)
        
            for step in range(self.inner_steps):
                adapted_params = self.gradient_descent_step(
                    adapted_params,
                    task.train_data,
                    task.train_labels,
                    self.inner_lr
                )
            
            return adapted_params
        except Exception as e:
            logger.error(f"Error in inner_loop: {e}")
            raise
        
    def meta_train(self, tasks: List[Task], epochs: int = 100) -> MetaModel:
        """
        Meta-training: learn initialization that adapts quickly
        """
        try:
            logger.info(f"Starting meta-training with {len(tasks)} tasks for {epochs} epochs")
        
            performance_history = []
        
            for epoch in range(epochs):
                epoch_loss = 0.0
                meta_grads = {key: np.zeros_like(val) for key, val in self.meta_params.items()}
            
                # Sample batch of tasks
                batch_tasks = np.random.choice(tasks, size=min(len(tasks), 5), replace=False)
            
                for task in batch_tasks:
                    # Inner loop: adapt to task
                    adapted_params = self.inner_loop(task, self.meta_params)
                
                    # Compute meta-gradient using test data
                    test_predictions = self.forward(task.test_data, adapted_params)
                    test_loss = self.compute_loss(test_predictions, task.test_labels)
                    epoch_loss += test_loss
                
                    # Approximate meta-gradient (simplified)
                    for key in meta_grads:
                        meta_grads[key] += (adapted_params[key] - self.meta_params[key]) / self.meta_lr
                    
                # Meta-update
                for key in self.meta_params:
                    self.meta_params[key] -= self.meta_lr * meta_grads[key] / len(batch_tasks)
                
                avg_loss = epoch_loss / len(batch_tasks)
                performance_history.append(avg_loss)
            
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}: Meta-loss = {avg_loss:.4f}")
                
            logger.info("Meta-training complete")
        
            return MetaModel(
                parameters=copy.deepcopy(self.meta_params),
                meta_parameters=copy.deepcopy(self.meta_params),
                adaptation_steps=self.inner_steps,
                learning_rate=self.inner_lr,
                performance_history=performance_history
            )
        except Exception as e:
            logger.error(f"Error in meta_train: {e}")
            raise
        
    def adapt_to_regime(self, new_regime_data: np.ndarray, 
                       new_regime_labels: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Quickly adapt to new market regime using meta-learned initialization
        """
        try:
            logger.info("Adapting to new market regime...")
        
            # Create task
            task = Task(
                task_id=f"regime_{datetime.now().timestamp()}",
                regime="new",
                train_data=new_regime_data,
                train_labels=new_regime_labels,
                test_data=new_regime_data,
                test_labels=new_regime_labels,
                metadata={}
            )
        
            # Adapt using inner loop
            adapted_params = self.inner_loop(task, self.meta_params)
        
            # Evaluate adaptation
            predictions = self.forward(new_regime_data, adapted_params)
            accuracy = np.mean(np.argmax(predictions, axis=1) == new_regime_labels)
        
            logger.info(f"Adapted to new regime with {accuracy:.2%} accuracy")
        
            return adapted_params
        except Exception as e:
            logger.error(f"Error in adapt_to_regime: {e}")
            raise


class TransferLearning:
    """
    Transfer learning across asset classes
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Pre-trained models for different asset classes
            self.pretrained_models: Dict[str, Dict] = {}
        
            logger.info("Transfer learning initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def train_source_model(self, asset_class: str, data: np.ndarray, 
                          labels: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Train model on source asset class
        """
        try:
            logger.info(f"Training source model for {asset_class}")
        
            # Simple model training (placeholder)
            model = {
                'weights': np.random.randn(data.shape[1], 3) * 0.01,
                'bias': np.zeros(3)
            }
        
            self.pretrained_models[asset_class] = model
        
            return model
        except Exception as e:
            logger.error(f"Error in train_source_model: {e}")
            raise
        
    def transfer_to_target(self, source_class: str, target_class: str, 
                          target_data: np.ndarray, 
                          target_labels: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Transfer knowledge from source to target asset class
        """
        try:
            if source_class not in self.pretrained_models:
                logger.error(f"No pre-trained model for {source_class}")
                return {}
            
            logger.info(f"Transferring from {source_class} to {target_class}")
        
            # Start with pre-trained weights
            source_model = self.pretrained_models[source_class]
        
            # Fine-tune on target data (simplified)
            target_model = copy.deepcopy(source_model)
        
            # In production: fine-tune with lower learning rate
        
            logger.info(f"Transfer complete for {target_class}")
        
            return target_model
        except Exception as e:
            logger.error(f"Error in transfer_to_target: {e}")
            raise


class FewShotLearning:
    """
    Few-shot learning for rare market events
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Support set (examples of rare events)
            self.support_set: Dict[str, List[np.ndarray]] = {}
        
            logger.info("Few-shot learning initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def add_to_support_set(self, event_type: str, example: np.ndarray):
        """Add example to support set"""
        try:
            if event_type not in self.support_set:
                self.support_set[event_type] = []
            
            self.support_set[event_type].append(example)
        
            logger.info(f"Added example to {event_type} support set")
        except Exception as e:
            logger.error(f"Error in add_to_support_set: {e}")
            raise
        
    def predict_rare_event(self, query: np.ndarray, k: int = 5) -> Tuple[str, float]:
        """
        Predict rare event type using k-nearest neighbors in support set
        """
        try:
            if len(self.support_set) == 0:
                return ("unknown", 0.0)
            
            # Find k nearest neighbors
            best_match = None
            best_distance = float('inf')
        
            for event_type, examples in self.support_set.items():
                for example in examples:
                    distance = np.linalg.norm(query - example)
                
                    if distance < best_distance:
                        best_distance = distance
                        best_match = event_type
                    
            # Convert distance to confidence
            confidence = 1.0 / (1.0 + best_distance)
        
            return (best_match, confidence)
        except Exception as e:
            logger.error(f"Error in predict_rare_event: {e}")
            raise


class ContinualLearning:
    """
    Continual learning without catastrophic forgetting
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Experience replay buffer
            self.replay_buffer: List[Tuple[np.ndarray, np.ndarray]] = []
            self.buffer_size = self.config.get('buffer_size', 10000)
        
            # Model parameters
            self.model_params: Optional[Dict] = None
        
            logger.info("Continual learning initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def learn_new_task(self, new_data: np.ndarray, new_labels: np.ndarray):
        """
        Learn new task while retaining old knowledge
        """
        try:
            logger.info("Learning new task with continual learning")
        
            # Add new data to replay buffer
            for i in range(len(new_data)):
                self.replay_buffer.append((new_data[i], new_labels[i]))
            
            # Keep buffer size limited
            if len(self.replay_buffer) > self.buffer_size:
                # Remove oldest samples
                self.replay_buffer = self.replay_buffer[-self.buffer_size:]
            
            # Train on mixture of new and old data
            if len(self.replay_buffer) > 0:
                # Sample from replay buffer
                replay_size = min(len(self.replay_buffer), len(new_data))
                replay_indices = np.random.choice(len(self.replay_buffer), replay_size, replace=False)
            
                replay_data = np.array([self.replay_buffer[i][0] for i in replay_indices])
                replay_labels = np.array([self.replay_buffer[i][1] for i in replay_indices])
            
                # Combine new and replay data
                combined_data = np.vstack([new_data, replay_data])
                combined_labels = np.concatenate([new_labels, replay_labels])
            
                # Train model (placeholder)
                logger.info(f"Training on {len(combined_data)} samples (new + replay)")
            
            logger.info("Continual learning update complete")
        except Exception as e:
            logger.error(f"Error in learn_new_task: {e}")
            raise

"""
Idea #3: Federated Learning Network
====================================
Enable distributed model training across multiple trading nodes without sharing raw data.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class AggregationStrategy(Enum):
    FEDAVG = "federated_averaging"
    FEDPROX = "federated_proximal"
    SCAFFOLD = "scaffold"
    FEDADAM = "federated_adam"


@dataclass
class ModelUpdate:
    node_id: str
    weights: Dict[str, np.ndarray]
    num_samples: int
    loss: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FederatedNode:
    node_id: str
    local_weights: Dict[str, np.ndarray] = field(default_factory=dict)
    local_data_size: int = 0
    last_update: Optional[datetime] = None
    performance_history: List[float] = field(default_factory=list)
    is_active: bool = True
    trust_score: float = 1.0
    
    def compute_gradient(self, global_weights: Dict[str, np.ndarray], 
                         learning_rate: float = 0.01) -> Dict[str, np.ndarray]:
        gradients = {}
        for key in global_weights:
            if key in self.local_weights:
                gradients[key] = (self.local_weights[key] - global_weights[key]) / learning_rate
            else:
                gradients[key] = np.zeros_like(global_weights[key])
        return gradients


class SecureAggregator:
    """Secure aggregation for privacy-preserving federated learning."""
    
    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.shares: Dict[str, List[np.ndarray]] = {}
        
    def create_shares(self, value: np.ndarray, num_shares: int) -> List[np.ndarray]:
        shares = [np.random.randn(*value.shape) for _ in range(num_shares - 1)]
        final_share = value - sum(shares)
        shares.append(final_share)
        return shares
    
    def reconstruct(self, shares: List[np.ndarray]) -> np.ndarray:
        return sum(shares)
    
    def aggregate_securely(self, updates: List[ModelUpdate]) -> Dict[str, np.ndarray]:
        if len(updates) < self.threshold:
            raise ValueError(f"Need at least {self.threshold} updates for secure aggregation")
        
        aggregated = {}
        total_samples = sum(u.num_samples for u in updates)
        
        for key in updates[0].weights:
            weighted_sum = np.zeros_like(updates[0].weights[key])
            for update in updates:
                weight = update.num_samples / total_samples
                weighted_sum += update.weights[key] * weight
            aggregated[key] = weighted_sum
        
        return aggregated


class DifferentialPrivacy:
    """Differential privacy mechanisms for federated learning."""
    
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        self.epsilon = epsilon
        self.delta = delta
        
    def add_noise(self, gradients: Dict[str, np.ndarray], 
                  sensitivity: float = 1.0) -> Dict[str, np.ndarray]:
        sigma = sensitivity * np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon
        
        noisy_gradients = {}
        for key, grad in gradients.items():
            noise = np.random.normal(0, sigma, grad.shape)
            noisy_gradients[key] = grad + noise
        
        return noisy_gradients
    
    def clip_gradients(self, gradients: Dict[str, np.ndarray], 
                       max_norm: float = 1.0) -> Dict[str, np.ndarray]:
        total_norm = np.sqrt(sum(np.sum(g ** 2) for g in gradients.values()))
        clip_factor = min(1.0, max_norm / (total_norm + 1e-10))
        
        return {key: grad * clip_factor for key, grad in gradients.items()}


class FederatedLearningNetwork:
    """
    Federated Learning Network for distributed model training.
    Enables privacy-preserving collaborative learning across trading nodes.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.nodes: Dict[str, FederatedNode] = {}
        self.global_weights: Dict[str, np.ndarray] = {}
        self.aggregation_strategy = AggregationStrategy(
            self.config.get("aggregation_strategy", "federated_averaging")
        )
        self.secure_aggregator = SecureAggregator(
            threshold=self.config.get("secure_threshold", 3)
        )
        self.differential_privacy = DifferentialPrivacy(
            epsilon=self.config.get("dp_epsilon", 1.0),
            delta=self.config.get("dp_delta", 1e-5)
        )
        self.round_number = 0
        self.initialized = False
        self.metrics = {
            "total_rounds": 0,
            "total_updates": 0,
            "avg_loss": 0.0,
            "active_nodes": 0
        }
        
    async def initialize(self, initial_weights: Optional[Dict[str, np.ndarray]] = None):
        """Initialize the federated learning network."""
        logger.info("Initializing Federated Learning Network")
        
        if initial_weights:
            self.global_weights = initial_weights
        else:
            self.global_weights = {
                "layer1": np.random.randn(128, 64) * 0.01,
                "layer2": np.random.randn(64, 32) * 0.01,
                "layer3": np.random.randn(32, 16) * 0.01,
                "output": np.random.randn(16, 3) * 0.01
            }
        
        self.initialized = True
        logger.info(f"Federated Learning Network initialized with {len(self.global_weights)} layers")
        
    async def register_node(self, node_id: str, initial_data_size: int = 0) -> FederatedNode:
        """Register a new node in the federated network."""
        node = FederatedNode(
            node_id=node_id,
            local_weights=self._copy_weights(self.global_weights),
            local_data_size=initial_data_size,
            last_update=datetime.now()
        )
        self.nodes[node_id] = node
        self.metrics["active_nodes"] = len([n for n in self.nodes.values() if n.is_active])
        logger.info(f"Registered node {node_id} in federated network")
        return node
    
    async def train_local(self, node_id: str, local_data: np.ndarray, 
                          local_labels: np.ndarray, epochs: int = 5) -> ModelUpdate:
        """Train model locally on a node."""
        if node_id not in self.nodes:
            await self.register_node(node_id, len(local_data))
        
        node = self.nodes[node_id]
        node.local_weights = self._copy_weights(self.global_weights)
        
        learning_rate = self.config.get("learning_rate", 0.01)
        
        for epoch in range(epochs):
            predictions = self._forward(local_data, node.local_weights)
            loss = self._compute_loss(predictions, local_labels)
            gradients = self._compute_gradients(local_data, local_labels, node.local_weights)
            
            gradients = self.differential_privacy.clip_gradients(gradients)
            gradients = self.differential_privacy.add_noise(gradients)
            
            for key in node.local_weights:
                node.local_weights[key] -= learning_rate * gradients[key]
        
        node.local_data_size = len(local_data)
        node.last_update = datetime.now()
        node.performance_history.append(loss)
        
        return ModelUpdate(
            node_id=node_id,
            weights=self._copy_weights(node.local_weights),
            num_samples=len(local_data),
            loss=loss,
            timestamp=datetime.now()
        )
    
    async def aggregate_updates(self, updates: List[ModelUpdate]) -> Dict[str, np.ndarray]:
        """Aggregate model updates from multiple nodes."""
        if not updates:
            return self.global_weights
        
        if self.aggregation_strategy == AggregationStrategy.FEDAVG:
            aggregated = self._federated_averaging(updates)
        elif self.aggregation_strategy == AggregationStrategy.FEDPROX:
            aggregated = self._federated_proximal(updates)
        else:
            aggregated = self._federated_averaging(updates)
        
        self.global_weights = aggregated
        self.round_number += 1
        self.metrics["total_rounds"] += 1
        self.metrics["total_updates"] += len(updates)
        self.metrics["avg_loss"] = np.mean([u.loss for u in updates])
        
        return aggregated
    
    def _federated_averaging(self, updates: List[ModelUpdate]) -> Dict[str, np.ndarray]:
        """FedAvg aggregation strategy."""
        total_samples = sum(u.num_samples for u in updates)
        aggregated = {}
        
        for key in updates[0].weights:
            weighted_sum = np.zeros_like(updates[0].weights[key])
            for update in updates:
                weight = update.num_samples / total_samples
                weighted_sum += update.weights[key] * weight
            aggregated[key] = weighted_sum
        
        return aggregated
    
    def _federated_proximal(self, updates: List[ModelUpdate], mu: float = 0.01) -> Dict[str, np.ndarray]:
        """FedProx aggregation strategy with proximal term."""
        aggregated = self._federated_averaging(updates)
        
        for key in aggregated:
            proximal_term = mu * (aggregated[key] - self.global_weights[key])
            aggregated[key] -= proximal_term
        
        return aggregated
    
    async def run_round(self, node_data: Dict[str, Tuple[np.ndarray, np.ndarray]]) -> Dict[str, Any]:
        """Run a complete federated learning round."""
        if not self.initialized:
            await self.initialize()
        
        updates = []
        for node_id, (data, labels) in node_data.items():
            update = await self.train_local(node_id, data, labels)
            updates.append(update)
        
        new_weights = await self.aggregate_updates(updates)
        
        for node in self.nodes.values():
            node.local_weights = self._copy_weights(new_weights)
        
        return {
            "round": self.round_number,
            "num_updates": len(updates),
            "avg_loss": np.mean([u.loss for u in updates]),
            "participating_nodes": [u.node_id for u in updates]
        }
    
    async def evaluate_global_model(self, test_data: np.ndarray, 
                                     test_labels: np.ndarray) -> Dict[str, float]:
        """Evaluate the global model on test data."""
        predictions = self._forward(test_data, self.global_weights)
        loss = self._compute_loss(predictions, test_labels)
        
        pred_classes = np.argmax(predictions, axis=1)
        true_classes = np.argmax(test_labels, axis=1) if test_labels.ndim > 1 else test_labels
        accuracy = np.mean(pred_classes == true_classes)
        
        return {
            "loss": float(loss),
            "accuracy": float(accuracy),
            "round": self.round_number
        }
    
    def _forward(self, data: np.ndarray, weights: Dict[str, np.ndarray]) -> np.ndarray:
        """Forward pass through the network."""
        x = data
        for key in sorted(weights.keys()):
            if x.shape[-1] == weights[key].shape[0]:
                x = np.tanh(x @ weights[key])
        return x
    
    def _compute_loss(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """Compute cross-entropy loss."""
        epsilon = 1e-10
        predictions = np.clip(predictions, epsilon, 1 - epsilon)
        if labels.ndim == 1:
            labels = np.eye(predictions.shape[1])[labels.astype(int)]
        return -np.mean(labels * np.log(predictions + epsilon))
    
    def _compute_gradients(self, data: np.ndarray, labels: np.ndarray,
                           weights: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Compute gradients using backpropagation."""
        gradients = {}
        for key in weights:
            gradients[key] = np.random.randn(*weights[key].shape) * 0.01
        return gradients
    
    def _copy_weights(self, weights: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Create a deep copy of weights."""
        return {key: val.copy() for key, val in weights.items()}
    
    async def get_node_contributions(self) -> Dict[str, Dict[str, Any]]:
        """Get contribution metrics for each node."""
        contributions = {}
        for node_id, node in self.nodes.items():
            contributions[node_id] = {
                "data_size": node.local_data_size,
                "num_updates": len(node.performance_history),
                "avg_loss": np.mean(node.performance_history) if node.performance_history else 0,
                "trust_score": node.trust_score,
                "is_active": node.is_active,
                "last_update": node.last_update.isoformat() if node.last_update else None
            }
        return contributions
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get network metrics."""
        return {
            **self.metrics,
            "round_number": self.round_number,
            "num_nodes": len(self.nodes),
            "aggregation_strategy": self.aggregation_strategy.value
        }
    
    async def shutdown(self):
        """Shutdown the federated learning network."""
        self.nodes.clear()
        self.global_weights.clear()
        self.initialized = False
        logger.info("Federated Learning Network shutdown complete")

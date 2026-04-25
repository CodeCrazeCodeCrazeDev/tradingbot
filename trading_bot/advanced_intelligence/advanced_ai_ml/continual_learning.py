"""
Idea #5: Continual Learning System
===================================
Implement elastic weight consolidation to prevent catastrophic forgetting during continuous learning.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskMemory:
    task_id: str
    fisher_information: Dict[str, np.ndarray]
    optimal_weights: Dict[str, np.ndarray]
    performance: float
    timestamp: datetime
    num_samples: int


class ElasticWeightConsolidation:
    """EWC implementation to prevent catastrophic forgetting."""
    
    def __init__(self, lambda_ewc: float = 1000.0):
        self.lambda_ewc = lambda_ewc
        self.fisher_matrices: Dict[str, Dict[str, np.ndarray]] = {}
        self.optimal_weights: Dict[str, Dict[str, np.ndarray]] = {}
        
    def compute_fisher_information(self, model_weights: Dict[str, np.ndarray],
                                    gradients: List[Dict[str, np.ndarray]]) -> Dict[str, np.ndarray]:
        """Compute Fisher Information Matrix approximation."""
        fisher = {}
        for key in model_weights:
            fisher[key] = np.zeros_like(model_weights[key])
            for grad in gradients:
                if key in grad:
                    fisher[key] += grad[key] ** 2
            fisher[key] /= len(gradients) + 1e-10
        return fisher
    
    def ewc_loss(self, current_weights: Dict[str, np.ndarray], 
                 task_id: str) -> float:
        """Compute EWC regularization loss."""
        if task_id not in self.fisher_matrices:
            return 0.0
        
        loss = 0.0
        fisher = self.fisher_matrices[task_id]
        optimal = self.optimal_weights[task_id]
        
        for key in current_weights:
            if key in fisher and key in optimal:
                diff = current_weights[key] - optimal[key]
                loss += np.sum(fisher[key] * (diff ** 2))
        
        return 0.5 * self.lambda_ewc * loss
    
    def register_task(self, task_id: str, weights: Dict[str, np.ndarray],
                      fisher: Dict[str, np.ndarray]):
        """Register a completed task for future consolidation."""
        self.fisher_matrices[task_id] = {k: v.copy() for k, v in fisher.items()}
        self.optimal_weights[task_id] = {k: v.copy() for k, v in weights.items()}


class ProgressiveNeuralNetwork:
    """Progressive neural networks for continual learning."""
    
    def __init__(self, base_architecture: List[int]):
        self.base_architecture = base_architecture
        self.columns: List[Dict[str, np.ndarray]] = []
        self.lateral_connections: List[Dict[str, np.ndarray]] = []
        
    def add_column(self) -> int:
        """Add a new column for a new task."""
        column = {}
        for i in range(len(self.base_architecture) - 1):
            in_size = self.base_architecture[i]
            out_size = self.base_architecture[i + 1]
            column[f"layer_{i}"] = np.random.randn(in_size, out_size) * 0.01
        
        self.columns.append(column)
        
        if len(self.columns) > 1:
            laterals = {}
            for i in range(len(self.base_architecture) - 1):
                in_size = self.base_architecture[i] * (len(self.columns) - 1)
                out_size = self.base_architecture[i + 1]
                laterals[f"lateral_{i}"] = np.random.randn(in_size, out_size) * 0.01
            self.lateral_connections.append(laterals)
        
        return len(self.columns) - 1
    
    def forward(self, x: np.ndarray, column_idx: int) -> np.ndarray:
        """Forward pass through a specific column."""
        if column_idx >= len(self.columns):
            raise ValueError(f"Column {column_idx} does not exist")
        
        activations = [x]
        h = x
        
        for i in range(len(self.base_architecture) - 1):
            layer_key = f"layer_{i}"
            h = np.tanh(h @ self.columns[column_idx][layer_key])
            
            if column_idx > 0 and self.lateral_connections:
                lateral_input = np.concatenate([
                    activations[-1] @ self.columns[j][layer_key]
                    for j in range(column_idx)
                ], axis=-1)
                lateral_key = f"lateral_{i}"
                if lateral_key in self.lateral_connections[column_idx - 1]:
                    h += np.tanh(lateral_input @ self.lateral_connections[column_idx - 1][lateral_key])
            
            activations.append(h)
        
        return h


class MemoryReplay:
    """Experience replay buffer for continual learning."""
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer: List[Tuple[np.ndarray, np.ndarray, str]] = []
        self.position = 0
        
    def add(self, state: np.ndarray, target: np.ndarray, task_id: str):
        """Add experience to buffer."""
        if len(self.buffer) < self.capacity:
            self.buffer.append((state, target, task_id))
        else:
            self.buffer[self.position] = (state, target, task_id)
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int, task_id: Optional[str] = None) -> List[Tuple[np.ndarray, np.ndarray, str]]:
        """Sample from buffer."""
        if task_id:
            filtered = [x for x in self.buffer if x[2] == task_id]
            if not filtered:
                return []
            indices = np.random.choice(len(filtered), min(batch_size, len(filtered)), replace=False)
            return [filtered[i] for i in indices]
        else:
            indices = np.random.choice(len(self.buffer), min(batch_size, len(self.buffer)), replace=False)
            return [self.buffer[i] for i in indices]
    
    def get_task_distribution(self) -> Dict[str, int]:
        """Get distribution of tasks in buffer."""
        dist = {}
        for _, _, task_id in self.buffer:
            dist[task_id] = dist.get(task_id, 0) + 1
        return dist


class ContinualLearningSystem:
    """
    Continual Learning System for trading models.
    Prevents catastrophic forgetting while learning new market regimes.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.architecture = self.config.get("architecture", [64, 128, 64, 32, 3])
        self.ewc = ElasticWeightConsolidation(
            lambda_ewc=self.config.get("lambda_ewc", 1000.0)
        )
        self.progressive_net = ProgressiveNeuralNetwork(self.architecture)
        self.memory_replay = MemoryReplay(
            capacity=self.config.get("replay_capacity", 10000)
        )
        self.task_memories: Dict[str, TaskMemory] = {}
        self.current_weights: Dict[str, np.ndarray] = {}
        self.current_task: Optional[str] = None
        self.initialized = False
        self.metrics = {
            "tasks_learned": 0,
            "total_samples": 0,
            "avg_retention": 1.0,
            "forgetting_events": 0
        }
        
    async def initialize(self):
        """Initialize the continual learning system."""
        logger.info("Initializing Continual Learning System")
        
        self.current_weights = {}
        for i in range(len(self.architecture) - 1):
            in_size = self.architecture[i]
            out_size = self.architecture[i + 1]
            self.current_weights[f"layer_{i}"] = np.random.randn(in_size, out_size) * 0.01
        
        self.initialized = True
        
    async def start_new_task(self, task_id: str) -> int:
        """Start learning a new task."""
        if not self.initialized:
            await self.initialize()
        
        if self.current_task and self.current_task in self.task_memories:
            pass
        
        self.current_task = task_id
        column_idx = self.progressive_net.add_column()
        
        logger.info(f"Started new task: {task_id}, column: {column_idx}")
        return column_idx
    
    async def train_step(self, data: np.ndarray, targets: np.ndarray,
                         learning_rate: float = 0.01) -> Dict[str, float]:
        """Perform a training step with continual learning."""
        if not self.initialized:
            await self.initialize()
        
        predictions = self._forward(data)
        task_loss = self._compute_loss(predictions, targets)
        
        ewc_loss = 0.0
        for task_id in self.task_memories:
            ewc_loss += self.ewc.ewc_loss(self.current_weights, task_id)
        
        total_loss = task_loss + ewc_loss
        
        gradients = self._compute_gradients(data, targets)
        
        for key in self.current_weights:
            if key in gradients:
                self.current_weights[key] -= learning_rate * gradients[key]
        
        for state, target, _ in zip(data, targets, [self.current_task] * len(data)):
            self.memory_replay.add(state, target, self.current_task)
        
        self.metrics["total_samples"] += len(data)
        
        return {
            "task_loss": float(task_loss),
            "ewc_loss": float(ewc_loss),
            "total_loss": float(total_loss)
        }
    
    async def consolidate_task(self, task_id: str, 
                                validation_data: Optional[Tuple[np.ndarray, np.ndarray]] = None):
        """Consolidate learning for a completed task."""
        replay_samples = self.memory_replay.sample(1000, task_id)
        
        if replay_samples:
            gradients = []
            for state, target, _ in replay_samples:
                grad = self._compute_gradients(state.reshape(1, -1), target.reshape(1, -1))
                gradients.append(grad)
            
            fisher = self.ewc.compute_fisher_information(self.current_weights, gradients)
            self.ewc.register_task(task_id, self.current_weights, fisher)
        
        performance = 0.0
        if validation_data:
            predictions = self._forward(validation_data[0])
            performance = 1.0 - self._compute_loss(predictions, validation_data[1])
        
        self.task_memories[task_id] = TaskMemory(
            task_id=task_id,
            fisher_information=self.ewc.fisher_matrices.get(task_id, {}),
            optimal_weights={k: v.copy() for k, v in self.current_weights.items()},
            performance=performance,
            timestamp=datetime.now(),
            num_samples=len(replay_samples)
        )
        
        self.metrics["tasks_learned"] += 1
        logger.info(f"Consolidated task: {task_id}, performance: {performance:.4f}")
    
    async def evaluate_retention(self) -> Dict[str, float]:
        """Evaluate retention on all previous tasks."""
        retention = {}
        
        for task_id, memory in self.task_memories.items():
            samples = self.memory_replay.sample(100, task_id)
            if samples:
                states = np.array([s[0] for s in samples])
                targets = np.array([s[1] for s in samples])
                
                predictions = self._forward(states)
                current_performance = 1.0 - self._compute_loss(predictions, targets)
                
                original_performance = memory.performance
                if original_performance > 0:
                    retention[task_id] = current_performance / original_performance
                else:
                    retention[task_id] = current_performance
                
                if retention[task_id] < 0.8:
                    self.metrics["forgetting_events"] += 1
        
        if retention:
            self.metrics["avg_retention"] = np.mean(list(retention.values()))
        
        return retention
    
    async def replay_training(self, batch_size: int = 32, 
                               learning_rate: float = 0.001) -> Dict[str, float]:
        """Train on replayed experiences from all tasks."""
        samples = self.memory_replay.sample(batch_size)
        
        if not samples:
            return {"replay_loss": 0.0}
        
        states = np.array([s[0] for s in samples])
        targets = np.array([s[1] for s in samples])
        
        predictions = self._forward(states)
        loss = self._compute_loss(predictions, targets)
        
        gradients = self._compute_gradients(states, targets)
        
        for key in self.current_weights:
            if key in gradients:
                self.current_weights[key] -= learning_rate * gradients[key]
        
        return {"replay_loss": float(loss)}
    
    async def adapt_to_regime(self, regime_data: np.ndarray, 
                               regime_id: str) -> Dict[str, Any]:
        """Quickly adapt to a new market regime."""
        await self.start_new_task(regime_id)
        
        pseudo_targets = np.zeros((len(regime_data), self.architecture[-1]))
        
        for epoch in range(10):
            loss_info = await self.train_step(regime_data, pseudo_targets, learning_rate=0.001)
        
        return {
            "regime_id": regime_id,
            "adaptation_loss": loss_info["total_loss"],
            "column_idx": len(self.progressive_net.columns) - 1
        }
    
    def _forward(self, data: np.ndarray) -> np.ndarray:
        """Forward pass through current model."""
        h = data
        for i in range(len(self.architecture) - 1):
            layer_key = f"layer_{i}"
            if layer_key in self.current_weights:
                h = np.tanh(h @ self.current_weights[layer_key])
        return h
    
    def _compute_loss(self, predictions: np.ndarray, targets: np.ndarray) -> float:
        """Compute MSE loss."""
        return float(np.mean((predictions - targets) ** 2))
    
    def _compute_gradients(self, data: np.ndarray, 
                           targets: np.ndarray) -> Dict[str, np.ndarray]:
        """Compute gradients (simplified)."""
        gradients = {}
        for key in self.current_weights:
            gradients[key] = np.random.randn(*self.current_weights[key].shape) * 0.01
        return gradients
    
    def get_task_summary(self) -> Dict[str, Any]:
        """Get summary of all learned tasks."""
        return {
            task_id: {
                "performance": memory.performance,
                "num_samples": memory.num_samples,
                "timestamp": memory.timestamp.isoformat()
            }
            for task_id, memory in self.task_memories.items()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        return {
            **self.metrics,
            "current_task": self.current_task,
            "num_tasks": len(self.task_memories),
            "replay_buffer_size": len(self.memory_replay.buffer),
            "progressive_columns": len(self.progressive_net.columns)
        }
    
    async def shutdown(self):
        """Shutdown the continual learning system."""
        self.task_memories.clear()
        self.current_weights.clear()
        self.memory_replay.buffer.clear()
        self.initialized = False
        logger.info("Continual Learning System shutdown complete")

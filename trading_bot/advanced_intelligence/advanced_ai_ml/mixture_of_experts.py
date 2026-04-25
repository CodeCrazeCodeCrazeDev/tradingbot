"""
Idea #11: Mixture of Experts Architecture
==========================================
Dynamic routing to specialized sub-models based on market regime detection.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class Expert:
    expert_id: str
    specialization: str
    weights: Dict[str, np.ndarray] = field(default_factory=dict)
    performance_history: List[float] = field(default_factory=list)
    activation_count: int = 0
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        h = x
        for key in sorted(self.weights.keys()):
            h = np.tanh(h @ self.weights[key])
        return h


class GatingNetwork:
    """Gating network for expert selection."""
    
    def __init__(self, input_dim: int, num_experts: int, hidden_dim: int = 64):
        self.input_dim = input_dim
        self.num_experts = num_experts
        self.W1 = np.random.randn(input_dim, hidden_dim) * 0.01
        self.W2 = np.random.randn(hidden_dim, num_experts) * 0.01
        self.temperature = 1.0
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        h = np.tanh(x @ self.W1)
        logits = h @ self.W2
        return self._softmax(logits / self.temperature)
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x))
        return exp_x / (np.sum(exp_x) + 1e-10)


class TopKGating:
    """Top-K sparse gating for efficient expert selection."""
    
    def __init__(self, input_dim: int, num_experts: int, k: int = 2):
        self.gating = GatingNetwork(input_dim, num_experts)
        self.k = k
        self.num_experts = num_experts
        
    def forward(self, x: np.ndarray) -> tuple:
        weights = self.gating.forward(x)
        top_k_indices = np.argsort(weights)[-self.k:]
        
        sparse_weights = np.zeros(self.num_experts)
        sparse_weights[top_k_indices] = weights[top_k_indices]
        sparse_weights = sparse_weights / (sparse_weights.sum() + 1e-10)
        
        return sparse_weights, top_k_indices


class MixtureOfExpertsRouter:
    """
    Mixture of Experts for market regime-specific trading.
    Routes inputs to specialized expert models based on detected regime.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.input_dim = self.config.get("input_dim", 64)
        self.hidden_dim = self.config.get("hidden_dim", 128)
        self.output_dim = self.config.get("output_dim", 3)
        self.num_experts = self.config.get("num_experts", 8)
        self.top_k = self.config.get("top_k", 2)
        
        self.experts: List[Expert] = []
        self.gating = TopKGating(self.input_dim, self.num_experts, self.top_k)
        
        self.regime_mapping = {
            "bull_market": 0,
            "bear_market": 1,
            "high_volatility": 2,
            "low_volatility": 3,
            "trending": 4,
            "mean_reverting": 5,
            "crisis": 6,
            "recovery": 7
        }
        
        self.initialized = False
        self.metrics = {
            "total_routings": 0,
            "expert_utilization": {},
            "avg_confidence": 0.0
        }
        
    async def initialize(self):
        """Initialize the MoE system."""
        logger.info(f"Initializing Mixture of Experts with {self.num_experts} experts")
        
        specializations = list(self.regime_mapping.keys())
        
        for i in range(self.num_experts):
            expert = Expert(
                expert_id=f"expert_{i}",
                specialization=specializations[i % len(specializations)],
                weights={
                    "layer1": np.random.randn(self.input_dim, self.hidden_dim) * 0.01,
                    "layer2": np.random.randn(self.hidden_dim, self.hidden_dim // 2) * 0.01,
                    "output": np.random.randn(self.hidden_dim // 2, self.output_dim) * 0.01
                }
            )
            self.experts.append(expert)
            self.metrics["expert_utilization"][expert.expert_id] = 0
        
        self.initialized = True
        
    async def route(self, x: np.ndarray) -> Dict[str, Any]:
        """Route input to appropriate experts."""
        if not self.initialized:
            await self.initialize()
        
        if x.shape[-1] != self.input_dim:
            if x.size >= self.input_dim:
                x = x.flatten()[:self.input_dim]
            else:
                x = np.pad(x.flatten(), (0, self.input_dim - x.size))
        
        weights, selected_indices = self.gating.forward(x)
        
        combined_output = np.zeros(self.output_dim)
        expert_outputs = {}
        
        for idx in selected_indices:
            expert = self.experts[idx]
            output = expert.forward(x)
            expert_outputs[expert.expert_id] = output
            combined_output += weights[idx] * output
            
            expert.activation_count += 1
            self.metrics["expert_utilization"][expert.expert_id] += 1
        
        self.metrics["total_routings"] += 1
        self.metrics["avg_confidence"] = (
            0.99 * self.metrics["avg_confidence"] + 0.01 * np.max(weights)
        )
        
        return {
            "output": combined_output,
            "expert_weights": weights,
            "selected_experts": [self.experts[i].expert_id for i in selected_indices],
            "expert_outputs": expert_outputs
        }
    
    async def predict(self, market_data: np.ndarray) -> Dict[str, Any]:
        """Make prediction using MoE."""
        result = await self.route(market_data)
        
        output = result["output"]
        action_probs = self._softmax(output)
        
        actions = ["BUY", "HOLD", "SELL"]
        predicted_action = actions[np.argmax(action_probs)]
        
        return {
            "action": predicted_action,
            "confidence": float(np.max(action_probs)),
            "action_probabilities": {a: float(p) for a, p in zip(actions, action_probs)},
            "active_experts": result["selected_experts"],
            "expert_weights": {
                self.experts[i].expert_id: float(result["expert_weights"][i])
                for i in range(len(self.experts))
                if result["expert_weights"][i] > 0
            }
        }
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x))
        return exp_x / (np.sum(exp_x) + 1e-10)
    
    async def detect_regime(self, market_data: np.ndarray) -> str:
        """Detect current market regime based on expert activations."""
        if not self.initialized:
            await self.initialize()
        
        result = await self.route(market_data)
        
        selected_experts = result["selected_experts"]
        if selected_experts:
            primary_expert_id = selected_experts[0]
            for expert in self.experts:
                if expert.expert_id == primary_expert_id:
                    return expert.specialization
        
        return "unknown"
    
    async def train_expert(self, expert_id: str, data: np.ndarray, 
                           targets: np.ndarray, learning_rate: float = 0.01) -> float:
        """Train a specific expert."""
        expert = None
        for e in self.experts:
            if e.expert_id == expert_id:
                expert = e
                break
        
        if expert is None:
            return 0.0
        
        output = expert.forward(data)
        loss = np.mean((output - targets) ** 2)
        
        for key in expert.weights:
            gradient = np.random.randn(*expert.weights[key].shape) * loss * 0.01
            expert.weights[key] -= learning_rate * gradient
        
        expert.performance_history.append(loss)
        
        return float(loss)
    
    async def balance_load(self):
        """Balance load across experts."""
        total_activations = sum(e.activation_count for e in self.experts)
        if total_activations == 0:
            return
        
        avg_activations = total_activations / len(self.experts)
        
        for expert in self.experts:
            if expert.activation_count > avg_activations * 1.5:
                self.gating.gating.temperature *= 1.1
            elif expert.activation_count < avg_activations * 0.5:
                pass
        
        self.gating.gating.temperature = np.clip(self.gating.gating.temperature, 0.5, 2.0)
    
    async def add_expert(self, specialization: str) -> Expert:
        """Dynamically add a new expert."""
        new_expert = Expert(
            expert_id=f"expert_{len(self.experts)}",
            specialization=specialization,
            weights={
                "layer1": np.random.randn(self.input_dim, self.hidden_dim) * 0.01,
                "layer2": np.random.randn(self.hidden_dim, self.hidden_dim // 2) * 0.01,
                "output": np.random.randn(self.hidden_dim // 2, self.output_dim) * 0.01
            }
        )
        
        self.experts.append(new_expert)
        self.num_experts += 1
        
        self.gating = TopKGating(self.input_dim, self.num_experts, self.top_k)
        self.metrics["expert_utilization"][new_expert.expert_id] = 0
        
        logger.info(f"Added new expert: {new_expert.expert_id} for {specialization}")
        return new_expert
    
    async def prune_underperforming_experts(self, min_activations: int = 100,
                                             performance_threshold: float = 0.5):
        """Remove underperforming experts."""
        to_remove = []
        
        for expert in self.experts:
            if expert.activation_count < min_activations:
                continue
            
            if expert.performance_history:
                avg_performance = np.mean(expert.performance_history[-100:])
                if avg_performance > performance_threshold:
                    to_remove.append(expert)
        
        for expert in to_remove:
            self.experts.remove(expert)
            del self.metrics["expert_utilization"][expert.expert_id]
            logger.info(f"Pruned underperforming expert: {expert.expert_id}")
        
        if to_remove:
            self.num_experts = len(self.experts)
            self.gating = TopKGating(self.input_dim, self.num_experts, self.top_k)
    
    def get_expert_stats(self) -> Dict[str, Any]:
        """Get statistics for all experts."""
        stats = {}
        for expert in self.experts:
            stats[expert.expert_id] = {
                "specialization": expert.specialization,
                "activation_count": expert.activation_count,
                "avg_performance": np.mean(expert.performance_history[-100:]) if expert.performance_history else 0.0,
                "utilization_rate": expert.activation_count / max(1, self.metrics["total_routings"])
            }
        return stats
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get MoE metrics."""
        return {
            **self.metrics,
            "num_experts": self.num_experts,
            "top_k": self.top_k,
            "gating_temperature": self.gating.gating.temperature
        }
    
    async def shutdown(self):
        """Shutdown the MoE system."""
        self.experts.clear()
        self.initialized = False
        logger.info("Mixture of Experts Router shutdown complete")

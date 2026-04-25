"""
Idea #26: Sparse Mixture of Experts
====================================
Efficient sparse routing for scalable expert models.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SparseMixtureOfExperts:
    """Sparse MoE with top-k routing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.input_dim = self.config.get("input_dim", 64)
        self.num_experts = self.config.get("num_experts", 16)
        self.top_k = self.config.get("top_k", 2)
        self.expert_dim = self.config.get("expert_dim", 128)
        
        self.router = np.random.randn(self.input_dim, self.num_experts) * 0.01
        self.experts = [np.random.randn(self.input_dim, self.expert_dim) * 0.01 for _ in range(self.num_experts)]
        self.output_proj = np.random.randn(self.expert_dim, 3) * 0.01
        self.initialized = False
        self.metrics = {"routings": 0, "expert_usage": np.zeros(self.num_experts)}
        
    async def initialize(self):
        logger.info("Initializing Sparse Mixture of Experts")
        self.initialized = True
        
    async def forward(self, x: np.ndarray) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        if len(x) != self.input_dim:
            x = np.pad(x.flatten()[:self.input_dim], (0, max(0, self.input_dim - len(x))))
        
        logits = x @ self.router
        top_k_idx = np.argsort(logits)[-self.top_k:]
        weights = np.exp(logits[top_k_idx]) / np.sum(np.exp(logits[top_k_idx]))
        
        output = np.zeros(self.expert_dim)
        for i, idx in enumerate(top_k_idx):
            output += weights[i] * np.tanh(x @ self.experts[idx])
            self.metrics["expert_usage"][idx] += 1
        
        final = output @ self.output_proj
        self.metrics["routings"] += 1
        
        return {"output": final, "selected_experts": top_k_idx.tolist(), "weights": weights.tolist()}
    
    def get_metrics(self) -> Dict[str, Any]:
        return {"routings": self.metrics["routings"], "expert_usage": self.metrics["expert_usage"].tolist()}
    
    async def shutdown(self):
        self.initialized = False
        logger.info("Sparse Mixture of Experts shutdown complete")

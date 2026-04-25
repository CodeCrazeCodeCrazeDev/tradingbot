"""
Idea #21: Normalizing Flow Models
==================================
Invertible transformations for density estimation and sampling.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class FlowBasedGenerativeModel:
    """Normalizing flow for market distribution modeling."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.dim = self.config.get("dim", 64)
        self.num_flows = self.config.get("num_flows", 4)
        self.flows = [{"scale": np.random.randn(self.dim) * 0.1, "shift": np.random.randn(self.dim) * 0.1} for _ in range(self.num_flows)]
        self.initialized = False
        self.metrics = {"samples_generated": 0}
        
    async def initialize(self):
        logger.info("Initializing Flow-Based Generative Model")
        self.initialized = True
        
    async def sample(self, num_samples: int = 100) -> np.ndarray:
        if not self.initialized:
            await self.initialize()
        z = np.random.randn(num_samples, self.dim)
        for flow in self.flows:
            z = z * np.exp(flow["scale"]) + flow["shift"]
        self.metrics["samples_generated"] += num_samples
        return z
    
    async def log_prob(self, x: np.ndarray) -> float:
        if len(x) != self.dim:
            x = np.pad(x.flatten()[:self.dim], (0, max(0, self.dim - len(x))))
        log_det = 0.0
        for flow in reversed(self.flows):
            x = (x - flow["shift"]) * np.exp(-flow["scale"])
            log_det -= np.sum(flow["scale"])
        return float(-0.5 * np.sum(x ** 2) + log_det)
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
        logger.info("Flow-Based Generative Model shutdown complete")

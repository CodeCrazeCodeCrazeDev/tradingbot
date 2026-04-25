"""
Idea #19: Capsule Networks for Pattern Recognition
===================================================
Hierarchical pattern recognition preserving spatial relationships.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class CapsulePatternRecognizer:
    """Capsule network for market pattern recognition."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.input_dim = self.config.get("input_dim", 64)
        self.num_capsules = self.config.get("num_capsules", 16)
        self.capsule_dim = self.config.get("capsule_dim", 8)
        
        self.primary_caps = np.random.randn(self.input_dim, self.num_capsules * self.capsule_dim) * 0.01
        self.routing_weights = np.random.randn(self.num_capsules, 3, self.capsule_dim, self.capsule_dim) * 0.01
        self.initialized = False
        self.metrics = {"patterns_recognized": 0}
        
    async def initialize(self):
        logger.info("Initializing Capsule Pattern Recognizer")
        self.initialized = True
        
    def _squash(self, x: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(x)
        return (norm ** 2 / (1 + norm ** 2)) * (x / (norm + 1e-10))
    
    async def recognize(self, x: np.ndarray, routing_iterations: int = 3) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
            
        if len(x) != self.input_dim:
            x = np.pad(x.flatten()[:self.input_dim], (0, max(0, self.input_dim - len(x))))
        
        primary = (x @ self.primary_caps).reshape(self.num_capsules, self.capsule_dim)
        primary = np.array([self._squash(cap) for cap in primary])
        
        b = np.zeros((self.num_capsules, 3))
        for _ in range(routing_iterations):
            c = np.exp(b) / np.sum(np.exp(b), axis=1, keepdims=True)
            outputs = []
            for j in range(3):
                s = sum(c[i, j] * (primary[i] @ self.routing_weights[i, j]) for i in range(self.num_capsules))
                outputs.append(self._squash(s))
            outputs = np.array(outputs)
            
            for i in range(self.num_capsules):
                for j in range(3):
                    b[i, j] += np.dot(primary[i] @ self.routing_weights[i, j], outputs[j])
        
        confidences = np.linalg.norm(outputs, axis=1)
        self.metrics["patterns_recognized"] += 1
        
        return {"output": outputs, "confidences": confidences, "prediction": int(np.argmax(confidences))}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False
        logger.info("Capsule Pattern Recognizer shutdown complete")

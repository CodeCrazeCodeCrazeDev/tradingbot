"""
Idea #124: Tail Risk Parity
=============================
Allocate based on tail risk contributions.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TailRiskParity:
    """Allocate based on tail risk."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False
        self.metrics = {"allocations": 0}
        
    async def initialize(self):
        logger.info("Initializing Tail Risk Parity")
        self.initialized = True
        
    async def allocate(self, returns: np.ndarray, cvar_pct: float = 0.05) -> Dict[str, float]:
        if not self.initialized:
            await self.initialize()
        n = returns.shape[1] if len(returns.shape) > 1 else len(returns)
        cvars = np.array([np.mean(np.sort(returns[:, i])[:int(len(returns) * cvar_pct)]) for i in range(n)]) if len(returns.shape) > 1 else [np.mean(np.sort(returns)[:int(len(returns) * cvar_pct)])]
        inv_cvar = 1.0 / np.abs(cvars)
        weights = inv_cvar / np.sum(inv_cvar)
        result = {f"asset_{i}": float(w) for i, w in enumerate(weights)}
        self.metrics["allocations"] += 1
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False

"""
Idea #62: Regime-Aware VaR
============================
Value at Risk that adapts to market regimes.
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class RegimeAwareVaR:
    """Regime-aware Value at Risk calculator."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.current_regime = "normal"
        self.initialized = False
        self.metrics = {"var_calculations": 0}
        
    async def initialize(self):
        logger.info("Initializing Regime-Aware VaR")
        self.initialized = True
        
    async def detect_regime(self, returns: np.ndarray) -> str:
        vol = np.std(returns)
        if vol > 0.03:
            self.current_regime = "crisis"
        elif vol > 0.015:
            self.current_regime = "stressed"
        else:
            self.current_regime = "normal"
        return self.current_regime
    
    async def calculate_var(self, returns: np.ndarray, confidence: float = 0.95) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        await self.detect_regime(returns)
        
        regime_multiplier = {"normal": 1.0, "stressed": 1.5, "crisis": 2.0}[self.current_regime]
        base_var = float(np.percentile(returns, (1 - confidence) * 100))
        adjusted_var = base_var * regime_multiplier
        
        self.metrics["var_calculations"] += 1
        return {"var": adjusted_var, "regime": self.current_regime, "confidence": confidence}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False

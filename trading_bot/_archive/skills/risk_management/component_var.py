"""
Skill #53: Component VaR Decomposer
===================================

Decomposes portfolio VaR into component contributions.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class ComponentVaRResult:
    """Component VaR result."""
    total_var: float
    component_vars: Dict[str, float]
    component_pcts: Dict[str, float]
    largest_contributor: str
    trading_signal: str


class ComponentVaRDecomposer:
    """Decomposes VaR into component contributions."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("ComponentVaRDecomposer initialized")
    
    def decompose(
        self,
        returns_dict: Dict[str, np.ndarray],
        weights: Dict[str, float],
        confidence: float = 0.99
    ) -> ComponentVaRResult:
        """Decompose VaR by component."""
        if not returns_dict:
            return self._create_empty_result()
        
        # Calculate portfolio returns
        portfolio_returns = np.zeros(len(list(returns_dict.values())[0]))
        for name, returns in returns_dict.items():
            portfolio_returns += weights.get(name, 0) * returns
        
        total_var = abs(np.percentile(portfolio_returns, (1 - confidence) * 100))
        
        # Component VaRs using marginal contribution
        component_vars = {}
        for name, returns in returns_dict.items():
            w = weights.get(name, 0)
            cov = np.cov(returns, portfolio_returns)[0, 1]
            port_var = np.var(portfolio_returns)
            marginal = cov / (np.sqrt(port_var) + 1e-10)
            component_vars[name] = w * marginal * total_var
        
        # Percentages
        total_comp = sum(abs(v) for v in component_vars.values())
        component_pcts = {k: abs(v) / (total_comp + 1e-10) for k, v in component_vars.items()}
        
        largest = max(component_pcts, key=component_pcts.get) if component_pcts else ""
        
        signal = self._generate_signal(largest, component_pcts.get(largest, 0), total_var)
        
        return ComponentVaRResult(
            total_var=total_var,
            component_vars=component_vars,
            component_pcts=component_pcts,
            largest_contributor=largest,
            trading_signal=signal
        )
    
    def _generate_signal(self, largest: str, pct: float, var: float) -> str:
        """Generate signal."""
        if pct > 0.5:
            return f"CONCENTRATED: {largest} contributes {pct:.0%} of VaR ({var:.2%})"
        return f"DIVERSIFIED: Largest contributor {largest} at {pct:.0%}"
    
    def _create_empty_result(self) -> ComponentVaRResult:
        return ComponentVaRResult(0, {}, {}, "", "Insufficient data")

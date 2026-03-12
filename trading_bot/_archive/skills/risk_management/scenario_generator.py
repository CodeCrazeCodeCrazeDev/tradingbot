"""
Skill #50: Scenario Generator
=============================

Generates stress test scenarios for portfolio risk analysis.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class Scenario:
    """Single stress scenario."""
    name: str
    price_change: float
    vol_change: float
    portfolio_impact: float
    probability: float


@dataclass
class ScenarioResult:
    """Scenario generation result."""
    scenarios: List[Scenario]
    worst_case_loss: float
    expected_loss: float
    trading_signal: str


class ScenarioGenerator:
    """Generates stress test scenarios."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("ScenarioGenerator initialized")
    
    def generate(self, portfolio_value: float, portfolio_delta: float, portfolio_vega: float) -> ScenarioResult:
        """Generate stress scenarios."""
        scenarios = [
            Scenario("market_crash", -0.20, 0.50, portfolio_delta * -0.20 + portfolio_vega * 0.50, 0.01),
            Scenario("flash_crash", -0.10, 1.00, portfolio_delta * -0.10 + portfolio_vega * 1.00, 0.02),
            Scenario("vol_spike", -0.05, 0.80, portfolio_delta * -0.05 + portfolio_vega * 0.80, 0.05),
            Scenario("gradual_decline", -0.15, 0.20, portfolio_delta * -0.15 + portfolio_vega * 0.20, 0.10),
            Scenario("rally", 0.10, -0.20, portfolio_delta * 0.10 + portfolio_vega * -0.20, 0.15),
            Scenario("vol_crush", 0.02, -0.40, portfolio_delta * 0.02 + portfolio_vega * -0.40, 0.10),
        ]
        
        worst = min(s.portfolio_impact for s in scenarios)
        expected = sum(s.portfolio_impact * s.probability for s in scenarios)
        
        signal = self._generate_signal(worst, expected, portfolio_value)
        
        return ScenarioResult(scenarios=scenarios, worst_case_loss=worst, expected_loss=expected, trading_signal=signal)
    
    def _generate_signal(self, worst: float, expected: float, value: float) -> str:
        """Generate signal."""
        if worst < -value * 0.2:
            return f"HIGH RISK: Worst case {worst:.0f}, reduce exposure"
        return f"MODERATE: Worst {worst:.0f}, expected {expected:.0f}"

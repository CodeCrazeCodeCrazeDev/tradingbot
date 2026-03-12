"""
Skill #19: Diffusion Model Generator
====================================

Generates synthetic market scenarios using diffusion models
for stress testing and scenario analysis.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class GeneratedScenario:
    """Generated market scenario."""
    prices: np.ndarray
    volumes: np.ndarray
    scenario_type: str
    probability: float
    max_drawdown: float
    max_gain: float


@dataclass
class DiffusionResult:
    """Diffusion model generation result."""
    scenarios: List[GeneratedScenario]
    mean_scenario: np.ndarray
    worst_case: GeneratedScenario
    best_case: GeneratedScenario
    var_95: float
    expected_return: float
    trading_signal: str


class DiffusionModelGenerator:
    """Diffusion-based synthetic scenario generator."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.num_steps = self.config.get('num_steps', 100)
            self.noise_schedule = self.config.get('noise_schedule', 'linear')
            logger.info("DiffusionModelGenerator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def generate(
        self,
        prices: np.ndarray,
        num_scenarios: int = 100,
        horizon: int = 20
    ) -> DiffusionResult:
        """Generate synthetic scenarios."""
        try:
            if len(prices) < 20:
                return self._create_empty_result()
        
            # Learn distribution from historical data
            returns = np.diff(prices) / prices[:-1]
            mu = np.mean(returns)
            sigma = np.std(returns)
        
            # Generate scenarios using diffusion process
            scenarios = []
            for _ in range(num_scenarios):
                scenario = self._generate_scenario(prices[-1], mu, sigma, horizon)
                scenarios.append(scenario)
        
            # Calculate statistics
            mean_scenario = np.mean([s.prices for s in scenarios], axis=0)
            worst = min(scenarios, key=lambda s: s.prices[-1])
            best = max(scenarios, key=lambda s: s.prices[-1])
        
            final_returns = [(s.prices[-1] - prices[-1]) / prices[-1] for s in scenarios]
            var_95 = np.percentile(final_returns, 5)
            expected = np.mean(final_returns)
        
            signal = self._generate_signal(expected, var_95, scenarios)
        
            return DiffusionResult(
                scenarios=scenarios[:10],
                mean_scenario=mean_scenario,
                worst_case=worst,
                best_case=best,
                var_95=var_95,
                expected_return=expected,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in generate: {e}")
            raise
    
    def _generate_scenario(
        self,
        start_price: float,
        mu: float,
        sigma: float,
        horizon: int
    ) -> GeneratedScenario:
        """Generate single scenario using diffusion."""
        try:
            prices = [start_price]
            volumes = [1000]
        
            for _ in range(horizon):
                # Diffusion step with denoising
                noise = np.random.randn() * sigma
                drift = mu
                new_price = prices[-1] * (1 + drift + noise)
                prices.append(max(0.01, new_price))
                volumes.append(volumes[-1] * (1 + np.random.randn() * 0.1))
        
            prices = np.array(prices)
            volumes = np.array(volumes)
        
            # Classify scenario
            total_return = (prices[-1] - prices[0]) / prices[0]
            if total_return > 0.05:
                scenario_type = "bullish"
            elif total_return < -0.05:
                scenario_type = "bearish"
            else:
                scenario_type = "neutral"
        
            max_dd = self._calculate_max_drawdown(prices)
            max_gain = np.max(prices) / prices[0] - 1
        
            return GeneratedScenario(
                prices=prices,
                volumes=volumes,
                scenario_type=scenario_type,
                probability=1.0 / 100,
                max_drawdown=max_dd,
                max_gain=max_gain
            )
        except Exception as e:
            logger.error(f"Error in _generate_scenario: {e}")
            raise
    
    def _calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """Calculate maximum drawdown."""
        try:
            peak = prices[0]
            max_dd = 0
            for price in prices:
                if price > peak:
                    peak = price
                dd = (peak - price) / peak
                max_dd = max(max_dd, dd)
            return max_dd
        except Exception as e:
            logger.error(f"Error in _calculate_max_drawdown: {e}")
            raise
    
    def _generate_signal(
        self,
        expected: float,
        var_95: float,
        scenarios: List[GeneratedScenario]
    ) -> str:
        """Generate trading signal."""
        try:
            bullish = sum(1 for s in scenarios if s.scenario_type == "bullish")
            bearish = sum(1 for s in scenarios if s.scenario_type == "bearish")
        
            if expected > 0.02 and var_95 > -0.05:
                return f"BUY: Expected {expected:.1%}, VaR95 {var_95:.1%}, {bullish}% bullish"
            elif expected < -0.02 or var_95 < -0.1:
                return f"SELL: Expected {expected:.1%}, VaR95 {var_95:.1%}, {bearish}% bearish"
            return f"NEUTRAL: Expected {expected:.1%}, VaR95 {var_95:.1%}"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> DiffusionResult:
        """Create empty result."""
        try:
            empty = GeneratedScenario(np.array([]), np.array([]), "unknown", 0, 0, 0)
            return DiffusionResult([], np.array([]), empty, empty, 0, 0, "Insufficient data")
        except Exception as e:
            logger.error(f"Error in _create_empty_result: {e}")
            raise

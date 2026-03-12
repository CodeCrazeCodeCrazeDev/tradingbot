"""
Phase 4: World Models - Synthetic Market Generation
Creates realistic market scenarios for training and testing
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Different market regimes to simulate."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    CRISIS = "crisis"


@dataclass
class MarketScenario:
    """Parameters for market scenario generation."""
    regime: MarketRegime
    duration: int  # Number of timesteps
    volatility: float
    trend_strength: float = 0.0
    mean_reversion: float = 0.0
    jumps_frequency: float = 0.0
    seasonality: Optional[Dict] = None


class SyntheticMarketGenerator:
    """
    Generates synthetic market data for various scenarios.
    Combines different market dynamics and regimes.
    """
    
    def __init__(
        self,
        base_volatility: float = 0.01,
        dt: float = 1.0/252.0  # Daily timesteps
    ):
        self.base_volatility = base_volatility
        self.dt = dt
        
        # Default parameters for different regimes
        self.regime_params = {
            MarketRegime.TRENDING_UP: {
                'trend_strength': 0.2,
                'volatility': 1.0,
                'mean_reversion': 0.0,
                'jumps_frequency': 0.01
            },
            MarketRegime.TRENDING_DOWN: {
                'trend_strength': -0.2,
                'volatility': 1.0,
                'mean_reversion': 0.0,
                'jumps_frequency': 0.01
            },
            MarketRegime.RANGING: {
                'trend_strength': 0.0,
                'volatility': 0.8,
                'mean_reversion': 0.1,
                'jumps_frequency': 0.0
            },
            MarketRegime.HIGH_VOLATILITY: {
                'trend_strength': 0.0,
                'volatility': 2.0,
                'mean_reversion': 0.0,
                'jumps_frequency': 0.05
            },
            MarketRegime.LOW_VOLATILITY: {
                'trend_strength': 0.0,
                'volatility': 0.5,
                'mean_reversion': 0.05,
                'jumps_frequency': 0.0
            },
            MarketRegime.BREAKOUT: {
                'trend_strength': 0.3,
                'volatility': 1.5,
                'mean_reversion': -0.1,
                'jumps_frequency': 0.1
            },
            MarketRegime.REVERSAL: {
                'trend_strength': -0.3,
                'volatility': 1.5,
                'mean_reversion': 0.2,
                'jumps_frequency': 0.1
            },
            MarketRegime.CRISIS: {
                'trend_strength': -0.5,
                'volatility': 3.0,
                'mean_reversion': -0.2,
                'jumps_frequency': 0.2
            }
        }
        
        logger.info("✅ Synthetic Market Generator initialized")
    
    def generate_scenario(
        self,
        scenario: MarketScenario,
        initial_price: float = 100.0
    ) -> Dict:
        """
        Generate synthetic market data for a scenario.
        
        Args:
            scenario: Market scenario parameters
            initial_price: Starting price
        
        Returns:
            Dictionary with price and indicator data
        """
        # Get base parameters for regime
        base_params = self.regime_params[scenario.regime]
        
        # Combine with scenario-specific parameters
        params = {
            'trend_strength': scenario.trend_strength or base_params['trend_strength'],
            'volatility': scenario.volatility * base_params['volatility'],
            'mean_reversion': scenario.mean_reversion or base_params['mean_reversion'],
            'jumps_frequency': scenario.jumps_frequency or base_params['jumps_frequency']
        }
        
        # Generate price path
        prices = self._generate_price_path(
            initial_price,
            scenario.duration,
            params
        )
        
        # Calculate returns
        returns = np.diff(np.log(prices))
        
        # Calculate indicators
        indicators = self._calculate_indicators(prices, returns)
        
        # Add some noise to indicators
        indicators = self._add_indicator_noise(indicators)
        
        return {
            'prices': prices,
            'returns': returns,
            'indicators': indicators,
            'metadata': {
                'regime': scenario.regime.value,
                'duration': scenario.duration,
                'params': params
            }
        }
    
    def _generate_price_path(
        self,
        initial_price: float,
        duration: int,
        params: Dict
    ) -> np.ndarray:
        """Generate synthetic price path."""
        prices = np.zeros(duration)
        prices[0] = initial_price
        
        # Unpack parameters
        mu = params['trend_strength']
        sigma = params['volatility'] * self.base_volatility
        mean_rev = params['mean_reversion']
        jump_freq = params['jumps_frequency']
        
        # Generate path
        for t in range(1, duration):
            # Drift component
            drift = mu * self.dt
            
            # Diffusion component
            diffusion = sigma * np.sqrt(self.dt) * np.random.normal()
            
            # Mean reversion component
            if mean_rev != 0:
                log_price = np.log(prices[t-1])
                mean_price = np.log(initial_price)
                mean_rev_component = mean_rev * (mean_price - log_price) * self.dt
            else:
                mean_rev_component = 0
            
            # Jump component
            if np.random.random() < jump_freq:
                jump = np.random.normal(0, sigma * 3)  # Larger jumps
            else:
                jump = 0
            
            # Combine components
            log_return = drift + diffusion + mean_rev_component + jump
            
            # Update price
            prices[t] = prices[t-1] * np.exp(log_return)
        
        return prices
    
    def _calculate_indicators(
        self,
        prices: np.ndarray,
        returns: np.ndarray
    ) -> Dict:
        """Calculate technical indicators from price data."""
        n = len(prices)
        
        # Moving averages
        sma_20 = np.zeros(n)
        sma_50 = np.zeros(n)
        
        for i in range(n):
            if i >= 20:
                sma_20[i] = np.mean(prices[i-20:i])
            if i >= 50:
                sma_50[i] = np.mean(prices[i-50:i])
        
        # RSI - pad returns to match prices length
        padded_returns = np.concatenate([[0], returns])  # Add 0 at start
        gains = np.maximum(padded_returns, 0)
        losses = -np.minimum(padded_returns, 0)
        
        avg_gain = np.zeros(n)
        avg_loss = np.zeros(n)
        rsi = np.zeros(n)
        
        for i in range(14, n):
            if i == 14:
                avg_gain[i] = np.mean(gains[1:15])
                avg_loss[i] = np.mean(losses[1:15])
            else:
                avg_gain[i] = (avg_gain[i-1] * 13 + gains[i]) / 14
                avg_loss[i] = (avg_loss[i-1] * 13 + losses[i]) / 14
            
            if avg_loss[i] == 0:
                rsi[i] = 100
            else:
                rs = avg_gain[i] / avg_loss[i]
                rsi[i] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = np.zeros(n)
        ema_26 = np.zeros(n)
        macd = np.zeros(n)
        
        for i in range(n):
            if i == 0:
                ema_12[i] = prices[i]
                ema_26[i] = prices[i]
            else:
                ema_12[i] = prices[i] * 0.15 + ema_12[i-1] * 0.85
                ema_26[i] = prices[i] * 0.075 + ema_26[i-1] * 0.925
            macd[i] = ema_12[i] - ema_26[i]
        
        # Volatility (20-day rolling)
        volatility = np.zeros(n)
        for i in range(20, n):
            volatility[i] = np.std(returns[i-20:i]) * np.sqrt(252)
        
        return {
            'sma_20': sma_20,
            'sma_50': sma_50,
            'rsi': rsi,
            'macd': macd,
            'volatility': volatility
        }
    
    def _add_indicator_noise(self, indicators: Dict) -> Dict:
        """Add realistic noise to indicators."""
        noisy_indicators = {}
        
        for name, values in indicators.items():
            # Add small Gaussian noise
            noise = np.random.normal(0, 0.02 * np.std(values), size=len(values))
            noisy_indicators[name] = values + noise
        
        return noisy_indicators
    
    def generate_regime_transition(
        self,
        initial_regime: MarketRegime,
        final_regime: MarketRegime,
        transition_duration: int,
        total_duration: int
    ) -> Dict:
        """
        Generate scenario with smooth regime transition.
        
        Args:
            initial_regime: Starting regime
            final_regime: Ending regime
            transition_duration: Duration of transition
            total_duration: Total scenario duration
        
        Returns:
            Market data with regime transition
        """
        # Generate initial regime
        initial_scenario = MarketScenario(
            regime=initial_regime,
            duration=total_duration,
            volatility=1.0
        )
        initial_data = self.generate_scenario(initial_scenario)
        
        # Generate final regime
        final_scenario = MarketScenario(
            regime=final_regime,
            duration=total_duration,
            volatility=1.0
        )
        final_data = self.generate_scenario(final_scenario)
        
        # Create transition weights
        transition_weights = np.zeros(total_duration)
        for t in range(total_duration):
            if t < transition_duration:
                # Smooth transition
                weight = t / transition_duration
                transition_weights[t] = 0.5 * (1 + np.cos(np.pi * (1 - weight)))
        
        # Blend regimes
        blended_data = {
            'prices': (
                initial_data['prices'] * (1 - transition_weights) +
                final_data['prices'] * transition_weights
            ),
            'metadata': {
                'initial_regime': initial_regime.value,
                'final_regime': final_regime.value,
                'transition_duration': transition_duration
            }
        }
        
        # Recalculate indicators for blended prices
        returns = np.diff(np.log(blended_data['prices']))
        blended_data['indicators'] = self._calculate_indicators(
            blended_data['prices'],
            returns
        )
        
        return blended_data
    
    def generate_market_cycle(
        self,
        cycle_duration: int,
        num_regimes: int = 4
    ) -> Dict:
        """
        Generate complete market cycle with multiple regime changes.
        
        Args:
            cycle_duration: Total duration of cycle
            num_regimes: Number of regime changes
        
        Returns:
            Market data for complete cycle
        """
        # Define cycle phases
        cycle_regimes = [
            MarketRegime.RANGING,
            MarketRegime.TRENDING_UP,
            MarketRegime.HIGH_VOLATILITY,
            MarketRegime.TRENDING_DOWN,
            MarketRegime.LOW_VOLATILITY
        ]
        
        # Duration for each regime
        regime_duration = cycle_duration // num_regimes
        transition_duration = regime_duration // 3
        
        # Generate data for each phase
        cycle_data = []
        current_price = 100.0
        
        for i in range(num_regimes):
            # Select regime
            regime = cycle_regimes[i % len(cycle_regimes)]
            
            # Generate scenario
            scenario = MarketScenario(
                regime=regime,
                duration=regime_duration,
                volatility=1.0
            )
            
            data = self.generate_scenario(scenario, initial_price=current_price)
            cycle_data.append(data)
            
            # Update starting price for next phase
            current_price = data['prices'][-1]
        
        # Combine phases
        combined_data = {
            'prices': np.concatenate([d['prices'] for d in cycle_data]),
            'metadata': {
                'cycle_duration': cycle_duration,
                'num_regimes': num_regimes,
                'regime_sequence': [d['metadata']['regime'] for d in cycle_data]
            }
        }
        
        # Calculate final indicators
        returns = np.diff(np.log(combined_data['prices']))
        combined_data['indicators'] = self._calculate_indicators(
            combined_data['prices'],
            returns
        )
        
        return combined_data

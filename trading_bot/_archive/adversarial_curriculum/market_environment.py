"""
Adversarial Market Environment

Implements a progressively hardening market simulation that introduces
increasing complexity, noise, and adversarial behavior at each level.
"""

import logging
import random
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from .core_types import (
    AgentAction,
    AgentState,
    CurriculumLevel,
    EpisodeResult,
    HardeningMechanism,
    LevelConfig,
    MarketRegime,
    MarketState,
    get_level_config,
)

logger = logging.getLogger(__name__)


# =============================================================================
# NOISE INJECTION
# =============================================================================

class NoiseInjector:
    """
    Injects various types of noise into market data.
    Noise intensity scales with curriculum level.
    """
    
    def __init__(self, config: LevelConfig):
        self.config = config
        self.rng = np.random.default_rng()
    
    def inject_price_noise(self, price: float) -> float:
        """Add noise to price."""
        if self.config.price_noise_std <= 0:
            return price
        
        noise = self.rng.normal(0, self.config.price_noise_std * price)
        return price + noise
    
    def inject_volume_noise(self, volume: float) -> float:
        """Add noise to volume."""
        if self.config.volume_noise_std <= 0:
            return volume
        
        noise = self.rng.normal(0, self.config.volume_noise_std * volume)
        return max(0, volume + noise)
    
    def inject_spread_noise(self, spread: float) -> float:
        """Add noise to spread."""
        if self.config.spread_variance <= 0:
            return spread
        
        multiplier = self.rng.lognormal(0, self.config.spread_variance)
        return spread * multiplier
    
    def inject_latency(self) -> float:
        """Generate random latency in milliseconds."""
        if self.config.latency_mean_ms <= 0:
            return 0
        
        # Use gamma distribution for realistic latency
        shape = (self.config.latency_mean_ms / self.config.latency_variance_ms) ** 2 if self.config.latency_variance_ms > 0 else 1
        scale = self.config.latency_variance_ms ** 2 / self.config.latency_mean_ms if self.config.latency_mean_ms > 0 else 1
        
        return self.rng.gamma(shape, scale)


# =============================================================================
# EXECUTION SIMULATOR
# =============================================================================

class ExecutionSimulator:
    """
    Simulates realistic order execution with slippage, partial fills,
    and order rejections.
    """
    
    def __init__(self, config: LevelConfig):
        self.config = config
        self.rng = np.random.default_rng()
    
    def calculate_slippage(self, order_size: float, liquidity: float, volatility: float) -> float:
        """
        Calculate slippage in basis points.
        Slippage increases with order size and volatility, decreases with liquidity.
        """
        base_slippage = self.config.base_slippage_bps
        
        # Size impact
        size_impact = (order_size / (liquidity + 1e-8)) * 10
        
        # Volatility impact
        vol_impact = volatility * 100
        
        # Random component
        random_component = 0
        if self.config.slippage_variance > 0:
            random_component = self.rng.normal(0, self.config.slippage_variance)
        
        total_slippage = base_slippage + size_impact + vol_impact + random_component
        return max(0, total_slippage)
    
    def simulate_fill(
        self,
        order_size: float,
        order_price: float,
        side: str,
        market_state: MarketState
    ) -> Tuple[float, float, str]:
        """
        Simulate order fill.
        
        Returns:
            Tuple of (filled_size, fill_price, status)
            status: 'filled', 'partial', 'rejected'
        """
        # Check for rejection
        if self.rng.random() < self.config.order_rejection_probability:
            return 0, 0, 'rejected'
        
        # Check for partial fill
        if self.rng.random() < self.config.partial_fill_probability:
            fill_ratio = self.rng.uniform(0.3, 0.9)
            filled_size = order_size * fill_ratio
            status = 'partial'
        else:
            filled_size = order_size
            status = 'filled'
        
        # Calculate slippage
        slippage_bps = self.calculate_slippage(
            order_size, 
            market_state.liquidity_depth,
            market_state.volatility
        )
        
        # Apply slippage to price
        slippage_multiplier = slippage_bps / 10000
        if side == 'BUY':
            fill_price = order_price * (1 + slippage_multiplier)
        else:
            fill_price = order_price * (1 - slippage_multiplier)
        
        return filled_size, fill_price, status


# =============================================================================
# REGIME SWITCHER
# =============================================================================

class RegimeSwitcher:
    """
    Manages market regime transitions.
    Regime switching becomes more frequent at higher levels.
    """
    
    def __init__(self, config: LevelConfig):
        self.config = config
        self.current_regime = MarketRegime.RANGING
        self.regime_duration = 0
        self.rng = np.random.default_rng()
        
        # Transition matrix (simplified)
        self.transition_probs = {
            MarketRegime.TRENDING_UP: {
                MarketRegime.TRENDING_UP: 0.7,
                MarketRegime.TRENDING_DOWN: 0.05,
                MarketRegime.RANGING: 0.15,
                MarketRegime.HIGH_VOLATILITY: 0.05,
                MarketRegime.LOW_VOLATILITY: 0.03,
                MarketRegime.CRISIS: 0.02,
            },
            MarketRegime.TRENDING_DOWN: {
                MarketRegime.TRENDING_UP: 0.05,
                MarketRegime.TRENDING_DOWN: 0.7,
                MarketRegime.RANGING: 0.12,
                MarketRegime.HIGH_VOLATILITY: 0.08,
                MarketRegime.LOW_VOLATILITY: 0.02,
                MarketRegime.CRISIS: 0.03,
            },
            MarketRegime.RANGING: {
                MarketRegime.TRENDING_UP: 0.15,
                MarketRegime.TRENDING_DOWN: 0.15,
                MarketRegime.RANGING: 0.55,
                MarketRegime.HIGH_VOLATILITY: 0.08,
                MarketRegime.LOW_VOLATILITY: 0.05,
                MarketRegime.CRISIS: 0.02,
            },
            MarketRegime.HIGH_VOLATILITY: {
                MarketRegime.TRENDING_UP: 0.1,
                MarketRegime.TRENDING_DOWN: 0.15,
                MarketRegime.RANGING: 0.2,
                MarketRegime.HIGH_VOLATILITY: 0.4,
                MarketRegime.LOW_VOLATILITY: 0.05,
                MarketRegime.CRISIS: 0.1,
            },
            MarketRegime.LOW_VOLATILITY: {
                MarketRegime.TRENDING_UP: 0.15,
                MarketRegime.TRENDING_DOWN: 0.1,
                MarketRegime.RANGING: 0.35,
                MarketRegime.HIGH_VOLATILITY: 0.1,
                MarketRegime.LOW_VOLATILITY: 0.28,
                MarketRegime.CRISIS: 0.02,
            },
            MarketRegime.CRISIS: {
                MarketRegime.TRENDING_UP: 0.05,
                MarketRegime.TRENDING_DOWN: 0.25,
                MarketRegime.RANGING: 0.1,
                MarketRegime.HIGH_VOLATILITY: 0.3,
                MarketRegime.LOW_VOLATILITY: 0.0,
                MarketRegime.CRISIS: 0.25,
                MarketRegime.RECOVERY: 0.05,
            },
            MarketRegime.RECOVERY: {
                MarketRegime.TRENDING_UP: 0.35,
                MarketRegime.TRENDING_DOWN: 0.05,
                MarketRegime.RANGING: 0.25,
                MarketRegime.HIGH_VOLATILITY: 0.15,
                MarketRegime.LOW_VOLATILITY: 0.1,
                MarketRegime.CRISIS: 0.05,
                MarketRegime.RECOVERY: 0.05,
            },
            MarketRegime.MANIPULATION: {
                MarketRegime.TRENDING_UP: 0.1,
                MarketRegime.TRENDING_DOWN: 0.1,
                MarketRegime.RANGING: 0.3,
                MarketRegime.HIGH_VOLATILITY: 0.2,
                MarketRegime.LOW_VOLATILITY: 0.1,
                MarketRegime.CRISIS: 0.1,
                MarketRegime.MANIPULATION: 0.1,
            },
        }
    
    def step(self) -> Tuple[MarketRegime, bool]:
        """
        Step the regime forward.
        
        Returns:
            Tuple of (current_regime, regime_changed)
        """
        self.regime_duration += 1
        
        # Check for regime switch
        if self.rng.random() < self.config.regime_switch_probability:
            # Transition to new regime
            probs = self.transition_probs.get(self.current_regime, {})
            if probs:
                regimes = list(probs.keys())
                weights = list(probs.values())
                # Normalize weights
                total = sum(weights)
                weights = [w / total for w in weights]
                
                new_regime = self.rng.choice(regimes, p=weights)
                if new_regime != self.current_regime:
                    old_regime = self.current_regime
                    self.current_regime = new_regime
                    self.regime_duration = 0
                    logger.debug(f"Regime switch: {old_regime.name} -> {new_regime.name}")
                    return self.current_regime, True
        
        return self.current_regime, False
    
    def force_regime(self, regime: MarketRegime):
        """Force a specific regime (for testing)."""
        self.current_regime = regime
        self.regime_duration = 0


# =============================================================================
# ADVERSARIAL MECHANISMS
# =============================================================================

class AdversarialMechanisms:
    """
    Implements adversarial market behaviors like fake signals,
    stop hunting, and manipulation.
    """
    
    def __init__(self, config: LevelConfig):
        self.config = config
        self.rng = np.random.default_rng()
        
        # Track agent positions for stop hunting
        self.known_stop_levels: List[float] = []
    
    def generate_fake_signal(self, true_direction: int) -> Optional[int]:
        """
        Generate a fake signal opposite to the true direction.
        
        Args:
            true_direction: 1 for up, -1 for down, 0 for neutral
            
        Returns:
            Fake signal direction or None if no fake signal
        """
        if self.rng.random() < self.config.fake_signal_probability:
            # Generate opposite signal
            return -true_direction if true_direction != 0 else self.rng.choice([-1, 1])
        return None
    
    def check_stop_hunt(self, price: float, agent_state: AgentState) -> Optional[float]:
        """
        Check if a stop hunt should occur.
        
        Returns:
            Target price for stop hunt or None
        """
        if self.rng.random() >= self.config.stop_hunt_probability:
            return None
        
        # Estimate stop loss levels based on position
        if agent_state.position > 0:
            # Long position - hunt below entry
            stop_estimate = agent_state.avg_entry_price * 0.98
            if price > stop_estimate:
                return stop_estimate * 0.995  # Spike down to trigger stops
        elif agent_state.position < 0:
            # Short position - hunt above entry
            stop_estimate = agent_state.avg_entry_price * 1.02
            if price < stop_estimate:
                return stop_estimate * 1.005  # Spike up to trigger stops
        
        return None
    
    def apply_manipulation(self, price: float, volume: float) -> Tuple[float, float]:
        """
        Apply market manipulation effects.
        
        Returns:
            Tuple of (manipulated_price, manipulated_volume)
        """
        if self.rng.random() >= self.config.manipulation_probability:
            return price, volume
        
        manipulation_type = self.rng.choice(['pump', 'dump', 'wash', 'spoof'])
        
        if manipulation_type == 'pump':
            # Artificial price increase
            price *= 1 + self.rng.uniform(0.005, 0.02)
            volume *= self.rng.uniform(1.5, 3.0)
        elif manipulation_type == 'dump':
            # Artificial price decrease
            price *= 1 - self.rng.uniform(0.005, 0.02)
            volume *= self.rng.uniform(1.5, 3.0)
        elif manipulation_type == 'wash':
            # Fake volume
            volume *= self.rng.uniform(2.0, 5.0)
        elif manipulation_type == 'spoof':
            # Price moves then reverses (handled in price generation)
            pass
        
        return price, volume


# =============================================================================
# CRISIS SIMULATOR
# =============================================================================

class CrisisSimulator:
    """
    Simulates black swan events, flash crashes, and liquidity crises.
    """
    
    def __init__(self, config: LevelConfig):
        self.config = config
        self.rng = np.random.default_rng()
        
        # Crisis state
        self.in_crisis = False
        self.crisis_type: Optional[str] = None
        self.crisis_duration = 0
        self.crisis_severity = 0.0
    
    def check_flash_crash(self) -> Optional[Dict[str, Any]]:
        """Check if a flash crash should occur."""
        if self.rng.random() < self.config.flash_crash_probability:
            severity = self.rng.uniform(0.05, 0.15)  # 5-15% drop
            duration = self.rng.integers(5, 20)  # 5-20 steps
            
            return {
                'type': 'flash_crash',
                'severity': severity,
                'duration': duration,
                'recovery_speed': self.rng.uniform(0.3, 0.7),
            }
        return None
    
    def check_liquidity_crisis(self) -> Optional[Dict[str, Any]]:
        """Check if a liquidity crisis should occur."""
        if self.rng.random() < self.config.liquidity_crisis_probability:
            severity = self.rng.uniform(0.5, 0.9)  # 50-90% liquidity reduction
            duration = self.rng.integers(20, 100)  # 20-100 steps
            
            return {
                'type': 'liquidity_crisis',
                'severity': severity,
                'duration': duration,
                'spread_multiplier': self.rng.uniform(3, 10),
            }
        return None
    
    def check_correlation_breakdown(self) -> Optional[Dict[str, Any]]:
        """Check if correlation breakdown should occur."""
        if self.rng.random() < self.config.correlation_breakdown_probability:
            return {
                'type': 'correlation_breakdown',
                'duration': self.rng.integers(50, 200),
                'correlation_shift': self.rng.uniform(-0.5, 0.5),
            }
        return None
    
    def apply_crisis_effects(
        self,
        price: float,
        spread: float,
        liquidity: float,
        crisis_info: Dict[str, Any]
    ) -> Tuple[float, float, float]:
        """Apply crisis effects to market data."""
        
        crisis_type = crisis_info.get('type')
        
        if crisis_type == 'flash_crash':
            severity = crisis_info['severity']
            price *= (1 - severity)
            spread *= 5  # Spreads widen dramatically
            liquidity *= 0.1  # Liquidity evaporates
            
        elif crisis_type == 'liquidity_crisis':
            severity = crisis_info['severity']
            spread *= crisis_info.get('spread_multiplier', 5)
            liquidity *= (1 - severity)
            
        return price, spread, liquidity


# =============================================================================
# MAIN ENVIRONMENT
# =============================================================================

class AdversarialMarketEnvironment:
    """
    Main adversarial market environment that combines all hardening mechanisms.
    """
    
    def __init__(
        self,
        level: CurriculumLevel,
        initial_price: float = 100.0,
        initial_capital: float = 100000.0,
        episode_length: int = 1000,
        seed: Optional[int] = None
    ):
        self.level = level
        self.config = get_level_config(level)
        self.initial_price = initial_price
        self.initial_capital = initial_capital
        self.episode_length = episode_length
        
        # Set seed
        self.seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self.rng = np.random.default_rng(self.seed)
        random.seed(self.seed)
        
        # Initialize components
        self.noise_injector = NoiseInjector(self.config)
        self.execution_simulator = ExecutionSimulator(self.config)
        self.regime_switcher = RegimeSwitcher(self.config)
        self.adversarial = AdversarialMechanisms(self.config)
        self.crisis_simulator = CrisisSimulator(self.config)
        
        # State
        self.current_step = 0
        self.episode_id = str(uuid.uuid4())[:8]
        self.done = False
        
        # Market state
        self.price_history: List[float] = []
        self.volume_history: List[float] = []
        self.regime_history: List[MarketRegime] = []
        self.hardening_events: List[HardeningMechanism] = []
        
        # Agent state
        self.agent_state: Optional[AgentState] = None
        
        # Crisis state
        self.active_crisis: Optional[Dict[str, Any]] = None
        self.crisis_remaining_duration = 0
        
        # Correlated assets (for Level 6+)
        self.correlated_assets: Dict[str, float] = {}
        self.correlation_matrix: Optional[np.ndarray] = None
        
        if level.value >= 6:
            self._initialize_correlated_assets()
        
        logger.info(f"Environment initialized: Level {level.value}, Seed {self.seed}")
    
    def _initialize_correlated_assets(self):
        """Initialize correlated assets for multi-asset levels."""
        n_assets = 3
        self.correlated_assets = {
            f"ASSET_{i}": self.initial_price * (0.8 + self.rng.random() * 0.4)
            for i in range(n_assets)
        }
        
        # Generate correlation matrix
        # Start with identity and add correlations
        self.correlation_matrix = np.eye(n_assets + 1)
        for i in range(n_assets):
            corr = self.rng.uniform(0.3, 0.9) * self.rng.choice([-1, 1])
            self.correlation_matrix[0, i + 1] = corr
            self.correlation_matrix[i + 1, 0] = corr
    
    def reset(self) -> MarketState:
        """Reset the environment for a new episode."""
        self.current_step = 0
        self.episode_id = str(uuid.uuid4())[:8]
        self.done = False
        
        # Reset histories
        self.price_history = [self.initial_price]
        self.volume_history = [1000.0]
        self.regime_history = [MarketRegime.RANGING]
        self.hardening_events = []
        
        # Reset agent state
        self.agent_state = AgentState(
            capital=self.initial_capital,
            position=0.0,
            avg_entry_price=0.0,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            trade_count=0,
            win_count=0,
            loss_count=0,
            max_drawdown=0.0,
            current_drawdown=0.0,
            peak_capital=self.initial_capital,
            leverage=0.0,
        )
        
        # Reset crisis state
        self.active_crisis = None
        self.crisis_remaining_duration = 0
        
        # Reset regime
        self.regime_switcher.current_regime = MarketRegime.RANGING
        
        # Reset correlated assets
        if self.level.value >= 6:
            self._initialize_correlated_assets()
        
        return self._get_market_state()
    
    def _get_market_state(self) -> MarketState:
        """Get current market state."""
        price = self.price_history[-1]
        volume = self.volume_history[-1]
        regime = self.regime_switcher.current_regime
        
        # Calculate spread
        base_spread = self.config.base_spread_bps / 10000 * price
        spread = self.noise_injector.inject_spread_noise(base_spread)
        
        # Calculate volatility from recent prices
        if len(self.price_history) > 20:
            returns = np.diff(self.price_history[-21:]) / np.array(self.price_history[-21:-1])
            volatility = np.std(returns)
        else:
            volatility = 0.01
        
        # Estimate liquidity
        liquidity = volume * 10  # Simplified
        
        # Apply crisis effects if active
        if self.active_crisis:
            price, spread, liquidity = self.crisis_simulator.apply_crisis_effects(
                price, spread, liquidity, self.active_crisis
            )
        
        return MarketState(
            timestamp=datetime.now(),
            price=price,
            bid=price - spread / 2,
            ask=price + spread / 2,
            volume=volume,
            volatility=volatility,
            regime=regime,
            spread=spread,
            liquidity_depth=liquidity,
            price_history=np.array(self.price_history[-100:]),
            volume_history=np.array(self.volume_history[-100:]),
            correlated_assets=self.correlated_assets.copy(),
            correlation_matrix=self.correlation_matrix,
            true_regime=regime,
            manipulation_active=self.active_crisis is not None,
        )
    
    def _generate_price_movement(self) -> float:
        """Generate next price based on regime and noise."""
        current_price = self.price_history[-1]
        regime = self.regime_switcher.current_regime
        
        # Base drift based on regime
        drift_map = {
            MarketRegime.TRENDING_UP: 0.0005,
            MarketRegime.TRENDING_DOWN: -0.0005,
            MarketRegime.RANGING: 0.0,
            MarketRegime.HIGH_VOLATILITY: 0.0,
            MarketRegime.LOW_VOLATILITY: 0.0,
            MarketRegime.CRISIS: -0.002,
            MarketRegime.RECOVERY: 0.001,
            MarketRegime.MANIPULATION: 0.0,
        }
        
        drift = drift_map.get(regime, 0.0)
        
        # Volatility based on regime
        vol_map = {
            MarketRegime.TRENDING_UP: 0.01,
            MarketRegime.TRENDING_DOWN: 0.012,
            MarketRegime.RANGING: 0.008,
            MarketRegime.HIGH_VOLATILITY: 0.025,
            MarketRegime.LOW_VOLATILITY: 0.004,
            MarketRegime.CRISIS: 0.05,
            MarketRegime.RECOVERY: 0.015,
            MarketRegime.MANIPULATION: 0.02,
        }
        
        volatility = vol_map.get(regime, 0.01)
        
        # Generate return
        return_val = drift + volatility * self.rng.standard_normal()
        
        # Apply noise injection
        new_price = current_price * (1 + return_val)
        new_price = self.noise_injector.inject_price_noise(new_price)
        
        return new_price
    
    def _generate_volume(self) -> float:
        """Generate volume for current step."""
        base_volume = 1000.0
        
        # Volume varies with regime
        regime = self.regime_switcher.current_regime
        vol_multiplier = {
            MarketRegime.TRENDING_UP: 1.2,
            MarketRegime.TRENDING_DOWN: 1.5,
            MarketRegime.RANGING: 0.8,
            MarketRegime.HIGH_VOLATILITY: 2.0,
            MarketRegime.LOW_VOLATILITY: 0.5,
            MarketRegime.CRISIS: 3.0,
            MarketRegime.RECOVERY: 1.3,
            MarketRegime.MANIPULATION: 2.5,
        }.get(regime, 1.0)
        
        volume = base_volume * vol_multiplier * (0.5 + self.rng.random())
        volume = self.noise_injector.inject_volume_noise(volume)
        
        return max(100, volume)
    
    def _check_for_crises(self):
        """Check and initiate crisis events."""
        if self.active_crisis:
            self.crisis_remaining_duration -= 1
            if self.crisis_remaining_duration <= 0:
                logger.debug(f"Crisis ended: {self.active_crisis['type']}")
                self.active_crisis = None
            return
        
        # Check for new crises
        flash_crash = self.crisis_simulator.check_flash_crash()
        if flash_crash:
            self.active_crisis = flash_crash
            self.crisis_remaining_duration = flash_crash['duration']
            self.hardening_events.append(HardeningMechanism.FLASH_CRASH)
            logger.debug(f"Flash crash initiated: severity {flash_crash['severity']:.2%}")
            return
        
        liquidity_crisis = self.crisis_simulator.check_liquidity_crisis()
        if liquidity_crisis:
            self.active_crisis = liquidity_crisis
            self.crisis_remaining_duration = liquidity_crisis['duration']
            self.hardening_events.append(HardeningMechanism.LIQUIDITY_DROUGHTS)
            logger.debug("Liquidity crisis initiated")
            return
        
        corr_breakdown = self.crisis_simulator.check_correlation_breakdown()
        if corr_breakdown:
            self.active_crisis = corr_breakdown
            self.crisis_remaining_duration = corr_breakdown['duration']
            self.hardening_events.append(HardeningMechanism.CORRELATION_BREAKDOWN)
            logger.debug("Correlation breakdown initiated")
    
    def _update_correlated_assets(self, main_return: float):
        """Update correlated asset prices."""
        if not self.correlated_assets or self.correlation_matrix is None:
            return
        
        for i, (asset, price) in enumerate(self.correlated_assets.items()):
            # Get correlation with main asset
            corr = self.correlation_matrix[0, i + 1]
            
            # Apply correlation breakdown if active
            if self.active_crisis and self.active_crisis.get('type') == 'correlation_breakdown':
                corr += self.active_crisis.get('correlation_shift', 0)
                corr = np.clip(corr, -1, 1)
            
            # Generate correlated return
            idiosyncratic = self.rng.standard_normal() * 0.01
            correlated_return = corr * main_return + np.sqrt(1 - corr**2) * idiosyncratic
            
            self.correlated_assets[asset] = price * (1 + correlated_return)
    
    def _execute_action(self, action: AgentAction, market_state: MarketState) -> Dict[str, Any]:
        """Execute agent action and return execution result."""
        result = {
            'action': action,
            'executed': False,
            'fill_price': 0.0,
            'fill_size': 0.0,
            'status': 'pending',
            'slippage': 0.0,
            'latency_ms': 0.0,
        }
        
        if action == AgentAction.HOLD:
            result['executed'] = True
            result['status'] = 'no_action'
            return result
        
        # Determine order parameters
        position_sizes = {
            AgentAction.BUY: 1.0,
            AgentAction.SELL: 1.0,
            AgentAction.BUY_SMALL: 0.25,
            AgentAction.BUY_MEDIUM: 0.5,
            AgentAction.BUY_LARGE: 1.0,
            AgentAction.SELL_SMALL: 0.25,
            AgentAction.SELL_MEDIUM: 0.5,
            AgentAction.SELL_LARGE: 1.0,
            AgentAction.SCALE_IN: 0.25,
            AgentAction.SCALE_OUT: 0.25,
            AgentAction.CLOSE_ALL: abs(self.agent_state.position),
            AgentAction.HEDGE: 0.5,
            AgentAction.REDUCE_EXPOSURE: 0.5,
            AgentAction.EMERGENCY_EXIT: abs(self.agent_state.position),
        }
        
        size_multiplier = position_sizes.get(action, 0.0)
        if size_multiplier == 0:
            return result
        
        # Calculate order size based on capital
        max_position = self.agent_state.capital / market_state.price
        order_size = max_position * size_multiplier * 0.1  # 10% of max per unit
        
        # Determine side
        buy_actions = {AgentAction.BUY, AgentAction.BUY_SMALL, AgentAction.BUY_MEDIUM, 
                       AgentAction.BUY_LARGE, AgentAction.SCALE_IN}
        sell_actions = {AgentAction.SELL, AgentAction.SELL_SMALL, AgentAction.SELL_MEDIUM,
                        AgentAction.SELL_LARGE, AgentAction.SCALE_OUT, AgentAction.CLOSE_ALL,
                        AgentAction.REDUCE_EXPOSURE, AgentAction.EMERGENCY_EXIT}
        
        if action in buy_actions:
            side = 'BUY'
            order_price = market_state.ask
        elif action in sell_actions:
            side = 'SELL'
            order_price = market_state.bid
            if action in {AgentAction.CLOSE_ALL, AgentAction.EMERGENCY_EXIT}:
                order_size = abs(self.agent_state.position)
        else:
            return result
        
        # Add latency
        latency = self.noise_injector.inject_latency()
        result['latency_ms'] = latency
        
        # Execute order
        fill_size, fill_price, status = self.execution_simulator.simulate_fill(
            order_size, order_price, side, market_state
        )
        
        result['fill_size'] = fill_size
        result['fill_price'] = fill_price
        result['status'] = status
        result['executed'] = status in ['filled', 'partial']
        
        if result['executed']:
            result['slippage'] = abs(fill_price - order_price) / order_price * 10000  # bps
            self._update_agent_position(side, fill_size, fill_price)
        
        return result
    
    def _update_agent_position(self, side: str, size: float, price: float):
        """Update agent position after trade."""
        if side == 'BUY':
            # Update average entry price
            if self.agent_state.position >= 0:
                total_cost = self.agent_state.position * self.agent_state.avg_entry_price + size * price
                self.agent_state.position += size
                self.agent_state.avg_entry_price = total_cost / self.agent_state.position if self.agent_state.position > 0 else 0
            else:
                # Covering short
                if size >= abs(self.agent_state.position):
                    # Realize P&L on short
                    pnl = (self.agent_state.avg_entry_price - price) * abs(self.agent_state.position)
                    self.agent_state.realized_pnl += pnl
                    if pnl > 0:
                        self.agent_state.win_count += 1
                    else:
                        self.agent_state.loss_count += 1
                    
                    remaining = size - abs(self.agent_state.position)
                    self.agent_state.position = remaining
                    self.agent_state.avg_entry_price = price if remaining > 0 else 0
                else:
                    self.agent_state.position += size
        else:  # SELL
            if self.agent_state.position <= 0:
                # Adding to short
                total_cost = abs(self.agent_state.position) * self.agent_state.avg_entry_price + size * price
                self.agent_state.position -= size
                self.agent_state.avg_entry_price = total_cost / abs(self.agent_state.position) if self.agent_state.position != 0 else 0
            else:
                # Closing long
                if size >= self.agent_state.position:
                    # Realize P&L on long
                    pnl = (price - self.agent_state.avg_entry_price) * self.agent_state.position
                    self.agent_state.realized_pnl += pnl
                    if pnl > 0:
                        self.agent_state.win_count += 1
                    else:
                        self.agent_state.loss_count += 1
                    
                    remaining = size - self.agent_state.position
                    self.agent_state.position = -remaining
                    self.agent_state.avg_entry_price = price if remaining > 0 else 0
                else:
                    self.agent_state.position -= size
        
        self.agent_state.trade_count += 1
        self.agent_state.trade_history.append({
            'step': self.current_step,
            'side': side,
            'size': size,
            'price': price,
        })
    
    def _update_agent_pnl(self, current_price: float):
        """Update agent P&L based on current price."""
        if self.agent_state.position > 0:
            self.agent_state.unrealized_pnl = (current_price - self.agent_state.avg_entry_price) * self.agent_state.position
        elif self.agent_state.position < 0:
            self.agent_state.unrealized_pnl = (self.agent_state.avg_entry_price - current_price) * abs(self.agent_state.position)
        else:
            self.agent_state.unrealized_pnl = 0
        
        # Update capital
        total_pnl = self.agent_state.realized_pnl + self.agent_state.unrealized_pnl
        current_capital = self.initial_capital + total_pnl
        
        # Update peak and drawdown
        if current_capital > self.agent_state.peak_capital:
            self.agent_state.peak_capital = current_capital
        
        self.agent_state.current_drawdown = (self.agent_state.peak_capital - current_capital) / self.agent_state.peak_capital
        self.agent_state.max_drawdown = max(self.agent_state.max_drawdown, self.agent_state.current_drawdown)
        
        # Update leverage
        position_value = abs(self.agent_state.position) * current_price
        self.agent_state.leverage = position_value / current_capital if current_capital > 0 else 0
        
        self.agent_state.capital = current_capital
    
    def step(self, action: AgentAction) -> Tuple[MarketState, float, bool, Dict[str, Any]]:
        """
        Take a step in the environment.
        
        Args:
            action: Agent's action
            
        Returns:
            Tuple of (next_state, reward, done, info)
        """
        self.current_step += 1
        
        # Get current state for execution
        current_state = self._get_market_state()
        
        # Execute action
        execution_result = self._execute_action(action, current_state)
        
        # Update regime
        regime, regime_changed = self.regime_switcher.step()
        if regime_changed:
            self.hardening_events.append(HardeningMechanism.REGIME_SWITCHING)
        
        # Check for crises
        self._check_for_crises()
        
        # Generate new price
        new_price = self._generate_price_movement()
        
        # Apply adversarial mechanisms
        if self.level.value >= 5:
            stop_hunt_price = self.adversarial.check_stop_hunt(new_price, self.agent_state)
            if stop_hunt_price:
                new_price = stop_hunt_price
                self.hardening_events.append(HardeningMechanism.STOP_HUNTING)
            
            new_price, new_volume = self.adversarial.apply_manipulation(
                new_price, self._generate_volume()
            )
        else:
            new_volume = self._generate_volume()
        
        # Update histories
        old_price = self.price_history[-1]
        self.price_history.append(new_price)
        self.volume_history.append(new_volume)
        self.regime_history.append(regime)
        
        # Update correlated assets
        main_return = (new_price - old_price) / old_price
        self._update_correlated_assets(main_return)
        
        # Update agent P&L
        self._update_agent_pnl(new_price)
        
        # Calculate reward
        reward = self._calculate_reward(execution_result)
        
        # Check termination
        self.done = (
            self.current_step >= self.episode_length or
            self.agent_state.capital <= 0 or
            self.agent_state.max_drawdown >= 0.5  # 50% drawdown = game over
        )
        
        # Get next state
        next_state = self._get_market_state()
        
        info = {
            'execution': execution_result,
            'regime': regime.name,
            'regime_changed': regime_changed,
            'crisis_active': self.active_crisis is not None,
            'agent_state': self.agent_state,
            'step': self.current_step,
        }
        
        return next_state, reward, self.done, info
    
    def _calculate_reward(self, execution_result: Dict[str, Any]) -> float:
        """
        Calculate reward for the current step.
        
        Reward is designed to encourage:
        - Capital preservation
        - Risk-adjusted returns
        - Avoiding tail risks
        
        Reward penalizes:
        - Excessive drawdown
        - High leverage
        - Tail risk exposure
        """
        # Base reward: change in capital
        capital_change = self.agent_state.capital - self.initial_capital
        base_reward = capital_change / self.initial_capital * 100  # Percentage
        
        # Drawdown penalty
        drawdown_penalty = self.agent_state.current_drawdown * self.config.drawdown_penalty_multiplier * 10
        
        # Leverage penalty (if excessive)
        leverage_penalty = 0
        if self.agent_state.leverage > 2.0:
            leverage_penalty = (self.agent_state.leverage - 2.0) * 5
        
        # Tail risk penalty
        tail_penalty = 0
        if self.agent_state.max_drawdown > 0.2:
            tail_penalty = (self.agent_state.max_drawdown - 0.2) * self.config.tail_risk_penalty * 100
        
        # Execution cost penalty
        execution_penalty = execution_result.get('slippage', 0) / 100  # Convert bps to penalty
        
        # Total reward
        reward = base_reward - drawdown_penalty - leverage_penalty - tail_penalty - execution_penalty
        
        return reward
    
    def get_episode_result(self) -> EpisodeResult:
        """Get the result of the current episode."""
        # Calculate metrics
        returns = np.diff(self.price_history) / np.array(self.price_history[:-1])
        
        if len(returns) > 1:
            sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
            downside_returns = returns[returns < 0]
            sortino = np.mean(returns) / (np.std(downside_returns) + 1e-8) * np.sqrt(252) if len(downside_returns) > 0 else 0
        else:
            sharpe = 0
            sortino = 0
        
        # Win rate
        total_trades = self.agent_state.win_count + self.agent_state.loss_count
        win_rate = self.agent_state.win_count / total_trades if total_trades > 0 else 0
        
        # Profit factor
        wins = [t for t in self.agent_state.trade_history if t.get('pnl', 0) > 0]
        losses = [t for t in self.agent_state.trade_history if t.get('pnl', 0) < 0]
        gross_profit = sum(t.get('pnl', 0) for t in wins)
        gross_loss = abs(sum(t.get('pnl', 0) for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # VaR and CVaR
        if len(returns) > 0:
            var_95 = np.percentile(returns, 5)
            cvar_95 = np.mean(returns[returns <= var_95]) if len(returns[returns <= var_95]) > 0 else var_95
        else:
            var_95 = 0
            cvar_95 = 0
        
        return EpisodeResult(
            episode_id=self.episode_id,
            level=self.level,
            seed=self.seed,
            total_return=(self.agent_state.capital - self.initial_capital) / self.initial_capital,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=self.agent_state.max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor if profit_factor != float('inf') else 10.0,
            total_trades=self.agent_state.trade_count,
            winning_trades=self.agent_state.win_count,
            losing_trades=self.agent_state.loss_count,
            avg_win=gross_profit / len(wins) if wins else 0,
            avg_loss=gross_loss / len(losses) if losses else 0,
            largest_win=max((t.get('pnl', 0) for t in wins), default=0),
            largest_loss=min((t.get('pnl', 0) for t in losses), default=0),
            var_95=var_95,
            cvar_95=cvar_95,
            tail_ratio=abs(cvar_95 / var_95) if var_95 != 0 else 1,
            avg_position_size=np.mean([abs(p) for p in self.agent_state.position_history]) if self.agent_state.position_history else 0,
            max_leverage_used=self.agent_state.leverage,
            trade_frequency=self.agent_state.trade_count / self.current_step if self.current_step > 0 else 0,
            duration_steps=self.current_step,
            regimes_encountered=list(set(self.regime_history)),
            hardening_events=list(set(self.hardening_events)),
        )

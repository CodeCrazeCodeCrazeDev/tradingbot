"""
Simulation Systems
==================

Advanced simulation capabilities including:
- World Model Learning
- Digital Twin of Trading System
- Adversarial Market Simulator
- Multi-Fidelity Simulation
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# WORLD MODEL LEARNING
# =============================================================================

class DynamicsType(Enum):
    """Types of market dynamics"""
    TRENDING = "trending"
    MEAN_REVERTING = "mean_reverting"
    RANDOM_WALK = "random_walk"
    REGIME_SWITCHING = "regime_switching"
    JUMP_DIFFUSION = "jump_diffusion"


@dataclass
class WorldState:
    """State of the world model"""
    timestamp: datetime
    price: float
    volume: float
    volatility: float
    regime: str
    hidden_state: np.ndarray
    
    def to_vector(self) -> np.ndarray:
        return np.array([
            self.price, self.volume, self.volatility,
            *self.hidden_state
        ])


class WorldModel:
    """
    World Model Learning
    
    Learns a model of market dynamics for planning
    and simulation.
    """
    
    def __init__(
        self,
        state_dim: int = 10,
        action_dim: int = 3,
        hidden_dim: int = 64,
        learning_rate: float = 0.001
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate
        
        # Transition model parameters (simplified)
        self.transition_weights = np.random.randn(state_dim + action_dim, state_dim) * 0.1
        self.reward_weights = np.random.randn(state_dim + action_dim, 1) * 0.1
        
        # Experience buffer
        self.experience_buffer: List[Tuple[np.ndarray, int, float, np.ndarray]] = []
        self.max_buffer_size = 10000
        
        # Learned dynamics
        self.dynamics_type = DynamicsType.RANDOM_WALK
        self.regime_transition_matrix = np.array([
            [0.95, 0.03, 0.02],  # Trending -> Trending, MeanRev, Random
            [0.05, 0.90, 0.05],  # MeanRev -> ...
            [0.10, 0.10, 0.80]   # Random -> ...
        ])
        
        logger.info("WorldModel initialized")
    
    def encode_state(self, market_data: Dict[str, Any]) -> np.ndarray:
        """Encode market data into state vector"""
        
        state = np.zeros(self.state_dim)
        
        if 'price' in market_data:
            state[0] = market_data['price']
        if 'volume' in market_data:
            state[1] = market_data['volume']
        if 'volatility' in market_data:
            state[2] = market_data['volatility']
        if 'returns' in market_data:
            returns = market_data['returns']
            if len(returns) >= 5:
                state[3:8] = returns[-5:]
        
        return state
    
    def predict_next_state(
        self,
        state: np.ndarray,
        action: int
    ) -> Tuple[np.ndarray, float]:
        """
        Predict next state and reward given current state and action
        
        Args:
            state: Current state vector
            action: Action taken (0=sell, 1=hold, 2=buy)
        
        Returns:
            (next_state, reward)
        """
        
        # One-hot encode action
        action_vec = np.zeros(self.action_dim)
        action_vec[action] = 1.0
        
        # Concatenate state and action
        input_vec = np.concatenate([state, action_vec])
        
        # Predict next state
        next_state = state + np.tanh(input_vec @ self.transition_weights) * 0.1
        
        # Predict reward
        reward = float(np.tanh(input_vec @ self.reward_weights))
        
        return next_state, reward
    
    def add_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray
    ):
        """Add experience to buffer"""
        
        self.experience_buffer.append((state, action, reward, next_state))
        
        if len(self.experience_buffer) > self.max_buffer_size:
            self.experience_buffer.pop(0)
    
    def train(self, batch_size: int = 32, epochs: int = 10):
        """Train world model on experience buffer"""
        
        if len(self.experience_buffer) < batch_size:
            return
        
        for epoch in range(epochs):
            # Sample batch
            indices = np.random.choice(len(self.experience_buffer), batch_size, replace=False)
            batch = [self.experience_buffer[i] for i in indices]
            
            total_loss = 0.0
            
            for state, action, reward, next_state in batch:
                # Predict
                pred_next, pred_reward = self.predict_next_state(state, action)
                
                # Compute errors
                state_error = next_state - pred_next
                reward_error = reward - pred_reward
                
                # Update weights (simplified gradient descent)
                action_vec = np.zeros(self.action_dim)
                action_vec[action] = 1.0
                input_vec = np.concatenate([state, action_vec])
                
                self.transition_weights += self.learning_rate * np.outer(
                    input_vec, state_error
                )
                self.reward_weights += self.learning_rate * input_vec.reshape(-1, 1) * reward_error
                
                total_loss += np.sum(state_error ** 2) + reward_error ** 2
            
            avg_loss = total_loss / batch_size
            
            if (epoch + 1) % 5 == 0:
                logger.debug(f"World model training epoch {epoch + 1}: loss = {avg_loss:.4f}")
    
    def simulate_trajectory(
        self,
        initial_state: np.ndarray,
        policy: Callable[[np.ndarray], int],
        horizon: int = 50
    ) -> List[Tuple[np.ndarray, int, float]]:
        """
        Simulate trajectory using learned model
        
        Args:
            initial_state: Starting state
            policy: Function that maps state to action
            horizon: Number of steps to simulate
        
        Returns:
            List of (state, action, reward) tuples
        """
        
        trajectory = []
        state = initial_state.copy()
        
        for _ in range(horizon):
            action = policy(state)
            next_state, reward = self.predict_next_state(state, action)
            
            trajectory.append((state.copy(), action, reward))
            state = next_state
        
        return trajectory
    
    def plan_with_mpc(
        self,
        current_state: np.ndarray,
        horizon: int = 10,
        num_samples: int = 100
    ) -> int:
        """
        Model Predictive Control planning
        
        Args:
            current_state: Current state
            horizon: Planning horizon
            num_samples: Number of action sequences to sample
        
        Returns:
            Best first action
        """
        
        best_action = 1  # Default: hold
        best_return = float('-inf')
        
        for _ in range(num_samples):
            # Sample random action sequence
            actions = np.random.randint(0, self.action_dim, horizon)
            
            # Simulate trajectory
            state = current_state.copy()
            total_return = 0.0
            discount = 0.99
            
            for t, action in enumerate(actions):
                next_state, reward = self.predict_next_state(state, action)
                total_return += (discount ** t) * reward
                state = next_state
            
            if total_return > best_return:
                best_return = total_return
                best_action = actions[0]
        
        return int(best_action)
    
    def detect_regime(self, price_history: np.ndarray) -> DynamicsType:
        """Detect current market regime"""
        
        if len(price_history) < 20:
            return DynamicsType.RANDOM_WALK
        
        returns = np.diff(price_history) / price_history[:-1]
        
        # Hurst exponent approximation
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Autocorrelation
        if len(returns) > 1:
            autocorr = np.corrcoef(returns[:-1], returns[1:])[0, 1]
        else:
            autocorr = 0
        
        if autocorr > 0.3:
            return DynamicsType.TRENDING
        elif autocorr < -0.3:
            return DynamicsType.MEAN_REVERTING
        else:
            return DynamicsType.RANDOM_WALK


# =============================================================================
# DIGITAL TWIN OF TRADING SYSTEM
# =============================================================================

@dataclass
class TwinState:
    """State of the digital twin"""
    timestamp: datetime
    equity: float
    positions: Dict[str, float]
    open_orders: List[Dict[str, Any]]
    realized_pnl: float
    unrealized_pnl: float
    margin_used: float
    
    def copy(self) -> 'TwinState':
        return TwinState(
            timestamp=self.timestamp,
            equity=self.equity,
            positions=self.positions.copy(),
            open_orders=list(self.open_orders),
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
            margin_used=self.margin_used
        )


class DigitalTwin:
    """
    Digital Twin of Trading System
    
    A perfect replica of the trading system for safe
    experimentation and testing.
    """
    
    def __init__(
        self,
        initial_equity: float = 100000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005
    ):
        self.initial_equity = initial_equity
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        
        self.state = TwinState(
            timestamp=datetime.utcnow(),
            equity=initial_equity,
            positions={},
            open_orders=[],
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            margin_used=0.0
        )
        
        self.state_history: List[TwinState] = []
        self.trade_history: List[Dict[str, Any]] = []
        
        # Market data
        self.current_prices: Dict[str, float] = {}
        
        logger.info("DigitalTwin initialized")
    
    def sync_with_live(self, live_state: Dict[str, Any]):
        """Synchronize twin with live system state"""
        
        self.state = TwinState(
            timestamp=datetime.utcnow(),
            equity=live_state.get('equity', self.initial_equity),
            positions=live_state.get('positions', {}),
            open_orders=live_state.get('open_orders', []),
            realized_pnl=live_state.get('realized_pnl', 0.0),
            unrealized_pnl=live_state.get('unrealized_pnl', 0.0),
            margin_used=live_state.get('margin_used', 0.0)
        )
        
        logger.info("Digital twin synchronized with live system")
    
    def update_prices(self, prices: Dict[str, float]):
        """Update current market prices"""
        self.current_prices.update(prices)
        self._update_unrealized_pnl()
    
    def _update_unrealized_pnl(self):
        """Update unrealized P&L based on current prices"""
        
        unrealized = 0.0
        
        for symbol, position in self.state.positions.items():
            if symbol in self.current_prices:
                # Simplified: assume position is quantity * entry_price
                current_value = position * self.current_prices[symbol]
                unrealized += current_value - position  # Simplified
        
        self.state.unrealized_pnl = unrealized
    
    def execute_order(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        quantity: float,
        order_type: str = 'market'
    ) -> Dict[str, Any]:
        """Execute an order in the twin"""
        
        if symbol not in self.current_prices:
            return {'success': False, 'error': 'No price available'}
        
        price = self.current_prices[symbol]
        
        # Apply slippage
        if side == 'buy':
            fill_price = price * (1 + self.slippage_rate)
        else:
            fill_price = price * (1 - self.slippage_rate)
        
        # Calculate commission
        commission = quantity * fill_price * self.commission_rate
        
        # Update position
        current_position = self.state.positions.get(symbol, 0.0)
        
        if side == 'buy':
            new_position = current_position + quantity
            cost = quantity * fill_price + commission
            self.state.equity -= cost
        else:
            new_position = current_position - quantity
            proceeds = quantity * fill_price - commission
            self.state.equity += proceeds
        
        self.state.positions[symbol] = new_position
        
        # Record trade
        trade = {
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': fill_price,
            'commission': commission
        }
        self.trade_history.append(trade)
        
        return {'success': True, 'trade': trade}
    
    def simulate_strategy(
        self,
        strategy_function: Callable[[Dict[str, Any]], Dict[str, Any]],
        price_sequence: Dict[str, np.ndarray],
        initial_state: Optional[TwinState] = None
    ) -> Dict[str, Any]:
        """
        Simulate a strategy over price sequence
        
        Args:
            strategy_function: Function that takes market data and returns orders
            price_sequence: Dict of symbol -> price array
            initial_state: Optional initial state
        
        Returns:
            Simulation results
        """
        
        if initial_state:
            self.state = initial_state.copy()
        
        # Get sequence length
        seq_length = min(len(prices) for prices in price_sequence.values())
        
        equity_curve = [self.state.equity]
        
        for i in range(seq_length):
            # Update prices
            current_prices = {
                symbol: prices[i]
                for symbol, prices in price_sequence.items()
            }
            self.update_prices(current_prices)
            
            # Get strategy decision
            market_data = {
                'prices': current_prices,
                'positions': self.state.positions,
                'equity': self.state.equity
            }
            
            try:
                orders = strategy_function(market_data)
                
                # Execute orders
                if orders:
                    for order in orders if isinstance(orders, list) else [orders]:
                        if 'symbol' in order and 'side' in order:
                            self.execute_order(
                                order['symbol'],
                                order['side'],
                                order.get('quantity', 1.0)
                            )
            except Exception as e:
                logger.warning(f"Strategy error at step {i}: {e}")
            
            equity_curve.append(self.state.equity)
            self.state_history.append(self.state.copy())
        
        # Calculate metrics
        equity_curve = np.array(equity_curve)
        returns = np.diff(equity_curve) / equity_curve[:-1]
        
        return {
            'final_equity': self.state.equity,
            'total_return': (self.state.equity - self.initial_equity) / self.initial_equity,
            'num_trades': len(self.trade_history),
            'sharpe_ratio': np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252),
            'max_drawdown': self._calculate_max_drawdown(equity_curve),
            'equity_curve': equity_curve.tolist()
        }
    
    def _calculate_max_drawdown(self, equity_curve: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        peak = equity_curve[0]
        max_dd = 0.0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def fork(self) -> 'DigitalTwin':
        """Create a fork of the twin for parallel experimentation"""
        
        forked = DigitalTwin(
            initial_equity=self.initial_equity,
            commission_rate=self.commission_rate,
            slippage_rate=self.slippage_rate
        )
        
        forked.state = self.state.copy()
        forked.current_prices = self.current_prices.copy()
        
        return forked
    
    def compare_scenarios(
        self,
        strategy_function: Callable,
        base_prices: Dict[str, np.ndarray],
        scenario_prices: List[Dict[str, np.ndarray]],
        scenario_names: List[str]
    ) -> Dict[str, Any]:
        """Compare strategy performance across scenarios"""
        
        results = {}
        
        # Base scenario
        base_twin = self.fork()
        results['base'] = base_twin.simulate_strategy(strategy_function, base_prices)
        
        # Alternative scenarios
        for name, prices in zip(scenario_names, scenario_prices):
            scenario_twin = self.fork()
            results[name] = scenario_twin.simulate_strategy(strategy_function, prices)
        
        return results


# =============================================================================
# ADVERSARIAL MARKET SIMULATOR
# =============================================================================

class AdversarialMarketSimulator:
    """
    Adversarial Market Simulator
    
    Generates challenging market conditions to stress test
    trading strategies.
    """
    
    def __init__(self, base_price: float = 100.0):
        self.base_price = base_price
        self.scenarios: Dict[str, Callable] = {}
        
        # Register default scenarios
        self._register_default_scenarios()
        
        logger.info("AdversarialMarketSimulator initialized")
    
    def _register_default_scenarios(self):
        """Register default adversarial scenarios"""
        
        self.scenarios['flash_crash'] = self._generate_flash_crash
        self.scenarios['flash_rally'] = self._generate_flash_rally
        self.scenarios['whipsaw'] = self._generate_whipsaw
        self.scenarios['liquidity_crisis'] = self._generate_liquidity_crisis
        self.scenarios['trending_trap'] = self._generate_trending_trap
        self.scenarios['stop_hunt'] = self._generate_stop_hunt
        self.scenarios['gap_down'] = self._generate_gap_down
        self.scenarios['volatility_explosion'] = self._generate_volatility_explosion
    
    def _generate_flash_crash(
        self,
        length: int,
        crash_magnitude: float = 0.15,
        crash_duration: int = 10,
        recovery_duration: int = 50
    ) -> np.ndarray:
        """Generate flash crash scenario"""
        
        prices = np.ones(length) * self.base_price
        
        # Normal period
        crash_start = length // 3
        
        for i in range(crash_start):
            prices[i] = self.base_price * (1 + np.random.randn() * 0.01)
        
        # Crash
        for i in range(crash_duration):
            idx = crash_start + i
            if idx < length:
                progress = i / crash_duration
                drop = crash_magnitude * (1 - np.exp(-3 * progress))
                prices[idx] = prices[crash_start - 1] * (1 - drop)
        
        # Recovery
        crash_bottom = prices[crash_start + crash_duration - 1]
        for i in range(recovery_duration):
            idx = crash_start + crash_duration + i
            if idx < length:
                progress = i / recovery_duration
                recovery = (self.base_price - crash_bottom) * (1 - np.exp(-2 * progress))
                prices[idx] = crash_bottom + recovery + np.random.randn() * 0.5
        
        # Post-recovery
        for i in range(crash_start + crash_duration + recovery_duration, length):
            prices[i] = prices[i-1] * (1 + np.random.randn() * 0.01)
        
        return prices
    
    def _generate_flash_rally(
        self,
        length: int,
        rally_magnitude: float = 0.10
    ) -> np.ndarray:
        """Generate flash rally (inverse of crash)"""
        
        prices = self._generate_flash_crash(length, -rally_magnitude)
        return prices
    
    def _generate_whipsaw(
        self,
        length: int,
        num_whipsaws: int = 5,
        magnitude: float = 0.05
    ) -> np.ndarray:
        """Generate whipsaw pattern"""
        
        prices = np.ones(length) * self.base_price
        
        whipsaw_interval = length // (num_whipsaws + 1)
        
        for i in range(length):
            base = self.base_price
            
            # Add whipsaw spikes
            for w in range(num_whipsaws):
                whipsaw_center = (w + 1) * whipsaw_interval
                distance = abs(i - whipsaw_center)
                
                if distance < whipsaw_interval // 4:
                    direction = 1 if w % 2 == 0 else -1
                    spike = direction * magnitude * np.exp(-distance / 5)
                    base *= (1 + spike)
            
            prices[i] = base + np.random.randn() * 0.5
        
        return prices
    
    def _generate_liquidity_crisis(
        self,
        length: int,
        crisis_start: Optional[int] = None,
        spread_multiplier: float = 10.0
    ) -> np.ndarray:
        """Generate liquidity crisis with wide spreads"""
        
        prices = np.ones(length) * self.base_price
        
        if crisis_start is None:
            crisis_start = length // 2
        
        for i in range(length):
            if i < crisis_start:
                noise = np.random.randn() * 0.01
            else:
                # High volatility during crisis
                noise = np.random.randn() * 0.05
            
            prices[i] = prices[max(0, i-1)] * (1 + noise)
        
        return prices
    
    def _generate_trending_trap(
        self,
        length: int,
        trend_duration: int = 50,
        reversal_speed: int = 10
    ) -> np.ndarray:
        """Generate trending trap (false breakout)"""
        
        prices = np.ones(length) * self.base_price
        
        # Build up trend
        trend_start = length // 4
        
        for i in range(trend_start):
            prices[i] = self.base_price * (1 + np.random.randn() * 0.005)
        
        # Strong trend
        for i in range(trend_duration):
            idx = trend_start + i
            if idx < length:
                trend = 0.002 * i  # Gradual uptrend
                prices[idx] = prices[idx-1] * (1 + trend + np.random.randn() * 0.005)
        
        # Sharp reversal
        reversal_start = trend_start + trend_duration
        for i in range(reversal_speed):
            idx = reversal_start + i
            if idx < length:
                reversal = -0.01 * (i + 1)
                prices[idx] = prices[idx-1] * (1 + reversal)
        
        # Continue lower
        for i in range(reversal_start + reversal_speed, length):
            prices[i] = prices[i-1] * (1 - 0.001 + np.random.randn() * 0.01)
        
        return prices
    
    def _generate_stop_hunt(
        self,
        length: int,
        hunt_magnitude: float = 0.03
    ) -> np.ndarray:
        """Generate stop hunt pattern"""
        
        prices = np.ones(length) * self.base_price
        
        # Normal trading
        for i in range(length // 2):
            prices[i] = self.base_price * (1 + np.random.randn() * 0.005)
        
        # Stop hunt spike
        hunt_start = length // 2
        hunt_duration = 5
        
        for i in range(hunt_duration):
            idx = hunt_start + i
            if idx < length:
                if i < hunt_duration // 2:
                    spike = hunt_magnitude * (i + 1) / (hunt_duration // 2)
                else:
                    spike = hunt_magnitude * (hunt_duration - i) / (hunt_duration // 2)
                prices[idx] = prices[hunt_start - 1] * (1 + spike)
        
        # Return to normal
        for i in range(hunt_start + hunt_duration, length):
            prices[i] = self.base_price * (1 + np.random.randn() * 0.005)
        
        return prices
    
    def _generate_gap_down(
        self,
        length: int,
        gap_size: float = 0.05
    ) -> np.ndarray:
        """Generate gap down scenario"""
        
        prices = np.ones(length) * self.base_price
        
        gap_point = length // 2
        
        for i in range(gap_point):
            prices[i] = self.base_price * (1 + np.random.randn() * 0.005)
        
        # Gap down
        prices[gap_point] = prices[gap_point - 1] * (1 - gap_size)
        
        # Continue after gap
        for i in range(gap_point + 1, length):
            prices[i] = prices[i-1] * (1 + np.random.randn() * 0.01)
        
        return prices
    
    def _generate_volatility_explosion(
        self,
        length: int,
        explosion_factor: float = 5.0
    ) -> np.ndarray:
        """Generate volatility explosion"""
        
        prices = np.ones(length) * self.base_price
        
        explosion_start = length // 3
        explosion_duration = length // 3
        
        for i in range(length):
            if i < explosion_start:
                vol = 0.01
            elif i < explosion_start + explosion_duration:
                progress = (i - explosion_start) / explosion_duration
                vol = 0.01 * (1 + (explosion_factor - 1) * progress)
            else:
                vol = 0.01 * explosion_factor
            
            prices[i] = prices[max(0, i-1)] * (1 + np.random.randn() * vol)
        
        return prices
    
    def generate_scenario(
        self,
        scenario_name: str,
        length: int = 500,
        **kwargs
    ) -> np.ndarray:
        """Generate a specific scenario"""
        
        if scenario_name not in self.scenarios:
            logger.warning(f"Unknown scenario: {scenario_name}")
            return np.ones(length) * self.base_price
        
        return self.scenarios[scenario_name](length, **kwargs)
    
    def generate_all_scenarios(
        self,
        length: int = 500
    ) -> Dict[str, np.ndarray]:
        """Generate all adversarial scenarios"""
        
        return {
            name: generator(length)
            for name, generator in self.scenarios.items()
        }


# =============================================================================
# MULTI-FIDELITY SIMULATION
# =============================================================================

class FidelityLevel(Enum):
    """Simulation fidelity levels"""
    LOW = "low"  # Fast, approximate
    MEDIUM = "medium"  # Balanced
    HIGH = "high"  # Accurate, slow
    ULTRA = "ultra"  # Maximum accuracy


@dataclass
class SimulationConfig:
    """Configuration for simulation"""
    fidelity: FidelityLevel
    tick_size: float
    spread_model: str
    slippage_model: str
    market_impact: bool
    latency_simulation: bool
    order_book_depth: int


class MultiFidelitySimulator:
    """
    Multi-Fidelity Simulation
    
    Adaptive simulation that balances speed and accuracy
    based on requirements.
    """
    
    def __init__(self):
        self.configs = {
            FidelityLevel.LOW: SimulationConfig(
                fidelity=FidelityLevel.LOW,
                tick_size=0.01,
                spread_model='fixed',
                slippage_model='none',
                market_impact=False,
                latency_simulation=False,
                order_book_depth=1
            ),
            FidelityLevel.MEDIUM: SimulationConfig(
                fidelity=FidelityLevel.MEDIUM,
                tick_size=0.001,
                spread_model='variable',
                slippage_model='linear',
                market_impact=False,
                latency_simulation=False,
                order_book_depth=5
            ),
            FidelityLevel.HIGH: SimulationConfig(
                fidelity=FidelityLevel.HIGH,
                tick_size=0.0001,
                spread_model='stochastic',
                slippage_model='nonlinear',
                market_impact=True,
                latency_simulation=True,
                order_book_depth=10
            ),
            FidelityLevel.ULTRA: SimulationConfig(
                fidelity=FidelityLevel.ULTRA,
                tick_size=0.00001,
                spread_model='microstructure',
                slippage_model='full',
                market_impact=True,
                latency_simulation=True,
                order_book_depth=20
            )
        }
        
        self.current_fidelity = FidelityLevel.MEDIUM
        
        logger.info("MultiFidelitySimulator initialized")
    
    def set_fidelity(self, fidelity: FidelityLevel):
        """Set simulation fidelity level"""
        self.current_fidelity = fidelity
        logger.info(f"Simulation fidelity set to {fidelity.value}")
    
    def auto_select_fidelity(
        self,
        time_budget_seconds: float,
        num_simulations: int,
        accuracy_requirement: float
    ) -> FidelityLevel:
        """Automatically select appropriate fidelity level"""
        
        time_per_sim = time_budget_seconds / num_simulations
        
        if time_per_sim < 0.01:
            fidelity = FidelityLevel.LOW
        elif time_per_sim < 0.1:
            fidelity = FidelityLevel.MEDIUM
        elif time_per_sim < 1.0:
            fidelity = FidelityLevel.HIGH
        else:
            fidelity = FidelityLevel.ULTRA
        
        # Adjust for accuracy requirement
        if accuracy_requirement > 0.95 and fidelity.value in ['low', 'medium']:
            fidelity = FidelityLevel.HIGH
        
        self.current_fidelity = fidelity
        return fidelity
    
    def simulate_execution(
        self,
        order_type: str,
        side: str,
        quantity: float,
        price: float,
        market_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate order execution at current fidelity"""
        
        config = self.configs[self.current_fidelity]
        
        # Base fill price
        fill_price = price
        
        # Apply spread
        if config.spread_model == 'fixed':
            spread = 0.0001
        elif config.spread_model == 'variable':
            spread = 0.0001 * (1 + market_state.get('volatility', 0) * 10)
        elif config.spread_model == 'stochastic':
            spread = 0.0001 * (1 + np.random.exponential(0.5))
        else:
            spread = 0.0002
        
        if side == 'buy':
            fill_price += spread / 2
        else:
            fill_price -= spread / 2
        
        # Apply slippage
        if config.slippage_model == 'linear':
            slippage = quantity * 0.00001
        elif config.slippage_model == 'nonlinear':
            slippage = quantity ** 1.5 * 0.000001
        elif config.slippage_model == 'full':
            # Full market impact model
            volume = market_state.get('volume', 1000000)
            participation = quantity / volume
            slippage = participation ** 0.5 * 0.01
        else:
            slippage = 0
        
        if side == 'buy':
            fill_price *= (1 + slippage)
        else:
            fill_price *= (1 - slippage)
        
        # Simulate latency
        latency_ms = 0
        if config.latency_simulation:
            latency_ms = np.random.exponential(10)  # Average 10ms
        
        return {
            'fill_price': fill_price,
            'fill_quantity': quantity,
            'slippage': abs(fill_price - price) / price,
            'latency_ms': latency_ms,
            'fidelity': self.current_fidelity.value
        }
    
    def run_backtest(
        self,
        strategy_function: Callable,
        price_data: np.ndarray,
        fidelity: Optional[FidelityLevel] = None
    ) -> Dict[str, Any]:
        """Run backtest at specified fidelity"""
        
        if fidelity:
            self.set_fidelity(fidelity)
        
        config = self.configs[self.current_fidelity]
        
        equity = 100000.0
        position = 0.0
        trades = []
        
        for i in range(1, len(price_data)):
            market_state = {
                'price': price_data[i],
                'volatility': np.std(price_data[max(0, i-20):i]) / np.mean(price_data[max(0, i-20):i]) if i > 1 else 0.01,
                'volume': 1000000
            }
            
            # Get strategy signal
            try:
                signal = strategy_function({
                    'price': price_data[i],
                    'position': position,
                    'equity': equity
                })
            except:
                signal = {'action': 'hold'}
            
            action = signal.get('action', 'hold')
            
            if action == 'buy' and position <= 0:
                execution = self.simulate_execution(
                    'market', 'buy', 1.0, price_data[i], market_state
                )
                position = 1.0
                equity -= execution['fill_price']
                trades.append(execution)
            
            elif action == 'sell' and position >= 0:
                execution = self.simulate_execution(
                    'market', 'sell', 1.0, price_data[i], market_state
                )
                position = -1.0
                equity += execution['fill_price']
                trades.append(execution)
        
        return {
            'final_equity': equity + position * price_data[-1],
            'num_trades': len(trades),
            'fidelity': self.current_fidelity.value,
            'avg_slippage': np.mean([t['slippage'] for t in trades]) if trades else 0
        }


# =============================================================================
# INTEGRATED SIMULATION SYSTEM
# =============================================================================

class IntegratedSimulationSystem:
    """
    Integrated Simulation System
    
    Combines all simulation components for comprehensive
    strategy testing and development.
    """
    
    def __init__(self):
        self.world_model = WorldModel()
        self.digital_twin = DigitalTwin()
        self.adversarial_sim = AdversarialMarketSimulator()
        self.multi_fidelity = MultiFidelitySimulator()
        
        logger.info("IntegratedSimulationSystem initialized")
    
    async def comprehensive_simulation(
        self,
        strategy_function: Callable,
        historical_data: np.ndarray,
        num_scenarios: int = 10
    ) -> Dict[str, Any]:
        """
        Run comprehensive simulation suite
        
        Args:
            strategy_function: Strategy to test
            historical_data: Historical price data
            num_scenarios: Number of adversarial scenarios
        
        Returns:
            Comprehensive simulation results
        """
        
        results = {}
        
        # 1. Historical backtest
        results['historical'] = self.multi_fidelity.run_backtest(
            strategy_function, historical_data, FidelityLevel.HIGH
        )
        
        # 2. Adversarial scenarios
        adversarial_results = {}
        scenarios = self.adversarial_sim.generate_all_scenarios(len(historical_data))
        
        for name, prices in scenarios.items():
            adversarial_results[name] = self.multi_fidelity.run_backtest(
                strategy_function, prices, FidelityLevel.MEDIUM
            )
        
        results['adversarial'] = adversarial_results
        
        # 3. World model planning
        initial_state = self.world_model.encode_state({'price': historical_data[-1]})
        best_action = self.world_model.plan_with_mpc(initial_state)
        results['world_model_recommendation'] = ['sell', 'hold', 'buy'][best_action]
        
        # 4. Summary statistics
        all_returns = [results['historical']['final_equity'] / 100000 - 1]
        for r in adversarial_results.values():
            all_returns.append(r['final_equity'] / 100000 - 1)
        
        results['summary'] = {
            'mean_return': np.mean(all_returns),
            'worst_return': np.min(all_returns),
            'best_return': np.max(all_returns),
            'return_std': np.std(all_returns),
            'robustness_score': np.mean([1 if r > 0 else 0 for r in all_returns])
        }
        
        return results
    
    def get_report(self) -> Dict[str, Any]:
        """Get simulation system report"""
        
        return {
            'world_model_experience': len(self.world_model.experience_buffer),
            'digital_twin_trades': len(self.digital_twin.trade_history),
            'adversarial_scenarios': len(self.adversarial_sim.scenarios),
            'current_fidelity': self.multi_fidelity.current_fidelity.value
        }


# Convenience functions
def create_simulation_system() -> IntegratedSimulationSystem:
    """Create integrated simulation system"""
    return IntegratedSimulationSystem()

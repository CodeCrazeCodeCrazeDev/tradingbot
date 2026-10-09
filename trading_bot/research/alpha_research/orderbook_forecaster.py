"""
Predictive Order-Book Dynamics
==============================
Advanced LOB forecasting and counterfactual simulation.

Features:
- Sequence models for LOB prediction
- Price ladder forecasting
- Fill probability estimation
- Counterfactual simulators
- Agent-based market simulation
- Game-theoretic reasoning

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import threading

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class LOBSnapshot:
    """Order book snapshot"""
    timestamp: datetime
    symbol: str
    
    # Price levels (price, size, order_count)
    bids: List[Tuple[float, float, int]] = field(default_factory=list)
    asks: List[Tuple[float, float, int]] = field(default_factory=list)
    
    # Derived
    mid_price: float = 0.0
    spread: float = 0.0
    imbalance: float = 0.0


@dataclass
class LOBForecast:
    """Order book forecast"""
    timestamp: datetime
    horizon_ms: int
    
    # Price predictions
    predicted_mid: float = 0.0
    predicted_spread: float = 0.0
    
    # Direction probability
    up_probability: float = 0.5
    down_probability: float = 0.5
    
    # Fill probabilities at price levels
    bid_fill_probs: Dict[float, float] = field(default_factory=dict)
    ask_fill_probs: Dict[float, float] = field(default_factory=dict)
    
    # Confidence
    confidence: float = 0.5


@dataclass
class CounterfactualResult:
    """Result of counterfactual simulation"""
    scenario: str
    
    # Our order
    order_size: float
    order_side: str
    order_price: float
    
    # Outcomes
    fill_probability: float = 0.0
    expected_fill_price: float = 0.0
    expected_slippage_bps: float = 0.0
    market_impact_bps: float = 0.0
    
    # Alternative scenarios
    alternatives: List[Dict] = field(default_factory=list)


@dataclass
class GameTheoreticEquilibrium:
    """Game-theoretic equilibrium result"""
    timestamp: datetime
    
    # Players
    player_types: List[str] = field(default_factory=list)
    
    # Equilibrium
    equilibrium_price: float = 0.0
    equilibrium_spread: float = 0.0
    
    # Pressures
    buy_pressure: float = 0.0
    sell_pressure: float = 0.0
    
    # Predictions
    short_term_direction: str = "neutral"
    confidence: float = 0.5


# ============================================================================
# LOB Encoder Network
# ============================================================================

if TORCH_AVAILABLE:
    class LOBEncoder(nn.Module):
        """Encode LOB state"""
        
        def __init__(self, n_levels: int = 10, hidden_dim: int = 64):
            super().__init__()
            
            # Input: bid prices, bid sizes, ask prices, ask sizes
            input_dim = n_levels * 4
            
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU()
            )
            
        def forward(self, x):
            return self.encoder(x)
    
    
    class TemporalLOBModel(nn.Module):
        """Temporal model for LOB sequences"""
        
        def __init__(
            self,
            n_levels: int = 10,
            hidden_dim: int = 64,
            n_heads: int = 4,
            n_layers: int = 2
        ):
            super().__init__()
            
            self.lob_encoder = LOBEncoder(n_levels, hidden_dim)
            
            # Transformer for temporal modeling
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=hidden_dim,
                nhead=n_heads,
                dim_feedforward=hidden_dim * 4,
                batch_first=True
            )
            self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
            
            # Output heads
            self.price_head = nn.Linear(hidden_dim, 1)  # Mid price change
            self.spread_head = nn.Linear(hidden_dim, 1)  # Spread
            self.direction_head = nn.Linear(hidden_dim, 3)  # Up/Down/Neutral
            
        def forward(self, x_seq):
            # x_seq: (batch, seq_len, n_levels * 4)
            batch_size, seq_len, _ = x_seq.shape
            
            # Encode each timestep
            encoded = []
            for t in range(seq_len):
                enc = self.lob_encoder(x_seq[:, t, :])
                encoded.append(enc)
            
            encoded = torch.stack(encoded, dim=1)  # (batch, seq_len, hidden)
            
            # Temporal modeling
            temporal = self.transformer(encoded)
            
            # Use last timestep for prediction
            last = temporal[:, -1, :]
            
            price_change = self.price_head(last)
            spread = self.spread_head(last)
            direction = self.direction_head(last)
            
            return price_change, spread, direction


# ============================================================================
# LOB Forecaster
# ============================================================================

class LOBForecaster:
    """Predictive order book dynamics"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.snapshot_history: deque = deque(maxlen=1000)
        self.n_levels = self.config.get('n_levels', 10)
        
        # Model
        self.model = None
        if TORCH_AVAILABLE:
            self.model = TemporalLOBModel(n_levels=self.n_levels)
        
        self.is_trained = False
        
    def add_snapshot(self, snapshot: LOBSnapshot):
        """Add LOB snapshot"""
        
        # Calculate derived metrics
        if snapshot.bids and snapshot.asks:
            snapshot.mid_price = (snapshot.bids[0][0] + snapshot.asks[0][0]) / 2
            snapshot.spread = snapshot.asks[0][0] - snapshot.bids[0][0]
            
            bid_vol = sum(b[1] for b in snapshot.bids[:5])
            ask_vol = sum(a[1] for a in snapshot.asks[:5])
            snapshot.imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol) if (bid_vol + ask_vol) > 0 else 0
        
        self.snapshot_history.append(snapshot)
    
    def _snapshot_to_features(self, snapshot: LOBSnapshot) -> np.ndarray:
        """Convert snapshot to feature vector"""
        
        features = []
        
        # Bid levels
        for i in range(self.n_levels):
            if i < len(snapshot.bids):
                features.append(snapshot.bids[i][0])  # Price
                features.append(snapshot.bids[i][1])  # Size
            else:
                features.append(0)
                features.append(0)
        
        # Ask levels
        for i in range(self.n_levels):
            if i < len(snapshot.asks):
                features.append(snapshot.asks[i][0])
                features.append(snapshot.asks[i][1])
            else:
                features.append(0)
                features.append(0)
        
        return np.array(features)
    
    def forecast(self, horizon_ms: int = 100) -> LOBForecast:
        """Forecast LOB dynamics"""
        
        if len(self.snapshot_history) < 20:
            return LOBForecast(timestamp=datetime.now(), horizon_ms=horizon_ms)
        
        recent = list(self.snapshot_history)[-20:]
        current = recent[-1]
        
        # Simple statistical forecast if model not trained
        if not self.is_trained or self.model is None:
            return self._statistical_forecast(recent, horizon_ms)
        
        # Neural forecast
        return self._neural_forecast(recent, horizon_ms)
    
    def _statistical_forecast(
        self,
        snapshots: List[LOBSnapshot],
        horizon_ms: int
    ) -> LOBForecast:
        """Statistical LOB forecast"""
        
        current = snapshots[-1]
        
        # Price momentum
        mids = [s.mid_price for s in snapshots if s.mid_price > 0]
        if len(mids) >= 5:
            momentum = (mids[-1] - mids[-5]) / mids[-5] if mids[-5] > 0 else 0
        else:
            momentum = 0
        
        # Imbalance signal
        imbalances = [s.imbalance for s in snapshots]
        avg_imbalance = np.mean(imbalances)
        
        # Predict direction
        signal = 0.6 * avg_imbalance + 0.4 * np.sign(momentum)
        
        if signal > 0.2:
            up_prob = 0.5 + signal * 0.3
            down_prob = 1 - up_prob
        elif signal < -0.2:
            down_prob = 0.5 - signal * 0.3
            up_prob = 1 - down_prob
        else:
            up_prob = 0.5
            down_prob = 0.5
        
        # Predict mid price
        predicted_mid = current.mid_price * (1 + momentum * 0.1)
        
        # Predict spread
        spreads = [s.spread for s in snapshots]
        predicted_spread = np.mean(spreads)
        
        # Fill probabilities
        bid_fill_probs = {}
        ask_fill_probs = {}
        
        for i, (price, size, _) in enumerate(current.bids[:5]):
            # Higher queue position = lower fill prob
            bid_fill_probs[price] = max(0.9 - i * 0.15, 0.2)
        
        for i, (price, size, _) in enumerate(current.asks[:5]):
            ask_fill_probs[price] = max(0.9 - i * 0.15, 0.2)
        
        return LOBForecast(
            timestamp=datetime.now(),
            horizon_ms=horizon_ms,
            predicted_mid=predicted_mid,
            predicted_spread=predicted_spread,
            up_probability=up_prob,
            down_probability=down_prob,
            bid_fill_probs=bid_fill_probs,
            ask_fill_probs=ask_fill_probs,
            confidence=0.6
        )
    
    def _neural_forecast(
        self,
        snapshots: List[LOBSnapshot],
        horizon_ms: int
    ) -> LOBForecast:
        """Neural network LOB forecast"""
        
        if not TORCH_AVAILABLE or self.model is None:
            return self._statistical_forecast(snapshots, horizon_ms)
        
        # Prepare sequence
        features = [self._snapshot_to_features(s) for s in snapshots]
        x = torch.FloatTensor(features).unsqueeze(0)  # (1, seq_len, features)
        
        # Predict
        self.model.eval()
        with torch.no_grad():
            price_change, spread, direction = self.model(x)
        
        current = snapshots[-1]
        
        predicted_mid = current.mid_price * (1 + price_change.item() * 0.01)
        predicted_spread = spread.item()
        
        direction_probs = torch.softmax(direction, dim=1).numpy()[0]
        up_prob = direction_probs[0]
        down_prob = direction_probs[1]
        
        return LOBForecast(
            timestamp=datetime.now(),
            horizon_ms=horizon_ms,
            predicted_mid=predicted_mid,
            predicted_spread=predicted_spread,
            up_probability=up_prob,
            down_probability=down_prob,
            confidence=0.7
        )


# ============================================================================
# Counterfactual Simulator
# ============================================================================

class CounterfactualSimulator:
    """Simulate what-if scenarios"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Impact model parameters
        self.temp_impact_coef = 0.1
        self.perm_impact_coef = 0.05
        
    def simulate_order(
        self,
        order_size: float,
        order_side: str,
        order_price: float,
        current_book: LOBSnapshot,
        adv: float
    ) -> CounterfactualResult:
        """Simulate order execution"""
        
        participation = order_size / adv if adv > 0 else 0.01
        
        # Estimate fill probability
        if order_side == 'buy':
            # Check against ask side
            available = sum(a[1] for a in current_book.asks if a[0] <= order_price)
            fill_prob = min(available / order_size, 1.0) if order_size > 0 else 0
        else:
            # Check against bid side
            available = sum(b[1] for b in current_book.bids if b[0] >= order_price)
            fill_prob = min(available / order_size, 1.0) if order_size > 0 else 0
        
        # Estimate fill price
        if order_side == 'buy':
            # Walk the book
            remaining = order_size
            total_cost = 0
            for price, size, _ in current_book.asks:
                if price > order_price:
                    break
                fill = min(remaining, size)
                total_cost += fill * price
                remaining -= fill
                if remaining <= 0:
                    break
            
            filled = order_size - remaining
            expected_fill_price = total_cost / filled if filled > 0 else order_price
        else:
            remaining = order_size
            total_proceeds = 0
            for price, size, _ in current_book.bids:
                if price < order_price:
                    break
                fill = min(remaining, size)
                total_proceeds += fill * price
                remaining -= fill
                if remaining <= 0:
                    break
            
            filled = order_size - remaining
            expected_fill_price = total_proceeds / filled if filled > 0 else order_price
        
        # Estimate slippage
        if order_side == 'buy':
            slippage_bps = (expected_fill_price - current_book.asks[0][0]) / current_book.asks[0][0] * 10000
        else:
            slippage_bps = (current_book.bids[0][0] - expected_fill_price) / current_book.bids[0][0] * 10000
        
        # Estimate market impact
        market_impact_bps = self.temp_impact_coef * np.sqrt(participation) * 10000
        
        # Generate alternatives
        alternatives = []
        
        # Alternative 1: Smaller size
        if order_size > 1000:
            alt_size = order_size * 0.5
            alt_impact = self.temp_impact_coef * np.sqrt(alt_size / adv) * 10000
            alternatives.append({
                'scenario': 'half_size',
                'size': alt_size,
                'expected_impact_bps': alt_impact
            })
        
        # Alternative 2: Passive limit
        if order_side == 'buy':
            passive_price = current_book.bids[0][0]
        else:
            passive_price = current_book.asks[0][0]
        
        alternatives.append({
            'scenario': 'passive_limit',
            'price': passive_price,
            'expected_fill_prob': 0.3,
            'expected_impact_bps': 0
        })
        
        return CounterfactualResult(
            scenario='base',
            order_size=order_size,
            order_side=order_side,
            order_price=order_price,
            fill_probability=fill_prob,
            expected_fill_price=expected_fill_price,
            expected_slippage_bps=slippage_bps,
            market_impact_bps=market_impact_bps,
            alternatives=alternatives
        )


# ============================================================================
# Agent-Based Simulator
# ============================================================================

class MarketAgent:
    """Base market agent"""
    
    def __init__(self, agent_type: str, inventory: float = 0):
        self.agent_type = agent_type
        self.inventory = inventory
        
    def decide(self, market_state: Dict) -> Optional[Dict]:
        """Make trading decision based on market state"""
        # Base implementation - can be overridden by subclasses
        mid_price = market_state.get('mid_price', 100.0)
        spread = market_state.get('spread', 0.1)
        
        # Simple decision logic
        if spread > 0.2:  # Wide spread - opportunity
            return {
                'action': 'provide_liquidity',
                'price': mid_price,
                'size': 1.0
            }
        
        return None  # No action


class MarketMakerAgent(MarketAgent):
    """Market maker agent"""
    
    def __init__(self, inventory: float = 0, risk_aversion: float = 0.1):
        super().__init__('market_maker', inventory)
        self.risk_aversion = risk_aversion
        
    def decide(self, market_state: Dict) -> Optional[Dict]:
        mid = market_state.get('mid_price', 100)
        volatility = market_state.get('volatility', 0.01)
        
        # Avellaneda-Stoikov optimal spread
        spread = volatility * np.sqrt(1 + self.risk_aversion * abs(self.inventory))
        
        bid = mid - spread / 2 - self.risk_aversion * self.inventory * volatility
        ask = mid + spread / 2 - self.risk_aversion * self.inventory * volatility
        
        return {
            'type': 'quote',
            'bid': bid,
            'ask': ask,
            'size': 100
        }


class MomentumAgent(MarketAgent):
    """Momentum trader agent"""
    
    def __init__(self, threshold: float = 0.001):
        super().__init__('momentum')
        self.threshold = threshold
        
    def decide(self, market_state: Dict) -> Optional[Dict]:
        momentum = market_state.get('momentum', 0)
        
        if momentum > self.threshold:
            return {'type': 'market', 'side': 'buy', 'size': 50}
        elif momentum < -self.threshold:
            return {'type': 'market', 'side': 'sell', 'size': 50}
        
        return None


class AgentBasedSimulator:
    """Agent-based market simulator"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.agents: List[MarketAgent] = []
        
        # Initialize default agents
        self._init_default_agents()
        
    def _init_default_agents(self):
        """Initialize default market agents"""
        
        # Market makers
        for i in range(3):
            self.agents.append(MarketMakerAgent(
                inventory=np.random.randn() * 100,
                risk_aversion=0.05 + np.random.random() * 0.1
            ))
        
        # Momentum traders
        for i in range(5):
            self.agents.append(MomentumAgent(
                threshold=0.0005 + np.random.random() * 0.001
            ))
    
    def simulate_step(
        self,
        market_state: Dict,
        our_order: Optional[Dict] = None
    ) -> Dict:
        """Simulate one market step"""
        
        orders = []
        
        # Collect agent decisions
        for agent in self.agents:
            decision = agent.decide(market_state)
            if decision:
                orders.append(decision)
        
        # Add our order
        if our_order:
            orders.append(our_order)
        
        # Process orders (simplified)
        new_mid = market_state.get('mid_price', 100)
        
        buy_volume = sum(o.get('size', 0) for o in orders if o.get('side') == 'buy')
        sell_volume = sum(o.get('size', 0) for o in orders if o.get('side') == 'sell')
        
        imbalance = (buy_volume - sell_volume) / (buy_volume + sell_volume + 1)
        new_mid = new_mid * (1 + imbalance * 0.0001)
        
        return {
            'mid_price': new_mid,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'imbalance': imbalance
        }
    
    def simulate_trajectory(
        self,
        initial_state: Dict,
        our_order: Optional[Dict],
        n_steps: int = 100
    ) -> List[Dict]:
        """Simulate market trajectory"""
        
        trajectory = [initial_state]
        state = initial_state.copy()
        
        for i in range(n_steps):
            # Add our order only on first step
            order = our_order if i == 0 else None
            
            new_state = self.simulate_step(state, order)
            
            # Update momentum
            new_state['momentum'] = (new_state['mid_price'] - state['mid_price']) / state['mid_price']
            new_state['volatility'] = state.get('volatility', 0.01)
            
            trajectory.append(new_state)
            state = new_state
        
        return trajectory


# ============================================================================
# Game-Theoretic Reasoner
# ============================================================================

class GameTheoreticReasoner:
    """Game-theoretic reasoning for market dynamics"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def analyze_equilibrium(
        self,
        market_state: Dict,
        player_positions: Dict[str, float]
    ) -> GameTheoreticEquilibrium:
        """Analyze game-theoretic equilibrium"""
        
        mid_price = market_state.get('mid_price', 100)
        
        # Identify player types and their pressures
        player_types = list(player_positions.keys())
        
        # Calculate pressures
        buy_pressure = 0
        sell_pressure = 0
        
        for player, position in player_positions.items():
            if 'delta_hedger' in player.lower():
                # Delta hedgers create mean-reverting pressure
                if position > 0:
                    sell_pressure += abs(position) * 0.1
                else:
                    buy_pressure += abs(position) * 0.1
            
            elif 'momentum' in player.lower():
                # Momentum traders amplify trends
                if position > 0:
                    buy_pressure += abs(position) * 0.05
                else:
                    sell_pressure += abs(position) * 0.05
            
            elif 'market_maker' in player.lower():
                # Market makers provide liquidity
                pass  # Neutral pressure
        
        # Calculate equilibrium
        net_pressure = buy_pressure - sell_pressure
        
        equilibrium_price = mid_price * (1 + net_pressure * 0.001)
        equilibrium_spread = market_state.get('spread', 0.01) * (1 + abs(net_pressure) * 0.1)
        
        # Predict direction
        if net_pressure > 0.1:
            direction = "up"
            confidence = min(net_pressure, 1.0)
        elif net_pressure < -0.1:
            direction = "down"
            confidence = min(abs(net_pressure), 1.0)
        else:
            direction = "neutral"
            confidence = 0.5
        
        return GameTheoreticEquilibrium(
            timestamp=datetime.now(),
            player_types=player_types,
            equilibrium_price=equilibrium_price,
            equilibrium_spread=equilibrium_spread,
            buy_pressure=buy_pressure,
            sell_pressure=sell_pressure,
            short_term_direction=direction,
            confidence=confidence
        )
    
    def analyze_gamma_squeeze(
        self,
        spot_price: float,
        gamma_exposure: float,
        delta_hedger_inventory: float
    ) -> Dict[str, Any]:
        """Analyze gamma squeeze dynamics"""
        
        # Gamma squeeze occurs when:
        # 1. Large positive gamma exposure
        # 2. Price moves toward strikes
        # 3. Delta hedgers must buy/sell to stay hedged
        
        squeeze_potential = 0
        
        if gamma_exposure > 0:
            # Positive gamma = dealers short gamma
            # Price up -> dealers buy -> more up
            squeeze_potential = gamma_exposure * 0.1
        
        # Feedback loop strength
        feedback = abs(gamma_exposure) * abs(delta_hedger_inventory) * 0.01
        
        return {
            'squeeze_potential': squeeze_potential,
            'feedback_strength': feedback,
            'direction': 'up' if gamma_exposure > 0 else 'down',
            'recommendation': 'Follow momentum' if squeeze_potential > 0.5 else 'Normal trading'
        }


# ============================================================================
# Main System
# ============================================================================

class OrderBookForecastingSystem:
    """
    Complete Order Book Forecasting System.
    
    Features:
    - Predictive LOB dynamics
    - Counterfactual simulation
    - Agent-based modeling
    - Game-theoretic reasoning
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.lob_forecaster = LOBForecaster(config)
        self.counterfactual = CounterfactualSimulator(config)
        self.agent_simulator = AgentBasedSimulator(config)
        self.game_reasoner = GameTheoreticReasoner(config)
        
        logger.info("OrderBookForecastingSystem initialized")
    
    def update(self, snapshot: LOBSnapshot):
        """Update with new LOB snapshot"""
        self.lob_forecaster.add_snapshot(snapshot)
    
    def forecast(self, horizon_ms: int = 100) -> LOBForecast:
        """Forecast LOB dynamics"""
        return self.lob_forecaster.forecast(horizon_ms)
    
    def simulate_order(
        self,
        order_size: float,
        order_side: str,
        order_price: float,
        adv: float
    ) -> CounterfactualResult:
        """Simulate order execution"""
        
        if not self.lob_forecaster.snapshot_history:
            return CounterfactualResult(
                scenario='no_data',
                order_size=order_size,
                order_side=order_side,
                order_price=order_price
            )
        
        current_book = self.lob_forecaster.snapshot_history[-1]
        return self.counterfactual.simulate_order(
            order_size, order_side, order_price, current_book, adv
        )
    
    def get_optimal_execution(
        self,
        order_size: float,
        order_side: str,
        adv: float,
        urgency: float = 0.5
    ) -> Dict[str, Any]:
        """Get optimal execution recommendation"""
        
        if not self.lob_forecaster.snapshot_history:
            return {'recommendation': 'insufficient_data'}
        
        current_book = self.lob_forecaster.snapshot_history[-1]
        
        # Forecast
        forecast = self.forecast(horizon_ms=1000)
        
        # Simulate different scenarios
        scenarios = []
        
        # Market order
        if order_side == 'buy':
            market_price = current_book.asks[0][0] if current_book.asks else 0
        else:
            market_price = current_book.bids[0][0] if current_book.bids else 0
        
        market_result = self.simulate_order(order_size, order_side, market_price * 1.01, adv)
        scenarios.append(('market', market_result))
        
        # Limit at mid
        mid = current_book.mid_price
        limit_result = self.simulate_order(order_size, order_side, mid, adv)
        scenarios.append(('limit_mid', limit_result))
        
        # Passive limit
        if order_side == 'buy':
            passive_price = current_book.bids[0][0] if current_book.bids else mid * 0.999
        else:
            passive_price = current_book.asks[0][0] if current_book.asks else mid * 1.001
        
        passive_result = self.simulate_order(order_size, order_side, passive_price, adv)
        scenarios.append(('passive', passive_result))
        
        # Choose based on urgency
        if urgency > 0.8:
            recommendation = 'market'
            best_result = market_result
        elif urgency > 0.5:
            recommendation = 'limit_mid'
            best_result = limit_result
        else:
            recommendation = 'passive'
            best_result = passive_result
        
        return {
            'recommendation': recommendation,
            'expected_fill_prob': best_result.fill_probability,
            'expected_slippage_bps': best_result.expected_slippage_bps,
            'expected_impact_bps': best_result.market_impact_bps,
            'forecast': {
                'up_prob': forecast.up_probability,
                'down_prob': forecast.down_probability
            },
            'scenarios': {name: {
                'fill_prob': r.fill_probability,
                'slippage': r.expected_slippage_bps
            } for name, r in scenarios}
        }


# Factory function
def create_orderbook_forecaster(config: Optional[Dict] = None) -> OrderBookForecastingSystem:
    """Create and return an OrderBookForecastingSystem instance"""
    return OrderBookForecastingSystem(config)

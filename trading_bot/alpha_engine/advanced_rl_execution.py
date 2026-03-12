"""
Advanced Reinforcement Learning Execution Module
=================================================

Meta-RL (MAML-based) for Adaptive Trade Execution:
- Full state space (position, time, LOB, trajectory, volatility, impact, P&L)
- Comprehensive action space (order type, size, price, venue)
- Multi-objective reward function
- Adaptive execution policies
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import random
import math

logger = logging.getLogger(__name__)

# Try importing PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class OrderType(Enum):
    """Order types for execution"""
    MARKET = "market"
    LIMIT = "limit"
    LIMIT_IOC = "limit_ioc"  # Immediate or cancel
    LIMIT_FOK = "limit_fok"  # Fill or kill
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"


class ExecutionUrgency(Enum):
    """Execution urgency levels"""
    PASSIVE = "passive"  # Patient, minimize impact
    NORMAL = "normal"  # Balanced
    AGGRESSIVE = "aggressive"  # Fast execution
    URGENT = "urgent"  # Immediate, any cost


@dataclass
class ExecutionState:
    """
    Complete state for RL execution agent
    
    Captures all relevant information for optimal execution decisions
    """
    # Position state
    current_position: float  # Current filled quantity
    target_position: float  # Target quantity to fill
    remaining_quantity: float  # Remaining to fill
    
    # Time state
    time_remaining: float  # Normalized (0-1)
    time_elapsed: float
    
    # LOB features
    bid_price: float
    ask_price: float
    spread: float
    bid_depth: float  # Volume at best bid
    ask_depth: float  # Volume at best ask
    order_imbalance: float  # (bid_vol - ask_vol) / total
    
    # Price trajectory
    price_momentum: float  # Recent price change
    price_volatility: float  # Recent volatility
    vwap: float  # Volume-weighted average price
    
    # Market impact estimates
    estimated_impact: float
    realized_impact: float
    
    # P&L state
    current_pnl: float
    unrealized_pnl: float
    
    # Regime
    volatility_regime: str  # 'low', 'medium', 'high'
    liquidity_regime: str  # 'thin', 'normal', 'deep'
    
    def to_tensor(self) -> np.ndarray:
        """Convert to feature tensor"""
        return np.array([
            self.current_position / max(self.target_position, 1),
            self.remaining_quantity / max(self.target_position, 1),
            self.time_remaining,
            self.time_elapsed,
            self.spread * 10000,  # In bps
            self.bid_depth / 1000,  # Normalized
            self.ask_depth / 1000,
            self.order_imbalance,
            self.price_momentum * 100,
            self.price_volatility * 100,
            self.estimated_impact * 10000,
            self.realized_impact * 10000,
            self.current_pnl / 1000,
            1 if self.volatility_regime == 'high' else (0.5 if self.volatility_regime == 'medium' else 0),
            1 if self.liquidity_regime == 'deep' else (0.5 if self.liquidity_regime == 'normal' else 0),
        ], dtype=np.float32)


@dataclass
class ExecutionAction:
    """
    Action taken by execution agent
    """
    order_type: OrderType
    size_fraction: float  # 0-1, fraction of remaining to execute
    price_offset: float  # Offset from mid price (negative = aggressive)
    time_in_force: int  # Seconds
    venue: str  # Target venue
    
    @classmethod
    def from_discrete(cls, action_idx: int, num_actions: int = 64) -> 'ExecutionAction':
        """Convert discrete action index to ExecutionAction"""
        # Decode action
        # Action space: 4 order types × 4 sizes × 4 price offsets = 64 actions
        
        order_type_idx = action_idx // 16
        size_idx = (action_idx % 16) // 4
        price_idx = action_idx % 4
        
        order_types = [OrderType.MARKET, OrderType.LIMIT, OrderType.LIMIT_IOC, OrderType.ICEBERG]
        sizes = [0.25, 0.50, 0.75, 1.0]
        price_offsets = [0.0, -0.0001, -0.0002, 0.0001]  # Negative = aggressive
        
        return cls(
            order_type=order_types[order_type_idx],
            size_fraction=sizes[size_idx],
            price_offset=price_offsets[price_idx],
            time_in_force=30,
            venue='primary',
        )
    
    def to_discrete(self) -> int:
        """Convert to discrete action index"""
        order_type_map = {
            OrderType.MARKET: 0,
            OrderType.LIMIT: 1,
            OrderType.LIMIT_IOC: 2,
            OrderType.ICEBERG: 3,
        }
        size_map = {0.25: 0, 0.50: 1, 0.75: 2, 1.0: 3}
        price_map = {0.0: 0, -0.0001: 1, -0.0002: 2, 0.0001: 3}
        
        order_idx = order_type_map.get(self.order_type, 0)
        size_idx = min(range(4), key=lambda i: abs([0.25, 0.50, 0.75, 1.0][i] - self.size_fraction))
        price_idx = min(range(4), key=lambda i: abs([0.0, -0.0001, -0.0002, 0.0001][i] - self.price_offset))
        
        return order_idx * 16 + size_idx * 4 + price_idx


@dataclass
class ExecutionResult:
    """Result of an execution action"""
    filled_quantity: float
    fill_price: float
    slippage: float  # vs arrival price
    market_impact: float
    execution_time: float  # seconds
    
    # Quality metrics
    price_quality: float  # 0-1, how good was the price
    speed_quality: float  # 0-1, how fast
    impact_quality: float  # 0-1, how low was impact


class RewardCalculator:
    """
    Multi-objective reward function for execution
    
    Reward = (Price Quality × 0.4) + (Slippage Min × 0.3) + (Speed × 0.2) - (Impact × 0.1)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Reward weights
        self.price_weight = self.config.get('price_weight', 0.4)
        self.slippage_weight = self.config.get('slippage_weight', 0.3)
        self.speed_weight = self.config.get('speed_weight', 0.2)
        self.impact_weight = self.config.get('impact_weight', 0.1)
        
        # Benchmarks
        self.target_slippage = self.config.get('target_slippage', 0.0005)  # 5 bps
        self.target_time = self.config.get('target_time', 60)  # 60 seconds
    
    def calculate(self, state: ExecutionState, action: ExecutionAction,
                 result: ExecutionResult, next_state: ExecutionState) -> float:
        """Calculate reward for state-action-result transition"""
        
        # Price quality: How close to VWAP
        if state.vwap > 0:
            price_deviation = abs(result.fill_price - state.vwap) / state.vwap
            price_quality = max(0, 1 - price_deviation * 100)
        else:
            price_quality = 0.5
        
        # Slippage quality: How low was slippage
        slippage_quality = max(0, 1 - abs(result.slippage) / self.target_slippage)
        
        # Speed quality: How fast relative to target
        speed_quality = max(0, 1 - result.execution_time / self.target_time)
        
        # Impact quality: How low was market impact
        impact_quality = max(0, 1 - abs(result.market_impact) / 0.001)
        
        # Completion bonus
        completion_bonus = 0
        if next_state.remaining_quantity <= 0:
            completion_bonus = 0.5
        
        # Calculate total reward
        reward = (
            self.price_weight * price_quality +
            self.slippage_weight * slippage_quality +
            self.speed_weight * speed_quality -
            self.impact_weight * (1 - impact_quality) +
            completion_bonus
        )
        
        return reward


if TORCH_AVAILABLE:
    
    class ExecutionPolicyNetwork(nn.Module):
        """
        Policy network for execution decisions
        
        Uses actor-critic architecture
        """
        
        def __init__(self, state_dim: int = 15, action_dim: int = 64, hidden_dim: int = 128):
            super().__init__()
            
            # Shared feature extractor
            self.feature_extractor = nn.Sequential(
                nn.Linear(state_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
            )
            
            # Actor head (policy)
            self.actor = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, action_dim),
            )
            
            # Critic head (value)
            self.critic = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 1),
            )
        
        def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
            """
            Forward pass
            
            Returns:
                Tuple of (action_logits, state_value)
            """
            features = self.feature_extractor(state)
            action_logits = self.actor(features)
            state_value = self.critic(features)
            
            return action_logits, state_value
        
        def get_action(self, state: torch.Tensor, deterministic: bool = False) -> Tuple[int, torch.Tensor]:
            """Get action from policy"""
            action_logits, _ = self.forward(state)
            action_probs = F.softmax(action_logits, dim=-1)
            
            if deterministic:
                action = torch.argmax(action_probs, dim=-1)
            else:
                action = torch.multinomial(action_probs, 1).squeeze(-1)
            
            log_prob = F.log_softmax(action_logits, dim=-1)
            action_log_prob = log_prob.gather(-1, action.unsqueeze(-1)).squeeze(-1)
            
            return action.item(), action_log_prob
    
    
    class MAMLExecutionAgent(nn.Module):
        """
        MAML-based Meta-Learning Execution Agent
        
        Learns to quickly adapt to new market conditions
        """
        
        def __init__(self, config: Dict[str, Any] = None):
            super().__init__()
            self.config = config or {}
            
            # Network dimensions
            self.state_dim = self.config.get('state_dim', 15)
            self.action_dim = self.config.get('action_dim', 64)
            self.hidden_dim = self.config.get('hidden_dim', 128)
            
            # Policy network
            self.policy = ExecutionPolicyNetwork(
                self.state_dim, self.action_dim, self.hidden_dim
            )
            
            # MAML parameters
            self.inner_lr = self.config.get('inner_lr', 0.01)
            self.outer_lr = self.config.get('outer_lr', 0.001)
            self.num_inner_steps = self.config.get('num_inner_steps', 5)
            
            # Optimizer
            self.optimizer = optim.Adam(self.policy.parameters(), lr=self.outer_lr)
        
        def adapt(self, support_data: List[Tuple]) -> nn.Module:
            """
            Adapt policy to new task using support data
            
            Args:
                support_data: List of (state, action, reward, next_state) tuples
                
            Returns:
                Adapted policy network
            """
            # Clone policy for adaptation
            adapted_policy = ExecutionPolicyNetwork(
                self.state_dim, self.action_dim, self.hidden_dim
            )
            adapted_policy.load_state_dict(self.policy.state_dict())
            
            # Inner loop optimization
            inner_optimizer = optim.SGD(adapted_policy.parameters(), lr=self.inner_lr)
            
            for _ in range(self.num_inner_steps):
                total_loss = 0
                
                for state, action, reward, next_state in support_data:
                    state_tensor = torch.FloatTensor(state).unsqueeze(0)
                    
                    action_logits, value = adapted_policy(state_tensor)
                    action_probs = F.softmax(action_logits, dim=-1)
                    
                    # Policy gradient loss
                    log_prob = torch.log(action_probs[0, action] + 1e-8)
                    advantage = reward - value.item()
                    policy_loss = -log_prob * advantage
                    
                    # Value loss
                    value_loss = F.mse_loss(value, torch.tensor([[reward]]))
                    
                    total_loss += policy_loss + 0.5 * value_loss
                
                if len(support_data) > 0:
                    total_loss /= len(support_data)
                    
                    inner_optimizer.zero_grad()
                    total_loss.backward()
                    inner_optimizer.step()
            
            return adapted_policy
        
        def get_action(self, state: ExecutionState, adapted_policy: nn.Module = None,
                      deterministic: bool = False) -> ExecutionAction:
            """Get execution action for state"""
            policy = adapted_policy if adapted_policy else self.policy
            
            state_tensor = torch.FloatTensor(state.to_tensor()).unsqueeze(0)
            action_idx, _ = policy.get_action(state_tensor, deterministic)
            
            return ExecutionAction.from_discrete(action_idx)


class ExecutionSimulator:
    """
    Simulates order execution for training
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Market parameters
        self.base_spread = self.config.get('base_spread', 0.0001)
        self.base_depth = self.config.get('base_depth', 1000)
        self.volatility = self.config.get('volatility', 0.02)
        
        # Impact model parameters
        self.permanent_impact = self.config.get('permanent_impact', 0.1)
        self.temporary_impact = self.config.get('temporary_impact', 0.5)
    
    def simulate_execution(self, state: ExecutionState, action: ExecutionAction) -> ExecutionResult:
        """Simulate execution of action"""
        # Calculate execution quantity
        exec_quantity = state.remaining_quantity * action.size_fraction
        
        # Simulate fill based on order type
        if action.order_type == OrderType.MARKET:
            # Market order: immediate fill with slippage
            fill_rate = 1.0
            slippage = self._calculate_slippage(exec_quantity, state)
        elif action.order_type == OrderType.LIMIT:
            # Limit order: probabilistic fill
            fill_rate = self._calculate_fill_probability(action.price_offset, state)
            slippage = action.price_offset
        elif action.order_type == OrderType.LIMIT_IOC:
            # IOC: partial fill possible
            fill_rate = self._calculate_fill_probability(action.price_offset, state) * 0.8
            slippage = action.price_offset * 0.5
        else:
            fill_rate = 0.9
            slippage = self._calculate_slippage(exec_quantity, state) * 0.7
        
        filled_quantity = exec_quantity * fill_rate
        
        # Calculate fill price
        mid_price = (state.bid_price + state.ask_price) / 2
        fill_price = mid_price * (1 + slippage)
        
        # Calculate market impact
        market_impact = self._calculate_impact(filled_quantity, state)
        
        # Execution time
        if action.order_type == OrderType.MARKET:
            exec_time = 0.1
        else:
            exec_time = random.uniform(1, action.time_in_force)
        
        # Quality metrics
        price_quality = max(0, 1 - abs(slippage) * 1000)
        speed_quality = max(0, 1 - exec_time / 60)
        impact_quality = max(0, 1 - abs(market_impact) * 1000)
        
        return ExecutionResult(
            filled_quantity=filled_quantity,
            fill_price=fill_price,
            slippage=slippage,
            market_impact=market_impact,
            execution_time=exec_time,
            price_quality=price_quality,
            speed_quality=speed_quality,
            impact_quality=impact_quality,
        )
    
    def _calculate_slippage(self, quantity: float, state: ExecutionState) -> float:
        """Calculate expected slippage"""
        # Linear impact model
        depth = (state.bid_depth + state.ask_depth) / 2
        if depth == 0:
            depth = self.base_depth
        
        impact = (quantity / depth) * self.temporary_impact * state.spread
        
        # Add volatility component
        vol_impact = state.price_volatility * random.gauss(0, 0.5)
        
        return impact + vol_impact
    
    def _calculate_fill_probability(self, price_offset: float, state: ExecutionState) -> float:
        """Calculate probability of limit order fill"""
        # More aggressive (negative offset) = higher fill probability
        base_prob = 0.5
        
        if price_offset < 0:
            # Aggressive: higher fill prob
            prob = base_prob + abs(price_offset) * 1000
        else:
            # Passive: lower fill prob
            prob = base_prob - price_offset * 1000
        
        # Adjust for order imbalance
        prob += state.order_imbalance * 0.1
        
        return np.clip(prob, 0.1, 0.95)
    
    def _calculate_impact(self, quantity: float, state: ExecutionState) -> float:
        """Calculate market impact"""
        depth = (state.bid_depth + state.ask_depth) / 2
        if depth == 0:
            depth = self.base_depth
        
        # Square root impact model
        impact = self.permanent_impact * np.sqrt(quantity / depth) * state.price_volatility
        
        return impact


class AdaptiveExecutionAgent:
    """
    High-level adaptive execution agent
    
    Combines MAML with execution simulation for optimal trade execution
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        if TORCH_AVAILABLE:
            self.maml_agent = MAMLExecutionAgent(config)
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.maml_agent.to(self.device)
        else:
            self.maml_agent = None
        
        self.simulator = ExecutionSimulator(config)
        self.reward_calculator = RewardCalculator(config)
        
        # Experience buffer for adaptation
        self.experience_buffer: deque = deque(maxlen=1000)
        
        # Current adapted policy
        self.adapted_policy = None
        
        # Execution history
        self.execution_history: deque = deque(maxlen=1000)
        
        # Performance tracking
        self.total_slippage = 0.0
        self.total_impact = 0.0
        self.num_executions = 0
    
    def execute(self, state: ExecutionState, deterministic: bool = True) -> Tuple[ExecutionAction, ExecutionResult]:
        """
        Execute optimal action for current state
        
        Args:
            state: Current execution state
            deterministic: Whether to use deterministic policy
            
        Returns:
            Tuple of (action, result)
        """
        # Get action
        if TORCH_AVAILABLE and self.maml_agent:
            action = self.maml_agent.get_action(state, self.adapted_policy, deterministic)
        else:
            action = self._heuristic_action(state)
        
        # Simulate execution
        result = self.simulator.simulate_execution(state, action)
        
        # Update tracking
        self.total_slippage += abs(result.slippage)
        self.total_impact += abs(result.market_impact)
        self.num_executions += 1
        
        # Store experience
        self.execution_history.append({
            'timestamp': datetime.now(),
            'state': state,
            'action': action,
            'result': result,
        })
        
        return action, result
    
    def _heuristic_action(self, state: ExecutionState) -> ExecutionAction:
        """Fallback heuristic-based action selection"""
        # Determine urgency based on time remaining
        if state.time_remaining < 0.1:
            # Very little time: aggressive market order
            return ExecutionAction(
                order_type=OrderType.MARKET,
                size_fraction=1.0,
                price_offset=0,
                time_in_force=5,
                venue='primary',
            )
        elif state.time_remaining < 0.3:
            # Some urgency: aggressive limit
            return ExecutionAction(
                order_type=OrderType.LIMIT_IOC,
                size_fraction=0.75,
                price_offset=-0.0001,
                time_in_force=30,
                venue='primary',
            )
        else:
            # Patient: passive limit
            size = 0.25 if state.remaining_quantity > state.target_position * 0.5 else 0.5
            return ExecutionAction(
                order_type=OrderType.LIMIT,
                size_fraction=size,
                price_offset=0.0001,
                time_in_force=60,
                venue='primary',
            )
    
    def adapt_to_conditions(self, recent_experiences: List[Tuple] = None):
        """
        Adapt policy to current market conditions
        
        Args:
            recent_experiences: Recent (state, action, reward, next_state) tuples
        """
        if not TORCH_AVAILABLE or self.maml_agent is None:
            return
        
        if recent_experiences is None:
            # Use experience buffer
            recent_experiences = list(self.experience_buffer)[-50:]
        
        if len(recent_experiences) < 10:
            return
        
        # Convert to training format
        training_data = []
        for exp in recent_experiences:
            if isinstance(exp, dict):
                state = exp['state']
                action = exp['action']
                result = exp['result']
                # Calculate reward
                next_state = state  # Simplified
                reward = self.reward_calculator.calculate(state, action, result, next_state)
                training_data.append((
                    state.to_tensor(),
                    action.to_discrete(),
                    reward,
                    next_state.to_tensor(),
                ))
            else:
                training_data.append(exp)
        
        # Adapt policy
        self.adapted_policy = self.maml_agent.adapt(training_data)
    
    def get_statistics(self) -> Dict[str, float]:
        """Get execution statistics"""
        if self.num_executions == 0:
            return {}
        
        return {
            'avg_slippage_bps': self.total_slippage / self.num_executions * 10000,
            'avg_impact_bps': self.total_impact / self.num_executions * 10000,
            'total_executions': self.num_executions,
        }


class MultiConditionExecutor:
    """
    Manages multiple specialized execution agents for different conditions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Specialized agents for different conditions
        self.agents: Dict[str, AdaptiveExecutionAgent] = {
            'low_vol_liquid': AdaptiveExecutionAgent({
                'temporary_impact': 0.3,
                'permanent_impact': 0.05,
            }),
            'low_vol_illiquid': AdaptiveExecutionAgent({
                'temporary_impact': 0.7,
                'permanent_impact': 0.15,
            }),
            'high_vol_liquid': AdaptiveExecutionAgent({
                'temporary_impact': 0.5,
                'permanent_impact': 0.1,
            }),
            'high_vol_illiquid': AdaptiveExecutionAgent({
                'temporary_impact': 1.0,
                'permanent_impact': 0.2,
            }),
        }
        
        # Current condition
        self.current_condition = 'low_vol_liquid'
    
    def select_agent(self, state: ExecutionState) -> AdaptiveExecutionAgent:
        """Select appropriate agent based on state"""
        # Determine condition
        is_high_vol = state.volatility_regime == 'high'
        is_illiquid = state.liquidity_regime == 'thin'
        
        if is_high_vol and is_illiquid:
            condition = 'high_vol_illiquid'
        elif is_high_vol:
            condition = 'high_vol_liquid'
        elif is_illiquid:
            condition = 'low_vol_illiquid'
        else:
            condition = 'low_vol_liquid'
        
        self.current_condition = condition
        return self.agents[condition]
    
    def execute(self, state: ExecutionState) -> Tuple[ExecutionAction, ExecutionResult]:
        """Execute using appropriate agent"""
        agent = self.select_agent(state)
        return agent.execute(state)
    
    def adapt_all(self):
        """Adapt all agents to recent conditions"""
        for agent in self.agents.values():
            agent.adapt_to_conditions()

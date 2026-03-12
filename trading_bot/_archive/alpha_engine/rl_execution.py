"""
Reinforcement Learning Execution Module
========================================

Meta-RL (MAML-based) for adaptive trade execution optimization.
Learns optimal execution policies that adapt to changing market conditions.

Features:
- State space: position, time, LOB features, volatility, P&L
- Action space: order type, size, price offset, venue selection
- Reward: execution quality, slippage minimization, speed bonus
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
import json

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    from torch.distributions import Categorical
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. RL features will be limited.")


class OrderType(Enum):
    """Order types for execution"""
    MARKET = "market"
    LIMIT = "limit"
    LIMIT_IOC = "limit_ioc"  # Immediate or cancel
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"


class ExecutionVenue(Enum):
    """Trading venues"""
    PRIMARY = "primary"
    DARK_POOL = "dark_pool"
    ECN = "ecn"
    INTERNALIZE = "internalize"


@dataclass
class ExecutionState:
    """State representation for RL agent"""
    # Position state
    target_quantity: float
    filled_quantity: float
    remaining_quantity: float
    
    # Time state
    time_remaining: float  # Fraction of allowed time remaining
    urgency: float  # 0-1 urgency level
    
    # Market state
    mid_price: float
    spread: float
    bid_depth: float
    ask_depth: float
    imbalance: float
    volatility: float
    
    # Recent price trajectory
    price_momentum: float
    price_acceleration: float
    
    # Execution state
    avg_fill_price: float
    current_pnl: float
    slippage_so_far: float
    
    # Market impact estimate
    estimated_impact: float
    
    def to_tensor(self) -> np.ndarray:
        """Convert state to numpy array for model input"""
        return np.array([
            self.remaining_quantity / (self.target_quantity + 1e-10),
            self.time_remaining,
            self.urgency,
            self.spread,
            self.bid_depth,
            self.ask_depth,
            self.imbalance,
            self.volatility,
            self.price_momentum,
            self.price_acceleration,
            self.current_pnl,
            self.slippage_so_far,
            self.estimated_impact,
        ], dtype=np.float32)
    
    @classmethod
    def state_dim(cls) -> int:
        return 13


@dataclass
class ExecutionAction:
    """Action taken by RL agent"""
    order_type: OrderType
    size_fraction: float  # 0-1 fraction of remaining quantity
    price_offset: float  # Offset from mid price (negative = aggressive)
    venue: ExecutionVenue
    time_in_force: int  # Seconds
    
    def to_index(self, action_space_size: int = 64) -> int:
        """Convert action to discrete index"""
        # Discretize action space
        type_idx = list(OrderType).index(self.order_type)
        size_idx = int(self.size_fraction * 3)  # 0, 1, 2, 3 for 0%, 33%, 66%, 100%
        offset_idx = int((self.price_offset + 0.001) / 0.0005)  # Discretize offset
        venue_idx = list(ExecutionVenue).index(self.venue)
        
        # Combine into single index
        return (type_idx * 16 + size_idx * 4 + min(offset_idx, 3)) % action_space_size
    
    @classmethod
    def from_index(cls, index: int, remaining_qty: float) -> 'ExecutionAction':
        """Create action from discrete index"""
        # Decode index
        type_idx = (index // 16) % len(OrderType)
        size_idx = (index // 4) % 4
        offset_idx = index % 4
        venue_idx = (index // 32) % len(ExecutionVenue)
        
        return cls(
            order_type=list(OrderType)[type_idx],
            size_fraction=[0.0, 0.25, 0.5, 1.0][size_idx],
            price_offset=[-0.001, -0.0005, 0, 0.0005][offset_idx],
            venue=list(ExecutionVenue)[venue_idx],
            time_in_force=30,
        )


@dataclass
class ExecutionResult:
    """Result of execution action"""
    filled_quantity: float
    fill_price: float
    slippage: float  # vs arrival price
    market_impact: float
    execution_time: float  # seconds
    venue_used: ExecutionVenue
    fees: float


class RewardCalculator:
    """
    Calculate reward for execution actions
    
    Reward = (Execution_Price_Quality × 0.4) 
             + (Slippage_Minimization × 0.3)
             + (Speed_Bonus × 0.2)
             - (Market_Impact_Cost × 0.1)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.weights = {
            'price_quality': self.config.get('price_quality_weight', 0.4),
            'slippage': self.config.get('slippage_weight', 0.3),
            'speed': self.config.get('speed_weight', 0.2),
            'impact': self.config.get('impact_weight', 0.1),
        }
        
    def calculate(self, state: ExecutionState, action: ExecutionAction,
                  result: ExecutionResult, benchmark_price: float) -> float:
        """Calculate reward for execution"""
        # Price quality: how close to benchmark (VWAP, arrival, etc.)
        price_diff = abs(result.fill_price - benchmark_price) / benchmark_price
        price_quality = max(0, 1 - price_diff * 100)  # Penalize deviation
        
        # Slippage minimization
        slippage_penalty = min(1, abs(result.slippage) * 100)
        slippage_score = 1 - slippage_penalty
        
        # Speed bonus: reward for completing execution quickly
        time_used = 1 - state.time_remaining
        speed_score = 1 - time_used if result.filled_quantity > 0 else 0
        
        # Market impact cost
        impact_penalty = min(1, result.market_impact * 50)
        
        # Combine
        reward = (
            self.weights['price_quality'] * price_quality +
            self.weights['slippage'] * slippage_score +
            self.weights['speed'] * speed_score -
            self.weights['impact'] * impact_penalty
        )
        
        # Bonus for completing the order
        if state.remaining_quantity <= 0:
            reward += 0.5
        
        return reward


if TORCH_AVAILABLE:
    class ExecutionPolicyNetwork(nn.Module):
        """
        Policy network for execution decisions
        """
        
        def __init__(self, state_dim: int = 13, action_dim: int = 64, 
                     hidden_dim: int = 128):
            super().__init__()
            
            self.fc1 = nn.Linear(state_dim, hidden_dim)
            self.fc2 = nn.Linear(hidden_dim, hidden_dim)
            self.fc3 = nn.Linear(hidden_dim, hidden_dim // 2)
            
            # Policy head
            self.policy_head = nn.Linear(hidden_dim // 2, action_dim)
            
            # Value head
            self.value_head = nn.Linear(hidden_dim // 2, 1)
            
            self.dropout = nn.Dropout(0.1)
            
        def forward(self, state):
            x = F.relu(self.fc1(state))
            x = self.dropout(x)
            x = F.relu(self.fc2(x))
            x = self.dropout(x)
            x = F.relu(self.fc3(x))
            
            policy = F.softmax(self.policy_head(x), dim=-1)
            value = self.value_head(x)
            
            return policy, value
        
        def get_action(self, state, deterministic: bool = False):
            """Sample action from policy"""
            policy, value = self.forward(state)
            
            if deterministic:
                action_idx = torch.argmax(policy, dim=-1)
            else:
                dist = Categorical(policy)
                action_idx = dist.sample()
            
            return action_idx, policy, value
    
    
    class MAMLExecutionAgent(nn.Module):
        """
        MAML (Model-Agnostic Meta-Learning) based execution agent
        
        Learns to quickly adapt to new market conditions with few gradient steps.
        """
        
        def __init__(self, state_dim: int = 13, action_dim: int = 64,
                     hidden_dim: int = 128, meta_lr: float = 0.001,
                     inner_lr: float = 0.01):
            super().__init__()
            
            self.policy = ExecutionPolicyNetwork(state_dim, action_dim, hidden_dim)
            self.meta_optimizer = optim.Adam(self.policy.parameters(), lr=meta_lr)
            self.inner_lr = inner_lr
            
        def inner_update(self, support_states, support_actions, support_rewards):
            """
            Inner loop update on support set (few-shot adaptation)
            """
            # Clone policy for inner update
            fast_weights = {name: param.clone() for name, param in self.policy.named_parameters()}
            
            # Compute loss on support set
            policy, value = self.policy(support_states)
            
            # Policy gradient loss
            log_probs = torch.log(policy.gather(1, support_actions.unsqueeze(1)))
            advantages = support_rewards - value.detach()
            policy_loss = -(log_probs * advantages).mean()
            
            # Value loss
            value_loss = F.mse_loss(value.squeeze(), support_rewards)
            
            loss = policy_loss + 0.5 * value_loss
            
            # Compute gradients
            grads = torch.autograd.grad(loss, self.policy.parameters(), create_graph=True)
            
            # Update fast weights
            for (name, param), grad in zip(self.policy.named_parameters(), grads):
                fast_weights[name] = param - self.inner_lr * grad
            
            return fast_weights
        
        def meta_update(self, tasks):
            """
            Outer loop meta-update across tasks
            
            Args:
                tasks: List of (support_set, query_set) tuples
            """
            meta_loss = 0
            
            for support_set, query_set in tasks:
                support_states, support_actions, support_rewards = support_set
                query_states, query_actions, query_rewards = query_set
                
                # Inner update
                fast_weights = self.inner_update(support_states, support_actions, support_rewards)
                
                # Evaluate on query set with fast weights
                # (simplified - in practice would use functional forward)
                policy, value = self.policy(query_states)
                
                log_probs = torch.log(policy.gather(1, query_actions.unsqueeze(1)))
                advantages = query_rewards - value.detach()
                policy_loss = -(log_probs * advantages).mean()
                value_loss = F.mse_loss(value.squeeze(), query_rewards)
                
                meta_loss += policy_loss + 0.5 * value_loss
            
            # Meta update
            self.meta_optimizer.zero_grad()
            meta_loss.backward()
            self.meta_optimizer.step()
            
            return meta_loss.item() / len(tasks)


class RLExecutionAgent:
    """
    High-level RL execution agent interface
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.state_dim = ExecutionState.state_dim()
        self.action_dim = self.config.get('action_dim', 64)
        self.device = self.config.get('device', 'cuda' if TORCH_AVAILABLE and torch.cuda.is_available() else 'cpu')
        
        if TORCH_AVAILABLE:
            self.agent = MAMLExecutionAgent(
                state_dim=self.state_dim,
                action_dim=self.action_dim,
                hidden_dim=self.config.get('hidden_dim', 128),
            ).to(self.device)
        else:
            self.agent = None
        
        self.reward_calculator = RewardCalculator(self.config.get('reward_config', {}))
        
        # Experience buffer
        self.experience_buffer: deque = deque(maxlen=10000)
        
        # Execution history
        self.execution_history: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.total_executions = 0
        self.total_slippage = 0
        self.avg_execution_quality = 0
        
    def get_action(self, state: ExecutionState, deterministic: bool = False) -> ExecutionAction:
        """
        Get execution action for current state
        
        Args:
            state: Current execution state
            deterministic: Whether to use deterministic policy
            
        Returns:
            ExecutionAction to take
        """
        if not TORCH_AVAILABLE or self.agent is None:
            return self._heuristic_action(state)
        
        state_tensor = torch.tensor(state.to_tensor(), dtype=torch.float32).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action_idx, policy, value = self.agent.policy.get_action(state_tensor, deterministic)
        
        action_idx = action_idx.item()
        action = ExecutionAction.from_index(action_idx, state.remaining_quantity)
        
        return action
    
    def _heuristic_action(self, state: ExecutionState) -> ExecutionAction:
        """Fallback heuristic execution strategy"""
        # Simple TWAP-like heuristic
        if state.time_remaining < 0.1:
            # Urgent - use market order
            return ExecutionAction(
                order_type=OrderType.MARKET,
                size_fraction=1.0,
                price_offset=0,
                venue=ExecutionVenue.PRIMARY,
                time_in_force=10,
            )
        elif state.imbalance > 0.3 and state.remaining_quantity > 0:
            # Favorable imbalance - be aggressive
            return ExecutionAction(
                order_type=OrderType.LIMIT,
                size_fraction=0.5,
                price_offset=-0.0005,  # Aggressive
                venue=ExecutionVenue.PRIMARY,
                time_in_force=30,
            )
        elif state.volatility > 0.02:
            # High volatility - use smaller orders
            return ExecutionAction(
                order_type=OrderType.LIMIT,
                size_fraction=0.25,
                price_offset=0,
                venue=ExecutionVenue.PRIMARY,
                time_in_force=60,
            )
        else:
            # Normal conditions - standard limit
            return ExecutionAction(
                order_type=OrderType.LIMIT,
                size_fraction=0.33,
                price_offset=0.0002,  # Passive
                venue=ExecutionVenue.PRIMARY,
                time_in_force=60,
            )
    
    def update(self, state: ExecutionState, action: ExecutionAction,
               result: ExecutionResult, next_state: ExecutionState,
               benchmark_price: float):
        """
        Update agent with execution experience
        """
        reward = self.reward_calculator.calculate(state, action, result, benchmark_price)
        
        experience = {
            'state': state.to_tensor(),
            'action': action.to_index(self.action_dim),
            'reward': reward,
            'next_state': next_state.to_tensor(),
            'done': next_state.remaining_quantity <= 0,
        }
        
        self.experience_buffer.append(experience)
        
        # Update statistics
        self.total_executions += 1
        self.total_slippage += result.slippage
        self.avg_execution_quality = (self.avg_execution_quality * (self.total_executions - 1) + 
                                      reward) / self.total_executions
        
        # Log execution
        self.execution_history.append({
            'timestamp': datetime.now().isoformat(),
            'state': state.__dict__,
            'action': action.__dict__,
            'result': result.__dict__,
            'reward': reward,
        })
    
    def train(self, batch_size: int = 64, num_updates: int = 10):
        """Train agent on experience buffer"""
        if not TORCH_AVAILABLE or self.agent is None:
            return
        
        if len(self.experience_buffer) < batch_size:
            return
        
        for _ in range(num_updates):
            # Sample batch
            batch = random.sample(list(self.experience_buffer), batch_size)
            
            states = torch.tensor([e['state'] for e in batch], dtype=torch.float32).to(self.device)
            actions = torch.tensor([e['action'] for e in batch], dtype=torch.long).to(self.device)
            rewards = torch.tensor([e['reward'] for e in batch], dtype=torch.float32).to(self.device)
            
            # Update policy
            policy, value = self.agent.policy(states)
            
            log_probs = torch.log(policy.gather(1, actions.unsqueeze(1)) + 1e-10)
            advantages = rewards - value.squeeze().detach()
            
            policy_loss = -(log_probs.squeeze() * advantages).mean()
            value_loss = F.mse_loss(value.squeeze(), rewards)
            
            loss = policy_loss + 0.5 * value_loss
            
            self.agent.meta_optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.agent.parameters(), 1.0)
            self.agent.meta_optimizer.step()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            'total_executions': self.total_executions,
            'avg_slippage': self.total_slippage / max(1, self.total_executions),
            'avg_execution_quality': self.avg_execution_quality,
            'experience_buffer_size': len(self.experience_buffer),
        }


class MetaRLOptimizer:
    """
    Meta-RL optimizer for execution across different market conditions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.agents: Dict[str, RLExecutionAgent] = {}
        
        # Market condition categories
        self.conditions = ['low_vol', 'high_vol', 'trending', 'ranging', 'news']
        
        # Initialize specialized agents
        for condition in self.conditions:
            self.agents[condition] = RLExecutionAgent(self.config)
        
        # Meta-learner for condition detection
        self.condition_history: deque = deque(maxlen=100)
        
    def detect_condition(self, state: ExecutionState) -> str:
        """Detect current market condition"""
        if state.volatility > 0.03:
            return 'high_vol'
        elif state.volatility < 0.01:
            return 'low_vol'
        elif abs(state.price_momentum) > 0.005:
            return 'trending'
        else:
            return 'ranging'
    
    def get_action(self, state: ExecutionState) -> Tuple[ExecutionAction, str]:
        """Get action from appropriate specialized agent"""
        condition = self.detect_condition(state)
        self.condition_history.append(condition)
        
        agent = self.agents[condition]
        action = agent.get_action(state)
        
        return action, condition
    
    def update(self, state: ExecutionState, action: ExecutionAction,
               result: ExecutionResult, next_state: ExecutionState,
               benchmark_price: float, condition: str):
        """Update the appropriate specialized agent"""
        if condition in self.agents:
            self.agents[condition].update(state, action, result, next_state, benchmark_price)
    
    def train_all(self, batch_size: int = 64):
        """Train all specialized agents"""
        for agent in self.agents.values():
            agent.train(batch_size)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for all agents"""
        stats = {}
        for condition, agent in self.agents.items():
            stats[condition] = agent.get_statistics()
        
        # Condition distribution
        if self.condition_history:
            condition_counts = {}
            for c in self.conditions:
                condition_counts[c] = sum(1 for h in self.condition_history if h == c)
            stats['condition_distribution'] = condition_counts
        
        return stats


class ExecutionSimulator:
    """
    Simulates order execution for training and backtesting
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.fill_probability = self.config.get('fill_probability', 0.8)
        self.slippage_model = self.config.get('slippage_model', 'linear')
        self.impact_coefficient = self.config.get('impact_coefficient', 0.1)
        
    def simulate_execution(self, action: ExecutionAction, state: ExecutionState,
                          market_data: Dict[str, float]) -> ExecutionResult:
        """
        Simulate execution of an action
        
        Args:
            action: Execution action to simulate
            state: Current execution state
            market_data: Current market data (mid, spread, volume, etc.)
            
        Returns:
            ExecutionResult
        """
        mid_price = market_data.get('mid_price', state.mid_price)
        spread = market_data.get('spread', state.spread)
        volume = market_data.get('volume', 1000)
        
        # Calculate order size
        order_size = state.remaining_quantity * action.size_fraction
        
        # Determine fill probability based on order type and aggressiveness
        if action.order_type == OrderType.MARKET:
            fill_prob = 1.0
            price_offset = spread / 2  # Cross the spread
        elif action.order_type == OrderType.LIMIT:
            # More passive = lower fill probability
            aggressiveness = -action.price_offset / spread if spread > 0 else 0
            fill_prob = min(1.0, self.fill_probability + aggressiveness * 0.3)
            price_offset = action.price_offset
        else:
            fill_prob = self.fill_probability
            price_offset = action.price_offset
        
        # Simulate fill
        if random.random() < fill_prob:
            filled_quantity = order_size
        else:
            filled_quantity = order_size * random.uniform(0, 0.5)  # Partial fill
        
        # Calculate fill price with slippage
        if self.slippage_model == 'linear':
            # Linear impact model
            impact = self.impact_coefficient * (filled_quantity / volume)
        else:
            # Square root impact model
            impact = self.impact_coefficient * np.sqrt(filled_quantity / volume)
        
        # Direction of impact depends on buy/sell
        if state.remaining_quantity > 0:  # Buying
            fill_price = mid_price + price_offset + impact * mid_price
        else:  # Selling
            fill_price = mid_price + price_offset - impact * mid_price
        
        # Calculate slippage vs arrival price
        arrival_price = market_data.get('arrival_price', mid_price)
        slippage = (fill_price - arrival_price) / arrival_price
        
        # Simulate execution time
        if action.order_type == OrderType.MARKET:
            exec_time = random.uniform(0.01, 0.1)  # Fast
        else:
            exec_time = random.uniform(0.5, action.time_in_force)
        
        # Fees
        fees = filled_quantity * fill_price * 0.0001  # 1 bps
        
        return ExecutionResult(
            filled_quantity=filled_quantity,
            fill_price=fill_price,
            slippage=slippage,
            market_impact=impact,
            execution_time=exec_time,
            venue_used=action.venue,
            fees=fees,
        )


class ExecutionBenchmark:
    """
    Benchmark execution strategies (VWAP, TWAP, etc.)
    """
    
    @staticmethod
    def calculate_vwap(prices: List[float], volumes: List[float]) -> float:
        """Calculate VWAP benchmark"""
        if not prices or not volumes:
            return 0
        total_value = sum(p * v for p, v in zip(prices, volumes))
        total_volume = sum(volumes)
        return total_value / total_volume if total_volume > 0 else prices[-1]
    
    @staticmethod
    def calculate_twap(prices: List[float]) -> float:
        """Calculate TWAP benchmark"""
        return np.mean(prices) if prices else 0
    
    @staticmethod
    def calculate_arrival_price(prices: List[float]) -> float:
        """Get arrival price (first price)"""
        return prices[0] if prices else 0
    
    @staticmethod
    def calculate_implementation_shortfall(
        arrival_price: float,
        avg_fill_price: float,
        quantity: float,
        direction: str = 'buy'
    ) -> float:
        """
        Calculate implementation shortfall
        
        IS = (Avg Fill Price - Arrival Price) / Arrival Price
        Positive IS = cost (for buys), negative = savings
        """
        if arrival_price == 0:
            return 0
        
        shortfall = (avg_fill_price - arrival_price) / arrival_price
        
        if direction == 'sell':
            shortfall = -shortfall
        
        return shortfall

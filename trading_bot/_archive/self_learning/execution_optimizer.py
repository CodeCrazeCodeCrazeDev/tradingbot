"""
Self-Optimizing Execution Engine with Reinforcement Learning

This module implements RL-based execution optimization, adaptive order routing,
and continuous improvement of execution quality for profit maximization.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import deque
import logging

logger = logging.getLogger(__name__)


class ExecutionAction(Enum):
    """Possible execution actions"""
    MARKET_ORDER = "market_order"
    LIMIT_ORDER = "limit_order"
    ICEBERG_ORDER = "iceberg_order"
    TWAP = "twap"
    VWAP = "vwap"
    ADAPTIVE = "adaptive"
    WAIT = "wait"
    SPLIT_ORDER = "split_order"


class ExecutionState(Enum):
    """Execution environment states"""
    LOW_VOLATILITY = "low_volatility"
    HIGH_VOLATILITY = "high_volatility"
    LOW_LIQUIDITY = "low_liquidity"
    HIGH_LIQUIDITY = "high_liquidity"
    TRENDING = "trending"
    RANGING = "ranging"
    NEWS_EVENT = "news_event"


@dataclass
class ExecutionExperience:
    """Experience tuple for RL learning"""
    state: Dict[str, float]
    action: ExecutionAction
    reward: float
    next_state: Dict[str, float]
    done: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionMetrics:
    """Metrics for execution quality"""
    slippage: float = 0.0
    fill_rate: float = 1.0
    execution_time: float = 0.0
    market_impact: float = 0.0
    opportunity_cost: float = 0.0
    total_cost: float = 0.0
    profit_improvement: float = 0.0
    
    def calculate_reward(self) -> float:
        """Calculate reward signal for RL"""
        # Negative reward for costs, positive for improvements
        reward = (
            -10.0 * abs(self.slippage) +
            5.0 * self.fill_rate +
            -2.0 * self.execution_time +
            -5.0 * abs(self.market_impact) +
            -3.0 * abs(self.opportunity_cost) +
            10.0 * self.profit_improvement
        )
        return reward


class QNetwork:
    """Q-Network for execution action value estimation"""
    
    def __init__(self, state_dim: int, action_dim: int, learning_rate: float = 0.001):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        
        # Simple Q-table for now (can be upgraded to neural network)
        self.q_table: Dict[str, np.ndarray] = {}
        self.visit_counts: Dict[str, np.ndarray] = {}
        
    def _state_to_key(self, state: Dict[str, float]) -> str:
        """Convert state dict to hashable key"""
        # Discretize continuous states
        discretized = []
        for key in sorted(state.keys()):
            value = state[key]
            bucket = int(value * 10) / 10  # Round to 1 decimal
            discretized.append(f"{key}:{bucket}")
        return "_".join(discretized)
    
    def get_q_values(self, state: Dict[str, float]) -> np.ndarray:
        """Get Q-values for all actions in given state"""
        key = self._state_to_key(state)
        if key not in self.q_table:
            self.q_table[key] = np.zeros(self.action_dim)
            self.visit_counts[key] = np.zeros(self.action_dim)
        return self.q_table[key]
    
    def update(self, state: Dict[str, float], action_idx: int, target: float):
        """Update Q-value for state-action pair"""
        key = self._state_to_key(state)
        if key not in self.q_table:
            self.q_table[key] = np.zeros(self.action_dim)
            self.visit_counts[key] = np.zeros(self.action_dim)
        
        # Incremental update with learning rate
        self.visit_counts[key][action_idx] += 1
        alpha = self.learning_rate / (1.0 + 0.01 * self.visit_counts[key][action_idx])
        self.q_table[key][action_idx] += alpha * (target - self.q_table[key][action_idx])
    
    def get_best_action(self, state: Dict[str, float]) -> int:
        """Get best action for given state"""
        q_values = self.get_q_values(state)
        return int(np.argmax(q_values))


class ReplayBuffer:
    """Experience replay buffer for RL"""
    
    def __init__(self, capacity: int = 10000):
        self.buffer: deque = deque(maxlen=capacity)
    
    def add(self, experience: ExecutionExperience):
        """Add experience to buffer"""
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> List[ExecutionExperience]:
        """Sample random batch of experiences"""
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in indices]
    
    def __len__(self) -> int:
        return len(self.buffer)


class ExecutionRL:
    """Reinforcement Learning for execution optimization"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.actions = list(ExecutionAction)
        self.q_network = QNetwork(
            state_dim=10,  # Number of state features
            action_dim=len(self.actions),
            learning_rate=self.config.get('learning_rate', 0.001)
        )
        self.replay_buffer = ReplayBuffer(capacity=10000)
        self.epsilon = self.config.get('epsilon', 0.1)  # Exploration rate
        self.gamma = self.config.get('gamma', 0.95)  # Discount factor
        self.training_step = 0
        
    def select_action(self, state: Dict[str, float], explore: bool = True) -> ExecutionAction:
        """Select action using epsilon-greedy policy"""
        if explore and np.random.random() < self.epsilon:
            # Explore: random action
            action_idx = np.random.randint(len(self.actions))
        else:
            # Exploit: best action
            action_idx = self.q_network.get_best_action(state)
        
        return self.actions[action_idx]
    
    def learn_from_experience(self, experience: ExecutionExperience):
        """Learn from single experience"""
        self.replay_buffer.add(experience)
        
        # Train on batch
        if len(self.replay_buffer) >= 32:
            self._train_on_batch(batch_size=32)
    
    def _train_on_batch(self, batch_size: int):
        """Train on batch of experiences"""
        batch = self.replay_buffer.sample(batch_size)
        
        for exp in batch:
            action_idx = self.actions.index(exp.action)
            
            if exp.done:
                target = exp.reward
            else:
                # Q-learning update: Q(s,a) = r + gamma * max_a' Q(s',a')
                next_q_values = self.q_network.get_q_values(exp.next_state)
                target = exp.reward + self.gamma * np.max(next_q_values)
            
            self.q_network.update(exp.state, action_idx, target)
        
        self.training_step += 1
        
        # Decay epsilon (exploration rate)
        if self.training_step % 100 == 0:
            self.epsilon = max(0.01, self.epsilon * 0.995)
    
    def get_action_values(self, state: Dict[str, float]) -> Dict[ExecutionAction, float]:
        """Get Q-values for all actions"""
        q_values = self.q_network.get_q_values(state)
        return {action: q_values[i] for i, action in enumerate(self.actions)}


class AdaptiveRouter:
    """Adaptive order routing based on market conditions"""
    
    def __init__(self):
        self.venue_performance: Dict[str, List[float]] = {}
        self.venue_latency: Dict[str, deque] = {}
        self.venue_fill_rates: Dict[str, deque] = {}
        
    def route_order(self, order: Dict[str, Any], available_venues: List[str]) -> str:
        """Route order to best venue"""
        if not available_venues:
            return "default"
        
        # Score each venue
        scores = {}
        for venue in available_venues:
            score = self._calculate_venue_score(venue)
            scores[venue] = score
        
        # Select best venue
        best_venue = max(scores.items(), key=lambda x: x[1])[0]
        return best_venue
    
    def _calculate_venue_score(self, venue: str) -> float:
        """Calculate venue quality score"""
        score = 0.5  # Default
        
        # Performance history
        if venue in self.venue_performance and self.venue_performance[venue]:
            score += 0.3 * np.mean(self.venue_performance[venue][-20:])
        
        # Latency (lower is better)
        if venue in self.venue_latency and self.venue_latency[venue]:
            avg_latency = np.mean(list(self.venue_latency[venue]))
            score += 0.2 * (1.0 / (1.0 + avg_latency))
        
        # Fill rate
        if venue in self.venue_fill_rates and self.venue_fill_rates[venue]:
            score += 0.3 * np.mean(list(self.venue_fill_rates[venue]))
        
        return score
    
    def update_venue_performance(self, venue: str, performance: float, 
                                 latency: float, fill_rate: float):
        """Update venue performance metrics"""
        if venue not in self.venue_performance:
            self.venue_performance[venue] = []
            self.venue_latency[venue] = deque(maxlen=100)
            self.venue_fill_rates[venue] = deque(maxlen=100)
        
        self.venue_performance[venue].append(performance)
        self.venue_latency[venue].append(latency)
        self.venue_fill_rates[venue].append(fill_rate)


class ExecutionOptimizer:
    """Main execution optimizer with RL and adaptive routing"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.rl_agent = ExecutionRL(config)
        self.router = AdaptiveRouter()
        self.execution_history: deque = deque(maxlen=1000)
        self.performance_metrics: Dict[str, List[float]] = {
            'slippage': [],
            'fill_rate': [],
            'execution_time': [],
            'profit_improvement': []
        }
        
    def _extract_state(self, market_data: pd.DataFrame, order: Dict[str, Any]) -> Dict[str, float]:
        """Extract state features from market data and order"""
        state = {}
        
        if len(market_data) > 0:
            close = market_data['close'].values
            volume = market_data['volume'].values if 'volume' in market_data.columns else np.ones(len(close))
            
            # Price features
            state['price'] = close[-1] if len(close) > 0 else 0
            state['volatility'] = np.std(np.diff(close) / close[:-1]) if len(close) > 1 else 0
            
            # Volume features
            state['volume'] = volume[-1] if len(volume) > 0 else 0
            state['volume_trend'] = (volume[-1] / np.mean(volume)) if len(volume) > 0 and np.mean(volume) > 0 else 1.0
            
            # Order features
            state['order_size'] = order.get('quantity', 0)
            state['urgency'] = order.get('urgency', 0.5)
            
            # Market condition
            if len(close) >= 20:
                returns = np.diff(close) / close[:-1]
                state['trend'] = np.mean(returns[-20:])
                state['momentum'] = np.mean(returns[-5:])
            else:
                state['trend'] = 0
                state['momentum'] = 0
            
            # Spread estimate
            state['spread'] = order.get('spread', 0.001)
            state['liquidity'] = order.get('liquidity', 0.5)
        
        return state
    
    async def optimize_execution(self, order: Dict[str, Any], 
                                market_data: pd.DataFrame) -> Dict[str, Any]:
        """Optimize execution of an order"""
        # Extract current state
        state = self._extract_state(market_data, order)
        
        # Select optimal action using RL
        action = self.rl_agent.select_action(state, explore=True)
        
        # Route to best venue
        available_venues = order.get('venues', ['default'])
        best_venue = self.router.route_order(order, available_venues)
        
        # Create execution plan
        execution_plan = {
            'action': action.value,
            'venue': best_venue,
            'order': order,
            'state': state,
            'timestamp': datetime.utcnow()
        }
        
        logger.info(f"Execution plan: {action.value} on {best_venue}")
        
        return execution_plan
    
    async def learn_from_execution(self, execution_plan: Dict[str, Any], 
                                   execution_result: Dict[str, Any]):
        """Learn from execution outcome"""
        # Calculate metrics
        metrics = ExecutionMetrics(
            slippage=execution_result.get('slippage', 0),
            fill_rate=execution_result.get('fill_rate', 1.0),
            execution_time=execution_result.get('execution_time', 0),
            market_impact=execution_result.get('market_impact', 0),
            opportunity_cost=execution_result.get('opportunity_cost', 0),
            profit_improvement=execution_result.get('profit_improvement', 0)
        )
        
        # Calculate reward
        reward = metrics.calculate_reward()
        
        # Create experience
        experience = ExecutionExperience(
            state=execution_plan['state'],
            action=ExecutionAction(execution_plan['action']),
            reward=reward,
            next_state=execution_result.get('next_state', execution_plan['state']),
            done=execution_result.get('done', True),
            metadata={
                'venue': execution_plan['venue'],
                'metrics': metrics.__dict__
            }
        )
        
        # Learn from experience
        self.rl_agent.learn_from_experience(experience)
        
        # Update router
        self.router.update_venue_performance(
            venue=execution_plan['venue'],
            performance=reward / 10.0,  # Normalize
            latency=metrics.execution_time,
            fill_rate=metrics.fill_rate
        )
        
        # Track metrics
        self.performance_metrics['slippage'].append(metrics.slippage)
        self.performance_metrics['fill_rate'].append(metrics.fill_rate)
        self.performance_metrics['execution_time'].append(metrics.execution_time)
        self.performance_metrics['profit_improvement'].append(metrics.profit_improvement)
        
        # Store in history
        self.execution_history.append({
            'plan': execution_plan,
            'result': execution_result,
            'metrics': metrics.__dict__,
            'reward': reward,
            'timestamp': datetime.utcnow()
        })
        
        logger.info(f"Learned from execution. Reward: {reward:.2f}, "
                   f"Slippage: {metrics.slippage:.4f}, Fill rate: {metrics.fill_rate:.2%}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get execution performance summary"""
        summary = {
            'total_executions': len(self.execution_history),
            'rl_training_steps': self.rl_agent.training_step,
            'exploration_rate': self.rl_agent.epsilon,
            'avg_metrics': {}
        }
        
        for metric_name, values in self.performance_metrics.items():
            if values:
                summary['avg_metrics'][metric_name] = {
                    'mean': float(np.mean(values[-100:])),
                    'std': float(np.std(values[-100:])),
                    'recent_trend': 'improving' if len(values) > 10 and 
                                   np.mean(values[-10:]) < np.mean(values[-50:-10]) else 'stable'
                }
        
        return summary
    
    def get_action_preferences(self, state: Dict[str, float]) -> Dict[str, float]:
        """Get current action preferences for given state"""
        action_values = self.rl_agent.get_action_values(state)
        return {action.value: value for action, value in action_values.items()}


async def create_execution_optimizer(config: Optional[Dict] = None) -> ExecutionOptimizer:
    """Factory function to create execution optimizer"""
    optimizer = ExecutionOptimizer(config)
    logger.info("Execution optimizer initialized")
    return optimizer

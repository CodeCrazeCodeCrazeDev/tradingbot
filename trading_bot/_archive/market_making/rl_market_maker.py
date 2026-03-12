"""
Reinforcement Learning Market Making with Adaptive Spread Management

Implements RL-based market making using Avellaneda-Stoikov framework
with adaptive spread adjustment.
"""

import numpy as np
try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import logging
import numpy

logger = logging.getLogger(__name__)


@dataclass
class MarketState:
    """Market making state"""
    mid_price: float
    inventory: int
    time_remaining: float
    bid_ask_spread: float
    order_flow_imbalance: float
    volatility: float
    recent_fills: int


@dataclass
class QuoteDecision:
    """Market making quote decision"""
    bid_price: float
    ask_price: float
    bid_size: int
    ask_size: int
    spread: float
    skew: float  # Inventory skew


class MarketMakingNetwork(nn.Module):
    """Neural network for market making decisions"""
    
    def __init__(self, state_dim: int, hidden_dim: int = 128):
        super(MarketMakingNetwork, self).__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
        )
        
        # Output heads
        self.spread_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, 1),
            nn.Softplus()  # Ensure positive spread
        )
        
        self.skew_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, 1),
            nn.Tanh()  # Skew in [-1, 1]
        )
        
        self.value_head = nn.Linear(hidden_dim // 2, 1)
    
    def forward(self, state):
        features = self.network(state)
        
        spread = self.spread_head(features)
        skew = self.skew_head(features)
        value = self.value_head(features)
        
        return spread, skew, value


class AvellanedaStoikovModel:
    """
    Avellaneda-Stoikov Market Making Model
    
    Optimal market making with inventory risk management.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Model parameters
        self.risk_aversion = self.config.get('risk_aversion', 0.1)
        self.terminal_time = self.config.get('terminal_time', 1.0)
        self.volatility = self.config.get('volatility', 0.02)
        
    def calculate_reservation_price(
        self,
        mid_price: float,
        inventory: int,
        time_remaining: float
    ) -> float:
        """
        Calculate reservation price (indifference price)
        
        Args:
            mid_price: Current mid price
            inventory: Current inventory position
            time_remaining: Time until end of trading
            
        Returns:
            Reservation price
        """
        # Reservation price adjustment
        adjustment = self.risk_aversion * self.volatility ** 2 * inventory * time_remaining
        
        reservation_price = mid_price - adjustment
        
        return reservation_price
    
    def calculate_optimal_spread(
        self,
        time_remaining: float,
        volatility: float
    ) -> float:
        """
        Calculate optimal bid-ask spread
        
        Args:
            time_remaining: Time until end of trading
            volatility: Market volatility
            
        Returns:
            Optimal spread
        """
        # Optimal spread formula
        spread = self.risk_aversion * volatility ** 2 * time_remaining + 2 / self.risk_aversion * np.log(1 + self.risk_aversion / 2)
        
        return max(spread, 0.0001)  # Minimum spread
    
    def calculate_quotes(
        self,
        mid_price: float,
        inventory: int,
        time_remaining: float,
        volatility: float
    ) -> Tuple[float, float]:
        """
        Calculate optimal bid and ask prices
        
        Returns:
            (bid_price, ask_price)
        """
        reservation_price = self.calculate_reservation_price(mid_price, inventory, time_remaining)
        optimal_spread = self.calculate_optimal_spread(time_remaining, volatility)
        
        bid_price = reservation_price - optimal_spread / 2
        ask_price = reservation_price + optimal_spread / 2
        
        return bid_price, ask_price


class RLMarketMaker:
    """
    Reinforcement Learning Market Maker
    
    Learns optimal market making strategy through interaction with market.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # State dimension
        self.state_dim = 7  # mid_price, inventory, time, spread, flow, vol, fills
        
        # RL parameters
        self.learning_rate = self.config.get('learning_rate', 1e-4)
        self.gamma = self.config.get('gamma', 0.99)
        self.epsilon = self.config.get('epsilon', 0.1)
        self.epsilon_decay = self.config.get('epsilon_decay', 0.995)
        self.min_epsilon = self.config.get('min_epsilon', 0.01)
        
        # Initialize network
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.policy_net = MarketMakingNetwork(self.state_dim).to(self.device)
        self.target_net = MarketMakingNetwork(self.state_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.learning_rate)
        
        # Experience replay
        self.memory = deque(maxlen=10000)
        self.batch_size = self.config.get('batch_size', 64)
        
        # Avellaneda-Stoikov baseline
        self.as_model = AvellanedaStoikovModel(config)
        
        # Performance tracking
        self.episode_rewards = deque(maxlen=100)
        self.episode_pnls = deque(maxlen=100)
        
        logger.info(f"RL Market Maker initialized on {self.device}")
    
    def get_state_vector(self, state: MarketState) -> np.ndarray:
        """Convert market state to feature vector"""
        return np.array([
            state.mid_price / 100.0,  # Normalize
            state.inventory / 100.0,
            state.time_remaining,
            state.bid_ask_spread * 10000,  # bps
            state.order_flow_imbalance,
            state.volatility * 100,
            state.recent_fills / 10.0
        ])
    
    def select_action(self, state: MarketState, explore: bool = True) -> QuoteDecision:
        """
        Select market making action (quotes)
        
        Args:
            state: Current market state
            explore: Whether to explore (epsilon-greedy)
            
        Returns:
            Quote decision
        """
        # Epsilon-greedy exploration
        if explore and np.random.random() < self.epsilon:
            # Random exploration
            spread = np.random.uniform(0.0001, 0.01)
            skew = np.random.uniform(-0.5, 0.5)
        else:
            # Policy network
            state_tensor = torch.FloatTensor(self.get_state_vector(state)).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                spread_tensor, skew_tensor, _ = self.policy_net(state_tensor)
                spread = spread_tensor.item()
                skew = skew_tensor.item()
        
        # Calculate quotes
        reservation_price = self.as_model.calculate_reservation_price(
            state.mid_price, state.inventory, state.time_remaining
        )
        
        # Apply skew based on inventory
        bid_price = reservation_price - spread / 2 + skew * spread / 4
        ask_price = reservation_price + spread / 2 + skew * spread / 4
        
        # Quote sizes (could also be learned)
        base_size = 100
        bid_size = int(base_size * (1 - state.inventory / 100))  # Reduce bid size if long
        ask_size = int(base_size * (1 + state.inventory / 100))  # Reduce ask size if short
        
        return QuoteDecision(
            bid_price=bid_price,
            ask_price=ask_price,
            bid_size=max(1, bid_size),
            ask_size=max(1, ask_size),
            spread=spread,
            skew=skew
        )
    
    def store_experience(
        self,
        state: MarketState,
        action: QuoteDecision,
        reward: float,
        next_state: MarketState,
        done: bool
    ):
        """Store experience in replay buffer"""
        self.memory.append((
            self.get_state_vector(state),
            (action.spread, action.skew),
            reward,
            self.get_state_vector(next_state),
            done
        ))
    
    def train_step(self) -> Optional[float]:
        """
        Perform one training step
        
        Returns:
            Loss value if training occurred
        """
        if len(self.memory) < self.batch_size:
            return None
        
        # Sample batch
        batch = [self.memory[i] for i in np.random.choice(len(self.memory), self.batch_size, replace=False)]
        
        states = torch.FloatTensor([s for s, _, _, _, _ in batch]).to(self.device)
        actions = torch.FloatTensor([a for _, a, _, _, _ in batch]).to(self.device)
        rewards = torch.FloatTensor([r for _, _, r, _, _ in batch]).to(self.device)
        next_states = torch.FloatTensor([ns for _, _, _, ns, _ in batch]).to(self.device)
        dones = torch.FloatTensor([d for _, _, _, _, d in batch]).to(self.device)
        
        # Current Q values
        spread_pred, skew_pred, value_pred = self.policy_net(states)
        
        # Target Q values
        with torch.no_grad():
            _, _, next_value = self.target_net(next_states)
            target_value = rewards + self.gamma * next_value.squeeze() * (1 - dones)
        
        # Loss
        value_loss = nn.MSELoss()(value_pred.squeeze(), target_value)
        
        # Policy loss (maximize expected value)
        policy_loss = -value_pred.mean()
        
        total_loss = value_loss + 0.1 * policy_loss
        
        # Optimize
        self.optimizer.zero_grad()
        total_loss.backward()
        nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        # Decay epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
        return total_loss.item()
    
    def update_target_network(self):
        """Update target network"""
        self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def calculate_reward(
        self,
        pnl: float,
        inventory: int,
        filled_bid: bool,
        filled_ask: bool
    ) -> float:
        """
        Calculate reward for market making action
        
        Args:
            pnl: Profit and loss from trades
            inventory: Current inventory
            filled_bid: Whether bid was filled
            filled_ask: Whether ask was filled
            
        Returns:
            Reward value
        """
        # Base reward from PnL
        reward = pnl
        
        # Penalty for large inventory
        inventory_penalty = -0.01 * abs(inventory)
        
        # Bonus for fills (liquidity provision)
        fill_bonus = 0.1 * (int(filled_bid) + int(filled_ask))
        
        total_reward = reward + inventory_penalty + fill_bonus
        
        return total_reward
    
    def save_model(self, path: str):
        """Save model checkpoint"""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']
        logger.info(f"Model loaded from {path}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    market_maker = RLMarketMaker()
    
    # Simulate market making episode
    state = MarketState(
        mid_price=100.0,
        inventory=0,
        time_remaining=1.0,
        bid_ask_spread=0.01,
        order_flow_imbalance=0.0,
        volatility=0.02,
        recent_fills=0
    )
    
    # Get quote
    quote = market_maker.select_action(state, explore=False)
    
    logger.info(f"\nMarket Making Quote:")
    logger.info(f"  Bid: ${quote.bid_price:.4f} x {quote.bid_size}")
    logger.info(f"  Ask: ${quote.ask_price:.4f} x {quote.ask_size}")
    logger.info(f"  Spread: {quote.spread * 10000:.2f} bps")
    logger.info(f"  Skew: {quote.skew:.4f}")

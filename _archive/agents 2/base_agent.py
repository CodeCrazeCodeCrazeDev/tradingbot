"""
Phase 2: Multi-Agent Architecture - Base Agent
Foundation for specialized trading agents
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import numpy as np

# Set up logger
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of trading agents."""
    TREND_FOLLOWER = "trend_follower"
    MEAN_REVERTER = "mean_reverter"
    VOLATILITY_TRADER = "volatility_trader"
    ARBITRAGEUR = "arbitrageur"
    MARKET_MAKER = "market_maker"
    RISK_MANAGER = "risk_manager"


@dataclass
class AgentProposal:
    """Trading proposal from an agent."""
    agent_id: str
    agent_type: AgentType
    action: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    expected_return: float
    risk_score: float
    priority: int = 1
    
    def to_dict(self) -> Dict:
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'action': self.action,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'expected_return': self.expected_return,
            'risk_score': self.risk_score,
            'priority': self.priority
        }


class BaseAgent(ABC):
    """
    Base class for all trading agents.
    Each agent specializes in a specific trading strategy.
    """
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.performance_history = []
        self.win_rate = 0.0
        self.total_trades = 0
        self.successful_trades = 0
        
        logger.info(f"✅ {agent_type.value} agent '{agent_id}' initialized")
    
    @abstractmethod
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        """
        Analyze market and generate trading proposal.
        Must be implemented by each specialized agent.
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the strategy name."""
        pass
    
    def update_performance(self, trade_result: Dict):
        """Update agent's performance metrics."""
        self.total_trades += 1
        
        if trade_result.get('outcome') == 'win':
            self.successful_trades += 1
        
        self.win_rate = self.successful_trades / self.total_trades
        self.performance_history.append(trade_result)
        
        # Keep only last 100 trades
        if len(self.performance_history) > 100:
            self.performance_history.pop(0)
    
    def get_performance_metrics(self) -> Dict:
        """Get agent's performance statistics."""
        if not self.performance_history:
            return {
                'win_rate': 0.0,
                'total_trades': 0,
                'avg_return': 0.0,
                'sharpe_ratio': 0.0
            }
        
        returns = [t.get('pnl', 0) for t in self.performance_history]
        
        return {
            'win_rate': self.win_rate,
            'total_trades': self.total_trades,
            'avg_return': np.mean(returns),
            'sharpe_ratio': np.mean(returns) / (np.std(returns) + 1e-8),
            'recent_performance': returns[-10:] if len(returns) >= 10 else returns
        }
    
    def calculate_confidence(self, signal_strength: float, market_conditions: Dict) -> float:
        """
        Calculate confidence score based on signal strength and conditions.
        
        Args:
            signal_strength: Raw signal strength (0-1)
            market_conditions: Market state information
        
        Returns:
            Confidence score (0-1)
        """
        # Base confidence from signal
        confidence = signal_strength
        
        # Adjust based on agent's historical performance
        if self.total_trades > 10:
            performance_factor = self.win_rate
            confidence = 0.7 * confidence + 0.3 * performance_factor
        
        # Adjust based on market volatility
        volatility = market_conditions.get('volatility', 1.0)
        if volatility > 2.0:  # High volatility
            confidence *= 0.8  # Reduce confidence
        elif volatility < 0.5:  # Low volatility
            confidence *= 0.9  # Slightly reduce confidence
        
        return float(np.clip(confidence, 0.0, 1.0))
    
    def should_trade(self, market_data: Dict) -> bool:
        """
        Determine if agent should participate in trading decision.
        Can be overridden by specialized agents.
        """
        # Don't trade if performance is very poor
        if self.total_trades > 20 and self.win_rate < 0.3:
            logger.warning(f"⚠️ {self.agent_id} has low win rate ({self.win_rate:.1%}), abstaining")
            return False
        
        return True
    
    def get_risk_assessment(self, market_data: Dict) -> Dict:
        """
        Assess risk for current market conditions.
        Can be overridden by specialized agents.
        """
        volatility = market_data.get('volatility', 1.0)
        
        if volatility > 3.0:
            risk_level = 'HIGH'
            risk_score = 0.8
        elif volatility > 2.0:
            risk_level = 'MEDIUM'
            risk_score = 0.5
        else:
            risk_level = 'LOW'
            risk_score = 0.2
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'volatility': volatility
        }
    
    def __repr__(self):
        return f"{self.agent_type.value}(id={self.agent_id}, win_rate={self.win_rate:.1%})"


class AgentState:
    """Manages agent state and memory."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memory = {}
        self.recent_decisions = []
        self.market_regime = 'unknown'
    
    def update_memory(self, key: str, value):
        """Store information in agent memory."""
        self.memory[key] = value
    
    def get_memory(self, key: str, default=None):
        """Retrieve information from agent memory."""
        return self.memory.get(key, default)
    
    def add_decision(self, decision: Dict):
        """Record a decision for learning."""
        self.recent_decisions.append(decision)
        if len(self.recent_decisions) > 50:
            self.recent_decisions.pop(0)
    
    def update_regime(self, regime: str):
        """Update detected market regime."""
        self.market_regime = regime
        logger.info(f"🎯 {self.agent_id} detected {regime} regime")


class AgentCommunication:
    """Handles communication between agents."""
    
    def __init__(self):
        self.message_queue = []
        self.subscriptions = {}
    
    def broadcast(self, sender_id: str, message_type: str, data: Dict):
        """Broadcast message to all subscribed agents."""
        message = {
            'sender': sender_id,
            'type': message_type,
            'data': data,
            'timestamp': np.datetime64('now')
        }
        self.message_queue.append(message)
        
        # Notify subscribers
        if message_type in self.subscriptions:
            for subscriber in self.subscriptions[message_type]:
                logger.debug(f"📨 {sender_id} → {subscriber}: {message_type}")
    
    def subscribe(self, agent_id: str, message_type: str):
        """Subscribe agent to message type."""
        if message_type not in self.subscriptions:
            self.subscriptions[message_type] = []
        self.subscriptions[message_type].append(agent_id)
    
    def get_messages(self, agent_id: str, message_type: Optional[str] = None) -> List[Dict]:
        """Get messages for agent."""
        messages = []
        for msg in self.message_queue:
            if message_type is None or msg['type'] == message_type:
                if agent_id in self.subscriptions.get(msg['type'], []):
                    messages.append(msg)
        return messages
    
    def clear_old_messages(self, max_age_seconds: int = 300):
        """Clear old messages from queue."""
        current_time = np.datetime64('now')
        self.message_queue = [
            msg for msg in self.message_queue
            if (current_time - msg['timestamp']).astype(int) < max_age_seconds
        ]

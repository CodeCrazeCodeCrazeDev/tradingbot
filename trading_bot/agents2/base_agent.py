"""
Phase 2: Multi-Agent Architecture - Base Agent
Foundation for specialized trading agents.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import numpy as np

from ..a2a import A2AMessageBus
from ..world2agent import World2AgentBridge

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
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "action": self.action,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "expected_return": self.expected_return,
            "risk_score": self.risk_score,
            "priority": self.priority,
        }


class BaseAgent(ABC):
    """
    Base class for all trading agents.
    Each agent specializes in a specific trading strategy.
    """

    def __init__(self, agent_id: str, agent_type: AgentType):
        try:
            self.agent_id = agent_id
            self.agent_type = agent_type
            self.performance_history = []
            self.win_rate = 0.0
            self.total_trades = 0
            self.successful_trades = 0

            logger.info("%s agent '%s' initialized", agent_type.value, agent_id)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    @abstractmethod
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        """
        Analyze market and generate trading proposal.
        Must be implemented by each specialized agent.
        """

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the strategy name."""

    def update_performance(self, trade_result: Dict):
        """Update agent's performance metrics."""
        try:
            self.total_trades += 1

            if trade_result.get("outcome") == "win":
                self.successful_trades += 1

            self.win_rate = self.successful_trades / self.total_trades
            self.performance_history.append(trade_result)

            if len(self.performance_history) > 100:
                self.performance_history.pop(0)
        except Exception as e:
            logger.error(f"Error in update_performance: {e}")
            raise

    def get_performance_metrics(self) -> Dict:
        """Get agent's performance statistics."""
        try:
            if not self.performance_history:
                return {
                    "win_rate": 0.0,
                    "total_trades": 0,
                    "avg_return": 0.0,
                    "sharpe_ratio": 0.0,
                }

            returns = [t.get("pnl", 0) for t in self.performance_history]

            return {
                "win_rate": self.win_rate,
                "total_trades": self.total_trades,
                "avg_return": np.mean(returns),
                "sharpe_ratio": np.mean(returns) / (np.std(returns) + 1e-8),
                "recent_performance": returns[-10:] if len(returns) >= 10 else returns,
            }
        except Exception as e:
            logger.error(f"Error in get_performance_metrics: {e}")
            raise

    def calculate_confidence(self, signal_strength: float, market_conditions: Dict) -> float:
        """
        Calculate confidence score based on signal strength and conditions.

        Args:
            signal_strength: Raw signal strength (0-1)
            market_conditions: Market state information

        Returns:
            Confidence score (0-1)
        """
        try:
            confidence = signal_strength

            if self.total_trades > 10:
                performance_factor = self.win_rate
                confidence = 0.7 * confidence + 0.3 * performance_factor

            volatility = market_conditions.get("volatility", 1.0)
            if volatility > 2.0:
                confidence *= 0.8
            elif volatility < 0.5:
                confidence *= 0.9

            return float(np.clip(confidence, 0.0, 1.0))
        except Exception as e:
            logger.error(f"Error in calculate_confidence: {e}")
            raise

    def should_trade(self, market_data: Dict) -> bool:
        """
        Determine if agent should participate in trading decision.
        Can be overridden by specialized agents.
        """
        try:
            if self.total_trades > 20 and self.win_rate < 0.3:
                logger.warning(
                    "%s has low win rate (%.1f%%), abstaining",
                    self.agent_id,
                    self.win_rate * 100,
                )
                return False

            return True
        except Exception as e:
            logger.error(f"Error in should_trade: {e}")
            raise

    def get_risk_assessment(self, market_data: Dict) -> Dict:
        """
        Assess risk for current market conditions.
        Can be overridden by specialized agents.
        """
        try:
            volatility = market_data.get("volatility", 1.0)

            if volatility > 3.0:
                risk_level = "HIGH"
                risk_score = 0.8
            elif volatility > 2.0:
                risk_level = "MEDIUM"
                risk_score = 0.5
            else:
                risk_level = "LOW"
                risk_score = 0.2

            return {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "volatility": volatility,
            }
        except Exception as e:
            logger.error(f"Error in get_risk_assessment: {e}")
            raise

    def __repr__(self):
        return f"{self.agent_type.value}(id={self.agent_id}, win_rate={self.win_rate:.1%})"


class AgentState:
    """Manages agent state and memory."""

    def __init__(self, agent_id: str):
        try:
            self.agent_id = agent_id
            self.memory = {}
            self.recent_decisions = []
            self.market_regime = "unknown"
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def update_memory(self, key: str, value):
        """Store information in agent memory."""
        try:
            self.memory[key] = value
        except Exception as e:
            logger.error(f"Error in update_memory: {e}")
            raise

    def get_memory(self, key: str, default=None):
        """Retrieve information from agent memory."""
        return self.memory.get(key, default)

    def add_decision(self, decision: Dict):
        """Record a decision for learning."""
        try:
            self.recent_decisions.append(decision)
            if len(self.recent_decisions) > 50:
                self.recent_decisions.pop(0)
        except Exception as e:
            logger.error(f"Error in add_decision: {e}")
            raise

    def update_regime(self, regime: str):
        """Update detected market regime."""
        try:
            self.market_regime = regime
            logger.info("%s detected %s regime", self.agent_id, regime)
        except Exception as e:
            logger.error(f"Error in update_regime: {e}")
            raise


class AgentCommunication:
    """Handles local and shared A2A communication between agents."""

    def __init__(
        self,
        a2a_bus: Optional[A2AMessageBus] = None,
        world_bridge: Optional[World2AgentBridge] = None,
    ):
        try:
            self.message_queue = []
            self.subscriptions = {}
            self.a2a_bus = a2a_bus or A2AMessageBus()
            self.world_bridge = world_bridge or World2AgentBridge(self.a2a_bus)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def broadcast(self, sender_id: str, message_type: str, data: Dict):
        """Broadcast message to all subscribed agents."""
        try:
            message = {
                "sender": sender_id,
                "type": message_type,
                "data": data,
                "timestamp": np.datetime64("now"),
            }
            self.message_queue.append(message)
            recipients = list(dict.fromkeys(self.subscriptions.get(message_type, [])))
            self.a2a_bus.broadcast(
                sender=sender_id,
                intent=message_type,
                payload=data,
                recipients=recipients,
                channel="agents2",
                metadata={"transport": "agent_communication"},
            )

            if message_type in self.subscriptions:
                for subscriber in self.subscriptions[message_type]:
                    logger.debug("%s -> %s: %s", sender_id, subscriber, message_type)
        except Exception as e:
            logger.error(f"Error in broadcast: {e}")
            raise

    def subscribe(self, agent_id: str, message_type: str):
        """Subscribe agent to message type."""
        try:
            if message_type not in self.subscriptions:
                self.subscriptions[message_type] = []
            self.subscriptions[message_type].append(agent_id)
            self.a2a_bus.register_agent(agent_id)
        except Exception as e:
            logger.error(f"Error in subscribe: {e}")
            raise

    def get_messages(self, agent_id: str, message_type: Optional[str] = None) -> List[Dict]:
        """Get locally buffered messages for an agent."""
        try:
            messages = []
            for msg in self.message_queue:
                if message_type is None or msg["type"] == message_type:
                    if agent_id in self.subscriptions.get(msg["type"], []):
                        messages.append(msg)
            return messages
        except Exception as e:
            logger.error(f"Error in get_messages: {e}")
            raise

    def clear_old_messages(self, max_age_seconds: int = 300):
        """Clear old messages from queue."""
        try:
            current_time = np.datetime64("now")
            self.message_queue = [
                msg
                for msg in self.message_queue
                if (current_time - msg["timestamp"]).astype(int) < max_age_seconds
            ]
        except Exception as e:
            logger.error(f"Error in clear_old_messages: {e}")
            raise

    def register_agent(self, agent_id: str, capabilities: Optional[List[str]] = None):
        """Register an agent for shared A2A communication."""
        try:
            self.a2a_bus.register_agent(agent_id, capabilities=capabilities or [])
        except Exception as e:
            logger.error(f"Error in register_agent: {e}")
            raise

    def publish_world_state(
        self,
        sender_id: str,
        world_state: Dict,
        audience: Optional[List[str]] = None,
        context_type: str = "market",
    ) -> Dict:
        """Publish shared world context to the world2agent bridge."""
        try:
            snapshot = self.world_bridge.publish_world_state(
                source=sender_id,
                world_state=world_state,
                audience=audience,
                context_type=context_type,
            )
            return snapshot.to_dict()
        except Exception as e:
            logger.error(f"Error in publish_world_state: {e}")
            raise

    def get_a2a_messages(
        self,
        agent_id: str,
        message_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Fetch A2A messages for an agent."""
        try:
            return [
                message.to_dict()
                for message in self.a2a_bus.get_messages(
                    agent_id,
                    intent=message_type,
                    limit=limit,
                )
            ]
        except Exception as e:
            logger.error(f"Error in get_a2a_messages: {e}")
            raise

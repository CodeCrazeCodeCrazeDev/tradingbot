"""
Migrated Legacy Agents from agents2 system.
Relocated to core_agent_system to remove cross-package dependencies.
"""
import numpy as np
from typing import Dict, List, Optional
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AgentType(Enum):
    TREND_FOLLOWER = "trend_follower"
    MEAN_REVERTER = "mean_reverter"
    VOLATILITY_TRADER = "volatility_trader"
    ARBITRAGEUR = "arbitrageur"
    MARKET_MAKER = "market_maker"
    RISK_MANAGER = "risk_manager"

@dataclass
class AgentProposal:
    agent_id: str
    agent_type: AgentType
    action: str
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
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.win_rate = 0.0
        self.total_trades = 0

    @abstractmethod
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        pass

    def calculate_confidence(self, signal_strength: float, market_data: Dict) -> float:
        return min(signal_strength * 1.2, 0.95)

class TrendFollowingAgent(BaseAgent):
    def __init__(self, agent_id: str = "trend_agent"):
        super().__init__(agent_id, AgentType.TREND_FOLLOWER)

    def get_strategy_name(self) -> str: return "Trend Following"

    def analyze_market(self, market_data: Dict) -> AgentProposal:
        sma_20 = market_data.get('sma_20', 0)
        sma_50 = market_data.get('sma_50', 0)
        price = market_data.get('price', 0)
        if sma_20 > sma_50 * 1.01 and price > sma_20:
            action, strength = 'BUY', 0.8
        elif sma_20 < sma_50 * 0.99 and price < sma_20:
            action, strength = 'SELL', 0.8
        else:
            action, strength = 'HOLD', 0.0
        return AgentProposal(self.agent_id, self.agent_type, action, self.calculate_confidence(strength, market_data), "Migrated logic", 0.01, 0.3)

class MeanReversionAgent(BaseAgent):
    def __init__(self, agent_id: str = "mean_reversion_agent"):
        super().__init__(agent_id, AgentType.MEAN_REVERTER)
    def get_strategy_name(self) -> str: return "Mean Reversion"
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        rsi = market_data.get('rsi', 50)
        if rsi < 30: action, strength = 'BUY', 0.7
        elif rsi > 70: action, strength = 'SELL', 0.7
        else: action, strength = 'HOLD', 0.0
        return AgentProposal(self.agent_id, self.agent_type, action, self.calculate_confidence(strength, market_data), "Migrated logic", 0.01, 0.3)

class VolatilityAgent(BaseAgent):
    def __init__(self, agent_id: str = "volatility_agent"):
        super().__init__(agent_id, AgentType.VOLATILITY_TRADER)
    def get_strategy_name(self) -> str: return "Volatility"
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        return AgentProposal(self.agent_id, self.agent_type, "HOLD", 0.5, "Placeholder", 0.0, 0.5)

class RiskManagerAgent(BaseAgent):
    def __init__(self, agent_id: str = "risk_manager_agent"):
        super().__init__(agent_id, AgentType.RISK_MANAGER)
    def get_strategy_name(self) -> str: return "Risk Manager"
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        return AgentProposal(self.agent_id, self.agent_type, "HOLD", 0.9, "Placeholder", 0.0, 0.1)

class MarketMakerAgent(BaseAgent):
    def __init__(self, agent_id: str = "market_maker_agent"):
        super().__init__(agent_id, AgentType.MARKET_MAKER)
    def get_strategy_name(self) -> str: return "Market Maker"
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        return AgentProposal(self.agent_id, self.agent_type, "HOLD", 0.5, "Placeholder", 0.0, 0.2)

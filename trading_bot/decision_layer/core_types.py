"""
Core Types for Innovative Decision Layer

Defines all enums, data classes, and base classes for the 100 decision concepts.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class DecisionCategory(Enum):
    """Categories of decision concepts"""
    COGNITIVE = "cognitive"
    PROBABILISTIC = "probabilistic"
    BEHAVIORAL = "behavioral"
    GAME_THEORY = "game_theory"
    TEMPORAL = "temporal"
    RISK_AWARE = "risk_aware"
    MICROSTRUCTURE = "microstructure"
    ADAPTIVE = "adaptive"
    MULTI_AGENT = "multi_agent"
    META = "meta"
    QUANTITATIVE_EDGE = "quantitative_edge"
    RESEARCH_INFORMED = "research_informed"


class DecisionAction(Enum):
    """Possible decision actions"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    HOLD = "hold"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    ABSTAIN = "abstain"
    DEFER = "defer"


class DecisionUrgency(Enum):
    """Urgency levels for decisions"""
    IMMEDIATE = "immediate"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    NONE = "none"


@dataclass
class DecisionContext:
    """Context for making a decision"""
    symbol: str
    price: float
    volume: float
    volatility: float
    trend: float  # -1 to 1
    momentum: float  # -1 to 1
    sentiment: float  # -1 to 1
    regime: str
    timeframe: str
    portfolio_value: float
    current_position: float
    drawdown: float
    win_rate: float
    recent_trades: List[Dict] = field(default_factory=list)
    market_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DecisionResult:
    """Result from a decision concept"""
    concept_id: int
    concept_name: str
    category: DecisionCategory
    action: DecisionAction
    confidence: float
    urgency: DecisionUrgency
    reasoning: str
    factors: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'concept_id': self.concept_id,
            'concept_name': self.concept_name,
            'category': self.category.value,
            'action': self.action.value,
            'confidence': self.confidence,
            'urgency': self.urgency.value,
            'reasoning': self.reasoning,
            'factors': self.factors,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class AggregatedDecision:
    """Aggregated decision from multiple concepts"""
    final_action: DecisionAction
    final_confidence: float
    consensus_level: float
    contributing_concepts: List[DecisionResult]
    dissenting_concepts: List[DecisionResult]
    reasoning_chain: List[str]
    risk_adjusted_action: DecisionAction
    position_size_multiplier: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DecisionConcept(ABC):
    """Base class for all decision concepts"""
    
    def __init__(self, concept_id: int, name: str, category: DecisionCategory):
        try:
            self.concept_id = concept_id
            self.name = name
            self.category = category
            self.weight = 1.0
            self.enabled = True
            self.history: deque = deque(maxlen=100)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    @abstractmethod
    def decide(self, context: DecisionContext) -> DecisionResult:
        """Make a decision based on context"""
        pass
    
    def _create_result(
        self,
        action: DecisionAction,
        confidence: float,
        urgency: DecisionUrgency,
        reasoning: str,
        factors: Dict[str, float]
    ) -> DecisionResult:
        """Helper to create decision result"""
        try:
            result = DecisionResult(
                concept_id=self.concept_id,
                concept_name=self.name,
                category=self.category,
                action=action,
                confidence=min(max(confidence, 0.0), 1.0),
                urgency=urgency,
                reasoning=reasoning,
                factors=factors
            )
            self.history.append(result)
            return result
        except Exception as e:
            logger.error(f"Error in _create_result: {e}")
            raise
    
    def _signal_to_action(self, signal: float) -> DecisionAction:
        """Convert signal (-1 to 1) to action"""
        try:
            if signal > 0.6: return DecisionAction.STRONG_BUY
            if signal > 0.3: return DecisionAction.BUY
            if signal > 0.1: return DecisionAction.WEAK_BUY
            if signal > -0.1: return DecisionAction.HOLD
            if signal > -0.3: return DecisionAction.WEAK_SELL
            if signal > -0.6: return DecisionAction.SELL
            return DecisionAction.STRONG_SELL
        except Exception as e:
            logger.error(f"Error in _signal_to_action: {e}")
            raise

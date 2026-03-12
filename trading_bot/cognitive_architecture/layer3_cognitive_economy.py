"""
Layer 3: Cognitive Economy (Multi-Agent Decision System)
Multi-agent consensus for trading decisions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentDecision:
    """Decision made by an agent."""
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for cognitive agents."""
    
    def __init__(self, name: str, weight: float = 1.0):
        try:
            self.name = name
            self.weight = weight
            self.active = True
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> AgentDecision:
        """Analyze data and return decision."""
        pass


class DataAgent(BaseAgent):
    """Agent responsible for data quality and validation."""
    
    def __init__(self):
        try:
            super().__init__("DataAgent", weight=1.0)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, data: Dict[str, Any]) -> AgentDecision:
        """Validate data quality and completeness."""
        try:
            quality_score = data.get('data_quality', 0.8)
            return AgentDecision(
                action='hold' if quality_score < 0.5 else 'proceed',
                confidence=quality_score,
                reasoning=f"Data quality score: {quality_score:.2f}"
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class StrategyAgent(BaseAgent):
    """Agent responsible for strategy selection and signals."""
    
    def __init__(self):
        try:
            super().__init__("StrategyAgent", weight=1.5)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, data: Dict[str, Any]) -> AgentDecision:
        """Analyze market data and generate trading signal."""
        try:
            signal = data.get('signal', {})
            direction = signal.get('direction', 'hold')
            confidence = signal.get('confidence', 0.5)
        
            return AgentDecision(
                action=direction,
                confidence=confidence,
                reasoning=f"Strategy signal: {direction} with {confidence:.2f} confidence"
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class RiskAgent(BaseAgent):
    """Agent responsible for risk assessment."""
    
    def __init__(self):
        try:
            super().__init__("RiskAgent", weight=2.0)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, data: Dict[str, Any]) -> AgentDecision:
        """Assess risk and provide risk-adjusted decision."""
        try:
            risk_score = data.get('risk_score', 0.5)
            position_size = data.get('position_size', 0.0)
        
            # High risk = recommend hold
            if risk_score > 0.7:
                return AgentDecision(
                    action='hold',
                    confidence=0.8,
                    reasoning=f"High risk detected: {risk_score:.2f}"
                )
        
            return AgentDecision(
                action='proceed',
                confidence=1.0 - risk_score,
                reasoning=f"Risk acceptable: {risk_score:.2f}"
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class LearningAgent(BaseAgent):
    """Agent responsible for learning and adaptation."""
    
    def __init__(self):
        try:
            super().__init__("LearningAgent", weight=1.0)
            self.performance_history: List[float] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, data: Dict[str, Any]) -> AgentDecision:
        """Analyze based on learned patterns."""
        try:
            pattern_match = data.get('pattern_confidence', 0.5)
        
            return AgentDecision(
                action='proceed' if pattern_match > 0.6 else 'hold',
                confidence=pattern_match,
                reasoning=f"Pattern match confidence: {pattern_match:.2f}"
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def update(self, outcome: float):
        """Update learning based on outcome."""
        try:
            self.performance_history.append(outcome)
            if len(self.performance_history) > 100:
                self.performance_history.pop(0)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class SupervisorAgent(BaseAgent):
    """Supervisor agent that coordinates other agents."""
    
    def __init__(self):
        try:
            super().__init__("SupervisorAgent", weight=1.0)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, data: Dict[str, Any]) -> AgentDecision:
        """Supervise and validate decisions."""
        try:
            system_health = data.get('system_health', 1.0)
        
            if system_health < 0.5:
                return AgentDecision(
                    action='hold',
                    confidence=0.9,
                    reasoning=f"System health low: {system_health:.2f}"
                )
        
            return AgentDecision(
                action='proceed',
                confidence=system_health,
                reasoning=f"System healthy: {system_health:.2f}"
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class CognitiveEconomy:
    """
    Cognitive Economy - Layer 3 of Cognitive Architecture.
    
    Coordinates multiple agents for consensus-based decision making.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.agents: List[BaseAgent] = [
                DataAgent(),
                StrategyAgent(),
                RiskAgent(),
                LearningAgent(),
                SupervisorAgent()
            ]
            logger.info("CognitiveEconomy initialized with %d agents", len(self.agents))
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def reach_consensus(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Reach consensus among all agents."""
        try:
            decisions: List[AgentDecision] = []
        
            for agent in self.agents:
                if agent.active:
                    decision = agent.analyze(data)
                    decisions.append(decision)
        
            # Calculate weighted consensus
            action_scores = {'buy': 0.0, 'sell': 0.0, 'hold': 0.0, 'proceed': 0.0}
            total_weight = 0.0
        
            for agent, decision in zip(self.agents, decisions):
                if agent.active:
                    weight = agent.weight * decision.confidence
                    action_scores[decision.action] = action_scores.get(decision.action, 0.0) + weight
                    total_weight += weight
        
            # Normalize scores
            if total_weight > 0:
                for action in action_scores:
                    action_scores[action] /= total_weight
        
            # Determine final action
            final_action = max(action_scores, key=action_scores.get)
            final_confidence = action_scores[final_action]
        
            return {
                'action': final_action,
                'confidence': final_confidence,
                'agent_decisions': [
                    {'agent': a.name, 'action': d.action, 'confidence': d.confidence, 'reasoning': d.reasoning}
                    for a, d in zip(self.agents, decisions)
                ],
                'action_scores': action_scores
            }
        except Exception as e:
            logger.error(f"Error in reach_consensus: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        return {
            'total_agents': len(self.agents),
            'active_agents': len([a for a in self.agents if a.active]),
            'agents': [{'name': a.name, 'weight': a.weight, 'active': a.active} for a in self.agents]
        }

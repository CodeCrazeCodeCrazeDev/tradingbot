import logging
import numpy as np
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .models import SwarmSignal, SwarmLayer, SwarmTaskType
from ..agent_registry import BaseAgent, AgentRole

logger = logging.getLogger(__name__)

class MicroAgent(ABC):
    """Base for lightweight observers"""
    def __init__(self, agent_id: str, objective: str):
        self.agent_id = agent_id
        self.objective = objective
        self.memory = []
        self.max_memory = 10

    @abstractmethod
    def observe(self, market_data: Dict[str, Any]) -> SwarmSignal:
        pass

    def _update_memory(self, observation: Any):
        self.memory.append(observation)
        if len(self.memory) > self.max_memory:
            self.memory.pop(0)

class PatternObserver(MicroAgent):
    def observe(self, market_data: Dict[str, Any]) -> SwarmSignal:
        prices = market_data.get('prices', [])
        if len(prices) < 5:
            return SwarmSignal(self.agent_id, SwarmLayer.MICRO, 0, 0)

        # Simple trend detection
        trend = 1.0 if prices[-1] > prices[-5] else -1.0
        confidence = min(1.0, abs(prices[-1] - prices[-5]) / prices[-5] * 100)

        return SwarmSignal(
            self.agent_id,
            SwarmLayer.MICRO,
            trend,
            confidence,
            evidence={'trend': trend, 'change_pct': confidence}
        )

class MomentumObserver(MicroAgent):
    def observe(self, market_data: Dict[str, Any]) -> SwarmSignal:
        prices = market_data.get('prices', [])
        if len(prices) < 2:
            return SwarmSignal(self.agent_id, SwarmLayer.MICRO, 0, 0)

        velocity = (prices[-1] - prices[-2]) / prices[-2]
        direction = np.sign(velocity)
        confidence = min(1.0, abs(velocity) * 50)

        return SwarmSignal(
            self.agent_id,
            SwarmLayer.MICRO,
            direction,
            confidence,
            evidence={'velocity': velocity}
        )

class VolatilityObserver(MicroAgent):
    def observe(self, market_data: Dict[str, Any]) -> SwarmSignal:
        prices = market_data.get('prices', [])
        if len(prices) < 10:
            return SwarmSignal(self.agent_id, SwarmLayer.MICRO, 0, 0)

        vol = np.std(prices[-10:]) / np.mean(prices[-10:])
        # Volatility is usually regime-defining rather than directional
        # High volatility -> lower directional confidence
        return SwarmSignal(
            self.agent_id,
            SwarmLayer.MICRO,
            0, # Neutral direction
            vol,
            evidence={'volatility': vol}
        )

class SentimentObserver(MicroAgent):
    def observe(self, market_data: Dict[str, Any]) -> SwarmSignal:
        sentiment = market_data.get('sentiment_score', 0)
        direction = np.sign(sentiment)
        confidence = abs(sentiment)

        return SwarmSignal(
            self.agent_id,
            SwarmLayer.MICRO,
            direction,
            confidence,
            evidence={'sentiment': sentiment}
        )

class MicroLayer:
    """Manages the swarm of micro-agents"""
    def __init__(self):
        self.agents: List[MicroAgent] = []
        self._initialize_agents()

    def _initialize_agents(self):
        # Initialize default set of observers
        self.agents.append(PatternObserver(f"pattern_{uuid.uuid4().hex[:4]}", "Detect price patterns"))
        self.agents.append(MomentumObserver(f"momentum_{uuid.uuid4().hex[:4]}", "Observe momentum"))
        self.agents.append(VolatilityObserver(f"volatility_{uuid.uuid4().hex[:4]}", "Monitor volatility"))
        self.agents.append(SentimentObserver(f"sentiment_{uuid.uuid4().hex[:4]}", "Observe sentiment"))

    def get_signals(self, market_data: Dict[str, Any]) -> List[SwarmSignal]:
        signals = []
        for agent in self.agents:
            try:
                signal = agent.observe(market_data)
                if signal.confidence > 0:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error in micro-agent {agent.agent_id}: {e}")
        return signals

class ExpertLayer:
    """Manages specialized expert agents"""
    def __init__(self, agent_registry: Any):
        self.registry = agent_registry

    async def get_expert_analysis(self, task_type: SwarmTaskType, context: Dict[str, Any]) -> List[SwarmSignal]:
        signals = []

        # Mapping SwarmTaskType to AgentRoles
        role_map = {
            SwarmTaskType.ANALYSIS: [AgentRole.RESEARCHER, AgentRole.PLANNER],
            SwarmTaskType.RESEARCH: [AgentRole.RESEARCHER],
            SwarmTaskType.DEBATE: [AgentRole.RESEARCHER, AgentRole.PLANNER, AgentRole.EVALUATOR],
        }

        target_roles = role_map.get(task_type, [AgentRole.RESEARCHER])

        for role in target_roles:
            agents = self.registry.get_agents_by_role(role)
            for agent in agents:
                try:
                    result = await agent.execute({
                        'operation': 'analyze',
                        'context': context,
                        'data': context.get('market_state', context)
                    })

                    if result.get('success'):
                        signals.append(SwarmSignal(
                            source_id=agent.agent_id,
                            layer=SwarmLayer.EXPERT,
                            direction=result.get('direction', 0),
                            confidence=result.get('confidence', 0.5),
                            evidence=result.get('reasoning', {}),
                            metadata={'role': role.value}
                        ))
                except Exception as e:
                    logger.error(f"Error in expert agent {agent.agent_id}: {e}")

        return signals

import logging
import numpy as np
from typing import Any, Dict, List, Optional
from .models import SwarmSignal, SwarmConsensus, SwarmLayer, SwarmTaskType
from .layers import MicroLayer, ExpertLayer
from ..agent_registry import AgentRole
from .memory import AgentPerformanceMemory, EvolutionLayer

logger = logging.getLogger(__name__)

class SwarmController:
    """
    Central brain of the Unified Swarm Intelligence System.
    """
    def __init__(self, agent_registry: Any, config: Optional[Dict] = None):
        self.config = config or {}
        self.registry = agent_registry

        # Components
        self.performance_memory = AgentPerformanceMemory()
        self.evolution_layer = EvolutionLayer(self.performance_memory)
        self.micro_layer = MicroLayer()
        self.expert_layer = ExpertLayer(self.registry)

        logger.info("Swarm Controller initialized")

    async def get_consensus(self, task: str, context: Dict[str, Any]) -> SwarmConsensus:
        """
        Main entry point to get swarm consensus for a task.
        """
        market_data = context.get('market_state', {})

        # 1. Gather signals from Micro Layer
        micro_signals = self.micro_layer.get_signals(market_data)

        # 2. Gather signals from Expert Layer
        expert_signals = await self.expert_layer.get_expert_analysis(
            SwarmTaskType.ANALYSIS,
            context
        )

        all_signals = micro_signals + expert_signals

        if not all_signals:
            return SwarmConsensus(0, 0, 0, [], [])

        # 3. Weighted Aggregation
        weighted_direction = 0.0
        total_weight = 0.0

        for signal in all_signals:
            # Get historical accuracy weight
            perf_weight = self.performance_memory.get_agent_weight(
                signal.source_id,
                context
            )

            # Layer weighting (Experts carry more weight)
            layer_multiplier = 2.0 if signal.layer == SwarmLayer.EXPERT else 1.0

            # Final signal weight
            weight = signal.confidence * perf_weight * layer_multiplier

            weighted_direction += signal.direction * weight
            total_weight += weight

        final_direction = np.sign(weighted_direction)
        final_confidence = abs(weighted_direction) / total_weight if total_weight > 0 else 0

        # 4. Dissent Detection
        bullish_count = sum(1 for s in all_signals if s.direction > 0.2)
        bearish_count = sum(1 for s in all_signals if s.direction < -0.2)

        minority = min(bullish_count, bearish_count)
        majority = max(bullish_count, bearish_count)
        dissent_ratio = minority / majority if majority > 0 else 0

        # 5. Determine dominant factors
        dominant_factors = self._identify_dominant_factors(all_signals)

        consensus = SwarmConsensus(
            direction=final_direction,
            confidence=final_confidence * (1 - dissent_ratio * 0.5), # Penalty for dissent
            dissent_ratio=dissent_ratio,
            contributing_signals=all_signals,
            dominant_factors=dominant_factors
        )

        # 6. Mandatory Risk Validation
        safe_consensus = await self._validate_risk(consensus, context)

        logger.info(f"Swarm Consensus: dir={safe_consensus.direction}, conf={safe_consensus.confidence:.2f}, dissent={safe_consensus.dissent_ratio:.2f}")

        return safe_consensus

    async def _validate_risk(self, consensus: SwarmConsensus, context: Dict[str, Any]) -> SwarmConsensus:
        """Mandatory risk validation step"""
        risk_managers = self.registry.get_agents_by_role(AgentRole.SAFETY)
        if not risk_managers:
            logger.warning("No risk managers found in swarm controller! Defaulting to cautious confidence.")
            # Fallback: Apply a dynamic penalty if no safety agents are available
            safety_penalty = self.config.get('missing_safety_penalty', 0.5)
            consensus.confidence *= safety_penalty
            return consensus

        for rm in risk_managers:
            try:
                risk_result = await rm.execute({
                    'operation': 'validate_swarm',
                    'consensus': consensus.to_dict(),
                    'context': context
                })

                if not risk_result.get('is_safe', False):
                    logger.warning(f"Risk Manager {rm.agent_id} flagged swarm decision as unsafe!")
                    consensus.direction = 0.0
                    consensus.confidence = 0.0
                    break
            except Exception as e:
                logger.error(f"Error during risk validation: {e}")

        return consensus

    def _identify_dominant_factors(self, signals: List[SwarmSignal]) -> List[str]:
        """Identify which signals contributed most to the decision"""
        sorted_signals = sorted(
            signals,
            key=lambda s: s.confidence,
            reverse=True
        )
        return [s.source_id for s in sorted_signals[:3]]

    async def record_outcome(self, consensus: SwarmConsensus, outcome: float, market_context: Dict[str, Any]):
        """Record the actual outcome and update agent memory"""
        for signal in consensus.contributing_signals:
            accuracy = 1.0 if np.sign(signal.direction) == np.sign(outcome) else 0.0
            reward = accuracy * abs(outcome)

            from .memory import AgentExperience
            experience = AgentExperience(
                agent_id=signal.source_id,
                prediction=signal.direction,
                market_context=market_context,
                result=outcome,
                accuracy=accuracy,
                reward=reward
            )
            self.performance_memory.record_experience(experience)

        # Trigger evolution check periodically
        if len(self.performance_memory.experiences) % 100 == 0:
            await self.evolution_layer.evolve()

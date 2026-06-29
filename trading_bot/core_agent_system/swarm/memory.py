import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class AgentExperience:
    agent_id: str
    prediction: float
    market_context: Dict[str, Any]
    result: float
    accuracy: float
    reward: float
    timestamp: datetime = field(default_factory=datetime.now)

class AgentPerformanceMemory:
    """
    Stores and analyzes performance of all swarm agents.
    """
    def __init__(self, capacity: int = 10000):
        self.experiences: List[AgentExperience] = []
        self.agent_stats: Dict[str, Dict[str, Any]] = {}
        self.capacity = capacity

    def record_experience(self, experience: AgentExperience):
        self.experiences.append(experience)
        if len(self.experiences) > self.capacity:
            self.experiences.pop(0)

        self._update_agent_stats(experience)

    def _update_agent_stats(self, exp: AgentExperience):
        if exp.agent_id not in self.agent_stats:
            self.agent_stats[exp.agent_id] = {
                'total_predictions': 0,
                'avg_accuracy': 0.0,
                'avg_reward': 0.0,
                'last_active': exp.timestamp,
                'context_performance': {} # regime -> accuracy
            }

        stats = self.agent_stats[exp.agent_id]
        n = stats['total_predictions']
        stats['avg_accuracy'] = (stats['avg_accuracy'] * n + exp.accuracy) / (n + 1)
        stats['avg_reward'] = (stats['avg_reward'] * n + exp.reward) / (n + 1)
        stats['total_predictions'] += 1
        stats['last_active'] = exp.timestamp

        # Update context performance
        regime = exp.market_context.get('regime', 'unknown')
        if regime not in stats['context_performance']:
            stats['context_performance'][regime] = []
        stats['context_performance'][regime].append(exp.accuracy)
        if len(stats['context_performance'][regime]) > 100:
            stats['context_performance'][regime].pop(0)

    def get_agent_weight(self, agent_id: str, context: Dict[str, Any]) -> float:
        """
        Calculate context-aware weight for an agent based on historical accuracy.
        """
        if agent_id not in self.agent_stats:
            return 1.0 # Default weight for new agents

        stats = self.agent_stats[agent_id]
        regime = context.get('regime', 'unknown')

        context_accuracy = 0.5
        if regime in stats['context_performance'] and stats['context_performance'][regime]:
            context_accuracy = np.mean(stats['context_performance'][regime])

        # Combine global and context accuracy
        weight = 0.7 * context_accuracy + 0.3 * stats['avg_accuracy']

        # Boost for recent activity and consistency
        return max(0.1, weight * 2.0)

class EvolutionLayer:
    """
    Manages the lifecycle and evolution of agents in the swarm.
    """
    def __init__(self, memory: AgentPerformanceMemory):
        self.memory = memory
        self.survival_threshold = 0.4
        self.mutation_rate = 0.1

    async def evolve(self) -> Dict[str, Any]:
        """
        Perform evolution cycle:
        - Prune underperforming agents
        - Select top performers for replication/mutation
        """
        results = {'pruned': [], 'mutated': [], 'new_candidates': []}

        for agent_id, stats in list(self.memory.agent_stats.items()):
            # Only evolve agents with enough history
            if stats['total_predictions'] < 20:
                continue

            # Pruning
            if stats['avg_accuracy'] < self.survival_threshold:
                results['pruned'].append(agent_id)
                logger.info(f"Agent {agent_id} marked for pruning (Accuracy: {stats['avg_accuracy']:.2f})")

        return results

    def suggest_mutations(self, top_agents: List[str]) -> List[Dict[str, Any]]:
        """Suggest mutations for top performing agents"""
        # Implementation for parameter mutation
        return []

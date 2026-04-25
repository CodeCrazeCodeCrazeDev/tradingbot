"""
Multi-Agent Collaboration - Collective Intelligence
====================================================

Implements multi-agent systems:
- Agent Swarm: Specialized research agents
- Debate Protocol: Agents debate findings
- Consensus Mechanism: Reach agreement on discoveries
- Knowledge Sharing: Share insights between agents
- Collective Intelligence: Emergent group intelligence
"""

from .agent_swarm import AgentSwarm, ResearchAgent, AgentRole
from .debate_protocol import DebateProtocol, Debate, Argument, DebateOutcome
from .consensus_mechanism import ConsensusMechanism, ConsensusResult, VotingMethod
from .collective_intelligence import CollectiveIntelligence, SwarmDecision

__all__ = [
    "AgentSwarm",
    "ResearchAgent",
    "AgentRole",
    "DebateProtocol",
    "Debate",
    "Argument",
    "DebateOutcome",
    "ConsensusMechanism",
    "ConsensusResult",
    "VotingMethod",
    "CollectiveIntelligence",
    "SwarmDecision",
]

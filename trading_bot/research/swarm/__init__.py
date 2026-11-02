"""
Research Swarm sub-package.

Parallel research capacity for the Institutional Research Lab: a pool of
agents, each holding a private lab instance, executing research programs
concurrently with optional cross-agent replication and adjudication.
"""

from .agents import (
    ResearchAgentRole,
    ResearchTask,
    SwarmFinding,
    SwarmResearchAgent,
)
from .swarm import (
    ProgramVerdict,
    ResearchSwarm,
    SwarmProceedings,
)

__all__ = [
    "ResearchAgentRole",
    "ResearchTask",
    "SwarmFinding",
    "SwarmResearchAgent",
    "ProgramVerdict",
    "ResearchSwarm",
    "SwarmProceedings",
]

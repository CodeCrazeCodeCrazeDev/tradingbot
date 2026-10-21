"""CSC advisory swarm-intelligence package.

The swarm deliberates; the CSC decides. Nothing in this package can
authorize, size, veto, or execute a trade — consensus output is evidence.
"""
from .models import (EmergentSignals, MethodResult, SwarmConsensus,
                     SwarmVote, VotingMethod)
from .service import SwarmIntelligenceService, domain_for
from .knowledge import SwarmKnowledgeBase

__all__ = [
    "EmergentSignals", "MethodResult", "SwarmConsensus", "SwarmVote",
    "VotingMethod", "SwarmIntelligenceService", "SwarmKnowledgeBase",
    "domain_for",
]

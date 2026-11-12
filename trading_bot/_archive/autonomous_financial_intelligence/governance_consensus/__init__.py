"""
Governance Consensus Layer (GCL)

Distributed decision-making with stake-weighted voting.
Implements Byzantine fault-tolerant consensus mechanisms.
"""

from .consensus_engine import ConsensusEngine, ConsensusRound, ConsensusResult, ConsensusType
from .governance_token import GovernanceToken, TokenHolder, VotingPower
from .voting_contracts import VotingContract, Proposal, Vote, VoteType
from .dispute_resolution import DisputeResolution, Dispute, DisputeVerdict, DisputeStatus

__all__ = [
    'ConsensusEngine',
    'ConsensusRound',
    'ConsensusResult',
    'ConsensusType',
    'GovernanceToken',
    'TokenHolder',
    'VotingPower',
    'VotingContract',
    'Proposal',
    'Vote',
    'VoteType',
    'DisputeResolution',
    'Dispute',
    'DisputeVerdict',
    'DisputeStatus',
]

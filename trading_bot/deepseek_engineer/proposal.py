"""Proposal system — tracked change proposals with an approval workflow."""

import itertools
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ProposalType(Enum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    CONFIG = "config"


class ProposalStatus(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


@dataclass
class Proposal:
    proposal_id: str
    title: str
    description: str
    proposal_type: ProposalType
    status: ProposalStatus = ProposalStatus.DRAFT


class ProposalSystem:
    """Create and track change proposals; nothing applies without approval."""

    _counter = itertools.count(1)

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.proposals = {}

    def create_proposal(self, title: str, description: str,
                        proposal_type: ProposalType, **kwargs) -> Proposal:
        proposal = Proposal(
            proposal_id=f"PROP-{next(self._counter):04d}",
            title=title,
            description=description,
            proposal_type=proposal_type,
        )
        self.proposals[proposal.proposal_id] = proposal
        return proposal

    def submit_for_approval(self, proposal: Proposal):
        proposal.status = ProposalStatus.PENDING_REVIEW

    def approve_proposal(self, proposal_id: str):
        self.proposals[proposal_id].status = ProposalStatus.APPROVED

    def reject_proposal(self, proposal_id: str):
        self.proposals[proposal_id].status = ProposalStatus.REJECTED

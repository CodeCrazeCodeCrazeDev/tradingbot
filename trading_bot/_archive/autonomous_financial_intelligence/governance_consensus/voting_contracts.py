"""
Voting Contracts System

Smart contracts for decision governance with proposal management.
Implements time-locked execution and multi-signature requirements.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ProposalType(Enum):
    """Types of governance proposals."""
    PARAMETER_CHANGE = "parameter_change"
    CAPITAL_DEPLOYMENT = "capital_deployment"
    STRATEGY_APPROVAL = "strategy_approval"
    AGENT_AUTHORIZATION = "agent_authorization"
    EMERGENCY_ACTION = "emergency_action"
    UPGRADE = "upgrade"
    TREASURY_ALLOCATION = "treasury_allocation"
    SLASHING = "slashing"


class ProposalStatus(Enum):
    """Status of a proposal."""
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    VETOED = "vetoed"


class VoteType(Enum):
    """Types of votes."""
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


@dataclass
class Vote:
    """A vote on a proposal."""
    vote_id: str
    proposal_id: str
    voter_id: str
    vote_type: VoteType
    voting_power: float
    timestamp: datetime
    reason: Optional[str] = None
    signature: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'vote_id': self.vote_id,
            'proposal_id': self.proposal_id,
            'voter_id': self.voter_id,
            'vote_type': self.vote_type.value,
            'voting_power': self.voting_power,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason,
            'signature': self.signature,
        }


@dataclass
class Proposal:
    """A governance proposal."""
    proposal_id: str
    proposal_type: ProposalType
    title: str
    description: str
    proposer_id: str
    status: ProposalStatus
    created_at: datetime
    voting_starts: datetime
    voting_ends: datetime
    execution_delay: int
    execution_deadline: Optional[datetime]
    parameters: Dict[str, Any]
    votes_for: float = 0.0
    votes_against: float = 0.0
    votes_abstain: float = 0.0
    total_votes: int = 0
    quorum_required: float = 0.0
    approval_threshold: float = 0.0
    votes: List[Vote] = field(default_factory=list)
    execution_tx: Optional[str] = None
    veto_count: int = 0
    required_signatures: int = 1
    collected_signatures: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'proposal_id': self.proposal_id,
            'proposal_type': self.proposal_type.value,
            'title': self.title,
            'description': self.description,
            'proposer_id': self.proposer_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'voting_starts': self.voting_starts.isoformat(),
            'voting_ends': self.voting_ends.isoformat(),
            'execution_delay': self.execution_delay,
            'execution_deadline': self.execution_deadline.isoformat() if self.execution_deadline else None,
            'parameters': self.parameters,
            'votes_for': self.votes_for,
            'votes_against': self.votes_against,
            'votes_abstain': self.votes_abstain,
            'total_votes': self.total_votes,
            'quorum_required': self.quorum_required,
            'approval_threshold': self.approval_threshold,
            'votes': [v.to_dict() for v in self.votes],
            'execution_tx': self.execution_tx,
            'veto_count': self.veto_count,
            'required_signatures': self.required_signatures,
            'collected_signatures': self.collected_signatures,
        }


@dataclass
class VotingContract:
    """A voting contract with specific rules."""
    contract_id: str
    name: str
    proposal_types: List[ProposalType]
    quorum_percent: float
    approval_threshold: float
    voting_period_hours: int
    execution_delay_hours: int
    veto_threshold: int
    required_signatures: int
    is_active: bool
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'contract_id': self.contract_id,
            'name': self.name,
            'proposal_types': [pt.value for pt in self.proposal_types],
            'quorum_percent': self.quorum_percent,
            'approval_threshold': self.approval_threshold,
            'voting_period_hours': self.voting_period_hours,
            'execution_delay_hours': self.execution_delay_hours,
            'veto_threshold': self.veto_threshold,
            'required_signatures': self.required_signatures,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }


class VotingContractManager:
    """
    Manages voting contracts and proposals.
    
    Provides:
    - Proposal creation and management
    - Vote casting and tallying
    - Time-locked execution
    - Multi-signature requirements
    - Veto mechanisms
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'voting_contracts_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._contracts: Dict[str, VotingContract] = {}
        self._proposals: Dict[str, Proposal] = {}
        self._voter_registry: Dict[str, Dict[str, Any]] = {}
        
        self._execution_queue: List[Proposal] = []
        self._veto_holders: Set[str] = set()
        
        self._initialize_default_contracts()
        
        logger.info("✅ Voting Contract Manager initialized")
    
    def _initialize_default_contracts(self):
        """Initialize default voting contracts."""
        default_contracts = [
            VotingContract(
                contract_id="VC-STANDARD",
                name="Standard Governance",
                proposal_types=[
                    ProposalType.PARAMETER_CHANGE,
                    ProposalType.STRATEGY_APPROVAL,
                    ProposalType.AGENT_AUTHORIZATION,
                ],
                quorum_percent=33.0,
                approval_threshold=50.0,
                voting_period_hours=24,
                execution_delay_hours=6,
                veto_threshold=3,
                required_signatures=1,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            ),
            VotingContract(
                contract_id="VC-CAPITAL",
                name="Capital Deployment",
                proposal_types=[
                    ProposalType.CAPITAL_DEPLOYMENT,
                    ProposalType.TREASURY_ALLOCATION,
                ],
                quorum_percent=50.0,
                approval_threshold=67.0,
                voting_period_hours=48,
                execution_delay_hours=24,
                veto_threshold=2,
                required_signatures=2,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            ),
            VotingContract(
                contract_id="VC-EMERGENCY",
                name="Emergency Actions",
                proposal_types=[
                    ProposalType.EMERGENCY_ACTION,
                ],
                quorum_percent=25.0,
                approval_threshold=75.0,
                voting_period_hours=4,
                execution_delay_hours=1,
                veto_threshold=1,
                required_signatures=3,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            ),
            VotingContract(
                contract_id="VC-UPGRADE",
                name="System Upgrades",
                proposal_types=[
                    ProposalType.UPGRADE,
                ],
                quorum_percent=60.0,
                approval_threshold=80.0,
                voting_period_hours=72,
                execution_delay_hours=48,
                veto_threshold=2,
                required_signatures=3,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            ),
            VotingContract(
                contract_id="VC-SLASHING",
                name="Slashing Proposals",
                proposal_types=[
                    ProposalType.SLASHING,
                ],
                quorum_percent=40.0,
                approval_threshold=67.0,
                voting_period_hours=24,
                execution_delay_hours=12,
                veto_threshold=2,
                required_signatures=2,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            ),
        ]
        
        for contract in default_contracts:
            self._contracts[contract.contract_id] = contract
    
    async def register_voter(
        self,
        voter_id: str,
        voting_power: float,
        is_veto_holder: bool = False,
    ):
        """
        Register a voter in the system.
        
        Args:
            voter_id: Unique voter identifier
            voting_power: Voter's voting power
            is_veto_holder: Whether voter has veto rights
        """
        self._voter_registry[voter_id] = {
            'voter_id': voter_id,
            'voting_power': voting_power,
            'is_veto_holder': is_veto_holder,
            'registered_at': datetime.now(timezone.utc),
        }
        
        if is_veto_holder:
            self._veto_holders.add(voter_id)
    
    def update_voting_power(self, voter_id: str, voting_power: float):
        """Update a voter's voting power."""
        if voter_id in self._voter_registry:
            self._voter_registry[voter_id]['voting_power'] = voting_power
    
    async def create_proposal(
        self,
        proposal_type: ProposalType,
        title: str,
        description: str,
        proposer_id: str,
        parameters: Dict[str, Any],
        contract_id: Optional[str] = None,
    ) -> Optional[Proposal]:
        """
        Create a new governance proposal.
        
        Args:
            proposal_type: Type of proposal
            title: Proposal title
            description: Detailed description
            proposer_id: ID of the proposer
            parameters: Proposal parameters
            contract_id: Optional specific contract to use
        
        Returns:
            Proposal if successful
        """
        contract = None
        if contract_id:
            contract = self._contracts.get(contract_id)
        else:
            for c in self._contracts.values():
                if proposal_type in c.proposal_types and c.is_active:
                    contract = c
                    break
        
        if not contract:
            logger.error(f"No active contract found for proposal type {proposal_type.value}")
            return None
        
        proposal_id = f"PROP-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        voting_starts = now
        voting_ends = now + timedelta(hours=contract.voting_period_hours)
        execution_deadline = voting_ends + timedelta(hours=contract.execution_delay_hours + 24)
        
        total_voting_power = sum(
            v['voting_power'] for v in self._voter_registry.values()
        )
        quorum_required = total_voting_power * (contract.quorum_percent / 100)
        
        proposal = Proposal(
            proposal_id=proposal_id,
            proposal_type=proposal_type,
            title=title,
            description=description,
            proposer_id=proposer_id,
            status=ProposalStatus.ACTIVE,
            created_at=now,
            voting_starts=voting_starts,
            voting_ends=voting_ends,
            execution_delay=contract.execution_delay_hours,
            execution_deadline=execution_deadline,
            parameters=parameters,
            quorum_required=quorum_required,
            approval_threshold=contract.approval_threshold,
            required_signatures=contract.required_signatures,
        )
        
        self._proposals[proposal_id] = proposal
        await self._persist_proposal(proposal)
        
        logger.info(f"Created proposal {proposal_id}: {title}")
        
        return proposal
    
    async def cast_vote(
        self,
        proposal_id: str,
        voter_id: str,
        vote_type: VoteType,
        reason: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Cast a vote on a proposal.
        
        Args:
            proposal_id: ID of the proposal
            voter_id: ID of the voter
            vote_type: Type of vote
            reason: Optional reason for vote
        
        Returns:
            Tuple of (success, message)
        """
        if proposal_id not in self._proposals:
            return False, "Proposal not found"
        
        proposal = self._proposals[proposal_id]
        
        if proposal.status != ProposalStatus.ACTIVE:
            return False, f"Proposal is not active (status: {proposal.status.value})"
        
        now = datetime.now(timezone.utc)
        if now < proposal.voting_starts:
            return False, "Voting has not started yet"
        
        if now > proposal.voting_ends:
            await self._finalize_proposal(proposal)
            return False, "Voting period has ended"
        
        if voter_id not in self._voter_registry:
            return False, "Voter not registered"
        
        existing_vote = next(
            (v for v in proposal.votes if v.voter_id == voter_id),
            None
        )
        if existing_vote:
            return False, "Voter has already voted on this proposal"
        
        voter = self._voter_registry[voter_id]
        voting_power = voter['voting_power']
        
        vote_id = f"VOTE-{uuid.uuid4().hex[:12]}"
        vote_data = f"{vote_id}:{proposal_id}:{voter_id}:{vote_type.value}:{now.isoformat()}"
        signature = hashlib.sha256(vote_data.encode()).hexdigest()
        
        vote = Vote(
            vote_id=vote_id,
            proposal_id=proposal_id,
            voter_id=voter_id,
            vote_type=vote_type,
            voting_power=voting_power,
            timestamp=now,
            reason=reason,
            signature=signature,
        )
        
        proposal.votes.append(vote)
        proposal.total_votes += 1
        
        if vote_type == VoteType.FOR:
            proposal.votes_for += voting_power
        elif vote_type == VoteType.AGAINST:
            proposal.votes_against += voting_power
        else:
            proposal.votes_abstain += voting_power
        
        await self._persist_proposal(proposal)
        
        logger.debug(f"Vote cast on proposal {proposal_id} by {voter_id}: {vote_type.value}")
        
        return True, "Vote cast successfully"
    
    async def veto_proposal(
        self,
        proposal_id: str,
        veto_holder_id: str,
        reason: str,
    ) -> Tuple[bool, str]:
        """
        Veto a proposal (requires veto holder rights).
        
        Args:
            proposal_id: ID of the proposal
            veto_holder_id: ID of the veto holder
            reason: Reason for veto
        
        Returns:
            Tuple of (success, message)
        """
        if proposal_id not in self._proposals:
            return False, "Proposal not found"
        
        if veto_holder_id not in self._veto_holders:
            return False, "Not a veto holder"
        
        proposal = self._proposals[proposal_id]
        
        if proposal.status not in [ProposalStatus.ACTIVE, ProposalStatus.PASSED]:
            return False, "Proposal cannot be vetoed in current status"
        
        proposal.veto_count += 1
        
        contract = self._get_contract_for_proposal(proposal)
        if contract and proposal.veto_count >= contract.veto_threshold:
            proposal.status = ProposalStatus.VETOED
            logger.warning(f"Proposal {proposal_id} vetoed: {reason}")
        
        await self._persist_proposal(proposal)
        
        return True, f"Veto recorded (count: {proposal.veto_count})"
    
    async def add_signature(
        self,
        proposal_id: str,
        signer_id: str,
    ) -> Tuple[bool, str]:
        """
        Add a signature to a passed proposal for execution.
        
        Args:
            proposal_id: ID of the proposal
            signer_id: ID of the signer
        
        Returns:
            Tuple of (success, message)
        """
        if proposal_id not in self._proposals:
            return False, "Proposal not found"
        
        proposal = self._proposals[proposal_id]
        
        if proposal.status != ProposalStatus.PASSED:
            return False, "Proposal must be passed to collect signatures"
        
        if signer_id in proposal.collected_signatures:
            return False, "Already signed"
        
        proposal.collected_signatures.append(signer_id)
        
        if len(proposal.collected_signatures) >= proposal.required_signatures:
            self._execution_queue.append(proposal)
            logger.info(f"Proposal {proposal_id} ready for execution "
                       f"({len(proposal.collected_signatures)} signatures)")
        
        await self._persist_proposal(proposal)
        
        return True, f"Signature added ({len(proposal.collected_signatures)}/{proposal.required_signatures})"
    
    async def _finalize_proposal(self, proposal: Proposal):
        """Finalize voting on a proposal."""
        total_voted = proposal.votes_for + proposal.votes_against
        
        quorum_met = (proposal.votes_for + proposal.votes_against + proposal.votes_abstain) >= proposal.quorum_required
        
        if total_voted == 0:
            approval_rate = 0
        else:
            approval_rate = (proposal.votes_for / total_voted) * 100
        
        if quorum_met and approval_rate >= proposal.approval_threshold:
            proposal.status = ProposalStatus.PASSED
            logger.info(f"Proposal {proposal.proposal_id} PASSED "
                       f"(approval: {approval_rate:.1f}%)")
        else:
            proposal.status = ProposalStatus.REJECTED
            reason = "quorum not met" if not quorum_met else f"approval {approval_rate:.1f}% < {proposal.approval_threshold}%"
            logger.info(f"Proposal {proposal.proposal_id} REJECTED ({reason})")
        
        await self._persist_proposal(proposal)
    
    async def process_execution_queue(self) -> List[Dict[str, Any]]:
        """
        Process proposals ready for execution.
        
        Returns:
            List of executed proposals
        """
        now = datetime.now(timezone.utc)
        executed = []
        remaining = []
        
        for proposal in self._execution_queue:
            execution_time = proposal.voting_ends + timedelta(hours=proposal.execution_delay)
            
            if now >= execution_time:
                if proposal.execution_deadline and now > proposal.execution_deadline:
                    proposal.status = ProposalStatus.EXPIRED
                    logger.warning(f"Proposal {proposal.proposal_id} expired")
                elif proposal.status == ProposalStatus.VETOED:
                    logger.warning(f"Proposal {proposal.proposal_id} was vetoed, skipping execution")
                else:
                    proposal.status = ProposalStatus.EXECUTED
                    proposal.execution_tx = f"EXEC-{uuid.uuid4().hex[:12]}"
                    executed.append({
                        'proposal_id': proposal.proposal_id,
                        'proposal_type': proposal.proposal_type.value,
                        'parameters': proposal.parameters,
                        'execution_tx': proposal.execution_tx,
                    })
                    logger.info(f"Executed proposal {proposal.proposal_id}")
                
                await self._persist_proposal(proposal)
            else:
                remaining.append(proposal)
        
        self._execution_queue = remaining
        
        return executed
    
    def _get_contract_for_proposal(self, proposal: Proposal) -> Optional[VotingContract]:
        """Get the contract governing a proposal."""
        for contract in self._contracts.values():
            if proposal.proposal_type in contract.proposal_types:
                return contract
        return None
    
    async def cancel_proposal(
        self,
        proposal_id: str,
        canceller_id: str,
    ) -> Tuple[bool, str]:
        """
        Cancel a proposal (only by proposer before voting ends).
        
        Args:
            proposal_id: ID of the proposal
            canceller_id: ID of the canceller
        
        Returns:
            Tuple of (success, message)
        """
        if proposal_id not in self._proposals:
            return False, "Proposal not found"
        
        proposal = self._proposals[proposal_id]
        
        if proposal.proposer_id != canceller_id:
            return False, "Only proposer can cancel"
        
        if proposal.status != ProposalStatus.ACTIVE:
            return False, "Can only cancel active proposals"
        
        proposal.status = ProposalStatus.CANCELLED
        await self._persist_proposal(proposal)
        
        return True, "Proposal cancelled"
    
    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get a proposal by ID."""
        return self._proposals.get(proposal_id)
    
    def get_active_proposals(self) -> List[Proposal]:
        """Get all active proposals."""
        return [p for p in self._proposals.values() if p.status == ProposalStatus.ACTIVE]
    
    def get_contract(self, contract_id: str) -> Optional[VotingContract]:
        """Get a voting contract by ID."""
        return self._contracts.get(contract_id)
    
    async def _persist_proposal(self, proposal: Proposal):
        """Persist proposal to storage."""
        proposal_file = self.storage_path / 'proposals' / f"{proposal.proposal_id}.json"
        proposal_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(proposal_file, 'w') as f:
            json.dump(proposal.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get voting contract statistics."""
        status_counts = {}
        type_counts = {}
        
        for proposal in self._proposals.values():
            status_counts[proposal.status.value] = status_counts.get(proposal.status.value, 0) + 1
            type_counts[proposal.proposal_type.value] = type_counts.get(proposal.proposal_type.value, 0) + 1
        
        return {
            'total_contracts': len(self._contracts),
            'active_contracts': len([c for c in self._contracts.values() if c.is_active]),
            'total_proposals': len(self._proposals),
            'proposals_by_status': status_counts,
            'proposals_by_type': type_counts,
            'registered_voters': len(self._voter_registry),
            'veto_holders': len(self._veto_holders),
            'pending_executions': len(self._execution_queue),
        }

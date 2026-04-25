"""
Consensus Engine

Byzantine fault-tolerant consensus mechanism for distributed decision-making.
Implements stake-weighted voting with N-of-M agreement requirements.
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


class ConsensusType(Enum):
    """Types of consensus mechanisms."""
    SIMPLE_MAJORITY = "simple_majority"
    SUPER_MAJORITY = "super_majority"
    UNANIMOUS = "unanimous"
    STAKE_WEIGHTED = "stake_weighted"
    QUADRATIC = "quadratic"
    CONVICTION = "conviction"


class ConsensusPhase(Enum):
    """Phases of consensus process."""
    PROPOSAL = "proposal"
    VOTING = "voting"
    COMMIT = "commit"
    FINALIZATION = "finalization"
    COMPLETED = "completed"
    FAILED = "failed"


class VoteChoice(Enum):
    """Possible vote choices."""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class ConsensusVote:
    """A vote in a consensus round."""
    vote_id: str
    round_id: str
    voter_id: str
    choice: VoteChoice
    stake_weight: float
    reasoning: Optional[str]
    timestamp: datetime
    signature: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'vote_id': self.vote_id,
            'round_id': self.round_id,
            'voter_id': self.voter_id,
            'choice': self.choice.value,
            'stake_weight': self.stake_weight,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat(),
            'signature': self.signature,
        }


@dataclass
class ConsensusRound:
    """A round of consensus voting."""
    round_id: str
    proposal_id: str
    proposal_content: Dict[str, Any]
    consensus_type: ConsensusType
    phase: ConsensusPhase
    required_threshold: float
    minimum_participation: float
    created_at: datetime
    deadline: datetime
    votes: List[ConsensusVote] = field(default_factory=list)
    total_stake: float = 0.0
    participating_stake: float = 0.0
    approval_stake: float = 0.0
    rejection_stake: float = 0.0
    result: Optional[str] = None
    finalized_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'round_id': self.round_id,
            'proposal_id': self.proposal_id,
            'proposal_content': self.proposal_content,
            'consensus_type': self.consensus_type.value,
            'phase': self.phase.value,
            'required_threshold': self.required_threshold,
            'minimum_participation': self.minimum_participation,
            'created_at': self.created_at.isoformat(),
            'deadline': self.deadline.isoformat(),
            'votes': [v.to_dict() for v in self.votes],
            'total_stake': self.total_stake,
            'participating_stake': self.participating_stake,
            'approval_stake': self.approval_stake,
            'rejection_stake': self.rejection_stake,
            'result': self.result,
            'finalized_at': self.finalized_at.isoformat() if self.finalized_at else None,
        }


@dataclass
class ConsensusResult:
    """Result of a consensus round."""
    round_id: str
    proposal_id: str
    is_approved: bool
    approval_rate: float
    participation_rate: float
    total_votes: int
    approve_votes: int
    reject_votes: int
    abstain_votes: int
    consensus_type: ConsensusType
    finalized_at: datetime
    execution_allowed: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'round_id': self.round_id,
            'proposal_id': self.proposal_id,
            'is_approved': self.is_approved,
            'approval_rate': self.approval_rate,
            'participation_rate': self.participation_rate,
            'total_votes': self.total_votes,
            'approve_votes': self.approve_votes,
            'reject_votes': self.reject_votes,
            'abstain_votes': self.abstain_votes,
            'consensus_type': self.consensus_type.value,
            'finalized_at': self.finalized_at.isoformat(),
            'execution_allowed': self.execution_allowed,
        }


@dataclass
class ConsensusParticipant:
    """A participant in consensus."""
    participant_id: str
    name: str
    stake: float
    voting_power: float
    reputation: float
    is_active: bool
    total_votes: int = 0
    correct_votes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'participant_id': self.participant_id,
            'name': self.name,
            'stake': self.stake,
            'voting_power': self.voting_power,
            'reputation': self.reputation,
            'is_active': self.is_active,
            'total_votes': self.total_votes,
            'correct_votes': self.correct_votes,
        }


class ConsensusEngine:
    """
    Byzantine fault-tolerant consensus engine.
    
    Provides:
    - Multiple consensus mechanisms
    - Stake-weighted voting
    - Quorum requirements
    - Time-locked execution
    - Circuit breakers
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'consensus_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._rounds: Dict[str, ConsensusRound] = {}
        self._participants: Dict[str, ConsensusParticipant] = {}
        self._results: Dict[str, ConsensusResult] = {}
        
        self._consensus_config = {
            'simple_majority_threshold': 0.50,
            'super_majority_threshold': 0.67,
            'unanimous_threshold': 1.0,
            'minimum_participation': 0.33,
            'default_voting_period_seconds': 300,
            'time_lock_seconds': 60,
            'circuit_breaker_threshold': 0.9,
        }
        
        self._circuit_breaker_active = False
        self._pending_executions: List[Dict[str, Any]] = []
        
        logger.info("✅ Consensus Engine initialized")
    
    async def register_participant(
        self,
        participant_id: str,
        name: str,
        stake: float,
        reputation: float = 1.0,
    ) -> ConsensusParticipant:
        """
        Register a participant in the consensus system.
        
        Args:
            participant_id: Unique identifier
            name: Participant name
            stake: Stake amount
            reputation: Initial reputation score
        
        Returns:
            ConsensusParticipant
        """
        voting_power = self._calculate_voting_power(stake, reputation)
        
        participant = ConsensusParticipant(
            participant_id=participant_id,
            name=name,
            stake=stake,
            voting_power=voting_power,
            reputation=reputation,
            is_active=True,
        )
        
        self._participants[participant_id] = participant
        
        logger.info(f"Registered consensus participant: {name} (stake: {stake})")
        
        return participant
    
    def _calculate_voting_power(self, stake: float, reputation: float) -> float:
        """Calculate voting power from stake and reputation."""
        base_power = stake ** 0.5
        reputation_multiplier = 0.5 + (reputation * 0.5)
        return base_power * reputation_multiplier
    
    async def create_consensus_round(
        self,
        proposal_id: str,
        proposal_content: Dict[str, Any],
        consensus_type: ConsensusType = ConsensusType.STAKE_WEIGHTED,
        voting_period_seconds: Optional[int] = None,
        custom_threshold: Optional[float] = None,
    ) -> ConsensusRound:
        """
        Create a new consensus round for a proposal.
        
        Args:
            proposal_id: ID of the proposal
            proposal_content: Content being voted on
            consensus_type: Type of consensus mechanism
            voting_period_seconds: Duration of voting period
            custom_threshold: Custom approval threshold
        
        Returns:
            ConsensusRound
        """
        round_id = f"CNS-{uuid.uuid4().hex[:12]}"
        
        if consensus_type == ConsensusType.SIMPLE_MAJORITY:
            threshold = self._consensus_config['simple_majority_threshold']
        elif consensus_type == ConsensusType.SUPER_MAJORITY:
            threshold = self._consensus_config['super_majority_threshold']
        elif consensus_type == ConsensusType.UNANIMOUS:
            threshold = self._consensus_config['unanimous_threshold']
        else:
            threshold = custom_threshold or self._consensus_config['super_majority_threshold']
        
        voting_period = voting_period_seconds or self._consensus_config['default_voting_period_seconds']
        
        total_stake = sum(p.stake for p in self._participants.values() if p.is_active)
        
        round = ConsensusRound(
            round_id=round_id,
            proposal_id=proposal_id,
            proposal_content=proposal_content,
            consensus_type=consensus_type,
            phase=ConsensusPhase.VOTING,
            required_threshold=threshold,
            minimum_participation=self._consensus_config['minimum_participation'],
            created_at=datetime.now(timezone.utc),
            deadline=datetime.now(timezone.utc) + timedelta(seconds=voting_period),
            total_stake=total_stake,
        )
        
        self._rounds[round_id] = round
        await self._persist_round(round)
        
        logger.info(f"Created consensus round {round_id} for proposal {proposal_id}")
        
        return round
    
    async def submit_vote(
        self,
        round_id: str,
        voter_id: str,
        choice: VoteChoice,
        reasoning: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Submit a vote in a consensus round.
        
        Args:
            round_id: ID of the consensus round
            voter_id: ID of the voter
            choice: Vote choice
            reasoning: Optional reasoning for vote
        
        Returns:
            Tuple of (success, message)
        """
        if round_id not in self._rounds:
            return False, "Consensus round not found"
        
        round = self._rounds[round_id]
        
        if round.phase != ConsensusPhase.VOTING:
            return False, f"Round is not in voting phase (current: {round.phase.value})"
        
        if datetime.now(timezone.utc) > round.deadline:
            await self._finalize_round(round)
            return False, "Voting period has ended"
        
        if voter_id not in self._participants:
            return False, "Voter not registered as participant"
        
        participant = self._participants[voter_id]
        
        if not participant.is_active:
            return False, "Voter is not active"
        
        existing_vote = next((v for v in round.votes if v.voter_id == voter_id), None)
        if existing_vote:
            return False, "Voter has already voted in this round"
        
        vote_id = f"VOT-{uuid.uuid4().hex[:12]}"
        
        vote_data = f"{vote_id}:{round_id}:{voter_id}:{choice.value}:{datetime.now(timezone.utc).isoformat()}"
        signature = hashlib.sha256(vote_data.encode()).hexdigest()
        
        if round.consensus_type == ConsensusType.QUADRATIC:
            stake_weight = participant.stake ** 0.5
        else:
            stake_weight = participant.voting_power
        
        vote = ConsensusVote(
            vote_id=vote_id,
            round_id=round_id,
            voter_id=voter_id,
            choice=choice,
            stake_weight=stake_weight,
            reasoning=reasoning,
            timestamp=datetime.now(timezone.utc),
            signature=signature,
        )
        
        round.votes.append(vote)
        round.participating_stake += participant.stake
        
        if choice == VoteChoice.APPROVE:
            round.approval_stake += stake_weight
        elif choice == VoteChoice.REJECT:
            round.rejection_stake += stake_weight
        
        participant.total_votes += 1
        
        await self._persist_round(round)
        
        if await self._check_early_finalization(round):
            await self._finalize_round(round)
        
        logger.debug(f"Vote {vote_id} submitted for round {round_id}")
        
        return True, "Vote submitted successfully"
    
    async def _check_early_finalization(self, round: ConsensusRound) -> bool:
        """Check if round can be finalized early."""
        if round.total_stake == 0:
            return False
        
        participation_rate = round.participating_stake / round.total_stake
        
        if participation_rate < round.minimum_participation:
            return False
        
        total_voting_power = round.approval_stake + round.rejection_stake
        if total_voting_power == 0:
            return False
        
        approval_rate = round.approval_stake / total_voting_power
        
        remaining_stake = round.total_stake - round.participating_stake
        max_possible_approval = (round.approval_stake + remaining_stake) / (total_voting_power + remaining_stake)
        min_possible_approval = round.approval_stake / (total_voting_power + remaining_stake)
        
        if min_possible_approval >= round.required_threshold:
            return True
        
        if max_possible_approval < round.required_threshold:
            return True
        
        return False
    
    async def _finalize_round(self, round: ConsensusRound) -> ConsensusResult:
        """Finalize a consensus round and determine result."""
        round.phase = ConsensusPhase.FINALIZATION
        
        if round.total_stake == 0:
            participation_rate = 0
        else:
            participation_rate = round.participating_stake / round.total_stake
        
        total_voting_power = round.approval_stake + round.rejection_stake
        if total_voting_power == 0:
            approval_rate = 0
        else:
            approval_rate = round.approval_stake / total_voting_power
        
        participation_met = participation_rate >= round.minimum_participation
        threshold_met = approval_rate >= round.required_threshold
        
        is_approved = participation_met and threshold_met
        
        approve_count = sum(1 for v in round.votes if v.choice == VoteChoice.APPROVE)
        reject_count = sum(1 for v in round.votes if v.choice == VoteChoice.REJECT)
        abstain_count = sum(1 for v in round.votes if v.choice == VoteChoice.ABSTAIN)
        
        result = ConsensusResult(
            round_id=round.round_id,
            proposal_id=round.proposal_id,
            is_approved=is_approved,
            approval_rate=approval_rate,
            participation_rate=participation_rate,
            total_votes=len(round.votes),
            approve_votes=approve_count,
            reject_votes=reject_count,
            abstain_votes=abstain_count,
            consensus_type=round.consensus_type,
            finalized_at=datetime.now(timezone.utc),
            execution_allowed=is_approved and not self._circuit_breaker_active,
        )
        
        round.result = "approved" if is_approved else "rejected"
        round.finalized_at = datetime.now(timezone.utc)
        round.phase = ConsensusPhase.COMPLETED
        
        self._results[round.round_id] = result
        
        for vote in round.votes:
            participant = self._participants.get(vote.voter_id)
            if participant:
                if (vote.choice == VoteChoice.APPROVE) == is_approved:
                    participant.correct_votes += 1
                    participant.reputation = min(1.0, participant.reputation + 0.01)
                else:
                    participant.reputation = max(0.1, participant.reputation - 0.005)
                
                participant.voting_power = self._calculate_voting_power(
                    participant.stake, participant.reputation
                )
        
        if is_approved:
            await self._schedule_execution(round, result)
        
        await self._persist_round(round)
        await self._persist_result(result)
        
        logger.info(f"Consensus round {round.round_id} finalized: {round.result} "
                   f"(approval: {approval_rate:.1%}, participation: {participation_rate:.1%})")
        
        return result
    
    async def _schedule_execution(self, round: ConsensusRound, result: ConsensusResult):
        """Schedule execution after time lock."""
        time_lock = self._consensus_config['time_lock_seconds']
        
        execution = {
            'round_id': round.round_id,
            'proposal_id': round.proposal_id,
            'proposal_content': round.proposal_content,
            'execute_at': datetime.now(timezone.utc) + timedelta(seconds=time_lock),
            'result': result.to_dict(),
        }
        
        self._pending_executions.append(execution)
        
        logger.info(f"Scheduled execution for round {round.round_id} "
                   f"after {time_lock}s time lock")
    
    async def process_pending_executions(self) -> List[Dict[str, Any]]:
        """Process executions that have passed their time lock."""
        now = datetime.now(timezone.utc)
        ready = []
        remaining = []
        
        for execution in self._pending_executions:
            if now >= execution['execute_at']:
                if not self._circuit_breaker_active:
                    ready.append(execution)
                else:
                    logger.warning(f"Execution blocked by circuit breaker: {execution['round_id']}")
            else:
                remaining.append(execution)
        
        self._pending_executions = remaining
        
        return ready
    
    async def activate_circuit_breaker(self, reason: str):
        """Activate circuit breaker to halt all executions."""
        self._circuit_breaker_active = True
        logger.critical(f"Circuit breaker activated: {reason}")
    
    async def deactivate_circuit_breaker(self):
        """Deactivate circuit breaker."""
        self._circuit_breaker_active = False
        logger.info("Circuit breaker deactivated")
    
    async def get_round_status(self, round_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a consensus round."""
        if round_id not in self._rounds:
            return None
        
        round = self._rounds[round_id]
        
        if round.phase == ConsensusPhase.VOTING and datetime.now(timezone.utc) > round.deadline:
            await self._finalize_round(round)
        
        total_voting_power = round.approval_stake + round.rejection_stake
        
        return {
            'round_id': round.round_id,
            'phase': round.phase.value,
            'proposal_id': round.proposal_id,
            'consensus_type': round.consensus_type.value,
            'required_threshold': round.required_threshold,
            'current_approval_rate': round.approval_stake / total_voting_power if total_voting_power > 0 else 0,
            'participation_rate': round.participating_stake / round.total_stake if round.total_stake > 0 else 0,
            'votes_cast': len(round.votes),
            'time_remaining': max(0, (round.deadline - datetime.now(timezone.utc)).total_seconds()),
            'result': round.result,
        }
    
    def get_participant(self, participant_id: str) -> Optional[ConsensusParticipant]:
        """Get a participant by ID."""
        return self._participants.get(participant_id)
    
    def get_result(self, round_id: str) -> Optional[ConsensusResult]:
        """Get result of a consensus round."""
        return self._results.get(round_id)
    
    async def _persist_round(self, round: ConsensusRound):
        """Persist consensus round to storage."""
        round_file = self.storage_path / 'rounds' / f"{round.round_id}.json"
        round_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(round_file, 'w') as f:
            json.dump(round.to_dict(), f, indent=2)
    
    async def _persist_result(self, result: ConsensusResult):
        """Persist consensus result to storage."""
        result_file = self.storage_path / 'results' / f"{result.round_id}.json"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get consensus engine statistics."""
        completed_rounds = [r for r in self._rounds.values() if r.phase == ConsensusPhase.COMPLETED]
        approved_rounds = [r for r in completed_rounds if r.result == "approved"]
        
        return {
            'total_rounds': len(self._rounds),
            'completed_rounds': len(completed_rounds),
            'approved_rounds': len(approved_rounds),
            'approval_rate': len(approved_rounds) / len(completed_rounds) if completed_rounds else 0,
            'total_participants': len(self._participants),
            'active_participants': len([p for p in self._participants.values() if p.is_active]),
            'total_stake': sum(p.stake for p in self._participants.values()),
            'pending_executions': len(self._pending_executions),
            'circuit_breaker_active': self._circuit_breaker_active,
        }

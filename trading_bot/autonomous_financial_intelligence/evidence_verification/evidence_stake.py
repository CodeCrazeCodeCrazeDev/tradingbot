"""
Evidence Stake System

Stake-based evidence submission with slashing penalties for false claims.
Implements economic incentives for truthful evidence provision.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class StakeStatus(Enum):
    """Status of a stake."""
    ACTIVE = "active"
    LOCKED = "locked"
    SLASHED = "slashed"
    RELEASED = "released"
    PENDING_VERIFICATION = "pending_verification"


class SlashingReason(Enum):
    """Reasons for slashing stake."""
    FALSE_EVIDENCE = "false_evidence"
    DATA_MANIPULATION = "data_manipulation"
    TIMESTAMP_FRAUD = "timestamp_fraud"
    SOURCE_MISREPRESENTATION = "source_misrepresentation"
    REPEATED_VIOLATIONS = "repeated_violations"
    CONSENSUS_DEVIATION = "consensus_deviation"
    HALLUCINATION_DETECTED = "hallucination_detected"


@dataclass
class StakeRecord:
    """
    Record of stake associated with evidence submission.
    """
    stake_id: str
    agent_id: str
    evidence_id: str
    stake_amount: float
    status: StakeStatus
    created_at: datetime
    locked_until: Optional[datetime] = None
    released_at: Optional[datetime] = None
    slashed_at: Optional[datetime] = None
    slashing_reason: Optional[SlashingReason] = None
    slashing_amount: float = 0.0
    verification_count: int = 0
    successful_verifications: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'stake_id': self.stake_id,
            'agent_id': self.agent_id,
            'evidence_id': self.evidence_id,
            'stake_amount': self.stake_amount,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'released_at': self.released_at.isoformat() if self.released_at else None,
            'slashed_at': self.slashed_at.isoformat() if self.slashed_at else None,
            'slashing_reason': self.slashing_reason.value if self.slashing_reason else None,
            'slashing_amount': self.slashing_amount,
            'verification_count': self.verification_count,
            'successful_verifications': self.successful_verifications,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StakeRecord':
        return cls(
            stake_id=data['stake_id'],
            agent_id=data['agent_id'],
            evidence_id=data['evidence_id'],
            stake_amount=data['stake_amount'],
            status=StakeStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            locked_until=datetime.fromisoformat(data['locked_until']) if data.get('locked_until') else None,
            released_at=datetime.fromisoformat(data['released_at']) if data.get('released_at') else None,
            slashed_at=datetime.fromisoformat(data['slashed_at']) if data.get('slashed_at') else None,
            slashing_reason=SlashingReason(data['slashing_reason']) if data.get('slashing_reason') else None,
            slashing_amount=data.get('slashing_amount', 0.0),
            verification_count=data.get('verification_count', 0),
            successful_verifications=data.get('successful_verifications', 0),
        )


@dataclass
class SlashingEvent:
    """
    Record of a slashing event.
    """
    event_id: str
    stake_id: str
    agent_id: str
    evidence_id: str
    reason: SlashingReason
    slashed_amount: float
    remaining_stake: float
    timestamp: datetime
    evidence_of_violation: Dict[str, Any]
    appealed: bool = False
    appeal_result: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'stake_id': self.stake_id,
            'agent_id': self.agent_id,
            'evidence_id': self.evidence_id,
            'reason': self.reason.value,
            'slashed_amount': self.slashed_amount,
            'remaining_stake': self.remaining_stake,
            'timestamp': self.timestamp.isoformat(),
            'evidence_of_violation': self.evidence_of_violation,
            'appealed': self.appealed,
            'appeal_result': self.appeal_result,
        }


@dataclass
class AgentStakeProfile:
    """
    Profile tracking an agent's staking history and reputation.
    """
    agent_id: str
    total_stake: float
    available_stake: float
    locked_stake: float
    slashed_total: float
    reputation_score: float
    total_submissions: int
    successful_submissions: int
    failed_submissions: int
    slashing_events: int
    created_at: datetime
    last_activity: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'total_stake': self.total_stake,
            'available_stake': self.available_stake,
            'locked_stake': self.locked_stake,
            'slashed_total': self.slashed_total,
            'reputation_score': self.reputation_score,
            'total_submissions': self.total_submissions,
            'successful_submissions': self.successful_submissions,
            'failed_submissions': self.failed_submissions,
            'slashing_events': self.slashing_events,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
        }


class EvidenceStake:
    """
    Manages stake-based evidence submission with slashing penalties.
    
    Provides:
    - Stake requirement for evidence submission
    - Automatic slashing for false claims
    - Reputation tracking for agents
    - Economic incentives for truthfulness
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'evidence_stake_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._stakes: Dict[str, StakeRecord] = {}
        self._slashing_events: Dict[str, SlashingEvent] = {}
        self._agent_profiles: Dict[str, AgentStakeProfile] = {}
        
        self._slashing_config = {
            'false_evidence_rate': 0.5,
            'data_manipulation_rate': 0.75,
            'timestamp_fraud_rate': 0.3,
            'source_misrepresentation_rate': 0.4,
            'repeated_violations_rate': 1.0,
            'consensus_deviation_rate': 0.25,
            'hallucination_detected_rate': 0.6,
        }
        
        self._stake_config = {
            'minimum_stake': 100.0,
            'lock_period_hours': 24,
            'verification_threshold': 3,
            'reputation_decay_rate': 0.01,
            'reputation_recovery_rate': 0.005,
            'max_stake_multiplier': 10.0,
        }
        
        logger.info("✅ Evidence Stake System initialized")
    
    async def create_agent_profile(
        self,
        agent_id: str,
        initial_stake: float = 1000.0,
    ) -> AgentStakeProfile:
        """
        Create a new agent stake profile.
        
        Args:
            agent_id: Unique identifier for the agent
            initial_stake: Initial stake amount
        
        Returns:
            AgentStakeProfile for the agent
        """
        if agent_id in self._agent_profiles:
            return self._agent_profiles[agent_id]
        
        profile = AgentStakeProfile(
            agent_id=agent_id,
            total_stake=initial_stake,
            available_stake=initial_stake,
            locked_stake=0.0,
            slashed_total=0.0,
            reputation_score=1.0,
            total_submissions=0,
            successful_submissions=0,
            failed_submissions=0,
            slashing_events=0,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
        )
        
        self._agent_profiles[agent_id] = profile
        await self._persist_profile(profile)
        
        logger.info(f"Created stake profile for agent {agent_id} with {initial_stake} stake")
        
        return profile
    
    async def submit_evidence_with_stake(
        self,
        agent_id: str,
        evidence_id: str,
        stake_amount: Optional[float] = None,
    ) -> Tuple[bool, StakeRecord]:
        """
        Submit evidence with associated stake.
        
        Args:
            agent_id: ID of the submitting agent
            evidence_id: ID of the evidence being submitted
            stake_amount: Amount to stake (defaults to minimum)
        
        Returns:
            Tuple of (success, stake_record)
        """
        if agent_id not in self._agent_profiles:
            await self.create_agent_profile(agent_id)
        
        profile = self._agent_profiles[agent_id]
        
        stake_amount = stake_amount or self._stake_config['minimum_stake']
        
        required_stake = self._calculate_required_stake(profile, stake_amount)
        
        if profile.available_stake < required_stake:
            logger.warning(f"Agent {agent_id} has insufficient stake: "
                          f"{profile.available_stake} < {required_stake}")
            return False, None
        
        stake_id = f"STK-{uuid.uuid4().hex[:16]}"
        lock_period = timedelta(hours=self._stake_config['lock_period_hours'])
        
        stake_record = StakeRecord(
            stake_id=stake_id,
            agent_id=agent_id,
            evidence_id=evidence_id,
            stake_amount=required_stake,
            status=StakeStatus.LOCKED,
            created_at=datetime.now(timezone.utc),
            locked_until=datetime.now(timezone.utc) + lock_period,
        )
        
        profile.available_stake -= required_stake
        profile.locked_stake += required_stake
        profile.total_submissions += 1
        profile.last_activity = datetime.now(timezone.utc)
        
        self._stakes[stake_id] = stake_record
        
        await self._persist_stake(stake_record)
        await self._persist_profile(profile)
        
        logger.info(f"Agent {agent_id} staked {required_stake} for evidence {evidence_id}")
        
        return True, stake_record
    
    def _calculate_required_stake(
        self,
        profile: AgentStakeProfile,
        base_stake: float,
    ) -> float:
        """Calculate required stake based on agent reputation."""
        reputation_multiplier = 2.0 - profile.reputation_score
        
        if profile.slashing_events > 0:
            violation_multiplier = 1.0 + (profile.slashing_events * 0.25)
        else:
            violation_multiplier = 1.0
        
        required = base_stake * reputation_multiplier * violation_multiplier
        
        max_stake = base_stake * self._stake_config['max_stake_multiplier']
        return min(required, max_stake)
    
    async def verify_stake(
        self,
        stake_id: str,
        verification_passed: bool,
        verification_details: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[SlashingEvent]]:
        """
        Record verification result for a stake.
        
        Args:
            stake_id: ID of the stake
            verification_passed: Whether verification passed
            verification_details: Optional details about verification
        
        Returns:
            Tuple of (stake_released, slashing_event if any)
        """
        if stake_id not in self._stakes:
            logger.error(f"Stake {stake_id} not found")
            return False, None
        
        stake = self._stakes[stake_id]
        profile = self._agent_profiles.get(stake.agent_id)
        
        if not profile:
            logger.error(f"Profile not found for agent {stake.agent_id}")
            return False, None
        
        stake.verification_count += 1
        
        if verification_passed:
            stake.successful_verifications += 1
            
            if stake.successful_verifications >= self._stake_config['verification_threshold']:
                return await self._release_stake(stake, profile)
            
            return True, None
        else:
            slashing_event = await self._slash_stake(
                stake, 
                profile, 
                SlashingReason.FALSE_EVIDENCE,
                verification_details or {}
            )
            return False, slashing_event
    
    async def _release_stake(
        self,
        stake: StakeRecord,
        profile: AgentStakeProfile,
    ) -> Tuple[bool, None]:
        """Release stake back to agent."""
        stake.status = StakeStatus.RELEASED
        stake.released_at = datetime.now(timezone.utc)
        
        profile.locked_stake -= stake.stake_amount
        profile.available_stake += stake.stake_amount
        profile.successful_submissions += 1
        
        profile.reputation_score = min(
            1.0,
            profile.reputation_score + self._stake_config['reputation_recovery_rate']
        )
        
        await self._persist_stake(stake)
        await self._persist_profile(profile)
        
        logger.info(f"Released stake {stake.stake_id} for agent {stake.agent_id}")
        
        return True, None
    
    async def _slash_stake(
        self,
        stake: StakeRecord,
        profile: AgentStakeProfile,
        reason: SlashingReason,
        evidence: Dict[str, Any],
    ) -> SlashingEvent:
        """Slash stake for violation."""
        slashing_rate = self._slashing_config.get(
            f"{reason.value}_rate",
            0.5
        )
        
        slashed_amount = stake.stake_amount * slashing_rate
        remaining = stake.stake_amount - slashed_amount
        
        stake.status = StakeStatus.SLASHED
        stake.slashed_at = datetime.now(timezone.utc)
        stake.slashing_reason = reason
        stake.slashing_amount = slashed_amount
        
        profile.locked_stake -= stake.stake_amount
        profile.available_stake += remaining
        profile.slashed_total += slashed_amount
        profile.failed_submissions += 1
        profile.slashing_events += 1
        
        profile.reputation_score = max(
            0.0,
            profile.reputation_score - (slashing_rate * 0.5)
        )
        
        event_id = f"SLE-{uuid.uuid4().hex[:16]}"
        slashing_event = SlashingEvent(
            event_id=event_id,
            stake_id=stake.stake_id,
            agent_id=stake.agent_id,
            evidence_id=stake.evidence_id,
            reason=reason,
            slashed_amount=slashed_amount,
            remaining_stake=remaining,
            timestamp=datetime.now(timezone.utc),
            evidence_of_violation=evidence,
        )
        
        self._slashing_events[event_id] = slashing_event
        
        await self._persist_stake(stake)
        await self._persist_profile(profile)
        await self._persist_slashing_event(slashing_event)
        
        logger.warning(f"Slashed {slashed_amount} from agent {stake.agent_id} "
                      f"for {reason.value}")
        
        return slashing_event
    
    async def slash_for_hallucination(
        self,
        agent_id: str,
        evidence_id: str,
        hallucination_details: Dict[str, Any],
    ) -> Optional[SlashingEvent]:
        """
        Slash stake specifically for hallucination detection.
        
        Args:
            agent_id: ID of the agent
            evidence_id: ID of the evidence containing hallucination
            hallucination_details: Details about the detected hallucination
        
        Returns:
            SlashingEvent if stake was slashed
        """
        stake = None
        for s in self._stakes.values():
            if s.agent_id == agent_id and s.evidence_id == evidence_id:
                stake = s
                break
        
        if not stake:
            logger.warning(f"No stake found for agent {agent_id} evidence {evidence_id}")
            return None
        
        if stake.status != StakeStatus.LOCKED:
            logger.warning(f"Stake {stake.stake_id} is not locked, cannot slash")
            return None
        
        profile = self._agent_profiles.get(agent_id)
        if not profile:
            return None
        
        return await self._slash_stake(
            stake,
            profile,
            SlashingReason.HALLUCINATION_DETECTED,
            hallucination_details
        )
    
    async def add_stake(self, agent_id: str, amount: float) -> bool:
        """Add stake to an agent's profile."""
        if agent_id not in self._agent_profiles:
            await self.create_agent_profile(agent_id, amount)
            return True
        
        profile = self._agent_profiles[agent_id]
        profile.total_stake += amount
        profile.available_stake += amount
        profile.last_activity = datetime.now(timezone.utc)
        
        await self._persist_profile(profile)
        
        logger.info(f"Added {amount} stake to agent {agent_id}")
        return True
    
    async def process_expired_locks(self):
        """Process stakes with expired lock periods."""
        now = datetime.now(timezone.utc)
        
        for stake in self._stakes.values():
            if stake.status == StakeStatus.LOCKED and stake.locked_until:
                if now > stake.locked_until:
                    profile = self._agent_profiles.get(stake.agent_id)
                    if profile:
                        if stake.successful_verifications > 0:
                            await self._release_stake(stake, profile)
                        else:
                            stake.status = StakeStatus.PENDING_VERIFICATION
                            await self._persist_stake(stake)
    
    def get_agent_profile(self, agent_id: str) -> Optional[AgentStakeProfile]:
        """Get an agent's stake profile."""
        return self._agent_profiles.get(agent_id)
    
    def get_agent_reputation(self, agent_id: str) -> float:
        """Get an agent's reputation score."""
        profile = self._agent_profiles.get(agent_id)
        return profile.reputation_score if profile else 0.0
    
    def get_stake_record(self, stake_id: str) -> Optional[StakeRecord]:
        """Get a stake record by ID."""
        return self._stakes.get(stake_id)
    
    def get_agent_stakes(self, agent_id: str) -> List[StakeRecord]:
        """Get all stakes for an agent."""
        return [s for s in self._stakes.values() if s.agent_id == agent_id]
    
    def get_slashing_history(self, agent_id: str) -> List[SlashingEvent]:
        """Get slashing history for an agent."""
        return [e for e in self._slashing_events.values() if e.agent_id == agent_id]
    
    async def _persist_stake(self, stake: StakeRecord):
        """Persist stake record to storage."""
        stake_file = self.storage_path / 'stakes' / f"{stake.stake_id}.json"
        stake_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(stake_file, 'w') as f:
            json.dump(stake.to_dict(), f, indent=2)
    
    async def _persist_profile(self, profile: AgentStakeProfile):
        """Persist agent profile to storage."""
        profile_file = self.storage_path / 'profiles' / f"{profile.agent_id}.json"
        profile_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(profile_file, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
    
    async def _persist_slashing_event(self, event: SlashingEvent):
        """Persist slashing event to storage."""
        event_file = self.storage_path / 'slashing_events' / f"{event.event_id}.json"
        event_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(event_file, 'w') as f:
            json.dump(event.to_dict(), f, indent=2)
    
    async def load_from_storage(self):
        """Load all data from storage."""
        profiles_dir = self.storage_path / 'profiles'
        if profiles_dir.exists():
            for profile_file in profiles_dir.glob('*.json'):
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    profile = AgentStakeProfile(**{
                        **data,
                        'created_at': datetime.fromisoformat(data['created_at']),
                        'last_activity': datetime.fromisoformat(data['last_activity']),
                    })
                    self._agent_profiles[profile.agent_id] = profile
        
        stakes_dir = self.storage_path / 'stakes'
        if stakes_dir.exists():
            for stake_file in stakes_dir.glob('*.json'):
                with open(stake_file, 'r') as f:
                    data = json.load(f)
                    stake = StakeRecord.from_dict(data)
                    self._stakes[stake.stake_id] = stake
        
        logger.info(f"Loaded {len(self._agent_profiles)} profiles and "
                   f"{len(self._stakes)} stakes from storage")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the stake system."""
        total_staked = sum(p.total_stake for p in self._agent_profiles.values())
        total_slashed = sum(p.slashed_total for p in self._agent_profiles.values())
        
        active_stakes = [s for s in self._stakes.values() if s.status == StakeStatus.LOCKED]
        
        return {
            'total_agents': len(self._agent_profiles),
            'total_staked': total_staked,
            'total_slashed': total_slashed,
            'active_stakes': len(active_stakes),
            'total_stakes': len(self._stakes),
            'slashing_events': len(self._slashing_events),
            'average_reputation': sum(p.reputation_score for p in self._agent_profiles.values()) / len(self._agent_profiles) if self._agent_profiles else 0,
        }

"""
Verification Market System

Market for verification services with rewards and bounties.
Implements economic incentives for thorough verification.
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


class BountyStatus(Enum):
    """Status of a verification bounty."""
    OPEN = "open"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    PAID = "paid"
    EXPIRED = "expired"
    DISPUTED = "disputed"


class BountyType(Enum):
    """Types of verification bounties."""
    DATA_VERIFICATION = "data_verification"
    CLAIM_VERIFICATION = "claim_verification"
    PROOF_VERIFICATION = "proof_verification"
    ADVERSARIAL_TESTING = "adversarial_testing"
    BUG_BOUNTY = "bug_bounty"
    HALLUCINATION_DETECTION = "hallucination_detection"
    CROSS_VALIDATION = "cross_validation"


class BidStatus(Enum):
    """Status of a verification bid."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    COMPLETED = "completed"


@dataclass
class VerificationBounty:
    """
    A bounty for verification work.
    """
    bounty_id: str
    bounty_type: BountyType
    title: str
    description: str
    target_id: str
    reward_amount: float
    status: BountyStatus
    created_at: datetime
    expires_at: datetime
    created_by: str
    requirements: Dict[str, Any]
    minimum_reputation: float = 0.5
    required_validators: int = 1
    current_bids: int = 0
    accepted_bid_id: Optional[str] = None
    completion_proof: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'bounty_id': self.bounty_id,
            'bounty_type': self.bounty_type.value,
            'title': self.title,
            'description': self.description,
            'target_id': self.target_id,
            'reward_amount': self.reward_amount,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'created_by': self.created_by,
            'requirements': self.requirements,
            'minimum_reputation': self.minimum_reputation,
            'required_validators': self.required_validators,
            'current_bids': self.current_bids,
            'accepted_bid_id': self.accepted_bid_id,
            'completion_proof': self.completion_proof,
        }


@dataclass
class VerificationBid:
    """
    A bid to complete a verification bounty.
    """
    bid_id: str
    bounty_id: str
    bidder_id: str
    bid_amount: float
    proposed_approach: str
    estimated_completion_hours: float
    status: BidStatus
    created_at: datetime
    stake_amount: float = 0.0
    reputation_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'bid_id': self.bid_id,
            'bounty_id': self.bounty_id,
            'bidder_id': self.bidder_id,
            'bid_amount': self.bid_amount,
            'proposed_approach': self.proposed_approach,
            'estimated_completion_hours': self.estimated_completion_hours,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'stake_amount': self.stake_amount,
            'reputation_score': self.reputation_score,
        }


@dataclass
class VerificationSubmission:
    """
    A submission for a verification bounty.
    """
    submission_id: str
    bounty_id: str
    bid_id: str
    submitter_id: str
    verification_result: Dict[str, Any]
    evidence_provided: List[Dict[str, Any]]
    submitted_at: datetime
    is_accepted: bool = False
    review_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'submission_id': self.submission_id,
            'bounty_id': self.bounty_id,
            'bid_id': self.bid_id,
            'submitter_id': self.submitter_id,
            'verification_result': self.verification_result,
            'evidence_provided': self.evidence_provided,
            'submitted_at': self.submitted_at.isoformat(),
            'is_accepted': self.is_accepted,
            'review_notes': self.review_notes,
        }


@dataclass
class VerifierProfile:
    """
    Profile of a verifier in the market.
    """
    verifier_id: str
    name: str
    reputation_score: float
    total_verifications: int
    successful_verifications: int
    failed_verifications: int
    total_earnings: float
    specializations: List[str]
    stake_balance: float
    is_active: bool
    created_at: datetime
    last_activity: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'verifier_id': self.verifier_id,
            'name': self.name,
            'reputation_score': self.reputation_score,
            'total_verifications': self.total_verifications,
            'successful_verifications': self.successful_verifications,
            'failed_verifications': self.failed_verifications,
            'total_earnings': self.total_earnings,
            'specializations': self.specializations,
            'stake_balance': self.stake_balance,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
        }


class VerificationMarket:
    """
    Market for verification services with economic incentives.
    
    Provides:
    - Bounty creation and management
    - Bid submission and selection
    - Verification submission and review
    - Reward distribution
    - Reputation tracking
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'verification_market_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._bounties: Dict[str, VerificationBounty] = {}
        self._bids: Dict[str, VerificationBid] = {}
        self._submissions: Dict[str, VerificationSubmission] = {}
        self._verifiers: Dict[str, VerifierProfile] = {}
        
        self._market_config = {
            'minimum_bounty_reward': 10.0,
            'maximum_bounty_reward': 10000.0,
            'default_expiry_hours': 24,
            'platform_fee_percent': 5.0,
            'minimum_stake_percent': 10.0,
            'reputation_decay_rate': 0.01,
        }
        
        self._reward_pool: float = 100000.0
        
        logger.info("✅ Verification Market initialized")
    
    async def create_bounty(
        self,
        bounty_type: BountyType,
        title: str,
        description: str,
        target_id: str,
        reward_amount: float,
        created_by: str,
        requirements: Optional[Dict[str, Any]] = None,
        expiry_hours: Optional[int] = None,
        minimum_reputation: float = 0.5,
        required_validators: int = 1,
    ) -> VerificationBounty:
        """
        Create a new verification bounty.
        
        Args:
            bounty_type: Type of verification needed
            title: Bounty title
            description: Detailed description
            target_id: ID of the item to verify
            reward_amount: Reward for completion
            created_by: ID of bounty creator
            requirements: Specific requirements
            expiry_hours: Hours until expiry
            minimum_reputation: Minimum verifier reputation
            required_validators: Number of validators needed
        
        Returns:
            VerificationBounty
        """
        reward_amount = max(
            self._market_config['minimum_bounty_reward'],
            min(reward_amount, self._market_config['maximum_bounty_reward'])
        )
        
        bounty_id = f"BNT-{uuid.uuid4().hex[:12]}"
        expiry_hours = expiry_hours or self._market_config['default_expiry_hours']
        
        bounty = VerificationBounty(
            bounty_id=bounty_id,
            bounty_type=bounty_type,
            title=title,
            description=description,
            target_id=target_id,
            reward_amount=reward_amount,
            status=BountyStatus.OPEN,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
            created_by=created_by,
            requirements=requirements or {},
            minimum_reputation=minimum_reputation,
            required_validators=required_validators,
        )
        
        self._bounties[bounty_id] = bounty
        await self._persist_bounty(bounty)
        
        logger.info(f"Created bounty {bounty_id}: {title} (reward: {reward_amount})")
        
        return bounty
    
    async def submit_bid(
        self,
        bounty_id: str,
        bidder_id: str,
        bid_amount: float,
        proposed_approach: str,
        estimated_hours: float,
    ) -> Optional[VerificationBid]:
        """
        Submit a bid for a bounty.
        
        Args:
            bounty_id: ID of the bounty
            bidder_id: ID of the bidder
            bid_amount: Requested payment amount
            proposed_approach: Description of verification approach
            estimated_hours: Estimated completion time
        
        Returns:
            VerificationBid if successful
        """
        if bounty_id not in self._bounties:
            logger.error(f"Bounty {bounty_id} not found")
            return None
        
        bounty = self._bounties[bounty_id]
        
        if bounty.status != BountyStatus.OPEN:
            logger.error(f"Bounty {bounty_id} is not open for bids")
            return None
        
        if datetime.now(timezone.utc) > bounty.expires_at:
            bounty.status = BountyStatus.EXPIRED
            return None
        
        verifier = self._verifiers.get(bidder_id)
        if not verifier:
            verifier = await self.register_verifier(bidder_id, f"Verifier-{bidder_id[:8]}")
        
        if verifier.reputation_score < bounty.minimum_reputation:
            logger.warning(f"Bidder {bidder_id} reputation too low for bounty {bounty_id}")
            return None
        
        bid_id = f"BID-{uuid.uuid4().hex[:12]}"
        stake_amount = bid_amount * (self._market_config['minimum_stake_percent'] / 100)
        
        bid = VerificationBid(
            bid_id=bid_id,
            bounty_id=bounty_id,
            bidder_id=bidder_id,
            bid_amount=bid_amount,
            proposed_approach=proposed_approach,
            estimated_completion_hours=estimated_hours,
            status=BidStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            stake_amount=stake_amount,
            reputation_score=verifier.reputation_score,
        )
        
        self._bids[bid_id] = bid
        bounty.current_bids += 1
        
        await self._persist_bid(bid)
        
        logger.info(f"Bid {bid_id} submitted for bounty {bounty_id} by {bidder_id}")
        
        return bid
    
    async def accept_bid(self, bounty_id: str, bid_id: str) -> bool:
        """
        Accept a bid for a bounty.
        
        Args:
            bounty_id: ID of the bounty
            bid_id: ID of the bid to accept
        
        Returns:
            True if successful
        """
        if bounty_id not in self._bounties or bid_id not in self._bids:
            return False
        
        bounty = self._bounties[bounty_id]
        bid = self._bids[bid_id]
        
        if bid.bounty_id != bounty_id:
            return False
        
        if bounty.status != BountyStatus.OPEN:
            return False
        
        for other_bid in self._bids.values():
            if other_bid.bounty_id == bounty_id and other_bid.bid_id != bid_id:
                other_bid.status = BidStatus.REJECTED
        
        bid.status = BidStatus.ACCEPTED
        bounty.status = BountyStatus.IN_PROGRESS
        bounty.accepted_bid_id = bid_id
        
        await self._persist_bounty(bounty)
        await self._persist_bid(bid)
        
        logger.info(f"Bid {bid_id} accepted for bounty {bounty_id}")
        
        return True
    
    async def submit_verification(
        self,
        bounty_id: str,
        bid_id: str,
        submitter_id: str,
        verification_result: Dict[str, Any],
        evidence: List[Dict[str, Any]],
    ) -> Optional[VerificationSubmission]:
        """
        Submit verification work for a bounty.
        
        Args:
            bounty_id: ID of the bounty
            bid_id: ID of the accepted bid
            submitter_id: ID of the submitter
            verification_result: Results of verification
            evidence: Supporting evidence
        
        Returns:
            VerificationSubmission if successful
        """
        if bounty_id not in self._bounties or bid_id not in self._bids:
            return None
        
        bounty = self._bounties[bounty_id]
        bid = self._bids[bid_id]
        
        if bounty.status != BountyStatus.IN_PROGRESS:
            return None
        
        if bid.status != BidStatus.ACCEPTED:
            return None
        
        if bid.bidder_id != submitter_id:
            return None
        
        submission_id = f"SUB-{uuid.uuid4().hex[:12]}"
        
        submission = VerificationSubmission(
            submission_id=submission_id,
            bounty_id=bounty_id,
            bid_id=bid_id,
            submitter_id=submitter_id,
            verification_result=verification_result,
            evidence_provided=evidence,
            submitted_at=datetime.now(timezone.utc),
        )
        
        self._submissions[submission_id] = submission
        bounty.status = BountyStatus.SUBMITTED
        
        await self._persist_submission(submission)
        await self._persist_bounty(bounty)
        
        logger.info(f"Verification submitted for bounty {bounty_id}")
        
        return submission
    
    async def review_submission(
        self,
        submission_id: str,
        is_accepted: bool,
        review_notes: Optional[str] = None,
    ) -> bool:
        """
        Review a verification submission.
        
        Args:
            submission_id: ID of the submission
            is_accepted: Whether to accept the submission
            review_notes: Optional review notes
        
        Returns:
            True if successful
        """
        if submission_id not in self._submissions:
            return False
        
        submission = self._submissions[submission_id]
        bounty = self._bounties.get(submission.bounty_id)
        bid = self._bids.get(submission.bid_id)
        
        if not bounty or not bid:
            return False
        
        submission.is_accepted = is_accepted
        submission.review_notes = review_notes
        
        verifier = self._verifiers.get(submission.submitter_id)
        
        if is_accepted:
            bounty.status = BountyStatus.VERIFIED
            bounty.completion_proof = submission.verification_result
            bid.status = BidStatus.COMPLETED
            
            if verifier:
                verifier.successful_verifications += 1
                verifier.total_verifications += 1
                verifier.reputation_score = min(1.0, verifier.reputation_score + 0.02)
                verifier.last_activity = datetime.now(timezone.utc)
            
            await self._distribute_reward(bounty, bid, verifier)
        else:
            bounty.status = BountyStatus.DISPUTED
            
            if verifier:
                verifier.failed_verifications += 1
                verifier.total_verifications += 1
                verifier.reputation_score = max(0.0, verifier.reputation_score - 0.05)
                verifier.last_activity = datetime.now(timezone.utc)
        
        await self._persist_submission(submission)
        await self._persist_bounty(bounty)
        await self._persist_bid(bid)
        if verifier:
            await self._persist_verifier(verifier)
        
        return True
    
    async def _distribute_reward(
        self,
        bounty: VerificationBounty,
        bid: VerificationBid,
        verifier: Optional[VerifierProfile],
    ):
        """Distribute reward for completed verification."""
        platform_fee = bounty.reward_amount * (self._market_config['platform_fee_percent'] / 100)
        verifier_reward = bounty.reward_amount - platform_fee
        
        if verifier:
            verifier.total_earnings += verifier_reward
            verifier.stake_balance += bid.stake_amount
        
        bounty.status = BountyStatus.PAID
        
        logger.info(f"Distributed reward {verifier_reward} for bounty {bounty.bounty_id}")
    
    async def register_verifier(
        self,
        verifier_id: str,
        name: str,
        specializations: Optional[List[str]] = None,
        initial_stake: float = 100.0,
    ) -> VerifierProfile:
        """
        Register a new verifier in the market.
        
        Args:
            verifier_id: Unique identifier
            name: Verifier name
            specializations: Areas of expertise
            initial_stake: Initial stake amount
        
        Returns:
            VerifierProfile
        """
        if verifier_id in self._verifiers:
            return self._verifiers[verifier_id]
        
        verifier = VerifierProfile(
            verifier_id=verifier_id,
            name=name,
            reputation_score=0.5,
            total_verifications=0,
            successful_verifications=0,
            failed_verifications=0,
            total_earnings=0.0,
            specializations=specializations or [],
            stake_balance=initial_stake,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        
        self._verifiers[verifier_id] = verifier
        await self._persist_verifier(verifier)
        
        logger.info(f"Registered verifier: {name} ({verifier_id})")
        
        return verifier
    
    def get_open_bounties(
        self,
        bounty_type: Optional[BountyType] = None,
        min_reward: Optional[float] = None,
        max_reputation_required: Optional[float] = None,
    ) -> List[VerificationBounty]:
        """Get list of open bounties with optional filtering."""
        bounties = [
            b for b in self._bounties.values()
            if b.status == BountyStatus.OPEN and datetime.now(timezone.utc) < b.expires_at
        ]
        
        if bounty_type:
            bounties = [b for b in bounties if b.bounty_type == bounty_type]
        
        if min_reward:
            bounties = [b for b in bounties if b.reward_amount >= min_reward]
        
        if max_reputation_required:
            bounties = [b for b in bounties if b.minimum_reputation <= max_reputation_required]
        
        return sorted(bounties, key=lambda b: b.reward_amount, reverse=True)
    
    def get_bounty(self, bounty_id: str) -> Optional[VerificationBounty]:
        """Get a bounty by ID."""
        return self._bounties.get(bounty_id)
    
    def get_verifier(self, verifier_id: str) -> Optional[VerifierProfile]:
        """Get a verifier profile."""
        return self._verifiers.get(verifier_id)
    
    def get_verifier_bids(self, verifier_id: str) -> List[VerificationBid]:
        """Get all bids by a verifier."""
        return [b for b in self._bids.values() if b.bidder_id == verifier_id]
    
    async def process_expired_bounties(self):
        """Process bounties that have expired."""
        now = datetime.now(timezone.utc)
        
        for bounty in self._bounties.values():
            if bounty.status == BountyStatus.OPEN and now > bounty.expires_at:
                bounty.status = BountyStatus.EXPIRED
                await self._persist_bounty(bounty)
                logger.info(f"Bounty {bounty.bounty_id} expired")
    
    async def create_hallucination_bounty(
        self,
        claim_id: str,
        claim_content: Dict[str, Any],
        reward_amount: float = 100.0,
    ) -> VerificationBounty:
        """
        Create a bounty specifically for hallucination detection.
        
        Args:
            claim_id: ID of the claim to verify
            claim_content: Content of the claim
            reward_amount: Reward for finding hallucinations
        
        Returns:
            VerificationBounty
        """
        return await self.create_bounty(
            bounty_type=BountyType.HALLUCINATION_DETECTION,
            title=f"Verify claim {claim_id} for hallucinations",
            description="Analyze the claim for potential hallucinations, fabricated data, or unsupported assertions",
            target_id=claim_id,
            reward_amount=reward_amount,
            created_by="system",
            requirements={
                'claim_content': claim_content,
                'verification_type': 'hallucination_detection',
                'required_checks': [
                    'data_verification',
                    'source_verification',
                    'logical_consistency',
                    'temporal_validity',
                ],
            },
            minimum_reputation=0.7,
            required_validators=2,
        )
    
    async def _persist_bounty(self, bounty: VerificationBounty):
        """Persist bounty to storage."""
        bounty_file = self.storage_path / 'bounties' / f"{bounty.bounty_id}.json"
        bounty_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(bounty_file, 'w') as f:
            json.dump(bounty.to_dict(), f, indent=2)
    
    async def _persist_bid(self, bid: VerificationBid):
        """Persist bid to storage."""
        bid_file = self.storage_path / 'bids' / f"{bid.bid_id}.json"
        bid_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(bid_file, 'w') as f:
            json.dump(bid.to_dict(), f, indent=2)
    
    async def _persist_submission(self, submission: VerificationSubmission):
        """Persist submission to storage."""
        sub_file = self.storage_path / 'submissions' / f"{submission.submission_id}.json"
        sub_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(sub_file, 'w') as f:
            json.dump(submission.to_dict(), f, indent=2)
    
    async def _persist_verifier(self, verifier: VerifierProfile):
        """Persist verifier profile to storage."""
        verifier_file = self.storage_path / 'verifiers' / f"{verifier.verifier_id}.json"
        verifier_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(verifier_file, 'w') as f:
            json.dump(verifier.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get market statistics."""
        open_bounties = [b for b in self._bounties.values() if b.status == BountyStatus.OPEN]
        completed_bounties = [b for b in self._bounties.values() if b.status == BountyStatus.PAID]
        
        return {
            'total_bounties': len(self._bounties),
            'open_bounties': len(open_bounties),
            'completed_bounties': len(completed_bounties),
            'total_bids': len(self._bids),
            'total_submissions': len(self._submissions),
            'total_verifiers': len(self._verifiers),
            'active_verifiers': len([v for v in self._verifiers.values() if v.is_active]),
            'total_rewards_distributed': sum(b.reward_amount for b in completed_bounties),
            'average_bounty_reward': sum(b.reward_amount for b in self._bounties.values()) / len(self._bounties) if self._bounties else 0,
        }

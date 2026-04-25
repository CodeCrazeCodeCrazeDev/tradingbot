"""
Consensus Mechanism - Multi-Agent Agreement Protocol
======================================================

Implements consensus mechanisms for multi-agent decisions:
1. Voting protocols
2. Weighted consensus
3. Byzantine fault tolerance
4. Confidence aggregation

Based on the Foundation Agents paper (arXiv:2504.01990) multi-agent systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class VotingMethod(Enum):
    """Voting methods for consensus"""
    MAJORITY = "majority"               # Simple majority
    SUPERMAJORITY = "supermajority"     # 2/3 majority
    UNANIMOUS = "unanimous"             # All must agree
    WEIGHTED = "weighted"               # Weighted by expertise
    RANKED_CHOICE = "ranked_choice"     # Ranked preferences
    APPROVAL = "approval"               # Approve multiple options
    QUADRATIC = "quadratic"             # Quadratic voting


class ConsensusStatus(Enum):
    """Status of consensus process"""
    PENDING = "pending"
    VOTING = "voting"
    REACHED = "reached"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Vote:
    """A vote from an agent"""
    vote_id: str
    agent_id: str
    proposal_id: str
    
    # Vote content
    choice: str                         # Option chosen
    confidence: float = 0.5             # Confidence in choice
    reasoning: str = ""                 # Reasoning for vote
    
    # For ranked choice
    rankings: List[str] = field(default_factory=list)
    
    # For approval voting
    approvals: List[str] = field(default_factory=list)
    
    # Weight
    weight: float = 1.0
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'vote_id': self.vote_id,
            'agent_id': self.agent_id,
            'choice': self.choice,
            'confidence': self.confidence,
            'weight': self.weight
        }


@dataclass
class Proposal:
    """A proposal for consensus"""
    proposal_id: str
    title: str
    description: str
    
    # Options
    options: List[str] = field(default_factory=list)
    
    # Proposer
    proposer_id: str = ""
    
    # Votes
    votes: Dict[str, Vote] = field(default_factory=dict)  # agent_id -> Vote
    
    # Status
    status: ConsensusStatus = ConsensusStatus.PENDING
    
    # Result
    winning_option: Optional[str] = None
    vote_counts: Dict[str, float] = field(default_factory=dict)
    consensus_confidence: float = 0.0
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'proposal_id': self.proposal_id,
            'title': self.title,
            'options': self.options,
            'status': self.status.value,
            'n_votes': len(self.votes),
            'winning_option': self.winning_option,
            'consensus_confidence': self.consensus_confidence
        }


@dataclass
class ConsensusResult:
    """Result of a consensus process"""
    proposal_id: str
    method: VotingMethod
    
    # Outcome
    decision: str
    confidence: float
    
    # Vote breakdown
    vote_counts: Dict[str, float]
    participation_rate: float
    
    # Analysis
    agreement_level: float          # How much agents agreed
    dissent_reasons: List[str]      # Reasons for dissent
    
    # Timing
    duration_seconds: float
    
    def to_dict(self) -> Dict:
        return {
            'proposal_id': self.proposal_id,
            'method': self.method.value,
            'decision': self.decision,
            'confidence': self.confidence,
            'vote_counts': self.vote_counts,
            'participation_rate': self.participation_rate,
            'agreement_level': self.agreement_level
        }


class VotingProtocol:
    """Implements various voting protocols"""
    
    def count_majority(
        self,
        votes: List[Vote],
        options: List[str]
    ) -> Tuple[str, Dict[str, float]]:
        """Simple majority voting"""
        counts = defaultdict(float)
        
        for vote in votes:
            counts[vote.choice] += vote.weight
        
        if not counts:
            return options[0] if options else "", dict(counts)
        
        winner = max(counts.items(), key=lambda x: x[1])[0]
        return winner, dict(counts)
    
    def count_supermajority(
        self,
        votes: List[Vote],
        options: List[str],
        threshold: float = 0.67
    ) -> Tuple[Optional[str], Dict[str, float]]:
        """Supermajority voting (2/3 default)"""
        counts = defaultdict(float)
        total_weight = sum(v.weight for v in votes)
        
        for vote in votes:
            counts[vote.choice] += vote.weight
        
        for option, count in counts.items():
            if count / total_weight >= threshold:
                return option, dict(counts)
        
        return None, dict(counts)
    
    def count_unanimous(
        self,
        votes: List[Vote],
        options: List[str]
    ) -> Tuple[Optional[str], Dict[str, float]]:
        """Unanimous voting"""
        if not votes:
            return None, {}
        
        choices = set(v.choice for v in votes)
        counts = defaultdict(float)
        
        for vote in votes:
            counts[vote.choice] += vote.weight
        
        if len(choices) == 1:
            return votes[0].choice, dict(counts)
        
        return None, dict(counts)
    
    def count_weighted(
        self,
        votes: List[Vote],
        options: List[str],
        agent_weights: Dict[str, float]
    ) -> Tuple[str, Dict[str, float]]:
        """Weighted voting based on agent expertise"""
        counts = defaultdict(float)
        
        for vote in votes:
            weight = agent_weights.get(vote.agent_id, 1.0) * vote.weight
            counts[vote.choice] += weight * vote.confidence
        
        if not counts:
            return options[0] if options else "", dict(counts)
        
        winner = max(counts.items(), key=lambda x: x[1])[0]
        return winner, dict(counts)
    
    def count_ranked_choice(
        self,
        votes: List[Vote],
        options: List[str]
    ) -> Tuple[str, Dict[str, float]]:
        """Ranked choice voting (instant runoff)"""
        remaining_options = set(options)
        current_votes = votes.copy()
        
        while len(remaining_options) > 1:
            # Count first choices
            counts = defaultdict(float)
            for vote in current_votes:
                for choice in vote.rankings:
                    if choice in remaining_options:
                        counts[choice] += vote.weight
                        break
            
            if not counts:
                break
            
            # Check for majority
            total = sum(counts.values())
            for option, count in counts.items():
                if count > total / 2:
                    return option, dict(counts)
            
            # Eliminate lowest
            lowest = min(counts.items(), key=lambda x: x[1])[0]
            remaining_options.remove(lowest)
        
        winner = list(remaining_options)[0] if remaining_options else options[0]
        return winner, dict(counts) if 'counts' in dir() else {}
    
    def count_approval(
        self,
        votes: List[Vote],
        options: List[str]
    ) -> Tuple[str, Dict[str, float]]:
        """Approval voting"""
        counts = defaultdict(float)
        
        for vote in votes:
            for approved in vote.approvals:
                counts[approved] += vote.weight
        
        if not counts:
            return options[0] if options else "", dict(counts)
        
        winner = max(counts.items(), key=lambda x: x[1])[0]
        return winner, dict(counts)
    
    def count_quadratic(
        self,
        votes: List[Vote],
        options: List[str],
        vote_credits: Dict[str, int]
    ) -> Tuple[str, Dict[str, float]]:
        """Quadratic voting"""
        counts = defaultdict(float)
        
        for vote in votes:
            credits = vote_credits.get(vote.agent_id, 100)
            # In quadratic voting, cost = votes^2
            # So votes = sqrt(credits_spent)
            effective_votes = np.sqrt(credits * vote.confidence)
            counts[vote.choice] += effective_votes
        
        if not counts:
            return options[0] if options else "", dict(counts)
        
        winner = max(counts.items(), key=lambda x: x[1])[0]
        return winner, dict(counts)


class ConfidenceAggregator:
    """Aggregates confidence scores from multiple agents"""
    
    def aggregate_mean(self, confidences: List[float]) -> float:
        """Simple mean aggregation"""
        if not confidences:
            return 0.0
        return np.mean(confidences)
    
    def aggregate_weighted(
        self,
        confidences: List[float],
        weights: List[float]
    ) -> float:
        """Weighted mean aggregation"""
        if not confidences or not weights:
            return 0.0
        return np.average(confidences, weights=weights)
    
    def aggregate_bayesian(
        self,
        confidences: List[float],
        prior: float = 0.5
    ) -> float:
        """Bayesian aggregation"""
        if not confidences:
            return prior
        
        # Convert to log-odds
        log_odds = np.log(prior / (1 - prior + 1e-10))
        
        for conf in confidences:
            conf = max(0.01, min(0.99, conf))  # Clip to avoid log(0)
            log_odds += np.log(conf / (1 - conf))
        
        # Convert back to probability
        return 1 / (1 + np.exp(-log_odds))
    
    def aggregate_median(self, confidences: List[float]) -> float:
        """Median aggregation (robust to outliers)"""
        if not confidences:
            return 0.0
        return np.median(confidences)


class ConsensusMechanism:
    """
    Consensus Mechanism
    
    Manages consensus-building among multiple agents
    for collective decision-making.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.voting_protocol = VotingProtocol()
        self.confidence_aggregator = ConfidenceAggregator()
        
        # Proposals
        self.proposals: Dict[str, Proposal] = {}
        self.proposal_history: List[Proposal] = []
        
        # Agent weights (for weighted voting)
        self.agent_weights: Dict[str, float] = {}
        self.agent_vote_credits: Dict[str, int] = defaultdict(lambda: 100)
        
        # Statistics
        self.stats = {
            'proposals_created': 0,
            'consensus_reached': 0,
            'consensus_failed': 0,
            'total_votes': 0
        }
        
        logger.info("Consensus Mechanism initialized")
    
    def create_proposal(
        self,
        title: str,
        description: str,
        options: List[str],
        proposer_id: str,
        deadline: Optional[datetime] = None
    ) -> Proposal:
        """Create a new proposal for consensus"""
        proposal = Proposal(
            proposal_id=str(uuid.uuid4())[:8],
            title=title,
            description=description,
            options=options,
            proposer_id=proposer_id,
            deadline=deadline,
            status=ConsensusStatus.VOTING
        )
        
        self.proposals[proposal.proposal_id] = proposal
        self.stats['proposals_created'] += 1
        
        logger.info(f"Created proposal: {title}")
        
        return proposal
    
    def cast_vote(
        self,
        proposal_id: str,
        agent_id: str,
        choice: str,
        confidence: float = 0.5,
        reasoning: str = "",
        rankings: Optional[List[str]] = None,
        approvals: Optional[List[str]] = None
    ) -> Optional[Vote]:
        """Cast a vote on a proposal"""
        if proposal_id not in self.proposals:
            return None
        
        proposal = self.proposals[proposal_id]
        
        if proposal.status != ConsensusStatus.VOTING:
            return None
        
        if choice not in proposal.options and choice != "abstain":
            return None
        
        vote = Vote(
            vote_id=str(uuid.uuid4())[:8],
            agent_id=agent_id,
            proposal_id=proposal_id,
            choice=choice,
            confidence=confidence,
            reasoning=reasoning,
            rankings=rankings or [],
            approvals=approvals or [],
            weight=self.agent_weights.get(agent_id, 1.0)
        )
        
        proposal.votes[agent_id] = vote
        self.stats['total_votes'] += 1
        
        return vote
    
    def resolve_proposal(
        self,
        proposal_id: str,
        method: VotingMethod = VotingMethod.MAJORITY,
        required_participation: float = 0.5,
        total_agents: int = 1
    ) -> Optional[ConsensusResult]:
        """Resolve a proposal using specified voting method"""
        if proposal_id not in self.proposals:
            return None
        
        proposal = self.proposals[proposal_id]
        votes = list(proposal.votes.values())
        
        # Check participation
        participation_rate = len(votes) / max(1, total_agents)
        
        if participation_rate < required_participation:
            proposal.status = ConsensusStatus.FAILED
            self.stats['consensus_failed'] += 1
            return ConsensusResult(
                proposal_id=proposal_id,
                method=method,
                decision="",
                confidence=0.0,
                vote_counts={},
                participation_rate=participation_rate,
                agreement_level=0.0,
                dissent_reasons=["Insufficient participation"],
                duration_seconds=(datetime.utcnow() - proposal.created_at).total_seconds()
            )
        
        # Count votes based on method
        if method == VotingMethod.MAJORITY:
            winner, counts = self.voting_protocol.count_majority(votes, proposal.options)
        elif method == VotingMethod.SUPERMAJORITY:
            winner, counts = self.voting_protocol.count_supermajority(votes, proposal.options)
            if winner is None:
                proposal.status = ConsensusStatus.FAILED
                self.stats['consensus_failed'] += 1
                return self._create_failed_result(proposal, method, counts, participation_rate)
        elif method == VotingMethod.UNANIMOUS:
            winner, counts = self.voting_protocol.count_unanimous(votes, proposal.options)
            if winner is None:
                proposal.status = ConsensusStatus.FAILED
                self.stats['consensus_failed'] += 1
                return self._create_failed_result(proposal, method, counts, participation_rate)
        elif method == VotingMethod.WEIGHTED:
            winner, counts = self.voting_protocol.count_weighted(
                votes, proposal.options, self.agent_weights
            )
        elif method == VotingMethod.RANKED_CHOICE:
            winner, counts = self.voting_protocol.count_ranked_choice(votes, proposal.options)
        elif method == VotingMethod.APPROVAL:
            winner, counts = self.voting_protocol.count_approval(votes, proposal.options)
        elif method == VotingMethod.QUADRATIC:
            winner, counts = self.voting_protocol.count_quadratic(
                votes, proposal.options, dict(self.agent_vote_credits)
            )
        else:
            winner, counts = self.voting_protocol.count_majority(votes, proposal.options)
        
        # Calculate consensus confidence
        confidences = [v.confidence for v in votes if v.choice == winner]
        consensus_confidence = self.confidence_aggregator.aggregate_bayesian(confidences)
        
        # Calculate agreement level
        total_weight = sum(counts.values())
        winner_weight = counts.get(winner, 0)
        agreement_level = winner_weight / total_weight if total_weight > 0 else 0
        
        # Collect dissent reasons
        dissent_reasons = [
            v.reasoning for v in votes
            if v.choice != winner and v.reasoning
        ]
        
        # Update proposal
        proposal.winning_option = winner
        proposal.vote_counts = counts
        proposal.consensus_confidence = consensus_confidence
        proposal.status = ConsensusStatus.REACHED
        proposal.resolved_at = datetime.utcnow()
        
        self.proposal_history.append(proposal)
        self.stats['consensus_reached'] += 1
        
        result = ConsensusResult(
            proposal_id=proposal_id,
            method=method,
            decision=winner,
            confidence=consensus_confidence,
            vote_counts=counts,
            participation_rate=participation_rate,
            agreement_level=agreement_level,
            dissent_reasons=dissent_reasons[:5],
            duration_seconds=(proposal.resolved_at - proposal.created_at).total_seconds()
        )
        
        logger.info(f"Consensus reached on {proposal_id}: {winner}")
        
        return result
    
    def _create_failed_result(
        self,
        proposal: Proposal,
        method: VotingMethod,
        counts: Dict[str, float],
        participation_rate: float
    ) -> ConsensusResult:
        """Create a failed consensus result"""
        return ConsensusResult(
            proposal_id=proposal.proposal_id,
            method=method,
            decision="",
            confidence=0.0,
            vote_counts=counts,
            participation_rate=participation_rate,
            agreement_level=0.0,
            dissent_reasons=["Failed to reach required threshold"],
            duration_seconds=(datetime.utcnow() - proposal.created_at).total_seconds()
        )
    
    def set_agent_weight(self, agent_id: str, weight: float):
        """Set voting weight for an agent"""
        self.agent_weights[agent_id] = max(0.0, min(10.0, weight))
    
    def set_vote_credits(self, agent_id: str, credits: int):
        """Set vote credits for quadratic voting"""
        self.agent_vote_credits[agent_id] = max(0, credits)
    
    def quick_consensus(
        self,
        topic: str,
        options: List[str],
        agent_votes: Dict[str, Tuple[str, float]],  # agent_id -> (choice, confidence)
        method: VotingMethod = VotingMethod.WEIGHTED
    ) -> ConsensusResult:
        """Quick consensus without creating formal proposal"""
        proposal = self.create_proposal(
            title=topic,
            description=f"Quick consensus on: {topic}",
            options=options,
            proposer_id="system"
        )
        
        for agent_id, (choice, confidence) in agent_votes.items():
            self.cast_vote(
                proposal.proposal_id,
                agent_id,
                choice,
                confidence
            )
        
        return self.resolve_proposal(
            proposal.proposal_id,
            method=method,
            total_agents=len(agent_votes)
        )
    
    def aggregate_predictions(
        self,
        predictions: Dict[str, Tuple[float, float]],  # agent_id -> (prediction, confidence)
        method: str = "weighted_mean"
    ) -> Tuple[float, float]:
        """Aggregate numerical predictions from multiple agents"""
        if not predictions:
            return 0.0, 0.0
        
        values = [p[0] for p in predictions.values()]
        confidences = [p[1] for p in predictions.values()]
        weights = [self.agent_weights.get(aid, 1.0) for aid in predictions.keys()]
        
        if method == "weighted_mean":
            combined_weights = [w * c for w, c in zip(weights, confidences)]
            if sum(combined_weights) == 0:
                return np.mean(values), np.mean(confidences)
            
            prediction = np.average(values, weights=combined_weights)
            confidence = self.confidence_aggregator.aggregate_weighted(
                confidences, weights
            )
        elif method == "median":
            prediction = np.median(values)
            confidence = self.confidence_aggregator.aggregate_median(confidences)
        else:
            prediction = np.mean(values)
            confidence = self.confidence_aggregator.aggregate_mean(confidences)
        
        return prediction, confidence
    
    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get proposal by ID"""
        return self.proposals.get(proposal_id)
    
    def get_active_proposals(self) -> List[Proposal]:
        """Get active proposals"""
        return [
            p for p in self.proposals.values()
            if p.status == ConsensusStatus.VOTING
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get consensus statistics"""
        success_rate = 0.0
        total = self.stats['consensus_reached'] + self.stats['consensus_failed']
        if total > 0:
            success_rate = self.stats['consensus_reached'] / total
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'active_proposals': len(self.get_active_proposals()),
            'completed_proposals': len(self.proposal_history),
            'avg_votes_per_proposal': (
                self.stats['total_votes'] / max(1, self.stats['proposals_created'])
            )
        }

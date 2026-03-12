"""
Consensus Mechanisms for Hivemind
============================================================

Implements various consensus algorithms for collective decision-making:
- Majority voting
- Weighted voting
- Bayesian aggregation
- Delphi method
- Borda count
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from .core import (
    NodeVote,
    SwarmSignal,
    CollectiveDecision,
    SignalDirection,
    ConsensusMethod,
)

logger = logging.getLogger(__name__)


@dataclass
class VotingResult:
    """Result of a voting round"""
    direction: SignalDirection
    score: float  # -1 to 1
    consensus: float  # 0 to 1 (agreement level)
    confidence: float  # 0 to 1
    vote_breakdown: Dict[str, int] = field(default_factory=dict)


class VotingStrategy:
    """
    Base class for voting strategies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def aggregate(self, votes: List[NodeVote]) -> VotingResult:
        """Aggregate votes into a result"""
        raise NotImplementedError


class MajorityVoting(VotingStrategy):
    """Simple majority voting"""
    
    def aggregate(self, votes: List[NodeVote]) -> VotingResult:
        if not votes:
            return VotingResult(
                direction=SignalDirection.NEUTRAL,
                score=0.0,
                consensus=0.0,
                confidence=0.0,
            )
        
        # Count votes by direction category
        bullish = sum(1 for v in votes if v.direction.to_numeric() > 0.1)
        bearish = sum(1 for v in votes if v.direction.to_numeric() < -0.1)
        neutral = len(votes) - bullish - bearish
        
        total = len(votes)
        
        # Determine winner
        if bullish > bearish and bullish > neutral:
            direction = SignalDirection.BUY
            score = bullish / total
        elif bearish > bullish and bearish > neutral:
            direction = SignalDirection.SELL
            score = -bearish / total
        else:
            direction = SignalDirection.NEUTRAL
            score = 0.0
        
        # Calculate consensus
        max_votes = max(bullish, bearish, neutral)
        consensus = max_votes / total
        
        # Average confidence
        confidence = np.mean([v.confidence for v in votes])
        
        return VotingResult(
            direction=direction,
            score=score,
            consensus=consensus,
            confidence=confidence,
            vote_breakdown={'bullish': bullish, 'bearish': bearish, 'neutral': neutral},
        )


class WeightedVoting(VotingStrategy):
    """Weighted voting based on node performance"""
    
    def aggregate(self, votes: List[NodeVote]) -> VotingResult:
        if not votes:
            return VotingResult(
                direction=SignalDirection.NEUTRAL,
                score=0.0,
                consensus=0.0,
                confidence=0.0,
            )
        
        # Calculate weighted sum
        total_weight = sum(v.weight * v.confidence for v in votes)
        if total_weight == 0:
            total_weight = 1.0
        
        weighted_sum = sum(v.weighted_score for v in votes)
        score = weighted_sum / total_weight
        
        # Calculate consensus (weighted variance)
        weighted_variance = sum(
            v.weight * v.confidence * (v.direction.to_numeric() - score) ** 2
            for v in votes
        ) / total_weight
        consensus = max(0, 1 - weighted_variance)
        
        # Weighted confidence
        confidence = sum(v.weight * v.confidence for v in votes) / sum(v.weight for v in votes)
        
        direction = SignalDirection.from_numeric(score)
        
        # Vote breakdown
        bullish = sum(1 for v in votes if v.direction.to_numeric() > 0.1)
        bearish = sum(1 for v in votes if v.direction.to_numeric() < -0.1)
        neutral = len(votes) - bullish - bearish
        
        return VotingResult(
            direction=direction,
            score=score,
            consensus=consensus,
            confidence=confidence,
            vote_breakdown={'bullish': bullish, 'bearish': bearish, 'neutral': neutral},
        )


class BayesianAggregation(VotingStrategy):
    """Bayesian aggregation of opinions"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.prior_bullish = config.get('prior_bullish', 0.33)
        self.prior_bearish = config.get('prior_bearish', 0.33)
        self.prior_neutral = config.get('prior_neutral', 0.34)
    
    def aggregate(self, votes: List[NodeVote]) -> VotingResult:
        if not votes:
            return VotingResult(
                direction=SignalDirection.NEUTRAL,
                score=0.0,
                consensus=0.0,
                confidence=0.0,
            )
        
        # Start with priors
        p_bullish = self.prior_bullish
        p_bearish = self.prior_bearish
        p_neutral = self.prior_neutral
        
        # Update with each vote (Bayesian update)
        for vote in votes:
            signal = vote.direction.to_numeric()
            conf = vote.confidence
            weight = vote.weight
            
            # Likelihood of this vote given each hypothesis
            if signal > 0.1:
                # Bullish vote
                l_bullish = conf * weight
                l_bearish = (1 - conf) * weight * 0.2
                l_neutral = (1 - conf) * weight * 0.5
            elif signal < -0.1:
                # Bearish vote
                l_bullish = (1 - conf) * weight * 0.2
                l_bearish = conf * weight
                l_neutral = (1 - conf) * weight * 0.5
            else:
                # Neutral vote
                l_bullish = (1 - conf) * weight * 0.3
                l_bearish = (1 - conf) * weight * 0.3
                l_neutral = conf * weight
            
            # Normalize likelihoods
            total_l = l_bullish + l_bearish + l_neutral
            if total_l > 0:
                l_bullish /= total_l
                l_bearish /= total_l
                l_neutral /= total_l
            
            # Bayesian update
            p_bullish *= l_bullish
            p_bearish *= l_bearish
            p_neutral *= l_neutral
            
            # Normalize posteriors
            total_p = p_bullish + p_bearish + p_neutral
            if total_p > 0:
                p_bullish /= total_p
                p_bearish /= total_p
                p_neutral /= total_p
        
        # Determine direction from posteriors
        if p_bullish > p_bearish and p_bullish > p_neutral:
            direction = SignalDirection.BUY if p_bullish > 0.6 else SignalDirection.WEAK_BUY
            score = p_bullish - p_bearish
        elif p_bearish > p_bullish and p_bearish > p_neutral:
            direction = SignalDirection.SELL if p_bearish > 0.6 else SignalDirection.WEAK_SELL
            score = p_bullish - p_bearish
        else:
            direction = SignalDirection.NEUTRAL
            score = 0.0
        
        # Consensus is the max probability
        consensus = max(p_bullish, p_bearish, p_neutral)
        
        # Confidence from vote confidences
        confidence = np.mean([v.confidence for v in votes])
        
        return VotingResult(
            direction=direction,
            score=score,
            consensus=consensus,
            confidence=confidence,
            vote_breakdown={
                'p_bullish': round(p_bullish, 3),
                'p_bearish': round(p_bearish, 3),
                'p_neutral': round(p_neutral, 3),
            },
        )


class BordaCount(VotingStrategy):
    """Borda count for ranked preferences"""
    
    def aggregate(self, votes: List[NodeVote]) -> VotingResult:
        if not votes:
            return VotingResult(
                direction=SignalDirection.NEUTRAL,
                score=0.0,
                consensus=0.0,
                confidence=0.0,
            )
        
        # Assign points based on signal strength
        # Strong buy = 3, Buy = 2, Weak buy = 1, Neutral = 0, etc.
        points = {
            SignalDirection.STRONG_BUY: 3,
            SignalDirection.BUY: 2,
            SignalDirection.WEAK_BUY: 1,
            SignalDirection.NEUTRAL: 0,
            SignalDirection.WEAK_SELL: -1,
            SignalDirection.SELL: -2,
            SignalDirection.STRONG_SELL: -3,
        }
        
        # Calculate weighted Borda score
        total_weight = sum(v.weight for v in votes)
        if total_weight == 0:
            total_weight = 1.0
        
        borda_score = sum(
            points.get(v.direction, 0) * v.weight * v.confidence
            for v in votes
        ) / total_weight
        
        # Normalize to -1 to 1
        normalized_score = borda_score / 3.0
        
        direction = SignalDirection.from_numeric(normalized_score)
        
        # Consensus based on score spread
        scores = [points.get(v.direction, 0) for v in votes]
        if len(scores) > 1:
            variance = np.var(scores)
            consensus = max(0, 1 - variance / 9)  # Max variance is 9
        else:
            consensus = 1.0
        
        confidence = np.mean([v.confidence for v in votes])
        
        return VotingResult(
            direction=direction,
            score=normalized_score,
            consensus=consensus,
            confidence=confidence,
        )


class ConflictResolver:
    """
    Resolves conflicts when consensus is low.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_consensus = config.get('min_consensus', 0.5)
    
    def resolve(
        self,
        votes: List[NodeVote],
        swarm_signals: List[SwarmSignal],
    ) -> Tuple[SignalDirection, float, str]:
        """
        Resolve conflicts between votes and signals.
        
        Returns:
            (direction, confidence, resolution_method)
        """
        # Check if there's significant conflict
        if not votes and not swarm_signals:
            return SignalDirection.NEUTRAL, 0.0, "no_data"
        
        # Analyze vote distribution
        if votes:
            bullish_votes = [v for v in votes if v.direction.to_numeric() > 0.1]
            bearish_votes = [v for v in votes if v.direction.to_numeric() < -0.1]
            
            bullish_weight = sum(v.weight * v.confidence for v in bullish_votes)
            bearish_weight = sum(v.weight * v.confidence for v in bearish_votes)
            
            total_weight = bullish_weight + bearish_weight
            if total_weight > 0:
                imbalance = abs(bullish_weight - bearish_weight) / total_weight
            else:
                imbalance = 0
        else:
            imbalance = 0
            bullish_weight = 0
            bearish_weight = 0
        
        # If strong imbalance, go with majority
        if imbalance > 0.6:
            if bullish_weight > bearish_weight:
                return SignalDirection.BUY, imbalance, "strong_majority"
            else:
                return SignalDirection.SELL, imbalance, "strong_majority"
        
        # Check swarm signals for tiebreaker
        if swarm_signals:
            swarm_bullish = sum(1 for s in swarm_signals if s.direction.to_numeric() > 0.1)
            swarm_bearish = sum(1 for s in swarm_signals if s.direction.to_numeric() < -0.1)
            
            if swarm_bullish > swarm_bearish:
                return SignalDirection.WEAK_BUY, 0.5, "swarm_tiebreaker"
            elif swarm_bearish > swarm_bullish:
                return SignalDirection.WEAK_SELL, 0.5, "swarm_tiebreaker"
        
        # High conflict - stay neutral
        return SignalDirection.NEUTRAL, 0.3, "high_conflict_neutral"


class ConsensusEngine:
    """
    Main consensus engine that combines multiple strategies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.default_method = ConsensusMethod(
            config.get('default_method', ConsensusMethod.WEIGHTED_VOTE.value)
        )
        
        # Initialize strategies
        self.strategies = {
            ConsensusMethod.MAJORITY_VOTE: MajorityVoting(config),
            ConsensusMethod.WEIGHTED_VOTE: WeightedVoting(config),
            ConsensusMethod.BAYESIAN: BayesianAggregation(config),
            ConsensusMethod.BORDA_COUNT: BordaCount(config),
        }
        
        self.conflict_resolver = ConflictResolver(config)
    
    def reach_consensus(
        self,
        votes: List[NodeVote],
        swarm_signals: List[SwarmSignal],
        method: Optional[ConsensusMethod] = None,
    ) -> CollectiveDecision:
        """
        Reach consensus from votes and swarm signals.
        """
        method = method or self.default_method
        
        # Get voting result
        strategy = self.strategies.get(method, self.strategies[ConsensusMethod.WEIGHTED_VOTE])
        vote_result = strategy.aggregate(votes)
        
        # Check if consensus is sufficient
        min_consensus = self.config.get('min_consensus', 0.5)
        
        if vote_result.consensus < min_consensus:
            # Try to resolve conflict
            direction, confidence, resolution = self.conflict_resolver.resolve(votes, swarm_signals)
            logger.info(f"Low consensus ({vote_result.consensus:.0%}), resolved via {resolution}")
        else:
            direction = vote_result.direction
            confidence = vote_result.confidence
        
        # Determine action
        if direction.to_numeric() > 0.3:
            action = "BUY"
        elif direction.to_numeric() < -0.3:
            action = "SELL"
        else:
            action = "HOLD"
        
        # Count agreeing/dissenting nodes
        agreeing = sum(
            1 for v in votes
            if (direction.to_numeric() > 0 and v.direction.to_numeric() > 0) or
               (direction.to_numeric() < 0 and v.direction.to_numeric() < 0) or
               (abs(direction.to_numeric()) <= 0.1 and abs(v.direction.to_numeric()) <= 0.1)
        )
        dissenting = len(votes) - agreeing
        
        return CollectiveDecision(
            action=action,
            direction=direction,
            consensus_score=vote_result.consensus,
            confidence=confidence,
            node_votes=votes,
            total_nodes=len(votes),
            agreeing_nodes=agreeing,
            dissenting_nodes=dissenting,
            emergent_signals=swarm_signals,
            consensus_method=method,
        )
    
    def get_strategy(self, method: ConsensusMethod) -> VotingStrategy:
        """Get a specific voting strategy"""
        return self.strategies.get(method, self.strategies[ConsensusMethod.WEIGHTED_VOTE])

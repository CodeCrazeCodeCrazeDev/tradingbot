"""
Multi-Method Causal Attribution System

Fix #6: Your Three Memories Will Suffer from Attribution Error

The attack: You separate Decision, Outcome, and Failure memory—excellent design. 
But the causal link between them is where this breaks.

Fix: Require multiple independent attribution methods (counterfactual replay, 
control group comparison, statistical contribution analysis) and store disagreement 
as uncertainty in Failure Memory. Never act on single-attribution failures.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import logging
import numpy as np

logger = logging.getLogger(__name__)


class AttributionMethod(Enum):
    """Methods for attributing outcomes to decisions"""
    COUNTERFACTUAL_REPLAY = "counterfactual_replay"
    CONTROL_GROUP_COMPARISON = "control_group_comparison"
    STATISTICAL_CONTRIBUTION = "statistical_contribution"
    TEMPORAL_PROXIMITY = "temporal_proximity"
    STRUCTURAL_MODEL = "structural_model"


class AttributionConfidence(Enum):
    """Confidence level in attribution"""
    HIGH = "high"       # All methods agree
    MEDIUM = "medium"   # Most methods agree
    LOW = "low"         # Methods disagree
    UNCERTAIN = "uncertain"  # Cannot determine


@dataclass
class AttributionResult:
    """Result from a single attribution method"""
    method: AttributionMethod
    decision_id: str
    outcome_id: str
    attribution_score: float  # -1 to 1, negative = harmful, positive = helpful
    confidence: float  # 0-1
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class MultiMethodAttribution:
    """Combined attribution from multiple methods"""
    decision_id: str
    outcome_id: str
    individual_results: List[AttributionResult]
    consensus_score: float  # Aggregated score
    agreement_level: float  # How much methods agree (0-1)
    confidence_level: AttributionConfidence
    disagreement_details: Dict[str, Any]  # Where methods disagree
    uncertainty_quantified: float  # Uncertainty to store in Failure Memory
    action_recommended: str  # What action to take based on this attribution


class CounterfactualReplayAttribution:
    """
    Attribution via counterfactual replay:
    Replay the same decision conditions and see if outcome recurs.
    """
    
    def __init__(self, replay_buffer_size: int = 100):
        self.replay_buffer: Dict[str, List[Dict]] = defaultdict(list)
        self.buffer_size = replay_buffer_size
    
    def can_attribute(
        self,
        decision_id: str,
        decision_context: Dict,
        outcome: Dict
    ) -> Tuple[bool, float, Dict]:
        """
        Attempt attribution via replay.
        
        Returns: (can_attribute, confidence, details)
        """
        # Check if we have similar historical decisions
        similar_decisions = self._find_similar_decisions(decision_context)
        
        if len(similar_decisions) < 3:
            return False, 0.0, {'reason': 'insufficient_similar_decisions'}
        
        # Compare outcomes
        similar_outcomes = [d['outcome'] for d in similar_decisions]
        current_outcome_type = 'positive' if outcome.get('pnl', 0) > 0 else 'negative'
        
        consistent_outcomes = sum(
            1 for o in similar_outcomes
            if ('positive' if o.get('pnl', 0) > 0 else 'negative') == current_outcome_type
        )
        
        consistency_rate = consistent_outcomes / len(similar_outcomes)
        
        # Store in buffer
        self.replay_buffer[decision_id].append({
            'context': decision_context,
            'outcome': outcome,
            'timestamp': datetime.utcnow()
        })
        
        # Keep buffer size limited
        if len(self.replay_buffer[decision_id]) > self.buffer_size:
            self.replay_buffer[decision_id].pop(0)
        
        return True, consistency_rate, {
            'similar_decisions': len(similar_decisions),
            'consistency_rate': consistency_rate
        }
    
    def _find_similar_decisions(self, context: Dict) -> List[Dict]:
        """Find historically similar decisions"""
        similar = []
        
        for decision_id, replays in self.replay_buffer.items():
            for replay in replays:
                if self._context_similarity(context, replay['context']) > 0.8:
                    similar.append(replay)
        
        return similar
    
    def _context_similarity(self, ctx1: Dict, ctx2: Dict) -> float:
        """Calculate similarity between decision contexts"""
        # Simplified similarity - would be more sophisticated in production
        score = 0.0
        keys = ['symbol', 'regime', 'signal_type']
        
        for key in keys:
            if ctx1.get(key) == ctx2.get(key):
                score += 0.25
        
        # Position size similarity
        size_diff = abs(ctx1.get('position_size', 0) - ctx2.get('position_size', 0))
        if size_diff < 0.1:
            score += 0.25
        
        return score


class ControlGroupAttribution:
    """
    Attribution via control group comparison:
    Compare outcomes of similar strategies that didn't take this specific decision.
    """
    
    def __init__(self):
        self.control_outcomes: Dict[str, List[float]] = defaultdict(list)
    
    def can_attribute(
        self,
        decision_id: str,
        strategy_signature: str,
        decision_outcome: Dict,
        control_strategies: List[str]
    ) -> Tuple[bool, float, Dict]:
        """
        Compare decision outcome to control group outcomes.
        
        Returns: (can_attribute, confidence, details)
        """
        if not control_strategies:
            return False, 0.0, {'reason': 'no_control_strategies'}
        
        # Get control outcomes
        control_pnls = []
        for ctrl_id in control_strategies:
            if ctrl_id in self.control_outcomes:
                control_pnls.extend(self.control_outcomes[ctrl_id])
        
        if len(control_pnls) < 5:
            return False, 0.0, {'reason': 'insufficient_control_data'}
        
        # Compare
        decision_pnl = decision_outcome.get('pnl', 0)
        control_mean = np.mean(control_pnls)
        control_std = np.std(control_pnls) if len(control_pnls) > 1 else 0.01
        
        # Z-score of decision vs control
        if control_std > 0:
            z_score = (decision_pnl - control_mean) / control_std
        else:
            z_score = 0
        
        # Confidence based on z-score magnitude
        confidence = min(1.0, abs(z_score) / 2.0)
        
        return True, confidence, {
            'control_mean': control_mean,
            'decision_pnl': decision_pnl,
            'z_score': z_score,
            'control_sample_size': len(control_pnls)
        }
    
    def record_control_outcome(self, strategy_id: str, pnl: float):
        """Record outcome from a control strategy"""
        self.control_outcomes[strategy_id].append(pnl)
        # Keep only recent outcomes
        if len(self.control_outcomes[strategy_id]) > 50:
            self.control_outcomes[strategy_id].pop(0)


class StatisticalContributionAttribution:
    """
    Attribution via statistical contribution analysis:
    Analyze how much this decision contributed to portfolio outcome.
    """
    
    def __init__(self):
        self.decision_outcomes: Dict[str, List[float]] = defaultdict(list)
    
    def can_attribute(
        self,
        decision_id: str,
        portfolio_outcome: float,
        decision_outcome: Dict
    ) -> Tuple[bool, float, Dict]:
        """
        Calculate statistical contribution of decision to portfolio.
        
        Returns: (can_attribute, confidence, details)
        """
        decision_pnl = decision_outcome.get('pnl', 0)
        decision_size = decision_outcome.get('size', 0)
        
        # Simple contribution = (decision_pnl / portfolio_outcome) if portfolio moved
        if abs(portfolio_outcome) > 0.001:
            contribution_pct = decision_pnl / portfolio_outcome
        else:
            contribution_pct = 0
        
        # Confidence based on position size relative to portfolio
        # Larger positions = more confident in attribution
        confidence = min(1.0, decision_size * 5)  # Scale factor
        
        return True, confidence, {
            'contribution_pct': contribution_pct,
            'decision_pnl': decision_pnl,
            'portfolio_outcome': portfolio_outcome,
            'position_size': decision_size
        }


class MultiMethodAttributionEngine:
    """
    Multi-Method Causal Attribution Engine
    
    Combines multiple independent attribution methods and quantifies
    disagreement as uncertainty. Never acts on single-attribution failures.
    
    Methods:
    1. Counterfactual Replay - Replay decision conditions
    2. Control Group Comparison - Compare to similar strategies
    3. Statistical Contribution - Analyze portfolio contribution
    
    Aggregation:
    - All methods agree: High confidence
    - 2/3 agree: Medium confidence
    - No agreement: Low confidence, high uncertainty
    """
    
    def __init__(
        self,
        min_methods_required: int = 2,
        agreement_threshold: float = 0.6
    ):
        self.min_methods_required = min_methods_required
        self.agreement_threshold = agreement_threshold
        
        # Attribution method instances
        self.counterfactual = CounterfactualReplayAttribution()
        self.control_group = ControlGroupAttribution()
        self.statistical = StatisticalContributionAttribution()
        
        # History
        self.attribution_history: List[MultiMethodAttribution] = []
        self.uncertainty_by_decision: Dict[str, float] = {}
    
    def attribute_outcome(
        self,
        decision_id: str,
        outcome_id: str,
        decision_context: Dict,
        outcome: Dict,
        control_strategies: Optional[List[str]] = None,
        portfolio_outcome: Optional[float] = None
    ) -> MultiMethodAttribution:
        """
        Perform multi-method attribution for a decision-outcome pair.
        
        Returns:
            MultiMethodAttribution with consensus and uncertainty
        """
        individual_results = []
        
        # Method 1: Counterfactual Replay
        can_attr, conf, details = self.counterfactual.can_attribute(
            decision_id, decision_context, outcome
        )
        if can_attr:
            individual_results.append(AttributionResult(
                method=AttributionMethod.COUNTERFACTUAL_REPLAY,
                decision_id=decision_id,
                outcome_id=outcome_id,
                attribution_score=outcome.get('pnl', 0) * conf,
                confidence=conf,
                details=details,
                timestamp=datetime.utcnow()
            ))
        
        # Method 2: Control Group Comparison
        if control_strategies:
            can_attr, conf, details = self.control_group.can_attribute(
                decision_id, decision_context.get('strategy_signature', ''),
                outcome, control_strategies
            )
            if can_attr:
                individual_results.append(AttributionResult(
                    method=AttributionMethod.CONTROL_GROUP_COMPARISON,
                    decision_id=decision_id,
                    outcome_id=outcome_id,
                    attribution_score=outcome.get('pnl', 0) * conf,
                    confidence=conf,
                    details=details,
                    timestamp=datetime.utcnow()
                ))
        
        # Method 3: Statistical Contribution
        if portfolio_outcome is not None:
            can_attr, conf, details = self.statistical.can_attribute(
                decision_id, portfolio_outcome, outcome
            )
            if can_attr:
                individual_results.append(AttributionResult(
                    method=AttributionMethod.STATISTICAL_CONTRIBUTION,
                    decision_id=decision_id,
                    outcome_id=outcome_id,
                    attribution_score=outcome.get('pnl', 0) * conf,
                    confidence=conf,
                    details=details,
                    timestamp=datetime.utcnow()
                ))
        
        # Calculate consensus
        consensus_score, agreement_level, disagreement = self._calculate_consensus(
            individual_results
        )
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(
            len(individual_results), agreement_level
        )
        
        # Quantify uncertainty
        uncertainty = 1.0 - agreement_level
        
        # Determine action
        action = self._determine_action(
            consensus_score, confidence_level, len(individual_results)
        )
        
        multi_attr = MultiMethodAttribution(
            decision_id=decision_id,
            outcome_id=outcome_id,
            individual_results=individual_results,
            consensus_score=consensus_score,
            agreement_level=agreement_level,
            confidence_level=confidence_level,
            disagreement_details=disagreement,
            uncertainty_quantified=uncertainty,
            action_recommended=action
        )
        
        self.attribution_history.append(multi_attr)
        self.uncertainty_by_decision[decision_id] = uncertainty
        
        logger.info(
            f"Multi-method attribution for {decision_id}: "
            f"consensus={consensus_score:.2f}, "
            f"agreement={agreement_level:.2f}, "
            f"methods={len(individual_results)}, "
            f"action={action}"
        )
        
        return multi_attr
    
    def _calculate_consensus(
        self,
        results: List[AttributionResult]
    ) -> Tuple[float, float, Dict]:
        """
        Calculate consensus score and agreement level.
        
        Returns: (consensus_score, agreement_level, disagreement_details)
        """
        if not results:
            return 0.0, 0.0, {'reason': 'no_results'}
        
        if len(results) == 1:
            return results[0].attribution_score, 0.0, {'reason': 'single_method'}
        
        # Average attribution scores (weighted by confidence)
        total_weight = sum(r.confidence for r in results)
        if total_weight > 0:
            consensus_score = sum(
                r.attribution_score * r.confidence for r in results
            ) / total_weight
        else:
            consensus_score = 0.0
        
        # Calculate agreement
        # Agreement = 1 - (variance of attribution scores)
        scores = [r.attribution_score for r in results]
        if len(scores) > 1:
            variance = np.var(scores)
            agreement_level = max(0, 1.0 - variance * 4)  # Scale factor
        else:
            agreement_level = 0.0
        
        # Disagreement details
        disagreement = {
            'score_range': max(scores) - min(scores) if scores else 0,
            'sign_disagreement': any(s > 0 for s in scores) and any(s < 0 for s in scores),
            'method_count': len(results)
        }
        
        return consensus_score, agreement_level, disagreement
    
    def _determine_confidence_level(
        self,
        method_count: int,
        agreement_level: float
    ) -> AttributionConfidence:
        """Determine confidence level based on method count and agreement"""
        if method_count < 2:
            return AttributionConfidence.UNCERTAIN
        
        if agreement_level > 0.8 and method_count >= 3:
            return AttributionConfidence.HIGH
        elif agreement_level > 0.6 and method_count >= 2:
            return AttributionConfidence.MEDIUM
        else:
            return AttributionConfidence.LOW
    
    def _determine_action(
        self,
        consensus_score: float,
        confidence_level: AttributionConfidence,
        method_count: int
    ) -> str:
        """Determine recommended action based on attribution results"""
        # Never act on single-attribution failures
        if method_count < 2:
            return "insufficient_attribution_hold"
        
        # Low confidence = don't act
        if confidence_level == AttributionConfidence.LOW:
            return "low_confidence_monitor"
        
        # High confidence negative = investigate
        if consensus_score < -0.1 and confidence_level == AttributionConfidence.HIGH:
            return "high_confidence_investigate"
        
        # Medium confidence negative = enhanced monitoring
        if consensus_score < -0.05 and confidence_level == AttributionConfidence.MEDIUM:
            return "enhanced_monitoring"
        
        return "no_action"
    
    def get_uncertainty_for_failure_memory(self, decision_id: str) -> float:
        """Get quantified uncertainty to store in Failure Memory"""
        return self.uncertainty_by_decision.get(decision_id, 1.0)


# Factory function
def create_multi_method_attribution_engine(
    min_methods_required: int = 2
) -> MultiMethodAttributionEngine:
    """Factory function to create attribution engine"""
    
    return MultiMethodAttributionEngine(
        min_methods_required=min_methods_required
    )

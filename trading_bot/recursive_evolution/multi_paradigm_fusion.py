"""
Multi-Paradigm Decision Fusion
===============================

Advanced decision fusion system that combines multiple trading paradigms,
methodologies, and AI approaches to make superior trading decisions.

PARADIGMS INTEGRATED:
- Technical Analysis
- Fundamental Analysis
- Quantitative/Statistical
- Machine Learning
- Behavioral/Psychological
- Order Flow/Microstructure
- Sentiment Analysis
- Alternative Data
- Pattern Recognition
- Game Theory

Each paradigm provides independent analysis, and the system fuses them
using advanced ensemble methods with confidence weighting.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class ParadigmType(Enum):
    """Types of trading paradigms"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    QUANTITATIVE = "quantitative"
    MACHINE_LEARNING = "machine_learning"
    BEHAVIORAL = "behavioral"
    ORDER_FLOW = "order_flow"
    SENTIMENT = "sentiment"
    ALTERNATIVE_DATA = "alternative_data"
    PATTERN_RECOGNITION = "pattern_recognition"
    GAME_THEORY = "game_theory"


class DecisionType(Enum):
    """Types of trading decisions"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    HOLD = "hold"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class ParadigmDecision:
    """Decision from a single paradigm"""
    paradigm: ParadigmType
    decision: DecisionType
    confidence: float  # 0-1
    reasoning: str
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
    risk_factors: List[str]
    expected_return: float
    expected_risk: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DecisionConfidence:
    """Confidence metrics for a decision"""
    overall_confidence: float
    paradigm_agreement: float  # How much paradigms agree
    evidence_strength: float
    risk_adjusted_confidence: float
    uncertainty_level: float


@dataclass
class FusedDecision:
    """Final fused decision from all paradigms"""
    decision_id: str
    symbol: str
    timestamp: datetime
    
    # Final decision
    final_decision: DecisionType
    confidence: DecisionConfidence
    
    # Paradigm contributions
    paradigm_decisions: List[ParadigmDecision]
    paradigm_weights: Dict[ParadigmType, float]
    
    # Consensus analysis
    consensus_level: float  # 0-1
    dissenting_paradigms: List[ParadigmType]
    
    # Aggregated metrics
    expected_return: float
    expected_risk: float
    risk_reward_ratio: float
    
    # Reasoning
    primary_reasoning: str
    supporting_factors: List[str]
    risk_factors: List[str]
    
    # Actionable recommendations
    recommended_action: str
    position_size_multiplier: float  # 0-1
    stop_loss_suggestion: Optional[float]
    take_profit_suggestion: Optional[float]


class MultiParadigmFusion:
    """
    Multi-paradigm decision fusion system.
    
    This system:
    1. Collects decisions from multiple paradigms
    2. Weights paradigms based on historical performance
    3. Detects consensus and disagreement
    4. Fuses decisions using advanced ensemble methods
    5. Provides confidence-weighted recommendations
    6. Learns which paradigms work best in which conditions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Paradigm weights (learned over time)
        self.paradigm_weights: Dict[ParadigmType, float] = {
            paradigm: 1.0 for paradigm in ParadigmType
        }
        
        # Performance tracking per paradigm
        self.paradigm_performance: Dict[ParadigmType, List[float]] = defaultdict(list)
        
        # Decision history
        self.decision_history: List[FusedDecision] = []
        
        # Fusion parameters
        self.min_consensus_threshold = self.config.get('min_consensus', 0.6)
        self.min_confidence_threshold = self.config.get('min_confidence', 0.7)
        self.enable_adaptive_weighting = self.config.get('adaptive_weighting', True)
        
        logger.info("MultiParadigmFusion initialized with adaptive weighting")
    
    def fuse_decisions(self, symbol: str, 
                      paradigm_decisions: List[ParadigmDecision],
                      context: Optional[Dict[str, Any]] = None) -> FusedDecision:
        """
        Fuse decisions from multiple paradigms into a single decision.
        """
        decision_id = f"FUSED-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Fusing {len(paradigm_decisions)} paradigm decisions for {symbol}")
        
        # 1. Calculate paradigm weights for this context
        weights = self._calculate_paradigm_weights(paradigm_decisions, context)
        
        # 2. Analyze consensus
        consensus_level, dissenting = self._analyze_consensus(paradigm_decisions)
        
        # 3. Fuse decisions using weighted voting
        final_decision = self._weighted_voting(paradigm_decisions, weights)
        
        # 4. Calculate confidence
        confidence = self._calculate_confidence(paradigm_decisions, weights, consensus_level)
        
        # 5. Aggregate metrics
        expected_return = self._aggregate_returns(paradigm_decisions, weights)
        expected_risk = self._aggregate_risks(paradigm_decisions, weights)
        risk_reward = expected_return / (expected_risk + 1e-8)
        
        # 6. Generate reasoning
        primary_reasoning = self._generate_reasoning(paradigm_decisions, weights, final_decision)
        supporting_factors = self._collect_supporting_factors(paradigm_decisions, final_decision)
        risk_factors = self._collect_risk_factors(paradigm_decisions)
        
        # 7. Generate recommendations
        recommended_action = self._generate_recommendation(final_decision, confidence, risk_reward)
        position_size = self._calculate_position_size(confidence, risk_reward, expected_risk)
        stop_loss = self._suggest_stop_loss(paradigm_decisions, expected_risk)
        take_profit = self._suggest_take_profit(paradigm_decisions, expected_return)
        
        fused = FusedDecision(
            decision_id=decision_id,
            symbol=symbol,
            timestamp=datetime.utcnow(),
            final_decision=final_decision,
            confidence=confidence,
            paradigm_decisions=paradigm_decisions,
            paradigm_weights=weights,
            consensus_level=consensus_level,
            dissenting_paradigms=dissenting,
            expected_return=expected_return,
            expected_risk=expected_risk,
            risk_reward_ratio=risk_reward,
            primary_reasoning=primary_reasoning,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors,
            recommended_action=recommended_action,
            position_size_multiplier=position_size,
            stop_loss_suggestion=stop_loss,
            take_profit_suggestion=take_profit
        )
        
        self.decision_history.append(fused)
        
        logger.info(f"Fused decision: {final_decision.value} with confidence {confidence.overall_confidence:.2f}")
        
        return fused
    
    def _calculate_paradigm_weights(self, decisions: List[ParadigmDecision],
                                   context: Optional[Dict[str, Any]]) -> Dict[ParadigmType, float]:
        """Calculate weights for each paradigm based on performance and context"""
        
        weights = {}
        
        for decision in decisions:
            paradigm = decision.paradigm
            
            # Base weight from global performance
            if self.enable_adaptive_weighting and paradigm in self.paradigm_performance:
                perf_history = self.paradigm_performance[paradigm]
                if perf_history:
                    # Recent performance weighted more
                    recent_perf = np.mean(perf_history[-20:])
                    base_weight = max(0.1, min(2.0, recent_perf))
                else:
                    base_weight = 1.0
            else:
                base_weight = self.paradigm_weights.get(paradigm, 1.0)
            
            # Adjust weight based on paradigm confidence
            confidence_weight = decision.confidence
            
            # Context-based adjustments
            context_weight = 1.0
            if context:
                # In volatile markets, favor risk-aware paradigms
                if context.get('volatility', 0) > 0.7:
                    if paradigm in [ParadigmType.QUANTITATIVE, ParadigmType.MACHINE_LEARNING]:
                        context_weight = 1.2
                    elif paradigm == ParadigmType.TECHNICAL:
                        context_weight = 0.8
                
                # In trending markets, favor trend-following paradigms
                if context.get('regime') == 'trending':
                    if paradigm in [ParadigmType.TECHNICAL, ParadigmType.PATTERN_RECOGNITION]:
                        context_weight = 1.3
                
                # When institutional activity detected, favor order flow
                if context.get('institutional_activity', False):
                    if paradigm == ParadigmType.ORDER_FLOW:
                        context_weight = 1.5
            
            # Final weight
            weights[paradigm] = base_weight * confidence_weight * context_weight
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def _analyze_consensus(self, decisions: List[ParadigmDecision]) -> Tuple[float, List[ParadigmType]]:
        """Analyze consensus among paradigms"""
        
        if not decisions:
            return 0.0, []
        
        # Convert decisions to numerical scores
        decision_scores = {
            DecisionType.STRONG_SELL: -3,
            DecisionType.SELL: -2,
            DecisionType.WEAK_SELL: -1,
            DecisionType.HOLD: 0,
            DecisionType.WEAK_BUY: 1,
            DecisionType.BUY: 2,
            DecisionType.STRONG_BUY: 3
        }
        
        scores = [decision_scores[d.decision] for d in decisions]
        
        # Calculate consensus as inverse of variance
        if len(scores) > 1:
            variance = np.var(scores)
            # Normalize: variance of 0 = consensus 1.0, variance of 9 = consensus 0.0
            consensus = max(0.0, 1.0 - (variance / 9.0))
        else:
            consensus = 1.0
        
        # Find dissenting paradigms (those far from mean)
        mean_score = np.mean(scores)
        dissenting = []
        
        for decision, score in zip(decisions, scores):
            if abs(score - mean_score) > 2:  # More than 2 levels away
                dissenting.append(decision.paradigm)
        
        return consensus, dissenting
    
    def _weighted_voting(self, decisions: List[ParadigmDecision],
                        weights: Dict[ParadigmType, float]) -> DecisionType:
        """Perform weighted voting to determine final decision"""
        
        # Map decisions to scores
        decision_scores = {
            DecisionType.STRONG_SELL: -3,
            DecisionType.SELL: -2,
            DecisionType.WEAK_SELL: -1,
            DecisionType.HOLD: 0,
            DecisionType.WEAK_BUY: 1,
            DecisionType.BUY: 2,
            DecisionType.STRONG_BUY: 3
        }
        
        # Calculate weighted score
        weighted_score = 0.0
        total_weight = 0.0
        
        for decision in decisions:
            weight = weights.get(decision.paradigm, 1.0)
            score = decision_scores[decision.decision]
            weighted_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            avg_score = weighted_score / total_weight
        else:
            avg_score = 0.0
        
        # Map score back to decision
        if avg_score >= 2.5:
            return DecisionType.STRONG_BUY
        elif avg_score >= 1.5:
            return DecisionType.BUY
        elif avg_score >= 0.5:
            return DecisionType.WEAK_BUY
        elif avg_score <= -2.5:
            return DecisionType.STRONG_SELL
        elif avg_score <= -1.5:
            return DecisionType.SELL
        elif avg_score <= -0.5:
            return DecisionType.WEAK_SELL
        else:
            return DecisionType.HOLD
    
    def _calculate_confidence(self, decisions: List[ParadigmDecision],
                             weights: Dict[ParadigmType, float],
                             consensus: float) -> DecisionConfidence:
        """Calculate comprehensive confidence metrics"""
        
        # Weighted average of paradigm confidences
        weighted_conf = sum(d.confidence * weights.get(d.paradigm, 1.0) for d in decisions)
        total_weight = sum(weights.values())
        overall_confidence = weighted_conf / total_weight if total_weight > 0 else 0.5
        
        # Evidence strength
        total_supporting = sum(len(d.supporting_evidence) for d in decisions)
        total_contradicting = sum(len(d.contradicting_evidence) for d in decisions)
        total_evidence = total_supporting + total_contradicting
        
        if total_evidence > 0:
            evidence_strength = total_supporting / total_evidence
        else:
            evidence_strength = 0.5
        
        # Risk-adjusted confidence
        avg_risk = np.mean([d.expected_risk for d in decisions])
        risk_adjustment = max(0.5, 1.0 - avg_risk)
        risk_adjusted_confidence = overall_confidence * risk_adjustment
        
        # Uncertainty (inverse of consensus)
        uncertainty = 1.0 - consensus
        
        return DecisionConfidence(
            overall_confidence=overall_confidence,
            paradigm_agreement=consensus,
            evidence_strength=evidence_strength,
            risk_adjusted_confidence=risk_adjusted_confidence,
            uncertainty_level=uncertainty
        )
    
    def _aggregate_returns(self, decisions: List[ParadigmDecision],
                          weights: Dict[ParadigmType, float]) -> float:
        """Aggregate expected returns from paradigms"""
        
        weighted_return = 0.0
        total_weight = 0.0
        
        for decision in decisions:
            weight = weights.get(decision.paradigm, 1.0)
            weighted_return += decision.expected_return * weight
            total_weight += weight
        
        return weighted_return / total_weight if total_weight > 0 else 0.0
    
    def _aggregate_risks(self, decisions: List[ParadigmDecision],
                        weights: Dict[ParadigmType, float]) -> float:
        """Aggregate expected risks from paradigms"""
        
        # Use maximum risk (conservative approach)
        risks = [d.expected_risk for d in decisions]
        return max(risks) if risks else 0.5
    
    def _generate_reasoning(self, decisions: List[ParadigmDecision],
                           weights: Dict[ParadigmType, float],
                           final_decision: DecisionType) -> str:
        """Generate primary reasoning for the decision"""
        
        # Find paradigms that agree with final decision
        agreeing = [d for d in decisions if self._decisions_agree(d.decision, final_decision)]
        
        if not agreeing:
            return "Mixed signals across paradigms - proceeding with caution"
        
        # Get highest weighted agreeing paradigm
        best_paradigm = max(agreeing, key=lambda d: weights.get(d.paradigm, 0))
        
        return f"{best_paradigm.paradigm.value.replace('_', ' ').title()}: {best_paradigm.reasoning}"
    
    def _decisions_agree(self, d1: DecisionType, d2: DecisionType) -> bool:
        """Check if two decisions are in agreement"""
        
        bullish = [DecisionType.WEAK_BUY, DecisionType.BUY, DecisionType.STRONG_BUY]
        bearish = [DecisionType.WEAK_SELL, DecisionType.SELL, DecisionType.STRONG_SELL]
        
        if d1 in bullish and d2 in bullish:
            return True
        if d1 in bearish and d2 in bearish:
            return True
        if d1 == DecisionType.HOLD and d2 == DecisionType.HOLD:
            return True
        
        return False
    
    def _collect_supporting_factors(self, decisions: List[ParadigmDecision],
                                   final_decision: DecisionType) -> List[str]:
        """Collect supporting factors for the decision"""
        
        factors = []
        
        for decision in decisions:
            if self._decisions_agree(decision.decision, final_decision):
                factors.extend(decision.supporting_evidence[:2])  # Top 2 from each
        
        # Remove duplicates while preserving order
        seen = set()
        unique_factors = []
        for factor in factors:
            if factor not in seen:
                seen.add(factor)
                unique_factors.append(factor)
        
        return unique_factors[:5]  # Top 5 overall
    
    def _collect_risk_factors(self, decisions: List[ParadigmDecision]) -> List[str]:
        """Collect all risk factors"""
        
        all_risks = []
        for decision in decisions:
            all_risks.extend(decision.risk_factors)
        
        # Remove duplicates
        return list(set(all_risks))
    
    def _generate_recommendation(self, decision: DecisionType,
                                confidence: DecisionConfidence,
                                risk_reward: float) -> str:
        """Generate actionable recommendation"""
        
        if confidence.overall_confidence < self.min_confidence_threshold:
            return "WAIT - Confidence too low for action"
        
        if confidence.uncertainty_level > 0.5:
            return "MONITOR - High uncertainty, wait for clarity"
        
        if risk_reward < 1.5:
            return "AVOID - Risk/reward ratio unfavorable"
        
        if decision in [DecisionType.STRONG_BUY, DecisionType.BUY]:
            return f"BUY - Strong consensus with {confidence.overall_confidence:.1%} confidence"
        elif decision == DecisionType.WEAK_BUY:
            return f"CONSIDER BUY - Moderate signal with {confidence.overall_confidence:.1%} confidence"
        elif decision in [DecisionType.STRONG_SELL, DecisionType.SELL]:
            return f"SELL - Strong consensus with {confidence.overall_confidence:.1%} confidence"
        elif decision == DecisionType.WEAK_SELL:
            return f"CONSIDER SELL - Moderate signal with {confidence.overall_confidence:.1%} confidence"
        else:
            return "HOLD - No clear directional signal"
    
    def _calculate_position_size(self, confidence: DecisionConfidence,
                                 risk_reward: float,
                                 expected_risk: float) -> float:
        """Calculate position size multiplier based on confidence and risk"""
        
        # Base size from confidence
        base_size = confidence.risk_adjusted_confidence
        
        # Adjust for risk/reward
        if risk_reward > 3.0:
            rr_multiplier = 1.2
        elif risk_reward > 2.0:
            rr_multiplier = 1.0
        elif risk_reward > 1.5:
            rr_multiplier = 0.8
        else:
            rr_multiplier = 0.5
        
        # Adjust for expected risk
        risk_multiplier = max(0.5, 1.0 - expected_risk)
        
        # Final size
        size = base_size * rr_multiplier * risk_multiplier
        
        return np.clip(size, 0.1, 1.0)
    
    def _suggest_stop_loss(self, decisions: List[ParadigmDecision],
                          expected_risk: float) -> Optional[float]:
        """Suggest stop loss level"""
        
        # Use expected risk as basis
        # This would be calculated relative to entry price in production
        stop_distance = expected_risk * 2.0  # 2x expected risk
        
        return stop_distance if stop_distance > 0 else None
    
    def _suggest_take_profit(self, decisions: List[ParadigmDecision],
                            expected_return: float) -> Optional[float]:
        """Suggest take profit level"""
        
        # Use expected return as basis
        tp_distance = expected_return * 0.8  # 80% of expected return
        
        return tp_distance if tp_distance > 0 else None
    
    def update_paradigm_performance(self, paradigm: ParadigmType, performance: float):
        """Update performance tracking for a paradigm"""
        
        self.paradigm_performance[paradigm].append(performance)
        
        # Update weight if adaptive
        if self.enable_adaptive_weighting:
            recent_perf = self.paradigm_performance[paradigm][-20:]
            avg_perf = np.mean(recent_perf)
            self.paradigm_weights[paradigm] = max(0.1, min(2.0, avg_perf))
    
    def get_fusion_stats(self) -> Dict[str, Any]:
        """Get statistics about decision fusion"""
        
        if not self.decision_history:
            return {'total_decisions': 0}
        
        total = len(self.decision_history)
        
        # Decision distribution
        decision_counts = defaultdict(int)
        for decision in self.decision_history:
            decision_counts[decision.final_decision.value] += 1
        
        # Average metrics
        avg_confidence = np.mean([d.confidence.overall_confidence for d in self.decision_history])
        avg_consensus = np.mean([d.consensus_level for d in self.decision_history])
        avg_risk_reward = np.mean([d.risk_reward_ratio for d in self.decision_history])
        
        # Paradigm weights
        current_weights = {p.value: w for p, w in self.paradigm_weights.items()}
        
        return {
            'total_decisions': total,
            'decision_distribution': dict(decision_counts),
            'average_confidence': avg_confidence,
            'average_consensus': avg_consensus,
            'average_risk_reward': avg_risk_reward,
            'paradigm_weights': current_weights
        }


def quick_start_fusion(config: Optional[Dict[str, Any]] = None) -> MultiParadigmFusion:
    """Quick start function for multi-paradigm fusion"""
    return MultiParadigmFusion(config)

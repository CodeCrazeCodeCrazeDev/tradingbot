"""
Innovative Decision Engine - Orchestrates 110 Decision Concepts

This engine combines all 110 decision-making concepts across 11 categories
to produce robust, multi-perspective trading decisions.

Author: AlphaAlgo Innovation Lab
"""

import logging
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import Counter

from .core_types import (
    DecisionConcept, DecisionContext, DecisionResult, AggregatedDecision,
    DecisionCategory, DecisionAction, DecisionUrgency
)

from .concepts_1_cognitive import COGNITIVE_CONCEPTS
from .concepts_2_probabilistic import PROBABILISTIC_CONCEPTS
from .concepts_3_behavioral import BEHAVIORAL_CONCEPTS
from .concepts_4_game_theory import GAME_THEORY_CONCEPTS
from .concepts_5_temporal import TEMPORAL_CONCEPTS
from .concepts_6_risk import RISK_CONCEPTS
from .concepts_7_microstructure import MICROSTRUCTURE_CONCEPTS
from .concepts_8_adaptive import ADAPTIVE_CONCEPTS
from .concepts_9_multiagent import MULTIAGENT_CONCEPTS
from .concepts_10_meta import META_CONCEPTS
from .concepts_11_quantitative_edge import QUANTITATIVE_EDGE_CONCEPTS

logger = logging.getLogger(__name__)


class InnovativeDecisionEngine:
    """
    Master engine that orchestrates all 100 decision concepts.
    
    Features:
    - Runs all 100 concepts in parallel
    - Aggregates decisions using multiple methods
    - Provides confidence-weighted final decision
    - Tracks concept performance for adaptive weighting
    - Generates comprehensive reasoning chains
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize all 100 concepts
        self.concepts: List[DecisionConcept] = []
        self._initialize_concepts()
        
        # Category weights
        self.category_weights = {
            DecisionCategory.COGNITIVE: 1.0,
            DecisionCategory.PROBABILISTIC: 1.0,
            DecisionCategory.BEHAVIORAL: 0.9,
            DecisionCategory.GAME_THEORY: 0.8,
            DecisionCategory.TEMPORAL: 1.0,
            DecisionCategory.RISK_AWARE: 1.2,  # Risk gets higher weight
            DecisionCategory.MICROSTRUCTURE: 0.9,
            DecisionCategory.ADAPTIVE: 1.0,
            DecisionCategory.MULTI_AGENT: 0.9,
            DecisionCategory.META: 1.1,
            DecisionCategory.QUANTITATIVE_EDGE: 1.15,  # Quant edge gets elevated weight
        }
        
        # Concept performance tracking
        self.concept_accuracy: Dict[int, List[bool]] = {c.concept_id: [] for c in self.concepts}
        
        # Decision history
        self.decision_history: List[AggregatedDecision] = []
        
        logger.info(f"InnovativeDecisionEngine initialized with {len(self.concepts)} concepts")
    
    def _initialize_concepts(self):
        """Initialize all 100 decision concepts"""
        all_concept_classes = (
            COGNITIVE_CONCEPTS +
            PROBABILISTIC_CONCEPTS +
            BEHAVIORAL_CONCEPTS +
            GAME_THEORY_CONCEPTS +
            TEMPORAL_CONCEPTS +
            RISK_CONCEPTS +
            MICROSTRUCTURE_CONCEPTS +
            ADAPTIVE_CONCEPTS +
            MULTIAGENT_CONCEPTS +
            META_CONCEPTS +
            QUANTITATIVE_EDGE_CONCEPTS
        )
        
        for ConceptClass in all_concept_classes:
            try:
                concept = ConceptClass()
                self.concepts.append(concept)
            except Exception as e:
                logger.warning(f"Failed to initialize {ConceptClass.__name__}: {e}")
        
        logger.info(f"Initialized {len(self.concepts)} decision concepts")
    
    def decide(self, context: DecisionContext) -> AggregatedDecision:
        """
        Run all 100 concepts and aggregate into final decision.
        
        Args:
            context: Market context for decision making
            
        Returns:
            AggregatedDecision with final action and reasoning
        """
        start_time = datetime.utcnow()
        
        # Collect decisions from all concepts
        results: List[DecisionResult] = []
        
        for concept in self.concepts:
            if not concept.enabled:
                continue
            try:
            
                result = concept.decide(context)
                results.append(result)
            except Exception as e:
                logger.warning(f"Concept {concept.name} failed: {e}")
        
        # Aggregate decisions
        aggregated = self._aggregate_decisions(results, context)
        
        # Store in history
        self.decision_history.append(aggregated)
        if len(self.decision_history) > 1000:
            self.decision_history.pop(0)
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"Decision made in {duration_ms:.1f}ms: {aggregated.final_action.value} "
                   f"(conf={aggregated.final_confidence:.2f}, consensus={aggregated.consensus_level:.2f})")
        
        return aggregated
    
    def _aggregate_decisions(
        self,
        results: List[DecisionResult],
        context: DecisionContext
    ) -> AggregatedDecision:
        """Aggregate individual concept decisions into final decision"""
        
        if not results:
            return AggregatedDecision(
                final_action=DecisionAction.HOLD,
                final_confidence=0.0,
                consensus_level=0.0,
                contributing_concepts=[],
                dissenting_concepts=[],
                reasoning_chain=["No concept results available"],
                risk_adjusted_action=DecisionAction.HOLD,
                position_size_multiplier=0.0
            )
        
        # Convert actions to numeric scores
        action_scores = {
            DecisionAction.STRONG_BUY: 1.0,
            DecisionAction.BUY: 0.6,
            DecisionAction.WEAK_BUY: 0.3,
            DecisionAction.HOLD: 0.0,
            DecisionAction.WEAK_SELL: -0.3,
            DecisionAction.SELL: -0.6,
            DecisionAction.STRONG_SELL: -1.0,
            DecisionAction.ABSTAIN: 0.0,
            DecisionAction.DEFER: 0.0,
        }
        
        # Calculate weighted scores
        weighted_scores = []
        for result in results:
            category_weight = self.category_weights.get(result.category, 1.0)
            concept_weight = self._get_concept_weight(result.concept_id)
            score = action_scores[result.action] * result.confidence * category_weight * concept_weight
            weighted_scores.append((result, score))
        
        # Aggregate score
        total_weight = sum(abs(s[1]) for s in weighted_scores) + 0.01
        aggregate_score = sum(s[1] for s in weighted_scores) / total_weight
        
        # Determine final action
        final_action = self._score_to_action(aggregate_score)
        
        # Calculate confidence
        final_confidence = min(abs(aggregate_score) * 1.5, 1.0)
        
        # Calculate consensus
        action_counts = Counter(r.action for r in results)
        most_common_count = action_counts.most_common(1)[0][1] if action_counts else 0
        consensus_level = most_common_count / len(results) if results else 0
        
        # Separate contributing and dissenting concepts
        contributing = []
        dissenting = []
        
        for result in results:
            result_score = action_scores[result.action]
            if (result_score > 0 and aggregate_score > 0) or (result_score < 0 and aggregate_score < 0):
                contributing.append(result)
            elif result_score != 0:
                dissenting.append(result)
        
        # Generate reasoning chain
        reasoning_chain = self._generate_reasoning_chain(results, aggregate_score, context)
        
        # Risk-adjusted action
        risk_adjusted_action = self._apply_risk_adjustment(final_action, context, results)
        
        # Position size multiplier
        position_size_multiplier = self._calculate_position_size(
            final_confidence, consensus_level, context
        )
        
        return AggregatedDecision(
            final_action=final_action,
            final_confidence=final_confidence,
            consensus_level=consensus_level,
            contributing_concepts=contributing,
            dissenting_concepts=dissenting,
            reasoning_chain=reasoning_chain,
            risk_adjusted_action=risk_adjusted_action,
            position_size_multiplier=position_size_multiplier
        )
    
    def _get_concept_weight(self, concept_id: int) -> float:
        """Get adaptive weight for concept based on historical accuracy"""
        history = self.concept_accuracy.get(concept_id, [])
        if len(history) < 10:
            return 1.0
        
        accuracy = sum(history[-20:]) / len(history[-20:])
        return 0.5 + accuracy  # Range: 0.5 to 1.5
    
    def _score_to_action(self, score: float) -> DecisionAction:
        """Convert aggregate score to action"""
        if score > 0.5: return DecisionAction.STRONG_BUY
        if score > 0.25: return DecisionAction.BUY
        if score > 0.1: return DecisionAction.WEAK_BUY
        if score > -0.1: return DecisionAction.HOLD
        if score > -0.25: return DecisionAction.WEAK_SELL
        if score > -0.5: return DecisionAction.SELL
        return DecisionAction.STRONG_SELL
    
    def _generate_reasoning_chain(
        self,
        results: List[DecisionResult],
        aggregate_score: float,
        context: DecisionContext
    ) -> List[str]:
        """Generate human-readable reasoning chain"""
        chain = []
        
        # Market context
        chain.append(f"Market: trend={context.trend:.2f}, momentum={context.momentum:.2f}, "
                    f"vol={context.volatility:.2f}, regime={context.regime}")
        
        # Category summaries
        category_scores = {}
        for result in results:
            cat = result.category
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(result.confidence if 'buy' in result.action.value else -result.confidence)
        
        for cat, scores in category_scores.items():
            avg = sum(scores) / len(scores) if scores else 0
            direction = "bullish" if avg > 0.1 else ("bearish" if avg < -0.1 else "neutral")
            chain.append(f"{cat.value}: {direction} ({avg:.2f})")
        
        # Top contributing reasons
        top_contributors = sorted(results, key=lambda r: r.confidence, reverse=True)[:5]
        chain.append("Top signals:")
        for r in top_contributors:
            chain.append(f"  - {r.concept_name}: {r.action.value} ({r.confidence:.2f}) - {r.reasoning[:50]}")
        
        # Final decision
        chain.append(f"Aggregate score: {aggregate_score:.3f}")
        
        return chain
    
    def _apply_risk_adjustment(
        self,
        action: DecisionAction,
        context: DecisionContext,
        results: List[DecisionResult]
    ) -> DecisionAction:
        """Apply risk-based adjustment to action"""
        
        # Check risk concept results
        risk_results = [r for r in results if r.category == DecisionCategory.RISK_AWARE]
        
        if risk_results:
            risk_concerns = sum(1 for r in risk_results if r.action in [DecisionAction.HOLD, DecisionAction.ABSTAIN])
            
            if risk_concerns > len(risk_results) * 0.5:
                # Majority of risk concepts say hold
                if action in [DecisionAction.STRONG_BUY, DecisionAction.STRONG_SELL]:
                    return DecisionAction.WEAK_BUY if 'buy' in action.value else DecisionAction.WEAK_SELL
                elif action in [DecisionAction.BUY, DecisionAction.SELL]:
                    return DecisionAction.HOLD
        
        # Drawdown protection
        if context.drawdown > 0.1:
            if action in [DecisionAction.STRONG_BUY, DecisionAction.STRONG_SELL]:
                return DecisionAction.HOLD
        
        return action
    
    def _calculate_position_size(
        self,
        confidence: float,
        consensus: float,
        context: DecisionContext
    ) -> float:
        """Calculate position size multiplier"""
        
        base_size = 1.0
        
        # Confidence adjustment
        base_size *= (0.5 + confidence * 0.5)
        
        # Consensus adjustment
        base_size *= (0.7 + consensus * 0.3)
        
        # Volatility adjustment
        base_size *= (1.0 - context.volatility * 0.5)
        
        # Drawdown adjustment
        base_size *= (1.0 - context.drawdown * 2)
        
        return max(0.1, min(base_size, 1.5))
    
    def update_concept_accuracy(self, concept_id: int, was_correct: bool):
        """Update concept accuracy tracking"""
        if concept_id in self.concept_accuracy:
            self.concept_accuracy[concept_id].append(was_correct)
            # Keep last 100
            if len(self.concept_accuracy[concept_id]) > 100:
                self.concept_accuracy[concept_id].pop(0)
    
    def get_concept_stats(self) -> Dict[str, Any]:
        """Get statistics about concept performance"""
        stats = {
            'total_concepts': len(self.concepts),
            'enabled_concepts': sum(1 for c in self.concepts if c.enabled),
            'decisions_made': len(self.decision_history),
            'category_counts': {},
            'top_performers': [],
            'bottom_performers': [],
        }
        
        # Category counts
        for cat in DecisionCategory:
            count = sum(1 for c in self.concepts if c.category == cat)
            stats['category_counts'][cat.value] = count
        
        # Performance ranking
        performances = []
        for concept in self.concepts:
            history = self.concept_accuracy.get(concept.concept_id, [])
            if len(history) >= 10:
                accuracy = sum(history) / len(history)
                performances.append((concept.name, accuracy))
        
        performances.sort(key=lambda x: x[1], reverse=True)
        stats['top_performers'] = performances[:5]
        stats['bottom_performers'] = performances[-5:]
        
        return stats
    
    def enable_category(self, category: DecisionCategory, enabled: bool = True):
        """Enable or disable all concepts in a category"""
        for concept in self.concepts:
            if concept.category == category:
                concept.enabled = enabled
    
    def set_category_weight(self, category: DecisionCategory, weight: float):
        """Set weight for a category"""
        self.category_weights[category] = max(0.1, min(weight, 2.0))


def create_decision_engine(config: Optional[Dict] = None) -> InnovativeDecisionEngine:
    """Factory function to create decision engine"""
    return InnovativeDecisionEngine(config)


def quick_decide(
    symbol: str,
    price: float,
    trend: float,
    momentum: float,
    volatility: float,
    sentiment: float = 0.0,
    **kwargs
) -> AggregatedDecision:
    """Quick decision without full context"""
    engine = InnovativeDecisionEngine()
    
    context = DecisionContext(
        symbol=symbol,
        price=price,
        volume=kwargs.get('volume', 1000000),
        volatility=volatility,
        trend=trend,
        momentum=momentum,
        sentiment=sentiment,
        regime=kwargs.get('regime', 'normal'),
        timeframe=kwargs.get('timeframe', '1H'),
        portfolio_value=kwargs.get('portfolio_value', 100000),
        current_position=kwargs.get('current_position', 0),
        drawdown=kwargs.get('drawdown', 0),
        win_rate=kwargs.get('win_rate', 0.5),
    )
    
    return engine.decide(context)

"""
Research-Informed Decision Concepts (Category 12)
==================================================

Decision concepts informed by autonomous research, cross-domain knowledge transfer,
and continuous learning from the Research Orchestrator and Cognition Store.

Integrates findings from:
- ASI-Evolve style research experiments
- Cross-domain knowledge transfer
- Multi-agent debate outcomes
- Experiment management results

10 Research-Informed Concepts:
1. ExperimentBackedStrategy
2. CrossDomainAnalogy
3. ResearchConsensus
4. NovelPatternRecognition
5. KnowledgeGraphPath
6. TransferredStrategy
7. ValidatedHypothesis
8. CognitiveStoreMatch
9. ResearchDebateOutcome
10. MetaLearningTransfer
"""

import logging
import random
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from .core_types import (
    DecisionConcept, DecisionContext, DecisionResult,
    DecisionCategory, DecisionAction, DecisionUrgency
)

logger = logging.getLogger(__name__)


class ExperimentBackedStrategy(DecisionConcept):
    """
    Concept 121: Experiment-Backed Strategy
    
    Decides based on results from validated research experiments.
    Only trusts strategies that passed multi-stage validation.
    """
    
    def __init__(self):
        super().__init__(121, "ExperimentBackedStrategy", DecisionCategory.RESEARCH_INFORMED)
        self.validated_strategies: Dict[str, float] = {}  # strategy -> score
        
    def add_validated_strategy(self, strategy_name: str, score: float):
        """Add a validated strategy from experiment"""
        self.validated_strategies[strategy_name] = score
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Check if current context matches any validated strategy
        best_match = None
        best_score = 0.0
        
        for strategy, score in self.validated_strategies.items():
            if score > best_score:
                # Check if strategy applies to current regime
                if self._strategy_applies(strategy, context):
                    best_match = strategy
                    best_score = score
        
        if best_match and best_score > 0.7:
            signal = best_score if 'bull' in best_match else -best_score
            action = self._signal_to_action(signal)
            confidence = best_score
            reasoning = f"Validated experiment strategy '{best_match}' with score {best_score:.2f}"
            urgency = DecisionUrgency.NORMAL
        elif best_match:
            action = DecisionAction.HOLD
            confidence = 0.5
            reasoning = f"Validated strategy found but score ({best_score:.2f}) insufficient"
            urgency = DecisionUrgency.LOW
        else:
            action = DecisionAction.ABSTAIN
            confidence = 0.3
            reasoning = "No validated strategy matches current context"
            urgency = DecisionUrgency.LOW
        
        return self._create_result(
            action=action,
            confidence=confidence,
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'validated_strategy_count': len(self.validated_strategies),
                'best_match_score': best_score,
                'context_match': 1.0 if best_match else 0.0
            }
        )
    
    def _strategy_applies(self, strategy: str, context: DecisionContext) -> bool:
        """Check if a strategy applies to current context"""
        # Simple regime matching
        if 'trend' in strategy and context.trend > 0.2:
            return True
        if 'reversion' in strategy and abs(context.trend) < 0.2:
            return True
        if 'momentum' in strategy and abs(context.momentum) > 0.3:
            return True
        return True  # Default to true if no specific condition


class CrossDomainAnalogy(DecisionConcept):
    """
    Concept 122: Cross-Domain Analogy
    
    Applies insights from cross-domain knowledge transfer (physics, biology, etc.)
    to trading decisions.
    """
    
    def __init__(self):
        super().__init__(122, "CrossDomainAnalogy", DecisionCategory.RESEARCH_INFORMED)
        self.domain_insights: Dict[str, List[Dict]] = {
            'physics': [],
            'biology': [],
            'game_theory': [],
            'control_systems': []
        }
        
    def add_domain_insight(self, domain: str, concept: str, trading_app: str, efficacy: float):
        """Add a cross-domain insight"""
        if domain in self.domain_insights:
            self.domain_insights[domain].append({
                'concept': concept,
                'trading_application': trading_app,
                'efficacy': efficacy
            })
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Find best applicable cross-domain insight
        best_insight = None
        best_score = 0.0
        
        for domain, insights in self.domain_insights.items():
            for insight in insights:
                if insight['efficacy'] > best_score:
                    if self._insight_applies(insight, context):
                        best_insight = insight
                        best_score = insight['efficacy']
        
        if best_insight and best_score > 0.6:
            # Positive or negative based on insight type
            signal = best_score * self._get_signal_direction(best_insight, context)
            action = self._signal_to_action(signal)
            confidence = best_score
            reasoning = f"Cross-domain insight from {best_insight['concept']}: {best_insight['trading_application']}"
            urgency = DecisionUrgency.NORMAL
        else:
            action = DecisionAction.HOLD
            confidence = 0.4
            reasoning = "No high-efficacy cross-domain insight applicable"
            urgency = DecisionUrgency.LOW
        
        total_insights = sum(len(i) for i in self.domain_insights.values())
        
        return self._create_result(
            action=action,
            confidence=confidence,
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'domain_insights_available': total_insights,
                'best_insight_efficacy': best_score,
                'source_domain': best_insight['concept'].split('_')[0] if best_insight else 'none'
            }
        )
    
    def _insight_applies(self, insight: Dict, context: DecisionContext) -> bool:
        """Check if insight applies to context"""
        app = insight['trading_application'].lower()
        if 'momentum' in app and abs(context.momentum) < 0.2:
            return False
        if 'volatility' in app and context.volatility < 0.15:
            return False
        return True
    
    def _get_signal_direction(self, insight: Dict, context: DecisionContext) -> float:
        """Determine signal direction from insight"""
        app = insight['trading_application'].lower()
        if 'defense' in app or 'risk' in app:
            return -1.0 if context.drawdown > 0.05 else 1.0
        return 1.0


class ResearchConsensus(DecisionConcept):
    """
    Concept 123: Research Consensus
    
    Decides based on consensus from multi-agent debate system.
    Trusts decisions where research agents agree.
    """
    
    def __init__(self):
        super().__init__(123, "ResearchConsensus", DecisionCategory.RESEARCH_INFORMED)
        self.debate_outcomes: List[Dict] = []
        
    def record_debate_outcome(self, outcome: Dict):
        """Record outcome from multi-agent debate"""
        self.debate_outcomes.append(outcome)
        if len(self.debate_outcomes) > 100:
            self.debate_outcomes.pop(0)
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Analyze recent debate outcomes
        recent = self.debate_outcomes[-10:] if self.debate_outcomes else []
        
        if not recent:
            return self._create_result(
                action=DecisionAction.ABSTAIN,
                confidence=0.3,
                urgency=DecisionUrgency.LOW,
                reasoning="No debate outcomes available for consensus analysis",
                factors={'debates_available': 0}
            )
        
        # Count positions
        approve_count = sum(1 for o in recent if o.get('final_position') == 'approve')
        reject_count = sum(1 for o in recent if o.get('final_position') == 'reject')
        total = len(recent)
        
        # Calculate consensus metrics
        consensus_ratio = max(approve_count, reject_count) / total if total > 0 else 0
        avg_confidence = sum(o.get('final_confidence', 0.5) for o in recent) / total
        
        if consensus_ratio > 0.7 and approve_count > reject_count:
            action = DecisionAction.BUY
            confidence = avg_confidence * consensus_ratio
            reasoning = f"Strong research consensus for approval ({approve_count}/{total} debates)"
            urgency = DecisionUrgency.HIGH if consensus_ratio > 0.8 else DecisionUrgency.NORMAL
        elif consensus_ratio > 0.7 and reject_count > approve_count:
            action = DecisionAction.SELL
            confidence = avg_confidence * consensus_ratio
            reasoning = f"Strong research consensus for rejection ({reject_count}/{total} debates)"
            urgency = DecisionUrgency.HIGH if consensus_ratio > 0.8 else DecisionUrgency.NORMAL
        else:
            action = DecisionAction.HOLD
            confidence = 0.5
            reasoning = f"No clear research consensus ({approve_count} vs {reject_count})"
            urgency = DecisionUrgency.LOW
        
        return self._create_result(
            action=action,
            confidence=confidence,
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'debates_analyzed': total,
                'consensus_ratio': consensus_ratio,
                'avg_debate_confidence': avg_confidence,
                'approve_ratio': approve_count / total if total > 0 else 0
            }
        )


class NovelPatternRecognition(DecisionConcept):
    """
    Concept 124: Novel Pattern Recognition
    
    Identifies and acts on novel patterns discovered through research.
    Distinct from standard technical patterns - these are AI-discovered.
    """
    
    def __init__(self):
        super().__init__(124, "NovelPatternRecognition", DecisionCategory.RESEARCH_INFORMED)
        self.novel_patterns: List[Dict] = []
        
    def add_novel_pattern(self, pattern: Dict):
        """Add a novel pattern discovered by research"""
        self.novel_patterns.append(pattern)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Check if any novel patterns match current context
        matching_patterns = []
        
        for pattern in self.novel_patterns:
            match_score = self._match_pattern(pattern, context)
            if match_score > 0.7:
                matching_patterns.append((pattern, match_score))
        
        if matching_patterns:
            # Best matching pattern
            best_pattern, best_score = max(matching_patterns, key=lambda x: x[1])
            
            signal = best_score * best_pattern.get('direction', 1)
            action = self._signal_to_action(signal)
            confidence = best_score * best_pattern.get('validation_score', 0.5)
            reasoning = f"Novel pattern '{best_pattern.get('name', 'unknown')}' detected with {best_score:.1%} match"
            urgency = DecisionUrgency.HIGH if best_score > 0.85 else DecisionUrgency.NORMAL
        else:
            action = DecisionAction.HOLD
            confidence = 0.4
            reasoning = f"No novel patterns match current context ({len(self.novel_patterns)} patterns available)"
            urgency = DecisionUrgency.LOW
        
        return self._create_result(
            action=action,
            confidence=confidence,
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'novel_patterns_known': len(self.novel_patterns),
                'patterns_matching': len(matching_patterns),
                'best_match_score': max((m[1] for m in matching_patterns), default=0)
            }
        )
    
    def _match_pattern(self, pattern: Dict, context: DecisionContext) -> float:
        """Match pattern to current context"""
        conditions = pattern.get('conditions', {})
        match_score = 1.0
        
        if 'min_volatility' in conditions:
            match_score *= 0.5 if context.volatility < conditions['min_volatility'] else 1.0
        if 'min_trend' in conditions:
            match_score *= 0.5 if abs(context.trend) < conditions['min_trend'] else 1.0
        if 'regime' in conditions:
            match_score *= 0.7 if context.regime != conditions['regime'] else 1.0
        
        return match_score


class KnowledgeGraphPath(DecisionConcept):
    """
    Concept 125: Knowledge Graph Path
    
    Uses paths through the knowledge graph to inform decisions.
    Finds reasoning chains connecting concepts.
    """
    
    def __init__(self):
        super().__init__(125, "KnowledgeGraphPath", DecisionCategory.RESEARCH_INFORMED)
        self.knowledge_paths: List[List[str]] = []
        
    def add_knowledge_path(self, path: List[str]):
        """Add a knowledge graph path"""
        self.knowledge_paths.append(path)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Find relevant knowledge paths
        relevant_paths = []
        
        for path in self.knowledge_paths:
            relevance = self._score_path_relevance(path, context)
            if relevance > 0.5:
                relevant_paths.append((path, relevance))
        
        if relevant_paths:
            best_path, best_relevance = max(relevant_paths, key=lambda x: x[1])
            
            # Determine signal from path
            signal = best_relevance * self._extract_signal_from_path(best_path)
            action = self._signal_to_action(signal)
            confidence = best_relevance
            reasoning = f"Knowledge graph path suggests: {' -> '.join(best_path[:3])}..."
            urgency = DecisionUrgency.NORMAL
        else:
            action = DecisionAction.HOLD
            confidence = 0.4
            reasoning = "No relevant knowledge graph paths found"
            urgency = DecisionUrgency.LOW
        
        return self._create_result(
            action=action,
            confidence=confidence,
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'paths_available': len(self.knowledge_paths),
                'relevant_paths': len(relevant_paths),
                'best_path_relevance': best_relevance if relevant_paths else 0
            }
        )
    
    def _score_path_relevance(self, path: List[str], context: DecisionContext) -> float:
        """Score how relevant a path is to current context"""
        score = 0.5
        path_str = ' '.join(path).lower()
        
        if context.regime in path_str:
            score += 0.2
        if context.volatility > 0.2 and 'volatility' in path_str:
            score += 0.2
        if abs(context.trend) > 0.3 and 'trend' in path_str:
            score += 0.2
        
        return min(1.0, score)
    
    def _extract_signal_from_path(self, path: List[str]) -> float:
        """Extract signal direction from path"""
        path_str = ' '.join(path).lower()
        if any(word in path_str for word in ['bullish', 'buy', 'up', 'growth']):
            return 1.0
        elif any(word in path_str for word in ['bearish', 'sell', 'down', 'decline']):
            return -1.0
        return 0.5


class TransferredStrategy(DecisionConcept):
    """
    Concept 126: Transferred Strategy
    
    Applies strategies that have been successfully transferred from other domains.
    """
    
    def __init__(self):
        super().__init__(126, "TransferredStrategy", DecisionCategory.RESEARCH_INFORMED)
        self.transfers: List[Dict] = []
        
    def add_transfer(self, transfer: Dict):
        """Add a strategy transfer"""
        self.transfers.append(transfer)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Find active transfers applicable to context
        applicable = []
        
        for transfer in self.transfers:
            if transfer.get('status') == 'ACTIVE':
                applicability = self._score_transfer_applicability(transfer, context)
                if applicability > 0.5:
                    applicable.append((transfer, applicability))
        
        if applicable:
            best_transfer, best_applicability = max(applicable, key=lambda x: x[1])
            efficacy = best_transfer.get('efficacy_score', 0.5)
            
            signal = best_applicability * efficacy
            action = self._signal_to_action(signal)
            confidence = best_applicability * efficacy
            reasoning = f"Transferred strategy from {best_transfer.get('source_domain', 'unknown')}: {best_transfer.get('original_concept', 'unknown')}"
            urgency = DecisionUrgency.NORMAL
        else:
            action = DecisionAction.HOLD
            confidence = 0.4
            reasoning = "No applicable transferred strategies"
            urgency = DecisionUrgency.LOW
        
        return self._create_result(
            action=action,
            confidence=confidence,
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'transfers_available': len(self.transfers),
                'active_transfers': len([t for t in self.transfers if t.get('status') == 'ACTIVE']),
                'best_applicability': best_applicability if applicable else 0
            }
        )
    
    def _score_transfer_applicability(self, transfer: Dict, context: DecisionContext) -> float:
        """Score how applicable a transfer is"""
        score = 0.5
        
        # Match domain characteristics to context
        if 'momentum' in str(transfer).lower() and abs(context.momentum) > 0.3:
            score += 0.3
        if 'risk' in str(transfer).lower() and context.drawdown > 0.03:
            score += 0.2
        
        return min(1.0, score)


class ValidatedHypothesis(DecisionConcept):
    """
    Concept 127: Validated Hypothesis
    
    Acts on hypotheses that have been validated through research experiments.
    """
    
    def __init__(self):
        super().__init__(127, "ValidatedHypothesis", DecisionCategory.RESEARCH_INFORMED)
        self.validated_hypotheses: List[Dict] = []
        
    def add_validated_hypothesis(self, hypothesis: Dict):
        """Add a validated hypothesis"""
        self.validated_hypotheses.append(hypothesis)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Find matching validated hypotheses
        matches = []
        
        for hyp in self.validated_hypotheses:
            match_score = self._match_hypothesis(hyp, context)
            if match_score > 0.6:
                matches.append((hyp, match_score))
        
        if matches:
            best_hyp, best_match = max(matches, key=lambda x: x[1])
            validation_score = best_hyp.get('validation_score', 0.5)
            
            signal = best_match * validation_score * best_hyp.get('direction', 1)
            action = self._signal_to_action(signal)
            confidence = best_match * validation_score
            reasoning = f"Validated hypothesis: {best_hyp.get('description', 'unknown')}"
            urgency = DecisionUrgency.HIGH if validation_score > 0.8 else DecisionUrgency.NORMAL
        else:
            action = DecisionAction.HOLD
            confidence = 0.4
            reasoning = "No validated hypotheses match current context"
            urgency = DecisionUrgency.LOW
        
        return self._create_result(
            action=action,
            confidence=confidence,
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'validated_hypotheses': len(self.validated_hypotheses),
                'matching_hypotheses': len(matches),
                'best_validation_score': max((m[0].get('validation_score', 0) for m in matches), default=0)
            }
        )
    
    def _match_hypothesis(self, hypothesis: Dict, context: DecisionContext) -> float:
        """Match hypothesis to current context"""
        match = 1.0
        
        conditions = hypothesis.get('conditions', {})
        if 'regime' in conditions and conditions['regime'] != context.regime:
            match *= 0.6
        if 'min_confidence' in conditions:
            # Context doesn't have direct confidence, use trend strength as proxy
            trend_strength = abs(context.trend)
            if trend_strength < conditions['min_confidence']:
                match *= 0.7
        
        return match


class CognitiveStoreMatch(DecisionConcept):
    """
    Concept 128: Cognitive Store Match
    
    Decides based on semantic matches from the cognition store.
    """
    
    def __init__(self):
        super().__init__(128, "CognitiveStoreMatch", DecisionCategory.RESEARCH_INFORMED)
        self.cognition_matches: List[Dict] = []
        
    def record_cognition_match(self, match: Dict):
        """Record a cognition store match"""
        self.cognition_matches.append(match)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Simulate cognition store query based on context
        context_description = f"{context.regime} regime volatility {context.volatility} trend {context.trend}"
        
        # Find best matches (simulated)
        best_match = None
        best_score = 0.0
        
        for match in self.cognition_matches[-20:]:  # Recent matches
            score = match.get('similarity', 0)
            if score > best_score:
                best_score = score
                best_match = match
        
        if best_match and best_score > 0.7:
            entry_type = best_match.get('entry_type', 'insight')
            importance = best_match.get('importance', 0.5)
            
            signal = best_score * importance * (1 if entry_type in ['success', 'strategy'] else -0.5)
            action = self._signal_to_action(signal)
            confidence = best_score * importance
            reasoning = f"Cognition store match ({best_score:.1%} similar): {best_match.get('content', 'N/A')[:50]}..."
            urgency = DecisionUrgency.NORMAL
        else:
            action = DecisionAction.HOLD
            confidence = 0.4
            reasoning = "No strong cognition store matches"
            urgency = DecisionUrgency.LOW
        
        return self._create_result(
            action=action,
            confidence=confidence,
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'cognition_entries_matched': len(self.cognition_matches),
                'best_similarity': best_score,
                'entry_type': best_match.get('entry_type', 'none') if best_match else 'none'
            }
        )


class ResearchDebateOutcome(DecisionConcept):
    """
    Concept 129: Research Debate Outcome
    
    Directly uses outcomes from multi-agent research debates.
    """
    
    def __init__(self):
        super().__init__(129, "ResearchDebateOutcome", DecisionCategory.RESEARCH_INFORMED)
        self.recent_outcomes: List[Dict] = []
        
    def record_outcome(self, outcome: Dict):
        """Record a debate outcome"""
        self.recent_outcomes.append(outcome)
        if len(self.recent_outcomes) > 50:
            self.recent_outcomes.pop(0)
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        if not self.recent_outcomes:
            return self._create_result(
                action=DecisionAction.ABSTAIN,
                confidence=0.3,
                urgency=DecisionUrgency.LOW,
                reasoning="No research debate outcomes available",
                factors={'outcomes_available': 0}
            )
        
        # Get most recent outcome
        latest = self.recent_outcomes[-1]
        
        position = latest.get('final_position', 'defer')
        confidence = latest.get('final_confidence', 0.5)
        consensus = latest.get('consensus_achieved', False)
        
        if position == 'approve' and consensus:
            action = DecisionAction.BUY
        elif position == 'approve':
            action = DecisionAction.WEAK_BUY
        elif position == 'reject' and consensus:
            action = DecisionAction.SELL
        elif position == 'reject':
            action = DecisionAction.WEAK_SELL
        else:
            action = DecisionAction.HOLD
        
        reasoning = f"Research debate outcome: {position} (consensus={consensus}, conf={confidence:.2f})"
        urgency = DecisionUrgency.HIGH if consensus else DecisionUrgency.NORMAL
        
        return self._create_result(
            action=action,
            confidence=confidence,
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'outcomes_considered': len(self.recent_outcomes),
                'latest_position': position,
                'consensus_achieved': 1.0 if consensus else 0.0,
                'debate_confidence': confidence
            }
        )


class MetaLearningTransfer(DecisionConcept):
    """
    Concept 130: Meta-Learning Transfer
    
    Applies meta-learning insights about strategy performance across regimes.
    """
    
    def __init__(self):
        super().__init__(130, "MetaLearningTransfer", DecisionCategory.RESEARCH_INFORMED)
        self.meta_insights: Dict[str, Any] = {
            'regime_performance': {},
            'strategy_transfers': [],
            'learning_curves': {}
        }
        
    def add_meta_insight(self, category: str, insight: Any):
        """Add meta-learning insight"""
        if category in self.meta_insights:
            if isinstance(self.meta_insights[category], dict):
                self.meta_insights[category].update(insight)
            elif isinstance(self.meta_insights[category], list):
                self.meta_insights[category].append(insight)
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Use meta-learning to predict strategy performance
        regime = context.regime
        
        # Get regime-specific performance prediction
        regime_perf = self.meta_insights.get('regime_performance', {})
        predicted_perf = regime_perf.get(regime, 0.5)
        
        # Check for relevant strategy transfers
        transfers = self.meta_insights.get('strategy_transfers', [])
        relevant_transfers = [t for t in transfers if t.get('target_regime') == regime]
        
        if predicted_perf > 0.6 or relevant_transfers:
            signal = predicted_perf if predicted_perf > 0.5 else 0.6
            action = self._signal_to_action(signal)
            confidence = predicted_perf if predicted_perf > 0.5 else 0.6
            reasoning = f"Meta-learning predicts {predicted_perf:.1%} performance in {regime} regime"
            if relevant_transfers:
                reasoning += f" with {len(relevant_transfers)} relevant strategy transfers"
            urgency = DecisionUrgency.NORMAL if predicted_perf > 0.7 else DecisionUrgency.LOW
        else:
            action = DecisionAction.HOLD
            confidence = 0.5
            reasoning = f"Meta-learning shows uncertainty for {regime} regime (predicted: {predicted_perf:.1%})"
            urgency = DecisionUrgency.LOW
        
        return self._create_result(
            action=action,
            confidence=confidence,
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'predicted_regime_performance': predicted_perf,
                'regimes_characterized': len(regime_perf),
                'relevant_transfers': len(relevant_transfers),
                'meta_insights_available': len(self.meta_insights)
            }
        )


# Export all research-informed concepts
RESEARCH_INFORMED_CONCEPTS = [
    ExperimentBackedStrategy,
    CrossDomainAnalogy,
    ResearchConsensus,
    NovelPatternRecognition,
    KnowledgeGraphPath,
    TransferredStrategy,
    ValidatedHypothesis,
    CognitiveStoreMatch,
    ResearchDebateOutcome,
    MetaLearningTransfer,
]

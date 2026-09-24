"""
Interestingness Ranker - Multi-Criteria Research Prioritization
================================================================

Implements ranking of hypotheses and research directions by:
1. Novelty: How new/unexplored is this?
2. Impact: Potential value if true
3. Feasibility: Can we test this?
4. Urgency: Time-sensitive opportunities
5. Synergy: Builds on existing knowledge

Based on the Foundation Agents paper (arXiv:2504.01990) curiosity systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)


class InterestDimension(Enum):
    """Dimensions of interestingness"""
    NOVELTY = "novelty"              # How new/unexplored
    IMPACT = "impact"                # Potential value
    FEASIBILITY = "feasibility"      # Can we test it
    URGENCY = "urgency"              # Time sensitivity
    SYNERGY = "synergy"              # Builds on knowledge
    CURIOSITY = "curiosity"          # Intrinsic interest
    ACTIONABILITY = "actionability"  # Can we act on it
    CONFIDENCE = "confidence"        # Confidence in assessment


@dataclass
class InterestScore:
    """Score for a research item"""
    item_id: str
    item_type: str  # hypothesis, anomaly, pattern, etc.
    
    # Dimension scores (0-1)
    novelty: float = 0.5
    impact: float = 0.5
    feasibility: float = 0.5
    urgency: float = 0.5
    synergy: float = 0.5
    curiosity: float = 0.5
    actionability: float = 0.5
    confidence: float = 0.5
    
    # Composite score
    overall_score: float = 0.0
    
    # Ranking
    rank: Optional[int] = None
    percentile: Optional[float] = None
    
    # Metadata
    computed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'item_id': self.item_id,
            'item_type': self.item_type,
            'novelty': self.novelty,
            'impact': self.impact,
            'feasibility': self.feasibility,
            'urgency': self.urgency,
            'synergy': self.synergy,
            'curiosity': self.curiosity,
            'actionability': self.actionability,
            'confidence': self.confidence,
            'overall_score': self.overall_score,
            'rank': self.rank,
            'percentile': self.percentile
        }


class NoveltyScorer:
    """Score novelty of research items"""
    
    def __init__(self):
        self.seen_patterns: Dict[str, int] = defaultdict(int)
        self.topic_counts: Dict[str, int] = defaultdict(int)
    
    def score(
        self,
        item_id: str,
        topics: List[str],
        pattern_hash: Optional[str] = None,
        similar_items: int = 0
    ) -> float:
        """Score novelty of an item"""
        scores = []
        
        # Topic novelty
        if topics:
            topic_novelties = []
            for topic in topics:
                count = self.topic_counts.get(topic, 0)
                novelty = 1.0 / (1 + np.log1p(count))
                topic_novelties.append(novelty)
                self.topic_counts[topic] += 1
            scores.append(np.mean(topic_novelties))
        
        # Pattern novelty
        if pattern_hash:
            pattern_count = self.seen_patterns.get(pattern_hash, 0)
            pattern_novelty = 1.0 / (1 + np.sqrt(pattern_count))
            self.seen_patterns[pattern_hash] += 1
            scores.append(pattern_novelty)
        
        # Similar items penalty
        similarity_penalty = 1.0 / (1 + similar_items * 0.2)
        scores.append(similarity_penalty)
        
        return np.mean(scores) if scores else 0.5


class ImpactScorer:
    """Score potential impact of research items"""
    
    def __init__(self):
        self.impact_history: Dict[str, List[float]] = defaultdict(list)
    
    def score(
        self,
        item_type: str,
        potential_profit: Optional[float] = None,
        affected_assets: int = 1,
        time_horizon: str = "medium",
        confidence: float = 0.5
    ) -> float:
        """Score potential impact"""
        scores = []
        
        # Profit potential
        if potential_profit is not None:
            # Normalize profit (assuming percentage)
            profit_score = min(1.0, abs(potential_profit) / 0.1)  # 10% = max score
            scores.append(profit_score)
        
        # Breadth of impact
        breadth_score = min(1.0, np.log1p(affected_assets) / 3)  # ~20 assets = max
        scores.append(breadth_score)
        
        # Time horizon value
        horizon_values = {
            "immediate": 0.3,
            "short": 0.5,
            "medium": 0.7,
            "long": 0.9
        }
        scores.append(horizon_values.get(time_horizon, 0.5))
        
        # Confidence adjustment
        base_score = np.mean(scores) if scores else 0.5
        adjusted_score = base_score * (0.5 + 0.5 * confidence)
        
        # Record for learning
        self.impact_history[item_type].append(adjusted_score)
        
        return adjusted_score


class FeasibilityScorer:
    """Score feasibility of testing/implementing"""
    
    def score(
        self,
        data_available: bool = True,
        compute_required: str = "low",
        time_required: timedelta = timedelta(hours=1),
        dependencies_met: bool = True,
        expertise_required: str = "low"
    ) -> float:
        """Score feasibility"""
        scores = []
        
        # Data availability
        scores.append(1.0 if data_available else 0.2)
        
        # Compute requirements
        compute_values = {"low": 0.9, "medium": 0.6, "high": 0.3, "very_high": 0.1}
        scores.append(compute_values.get(compute_required, 0.5))
        
        # Time requirements
        hours = time_required.total_seconds() / 3600
        time_score = 1.0 / (1 + hours / 24)  # 24 hours = 0.5 score
        scores.append(time_score)
        
        # Dependencies
        scores.append(1.0 if dependencies_met else 0.3)
        
        # Expertise
        expertise_values = {"low": 0.9, "medium": 0.7, "high": 0.4, "expert": 0.2}
        scores.append(expertise_values.get(expertise_required, 0.5))
        
        return np.mean(scores)


class UrgencyScorer:
    """Score time-sensitivity of research items"""
    
    def score(
        self,
        deadline: Optional[datetime] = None,
        market_event: bool = False,
        decay_rate: float = 0.1,
        opportunity_window: Optional[timedelta] = None
    ) -> float:
        """Score urgency"""
        scores = []
        
        # Deadline urgency
        if deadline:
            time_to_deadline = (deadline - datetime.utcnow()).total_seconds() / 3600
            if time_to_deadline <= 0:
                scores.append(0.0)  # Missed deadline
            else:
                urgency = 1.0 / (1 + time_to_deadline / 24)
                scores.append(urgency)
        
        # Market event urgency
        if market_event:
            scores.append(0.9)
        
        # Opportunity window
        if opportunity_window:
            window_hours = opportunity_window.total_seconds() / 3600
            window_urgency = 1.0 / (1 + window_hours / 48)
            scores.append(window_urgency)
        
        # Decay-based urgency
        decay_urgency = 1.0 - np.exp(-decay_rate)
        scores.append(decay_urgency)
        
        return np.mean(scores) if scores else 0.3


class SynergyScorer:
    """Score synergy with existing knowledge"""
    
    def __init__(self):
        self.knowledge_graph: Dict[str, set] = defaultdict(set)
    
    def add_knowledge(self, topic: str, related_topics: List[str]):
        """Add knowledge relationships"""
        for related in related_topics:
            self.knowledge_graph[topic].add(related)
            self.knowledge_graph[related].add(topic)
    
    def score(
        self,
        topics: List[str],
        builds_on: List[str] = None,
        extends_hypothesis: Optional[str] = None
    ) -> float:
        """Score synergy with existing knowledge"""
        scores = []
        
        # Topic connectivity
        if topics:
            connections = 0
            for topic in topics:
                connections += len(self.knowledge_graph.get(topic, set()))
            connectivity_score = min(1.0, connections / (len(topics) * 5))
            scores.append(connectivity_score)
        
        # Builds on existing work
        if builds_on:
            build_score = min(1.0, len(builds_on) / 3)
            scores.append(build_score)
        
        # Extends hypothesis
        if extends_hypothesis:
            scores.append(0.8)
        
        return np.mean(scores) if scores else 0.3


class InterestingnessRanker:
    """
    Interestingness Ranker
    
    Central system for ranking research items by interestingness.
    Combines multiple dimensions with configurable weights.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Dimension scorers
        self.novelty_scorer = NoveltyScorer()
        self.impact_scorer = ImpactScorer()
        self.feasibility_scorer = FeasibilityScorer()
        self.urgency_scorer = UrgencyScorer()
        self.synergy_scorer = SynergyScorer()
        
        # Dimension weights (configurable)
        self.weights = self.config.get('weights', {
            'novelty': 0.20,
            'impact': 0.25,
            'feasibility': 0.15,
            'urgency': 0.10,
            'synergy': 0.10,
            'curiosity': 0.10,
            'actionability': 0.10
        })
        
        # Scored items
        self.scores: Dict[str, InterestScore] = {}
        self.score_history: List[InterestScore] = []
        
        # Statistics
        self.stats = {
            'items_scored': 0,
            'avg_score': 0.0,
            'score_distribution': []
        }
        
        logger.info("Interestingness Ranker initialized")
    
    def score_hypothesis(
        self,
        hypothesis_id: str,
        statement: str,
        hypothesis_type: str,
        topics: List[str],
        potential_profit: Optional[float] = None,
        data_available: bool = True,
        time_required: timedelta = timedelta(hours=1),
        deadline: Optional[datetime] = None,
        builds_on: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> InterestScore:
        """Score a hypothesis"""
        # Calculate dimension scores
        novelty = self.novelty_scorer.score(
            item_id=hypothesis_id,
            topics=topics,
            pattern_hash=hypothesis_type
        )
        
        impact = self.impact_scorer.score(
            item_type="hypothesis",
            potential_profit=potential_profit,
            affected_assets=len(topics)
        )
        
        feasibility = self.feasibility_scorer.score(
            data_available=data_available,
            time_required=time_required
        )
        
        urgency = self.urgency_scorer.score(deadline=deadline)
        
        synergy = self.synergy_scorer.score(
            topics=topics,
            builds_on=builds_on or []
        )
        
        # Curiosity based on novelty and impact
        curiosity = 0.6 * novelty + 0.4 * impact
        
        # Actionability based on feasibility and impact
        actionability = 0.5 * feasibility + 0.5 * impact
        
        # Confidence in scoring
        confidence = 0.7  # Base confidence
        
        # Create score object
        score = InterestScore(
            item_id=hypothesis_id,
            item_type="hypothesis",
            novelty=novelty,
            impact=impact,
            feasibility=feasibility,
            urgency=urgency,
            synergy=synergy,
            curiosity=curiosity,
            actionability=actionability,
            confidence=confidence,
            metadata=metadata or {}
        )
        
        # Calculate overall score
        score.overall_score = self._calculate_overall(score)
        
        # Store and return
        self._store_score(score)
        return score
    
    def score_anomaly(
        self,
        anomaly_id: str,
        anomaly_type: str,
        severity: int,
        asset: Optional[str] = None,
        topics: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> InterestScore:
        """Score an anomaly"""
        topics = topics or [anomaly_type]
        if asset:
            topics.append(asset)
        
        # Novelty
        novelty = self.novelty_scorer.score(
            item_id=anomaly_id,
            topics=topics,
            pattern_hash=anomaly_type
        )
        
        # Impact based on severity
        impact = min(1.0, severity / 4)  # Assuming 4 is max severity
        
        # Anomalies are generally feasible to investigate
        feasibility = 0.8
        
        # Anomalies are often urgent
        urgency = 0.7
        
        # Synergy
        synergy = self.synergy_scorer.score(topics=topics)
        
        # High curiosity for anomalies
        curiosity = 0.7 * novelty + 0.3 * impact
        
        # Actionability
        actionability = 0.6
        
        score = InterestScore(
            item_id=anomaly_id,
            item_type="anomaly",
            novelty=novelty,
            impact=impact,
            feasibility=feasibility,
            urgency=urgency,
            synergy=synergy,
            curiosity=curiosity,
            actionability=actionability,
            confidence=0.8,
            metadata=metadata or {}
        )
        
        score.overall_score = self._calculate_overall(score)
        self._store_score(score)
        return score
    
    def score_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        frequency: int,
        success_rate: float,
        assets: List[str],
        metadata: Optional[Dict] = None
    ) -> InterestScore:
        """Score a discovered pattern"""
        topics = [pattern_type] + assets[:3]
        
        # Novelty decreases with frequency
        novelty = 1.0 / (1 + np.log1p(frequency))
        
        # Impact based on success rate
        impact = success_rate
        
        # Patterns are feasible to use
        feasibility = 0.9
        
        # Not usually urgent
        urgency = 0.3
        
        # Synergy
        synergy = self.synergy_scorer.score(topics=topics)
        
        # Curiosity
        curiosity = 0.5 * novelty + 0.5 * (1 - success_rate)  # More curious about uncertain patterns
        
        # High actionability for patterns
        actionability = 0.8 * success_rate
        
        score = InterestScore(
            item_id=pattern_id,
            item_type="pattern",
            novelty=novelty,
            impact=impact,
            feasibility=feasibility,
            urgency=urgency,
            synergy=synergy,
            curiosity=curiosity,
            actionability=actionability,
            confidence=min(0.9, 0.5 + frequency * 0.05),
            metadata=metadata or {}
        )
        
        score.overall_score = self._calculate_overall(score)
        self._store_score(score)
        return score
    
    def _calculate_overall(self, score: InterestScore) -> float:
        """Calculate overall score from dimensions"""
        weighted_sum = (
            score.novelty * self.weights.get('novelty', 0.2) +
            score.impact * self.weights.get('impact', 0.25) +
            score.feasibility * self.weights.get('feasibility', 0.15) +
            score.urgency * self.weights.get('urgency', 0.1) +
            score.synergy * self.weights.get('synergy', 0.1) +
            score.curiosity * self.weights.get('curiosity', 0.1) +
            score.actionability * self.weights.get('actionability', 0.1)
        )
        
        # Adjust by confidence
        return weighted_sum * (0.7 + 0.3 * score.confidence)
    
    def _store_score(self, score: InterestScore):
        """Store a score"""
        self.scores[score.item_id] = score
        self.score_history.append(score)
        
        self.stats['items_scored'] += 1
        self.stats['score_distribution'].append(score.overall_score)
        if len(self.stats['score_distribution']) > 1000:
            self.stats['score_distribution'] = self.stats['score_distribution'][-1000:]
        self.stats['avg_score'] = np.mean(self.stats['score_distribution'])
    
    def rank_items(
        self,
        item_type: Optional[str] = None,
        min_score: float = 0.0,
        limit: int = 20
    ) -> List[InterestScore]:
        """Rank items by overall score"""
        candidates = list(self.scores.values())
        
        if item_type:
            candidates = [s for s in candidates if s.item_type == item_type]
        
        if min_score > 0:
            candidates = [s for s in candidates if s.overall_score >= min_score]
        
        # Sort by overall score
        candidates.sort(key=lambda s: s.overall_score, reverse=True)
        
        # Assign ranks and percentiles
        for i, score in enumerate(candidates):
            score.rank = i + 1
            score.percentile = 100 * (1 - i / max(len(candidates), 1))
        
        return candidates[:limit]
    
    def get_top_by_dimension(
        self,
        dimension: InterestDimension,
        limit: int = 10
    ) -> List[InterestScore]:
        """Get top items by a specific dimension"""
        candidates = list(self.scores.values())
        
        # Sort by dimension
        dim_name = dimension.value
        candidates.sort(
            key=lambda s: getattr(s, dim_name, 0),
            reverse=True
        )
        
        return candidates[:limit]
    
    def update_weights(self, new_weights: Dict[str, float]):
        """Update dimension weights"""
        self.weights.update(new_weights)
        
        # Normalize weights
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v/total for k, v in self.weights.items()}
        
        # Recalculate all scores
        for score in self.scores.values():
            score.overall_score = self._calculate_overall(score)
        
        logger.info(f"Updated weights: {self.weights}")
    
    def get_score(self, item_id: str) -> Optional[InterestScore]:
        """Get score for an item"""
        return self.scores.get(item_id)
    
    def compare_items(
        self,
        item_id1: str,
        item_id2: str
    ) -> Dict[str, Any]:
        """Compare two items"""
        score1 = self.scores.get(item_id1)
        score2 = self.scores.get(item_id2)
        
        if not score1 or not score2:
            return {'error': 'Item not found'}
        
        comparison = {
            'item1': item_id1,
            'item2': item_id2,
            'overall': {
                'item1': score1.overall_score,
                'item2': score2.overall_score,
                'winner': item_id1 if score1.overall_score > score2.overall_score else item_id2
            },
            'dimensions': {}
        }
        
        for dim in InterestDimension:
            dim_name = dim.value
            if hasattr(score1, dim_name) and hasattr(score2, dim_name):
                v1 = getattr(score1, dim_name)
                v2 = getattr(score2, dim_name)
                comparison['dimensions'][dim_name] = {
                    'item1': v1,
                    'item2': v2,
                    'winner': item_id1 if v1 > v2 else item_id2
                }
        
        return comparison
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ranking statistics"""
        if not self.scores:
            return {'status': 'no_items_scored'}
        
        all_scores = [s.overall_score for s in self.scores.values()]
        
        return {
            'items_scored': self.stats['items_scored'],
            'avg_score': np.mean(all_scores),
            'median_score': np.median(all_scores),
            'std_score': np.std(all_scores),
            'min_score': np.min(all_scores),
            'max_score': np.max(all_scores),
            'by_type': {
                item_type: len([s for s in self.scores.values() if s.item_type == item_type])
                for item_type in set(s.item_type for s in self.scores.values())
            },
            'weights': self.weights
        }

"""
Hypothesis Generator - Autonomous Research Question Generation
===============================================================

Implements automatic hypothesis generation from anomalies and surprises:
1. Pattern-based hypotheses from anomaly patterns
2. Causal hypotheses from correlations
3. Predictive hypotheses from trends
4. Comparative hypotheses across assets/timeframes
5. Mechanistic hypotheses about market dynamics

Based on the Foundation Agents paper (arXiv:2504.01990) curiosity systems.
"""

import logging
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class HypothesisType(Enum):
    """Types of hypotheses"""
    CAUSAL = "causal"                    # X causes Y
    CORRELATIONAL = "correlational"      # X correlates with Y
    PREDICTIVE = "predictive"            # X predicts Y
    COMPARATIVE = "comparative"          # X differs from Y
    MECHANISTIC = "mechanistic"          # How X works
    EXPLANATORY = "explanatory"          # Why X happened
    EXPLORATORY = "exploratory"          # What is X
    COUNTERFACTUAL = "counterfactual"    # What if X


class HypothesisStatus(Enum):
    """Status of a hypothesis"""
    GENERATED = "generated"      # Just created
    PRIORITIZED = "prioritized"  # Selected for testing
    TESTING = "testing"          # Currently being tested
    SUPPORTED = "supported"      # Evidence supports
    REJECTED = "rejected"        # Evidence rejects
    INCONCLUSIVE = "inconclusive"  # Not enough evidence
    ARCHIVED = "archived"        # No longer active


class HypothesisPriority(Enum):
    """Priority for testing hypotheses"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


@dataclass
class Hypothesis:
    """A research hypothesis"""
    hypothesis_id: str
    hypothesis_type: HypothesisType
    
    # Content
    statement: str  # The hypothesis statement
    null_hypothesis: Optional[str] = None  # H0
    alternative_hypothesis: Optional[str] = None  # H1
    
    # Variables
    independent_vars: List[str] = field(default_factory=list)
    dependent_vars: List[str] = field(default_factory=list)
    control_vars: List[str] = field(default_factory=list)
    
    # Source
    source_anomaly_id: Optional[str] = None
    source_surprise_id: Optional[str] = None
    triggered_by: str = ""  # What triggered this hypothesis
    
    # Priority and status
    priority: HypothesisPriority = HypothesisPriority.MEDIUM
    status: HypothesisStatus = HypothesisStatus.GENERATED
    
    # Scoring
    novelty_score: float = 0.5      # How novel is this hypothesis
    impact_score: float = 0.5       # Potential impact if true
    feasibility_score: float = 0.5  # How feasible to test
    confidence_score: float = 0.0   # Confidence in hypothesis (after testing)
    
    # Testing
    test_method: Optional[str] = None
    required_data: List[str] = field(default_factory=list)
    estimated_test_duration: Optional[timedelta] = None
    
    # Results
    evidence_for: List[Dict] = field(default_factory=list)
    evidence_against: List[Dict] = field(default_factory=list)
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    tested_at: Optional[datetime] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    related_hypotheses: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def overall_score(self) -> float:
        """Calculate overall priority score"""
        return (
            self.novelty_score * 0.3 +
            self.impact_score * 0.4 +
            self.feasibility_score * 0.3
        )
    
    def to_dict(self) -> Dict:
        return {
            'hypothesis_id': self.hypothesis_id,
            'hypothesis_type': self.hypothesis_type.value,
            'statement': self.statement,
            'priority': self.priority.value,
            'status': self.status.value,
            'novelty_score': self.novelty_score,
            'impact_score': self.impact_score,
            'feasibility_score': self.feasibility_score,
            'overall_score': self.overall_score(),
            'created_at': self.created_at.isoformat(),
            'tags': self.tags
        }


class HypothesisTemplate:
    """Templates for generating hypotheses"""
    
    CAUSAL_TEMPLATES = [
        "Changes in {var1} cause changes in {var2}",
        "{var1} is a leading indicator of {var2}",
        "Increases in {var1} lead to decreases in {var2}",
        "{var1} drives {var2} through {mechanism}",
    ]
    
    CORRELATIONAL_TEMPLATES = [
        "{var1} and {var2} are positively correlated during {condition}",
        "The correlation between {var1} and {var2} breaks down when {condition}",
        "{var1} co-moves with {var2} with a lag of {lag}",
    ]
    
    PREDICTIVE_TEMPLATES = [
        "{var1} can predict {var2} with {timeframe} lead time",
        "The pattern in {var1} predicts {outcome}",
        "When {condition}, {var1} predicts {var2}",
    ]
    
    COMPARATIVE_TEMPLATES = [
        "{var1} behaves differently in {regime1} vs {regime2}",
        "{asset1} outperforms {asset2} when {condition}",
        "The relationship between {var1} and {var2} differs across {dimension}",
    ]
    
    MECHANISTIC_TEMPLATES = [
        "The mechanism behind {phenomenon} involves {factors}",
        "{var1} affects {var2} through the channel of {channel}",
        "The {phenomenon} is driven by {mechanism}",
    ]
    
    EXPLANATORY_TEMPLATES = [
        "The anomaly in {var1} is explained by {explanation}",
        "{phenomenon} occurred because of {cause}",
        "The surprise in {var1} can be attributed to {factor}",
    ]


class CausalHypothesisGenerator:
    """Generate causal hypotheses"""
    
    def generate(
        self,
        var1: str,
        var2: str,
        correlation: float,
        lag: Optional[int] = None,
        context: Optional[Dict] = None
    ) -> List[Hypothesis]:
        """Generate causal hypotheses from correlation"""
        hypotheses = []
        
        # Basic causal hypothesis
        if abs(correlation) > 0.5:
            direction = "positive" if correlation > 0 else "negative"
            
            h = Hypothesis(
                hypothesis_id=f"causal_{var1}_{var2}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                hypothesis_type=HypothesisType.CAUSAL,
                statement=f"Changes in {var1} cause {direction} changes in {var2}",
                null_hypothesis=f"{var1} has no causal effect on {var2}",
                alternative_hypothesis=f"{var1} has a {direction} causal effect on {var2}",
                independent_vars=[var1],
                dependent_vars=[var2],
                triggered_by=f"correlation={correlation:.2f}",
                novelty_score=0.6,
                impact_score=0.7 if abs(correlation) > 0.7 else 0.5,
                feasibility_score=0.7,
                test_method="granger_causality",
                tags=["causal", var1, var2]
            )
            hypotheses.append(h)
        
        # Lead-lag hypothesis
        if lag is not None and lag > 0:
            h = Hypothesis(
                hypothesis_id=f"leadlag_{var1}_{var2}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                hypothesis_type=HypothesisType.PREDICTIVE,
                statement=f"{var1} leads {var2} by {lag} periods",
                independent_vars=[var1],
                dependent_vars=[var2],
                triggered_by=f"lag={lag}",
                novelty_score=0.7,
                impact_score=0.8,
                feasibility_score=0.8,
                test_method="cross_correlation",
                tags=["lead-lag", var1, var2],
                metadata={'lag': lag}
            )
            hypotheses.append(h)
        
        return hypotheses


class AnomalyHypothesisGenerator:
    """Generate hypotheses from anomalies"""
    
    def generate(
        self,
        anomaly_type: str,
        description: str,
        asset: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[Hypothesis]:
        """Generate hypotheses to explain an anomaly"""
        hypotheses = []
        context = context or {}
        
        # Explanatory hypothesis
        h_explain = Hypothesis(
            hypothesis_id=f"explain_{anomaly_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            hypothesis_type=HypothesisType.EXPLANATORY,
            statement=f"The {anomaly_type} anomaly in {asset or 'the market'} is caused by an underlying regime change",
            triggered_by=description,
            novelty_score=0.6,
            impact_score=0.7,
            feasibility_score=0.6,
            test_method="regime_detection",
            tags=["anomaly", anomaly_type, "explanation"]
        )
        hypotheses.append(h_explain)
        
        # Predictive hypothesis
        h_predict = Hypothesis(
            hypothesis_id=f"predict_{anomaly_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            hypothesis_type=HypothesisType.PREDICTIVE,
            statement=f"The {anomaly_type} anomaly predicts future price movement",
            triggered_by=description,
            novelty_score=0.7,
            impact_score=0.8,
            feasibility_score=0.7,
            test_method="event_study",
            tags=["anomaly", anomaly_type, "prediction"]
        )
        hypotheses.append(h_predict)
        
        # Pattern hypothesis
        if 'observed_value' in context and 'expected_value' in context:
            deviation = context['observed_value'] - context['expected_value']
            direction = "above" if deviation > 0 else "below"
            
            h_pattern = Hypothesis(
                hypothesis_id=f"pattern_{anomaly_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                hypothesis_type=HypothesisType.EXPLORATORY,
                statement=f"Values {direction} expectation in {asset or 'this context'} represent a recurring pattern",
                triggered_by=description,
                novelty_score=0.5,
                impact_score=0.6,
                feasibility_score=0.8,
                test_method="pattern_analysis",
                tags=["anomaly", "pattern"],
                metadata={'deviation': deviation}
            )
            hypotheses.append(h_pattern)
        
        return hypotheses


class SurpriseHypothesisGenerator:
    """Generate hypotheses from surprising events"""
    
    def generate(
        self,
        surprise_type: str,
        surprise_value: float,
        variable: str,
        observed: Any,
        expected: Optional[Any] = None,
        context: Optional[Dict] = None
    ) -> List[Hypothesis]:
        """Generate hypotheses from surprising observations"""
        hypotheses = []
        
        # Why was this surprising?
        h_why = Hypothesis(
            hypothesis_id=f"why_surprise_{variable}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            hypothesis_type=HypothesisType.EXPLANATORY,
            statement=f"The surprising value of {variable} indicates a structural change in the underlying process",
            triggered_by=f"surprise_value={surprise_value:.2f}",
            novelty_score=0.7,
            impact_score=0.6,
            feasibility_score=0.6,
            test_method="structural_break_test",
            tags=["surprise", variable, "structural"]
        )
        hypotheses.append(h_why)
        
        # Is this the new normal?
        h_regime = Hypothesis(
            hypothesis_id=f"regime_{variable}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            hypothesis_type=HypothesisType.PREDICTIVE,
            statement=f"The surprising {variable} value represents a regime shift that will persist",
            triggered_by=f"surprise_value={surprise_value:.2f}",
            novelty_score=0.6,
            impact_score=0.8,
            feasibility_score=0.5,
            test_method="regime_persistence_test",
            tags=["surprise", variable, "regime"]
        )
        hypotheses.append(h_regime)
        
        # What else is affected?
        h_spillover = Hypothesis(
            hypothesis_id=f"spillover_{variable}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            hypothesis_type=HypothesisType.CAUSAL,
            statement=f"The surprise in {variable} will cause spillover effects in related variables",
            triggered_by=f"surprise_value={surprise_value:.2f}",
            novelty_score=0.6,
            impact_score=0.7,
            feasibility_score=0.7,
            test_method="spillover_analysis",
            tags=["surprise", variable, "spillover"]
        )
        hypotheses.append(h_spillover)
        
        return hypotheses


class HypothesisGenerator:
    """
    Hypothesis Generator
    
    Central system for generating research hypotheses from:
    - Anomalies
    - Surprises
    - Patterns
    - Correlations
    - External triggers
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Sub-generators
        self.causal_gen = CausalHypothesisGenerator()
        self.anomaly_gen = AnomalyHypothesisGenerator()
        self.surprise_gen = SurpriseHypothesisGenerator()
        
        # Hypothesis storage
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.hypothesis_history: List[Hypothesis] = []
        
        # Deduplication
        self.hypothesis_hashes: set = set()
        
        # Statistics
        self.stats = {
            'total_generated': 0,
            'by_type': {ht.value: 0 for ht in HypothesisType},
            'by_status': {hs.value: 0 for hs in HypothesisStatus},
            'supported': 0,
            'rejected': 0
        }
        
        logger.info("Hypothesis Generator initialized")
    
    def _hash_hypothesis(self, statement: str) -> str:
        """Create hash for deduplication"""
        return hashlib.md5(statement.lower().encode()).hexdigest()
    
    def _is_duplicate(self, statement: str) -> bool:
        """Check if hypothesis is duplicate"""
        h = self._hash_hypothesis(statement)
        if h in self.hypothesis_hashes:
            return True
        self.hypothesis_hashes.add(h)
        return False
    
    def generate_from_anomaly(
        self,
        anomaly_type: str,
        description: str,
        asset: Optional[str] = None,
        anomaly_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[Hypothesis]:
        """Generate hypotheses from an anomaly"""
        hypotheses = self.anomaly_gen.generate(
            anomaly_type=anomaly_type,
            description=description,
            asset=asset,
            context=context
        )
        
        # Filter duplicates and store
        unique = []
        for h in hypotheses:
            if not self._is_duplicate(h.statement):
                h.source_anomaly_id = anomaly_id
                self._store_hypothesis(h)
                unique.append(h)
        
        return unique
    
    def generate_from_surprise(
        self,
        surprise_type: str,
        surprise_value: float,
        variable: str,
        observed: Any,
        expected: Optional[Any] = None,
        surprise_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[Hypothesis]:
        """Generate hypotheses from a surprising event"""
        hypotheses = self.surprise_gen.generate(
            surprise_type=surprise_type,
            surprise_value=surprise_value,
            variable=variable,
            observed=observed,
            expected=expected,
            context=context
        )
        
        # Filter duplicates and store
        unique = []
        for h in hypotheses:
            if not self._is_duplicate(h.statement):
                h.source_surprise_id = surprise_id
                self._store_hypothesis(h)
                unique.append(h)
        
        return unique
    
    def generate_from_correlation(
        self,
        var1: str,
        var2: str,
        correlation: float,
        lag: Optional[int] = None,
        context: Optional[Dict] = None
    ) -> List[Hypothesis]:
        """Generate hypotheses from correlation observation"""
        hypotheses = self.causal_gen.generate(
            var1=var1,
            var2=var2,
            correlation=correlation,
            lag=lag,
            context=context
        )
        
        # Filter duplicates and store
        unique = []
        for h in hypotheses:
            if not self._is_duplicate(h.statement):
                self._store_hypothesis(h)
                unique.append(h)
        
        return unique
    
    def generate_custom(
        self,
        hypothesis_type: HypothesisType,
        statement: str,
        independent_vars: Optional[List[str]] = None,
        dependent_vars: Optional[List[str]] = None,
        triggered_by: str = "manual",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Hypothesis]:
        """Generate a custom hypothesis"""
        if self._is_duplicate(statement):
            return None
        
        h = Hypothesis(
            hypothesis_id=f"custom_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(statement.encode()).hexdigest()[:8]}",
            hypothesis_type=hypothesis_type,
            statement=statement,
            independent_vars=independent_vars or [],
            dependent_vars=dependent_vars or [],
            triggered_by=triggered_by,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self._store_hypothesis(h)
        return h
    
    def _store_hypothesis(self, hypothesis: Hypothesis):
        """Store a hypothesis"""
        self.hypotheses[hypothesis.hypothesis_id] = hypothesis
        self.hypothesis_history.append(hypothesis)
        
        self.stats['total_generated'] += 1
        self.stats['by_type'][hypothesis.hypothesis_type.value] += 1
        self.stats['by_status'][hypothesis.status.value] += 1
        
        logger.info(f"Generated hypothesis: {hypothesis.statement[:50]}...")
    
    def prioritize_hypotheses(
        self,
        limit: int = 10,
        hypothesis_type: Optional[HypothesisType] = None,
        min_score: float = 0.0
    ) -> List[Hypothesis]:
        """Prioritize hypotheses for testing"""
        candidates = [
            h for h in self.hypotheses.values()
            if h.status == HypothesisStatus.GENERATED
        ]
        
        if hypothesis_type:
            candidates = [h for h in candidates if h.hypothesis_type == hypothesis_type]
        
        if min_score > 0:
            candidates = [h for h in candidates if h.overall_score() >= min_score]
        
        # Sort by overall score
        candidates.sort(key=lambda h: h.overall_score(), reverse=True)
        
        # Mark as prioritized
        prioritized = candidates[:limit]
        for h in prioritized:
            h.status = HypothesisStatus.PRIORITIZED
            self.stats['by_status'][HypothesisStatus.GENERATED.value] -= 1
            self.stats['by_status'][HypothesisStatus.PRIORITIZED.value] += 1
        
        return prioritized
    
    def update_hypothesis_status(
        self,
        hypothesis_id: str,
        status: HypothesisStatus,
        evidence: Optional[Dict] = None,
        p_value: Optional[float] = None,
        effect_size: Optional[float] = None
    ):
        """Update hypothesis status after testing"""
        if hypothesis_id not in self.hypotheses:
            return
        
        h = self.hypotheses[hypothesis_id]
        old_status = h.status
        h.status = status
        h.tested_at = datetime.utcnow()
        
        if p_value is not None:
            h.p_value = p_value
        
        if effect_size is not None:
            h.effect_size = effect_size
        
        if evidence:
            if status == HypothesisStatus.SUPPORTED:
                h.evidence_for.append(evidence)
                h.confidence_score = min(1.0, h.confidence_score + 0.2)
                self.stats['supported'] += 1
            elif status == HypothesisStatus.REJECTED:
                h.evidence_against.append(evidence)
                h.confidence_score = max(0.0, h.confidence_score - 0.2)
                self.stats['rejected'] += 1
        
        # Update status counts
        self.stats['by_status'][old_status.value] -= 1
        self.stats['by_status'][status.value] += 1
        
        logger.info(f"Hypothesis {hypothesis_id} status: {old_status.value} -> {status.value}")
    
    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Get a hypothesis by ID"""
        return self.hypotheses.get(hypothesis_id)
    
    def get_hypotheses_by_status(self, status: HypothesisStatus) -> List[Hypothesis]:
        """Get hypotheses by status"""
        return [h for h in self.hypotheses.values() if h.status == status]
    
    def get_hypotheses_by_type(self, hypothesis_type: HypothesisType) -> List[Hypothesis]:
        """Get hypotheses by type"""
        return [h for h in self.hypotheses.values() if h.hypothesis_type == hypothesis_type]
    
    def get_related_hypotheses(self, hypothesis_id: str) -> List[Hypothesis]:
        """Get hypotheses related to a given hypothesis"""
        if hypothesis_id not in self.hypotheses:
            return []
        
        h = self.hypotheses[hypothesis_id]
        related = []
        
        # Find by shared variables
        h_vars = set(h.independent_vars + h.dependent_vars)
        for other in self.hypotheses.values():
            if other.hypothesis_id == hypothesis_id:
                continue
            
            other_vars = set(other.independent_vars + other.dependent_vars)
            if h_vars & other_vars:  # Intersection
                related.append(other)
        
        # Find by shared tags
        h_tags = set(h.tags)
        for other in self.hypotheses.values():
            if other.hypothesis_id == hypothesis_id:
                continue
            if other in related:
                continue
            
            other_tags = set(other.tags)
            if len(h_tags & other_tags) >= 2:  # At least 2 shared tags
                related.append(other)
        
        return related
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get hypothesis generation statistics"""
        return {
            **self.stats,
            'active_hypotheses': len([h for h in self.hypotheses.values() 
                                      if h.status not in [HypothesisStatus.ARCHIVED, 
                                                          HypothesisStatus.REJECTED]]),
            'avg_score': np.mean([h.overall_score() for h in self.hypotheses.values()]) 
                        if self.hypotheses else 0,
            'top_hypotheses': [
                h.to_dict() for h in sorted(
                    self.hypotheses.values(),
                    key=lambda x: x.overall_score(),
                    reverse=True
                )[:5]
            ]
        }

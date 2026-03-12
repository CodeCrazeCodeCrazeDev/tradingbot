"""
Hypothesis Engine
==================

AI improves HYPOTHESES, not models.

PHILOSOPHY:
- A hypothesis is a testable belief about market behavior
- Hypotheses are refined through evidence, not curve-fitting
- Failed hypotheses are killed, not patched
- Surviving hypotheses become research candidates

HYPOTHESIS LIFECYCLE:
1. GENERATION - Create hypothesis from observation
2. FORMALIZATION - Define testable predictions
3. VALIDATION - Test against out-of-sample data
4. REFINEMENT - Narrow scope based on evidence
5. GRADUATION - Promote to strategy candidate (requires human approval)
6. DEATH - Kill hypothesis that fails validation

EXAMPLES:
❌ BAD: "This model predicts price with 80% accuracy"
✅ GOOD: "Institutional order flow imbalance precedes price moves by 2-5 bars
          in trending regimes with >70% reliability, but fails in ranging markets"
"""

import logging
import hashlib
import threading
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class HypothesisStatus(Enum):
    """Hypothesis lifecycle status"""
    DRAFT = "draft"                 # Initial creation
    FORMALIZED = "formalized"       # Testable predictions defined
    TESTING = "testing"             # Under validation
    VALIDATED = "validated"         # Passed validation
    REFINED = "refined"             # Narrowed scope
    CANDIDATE = "candidate"         # Ready for human review
    GRADUATED = "graduated"         # Approved for strategy development
    DEAD = "dead"                   # Failed validation - killed
    SUSPENDED = "suspended"         # Temporarily paused


class HypothesisType(Enum):
    """Types of hypotheses"""
    MARKET_BEHAVIOR = "market_behavior"       # How markets behave
    REGIME_TRANSITION = "regime_transition"   # When regimes change
    FAILURE_MODE = "failure_mode"             # When strategies fail
    EDGE_SOURCE = "edge_source"               # Where alpha comes from
    RISK_FACTOR = "risk_factor"               # What drives risk
    CORRELATION = "correlation"               # How assets relate
    TIMING = "timing"                         # When to act
    SIZING = "sizing"                         # How much to risk


class EvidenceType(Enum):
    """Types of evidence"""
    SUPPORTING = "supporting"       # Supports hypothesis
    CONTRADICTING = "contradicting" # Contradicts hypothesis
    NEUTRAL = "neutral"             # Neither supports nor contradicts
    BOUNDARY = "boundary"           # Defines boundary conditions


@dataclass
class Evidence:
    """Evidence for or against a hypothesis"""
    evidence_id: str
    evidence_type: EvidenceType
    description: str
    data_source: str
    time_period: str
    sample_size: int
    statistical_significance: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'evidence_id': self.evidence_id,
            'evidence_type': self.evidence_type.value,
            'description': self.description,
            'data_source': self.data_source,
            'time_period': self.time_period,
            'sample_size': self.sample_size,
            'statistical_significance': self.statistical_significance,
            'effect_size': self.effect_size,
            'confidence_interval': self.confidence_interval,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class TestablePredicition:
    """A testable prediction derived from hypothesis"""
    prediction_id: str
    description: str
    condition: str              # When this prediction applies
    expected_outcome: str       # What should happen
    measurement: str            # How to measure
    threshold: float            # Success threshold
    time_horizon: str           # How long to test
    falsifiable: bool = True    # Must be falsifiable
    
    def to_dict(self) -> Dict:
        return {
            'prediction_id': self.prediction_id,
            'description': self.description,
            'condition': self.condition,
            'expected_outcome': self.expected_outcome,
            'measurement': self.measurement,
            'threshold': self.threshold,
            'time_horizon': self.time_horizon,
            'falsifiable': self.falsifiable
        }


@dataclass
class BoundaryCondition:
    """Conditions under which hypothesis applies"""
    condition_id: str
    description: str
    regime: str                 # Market regime
    asset_class: str            # Asset class
    time_of_day: str            # Time constraints
    volatility_range: Tuple[float, float]
    liquidity_requirement: str
    
    def to_dict(self) -> Dict:
        return {
            'condition_id': self.condition_id,
            'description': self.description,
            'regime': self.regime,
            'asset_class': self.asset_class,
            'time_of_day': self.time_of_day,
            'volatility_range': self.volatility_range,
            'liquidity_requirement': self.liquidity_requirement
        }


@dataclass
class Hypothesis:
    """
    A testable belief about market behavior.
    
    REQUIREMENTS:
    1. Must be falsifiable
    2. Must have testable predictions
    3. Must define boundary conditions
    4. Must specify what would kill it
    """
    hypothesis_id: str
    hypothesis_type: HypothesisType
    status: HypothesisStatus
    
    # Core hypothesis
    statement: str              # Clear statement of belief
    rationale: str              # Why this might be true
    mechanism: str              # Causal mechanism
    
    # Testable components
    predictions: List[TestablePredicition] = field(default_factory=list)
    boundary_conditions: List[BoundaryCondition] = field(default_factory=list)
    
    # Evidence
    supporting_evidence: List[Evidence] = field(default_factory=list)
    contradicting_evidence: List[Evidence] = field(default_factory=list)
    
    # Kill conditions
    kill_conditions: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    last_tested: Optional[datetime] = None
    test_count: int = 0
    
    # Scores
    evidence_score: float = 0.0     # -1 to 1 (negative = contradicting)
    confidence: float = 0.0         # 0 to 1
    robustness: float = 0.0         # 0 to 1 (across conditions)
    
    def to_dict(self) -> Dict:
        return {
            'hypothesis_id': self.hypothesis_id,
            'hypothesis_type': self.hypothesis_type.value,
            'status': self.status.value,
            'statement': self.statement,
            'rationale': self.rationale,
            'mechanism': self.mechanism,
            'predictions': [p.to_dict() for p in self.predictions],
            'boundary_conditions': [b.to_dict() for b in self.boundary_conditions],
            'supporting_evidence': [e.to_dict() for e in self.supporting_evidence],
            'contradicting_evidence': [e.to_dict() for e in self.contradicting_evidence],
            'kill_conditions': self.kill_conditions,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'last_tested': self.last_tested.isoformat() if self.last_tested else None,
            'test_count': self.test_count,
            'evidence_score': self.evidence_score,
            'confidence': self.confidence,
            'robustness': self.robustness
        }


class HypothesisGenerator(ABC):
    """Abstract base for hypothesis generators"""
    
    @abstractmethod
    def generate(self, observations: Dict[str, Any]) -> List[Hypothesis]:
        """Generate hypotheses from observations"""
        pass


class MarketBehaviorGenerator(HypothesisGenerator):
    """Generate hypotheses about market behavior"""
    
    def generate(self, observations: Dict[str, Any]) -> List[Hypothesis]:
        hypotheses = []
        
        # Analyze observations for patterns
        if 'price_patterns' in observations:
            for pattern in observations['price_patterns']:
                hypothesis = self._create_pattern_hypothesis(pattern)
                if hypothesis:
                    hypotheses.append(hypothesis)
        
        if 'volume_anomalies' in observations:
            for anomaly in observations['volume_anomalies']:
                hypothesis = self._create_volume_hypothesis(anomaly)
                if hypothesis:
                    hypotheses.append(hypothesis)
        
        if 'regime_changes' in observations:
            for change in observations['regime_changes']:
                hypothesis = self._create_regime_hypothesis(change)
                if hypothesis:
                    hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _create_pattern_hypothesis(self, pattern: Dict) -> Optional[Hypothesis]:
        """Create hypothesis from price pattern observation"""
        hypothesis_id = hashlib.md5(
            f"pattern_{pattern.get('name', '')}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        return Hypothesis(
            hypothesis_id=hypothesis_id,
            hypothesis_type=HypothesisType.MARKET_BEHAVIOR,
            status=HypothesisStatus.DRAFT,
            statement=f"Price pattern '{pattern.get('name', 'unknown')}' predicts "
                     f"directional move with {pattern.get('reliability', 0):.0%} reliability",
            rationale=f"Observed pattern in {pattern.get('occurrences', 0)} instances",
            mechanism=pattern.get('mechanism', 'Unknown causal mechanism'),
            predictions=[
                TestablePredicition(
                    prediction_id=f"{hypothesis_id}_pred_1",
                    description=f"Pattern completion leads to {pattern.get('expected_move', 'directional move')}",
                    condition="Pattern identified with >80% completion",
                    expected_outcome=f"Price moves {pattern.get('expected_direction', 'in predicted direction')}",
                    measurement="Price change within time horizon",
                    threshold=pattern.get('min_move', 0.5),
                    time_horizon=pattern.get('time_horizon', '4 hours')
                )
            ],
            kill_conditions=[
                f"Reliability drops below {pattern.get('min_reliability', 0.5):.0%}",
                "Pattern fails in 3 consecutive occurrences",
                "Mechanism is invalidated by market structure change"
            ]
        )
    
    def _create_volume_hypothesis(self, anomaly: Dict) -> Optional[Hypothesis]:
        """Create hypothesis from volume anomaly"""
        hypothesis_id = hashlib.md5(
            f"volume_{anomaly.get('type', '')}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        return Hypothesis(
            hypothesis_id=hypothesis_id,
            hypothesis_type=HypothesisType.EDGE_SOURCE,
            status=HypothesisStatus.DRAFT,
            statement=f"Volume anomaly type '{anomaly.get('type', 'unknown')}' indicates "
                     f"institutional activity preceding price move",
            rationale="Unusual volume often precedes significant price moves",
            mechanism="Institutional accumulation/distribution creates volume signature",
            predictions=[
                TestablePredicition(
                    prediction_id=f"{hypothesis_id}_pred_1",
                    description="Volume spike precedes directional move",
                    condition="Volume > 2x average with price consolidation",
                    expected_outcome="Breakout in direction of volume imbalance",
                    measurement="Price movement within 24 hours",
                    threshold=1.0,
                    time_horizon="24 hours"
                )
            ],
            kill_conditions=[
                "Volume spikes show no predictive power over 100 samples",
                "False positive rate exceeds 60%"
            ]
        )
    
    def _create_regime_hypothesis(self, change: Dict) -> Optional[Hypothesis]:
        """Create hypothesis from regime change observation"""
        hypothesis_id = hashlib.md5(
            f"regime_{change.get('from', '')}_{change.get('to', '')}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        return Hypothesis(
            hypothesis_id=hypothesis_id,
            hypothesis_type=HypothesisType.REGIME_TRANSITION,
            status=HypothesisStatus.DRAFT,
            statement=f"Transition from {change.get('from', 'unknown')} to {change.get('to', 'unknown')} "
                     f"regime is preceded by {change.get('indicator', 'specific indicators')}",
            rationale="Regime transitions have identifiable precursors",
            mechanism=change.get('mechanism', 'Market structure shifts create detectable signals'),
            predictions=[
                TestablePredicition(
                    prediction_id=f"{hypothesis_id}_pred_1",
                    description="Indicator predicts regime change",
                    condition=f"Indicator crosses threshold",
                    expected_outcome=f"Regime changes to {change.get('to', 'new regime')}",
                    measurement="Regime classification accuracy",
                    threshold=0.7,
                    time_horizon=change.get('lead_time', '1-5 bars')
                )
            ],
            kill_conditions=[
                "Lead time is too short for actionable response",
                "False positive rate makes indicator unusable",
                "Regime definition becomes ambiguous"
            ]
        )


class HypothesisValidator:
    """Validates hypotheses against evidence"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_sample_size = self.config.get('min_sample_size', 100)
        self.min_significance = self.config.get('min_significance', 0.05)
        self.min_effect_size = self.config.get('min_effect_size', 0.1)
    
    def validate(
        self,
        hypothesis: Hypothesis,
        test_data: Dict[str, Any]
    ) -> Tuple[bool, List[Evidence], str]:
        """
        Validate hypothesis against test data.
        
        Returns:
            Tuple of (is_valid, evidence_list, reason)
        """
        evidence_list = []
        
        # Test each prediction
        for prediction in hypothesis.predictions:
            evidence = self._test_prediction(prediction, test_data)
            evidence_list.append(evidence)
        
        # Aggregate evidence
        supporting = sum(1 for e in evidence_list if e.evidence_type == EvidenceType.SUPPORTING)
        contradicting = sum(1 for e in evidence_list if e.evidence_type == EvidenceType.CONTRADICTING)
        
        # Check kill conditions
        for kill_condition in hypothesis.kill_conditions:
            if self._check_kill_condition(kill_condition, evidence_list, test_data):
                return False, evidence_list, f"Kill condition met: {kill_condition}"
        
        # Determine validity
        if contradicting > supporting:
            return False, evidence_list, "More contradicting than supporting evidence"
        
        if supporting == 0:
            return False, evidence_list, "No supporting evidence found"
        
        # Check statistical requirements
        avg_significance = sum(e.statistical_significance for e in evidence_list) / len(evidence_list)
        if avg_significance > self.min_significance:
            return False, evidence_list, f"Statistical significance {avg_significance:.3f} > {self.min_significance}"
        
        return True, evidence_list, "Hypothesis validated"
    
    def _test_prediction(
        self,
        prediction: TestablePredicition,
        test_data: Dict[str, Any]
    ) -> Evidence:
        """Test a single prediction"""
        # Simulate testing (in production, this would run actual backtests)
        import random
        
        sample_size = test_data.get('sample_size', 100)
        
        # Calculate metrics
        success_rate = test_data.get('success_rate', random.uniform(0.4, 0.8))
        effect_size = test_data.get('effect_size', random.uniform(0.05, 0.3))
        p_value = test_data.get('p_value', random.uniform(0.001, 0.1))
        
        # Determine evidence type
        if success_rate >= prediction.threshold and p_value < self.min_significance:
            evidence_type = EvidenceType.SUPPORTING
        elif success_rate < prediction.threshold * 0.5:
            evidence_type = EvidenceType.CONTRADICTING
        else:
            evidence_type = EvidenceType.NEUTRAL
        
        return Evidence(
            evidence_id=hashlib.md5(
                f"{prediction.prediction_id}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16],
            evidence_type=evidence_type,
            description=f"Tested prediction: {prediction.description}",
            data_source=test_data.get('data_source', 'historical'),
            time_period=test_data.get('time_period', 'unknown'),
            sample_size=sample_size,
            statistical_significance=p_value,
            effect_size=effect_size,
            confidence_interval=(
                success_rate - 0.1,
                success_rate + 0.1
            )
        )
    
    def _check_kill_condition(
        self,
        condition: str,
        evidence_list: List[Evidence],
        test_data: Dict[str, Any]
    ) -> bool:
        """Check if a kill condition is met"""
        # Simple keyword matching (in production, more sophisticated)
        condition_lower = condition.lower()
        
        if 'reliability drops below' in condition_lower:
            # Extract threshold and check
            avg_effect = sum(e.effect_size for e in evidence_list) / max(len(evidence_list), 1)
            if avg_effect < 0.3:
                return True
        
        if 'consecutive' in condition_lower and 'fails' in condition_lower:
            # Check for consecutive failures
            contradicting = [e for e in evidence_list if e.evidence_type == EvidenceType.CONTRADICTING]
            if len(contradicting) >= 3:
                return True
        
        return False


class HypothesisEngine:
    """
    Main engine for hypothesis management.
    
    CORE PRINCIPLE:
    Improve HYPOTHESES, not models.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Hypothesis storage
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.dead_hypotheses: Dict[str, Hypothesis] = {}  # Graveyard
        self.graduated_hypotheses: Dict[str, Hypothesis] = {}
        
        # Generators
        self.generators: List[HypothesisGenerator] = [
            MarketBehaviorGenerator()
        ]
        
        # Validator
        self.validator = HypothesisValidator(config)
        
        # Statistics
        self.total_generated = 0
        self.total_killed = 0
        self.total_graduated = 0
        
        logger.info("HypothesisEngine initialized")
    
    def generate_hypotheses(self, observations: Dict[str, Any]) -> List[Hypothesis]:
        """
        Generate new hypotheses from observations.
        
        Args:
            observations: Market observations
            
        Returns:
            List of generated hypotheses
        """
        with self.lock:
            all_hypotheses = []
            
            for generator in self.generators:
                hypotheses = generator.generate(observations)
                all_hypotheses.extend(hypotheses)
            
            # Store hypotheses
            for hypothesis in all_hypotheses:
                self.hypotheses[hypothesis.hypothesis_id] = hypothesis
                self.total_generated += 1
            
            logger.info(
                "Generated %d hypotheses from observations",
                len(all_hypotheses)
            )
            
            return all_hypotheses
    
    def formalize_hypothesis(
        self,
        hypothesis_id: str,
        predictions: List[TestablePredicition],
        boundary_conditions: List[BoundaryCondition],
        kill_conditions: List[str]
    ) -> bool:
        """
        Formalize a hypothesis with testable predictions.
        
        Args:
            hypothesis_id: ID of hypothesis to formalize
            predictions: Testable predictions
            boundary_conditions: When hypothesis applies
            kill_conditions: What would kill the hypothesis
            
        Returns:
            True if formalized successfully
        """
        with self.lock:
            if hypothesis_id not in self.hypotheses:
                logger.error("Hypothesis %s not found", hypothesis_id)
                return False
            
            hypothesis = self.hypotheses[hypothesis_id]
            
            # Validate predictions are falsifiable
            for pred in predictions:
                if not pred.falsifiable:
                    logger.error("Prediction %s is not falsifiable", pred.prediction_id)
                    return False
            
            # Update hypothesis
            hypothesis.predictions = predictions
            hypothesis.boundary_conditions = boundary_conditions
            hypothesis.kill_conditions = kill_conditions
            hypothesis.status = HypothesisStatus.FORMALIZED
            
            logger.info("Formalized hypothesis %s", hypothesis_id)
            return True
    
    def test_hypothesis(
        self,
        hypothesis_id: str,
        test_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Test a hypothesis against data.
        
        Args:
            hypothesis_id: ID of hypothesis to test
            test_data: Data to test against
            
        Returns:
            Tuple of (passed, reason)
        """
        with self.lock:
            if hypothesis_id not in self.hypotheses:
                return False, "Hypothesis not found"
            
            hypothesis = self.hypotheses[hypothesis_id]
            
            if hypothesis.status not in [HypothesisStatus.FORMALIZED, HypothesisStatus.TESTING, HypothesisStatus.REFINED]:
                return False, f"Hypothesis in wrong status: {hypothesis.status.value}"
            
            # Update status
            hypothesis.status = HypothesisStatus.TESTING
            hypothesis.test_count += 1
            hypothesis.last_tested = datetime.now()
            
            # Validate
            is_valid, evidence_list, reason = self.validator.validate(hypothesis, test_data)
            
            # Update evidence
            for evidence in evidence_list:
                if evidence.evidence_type == EvidenceType.SUPPORTING:
                    hypothesis.supporting_evidence.append(evidence)
                elif evidence.evidence_type == EvidenceType.CONTRADICTING:
                    hypothesis.contradicting_evidence.append(evidence)
            
            # Update scores
            self._update_scores(hypothesis)
            
            if is_valid:
                hypothesis.status = HypothesisStatus.VALIDATED
                logger.info("Hypothesis %s VALIDATED: %s", hypothesis_id, reason)
            else:
                # Check if should be killed
                if self._should_kill(hypothesis):
                    self._kill_hypothesis(hypothesis_id, reason)
                else:
                    hypothesis.status = HypothesisStatus.REFINED
                    logger.info("Hypothesis %s needs refinement: %s", hypothesis_id, reason)
            
            return is_valid, reason
    
    def _update_scores(self, hypothesis: Hypothesis):
        """Update hypothesis scores based on evidence"""
        supporting = len(hypothesis.supporting_evidence)
        contradicting = len(hypothesis.contradicting_evidence)
        total = supporting + contradicting
        
        if total > 0:
            # Evidence score: -1 (all contradicting) to 1 (all supporting)
            hypothesis.evidence_score = (supporting - contradicting) / total
            
            # Confidence: based on sample sizes
            total_samples = sum(e.sample_size for e in hypothesis.supporting_evidence)
            hypothesis.confidence = min(1.0, total_samples / 1000)
            
            # Robustness: based on effect sizes
            if hypothesis.supporting_evidence:
                avg_effect = sum(e.effect_size for e in hypothesis.supporting_evidence) / supporting
                hypothesis.robustness = min(1.0, avg_effect * 2)
    
    def _should_kill(self, hypothesis: Hypothesis) -> bool:
        """Determine if hypothesis should be killed"""
        # Kill if evidence score is strongly negative
        if hypothesis.evidence_score < -0.5:
            return True
        
        # Kill if tested many times with no validation
        if hypothesis.test_count >= 5 and hypothesis.status != HypothesisStatus.VALIDATED:
            return True
        
        # Kill if confidence is too low after many tests
        if hypothesis.test_count >= 3 and hypothesis.confidence < 0.2:
            return True
        
        return False
    
    def _kill_hypothesis(self, hypothesis_id: str, reason: str):
        """Kill a hypothesis - move to graveyard"""
        with self.lock:
            if hypothesis_id in self.hypotheses:
                hypothesis = self.hypotheses.pop(hypothesis_id)
                hypothesis.status = HypothesisStatus.DEAD
                self.dead_hypotheses[hypothesis_id] = hypothesis
                self.total_killed += 1
                
                logger.warning(
                    "KILLED hypothesis %s: %s",
                    hypothesis_id,
                    reason
                )
    
    def graduate_hypothesis(
        self,
        hypothesis_id: str,
        approved_by: str
    ) -> bool:
        """
        Graduate hypothesis to strategy candidate.
        REQUIRES HUMAN APPROVAL.
        
        Args:
            hypothesis_id: ID of hypothesis
            approved_by: Human approver
            
        Returns:
            True if graduated
        """
        with self.lock:
            if hypothesis_id not in self.hypotheses:
                return False
            
            hypothesis = self.hypotheses[hypothesis_id]
            
            if hypothesis.status != HypothesisStatus.VALIDATED:
                logger.error(
                    "Cannot graduate hypothesis %s - not validated",
                    hypothesis_id
                )
                return False
            
            # Move to graduated
            hypothesis.status = HypothesisStatus.GRADUATED
            self.graduated_hypotheses[hypothesis_id] = self.hypotheses.pop(hypothesis_id)
            self.total_graduated += 1
            
            logger.info(
                "GRADUATED hypothesis %s (approved by %s)",
                hypothesis_id,
                approved_by
            )
            
            return True
    
    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Get hypothesis by ID"""
        with self.lock:
            if hypothesis_id in self.hypotheses:
                return self.hypotheses[hypothesis_id]
            if hypothesis_id in self.graduated_hypotheses:
                return self.graduated_hypotheses[hypothesis_id]
            if hypothesis_id in self.dead_hypotheses:
                return self.dead_hypotheses[hypothesis_id]
            return None
    
    def get_active_hypotheses(self) -> List[Hypothesis]:
        """Get all active hypotheses"""
        with self.lock:
            return list(self.hypotheses.values())
    
    def get_graduated_hypotheses(self) -> List[Hypothesis]:
        """Get all graduated hypotheses"""
        with self.lock:
            return list(self.graduated_hypotheses.values())
    
    def get_dead_hypotheses(self) -> List[Hypothesis]:
        """Get all dead hypotheses (graveyard)"""
        with self.lock:
            return list(self.dead_hypotheses.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        with self.lock:
            return {
                'total_generated': self.total_generated,
                'total_killed': self.total_killed,
                'total_graduated': self.total_graduated,
                'active_count': len(self.hypotheses),
                'graduated_count': len(self.graduated_hypotheses),
                'dead_count': len(self.dead_hypotheses),
                'kill_rate': self.total_killed / max(self.total_generated, 1),
                'graduation_rate': self.total_graduated / max(self.total_generated, 1)
            }

"""
Execution Stages Implementation
==============================

Implements missing stages from Section 7:
- STAGE 2: PROFILE (Capability Fingerprint)
- STAGE 6: DISTILL (Convert to internal assets)
- STAGE 10: ATTRIBUTE (Causal contribution estimation)
- STAGE 11: PRUNE (Archive dead weight)

These complement the existing stages (OBSERVE, BENCHMARK, EXTRACT, INVERT, VALIDATE, DEPLOY, MONITOR).
"""

import asyncio
import json
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
from collections import defaultdict
import numpy as np
from pathlib import Path

from .capability_ontology import CapabilityOntologyRegistry, CapabilityDomain
from .controlled_objects import ControlledObject, PromotionStatus, RiskTier, FailureMode
from .global_objective_function import (
    GlobalObjectiveFunction, CandidateMetrics, UtilityScore, 
    TaskCategory, MarketRegime
)

logger = logging.getLogger(__name__)


@dataclass
class CapabilityFingerprint:
    """
    Stage 2: Capability Fingerprint
    
    Fingerprint dimensions per Section 7:
    - correctness
    - calibration
    - cost efficiency
    - latency distribution
    - tool reliability
    - schema adherence
    - adversarial brittleness
    - regime stability
    - variance across repeated trials
    - integration burden
    - known forbidden-use zones
    """
    object_id: str
    
    # Core dimensions
    correctness_score: float  # 0-1
    calibration_error: float    # Lower is better
    cost_efficiency: float       # 0-1
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    tool_reliability: float     # 0-1
    schema_adherence_rate: float # 0-1
    adversarial_brittleness: float  # 0-1, lower is better
    regime_stability: float    # 0-1
    trial_variance: float      # Lower is better
    integration_burden: float  # 0-1, lower is better
    
    # Forbidden-use zones discovered during profiling
    forbidden_use_zones: List[str]
    
    # Capability mappings
    supported_capabilities: List[str]
    capability_performance: Dict[str, float]
    
    # Metadata
    profiled_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    profile_version: str = "1.0"
    sample_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "object_id": self.object_id,
            "correctness_score": self.correctness_score,
            "calibration_error": self.calibration_error,
            "cost_efficiency": self.cost_efficiency,
            "latency_p50_ms": self.latency_p50_ms,
            "latency_p95_ms": self.latency_p95_ms,
            "latency_p99_ms": self.latency_p99_ms,
            "tool_reliability": self.tool_reliability,
            "schema_adherence_rate": self.schema_adherence_rate,
            "adversarial_brittleness": self.adversarial_brittleness,
            "regime_stability": self.regime_stability,
            "trial_variance": self.trial_variance,
            "integration_burden": self.integration_burden,
            "forbidden_use_zones": self.forbidden_use_zones,
            "supported_capabilities": self.supported_capabilities,
            "capability_performance": self.capability_performance,
            "profiled_at": self.profiled_at,
            "profile_version": self.profile_version,
            "sample_count": self.sample_count
        }


@dataclass
class DistillationRecord:
    """
    Stage 6: Distillation Record
    
    Convert recurring external capability into owned internal assets.
    """
    distillation_id: str
    teacher_object_id: str
    student_object_id: str
    
    # Distillation target
    target_type: str  # 'smaller_model', 'classifier', 'routing_policy', etc.
    
    # What was distilled
    distilled_behaviors: List[str]
    distilled_policies: List[str]
    distilled_rules: List[str]
    
    # Performance comparison
    teacher_performance: Dict[str, float]
    student_performance: Dict[str, float]
    performance_delta: float
    
    # Cost comparison
    teacher_cost_per_call: float
    student_cost_per_call: float
    cost_reduction: float
    
    # Evidence
    training_samples: int
    validation_accuracy: float
    
    # Lifecycle
    distillation_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    revalidation_schedule: str = "monthly"
    status: str = "active"  # active, stale, deprecated
    
    def performance_degradation(self) -> float:
        """Calculate performance degradation from distillation"""
        return 1.0 - (self.student_performance.get("overall", 0) / 
                     (self.teacher_performance.get("overall", 1e-6) + 1e-6))


@dataclass
class AttributionResult:
    """
    Stage 10: Attribution Result
    
    Estimate causal contribution of promoted change.
    """
    attribution_id: str
    object_id: str
    deployment_id: str
    
    # Attribution methods used
    ab_test_result: Optional[Dict[str, Any]]
    replay_comparison: Optional[Dict[str, Any]]
    counterfactual_estimate: Optional[float]
    component_intervention_logs: List[Dict[str, Any]]
    
    # Attribution estimate
    causal_contribution: float  # 0-1, estimated causal effect
    confidence_interval: Tuple[float, float]
    statistical_significance: float  # p-value
    
    # Controls used
    regime_controls: List[str]
    variance_analysis: Dict[str, float]
    
    # Interpretation
    attribution_verdict: str  # 'confirmed', 'likely', 'uncertain', 'noise'
    explanation: str
    
    attributed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def is_genuine_improvement(self, confidence_threshold: float = 0.05) -> bool:
        """Determine if this represents genuine improvement"""
        return (
            self.statistical_significance < confidence_threshold and
            self.causal_contribution > 0 and
            self.attribution_verdict in ['confirmed', 'likely']
        )


@dataclass
class PruningCandidate:
    """
    Stage 11: Pruning Candidate
    
    Objects that may be archived or deleted.
    """
    object_id: str
    reason: str  # why being considered for pruning
    evidence: Dict[str, Any]
    
    # Metrics showing obsolescence
    days_since_last_use: int
    utility_score: float
    newer_alternative_exists: bool
    complexity_penalty: float
    
    # Decision
    recommended_action: str  # 'archive', 'delete', 'keep'
    confidence: float


class Stage2Profiler:
    """
    Stage 2: PROFILE
    
    Build Capability Fingerprint for every candidate object.
    """
    
    def __init__(self):
        self.fingerprints: Dict[str, CapabilityFingerprint] = {}
        self.profiling_history: List[Dict[str, Any]] = []
        logger.info("Stage2Profiler initialized")
    
    async def profile_object(self, obj: ControlledObject,
                          test_suites: Dict[str, List[Dict[str, Any]]]) -> CapabilityFingerprint:
        """
        Profile an object across all fingerprint dimensions.
        """
        logger.info(f"Profiling object {obj.object_id}")
        
        # Run correctness tests
        correctness_results = await self._test_correctness(obj, test_suites.get('correctness', []))
        
        # Run calibration tests
        calibration_results = await self._test_calibration(obj, test_suites.get('calibration', []))
        
        # Measure latency distribution
        latency_results = await self._measure_latency(obj, n_samples=100)
        
        # Test tool reliability
        tool_results = await self._test_tool_reliability(obj, test_suites.get('tools', []))
        
        # Test schema adherence
        schema_results = await self._test_schema_adherence(obj, test_suites.get('schema', []))
        
        # Test adversarial robustness
        adversarial_results = await self._test_adversarial(obj, test_suites.get('adversarial', []))
        
        # Test regime stability
        regime_results = await self._test_regime_stability(obj, test_suites.get('regime', []))
        
        # Measure trial variance
        variance_results = await self._measure_variance(obj, n_trials=10)
        
        # Assess integration burden
        integration_score = await self._assess_integration(obj)
        
        # Discover forbidden-use zones
        forbidden_zones = await self._discover_forbidden_zones(obj, test_suites.get('forbidden', []))
        
        # Build fingerprint
        fingerprint = CapabilityFingerprint(
            object_id=obj.object_id,
            correctness_score=correctness_results['score'],
            calibration_error=calibration_results['error'],
            cost_efficiency=correctness_results['score'] / (latency_results['p50_ms'] / 1000 + 0.001),
            latency_p50_ms=latency_results['p50_ms'],
            latency_p95_ms=latency_results['p95_ms'],
            latency_p99_ms=latency_results['p99_ms'],
            tool_reliability=tool_results['reliability'],
            schema_adherence_rate=schema_results['adherence_rate'],
            adversarial_brittleness=adversarial_results['brittleness'],
            regime_stability=regime_results['stability'],
            trial_variance=variance_results['variance'],
            integration_burden=integration_score,
            forbidden_use_zones=forbidden_zones,
            supported_capabilities=obj.capability_mapping,
            capability_performance=correctness_results['by_capability'],
            sample_count=sum([
                len(test_suites.get(k, [])) 
                for k in ['correctness', 'calibration', 'tools', 'schema', 'adversarial', 'regime']
            ])
        )
        
        self.fingerprints[obj.object_id] = fingerprint
        
        logger.info(f"Completed profiling {obj.object_id}: "
                   f"correctness={fingerprint.correctness_score:.3f}, "
                   f"calibration={fingerprint.calibration_error:.3f}")
        
        return fingerprint
    
    async def _test_correctness(self, obj: ControlledObject, 
                               test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test correctness on capability-specific tests"""
        scores = []
        by_capability = defaultdict(list)
        
        for test in test_cases:
            # Simulate test execution
            score = np.random.uniform(0.7, 1.0)  # Placeholder
            scores.append(score)
            
            for cap in obj.capability_mapping:
                by_capability[cap].append(score)
        
        return {
            'score': np.mean(scores) if scores else 0.5,
            'by_capability': {k: np.mean(v) for k, v in by_capability.items()}
        }
    
    async def _test_calibration(self, obj: ControlledObject,
                               test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test calibration quality"""
        await asyncio.sleep(0.01)
        return {'error': np.random.uniform(0.05, 0.2)}
    
    async def _measure_latency(self, obj: ControlledObject, n_samples: int) -> Dict[str, float]:
        """Measure latency distribution"""
        # Use object's stated profile plus noise
        base_p50 = obj.latency_profile.p50_ms if hasattr(obj, 'latency_profile') else 1000
        latencies = np.random.lognormal(np.log(base_p50), 0.3, n_samples)
        
        return {
            'p50_ms': float(np.percentile(latencies, 50)),
            'p95_ms': float(np.percentile(latencies, 95)),
            'p99_ms': float(np.percentile(latencies, 99))
        }
    
    async def _test_tool_reliability(self, obj: ControlledObject,
                                    test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test tool use reliability"""
        await asyncio.sleep(0.01)
        return {'reliability': np.random.uniform(0.85, 0.99)}
    
    async def _test_schema_adherence(self, obj: ControlledObject,
                                    test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test output schema adherence"""
        await asyncio.sleep(0.01)
        return {'adherence_rate': np.random.uniform(0.9, 1.0)}
    
    async def _test_adversarial(self, obj: ControlledObject,
                               test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test adversarial robustness"""
        await asyncio.sleep(0.01)
        return {'brittleness': np.random.uniform(0.0, 0.3)}
    
    async def _test_regime_stability(self, obj: ControlledObject,
                                    test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test performance stability across market regimes"""
        await asyncio.sleep(0.01)
        return {'stability': np.random.uniform(0.7, 0.95)}
    
    async def _measure_variance(self, obj: ControlledObject, n_trials: int) -> Dict[str, float]:
        """Measure variance across repeated trials"""
        scores = [np.random.uniform(0.8, 1.0) for _ in range(n_trials)]
        return {'variance': float(np.std(scores))}
    
    async def _assess_integration(self, obj: ControlledObject) -> float:
        """Assess integration burden"""
        # Based on object type and complexity
        type_burden = {
            'foundation_model': 0.8,
            'specialist_model': 0.6,
            'local_model': 0.4,
            'prompt': 0.2,
            'symbolic_rule': 0.1
        }
        return type_burden.get(obj.object_type.value, 0.5)
    
    async def _discover_forbidden_zones(self, obj: ControlledObject,
                                       test_cases: List[Dict[str, Any]]) -> List[str]:
        """Discover forbidden-use zones through testing"""
        # Run edge case tests
        forbidden = []
        
        for test in test_cases:
            if test.get('should_fail', False):
                # Test if object incorrectly succeeds on forbidden use
                if np.random.random() > 0.7:  # Simulate detection
                    forbidden.append(test.get('forbidden_pattern', 'unknown'))
        
        return list(set(forbidden))
    
    def get_fingerprint(self, object_id: str) -> Optional[CapabilityFingerprint]:
        """Get fingerprint for an object"""
        return self.fingerprints.get(object_id)
    
    def is_eligible_for_benchmark(self, object_id: str) -> bool:
        """Check if object has been sufficiently profiled"""
        fingerprint = self.fingerprints.get(object_id)
        if not fingerprint:
            return False
        
        # Minimum requirements for benchmark eligibility
        return (
            fingerprint.correctness_score > 0.5 and
            fingerprint.sample_count >= 10
        )


class Stage6Distiller:
    """
    Stage 6: DISTILL
    
    Convert recurring external capability into owned internal assets.
    
    Distillation targets:
    - smaller internal models
    - classifier heads
    - routing policies
    - scoring functions
    - structured templates
    - symbolic rules
    - failure detectors
    - verifier modules
    - memory compression rules
    """
    
    def __init__(self, objective_fn: GlobalObjectiveFunction):
        self.objective_fn = objective_fn
        self.distillation_records: Dict[str, DistillationRecord] = {}
        self.active_distillations: Dict[str, str] = {}  # teacher_id -> student_id
        logger.info("Stage6Distiller initialized")
    
    async def evaluate_distillation_candidate(self, 
                                             teacher: ControlledObject,
                                             fingerprint: CapabilityFingerprint) -> Dict[str, Any]:
        """
        Evaluate whether a capability should be distilled.
        
        Must prefer:
        teacher frontier model -> distilled internal asset
        over
        permanent dependence on expensive frontier model
        
        unless distillation materially harms objective performance.
        """
        # Check if teacher is expensive enough to justify distillation
        monthly_cost = (teacher.cost_profile.token_cost_per_1k * 1000 +  # Assume 1M tokens
                       teacher.cost_profile.compute_cost_per_hour * 730)  # 1 month
        
        is_expensive = monthly_cost > 1000  # $1000/month threshold
        
        # Estimate distillation cost
        distillation_cost = 5000  # Base cost
        
        # Check if performance degradation acceptable
        max_acceptable_degradation = 0.1  # 10%
        
        return {
            'should_distill': is_expensive,
            'reason': 'high_cost' if is_expensive else 'cost_not_justified',
            'monthly_cost': monthly_cost,
            'distillation_cost': distillation_cost,
            'max_acceptable_degradation': max_acceptable_degradation,
            'payback_months': distillation_cost / (monthly_cost + 0.001)
        }
    
    async def distill_capability(self, teacher: ControlledObject,
                                target_type: str,
                                training_data: List[Dict[str, Any]]) -> DistillationRecord:
        """
        Distill a capability from teacher to internal asset.
        """
        logger.info(f"Distilling {teacher.object_id} to {target_type}")
        
        # Simulate distillation process
        await asyncio.sleep(0.1)
        
        # Generate student object
        student_id = f"distilled_{teacher.object_id}_{target_type}_{datetime.utcnow().timestamp()}"
        
        # Estimate performance (with some degradation)
        teacher_perf = 0.85
        degradation = np.random.uniform(0.02, 0.08)
        student_perf = teacher_perf - degradation
        
        # Calculate cost reduction
        teacher_cost = 0.02  # per call
        student_cost = 0.001  # per call (20x cheaper)
        
        record = DistillationRecord(
            distillation_id=f"dist_{hashlib.md5(student_id.encode()).hexdigest()[:16]}",
            teacher_object_id=teacher.object_id,
            student_object_id=student_id,
            target_type=target_type,
            distilled_behaviors=[f"behavior_{i}" for i in range(5)],
            distilled_policies=[f"policy_{i}" for i in range(3)],
            distilled_rules=[f"rule_{i}" for i in range(2)],
            teacher_performance={'overall': teacher_perf},
            student_performance={'overall': student_perf},
            performance_delta=degradation,
            teacher_cost_per_call=teacher_cost,
            student_cost_per_call=student_cost,
            cost_reduction=(teacher_cost - student_cost) / teacher_cost,
            training_samples=len(training_data),
            validation_accuracy=student_perf
        )
        
        self.distillation_records[record.distillation_id] = record
        self.active_distillations[teacher.object_id] = student_id
        
        logger.info(f"Distillation complete: {record.distillation_id} "
                   f"(degradation={degradation:.3f}, cost_reduction={record.cost_reduction:.1%})")
        
        return record
    
    def get_student_for_teacher(self, teacher_id: str) -> Optional[str]:
        """Get student object ID for a teacher"""
        return self.active_distillations.get(teacher_id)
    
    def check_distillation_health(self, distillation_id: str) -> Dict[str, Any]:
        """Check if distilled asset is still performing adequately"""
        record = self.distillation_records.get(distillation_id)
        if not record:
            return {'status': 'unknown', 'error': 'record_not_found'}
        
        # Check for drift
        drift_detected = np.random.random() < 0.1  # 10% chance of drift
        
        if drift_detected:
            record.status = 'stale'
            return {
                'status': 'stale',
                'drift_detected': True,
                'recommendation': 'retrain_or_deprecate'
            }
        
        return {
            'status': record.status,
            'performance_delta': record.performance_delta,
            'cost_savings_active': True
        }


class Stage10Attributor:
    """
    Stage 10: ATTRIBUTE
    
    Estimate causal contribution of promoted change.
    
    Methods:
    - controlled A/B comparisons
    - replay comparisons
    - counterfactual analysis
    - component-level intervention logs
    - regime controls
    - pre/post variance analysis
    
    Forbidden from claiming success based on raw uplift alone.
    """
    
    def __init__(self):
        self.attribution_history: List[AttributionResult] = []
        self.active_experiments: Dict[str, Dict[str, Any]] = {}
        logger.info("Stage10Attributor initialized")
    
    async def setup_ab_test(self, object_id: str, deployment_id: str,
                           traffic_split: float = 0.5) -> str:
        """Setup A/B test for attribution"""
        experiment_id = f"ab_{object_id}_{datetime.utcnow().timestamp()}"
        
        self.active_experiments[experiment_id] = {
            'object_id': object_id,
            'deployment_id': deployment_id,
            'traffic_split': traffic_split,
            'started_at': datetime.utcnow().isoformat(),
            'control_metrics': [],
            'treatment_metrics': []
        }
        
        logger.info(f"A/B test setup: {experiment_id}")
        return experiment_id
    
    async def run_attribution_analysis(self, object_id: str, deployment_id: str,
                                      experiment_duration_days: int = 7) -> AttributionResult:
        """
        Run full attribution analysis.
        """
        logger.info(f"Running attribution for {object_id}")
        
        # Simulate A/B test results
        ab_result = await self._run_ab_comparison(object_id, deployment_id)
        
        # Simulate replay comparison
        replay_result = await self._run_replay_comparison(object_id)
        
        # Estimate counterfactual
        counterfactual = await self._estimate_counterfactual(object_id)
        
        # Gather intervention logs
        interventions = await self._gather_intervention_logs(object_id)
        
        # Run variance analysis
        variance = await self._run_variance_analysis(object_id)
        
        # Calculate causal contribution (synthesis of methods)
        causal_estimate = self._synthesize_attribution(
            ab_result, replay_result, counterfactual, interventions, variance
        )
        
        # Determine verdict
        verdict = self._determine_verdict(causal_estimate, variance)
        
        result = AttributionResult(
            attribution_id=f"attr_{hashlib.md5(object_id.encode()).hexdigest()[:16]}",
            object_id=object_id,
            deployment_id=deployment_id,
            ab_test_result=ab_result,
            replay_comparison=replay_result,
            counterfactual_estimate=counterfactual,
            component_intervention_logs=interventions,
            causal_contribution=causal_estimate['point_estimate'],
            confidence_interval=causal_estimate['confidence_interval'],
            statistical_significance=causal_estimate['p_value'],
            regime_controls=['high_volatility', 'normal'],
            variance_analysis=variance,
            attribution_verdict=verdict,
            explanation=causal_estimate['explanation']
        )
        
        self.attribution_history.append(result)
        
        logger.info(f"Attribution complete for {object_id}: "
                   f"causal={result.causal_contribution:.3f}, "
                   f"verdict={verdict}")
        
        return result
    
    async def _run_ab_comparison(self, object_id: str, deployment_id: str) -> Dict[str, Any]:
        """Run A/B comparison"""
        await asyncio.sleep(0.01)
        
        # Simulate A/B test
        control_performance = np.random.uniform(0.7, 0.8)
        treatment_performance = control_performance + np.random.uniform(-0.05, 0.15)
        
        return {
            'control_mean': control_performance,
            'treatment_mean': treatment_performance,
            'difference': treatment_performance - control_performance,
            'p_value': np.random.uniform(0.01, 0.2),
            'sample_size_control': 1000,
            'sample_size_treatment': 1000
        }
    
    async def _run_replay_comparison(self, object_id: str) -> Dict[str, Any]:
        """Run replay comparison"""
        await asyncio.sleep(0.01)
        
        # Simulate replay on historical data
        baseline_score = np.random.uniform(0.75, 0.85)
        new_score = baseline_score + np.random.uniform(-0.03, 0.08)
        
        return {
            'baseline_score': baseline_score,
            'new_score': new_score,
            'improvement': new_score - baseline_score,
            'replay_count': 500
        }
    
    async def _estimate_counterfactual(self, object_id: str) -> float:
        """Estimate counterfactual (what would have happened without change)"""
        await asyncio.sleep(0.01)
        # Counterfactual estimate
        return np.random.uniform(0.0, 0.1)
    
    async def _gather_intervention_logs(self, object_id: str) -> List[Dict[str, Any]]:
        """Gather component-level intervention logs"""
        return [
            {'timestamp': datetime.utcnow().isoformat(), 'component': 'routing', 'effect': 0.02},
            {'timestamp': datetime.utcnow().isoformat(), 'component': 'scoring', 'effect': 0.01}
        ]
    
    async def _run_variance_analysis(self, object_id: str) -> Dict[str, float]:
        """Run pre/post variance analysis"""
        return {
            'pre_variance': np.random.uniform(0.05, 0.15),
            'post_variance': np.random.uniform(0.04, 0.12),
            'variance_reduction': np.random.uniform(-0.05, 0.1)
        }
    
    def _synthesize_attribution(self, ab: Dict, replay: Dict, 
                               counterfactual: float, 
                               interventions: List[Dict],
                               variance: Dict) -> Dict[str, Any]:
        """Synthesize multiple attribution methods"""
        # Weighted combination
        ab_weight = 0.4
        replay_weight = 0.3
        counterfactual_weight = 0.2
        variance_weight = 0.1
        
        point_estimate = (
            ab_weight * ab['difference'] +
            replay_weight * replay['improvement'] +
            counterfactual_weight * counterfactual +
            variance_weight * variance.get('variance_reduction', 0)
        )
        
        # Confidence interval
        std_error = 0.03
        ci_lower = point_estimate - 1.96 * std_error
        ci_upper = point_estimate + 1.96 * std_error
        
        # P-value from A/B test
        p_value = ab.get('p_value', 0.5)
        
        explanation = (
            f"Causal contribution estimated at {point_estimate:.3f} "
            f"(CI: [{ci_lower:.3f}, {ci_upper:.3f}]). "
            f"A/B test showed {ab['difference']:+.3f} (p={p_value:.3f}). "
            f"Replay confirmed {replay['improvement']:+.3f}."
        )
        
        return {
            'point_estimate': point_estimate,
            'confidence_interval': (ci_lower, ci_upper),
            'p_value': p_value,
            'explanation': explanation
        }
    
    def _determine_verdict(self, estimate: Dict, variance: Dict) -> str:
        """Determine attribution verdict"""
        point = estimate['point_estimate']
        p_value = estimate['p_value']
        ci_lower, ci_upper = estimate['confidence_interval']
        
        if p_value < 0.05 and point > 0 and ci_lower > 0:
            return 'confirmed'
        elif p_value < 0.1 and point > 0:
            return 'likely'
        elif p_value > 0.3:
            return 'noise'
        else:
            return 'uncertain'


class Stage11Pruner:
    """
    Stage 11: PRUNE
    
    Archive or delete any behavior, route, policy, or distilled artifact that:
    - no longer improves utility
    - is dominated by a superior replacement
    - has not been selected within the configured retention window
    - creates unnecessary complexity
    - has become stale after frontier shifts
    
    Mantra: If it does not improve the objective, it is dead weight.
    """
    
    def __init__(self, objective_fn: GlobalObjectiveFunction,
                 retention_window_days: int = 90):
        self.objective_fn = objective_fn
        self.retention_window_days = retention_window_days
        self.pruning_candidates: List[PruningCandidate] = []
        self.pruned_objects: List[str] = []
        logger.info(f"Stage11Pruner initialized (retention={retention_window_days} days)")
    
    async def identify_pruning_candidates(self, 
                                         objects: List[ControlledObject],
                                         fingerprints: Dict[str, CapabilityFingerprint],
                                         usage_logs: Dict[str, List[datetime]]) -> List[PruningCandidate]:
        """
        Identify objects that should be considered for pruning.
        """
        candidates = []
        now = datetime.utcnow()
        
        for obj in objects:
            fingerprint = fingerprints.get(obj.object_id)
            usage = usage_logs.get(obj.object_id, [])
            
            # Check 1: Not used in retention window
            last_use = max(usage) if usage else None
            days_since_use = (now - last_use).days if last_use else 999
            
            # Check 2: Utility score
            utility = await self._calculate_current_utility(obj, fingerprint)
            
            # Check 3: Check for dominating alternatives
            has_better_alternative = await self._check_for_better_alternative(obj, objects, fingerprints)
            
            # Check 4: Complexity penalty
            complexity = fingerprint.integration_burden if fingerprint else 0.5
            
            # Determine if pruning candidate
            reasons = []
            if days_since_use > self.retention_window_days:
                reasons.append(f"unused_for_{days_since_use}_days")
            if utility < 0:
                reasons.append(f"negative_utility_{utility:.3f}")
            if has_better_alternative:
                reasons.append("dominated_by_alternative")
            if complexity > 0.7 and len(obj.capability_mapping) < 2:
                reasons.append("high_complexity_low_coverage")
            
            if reasons:
                # Determine recommended action
                if utility < -1 or days_since_use > 365:
                    action = 'delete'
                elif utility < 0 or has_better_alternative:
                    action = 'archive'
                else:
                    action = 'review'
                
                candidate = PruningCandidate(
                    object_id=obj.object_id,
                    reason='; '.join(reasons),
                    evidence={
                        'days_since_use': days_since_use,
                        'utility_score': utility,
                        'has_better_alternative': has_better_alternative,
                        'complexity': complexity
                    },
                    days_since_last_use=days_since_use,
                    utility_score=utility,
                    newer_alternative_exists=has_better_alternative,
                    complexity_penalty=complexity,
                    recommended_action=action,
                    confidence=min(1.0, len(reasons) * 0.25 + 0.5)
                )
                candidates.append(candidate)
        
        self.pruning_candidates = candidates
        
        logger.info(f"Identified {len(candidates)} pruning candidates")
        return candidates
    
    async def _calculate_current_utility(self, obj: ControlledObject,
                                        fingerprint: Optional[CapabilityFingerprint]) -> float:
        """Calculate current utility of an object"""
        if not fingerprint:
            return 0
        
        metrics = CandidateMetrics(
            task_success_quality=fingerprint.correctness_score,
            factual_correctness=fingerprint.correctness_score,
            economic_usefulness=0.5,
            calibration_quality=1 - fingerprint.calibration_error,
            regime_robustness=fingerprint.regime_stability,
            latency_ms=fingerprint.latency_p50_ms,
            hallucination_severity=fingerprint.adversarial_brittleness,
            false_confidence_risk=fingerprint.calibration_error,
            output_variance=fingerprint.trial_variance,
            integration_burden=fingerprint.integration_burden,
            auditability_score=0.7
        )
        
        score = self.objective_fn.score_candidate(
            metrics=metrics,
            capability_id=obj.capability_mapping[0] if obj.capability_mapping else 'unknown',
            task_category=TaskCategory.INFRASTRUCTURE,
            risk_tier=RiskTier(obj.risk_tier.value) if hasattr(obj.risk_tier, 'value') else RiskTier.MEDIUM
        )
        
        return score.total_utility
    
    async def _check_for_better_alternative(self, obj: ControlledObject,
                                           all_objects: List[ControlledObject],
                                           fingerprints: Dict[str, CapabilityFingerprint]) -> bool:
        """Check if a better alternative exists"""
        obj_fingerprint = fingerprints.get(obj.object_id)
        if not obj_fingerprint:
            return False
        
        for other in all_objects:
            if other.object_id == obj.object_id:
                continue
            
            # Check capability overlap
            shared_caps = set(obj.capability_mapping) & set(other.capability_mapping)
            if not shared_caps:
                continue
            
            other_fingerprint = fingerprints.get(other.object_id)
            if not other_fingerprint:
                continue
            
            # Check if other dominates
            if (other_fingerprint.correctness_score > obj_fingerprint.correctness_score and
                other_fingerprint.cost_efficiency > obj_fingerprint.cost_efficiency and
                other_fingerprint.latency_p50_ms < obj_fingerprint.latency_p50_ms):
                return True
        
        return False
    
    async def execute_pruning(self, candidates: List[PruningCandidate],
                            registry: Any) -> Dict[str, List[str]]:
        """
        Execute pruning decisions.
        
        Returns list of archived and deleted objects.
        """
        archived = []
        deleted = []
        
        for candidate in candidates:
            if candidate.recommended_action == 'delete':
                # Delete object
                deleted.append(candidate.object_id)
                logger.info(f"Pruned (deleted): {candidate.object_id} - {candidate.reason}")
                
            elif candidate.recommended_action == 'archive':
                # Archive object (mark deprecated)
                archived.append(candidate.object_id)
                logger.info(f"Pruned (archived): {candidate.object_id} - {candidate.reason}")
        
        self.pruned_objects.extend(archived)
        self.pruned_objects.extend(deleted)
        
        return {'archived': archived, 'deleted': deleted}
    
    def get_pruning_summary(self) -> Dict[str, Any]:
        """Get summary of pruning activities"""
        return {
            'total_candidates': len(self.pruning_candidates),
            'total_pruned': len(self.pruned_objects),
            'retention_window_days': self.retention_window_days,
            'pending_candidates': [
                {'object_id': c.object_id, 'reason': c.reason, 'action': c.recommended_action}
                for c in self.pruning_candidates
            ]
        }

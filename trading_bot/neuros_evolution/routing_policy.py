"""
Runtime Routing Policy
======================

Per Section 10: Runtime object selection.

Selection criteria:
- capability fit
- risk tier
- regime
- cost budget
- latency budget
- schema reliability
- verifier compatibility
- historical route performance
- fallback readiness

Every routing decision must produce machine-readable explanation.
"""

import asyncio
import json
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
from collections import defaultdict
import numpy as np

from .capability_ontology import CapabilityOntologyRegistry
from .controlled_objects import ControlledObject, ControlledObjectRegistry, RiskTier, PromotionStatus
from .memory_systems import RoutePerformanceMemory, FailureLibrary, DistillationRegistry

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """
    Routing decision with full explainability.
    
    Must contain:
    - selected object
    - rejected alternatives
    - capability match
    - constraints satisfied
    - controls applied
    - fallback route
    - confidence and uncertainty state
    """
    decision_id: str
    timestamp: str
    
    # Task context
    task_id: str
    required_capabilities: List[str]
    risk_tier: str
    regime: str
    
    # Selected route
    selected_object_id: str
    selection_confidence: float  # 0-1
    
    # Decision rationale
    capability_match_score: float
    constraints_satisfied: List[str]
    constraints_violated: List[str]
    controls_applied: List[str]
    
    # Alternatives
    rejected_alternatives: List[Dict[str, Any]]  # object_id + reason
    
    # Fallback
    fallback_object_id: Optional[str]
    fallback_trigger_conditions: List[str]
    
    # Confidence/uncertainty
    confidence_state: str  # 'high', 'medium', 'low', 'uncertain'
    uncertainty_sources: List[str]
    
    # Cost estimates
    estimated_cost: float
    estimated_latency_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "required_capabilities": self.required_capabilities,
            "risk_tier": self.risk_tier,
            "regime": self.regime,
            "selected_object_id": self.selected_object_id,
            "selection_confidence": self.selection_confidence,
            "capability_match_score": self.capability_match_score,
            "constraints_satisfied": self.constraints_satisfied,
            "constraints_violated": self.constraints_violated,
            "controls_applied": self.controls_applied,
            "rejected_alternatives": self.rejected_alternatives,
            "fallback_object_id": self.fallback_object_id,
            "fallback_trigger_conditions": self.fallback_trigger_conditions,
            "confidence_state": self.confidence_state,
            "uncertainty_sources": self.uncertainty_sources,
            "estimated_cost": self.estimated_cost,
            "estimated_latency_ms": self.estimated_latency_ms
        }


@dataclass
class RoutingConstraints:
    """Constraints for routing decision"""
    max_latency_ms: float
    max_cost: float
    min_capability_score: float
    allowed_risk_tiers: List[str]
    required_regimes: List[str]
    forbidden_objects: List[str]
    schema_requirements: List[str]


class RoutingPolicy:
    """
    Runtime routing policy per Section 10.
    
    Governs selection of controlled objects at runtime.
    """
    
    def __init__(self,
                 object_registry: ControlledObjectRegistry,
                 ontology: CapabilityOntologyRegistry,
                 route_memory: RoutePerformanceMemory,
                 failure_library: FailureLibrary,
                 distillation_registry: DistillationRegistry):
        self.object_registry = object_registry
        self.ontology = ontology
        self.route_memory = route_memory
        self.failure_library = failure_library
        self.distillation_registry = distillation_registry
        
        # Decision history
        self.decisions: List[RoutingDecision] = []
        
        logger.info("RoutingPolicy initialized")
    
    async def select_object(self,
                           task_id: str,
                           required_capabilities: List[str],
                           risk_tier: str,
                           regime: str,
                           constraints: RoutingConstraints) -> RoutingDecision:
        """
        Select best object for task.
        
        Considers:
        - capability fit
        - risk tier
        - regime
        - cost budget
        - latency budget
        - schema reliability
        - verifier compatibility
        - historical route performance
        - fallback readiness
        """
        logger.debug(f"Selecting object for task {task_id}, caps={required_capabilities}")
        
        # Get all candidates
        candidates = await self._get_candidates(required_capabilities)
        
        # Score candidates
        scored_candidates = []
        for candidate in candidates:
            score = await self._score_candidate(
                candidate, required_capabilities, risk_tier, regime, constraints
            )
            scored_candidates.append((candidate, score))
        
        # Sort by score
        scored_candidates.sort(key=lambda x: x[1]['total_score'], reverse=True)
        
        # Select best
        if not scored_candidates:
            # No candidates - create empty decision
            return self._create_fallback_decision(
                task_id, required_capabilities, risk_tier, regime,
                "no_candidates_available"
            )
        
        best_candidate, best_score = scored_candidates[0]
        
        # Check if best is acceptable
        if best_score['total_score'] < 0.3:
            return self._create_fallback_decision(
                task_id, required_capabilities, risk_tier, regime,
                "no_acceptable_candidate"
            )
        
        # Build rejected alternatives list
        rejected = [
            {
                "object_id": c.object_id,
                "reason": f"lower_score_{s['total_score']:.3f}",
                "score": s['total_score']
            }
            for c, s in scored_candidates[1:5]  # Top 5 rejects
        ]
        
        # Identify fallback
        fallback_id = await self._identify_fallback(
            best_candidate, scored_candidates[1:] if len(scored_candidates) > 1 else []
        )
        
        # Build decision
        decision = RoutingDecision(
            decision_id=f"route_{hashlib.md5(f'{task_id}_{datetime.utcnow().timestamp()}'.encode()).hexdigest()[:16]}",
            timestamp=datetime.utcnow().isoformat(),
            task_id=task_id,
            required_capabilities=required_capabilities,
            risk_tier=risk_tier,
            regime=regime,
            selected_object_id=best_candidate.object_id,
            selection_confidence=best_score['confidence'],
            capability_match_score=best_score['capability_match'],
            constraints_satisfied=best_score['satisfied_constraints'],
            constraints_violated=best_score['violated_constraints'],
            controls_applied=best_score['controls'],
            rejected_alternatives=rejected,
            fallback_object_id=fallback_id,
            fallback_trigger_conditions=best_score['fallback_triggers'],
            confidence_state=best_score['confidence_state'],
            uncertainty_sources=best_score['uncertainty_sources'],
            estimated_cost=best_score['estimated_cost'],
            estimated_latency_ms=best_score['estimated_latency']
        )
        
        self.decisions.append(decision)
        
        logger.info(f"Selected {best_candidate.object_id} for task {task_id} "
                   f"(score={best_score['total_score']:.3f}, confidence={best_score['confidence']:.3f})")
        
        return decision
    
    async def _get_candidates(self, required_capabilities: List[str]) -> List[ControlledObject]:
        """Get candidate objects supporting required capabilities"""
        candidates = []
        
        for cap_id in required_capabilities:
            objects = self.object_registry.get_by_capability(cap_id, PromotionStatus.DEPLOYED)
            candidates.extend(objects)
        
        # Deduplicate
        seen = set()
        unique_candidates = []
        for obj in candidates:
            if obj.object_id not in seen:
                seen.add(obj.object_id)
                unique_candidates.append(obj)
        
        return unique_candidates
    
    async def _score_candidate(self,
                              candidate: ControlledObject,
                              required_capabilities: List[str],
                              risk_tier: str,
                              regime: str,
                              constraints: RoutingConstraints) -> Dict[str, Any]:
        """Score a candidate object"""
        
        # 1. Capability match (30% weight)
        matching_caps = set(candidate.capability_mapping) & set(required_capabilities)
        capability_match = len(matching_caps) / len(required_capabilities) if required_capabilities else 0
        
        # 2. Risk tier match (20% weight)
        risk_score = self._score_risk_tier(candidate.risk_tier.value, risk_tier)
        
        # 3. Regime applicability (15% weight)
        regime_score = 1.0 if candidate.is_applicable_to_regime(regime) else 0.0
        
        # 4. Historical performance (20% weight)
        historical = self.route_memory.get_object_performance(
            candidate.object_id, 
            required_capabilities[0] if required_capabilities else None,
            regime,
            limit=50
        )
        
        if historical:
            success_rate = sum(1 for h in historical if h['success']) / len(historical)
            avg_quality = np.mean([h['output_quality'] for h in historical])
            historical_score = (success_rate + avg_quality) / 2
        else:
            historical_score = 0.5  # Unknown - neutral
        
        # 5. Constraint satisfaction (15% weight)
        constraint_results = self._check_constraints(candidate, constraints)
        
        # Calculate total score
        total_score = (
            0.30 * capability_match +
            0.20 * risk_score +
            0.15 * regime_score +
            0.20 * historical_score +
            0.15 * constraint_results['satisfaction_rate']
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            capability_match, len(historical), constraint_results
        )
        
        # Identify uncertainty sources
        uncertainty = []
        if not historical:
            uncertainty.append("no_historical_data")
        if len(historical) < 10:
            uncertainty.append("limited_historical_data")
        if capability_match < 1.0:
            uncertainty.append("partial_capability_match")
        
        # Check for historical failures (regression risk)
        failures = self.failure_library.check_for_regression(
            candidate.object_id, 
            required_capabilities[0] if required_capabilities else None
        )
        
        controls = []
        fallback_triggers = []
        
        if failures:
            controls.append("failure_history_monitor")
            fallback_triggers.append("historical_failure_pattern_detected")
        
        if candidate.risk_tier.value == "critical":
            controls.append("enhanced_verification")
            fallback_triggers.append("critical_risk_escalation")
        
        return {
            'total_score': total_score,
            'capability_match': capability_match,
            'confidence': confidence,
            'confidence_state': 'high' if confidence > 0.8 else 'medium' if confidence > 0.5 else 'low',
            'satisfied_constraints': constraint_results['satisfied'],
            'violated_constraints': constraint_results['violated'],
            'controls': controls,
            'fallback_triggers': fallback_triggers,
            'uncertainty_sources': uncertainty,
            'estimated_cost': candidate.cost_profile.estimate_total_cost({
                'tokens_k': 10, 'compute_hours': 0.1, 'api_calls': 1
            }),
            'estimated_latency': candidate.latency_profile.p50_ms
        }
    
    def _score_risk_tier(self, candidate_tier: str, required_tier: str) -> float:
        """Score risk tier match"""
        tier_order = ['low', 'medium', 'high', 'critical']
        
        candidate_idx = tier_order.index(candidate_tier) if candidate_tier in tier_order else 1
        required_idx = tier_order.index(required_tier) if required_tier in tier_order else 1
        
        # Higher tier than required is acceptable (safer)
        # Lower tier than required is problematic
        if candidate_idx >= required_idx:
            return 1.0
        else:
            # Penalty for insufficient tier
            return max(0, 1.0 - (required_idx - candidate_idx) * 0.3)
    
    def _check_constraints(self, candidate: ControlledObject,
                          constraints: RoutingConstraints) -> Dict[str, Any]:
        """Check constraint satisfaction"""
        satisfied = []
        violated = []
        
        # Latency
        if candidate.latency_profile.p95_ms <= constraints.max_latency_ms:
            satisfied.append("latency_budget")
        else:
            violated.append("latency_budget")
        
        # Cost
        est_cost = candidate.cost_profile.estimate_total_cost({
            'tokens_k': 10, 'compute_hours': 0.1, 'api_calls': 1
        })
        if est_cost <= constraints.max_cost:
            satisfied.append("cost_budget")
        else:
            violated.append("cost_budget")
        
        # Risk tier
        if candidate.risk_tier.value in constraints.allowed_risk_tiers:
            satisfied.append("risk_tier")
        else:
            violated.append("risk_tier")
        
        # Forbidden objects
        if candidate.object_id not in constraints.forbidden_objects:
            satisfied.append("not_forbidden")
        else:
            violated.append("forbidden_object")
        
        satisfaction_rate = len(satisfied) / (len(satisfied) + len(violated)) if (satisfied or violated) else 1.0
        
        return {
            'satisfied': satisfied,
            'violated': violated,
            'satisfaction_rate': satisfaction_rate
        }
    
    def _calculate_confidence(self, capability_match: float,
                             historical_count: int,
                             constraint_results: Dict[str, Any]) -> float:
        """Calculate overall confidence in selection"""
        base_confidence = capability_match
        
        # Boost confidence with historical data
        if historical_count > 100:
            base_confidence += 0.2
        elif historical_count > 20:
            base_confidence += 0.1
        
        # Penalize constraint violations
        base_confidence -= (1 - constraint_results['satisfaction_rate']) * 0.3
        
        return max(0, min(1, base_confidence))
    
    async def _identify_fallback(self, primary: ControlledObject,
                               alternatives: List[Tuple[ControlledObject, Dict]]) -> Optional[str]:
        """Identify fallback object"""
        # Prefer first alternative with lower risk
        for alt, score in alternatives:
            if alt.risk_tier.value == 'low' or alt.risk_tier.value == primary.risk_tier.value:
                return alt.object_id
        
        # Or just take first alternative
        if alternatives:
            return alternatives[0][0].object_id
        
        return None
    
    def _create_fallback_decision(self, task_id: str, required_capabilities: List[str],
                                  risk_tier: str, regime: str,
                                  reason: str) -> RoutingDecision:
        """Create a fallback decision when no good option found"""
        return RoutingDecision(
            decision_id=f"route_fallback_{hashlib.md5(f'{task_id}_{datetime.utcnow().timestamp()}'.encode()).hexdigest()[:16]}",
            timestamp=datetime.utcnow().isoformat(),
            task_id=task_id,
            required_capabilities=required_capabilities,
            risk_tier=risk_tier,
            regime=regime,
            selected_object_id="HUMAN_ESCALATION",
            selection_confidence=0.0,
            capability_match_score=0.0,
            constraints_satisfied=[],
            constraints_violated=["no_valid_candidate"],
            controls=["human_review_required"],
            rejected_alternatives=[],
            fallback_object_id=None,
            fallback_trigger_conditions=[],
            confidence_state="uncertain",
            uncertainty_sources=[reason],
            estimated_cost=0,
            estimated_latency_ms=0
        )
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics"""
        if not self.decisions:
            return {"total_decisions": 0}
        
        recent = [d for d in self.decisions[-100:]]
        
        return {
            "total_decisions": len(self.decisions),
            "avg_confidence": np.mean([d.selection_confidence for d in recent]),
            "fallback_rate": sum(1 for d in recent if d.selected_object_id == "HUMAN_ESCALATION") / len(recent),
            "by_confidence_state": {
                state: sum(1 for d in recent if d.confidence_state == state)
                for state in ['high', 'medium', 'low', 'uncertain']
            }
        }

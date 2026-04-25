"""
Fallback Hierarchy
==================

Per Section 11: Every production route must define:
- primary route
- secondary route
- degraded safe route
- symbolic/rule fallback where possible
- human escalation path where required

Failure triggers:
- timeout
- malformed output
- schema violation
- verifier failure
- cost breach
- confidence collapse
- forbidden content generation
- contradiction with protected facts or rules

No route may exist without a fallback strategy.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of failures that trigger fallback"""
    TIMEOUT = "timeout"
    MALFORMED_OUTPUT = "malformed_output"
    SCHEMA_VIOLATION = "schema_violation"
    VERIFIER_FAILURE = "verifier_failure"
    COST_BREACH = "cost_breach"
    CONFIDENCE_COLLAPSE = "confidence_collapse"
    FORBIDDEN_CONTENT = "forbidden_content"
    CONTRADICTION = "contradiction"
    UNEXPECTED_ERROR = "unexpected_error"
    LATENCY_SPIKE = "latency_spike"
    RATE_LIMIT = "rate_limit"


class FallbackLevel(Enum):
    """Levels of fallback"""
    PRIMARY = "primary"          # Normal operation
    SECONDARY = "secondary"    # Alternative object/model
    DEGRADED = "degraded"      # Reduced functionality
    SYMBOLIC = "symbolic"      # Rule-based fallback
    HUMAN = "human"           # Human escalation


@dataclass
class FallbackRoute:
    """
    Definition of a fallback route.
    """
    level: FallbackLevel
    object_id: str  # Can be "HUMAN_ESCALATION" for human level
    
    # Activation conditions
    failure_triggers: List[FailureType]
    confidence_threshold: Optional[float]  # Activate if confidence below this
    
    # Route characteristics
    expected_latency_ms: float
    expected_quality_degradation: float  # 0-1, expected quality loss
    
    # Execution
    execution_config: Dict[str, Any]
    
    def should_activate(self, failure: FailureType,
                       confidence: float,
                       context: Dict[str, Any]) -> bool:
        """Determine if this fallback should activate"""
        if failure in self.failure_triggers:
            return True
        
        if self.confidence_threshold is not None:
            if confidence < self.confidence_threshold:
                return True
        
        return False


@dataclass
class FallbackChain:
    """
    Complete fallback chain for a capability.
    
    Must define all levels per Section 11.
    """
    capability_id: str
    
    primary: FallbackRoute
    secondary: FallbackRoute
    degraded: FallbackRoute
    symbolic: Optional[FallbackRoute]  # Optional but preferred
    human: FallbackRoute
    
    # Configuration
    auto_escalation: bool = True  # Auto-escalate on failure
    max_fallback_depth: int = 3
    
    # State
    current_level: FallbackLevel = FallbackLevel.PRIMARY
    activation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_active_route(self) -> FallbackRoute:
        """Get currently active route"""
        route_map = {
            FallbackLevel.PRIMARY: self.primary,
            FallbackLevel.SECONDARY: self.secondary,
            FallbackLevel.DEGRADED: self.degraded,
            FallbackLevel.SYMBOLIC: self.symbolic or self.degraded,
            FallbackLevel.HUMAN: self.human
        }
        return route_map.get(self.current_level, self.human)
    
    def escalate(self, failure: FailureType, context: Dict[str, Any]) -> FallbackRoute:
        """
        Escalate to next fallback level.
        
        Returns new active route.
        """
        old_level = self.current_level
        
        # Define escalation path
        escalation_path = {
            FallbackLevel.PRIMARY: FallbackLevel.SECONDARY,
            FallbackLevel.SECONDARY: FallbackLevel.DEGRADED,
            FallbackLevel.DEGRADED: FallbackLevel.SYMBOLIC if self.symbolic else FallbackLevel.HUMAN,
            FallbackLevel.SYMBOLIC: FallbackLevel.HUMAN,
            FallbackLevel.HUMAN: FallbackLevel.HUMAN  # Terminal
        }
        
        self.current_level = escalation_path.get(self.current_level, FallbackLevel.HUMAN)
        
        # Record activation
        self.activation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "from_level": old_level.value,
            "to_level": self.current_level.value,
            "trigger": failure.value,
            "context": context
        })
        
        logger.warning(f"Fallback escalation for {self.capability_id}: "
                      f"{old_level.value} -> {self.current_level.value}")
        
        return self.get_active_route()
    
    def reset(self):
        """Reset to primary after issue resolved"""
        if self.current_level != FallbackLevel.PRIMARY:
            logger.info(f"Fallback reset for {self.capability_id}: "
                       f"{self.current_level.value} -> primary")
            self.current_level = FallbackLevel.PRIMARY
    
    def validate_chain(self) -> List[str]:
        """Validate fallback chain completeness"""
        issues = []
        
        if not self.primary:
            issues.append("Missing primary route")
        if not self.secondary:
            issues.append("Missing secondary route")
        if not self.degraded:
            issues.append("Missing degraded route")
        if not self.human:
            issues.append("Missing human escalation route")
        
        # Check for gaps in escalation
        required_order = [self.primary, self.secondary, self.degraded, self.human]
        for i, route in enumerate(required_order):
            if not route:
                issues.append(f"Missing route at position {i}")
        
        return issues


class FallbackHierarchyManager:
    """
    Manages fallback hierarchies for all capabilities.
    
    Ensures every production route has defined fallbacks.
    """
    
    def __init__(self):
        self.chains: Dict[str, FallbackChain] = {}
        self.activation_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        logger.info("FallbackHierarchyManager initialized")
    
    def register_fallback_chain(self, chain: FallbackChain) -> str:
        """
        Register a fallback chain.
        
        Validates that all required levels are present.
        """
        # Validate
        issues = chain.validate_chain()
        if issues:
            raise ValueError(f"Invalid fallback chain for {chain.capability_id}: {issues}")
        
        self.chains[chain.capability_id] = chain
        logger.info(f"Registered fallback chain for {chain.capability_id}")
        return chain.capability_id
    
    def get_fallback_chain(self, capability_id: str) -> Optional[FallbackChain]:
        """Get fallback chain for a capability"""
        return self.chains.get(capability_id)
    
    def handle_failure(self, capability_id: str,
                      failure: FailureType,
                      current_object_id: str,
                      confidence: float,
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a failure and determine fallback action.
        
        Returns:
        - new_object_id: Object to use for fallback
        - level: Fallback level activated
        - action: What to do (escalate, retry, abort)
        """
        chain = self.chains.get(capability_id)
        
        if not chain:
            logger.error(f"No fallback chain for {capability_id}")
            return {
                "new_object_id": "HUMAN_ESCALATION",
                "level": FallbackLevel.HUMAN.value,
                "action": "immediate_escalation",
                "reason": "no_fallback_chain_defined"
            }
        
        # Get current route
        current_route = chain.get_active_route()
        
        # Check if current route can handle this failure
        if current_route.should_activate(failure, confidence, context):
            # Already at appropriate level, try retry
            return {
                "new_object_id": current_route.object_id,
                "level": chain.current_level.value,
                "action": "retry",
                "reason": f"retry_at_{chain.current_level.value}"
            }
        
        # Need to escalate
        new_route = chain.escalate(failure, context)
        
        # Update stats
        self.activation_stats[capability_id][failure.value] += 1
        
        return {
            "new_object_id": new_route.object_id,
            "level": chain.current_level.value,
            "action": "escalate",
            "reason": f"escalated_from_{current_route.level.value}_due_to_{failure.value}",
            "quality_degradation": new_route.expected_quality_degradation
        }
    
    def create_standard_chain(self,
                             capability_id: str,
                             primary_object_id: str,
                             secondary_object_id: str,
                             degraded_object_id: str,
                             human_escalation_path: str = "HUMAN_ESCALATION",
                             symbolic_fallback: Optional[str] = None) -> FallbackChain:
        """
        Create a standard fallback chain with common failure triggers.
        """
        primary = FallbackRoute(
            level=FallbackLevel.PRIMARY,
            object_id=primary_object_id,
            failure_triggers=[],  # Primary has no failure triggers - it's the starting point
            confidence_threshold=None,
            expected_latency_ms=1000,
            expected_quality_degradation=0.0,
            execution_config={"timeout_ms": 5000, "retry_count": 1}
        )
        
        secondary = FallbackRoute(
            level=FallbackLevel.SECONDARY,
            object_id=secondary_object_id,
            failure_triggers=[
                FailureType.TIMEOUT,
                FailureType.UNEXPECTED_ERROR,
                FailureType.RATE_LIMIT
            ],
            confidence_threshold=0.3,
            expected_latency_ms=2000,
            expected_quality_degradation=0.1,
            execution_config={"timeout_ms": 10000, "retry_count": 2}
        )
        
        degraded = FallbackRoute(
            level=FallbackLevel.DEGRADED,
            object_id=degraded_object_id,
            failure_triggers=[
                FailureType.VERIFIER_FAILURE,
                FailureType.CONFIDENCE_COLLAPSE,
                FailureType.LATENCY_SPIKE
            ],
            confidence_threshold=0.2,
            expected_latency_ms=1500,
            expected_quality_degradation=0.3,
            execution_config={"timeout_ms": 8000, "simplified_mode": True}
        )
        
        symbolic = None
        if symbolic_fallback:
            symbolic = FallbackRoute(
                level=FallbackLevel.SYMBOLIC,
                object_id=symbolic_fallback,
                failure_triggers=[
                    FailureType.FORBIDDEN_CONTENT,
                    FailureType.CONTRADICTION
                ],
                confidence_threshold=0.1,
                expected_latency_ms=500,
                expected_quality_degradation=0.5,
                execution_config={"rule_based": True}
            )
        
        human = FallbackRoute(
            level=FallbackLevel.HUMAN,
            object_id=human_escalation_path,
            failure_triggers=[
                FailureType.COST_BREACH,
                FailureType.MALFORMED_OUTPUT,
                FailureType.SCHEMA_VIOLATION
            ],
            confidence_threshold=0.0,
            expected_latency_ms=3600000,  # 1 hour for human
            expected_quality_degradation=0.0,  # Human is ground truth
            execution_config={"escalation_priority": "high"}
        )
        
        return FallbackChain(
            capability_id=capability_id,
            primary=primary,
            secondary=secondary,
            degraded=degraded,
            symbolic=symbolic,
            human=human
        )
    
    def get_chain_health(self, capability_id: str) -> Dict[str, Any]:
        """Get health status of a fallback chain"""
        chain = self.chains.get(capability_id)
        
        if not chain:
            return {"status": "missing", "issues": ["No fallback chain defined"]}
        
        issues = chain.validate_chain()
        
        # Check activation history
        recent_activations = [
            a for a in chain.activation_history
            if (datetime.utcnow() - datetime.fromisoformat(a["timestamp"])).days < 7
        ]
        
        frequent_escalation = len(recent_activations) > 10
        
        if issues:
            status = "invalid"
        elif frequent_escalation:
            status = "unstable"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "current_level": chain.current_level.value,
            "issues": issues,
            "recent_activations": len(recent_activations),
            "total_activations": len(chain.activation_history),
            "frequent_escalation": frequent_escalation
        }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global fallback statistics"""
        return {
            "total_chains": len(self.chains),
            "activation_stats": dict(self.activation_stats),
            "chains_by_health": {
                "healthy": sum(1 for c in self.chains.values() if self.get_chain_health(c.capability_id)["status"] == "healthy"),
                "unstable": sum(1 for c in self.chains.values() if self.get_chain_health(c.capability_id)["status"] == "unstable"),
                "invalid": sum(1 for c in self.chains.values() if self.get_chain_health(c.capability_id)["status"] == "invalid")
            }
        }


from collections import defaultdict

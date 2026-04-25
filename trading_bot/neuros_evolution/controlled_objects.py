"""
Controlled Objects System
=========================

Every controlled object must have:
- unique ID
- version
- owner
- task scope
- capability mapping
- risk tier
- regime applicability
- cost profile
- latency profile
- known failure modes
- forbidden uses
- promotion status
- rollback target
- provenance trail

Section 4 of AlphaAlgo Meta-Intelligence Layer Specification.
If any of these are missing, the object is ineligible for promotion.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime
from pathlib import Path
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


class RiskTier(Enum):
    """Risk tiers for controlled objects"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PromotionStatus(Enum):
    """Promotion status for controlled objects"""
    OBSERVED = "observed"           # Stage 1: Just observed
    PROFILED = "profiled"           # Stage 2: Capability fingerprint built
    BENCHMARKED = "benchmarked"     # Stage 3: Evaluated on capability-specific tests
    EXTRACTED = "extracted"         # Stage 4: Mechanism extracted
    CONTROLLED = "controlled"     # Stage 5: Weakness controls created
    DISTILLED = "distilled"         # Stage 6: Converted to internal asset
    VALIDATING = "validating"       # Stage 7: In sandbox validation
    VALIDATED = "validated"         # Stage 7: Passed validation gates
    DEPLOYED = "deployed"           # Stage 8: In production (canary or limited)
    MONITORING = "monitoring"       # Stage 9: Post-deployment monitoring
    ATTRIBUTED = "attributed"       # Stage 10: Causal contribution estimated
    PRUNED = "pruned"               # Stage 11: Archived or deleted
    REJECTED = "rejected"           # Failed at some stage


class ControlledObjectType(Enum):
    """Types of controlled objects"""
    FOUNDATION_MODEL = "foundation_model"
    SPECIALIST_MODEL = "specialist_model"
    LOCAL_MODEL = "local_model"
    PROMPT = "prompt"
    REASONING_TEMPLATE = "reasoning_template"
    RETRIEVAL_PIPELINE = "retrieval_pipeline"
    RERANKER = "reranker"
    VERIFIER = "verifier"
    SYMBOLIC_RULE = "symbolic_rule"
    ROUTING_POLICY = "routing_policy"
    MEMORY_POLICY = "memory_policy"
    DISTILLATION_ARTIFACT = "distillation_artifact"
    FALLBACK_CHAIN = "fallback_chain"
    OUTPUT_SCHEMA = "output_schema"
    TOOL_USE_POLICY = "tool_use_policy"


@dataclass
class CostProfile:
    """Cost profile for a controlled object"""
    token_cost_per_1k: float = 0.0
    compute_cost_per_hour: float = 0.0
    api_call_cost: float = 0.0
    storage_cost_gb_month: float = 0.0
    
    def estimate_total_cost(self, usage: Dict[str, float]) -> float:
        """Estimate total cost given usage metrics"""
        return (
            self.token_cost_per_1k * (usage.get("tokens_k", 0) / 1000) +
            self.compute_cost_per_hour * usage.get("compute_hours", 0) +
            self.api_call_cost * usage.get("api_calls", 0) +
            self.storage_cost_gb_month * usage.get("storage_gb", 0)
        )


@dataclass
class LatencyProfile:
    """Latency profile for a controlled object"""
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    max_ms: float = 0.0
    cold_start_ms: float = 0.0


@dataclass
class FailureMode:
    """Known failure mode"""
    failure_id: str
    description: str
    detection_pattern: str
    severity: str  # low, medium, high, critical
    frequency: str  # rare, occasional, frequent
    mitigation: str
    last_observed: Optional[str] = None


@dataclass
class ProvenanceEntry:
    """Single entry in provenance trail"""
    timestamp: str
    stage: str
    action: str
    actor: str
    evidence_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackTarget:
    """Rollback target configuration"""
    target_object_id: str
    target_version: str
    rollback_conditions: List[str]
    rollback_procedure: str
    estimated_downtime_ms: float
    data_preservation_plan: str


@dataclass
class ControlledObject:
    """
    Controlled object per Section 4.
    
    Every field is mandatory for promotion eligibility.
    """
    # Core identification
    object_id: str
    version: str
    owner: str
    object_type: ControlledObjectType
    
    # Scope and mapping
    task_scope: List[str]
    capability_mapping: List[str]  # CAP-* IDs
    
    # Risk and regime
    risk_tier: RiskTier
    regime_applicability: List[str]  # e.g., ["high_volatility", "trending", "ranging"]
    
    # Performance profiles
    cost_profile: CostProfile
    latency_profile: LatencyProfile
    
    # Safety
    known_failure_modes: List[FailureMode]
    forbidden_uses: List[str]
    
    # Lifecycle
    promotion_status: PromotionStatus
    rollback_target: Optional[RollbackTarget]
    provenance_trail: List[ProvenanceEntry] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_eligible_for_promotion(self) -> bool:
        """Check if object has all required fields for promotion"""
        required_fields = [
            self.object_id,
            self.version,
            self.owner,
            self.task_scope,
            self.capability_mapping,
            self.risk_tier,
            self.regime_applicability,
            self.forbidden_uses,
        ]
        
        # Check all required fields present
        if not all(required_fields):
            return False
        
        # Check rollback target defined for promoted objects
        if self.promotion_status in [
            PromotionStatus.DEPLOYED, 
            PromotionStatus.MONITORING,
            PromotionStatus.ATTRIBUTED
        ]:
            if not self.rollback_target:
                return False
        
        # Check provenance trail exists
        if not self.provenance_trail:
            return False
        
        return True
    
    def add_provenance_entry(self, stage: str, action: str, actor: str,
                            evidence: Dict[str, Any]):
        """Add entry to provenance trail"""
        evidence_str = json.dumps(evidence, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()[:16]
        
        entry = ProvenanceEntry(
            timestamp=datetime.utcnow().isoformat(),
            stage=stage,
            action=action,
            actor=actor,
            evidence_hash=evidence_hash,
            metadata=evidence
        )
        self.provenance_trail.append(entry)
        self.last_updated = datetime.utcnow().isoformat()
    
    def get_latest_failure_modes(self, severity_filter: Optional[str] = None) -> List[FailureMode]:
        """Get failure modes, optionally filtered by severity"""
        if severity_filter:
            return [f for f in self.known_failure_modes if f.severity == severity_filter]
        return self.known_failure_modes
    
    def supports_capability(self, capability_id: str) -> bool:
        """Check if object supports a specific capability"""
        return capability_id in self.capability_mapping
    
    def is_applicable_to_regime(self, regime: str) -> bool:
        """Check if object applicable to a market regime"""
        return regime in self.regime_applicability or "universal" in self.regime_applicability
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "object_id": self.object_id,
            "version": self.version,
            "owner": self.owner,
            "object_type": self.object_type.value,
            "task_scope": self.task_scope,
            "capability_mapping": self.capability_mapping,
            "risk_tier": self.risk_tier.value,
            "regime_applicability": self.regime_applicability,
            "cost_profile": {
                "token_cost_per_1k": self.cost_profile.token_cost_per_1k,
                "compute_cost_per_hour": self.cost_profile.compute_cost_per_hour,
                "api_call_cost": self.cost_profile.api_call_cost,
                "storage_cost_gb_month": self.cost_profile.storage_cost_gb_month
            },
            "latency_profile": {
                "p50_ms": self.latency_profile.p50_ms,
                "p95_ms": self.latency_profile.p95_ms,
                "p99_ms": self.latency_profile.p99_ms,
                "max_ms": self.latency_profile.max_ms,
                "cold_start_ms": self.latency_profile.cold_start_ms
            },
            "known_failure_modes": [
                {
                    "failure_id": f.failure_id,
                    "description": f.description,
                    "detection_pattern": f.detection_pattern,
                    "severity": f.severity,
                    "frequency": f.frequency,
                    "mitigation": f.mitigation
                } for f in self.known_failure_modes
            ],
            "forbidden_uses": self.forbidden_uses,
            "promotion_status": self.promotion_status.value,
            "rollback_target": {
                "target_object_id": self.rollback_target.target_object_id,
                "target_version": self.rollback_target.target_version,
                "rollback_conditions": self.rollback_target.rollback_conditions,
                "rollback_procedure": self.rollback_target.rollback_procedure,
                "estimated_downtime_ms": self.rollback_target.estimated_downtime_ms,
                "data_preservation_plan": self.rollback_target.data_preservation_plan
            } if self.rollback_target else None,
            "provenance_trail": [
                {
                    "timestamp": p.timestamp,
                    "stage": p.stage,
                    "action": p.action,
                    "actor": p.actor,
                    "evidence_hash": p.evidence_hash
                } for p in self.provenance_trail
            ],
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }


class ControlledObjectRegistry:
    """Registry for all controlled objects"""
    
    def __init__(self, storage_path: str = "./controlled_objects.json"):
        self.storage_path = Path(storage_path)
        self.objects: Dict[str, ControlledObject] = {}
        self._load()
        logger.info(f"ControlledObjectRegistry initialized with {len(self.objects)} objects")
    
    def _load(self):
        """Load objects from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    # Reconstruct objects from dict
                    for obj_id, obj_dict in data.items():
                        self.objects[obj_id] = self._dict_to_object(obj_dict)
            except Exception as e:
                logger.error(f"Error loading controlled objects: {e}")
    
    def _save(self):
        """Save objects to storage"""
        data = {obj_id: obj.to_dict() for obj_id, obj in self.objects.items()}
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _dict_to_object(self, data: Dict[str, Any]) -> ControlledObject:
        """Convert dictionary to ControlledObject"""
        # Parse cost profile
        cost_data = data.get("cost_profile", {})
        cost_profile = CostProfile(
            token_cost_per_1k=cost_data.get("token_cost_per_1k", 0),
            compute_cost_per_hour=cost_data.get("compute_cost_per_hour", 0),
            api_call_cost=cost_data.get("api_call_cost", 0),
            storage_cost_gb_month=cost_data.get("storage_cost_gb_month", 0)
        )
        
        # Parse latency profile
        latency_data = data.get("latency_profile", {})
        latency_profile = LatencyProfile(
            p50_ms=latency_data.get("p50_ms", 0),
            p95_ms=latency_data.get("p95_ms", 0),
            p99_ms=latency_data.get("p99_ms", 0),
            max_ms=latency_data.get("max_ms", 0),
            cold_start_ms=latency_data.get("cold_start_ms", 0)
        )
        
        # Parse failure modes
        failure_modes = [
            FailureMode(
                failure_id=f["failure_id"],
                description=f["description"],
                detection_pattern=f["detection_pattern"],
                severity=f["severity"],
                frequency=f["frequency"],
                mitigation=f["mitigation"],
                last_observed=f.get("last_observed")
            )
            for f in data.get("known_failure_modes", [])
        ]
        
        # Parse rollback target
        rollback_data = data.get("rollback_target")
        rollback_target = None
        if rollback_data:
            rollback_target = RollbackTarget(
                target_object_id=rollback_data["target_object_id"],
                target_version=rollback_data["target_version"],
                rollback_conditions=rollback_data["rollback_conditions"],
                rollback_procedure=rollback_data["rollback_procedure"],
                estimated_downtime_ms=rollback_data["estimated_downtime_ms"],
                data_preservation_plan=rollback_data["data_preservation_plan"]
            )
        
        # Parse provenance
        provenance = [
            ProvenanceEntry(
                timestamp=p["timestamp"],
                stage=p["stage"],
                action=p["action"],
                actor=p["actor"],
                evidence_hash=p["evidence_hash"],
                metadata=p.get("metadata", {})
            )
            for p in data.get("provenance_trail", [])
        ]
        
        return ControlledObject(
            object_id=data["object_id"],
            version=data["version"],
            owner=data["owner"],
            object_type=ControlledObjectType(data["object_type"]),
            task_scope=data["task_scope"],
            capability_mapping=data["capability_mapping"],
            risk_tier=RiskTier(data["risk_tier"]),
            regime_applicability=data["regime_applicability"],
            cost_profile=cost_profile,
            latency_profile=latency_profile,
            known_failure_modes=failure_modes,
            forbidden_uses=data.get("forbidden_uses", []),
            promotion_status=PromotionStatus(data["promotion_status"]),
            rollback_target=rollback_target,
            provenance_trail=provenance,
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            last_updated=data.get("last_updated", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {})
        )
    
    def register(self, obj: ControlledObject) -> str:
        """Register a controlled object"""
        if not obj.is_eligible_for_promotion():
            logger.warning(f"Object {obj.object_id} missing required fields for promotion")
        
        self.objects[obj.object_id] = obj
        self._save()
        logger.info(f"Registered controlled object {obj.object_id} v{obj.version}")
        return obj.object_id
    
    def get(self, object_id: str) -> Optional[ControlledObject]:
        """Get controlled object by ID"""
        return self.objects.get(object_id)
    
    def get_by_capability(self, capability_id: str, 
                         status: Optional[PromotionStatus] = None) -> List[ControlledObject]:
        """Get objects supporting a capability"""
        objects = [obj for obj in self.objects.values() 
                  if capability_id in obj.capability_mapping]
        if status:
            objects = [obj for obj in objects if obj.promotion_status == status]
        return objects
    
    def get_by_risk_tier(self, risk_tier: RiskTier) -> List[ControlledObject]:
        """Get objects by risk tier"""
        return [obj for obj in self.objects.values() if obj.risk_tier == risk_tier]
    
    def get_eligible_for_promotion(self) -> List[ControlledObject]:
        """Get all objects eligible for promotion"""
        return [obj for obj in self.objects.values() if obj.is_eligible_for_promotion()]
    
    def update_status(self, object_id: str, new_status: PromotionStatus,
                     actor: str, evidence: Dict[str, Any]):
        """Update promotion status with provenance"""
        obj = self.objects.get(object_id)
        if not obj:
            raise ValueError(f"Object {object_id} not found")
        
        old_status = obj.promotion_status
        obj.promotion_status = new_status
        obj.add_provenance_entry(
            stage=new_status.value,
            action=f"promoted_from_{old_status.value}",
            actor=actor,
            evidence=evidence
        )
        self._save()
        logger.info(f"Updated {object_id} from {old_status.value} to {new_status.value}")
    
    def add_failure_mode(self, object_id: str, failure: FailureMode, actor: str):
        """Add a failure mode to an object"""
        obj = self.objects.get(object_id)
        if not obj:
            raise ValueError(f"Object {object_id} not found")
        
        obj.known_failure_modes.append(failure)
        obj.add_provenance_entry(
            stage=obj.promotion_status.value,
            action="failure_mode_added",
            actor=actor,
            evidence={"failure_id": failure.failure_id, "severity": failure.severity}
        )
        self._save()
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """Get summary of registry"""
        by_status = {}
        by_risk = {}
        by_type = {}
        
        for obj in self.objects.values():
            status = obj.promotion_status.value
            risk = obj.risk_tier.value
            obj_type = obj.object_type.value
            
            by_status[status] = by_status.get(status, 0) + 1
            by_risk[risk] = by_risk.get(risk, 0) + 1
            by_type[obj_type] = by_type.get(obj_type, 0) + 1
        
        return {
            "total_objects": len(self.objects),
            "by_promotion_status": by_status,
            "by_risk_tier": by_risk,
            "by_object_type": by_type,
            "eligible_for_promotion": len(self.get_eligible_for_promotion())
        }


# Factory functions
def create_controlled_object(
    object_id: str,
    version: str,
    owner: str,
    object_type: ControlledObjectType,
    task_scope: List[str],
    capability_mapping: List[str],
    risk_tier: RiskTier,
    regime_applicability: List[str],
    cost_profile: CostProfile,
    latency_profile: LatencyProfile,
    known_failure_modes: List[FailureMode],
    forbidden_uses: List[str],
    rollback_target: Optional[RollbackTarget] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ControlledObject:
    """Factory function to create a controlled object"""
    return ControlledObject(
        object_id=object_id,
        version=version,
        owner=owner,
        object_type=object_type,
        task_scope=task_scope,
        capability_mapping=capability_mapping,
        risk_tier=risk_tier,
        regime_applicability=regime_applicability,
        cost_profile=cost_profile,
        latency_profile=latency_profile,
        known_failure_modes=known_failure_modes,
        forbidden_uses=forbidden_uses,
        promotion_status=PromotionStatus.OBSERVED,
        rollback_target=rollback_target,
        provenance_trail=[],
        metadata=metadata or {}
    )


def create_registry(storage_path: str = "./controlled_objects.json") -> ControlledObjectRegistry:
    """Factory function to create a controlled object registry"""
    return ControlledObjectRegistry(storage_path)

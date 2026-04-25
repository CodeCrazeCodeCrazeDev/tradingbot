"""
Memory Systems
==============

Per Section 9: All memory layers with provenance and timestamp requirements.

- Behavior Library: Validated reusable behaviors and policies
- Failure Library: Failure patterns, forbidden-use zones, historical regressions
- Capability Registry: Capability definitions, thresholds, budgets, mappings
- Candidate Archive: Rejected candidates and reasons for rejection
- Route Performance Memory: Historical route performance by capability, regime, risk tier
- Distillation Registry: Teacher-student relationships, distillation evidence, drift tracking

No memory entry may exist without provenance and timestamp.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib
import logging
import sqlite3
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Provenance:
    """Provenance information for all memory entries"""
    created_at: str
    created_by: str
    source_object_id: Optional[str]
    evidence_hash: str
    validation_status: str
    last_verified: Optional[str] = None


def create_provenance(created_by: str, source_object_id: Optional[str] = None,
                     evidence: Optional[Dict[str, Any]] = None) -> Provenance:
    """Create provenance record with automatic timestamp and hash"""
    evidence_dict = evidence or {}
    evidence_str = json.dumps(evidence_dict, sort_keys=True)
    evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()[:16]
    
    return Provenance(
        created_at=datetime.utcnow().isoformat(),
        created_by=created_by,
        source_object_id=source_object_id,
        evidence_hash=evidence_hash,
        validation_status="pending"
    )


# ============================================================================
# Behavior Library
# ============================================================================

@dataclass
class BehaviorEntry:
    """
    Behavior Library Entry
    
    Stores validated reusable behaviors and policies.
    Every entry must have behavioral mechanism, not just output examples.
    """
    behavior_id: str
    name: str
    behavior_type: str  # 'prompt_policy', 'decomposition', 'tool_use', 'routing', etc.
    
    # Core: The behavioral mechanism (not just example)
    mechanism_description: str
    implementation_pattern: Dict[str, Any]
    applicability_conditions: List[str]
    
    # Capability mapping
    target_capabilities: List[str]  # CAP-* IDs
    performance_delta: float  # Improvement over baseline
    cost_delta: float  # Cost change
    
    # Safety
    known_failure_conditions: List[str]
    expiry_schedule: str  # When to revalidate
    
    # Provenance (required)
    provenance: Provenance
    
    # Metadata
    usage_count: int = 0
    last_used: Optional[str] = None
    status: str = "active"  # active, deprecated, under_review
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "behavior_id": self.behavior_id,
            "name": self.name,
            "behavior_type": self.behavior_type,
            "mechanism_description": self.mechanism_description,
            "implementation_pattern": self.implementation_pattern,
            "applicability_conditions": self.applicability_conditions,
            "target_capabilities": self.target_capabilities,
            "performance_delta": self.performance_delta,
            "cost_delta": self.cost_delta,
            "known_failure_conditions": self.known_failure_conditions,
            "expiry_schedule": self.expiry_schedule,
            "provenance": {
                "created_at": self.provenance.created_at,
                "created_by": self.provenance.created_by,
                "source_object_id": self.provenance.source_object_id,
                "evidence_hash": self.provenance.evidence_hash,
                "validation_status": self.provenance.validation_status
            },
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "status": self.status
        }


class BehaviorLibrary:
    """Behavior Library per Section 9"""
    
    def __init__(self, storage_path: str = "./behavior_library.json"):
        self.storage_path = Path(storage_path)
        self.behaviors: Dict[str, BehaviorEntry] = {}
        self._load()
        logger.info(f"BehaviorLibrary initialized with {len(self.behaviors)} behaviors")
    
    def _load(self):
        """Load from storage"""
        if self.storage_path.exists():
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for behavior_id, behavior_dict in data.items():
                    self.behaviors[behavior_id] = self._dict_to_behavior(behavior_dict)
    
    def _save(self):
        """Save to storage"""
        data = {k: v.to_dict() for k, v in self.behaviors.items()}
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _dict_to_behavior(self, data: Dict[str, Any]) -> BehaviorEntry:
        prov_data = data.get("provenance", {})
        provenance = Provenance(
            created_at=prov_data.get("created_at", datetime.utcnow().isoformat()),
            created_by=prov_data.get("created_by", "unknown"),
            source_object_id=prov_data.get("source_object_id"),
            evidence_hash=prov_data.get("evidence_hash", "unknown"),
            validation_status=prov_data.get("validation_status", "pending")
        )
        
        return BehaviorEntry(
            behavior_id=data["behavior_id"],
            name=data["name"],
            behavior_type=data["behavior_type"],
            mechanism_description=data["mechanism_description"],
            implementation_pattern=data.get("implementation_pattern", {}),
            applicability_conditions=data.get("applicability_conditions", []),
            target_capabilities=data.get("target_capabilities", []),
            performance_delta=data.get("performance_delta", 0),
            cost_delta=data.get("cost_delta", 0),
            known_failure_conditions=data.get("known_failure_conditions", []),
            expiry_schedule=data.get("expiry_schedule", "quarterly"),
            provenance=provenance,
            usage_count=data.get("usage_count", 0),
            last_used=data.get("last_used"),
            status=data.get("status", "active")
        )
    
    def store_behavior(self, behavior: BehaviorEntry) -> str:
        """Store a validated behavior"""
        # Validate: Must have mechanism, not just example
        if not behavior.mechanism_description or len(behavior.mechanism_description) < 20:
            raise ValueError("Behavior must have substantial mechanism description, not just examples")
        
        self.behaviors[behavior.behavior_id] = behavior
        self._save()
        logger.info(f"Stored behavior {behavior.behavior_id} for {behavior.target_capabilities}")
        return behavior.behavior_id
    
    def find_behaviors_for_capability(self, capability_id: str,
                                     status: str = "active") -> List[BehaviorEntry]:
        """Find behaviors for a specific capability"""
        return [
            b for b in self.behaviors.values()
            if capability_id in b.target_capabilities and b.status == status
        ]
    
    def get_expired_behaviors(self) -> List[BehaviorEntry]:
        """Get behaviors past their revalidation date"""
        expired = []
        now = datetime.utcnow()
        
        for behavior in self.behaviors.values():
            created = datetime.fromisoformat(behavior.provenance.created_at)
            
            if behavior.expiry_schedule == "monthly":
                expiry = created + timedelta(days=30)
            elif behavior.expiry_schedule == "quarterly":
                expiry = created + timedelta(days=90)
            else:  # default
                expiry = created + timedelta(days=90)
            
            if now > expiry:
                expired.append(behavior)
        
        return expired
    
    def record_usage(self, behavior_id: str):
        """Record usage of a behavior"""
        if behavior_id in self.behaviors:
            self.behaviors[behavior_id].usage_count += 1
            self.behaviors[behavior_id].last_used = datetime.utcnow().isoformat()
            self._save()


# ============================================================================
# Failure Library
# ============================================================================

@dataclass
class FailurePattern:
    """
    Failure Library Entry
    
    Stores failure patterns, forbidden-use zones, and historical regressions.
    """
    pattern_id: str
    failure_type: str  # 'hallucination', 'calibration_error', 'timeout', 'schema_violation', etc.
    
    # Description
    description: str
    detection_signature: str  # Pattern to detect this failure
    severity: str  # 'low', 'medium', 'high', 'critical'
    
    # Context
    affected_capabilities: List[str]  # CAP-* IDs
    affected_objects: List[str]  # Object IDs
    
    # History
    first_observed: str
    last_observed: str
    occurrence_count: int
    
    # Learning
    root_cause_analysis: str
    mitigation_strategies: List[str]
    prevention_controls: List[str]
    
    # Regression tracking
    regression_history: List[Dict[str, Any]]  # When this failure recurred
    
    # Provenance (required)
    provenance: Provenance
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "failure_type": self.failure_type,
            "description": self.description,
            "detection_signature": self.detection_signature,
            "severity": self.severity,
            "affected_capabilities": self.affected_capabilities,
            "affected_objects": self.affected_objects,
            "first_observed": self.first_observed,
            "last_observed": self.last_observed,
            "occurrence_count": self.occurrence_count,
            "root_cause_analysis": self.root_cause_analysis,
            "mitigation_strategies": self.mitigation_strategies,
            "prevention_controls": self.prevention_controls,
            "regression_history": self.regression_history,
            "provenance": {
                "created_at": self.provenance.created_at,
                "created_by": self.provenance.created_by,
                "source_object_id": self.provenance.source_object_id,
                "evidence_hash": self.provenance.evidence_hash,
                "validation_status": self.provenance.validation_status
            }
        }


class FailureLibrary:
    """Failure Library per Section 9"""
    
    def __init__(self, storage_path: str = "./failure_library.json"):
        self.storage_path = Path(storage_path)
        self.failures: Dict[str, FailurePattern] = {}
        self._load()
        logger.info(f"FailureLibrary initialized with {len(self.failures)} patterns")
    
    def _load(self):
        """Load from storage"""
        if self.storage_path.exists():
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for pattern_id, pattern_dict in data.items():
                    self.failures[pattern_id] = self._dict_to_failure(pattern_dict)
    
    def _save(self):
        """Save to storage"""
        data = {k: v.to_dict() for k, v in self.failures.items()}
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _dict_to_failure(self, data: Dict[str, Any]) -> FailurePattern:
        prov_data = data.get("provenance", {})
        provenance = Provenance(
            created_at=prov_data.get("created_at", datetime.utcnow().isoformat()),
            created_by=prov_data.get("created_by", "unknown"),
            source_object_id=prov_data.get("source_object_id"),
            evidence_hash=prov_data.get("evidence_hash", "unknown"),
            validation_status=prov_data.get("validation_status", "pending")
        )
        
        return FailurePattern(
            pattern_id=data["pattern_id"],
            failure_type=data["failure_type"],
            description=data["description"],
            detection_signature=data["detection_signature"],
            severity=data.get("severity", "medium"),
            affected_capabilities=data.get("affected_capabilities", []),
            affected_objects=data.get("affected_objects", []),
            first_observed=data.get("first_observed", datetime.utcnow().isoformat()),
            last_observed=data.get("last_observed", datetime.utcnow().isoformat()),
            occurrence_count=data.get("occurrence_count", 1),
            root_cause_analysis=data.get("root_cause_analysis", ""),
            mitigation_strategies=data.get("mitigation_strategies", []),
            prevention_controls=data.get("prevention_controls", []),
            regression_history=data.get("regression_history", []),
            provenance=provenance
        )
    
    def record_failure(self, failure: FailurePattern) -> str:
        """Record a failure pattern"""
        # Check if similar pattern exists
        existing = self._find_similar_pattern(failure.detection_signature)
        
        if existing:
            # Update existing
            existing.last_observed = datetime.utcnow().isoformat()
            existing.occurrence_count += 1
            existing.affected_objects = list(set(existing.affected_objects + failure.affected_objects))
            
            # Add to regression history
            existing.regression_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "new_objects": failure.affected_objects
            })
            
            self._save()
            logger.info(f"Updated failure pattern {existing.pattern_id} (count={existing.occurrence_count})")
            return existing.pattern_id
        else:
            # Store new
            self.failures[failure.pattern_id] = failure
            self._save()
            logger.info(f"Recorded new failure pattern {failure.pattern_id}")
            return failure.pattern_id
    
    def _find_similar_pattern(self, signature: str) -> Optional[FailurePattern]:
        """Find existing pattern with similar signature"""
        for failure in self.failures.values():
            # Simple similarity check - can be enhanced
            if failure.detection_signature == signature:
                return failure
        return None
    
    def get_failures_for_object(self, object_id: str) -> List[FailurePattern]:
        """Get all failure patterns affecting an object"""
        return [f for f in self.failures.values() if object_id in f.affected_objects]
    
    def get_failures_for_capability(self, capability_id: str) -> List[FailurePattern]:
        """Get all failure patterns affecting a capability"""
        return [f for f in self.failures.values() if capability_id in f.affected_capabilities]
    
    def get_critical_failures(self) -> List[FailurePattern]:
        """Get all critical severity failures"""
        return [f for f in self.failures.values() if f.severity == "critical"]
    
    def check_for_regression(self, object_id: str, capability_id: str) -> List[FailurePattern]:
        """Check if an object/capability has historical failures (regression risk)"""
        patterns = []
        patterns.extend(self.get_failures_for_object(object_id))
        patterns.extend(self.get_failures_for_capability(capability_id))
        return list({p.pattern_id: p for p in patterns}.values())  # Deduplicate


# ============================================================================
# Candidate Archive
# ============================================================================

@dataclass
class RejectedCandidate:
    """
    Candidate Archive Entry
    
    Stores rejected candidates and reasons for rejection.
    """
    candidate_id: str
    object_type: str
    
    # Rejection details
    rejection_stage: str  # Which stage rejected: observed, profiled, benchmarked, etc.
    rejection_reason: str
    rejection_criteria: List[str]  # Which criteria failed
    
    # Performance at rejection
    performance_metrics: Dict[str, float]
    comparison_to_threshold: Dict[str, float]  # How far from threshold
    
    # Context
    alternative_selected: Optional[str]  # What was selected instead
    timestamp: str
    
    # Provenance
    provenance: Provenance
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "object_type": self.object_type,
            "rejection_stage": self.rejection_stage,
            "rejection_reason": self.rejection_reason,
            "rejection_criteria": self.rejection_criteria,
            "performance_metrics": self.performance_metrics,
            "comparison_to_threshold": self.comparison_to_threshold,
            "alternative_selected": self.alternative_selected,
            "timestamp": self.timestamp,
            "provenance": {
                "created_at": self.provenance.created_at,
                "created_by": self.provenance.created_by,
                "source_object_id": self.provenance.source_object_id,
                "evidence_hash": self.provenance.evidence_hash
            }
        }


class CandidateArchive:
    """Candidate Archive per Section 9"""
    
    def __init__(self, storage_path: str = "./candidate_archive.json"):
        self.storage_path = Path(storage_path)
        self.rejected: Dict[str, RejectedCandidate] = {}
        self._load()
        logger.info(f"CandidateArchive initialized with {len(self.rejected)} rejected candidates")
    
    def _load(self):
        """Load from storage"""
        if self.storage_path.exists():
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for candidate_id, candidate_dict in data.items():
                    self.rejected[candidate_id] = self._dict_to_candidate(candidate_dict)
    
    def _save(self):
        """Save to storage"""
        data = {k: v.to_dict() for k, v in self.rejected.items()}
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _dict_to_candidate(self, data: Dict[str, Any]) -> RejectedCandidate:
        prov_data = data.get("provenance", {})
        provenance = Provenance(
            created_at=prov_data.get("created_at", datetime.utcnow().isoformat()),
            created_by=prov_data.get("created_by", "unknown"),
            source_object_id=prov_data.get("source_object_id"),
            evidence_hash=prov_data.get("evidence_hash", "unknown"),
            validation_status="rejected"
        )
        
        return RejectedCandidate(
            candidate_id=data["candidate_id"],
            object_type=data["object_type"],
            rejection_stage=data["rejection_stage"],
            rejection_reason=data["rejection_reason"],
            rejection_criteria=data.get("rejection_criteria", []),
            performance_metrics=data.get("performance_metrics", {}),
            comparison_to_threshold=data.get("comparison_to_threshold", {}),
            alternative_selected=data.get("alternative_selected"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            provenance=provenance
        )
    
    def archive_rejection(self, candidate: RejectedCandidate) -> str:
        """Archive a rejected candidate"""
        self.rejected[candidate.candidate_id] = candidate
        self._save()
        logger.info(f"Archived rejected candidate {candidate.candidate_id}: {candidate.rejection_reason}")
        return candidate.candidate_id
    
    def find_similar_rejections(self, object_type: str, 
                               capability_id: str) -> List[RejectedCandidate]:
        """Find similar past rejections (to avoid repeating mistakes)"""
        # This would need capability info in the archive entry
        # Simplified version here
        return [
            c for c in self.rejected.values()
            if c.object_type == object_type
        ]
    
    def get_rejection_statistics(self) -> Dict[str, Any]:
        """Get statistics on rejections"""
        by_stage = defaultdict(int)
        by_reason = defaultdict(int)
        
        for candidate in self.rejected.values():
            by_stage[candidate.rejection_stage] += 1
            by_reason[candidate.rejection_reason] += 1
        
        return {
            "total_rejected": len(self.rejected),
            "by_stage": dict(by_stage),
            "by_reason": dict(by_reason)
        }


# ============================================================================
# Route Performance Memory
# ============================================================================

@dataclass
class RoutePerformanceRecord:
    """
    Route Performance Memory Entry
    
    Stores historical route performance by capability, regime, and risk tier.
    """
    record_id: str
    
    # Context
    capability_id: str
    regime: str
    risk_tier: str
    
    # Selected object
    selected_object_id: str
    
    # Performance
    success: bool
    latency_ms: float
    output_quality: float
    cost: float
    
    # Comparison to alternatives
    alternatives_considered: List[str]
    alternative_performances: Dict[str, float]  # If they had been selected
    
    # Was this a good decision?
    counterfactual_regret: float  # Regret vs best alternative
    
    # Timestamp
    timestamp: str
    
    # Provenance
    provenance: Provenance
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "capability_id": self.capability_id,
            "regime": self.regime,
            "risk_tier": self.risk_tier,
            "selected_object_id": self.selected_object_id,
            "success": self.success,
            "latency_ms": self.latency_ms,
            "output_quality": self.output_quality,
            "cost": self.cost,
            "alternatives_considered": self.alternatives_considered,
            "alternative_performances": self.alternative_performances,
            "counterfactual_regret": self.counterfactual_regret,
            "timestamp": self.timestamp,
            "provenance": {
                "created_at": self.provenance.created_at,
                "created_by": self.provenance.created_by
            }
        }


class RoutePerformanceMemory:
    """Route Performance Memory per Section 9"""
    
    def __init__(self, db_path: str = "./route_performance.db"):
        self.db_path = Path(db_path)
        self._init_db()
        logger.info("RoutePerformanceMemory initialized")
    
    def _init_db(self):
        """Initialize database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS route_performance (
                record_id TEXT PRIMARY KEY,
                capability_id TEXT,
                regime TEXT,
                risk_tier TEXT,
                selected_object_id TEXT,
                success INTEGER,
                latency_ms REAL,
                output_quality REAL,
                cost REAL,
                alternatives_considered TEXT,
                alternative_performances TEXT,
                counterfactual_regret REAL,
                timestamp TEXT,
                provenance TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cap ON route_performance(capability_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_regime ON route_performance(regime)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_object ON route_performance(selected_object_id)")
        conn.commit()
        conn.close()
    
    def record_performance(self, record: RoutePerformanceRecord):
        """Record a routing performance"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO route_performance VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.record_id,
            record.capability_id,
            record.regime,
            record.risk_tier,
            record.selected_object_id,
            1 if record.success else 0,
            record.latency_ms,
            record.output_quality,
            record.cost,
            json.dumps(record.alternatives_considered),
            json.dumps(record.alternative_performances),
            record.counterfactual_regret,
            record.timestamp,
            json.dumps({"created_at": record.provenance.created_at, "created_by": record.provenance.created_by})
        ))
        conn.commit()
        conn.close()
    
    def get_object_performance(self, object_id: str, 
                              capability_id: Optional[str] = None,
                              regime: Optional[str] = None,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get performance history for an object"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM route_performance WHERE selected_object_id = ?"
        params = [object_id]
        
        if capability_id:
            query += " AND capability_id = ?"
            params.append(capability_id)
        if regime:
            query += " AND regime = ?"
            params.append(regime)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = conn.execute(query, params).fetchall()
        conn.close()
        
        return [
            {
                "capability_id": row[1],
                "regime": row[2],
                "success": bool(row[5]),
                "latency_ms": row[6],
                "output_quality": row[7],
                "counterfactual_regret": row[11],
                "timestamp": row[12]
            }
            for row in rows
        ]
    
    def get_best_object_for_context(self, capability_id: str, 
                                   regime: str, 
                                   risk_tier: str,
                                   min_samples: int = 10) -> Optional[str]:
        """Get best performing object for a specific context"""
        conn = sqlite3.connect(self.db_path)
        
        rows = conn.execute("""
            SELECT selected_object_id, 
                   AVG(output_quality) as avg_quality,
                   AVG(counterfactual_regret) as avg_regret,
                   COUNT(*) as sample_count
            FROM route_performance
            WHERE capability_id = ? AND regime = ? AND risk_tier = ?
            GROUP BY selected_object_id
            HAVING COUNT(*) >= ?
            ORDER BY avg_quality - avg_regret DESC
            LIMIT 1
        """, (capability_id, regime, risk_tier, min_samples)).fetchall()
        
        conn.close()
        
        if rows:
            return rows[0][0]
        return None


# ============================================================================
# Distillation Registry
# ============================================================================

@dataclass
class DistillationRegistryEntry:
    """
    Distillation Registry Entry
    
    Stores teacher-student relationships, distillation evidence, 
    and student performance drift tracking.
    """
    entry_id: str
    
    # Teacher-student relationship
    teacher_object_id: str
    student_object_id: str
    
    # What was distilled
    distilled_capabilities: List[str]
    distillation_method: str
    training_dataset_size: int
    
    # Initial performance
    teacher_initial_performance: Dict[str, float]
    student_initial_performance: Dict[str, float]
    initial_gap: float
    
    # Drift tracking
    performance_history: List[Dict[str, Any]]  # Timestamped performance checks
    drift_detected: bool
    drift_metrics: Dict[str, float]
    
    # Revalidation
    last_revalidation: str
    next_revalidation: str
    
    # Status
    status: str  # 'active', 'stale', 'deprecated', 'retraining'
    
    # Provenance
    provenance: Provenance
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "teacher_object_id": self.teacher_object_id,
            "student_object_id": self.student_object_id,
            "distilled_capabilities": self.distilled_capabilities,
            "distillation_method": self.distillation_method,
            "training_dataset_size": self.training_dataset_size,
            "teacher_initial_performance": self.teacher_initial_performance,
            "student_initial_performance": self.student_initial_performance,
            "initial_gap": self.initial_gap,
            "performance_history": self.performance_history,
            "drift_detected": self.drift_detected,
            "drift_metrics": self.drift_metrics,
            "last_revalidation": self.last_revalidation,
            "next_revalidation": self.next_revalidation,
            "status": self.status,
            "provenance": {
                "created_at": self.provenance.created_at,
                "created_by": self.provenance.created_by
            }
        }


class DistillationRegistry:
    """Distillation Registry per Section 9"""
    
    def __init__(self, storage_path: str = "./distillation_registry.json"):
        self.storage_path = Path(storage_path)
        self.entries: Dict[str, DistillationRegistryEntry] = {}
        self._load()
        logger.info(f"DistillationRegistry initialized with {len(self.entries)} entries")
    
    def _load(self):
        """Load from storage"""
        if self.storage_path.exists():
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for entry_id, entry_dict in data.items():
                    self.entries[entry_id] = self._dict_to_entry(entry_dict)
    
    def _save(self):
        """Save to storage"""
        data = {k: v.to_dict() for k, v in self.entries.items()}
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _dict_to_entry(self, data: Dict[str, Any]) -> DistillationRegistryEntry:
        prov_data = data.get("provenance", {})
        provenance = Provenance(
            created_at=prov_data.get("created_at", datetime.utcnow().isoformat()),
            created_by=prov_data.get("created_by", "unknown"),
            source_object_id=data.get("teacher_object_id"),
            evidence_hash="distillation_evidence",
            validation_status="active"
        )
        
        return DistillationRegistryEntry(
            entry_id=data["entry_id"],
            teacher_object_id=data["teacher_object_id"],
            student_object_id=data["student_object_id"],
            distilled_capabilities=data.get("distilled_capabilities", []),
            distillation_method=data.get("distillation_method", "unknown"),
            training_dataset_size=data.get("training_dataset_size", 0),
            teacher_initial_performance=data.get("teacher_initial_performance", {}),
            student_initial_performance=data.get("student_initial_performance", {}),
            initial_gap=data.get("initial_gap", 0),
            performance_history=data.get("performance_history", []),
            drift_detected=data.get("drift_detected", False),
            drift_metrics=data.get("drift_metrics", {}),
            last_revalidation=data.get("last_revalidation", datetime.utcnow().isoformat()),
            next_revalidation=data.get("next_revalidation", ""),
            status=data.get("status", "active"),
            provenance=provenance
        )
    
    def register_distillation(self, entry: DistillationRegistryEntry) -> str:
        """Register a distillation relationship"""
        self.entries[entry.entry_id] = entry
        self._save()
        logger.info(f"Registered distillation {entry.entry_id}: "
                   f"{entry.teacher_object_id} -> {entry.student_object_id}")
        return entry.entry_id
    
    def record_performance_check(self, entry_id: str, 
                              current_performance: Dict[str, float]):
        """Record a performance check for drift detection"""
        entry = self.entries.get(entry_id)
        if not entry:
            return
        
        # Check for drift
        initial = entry.student_initial_performance.get("overall", 1.0)
        current = current_performance.get("overall", 1.0)
        drift = initial - current
        
        entry.performance_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "performance": current_performance,
            "drift_from_initial": drift
        })
        
        if drift > 0.05:  # 5% degradation threshold
            entry.drift_detected = True
            entry.drift_metrics = {"current_drift": drift, "threshold": 0.05}
            entry.status = "stale"
            logger.warning(f"Drift detected in distillation {entry_id}: {drift:.3f}")
        
        entry.last_revalidation = datetime.utcnow().isoformat()
        self._save()
    
    def get_student_for_teacher(self, teacher_id: str) -> Optional[str]:
        """Get student object ID for a teacher"""
        for entry in self.entries.values():
            if entry.teacher_object_id == teacher_id and entry.status == "active":
                return entry.student_object_id
        return None
    
    def get_distillations_needing_revalidation(self) -> List[DistillationRegistryEntry]:
        """Get distillations past their revalidation date"""
        now = datetime.utcnow()
        needing_revalidation = []
        
        for entry in self.entries.values():
            if entry.next_revalidation:
                next_date = datetime.fromisoformat(entry.next_revalidation)
                if now > next_date:
                    needing_revalidation.append(entry)
        
        return needing_revalidation


# ============================================================================
# Unified Memory Manager
# ============================================================================

class MemoryManager:
    """
    Unified manager for all memory systems.
    
    Provides coordinated access to:
    - Behavior Library
    - Failure Library
    - Candidate Archive
    - Route Performance Memory
    - Distillation Registry
    """
    
    def __init__(self, base_path: str = "./memory"):
        base = Path(base_path)
        base.mkdir(parents=True, exist_ok=True)
        
        self.behavior_library = BehaviorLibrary(str(base / "behavior_library.json"))
        self.failure_library = FailureLibrary(str(base / "failure_library.json"))
        self.candidate_archive = CandidateArchive(str(base / "candidate_archive.json"))
        self.route_memory = RoutePerformanceMemory(str(base / "route_performance.db"))
        self.distillation_registry = DistillationRegistry(str(base / "distillation_registry.json"))
        
        logger.info("MemoryManager initialized with all memory systems")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of all memory systems"""
        return {
            "behavior_library": {
                "total_behaviors": len(self.behavior_library.behaviors),
                "active": len([b for b in self.behavior_library.behaviors.values() if b.status == "active"]),
                "expired": len(self.behavior_library.get_expired_behaviors())
            },
            "failure_library": {
                "total_patterns": len(self.failure_library.failures),
                "critical": len(self.failure_library.get_critical_failures())
            },
            "candidate_archive": {
                "total_rejected": len(self.candidate_archive.rejected),
                "statistics": self.candidate_archive.get_rejection_statistics()
            },
            "distillation_registry": {
                "total_entries": len(self.distillation_registry.entries),
                "active": len([e for e in self.distillation_registry.entries.values() if e.status == "active"]),
                "needing_revalidation": len(self.distillation_registry.get_distillations_needing_revalidation())
            }
        }

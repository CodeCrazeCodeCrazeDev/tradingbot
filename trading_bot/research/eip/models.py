from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SourceType(Enum):
    GITHUB = "github"
    ARXIV = "arxiv"
    CREATOR = "creator"
    FRONTIER_MODEL = "frontier_model"
    PAPERS_WITH_CODE = "papers_with_code"
    HUGGING_FACE = "hugging_face"
    BENCHMARK = "benchmark"
    TECHNICAL_BLOG = "technical_blog"


class CapabilityDomain(Enum):
    COGNITIVE = "cognitive"          # Planning, reasoning, memory patterns
    ALGORITHMIC = "algorithmic"      # Math, statistics, indicators, execution algorithms
    BUSINESS = "business"            # Funnels, offers, operations, pricing models
    INFRASTRUCTURE = "infrastructure"# Devops, orchestration, security, data engineering


@dataclass
class EvidencePayload:
    """Represents a unified collected raw evidence artifact from any source adapter."""
    source_type: SourceType
    source_name: str
    source_url: str
    version_id: str
    collector_author: str
    claims: Dict[str, Any]
    code_samples: List[str] = field(default_factory=list)
    readme_content: str = ""
    license_name: str = "Unknown"
    collected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvidenceReport:
    """The output of the Evidence Quality Engine (EQE)."""
    base_weight: float
    cross_validation_bonus: float
    final_quality_score: float  # Weighted final score between 0.0 and 1.0
    passed_eq_gate: bool
    verified_checks: List[str]
    warnings: List[str]


@dataclass
class DistilledCapability:
    """A clean, distilled, structured quantitative pattern or business blueprint."""
    capability_id: str
    name: str
    domain: CapabilityDomain
    extracted_pattern: str        # The core pattern, decoupled from external dependencies
    original_weaknesses: List[str]
    inversion_controls: List[str] # Defensive controls to wrap inside the dynamic skill
    evidence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    distilled_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EIPProposal:
    """Provenance and rollout control node for EIP promotion."""
    proposal_id: str
    capability_id: str
    name: str
    domain: CapabilityDomain
    source_url: str
    version_id: str
    evidence_quality_score: float
    security_passed: bool
    license_status: str
    is_active: bool
    stage: str  # sandbox, shadow, canary, limited_production, full_deployment
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RegistryEntry:
    """Immutable Universal Capability Registry entity."""
    capability_id: str
    name: str
    domain: CapabilityDomain
    source_url: str
    version_id: str
    distilled_pattern: str
    compiled_code: str
    evidence_score: float
    validation_history: List[Dict[str, Any]] = field(default_factory=list)
    deployment_history: List[Dict[str, Any]] = field(default_factory=list)
    rollback_triggers: Dict[str, Any] = field(default_factory=dict)
    promoted_at: datetime = field(default_factory=datetime.utcnow)

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SourceType(Enum):
    GITHUB = "github"
    ARXIV = "arxiv"
    HUGGING_FACE = "hugging_face"
    BENCHMARK = "benchmark"
    BLOG = "blog"


class CapabilityCategory(Enum):
    EXECUTION = "execution"
    RISK = "risk"
    BACKTESTING = "backtesting"
    STATS = "stats"
    MICROSTRUCTURE = "microstructure"
    PORTFOLIO = "portfolio"


class TrustLevel(Enum):
    ZERO = "zero"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LicenseStatus(Enum):
    APPROVED = "approved"
    FORBIDDEN = "forbidden"
    UNKNOWN = "unknown"


class PromotionStage(Enum):
    SANDBOX = "sandbox"
    SHADOW = "shadow"
    CANARY = "canary"
    LIMITED_PRODUCTION = "limited_production"
    FULL_DEPLOYMENT = "full_deployment"


@dataclass
class ExternalCandidate:
    """Represents a discovered repository or research paper."""
    source_type: SourceType
    name: str
    url: str
    version_id: str  # Commit SHA or paper version ID
    author: str
    description: str
    readme_content: str = ""
    license_name: str = "Unknown"
    stars: int = 0
    forks: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TrustReport:
    """Trust scoring metrics."""
    overall_score: float  # 0.0 to 100.0
    trust_level: TrustLevel
    signals: Dict[str, Any]  # metrics like cadence, maintainer history, test quality
    is_acceptable: bool


@dataclass
class SecurityReport:
    """Security and static code audit results."""
    is_secure: bool
    secrets_found: List[str]
    unsafe_patterns: List[str]
    malicious_scripts_detected: bool
    filesystem_access_flagged: bool
    network_calls_flagged: bool
    import_warnings: List[str]
    dependency_vulnerabilities: List[str]
    raw_output: str = ""


@dataclass
class DistilledPattern:
    """Represents core quantitative logic isolated from external wrappers."""
    pattern_id: str
    candidate_url: str
    version_id: str
    category: CapabilityCategory
    extracted_logic: str  # Code template or algorithmic description
    original_weaknesses: List[str]
    inversion_controls: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    distilled_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CompiledSkill:
    """An executable AlphaAlgo One Brain skill program."""
    skill_id: str
    name: str
    category: CapabilityCategory
    code: str  # Executable python code
    provenance_hash: str
    falsification_tests: List[str]
    compiled_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PromotionProposal:
    """Provenance and rollout control node stored in Research OS."""
    proposal_id: str
    compiled_skill: CompiledSkill
    candidate_url: str
    version_id: str
    license_name: str
    trust_score: float
    security_passed: bool
    stage: PromotionStage
    benchmarks: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

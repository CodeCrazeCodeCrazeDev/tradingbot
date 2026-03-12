"""
Intelligent & Social Delegation - Core Types
Based on Google DeepMind "Intelligent AI Delegation" (2026, arXiv:2602.11865)

Defines all data structures, enums, and contracts for the delegation framework.
Maps the paper's 9-component framework to algorithmic trading:
  4.1 Task Decomposition | 4.2 Task Assignment | 4.3 Multi-objective Optimization
  4.4 Adaptive Coordination | 4.5 Monitoring | 4.6 Trust & Reputation
  4.7 Permission Handling | 4.8 Verifiable Task Completion | 4.9 Security
"""

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, IntEnum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# SECTION 2.2: Task Characteristic Axes (11 dimensions from the paper)
# ============================================================================

class TaskComplexity(IntEnum):
    """Degree of difficulty inherent in the task."""
    TRIVIAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    EXTREME = 5


class TaskCriticality(IntEnum):
    """Severity of consequences associated with failure."""
    INFORMATIONAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    CRITICAL = 5


class TaskUncertainty(IntEnum):
    """Level of ambiguity regarding environment, inputs, or outcome probability."""
    DETERMINISTIC = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    UNKNOWN = 5


class TaskReversibility(IntEnum):
    """Degree to which effects of task execution can be undone."""
    FULLY_REVERSIBLE = 1
    MOSTLY_REVERSIBLE = 2
    PARTIALLY_REVERSIBLE = 3
    MOSTLY_IRREVERSIBLE = 4
    IRREVERSIBLE = 5


class TaskVerifiability(IntEnum):
    """Relative difficulty and cost of validating the task outcome."""
    AUTO_VERIFIABLE = 1
    EASILY_VERIFIABLE = 2
    MODERATELY_VERIFIABLE = 3
    HARD_TO_VERIFY = 4
    UNVERIFIABLE = 5


class TaskSubjectivity(IntEnum):
    """Extent to which success criteria are preference vs objective fact."""
    OBJECTIVE = 1
    MOSTLY_OBJECTIVE = 2
    MIXED = 3
    MOSTLY_SUBJECTIVE = 4
    SUBJECTIVE = 5


class TaskContextuality(IntEnum):
    """Volume and sensitivity of external state required."""
    CONTEXT_FREE = 1
    LOW_CONTEXT = 2
    MODERATE_CONTEXT = 3
    HIGH_CONTEXT = 4
    FULL_CONTEXT = 5


# ============================================================================
# SECTION 2.2: Delegation Axes
# ============================================================================

class ActorType(Enum):
    """Delegator or Delegatee type."""
    HUMAN = "human"
    AI_AGENT = "ai_agent"
    AI_SPECIALIST = "ai_specialist"
    AI_ENSEMBLE = "ai_ensemble"
    HYBRID_TEAM = "hybrid_team"


class DelegationGranularity(Enum):
    """Fine-grained vs coarse-grained objectives."""
    ATOMIC = "atomic"
    FINE_GRAINED = "fine_grained"
    MODERATE = "moderate"
    COARSE_GRAINED = "coarse_grained"
    OPEN_ENDED = "open_ended"


class AutonomyLevel(IntEnum):
    """Level of autonomy granted to delegatee."""
    NONE = 0
    EXECUTE_ONLY = 1
    EXECUTE_WITH_PARAMS = 2
    DECOMPOSE_AND_EXECUTE = 3
    FULL_AUTONOMY = 4


class MonitoringMode(Enum):
    """Monitoring frequency for delegated tasks."""
    CONTINUOUS = "continuous"
    PERIODIC = "periodic"
    EVENT_TRIGGERED = "event_triggered"
    OUTCOME_ONLY = "outcome_only"


# ============================================================================
# TRADING-SPECIFIC: Agent Specializations
# ============================================================================

class AgentSpecialization(Enum):
    """Specialized trading agent roles that can be delegated to."""
    MARKET_ANALYST = "market_analyst"
    TECHNICAL_ANALYST = "technical_analyst"
    FUNDAMENTAL_ANALYST = "fundamental_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    RISK_MANAGER = "risk_manager"
    POSITION_SIZER = "position_sizer"
    EXECUTION_ENGINE = "execution_engine"
    ORDER_ROUTER = "order_router"
    PORTFOLIO_OPTIMIZER = "portfolio_optimizer"
    REGIME_DETECTOR = "regime_detector"
    VOLATILITY_FORECASTER = "volatility_forecaster"
    CORRELATION_TRACKER = "correlation_tracker"
    NEWS_PROCESSOR = "news_processor"
    DATA_VALIDATOR = "data_validator"
    COMPLIANCE_CHECKER = "compliance_checker"
    PERFORMANCE_TRACKER = "performance_tracker"
    STRATEGY_SELECTOR = "strategy_selector"
    SIGNAL_GENERATOR = "signal_generator"
    STOP_LOSS_MANAGER = "stop_loss_manager"
    HUMAN_OVERSEER = "human_overseer"


class TradingTaskType(Enum):
    """Types of trading tasks that can be delegated."""
    ANALYZE_MARKET = "analyze_market"
    GENERATE_SIGNAL = "generate_signal"
    VALIDATE_SIGNAL = "validate_signal"
    CALCULATE_POSITION_SIZE = "calculate_position_size"
    ASSESS_RISK = "assess_risk"
    EXECUTE_ORDER = "execute_order"
    MONITOR_POSITION = "monitor_position"
    MANAGE_STOP_LOSS = "manage_stop_loss"
    OPTIMIZE_PORTFOLIO = "optimize_portfolio"
    DETECT_REGIME = "detect_regime"
    FORECAST_VOLATILITY = "forecast_volatility"
    PROCESS_NEWS = "process_news"
    VALIDATE_DATA = "validate_data"
    CHECK_COMPLIANCE = "check_compliance"
    TRACK_PERFORMANCE = "track_performance"
    HEDGE_POSITION = "hedge_position"
    REBALANCE_PORTFOLIO = "rebalance_portfolio"
    EMERGENCY_EXIT = "emergency_exit"
    HUMAN_REVIEW = "human_review"
    HUMAN_APPROVAL = "human_approval"


# ============================================================================
# SECTION 2.2: Task Characteristics (11-dimensional descriptor)
# ============================================================================

@dataclass
class TaskCharacteristics:
    """11-dimensional task descriptor from Section 2.2 of the paper."""
    complexity: TaskComplexity = TaskComplexity.MODERATE
    criticality: TaskCriticality = TaskCriticality.MODERATE
    uncertainty: TaskUncertainty = TaskUncertainty.MODERATE
    duration_seconds: float = 60.0
    cost_estimate: float = 0.0
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    verifiability: TaskVerifiability = TaskVerifiability.MODERATELY_VERIFIABLE
    reversibility: TaskReversibility = TaskReversibility.PARTIALLY_REVERSIBLE
    contextuality: TaskContextuality = TaskContextuality.MODERATE_CONTEXT
    subjectivity: TaskSubjectivity = TaskSubjectivity.MOSTLY_OBJECTIVE

    @property
    def risk_score(self) -> float:
        """Composite risk score (0-1) based on criticality, irreversibility, uncertainty."""
        return (
            (self.criticality.value / 5.0) * 0.4 +
            (self.reversibility.value / 5.0) * 0.3 +
            (self.uncertainty.value / 5.0) * 0.3
        )

    @property
    def requires_human_oversight(self) -> bool:
        """Paper Section 4.7: High-stakes tasks require human-in-the-loop."""
        return (
            self.criticality >= TaskCriticality.HIGH and
            self.reversibility >= TaskReversibility.MOSTLY_IRREVERSIBLE
        )

    @property
    def bypass_delegation(self) -> bool:
        """Paper Section 4.3: Complexity floor — trivial tasks skip delegation."""
        return (
            self.complexity <= TaskComplexity.LOW and
            self.criticality <= TaskCriticality.LOW and
            self.uncertainty <= TaskUncertainty.LOW and
            self.duration_seconds < 5.0
        )


# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

@dataclass
class DelegationTask:
    """A task to be delegated within the intelligent delegation framework."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    task_type: TradingTaskType = TradingTaskType.ANALYZE_MARKET
    description: str = ""
    characteristics: TaskCharacteristics = field(default_factory=TaskCharacteristics)
    input_data: Dict[str, Any] = field(default_factory=dict)
    expected_output_schema: Dict[str, str] = field(default_factory=dict)
    parent_task_id: Optional[str] = None
    sub_task_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    status: str = "pending"
    assigned_to: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    verification_status: str = "unverified"
    delegation_chain: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.deadline:
            return datetime.utcnow() > self.deadline
        return False

    @property
    def chain_depth(self) -> int:
        return len(self.delegation_chain)

    def fingerprint(self) -> str:
        """Unique content hash for idempotency."""
        content = f"{self.task_type.value}:{self.description}:{self.input_data}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class AgentCapability:
    """Describes what an agent can do and how well."""
    specialization: AgentSpecialization = AgentSpecialization.MARKET_ANALYST
    supported_tasks: List[TradingTaskType] = field(default_factory=list)
    proficiency_score: float = 0.5
    max_concurrent_tasks: int = 5
    avg_latency_ms: float = 100.0
    success_rate: float = 0.9
    cost_per_task: float = 0.0
    certifications: List[str] = field(default_factory=list)
    resource_limits: Dict[str, float] = field(default_factory=dict)


@dataclass
class AgentProfile:
    """Complete profile of a delegation agent (AI or human)."""
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    actor_type: ActorType = ActorType.AI_AGENT
    capabilities: List[AgentCapability] = field(default_factory=list)
    current_load: int = 0
    max_load: int = 10
    is_available: bool = True
    trust_score: float = 0.5
    reputation_score: float = 0.5
    permissions: Set[str] = field(default_factory=set)
    active_tasks: List[str] = field(default_factory=list)
    completed_tasks: int = 0
    failed_tasks: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def utilization(self) -> float:
        return self.current_load / max(self.max_load, 1)

    @property
    def is_overloaded(self) -> bool:
        return self.current_load >= self.max_load

    def supports_task(self, task_type: TradingTaskType) -> bool:
        return any(task_type in cap.supported_tasks for cap in self.capabilities)

    def get_capability_for(self, task_type: TradingTaskType) -> Optional[AgentCapability]:
        for cap in self.capabilities:
            if task_type in cap.supported_tasks:
                return cap
        return None


# ============================================================================
# SECTION 4.2: Smart Contracts for Delegation
# ============================================================================

@dataclass
class DelegationContract:
    """Bidirectional smart contract between delegator and delegatee (Section 4.2)."""
    contract_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    task_id: str = ""
    delegator_id: str = ""
    delegatee_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    autonomy_level: AutonomyLevel = AutonomyLevel.EXECUTE_ONLY
    monitoring_mode: MonitoringMode = MonitoringMode.PERIODIC
    monitoring_interval_seconds: float = 30.0
    performance_requirements: Dict[str, float] = field(default_factory=dict)
    verification_method: str = "direct_inspection"
    max_resource_budget: Dict[str, float] = field(default_factory=dict)
    penalty_for_breach: float = 0.0
    cancellation_terms: str = "immediate"
    renegotiation_allowed: bool = True
    privacy_constraints: List[str] = field(default_factory=list)
    backup_agent_id: Optional[str] = None
    dispute_resolution: str = "delegator_decides"
    escrow_amount: float = 0.0
    status: str = "active"
    attestations: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False


# ============================================================================
# SECTION 4.5: Monitoring Events
# ============================================================================

class MonitoringTarget(Enum):
    """What is being monitored (Section 4.5 Axis 1)."""
    OUTCOME = "outcome"
    PROCESS = "process"


class MonitoringObservability(Enum):
    """How monitoring is performed (Section 4.5 Axis 2)."""
    DIRECT = "direct"
    INDIRECT = "indirect"


class MonitoringTransparency(Enum):
    """System transparency level (Section 4.5 Axis 3)."""
    BLACK_BOX = "black_box"
    GREY_BOX = "grey_box"
    WHITE_BOX = "white_box"


class MonitoringPrivacy(Enum):
    """Privacy level for monitoring (Section 4.5 Axis 4)."""
    FULL_TRANSPARENCY = "full_transparency"
    ANONYMIZED = "anonymized"
    ENCRYPTED = "encrypted"
    ZERO_KNOWLEDGE = "zero_knowledge"


@dataclass
class MonitoringEvent:
    """An event emitted during task monitoring."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    task_id: str = ""
    agent_id: str = ""
    event_type: str = "CHECKPOINT_REACHED"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    progress_percent: float = 0.0
    resource_consumed: Dict[str, float] = field(default_factory=dict)
    quality_score: Optional[float] = None
    anomaly_detected: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# SECTION 4.6: Trust & Reputation
# ============================================================================

class TrustDimension(Enum):
    """Dimensions of trust assessment."""
    COMPETENCE = "competence"
    RELIABILITY = "reliability"
    INTEGRITY = "integrity"
    ALIGNMENT = "alignment"
    TRANSPARENCY = "transparency"


@dataclass
class ReputationRecord:
    """Immutable record of a completed delegation (Section 4.6)."""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    agent_id: str = ""
    task_id: str = ""
    task_type: TradingTaskType = TradingTaskType.ANALYZE_MARKET
    success: bool = True
    quality_score: float = 0.8
    latency_ms: float = 100.0
    resource_consumed: Dict[str, float] = field(default_factory=dict)
    deadline_met: bool = True
    constraint_violations: List[str] = field(default_factory=list)
    delegator_feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    verified: bool = False
    attestation_hash: Optional[str] = None

    def compute_attestation(self) -> str:
        content = (
            f"{self.agent_id}:{self.task_id}:{self.success}:"
            f"{self.quality_score}:{self.timestamp.isoformat()}"
        )
        self.attestation_hash = hashlib.sha256(content.encode()).hexdigest()
        return self.attestation_hash


# ============================================================================
# SECTION 4.7: Permissions
# ============================================================================

class PermissionScope(Enum):
    """Scope of permissions granted."""
    READ_MARKET_DATA = "read_market_data"
    READ_PORTFOLIO = "read_portfolio"
    READ_POSITIONS = "read_positions"
    GENERATE_SIGNALS = "generate_signals"
    PLACE_ORDERS = "place_orders"
    MODIFY_ORDERS = "modify_orders"
    CANCEL_ORDERS = "cancel_orders"
    MODIFY_RISK_PARAMS = "modify_risk_params"
    ACCESS_CREDENTIALS = "access_credentials"
    SUB_DELEGATE = "sub_delegate"
    EMERGENCY_ACTIONS = "emergency_actions"
    HUMAN_ESCALATION = "human_escalation"


@dataclass
class PermissionGrant:
    """A time-bounded, scoped permission (Section 4.7)."""
    grant_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    agent_id: str = ""
    scope: PermissionScope = PermissionScope.READ_MARKET_DATA
    granted_by: str = ""
    granted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    is_revoked: bool = False
    revoked_reason: Optional[str] = None
    can_sub_delegate: bool = False
    max_delegation_depth: int = 1

    @property
    def is_valid(self) -> bool:
        if self.is_revoked:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def attenuate(self, new_agent_id: str) -> Optional['PermissionGrant']:
        """Privilege attenuation for sub-delegation (Section 4.7)."""
        if not self.can_sub_delegate or self.max_delegation_depth <= 0:
            return None
        return PermissionGrant(
            agent_id=new_agent_id,
            scope=self.scope,
            granted_by=self.agent_id,
            expires_at=self.expires_at,
            constraints=self.constraints.copy(),
            can_sub_delegate=self.max_delegation_depth > 1,
            max_delegation_depth=self.max_delegation_depth - 1,
        )


# ============================================================================
# SECTION 4.9: Security Threat Categories
# ============================================================================

class ThreatCategory(Enum):
    """Security threat categories from Section 4.9."""
    DATA_EXFILTRATION = "data_exfiltration"
    DATA_POISONING = "data_poisoning"
    VERIFICATION_SUBVERSION = "verification_subversion"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    BACKDOOR_IMPLANTING = "backdoor_implanting"
    HARMFUL_DELEGATION = "harmful_delegation"
    VULNERABILITY_PROBING = "vulnerability_probing"
    PROMPT_INJECTION = "prompt_injection"
    MODEL_EXTRACTION = "model_extraction"
    REPUTATION_SABOTAGE = "reputation_sabotage"
    SYBIL_ATTACK = "sybil_attack"
    COLLUSION = "collusion"
    AGENT_TRAP = "agent_trap"
    AGENTIC_VIRUS = "agentic_virus"
    PROTOCOL_EXPLOITATION = "protocol_exploitation"
    COGNITIVE_MONOCULTURE = "cognitive_monoculture"


class ThreatSeverity(IntEnum):
    """Severity of detected threat."""
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


@dataclass
class SecurityThreat:
    """A detected security threat."""
    threat_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    category: ThreatCategory = ThreatCategory.DATA_POISONING
    severity: ThreatSeverity = ThreatSeverity.MEDIUM
    source_agent_id: Optional[str] = None
    target_agent_id: Optional[str] = None
    task_id: Optional[str] = None
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    mitigated: bool = False
    mitigation_action: Optional[str] = None


# ============================================================================
# SECTION 4.4: Adaptive Coordination Triggers
# ============================================================================

class AdaptiveTriggerType(Enum):
    """Triggers for adaptive re-delegation (Section 4.4)."""
    SPEC_CHANGE = "spec_change"
    TASK_CANCELLED = "task_cancelled"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    HIGHER_PRIORITY_TASK = "higher_priority_task"
    SECURITY_THREAT = "security_threat"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    BUDGET_EXCEEDED = "budget_exceeded"
    VERIFICATION_FAILED = "verification_failed"
    AGENT_UNRESPONSIVE = "agent_unresponsive"
    MARKET_REGIME_CHANGE = "market_regime_change"
    VOLATILITY_SPIKE = "volatility_spike"
    LIQUIDITY_CRISIS = "liquidity_crisis"


@dataclass
class AdaptiveTrigger:
    """An event that triggers adaptive re-delegation."""
    trigger_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    trigger_type: AdaptiveTriggerType = AdaptiveTriggerType.PERFORMANCE_DEGRADATION
    task_id: str = ""
    agent_id: str = ""
    severity: ThreatSeverity = ThreatSeverity.MEDIUM
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)
    requires_immediate_response: bool = False
    requires_human_escalation: bool = False


# ============================================================================
# SECTION 5: Ethical Delegation
# ============================================================================

class EthicalConcern(Enum):
    """Ethical concerns from Section 5 of the paper."""
    MEANINGFUL_HUMAN_CONTROL = "meaningful_human_control"
    ACCOUNTABILITY_VACUUM = "accountability_vacuum"
    RELIABILITY_PREMIUM = "reliability_premium"
    SAFETY_AS_LUXURY = "safety_as_luxury"
    SOCIAL_INTELLIGENCE = "social_intelligence"
    DE_SKILLING_RISK = "de_skilling_risk"
    MORAL_CRUMPLE_ZONE = "moral_crumple_zone"
    ALARM_FATIGUE = "alarm_fatigue"
    COGNITIVE_FRICTION = "cognitive_friction"
    APPRENTICESHIP_EROSION = "apprenticeship_erosion"


# ============================================================================
# PAPER RISKS & UNRESOLVED CHALLENGES (Comprehensive catalog)
# ============================================================================

class RiskCategory(Enum):
    """All risks and unresolved challenges identified in the paper."""
    # Section 4.1 - Task Decomposition Risks
    DECOMPOSITION_EXPLOSION = "decomposition_explosion"
    VERIFICATION_GAP = "verification_gap"
    LATENCY_ASYMMETRY = "latency_asymmetry"

    # Section 4.2 - Task Assignment Risks
    MARKET_MANIPULATION = "market_manipulation"
    BID_COLLUSION = "bid_collusion"
    UNFAIR_CONTRACTS = "unfair_contracts"

    # Section 4.3 - Multi-objective Optimization Risks
    PARETO_SUBOPTIMALITY = "pareto_suboptimality"
    DELEGATION_OVERHEAD = "delegation_overhead"
    COST_OF_ADAPTATION = "cost_of_adaptation"

    # Section 4.4 - Adaptive Coordination Risks
    OSCILLATION = "oscillation"
    CASCADE_REALLOCATION = "cascade_reallocation"
    SINGLE_POINT_OF_FAILURE = "single_point_of_failure"
    CENTRALIZATION_BOTTLENECK = "centralization_bottleneck"

    # Section 4.5 - Monitoring Risks
    UNFAITHFUL_REASONING = "unfaithful_reasoning"
    TRANSITIVE_MONITORING_FAILURE = "transitive_monitoring_failure"
    MONITORING_OVERHEAD = "monitoring_overhead"

    # Section 4.6 - Trust & Reputation Risks
    REPUTATION_GAMING = "reputation_gaming"
    REPUTATION_SABOTAGE = "reputation_sabotage"
    TRUST_THRESHOLD_MISCALIBRATION = "trust_threshold_miscalibration"

    # Section 4.7 - Permission Risks
    CONFUSED_DEPUTY = "confused_deputy"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PERMISSION_DRIFT = "permission_drift"

    # Section 4.8 - Verification Risks
    SUBJECTIVE_DISAGREEMENT = "subjective_disagreement"
    POST_HOC_ERROR_DISCOVERY = "post_hoc_error_discovery"
    RECURSIVE_LIABILITY = "recursive_liability"

    # Section 4.9 - Security Risks
    SYBIL_ATTACK = "sybil_attack"
    AGENTIC_VIRUS = "agentic_virus"
    COGNITIVE_MONOCULTURE = "cognitive_monoculture"
    PROTOCOL_EXPLOITATION = "protocol_exploitation"

    # Section 5 - Ethical Risks
    EROSION_OF_HUMAN_CONTROL = "erosion_of_human_control"
    ACCOUNTABILITY_VACUUM = "accountability_vacuum"
    SAFETY_INEQUALITY = "safety_inequality"
    DE_SKILLING = "de_skilling"
    ALARM_FATIGUE = "alarm_fatigue"
    APPRENTICESHIP_EROSION = "apprenticeship_erosion"


@dataclass
class RiskMitigation:
    """A mitigation strategy for an identified risk."""
    risk: RiskCategory
    description: str
    mitigation_strategy: str
    implementation_status: str = "implemented"
    severity_before: ThreatSeverity = ThreatSeverity.HIGH
    severity_after: ThreatSeverity = ThreatSeverity.LOW
    automated: bool = True


# ============================================================================
# DELEGATION RESULT
# ============================================================================

@dataclass
class DelegationResult:
    """Result of a delegation operation."""
    task_id: str = ""
    success: bool = False
    output: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    latency_ms: float = 0.0
    agent_id: str = ""
    verification_passed: bool = False
    verification_method: str = ""
    attestation_hash: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sub_results: List['DelegationResult'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# TRADING-SPECIFIC TASK TEMPLATES
# ============================================================================

TRADING_TASK_TEMPLATES: Dict[TradingTaskType, TaskCharacteristics] = {
    TradingTaskType.ANALYZE_MARKET: TaskCharacteristics(
        complexity=TaskComplexity.MODERATE,
        criticality=TaskCriticality.MODERATE,
        uncertainty=TaskUncertainty.MODERATE,
        duration_seconds=5.0,
        verifiability=TaskVerifiability.MODERATELY_VERIFIABLE,
        reversibility=TaskReversibility.FULLY_REVERSIBLE,
        contextuality=TaskContextuality.HIGH_CONTEXT,
        subjectivity=TaskSubjectivity.MIXED,
    ),
    TradingTaskType.GENERATE_SIGNAL: TaskCharacteristics(
        complexity=TaskComplexity.HIGH,
        criticality=TaskCriticality.HIGH,
        uncertainty=TaskUncertainty.HIGH,
        duration_seconds=10.0,
        verifiability=TaskVerifiability.HARD_TO_VERIFY,
        reversibility=TaskReversibility.FULLY_REVERSIBLE,
        contextuality=TaskContextuality.HIGH_CONTEXT,
        subjectivity=TaskSubjectivity.MIXED,
    ),
    TradingTaskType.EXECUTE_ORDER: TaskCharacteristics(
        complexity=TaskComplexity.MODERATE,
        criticality=TaskCriticality.CRITICAL,
        uncertainty=TaskUncertainty.MODERATE,
        duration_seconds=2.0,
        verifiability=TaskVerifiability.AUTO_VERIFIABLE,
        reversibility=TaskReversibility.MOSTLY_IRREVERSIBLE,
        contextuality=TaskContextuality.HIGH_CONTEXT,
        subjectivity=TaskSubjectivity.OBJECTIVE,
    ),
    TradingTaskType.ASSESS_RISK: TaskCharacteristics(
        complexity=TaskComplexity.HIGH,
        criticality=TaskCriticality.CRITICAL,
        uncertainty=TaskUncertainty.MODERATE,
        duration_seconds=3.0,
        verifiability=TaskVerifiability.EASILY_VERIFIABLE,
        reversibility=TaskReversibility.FULLY_REVERSIBLE,
        contextuality=TaskContextuality.HIGH_CONTEXT,
        subjectivity=TaskSubjectivity.MOSTLY_OBJECTIVE,
    ),
    TradingTaskType.EMERGENCY_EXIT: TaskCharacteristics(
        complexity=TaskComplexity.LOW,
        criticality=TaskCriticality.CRITICAL,
        uncertainty=TaskUncertainty.HIGH,
        duration_seconds=1.0,
        verifiability=TaskVerifiability.AUTO_VERIFIABLE,
        reversibility=TaskReversibility.IRREVERSIBLE,
        contextuality=TaskContextuality.HIGH_CONTEXT,
        subjectivity=TaskSubjectivity.OBJECTIVE,
    ),
    TradingTaskType.HUMAN_APPROVAL: TaskCharacteristics(
        complexity=TaskComplexity.MODERATE,
        criticality=TaskCriticality.CRITICAL,
        uncertainty=TaskUncertainty.LOW,
        duration_seconds=300.0,
        verifiability=TaskVerifiability.AUTO_VERIFIABLE,
        reversibility=TaskReversibility.FULLY_REVERSIBLE,
        contextuality=TaskContextuality.HIGH_CONTEXT,
        subjectivity=TaskSubjectivity.SUBJECTIVE,
    ),
    TradingTaskType.DETECT_REGIME: TaskCharacteristics(
        complexity=TaskComplexity.HIGH,
        criticality=TaskCriticality.HIGH,
        uncertainty=TaskUncertainty.HIGH,
        duration_seconds=5.0,
        verifiability=TaskVerifiability.HARD_TO_VERIFY,
        reversibility=TaskReversibility.FULLY_REVERSIBLE,
        contextuality=TaskContextuality.HIGH_CONTEXT,
        subjectivity=TaskSubjectivity.MIXED,
    ),
    TradingTaskType.VALIDATE_DATA: TaskCharacteristics(
        complexity=TaskComplexity.LOW,
        criticality=TaskCriticality.HIGH,
        uncertainty=TaskUncertainty.LOW,
        duration_seconds=1.0,
        verifiability=TaskVerifiability.AUTO_VERIFIABLE,
        reversibility=TaskReversibility.FULLY_REVERSIBLE,
        contextuality=TaskContextuality.LOW_CONTEXT,
        subjectivity=TaskSubjectivity.OBJECTIVE,
    ),
    TradingTaskType.CALCULATE_POSITION_SIZE: TaskCharacteristics(
        complexity=TaskComplexity.MODERATE,
        criticality=TaskCriticality.HIGH,
        uncertainty=TaskUncertainty.MODERATE,
        duration_seconds=2.0,
        verifiability=TaskVerifiability.AUTO_VERIFIABLE,
        reversibility=TaskReversibility.FULLY_REVERSIBLE,
        contextuality=TaskContextuality.HIGH_CONTEXT,
        subjectivity=TaskSubjectivity.OBJECTIVE,
    ),
    TradingTaskType.MONITOR_POSITION: TaskCharacteristics(
        complexity=TaskComplexity.MODERATE,
        criticality=TaskCriticality.HIGH,
        uncertainty=TaskUncertainty.MODERATE,
        duration_seconds=0.5,
        verifiability=TaskVerifiability.EASILY_VERIFIABLE,
        reversibility=TaskReversibility.FULLY_REVERSIBLE,
        contextuality=TaskContextuality.HIGH_CONTEXT,
        subjectivity=TaskSubjectivity.MOSTLY_OBJECTIVE,
    ),
}


def get_task_template(task_type: TradingTaskType) -> TaskCharacteristics:
    """Get default characteristics for a trading task type."""
    return TRADING_TASK_TEMPLATES.get(
        task_type,
        TaskCharacteristics()
    )


logger.info("Intelligent Delegation types loaded — based on DeepMind arXiv:2602.11865")

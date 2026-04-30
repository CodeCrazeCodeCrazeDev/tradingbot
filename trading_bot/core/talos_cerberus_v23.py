"""TALOS-CERBERUS v2.3 research evidence pipeline.

Trust-Augmented Live Operations System + Counterintelligent Evidence Reasoning
Browser Engine for Regulated Unified Synthesis.

This is deliberately narrow: legal-source registry, deterministic task policy,
taint-aware observations and claims, verification, scorecards, manual review,
insert-only memory, and a read-only AlphaAlgo research bridge. It cannot trade,
control capital, access broker credentials, or bypass AlphaAlgo gates.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlparse

from trading_bot.core.signal_counterintelligence import (
    AppendOnlyJsonlAuditLedger,
    ImmutableAuditLedger,
    IntelligenceRole,
    SourceLicenseStatus,
)


class TalosDecision(str, Enum):
    """Deterministic decision states used across TALOS-CERBERUS."""

    ALLOW_NAVIGATION = "allow_navigation"
    BLOCK_NAVIGATION = "block_navigation"
    QUARANTINE_TASK = "quarantine_task"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    POLICY_VIOLATION = "policy_violation"
    UNKNOWN = "unknown"
    ACCEPT_OBSERVATION = "accept_observation"
    REJECT_OBSERVATION = "reject_observation"
    QUARANTINE_OBSERVATION = "quarantine_observation"
    TRUSTED_RESEARCH_ONLY = "trusted_research_only"
    UNCERTAIN = "uncertain"
    CONTRADICTED = "contradicted"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TalosTaintStatus(str, Enum):
    """Concrete taint states."""

    TAINTED_EXTERNAL = "tainted_external"
    TAINTED_EXTRACTED = "tainted_extracted"
    TAINTED_TRANSFORMED = "tainted_transformed"
    VERIFIED_LOW_CONFIDENCE = "verified_low_confidence"
    VERIFIED_HIGH_CONFIDENCE = "verified_high_confidence"
    TRUSTED_RESEARCH_ONLY = "trusted_research_only"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


class ClaimType(str, Enum):
    """Supported claim families."""

    FACT = "fact"
    NUMERICAL_CLAIM = "numerical_claim"
    CAUSAL_CLAIM = "causal_claim"
    OPINION = "opinion"
    FORECAST = "forecast"
    ESTIMATE = "estimate"
    RUMOR = "rumor"
    LEGAL_CLAIM = "legal_claim"
    UNVERIFIABLE = "unverifiable"


class VerificationStatus(str, Enum):
    """Verification state for claims and observations."""

    UNVERIFIED = "unverified"
    PASSED = "passed"
    FAILED = "failed"
    CONTRADICTED = "contradicted"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class RiskIfWrong(str, Enum):
    """Impact of a wrong claim."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ArgusActionType(str, Enum):
    """Allowed Argus browser action grammar."""

    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_TABLE = "extract_table"
    SCREENSHOT = "screenshot"
    DOWNLOAD = "download"
    WAIT_FOR = "wait_for"
    STOP = "stop"


class TalosDeploymentStage(str, Enum):
    """Deployment maturity gates."""

    MVP = "mvp"
    PRODUCTION_RESEARCH_TOOL = "production_research_tool"
    INSTITUTIONAL_CAPITAL_INFLUENCING_TOOL = "institutional_capital_influencing_tool"


@dataclass
class LegalSourceRecord:
    """Legal-source registry entry."""

    source_id: str
    domain: str
    owner: str
    source_type: str
    allowed_usage: str
    license_status: SourceLicenseStatus
    license_start: float
    license_expiry: Optional[float]
    automation_allowed: bool
    extraction_allowed: bool
    storage_allowed: bool
    redistribution_allowed: bool
    citation_required: bool
    robots_policy_status: str
    rate_limit_policy: str
    legal_review_status: str
    last_reviewed_at: float
    compliance_notes: List[str] = field(default_factory=list)
    terms_fingerprint: str = ""

    def __post_init__(self) -> None:
        self.domain = _domain(self.domain)
        self.license_status = _coerce_license(self.license_status)
        if not self.terms_fingerprint:
            payload = f"{self.domain}:{self.owner}:{self.allowed_usage}:{self.license_status.value}"
            self.terms_fingerprint = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def license_active(self, now: Optional[float] = None) -> bool:
        now = now or time.time()
        if self.license_status in {
            SourceLicenseStatus.UNKNOWN,
            SourceLicenseStatus.PRIVATE,
            SourceLicenseStatus.STOLEN,
            SourceLicenseStatus.CONFIDENTIAL,
            SourceLicenseStatus.MATERIAL_NONPUBLIC,
        }:
            return False
        return self.license_expiry is None or self.license_expiry > now

    def rights_clear(self) -> bool:
        return (
            self.automation_allowed
            and self.extraction_allowed
            and self.storage_allowed
            and self.legal_review_status == "approved"
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["license_status"] = self.license_status.value
        return data


class LegalSourceRegistry:
    """Allowlisted source registry with explicit automation/storage rights."""

    def __init__(self, records: Optional[Sequence[LegalSourceRecord]] = None):
        self.records_by_domain: Dict[str, LegalSourceRecord] = {}
        self.records_by_id: Dict[str, LegalSourceRecord] = {}
        for record in records or []:
            self.register(record)

    def register(self, record: LegalSourceRecord) -> None:
        self.records_by_domain[record.domain] = record
        self.records_by_id[record.source_id] = record

    def get_by_url(self, url: str) -> Optional[LegalSourceRecord]:
        return self.records_by_domain.get(_domain(url))

    def get(self, source_id: str) -> Optional[LegalSourceRecord]:
        return self.records_by_id.get(source_id)

    def revoke(self, source_id: str, reason: str) -> None:
        record = self.records_by_id[source_id]
        record.license_status = SourceLicenseStatus.UNKNOWN
        record.license_expiry = time.time() - 1
        record.compliance_notes.append(f"revoked: {reason}")


@dataclass
class TaskDossier:
    """Signed deterministic task-governor output."""

    task_id: str
    user_id: str
    user_role: str
    task: str
    requested_urls: List[str]
    allowed_tools: List[str]
    browser_step_budget: int
    cost_budget: float
    latency_budget_ms: int
    source_call_budget: int
    risk_classification: str
    manual_review_required: bool
    approval_triggers: List[str]
    policy_decision: TalosDecision
    issued_at_utc: str
    signature: str = ""

    def signing_payload(self) -> Dict[str, Any]:
        data = asdict(self)
        data["policy_decision"] = self.policy_decision.value
        data.pop("signature", None)
        return data

    def sign(self, secret: str) -> "TaskDossier":
        payload = json.dumps(self.signing_payload(), sort_keys=True, default=str).encode("utf-8")
        self.signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return self

    def verify(self, secret: str) -> bool:
        payload = json.dumps(self.signing_payload(), sort_keys=True, default=str).encode("utf-8")
        expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return bool(self.signature) and hmac.compare_digest(self.signature, expected)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["policy_decision"] = self.policy_decision.value
        return data


class PolicyRouter:
    """Deterministic policy router and task governor."""

    mnpi_terms = {"mnpi", "insider", "confidential", "private", "leaked", "nonpublic", "non-public"}

    def __init__(
        self,
        registry: LegalSourceRegistry,
        audit_ledger: Optional[ImmutableAuditLedger] = None,
        signing_secret: str = "talos-cerberus-task-dossier",
    ):
        self.registry = registry
        self.audit_ledger = audit_ledger or AppendOnlyJsonlAuditLedger()
        self.signing_secret = signing_secret

    def issue_task_dossier(
        self,
        user_id: str,
        user_role: str,
        task: str,
        requested_urls: Sequence[str],
        intended_use: str = "research",
        browser_step_budget: int = 12,
        cost_budget: float = 2.50,
        latency_budget_ms: int = 30000,
        source_call_budget: int = 4,
    ) -> TaskDossier:
        triggers: List[str] = []
        task_lower = task.lower()
        risk = "low"
        if any(term in task_lower for term in self.mnpi_terms):
            triggers.append("task mentions private/confidential/MNPI-like data")
            risk = "critical"
        if "capital" in intended_use or "signal" in intended_use:
            triggers.append("evidence intended to support a capital-influencing signal")
            risk = "high" if risk != "critical" else risk
        for url in requested_urls:
            record = self.registry.get_by_url(url)
            if record is None:
                triggers.append(f"source not in allowlist: {_domain(url)}")
                continue
            if not record.license_active():
                triggers.append(f"source license unknown or expired: {record.source_id}")
            if not record.rights_clear():
                triggers.append(f"source automation/storage rights unclear: {record.source_id}")
            if "changed terms" in " ".join(record.compliance_notes).lower():
                triggers.append(f"source terms changed recently: {record.source_id}")
        role = user_role.lower()
        if role in {"execution_operator", "production_runtime"}:
            triggers.append("execution roles cannot request TALOS browser research tasks")
            risk = "critical"
        decision = TalosDecision.MANUAL_REVIEW_REQUIRED if triggers else TalosDecision.ALLOW_NAVIGATION
        dossier = TaskDossier(
            task_id=_digest(f"{user_id}:{task}:{time.time():.6f}")[:16],
            user_id=user_id,
            user_role=user_role,
            task=task,
            requested_urls=list(requested_urls),
            allowed_tools=["argus_browser", "deterministic_extractor", "financial_verifier"],
            browser_step_budget=browser_step_budget,
            cost_budget=cost_budget,
            latency_budget_ms=latency_budget_ms,
            source_call_budget=source_call_budget,
            risk_classification=risk,
            manual_review_required=bool(triggers),
            approval_triggers=triggers,
            policy_decision=decision,
            issued_at_utc=_utc_now(),
        ).sign(self.signing_secret)
        self.audit_ledger.append("talos_task_dossier", dossier.to_dict(), actor=user_id, action="issue_task_dossier")
        return dossier


@dataclass
class SourceValidationDecision:
    """Pre/post source-validation output."""

    validation_id: str
    decision: TalosDecision
    source_id: str
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.value
        return data


class PreNavigationSourceValidator:
    """Runs before any browser navigation."""

    def __init__(self, registry: LegalSourceRegistry):
        self.registry = registry

    def validate(self, url: str, usage_category: str = "research") -> SourceValidationDecision:
        reasons: List[str] = []
        record = self.registry.get_by_url(url)
        if record is None:
            return SourceValidationDecision(_digest(f"pre:{url}:{time.time()}")[:16], TalosDecision.MANUAL_REVIEW_REQUIRED, "", ["domain is not allowlisted"])
        if not record.license_active():
            reasons.append("license is unknown or expired")
        if not record.automation_allowed:
            reasons.append("automation is not allowed")
        if not record.storage_allowed:
            reasons.append("storage is not allowed")
        if record.robots_policy_status not in {"allowed", "not_applicable"}:
            reasons.append("robots policy does not allow collection")
        if usage_category not in record.allowed_usage and record.allowed_usage != "research":
            reasons.append("usage category is outside approved source policy")
        if reasons:
            decision = TalosDecision.MANUAL_REVIEW_REQUIRED if any("unknown" in reason or "not allowed" in reason for reason in reasons) else TalosDecision.BLOCK_NAVIGATION
        else:
            decision = TalosDecision.ALLOW_NAVIGATION
        return SourceValidationDecision(_digest(f"pre:{url}:{time.time()}")[:16], decision, record.source_id, reasons)


class PostCaptureSourceValidator:
    """Runs after browser collection to catch redirects, drift, unsafe content, and revoked rights."""

    forbidden_instruction_terms = {"ignore previous", "system prompt", "developer message", "send email", "place order", "broker login"}

    def __init__(self, registry: LegalSourceRegistry):
        self.registry = registry

    def validate(self, observation: "ObservationPackage") -> SourceValidationDecision:
        reasons: List[str] = []
        record = self.registry.get(observation.source_id)
        final_domain = observation.source_domain
        if record is None:
            reasons.append("source missing from registry after capture")
        else:
            if final_domain != record.domain:
                reasons.append("domain drift detected")
            if not record.license_active():
                reasons.append("license revoked or expired mid-session")
            if not record.automation_allowed or not record.storage_allowed:
                reasons.append("automation/storage rights no longer valid")
        if not observation.content_hash:
            reasons.append("content hash missing")
        if observation.extraction_method == "browser_screenshot" and not observation.screenshot_hash:
            reasons.append("screenshot hash missing")
        if observation.forbidden_instructions_detected:
            reasons.append("forbidden page instructions detected")
        if reasons:
            decision = TalosDecision.POLICY_VIOLATION if any("revoked" in reason or "drift" in reason for reason in reasons) else TalosDecision.QUARANTINE_OBSERVATION
        else:
            decision = TalosDecision.ACCEPT_OBSERVATION
        return SourceValidationDecision(_digest(f"post:{observation.observation_id}:{time.time()}")[:16], decision, observation.source_id, reasons)


@dataclass
class ArgusAction:
    """One approved Playwright action descriptor."""

    action_type: ArgusActionType
    target: str
    value: str = ""
    timeout_ms: int = 5000
    policy_approved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["action_type"] = self.action_type.value
        return data


@dataclass
class ArgusActionResult:
    """Validation result for one Argus action."""

    accepted: bool
    action: ArgusAction
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accepted": self.accepted,
            "action": self.action.to_dict(),
            "reasons": list(self.reasons),
        }


@dataclass
class ArgusSessionReport:
    """Strict browser-session report emitted by Argus."""

    session_id: str
    task_id: str
    accepted: bool
    action_results: List[ArgusActionResult]
    browser_steps_used: int
    content_hashes: List[str]
    screenshot_hashes: List[str]
    blocked_reasons: List[str]
    audit_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "accepted": self.accepted,
            "action_results": [item.to_dict() for item in self.action_results],
            "browser_steps_used": self.browser_steps_used,
            "content_hashes": list(self.content_hashes),
            "screenshot_hashes": list(self.screenshot_hashes),
            "blocked_reasons": list(self.blocked_reasons),
            "audit_digest": self.audit_digest,
        }


class ArgusCollector:
    """Playwright/Chromium adapter guardrail; it validates action grammar before execution.

    The MVP unit-test implementation does not drive a live browser. Production wires
    these approved descriptors to Playwright inside an ephemeral sandbox.
    """

    forbidden_targets = {"broker", "api", "internal", "credential", "password", "email", "message"}

    def __init__(
        self,
        registry: LegalSourceRegistry,
        audit_ledger: Optional[ImmutableAuditLedger] = None,
    ):
        self.registry = registry
        self.audit_ledger = audit_ledger or AppendOnlyJsonlAuditLedger()

    def validate_action(
        self,
        action: ArgusAction,
        dossier: TaskDossier,
        approved_fields: Optional[Sequence[str]] = None,
    ) -> ArgusActionResult:
        approved_fields = list(approved_fields or [])
        reasons: List[str] = []
        target_lower = action.target.lower()
        if any(token in target_lower for token in self.forbidden_targets):
            reasons.append("target is outside TALOS research browser boundary")
        if action.action_type == ArgusActionType.NAVIGATE:
            if self.registry.get_by_url(action.target) is None:
                reasons.append("navigation target is not allowlisted")
        if action.action_type == ArgusActionType.TYPE and action.target not in approved_fields:
            reasons.append("typing is only allowed into policy-approved fields")
        if action.action_type == ArgusActionType.DOWNLOAD and not action.policy_approved:
            reasons.append("download requires explicit policy approval")
        if action.action_type in {ArgusActionType.CLICK, ArgusActionType.TYPE} and not action.policy_approved:
            reasons.append("interactive action requires selector visibility/text/bounding-box validation")
        if "javascript:" in action.target.lower():
            reasons.append("arbitrary JavaScript execution is forbidden")
        if action.action_type.value not in dossier.allowed_tools and action.action_type not in {
            ArgusActionType.NAVIGATE,
            ArgusActionType.CLICK,
            ArgusActionType.TYPE,
            ArgusActionType.SCROLL,
            ArgusActionType.EXTRACT_TEXT,
            ArgusActionType.EXTRACT_TABLE,
            ArgusActionType.SCREENSHOT,
            ArgusActionType.DOWNLOAD,
            ArgusActionType.WAIT_FOR,
            ArgusActionType.STOP,
        }:
            reasons.append("action is outside allowed grammar")
        return ArgusActionResult(not reasons, action, reasons)

    def dry_run(
        self,
        dossier: TaskDossier,
        actions: Sequence[ArgusAction],
        approved_fields: Optional[Sequence[str]] = None,
    ) -> ArgusSessionReport:
        results = [self.validate_action(action, dossier, approved_fields) for action in actions]
        blocked = [reason for result in results for reason in result.reasons]
        if len(actions) > dossier.browser_step_budget:
            blocked.append("browser step budget exceeded")
        content_hashes = [_digest(item.action.target) for item in results if item.action.action_type in {ArgusActionType.EXTRACT_TEXT, ArgusActionType.EXTRACT_TABLE}]
        screenshot_hashes = [_digest(item.action.target) for item in results if item.action.action_type == ArgusActionType.SCREENSHOT]
        session_id = _digest(f"argus:{dossier.task_id}:{time.time()}")[:16]
        audit = self.audit_ledger.append(
            "talos_argus_session_dry_run",
            {
                "task_id": dossier.task_id,
                "actions": [action.to_dict() for action in actions],
                "blocked_reasons": blocked,
            },
            actor="argus",
            action="dry_run",
        )
        return ArgusSessionReport(
            session_id=session_id,
            task_id=dossier.task_id,
            accepted=not blocked,
            action_results=results,
            browser_steps_used=len(actions),
            content_hashes=content_hashes,
            screenshot_hashes=screenshot_hashes,
            blocked_reasons=blocked,
            audit_digest=audit.record_hash,
        )


@dataclass
class ObservationPackage:
    """Tainted browser observation package."""

    observation_id: str
    task_id: str
    source_id: str
    agent_id: str
    source_url_hash: str
    source_domain: str
    redirect_chain: List[str]
    source_type: str
    content_hash: str
    screenshot_hash: str
    retrieved_at_utc: str
    published_at_utc: Optional[str]
    license_status: SourceLicenseStatus
    license_fingerprint: str
    automation_allowed: bool
    storage_allowed: bool
    compliance_score: float
    source_reliability_score: float
    raw_extract_ref: str
    extraction_method: str
    taint_status: TalosTaintStatus
    taint_origin: str
    pre_navigation_validation_id: str
    post_capture_validation_id: str
    browser_session_id: str
    forbidden_instructions_detected: bool
    audit_event_id: str
    cost_used: float
    latency_ms: int
    browser_steps_used: int
    raw_text: str = ""
    taint_transforms: List[str] = field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    allowed_usage: str = "research"

    @classmethod
    def from_raw_capture(
        cls,
        task_id: str,
        source: LegalSourceRecord,
        url: str,
        raw_text: str,
        pre_validation_id: str,
        agent_id: str = "argus",
        browser_session_id: str = "",
        extraction_method: str = "extract_text",
        published_at_utc: Optional[str] = None,
        redirect_chain: Optional[Sequence[str]] = None,
        screenshot_bytes: bytes = b"",
        cost_used: float = 0.0,
        latency_ms: int = 0,
        browser_steps_used: int = 1,
    ) -> "ObservationPackage":
        forbidden = _contains_forbidden_instruction(raw_text)
        content_hash = _digest(raw_text)
        screenshot_hash = hashlib.sha256(screenshot_bytes).hexdigest() if screenshot_bytes else _digest(f"screenshot:{url}:{content_hash}")
        observation_id = _digest(f"{task_id}:{url}:{content_hash}")[:16]
        return cls(
            observation_id=observation_id,
            task_id=task_id,
            source_id=source.source_id,
            agent_id=agent_id,
            source_url_hash=_digest(url),
            source_domain=_domain(url),
            redirect_chain=list(redirect_chain or [url]),
            source_type=source.source_type,
            content_hash=content_hash,
            screenshot_hash=screenshot_hash,
            retrieved_at_utc=_utc_now(),
            published_at_utc=published_at_utc,
            license_status=source.license_status,
            license_fingerprint=source.terms_fingerprint,
            automation_allowed=source.automation_allowed,
            storage_allowed=source.storage_allowed,
            compliance_score=1.0 if source.rights_clear() else 0.4,
            source_reliability_score=0.85,
            raw_extract_ref=f"postgres-large-object:{content_hash[:16]}",
            extraction_method=extraction_method,
            taint_status=TalosTaintStatus.TAINTED_EXTERNAL,
            taint_origin="browser",
            pre_navigation_validation_id=pre_validation_id,
            post_capture_validation_id="",
            browser_session_id=browser_session_id or _digest(f"session:{task_id}")[:16],
            forbidden_instructions_detected=forbidden,
            audit_event_id="",
            cost_used=cost_used,
            latency_ms=latency_ms,
            browser_steps_used=browser_steps_used,
            raw_text=raw_text,
            allowed_usage=source.allowed_usage,
        )

    @staticmethod
    def json_schema() -> Dict[str, Any]:
        return _schema_for(
            "ObservationPackage",
            [
                "observation_id",
                "task_id",
                "source_id",
                "agent_id",
                "source_url_hash",
                "source_domain",
                "redirect_chain",
                "source_type",
                "content_hash",
                "screenshot_hash",
                "retrieved_at_utc",
                "published_at_utc",
                "license_status",
                "license_fingerprint",
                "automation_allowed",
                "storage_allowed",
                "compliance_score",
                "source_reliability_score",
                "raw_extract_ref",
                "extraction_method",
                "taint_status",
                "taint_origin",
                "pre_navigation_validation_id",
                "post_capture_validation_id",
                "browser_session_id",
                "forbidden_instructions_detected",
                "audit_event_id",
                "cost_used",
                "latency_ms",
                "browser_steps_used",
            ],
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["license_status"] = self.license_status.value
        data["taint_status"] = self.taint_status.value
        data["verification_status"] = self.verification_status.value
        return data


@dataclass
class ClaimPackage:
    """Atomic claim package."""

    claim_id: str
    claim_text: str
    claim_type: ClaimType
    entity: str
    metric: Optional[str]
    value: Optional[Any]
    currency: Optional[str]
    unit: Optional[str]
    time_period: Optional[str]
    source_observation_id: str
    evidence_span: str
    quote_span: str
    extraction_method: str
    confidence_score: float
    source_grade: str
    extracted_at_utc: str
    published_at_utc: Optional[str]
    license_status: SourceLicenseStatus
    contradiction_status: str
    uncertainty_type: str
    evidence_gaps: List[str]
    allowed_usage: str
    risk_if_wrong: RiskIfWrong
    trading_allowed: bool
    requires_signal_validation: bool
    taint_status: TalosTaintStatus
    taint_origin: str = "claim_extractor"
    taint_transforms: List[str] = field(default_factory=lambda: ["claim_extraction"])
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    @staticmethod
    def json_schema() -> Dict[str, Any]:
        return _schema_for(
            "ClaimPackage",
            [
                "claim_id",
                "claim_text",
                "claim_type",
                "entity",
                "metric",
                "value",
                "currency",
                "unit",
                "time_period",
                "source_observation_id",
                "evidence_span",
                "quote_span",
                "extraction_method",
                "confidence_score",
                "source_grade",
                "extracted_at_utc",
                "published_at_utc",
                "license_status",
                "contradiction_status",
                "uncertainty_type",
                "evidence_gaps",
                "allowed_usage",
                "risk_if_wrong",
                "trading_allowed",
                "requires_signal_validation",
                "taint_status",
            ],
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["claim_type"] = self.claim_type.value
        data["license_status"] = self.license_status.value
        data["risk_if_wrong"] = self.risk_if_wrong.value
        data["taint_status"] = self.taint_status.value
        data["verification_status"] = self.verification_status.value
        return data


class ClaimExtractor:
    """Deterministic-first claim extraction."""

    number_pattern = re.compile(r"(?P<label>[A-Za-z][A-Za-z\s-]{2,40})\s+(?:was|were|of|:)?\s*\$?(?P<value>-?\d+(?:\.\d+)?)\s*(?P<unit>billion|million|percent|%|bps)?", re.IGNORECASE)

    def extract(self, observation: ObservationPackage) -> List[ClaimPackage]:
        text = observation.raw_text
        claims: List[ClaimPackage] = []
        for match in self.number_pattern.finditer(text):
            label = " ".join(match.group("label").split())[-64:]
            value = float(match.group("value"))
            unit = match.group("unit")
            span = match.group(0)
            claim_id = _digest(f"{observation.observation_id}:{span}")[:16]
            claims.append(
                ClaimPackage(
                    claim_id=claim_id,
                    claim_text=span,
                    claim_type=ClaimType.NUMERICAL_CLAIM,
                    entity=observation.source_domain,
                    metric=label.lower(),
                    value=value,
                    currency="USD" if "$" in span else None,
                    unit=unit,
                    time_period=None,
                    source_observation_id=observation.observation_id,
                    evidence_span=span,
                    quote_span=span,
                    extraction_method="regex_numeric",
                    confidence_score=0.82,
                    source_grade="B",
                    extracted_at_utc=_utc_now(),
                    published_at_utc=observation.published_at_utc,
                    license_status=observation.license_status,
                    contradiction_status="not_checked",
                    uncertainty_type="parser_span",
                    evidence_gaps=[],
                    allowed_usage=observation.allowed_usage,
                    risk_if_wrong=RiskIfWrong.MEDIUM,
                    trading_allowed=False,
                    requires_signal_validation=True,
                    taint_status=TalosTaintStatus.TAINTED_EXTRACTED,
                )
            )
        if not claims and text.strip():
            span = text.strip()[:280]
            claims.append(
                ClaimPackage(
                    claim_id=_digest(f"{observation.observation_id}:{span}")[:16],
                    claim_text=span,
                    claim_type=ClaimType.FACT,
                    entity=observation.source_domain,
                    metric=None,
                    value=None,
                    currency=None,
                    unit=None,
                    time_period=None,
                    source_observation_id=observation.observation_id,
                    evidence_span=span,
                    quote_span=span,
                    extraction_method="deterministic_sentence",
                    confidence_score=0.60,
                    source_grade="B",
                    extracted_at_utc=_utc_now(),
                    published_at_utc=observation.published_at_utc,
                    license_status=observation.license_status,
                    contradiction_status="not_checked",
                    uncertainty_type="narrative",
                    evidence_gaps=["numeric parser did not find structured value"],
                    allowed_usage=observation.allowed_usage,
                    risk_if_wrong=RiskIfWrong.MEDIUM,
                    trading_allowed=False,
                    requires_signal_validation=True,
                    taint_status=TalosTaintStatus.TAINTED_EXTRACTED,
                )
            )
        return claims


@dataclass
class VerificationResult:
    """Claim verification result."""

    claim_id: str
    status: VerificationStatus
    checks: Dict[str, bool]
    issues: List[str]
    script_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


class FinancialVerifier:
    """Deterministic verifier for spans, timestamps, and basic financial math."""

    def verify(self, claim: ClaimPackage, observation: ObservationPackage) -> VerificationResult:
        checks: Dict[str, bool] = {
            "span_present": bool(claim.evidence_span and claim.evidence_span in observation.raw_text),
            "license_active": claim.license_status not in {SourceLicenseStatus.UNKNOWN, SourceLicenseStatus.PRIVATE, SourceLicenseStatus.STOLEN, SourceLicenseStatus.CONFIDENTIAL, SourceLicenseStatus.MATERIAL_NONPUBLIC},
            "timestamp_present": bool(observation.retrieved_at_utc),
            "numeric_value_parseable": claim.claim_type != ClaimType.NUMERICAL_CLAIM or isinstance(claim.value, (int, float)),
        }
        issues = [name for name, passed in checks.items() if not passed]
        status = VerificationStatus.PASSED if not issues else VerificationStatus.FAILED
        script_hash = _digest("financial_verifier:v2.3:span-license-timestamp-numeric")
        claim.verification_status = status
        if status == VerificationStatus.PASSED:
            claim.taint_status = TalosTaintStatus.VERIFIED_HIGH_CONFIDENCE if claim.confidence_score >= 0.80 else TalosTaintStatus.VERIFIED_LOW_CONFIDENCE
        return VerificationResult(claim.claim_id, status, checks, issues, script_hash)


class AdversarialReviewer:
    """MVP adversarial reviewer."""

    prompt_injection_terms = {"ignore previous", "system prompt", "developer message", "hidden instruction", "jailbreak"}
    fake_domain_terms = {"sec-gov", "edgar-sec", "filings-sec"}

    def review(self, claim: ClaimPackage, observation: ObservationPackage) -> List[str]:
        text = f"{claim.claim_text} {observation.raw_text}".lower()
        failures: List[str] = []
        if any(term in text for term in self.prompt_injection_terms):
            failures.append("prompt injection string detected")
        if any(term in observation.source_domain for term in self.fake_domain_terms):
            failures.append("fake domain pattern detected")
        if observation.source_domain not in [_domain(url) for url in observation.redirect_chain]:
            failures.append("URL drift detected")
        if not claim.evidence_span:
            failures.append("missing evidence span")
        if claim.evidence_span and claim.evidence_span not in observation.raw_text:
            failures.append("extraction hallucination suspected")
        return failures


@dataclass
class MentatVerificationAttempt:
    """One bounded verification loop attempt."""

    iteration: int
    verification: VerificationResult
    adversarial_failures: List[str]
    action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "verification": self.verification.to_dict(),
            "adversarial_failures": list(self.adversarial_failures),
            "action": self.action,
        }


@dataclass
class MentatVerificationReport:
    """Mentat verifier output; deterministic checks first, bounded critique last."""

    claim_id: str
    final_status: VerificationStatus
    attempts: List[MentatVerificationAttempt]
    final_claim: ClaimPackage
    adversarial_failures: List[str]
    decision: TalosDecision

    def final_verification(self) -> VerificationResult:
        return self.attempts[-1].verification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "final_status": self.final_status.value,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "final_claim": self.final_claim.to_dict(),
            "adversarial_failures": list(self.adversarial_failures),
            "decision": self.decision.value,
        }


class MentatVerifier:
    """Verifier loop, not a black-box model."""

    def __init__(
        self,
        financial_verifier: Optional[FinancialVerifier] = None,
        adversarial_reviewer: Optional[AdversarialReviewer] = None,
        max_iterations: int = 3,
    ):
        self.financial_verifier = financial_verifier or FinancialVerifier()
        self.adversarial_reviewer = adversarial_reviewer or AdversarialReviewer()
        self.max_iterations = max(1, min(3, max_iterations))

    def verify(self, claim: ClaimPackage, observation: ObservationPackage) -> MentatVerificationReport:
        attempts: List[MentatVerificationAttempt] = []
        current = claim
        adversarial_failures: List[str] = []
        decision = TalosDecision.UNCERTAIN
        for iteration in range(self.max_iterations):
            verification = self.financial_verifier.verify(current, observation)
            adversarial_failures = self.adversarial_reviewer.review(current, observation)
            if adversarial_failures:
                attempts.append(MentatVerificationAttempt(iteration, verification, adversarial_failures, "quarantine_adversarial_failure"))
                current.verification_status = VerificationStatus.FAILED
                decision = TalosDecision.QUARANTINED
                break
            if verification.status == VerificationStatus.PASSED:
                attempts.append(MentatVerificationAttempt(iteration, verification, [], "accept_deterministic_verification"))
                decision = TalosDecision.TRUSTED_RESEARCH_ONLY
                break
            if "span_present" in verification.issues and current.quote_span:
                current.evidence_span = current.quote_span
                attempts.append(MentatVerificationAttempt(iteration, verification, [], "revise_span_from_quote"))
                continue
            attempts.append(MentatVerificationAttempt(iteration, verification, [], "restart_extraction_or_manual_review"))
            decision = TalosDecision.MANUAL_REVIEW_REQUIRED
            break
        else:
            decision = TalosDecision.MANUAL_REVIEW_REQUIRED
        final_status = attempts[-1].verification.status if attempts else VerificationStatus.UNVERIFIED
        return MentatVerificationReport(
            claim_id=current.claim_id,
            final_status=final_status,
            attempts=attempts,
            final_claim=current,
            adversarial_failures=adversarial_failures,
            decision=decision,
        )


@dataclass
class EvidenceScorecardResult:
    """Evidence scorecard output."""

    claim_id: str
    decision: TalosDecision
    score: float
    hard_blocks: List[str]
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.value
        return data


class EvidenceScorecard:
    """Hard overrides plus weighted evidence-quality scoring."""

    def score(
        self,
        claim: ClaimPackage,
        observation: ObservationPackage,
        verification: VerificationResult,
        adversarial_failures: Sequence[str],
        unresolved_contradiction: bool = False,
    ) -> EvidenceScorecardResult:
        hard_blocks: List[str] = []
        if claim.license_status in {SourceLicenseStatus.UNKNOWN, SourceLicenseStatus.PRIVATE, SourceLicenseStatus.STOLEN, SourceLicenseStatus.CONFIDENTIAL, SourceLicenseStatus.MATERIAL_NONPUBLIC}:
            hard_blocks.append("unknown or forbidden source rights")
        if not claim.evidence_span:
            hard_blocks.append("missing evidence span")
        if unresolved_contradiction:
            hard_blocks.append("unresolved contradiction")
        if observation.compliance_score < 0.80:
            hard_blocks.append("low compliance score")
        if adversarial_failures:
            hard_blocks.extend(adversarial_failures)
        if hard_blocks:
            return EvidenceScorecardResult(claim.claim_id, TalosDecision.QUARANTINED, 0.0, hard_blocks, hard_blocks)
        score = (
            observation.source_reliability_score * 0.20
            + observation.compliance_score * 0.20
            + claim.confidence_score * 0.20
            + (1.0 if verification.status == VerificationStatus.PASSED else 0.0) * 0.25
            + (1.0 if claim.taint_status in {TalosTaintStatus.VERIFIED_LOW_CONFIDENCE, TalosTaintStatus.VERIFIED_HIGH_CONFIDENCE} else 0.0) * 0.15
        )
        if score >= 0.82:
            decision = TalosDecision.TRUSTED_RESEARCH_ONLY
            claim.taint_status = TalosTaintStatus.TRUSTED_RESEARCH_ONLY
        elif score >= 0.60:
            decision = TalosDecision.UNCERTAIN
        else:
            decision = TalosDecision.QUARANTINED
        return EvidenceScorecardResult(claim.claim_id, decision, round(score, 4), [], [f"score={score:.4f}"])


@dataclass
class ManualReviewItem:
    """Human review queue item."""

    queue_id: str
    reason_for_review: str
    source_id: str
    claim_id: str
    risk_if_wrong: RiskIfWrong
    evidence_span: str
    reviewer_role_required: str
    sla: str
    decision_options: List[str]
    reviewer_id: str = ""
    decision_timestamp: str = ""
    audit_event_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_if_wrong"] = self.risk_if_wrong.value
        return data


class ManualReviewQueue:
    """Simple manual review queue."""

    def __init__(self):
        self.items: Dict[str, ManualReviewItem] = {}

    def enqueue(self, reason: str, source_id: str, claim: ClaimPackage, reviewer_role_required: str = "compliance_officer") -> ManualReviewItem:
        item = ManualReviewItem(
            queue_id=_digest(f"{reason}:{claim.claim_id}:{time.time()}")[:16],
            reason_for_review=reason,
            source_id=source_id,
            claim_id=claim.claim_id,
            risk_if_wrong=claim.risk_if_wrong,
            evidence_span=claim.evidence_span,
            reviewer_role_required=reviewer_role_required,
            sla="2 business days" if claim.risk_if_wrong in {RiskIfWrong.LOW, RiskIfWrong.MEDIUM} else "4 business hours",
            decision_options=["approve", "reject", "quarantine", "request_more_evidence", "legal_review", "compliance_review"],
        )
        self.items[item.queue_id] = item
        return item


class TalosMemoryStore:
    """Insert-only PostgreSQL-shaped in-memory MVP store."""

    def __init__(self):
        self.trusted_evidence: List[Dict[str, Any]] = []
        self.quarantine_evidence: List[Dict[str, Any]] = []
        self.failure_memory: List[Dict[str, Any]] = []
        self.audit_log: List[Dict[str, Any]] = []

    def insert(self, schema: str, row: Mapping[str, Any]) -> None:
        payload = dict(row)
        payload["inserted_at_utc"] = _utc_now()
        payload["row_version_hash"] = _digest(payload)
        if schema == "trusted_evidence":
            self.trusted_evidence.append(payload)
        elif schema == "quarantine_evidence":
            self.quarantine_evidence.append(payload)
        elif schema == "failure_memory":
            self.failure_memory.append(payload)
        elif schema == "audit_log":
            self.audit_log.append(payload)
        else:
            raise ValueError(f"unknown TALOS memory schema: {schema}")


class Archivist:
    """Only service allowed to write TALOS memory."""

    def __init__(self, store: TalosMemoryStore, audit_ledger: Optional[ImmutableAuditLedger] = None):
        self.store = store
        self.audit_ledger = audit_ledger or AppendOnlyJsonlAuditLedger()

    def write(self, claim: ClaimPackage, observation: ObservationPackage, scorecard: EvidenceScorecardResult) -> str:
        row = {
            "claim": claim.to_dict(),
            "observation_id": observation.observation_id,
            "source_id": observation.source_id,
            "evidence_span": claim.evidence_span,
            "license_status": claim.license_status.value,
            "taint_status": claim.taint_status.value,
            "taint_transforms": list(claim.taint_transforms),
            "scorecard": scorecard.to_dict(),
        }
        if scorecard.decision == TalosDecision.TRUSTED_RESEARCH_ONLY:
            schema = "trusted_evidence"
        elif scorecard.decision in {TalosDecision.QUARANTINED, TalosDecision.UNCERTAIN, TalosDecision.CONTRADICTED}:
            schema = "quarantine_evidence"
        else:
            schema = "failure_memory"
        self.store.insert(schema, row)
        audit = self.audit_ledger.append("talos_graph_write_event", {"schema": schema, "row": row}, actor="archivist", action="write_memory")
        return audit.record_hash


class AlphaAlgoResearchBridge:
    """Read-only research API. Execution roles are blocked."""

    blocked_roles = {"execution_operator", "production_runtime"}

    def __init__(self, store: TalosMemoryStore, audit_ledger: Optional[ImmutableAuditLedger] = None):
        self.store = store
        self.audit_ledger = audit_ledger or AppendOnlyJsonlAuditLedger()

    def search_evidence(self, query: str, user_role: str) -> List[Dict[str, Any]]:
        if user_role.lower() in self.blocked_roles:
            self.audit_ledger.append("talos_bridge_blocked", {"query": query, "role": user_role}, actor=user_role, action="search_evidence")
            raise PermissionError("execution systems cannot query TALOS evidence bridge")
        query_lower = query.lower()
        results = [
            row for row in self.store.trusted_evidence
            if query_lower in json.dumps(row, sort_keys=True).lower()
        ]
        self.audit_ledger.append("talos_bridge_query", {"query": query, "role": user_role, "result_count": len(results)}, actor=user_role, action="search_evidence")
        return results


@dataclass
class TalosKPIReport:
    """Evidence-quality and AlphaAlgo-impact KPI snapshot."""

    citation_traceability_rate: float
    numeric_extraction_accuracy: Optional[float]
    unsupported_claim_rate: float
    contradiction_detection_rate: Optional[float]
    source_provenance_completeness: float
    license_policy_compliance_rate: float
    manual_review_resolution_time: Optional[float]
    evidence_rejection_rate: float
    evidence_quarantine_rate: float
    weak_signal_promotion_rate_before: Optional[float] = None
    weak_signal_promotion_rate_after: Optional[float] = None
    bad_signal_rejection_rate: Optional[float] = None
    evidence_supported_hypothesis_rate: Optional[float] = None
    paper_trade_quality_delta: Optional[float] = None
    false_signal_reduction: Optional[float] = None
    research_time_to_evidence: Optional[float] = None
    cost_per_valid_claim: Optional[float] = None
    latency_per_task: Optional[float] = None

    def weak_signal_promotion_reduced(self) -> bool:
        if self.weak_signal_promotion_rate_before is None or self.weak_signal_promotion_rate_after is None:
            return False
        return self.weak_signal_promotion_rate_after < self.weak_signal_promotion_rate_before

    def evidence_quality_improved(self) -> bool:
        return (
            self.citation_traceability_rate >= 0.95
            and self.source_provenance_completeness >= 0.95
            and self.license_policy_compliance_rate >= 1.0
            and self.unsupported_claim_rate <= 0.10
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkGateReport:
    """MVP/production/institutional benchmark gate result."""

    stage: TalosDeploymentStage
    accepted: bool
    reasons: List[str]
    kpis: TalosKPIReport
    kill_or_downgrade: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["stage"] = self.stage.value
        data["kpis"] = self.kpis.to_dict()
        return data


class TalosObservability:
    """Computes MVP observability metrics from pipeline reports and memory."""

    def snapshot(
        self,
        reports: Sequence[TalosPipelineReport],
        store: TalosMemoryStore,
        weak_signal_promotion_rate_before: Optional[float] = None,
        weak_signal_promotion_rate_after: Optional[float] = None,
    ) -> TalosKPIReport:
        claims = [claim for report in reports for claim in report.claims]
        scorecards = [score for report in reports for score in report.scorecards]
        observations = [report.observation for report in reports]
        total_claims = len(claims) or 1
        span_claims = sum(1 for claim in claims if claim.evidence_span)
        unsupported = sum(1 for report in reports for verification in report.verification_results if verification.status == VerificationStatus.FAILED)
        trusted = len(store.trusted_evidence)
        quarantined = len(store.quarantine_evidence)
        rejected = len(store.failure_memory)
        total_memory = trusted + quarantined + rejected or 1
        license_compliant = sum(1 for observation in observations if observation.license_status not in {SourceLicenseStatus.UNKNOWN, SourceLicenseStatus.PRIVATE, SourceLicenseStatus.STOLEN, SourceLicenseStatus.CONFIDENTIAL, SourceLicenseStatus.MATERIAL_NONPUBLIC})
        total_observations = len(observations) or 1
        latency = sum(report.observation.latency_ms for report in reports) / (len(reports) or 1)
        cost = sum(report.observation.cost_used for report in reports)
        return TalosKPIReport(
            citation_traceability_rate=span_claims / total_claims,
            numeric_extraction_accuracy=None,
            unsupported_claim_rate=unsupported / total_claims,
            contradiction_detection_rate=None,
            source_provenance_completeness=sum(1 for observation in observations if observation.source_id and observation.content_hash) / total_observations,
            license_policy_compliance_rate=license_compliant / total_observations,
            manual_review_resolution_time=None,
            evidence_rejection_rate=rejected / total_memory,
            evidence_quarantine_rate=quarantined / total_memory,
            weak_signal_promotion_rate_before=weak_signal_promotion_rate_before,
            weak_signal_promotion_rate_after=weak_signal_promotion_rate_after,
            research_time_to_evidence=latency,
            cost_per_valid_claim=cost / max(1, trusted),
            latency_per_task=latency,
        )


class BenchmarkGate:
    """Benchmark-gated deployment without fake precision."""

    def evaluate_mvp(
        self,
        kpis: TalosKPIReport,
        labelled_filing_test_set_exists: bool,
        numeric_extraction_accuracy: Optional[float],
        critical_policy_bypasses: int,
        audit_logging_rate: float,
        execution_isolation_rate: float,
        days_elapsed: int = 0,
    ) -> BenchmarkGateReport:
        reasons: List[str] = []
        if not labelled_filing_test_set_exists:
            reasons.append("labelled filing test set is required before benchmark claims")
        if numeric_extraction_accuracy is None or numeric_extraction_accuracy < 0.90:
            reasons.append("numeric extraction accuracy must be measured and >= 90%")
        if kpis.citation_traceability_rate < 0.95:
            reasons.append("citation traceability must be >= 95%")
        if audit_logging_rate < 1.0:
            reasons.append("audit logging must be 100%")
        if execution_isolation_rate < 1.0:
            reasons.append("execution isolation must be 100%")
        if critical_policy_bypasses > 0:
            reasons.append("critical policy bypasses must be zero")
        if kpis.weak_signal_promotion_rate_before is None or kpis.weak_signal_promotion_rate_after is None:
            reasons.append("before/after weak-signal promotion must be measured")
        kill_or_downgrade = days_elapsed >= 90 and (
            not kpis.weak_signal_promotion_reduced()
            or not kpis.evidence_quality_improved()
        )
        if kill_or_downgrade:
            reasons.append("90-day value gate failed: downgrade or kill TALOS")
        return BenchmarkGateReport(
            stage=TalosDeploymentStage.MVP,
            accepted=not reasons,
            reasons=reasons,
            kpis=kpis,
            kill_or_downgrade=kill_or_downgrade,
        )


@dataclass
class TalosPipelineReport:
    """End-to-end TALOS-CERBERUS MVP run report."""

    dossier: TaskDossier
    pre_navigation: SourceValidationDecision
    post_capture: SourceValidationDecision
    observation: ObservationPackage
    claims: List[ClaimPackage]
    verification_results: List[VerificationResult]
    mentat_reports: List[MentatVerificationReport]
    scorecards: List[EvidenceScorecardResult]
    manual_review_items: List[ManualReviewItem]
    audit_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dossier": self.dossier.to_dict(),
            "pre_navigation": self.pre_navigation.to_dict(),
            "post_capture": self.post_capture.to_dict(),
            "observation": self.observation.to_dict(),
            "claims": [claim.to_dict() for claim in self.claims],
            "verification_results": [result.to_dict() for result in self.verification_results],
            "mentat_reports": [report.to_dict() for report in self.mentat_reports],
            "scorecards": [score.to_dict() for score in self.scorecards],
            "manual_review_items": [item.to_dict() for item in self.manual_review_items],
            "audit_digest": self.audit_digest,
        }


class TalosCerberusAI:
    """MVP TALOS-CERBERUS research AI orchestrator."""

    def __init__(
        self,
        registry: LegalSourceRegistry,
        audit_ledger: Optional[ImmutableAuditLedger] = None,
        store: Optional[TalosMemoryStore] = None,
    ):
        self.audit_ledger = audit_ledger or AppendOnlyJsonlAuditLedger()
        self.registry = registry
        self.policy_router = PolicyRouter(registry, self.audit_ledger)
        self.pre_validator = PreNavigationSourceValidator(registry)
        self.post_validator = PostCaptureSourceValidator(registry)
        self.extractor = ClaimExtractor()
        self.financial_verifier = FinancialVerifier()
        self.adversarial_reviewer = AdversarialReviewer()
        self.mentat = MentatVerifier(self.financial_verifier, self.adversarial_reviewer)
        self.scorecard = EvidenceScorecard()
        self.review_queue = ManualReviewQueue()
        self.store = store or TalosMemoryStore()
        self.archivist = Archivist(self.store, self.audit_ledger)
        self.bridge = AlphaAlgoResearchBridge(self.store, self.audit_ledger)
        self.observability = TalosObservability()
        self.benchmark_gate = BenchmarkGate()

    def process_static_capture(
        self,
        user_id: str,
        user_role: str,
        task: str,
        url: str,
        raw_text: str,
        intended_use: str = "research",
    ) -> TalosPipelineReport:
        dossier = self.policy_router.issue_task_dossier(user_id, user_role, task, [url], intended_use=intended_use)
        pre = self.pre_validator.validate(url)
        source = self.registry.get_by_url(url)
        if source is None:
            raise ValueError("cannot capture from source outside legal registry")
        observation = ObservationPackage.from_raw_capture(dossier.task_id, source, url, raw_text, pre.validation_id)
        post = self.post_validator.validate(observation)
        observation.post_capture_validation_id = post.validation_id
        claims = self.extractor.extract(observation)
        verification_results: List[VerificationResult] = []
        mentat_reports: List[MentatVerificationReport] = []
        scorecards: List[EvidenceScorecardResult] = []
        manual_items: List[ManualReviewItem] = []
        for claim in claims:
            mentat_report = self.mentat.verify(claim, observation)
            mentat_reports.append(mentat_report)
            verification = mentat_report.final_verification()
            verification_results.append(verification)
            score = self.scorecard.score(claim, observation, verification, mentat_report.adversarial_failures)
            scorecards.append(score)
            if score.decision in {TalosDecision.MANUAL_REVIEW_REQUIRED, TalosDecision.QUARANTINED, TalosDecision.UNCERTAIN} or dossier.manual_review_required or post.decision != TalosDecision.ACCEPT_OBSERVATION:
                reason = "; ".join(dossier.approval_triggers + post.reasons + score.reasons)
                manual_items.append(self.review_queue.enqueue(reason or "manual review required", source.source_id, claim))
            self.archivist.write(claim, observation, score)
        audit = self.audit_ledger.append(
            "talos_cerberus_pipeline_run",
            {
                "task_id": dossier.task_id,
                "observation_id": observation.observation_id,
                "claim_count": len(claims),
                "trusted_count": sum(1 for item in scorecards if item.decision == TalosDecision.TRUSTED_RESEARCH_ONLY),
                "manual_review_count": len(manual_items),
            },
            actor=user_id,
            action="process_static_capture",
        )
        return TalosPipelineReport(dossier, pre, post, observation, claims, verification_results, mentat_reports, scorecards, manual_items, audit.record_hash)


def default_edgar_source(now: Optional[float] = None) -> LegalSourceRecord:
    """Default MVP source family: SEC EDGAR public filings."""

    now = now or time.time()
    return LegalSourceRecord(
        source_id="sec-edgar",
        domain="sec.gov",
        owner="U.S. Securities and Exchange Commission",
        source_type="public_filing",
        allowed_usage="research",
        license_status=SourceLicenseStatus.PUBLIC,
        license_start=now,
        license_expiry=None,
        automation_allowed=True,
        extraction_allowed=True,
        storage_allowed=True,
        redistribution_allowed=False,
        citation_required=True,
        robots_policy_status="allowed",
        rate_limit_policy="respect SEC fair-access rate limits",
        legal_review_status="approved",
        last_reviewed_at=now,
        compliance_notes=["MVP allowlist source; public does not imply redistribution rights"],
    )


def _domain(value: str) -> str:
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return parsed.netloc.lower()


def _coerce_license(value: Any) -> SourceLicenseStatus:
    if isinstance(value, SourceLicenseStatus):
        return value
    try:
        return SourceLicenseStatus(str(value))
    except ValueError:
        return SourceLicenseStatus.UNKNOWN


def _contains_forbidden_instruction(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in ("ignore previous", "system prompt", "developer message", "send email", "place order", "broker login"))


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _schema_for(title: str, required: Sequence[str]) -> Dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        "type": "object",
        "required": list(required),
        "properties": {name: {} for name in required},
        "additionalProperties": True,
    }


__all__ = [
    "AdversarialReviewer",
    "AlphaAlgoResearchBridge",
    "ArgusAction",
    "ArgusActionResult",
    "ArgusActionType",
    "ArgusCollector",
    "ArgusSessionReport",
    "Archivist",
    "BenchmarkGate",
    "BenchmarkGateReport",
    "ClaimExtractor",
    "ClaimPackage",
    "ClaimType",
    "EvidenceScorecard",
    "EvidenceScorecardResult",
    "FinancialVerifier",
    "LegalSourceRecord",
    "LegalSourceRegistry",
    "ManualReviewItem",
    "ManualReviewQueue",
    "ObservationPackage",
    "PolicyRouter",
    "PostCaptureSourceValidator",
    "PreNavigationSourceValidator",
    "RiskIfWrong",
    "SourceValidationDecision",
    "TalosCerberusAI",
    "TalosDecision",
    "TalosDeploymentStage",
    "TalosKPIReport",
    "TalosMemoryStore",
    "TalosObservability",
    "TalosPipelineReport",
    "TalosTaintStatus",
    "TaskDossier",
    "MentatVerificationAttempt",
    "MentatVerificationReport",
    "MentatVerifier",
    "VerificationResult",
    "VerificationStatus",
    "default_edgar_source",
]

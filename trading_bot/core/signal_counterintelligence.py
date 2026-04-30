"""Signal counterintelligence and intelligence-directorate controls.

This module makes AlphaAlgo treat financial signals like intelligence claims:
every source must be legal, provenance-backed, timestamped, compartmentalized,
and adversarially challenged before it can influence a decision.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class DataSourceCategory(str, Enum):
    """Collection-layer source families."""

    MARKET = "market"
    MACRO = "macro"
    NEWS_FILINGS = "news_filings"
    SENTIMENT = "sentiment"
    BROKER_TELEMETRY = "broker_telemetry"
    ALTERNATIVE = "alternative"
    INTERNAL_GENERATED = "internal_generated"


class SourceLicenseStatus(str, Enum):
    """Allowed and forbidden source-license states."""

    PUBLIC = "public"
    LICENSED = "licensed"
    PERMISSIONED = "permissioned"
    INTERNAL_GENERATED = "internal_generated"
    UNKNOWN = "unknown"
    PRIVATE = "private"
    STOLEN = "stolen"
    CONFIDENTIAL = "confidential"
    MATERIAL_NONPUBLIC = "material_nonpublic"


class CounterintelligenceMode(str, Enum):
    """How counterintelligence verdicts are enforced."""

    RESEARCH_ONLY = "research_only"
    ADVISORY = "advisory"
    HARD_GATE = "hard_gate"


class IntelligenceZone(str, Enum):
    """Software-enforced zero-trust zones for the model lifecycle."""

    RESEARCH = "research"
    STAGING = "staging"
    PRODUCTION = "production"


class IntelligenceCompartment(str, Enum):
    """Need-to-know environments for AlphaAlgo intelligence work."""

    RESEARCH = "research"
    EXECUTION = "execution"
    PRODUCTION_MODEL = "production_model"
    GOVERNANCE = "governance"
    AUDIT = "audit"


class IntelligenceRole(str, Enum):
    """Role-based access personas."""

    RESEARCH_ANALYST = "research_analyst"
    EXECUTION_OPERATOR = "execution_operator"
    RISK_OFFICER = "risk_officer"
    GOVERNANCE_APPROVER = "governance_approver"
    VALIDATION_OFFICER = "validation_officer"
    COMPLIANCE_OFFICER = "compliance_officer"
    RED_TEAM = "red_team"
    STAGING_SYSTEM = "staging_system"
    PRODUCTION_RUNTIME = "production_runtime"
    AUDITOR = "auditor"
    AI_ENGINEERING_AGENT = "ai_engineering_agent"


class LicenseLedgerStatus(str, Enum):
    """Central compliance-ledger license states."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class KillSwitchLevel(str, Enum):
    """Graduated kill-switch actions; flattening is the last resort."""

    NONE = "none"
    STOP_NEW_ORDERS = "stop_new_orders"
    CANCEL_OPEN_ORDERS = "cancel_open_orders"
    REDUCE_EXPOSURE = "reduce_exposure"
    HEDGE_EXPOSURE = "hedge_exposure"
    EMERGENCY_FLATTEN = "emergency_flatten"


class SignalAttackVector(str, Enum):
    """Counterintelligence attacks against a signal or source."""

    ILLEGAL_SOURCE = "illegal_source"
    MISSING_PROVENANCE = "missing_provenance"
    TIMESTAMP_ANOMALY = "timestamp_anomaly"
    LOW_COMPLIANCE = "low_compliance"
    SOURCE_RELIABILITY_WEAKNESS = "source_reliability_weakness"
    MATERIAL_NONPUBLIC_INFORMATION = "material_nonpublic_information"
    DATA_LEAKAGE = "data_leakage"
    OVERFITTING = "overfitting"
    ADVERSARIAL_MARKET_BEHAVIOR = "adversarial_market_behavior"
    WEAK_CLAIM = "weak_claim"
    COMPARTMENT_BREACH = "compartment_breach"
    PROMOTION_GATE_FAILURE = "promotion_gate_failure"
    REGIME_FRAGILITY = "regime_fragility"
    CAUSAL_PLAUSIBILITY_FAILURE = "causal_plausibility_failure"
    CROWDING_CAPACITY_RISK = "crowding_capacity_risk"
    EXECUTION_STRESS_FAILURE = "execution_stress_failure"


class IntelligenceDecision(str, Enum):
    """Final decision state for a signal or directorate run."""

    ACCEPT = "accept"
    QUARANTINE = "quarantine"
    REJECT = "reject"


@dataclass
class CollectionTask:
    """One legal collection request in the intelligence collection layer."""

    collector_id: str
    category: DataSourceCategory
    source_name: str
    source_uri: str
    license_status: SourceLicenseStatus
    permission_basis: str
    purpose: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["category"] = self.category.value
        data["license_status"] = self.license_status.value
        return data


@dataclass
class CollectionPlan:
    """Legal/licensed-only collection manifest."""

    mission_id: str
    approved_tasks: List[CollectionTask]
    rejected_tasks: List[CollectionTask]
    required_categories: List[DataSourceCategory]
    compliance_notes: List[str] = field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return not self.rejected_tasks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "approved_tasks": [task.to_dict() for task in self.approved_tasks],
            "rejected_tasks": [task.to_dict() for task in self.rejected_tasks],
            "required_categories": [category.value for category in self.required_categories],
            "compliance_notes": list(self.compliance_notes),
            "accepted": self.accepted,
        }


@dataclass
class MissionRequirement:
    """Requirements and mission layer for a tradable question."""

    mission_id: str
    tradable_question: str
    edge_hypothesis: str
    objective_functions: List[str]
    risk_budget: float
    allowed_assets: List[str]
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DataSourceProvenance:
    """Required provenance envelope for every data source."""

    source_id: str
    name: str
    category: DataSourceCategory
    license_status: SourceLicenseStatus
    license_name: str
    permission_basis: str
    collected_at: float
    observed_at: float
    uri: str = ""
    provenance_chain: List[str] = field(default_factory=list)
    compliance_score: float = 1.0
    reliability_score: float = 1.0
    contains_mnpi: bool = False
    confidentiality_flags: List[str] = field(default_factory=list)
    source_timestamp: float = 0.0
    license_id: str = ""
    license_expires_at: Optional[float] = None
    symbol_universe: List[str] = field(default_factory=list)
    data_vendor: str = ""
    ingestion_time: float = 0.0
    adjustment_method: str = "raw"
    survivorship_bias_status: str = "not_applicable"
    lookahead_risk_status: str = "point_in_time"
    quality_score: float = 1.0

    def __post_init__(self) -> None:
        self.category = _coerce_data_category(self.category)
        self.license_status = _coerce_source_license(self.license_status)
        if not self.source_timestamp:
            self.source_timestamp = self.observed_at
        if not self.ingestion_time:
            self.ingestion_time = self.collected_at
        if not self.data_vendor:
            self.data_vendor = self.name
        if not self.symbol_universe:
            self.symbol_universe = ["UNKNOWN"]
        if not self.adjustment_method:
            self.adjustment_method = "raw"
        if not self.survivorship_bias_status:
            self.survivorship_bias_status = "not_applicable"
        if not self.lookahead_risk_status:
            self.lookahead_risk_status = "point_in_time"
        if self.quality_score <= 0:
            self.quality_score = min(self.compliance_score, self.reliability_score)
        if not self.license_id:
            license_payload = f"{self.name}:{self.license_name}:{self.permission_basis}:{self.license_status.value}"
            self.license_id = hashlib.sha256(license_payload.encode("utf-8")).hexdigest()[:16]

    def lineage_hash(self) -> str:
        category = _coerce_data_category(self.category)
        license_status = _coerce_source_license(self.license_status)
        payload = json.dumps(
            {
                "source_id": self.source_id,
                "name": self.name,
                "category": category.value,
                "license_status": license_status.value,
                "license_name": self.license_name,
                "permission_basis": self.permission_basis,
                "collected_at": round(self.collected_at, 6),
                "observed_at": round(self.observed_at, 6),
                "source_timestamp": round(self.source_timestamp, 6),
                "license_id": self.license_id,
                "license_expires_at": self.license_expires_at,
                "uri": self.uri,
                "provenance_chain": self.provenance_chain,
                "symbol_universe": self.symbol_universe,
                "data_vendor": self.data_vendor,
                "ingestion_time": round(self.ingestion_time, 6),
                "adjustment_method": self.adjustment_method,
                "survivorship_bias_status": self.survivorship_bias_status,
                "lookahead_risk_status": self.lookahead_risk_status,
                "quality_score": round(self.quality_score, 6),
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["category"] = _coerce_data_category(self.category).value
        data["license_status"] = _coerce_source_license(self.license_status).value
        data["lineage_hash"] = self.lineage_hash()
        return data


@dataclass
class SignalIntelligencePackage:
    """Canonical intelligence inputs derived from a raw signal object."""

    mission: MissionRequirement
    signal: SignalClaim
    sources: List[DataSourceProvenance]
    evidence: List[IntelligenceEvidence]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission": self.mission.to_dict(),
            "signal": self.signal.to_dict(),
            "sources": [source.to_dict() for source in self.sources],
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass
class SourceValidationReport:
    """Source validation layer output."""

    source_id: str
    accepted: bool
    decision: IntelligenceDecision
    compliance_score: float
    reliability_score: float
    findings: List[str] = field(default_factory=list)
    lineage_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.value
        return data


@dataclass
class IntelligenceEvidence:
    """Evidence unit attached to a signal claim."""

    evidence_id: str
    source_id: str
    claim: str
    observed_at: float
    content_hash: str
    features: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SignalClaim:
    """Signal claim entering counterintelligence review."""

    signal_id: str
    asset: str
    thesis: str
    horizon: str
    confidence: float
    source_ids: List[str]
    evidence_ids: List[str]
    generated_at: float = field(default_factory=time.time)
    features: Dict[str, float] = field(default_factory=dict)
    proposed_action: str = "research_only"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CounterintelligenceFinding:
    """One adversarial finding against a source, signal, or access path."""

    finding_id: str
    vector: SignalAttackVector
    severity: str
    description: str
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["vector"] = self.vector.value
        return data


@dataclass
class SignalCounterintelligenceReport:
    """Counterintelligence verdict for one signal."""

    signal_id: str
    decision: IntelligenceDecision
    accepted: bool
    findings: List[CounterintelligenceFinding]
    source_reports: List[SourceValidationReport]
    compliance_score: float
    reliability_score: float
    blocked_reasons: List[str]
    audit_digest: str
    mode: CounterintelligenceMode = CounterintelligenceMode.HARD_GATE
    execution_allowed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "decision": self.decision.value,
            "accepted": self.accepted,
            "mode": _coerce_counterintelligence_mode(self.mode).value,
            "execution_allowed": self.execution_allowed,
            "findings": [finding.to_dict() for finding in self.findings],
            "source_reports": [report.to_dict() for report in self.source_reports],
            "compliance_score": self.compliance_score,
            "reliability_score": self.reliability_score,
            "blocked_reasons": list(self.blocked_reasons),
            "audit_digest": self.audit_digest,
        }


@dataclass
class AccessDecision:
    """Compartmentalized access-control decision."""

    accepted: bool
    role: IntelligenceRole
    compartment: IntelligenceCompartment
    action: str
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["role"] = self.role.value
        data["compartment"] = self.compartment.value
        return data


@dataclass
class ImmutableAuditRecord:
    """Append-only audit record with hash-chain integrity."""

    record_id: str
    event_type: str
    payload_hash: str
    previous_hash: str
    timestamp: float
    record_hash: str
    actor: str = "system"
    action: str = ""
    artifact_hash: str = ""
    input_hash: str = ""
    output_hash: str = ""
    signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SignedModelArtifact:
    """Read-only signed model artifact for production model access."""

    artifact_id: str
    model_name: str
    model_digest: str
    signer: str
    signature: str
    created_at: float
    read_only: bool = True
    approved_for_production: bool = False
    author: str = ""
    data_manifest_hash: str = ""
    build_digest: str = ""
    deterministic_build: bool = True
    staging_signer: str = ""
    staging_signature: str = ""
    validation_signer: str = ""
    validation_signature: str = ""
    counter_signatures: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LicenseLedgerEvent:
    """Full-fidelity compliance ledger event with a tamper-evident hash chain."""

    event_id: str
    event_type: str
    license_id: str
    timestamp: float
    actor: str
    payload: Dict[str, Any]
    previous_event_hash: str
    event_hash: str
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DataLicenseRecord:
    """Current license state reconstructed from the compliance ledger."""

    license_id: str
    source: str
    data_vendor: str
    license_status: SourceLicenseStatus
    permission_basis: str
    issued_at: float
    expires_at: Optional[float]
    status: LicenseLedgerStatus = LicenseLedgerStatus.ACTIVE
    revoked_at: Optional[float] = None
    terms_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["license_status"] = _coerce_source_license(self.license_status).value
        data["status"] = _coerce_license_ledger_status(self.status).value
        return data


@dataclass
class DataPassport:
    """Cryptographically signed lineage passport attached by the sidecar proxy."""

    passport_id: str
    dataset_id: str
    source: str
    source_timestamp: float
    license: str
    license_id: str
    symbol_universe: List[str]
    data_vendor: str
    ingestion_time: float
    adjustment_method: str
    survivorship_bias_status: str
    lookahead_risk_status: str
    quality_score: float
    lineage_hash: str
    issued_at: float
    issuer: str = "alphaalgo-sidecar"
    signature: str = ""

    def signing_payload(self) -> Dict[str, Any]:
        data = asdict(self)
        data.pop("signature", None)
        return data

    def sign(self, signing_secret: str) -> "DataPassport":
        payload = json.dumps(self.signing_payload(), sort_keys=True, default=str).encode("utf-8")
        self.signature = hmac.new(signing_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return self

    def verify(self, signing_secret: str) -> bool:
        payload = json.dumps(self.signing_payload(), sort_keys=True, default=str).encode("utf-8")
        expected = hmac.new(signing_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return bool(self.signature) and hmac.compare_digest(self.signature, expected)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DataPassportValidationResult:
    """Sidecar verification result for an inbound message."""

    accepted: bool
    passport_id: str = ""
    lineage_hash: str = ""
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ZonePolicyReport:
    """Zero-trust zone policy evaluation."""

    accepted: bool
    zone: IntelligenceZone
    role: IntelligenceRole
    action: str
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["zone"] = _coerce_intelligence_zone(self.zone).value
        data["role"] = self.role.value
        return data


@dataclass
class PromotionGateChecklist:
    """Mandatory adversarial promotion checklist for live signals."""

    hypothesis_written: bool = False
    data_manifest_attached: bool = False
    leakage_test_passed: bool = False
    walk_forward_passed: bool = False
    transaction_costs_included: bool = False
    slippage_modeled: bool = False
    capacity_estimated: bool = False
    regime_behavior_known: bool = False
    risk_impact_approved: bool = False
    paper_trading_passed: bool = False

    @property
    def accepted(self) -> bool:
        return all(asdict(self).values())

    @property
    def missing_items(self) -> List[str]:
        return [key for key, value in asdict(self).items() if not value]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["accepted"] = self.accepted
        data["missing_items"] = self.missing_items
        return data


@dataclass
class ModelPromotionReport:
    """Result of one model-promotion chain action."""

    accepted: bool
    decision: IntelligenceDecision
    artifact: SignedModelArtifact
    checklist: PromotionGateChecklist
    reasons: List[str]
    audit_record: ImmutableAuditRecord

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accepted": self.accepted,
            "decision": self.decision.value,
            "artifact": self.artifact.to_dict(),
            "checklist": self.checklist.to_dict(),
            "reasons": list(self.reasons),
            "audit_record": self.audit_record.to_dict(),
        }


@dataclass
class SignalHealthReport:
    """Real-time signal health, attribution, and decay status."""

    signal_id: str
    status: IntelligenceDecision
    staging_test_sharpe: float
    out_of_sample_sharpe: float
    pnl_attribution: float
    risk_attribution: float
    regime: str
    decay_detected: bool
    kill_switch_level: KillSwitchLevel
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["kill_switch_level"] = _coerce_kill_switch_level(self.kill_switch_level).value
        return data


@dataclass
class AnalysisCellOutput:
    """Output from one intelligence analysis cell."""

    cell_name: str
    summary: str
    confidence: float
    evidence_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FusionKnowledgeReport:
    """Fusion and knowledge-layer artifact."""

    entity_resolution: Dict[str, Any]
    cross_asset_links: Dict[str, float]
    event_graph: List[Dict[str, str]]
    regime_memory: Dict[str, Any]
    strategy_evidence_graph: Dict[str, Any]
    graph_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeedbackEvaluationReport:
    """Feedback and evaluation layer."""

    forecast_accuracy: float
    pnl_attribution: float
    slippage_attribution: float
    regime_specific_performance: float
    strategy_decay_score: float
    strategy_decay_detected: bool
    staging_test_sharpe: float = 0.0
    out_of_sample_sharpe: float = 0.0
    signal_health_status: IntelligenceDecision = IntelligenceDecision.ACCEPT
    kill_switch_level: KillSwitchLevel = KillSwitchLevel.NONE
    quarantine_recommended: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["signal_health_status"] = self.signal_health_status.value
        data["kill_switch_level"] = _coerce_kill_switch_level(self.kill_switch_level).value
        return data


@dataclass
class DecisionGovernanceReport:
    """Decision governance system output."""

    signal_validator_passed: bool
    risk_gatekeeper_passed: bool
    capital_allocation_judge_passed: bool
    kill_switch_active: bool
    audit_logger_enabled: bool
    decision: IntelligenceDecision
    reasons: List[str] = field(default_factory=list)
    kill_switch_level: KillSwitchLevel = KillSwitchLevel.NONE

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.value
        data["kill_switch_level"] = _coerce_kill_switch_level(self.kill_switch_level).value
        return data


@dataclass
class DirectorateRunReport:
    """End-to-end AlphaAlgo Intelligence Directorate report."""

    mission: MissionRequirement
    collection_plan: CollectionPlan
    source_reports: List[SourceValidationReport]
    model_artifact_report: Optional[AccessDecision]
    fusion_report: FusionKnowledgeReport
    fusion_graph: Dict[str, Any]
    analysis_cells: List[AnalysisCellOutput]
    counterintelligence: SignalCounterintelligenceReport
    governance_report: DecisionGovernanceReport
    governance_decision: IntelligenceDecision
    compartment_report: AccessDecision
    feedback_report: FeedbackEvaluationReport
    feedback_metrics: Dict[str, float]
    audit_record: ImmutableAuditRecord

    def to_execution_metadata(self) -> Dict[str, Any]:
        return {
            "decision": self.counterintelligence.decision.value,
            "counterintelligence_decision": self.counterintelligence.decision.value,
            "governance_decision": self.governance_decision.value,
            "governance_decision_id": self.audit_record.record_id,
            "audit_digest": self.counterintelligence.audit_digest,
            "directorate_audit_digest": self.audit_record.record_hash,
            "source_lineage_hashes": [
                report.lineage_hash for report in self.source_reports if report.lineage_hash
            ],
            "signal_health_status": self.feedback_report.signal_health_status.value,
            "kill_switch_level": self.governance_report.kill_switch_level.value,
            "execution_allowed": (
                self.counterintelligence.execution_allowed
                and self.governance_decision == IntelligenceDecision.ACCEPT
                and self.feedback_report.signal_health_status == IntelligenceDecision.ACCEPT
                and self.governance_report.kill_switch_level == KillSwitchLevel.NONE
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission": self.mission.to_dict(),
            "collection_plan": self.collection_plan.to_dict(),
            "source_reports": [report.to_dict() for report in self.source_reports],
            "model_artifact_report": self.model_artifact_report.to_dict() if self.model_artifact_report else None,
            "fusion_report": self.fusion_report.to_dict(),
            "fusion_graph": dict(self.fusion_graph),
            "analysis_cells": [cell.to_dict() for cell in self.analysis_cells],
            "counterintelligence": self.counterintelligence.to_dict(),
            "governance_report": self.governance_report.to_dict(),
            "governance_decision": self.governance_decision.value,
            "compartment_report": self.compartment_report.to_dict(),
            "feedback_report": self.feedback_report.to_dict(),
            "feedback_metrics": dict(self.feedback_metrics),
            "audit_record": self.audit_record.to_dict(),
            "execution_metadata": self.to_execution_metadata(),
        }


class ImmutableAuditLedger:
    """Minimal immutable hash-chain audit ledger."""

    def __init__(self, signing_secret: str = "alphaalgo-audit-ledger"):
        self.signing_secret = signing_secret
        self.records: List[ImmutableAuditRecord] = []

    def append(
        self,
        event_type: str,
        payload: Dict[str, Any],
        actor: str = "system",
        action: str = "",
        artifact_hash: str = "",
        input_hash: str = "",
        output_hash: str = "",
    ) -> ImmutableAuditRecord:
        previous_hash = self.records[-1].record_hash if self.records else "GENESIS"
        payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        timestamp = time.time()
        record_id = hashlib.sha256(f"{event_type}:{payload_hash}:{timestamp:.6f}".encode("utf-8")).hexdigest()[:16]
        record_hash = hashlib.sha256(f"{record_id}:{payload_hash}:{previous_hash}:{timestamp:.6f}".encode("utf-8")).hexdigest()
        signature = self._sign_record_hash(record_hash)
        record = ImmutableAuditRecord(
            record_id,
            event_type,
            payload_hash,
            previous_hash,
            timestamp,
            record_hash,
            actor,
            action or event_type,
            artifact_hash,
            input_hash,
            output_hash,
            signature,
        )
        self.records.append(record)
        return record

    def verify(self) -> bool:
        previous = "GENESIS"
        for record in self.records:
            expected = hashlib.sha256(
                f"{record.record_id}:{record.payload_hash}:{previous}:{record.timestamp:.6f}".encode("utf-8")
            ).hexdigest()
            if record.previous_hash != previous or record.record_hash != expected:
                return False
            if record.signature and not hmac.compare_digest(record.signature, self._sign_record_hash(record.record_hash)):
                return False
            previous = record.record_hash
        return True

    def daily_digest(self) -> str:
        payload = [record.to_dict() for record in self.records]
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()

    def _sign_record_hash(self, record_hash: str) -> str:
        return hmac.new(
            self.signing_secret.encode("utf-8"),
            record_hash.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()


class AppendOnlyJsonlAuditLedger(ImmutableAuditLedger):
    """Append-only JSONL audit ledger with hash-chain verification."""

    def __init__(
        self,
        audit_dir: str = "audit_logs/intelligence_directorate",
        ledger_name: str = "directorate_audit.jsonl",
        signing_secret: str = "alphaalgo-audit-ledger",
    ):
        self.signing_secret = signing_secret
        self.audit_dir = Path(audit_dir)
        self.path = self.audit_dir / ledger_name
        self.records = self._read_records()

    def append(
        self,
        event_type: str,
        payload: Dict[str, Any],
        actor: str = "system",
        action: str = "",
        artifact_hash: str = "",
        input_hash: str = "",
        output_hash: str = "",
    ) -> ImmutableAuditRecord:
        previous_hash = self.records[-1].record_hash if self.records else "GENESIS"
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        timestamp = time.time()
        record_id = hashlib.sha256(
            f"{event_type}:{payload_hash}:{timestamp:.6f}".encode("utf-8")
        ).hexdigest()[:16]
        record_hash = hashlib.sha256(
            f"{record_id}:{payload_hash}:{previous_hash}:{timestamp:.6f}".encode("utf-8")
        ).hexdigest()
        signature = self._sign_record_hash(record_hash)
        record = ImmutableAuditRecord(
            record_id,
            event_type,
            payload_hash,
            previous_hash,
            timestamp,
            record_hash,
            actor,
            action or event_type,
            artifact_hash,
            input_hash,
            output_hash,
            signature,
        )
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
        self.records.append(record)
        return record

    def verify(self) -> bool:
        records = self._read_records() if self.path.exists() else list(self.records)
        previous = "GENESIS"
        for record in records:
            expected = hashlib.sha256(
                f"{record.record_id}:{record.payload_hash}:{previous}:{record.timestamp:.6f}".encode("utf-8")
            ).hexdigest()
            if record.previous_hash != previous or record.record_hash != expected:
                return False
            if record.signature and not hmac.compare_digest(record.signature, self._sign_record_hash(record.record_hash)):
                return False
            previous = record.record_hash
        return True

    def _read_records(self) -> List[ImmutableAuditRecord]:
        if not self.path.exists():
            return []
        records: List[ImmutableAuditRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                data = json.loads(text)
                records.append(
                    ImmutableAuditRecord(
                        record_id=str(data["record_id"]),
                        event_type=str(data["event_type"]),
                        payload_hash=str(data["payload_hash"]),
                        previous_hash=str(data["previous_hash"]),
                        timestamp=float(data["timestamp"]),
                        record_hash=str(data["record_hash"]),
                        actor=str(data.get("actor", "system")),
                        action=str(data.get("action", "")),
                        artifact_hash=str(data.get("artifact_hash", "")),
                        input_hash=str(data.get("input_hash", "")),
                        output_hash=str(data.get("output_hash", "")),
                        signature=str(data.get("signature", "")),
                    )
                )
        return records


class ComplianceLicenseLedger:
    """Central immutable license ledger with automatic expiry revocation."""

    allowed_license_states = {
        SourceLicenseStatus.PUBLIC,
        SourceLicenseStatus.LICENSED,
        SourceLicenseStatus.PERMISSIONED,
        SourceLicenseStatus.INTERNAL_GENERATED,
    }

    def __init__(
        self,
        audit_dir: str = "audit_logs/intelligence_directorate",
        ledger_name: str = "compliance_license_ledger.jsonl",
        signing_secret: str = "alphaalgo-compliance-ledger",
    ):
        self.audit_dir = Path(audit_dir)
        self.path = self.audit_dir / ledger_name
        self.signing_secret = signing_secret
        self.events: List[LicenseLedgerEvent] = self._read_events()
        self.licenses: Dict[str, DataLicenseRecord] = {}
        self._rebuild_state()

    def register_license(
        self,
        source: str,
        license_status: SourceLicenseStatus,
        permission_basis: str,
        data_vendor: str = "",
        expires_at: Optional[float] = None,
        license_id: str = "",
        actor: str = "compliance",
        issued_at: Optional[float] = None,
        terms_hash: str = "",
    ) -> DataLicenseRecord:
        license_status = _coerce_source_license(license_status)
        issued = issued_at or time.time()
        if not license_id:
            license_id = hashlib.sha256(
                f"{source}:{data_vendor}:{license_status.value}:{permission_basis}".encode("utf-8")
            ).hexdigest()[:16]
        status = (
            LicenseLedgerStatus.ACTIVE
            if license_status in self.allowed_license_states and (expires_at is None or expires_at > time.time())
            else LicenseLedgerStatus.EXPIRED
        )
        record = DataLicenseRecord(
            license_id=license_id,
            source=source,
            data_vendor=data_vendor or source,
            license_status=license_status,
            permission_basis=permission_basis,
            issued_at=issued,
            expires_at=expires_at,
            status=status,
            terms_hash=terms_hash,
        )
        self._append_event("license_registered", license_id, actor, record.to_dict())
        self.licenses[license_id] = record
        if status == LicenseLedgerStatus.EXPIRED:
            self.revoke_license(license_id, "license expired before registration", actor=actor, expired=True)
        return self.licenses[license_id]

    def revoke_license(
        self,
        license_id: str,
        reason: str,
        actor: str = "compliance",
        expired: bool = False,
    ) -> DataLicenseRecord:
        existing = self.licenses.get(license_id)
        if existing is None:
            existing = DataLicenseRecord(
                license_id=license_id,
                source="unknown",
                data_vendor="unknown",
                license_status=SourceLicenseStatus.UNKNOWN,
                permission_basis="",
                issued_at=time.time(),
                expires_at=None,
                status=LicenseLedgerStatus.REVOKED,
            )
        existing.status = LicenseLedgerStatus.EXPIRED if expired else LicenseLedgerStatus.REVOKED
        existing.revoked_at = time.time()
        self.licenses[license_id] = existing
        self._append_event(
            "license_expired" if expired else "license_revoked",
            license_id,
            actor,
            {"license_id": license_id, "reason": reason, "status": existing.status.value},
        )
        return existing

    def is_license_active(self, license_id: str, now: Optional[float] = None) -> Tuple[bool, List[str]]:
        now = now or time.time()
        record = self.licenses.get(license_id)
        if record is None:
            return False, [f"license {license_id} is not registered in compliance ledger"]
        status = _coerce_license_ledger_status(record.status)
        if record.expires_at is not None and record.expires_at <= now and status == LicenseLedgerStatus.ACTIVE:
            self.revoke_license(license_id, "license expired", expired=True)
            status = LicenseLedgerStatus.EXPIRED
        reasons: List[str] = []
        if status != LicenseLedgerStatus.ACTIVE:
            reasons.append(f"license {license_id} is {status.value}")
        if _coerce_source_license(record.license_status) not in self.allowed_license_states:
            reasons.append(f"license {license_id} has forbidden source status {record.license_status.value}")
        return not reasons, reasons

    def verify(self) -> bool:
        previous = "GENESIS"
        for event in self._read_events() if self.path.exists() else self.events:
            expected_hash = self._event_hash(
                event.event_id,
                event.event_type,
                event.license_id,
                event.timestamp,
                event.actor,
                event.payload,
                previous,
            )
            if event.previous_event_hash != previous or event.event_hash != expected_hash:
                return False
            if not hmac.compare_digest(event.signature, self._sign_event_hash(event.event_hash)):
                return False
            previous = event.event_hash
        return True

    def _append_event(
        self,
        event_type: str,
        license_id: str,
        actor: str,
        payload: Dict[str, Any],
    ) -> LicenseLedgerEvent:
        previous_hash = self.events[-1].event_hash if self.events else "GENESIS"
        timestamp = time.time()
        event_id = hashlib.sha256(f"{event_type}:{license_id}:{timestamp:.6f}".encode("utf-8")).hexdigest()[:16]
        event_hash = self._event_hash(event_id, event_type, license_id, timestamp, actor, payload, previous_hash)
        signature = self._sign_event_hash(event_hash)
        event = LicenseLedgerEvent(
            event_id,
            event_type,
            license_id,
            timestamp,
            actor,
            payload,
            previous_hash,
            event_hash,
            signature,
        )
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), sort_keys=True, default=str) + "\n")
        self.events.append(event)
        return event

    def _rebuild_state(self) -> None:
        for event in self.events:
            if event.event_type == "license_registered":
                payload = event.payload
                record = DataLicenseRecord(
                    license_id=str(payload["license_id"]),
                    source=str(payload["source"]),
                    data_vendor=str(payload.get("data_vendor", payload["source"])),
                    license_status=_coerce_source_license(payload.get("license_status")),
                    permission_basis=str(payload.get("permission_basis", "")),
                    issued_at=float(payload.get("issued_at", event.timestamp)),
                    expires_at=payload.get("expires_at"),
                    status=_coerce_license_ledger_status(payload.get("status", LicenseLedgerStatus.ACTIVE)),
                    revoked_at=payload.get("revoked_at"),
                    terms_hash=str(payload.get("terms_hash", "")),
                )
                if record.expires_at is not None:
                    record.expires_at = float(record.expires_at)
                if record.revoked_at is not None:
                    record.revoked_at = float(record.revoked_at)
                self.licenses[record.license_id] = record
            elif event.event_type in {"license_revoked", "license_expired"}:
                record = self.licenses.get(event.license_id)
                if record:
                    record.status = (
                        LicenseLedgerStatus.EXPIRED
                        if event.event_type == "license_expired"
                        else LicenseLedgerStatus.REVOKED
                    )
                    record.revoked_at = event.timestamp

    def _read_events(self) -> List[LicenseLedgerEvent]:
        if not self.path.exists():
            return []
        events: List[LicenseLedgerEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                data = json.loads(text)
                events.append(
                    LicenseLedgerEvent(
                        event_id=str(data["event_id"]),
                        event_type=str(data["event_type"]),
                        license_id=str(data["license_id"]),
                        timestamp=float(data["timestamp"]),
                        actor=str(data["actor"]),
                        payload=dict(data["payload"]),
                        previous_event_hash=str(data["previous_event_hash"]),
                        event_hash=str(data["event_hash"]),
                        signature=str(data["signature"]),
                    )
                )
        return events

    def _event_hash(
        self,
        event_id: str,
        event_type: str,
        license_id: str,
        timestamp: float,
        actor: str,
        payload: Dict[str, Any],
        previous_hash: str,
    ) -> str:
        event_payload = {
            "event_id": event_id,
            "event_type": event_type,
            "license_id": license_id,
            "timestamp": round(timestamp, 6),
            "actor": actor,
            "payload": payload,
            "previous_event_hash": previous_hash,
        }
        return hashlib.sha256(json.dumps(event_payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()

    def _sign_event_hash(self, event_hash: str) -> str:
        return hmac.new(
            self.signing_secret.encode("utf-8"),
            event_hash.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()


class DataPassportSidecarProxy:
    """Lightweight ingress proxy that attaches and verifies signed data passports."""

    required_fields = {
        "source",
        "source_timestamp",
        "license",
        "symbol_universe",
        "data_vendor",
        "ingestion_time",
        "adjustment_method",
        "survivorship_bias_status",
        "lookahead_risk_status",
        "quality_score",
        "lineage_hash",
    }

    def __init__(
        self,
        signing_secret: str = "alphaalgo-data-passport",
        compliance_ledger: Optional[ComplianceLicenseLedger] = None,
    ):
        self.signing_secret = signing_secret
        self.compliance_ledger = compliance_ledger or ComplianceLicenseLedger()

    def attach_passport(
        self,
        message: Mapping[str, Any],
        source: DataSourceProvenance,
        issuer: str = "alphaalgo-sidecar",
    ) -> Dict[str, Any]:
        passport = self.passport_from_source(source, issuer)
        wrapped = dict(message)
        wrapped["data_passport"] = passport.to_dict()
        wrapped.setdefault("metadata", {})
        if isinstance(wrapped["metadata"], Mapping):
            metadata = dict(wrapped["metadata"])
            metadata["data_passport_id"] = passport.passport_id
            metadata["data_passport_signature"] = passport.signature
            metadata["source_lineage_hash"] = passport.lineage_hash
            wrapped["metadata"] = metadata
        return wrapped

    def passport_from_source(self, source: DataSourceProvenance, issuer: str = "alphaalgo-sidecar") -> DataPassport:
        passport = DataPassport(
            passport_id=hashlib.sha256(f"{source.source_id}:{source.lineage_hash()}:{time.time():.6f}".encode("utf-8")).hexdigest()[:16],
            dataset_id=source.source_id,
            source=source.name,
            source_timestamp=source.source_timestamp,
            license=_coerce_source_license(source.license_status).value,
            license_id=source.license_id,
            symbol_universe=list(source.symbol_universe),
            data_vendor=source.data_vendor,
            ingestion_time=source.ingestion_time,
            adjustment_method=source.adjustment_method,
            survivorship_bias_status=source.survivorship_bias_status,
            lookahead_risk_status=source.lookahead_risk_status,
            quality_score=source.quality_score,
            lineage_hash=source.lineage_hash(),
            issued_at=time.time(),
            issuer=issuer,
        )
        return passport.sign(self.signing_secret)

    def verify_message(self, message: Mapping[str, Any], now: Optional[float] = None) -> DataPassportValidationResult:
        passport_payload = message.get("data_passport") if isinstance(message, Mapping) else None
        if not isinstance(passport_payload, Mapping):
            return DataPassportValidationResult(False, reasons=["missing signed data passport"])
        passport = self._passport_from_mapping(passport_payload)
        reasons: List[str] = []
        if not passport.verify(self.signing_secret):
            reasons.append("invalid data passport signature")
        missing = [
            field_name
            for field_name in self.required_fields
            if not passport_payload.get(field_name)
        ]
        if missing:
            reasons.append("data passport missing required fields: " + ", ".join(sorted(missing)))
        if passport.quality_score < 0.80:
            reasons.append(f"data passport quality score {passport.quality_score:.2f} below threshold 0.80")
        if passport.survivorship_bias_status.lower() in {"unknown", "unchecked", "biased"}:
            reasons.append("survivorship-bias status is not cleared")
        if passport.lookahead_risk_status.lower() in {"unknown", "unchecked", "unsafe", "failed"}:
            reasons.append("lookahead-risk status is not point-in-time safe")
        active, ledger_reasons = self.compliance_ledger.is_license_active(passport.license_id, now=now)
        if not active:
            reasons.extend(ledger_reasons)
        return DataPassportValidationResult(
            accepted=not reasons,
            passport_id=passport.passport_id,
            lineage_hash=passport.lineage_hash,
            reasons=reasons,
        )

    def require_passport(self, message: Mapping[str, Any], now: Optional[float] = None) -> Tuple[bool, List[str]]:
        result = self.verify_message(message, now=now)
        return result.accepted, result.reasons

    def _passport_from_mapping(self, payload: Mapping[str, Any]) -> DataPassport:
        return DataPassport(
            passport_id=str(payload.get("passport_id", "")),
            dataset_id=str(payload.get("dataset_id", "")),
            source=str(payload.get("source", "")),
            source_timestamp=_coerce_timestamp(payload.get("source_timestamp")),
            license=str(payload.get("license", "")),
            license_id=str(payload.get("license_id", "")),
            symbol_universe=list(payload.get("symbol_universe") or []),
            data_vendor=str(payload.get("data_vendor", "")),
            ingestion_time=_coerce_timestamp(payload.get("ingestion_time")),
            adjustment_method=str(payload.get("adjustment_method", "")),
            survivorship_bias_status=str(payload.get("survivorship_bias_status", "")),
            lookahead_risk_status=str(payload.get("lookahead_risk_status", "")),
            quality_score=float(payload.get("quality_score", 0.0)),
            lineage_hash=str(payload.get("lineage_hash", "")),
            issued_at=_coerce_timestamp(payload.get("issued_at")),
            issuer=str(payload.get("issuer", "")),
            signature=str(payload.get("signature", "")),
        )


class LegalCollectionLayer:
    """Builds collection plans using only public, licensed, permissioned, or internal data."""

    allowed_license_states = {
        SourceLicenseStatus.PUBLIC,
        SourceLicenseStatus.LICENSED,
        SourceLicenseStatus.PERMISSIONED,
        SourceLicenseStatus.INTERNAL_GENERATED,
    }

    default_required_categories = [
        DataSourceCategory.MARKET,
        DataSourceCategory.MACRO,
        DataSourceCategory.NEWS_FILINGS,
        DataSourceCategory.SENTIMENT,
        DataSourceCategory.BROKER_TELEMETRY,
        DataSourceCategory.ALTERNATIVE,
    ]

    def plan(self, mission: MissionRequirement, requested_tasks: Sequence[CollectionTask]) -> CollectionPlan:
        approved: List[CollectionTask] = []
        rejected: List[CollectionTask] = []
        notes: List[str] = []
        for task in requested_tasks:
            if task.license_status in self.allowed_license_states and task.permission_basis.strip():
                approved.append(task)
            else:
                rejected.append(task)
                notes.append(
                    f"rejected {task.collector_id}: source must be public, licensed, permissioned, or internally generated"
                )
        covered = {task.category for task in approved}
        missing = [category for category in self.default_required_categories if category not in covered]
        if missing:
            notes.append("missing collection categories: " + ", ".join(category.value for category in missing))
        return CollectionPlan(mission.mission_id, approved, rejected, self.default_required_categories, notes)

    def from_sources(self, mission: MissionRequirement, sources: Sequence[DataSourceProvenance]) -> CollectionPlan:
        tasks = [
            CollectionTask(
                collector_id=f"collector:{source.source_id}",
                category=source.category,
                source_name=source.name,
                source_uri=source.uri,
                license_status=source.license_status,
                permission_basis=source.permission_basis,
                purpose=mission.tradable_question,
            )
            for source in sources
        ]
        return self.plan(mission, tasks)


class ModelArtifactRegistry:
    """Signs and verifies read-only production model artifacts."""

    def __init__(self, signing_secret: str = "alphaalgo-model-registry"):
        self.signing_secret = signing_secret
        self.artifacts: Dict[str, SignedModelArtifact] = {}

    def sign(
        self,
        model_name: str,
        model_bytes: bytes,
        signer: str,
        approved_for_production: bool = False,
        data_manifest: Optional[Mapping[str, Any]] = None,
        deterministic_build: bool = True,
    ) -> SignedModelArtifact:
        model_digest = hashlib.sha256(model_bytes).hexdigest()
        data_manifest_hash = hashlib.sha256(
            json.dumps(data_manifest or {}, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        build_digest = hashlib.sha256(
            f"{model_name}:{model_digest}:{data_manifest_hash}:{deterministic_build}".encode("utf-8")
        ).hexdigest()
        created_at = time.time()
        artifact_id = hashlib.sha256(f"{model_name}:{model_digest}:{created_at:.6f}".encode("utf-8")).hexdigest()[:16]
        signature = self._signature(model_name, model_digest, signer, created_at)
        artifact = SignedModelArtifact(
            artifact_id,
            model_name,
            model_digest,
            signer,
            signature,
            created_at,
            read_only=True,
            approved_for_production=approved_for_production,
            author=signer,
            data_manifest_hash=data_manifest_hash,
            build_digest=build_digest,
            deterministic_build=deterministic_build,
        )
        self.artifacts[artifact_id] = artifact
        return artifact

    def verify(self, artifact: SignedModelArtifact) -> bool:
        expected = self._signature(artifact.model_name, artifact.model_digest, artifact.signer, artifact.created_at)
        staging_expected = self._counter_signature(artifact, "staging", artifact.staging_signer)
        validation_expected = self._counter_signature(artifact, "validation", artifact.validation_signer)
        return (
            artifact.signature == expected
            and artifact.read_only
            and bool(artifact.approved_for_production)
            and bool(artifact.deterministic_build)
            and bool(artifact.staging_signature)
            and bool(artifact.validation_signature)
            and hmac.compare_digest(artifact.staging_signature, staging_expected)
            and hmac.compare_digest(artifact.validation_signature, validation_expected)
        )

    def access_report(self, artifact: Optional[SignedModelArtifact], role: IntelligenceRole) -> AccessDecision:
        if artifact is None:
            return AccessDecision(False, role, IntelligenceCompartment.PRODUCTION_MODEL, "read production model", ["missing signed model artifact"])
        if not self.verify(artifact):
            return AccessDecision(False, role, IntelligenceCompartment.PRODUCTION_MODEL, "read production model", ["invalid or unapproved model signature"])
        return AccessDecision(True, role, IntelligenceCompartment.PRODUCTION_MODEL, "read production model", [])

    def _signature(self, model_name: str, model_digest: str, signer: str, created_at: float) -> str:
        payload = f"{model_name}:{model_digest}:{signer}:{created_at:.6f}:{self.signing_secret}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def counter_sign(self, artifact: SignedModelArtifact, stage: str, signer: str) -> SignedModelArtifact:
        signature = self._counter_signature(artifact, stage, signer)
        artifact.counter_signatures.append({"stage": stage, "signer": signer, "signature": signature})
        if stage == "staging":
            artifact.staging_signer = signer
            artifact.staging_signature = signature
        elif stage == "validation":
            artifact.validation_signer = signer
            artifact.validation_signature = signature
        return artifact

    def approve_for_production(self, artifact: SignedModelArtifact) -> SignedModelArtifact:
        artifact.approved_for_production = True
        artifact.read_only = True
        self.artifacts[artifact.artifact_id] = artifact
        return artifact

    def _counter_signature(self, artifact: SignedModelArtifact, stage: str, signer: str) -> str:
        payload = {
            "artifact_id": artifact.artifact_id,
            "model_digest": artifact.model_digest,
            "data_manifest_hash": artifact.data_manifest_hash,
            "build_digest": artifact.build_digest,
            "stage": stage,
            "signer": signer,
            "secret": self.signing_secret,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class ZeroTrustZonePolicy:
    """Software control model for research, staging, and production isolation."""

    allowed_flows = {
        (IntelligenceZone.RESEARCH, IntelligenceZone.STAGING),
        (IntelligenceZone.STAGING, IntelligenceZone.PRODUCTION),
    }

    def evaluate(
        self,
        role: IntelligenceRole,
        zone: IntelligenceZone,
        action: str,
        source_zone: Optional[IntelligenceZone] = None,
        target_zone: Optional[IntelligenceZone] = None,
    ) -> ZonePolicyReport:
        zone = _coerce_intelligence_zone(zone)
        action_lower = action.lower()
        reasons: List[str] = []
        if source_zone and target_zone and (_coerce_intelligence_zone(source_zone), _coerce_intelligence_zone(target_zone)) not in self.allowed_flows:
            reasons.append("zone transfer must follow research -> staging -> production promotion flow")
        if zone == IntelligenceZone.RESEARCH:
            if any(token in action_lower for token in ("live order", "execute", "trade live", "production token")):
                reasons.append("research zone has no live-order or execution access")
            if "promote" in action_lower or "deploy" in action_lower:
                reasons.append("researchers cannot promote or deploy artifacts")
        if zone == IntelligenceZone.STAGING:
            if "modify artifact" in action_lower or "alter test result" in action_lower:
                reasons.append("staging permits review access, not artifact or test-result mutation")
            if role in {IntelligenceRole.RESEARCH_ANALYST, IntelligenceRole.EXECUTION_OPERATOR} and "approve" in action_lower:
                reasons.append("staging approvals require a validation officer or staging system signature")
        if zone == IntelligenceZone.PRODUCTION:
            if any(token in action_lower for token in ("ssh", "shell", "write model", "modify config", "mutable filesystem")):
                reasons.append("production allows read-only models/configs and writable logs only")
            if role == IntelligenceRole.RED_TEAM and "live signal" in action_lower:
                reasons.append("red-team cannot see live production signals")
            if role == IntelligenceRole.EXECUTION_OPERATOR and any(token in action_lower for token in ("modify", "write", "deploy")):
                reasons.append("operators cannot modify production artifacts or configs")
        if role == IntelligenceRole.RESEARCH_ANALYST and ("promote" in action_lower or "deploy" in action_lower):
            reasons.append("research role cannot promote")
        if role == IntelligenceRole.RED_TEAM and "live signal" in action_lower:
            reasons.append("red-team is isolated from live signals")
        return ZonePolicyReport(not reasons, zone, role, action, reasons)


class ModelPromotionChain:
    """CI/CD-like model promotion with deterministic artifacts and adversarial gates."""

    def __init__(
        self,
        registry: Optional[ModelArtifactRegistry] = None,
        audit_ledger: Optional[ImmutableAuditLedger] = None,
        zone_policy: Optional[ZeroTrustZonePolicy] = None,
    ):
        self.registry = registry or ModelArtifactRegistry()
        self.audit_ledger = audit_ledger or AppendOnlyJsonlAuditLedger()
        self.zone_policy = zone_policy or ZeroTrustZonePolicy()

    def submit_research_artifact(
        self,
        model_name: str,
        model_bytes: bytes,
        author: str,
        data_manifest: Mapping[str, Any],
        hypothesis: str,
    ) -> SignedModelArtifact:
        manifest = dict(data_manifest)
        manifest["hypothesis"] = hypothesis
        artifact = self.registry.sign(
            model_name,
            model_bytes,
            author,
            approved_for_production=False,
            data_manifest=manifest,
            deterministic_build=True,
        )
        self.audit_ledger.append(
            "model_research_artifact_submitted",
            {"artifact": artifact.to_dict(), "hypothesis": hypothesis},
            actor=author,
            action="submit_research_artifact",
            artifact_hash=artifact.model_digest,
            input_hash=artifact.data_manifest_hash,
        )
        return artifact

    def run_staging_gate(
        self,
        artifact: SignedModelArtifact,
        checklist: PromotionGateChecklist,
        ci_report: SignalCounterintelligenceReport,
        staging_actor: str = "staging-system",
    ) -> ModelPromotionReport:
        reasons: List[str] = []
        zone_report = self.zone_policy.evaluate(
            IntelligenceRole.STAGING_SYSTEM,
            IntelligenceZone.STAGING,
            "run adversarial promotion gate",
            source_zone=IntelligenceZone.RESEARCH,
            target_zone=IntelligenceZone.STAGING,
        )
        if not zone_report.accepted:
            reasons.extend(zone_report.reasons)
        if not checklist.accepted:
            reasons.append("promotion checklist incomplete: " + ", ".join(checklist.missing_items))
        if ci_report.decision != IntelligenceDecision.ACCEPT or not ci_report.execution_allowed:
            reasons.append("counterintelligence report did not accept artifact")
        if not artifact.read_only or not artifact.deterministic_build:
            reasons.append("artifact must be read-only and deterministically built")
        if reasons:
            decision = IntelligenceDecision.REJECT
        else:
            self.registry.counter_sign(artifact, "staging", staging_actor)
            decision = IntelligenceDecision.ACCEPT
        audit_record = self.audit_ledger.append(
            "model_staging_counterintelligence_gate",
            {
                "artifact": artifact.to_dict(),
                "checklist": checklist.to_dict(),
                "counterintelligence": ci_report.to_dict(),
                "zone_policy": zone_report.to_dict(),
                "decision": decision.value,
                "reasons": reasons,
            },
            actor=staging_actor,
            action="run_staging_gate",
            artifact_hash=artifact.model_digest,
            input_hash=artifact.data_manifest_hash,
            output_hash=ci_report.audit_digest,
        )
        return ModelPromotionReport(
            accepted=decision == IntelligenceDecision.ACCEPT,
            decision=decision,
            artifact=artifact,
            checklist=checklist,
            reasons=reasons,
            audit_record=audit_record,
        )

    def validation_officer_approve(
        self,
        artifact: SignedModelArtifact,
        checklist: PromotionGateChecklist,
        validation_officer: str,
        author: str,
    ) -> ModelPromotionReport:
        reasons: List[str] = []
        if validation_officer == author:
            reasons.append("validation officer must be separate from artifact author")
        if not artifact.staging_signature:
            reasons.append("staging counter-signature is required before approval")
        if not checklist.accepted:
            reasons.append("promotion checklist incomplete: " + ", ".join(checklist.missing_items))
        zone_report = self.zone_policy.evaluate(
            IntelligenceRole.VALIDATION_OFFICER,
            IntelligenceZone.STAGING,
            "approve staged artifact",
        )
        if not zone_report.accepted:
            reasons.extend(zone_report.reasons)
        if reasons:
            decision = IntelligenceDecision.REJECT
        else:
            self.registry.counter_sign(artifact, "validation", validation_officer)
            self.registry.approve_for_production(artifact)
            decision = IntelligenceDecision.ACCEPT
        audit_record = self.audit_ledger.append(
            "model_validation_officer_approval",
            {
                "artifact": artifact.to_dict(),
                "checklist": checklist.to_dict(),
                "zone_policy": zone_report.to_dict(),
                "decision": decision.value,
                "reasons": reasons,
            },
            actor=validation_officer,
            action="validation_officer_approve",
            artifact_hash=artifact.model_digest,
            input_hash=artifact.data_manifest_hash,
        )
        return ModelPromotionReport(
            accepted=decision == IntelligenceDecision.ACCEPT,
            decision=decision,
            artifact=artifact,
            checklist=checklist,
            reasons=reasons,
            audit_record=audit_record,
        )


class SignalIntelligenceAdapter:
    """Converts dict, dataclass, and Pydantic signal objects into intelligence inputs."""

    def adapt(
        self,
        raw_signal: Any,
        mission: Optional[MissionRequirement] = None,
        sources: Optional[Sequence[DataSourceProvenance]] = None,
        evidence: Optional[Sequence[IntelligenceEvidence]] = None,
    ) -> SignalIntelligencePackage:
        payload = self._as_mapping(raw_signal)
        metadata = self._as_mapping(payload.get("metadata", {}))
        merged = dict(metadata)
        merged.update(payload)
        now = time.time()

        source_items = list(sources) if sources is not None else self._extract_sources(merged, now)
        evidence_items = list(evidence) if evidence is not None else self._extract_evidence(merged, source_items, now)
        signal = self._build_signal_claim(merged, source_items, evidence_items, now)
        mission = mission or self._build_mission(merged, signal, now)
        return SignalIntelligencePackage(mission, signal, source_items, evidence_items)

    def _as_mapping(self, value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        if hasattr(value, "model_dump"):
            return dict(value.model_dump())
        if hasattr(value, "dict"):
            return dict(value.dict())
        if hasattr(value, "__dataclass_fields__"):
            return asdict(value)
        if hasattr(value, "__dict__"):
            return dict(value.__dict__)
        return {}

    def _extract_sources(self, payload: Dict[str, Any], now: float) -> List[DataSourceProvenance]:
        raw_sources = (
            payload.get("source_provenance")
            or payload.get("sources")
            or payload.get("data_sources")
            or payload.get("provenance_sources")
            or []
        )
        if isinstance(raw_sources, Mapping):
            raw_sources = [raw_sources]
        if isinstance(raw_sources, str):
            raw_sources = [{"name": raw_sources}]

        sources: List[DataSourceProvenance] = []
        for index, raw_source in enumerate(raw_sources or []):
            if isinstance(raw_source, DataSourceProvenance):
                sources.append(raw_source)
                continue
            item = self._as_mapping(raw_source)
            source_id = str(item.get("source_id") or item.get("id") or f"source-{index + 1}")
            sources.append(
                DataSourceProvenance(
                    source_id=source_id,
                    name=str(item.get("name") or item.get("source_name") or item.get("source") or source_id),
                    category=_coerce_data_category(item.get("category", DataSourceCategory.INTERNAL_GENERATED)),
                    license_status=_coerce_source_license(
                        item.get("license_status", item.get("license", SourceLicenseStatus.UNKNOWN))
                    ),
                    license_name=str(item.get("license_name") or item.get("license_terms") or ""),
                    permission_basis=str(item.get("permission_basis") or item.get("permission") or ""),
                    collected_at=_coerce_timestamp(item.get("collected_at", item.get("timestamp", now))),
                    observed_at=_coerce_timestamp(item.get("observed_at", item.get("timestamp", now))),
                    uri=str(item.get("uri") or item.get("source_uri") or ""),
                    provenance_chain=list(item.get("provenance_chain") or item.get("provenance") or []),
                    compliance_score=float(item.get("compliance_score", 0.0)),
                    reliability_score=float(item.get("reliability_score", 0.0)),
                    contains_mnpi=bool(item.get("contains_mnpi", False)),
                    confidentiality_flags=list(item.get("confidentiality_flags") or []),
                    source_timestamp=_coerce_timestamp(
                        item.get("source_timestamp", item.get("observed_at", item.get("timestamp", now)))
                    ),
                    license_id=str(item.get("license_id") or ""),
                    license_expires_at=(
                        _coerce_timestamp(item.get("license_expires_at"))
                        if item.get("license_expires_at") is not None
                        else None
                    ),
                    symbol_universe=list(
                        item.get("symbol_universe")
                        or item.get("symbols")
                        or item.get("universe")
                        or [payload.get("symbol") or payload.get("asset") or "UNKNOWN"]
                    ),
                    data_vendor=str(item.get("data_vendor") or item.get("vendor") or item.get("source_name") or ""),
                    ingestion_time=_coerce_timestamp(
                        item.get("ingestion_time", item.get("collected_at", item.get("timestamp", now)))
                    ),
                    adjustment_method=str(item.get("adjustment_method") or "raw"),
                    survivorship_bias_status=str(item.get("survivorship_bias_status") or "not_applicable"),
                    lookahead_risk_status=str(item.get("lookahead_risk_status") or "point_in_time"),
                    quality_score=float(item.get("quality_score", item.get("compliance_score", 0.0))),
                )
            )

        source_name = payload.get("source")
        if not sources and source_name:
            sources.append(
                DataSourceProvenance(
                    source_id=str(source_name),
                    name=str(source_name),
                    category=DataSourceCategory.INTERNAL_GENERATED,
                    license_status=SourceLicenseStatus.UNKNOWN,
                    license_name="",
                    permission_basis="",
                    collected_at=now,
                    observed_at=now,
                    provenance_chain=[],
                    compliance_score=0.0,
                    reliability_score=0.0,
                    symbol_universe=[str(payload.get("symbol") or payload.get("asset") or "UNKNOWN")],
                    data_vendor=str(source_name),
                    quality_score=0.0,
                )
            )
        return sources

    def _extract_evidence(
        self,
        payload: Dict[str, Any],
        sources: Sequence[DataSourceProvenance],
        now: float,
    ) -> List[IntelligenceEvidence]:
        raw_evidence = payload.get("evidence") or payload.get("evidence_items") or []
        if isinstance(raw_evidence, Mapping):
            raw_evidence = [raw_evidence]
        if isinstance(raw_evidence, str):
            raw_evidence = [{"claim": raw_evidence}]

        evidence: List[IntelligenceEvidence] = []
        default_source_id = sources[0].source_id if sources else ""
        for index, raw_item in enumerate(raw_evidence or []):
            if isinstance(raw_item, IntelligenceEvidence):
                evidence.append(raw_item)
                continue
            item = self._as_mapping(raw_item)
            claim = str(item.get("claim") or item.get("description") or item.get("rationale") or "")
            content_hash = str(item.get("content_hash") or hashlib.sha256(claim.encode("utf-8")).hexdigest())
            evidence.append(
                IntelligenceEvidence(
                    evidence_id=str(item.get("evidence_id") or item.get("id") or f"evidence-{index + 1}"),
                    source_id=str(item.get("source_id") or default_source_id),
                    claim=claim,
                    observed_at=_coerce_timestamp(item.get("observed_at", item.get("timestamp", now))),
                    content_hash=content_hash,
                    features=dict(item.get("features") or {}),
                )
            )
        return evidence

    def _build_signal_claim(
        self,
        payload: Dict[str, Any],
        sources: Sequence[DataSourceProvenance],
        evidence: Sequence[IntelligenceEvidence],
        now: float,
    ) -> SignalClaim:
        signal_id = str(payload.get("signal_id") or payload.get("id") or f"signal-{int(now * 1000)}")
        asset = str(payload.get("asset") or payload.get("symbol") or "UNKNOWN")
        direction = str(payload.get("direction") or payload.get("side") or payload.get("action") or "research_only")
        thesis = str(
            payload.get("thesis")
            or payload.get("rationale")
            or payload.get("reason")
            or f"{direction} signal for {asset}"
        )
        features = dict(payload.get("features") or {})
        for key in ("validation_sharpe", "train_sharpe", "sample_size", "p_value", "confidence"):
            if key in payload and key not in features:
                features[key] = payload[key]
        return SignalClaim(
            signal_id=signal_id,
            asset=asset,
            thesis=thesis,
            horizon=str(payload.get("horizon") or payload.get("timeframe") or "unknown"),
            confidence=float(payload.get("confidence", payload.get("strength", 0.0))),
            source_ids=[source.source_id for source in sources],
            evidence_ids=[item.evidence_id for item in evidence],
            generated_at=_coerce_timestamp(payload.get("generated_at", payload.get("timestamp", now))),
            features=features,
            proposed_action=direction,
        )

    def _build_mission(self, payload: Dict[str, Any], signal: SignalClaim, now: float) -> MissionRequirement:
        mission_payload = self._as_mapping(payload.get("mission"))
        return MissionRequirement(
            mission_id=str(mission_payload.get("mission_id") or payload.get("mission_id") or f"mission-{signal.signal_id}"),
            tradable_question=str(
                mission_payload.get("tradable_question")
                or payload.get("tradable_question")
                or f"Can compliant evidence support {signal.asset} over {signal.horizon}?"
            ),
            edge_hypothesis=str(
                mission_payload.get("edge_hypothesis")
                or payload.get("edge_hypothesis")
                or signal.thesis
            ),
            objective_functions=list(
                mission_payload.get("objective_functions")
                or payload.get("objective_functions")
                or ["compliance", "risk_adjusted_return"]
            ),
            risk_budget=float(mission_payload.get("risk_budget", payload.get("risk_budget", 0.01))),
            allowed_assets=list(mission_payload.get("allowed_assets") or payload.get("allowed_assets") or [signal.asset]),
            created_at=_coerce_timestamp(mission_payload.get("created_at", now)),
        )


class SourceValidationLayer:
    """Validates provenance, timestamps, licenses, and source reliability."""

    allowed_license_states = {
        SourceLicenseStatus.PUBLIC,
        SourceLicenseStatus.LICENSED,
        SourceLicenseStatus.PERMISSIONED,
        SourceLicenseStatus.INTERNAL_GENERATED,
    }
    forbidden_license_states = {
        SourceLicenseStatus.PRIVATE,
        SourceLicenseStatus.STOLEN,
        SourceLicenseStatus.CONFIDENTIAL,
        SourceLicenseStatus.MATERIAL_NONPUBLIC,
    }

    def __init__(
        self,
        min_compliance_score: float = 0.80,
        min_reliability_score: float = 0.45,
        min_quality_score: float = 0.80,
        max_source_age_seconds: float = 30 * 24 * 60 * 60,
        compliance_ledger: Optional[ComplianceLicenseLedger] = None,
    ):
        self.min_compliance_score = min_compliance_score
        self.min_reliability_score = min_reliability_score
        self.min_quality_score = min_quality_score
        self.max_source_age_seconds = max_source_age_seconds
        self.compliance_ledger = compliance_ledger

    def validate(self, source: DataSourceProvenance, now: Optional[float] = None) -> SourceValidationReport:
        now = now or time.time()
        license_status = _coerce_source_license(source.license_status)
        findings: List[str] = []
        if not source.source_id or not source.name:
            findings.append("missing source identity")
        if not source.license_name or not source.permission_basis:
            findings.append("missing license or permission basis")
        if license_status in self.forbidden_license_states:
            findings.append(f"forbidden source license status: {license_status.value}")
        if license_status not in self.allowed_license_states:
            findings.append(f"unapproved source license status: {license_status.value}")
        if source.contains_mnpi:
            findings.append("source flagged as material nonpublic information")
        if any(flag.lower() in {"private", "stolen", "confidential", "mnpi", "material_nonpublic"} for flag in source.confidentiality_flags):
            findings.append("source has forbidden confidentiality flags")
        if source.collected_at <= 0 or source.observed_at <= 0:
            findings.append("missing timestamp integrity")
        if source.source_timestamp <= 0 or source.ingestion_time <= 0:
            findings.append("missing source timestamp or ingestion time")
        if source.observed_at > source.collected_at + 300:
            findings.append("observed timestamp is after collection timestamp")
        if source.collected_at > now + 300 or source.observed_at > now + 300:
            findings.append("source timestamp is in the future")
        if self.max_source_age_seconds and now - source.collected_at > self.max_source_age_seconds:
            findings.append("source timestamp is stale")
        if source.license_expires_at is not None and source.license_expires_at <= now:
            findings.append("source license has expired")
        if not source.provenance_chain:
            findings.append("missing provenance chain")
        if not source.data_vendor:
            findings.append("missing data vendor")
        if not source.symbol_universe:
            findings.append("missing symbol universe")
        if not source.adjustment_method:
            findings.append("missing adjustment method")
        if source.survivorship_bias_status.lower() in {"unknown", "unchecked", "biased"}:
            findings.append("survivorship-bias status is not cleared")
        if source.lookahead_risk_status.lower() in {"unknown", "unchecked", "unsafe", "failed"}:
            findings.append("lookahead-risk status is not point-in-time safe")
        if source.compliance_score < self.min_compliance_score:
            findings.append(f"compliance score {source.compliance_score:.2f} below threshold {self.min_compliance_score:.2f}")
        if source.reliability_score < self.min_reliability_score:
            findings.append(f"reliability score {source.reliability_score:.2f} below threshold {self.min_reliability_score:.2f}")
        if source.quality_score < self.min_quality_score:
            findings.append(f"quality score {source.quality_score:.2f} below threshold {self.min_quality_score:.2f}")
        if self.compliance_ledger is not None:
            active, ledger_reasons = self.compliance_ledger.is_license_active(source.license_id, now=now)
            findings.extend(ledger_reasons if not active else [])
        accepted = not findings
        return SourceValidationReport(
            source_id=source.source_id,
            accepted=accepted,
            decision=IntelligenceDecision.ACCEPT if accepted else IntelligenceDecision.REJECT,
            compliance_score=source.compliance_score,
            reliability_score=source.reliability_score,
            findings=findings,
            lineage_hash=source.lineage_hash(),
        )

    def validate_many(self, sources: Sequence[DataSourceProvenance]) -> List[SourceValidationReport]:
        return [self.validate(source) for source in sources]


class CompartmentalizedSecurityModel:
    """Need-to-know security model for research, execution, models, governance, and audit."""

    _allowed = {
        IntelligenceRole.RESEARCH_ANALYST: {
            IntelligenceCompartment.RESEARCH: {"read", "write", "analyze"},
            IntelligenceCompartment.AUDIT: {"read"},
        },
        IntelligenceRole.EXECUTION_OPERATOR: {
            IntelligenceCompartment.EXECUTION: {"read", "execute"},
            IntelligenceCompartment.PRODUCTION_MODEL: {"read"},
        },
        IntelligenceRole.RISK_OFFICER: {
            IntelligenceCompartment.RESEARCH: {"read"},
            IntelligenceCompartment.EXECUTION: {"read"},
            IntelligenceCompartment.GOVERNANCE: {"read", "approve"},
            IntelligenceCompartment.AUDIT: {"read"},
        },
        IntelligenceRole.GOVERNANCE_APPROVER: {
            IntelligenceCompartment.GOVERNANCE: {"read", "approve"},
            IntelligenceCompartment.AUDIT: {"read"},
        },
        IntelligenceRole.VALIDATION_OFFICER: {
            IntelligenceCompartment.GOVERNANCE: {"read", "approve"},
            IntelligenceCompartment.AUDIT: {"read"},
            IntelligenceCompartment.PRODUCTION_MODEL: {"read"},
        },
        IntelligenceRole.COMPLIANCE_OFFICER: {
            IntelligenceCompartment.GOVERNANCE: {"read", "approve"},
            IntelligenceCompartment.AUDIT: {"read", "write"},
        },
        IntelligenceRole.RED_TEAM: {
            IntelligenceCompartment.RESEARCH: {"read", "analyze"},
            IntelligenceCompartment.GOVERNANCE: {"read"},
            IntelligenceCompartment.AUDIT: {"read"},
        },
        IntelligenceRole.STAGING_SYSTEM: {
            IntelligenceCompartment.GOVERNANCE: {"read", "approve"},
            IntelligenceCompartment.PRODUCTION_MODEL: {"read"},
            IntelligenceCompartment.AUDIT: {"read", "write"},
        },
        IntelligenceRole.PRODUCTION_RUNTIME: {
            IntelligenceCompartment.EXECUTION: {"read", "execute"},
            IntelligenceCompartment.PRODUCTION_MODEL: {"read"},
            IntelligenceCompartment.AUDIT: {"write"},
        },
        IntelligenceRole.AUDITOR: {
            IntelligenceCompartment.AUDIT: {"read"},
            IntelligenceCompartment.GOVERNANCE: {"read"},
        },
        IntelligenceRole.AI_ENGINEERING_AGENT: {
            IntelligenceCompartment.RESEARCH: {"read", "analyze"},
            IntelligenceCompartment.AUDIT: {"read"},
        },
    }

    def validate_access(
        self,
        role: IntelligenceRole,
        compartment: IntelligenceCompartment,
        action: str,
        signed_model_artifact: bool = False,
        signed_approval: bool = False,
        kill_switch_active: bool = False,
    ) -> AccessDecision:
        action_lower = action.lower()
        verb = self._verb(action_lower)
        reasons: List[str] = []
        allowed_verbs = self._allowed.get(role, {}).get(compartment, set())
        if verb not in allowed_verbs:
            reasons.append(f"role {role.value} lacks {verb} access to {compartment.value}")
        if compartment == IntelligenceCompartment.PRODUCTION_MODEL:
            if verb != "read":
                reasons.append("production models are read-only")
            if not signed_model_artifact:
                reasons.append("production model access requires signed model artifact")
        if "self-modification" in action_lower or "self modification" in action_lower or "live self" in action_lower:
            reasons.append("no live self-modification")
        if "risk limit" in action_lower and not signed_approval:
            reasons.append("risk-limit changes require signed approval gate")
        if role == IntelligenceRole.RESEARCH_ANALYST and ("promote" in action_lower or "deploy" in action_lower):
            reasons.append("researchers cannot promote or deploy artifacts")
        if role == IntelligenceRole.EXECUTION_OPERATOR and any(token in action_lower for token in ("modify", "mutate", "write model", "deploy")):
            reasons.append("operators cannot modify models, configs, or promotion state")
        if role == IntelligenceRole.RED_TEAM and "live signal" in action_lower:
            reasons.append("red-team cannot see live signals")
        if "deploy" in action_lower and role == IntelligenceRole.AI_ENGINEERING_AGENT:
            reasons.append("AI engineering agent may not deploy to production")
        if kill_switch_active and verb == "execute":
            reasons.append("kill switch active")
        return AccessDecision(not reasons, role, compartment, action, reasons)

    def _verb(self, action: str) -> str:
        if any(token in action for token in ("execute", "trade", "order")):
            return "execute"
        if any(token in action for token in ("approve", "authorize")):
            return "approve"
        if any(token in action for token in ("write", "modify", "mutate", "deploy", "change")):
            return "write"
        if "analyze" in action:
            return "analyze"
        return "read"


class SignalCounterintelligenceEngine:
    """Attacks every signal before it can influence a financial decision."""

    leakage_terms = {"future_return", "future_price", "next_bar_return", "target_return", "post_event_outcome"}
    adversarial_terms = {"spoofing", "layering", "wash trade", "pump", "quote stuffing", "liquidity mirage"}
    mnpi_terms = {"insider", "non-public", "nonpublic", "confidential source", "leaked earnings", "board material"}

    def __init__(
        self,
        source_validator: Optional[SourceValidationLayer] = None,
        audit_ledger: Optional[ImmutableAuditLedger] = None,
        mode: CounterintelligenceMode = CounterintelligenceMode.HARD_GATE,
        passport_proxy: Optional[DataPassportSidecarProxy] = None,
    ):
        self.source_validator = source_validator or SourceValidationLayer()
        self.audit_ledger = audit_ledger or AppendOnlyJsonlAuditLedger()
        self.mode = _coerce_counterintelligence_mode(mode)
        self.passport_proxy = passport_proxy

    def review_signal(
        self,
        signal: SignalClaim,
        sources: Sequence[DataSourceProvenance],
        evidence: Sequence[IntelligenceEvidence],
        mode: Optional[CounterintelligenceMode] = None,
    ) -> SignalCounterintelligenceReport:
        mode = _coerce_counterintelligence_mode(mode or self.mode)
        source_by_id = {source.source_id: source for source in sources}
        evidence_by_id = {item.evidence_id: item for item in evidence}
        source_reports = [self.source_validator.validate(source) for source in sources]
        findings: List[CounterintelligenceFinding] = []

        for report in source_reports:
            if not report.accepted:
                description = f"source {report.source_id} failed validation: {'; '.join(report.findings)}"
                if any("compliance score" in item for item in report.findings):
                    vector = SignalAttackVector.LOW_COMPLIANCE
                elif any("reliability score" in item for item in report.findings):
                    vector = SignalAttackVector.SOURCE_RELIABILITY_WEAKNESS
                elif any("timestamp" in item for item in report.findings):
                    vector = SignalAttackVector.TIMESTAMP_ANOMALY
                elif any("forbidden" in item or "material nonpublic" in item for item in report.findings):
                    vector = SignalAttackVector.ILLEGAL_SOURCE
                else:
                    vector = SignalAttackVector.MISSING_PROVENANCE
                findings.append(self._finding(
                    vector,
                    "critical" if any("forbidden" in item or "material nonpublic" in item for item in report.findings) else "high",
                    description,
                    [report.source_id, report.lineage_hash],
                ))

        missing_sources = [source_id for source_id in signal.source_ids if source_id not in source_by_id]
        if missing_sources:
            findings.append(self._finding(
                SignalAttackVector.MISSING_PROVENANCE,
                "high",
                f"signal references missing sources: {', '.join(missing_sources)}",
                missing_sources,
            ))
        missing_evidence = [evidence_id for evidence_id in signal.evidence_ids if evidence_id not in evidence_by_id]
        if missing_evidence:
            findings.append(self._finding(
                SignalAttackVector.WEAK_CLAIM,
                "high",
                f"signal references missing evidence: {', '.join(missing_evidence)}",
                missing_evidence,
            ))
        evidence_with_missing_sources = [
            item.evidence_id for item in evidence if item.source_id and item.source_id not in source_by_id
        ]
        if evidence_with_missing_sources:
            findings.append(self._finding(
                SignalAttackVector.MISSING_PROVENANCE,
                "high",
                f"evidence references missing sources: {', '.join(evidence_with_missing_sources)}",
                evidence_with_missing_sources,
            ))

        thesis_lower = signal.thesis.lower()
        if any(term in thesis_lower for term in self.mnpi_terms):
            findings.append(self._finding(
                SignalAttackVector.MATERIAL_NONPUBLIC_INFORMATION,
                "critical",
                "signal thesis appears to rely on private, confidential, leaked, or material nonpublic information",
                signal.evidence_ids,
            ))
        feature_keys = {key.lower() for key in signal.features}
        for item in evidence:
            feature_keys.update(key.lower() for key in item.features)
        if feature_keys & self.leakage_terms:
            findings.append(self._finding(
                SignalAttackVector.DATA_LEAKAGE,
                "critical",
                f"signal uses leakage-prone features: {', '.join(sorted(feature_keys & self.leakage_terms))}",
                signal.evidence_ids,
            ))
        if any(term in thesis_lower for term in self.adversarial_terms):
            findings.append(self._finding(
                SignalAttackVector.ADVERSARIAL_MARKET_BEHAVIOR,
                "high",
                "signal may be contaminated by adversarial market behavior",
                signal.evidence_ids,
            ))
        overfit = self._overfit_reason(signal.features)
        if overfit:
            findings.append(self._finding(SignalAttackVector.OVERFITTING, "high", overfit, signal.evidence_ids))
        if self._weak_claim(signal, source_reports):
            findings.append(self._finding(
                SignalAttackVector.WEAK_CLAIM,
                "medium",
                "claim confidence is not supported by enough reliable, compliant evidence",
                signal.evidence_ids,
            ))
        findings.extend(self._adversarial_gauntlet_findings(signal, evidence))

        critical = any(finding.severity == "critical" for finding in findings)
        high_count = sum(1 for finding in findings if finding.severity == "high")
        compliance_score = self._mean(report.compliance_score for report in source_reports)
        reliability_score = self._mean(report.reliability_score for report in source_reports)
        accepted = not critical and high_count == 0 and compliance_score >= 0.80 and reliability_score >= 0.45
        decision = (
            IntelligenceDecision.ACCEPT
            if accepted
            else (
                IntelligenceDecision.REJECT
                if critical or mode == CounterintelligenceMode.HARD_GATE
                else IntelligenceDecision.QUARANTINE
            )
        )
        execution_allowed = self._execution_allowed(accepted, mode)
        blocked_reasons = [finding.description for finding in findings if finding.severity in {"critical", "high"}]
        audit_record = self.audit_ledger.append(
            "signal_counterintelligence_review",
            {
                "signal": signal.to_dict(),
                "findings": [finding.to_dict() for finding in findings],
                "decision": decision.value,
                "mode": mode.value,
                "execution_allowed": execution_allowed,
                "source_reports": [report.to_dict() for report in source_reports],
            },
        )
        return SignalCounterintelligenceReport(
            signal.signal_id,
            decision,
            accepted,
            findings,
            source_reports,
            round(compliance_score, 4),
            round(reliability_score, 4),
            blocked_reasons,
            audit_record.record_hash,
            mode,
            execution_allowed,
        )

    def review_raw_signal(
        self,
        raw_signal: Any,
        mode: Optional[CounterintelligenceMode] = None,
        mission: Optional[MissionRequirement] = None,
        sources: Optional[Sequence[DataSourceProvenance]] = None,
        evidence: Optional[Sequence[IntelligenceEvidence]] = None,
    ) -> SignalCounterintelligenceReport:
        mode = _coerce_counterintelligence_mode(mode or self.mode)
        if self.passport_proxy is not None:
            payload = SignalIntelligenceAdapter()._as_mapping(raw_signal)
            accepted, passport_reasons = self.passport_proxy.require_passport(payload)
            if not accepted and mode == CounterintelligenceMode.HARD_GATE:
                signal_id = str(payload.get("signal_id") or payload.get("id") or "unpassported-message")
                finding = self._finding(
                    SignalAttackVector.MISSING_PROVENANCE,
                    "critical",
                    "inbound message rejected by data-passport sidecar: " + "; ".join(passport_reasons),
                    [],
                )
                audit_record = self.audit_ledger.append(
                    "data_passport_rejection",
                    {"signal_id": signal_id, "reasons": passport_reasons},
                )
                return SignalCounterintelligenceReport(
                    signal_id,
                    IntelligenceDecision.REJECT,
                    False,
                    [finding],
                    [],
                    0.0,
                    0.0,
                    [finding.description],
                    audit_record.record_hash,
                    mode,
                    False,
                )
        package = SignalIntelligenceAdapter().adapt(raw_signal, mission, sources, evidence)
        return self.review_signal(package.signal, package.sources, package.evidence, mode=mode)

    def _overfit_reason(self, features: Dict[str, float]) -> Optional[str]:
        train = features.get("train_sharpe")
        validation = features.get("validation_sharpe")
        sample_size = features.get("sample_size")
        p_value = features.get("p_value")
        if train is not None and validation is not None and train > validation * 2.0 and train - validation > 1.0:
            return f"train Sharpe {train:.2f} is not supported by validation Sharpe {validation:.2f}"
        if sample_size is not None and sample_size < 60 and features.get("confidence", 0.0) > 0.70:
            return f"sample size {sample_size:.0f} is too small for high-confidence signal"
        if p_value is not None and p_value <= 0.000001:
            return "suspicious p-value may indicate p-hacking or leakage"
        return None

    def _weak_claim(self, signal: SignalClaim, reports: Sequence[SourceValidationReport]) -> bool:
        accepted_sources = sum(1 for report in reports if report.accepted)
        if signal.confidence > 0.75 and accepted_sources < 2:
            return True
        if not signal.evidence_ids or not signal.source_ids:
            return True
        return False

    def _adversarial_gauntlet_findings(
        self,
        signal: SignalClaim,
        evidence: Sequence[IntelligenceEvidence],
    ) -> List[CounterintelligenceFinding]:
        findings: List[CounterintelligenceFinding] = []
        features = dict(signal.features)
        for item in evidence:
            for key, value in item.features.items():
                features.setdefault(key, value)
        live_gate_required = self._requires_live_gate(signal)

        if bool(features.get("lookahead_bias_detected", False)):
            findings.append(self._finding(
                SignalAttackVector.DATA_LEAKAGE,
                "critical",
                "point-in-time replay detected look-ahead bias",
                signal.evidence_ids,
            ))
        if live_gate_required and features.get("point_in_time_replay_passed") is False:
            findings.append(self._finding(
                SignalAttackVector.DATA_LEAKAGE,
                "critical",
                "data leakage scanner failed point-in-time replay",
                signal.evidence_ids,
            ))

        for required_flag, description in {
            "purged_cv_passed": "purged cross-validation failed or was not supplied",
            "embargoed_cv_passed": "embargoed cross-validation failed or was not supplied",
            "walk_forward_passed": "walk-forward validation failed or was not supplied",
            "out_of_sample_holdout_passed": "out-of-sample holdout failed or was not supplied",
        }.items():
            if live_gate_required and features.get(required_flag) is not True:
                findings.append(self._finding(
                    SignalAttackVector.OVERFITTING,
                    "high",
                    description,
                    signal.evidence_ids,
                ))

        alternate_survival = features.get("alternate_history_survival_rate")
        if alternate_survival is not None and float(alternate_survival) < 0.95:
            findings.append(self._finding(
                SignalAttackVector.OVERFITTING,
                "high",
                f"signal survived only {float(alternate_survival):.1%} of alternate-history perturbations",
                signal.evidence_ids,
            ))

        adversarial_drop = features.get("adversarial_sharpe_drop")
        if adversarial_drop is not None and float(adversarial_drop) > 0.20:
            findings.append(self._finding(
                SignalAttackVector.ADVERSARIAL_MARKET_BEHAVIOR,
                "high",
                f"adversarial market emulator reduced Sharpe by {float(adversarial_drop):.1%}",
                signal.evidence_ids,
            ))

        for required_flag, description in {
            "out_of_regime_passed": "out-of-regime regime saboteur test failed or was not supplied",
            "black_swan_passed": "black-swan regime behavior failed or was not supplied",
        }.items():
            if live_gate_required and features.get(required_flag) is not True:
                findings.append(self._finding(
                    SignalAttackVector.REGIME_FRAGILITY,
                    "high",
                    description,
                    signal.evidence_ids,
                ))

        if live_gate_required and features.get("causal_plausibility_passed") is not True:
            findings.append(self._finding(
                SignalAttackVector.CAUSAL_PLAUSIBILITY_FAILURE,
                "high",
                "causal plausibility check failed or was not supplied",
                signal.evidence_ids,
            ))

        crowding_erosion = features.get("crowding_edge_erosion")
        if crowding_erosion is not None and float(crowding_erosion) > 0.50:
            findings.append(self._finding(
                SignalAttackVector.CROWDING_CAPACITY_RISK,
                "high",
                f"crowding sensor estimates {float(crowding_erosion):.1%} edge erosion",
                signal.evidence_ids,
            ))

        for required_flag, description in {
            "transaction_costs_included": "transaction costs were not included",
            "slippage_modeled": "slippage was not modeled",
            "capacity_estimated": "capacity was not estimated",
            "latency_stress_passed": "latency stress test failed or was not supplied",
            "broker_execution_replay_passed": "broker execution replay failed or was not supplied",
            "paper_trading_passed": "paper trading failed or was not supplied",
        }.items():
            if live_gate_required and features.get(required_flag) is not True:
                findings.append(self._finding(
                    SignalAttackVector.EXECUTION_STRESS_FAILURE,
                    "high",
                    description,
                    signal.evidence_ids,
                ))

        if live_gate_required:
            checklist = PromotionGateChecklist(
                hypothesis_written=bool(features.get("hypothesis_written")),
                data_manifest_attached=bool(features.get("data_manifest_attached")),
                leakage_test_passed=bool(features.get("leakage_test_passed")),
                walk_forward_passed=bool(features.get("walk_forward_passed")),
                transaction_costs_included=bool(features.get("transaction_costs_included")),
                slippage_modeled=bool(features.get("slippage_modeled")),
                capacity_estimated=bool(features.get("capacity_estimated")),
                regime_behavior_known=bool(features.get("regime_behavior_known")),
                risk_impact_approved=bool(features.get("risk_impact_approved")),
                paper_trading_passed=bool(features.get("paper_trading_passed")),
            )
            if not checklist.accepted:
                findings.append(self._finding(
                    SignalAttackVector.PROMOTION_GATE_FAILURE,
                    "high",
                    "live-signal promotion checklist incomplete: " + ", ".join(checklist.missing_items),
                    signal.evidence_ids,
                ))
        return findings

    def _requires_live_gate(self, signal: SignalClaim) -> bool:
        action = signal.proposed_action.lower()
        if signal.features.get("go_live") or signal.features.get("promotion_required"):
            return True
        return action not in {"research_only", "research", "observe", "hold", "paper"}

    def _execution_allowed(self, accepted: bool, mode: CounterintelligenceMode) -> bool:
        if mode == CounterintelligenceMode.HARD_GATE:
            return accepted
        if mode == CounterintelligenceMode.ADVISORY:
            return True
        return False

    def _finding(
        self,
        vector: SignalAttackVector,
        severity: str,
        description: str,
        evidence_ids: Sequence[str],
    ) -> CounterintelligenceFinding:
        finding_id = hashlib.sha256(f"{vector.value}:{severity}:{description}:{','.join(evidence_ids)}".encode("utf-8")).hexdigest()[:16]
        return CounterintelligenceFinding(finding_id, vector, severity, description, list(evidence_ids))

    def _mean(self, values: Iterable[float]) -> float:
        values_list = list(values)
        return sum(values_list) / len(values_list) if values_list else 0.0


class DecisionGovernanceSystem:
    """Signal validator, risk gatekeeper, capital judge, kill switch, and audit gate."""

    def evaluate(
        self,
        ci_report: SignalCounterintelligenceReport,
        access: AccessDecision,
        mission: MissionRequirement,
        kill_switch_active: bool = False,
        kill_switch_level: KillSwitchLevel = KillSwitchLevel.NONE,
        audit_logger_enabled: bool = True,
    ) -> DecisionGovernanceReport:
        reasons: List[str] = []
        kill_switch_level = _coerce_kill_switch_level(kill_switch_level)
        signal_validator_passed = ci_report.accepted
        if not signal_validator_passed:
            reasons.extend(ci_report.blocked_reasons or ["signal validator rejected or quarantined claim"])
        risk_gatekeeper_passed = mission.risk_budget > 0 and mission.risk_budget <= 0.05
        if not risk_gatekeeper_passed:
            reasons.append("risk budget must be positive and no greater than 5%")
        capital_allocation_judge_passed = access.accepted and signal_validator_passed and risk_gatekeeper_passed
        if not access.accepted:
            reasons.extend(access.reasons)
        if kill_switch_active:
            reasons.append("kill switch active")
        if kill_switch_level != KillSwitchLevel.NONE:
            reasons.append(f"kill switch level active: {kill_switch_level.value}")
        if not audit_logger_enabled:
            reasons.append("immutable audit logger unavailable")
        if kill_switch_active or kill_switch_level != KillSwitchLevel.NONE or not audit_logger_enabled or not access.accepted or ci_report.decision == IntelligenceDecision.REJECT:
            decision = IntelligenceDecision.REJECT
        elif not capital_allocation_judge_passed or ci_report.decision == IntelligenceDecision.QUARANTINE:
            decision = IntelligenceDecision.QUARANTINE
        else:
            decision = IntelligenceDecision.ACCEPT
        return DecisionGovernanceReport(
            signal_validator_passed,
            risk_gatekeeper_passed,
            capital_allocation_judge_passed,
            kill_switch_active,
            audit_logger_enabled,
            decision,
            reasons,
            kill_switch_level,
        )


class AlphaAlgoIntelligenceDirectorate:
    """Eight-layer intelligence directorate for governed financial decisions."""

    analysis_cells = (
        "macro",
        "microstructure",
        "sentiment",
        "volatility",
        "liquidity",
        "risk",
        "execution_feasibility",
    )

    def __init__(
        self,
        counterintelligence: Optional[SignalCounterintelligenceEngine] = None,
        security_model: Optional[CompartmentalizedSecurityModel] = None,
        collection_layer: Optional[LegalCollectionLayer] = None,
        model_registry: Optional[ModelArtifactRegistry] = None,
        audit_ledger: Optional[ImmutableAuditLedger] = None,
        compliance_ledger: Optional[ComplianceLicenseLedger] = None,
        passport_proxy: Optional[DataPassportSidecarProxy] = None,
        zone_policy: Optional[ZeroTrustZonePolicy] = None,
        mode: CounterintelligenceMode = CounterintelligenceMode.HARD_GATE,
    ):
        self.mode = _coerce_counterintelligence_mode(mode)
        self.audit_ledger = audit_ledger or AppendOnlyJsonlAuditLedger()
        self.compliance_ledger = compliance_ledger or ComplianceLicenseLedger()
        self.passport_proxy = passport_proxy or DataPassportSidecarProxy(compliance_ledger=self.compliance_ledger)
        self.counterintelligence = counterintelligence or SignalCounterintelligenceEngine(
            source_validator=SourceValidationLayer(compliance_ledger=self.compliance_ledger),
            audit_ledger=self.audit_ledger,
            mode=self.mode,
            passport_proxy=self.passport_proxy,
        )
        self.security_model = security_model or CompartmentalizedSecurityModel()
        self.zone_policy = zone_policy or ZeroTrustZonePolicy()
        self.collection_layer = collection_layer or LegalCollectionLayer()
        self.model_registry = model_registry or ModelArtifactRegistry()
        self.promotion_chain = ModelPromotionChain(self.model_registry, self.audit_ledger, self.zone_policy)
        self.feedback_monitor = SignalFeedbackMonitor(self.audit_ledger)
        self.governance_system = DecisionGovernanceSystem()
        self.adapter = SignalIntelligenceAdapter()

    def evaluate(
        self,
        mission: MissionRequirement,
        signal: SignalClaim,
        sources: Sequence[DataSourceProvenance],
        evidence: Sequence[IntelligenceEvidence],
        role: IntelligenceRole = IntelligenceRole.RESEARCH_ANALYST,
        compartment: IntelligenceCompartment = IntelligenceCompartment.RESEARCH,
        collection_tasks: Optional[Sequence[CollectionTask]] = None,
        production_model_artifact: Optional[SignedModelArtifact] = None,
        feedback_metrics: Optional[Dict[str, float]] = None,
        mode: Optional[CounterintelligenceMode] = None,
        kill_switch_active: bool = False,
        kill_switch_level: KillSwitchLevel = KillSwitchLevel.NONE,
        audit_logger_enabled: bool = True,
    ) -> DirectorateRunReport:
        mode = _coerce_counterintelligence_mode(mode or self.mode)
        kill_switch_level = _coerce_kill_switch_level(kill_switch_level)
        self._ensure_license_records(sources)
        collection_plan = (
            self.collection_layer.plan(mission, collection_tasks)
            if collection_tasks is not None
            else self.collection_layer.from_sources(mission, sources)
        )
        source_reports = self.counterintelligence.source_validator.validate_many(sources)
        model_artifact_report = self.model_registry.access_report(production_model_artifact, role) if production_model_artifact else None
        fusion_report = self._build_fusion_report(signal, sources, evidence)
        fusion_graph = fusion_report.to_dict()
        analysis_outputs = self._run_analysis_cells(signal, evidence)
        ci_report = self.counterintelligence.review_signal(signal, sources, evidence, mode=mode)
        access = self.security_model.validate_access(
            role,
            compartment,
            "analyze signal",
            kill_switch_active=kill_switch_active,
        )
        governance_report = self.governance_system.evaluate(
            ci_report,
            access,
            mission,
            kill_switch_active=kill_switch_active,
            kill_switch_level=kill_switch_level,
            audit_logger_enabled=audit_logger_enabled,
        )
        if not collection_plan.accepted:
            governance_report.decision = IntelligenceDecision.REJECT
            governance_report.reasons.extend(collection_plan.compliance_notes)
        if model_artifact_report and not model_artifact_report.accepted:
            governance_report.decision = IntelligenceDecision.REJECT
            governance_report.reasons.extend(model_artifact_report.reasons)
        governance_decision = governance_report.decision
        feedback_report = self._build_feedback_report(feedback_metrics)
        if feedback_report.strategy_decay_detected and governance_decision == IntelligenceDecision.ACCEPT:
            governance_report.decision = IntelligenceDecision.QUARANTINE
            governance_report.reasons.append("strategy decay detected by feedback monitor")
            governance_decision = governance_report.decision
        if feedback_report.kill_switch_level != KillSwitchLevel.NONE:
            governance_report.decision = IntelligenceDecision.REJECT
            governance_report.kill_switch_level = feedback_report.kill_switch_level
            governance_report.reasons.append(f"feedback monitor requested kill switch level {feedback_report.kill_switch_level.value}")
            governance_decision = governance_report.decision
        audit_record = self.audit_ledger.append(
            "alphaalgo_intelligence_directorate_decision",
            {
                "mission": mission.to_dict(),
                "collection_plan": collection_plan.to_dict(),
                "signal_id": signal.signal_id,
                "mode": mode.value,
                "fusion_report": fusion_report.to_dict(),
                "counterintelligence": ci_report.to_dict(),
                "governance_report": governance_report.to_dict(),
                "governance_decision": governance_decision.value,
                "access": access.to_dict(),
                "model_artifact_report": model_artifact_report.to_dict() if model_artifact_report else None,
                "feedback_report": feedback_report.to_dict(),
            },
        )
        return DirectorateRunReport(
            mission,
            collection_plan,
            source_reports,
            model_artifact_report,
            fusion_report,
            fusion_graph,
            analysis_outputs,
            ci_report,
            governance_report,
            governance_decision,
            access,
            feedback_report,
            feedback_report.to_dict(),
            audit_record,
        )

    def evaluate_raw_signal(
        self,
        raw_signal: Any,
        role: IntelligenceRole = IntelligenceRole.RESEARCH_ANALYST,
        compartment: IntelligenceCompartment = IntelligenceCompartment.RESEARCH,
        production_model_artifact: Optional[SignedModelArtifact] = None,
        feedback_metrics: Optional[Dict[str, float]] = None,
        mode: Optional[CounterintelligenceMode] = None,
        kill_switch_active: bool = False,
        kill_switch_level: KillSwitchLevel = KillSwitchLevel.NONE,
        audit_logger_enabled: bool = True,
    ) -> DirectorateRunReport:
        package = self.adapter.adapt(raw_signal)
        return self.evaluate(
            package.mission,
            package.signal,
            package.sources,
            package.evidence,
            role=role,
            compartment=compartment,
            production_model_artifact=production_model_artifact,
            feedback_metrics=feedback_metrics,
            mode=mode,
            kill_switch_active=kill_switch_active,
            kill_switch_level=kill_switch_level,
            audit_logger_enabled=audit_logger_enabled,
        )

    def _build_fusion_report(
        self,
        signal: SignalClaim,
        sources: Sequence[DataSourceProvenance],
        evidence: Sequence[IntelligenceEvidence],
    ) -> FusionKnowledgeReport:
        entity_resolution = {"asset": signal.asset, "source_count": len(sources)}
        cross_asset_links = {
            "strength": float(signal.features.get("cross_asset_links", 0.0)),
            "asset_count": float(signal.features.get("linked_asset_count", 1.0)),
        }
        event_graph = [
            {"evidence_id": item.evidence_id, "source_id": item.source_id, "claim": item.claim}
            for item in evidence
        ]
        regime_memory = {
            "regime": signal.features.get("regime", "unknown"),
            "horizon": signal.horizon,
        }
        strategy_evidence_graph = {
            "signal": signal.signal_id,
            "sources": [source.source_id for source in sources],
            "evidence": [item.evidence_id for item in evidence],
        }
        digest_payload = {
            "entity_resolution": entity_resolution,
            "cross_asset_links": cross_asset_links,
            "event_graph": event_graph,
            "regime_memory": regime_memory,
            "strategy_evidence_graph": strategy_evidence_graph,
        }
        graph_digest = hashlib.sha256(json.dumps(digest_payload, sort_keys=True).encode("utf-8")).hexdigest()
        return FusionKnowledgeReport(
            entity_resolution,
            cross_asset_links,
            event_graph,
            regime_memory,
            strategy_evidence_graph,
            graph_digest,
        )

    def _ensure_license_records(self, sources: Sequence[DataSourceProvenance]) -> None:
        for source in sources:
            if source.license_id in self.compliance_ledger.licenses:
                self.compliance_ledger.is_license_active(source.license_id)
                continue
            self.compliance_ledger.register_license(
                source=source.name,
                license_status=source.license_status,
                permission_basis=source.permission_basis,
                data_vendor=source.data_vendor,
                expires_at=source.license_expires_at,
                license_id=source.license_id,
                actor="directorate",
                issued_at=source.collected_at,
                terms_hash=hashlib.sha256(
                    f"{source.license_name}:{source.permission_basis}".encode("utf-8")
                ).hexdigest(),
            )

    def _run_analysis_cells(self, signal: SignalClaim, evidence: Sequence[IntelligenceEvidence]) -> List[AnalysisCellOutput]:
        outputs = []
        evidence_ids = [item.evidence_id for item in evidence]
        for cell in self.analysis_cells:
            cell_feature = float(signal.features.get(f"{cell}_confidence", signal.confidence * 0.85))
            outputs.append(AnalysisCellOutput(
                cell_name=cell,
                summary=f"{cell} cell reviewed {signal.asset} signal for {signal.horizon}",
                confidence=round(max(0.0, min(1.0, cell_feature)), 4),
                evidence_ids=evidence_ids,
            ))
        return outputs

    def _build_feedback_report(self, feedback_metrics: Optional[Dict[str, float]]) -> FeedbackEvaluationReport:
        metrics = feedback_metrics or {}
        decay_score = float(metrics.get("strategy_decay_score", 0.0))
        staging_sharpe = float(metrics.get("staging_test_sharpe", 0.0))
        out_of_sample_sharpe = float(metrics.get("out_of_sample_sharpe", 0.0))
        sharpe_decay = staging_sharpe > 0 and out_of_sample_sharpe < staging_sharpe * 0.50
        decay_detected = decay_score >= 0.70 or sharpe_decay
        kill_switch_level = _coerce_kill_switch_level(metrics.get("kill_switch_level", KillSwitchLevel.NONE))
        signal_health_status = IntelligenceDecision.QUARANTINE if decay_detected else IntelligenceDecision.ACCEPT
        return FeedbackEvaluationReport(
            forecast_accuracy=float(metrics.get("forecast_accuracy", 0.0)),
            pnl_attribution=float(metrics.get("pnl_attribution", 0.0)),
            slippage_attribution=float(metrics.get("slippage_attribution", 0.0)),
            regime_specific_performance=float(metrics.get("regime_specific_performance", 0.0)),
            strategy_decay_score=decay_score,
            strategy_decay_detected=decay_detected,
            staging_test_sharpe=staging_sharpe,
            out_of_sample_sharpe=out_of_sample_sharpe,
            signal_health_status=signal_health_status,
            kill_switch_level=kill_switch_level,
            quarantine_recommended=decay_detected or kill_switch_level != KillSwitchLevel.NONE,
        )


class SignalFeedbackMonitor:
    """Runtime feedback loop for attribution, decay alerts, and kill post-mortems."""

    def __init__(self, audit_ledger: Optional[ImmutableAuditLedger] = None):
        self.audit_ledger = audit_ledger or AppendOnlyJsonlAuditLedger()
        self.post_mortems: List[Dict[str, Any]] = []

    def evaluate_signal_health(
        self,
        signal_id: str,
        staging_test_sharpe: float,
        out_of_sample_sharpe: float,
        pnl_attribution: float,
        risk_attribution: float,
        regime: str,
        kill_switch_level: KillSwitchLevel = KillSwitchLevel.NONE,
    ) -> SignalHealthReport:
        kill_switch_level = _coerce_kill_switch_level(kill_switch_level)
        reasons: List[str] = []
        decay_detected = staging_test_sharpe > 0 and out_of_sample_sharpe < staging_test_sharpe * 0.50
        if decay_detected:
            reasons.append("out-of-sample Sharpe fell below 50% of staging test Sharpe")
        if kill_switch_level != KillSwitchLevel.NONE:
            reasons.append(f"kill switch level active: {kill_switch_level.value}")
        status = (
            IntelligenceDecision.REJECT
            if kill_switch_level != KillSwitchLevel.NONE
            else (IntelligenceDecision.QUARANTINE if decay_detected else IntelligenceDecision.ACCEPT)
        )
        report = SignalHealthReport(
            signal_id=signal_id,
            status=status,
            staging_test_sharpe=staging_test_sharpe,
            out_of_sample_sharpe=out_of_sample_sharpe,
            pnl_attribution=pnl_attribution,
            risk_attribution=risk_attribution,
            regime=regime,
            decay_detected=decay_detected,
            kill_switch_level=kill_switch_level,
            reasons=reasons,
        )
        self.audit_ledger.append(
            "signal_feedback_health",
            report.to_dict(),
            actor="feedback-monitor",
            action="evaluate_signal_health",
            input_hash=hashlib.sha256(signal_id.encode("utf-8")).hexdigest(),
        )
        return report

    def record_kill_post_mortem(
        self,
        signal_id: str,
        kill_reason: str,
        lessons: Sequence[str],
        reviewer: str = "risk",
    ) -> ImmutableAuditRecord:
        post_mortem = {
            "signal_id": signal_id,
            "kill_reason": kill_reason,
            "lessons": list(lessons),
            "reviewer": reviewer,
            "created_at": time.time(),
        }
        self.post_mortems.append(post_mortem)
        return self.audit_ledger.append(
            "signal_kill_post_mortem",
            post_mortem,
            actor=reviewer,
            action="record_kill_post_mortem",
        )


def validate_intelligence_metadata(
    metadata: Optional[Mapping[str, Any]],
    mode: CounterintelligenceMode = CounterintelligenceMode.HARD_GATE,
) -> Tuple[bool, List[str]]:
    """Validate execution metadata required by the hard gate."""

    mode = _coerce_counterintelligence_mode(mode)
    if mode != CounterintelligenceMode.HARD_GATE:
        return True, []

    envelope = _extract_intelligence_metadata(metadata or {})
    reasons: List[str] = []
    decision = str(
        envelope.get("decision")
        or envelope.get("counterintelligence_decision")
        or ""
    ).lower()
    governance_decision = str(envelope.get("governance_decision") or "").lower()
    source_lineage_hashes = envelope.get("source_lineage_hashes") or envelope.get("lineage_hashes")
    if decision != IntelligenceDecision.ACCEPT.value:
        reasons.append("counterintelligence decision must be accept")
    if governance_decision and governance_decision != IntelligenceDecision.ACCEPT.value:
        reasons.append("governance decision must be accept")
    if not envelope.get("audit_digest"):
        reasons.append("audit_digest is required")
    if not source_lineage_hashes:
        reasons.append("source lineage hashes are required")
    if not envelope.get("governance_decision_id"):
        reasons.append("governance_decision_id is required")
    if envelope.get("execution_allowed") is False:
        reasons.append("intelligence metadata does not allow execution")
    if str(envelope.get("license_status", "")).lower() in {
        LicenseLedgerStatus.EXPIRED.value,
        LicenseLedgerStatus.REVOKED.value,
    }:
        reasons.append("license is not active")
    if str(envelope.get("signal_health_status", "")).lower() in {
        IntelligenceDecision.QUARANTINE.value,
        IntelligenceDecision.REJECT.value,
        "decayed",
        "killed",
    }:
        reasons.append("signal health does not allow execution")
    kill_switch_level = _coerce_kill_switch_level(envelope.get("kill_switch_level", KillSwitchLevel.NONE))
    if kill_switch_level != KillSwitchLevel.NONE:
        reasons.append(f"kill switch level blocks execution: {kill_switch_level.value}")
    position_after_trade = envelope.get("position_after_trade")
    position_limit = envelope.get("position_limit")
    if position_after_trade is not None and position_limit is not None:
        try:
            if abs(float(position_after_trade)) > abs(float(position_limit)):
                reasons.append("position limit would be exceeded")
        except (TypeError, ValueError):
            reasons.append("position limit metadata is invalid")
    var_after_trade = envelope.get("var_after_trade")
    var_limit = envelope.get("var_limit")
    if var_after_trade is not None and var_limit is not None:
        try:
            if float(var_after_trade) > float(var_limit):
                reasons.append("VaR limit would be exceeded")
        except (TypeError, ValueError):
            reasons.append("VaR metadata is invalid")
    return not reasons, reasons


def _extract_intelligence_metadata(metadata: Mapping[str, Any]) -> Dict[str, Any]:
    if not metadata:
        return {}
    if "intelligence" in metadata and isinstance(metadata["intelligence"], Mapping):
        return dict(metadata["intelligence"])
    if "counterintelligence" in metadata and isinstance(metadata["counterintelligence"], Mapping):
        return dict(metadata["counterintelligence"])
    if "intelligence_metadata" in metadata and isinstance(metadata["intelligence_metadata"], Mapping):
        return dict(metadata["intelligence_metadata"])
    return dict(metadata)


def _coerce_counterintelligence_mode(value: Any) -> CounterintelligenceMode:
    if isinstance(value, CounterintelligenceMode):
        return value
    try:
        return CounterintelligenceMode(str(value))
    except ValueError:
        return CounterintelligenceMode.HARD_GATE


def _coerce_source_license(value: Any) -> SourceLicenseStatus:
    if isinstance(value, SourceLicenseStatus):
        return value
    try:
        return SourceLicenseStatus(str(value))
    except ValueError:
        return SourceLicenseStatus.UNKNOWN


def _coerce_license_ledger_status(value: Any) -> LicenseLedgerStatus:
    if isinstance(value, LicenseLedgerStatus):
        return value
    try:
        return LicenseLedgerStatus(str(value))
    except ValueError:
        return LicenseLedgerStatus.REVOKED


def _coerce_kill_switch_level(value: Any) -> KillSwitchLevel:
    if isinstance(value, KillSwitchLevel):
        return value
    try:
        return KillSwitchLevel(str(value))
    except ValueError:
        return KillSwitchLevel.NONE


def _coerce_data_category(value: Any) -> DataSourceCategory:
    if isinstance(value, DataSourceCategory):
        return value
    try:
        return DataSourceCategory(str(value))
    except ValueError:
        return DataSourceCategory.INTERNAL_GENERATED


def _coerce_intelligence_zone(value: Any) -> IntelligenceZone:
    if isinstance(value, IntelligenceZone):
        return value
    try:
        return IntelligenceZone(str(value))
    except ValueError:
        return IntelligenceZone.RESEARCH


def _coerce_timestamp(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, datetime):
        return value.timestamp()
    text = str(value).strip()
    if not text:
        return 0.0
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return 0.0


__all__ = [
    "AccessDecision",
    "AlphaAlgoIntelligenceDirectorate",
    "AppendOnlyJsonlAuditLedger",
    "AnalysisCellOutput",
    "ComplianceLicenseLedger",
    "CompartmentalizedSecurityModel",
    "CounterintelligenceMode",
    "CounterintelligenceFinding",
    "CollectionPlan",
    "CollectionTask",
    "DataLicenseRecord",
    "DataPassport",
    "DataPassportSidecarProxy",
    "DataPassportValidationResult",
    "DataSourceCategory",
    "DataSourceProvenance",
    "DecisionGovernanceReport",
    "DecisionGovernanceSystem",
    "DirectorateRunReport",
    "FeedbackEvaluationReport",
    "FusionKnowledgeReport",
    "ImmutableAuditLedger",
    "ImmutableAuditRecord",
    "IntelligenceZone",
    "IntelligenceCompartment",
    "IntelligenceDecision",
    "IntelligenceEvidence",
    "IntelligenceRole",
    "KillSwitchLevel",
    "LegalCollectionLayer",
    "LicenseLedgerEvent",
    "LicenseLedgerStatus",
    "MissionRequirement",
    "ModelPromotionChain",
    "ModelPromotionReport",
    "ModelArtifactRegistry",
    "PromotionGateChecklist",
    "SignalAttackVector",
    "SignalClaim",
    "SignalCounterintelligenceEngine",
    "SignalCounterintelligenceReport",
    "SignalFeedbackMonitor",
    "SignalHealthReport",
    "SignalIntelligenceAdapter",
    "SignalIntelligencePackage",
    "SignedModelArtifact",
    "SourceLicenseStatus",
    "SourceValidationLayer",
    "SourceValidationReport",
    "ZeroTrustZonePolicy",
    "validate_intelligence_metadata",
]

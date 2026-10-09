"""Clean-room browser/reasoning research harness for AlphaAlgo.

This module combines public design patterns from browser-using agents and
Aletheia-style generate/verify/revise research loops, but keeps AlphaAlgo's
financial compliance rules in front: legal data only, signed passports,
source lineage, immutable audit, and no uncited claims.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlparse

from trading_bot.core.signal_counterintelligence import (
    AppendOnlyJsonlAuditLedger,
    DataPassportSidecarProxy,
    DataPassportValidationResult,
    DataSourceCategory,
    DataSourceProvenance,
    ImmutableAuditLedger,
    IntelligenceDecision,
    IntelligenceEvidence,
    SourceLicenseStatus,
    SourceValidationLayer,
)


class BrowserActionType(str, Enum):
    """Supported browser-control intentions."""

    OBSERVE = "observe"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    EXTRACT = "extract"
    STOP = "stop"


@dataclass
class BrowserAction:
    """One low-level browser action with safety metadata."""

    action_type: BrowserActionType
    target: str
    value: str = ""
    reason: str = ""
    risk_level: str = "low"
    requires_human_confirmation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["action_type"] = self.action_type.value
        return data


@dataclass
class BrowserTaskPlan:
    """A browser-use style plan with allowed domains and guardrails."""

    task_id: str
    goal: str
    start_urls: List[str]
    allowed_domains: List[str]
    actions: List[BrowserAction]
    rejected_reasons: List[str] = field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return not self.rejected_reasons

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "start_urls": list(self.start_urls),
            "allowed_domains": list(self.allowed_domains),
            "actions": [action.to_dict() for action in self.actions],
            "rejected_reasons": list(self.rejected_reasons),
            "accepted": self.accepted,
        }


@dataclass
class BrowserObservation:
    """Observation extracted from a page by a browser agent."""

    observation_id: str
    url: str
    title: str
    extracted_text: str
    extracted_facts: List[str]
    source: DataSourceProvenance
    observed_at: float = field(default_factory=time.time)
    screenshot_hash: str = ""
    passport_validation: Optional[DataPassportValidationResult] = None

    def __post_init__(self) -> None:
        if not self.screenshot_hash:
            payload = f"{self.url}:{self.title}:{self.extracted_text[:2048]}"
            self.screenshot_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "url": self.url,
            "title": self.title,
            "extracted_text_hash": hashlib.sha256(self.extracted_text.encode("utf-8")).hexdigest(),
            "extracted_facts": list(self.extracted_facts),
            "source": self.source.to_dict(),
            "observed_at": self.observed_at,
            "screenshot_hash": self.screenshot_hash,
            "passport_validation": (
                self.passport_validation.to_dict() if self.passport_validation else None
            ),
        }


@dataclass
class AletheiaClaim:
    """One generated claim with mandatory citations."""

    claim_id: str
    text: str
    citations: List[str]
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationIssue:
    """Verifier finding against a generated claim."""

    claim_id: str
    severity: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AletheiaResearchAttempt:
    """One generate/verify/revise pass."""

    round_index: int
    generated_claims: List[AletheiaClaim]
    issues: List[VerificationIssue]
    revised_claims: List[AletheiaClaim]
    decision: IntelligenceDecision

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_index": self.round_index,
            "generated_claims": [claim.to_dict() for claim in self.generated_claims],
            "issues": [issue.to_dict() for issue in self.issues],
            "revised_claims": [claim.to_dict() for claim in self.revised_claims],
            "decision": self.decision.value,
        }


@dataclass
class AletheiaBrowserResearchReport:
    """Final browser/research harness report."""

    task_plan: BrowserTaskPlan
    question: str
    decision: IntelligenceDecision
    accepted_claims: List[AletheiaClaim]
    attempts: List[AletheiaResearchAttempt]
    evidence: List[IntelligenceEvidence]
    source_lineage_hashes: List[str]
    audit_digest: str
    confidence: float
    blocked_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_plan": self.task_plan.to_dict(),
            "question": self.question,
            "decision": self.decision.value,
            "accepted_claims": [claim.to_dict() for claim in self.accepted_claims],
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "evidence": [item.to_dict() for item in self.evidence],
            "source_lineage_hashes": list(self.source_lineage_hashes),
            "audit_digest": self.audit_digest,
            "confidence": self.confidence,
            "blocked_reasons": list(self.blocked_reasons),
        }


class AlphaAlgoBrowserUsePlanner:
    """Browser-use style planner with financial-domain safety rails."""

    sensitive_terms = {"password", "login", "checkout", "order", "trade", "wire", "payment", "broker"}

    def plan(self, goal: str, start_urls: Sequence[str], allowed_domains: Sequence[str]) -> BrowserTaskPlan:
        task_id = hashlib.sha256(f"{goal}:{','.join(start_urls)}:{time.time():.6f}".encode("utf-8")).hexdigest()[:16]
        normalized_domains = sorted({self._domain(domain) for domain in allowed_domains if domain})
        reasons: List[str] = []
        for url in start_urls:
            domain = self._domain(url)
            if normalized_domains and domain not in normalized_domains:
                reasons.append(f"url {url} is outside allowed domains")
        if not start_urls:
            reasons.append("browser task requires at least one start URL")
        goal_lower = goal.lower()
        sensitive = any(term in goal_lower for term in self.sensitive_terms)
        actions = [
            BrowserAction(BrowserActionType.OBSERVE, "page", reason="inspect visible page state"),
            BrowserAction(BrowserActionType.EXTRACT, "citations", reason="extract cited public facts"),
            BrowserAction(
                BrowserActionType.STOP,
                "handoff",
                reason="stop before credential, trade, payment, or order submission",
                risk_level="high" if sensitive else "low",
                requires_human_confirmation=sensitive,
            ),
        ]
        return BrowserTaskPlan(task_id, goal, list(start_urls), normalized_domains, actions, reasons)

    def _domain(self, value: str) -> str:
        parsed = urlparse(value if "://" in value else f"https://{value}")
        return parsed.netloc.lower()


class AlphaAletheiaVerifier:
    """Aletheia-style verifier: every claim must survive adversarial scrutiny."""

    forbidden_terms = {"insider", "non-public", "nonpublic", "leaked", "confidential", "mnpi"}

    def verify(self, claims: Sequence[AletheiaClaim], observations: Sequence[BrowserObservation]) -> List[VerificationIssue]:
        observation_ids = {observation.observation_id for observation in observations}
        fact_index = {
            observation.observation_id: {self._normalize(fact) for fact in observation.extracted_facts}
            for observation in observations
        }
        issues: List[VerificationIssue] = []
        for claim in claims:
            claim_lower = claim.text.lower()
            if any(term in claim_lower for term in self.forbidden_terms):
                issues.append(VerificationIssue(claim.claim_id, "critical", "claim uses private, leaked, confidential, or MNPI language"))
            if not claim.citations:
                issues.append(VerificationIssue(claim.claim_id, "high", "claim has no citation"))
                continue
            missing = [citation for citation in claim.citations if citation not in observation_ids]
            if missing:
                issues.append(VerificationIssue(claim.claim_id, "high", "claim cites unknown observations: " + ", ".join(missing)))
            support_count = 0
            normalized_claim = self._normalize(claim.text)
            for citation in claim.citations:
                if citation in fact_index and any(fact in normalized_claim or normalized_claim in fact for fact in fact_index[citation]):
                    support_count += 1
            if support_count == 0:
                issues.append(VerificationIssue(claim.claim_id, "high", "claim is not supported by cited facts"))
            if claim.confidence > 0.80 and len(set(claim.citations)) < 2:
                issues.append(VerificationIssue(claim.claim_id, "medium", "high-confidence claim requires two-source corroboration"))
        return issues

    def revise(self, claims: Sequence[AletheiaClaim], issues: Sequence[VerificationIssue]) -> List[AletheiaClaim]:
        blocked_claim_ids = {
            issue.claim_id
            for issue in issues
            if issue.severity in {"critical", "high"}
        }
        medium_issue_ids = {
            issue.claim_id
            for issue in issues
            if issue.severity == "medium"
        }
        revised: List[AletheiaClaim] = []
        for claim in claims:
            if claim.claim_id in blocked_claim_ids:
                continue
            confidence = min(claim.confidence, 0.70) if claim.claim_id in medium_issue_ids else claim.confidence
            revised.append(AletheiaClaim(claim.claim_id, claim.text, list(claim.citations), confidence))
        return revised

    def _normalize(self, text: str) -> str:
        return " ".join(str(text).lower().replace(".", " ").replace(",", " ").split())


class AlphaAletheiaBrowserResearchEngine:
    """Domain-specific fusion of browser-use planning and Aletheia verification."""

    def __init__(
        self,
        planner: Optional[AlphaAlgoBrowserUsePlanner] = None,
        verifier: Optional[AlphaAletheiaVerifier] = None,
        source_validator: Optional[SourceValidationLayer] = None,
        audit_ledger: Optional[ImmutableAuditLedger] = None,
        passport_proxy: Optional[DataPassportSidecarProxy] = None,
    ):
        self.planner = planner or AlphaAlgoBrowserUsePlanner()
        self.verifier = verifier or AlphaAletheiaVerifier()
        self.source_validator = source_validator or SourceValidationLayer()
        self.audit_ledger = audit_ledger or AppendOnlyJsonlAuditLedger()
        self.passport_proxy = passport_proxy

    def run_research(
        self,
        question: str,
        start_urls: Sequence[str],
        allowed_domains: Sequence[str],
        observations: Sequence[BrowserObservation],
        max_rounds: int = 2,
    ) -> AletheiaBrowserResearchReport:
        task_plan = self.planner.plan(question, start_urls, allowed_domains)
        blocked_reasons = list(task_plan.rejected_reasons)
        evidence = self._observations_to_evidence(observations)
        lineage_hashes: List[str] = []
        for observation in observations:
            source_report = self.source_validator.validate(observation.source)
            if not source_report.accepted:
                blocked_reasons.extend(source_report.findings)
            lineage_hashes.append(source_report.lineage_hash)
            if observation.passport_validation is not None and not observation.passport_validation.accepted:
                blocked_reasons.extend(observation.passport_validation.reasons)

        attempts: List[AletheiaResearchAttempt] = []
        claims = self._generate_claims(question, observations)
        accepted_claims: List[AletheiaClaim] = []
        for round_index in range(max(1, max_rounds)):
            issues = self.verifier.verify(claims, observations)
            revised = self.verifier.revise(claims, issues)
            decision = IntelligenceDecision.ACCEPT if revised and not any(issue.severity in {"critical", "high"} for issue in issues) else IntelligenceDecision.QUARANTINE
            attempts.append(AletheiaResearchAttempt(round_index, claims, issues, revised, decision))
            accepted_claims = revised
            if decision == IntelligenceDecision.ACCEPT:
                break
            claims = self._regenerate_from_revisions(question, revised, observations)

        if blocked_reasons:
            decision = IntelligenceDecision.REJECT
        elif accepted_claims:
            decision = IntelligenceDecision.ACCEPT
        else:
            decision = IntelligenceDecision.QUARANTINE
            blocked_reasons.append("no claims survived verification")
        confidence = self._confidence(accepted_claims, observations, decision)
        audit_record = self.audit_ledger.append(
            "alpha_aletheia_browser_research",
            {
                "question": question,
                "task_plan": task_plan.to_dict(),
                "attempts": [attempt.to_dict() for attempt in attempts],
                "decision": decision.value,
                "lineage_hashes": lineage_hashes,
                "blocked_reasons": blocked_reasons,
            },
            actor="alpha-aletheia-browser-engine",
            action="run_research",
            input_hash=self._hash_payload([observation.to_dict() for observation in observations]),
            output_hash=self._hash_payload([claim.to_dict() for claim in accepted_claims]),
        )
        return AletheiaBrowserResearchReport(
            task_plan=task_plan,
            question=question,
            decision=decision,
            accepted_claims=accepted_claims,
            attempts=attempts,
            evidence=evidence,
            source_lineage_hashes=sorted(set(lineage_hashes)),
            audit_digest=audit_record.record_hash,
            confidence=confidence,
            blocked_reasons=blocked_reasons,
        )

    def observation_from_page(
        self,
        url: str,
        title: str,
        extracted_text: str,
        facts: Sequence[str],
        source_name: str,
        license_status: SourceLicenseStatus = SourceLicenseStatus.PUBLIC,
        permission_basis: str = "public web page",
        license_name: str = "public web terms",
        category: DataSourceCategory = DataSourceCategory.NEWS_FILINGS,
        passport_message: Optional[Mapping[str, Any]] = None,
    ) -> BrowserObservation:
        now = time.time()
        source_id = hashlib.sha256(f"{url}:{source_name}".encode("utf-8")).hexdigest()[:16]
        source = DataSourceProvenance(
            source_id=source_id,
            name=source_name,
            category=category,
            license_status=license_status,
            license_name=license_name,
            permission_basis=permission_basis,
            collected_at=now,
            observed_at=now,
            uri=url,
            provenance_chain=["browser_observation", "fact_extractor", "alpha_aletheia"],
            compliance_score=0.95 if license_status in {SourceLicenseStatus.PUBLIC, SourceLicenseStatus.LICENSED, SourceLicenseStatus.PERMISSIONED} else 0.0,
            reliability_score=0.80,
            symbol_universe=["MULTI"],
            data_vendor=source_name,
            ingestion_time=now,
            adjustment_method="not_applicable",
            survivorship_bias_status="not_applicable",
            lookahead_risk_status="point_in_time",
            quality_score=0.90,
        )
        passport_validation = None
        if self.passport_proxy is not None and passport_message is not None:
            passport_validation = self.passport_proxy.verify_message(passport_message)
        observation_id = hashlib.sha256(f"{url}:{title}:{now:.6f}".encode("utf-8")).hexdigest()[:16]
        return BrowserObservation(
            observation_id=observation_id,
            url=url,
            title=title,
            extracted_text=extracted_text,
            extracted_facts=list(facts),
            source=source,
            observed_at=now,
            passport_validation=passport_validation,
        )

    def _generate_claims(self, question: str, observations: Sequence[BrowserObservation]) -> List[AletheiaClaim]:
        claims: List[AletheiaClaim] = []
        for index, observation in enumerate(observations):
            if not observation.extracted_facts:
                continue
            best_fact = max(observation.extracted_facts, key=len)
            claim_id = hashlib.sha256(f"{question}:{observation.observation_id}:{index}".encode("utf-8")).hexdigest()[:16]
            claims.append(AletheiaClaim(claim_id, best_fact, [observation.observation_id], 0.68))
        if len(observations) >= 2:
            shared_text = " ; ".join(observation.extracted_facts[0] for observation in observations if observation.extracted_facts)
            if shared_text:
                claim_id = hashlib.sha256(f"{question}:synthesis".encode("utf-8")).hexdigest()[:16]
                claims.append(AletheiaClaim(claim_id, shared_text, [observation.observation_id for observation in observations], 0.74))
        return claims

    def _regenerate_from_revisions(
        self,
        question: str,
        revised: Sequence[AletheiaClaim],
        observations: Sequence[BrowserObservation],
    ) -> List[AletheiaClaim]:
        if revised:
            return list(revised)
        conservative_claims = []
        for observation in observations:
            if observation.extracted_facts:
                claim_id = hashlib.sha256(f"{question}:{observation.observation_id}:conservative".encode("utf-8")).hexdigest()[:16]
                conservative_claims.append(
                    AletheiaClaim(
                        claim_id,
                        observation.extracted_facts[0],
                        [observation.observation_id],
                        0.55,
                    )
                )
        return conservative_claims

    def _observations_to_evidence(self, observations: Sequence[BrowserObservation]) -> List[IntelligenceEvidence]:
        evidence: List[IntelligenceEvidence] = []
        for observation in observations:
            claim = " ".join(observation.extracted_facts)
            evidence.append(
                IntelligenceEvidence(
                    evidence_id=observation.observation_id,
                    source_id=observation.source.source_id,
                    claim=claim,
                    observed_at=observation.observed_at,
                    content_hash=hashlib.sha256(observation.extracted_text.encode("utf-8")).hexdigest(),
                    features={"fact_count": float(len(observation.extracted_facts))},
                )
            )
        return evidence

    def _confidence(
        self,
        claims: Sequence[AletheiaClaim],
        observations: Sequence[BrowserObservation],
        decision: IntelligenceDecision,
    ) -> float:
        if decision != IntelligenceDecision.ACCEPT or not claims:
            return 0.0
        source_count = len({observation.source.source_id for observation in observations})
        base = sum(claim.confidence for claim in claims) / len(claims)
        corroboration_bonus = min(0.15, max(0, source_count - 1) * 0.05)
        return round(min(0.95, base + corroboration_bonus), 4)

    def _hash_payload(self, payload: Any) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


__all__ = [
    "AletheiaBrowserResearchReport",
    "AletheiaClaim",
    "AletheiaResearchAttempt",
    "AlphaAletheiaBrowserResearchEngine",
    "AlphaAletheiaVerifier",
    "AlphaAlgoBrowserUsePlanner",
    "BrowserAction",
    "BrowserActionType",
    "BrowserObservation",
    "BrowserTaskPlan",
    "VerificationIssue",
]

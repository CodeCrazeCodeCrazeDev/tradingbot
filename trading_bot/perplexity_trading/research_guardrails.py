"""
Perplexity trading research guardrails.

This module keeps retrieval-augmented trading research from becoming direct
live-trading authority. It verifies citation quality, data freshness,
confidence, QA failures, and governance approval before BUY/SELL decisions can
leave the Perplexity research stack.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .core_types import ApprovalStatus, Citation, QACheckResult, TradingDecision


@dataclass
class ResearchGuardConfig:
    """Safety thresholds for Perplexity-style trading research."""

    min_citations_for_trade: int = 2
    min_distinct_source_types_for_trade: int = 2
    min_citation_confidence: float = 0.60
    max_data_age_seconds: float = 900.0
    min_confidence_for_trade: float = 0.70
    require_governance_for_live_trade: bool = True
    require_complete_risk_plan_for_trade: bool = True
    block_conflicting_evidence_for_trade: bool = True
    research_only_mode: bool = False
    max_position_size_without_approval: float = 0.0
    research_only_actions: List[str] = field(default_factory=lambda: ["HOLD", "WAIT", "NO_TRADE"])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchGuardReport:
    """Audit report emitted by the Perplexity trading guard."""

    accepted: bool
    original_action: str
    final_action: str
    reasons: List[str]
    citation_count: int
    source_type_count: int
    stale_citation_count: int
    low_confidence_citation_count: int
    conflicting_evidence_count: int
    missing_risk_fields: List[str] = field(default_factory=list)
    failed_qa_methods: List[str] = field(default_factory=list)
    forced_research_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerplexityTradingGuard:
    """Objective validator for retrieval-backed trading decisions."""

    def __init__(self, config: Optional[ResearchGuardConfig] = None):
        self.config = config or ResearchGuardConfig()

    def validate_decision(
        self,
        decision: TradingDecision,
        *,
        live_mode: bool = False,
        governance_approved: bool = False,
        now: Optional[datetime] = None,
    ) -> ResearchGuardReport:
        """Return a report without mutating the decision."""
        now = now or datetime.utcnow()
        action = str(decision.action or "HOLD").upper()
        trade_action = action in {"BUY", "SELL"}
        reasons: List[str] = []

        citation_count = len(decision.citations)
        source_types = {citation.source_type for citation in decision.citations}
        stale_citations = self._stale_citations(decision.citations, now)
        low_confidence_citations = [
            citation
            for citation in decision.citations
            if citation.confidence < self.config.min_citation_confidence
        ]
        failed_qa = [qa.method for qa in decision.qa_results if not qa.passed]
        conflicting_evidence = self._conflicting_evidence(decision)
        missing_risk_fields = self._missing_risk_fields(decision)

        if trade_action and self.config.research_only_mode:
            reasons.append("research-only mode blocks direct trade actions")
        if trade_action and citation_count < self.config.min_citations_for_trade:
            reasons.append(
                f"trade action needs at least {self.config.min_citations_for_trade} citations"
            )
        if trade_action and len(source_types) < self.config.min_distinct_source_types_for_trade:
            reasons.append(
                f"trade action needs at least {self.config.min_distinct_source_types_for_trade} distinct source types"
            )
        if trade_action and stale_citations:
            reasons.append(f"{len(stale_citations)} citations are stale")
        if trade_action and low_confidence_citations:
            reasons.append(f"{len(low_confidence_citations)} citations are low confidence")
        if trade_action and self.config.block_conflicting_evidence_for_trade and conflicting_evidence:
            reasons.append(f"{len(conflicting_evidence)} conflicting evidence items detected")
        if trade_action and self.config.require_complete_risk_plan_for_trade and missing_risk_fields:
            reasons.append(f"trade action missing risk fields: {', '.join(missing_risk_fields)}")
        if trade_action and decision.confidence < self.config.min_confidence_for_trade:
            reasons.append(
                f"decision confidence {decision.confidence:.2f} below {self.config.min_confidence_for_trade:.2f}"
            )
        if failed_qa:
            reasons.append(f"failed QA checks: {', '.join(failed_qa)}")
        if trade_action and decision.position_size:
            if decision.position_size > self.config.max_position_size_without_approval:
                if decision.approval_status not in {ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED}:
                    reasons.append("position size requires approval")
        if trade_action and live_mode and self.config.require_governance_for_live_trade and not governance_approved:
            reasons.append("live trade requires governance approval")

        accepted = not reasons
        final_action = action if accepted else ("NO_TRADE" if trade_action else action)
        return ResearchGuardReport(
            accepted=accepted,
            original_action=action,
            final_action=final_action,
            reasons=reasons,
            citation_count=citation_count,
            source_type_count=len(source_types),
            stale_citation_count=len(stale_citations),
            low_confidence_citation_count=len(low_confidence_citations),
            conflicting_evidence_count=len(conflicting_evidence),
            missing_risk_fields=missing_risk_fields,
            failed_qa_methods=failed_qa,
            forced_research_only=trade_action and not accepted,
        )

    def apply(
        self,
        decision: TradingDecision,
        *,
        live_mode: bool = False,
        governance_approved: bool = False,
        now: Optional[datetime] = None,
    ) -> Tuple[TradingDecision, ResearchGuardReport]:
        """Validate and mutate unsafe trade decisions to NO_TRADE."""
        report = self.validate_decision(
            decision,
            live_mode=live_mode,
            governance_approved=governance_approved,
            now=now,
        )
        if report.final_action != decision.action:
            decision.reasoning_chain.append(
                "[RESEARCH_GUARD] Trade blocked: " + "; ".join(report.reasons)
            )
            decision.action = report.final_action
            decision.requires_approval = False
            decision.approval_status = ApprovalStatus.REJECTED
            decision.approval_reason = "Perplexity research guard blocked trade"
        decision.qa_results.append(
            QACheckResult(
                passed=report.accepted,
                method="perplexity_research_guard",
                issues=list(report.reasons),
                confidence_adjustment=0.0 if report.accepted else -0.25,
            )
        )
        return decision, report

    def _stale_citations(self, citations: List[Citation], now: datetime) -> List[Citation]:
        return [
            citation
            for citation in citations
            if (now - citation.timestamp).total_seconds() > self.config.max_data_age_seconds
        ]

    def _missing_risk_fields(self, decision: TradingDecision) -> List[str]:
        missing = []
        for field_name in ("entry_price", "stop_loss", "take_profit", "position_size"):
            if getattr(decision, field_name) in {None, 0, 0.0}:
                missing.append(field_name)
        return missing

    def _conflicting_evidence(self, decision: TradingDecision) -> List[Citation]:
        directional_signals = set()
        conflicting = []
        for citation in decision.citations:
            text = f"{citation.data_point} {citation.raw_data or ''}".lower()
            if any(token in text for token in ("conflict", "contradict", "disagree")):
                conflicting.append(citation)
            signal = self._directional_signal(text, citation.raw_data)
            if signal:
                directional_signals.add(signal)
        if {"bullish", "bearish"}.issubset(directional_signals):
            conflicting.extend(decision.citations)
        for qa in decision.qa_results:
            if not qa.passed and qa.method in {"consistency_check", "source_conflict", "contradiction_check"}:
                # Count failed consistency QA as one conflict even when citations lack raw signals.
                if decision.citations:
                    conflicting.append(decision.citations[0])
        seen = set()
        deduped = []
        for citation in conflicting:
            key = (citation.source_type.value, citation.source_name, citation.data_point)
            if key not in seen:
                seen.add(key)
                deduped.append(citation)
        return deduped

    def _directional_signal(self, text: str, raw_data: Any) -> Optional[str]:
        if isinstance(raw_data, dict):
            for key in ("signal", "direction", "bias", "action"):
                value = str(raw_data.get(key, "")).lower()
                if value in {"buy", "long", "bullish"}:
                    return "bullish"
                if value in {"sell", "short", "bearish"}:
                    return "bearish"
        if any(token in text for token in (" buy", " long", "bullish")):
            return "bullish"
        if any(token in text for token in (" sell", " short", "bearish")):
            return "bearish"
        return None

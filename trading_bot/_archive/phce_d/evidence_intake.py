"""
PHCE-D Module 1: Evidence Intake

Collect only point-in-time, permissioned, timestamped evidence needed
to test the current hypothesis.

Hard rules:
- Stale data blocks the decision — it is not merely downweighted
- Lookahead or leakage suspicion → kill
- Missing required fields → kill
- Untrusted evidence for high-trust claim → kill
- Cost inputs unavailable when evaluating trade hypothesis → kill

Latency budget:
- Decision lane: 5-20 ms from in-memory cache
- Research lane: 100-1000 ms if historical retrieval required

Integrates with:
- trading_bot.core.research_mvp_pipeline (clean data, lineage hashing)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .core_types import (
    DecisionLane,
    DecisionOutput,
    EvidenceKind,
    EvidencePacket,
    EvidenceSource,
    EvidenceTrust,
    FreshnessPolicy,
    FreshnessStatus,
    LeakageRisk,
    PHCEDError,
    EvidenceStaleError,
)

logger = logging.getLogger(__name__)


@dataclass
class IntakeResult:
    """Result of evidence intake processing."""
    packet: Optional[EvidencePacket]
    accepted: bool
    kill_reason: Optional[str]
    stale_sources: List[str]
    missing_fields: List[str]
    lineage_hash: str
    processing_time_ms: float


class EvidenceIntake:
    """
    Module 1: Evidence Intake

    Collects, validates, and normalizes evidence from market and portfolio data.
    Enforces point-in-time discipline, freshness, and trust requirements.

    Kill criteria (any of these → decision is killed):
    - Missing required fields
    - Stale or untrusted evidence for a high-trust claim
    - Lookahead or leakage suspicion
    - Cost inputs unavailable when evaluating a trade hypothesis
    """

    # Required evidence kinds for any trade-related hypothesis
    REQUIRED_FOR_TRADE: set = {
        EvidenceKind.PORTFOLIO_STATE,
        EvidenceKind.SPREAD_LIQUIDITY,
        EvidenceKind.ONE_MINUTE_BARS,
        EvidenceKind.COST_MODEL,
    }

    # Required evidence kinds for research-only hypotheses
    REQUIRED_FOR_RESEARCH: set = {
        EvidenceKind.ONE_MINUTE_BARS,
    }

    # Fields that must never appear in point-in-time evidence
    FORBIDDEN_FIELDS: set = {
        "future_return",
        "post_signal_regime_label",
        "revised_macro_data",
        "forward_fill_value",
    }

    def __init__(
        self,
        freshness_policies: Optional[List[FreshnessPolicy]] = None,
        strict_mode: bool = True,
        max_latency_decision_ms: float = 20.0,
        max_latency_research_ms: float = 1000.0,
    ):
        self.freshness_policies = freshness_policies or FreshnessPolicy.default_policies()
        self.strict_mode = strict_mode
        self.max_latency_decision_ms = max_latency_decision_ms
        self.max_latency_research_ms = max_latency_research_ms
        self._policy_map = {p.evidence_kind: p for p in self.freshness_policies}

        # Statistics
        self.total_intakes = 0
        self.killed_intakes = 0
        self.stale_rejections = 0
        self.leakage_rejections = 0
        self.missing_field_rejections = 0

    def intake(
        self,
        symbol: str,
        raw_sources: Sequence[Dict[str, Any]],
        lane: DecisionLane,
        is_trade_hypothesis: bool = True,
        now: Optional[float] = None,
    ) -> IntakeResult:
        """
        Process raw evidence sources into a normalized evidence packet.

        Args:
            symbol: Trading symbol
            raw_sources: List of raw evidence dicts with keys:
                source_id, evidence_kind, timestamp, trust, value, lineage_hash
            lane: Decision or research lane
            is_trade_hypothesis: Whether this evidence supports a trade-related claim
            now: Current time (for testing); defaults to time.time()

        Returns:
            IntakeResult with packet if accepted, or kill reason if rejected
        """
        start = time.monotonic()
        now = now or time.time()
        self.total_intakes += 1

        # Step 1: Parse and validate raw sources
        parsed_sources: List[EvidenceSource] = []
        parse_errors: List[str] = []
        for raw in raw_sources:
            try:
                src = self._parse_source(raw)
                parsed_sources.append(src)
            except (KeyError, ValueError) as e:
                parse_errors.append(f"source_parse_error: {e}")

        # Step 2: Check for forbidden fields (lookahead detection)
        leakage_suspected = self._check_forbidden_fields(parsed_sources)
        if leakage_suspected:
            self.leakage_rejections += 1
            elapsed = (time.monotonic() - start) * 1000
            return IntakeResult(
                packet=None,
                accepted=False,
                kill_reason="lookahead_or_leakage_suspected",
                stale_sources=[],
                missing_fields=parse_errors,
                lineage_hash="",
                processing_time_ms=elapsed,
            )

        # Step 3: Check freshness
        stale_sources = self._check_freshness(parsed_sources, now)
        if stale_sources and self.strict_mode:
            self.stale_rejections += 1
            elapsed = (time.monotonic() - start) * 1000
            return IntakeResult(
                packet=None,
                accepted=False,
                kill_reason="stale_evidence_for_high_trust_claim",
                stale_sources=stale_sources,
                missing_fields=[],
                lineage_hash="",
                processing_time_ms=elapsed,
            )

        # Step 4: Check required fields
        available_kinds = {s.evidence_kind for s in parsed_sources}
        required = self.REQUIRED_FOR_TRADE if is_trade_hypothesis else self.REQUIRED_FOR_RESEARCH
        missing = required - available_kinds
        if missing and is_trade_hypothesis:
            self.missing_field_rejections += 1
            elapsed = (time.monotonic() - start) * 1000
            return IntakeResult(
                packet=None,
                accepted=False,
                kill_reason="missing_required_evidence_kinds",
                stale_sources=[],
                missing_fields=[k.value for k in missing],
                lineage_hash="",
                processing_time_ms=elapsed,
            )

        # Step 5: Check cost model availability for trade hypotheses
        if is_trade_hypothesis:
            cost_available = any(
                s.evidence_kind == EvidenceKind.COST_MODEL for s in parsed_sources
            )
            if not cost_available:
                self.killed_intakes += 1
                elapsed = (time.monotonic() - start) * 1000
                return IntakeResult(
                    packet=None,
                    accepted=False,
                    kill_reason="cost_inputs_unavailable_for_trade_hypothesis",
                    stale_sources=[],
                    missing_fields=["cost_model"],
                    lineage_hash="",
                    processing_time_ms=elapsed,
                )

        # Step 6: Build lineage hash
        lineage_hash = self._compute_lineage_hash(parsed_sources, symbol)

        # Step 7: Build completeness report
        completeness = {k.value: k in available_kinds for k in EvidenceKind}

        # Step 8: Build trust labels
        trust_labels = {s.source_id: s.trust for s in parsed_sources}

        # Step 9: Collect missing fields from sources
        all_missing = []
        for s in parsed_sources:
            all_missing.extend(s.missing_fields)
        all_missing.extend(parse_errors)

        # Build packet
        packet = EvidencePacket(
            packet_id=f"ep_{int(now * 1000)}_{symbol}",
            symbol=symbol,
            timestamp=now,
            sources=tuple(parsed_sources),
            lineage_hash=lineage_hash,
            completeness_report=completeness,
            missing_fields=all_missing,
            trust_labels=trust_labels,
            lane=lane,
        )

        # Check latency budget
        elapsed = (time.monotonic() - start) * 1000
        budget = self.max_latency_decision_ms if lane == DecisionLane.DECISION else self.max_latency_research_ms
        if elapsed > budget:
            logger.warning(
                f"Evidence intake exceeded {lane.value} latency budget: "
                f"{elapsed:.1f}ms > {budget:.1f}ms"
            )

        return IntakeResult(
            packet=packet,
            accepted=True,
            kill_reason=None,
            stale_sources=stale_sources,
            missing_fields=all_missing,
            lineage_hash=lineage_hash,
            processing_time_ms=elapsed,
        )

    def _parse_source(self, raw: Dict[str, Any]) -> EvidenceSource:
        """Parse a raw evidence dict into an EvidenceSource."""
        kind_str = raw.get("evidence_kind", "")
        try:
            kind = EvidenceKind(kind_str)
        except ValueError:
            raise ValueError(f"Unknown evidence kind: {kind_str}")

        trust_str = raw.get("trust", "medium")
        try:
            trust = EvidenceTrust(trust_str)
        except ValueError:
            raise ValueError(f"Unknown trust level: {trust_str}")

        return EvidenceSource(
            source_id=raw.get("source_id", f"src_{kind.value}"),
            evidence_kind=kind,
            timestamp=float(raw.get("timestamp", 0)),
            trust=trust,
            value=raw.get("value"),
            lineage_hash=raw.get("lineage_hash", ""),
            missing_fields=raw.get("missing_fields", []),
        )

    def _check_forbidden_fields(self, sources: List[EvidenceSource]) -> bool:
        """
        Check for lookahead / leakage indicators.
        If any source value contains forbidden field names, reject.
        """
        for src in sources:
            if src.value is None:
                continue
            # Check dict values for forbidden keys
            if isinstance(src.value, dict):
                for key in src.value:
                    if key in self.FORBIDDEN_FIELDS:
                        logger.error(
                            f"FORBIDDEN FIELD '{key}' detected in source "
                            f"{src.source_id} — leakage suspected"
                        )
                        return True
            # Check string values for forbidden field references
            if isinstance(src.value, str):
                for forbidden in self.FORBIDDEN_FIELDS:
                    if forbidden in src.value:
                        logger.error(
                            f"FORBIDDEN FIELD reference '{forbidden}' in source "
                            f"{src.source_id} — leakage suspected"
                        )
                        return True
        return False

    def _check_freshness(self, sources: List[EvidenceSource], now: float) -> List[str]:
        """
        Check freshness of each source against policies.
        Returns list of stale source IDs (only high-trust sources block decisions).
        """
        stale = []
        for src in sources:
            policy = self._policy_map.get(src.evidence_kind)
            if policy is None:
                continue
            status = src.check_freshness(policy, now)
            if status == FreshnessStatus.STALE:
                if src.trust in (EvidenceTrust.HIGH, EvidenceTrust.MEDIUM):
                    stale.append(src.source_id)
                    logger.warning(
                        f"STALE evidence: {src.source_id} ({src.evidence_kind.value}) "
                        f"age={now - src.timestamp:.1f}s > max={policy.max_age_seconds:.1f}s"
                    )
                else:
                    # Low/untrusted stale evidence is noted but doesn't block
                    logger.info(
                        f"Stale low-trust evidence noted: {src.source_id} "
                        f"({src.evidence_kind.value})"
                    )
        return stale

    def _compute_lineage_hash(self, sources: List[EvidenceSource], symbol: str) -> str:
        """Compute deterministic lineage hash over all evidence sources."""
        parts = [symbol]
        for src in sorted(sources, key=lambda s: s.source_id):
            parts.append(f"{src.source_id}:{src.evidence_kind.value}:{src.lineage_hash}")
        content = "|".join(parts)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_stats(self) -> Dict[str, Any]:
        """Return intake statistics."""
        return {
            "total_intakes": self.total_intakes,
            "killed_intakes": self.killed_intakes,
            "stale_rejections": self.stale_rejections,
            "leakage_rejections": self.leakage_rejections,
            "missing_field_rejections": self.missing_field_rejections,
            "kill_rate": self.killed_intakes / max(1, self.total_intakes),
        }

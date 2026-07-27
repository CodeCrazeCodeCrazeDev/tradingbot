import logging
from typing import Dict, List, Tuple

from .models import EvidencePayload, EvidenceReport, SourceType

logger = logging.getLogger("AlphaAlgo.EIP.EQE")


class EvidenceQualityEngine:
    """
    Evidence Quality Engine (EQE).
    Weights and cross-validates claims before capability extraction to block marketing hype.
    """

    def __init__(self, reject_threshold: float = 0.40):
        self.reject_threshold = reject_threshold

        # Authoritative Source Weights
        self.source_weights = {
            SourceType.BENCHMARK: 1.0,
            SourceType.ARXIV: 0.85,
            SourceType.PAPERS_WITH_CODE: 0.85,
            SourceType.HUGGING_FACE: 0.70,
            SourceType.GITHUB: 0.70,
            SourceType.TECHNICAL_BLOG: 0.50,
            SourceType.FRONTIER_MODEL: 0.60,
            SourceType.CREATOR: 0.25  # Heavily discounted (requires strict validation)
        }

    def evaluate_payload(self, payload: EvidencePayload) -> EvidenceReport:
        logger.info(f"EQE: Auditing evidence from {payload.source_name} ({payload.source_type.value})...")

        base_weight = self.source_weights.get(payload.source_type, 0.20)
        bonus = 0.0
        verified_checks = []
        warnings = []

        # Check 1: Presence of actual code samples (+0.10)
        if len(payload.code_samples) > 0 and len(payload.code_samples[0].strip()) > 20:
            bonus += 0.10
            verified_checks.append("replicable_code_samples_present")
        else:
            warnings.append("missing_source_code_samples")

        # Check 2: Peer reviewed / mathematically verified (+0.05)
        is_peer_reviewed = payload.claims.get("peer_reviewed", False) or payload.claims.get("mathematically_proven", False)
        if is_peer_reviewed:
            bonus += 0.05
            verified_checks.append("peer_reviewed_or_mathematically_proven")

        # Check 3: Check for unsupported marketing claims or hype words (-0.15 penalty)
        hype_words = ["get rich", "exponential gain", "passive income", "ponzi", "airdrop", "moon lambo", "100x"]
        text = f"{payload.readme_content} {payload.source_name}".lower()
        has_hype = any(hype in text for hype in hype_words)
        if has_hype:
            bonus -= 0.15
            warnings.append("marketing_hype_or_unsupported_claims_detected")

        final_score = min(max(base_weight + bonus, 0.0), 1.0)
        passed_gate = final_score >= self.reject_threshold

        if not passed_gate:
            warnings.append(f"rejected_by_evidence_quality_gate (score: {final_score:.2f} < threshold: {self.reject_threshold:.2f})")

        return EvidenceReport(
            base_weight=base_weight,
            cross_validation_bonus=round(bonus, 2),
            final_quality_score=round(final_score, 2),
            passed_eq_gate=passed_gate,
            verified_checks=verified_checks,
            warnings=warnings
        )

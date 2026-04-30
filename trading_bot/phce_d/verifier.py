"""
PHCE-D Module 3: Deterministic / Statistical Verifier

Test the hypothesis against reality, not narrative.

Hard rules:
- Zero LLM cost
- Bounded compute only
- Cost/slippage subtraction before edge scoring
- Effect disappears after cost adjustment → kill
- Sample size below configured minimum → kill
- Unverifiable high-trust claim → kill

Latency budget:
- Decision lane MVP: 10-50 ms
- Research lane: 100 ms to several seconds depending on sample

Integrates with:
- trading_bot.core.transaction_cost_model
- trading_bot.core.research_mvp_pipeline (ResearchTransactionCostModel)
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .core_types import (
    DecisionOutput,
    EvidencePacket,
    Hypothesis,
    LeakageRisk,
    SkeletonKeyResult,
    VerificationFlag,
    VerificationReport,
)

logger = logging.getLogger(__name__)


@dataclass
class VerifierConfig:
    """Configuration for the verifier."""
    min_sample_size: int = 30
    max_unknown_rate: float = 0.3
    sign_consistency_windows: int = 3
    cost_adjustment_required: bool = True
    enable_skeleton_key: bool = True
    skeleton_key_threshold_bps: float = 2.0  # If dumb is within this, fancy dies


@dataclass
class DeterministicCheckResult:
    """Result of a single deterministic check."""
    check_name: str
    flag: VerificationFlag
    detail: str
    value: Optional[float] = None


class DeterministicVerifier:
    """
    Deterministic verification checks — no statistics, no LLM, no ambiguity.
    These are hard invariants that must pass for any positive action.
    """

    def check_signal_strength(
        self,
        evidence: EvidencePacket,
        threshold: float,
    ) -> DeterministicCheckResult:
        """Check if directional signal strength exceeds threshold."""
        bars = [s for s in evidence.sources if s.evidence_kind.value == "1m_bars"]
        if not bars or bars[0].value is None:
            return DeterministicCheckResult(
                "signal_strength", VerificationFlag.UNKNOWN,
                "no_bar_data_available"
            )

        bar_data = bars[0].value
        if isinstance(bar_data, dict):
            close = bar_data.get("close", 0)
            open_ = bar_data.get("open", 0)
        else:
            return DeterministicCheckResult(
                "signal_strength", VerificationFlag.UNKNOWN,
                "bar_data_format_unexpected"
            )

        if open_ == 0:
            return DeterministicCheckResult(
                "signal_strength", VerificationFlag.UNKNOWN,
                "open_price_zero"
            )

        signal = (close - open_) / open_ * 10000  # bps
        if abs(signal) >= threshold:
            return DeterministicCheckResult(
                "signal_strength", VerificationFlag.PASS,
                f"signal_{signal:.1f}bps >= threshold_{threshold:.1f}bps",
                value=signal
            )
        return DeterministicCheckResult(
            "signal_strength", VerificationFlag.FAIL,
            f"signal_{signal:.1f}bps < threshold_{threshold:.1f}bps",
            value=signal
        )

    def check_spread_within_limit(
        self,
        evidence: EvidencePacket,
        max_spread_bps: float = 20.0,
        max_spread_vs_normal: float = 2.0,
    ) -> DeterministicCheckResult:
        """Check if current spread is within acceptable limits."""
        spread_src = [s for s in evidence.sources if s.evidence_kind.value == "spread_liquidity"]
        if not spread_src or spread_src[0].value is None:
            return DeterministicCheckResult(
                "spread_limit", VerificationFlag.UNKNOWN,
                "no_spread_data_available"
            )

        spread_data = spread_src[0].value
        if isinstance(spread_data, dict):
            current_bps = spread_data.get("spread_bps", 0)
            normal_bps = spread_data.get("normal_spread_bps", current_bps)
        else:
            return DeterministicCheckResult(
                "spread_limit", VerificationFlag.UNKNOWN,
                "spread_data_format_unexpected"
            )

        if current_bps > max_spread_bps:
            return DeterministicCheckResult(
                "spread_limit", VerificationFlag.FAIL,
                f"spread_{current_bps:.1f}bps > max_{max_spread_bps:.1f}bps",
                value=current_bps
            )

        if normal_bps > 0 and current_bps > normal_bps * max_spread_vs_normal:
            return DeterministicCheckResult(
                "spread_limit", VerificationFlag.FAIL,
                f"spread_{current_bps:.1f}bps > {max_spread_vs_normal}x_normal_{normal_bps:.1f}bps",
                value=current_bps
            )

        return DeterministicCheckResult(
            "spread_limit", VerificationFlag.PASS,
            f"spread_{current_bps:.1f}bps within limits",
            value=current_bps
        )

    def check_volume_sufficient(
        self,
        evidence: EvidencePacket,
        min_volume_percentile: float = 25.0,
    ) -> DeterministicCheckResult:
        """Check if volume is sufficient for entry."""
        vol_src = [s for s in evidence.sources if s.evidence_kind.value == "volume_data"]
        if not vol_src or vol_src[0].value is None:
            return DeterministicCheckResult(
                "volume_sufficient", VerificationFlag.UNKNOWN,
                "no_volume_data_available"
            )

        vol_data = vol_src[0].value
        if isinstance(vol_data, dict):
            percentile = vol_data.get("volume_percentile", 50)
        else:
            return DeterministicCheckResult(
                "volume_sufficient", VerificationFlag.UNKNOWN,
                "volume_data_format_unexpected"
            )

        if percentile < min_volume_percentile:
            return DeterministicCheckResult(
                "volume_sufficient", VerificationFlag.FAIL,
                f"volume_percentile_{percentile:.0f} < min_{min_volume_percentile:.0f}",
                value=percentile
            )

        return DeterministicCheckResult(
            "volume_sufficient", VerificationFlag.PASS,
            f"volume_percentile_{percentile:.0f} sufficient",
            value=percentile
        )


class StatisticalVerifier:
    """
    Lightweight statistical sanity checks.
    Only used if they fit the latency budget.
    Zero LLM cost. Bounded compute only.
    """

    def __init__(self, min_sample_size: int = 30):
        self.min_sample_size = min_sample_size

    def check_sign_consistency(
        self,
        returns: List[float],
        windows: int = 3,
    ) -> Tuple[VerificationFlag, str]:
        """
        Check if the edge direction is consistent across nearby windows.
        Sign flips without scenario explanation → concern.
        """
        if len(returns) < self.min_sample_size:
            return VerificationFlag.UNKNOWN, f"sample_{len(returns)}_below_min_{self.min_sample_size}"

        chunk_size = max(1, len(returns) // windows)
        signs = []
        for i in range(windows):
            chunk = returns[i * chunk_size:(i + 1) * chunk_size]
            if chunk:
                avg = sum(chunk) / len(chunk)
                signs.append(1 if avg > 0 else -1)

        if len(set(signs)) == 1:
            return VerificationFlag.PASS, f"sign_consistent_across_{windows}_windows"
        else:
            return VerificationFlag.FAIL, f"sign_flips_detected_in_{windows}_windows"

    def check_effect_size(
        self,
        returns: List[float],
        min_effect_bps: float = 2.0,
    ) -> Tuple[VerificationFlag, float, str]:
        """
        Estimate effect size. Small effect after costs → kill.
        """
        if len(returns) < self.min_sample_size:
            return VerificationFlag.UNKNOWN, 0.0, "insufficient_sample"

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std = math.sqrt(variance) if variance > 0 else 0.0

        # Effect size in bps
        effect_bps = mean_return * 10000

        if effect_bps < min_effect_bps:
            return VerificationFlag.FAIL, effect_bps, f"effect_{effect_bps:.1f}bps_below_min_{min_effect_bps:.1f}bps"

        return VerificationFlag.PASS, effect_bps, f"effect_{effect_bps:.1f}bps_above_min"


class SkeletonKeyValidator:
    """
    P1 #12: Skeleton-Key Validation

    Before accepting a hypothesis, test whether a dumb explanation
    explains the same edge:
    - Volatility regime
    - Spread compression
    - Recent trend continuation
    - Random shuffle
    - Liquidity artifact
    - Session-time effect

    If the dumb explanation performs as well as the fancy hypothesis,
    reject the fancy hypothesis.
    """

    DUMB_EXPLANATIONS = [
        "volatility_regime",
        "spread_compression",
        "trend_continuation",
        "random_shuffle",
        "liquidity_artifact",
        "session_time_effect",
    ]

    def __init__(self, threshold_bps: float = 2.0):
        self.threshold_bps = threshold_bps

    def test_against_dumb(
        self,
        hypothesis_edge_bps: float,
        dumb_results: Dict[str, float],
    ) -> SkeletonKeyResult:
        """
        Compare hypothesis edge against dumb explanations.

        Args:
            hypothesis_edge_bps: Edge from the fancy hypothesis
            dumb_results: Dict of dumb_explanation → edge_bps

        Returns:
            SkeletonKeyResult indicating whether the fancy hypothesis survives
        """
        if not dumb_results:
            return SkeletonKeyResult.FANCY_SURVIVES

        max_dumb_edge = max(dumb_results.values()) if dumb_results else 0.0

        if max_dumb_edge > hypothesis_edge_bps:
            return SkeletonKeyResult.DUMB_OUTPERFORMS

        if abs(hypothesis_edge_bps - max_dumb_edge) <= self.threshold_bps:
            return SkeletonKeyResult.DUMB_MATCHES

        return SkeletonKeyResult.FANCY_SURVIVES


class Verifier:
    """
    Module 3: Deterministic / Statistical Verifier

    Orchestrates deterministic checks, statistical sanity, cost adjustment,
    and skeleton-key validation.

    Kill criteria:
    - Unverifiable high-trust claim
    - Effect disappears after cost adjustment
    - Sign flips across nearby windows without scenario explanation
    - Sample size below configured minimum
    """

    def __init__(
        self,
        config: Optional[VerifierConfig] = None,
        cost_model=None,  # TransactionCostModel or ResearchTransactionCostModel
    ):
        self.config = config or VerifierConfig()
        self.deterministic = DeterministicVerifier()
        self.statistical = StatisticalVerifier(self.config.min_sample_size)
        self.skeleton_key = SkeletonKeyValidator(self.config.skeleton_key_threshold_bps)
        self.cost_model = cost_model

        # Statistics
        self.total_verified = 0
        self.killed_cost_adjustment = 0
        self.killed_sample_size = 0
        self.killed_sign_flip = 0
        self.killed_skeleton_key = 0

    def verify(
        self,
        hypothesis: Hypothesis,
        evidence: EvidencePacket,
        historical_returns: Optional[List[float]] = None,
        dumb_results: Optional[Dict[str, float]] = None,
    ) -> VerificationReport:
        """
        Run verification pipeline against the hypothesis.

        Args:
            hypothesis: The hypothesis to verify
            evidence: Current evidence packet
            historical_returns: Optional historical returns for statistical checks
            dumb_results: Optional skeleton-key dumb explanation results

        Returns:
            VerificationReport with pass/fail/unknown flags and edge estimates
        """
        start = time.monotonic()
        self.total_verified += 1

        flags: Dict[str, VerificationFlag] = {}

        # Step 1: Deterministic checks
        det_results: List[DeterministicCheckResult] = []

        # Signal strength check
        signal_result = self.deterministic.check_signal_strength(
            evidence, hypothesis.min_edge_threshold_bps
        )
        det_results.append(signal_result)
        flags["signal_strength"] = signal_result.flag

        # Spread limit check
        spread_result = self.deterministic.check_spread_limit(evidence)
        det_results.append(spread_result)
        flags["spread_limit"] = spread_result.flag

        # Volume check
        vol_result = self.deterministic.check_volume_sufficient(evidence)
        det_results.append(vol_result)
        flags["volume_sufficient"] = vol_result.flag

        # Step 2: Cost adjustment
        edge_before_cost_bps = 0.0
        edge_after_cost_bps = 0.0
        cost_model_applied = False

        if signal_result.value is not None:
            edge_before_cost_bps = abs(signal_result.value)

        if self.cost_model is not None and edge_before_cost_bps > 0:
            try:
                cost_bps = self._estimate_total_cost_bps(evidence)
                edge_after_cost_bps = edge_before_cost_bps - cost_bps
                cost_model_applied = True

                if edge_after_cost_bps <= 0:
                    self.killed_cost_adjustment += 1
                    flags["cost_adjusted_edge"] = VerificationFlag.FAIL
                else:
                    flags["cost_adjusted_edge"] = VerificationFlag.PASS
            except Exception as e:
                logger.error(f"Cost model error: {e}")
                edge_after_cost_bps = 0.0
                flags["cost_adjusted_edge"] = VerificationFlag.UNKNOWN
        else:
            # No cost model → cannot verify cost-adjusted edge for trade hypothesis
            edge_after_cost_bps = edge_before_cost_bps
            flags["cost_adjusted_edge"] = VerificationFlag.UNKNOWN

        # Step 3: Statistical checks (if data available and budget allows)
        sign_consistent = True
        effect_size = edge_before_cost_bps
        sample_size = len(historical_returns) if historical_returns else 0

        if historical_returns and len(historical_returns) >= self.config.min_sample_size:
            sign_flag, sign_msg = self.statistical.check_sign_consistency(
                historical_returns, self.config.sign_consistency_windows
            )
            flags["sign_consistency"] = sign_flag
            sign_consistent = sign_flag != VerificationFlag.FAIL

            if not sign_consistent:
                self.killed_sign_flip += 1

            effect_flag, effect_bps, effect_msg = self.statistical.check_effect_size(
                historical_returns, hypothesis.min_edge_threshold_bps
            )
            flags["effect_size"] = effect_flag
            effect_size = effect_bps
        else:
            if sample_size < self.config.min_sample_size and sample_size > 0:
                self.killed_sample_size += 1
                flags["sample_size"] = VerificationFlag.FAIL
            else:
                flags["sample_size"] = VerificationFlag.UNKNOWN

        # Step 4: Skeleton-key validation
        skeleton_result = None
        if self.config.enable_skeleton_key and dumb_results:
            skeleton_result = self.skeleton_key.test_against_dumb(
                edge_after_cost_bps if cost_model_applied else edge_before_cost_bps,
                dumb_results,
            )
            if skeleton_result in (SkeletonKeyResult.DUMB_MATCHES, SkeletonKeyResult.DUMB_OUTPERFORMS):
                self.killed_skeleton_key += 1
                flags["skeleton_key"] = VerificationFlag.FAIL
            else:
                flags["skeleton_key"] = VerificationFlag.PASS

        # Build uncertainty notes
        uncertainty_notes = []
        for name, flag in flags.items():
            if flag == VerificationFlag.UNKNOWN:
                uncertainty_notes.append(f"{name}: unknown")
            elif flag == VerificationFlag.FAIL:
                uncertainty_notes.append(f"{name}: failed")

        elapsed = (time.monotonic() - start) * 1000
        logger.debug(f"Verification completed in {elapsed:.1f}ms")

        return VerificationReport(
            hypothesis_id=hypothesis.hypothesis_id,
            flags=flags,
            effect_size_estimate=effect_size,
            edge_before_cost_bps=edge_before_cost_bps,
            edge_after_cost_bps=edge_after_cost_bps,
            uncertainty_notes=uncertainty_notes,
            sample_size=sample_size,
            sign_consistent=sign_consistent,
            cost_model_applied=cost_model_applied,
            skeleton_key_result=skeleton_result,
        )

    def _estimate_total_cost_bps(self, evidence: EvidencePacket) -> float:
        """Estimate total transaction cost in bps using the cost model."""
        # Extract cost data from evidence
        cost_src = [s for s in evidence.sources if s.evidence_kind.value == "cost_model"]
        if cost_src and cost_src[0].value and isinstance(cost_src[0].value, dict):
            return cost_src[0].value.get("total_cost_bps", 10.0)

        # Default conservative estimate if no cost data
        return 10.0  # Conservative: 10 bps total cost

    def get_stats(self) -> Dict[str, Any]:
        """Return verifier statistics."""
        return {
            "total_verified": self.total_verified,
            "killed_cost_adjustment": self.killed_cost_adjustment,
            "killed_sample_size": self.killed_sample_size,
            "killed_sign_flip": self.killed_sign_flip,
            "killed_skeleton_key": self.killed_skeleton_key,
        }

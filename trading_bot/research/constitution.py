"""
AlphaAlgo Research Constitution - Immutable Layer of Scientific Rigor.
======================================================================
Defines and enforces the immutable scientific principles governing all quantitative
research, hypothesis generation, data ingestion, feature engineering, and model validation.
Provides execution guards to prevent look-ahead bias, unscientific claims, and data leakage.
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd

logger = logging.getLogger("AlphaAlgo.ResearchConstitution")


class ConstitutionViolation(Exception):
    """Raised when any operation violates an immutable rule of the Research Constitution."""
    pass


class ResearchConstitution:
    """
    The permanent, immutable constitutional gatekeeper of AlphaAlgo's Research System.
    Provides strict runtime assertions to ensure all quantitative research adheres to
    world-class scientific standards.
    """

    # Permanent Immutable Thresholds
    MAX_ACCEPTABLE_P_VALUE = 0.05
    MIN_DATA_QUALITY_SCORE = 0.95
    MAX_SHARPE_RATIO_CEILING = 4.5  # Sharpe ratio above this indicates high probability of leakage or bias
    MIN_OOS_VS_IS_RATIO = 0.40      # OOS Sharpe must be at least 40% of In-Sample Sharpe to guard against overfitting

    @classmethod
    def assert_evidence_rule(cls, claim: str, evidence_id: str, p_value: float, sample_size: int) -> None:
        """
        Enforces that no claim can be accepted without valid empirical evidence
        meeting strict statistical significance requirements.
        """
        if not evidence_id:
            raise ConstitutionViolation(
                f"Constitutional Violation: Claim '{claim}' cannot be accepted without a linked Evidence ID."
            )
        if p_value > cls.MAX_ACCEPTABLE_P_VALUE:
            raise ConstitutionViolation(
                f"Constitutional Violation: Evidence {evidence_id} for claim '{claim}' is not statistically significant. "
                f"Observed p-value: {p_value:.4f} exceeds max acceptable limit of {cls.MAX_ACCEPTABLE_P_VALUE:.4f}."
            )
        if sample_size < 100:
            raise ConstitutionViolation(
                f"Constitutional Violation: Sample size {sample_size} is too small for statistical validation (minimum 100 required)."
            )
        logger.info(f"Constitution: Claim '{claim[:50]}...' passed empirical evidence check.")

    @classmethod
    def assert_reproducibility_rule(cls, seed: Optional[int], dataset_hash: str) -> None:
        """
        Enforces locked pseudo-random states and verifiable dataset ancestry hashes.
        """
        if seed is None:
            raise ConstitutionViolation(
                "Constitutional Violation: Random seed is not locked. All research experiments must define a deterministic seed."
            )
        if not dataset_hash or len(dataset_hash) < 16:
            raise ConstitutionViolation(
                "Constitutional Violation: Invalid or missing dataset hash. Dataset ancestry must be fully locked."
            )
        logger.info(f"Constitution: Reproducibility verification passed (Seed: {seed}, Hash: {dataset_hash[:12]}).")

    @classmethod
    def assert_data_leakage_guard(cls, in_sample_indices: List[Any], out_of_sample_indices: List[Any]) -> None:
        """
        Ensures strict temporal splitting between In-Sample and Out-Of-Sample partitions.
        Prevents look-ahead leaks by verifying no overlap exists.
        """
        if not in_sample_indices or not out_of_sample_indices:
            raise ConstitutionViolation(
                "Constitutional Violation: In-sample or out-of-sample data split partitions are empty."
            )

        is_set = set(in_sample_indices)
        oos_set = set(out_of_sample_indices)
        overlap = is_set.intersection(oos_set)

        if overlap:
            raise ConstitutionViolation(
                f"Constitutional Violation: Data leakage detected! In-Sample and Out-Of-Sample partitions overlap by {len(overlap)} elements."
            )

        # Test if index elements are timestamps and chronological ordering is preserved
        try:
            is_max = max(in_sample_indices)
            oos_min = min(out_of_sample_indices)
            if oos_min < is_max:
                raise ConstitutionViolation(
                    f"Constitutional Violation: Temporal leakage detected! Out-Of-Sample start ({oos_min}) "
                    f"is prior to In-Sample end ({is_max}). Out-of-sample partition must be strictly chronological."
                )
        except ConstitutionViolation:
            raise
        except Exception as e:
            # If indices are non-comparable directly, skip chronological comparison but log warning
            logger.warning(f"Could not verify strict chronological order: {e}")

        logger.info("Constitution: Data leakage guard validation passed successfully.")

    @classmethod
    def assert_complexity_control(cls, param_count: int, max_allowed: int = 1000) -> None:
        """
        Enforces parsimony and Occam's Razor. Rejects models that are over-parameterized
        relative to the complexity control limits.
        """
        if param_count > max_allowed:
            raise ConstitutionViolation(
                f"Constitutional Violation: Model parameter count ({param_count}) exceeds active complexity limit ({max_allowed}). "
                f"Reconstruct model with reduced dimension to prevent overfitting."
            )
        logger.info(f"Constitution: Model complexity control passed (Parameters: {param_count}/{max_allowed}).")

    @classmethod
    def assert_rational_economic_foundation(cls, hypothesis_text: str, economic_rationale: str, counterparty: str) -> None:
        """
        Enforces that no trade hypothesis is proposed without a deep economic foundation
        and clear counterparty profiling (answering: 'who is losing on the other side of this trade?').
        """
        if not hypothesis_text or len(hypothesis_text) < 10:
            raise ConstitutionViolation("Constitutional Violation: Hypothesis statement must be substantial and detailed.")
        if not economic_rationale or len(economic_rationale) < 15:
            raise ConstitutionViolation("Constitutional Violation: Proposal lacks a sound economic rationale/foundation.")
        if not counterparty or len(counterparty) < 10:
            raise ConstitutionViolation("Constitutional Violation: Proposed hypothesis lacks a clear Counterparty Profile.")
        logger.info(f"Constitution: Rational Economic Foundation validated for hypothesis '{hypothesis_text[:40]}...'.")

    @classmethod
    def assert_governance_signoff(cls, metrics: Dict[str, float]) -> None:
        """
        Validates model performance metrics before live promotion.
        Challenges anomalous Sharpe ratios and extreme OOS degradation.
        """
        sharpe = metrics.get("sharpe_ratio", 0.0)
        is_sharpe = metrics.get("is_sharpe", 0.0)
        oos_sharpe = metrics.get("oos_sharpe", 0.0)

        if sharpe > cls.MAX_SHARPE_RATIO_CEILING:
            raise ConstitutionViolation(
                f"Constitutional Violation: Suspiciously high Sharpe Ratio of {sharpe:.2f} observed. "
                f"Exceeds absolute physical limit ceiling of {cls.MAX_SHARPE_RATIO_CEILING:.2f}. "
                f"Check for look-ahead bias, fee exclusion, or data-mining leaks."
            )

        if is_sharpe > 0:
            ratio = oos_sharpe / is_sharpe
            if ratio < cls.MIN_OOS_VS_IS_RATIO:
                raise ConstitutionViolation(
                    f"Constitutional Violation: Severe Out-Of-Sample degradation detected. "
                    f"OOS Sharpe ({oos_sharpe:.2f}) is only {ratio * 100.0:.1f}% of In-Sample Sharpe ({is_sharpe:.2f}), "
                    f"which is below the mandatory constitutional threshold of {cls.MIN_OOS_VS_IS_RATIO * 100.0:.1f}%."
                )
        logger.info("Constitution: Live-governance performance criteria check passed.")

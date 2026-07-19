"""
Integration & Validation Suite for the Redesigned Quantitative Research System.
==============================================================================
Validates the Research Constitution enforcement guards, Machine-Readable Schemas,
and Capability Maturity Model evaluation mechanics.
"""

import pytest
import json
from datetime import datetime
from trading_bot.research.constitution import ResearchConstitution, ConstitutionViolation
from trading_bot.research.schemas import (
    HypothesisSchema,
    DatasetSchema,
    FeatureSchema,
    ExperimentSchema,
    ModelSchema,
    BenchmarkSchema,
    EvidenceSchema,
    DecisionSchema
)
from trading_bot.research.maturity import ResearchCapabilityAuditor


# ===========================================================================
# 1. Research Constitution Tests
# ===========================================================================

class TestResearchConstitution:
    """Validates runtime guards and constitutional assertions."""

    def test_assert_evidence_rule_success(self) -> None:
        # Should pass without raising exceptions
        ResearchConstitution.assert_evidence_rule(
            claim="Order Flow Imbalance has short-term predictive edge",
            evidence_id="evidence-1234",
            p_value=0.02,
            sample_size=500
        )

    def test_assert_evidence_rule_missing_evidence(self) -> None:
        with pytest.raises(ConstitutionViolation) as exc_info:
            ResearchConstitution.assert_evidence_rule(
                claim="Order Flow Imbalance has edge",
                evidence_id="",
                p_value=0.02,
                sample_size=500
            )
        assert "cannot be accepted without a linked Evidence ID" in str(exc_info.value)

    def test_assert_evidence_rule_insignificant_p_value(self) -> None:
        with pytest.raises(ConstitutionViolation) as exc_info:
            ResearchConstitution.assert_evidence_rule(
                claim="Order Flow Imbalance has edge",
                evidence_id="ev-1",
                p_value=0.15,
                sample_size=500
            )
        assert "is not statistically significant" in str(exc_info.value)

    def test_assert_evidence_rule_insufficient_sample_size(self) -> None:
        with pytest.raises(ConstitutionViolation) as exc_info:
            ResearchConstitution.assert_evidence_rule(
                claim="Order Flow Imbalance has edge",
                evidence_id="ev-1",
                p_value=0.01,
                sample_size=40
            )
        assert "too small" in str(exc_info.value)

    def test_assert_reproducibility_rule_success(self) -> None:
        ResearchConstitution.assert_reproducibility_rule(seed=42, dataset_hash="a" * 32)

    def test_assert_reproducibility_rule_missing_seed(self) -> None:
        with pytest.raises(ConstitutionViolation) as exc_info:
            ResearchConstitution.assert_reproducibility_rule(seed=None, dataset_hash="a" * 32)
        assert "Random seed is not locked" in str(exc_info.value)

    def test_assert_reproducibility_rule_missing_hash(self) -> None:
        with pytest.raises(ConstitutionViolation) as exc_info:
            ResearchConstitution.assert_reproducibility_rule(seed=42, dataset_hash="")
        assert "Invalid or missing dataset hash" in str(exc_info.value)

    def test_assert_data_leakage_guard_success(self) -> None:
        # Chronological and non-overlapping indices
        in_sample = [1, 2, 3, 4, 5]
        out_of_sample = [6, 7, 8, 9, 10]
        ResearchConstitution.assert_data_leakage_guard(in_sample, out_of_sample)

    def test_assert_data_leakage_guard_overlap(self) -> None:
        in_sample = [1, 2, 3, 4, 5]
        out_of_sample = [5, 6, 7, 8, 9]  # overlapping element '5'
        with pytest.raises(ConstitutionViolation) as exc_info:
            ResearchConstitution.assert_data_leakage_guard(in_sample, out_of_sample)
        assert "Data leakage detected! In-Sample and Out-Of-Sample partitions overlap" in str(exc_info.value)

    def test_assert_data_leakage_guard_temporal_anomaly(self) -> None:
        in_sample = [1, 2, 5, 10]
        out_of_sample = [3, 4, 6]  # temporal anomaly: 3 < 10
        with pytest.raises(ConstitutionViolation) as exc_info:
            ResearchConstitution.assert_data_leakage_guard(in_sample, out_of_sample)
        assert "Temporal leakage detected!" in str(exc_info.value)

    def test_assert_complexity_control_success(self) -> None:
        ResearchConstitution.assert_complexity_control(param_count=50, max_allowed=100)

    def test_assert_complexity_control_failure(self) -> None:
        with pytest.raises(ConstitutionViolation) as exc_info:
            ResearchConstitution.assert_complexity_control(param_count=500, max_allowed=100)
        assert "parameter count (500) exceeds active complexity limit" in str(exc_info.value)

    def test_assert_rational_economic_foundation_success(self) -> None:
        ResearchConstitution.assert_rational_economic_foundation(
            hypothesis_text="FX microstructure imbalance leads to rapid price correction",
            economic_rationale="Market makers must rebalance inventory at a premium",
            counterparty="Retail momentum traders experiencing FOMO"
        )

    def test_assert_rational_economic_foundation_missing_fields(self) -> None:
        with pytest.raises(ConstitutionViolation) as exc_info:
            ResearchConstitution.assert_rational_economic_foundation(
                hypothesis_text="Microstructure",
                economic_rationale="No rationale given here",
                counterparty=""
            )
        assert "lacks a clear Counterparty Profile" in str(exc_info.value)

    def test_assert_governance_signoff_success(self) -> None:
        metrics = {
            "sharpe_ratio": 2.1,
            "is_sharpe": 2.5,
            "oos_sharpe": 1.2
        }
        ResearchConstitution.assert_governance_signoff(metrics)

    def test_assert_governance_signoff_suspicious_sharpe(self) -> None:
        metrics = {
            "sharpe_ratio": 9.5,
            "is_sharpe": 2.5,
            "oos_sharpe": 1.2
        }
        with pytest.raises(ConstitutionViolation) as exc_info:
            ResearchConstitution.assert_governance_signoff(metrics)
        assert "Suspiciously high Sharpe Ratio" in str(exc_info.value)

    def test_assert_governance_signoff_severe_degradation(self) -> None:
        metrics = {
            "sharpe_ratio": 1.5,
            "is_sharpe": 3.0,
            "oos_sharpe": 0.5  # OOS is only 16% of IS (<40%)
        }
        with pytest.raises(ConstitutionViolation) as exc_info:
            ResearchConstitution.assert_governance_signoff(metrics)
        assert "Severe Out-Of-Sample degradation detected" in str(exc_info.value)


# ===========================================================================
# 2. Machine-Readable Schema Serialization Tests
# ===========================================================================

class TestMachineReadableSchemas:
    """Verifies dataclass structures and correct JSON serialization/deserialization."""

    def test_hypothesis_schema_serialization(self) -> None:
        hyp = HypothesisSchema(
            id="hyp-001",
            statement="Test statement",
            economic_foundation="Economic rationale",
            counterparty_profile="Counterparty profile",
            falsification_tests=["Test 1"],
            metadata={"priority": "high"}
        )
        serialized = hyp.to_json()
        data = json.loads(serialized)
        assert data["id"] == "hyp-001"
        assert data["metadata"]["priority"] == "high"

    def test_dataset_schema_serialization(self) -> None:
        ds = DatasetSchema(
            id="ds-001",
            source_name="MT5 EURUSD 15m",
            dataset_hash="h" * 64,
            record_count=10000,
            data_quality_score=0.99,
            lineage_parent_ids=["raw-mt5"],
            column_definitions={"close": "float"}
        )
        serialized = ds.to_json()
        data = json.loads(serialized)
        assert data["id"] == "ds-001"
        assert data["data_quality_score"] == 0.99
        assert "close" in data["column_definitions"]

    def test_evidence_schema_serialization(self) -> None:
        ev = EvidenceSchema(
            id="ev-100",
            experiment_id="exp-200",
            claim_text="Alpha has significant edge",
            observed_metric_value=2.8,
            p_value=0.004,
            is_reproducible=True,
            verdict="ACCEPTED"
        )
        serialized = ev.to_json()
        data = json.loads(serialized)
        assert data["id"] == "ev-100"
        assert data["is_reproducible"] is True


# ===========================================================================
# 3. Capability Maturity Model Evaluator Tests
# ===========================================================================

class TestCapabilityMaturityModel:
    """Checks the programmatic capability evaluator scores and outputs."""

    def test_capability_audit_scoring(self) -> None:
        auditor = ResearchCapabilityAuditor()
        report = auditor.audit_system()

        assert "overall_maturity_score" in report
        assert "maturity_class" in report
        assert "details" in report
        assert report["overall_maturity_score"] >= 4.0
        assert report["audited_capabilities_count"] == 10

        # Verify that all audited capabilities are returned
        details_names = [d["capability"] for d in report["details"]]
        assert "problem_discovery" in details_names
        assert "statistical_validation" in details_names
        assert "production_feedback_loops" in details_names

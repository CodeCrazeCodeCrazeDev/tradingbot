"""Wave-2 weakness fixes: failing tests first.

TD-09: governance/evolution_gate.py invents optimistic defaults for metrics
the caller never measured — a sparse candidate can 'beat' a baseline on
fabricated dimensions. The gate must evaluate only supplied evidence:
missing metrics on both sides are skipped, missing on one side is
insufficient evidence, and perf must exist on both sides to compute gain.
"""
import pytest


@pytest.mark.asyncio
async def test_gate_rejects_asymmetric_metric_evidence():
    """Baseline measured robustness; candidate never did. Comparing a real
    0.3 against a fabricated 0.8 previously let the candidate pass on a
    dimension it never supplied."""
    from trading_bot.governance.evolution_gate import EvolutionGate

    gate = EvolutionGate(validation_engine=None, threshold=0.05)
    candidate = {"reward": 0.9}
    baseline = {"reward": 0.1, "robustness": 0.3}
    result = await gate.validate_improvement("cand-asym", candidate, baseline)
    assert result is False


@pytest.mark.asyncio
async def test_gate_approves_when_missing_metrics_are_symmetric():
    """When neither side reports a dimension, that dimension is skipped —
    gain is computed on the evidence both sides actually supplied."""
    from trading_bot.governance.evolution_gate import EvolutionGate

    gate = EvolutionGate(validation_engine=None, threshold=0.05)
    candidate = {"reward": 0.9}
    baseline = {"reward": 0.1}
    result = await gate.validate_improvement("cand-sym", candidate, baseline)
    assert result is True


@pytest.mark.asyncio
async def test_gate_rejects_when_perf_missing():
    """A candidate with no perf/reward cannot demonstrate improvement —
    defaulting to 0.5 let metric-free proposals pass the gain check."""
    from trading_bot.governance.evolution_gate import EvolutionGate

    gate = EvolutionGate(validation_engine=None, threshold=0.05)
    candidate = {"safety_score": 1.0}
    baseline = {"reward": 0.1, "safety_score": 1.0}
    result = await gate.validate_improvement("cand-noperf", candidate, baseline)
    assert result is False


@pytest.mark.asyncio
async def test_gate_full_metrics_still_evaluates_all_dimensions():
    """Fully instrumented comparisons keep working: every supplied
    dimension is still gated, including robustness regression."""
    from trading_bot.governance.evolution_gate import EvolutionGate

    gate = EvolutionGate(validation_engine=None, threshold=0.05)
    full = {"reward": 0.9, "safety_score": 1.0, "latency": 5.0,
            "calibration": 0.95, "robustness": 0.6}
    baseline = {"reward": 0.1, "safety_score": 1.0, "latency": 10.0,
                "calibration": 0.9, "robustness": 0.8}
    # candidate robustness 0.6 < baseline 0.8 - 0.05 -> regression, reject
    assert await gate.validate_improvement("cand-reg", full, baseline) is False

    candidate = dict(full, robustness=0.85)
    assert await gate.validate_improvement("cand-ok", candidate, baseline) is True

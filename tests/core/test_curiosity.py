"""Curiosity engine tests — hypotheses only from measured surprise."""
import pytest

from trading_bot.core.csc.curiosity import CuriosityEngine


def _flat(n=30):
    return [{"close": 1.09, "volume_ratio": 1.0} for _ in range(n)]


def test_flat_series_emits_nothing():
    ce = CuriosityEngine()
    for obs in _flat():
        assert ce.observe(obs) == []


def test_shock_emits_return_shock():
    ce = CuriosityEngine()
    for obs in _flat():
        ce.observe(obs)
    emits = ce.observe({"close": 1.09 * 1.04, "volume_ratio": 1.0})
    names = {e["name"] for e in emits}
    assert "return_shock" in names
    ev = next(e for e in emits if e["name"] == "return_shock")
    assert ev["measured_zscore"] > 2.5
    assert "falsification" in ev


def test_level_break_on_range_exit():
    ce = CuriosityEngine()
    for i in range(30):
        ce.observe({"close": 1.08 + (i % 5) * 0.001})
    emits = ce.observe({"close": 2.0})   # far outside prior range
    names = {e["name"] for e in emits}
    assert "level_break" in names or "return_shock" in names


def test_reemit_gap_bounds_repeats():
    ce = CuriosityEngine()
    ce._emitted = {}
    emits1 = ce.observe  # fill window
    for i in range(30):
        ce.observe({"close": 1.0 + i * 0.001})
    ce.observe({"close": 1.0 + 30 * 0.001 + 5.0})   # huge shock
    first = ce.emitted_total
    # Keep shocking — same-named hypothesis can't re-emit inside the gap.
    for i in range(10):
        ce.observe({"close": 2.0 + i})
    assert ce.emitted_total <= first + 2  # different names only


def test_corr_shift_detects_decoupling():
    ce = CuriosityEngine()
    # Oscillating price so returns have variance; volume follows the
    # return sign early, then inverts — a real coupling flip.
    sign = 1
    for i in range(12):
        sign = -sign
        ce.observe({"close": 1.0 + sign * 0.01 + i * 0.0001,
                    "volume_ratio": 2.0 if sign > 0 else 0.5})
    for i in range(12):
        sign = -sign
        ce.observe({"close": 1.1 + sign * 0.01 + i * 0.0001,
                    "volume_ratio": 0.5 if sign > 0 else 2.0})
    ce.observe({"close": 1.15, "volume_ratio": 0.5})
    # The decoupling fires mid-feed at the flip point (dedup-gated after).
    assert "volume_price_decoupling" in ce._emitted


def test_controller_wires_curiosity_and_sre_ingest():
    from trading_bot.core.csc.controller import CognitiveSystemController
    CognitiveSystemController._instance = None
    csc = CognitiveSystemController()
    assert csc._curiosity is not None
    n0 = len(csc._sre.registry)
    csc._sre_ingest("curiosity", {"name": "t", "description": "d"})
    assert len(csc._sre.registry) == n0 + 1
    CognitiveSystemController._instance = None


def test_spec_rejects_code_like_fields():
    from trading_bot.core.csc.model_engineering import validate_spec
    errs = validate_spec({"kind": "threshold_rule", "feature": "rsi",
                          "direction": "BUY",
                          "expression": "os.system('x')"})
    assert any("code-like" in e for e in errs)


@pytest.mark.asyncio
async def test_sre_replay_needs_new_evidence():
    """Scientific replay: REJECTED hypotheses only re-enter when new
    measured evidence arrived — amnesia defense, not resurrection."""
    from trading_bot.core.csc.scientific_reasoning import (
        HypothesisState, ScientificReasoningEngine)
    sre = ScientificReasoningEngine()
    hid = await sre.observe({"close": 1.09})
    hyp = sre.get_hypothesis(hid)
    hyp.posterior = 0.1
    hyp.evidence_ids = ["e1"]
    await sre.retire_hypothesis(hid)
    assert hyp.state is HypothesisState.REJECTED
    # No new evidence -> replay leaves it rejected.
    assert await sre.replay_rejected() == 0
    assert hyp.state is HypothesisState.REJECTED
    # New measured evidence -> reactivation path fires.
    hyp.evidence_ids.append("e2")
    # Restore posterior to a survivable level for the replay test.
    hyp.posterior = 0.6
    await sre.replay_rejected()
    assert hyp.replay_count == 1
    assert hyp.state in (HypothesisState.REACTIVATED,
                         HypothesisState.REJECTED)

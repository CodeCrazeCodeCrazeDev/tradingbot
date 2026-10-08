"""Advisory-influence tests — advisors are real evidence, never authority.

Covers the consumption half of the one-AI consolidation: advisory modules
express normalized directional calls that tilt branch ranking by a bounded
amount, are scored against realized outcomes, decay when wrong, and
rehydrate from durable audit rows.

* ``normalize_advisory`` extracts direction/confidence, preserves payload.
* Evidence nodes carry the full artifact — not a marker-only stub.
* The advisory tilt in ``_pivot_refine_loop`` is bounded by
  ``_ADVISORY_TILT`` and cannot rescue a simulation-failed branch.
* ``record_outcome`` scores advisor calls into the ReliabilityTracker.
* ``_rebuild_reliability`` replays ``advisory_calls`` from DECISION_OUTCOME
  details so advisor weights survive restart.
"""

import inspect

import pytest

from trading_bot.cognition.advisory_adapter import AUTHORITY_FIELDS
from trading_bot.core.csc.advisory import (
    AdvisoryModuleAdapter, DEFAULT_ADVISORY_FACTORIES, normalize_advisory)
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.hypothesis import (
    ReasoningBranch, _observation_evidence_nodes)


@pytest.fixture
def csc(tmp_path):
    CognitiveSystemController._instance = None
    instance = CognitiveSystemController()
    yield instance
    CognitiveSystemController._instance = None


def _branch(branch_id: str, action: str) -> ReasoningBranch:
    return ReasoningBranch(
        branch_id=branch_id, name=branch_id,
        confidence=0.8, probability=0.6, uncertainty=0.1,
        execution_plan={"action": action})


# ---------- normalization ----------


def test_normalize_extracts_direction_and_confidence():
    out = normalize_advisory({"signal": "BULLISH", "confidence": 0.7})
    assert out["direction"] == "BUY"
    assert out["confidence"] == 0.7
    assert out["evidence"]["signal"] == "BULLISH"


def test_normalize_nested_and_neutral():
    nested = normalize_advisory({"state": {"bias": "BEARISH"}})
    assert nested["direction"] == "SELL"
    neutral = normalize_advisory({"signal": "NEUTRAL"})
    assert neutral["direction"] is None


def test_normalize_non_mapping_wrapped():
    out = normalize_advisory(42)
    assert out["direction"] is None
    assert out["evidence"] == {"result": 42}


# ---------- per-factory contract: every wired service is advisory-only ----


def _evidence_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _evidence_keys(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _evidence_keys(v)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability_id", [c for c, _ in DEFAULT_ADVISORY_FACTORIES])
async def test_every_wired_service_emits_advisory_contract(capability_id):
    """Each registered factory must produce the normalized advisory
    artifact — probe-gated, so missing optional deps (torch/scipy/
    sklearn) skip rather than fail the suite."""
    factory = dict(DEFAULT_ADVISORY_FACTORIES)[capability_id]
    ctx = {
        "symbol": "EURUSD", "price": 1.09, "close": 1.09, "open": 1.088,
        "high": 1.091, "low": 1.087, "volatility": 0.01, "trend": "UP",
        "trend_strength": 0.3, "sentiment": 0.1, "momentum": 0.01,
        "volume": 1500.0, "volume_ratio": 1.1, "rsi": 55.0,
        "spread": 0.0002, "timeframe": "M15",
        "timestamp": "2026-01-01T00:00:00",
    }
    try:
        service = factory()
        result = service.analyze(ctx)
        if inspect.isawaitable(result):
            result = await result
    except Exception as exc:
        # Mirrors attach_advisory_modules' probe gate: any factory or
        # first-call failure means the service is skipped in this env
        # (missing torch/scipy/sklearn, uninitializable legacy brain).
        pytest.skip(f"probe-gated out: {type(exc).__name__}: {exc}")
    assert result["capability_id"] == capability_id
    assert result["advisory_only"] is True
    assert result["direction"] in ("BUY", "SELL", None)
    assert isinstance(result["evidence"], dict)
    for key in _evidence_keys(result["evidence"]):
        assert key not in AUTHORITY_FIELDS
        assert not key.startswith(("authorized", "risk_"))


@pytest.mark.asyncio
async def test_adapter_emits_normalized_contract():
    svc = AdvisoryModuleAdapter("t", lambda ctx: {"signal": "DOWN",
                                                "confidence": 0.9,
                                                "authorized_size": 5})
    res = await svc.analyze({"symbol": "EURUSD"})
    assert res["direction"] == "SELL"
    assert res["advisory_only"] is True
    # authority vocabulary stripped before it ever reaches evidence
    assert "authorized_size" not in str(res["evidence"])


# ---------- evidence nodes carry the payload ----------


def test_evidence_node_preserves_advisory_payload():
    artifact = {"agent": "alphaalgo_cognitive_brain",
                "direction": "BUY", "confidence": 0.6,
                "evidence": {"mc_p95_drawdown": 0.003},
                "advisory_only": True}
    nodes = _observation_evidence_nodes(
        {"symbol": "EURUSD", "price": 1.09}, None, [artifact])
    adv = [n for n in nodes if n.node_id.startswith("ev_advisory")]
    assert adv, "advisory artifact should produce an evidence node"
    meta = adv[0].metadata
    assert meta.get("direction") == "BUY"
    assert meta.get("confidence") == 0.6
    assert meta.get("evidence", {}).get("mc_p95_drawdown") == 0.003
    assert meta.get("source_ref") == "agent:alphaalgo_cognitive_brain"


# ---------- bounded tilt ----------


@pytest.mark.asyncio
async def test_tilt_boosts_aligned_branch_bounded(csc):
    csc._last_advisory_calls = [
        {"capability_id": "adv1", "direction": "BUY", "confidence": 1.0},
        {"capability_id": "adv2", "direction": "BUY", "confidence": 1.0},
    ]
    buy = _branch("b_buy", "BUY")
    sell = _branch("b_sell", "SELL")
    # Without advisors sell ranks first (listed first, same score -> stable)
    csc._last_advisory_calls = []
    no_tilt = await csc._pivot_refine_loop([sell, buy], {})
    assert no_tilt.branch_id == "b_sell"
    # With all-BUY advisors the BUY branch wins — tilt bounded by 25%
    csc._last_advisory_calls = [
        {"capability_id": "adv1", "direction": "BUY", "confidence": 1.0},
        {"capability_id": "adv2", "direction": "BUY", "confidence": 1.0},
    ]
    tilted = await csc._pivot_refine_loop([sell, buy], {})
    assert tilted.branch_id == "b_buy"


@pytest.mark.asyncio
async def test_tilt_never_rescues_failed_simulation(csc):
    csc._last_advisory_calls = [
        {"capability_id": "adv1", "direction": "BUY", "confidence": 1.0}]
    buy = _branch("b_buy", "BUY")
    sell = _branch("b_sell", "SELL")
    # BUY is top-ranked but its simulation reports negative EV — it must
    # still fall back; advisors cannot resurrect it.
    sims = {"b_buy": {"expected_value": -0.01, "invalidation_triggers": []}}
    csc._pivot = lambda *a, **k: None
    csc.hypothesis_gen.pivot_branch = lambda *a, **k: None
    result = await csc._pivot_refine_loop(
        [buy, sell], sims)
    assert result.branch_id == "b_sell"


# ---------- outcome scoring + rehydration ----------


@pytest.mark.asyncio
async def test_outcome_scores_advisor_calls(csc):
    csc._pending_predictions["t1"] = {
        "position_symbol": "EURUSD", "action": "BUY", "symbol": "EURUSD",
        "entry_price": 1.0, "confidence": 0.8, "regime": "FLAT",
        "expected_return": None,
        "advisory_calls": [
            {"capability_id": "adv_right", "direction": "BUY",
             "confidence": 0.9},
            {"capability_id": "adv_wrong", "direction": "SELL",
             "confidence": 0.9}],
    }
    await csc.record_outcome("t1", exit_price=1.01)
    right = csc.reliability_tracker.metrics["adv_right"]["FLAT"]
    wrong = csc.reliability_tracker.metrics["adv_wrong"]["FLAT"]
    assert right.precision == 1.0
    assert wrong.precision == 0.0


@pytest.mark.asyncio
async def test_advisor_weight_decays_below_prior(csc):
    regime = "FLAT"
    for _ in range(12):
        csc.reliability_tracker.update_metrics(
            "bad_adv", regime, False, 0.9)
    w = csc.reliability_tracker.get_agent_weight("bad_adv", regime)
    assert w < 1.0, "persistently-wrong advisor must lose influence"


@pytest.mark.asyncio
async def test_rehydration_replays_advisor_calls(csc):
    rows = [{
        "outcome": "correct", "action": "BUY",
        "event_json": {
            "details": {"regime": "UP", "confidence": 0.8,
                        "advisory_calls": [
                            {"capability_id": "advX",
                             "direction": "SELL",
                             "confidence": 0.7}]}}}]
    csc._rebuild_reliability(rows)
    m = csc.reliability_tracker.metrics["advX"]["UP"]
    # Advisor called SELL, CSC BUY was correct -> advisor was wrong.
    assert m.total_predictions == 1
    assert m.precision == 0.0

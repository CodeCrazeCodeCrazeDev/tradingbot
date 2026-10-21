"""SRE wiring tests — the Scientific Reasoning Engine as an advisory
cognition service.

The SRE is the hypothesis lifecycle tracker: observe -> detect ->
question -> hypothesize -> evidence -> simulate -> counterfactual ->
debate -> design -> evaluate -> bayesian update -> calibrate ->
integrate -> retire. Every stage consumes real machinery (HMS, world
model, verifier swarm) or reports 'unmeasured' — nothing fabricated.
"""
import pytest

from trading_bot.core.csc.sre_bridge import SREAdvisoryService
from trading_bot.core.csc.scientific_reasoning import (
    HypothesisState, ScientificReasoningEngine)


def _obs():
    return {"symbol": "EURUSD", "price": 1.09, "close": 1.09,
            "volatility": 0.01, "momentum": 0.001, "timestamp": "t0"}


@pytest.mark.asyncio
async def test_cycle_runs_all_stages():
    sre = ScientificReasoningEngine()
    hid = await sre.run_cycle(_obs())
    hyp = sre.get_hypothesis(hid)
    assert hyp is not None
    # Numeric obs fields become measured model params.
    assert hyp.model_params["close"] == pytest.approx(1.09)
    # Reached an end-state (no world model -> lifecycle completes honest).
    assert hyp.state in (HypothesisState.DORMANT, HypothesisState.REJECTED,
                         HypothesisState.INCONCLUSIVE,
                         HypothesisState.INSTITUTIONALIZED)


@pytest.mark.asyncio
async def test_no_fabricated_evidence():
    """The fabricated-review path is gone: no human reviewer, neutral
    trust score, empty evidence when HMS is absent."""
    sre = ScientificReasoningEngine(hms=None, world_model=None)
    hid = await sre.run_cycle(_obs())
    hyp = sre.get_hypothesis(hid)
    assert hyp.approval_trace.get("reviewed_by") is None
    assert hyp.leni_trust_score == 1.0
    assert hyp.evidence_ids == []


@pytest.mark.asyncio
async def test_no_fabricated_scores():
    """Without a world model: expected_value 0 (not a default edge),
    validation_score 0 (not 0.75), debate 'unverified' (not np.random),
    no score inflation per cycle."""
    sre = ScientificReasoningEngine()
    hid = await sre.run_cycle(_obs())
    hyp = sre.get_hypothesis(hid)
    assert hyp.expected_value == 0.0
    assert hyp.validation_score == 0.0
    assert hyp.boundary_conditions.get("debate") == "unverified"
    assert hyp.boundary_conditions.get("experiment_executed") is False


@pytest.mark.asyncio
async def test_no_fabricated_action():
    """Without a hypothesis generator the target action is HOLD — a
    fabricated BUY must never reach the advisory channel."""
    sre = ScientificReasoningEngine()
    hid = await sre.run_cycle(_obs())
    hyp = sre.get_hypothesis(hid)
    assert hyp.model_params["target_action"] == "HOLD"


@pytest.mark.asyncio
async def test_unmeasured_anomaly_blocks_question():
    """No world model -> anomaly_status 'unmeasured' -> no formulated
    research question (never invented)."""
    sre = ScientificReasoningEngine(world_model=None)
    hid = await sre.run_cycle(_obs())
    hyp = sre.get_hypothesis(hid)
    assert hyp.boundary_conditions.get("anomaly_status") == "unmeasured"
    assert hyp.boundary_conditions.get("target_question") is None


@pytest.mark.asyncio
async def test_adapter_artifact_shape():
    sre = ScientificReasoningEngine()
    svc = SREAdvisoryService(sre)
    art = await svc.analyze(_obs())
    assert art["capability_id"] == "sre_lifecycle"
    assert art["advisory_only"] is True
    ev = art["evidence"]
    assert ev["status"] == "lifecycle"
    assert "state" in ev and "posterior" in ev


@pytest.mark.asyncio
async def test_adapter_throttles_and_bounds_registry():
    sre = ScientificReasoningEngine()
    svc = SREAdvisoryService(sre)
    for _ in range(30):
        await svc.analyze(_obs())
    # 30 calls -> 2 full cycles (1st + 26th) not 30.
    assert len(sre.registry) == 2


@pytest.mark.asyncio
async def test_statistical_anomaly_detection():
    """No world model -> real z-score anomaly over observed closes."""
    sre = ScientificReasoningEngine()
    for i in range(14):
        await sre.observe({"close": 1.09 + i * 0.0001})
    # A real shock: +3% against a flat series -> z-score anomaly.
    hid = await sre.observe({"close": 1.09 * 1.03})
    hyp = sre.get_hypothesis(hid)
    await sre.detect_anomalies(hid)
    assert hyp.boundary_conditions["anomaly_status"] == "detected"
    assert hyp.boundary_conditions["anomaly_zscore"] > 2.0


@pytest.mark.asyncio
async def test_ingest_external_provenance():
    sre = ScientificReasoningEngine()
    hid = sre.ingest_external(
        "phce_d", {"name": "cost_stress_survivor",
                   "description": "spread stress passed",
                   "confidence": 0.7})
    hyp = sre.get_hypothesis(hid)
    assert hyp is not None
    assert hyp.lineage.derivation_path == "external:phce_d"
    assert hyp.prior == pytest.approx(0.7)
    assert sre.ingest_log[-1]["source"] == "phce_d"


@pytest.mark.asyncio
async def test_epistemology_gate_holds_without_engine():
    """High posterior alone doesn't promote — the CDS epistemology audit
    must run; unavailable -> promotion HELD, not waived."""
    sre = ScientificReasoningEngine()
    sre._epistemology_tried = True   # engine absent in .venv
    hid = await sre.observe({"close": 1.09})
    hyp = sre.get_hypothesis(hid)
    hyp.posterior = 0.9
    hyp.boundary_conditions["debate"] = "survived"
    await sre.integrate_knowledge(hid)
    assert hyp.level.name != "LEVEL_3"
    assert "epistemology" in hyp.boundary_conditions["promotion_hold"]


def test_sre_report_surface():
    sre = ScientificReasoningEngine()
    sre.ingest_external("test", {"name": "h1"})
    rep = sre.report()
    assert rep["registry_size"] == 1
    assert rep["ingest_events"] == 1
    assert isinstance(rep["states"], dict)


# ------------------------------------------------- controller integration


@pytest.fixture
def csc():
    from trading_bot.core.csc.controller import CognitiveSystemController
    CognitiveSystemController._instance = None
    instance = CognitiveSystemController()
    yield instance
    CognitiveSystemController._instance = None


def test_csc_wires_sre(csc):
    assert csc._sre is not None
    ids = [s.capability_id for s in csc._advisory_services]
    assert "sre_lifecycle" in ids


def test_sre_is_self_wiring_node(csc):
    # The SRE joins the electorate like any advisory service — measured,
    # demotable, quarantinable on real emit quality.
    assert "sre_lifecycle" in csc._self_wiring.nodes


def test_sre_report_via_bridge(csc):
    svc = next(s for s in csc._advisory_services
               if s.capability_id == "sre_lifecycle")
    assert isinstance(svc, SREAdvisoryService)
    assert svc.engine is csc._sre

"""R0 regression tests: audit-integrity defects from the deep audit (2026-10-01).

These tests encode the DESIRED behavior of the one-brain trust chain. They
fail against the current codebase and pass only after the Release 1/2 fixes:

* fabricated provenance (git_sha="uca-2026-signed")
* hard-coded composite confidence components
* keyword-matching verifiers + generator keyword-feeding (self-certification)
* missing evidence provenance allowed through the graph gate
* wrong-instrument fallback ("BTC/USDT")
* dead HASP volatility guardrail (vol > 0.3 unreachable at FX scale)
* mechanical epistemic-uncertainty decay presented as learning
* forgeable inter-agent signatures (hard-coded "SYSTEM_SECRET_KEY")

The CSC import pulls torch (~15 s cold); keep CSC-dependent tests in this one
module so the cost is paid once per session.
"""

import asyncio

import pytest

from trading_bot.core.hms.models import (
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
    Hypothesis,
    RelationType,
    ResearchLedgerEntry,
)
from trading_bot.core.unified_event_bus import SignedInterAgentMessage
from trading_bot.core.verification.swarm import EvidenceGraphGate, VerificationSwarm


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _csc():
    """Minimal CSC instance: no world model / HMS needed for these stages."""
    from trading_bot.core.csc.controller import CognitiveSystemController

    return CognitiveSystemController()


@pytest.fixture
def csc(tmp_path, monkeypatch):
    """CSC instance whose lazy governance gate writes into tmp, not the repo."""
    monkeypatch.chdir(tmp_path)
    # The approval-gate singleton pins its storage dir at first construction;
    # redirect it so no human_layer/ artifacts land in the repo tree.
    try:
        from trading_bot.human_layer import approval as _approval

        if _approval._approval_gate_instance is not None:
            _approval._approval_gate_instance._storage_path = (
                tmp_path / "human_layer")
            _approval._approval_gate_instance._storage_path.mkdir(
                parents=True, exist_ok=True)
    except Exception:
        pass
    ctrl = _csc()
    yield ctrl
    try:
        from trading_bot.core.csc.controller import CognitiveSystemController

        asyncio.get_event_loop()
        asyncio.run(CognitiveSystemController.reset())
    except Exception:
        pass
    try:
        from trading_bot.core.unified_event_bus import UnifiedDecisionBus

        UnifiedDecisionBus.reset()
    except Exception:
        pass


def _ledger_with_real_evidence() -> ResearchLedgerEntry:
    """Entry whose evidence nodes carry resolvable source references and the
    measured values verifiers check — while the reasoning steps deliberately
    omit every auditor 'magic keyword'."""
    graph = EvidenceGraph()
    real_nodes = [
        ("ev_price", "Observed price 1.08", "obs:price", {"price": 1.08}),
        ("ev_volume", "Observed volume 1200000", "market_data:volume",
         {"volume": 1.2e6}),
        ("ev_vol", "Measured volatility 0.001", "feature:volatility",
         {"volatility": 0.001}),
        ("ev_trend", "Measured trend ranging", "observation:trend",
         {"trend": "ranging", "regime": "ranging"}),
        ("ev_risk", "Portfolio risk context", "risk_eval:portfolio",
         {"exposure": 0.02, "drawdown": 0.01, "quantity": 0.1}),
        ("ev_strategy", "Mean-reversion signal", "strategy_signal:mr_1",
         {"signal": "BUY"}),
    ]
    for node_id, content, ref, meta in real_nodes:
        graph.add_node(
            EvidenceNode(
                node_id=node_id,
                content=content,
                node_type="EVIDENCE",
                metadata={**meta, "source_ref": ref},
            )
        )
    graph.add_node(
        EvidenceNode(node_id="hyp_main", content="Bullish continuation",
                     node_type="HYPOTHESIS")
    )
    for node_id, *_ in real_nodes:
        graph.add_edge(
            EvidenceEdge(
                source_id=node_id, target_id="hyp_main",
                relation=RelationType.SUPPORTS,
            )
        )
    return ResearchLedgerEntry(
        reasoning_steps=[
            "Momentum estimate within one sigma of the rolling baseline",
            "Position size bounded by the configured exposure cap",
        ],
        evidence_graph_snapshot=graph,
        composite_confidence=0.6,
    )


def _ledger_with_fabricated_evidence() -> ResearchLedgerEntry:
    """Entry built the way the current generator builds it: generic filler
    nodes with no resolvable source reference."""
    graph = EvidenceGraph()
    for i in range(6):
        graph.add_node(
            EvidenceNode(
                node_id=f"node_branch_bull_{i}",
                content=f"Evidence {i} for Bull Case",
                node_type="EVIDENCE",
            )
        )
    for i in range(3):
        graph.add_edge(
            EvidenceEdge(
                source_id="node_branch_bull_0",
                target_id=f"node_branch_bull_{i + 1}",
                relation=RelationType.SUPPORTS,
            )
        )
    return ResearchLedgerEntry(
        reasoning_steps=[
            "Tail risk / black swan exposure evaluated against the regime",
            "Regime assessment: price=1.08, volatility=0.001",
        ],
        evidence_graph_snapshot=graph,
        composite_confidence=0.9,
    )


# ---------------------------------------------------------------------------
# fabricated artifacts
# ---------------------------------------------------------------------------

def test_ledger_provenance_has_no_fabricated_git_sha(csc):
    """_create_ledger_entry must not stamp a signed-looking fake git sha."""
    from trading_bot.core.csc.hypothesis import ReasoningBranch

    branch = ReasoningBranch(branch_id="b1", name="Bull Case")
    entry = csc._create_ledger_entry(branch, [])
    git_sha = getattr(entry.provenance, "git_sha", "")
    assert git_sha != "uca-2026-signed", (
        "provenance carries a fabricated signed git sha"
    )
    # Acceptable: real 40-hex sha, empty, or explicit unknown.
    assert git_sha in ("", "unknown") or (
        len(git_sha) == 40 and all(c in "0123456789abcdef" for c in git_sha)
    ), f"unexpected git_sha value: {git_sha!r}"


def test_composite_confidence_is_not_hardcoded(csc):
    """Confidence vector components must be measured or explicitly absent."""
    from trading_bot.core.csc.hypothesis import ReasoningBranch

    branch = ReasoningBranch(branch_id="b1", name="Bull Case", confidence=0.55)
    entry = csc._create_ledger_entry(branch, [])
    vec = csc._calculate_composite_confidence(entry)
    components = {
        "regime": getattr(vec, "regime", None),
        "execution": getattr(vec, "execution", None),
        "tail_risk": getattr(vec, "tail_risk", None),
        "model_stability": getattr(vec, "model_stability", None),
    }
    fabricated = {"regime": 0.8, "execution": 0.9, "tail_risk": 0.85,
                  "model_stability": 0.7}
    assert components != fabricated, (
        "composite confidence is the hard-coded 0.8/0.9/0.85/0.7 vector"
    )


def test_signed_message_has_no_builtin_forgeable_key():
    """A message must not verify under a key compiled into source."""
    msg = SignedInterAgentMessage(
        sender_id="attacker",
        sender_version="0",
        task_id="t",
        payload={"quantity": 10.0},
    )
    # Desired: verification without a provisioned verifier key fails closed.
    assert msg.verify_signature() is False, (
        "message verifies under the hard-coded SYSTEM_SECRET_KEY — forgable"
    )


# ---------------------------------------------------------------------------
# verification theater
# ---------------------------------------------------------------------------

def test_sound_evidence_does_not_need_magic_keywords():
    """Structured evidence without 'tail risk'/'regime' keywords must pass."""
    entry = _ledger_with_real_evidence()
    verdicts = asyncio.run(VerificationSwarm().run_swarm(entry))
    entry.verifier_reports = verdicts
    assert EvidenceGraphGate.verify_evidence_first(entry, verdicts), (
        f"vetoed on missing keywords: {EvidenceGraphGate.last_rejection_reason}"
    )


def test_fabricated_nodes_fail_evidence_provenance():
    """Filler nodes without resolvable source refs must be rejected even when
    the reasoning text contains every auditor keyword."""
    entry = _ledger_with_fabricated_evidence()
    verdicts = asyncio.run(VerificationSwarm().run_swarm(entry))
    entry.verifier_reports = verdicts
    assert not EvidenceGraphGate.verify_evidence_first(entry, verdicts), (
        "filler evidence with magic keywords passed the evidence gate"
    )


def test_verifier_does_not_unanimously_approve_nothing():
    """No verifier may return is_valid=True without inspecting the entry."""
    entry = _ledger_with_fabricated_evidence()
    verdicts = asyncio.run(VerificationSwarm().run_swarm(entry))
    assert verdicts, "swarm returned no verdicts"
    assert not all(v.is_valid for v in verdicts), (
        "every verifier approved fabricated evidence — verification theater"
    )


# ---------------------------------------------------------------------------
# semantic defects
# ---------------------------------------------------------------------------

def test_symbol_never_defaults_to_foreign_instrument(csc):
    """A proposal for an EURUSD observation must never emit BTC/USDT."""
    from trading_bot.core.csc.hypothesis import ReasoningBranch

    branch = ReasoningBranch(
        branch_id="b1", name="Bull Case", confidence=0.6,
        execution_plan={"action": "BUY"},  # no symbol — must not fabricate one
    )
    proposal = csc._select_optimal_action(branch, {}, trade_id="t1")
    assert proposal["symbol"] != "BTC/USDT", (
        "foreign-instrument default leaked into a proposal"
    )


def test_hasp_guardrail_fires_on_fx_extreme_volatility(csc):
    """volatility > 0.3 can never trigger on FX-scale vol (~0.001); an
    extreme 5% single-observation move must intervene."""
    normal = csc._apply_hasp_guardrails(
        {"volatility": 0.001, "symbol": "EURUSD"})
    assert normal.get("status") != "pf_intervention"
    extreme = csc._apply_hasp_guardrails(
        {"volatility": 0.05, "symbol": "EURUSD"})
    assert extreme.get("status") == "pf_intervention", (
        "guardrail is calibrated to a scale FX volatility can never reach"
    )


async def test_epistemic_uncertainty_does_not_mechanically_decay(tmp_path, monkeypatch):
    """Running tasks must not shrink uncertainty absent outcome evidence."""
    monkeypatch.chdir(tmp_path)
    ctrl = _csc()
    try:
        before = ctrl.state.epistemic_uncertainty
        await ctrl.execute_task("observe", {"symbol": "EURUSD", "price": 1.08})
        await ctrl.execute_task("observe", {"symbol": "EURUSD", "price": 1.081})
        assert ctrl.state.epistemic_uncertainty == before, (
            "epistemic_uncertainty decayed x0.9 per task — mechanical fake learning"
        )
    finally:
        from trading_bot.core.csc.controller import CognitiveSystemController
        from trading_bot.core.unified_event_bus import UnifiedDecisionBus

        await CognitiveSystemController.reset()
        UnifiedDecisionBus.reset()

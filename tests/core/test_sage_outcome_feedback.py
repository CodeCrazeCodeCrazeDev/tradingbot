"""SAGE edge evolution wired to settled trade outcomes.

Contract: advisor→signal claims recorded in HMS memory carry a weight
that realized position outcomes adjust — agreeing calls strengthen on
wins, dissenting calls weaken, and chronically wrong claims prune.
Evidence-only: edges are memory weights, never execution authority.
"""

import inspect

import pytest

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import (
    HierarchicalMemorySystem,
    SAGEGraphMemory,
)


@pytest.fixture
def hms(tmp_path):
    HierarchicalMemorySystem.reset()
    inst = HierarchicalMemorySystem(base_path=str(tmp_path / "hms"))
    yield inst
    HierarchicalMemorySystem.reset()


@pytest.fixture
def sage(tmp_path):
    return SAGEGraphMemory(str(tmp_path / "sage.graphml"))


def _bare_controller(hms=None):
    ctrl = object.__new__(CognitiveSystemController)
    ctrl.hms = hms
    return ctrl


# -- SAGEGraphMemory.upsert_evidence_edge ----------------------------------


def test_upsert_creates_then_reuses_edge(sage):
    triplet = ("advisor:momentum", "SIGNALED", "EURUSD:BUY")
    ctx = {"symbol": "EURUSD"}
    eid1 = sage.upsert_evidence_edge(triplet, ctx, {"confidence": 0.7})
    eid2 = sage.upsert_evidence_edge(triplet, ctx, {"confidence": 0.9})
    assert eid1 == eid2
    # One evolving claim per advisor→signal, not parallel duplicates.
    assert sage.graph.number_of_edges() == 1
    # Initial weight comes from the first observation's confidence.
    u, v, k = eid1
    assert sage.graph[u][v][k]["weight"] == pytest.approx(0.7)


def test_evolve_weights_positive_and_prune(sage):
    eid = sage.upsert_evidence_edge(
        ("advisor:x", "SIGNALED", "EURUSD:SELL"), {},
        {"confidence": 0.5})
    u, v, k = eid
    sage.evolve_weights(eid, 1.0)
    assert sage.graph[u][v][k]["weight"] == pytest.approx(0.6)
    # Repeated losses drive the weight under the prune floor and the
    # claim is removed rather than left as permanent negative evidence.
    for _ in range(10):
        sage.evolve_weights(eid, -1.0)
    assert not sage.graph.has_edge(u, v, k)


def test_evolve_ignores_unknown_edge(sage):
    sage.evolve_weights(("nobody", "none", "k"), 1.0)  # must not raise


# -- controller wiring ------------------------------------------------------


def test_signal_evidence_tags_agreement(hms):
    ctrl = _bare_controller(hms=hms)
    ctrl._last_advisory_calls = [
        {"capability_id": "momentum", "direction": "BUY",
         "confidence": 0.8},
        {"capability_id": "meanrev", "direction": "SELL",
         "confidence": 0.6},
        {"capability_id": "", "direction": "BUY"},       # no id — skipped
        {"capability_id": "flat", "direction": "HOLD"},  # non-directional
    ]
    entries = ctrl._sage_signal_evidence("EURUSD", "BUY")
    assert len(entries) == 2
    by_src = {e["edge_id"][0]: e for e in entries}
    assert by_src["advisor:momentum"]["agree"] == 1
    assert by_src["advisor:meanrev"]["agree"] == -1
    # Edges land in the graph keyed to each call's own direction.
    assert hms.sage.graph.has_edge(
        "advisor:momentum", "EURUSD:BUY")
    assert hms.sage.graph.has_edge(
        "advisor:meanrev", "EURUSD:SELL")


def test_outcome_feedback_moves_weights(hms):
    ctrl = _bare_controller(hms=hms)
    buy_e = hms.sage.upsert_evidence_edge(
        ("advisor:momentum", "SIGNALED", "EURUSD:BUY"), {},
        {"confidence": 0.5})
    sell_e = hms.sage.upsert_evidence_edge(
        ("advisor:meanrev", "SIGNALED", "EURUSD:SELL"), {},
        {"confidence": 0.5})
    pos = {"evidence_edge_ids": [
        {"edge_id": list(buy_e), "agree": 1},
        {"edge_id": list(sell_e), "agree": -1},
    ]}
    ctrl._sage_outcome_feedback(pos, 0.01)  # +1% win
    u, v, k = buy_e
    w_agree = hms.sage.graph[u][v][k]["weight"]
    u2, v2, k2 = sell_e
    w_dissent = hms.sage.graph[u2][v2][k2]["weight"]
    assert w_agree > 0.5    # agreeing advisor strengthened
    assert w_dissent < 0.5  # dissenting advisor weakened


def test_feedback_noop_without_hms_or_entries():
    ctrl = _bare_controller(hms=None)
    # Missing hms / missing edges must never break settlement.
    ctrl._sage_outcome_feedback(
        {"evidence_edge_ids": [{"edge_id": ["a", "b", "k"],
                                "agree": 1}]}, 0.01)
    ctrl._sage_outcome_feedback({}, 0.01)
    assert ctrl._sage_signal_evidence("EURUSD", "BUY") == []


def test_settlement_path_invokes_feedback():
    # The wire itself: _close_position must call the feedback hook —
    # guards against a refactor dropping it silently.
    src = inspect.getsource(CognitiveSystemController._close_position)
    assert "_sage_outcome_feedback" in src


def test_open_positions_preserve_edge_ids():
    ctrl = _bare_controller()
    ctrl._observation_seq = 7
    ctrl._open_positions = {"EURUSD": {
        "direction": "BUY", "entry_price": 1.1, "entry_seq": 3,
        "symbol": "EURUSD", "confidence": 0.6, "regime": "trend",
        "trade_ids": ["T1"],
        "evidence_edge_ids": [
            {"edge_id": ["advisor:m", "EURUSD:BUY", "SIGNALED_ab"],
             "agree": 1}],
    }}
    state = ctrl.export_open_positions()
    # JSON-safe round trip — edge ids serialize as lists.
    assert state["positions"]["EURUSD"]["evidence_edge_ids"][0][
        "edge_id"][0] == "advisor:m"

    ctrl2 = _bare_controller()
    ctrl2._observation_seq = 0
    ctrl2._open_positions = {}
    assert ctrl2.import_open_positions(state) == 1
    restored = ctrl2._open_positions["EURUSD"]
    assert restored["evidence_edge_ids"] == [
        {"edge_id": ["advisor:m", "EURUSD:BUY", "SIGNALED_ab"],
         "agree": 1}]

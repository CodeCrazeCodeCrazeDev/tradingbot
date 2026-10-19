"""AIStack — read-only three-plane introspection over the CSC.

Contract: snapshot/explain never raise on a partially-wired controller,
never mutate CSC state, and carry no authority fields.
"""

import json

import pytest

from trading_bot.ai_stack import AIStack
from trading_bot.core.csc.controller import CognitiveSystemController


@pytest.fixture
def csc():
    CognitiveSystemController._instance = None
    instance = CognitiveSystemController()
    yield instance
    CognitiveSystemController._instance = None


def test_snapshot_has_three_planes(csc):
    snap = AIStack(csc).snapshot()
    assert set(snap) == {"status", "state", "evidence", "selection",
                        "reflection"}
    for plane in ("state", "evidence", "selection", "reflection"):
        assert isinstance(snap[plane], dict)


def test_snapshot_is_json_safe(csc):
    snap = AIStack(csc).snapshot()
    json.dumps(snap, default=str)  # must not raise


def test_no_authority_fields(csc):
    """The read model must never surface authority-bearing keys."""
    snap = json.dumps(AIStack(csc).snapshot(), default=str)
    for forbidden in ("authorized_size", "risk_authorized", "veto",
                      "order_type", "approve"):
        assert forbidden not in snap


def test_explain_lines(csc):
    lines = AIStack(csc).explain()
    assert set(lines) == {"state", "evidence", "selection", "reflection"}
    assert all(isinstance(v, str) for v in lines.values())


def test_partially_wired_csc_does_not_raise():
    """An object missing every optional surface still snapshots."""
    class BareCSC:
        pass

    snap = AIStack(BareCSC()).snapshot()
    assert snap["evidence"]["attached"] == []
    assert snap["selection"]["pending_predictions"] == 0


def test_state_plane_reflects_runtime_mutation(csc):
    csc.vfe_history.append(0.42)
    csc.state.epistemic_uncertainty = 0.3
    s = AIStack(csc).state_plane()
    assert s["vfe_history_len"] == 1
    assert s["epistemic_uncertainty"] == pytest.approx(0.3)


def test_evidence_plane_lists_attached_advisors(csc):
    class DummyAdvisor:
        capability_id = "dummy_cap"

        def analyze(self, ctx):
            return {"direction": "BUY", "confidence": 0.5}

    csc.configure_cognition(DummyAdvisor())
    csc._last_advisory_calls = [
        {"capability_id": "dummy_cap", "direction": "BUY",
         "confidence": 0.5}]
    e = AIStack(csc).evidence_plane()
    assert "dummy_cap" in e["attached"]
    assert e["last_advisory_calls"][0]["capability_id"] == "dummy_cap"


def test_selection_plane_churn_math(csc):
    csc._observation_seq = 1000
    csc._recent_trade_seqs.extend([950, 990, 10])  # 10 outside the window
    sel = AIStack(csc).selection_plane()
    assert sel["churn"]["used_in_window"] == 2
    assert sel["advisory_tilt_bound"] == pytest.approx(0.25)

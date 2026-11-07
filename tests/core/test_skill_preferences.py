"""NanoResearch skill preference bank — DPO pair updates on the skill
bank (arXiv:2605.10813).

Contract: (chosen, rejected) routing pairs scored by realized utility
update per-task logits; capability-equal candidate ties resolve by
measured preference, not version. Evidence-only — no authority.
"""

import inspect
import math
import os
from types import SimpleNamespace

import numpy as np
import pytest

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.router import (
    SkillArtifact, SkillRouter, SkillType)
from trading_bot.core.csc.skill_preferences import SkillPreferenceBank


@pytest.fixture
def bank(tmp_path):
    return SkillPreferenceBank(
        state_path=str(tmp_path / "skill_prefs.json"))


@pytest.fixture
def router(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_PREF_STATE",
                       str(tmp_path / "skill_prefs.json"))
    SkillRouter.reset()
    inst = SkillRouter()
    yield inst
    SkillRouter.reset()


def _skill(skill_id, caps, version="1.0.0"):
    return SkillArtifact(
        skill_id=skill_id, skill_type=SkillType.PROGRAM,
        version=version, executable=lambda ctx: {},
        capabilities=set(caps), metadata={})


# -- bank units -------------------------------------------------------------


def test_pair_update_moves_logits(bank):
    lw, ll = bank.record_pair("market_ingestion", "alpha", "beta", 1.0)
    assert lw > 0 and ll < 0
    # Reversing the verdict reverses the direction of travel.
    lw2, ll2 = bank.record_pair(
        "market_ingestion", "alpha", "beta", -1.0)
    assert lw2 < lw and ll2 > ll


def test_confident_pairs_update_less(bank):
    # Repeated same-sign pairs: as z grows the BT gradient shrinks —
    # well-learned orderings shouldn't keep swinging.
    deltas = []
    prev = 0.0
    for _ in range(6):
        lw, _ = bank.record_pair("t", "w", "l", 1.0)
        deltas.append(lw - prev)
        prev = lw
    assert deltas[-1] < deltas[0]


def test_self_pair_ignored_and_logits_bounded(bank):
    before = dict(bank.logits)
    bank.record_pair("t", "a", "a", 1.0)
    bank.record_pair("t", "", "a", 1.0)
    assert bank.logits == before or not bank.logits
    for _ in range(200):
        bank.record_pair("t", "x", "y", 1.0)
    assert abs(bank.logits["t"]["x"]) <= 10.0
    assert abs(bank.logits["t"]["y"]) <= 10.0


def test_scores_softmax_and_choose(bank):
    for _ in range(5):
        bank.record_pair("t", "good", "bad", 1.0)
    s = bank.scores("t", ["good", "bad", "unseen"])
    assert s["good"] > s["bad"]
    assert abs(sum(s.values()) - 1.0) < 1e-9
    assert bank.choose("t", ["good", "bad", "unseen"]) == "good"
    assert bank.choose("t", []) is None


def test_persistence_roundtrip(tmp_path):
    path = str(tmp_path / "prefs.json")
    b1 = SkillPreferenceBank(state_path=path)
    b1.record_pair("t", "alpha", "beta", 1.0)
    b2 = SkillPreferenceBank(state_path=path)
    assert b2.logits["t"]["alpha"] > 0
    assert b2.pair_count == 1
    # Corrupt state → clean slate, no crash.
    with open(path, "w") as f:
        f.write("{not json")
    b3 = SkillPreferenceBank(state_path=path)
    assert b3.logits == {}


# -- router wiring ----------------------------------------------------------


def test_tie_break_uses_preference_bank(router):
    router.register_skill(_skill("lowver", {"hedging"}, "1.0.0"))
    router.register_skill(_skill("highver", {"hedging"}, "9.9.9"))
    # Preference for the lower version overrides the version sort.
    for _ in range(5):
        router._preference_bank.record_pair(
            "risk_task", "lowver", "highver", 1.0)
    chosen = router._resolve_best_skill({"hedging"}, task="risk_task")
    assert chosen.skill_id == "lowver"
    # Without preference, version ordering wins.
    chosen2 = router._resolve_best_skill({"hedging"}, task="other_task")
    assert chosen2.skill_id == "highver"


async def test_route_records_last_choice(router):
    router.register_skill(_skill("hedger", {"hedging", "risk_reduction"}))
    out = await router._route_task_async(
        "hedge_position", {"market": {}})
    assert router.last_choice is not None
    # hedging_behavior (v2.0.4) wins the capability tie on version order
    # when no preference data exists; both must appear as candidates.
    assert router.last_choice["chosen"] == "hedging_behavior"
    assert set(router.last_choice["candidates"]) >= {
        "hedging_behavior", "hedger"}


# -- controller wiring ------------------------------------------------------


def _bare():
    return object.__new__(CognitiveSystemController)


def test_skill_feedback_records_pairs(tmp_path):
    bank = SkillPreferenceBank(
        state_path=str(tmp_path / "p.json"))
    ctrl = _bare()
    ctrl.skill_router = SimpleNamespace(_preference_bank=bank)
    pos = {"skill_choices": [
        {"task": "hedge_position", "chosen": "hedger",
         "candidates": ["hedger", "alt_skill"]},
    ]}
    ctrl._skill_preference_feedback(pos, 0.01)  # +1% win
    assert bank.logits["hedge_position"]["hedger"] > 0
    assert bank.logits["hedge_position"]["alt_skill"] < 0
    # Loss reverses the verdict — one pair per unchosen candidate.
    ctrl._skill_preference_feedback(pos, -0.05)
    assert bank.pair_count == 2


def test_feedback_noop_without_bank_or_choices():
    ctrl = _bare()
    ctrl.skill_router = SimpleNamespace(_preference_bank=None)
    ctrl._skill_preference_feedback(
        {"skill_choices": [{"task": "t", "chosen": "a",
                            "candidates": ["a", "b"]}]}, 0.01)
    ctrl._skill_preference_feedback({}, 0.01)  # no crash


def test_settlement_and_registration_wired():
    src_close = inspect.getsource(
        CognitiveSystemController._close_position)
    assert "_skill_preference_feedback" in src_close
    src_reg = inspect.getsource(
        CognitiveSystemController._register_directional)
    assert "skill_choices" in src_reg
    src_guard = inspect.getsource(
        CognitiveSystemController._stage_guardrails)
    assert "_last_skill_choice" in src_guard


def test_open_positions_preserve_skill_choices():
    ctrl = _bare()
    ctrl._observation_seq = 1
    ctrl._fold_cursor = 0
    ctrl._fold_seq = 0
    ctrl._open_positions = {"EURUSD": {
        "direction": "BUY", "entry_price": 1.1, "entry_seq": 1,
        "symbol": "EURUSD", "trade_ids": ["T1"],
        "skill_choices": [{"task": "t", "chosen": "s",
                           "candidates": ["s", "o"]}],
    }}
    state = ctrl.export_open_positions()
    ctrl2 = _bare()
    ctrl2._observation_seq = 0
    ctrl2._open_positions = {}
    assert ctrl2.import_open_positions(state) == 1
    assert ctrl2._open_positions["EURUSD"]["skill_choices"] == [
        {"task": "t", "chosen": "s", "candidates": ["s", "o"]}]


def test_advisory_report_includes_skill_prefs(tmp_path):
    bank = SkillPreferenceBank(
        state_path=str(tmp_path / "p.json"))
    bank.record_pair("t", "a", "b", 1.0)
    ctrl = _bare()
    ctrl._advisory_services = []
    ctrl.reliability_tracker = SimpleNamespace(
        metrics={}, get_agent_weight=lambda *a, **k: 1.0)
    ctrl._funnel = {}
    ctrl.skill_router = SimpleNamespace(_preference_bank=bank)
    report = ctrl.advisory_report()
    assert report["skill_preferences"]["pair_count"] == 1

"""HIPIF strategic folding of the settled-outcome journal.

Contract: the settled-outcome deque is a temporary buffer; every
FOLD_WINDOW settlements its tail compresses into a durable 'lesson'
record in HMS self-improvement memory. Lessons are record-only — they
re-enter the evidence plane via recall_lessons/reflective context and
carry no authority.
"""

import inspect
from collections import deque

import pytest

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import HierarchicalMemorySystem


@pytest.fixture
def hms(tmp_path):
    HierarchicalMemorySystem.reset()
    inst = HierarchicalMemorySystem(base_path=str(tmp_path / "hms"))
    yield inst
    HierarchicalMemorySystem.reset()


def _bare(hms=None):
    ctrl = object.__new__(CognitiveSystemController)
    ctrl.hms = hms
    ctrl._settled_outcomes = deque(maxlen=256)
    ctrl._fold_cursor = 0
    ctrl._fold_seq = 0
    return ctrl


def _fill(ctrl, n, regime="trend", ret=0.01, symbol="EURUSD"):
    for i in range(n):
        ctrl._settled_outcomes.append({
            "symbol": symbol, "direction": "BUY",
            "realized_return": ret, "reason": "exit",
            "regime": regime, "entry_seq": i, "exit_seq": i + 1})


def test_fold_writes_lesson_at_window(hms):
    ctrl = _bare(hms)
    _fill(ctrl, 15)
    ctrl._maybe_fold_lessons()
    assert hms.recall_lessons(domain="execution_outcomes") == []
    _fill(ctrl, 1)
    ctrl._maybe_fold_lessons()
    lessons = hms.recall_lessons(domain="execution_outcomes")
    assert len(lessons) == 1
    ev = lessons[0]["evidence"]
    assert ev["fold_seq"] == 1
    assert ev["window"] == 16
    assert ev["lessons"]["trend"]["n"] == 16
    assert ev["lessons"]["trend"]["win_rate"] == pytest.approx(1.0)
    assert ev["lessons"]["trend"]["mean_return"] == pytest.approx(0.01)


def test_fold_cursor_advances_only_new_tail(hms):
    ctrl = _bare(hms)
    _fill(ctrl, 16, ret=0.01)
    ctrl._maybe_fold_lessons()
    _fill(ctrl, 16, ret=-0.01, regime="range")
    ctrl._maybe_fold_lessons()
    lessons = hms.recall_lessons(domain="execution_outcomes")
    assert len(lessons) == 2
    second = lessons[0]["evidence"]  # most-recent first
    assert second["fold_seq"] == 2
    assert second["window"] == 16
    assert "range" in second["lessons"]
    assert second["lessons"]["range"]["win_rate"] == pytest.approx(0.0)


def test_fold_mixed_regimes_in_one_window(hms):
    ctrl = _bare(hms)
    _fill(ctrl, 8, regime="trend", ret=0.02)
    _fill(ctrl, 8, regime="range", ret=-0.02)
    ctrl._maybe_fold_lessons()
    ev = hms.recall_lessons(domain="execution_outcomes")[0]["evidence"]
    assert set(ev["lessons"]) == {"trend", "range"}
    assert ev["lessons"]["trend"]["mean_return"] == pytest.approx(0.02)


def test_fold_noop_without_hms():
    ctrl = _bare(hms=None)
    _fill(ctrl, 20)
    ctrl._maybe_fold_lessons()  # must not raise
    assert ctrl._fold_seq == 0


def test_fold_cursor_clamps_after_eviction(hms):
    ctrl = _bare(hms)
    _fill(ctrl, 8)
    ctrl._fold_cursor = 999           # stale cursor beyond journal
    ctrl._maybe_fold_lessons()        # clamps to len=8; nothing unfurled
    assert hms.recall_lessons(domain="execution_outcomes") == []
    _fill(ctrl, 16)                   # len=24; clamped cursor=8 → 16 new
    ctrl._maybe_fold_lessons()
    lessons = hms.recall_lessons(domain="execution_outcomes")
    assert len(lessons) == 1
    # Window covers from the clamp point — the 8 surviving entries may
    # re-fold; that's the intended lossy-buffer semantics, not a crash.
    assert lessons[0]["evidence"]["window"] == 16


def test_settlement_path_invokes_fold():
    src = inspect.getsource(CognitiveSystemController._close_position)
    assert "_maybe_fold_lessons" in src


def test_fold_state_survives_export_import():
    ctrl = _bare()
    ctrl._observation_seq = 9
    ctrl._fold_cursor = 33
    ctrl._fold_seq = 2
    ctrl._open_positions = {}
    state = ctrl.export_open_positions()
    ctrl2 = _bare()
    ctrl2._observation_seq = 0
    ctrl2._open_positions = {}
    ctrl2.import_open_positions(state)
    assert ctrl2._fold_cursor == 33
    assert ctrl2._fold_seq == 2

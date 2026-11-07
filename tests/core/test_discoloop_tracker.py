"""DiscoLoop coupled discrete-continuous state tracker.

Contract: the reasoning recurrence's discrete entity channel and
continuous latent dynamics are tracked as coupled state — entity dwell,
churn, drift EMA, and a fragility flag for incoherent channels.
Evidence-only: feeds advisory_report and derived observation features.
"""

from types import SimpleNamespace

import numpy as np
import pytest

from trading_bot.core.csc.controller import (
    CognitiveSystemController, DiscoLoopCell)
from trading_bot.core.csc.loop_tracker import DiscoLoopTracker


def _bare():
    ctrl = object.__new__(CognitiveSystemController)
    return ctrl


# -- tracker units ----------------------------------------------------------


def test_step_tracks_entity_dwell_and_changes():
    t = DiscoLoopTracker()
    h = np.zeros(16)
    for _ in range(3):
        t.step(4, h)
    assert t.seq == 3 and t.entity == 4 and t.dwell == 3
    t.step(7, h)
    assert t.entity == 7 and t.dwell == 1 and t.entity_changes == 1


def test_drift_ema_reflects_latent_motion():
    t = DiscoLoopTracker(drift_alpha=1.0)  # alpha=1 → drift == last step
    t.step(0, np.zeros(8))
    assert t.drift == 0.0
    t.step(0, np.ones(8))                  # mean|Δh| = 1.0
    assert t.drift == pytest.approx(1.0)
    t.step(0, np.ones(8))
    assert t.drift == pytest.approx(0.0)


def test_coherence_flags_detached_discrete_channel():
    # Discrete channel churns entities while the latent barely moves —
    # fragmentation: the symbolic layer is detached from the dynamics.
    t = DiscoLoopTracker()
    still = np.zeros(8)
    for i in range(20):
        t.step(i, still)  # new entity each step, zero drift
    snap = t.snapshot()
    assert snap["churn_window"] == 1.0
    assert t.fragile is True


def test_coherence_flags_unresolved_latent():
    # Latent keeps jumping but never resolves into a new entity.
    t = DiscoLoopTracker()
    rng = np.random.RandomState(0)
    for i in range(20):
        # Same entity every step, alternating large latent moves so the
        # per-step drift stays high while the EMA baseline stays lower.
        t.step(0, rng.normal(0, 1.0 + 0.001 * i, 8) + (10.0 if i % 2 else -10.0))
    assert t.fragile is True


def test_coherent_recurrence_not_fragile():
    # Entities settle after brief churn and drift tracks motion — normal
    # coupled operation must not flag.
    t = DiscoLoopTracker(drift_alpha=0.5)
    h = np.zeros(8)
    for i in range(40):
        h = h * 0.9 + 0.1
        t.step(i // 10, h)  # entity holds for 10 steps, drift ~0.1
    snap = t.snapshot()
    assert snap["churn_window"] < 0.5
    assert t.fragile is False
    assert snap["drift_ema"] > 0


# -- controller integration -------------------------------------------------


async def test_reasoning_loop_steps_tracker():
    ctrl = _bare()
    ctrl.discoloop = DiscoLoopCell()
    ctrl.discrete_channel = []
    ctrl.continuous_state = {}
    ctrl._loop_tracker = DiscoLoopTracker()
    ctrl._max_loops = 2
    obs = {"price": 1.1, "volatility": 0.01, "volume": 1e6,
           "sentiment": 0.0}
    await ctrl._run_discoloop_reasoning(obs, k=4)
    assert ctrl._loop_tracker.seq == 4
    assert ctrl._loop_tracker.entity is not None
    assert ctrl._loop_tracker.dwell >= 1
    assert len(ctrl.discrete_channel) == 4


async def test_reasoning_loop_survives_missing_tracker():
    ctrl = _bare()
    ctrl.discoloop = DiscoLoopCell()
    ctrl.discrete_channel = []
    ctrl.continuous_state = {}
    ctrl._max_loops = 2
    await ctrl._run_discoloop_reasoning({}, k=2)  # no tracker → no crash
    assert len(ctrl.discrete_channel) == 2


def test_derived_features_emit_loop_state():
    ctrl = _bare()
    ctrl._obs_history = {}
    ctrl._vol_history = {}
    ctrl._peer_history = {}
    ctrl._loop_tracker = DiscoLoopTracker()
    for _ in range(3):
        ctrl._loop_tracker.step(2, np.ones(8))
    obs = {"symbol": "EURUSD", "price": 1.1, "close": 1.1, "volume": 10}
    ctrl._enrich_derived_features(obs)
    assert obs["loop_dwell"] == 3
    assert obs["loop_drift"] == pytest.approx(0.0)
    assert obs["loop_fragile"] == 0
    assert "loop_dwell" in obs["_derived_features"]


def test_advisory_report_includes_loop_state():
    ctrl = _bare()
    ctrl._advisory_services = []
    ctrl.reliability_tracker = SimpleNamespace(
        metrics={}, get_agent_weight=lambda *a, **k: 1.0)
    ctrl._funnel = {}
    ctrl._loop_tracker = DiscoLoopTracker()
    ctrl._loop_tracker.step(3, np.ones(8))
    report = ctrl.advisory_report()
    assert report["loop_state"]["seq"] == 1
    assert report["loop_state"]["entity"] == 3

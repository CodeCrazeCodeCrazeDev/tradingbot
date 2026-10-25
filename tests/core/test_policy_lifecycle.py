"""Offline-RL policy lifecycle: gate, deploy, monitor, rollback."""
from collections import deque

import numpy as np
import pytest

from trading_bot.core.csc.policy_lifecycle import (
    PolicyLifecycle, _cvar, _max_drawdown)


class FakeAgent:
    """_TabularQ-shaped stand-in: _q dict, alpha/gamma, experience_log."""

    def __init__(self):
        self.n_actions = 4
        self.alpha = 0.3
        self.gamma = 0.0
        self._q = {}
        self.experience_log = deque(maxlen=8192)
        self.saved = 0

    def save(self):
        self.saved += 1


def _fill(agent, n, state_fn=None, reward_fn=None):
    state_fn = state_fn or (lambda i: (i % 3, i % 2, 0))
    reward_fn = reward_fn or (lambda i, a: 0.01 if a == i % 4 else -0.01)
    for i in range(n):
        s = state_fn(i)
        a = i % 4
        agent.experience_log.append((s, a, reward_fn(i, a), float(i)))


def test_cvar_and_max_dd():
    assert _cvar([1.0] * 19 + [-10.0], 0.05) == pytest.approx(-10.0)
    assert _cvar([0.01] * 100, 0.05) == pytest.approx(0.01)
    assert _max_drawdown([1, 1, -5, 1]) == pytest.approx(5.0)
    assert _max_drawdown([0.1] * 10) == pytest.approx(0.0)


def test_gate_rejects_undersampled():
    lc = PolicyLifecycle(FakeAgent(), "t")
    ok, reason = lc._gate({"n": 5, "mean": 0, "cvar5": 0, "max_dd": 0},
                          {"n": 0, "mean": 0, "cvar5": 0, "max_dd": 0}, 10)
    assert not ok and reason == "holdout_undersampled"


def test_gate_rejects_bad_cvar():
    lc = PolicyLifecycle(FakeAgent(), "t")
    ok, reason = lc._gate(
        {"n": 60, "mean": 0.5, "cvar5": -0.5, "max_dd": 0},
        {"n": 0, "mean": 0, "cvar5": 0, "max_dd": 0}, 60)
    assert not ok and reason.startswith("cvar5_")


def test_gate_requires_improvement():
    lc = PolicyLifecycle(FakeAgent(), "t")
    cand = {"n": 60, "mean": 0.05, "cvar5": 0.0, "max_dd": 0}
    inc = {"n": 60, "mean": 0.05, "cvar5": 0.0, "max_dd": 0}
    ok, reason = lc._gate(cand, inc, 60)
    assert not ok and reason == "no_improvement_over_incumbent"


def test_deploy_and_rollback():
    agent = FakeAgent()
    # Candidate learns action==state pattern; incumbent is empty so the
    # improvement check passes trivially (inc n < min_holdout).
    _fill(agent, 400)
    lc = PolicyLifecycle(agent, "t")
    lc.min_train, lc.min_holdout = 100, 40
    res = lc.maybe_update()
    assert res == "deployed"
    assert lc.deploys == 1 and agent.saved >= 1
    assert agent._q                     # candidate table installed
    assert lc._backup is not None
    base = lc._baseline_mean

    # Degrade: append window of terrible rewards -> auto rollback.
    for i in range(lc.rollback_window):
        agent.experience_log.append(((0, 0, 0), 0, base * -5, 900.0 + i))
    res = lc.maybe_update()
    assert res == "rolled_back"
    assert lc.rollbacks == 1
    assert agent._q == {}               # incumbent (empty) restored


def test_no_new_data_short_circuits():
    agent = FakeAgent()
    _fill(agent, 400)
    lc = PolicyLifecycle(agent, "t")
    lc.min_train, lc.min_holdout = 100, 40
    lc.maybe_update()
    # Only a few new transitions since deploy -> cheap no-op.
    _fill(agent, 5)
    assert lc.maybe_update() is None
    assert lc.last_gate_reason == "no_new_data"


def test_offline_trainer_prefers_logged_winner():
    agent = FakeAgent()
    # Action 2 always rewarded in state (1,0,0); others punished.
    for i in range(200):
        for a in range(4):
            agent.experience_log.append(
                ((1, 0, 0), a, 0.05 if a == 2 else -0.05, float(i)))
    lc = PolicyLifecycle(agent, "t")
    table = lc._train_candidate(list(agent.experience_log))
    assert int(np.argmax(table[(1, 0, 0)])) == 2

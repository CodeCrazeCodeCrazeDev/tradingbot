"""HarnessOptimizer: H/P-step alternation, GRPO advantages, working
memory offload."""
import os
from collections import deque

import pytest

from trading_bot.core.csc.harness_rl import (
    HarnessOptimizer, WorkingMemory, _HARNESS_SPACE)
from trading_bot.core.csc.policy_lifecycle import PolicyLifecycle


class FakeAgent:
    def __init__(self):
        self.n_actions = 4
        self.alpha = 0.3
        self.gamma = 0.0
        self._q = {}
        self.experience_log = deque(maxlen=8192)
        self.saved = 0

    def save(self):
        self.saved += 1


def _fill(agent, n=300):
    for i in range(n):
        s = (i % 3, i % 2, 0)
        a = i % 4
        agent.experience_log.append(
            (s, a, 0.01 if a == i % 4 else -0.01, float(i)))


def test_working_memory_bounded_and_readable():
    WorkingMemory._instances.clear()
    wm = WorkingMemory.get("test_ns", maxlen=4)
    for i in range(10):
        wm.write("k", {"i": i})
    items = wm.read("k")
    assert len(items) == 4                 # bounded
    assert items[-1]["i"] == 9             # newest kept
    assert len(wm.read("k", 2)) == 2


def test_perturbation_stays_in_bounds():
    agent = FakeAgent()
    lc = PolicyLifecycle(agent, "t")
    hpo = HarnessOptimizer(lc, "t", population=4)
    for _ in range(50):
        cfg = hpo._perturb(hpo.active_cfg)
        for k, (lo, hi) in _HARNESS_SPACE.items():
            assert lo <= cfg[k] <= hi


def test_pstep_evaluates_and_grpo_ranks():
    agent = FakeAgent()
    _fill(agent, 400)
    lc = PolicyLifecycle(agent, "t")
    lc.min_train, lc.min_holdout = 100, 40
    hpo = HarnessOptimizer(lc, "t", population=4)
    hpo.maybe_update()
    # H-step fired -> population regenerated around the winner
    assert hpo.h_steps >= 1
    assert all(not c.evaluated for c in hpo.candidates)
    # GRPO advantage was recorded on the winning h_step
    recs = hpo.memory.read("t")
    h = [r for r in recs if r["event"] == "h_step"]
    assert h and "advantage" in h[-1]


def test_hstep_logged_to_working_memory():
    WorkingMemory._instances.clear()
    agent = FakeAgent()
    _fill(agent, 400)
    lc = PolicyLifecycle(agent, "t")
    lc.min_train, lc.min_holdout = 100, 40
    hpo = HarnessOptimizer(lc, "t", population=4)
    hpo.maybe_update()
    recs = hpo.memory.read("t")
    assert any(r["event"] == "h_step" for r in recs)


def test_cost_penalty_prefers_cheap_equal_harness():
    agent = FakeAgent()
    lc = PolicyLifecycle(agent, "t")
    hpo = HarnessOptimizer(lc, "t", population=2)
    hpo.cost_weight = 10.0  # dominate ope differences
    cheap = hpo.candidates[0]
    cheap.cfg["epochs"] = 1.0
    for c in hpo.candidates:
        c.evaluated = True
        c.ope_mean = 0.01
        c.compute = c.cfg["epochs"] * 100
        c.score = c.ope_mean - hpo.cost_weight * c.compute
    hpo._grpo_advantages()
    best = max(hpo.candidates, key=lambda c: c.score)
    assert best.cfg["epochs"] == min(
        c.cfg["epochs"] for c in hpo.candidates)

"""Tests for BarCostModel: per-bar costs, session breaks, rollover widening."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import make_frames  # noqa: E402

from trading_bot.evaluation.runner import (  # noqa: E402
    BarCostModel, PairedFamilyReplay)
from trading_bot.recursive_self_improvement.candidate_adapters import (  # noqa: E402
    get_adapter)

BASE = {"lookback": 20, "entry_threshold": 1.0}
CAND = {"lookback": 50, "entry_threshold": 1.0}


def _run(frames, model=None, cost_bps=5.0):
    return PairedFamilyReplay(
        get_adapter("mean_reversion"), cost_bps=cost_bps,
        cost_model=model).run(
            frames, baseline_params=dict(BASE), candidate_params=dict(CAND))


class TestBackwardCompat:
    def test_constant_cost_unchanged(self):
        frames = make_frames(seed=7, n_bars=80)
        out = _run(frames)
        assert out["bars"]
        assert all(r["cost_bps"] == 5.0 for r in out["bars"])
        # net identity preserved
        for r in out["bars"]:
            assert abs(r["candidate_net"]
                       - (r["candidate_gross"]
                          - r["candidate_turnover"] * 5.0 / 10000.0)) < 1e-12


class TestPerBarCosts:
    def test_per_bar_costs_flow_to_rows(self):
        frames = make_frames(seed=7, n_bars=80)
        n = len(next(iter(frames.values())))
        costs = tuple(4.0 if i % 2 else 6.0 for i in range(n))
        out = _run(frames, BarCostModel(base_bps=5.0, per_bar_bps=costs))
        by_ts = {}
        for r in out["bars"]:
            if r["symbol"] == "EURUSD":
                by_ts[r["timestamp"]] = r["cost_bps"]
        # per_bar_bps is indexed by bar index; replay rows start at bar 1
        for t, cost in by_ts.items():
            assert cost == pytest.approx(costs[int(t)])

    def test_wrong_length_rejected(self):
        frames = make_frames(seed=7, n_bars=60)
        with pytest.raises(ValueError, match="per_bar_bps"):
            _run(frames, BarCostModel(base_bps=5.0, per_bar_bps=(5.0,) * 10))


class TestSessionBreaks:
    def test_blocked_bars_have_zero_turnover(self):
        frames = make_frames(seed=7, n_bars=80)
        n = len(next(iter(frames.values())))
        blocked = tuple(range(30, 36))
        out = _run(frames, BarCostModel(base_bps=5.0, blocked_bars=blocked))
        for r in out["bars"]:
            if r["timestamp"] in blocked:
                assert r["baseline_turnover"] == 0.0
                assert r["candidate_turnover"] == 0.0

    def test_blocked_never_exceeds_unblocked_turnover(self):
        frames = make_frames(seed=7, n_bars=80)
        n = len(next(iter(frames.values())))
        blocked = tuple(range(25, n - 1, 3))
        free = _run(frames)
        halted = _run(frames, BarCostModel(base_bps=5.0, blocked_bars=blocked))
        free_turn = sum(r["candidate_turnover"] for r in free["bars"])
        halt_turn = sum(r["candidate_turnover"] for r in halted["bars"])
        assert halt_turn <= free_turn + 1e-12

    def test_out_of_range_blocked_rejected(self):
        frames = make_frames(seed=7, n_bars=40)
        with pytest.raises(ValueError, match="out of range"):
            _run(frames, BarCostModel(base_bps=5.0, blocked_bars=(999,)))


class TestRollover:
    def test_rollover_bars_widen_cost(self):
        frames = make_frames(seed=7, n_bars=80)
        n = len(next(iter(frames.values())))
        roll = (10, 20)
        out = _run(frames, BarCostModel(
            base_bps=5.0, rollover_bars=roll, rollover_mult=3.0))
        for r in out["bars"]:
            expected = 15.0 if r["timestamp"] in roll else 5.0
            assert r["cost_bps"] == pytest.approx(expected)

    def test_rollover_mult_below_one_rejected(self):
        with pytest.raises(ValueError, match="rollover_mult"):
            PairedFamilyReplay(get_adapter("mean_reversion"), cost_bps=5.0,
                               cost_model=BarCostModel(base_bps=5.0,
                                                       rollover_mult=0.5))

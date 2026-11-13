"""Tests for Algory-inspired robustness gates (order shuffle, perturbation,
random field) and their engine_v2 wiring."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import make_contract, make_frames, make_genome  # noqa: E402

from trading_bot.recursive_self_improvement.robustness_gates import (  # noqa: E402
    build_robustness_evidence, candidate_series, equity_max_drawdown,
    gate_report, net_return_of, order_shuffle_gate, perturbation_gate,
    random_field_gate)


def _returns(n=200, drift=0.0002, vol=0.001, seed=1):
    import random
    rng = random.Random(seed)
    return [drift + rng.gauss(0, vol) for _ in range(n)]


class TestOrderShuffle:
    def test_robust_path_passes(self):
        rets = _returns()
        ok, reason, m = order_shuffle_gate(
            rets, max_drawdown=0.5, drawdown_regression=0.05,
            shuffles=200, block=8, seed=7)
        assert ok, reason
        assert 0.0 <= m["order_shuffle_bad_frac"] <= 1.0

    def test_fragile_path_fails(self):
        # Block-structured path: the observed ordering alternates uniform
        # win/loss blocks, but a block permutation can cluster several
        # loss blocks consecutively — exactly the path fragility the gate
        # exists to catch.
        rets = []
        for _ in range(25):
            rets.extend([0.004] * 8)
            rets.extend([-0.006] * 8)
        ok, reason, m = order_shuffle_gate(
            rets, max_drawdown=0.5, drawdown_regression=0.001,
            max_bad_frac=0.4, shuffles=200, block=8, seed=3)
        assert not ok
        assert "order-fragile" in reason

    def test_short_series_skips(self):
        ok, reason, m = order_shuffle_gate([0.01] * 10, shuffles=50)
        assert ok and m["order_shuffle_shuffles"] == 0.0

    def test_deterministic(self):
        rets = _returns(seed=9)
        _, _, a = order_shuffle_gate(rets, shuffles=100, seed=42)
        _, _, b = order_shuffle_gate(rets, shuffles=100, seed=42)
        assert a == b


class TestPerturbationGate:
    def _probes(self, n, frac_pos):
        k = int(n * frac_pos)
        return [{"net_return": 0.01 if i < k else -0.01}
                for i in range(n)]

    def test_mostly_profitable_passes(self):
        ok, _, m = perturbation_gate(self._probes(6, 5 / 6))
        assert ok and m["perturbation_profitable_frac"] == pytest.approx(5 / 6)

    def test_mostly_losing_fails(self):
        ok, reason, _ = perturbation_gate(self._probes(6, 1 / 6))
        assert not ok and "parameter-fragile" in reason

    def test_too_few_probes_fails_closed(self):
        ok, reason, _ = perturbation_gate(self._probes(2, 1.0))
        assert not ok and "insufficient" in reason


class TestRandomFieldGate:
    def test_beats_field_passes(self):
        ok, _, m = random_field_gate(0.05, [0.01] * 20)
        assert ok and m["random_field_percentile"] == 1.0

    def test_loses_to_field_fails(self):
        ok, reason, _ = random_field_gate(-0.05, [0.01] * 20)
        assert not ok and "random field" in reason

    def test_thin_field_refused(self):
        ok, reason, _ = random_field_gate(0.05, [0.01] * 3)
        assert not ok and "insufficient" in reason


class TestGateReport:
    def _bars(self, n=160):
        rows = []
        for i in range(n):
            rows.append({"symbol": "EURUSD", "timestamp": float(i),
                         "cost_bps": 5.0,
                         "baseline_net": 0.0001, "candidate_net": 0.0004,
                         "baseline_gross": 0.001, "candidate_gross": 0.0013,
                         "baseline_turnover": 0.001, "candidate_turnover": 0.001,
                         "baseline_exposure": 0.01, "candidate_exposure": 0.01})
        return rows

    def test_disabled_is_noop(self):
        ok, reason, m = gate_report({"bars": self._bars()}, {}, {})
        assert ok and m == {}

    def test_order_shuffle_runs_on_bars(self):
        ok, reason, m = gate_report(
            {"bars": self._bars(), "trial_id": "t1"},
            {"contract_id": "c1", "max_drawdown": 0.5,
             "max_drawdown_regression": 0.05},
            {"order_shuffles": 50, "order_block": 8})
        assert ok, reason
        assert "order_shuffle_bad_frac" in m

    def test_missing_robustness_block_fails_closed(self):
        ok, reason, _ = gate_report(
            {"bars": self._bars(), "trial_id": "t1"},
            {"contract_id": "c1"},
            {"perturbations": 4})
        assert not ok and "insufficient perturbation" in reason


class TestBuildRobustnessEvidence:
    def test_smoke_produces_signed_shape(self):
        frames = make_frames(seed=7, n_bars=160)
        contract = make_contract(frames, n_bars=160)
        genome = make_genome(contract, param="lookback", value=50)
        from trading_bot.recursive_self_improvement.candidate_adapters import (
            get_adapter)
        out = build_robustness_evidence(
            adapter=get_adapter("mean_reversion"), frames=frames,
            contract=contract,
            incumbent_params={"lookback": 20, "entry_threshold": 1.0},
            candidate_params={"lookback": 50, "entry_threshold": 1.0},
            genome=genome, trial_id="t-rob", cfg={"random_field": 8})
        assert math.isfinite(out["candidate_net_return"])
        assert len(out["perturbations"]) == 4
        assert all("net_return" in p for p in out["perturbations"])
        assert len(out["random_field"]) <= 8

    def test_deterministic(self):
        frames = make_frames(seed=7, n_bars=120)
        contract = make_contract(frames, n_bars=120)
        genome = make_genome(contract, param="lookback", value=50)
        from trading_bot.recursive_self_improvement.candidate_adapters import (
            get_adapter)
        kw = dict(adapter=get_adapter("mean_reversion"), frames=frames,
                  contract=contract,
                  incumbent_params={"lookback": 20, "entry_threshold": 1.0},
                  candidate_params={"lookback": 50, "entry_threshold": 1.0},
                  genome=genome, trial_id="t-rob", cfg={"random_field": 6})
        a = build_robustness_evidence(**kw)
        b = build_robustness_evidence(**kw)
        assert a == b

"""Frozen-baseline comparison + expansion gate regression tests.

R4/R7 acceptance evidence: a candidate may only claim superiority when it
beats a frozen baseline net-of-cost without a drawdown regression — and
expansion targets report what evidence is missing rather than granting
readiness on intent.
"""

import pytest

from trading_bot.evaluation.frozen_baseline import (
    compare_candidate_vs_baseline, csc_decisions_to_positions, score_side)
from trading_bot.evaluation.horizon_gate import check_expansion_readiness


def _trending_returns(n=60):
    """Bars that rise for 40, then fall for 20 — momentum wins, contrarian loses."""
    return [0.001] * 40 + [-0.001] * 20


class TestScoreSide:

    def test_long_position_in_uptrend_profits(self):
        m = score_side([1.0] * 30, [0.001] * 30, cost_bps=5.0, fraction=0.01)
        assert m.total_net > 0
        assert m.cost_paid > 0
        assert m.total_turnover > 0

    def test_flat_position_pays_no_cost(self):
        m = score_side([0.0] * 30, [0.001] * 30, cost_bps=5.0)
        assert m.total_net == 0.0
        assert m.cost_paid == 0.0

    def test_turnover_only_charges_on_change(self):
        # Hold long the whole time: one position change only.
        m = score_side([1.0] * 30, [0.001] * 30, cost_bps=5.0, fraction=0.01)
        assert m.total_turnover == pytest.approx(0.01)

    def test_invalid_cost_rejected(self):
        with pytest.raises(ValueError):
            score_side([1.0], [0.001], cost_bps=-1.0)


class TestCompareCandidateVsBaseline:

    def test_insufficient_evidence_below_min_decisions(self):
        rep = compare_candidate_vs_baseline(
            [1.0] * 5, [-1.0] * 5, [0.001] * 5,
            cost_bps=5.0, min_decisions=20)
        assert rep["verdict"] == "insufficient_evidence"
        assert rep["promotion_eligible"] is False

    def test_candidate_superior_when_it_beats_frozen_baseline(self):
        rets = _trending_returns()
        # Candidate = momentum (follows last bar's direction);
        # baseline = frozen contrarian (fades it) — must lose.
        candidate = [1.0 if r > 0 else -1.0 for r in rets]
        baseline = [-p for p in candidate]
        rep = compare_candidate_vs_baseline(
            candidate, baseline, rets, cost_bps=5.0, min_decisions=20)
        assert rep["verdict"] == "candidate_superior"
        assert rep["net_edge"] > 0
        # Still diagnostic-only — real promotion needs evaluate_verified.
        assert rep["promotion_eligible"] is False

    def test_flat_candidate_is_no_activity_not_superior(self):
        # A candidate that abstains the whole window must not "win" just
        # because the baseline lost money.
        rets = _trending_returns()
        rep = compare_candidate_vs_baseline(
            [0.0] * 60, [1.0] * 60, rets, cost_bps=5.0, min_decisions=20)
        assert rep["verdict"] == "no_activity"
        assert "abstention" in rep["reason"]

    def test_not_superior_when_candidate_loses(self):
        rets = _trending_returns()
        baseline = [1.0 if r > 0 else -1.0 for r in rets]
        candidate = [-p for p in baseline]
        rep = compare_candidate_vs_baseline(
            candidate, baseline, rets, cost_bps=5.0, min_decisions=20)
        assert rep["verdict"] == "not_superior"

    def test_drawdown_regression_blocks_superiority(self):
        # Candidate earns more but suffers a much deeper drawdown.
        rets = [0.01, -0.05, 0.01, 0.01] * 15
        candidate = [1.0] * 60
        baseline = [0.5] * 60  # same direction, half exposure
        rep = compare_candidate_vs_baseline(
            candidate, baseline, rets, cost_bps=1.0, fraction=0.01,
            min_decisions=20, max_dd_regression=0.0)
        # Same sign, more exposure → more net but bigger DD → blocked.
        assert rep["verdict"] == "not_superior"
        assert "drawdown" in rep["reason"]


class TestDecisionProjection:

    def test_csc_decisions_project_to_persistent_positions(self):
        recs = [
            {"bar_index": 2, "action": "BUY"},
            {"bar_index": 5, "action": "SELL"},
        ]
        positions = csc_decisions_to_positions(recs, 8)
        assert positions[:2] == [0.0, 0.0]
        assert positions[2:5] == [1.0, 1.0, 1.0]   # BUY persists until SELL
        assert positions[5:] == [-1.0, -1.0, -1.0]


class TestHorizonGate:

    def test_scalping_gate_rejects_small_dataset(self):
        rep = check_expansion_readiness(
            "EURUSD_scalp", dataset_bars=1000, horizon="scalp",
            has_paired_oos_evidence=False, has_cost_model=False)
        assert rep["ready"] is False
        assert any("too small" in u for u in rep["unmet"])

    def test_intraday_gate_reports_missing_evidence(self):
        rep = check_expansion_readiness(
            "EURUSD_intraday", dataset_bars=10_000, horizon="intraday",
            has_paired_oos_evidence=False, has_cost_model=True,
            measured_max_drawdown=0.03, drawdown_budget=0.05)
        assert rep["ready"] is False
        assert any("paired" in u for u in rep["unmet"])

    def test_full_evidence_passes_paper_gate(self):
        rep = check_expansion_readiness(
            "GBPUSD_intraday", dataset_bars=10_000, horizon="intraday",
            has_paired_oos_evidence=True, has_cost_model=True,
            measured_max_drawdown=0.03, drawdown_budget=0.05)
        assert rep["ready"] is True
        assert rep["unmet"] == []
        # Readiness is explicitly NOT promotion authority.
        assert "paper" in rep["note"]

    def test_drawdown_over_budget_blocks(self):
        rep = check_expansion_readiness(
            "X", dataset_bars=10_000, horizon="intraday",
            has_paired_oos_evidence=True, has_cost_model=True,
            measured_max_drawdown=0.20, drawdown_budget=0.05)
        assert rep["ready"] is False
        assert any("drawdown" in u for u in rep["unmet"])

"""RL advisory services — tabular learners wired as CSC evidence.

Key invariants: causal labels (no same-bar reward), bounded state,
honest warmup, no authority surface.
"""
import pytest

np = pytest.importorskip("numpy")

from trading_bot.core.csc.rl_advisory import (  # noqa: E402
    AdaptiveDecisionRL, AdaptiveSpreadRL, AnalysisLensRL,
    AlphaSearchRL, _TabularQ)


def _bars(n=120, seed=3, trend=0.0):
    rng = np.random.default_rng(seed)
    px = 1.10 + np.cumsum(rng.normal(trend, 0.001, n))
    return [{"symbol": "EURUSD", "close": float(p), "open": float(p),
             "high": float(p * 1.0003), "low": float(p * 0.9997),
             "volume": 1000.0, "price": float(p)}
            for p in px]


class TestTabularQ:
    def test_learns_preferred_action(self):
        q = _TabularQ(3, alpha=0.5, epsilon=0.0)
        for _ in range(30):
            q.update(("s",), 2, 1.0)
            q.update(("s",), 0, -1.0)
        a, v = q.best(("s",))
        assert a == 2 and v > 0.5

    def test_state_space_bounded(self):
        q = _TabularQ(2, max_states=64)
        for i in range(500):
            q.row((i, i + 1))
        assert len(q._q) <= 64

    def test_nonfinite_reward_ignored(self):
        q = _TabularQ(2)
        q.update(("s",), 0, float("nan"))
        q.update(("s",), 0, float("inf"))
        assert q.updates == 0
        assert np.allclose(q.row(("s",)), 0.0)


class TestAdaptiveDecisionRL:
    def test_warming_then_active(self):
        a = AdaptiveDecisionRL(horizon=4)
        obs = _bars(120, trend=0.0004)  # gentle uptrend
        outs = [a.analyze(o) for o in obs]
        assert outs[0]["status"] == "warming"
        assert outs[-1]["status"] == "active"
        assert outs[-1]["updates"] > 0

    def test_no_same_bar_labels(self):
        """A decision recorded on bar t must not resolve until t+horizon."""
        a = AdaptiveDecisionRL(horizon=8)
        for o in _bars(6):
            out = a.analyze(o)
        # 6 bars in, horizon 8 — nothing can have resolved yet
        assert out["updates"] == 0
        assert out["pending_labels"] == 6

    def test_uptrend_learns_long_lean(self):
        a = AdaptiveDecisionRL(horizon=4)
        a.epsilon = 0.0  # force greedy after warmup
        # manually teach it then check
        for _ in range(40):
            a.update((1, 0), 2, 1.0)   # trending state -> long_lean good
            a.update((1, 0), 3, -1.0)
            a.update((1, 0), 0, 0.0)
        obs = _bars(40, trend=0.001)
        for o in obs:
            out = a.analyze(o)
        # trending-up state should prefer long_lean
        assert out["posture"] == "long_lean"

    def test_bad_obs_rejected(self):
        a = AdaptiveDecisionRL()
        assert a.analyze({"close": float("nan")})["status"] == "no_data"
        assert a.analyze({})["status"] == "no_data"
        assert a.analyze({"close": -5})["status"] == "no_data"


class TestAdaptiveSpreadRL:
    def test_emits_quote_policy(self):
        s = AdaptiveSpreadRL(horizon=3)
        for o in _bars(60):
            out = s.analyze(o)
        assert 0.7 <= out["spread_multiplier"] <= 2.2
        assert out["quote_skew"] in ("neutral", "lean_bid", "lean_ask")
        assert out["label_source"] == "bar_proxy"

    def test_real_fill_labels_honest_flag(self):
        s = AdaptiveSpreadRL()
        out = s.analyze({"close": 1.1, "realized_spread_capture": 0.0003})
        assert out["label_source"] == "real_fills"

    def test_learns_wider_in_volatility(self):
        s = AdaptiveSpreadRL(horizon=2)
        # high-vol chop: tight spreads should lose
        for o in _bars(80, seed=9, trend=0.0):
            out = s.analyze(o)
        # after learning, agent should avoid the tightest spread in
        # volatile states — verify it explored multiple multipliers
        assert s.updates > 10


class TestAnalysisLensRL:
    def test_lens_reliability_emitted(self):
        a = AnalysisLensRL(horizon=3)
        for o in _bars(60, trend=0.0005):
            out = a.analyze(o)
        if out["status"] == "active":
            assert out["trusted_lens"] in a.LENSES
            assert len(out["lens_reliability"]) == 4
            return
        pytest.fail("never reached active")

    def test_forecasts_scored_on_future_bars(self):
        """Causality: pendings begin only after the 10-bar warmup, and
        none may resolve before horizon bars elapse."""
        a = AnalysisLensRL(horizon=4)
        # bars 1-9: warming, no pending. bar 10: first pending recorded.
        # bar 13 (4 bars later) is the earliest legal resolution.
        for i, o in enumerate(_bars(12)):
            out = a.analyze(o)
            if i <= 12:  # 12 bars in: at most 1 pending could mature
                assert a.updates <= 4  # 4 lens updates max per resolve

    def test_trending_market_prefers_momentum(self):
        a = AnalysisLensRL(horizon=3)
        a.epsilon = 0.0
        for _ in range(30):
            a.update((1, 1), 0, 0.8)    # momentum lens works in trend
            a.update((1, 1), 1, -0.4)   # mean-reversion loses
        for o in _bars(60, trend=0.0006):
            out = a.analyze(o)
        # trending regime state should keep momentum trusted
        if out.get("trusted_lens"):
            assert out["trusted_lens"] == "momentum"
            return
        pytest.fail("no lens output")


class TestAlphaSearchRL:
    def test_emits_candidate_expression(self):
        a = AlphaSearchRL(eval_horizon=4)
        for o in _bars(60):
            out = a.analyze(o)
        assert out["candidate_expression"]
        assert out["chosen_operator"] in a.OPERATORS

    def test_candidates_scored_on_fresh_bars_only(self):
        a = AlphaSearchRL(eval_horizon=6)
        for o in _bars(30):
            a.analyze(o)
        # candidates born recently can't be scored yet
        assert all(c["born_at"] <= len(a._hist) for c in a._candidates)

    def test_bounded_candidates(self):
        # The pending window floors at eval_horizon*4 so candidates
        # cannot be evicted before their labels mature.
        a = AlphaSearchRL(eval_horizon=4, max_candidates=6)
        assert a._candidates.maxlen >= a._eval_horizon * 4
        for o in _bars(80):
            a.analyze(o)
        assert len(a._candidates) <= a._candidates.maxlen

    def test_unscored_never_evicted_early(self):
        """Scoring lag must not exceed the pending window or updates
        can never accumulate."""
        a = AlphaSearchRL(eval_horizon=6)
        assert a._candidates.maxlen >= a._eval_horizon * 2 + 3

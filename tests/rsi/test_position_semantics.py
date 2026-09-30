"""Regression: replay position semantics — "hold" preserves, "close" exits.

Strategy vocab (institutional_strategies): buy/sell/hold/close and
long_spread/short_spread/hold/close. Replays must treat "hold" as
no-directive (position carries) and "close" as a target of flat; turnover is
charged only when the position actually changes.
"""

from __future__ import annotations

import pandas as pd
import pytest

from trading_bot.evaluation.runner import (
    BoundedMeanReversionReplay,
    PairedFamilyReplay,
)
from trading_bot.recursive_self_improvement.candidate_adapters import (
    AdapterSpec,
    get_adapter,
)


class _ScriptedStrategy:
    """Emits a fixed action sequence, one per generate_signal call."""

    def __init__(self, actions, **kwargs):
        self.actions = list(actions)
        self.lookback = kwargs.get("lookback", 1)
        self.calls = 0

    def generate_signal(self, *args):
        action = self.actions[min(self.calls, len(self.actions) - 1)]
        self.calls += 1
        return {"action": action}


def _frame(n=8, symbol="EURUSD"):
    return pd.DataFrame(
        [{"timestamp": i, "open": 1.10, "close": 1.10 + 0.001 * i,
          "high": 1.11, "low": 1.09, "volume": 1000.0} for i in range(n)]
    )


def _spec(actions_by_side):
    real = get_adapter("mean_reversion")
    builds = iter(actions_by_side)
    return AdapterSpec(
        family="mean_reversion",
        allowed=real.allowed,
        pairs=False,
        min_history=lambda p: 1,
        build=lambda params: _ScriptedStrategy(next(builds)),
        direction_of=real.direction_of,
    )


def test_hold_preserves_position_and_close_exits():
    fraction = 0.25
    replay = PairedFamilyReplay(
        _spec([["buy", "hold", "hold", "close", "hold", "sell", "hold"],
               ["hold", "hold", "buy", "hold", "close", "hold", "hold"]]),
        cost_bps=5.0, fraction=fraction,
    )
    result = replay.run({"EURUSD": _frame()}, baseline_params={}, candidate_params={})
    rows = result["bars"]
    # baseline script: buy hold hold close hold sell hold
    expected_pos = [1, 1, 1, 0, 0, -1, -1]
    assert [r["baseline_direction"] for r in rows] == expected_pos
    # candidate script: hold hold buy hold close hold hold
    expected_cand = [0, 0, 1, 1, 0, 0, 0]
    assert [r["candidate_direction"] for r in rows] == expected_cand
    for row, pos, cpos in zip(rows, expected_pos, expected_cand):
        assert row["baseline_exposure"] == pytest.approx(fraction * abs(pos))
        assert row["candidate_exposure"] == pytest.approx(fraction * abs(cpos))
    # Turnover charged only on the bar where position changes.
    changes = [abs(expected_pos[i] - ([0] + expected_pos)[i]) for i in range(7)]
    for row, delta in zip(rows, changes):
        assert row["baseline_turnover"] == pytest.approx(delta * fraction)


def test_direction_of_vocabulary_is_explicit():
    direction_of = get_adapter("mean_reversion").direction_of
    assert direction_of({"action": "buy"}) == 1
    assert direction_of({"action": "sell"}) == -1
    assert direction_of({"action": "close"}) == 0
    assert direction_of({"action": "hold"}) is None
    assert direction_of({"action": "HOLD"}) is None
    with pytest.raises(ValueError):
        direction_of({"action": "nonsense"})

    spread_of = get_adapter("stat_arb").direction_of
    assert spread_of({"action": "long_spread"}) == 1
    assert spread_of({"action": "short_spread"}) == -1
    assert spread_of({"action": "close"}) == 0
    assert spread_of({"action": "hold"}) is None


def test_bounded_replay_hold_preserves(monkeypatch):
    import trading_bot.strategies.institutional_strategies as inst

    scripts = {2: ["buy", "hold", "close", "hold"], 3: ["hold", "buy", "hold"]}

    def _factory(lookback, entry_threshold=1.0):
        return _ScriptedStrategy(scripts[lookback], lookback=lookback)

    monkeypatch.setattr(inst, "MeanReversionStrategy", _factory)
    replay = BoundedMeanReversionReplay(cost_bps=5.0, fraction=0.5)
    df = _frame(7)
    result = replay.run(df, symbol="EURUSD", baseline_lookback=2, candidate_lookback=3)
    rows = result["bars"]
    # baseline (lookback 2, consulted at i>=2): buy hold close hold -> pos 1,1,0,0
    # candidate (lookback 3, consulted at i>=3): hold buy hold -> pos 0,0,1,1
    base_pos = [0] + [1, 1, 0, 0] + [0]
    cand_pos = [0, 0] + [0, 1, 1] + [1]
    assert [int(round(r["baseline_exposure"] / 0.5)) for r in rows] == base_pos
    assert [int(round(r["candidate_exposure"] / 0.5)) for r in rows] == cand_pos
    for row in rows:
        for side in ("baseline", "candidate"):
            expected = row[f"{side}_gross"] - row[f"{side}_turnover"] * 5.0 / 10000.0
            assert row[f"{side}_net"] == pytest.approx(expected)

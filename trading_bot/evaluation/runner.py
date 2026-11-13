"""Replay-backed simulation runner for recursive improvement experiments."""

from __future__ import annotations

import inspect
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .walk_forward import WalkForwardEvaluator

UNSEALED_EVIDENCE_SOURCE = "unsealed_diagnostic_replay"
PAIRED_BAR_KEYS = (
    "symbol", "timestamp", "cost_bps",
    "baseline_gross", "candidate_gross",
    "baseline_turnover", "candidate_turnover",
    "baseline_exposure", "candidate_exposure",
    "baseline_net", "candidate_net",
)


def _net_of_cost(gross: float, turnover: float, cost_bps: float) -> float:
    """Single authoritative cost convention shared by diagnostic replays."""
    return gross - turnover * cost_bps / 10000.0


def _paired_bar(symbol: str, timestamp: Any, cost_bps: float,
                baseline_gross: float, candidate_gross: float,
                baseline_turnover: float, candidate_turnover: float,
                baseline_exposure: float, candidate_exposure: float) -> Dict[str, Any]:
    """Emit one paired-return row in the schema evaluate_verified consumes."""
    return {
        "symbol": symbol,
        "timestamp": timestamp,
        "cost_bps": cost_bps,
        "baseline_gross": baseline_gross,
        "candidate_gross": candidate_gross,
        "baseline_turnover": baseline_turnover,
        "candidate_turnover": candidate_turnover,
        "baseline_exposure": baseline_exposure,
        "candidate_exposure": candidate_exposure,
        "baseline_net": _net_of_cost(baseline_gross, baseline_turnover, cost_bps),
        "candidate_net": _net_of_cost(candidate_gross, candidate_turnover, cost_bps),
    }


def _diagnostic_result(symbol: str, rows: list) -> Dict[str, Any]:
    return {
        "evidence_source": UNSEALED_EVIDENCE_SOURCE,
        "promotion_eligible": False,
        "symbol": symbol,
        "bars": rows,
    }


class WalkForwardSimulationRunner:
    """Adapt WalkForwardEvaluator to ExperimentManager's runner contract."""

    def __init__(
        self,
        *,
        db_path: Optional[Path] = None,
        symbol: str = "EURUSD",
        evaluator_factory: Callable[..., Any] = WalkForwardEvaluator,
    ) -> None:
        self.db_path = db_path
        self.symbol = symbol
        self.evaluator_factory = evaluator_factory

    async def __call__(self, domain: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        evaluator = self.evaluator_factory(**parameters) if parameters else self.evaluator_factory()
        result = evaluator.run(**({"db_path": self.db_path, "symbol": self.symbol} if self.db_path else {"symbol": self.symbol}))
        if inspect.isawaitable(result):
            result = await result
        train = result["train"]
        test = result["test"]
        return {
            "score": float(test.total_return),
            "total_return": float(test.total_return),
            "max_drawdown": float(test.max_drawdown),
            "win_rate": float(test.win_rate),
            "oos_score": float(test.total_return),
            "train_score": float(train.total_return),
            "ece_raw": float(test.ece_raw),
            "ece_calibrated": float(test.ece_calibrated),
            "evidence_source": "chronological_walk_forward",
            "promotion_eligible": False,
            "provenance": {
                "symbol": self.symbol,
                "db_path": str(self.db_path) if self.db_path else "default",
                "train_split": "chronological",
                "test_split": "chronological_oos",
            },
        }


class PairedStrategyReplay:
    """Diagnostic-only paired replay with explicit costs and exposure."""

    def __init__(self, cost_bps: float = 5.0) -> None:
        if cost_bps < 0:
            raise ValueError("cost_bps must be non-negative")
        self.cost_bps = float(cost_bps)

    def run(
        self,
        frame: Any,
        *,
        symbol: str,
        baseline_lookback: int,
        candidate_lookback: int,
    ) -> Dict[str, Any]:
        if baseline_lookback < 2 or candidate_lookback < 2:
            raise ValueError("lookbacks must be at least 2")
        rows = []
        closes = [float(value) for value in frame["close"]]
        timestamps = list(frame["timestamp"]) if "timestamp" in frame else list(range(len(closes)))
        previous_baseline = 0.0
        previous_candidate = 0.0
        for index in range(1, len(closes)):
            ret = closes[index] / closes[index - 1] - 1.0
            baseline_window = closes[max(0, index - baseline_lookback):index]
            candidate_window = closes[max(0, index - candidate_lookback):index]
            baseline_direction = 1.0 if closes[index - 1] >= sum(baseline_window) / len(baseline_window) else -1.0
            candidate_direction = 1.0 if closes[index - 1] >= sum(candidate_window) / len(candidate_window) else -1.0
            baseline_turnover = abs(baseline_direction - previous_baseline)
            candidate_turnover = abs(candidate_direction - previous_candidate)
            rows.append(_paired_bar(
                symbol, timestamps[index], self.cost_bps,
                baseline_gross=baseline_direction * ret,
                candidate_gross=candidate_direction * ret,
                baseline_turnover=baseline_turnover,
                candidate_turnover=candidate_turnover,
                baseline_exposure=0.01,
                candidate_exposure=0.01,
            ))
            previous_baseline, previous_candidate = baseline_direction, candidate_direction
        return _diagnostic_result(symbol, rows)


@dataclass(frozen=True)
class BarCostModel:
    """Per-bar cost/session structure for paired replays.

    Algory-changelog analogs made explicit and serializable (the model is
    built inside the sandboxed verifier, so it must be plain data):

    - ``per_bar_bps``: absolute cost override per bar index — the
      "spread measured per hour" case where the cost is not a scalar.
    - ``blocked_bars``: session-break / market-closed bars where the
      strategy may not change position (turnover is forced to zero and
      the held position simply rides through the break).
    - ``rollover_bars`` + ``rollover_mult``: rollover-hour spread
      widening applied to that bar's turnover cost.

    Every emitted ``cost_bps`` must still fall inside the contract's
    ``[min_cost_bps, max_cost_bps]`` band — widening models belong inside
    the band the operator contracted for.
    """

    base_bps: float
    per_bar_bps: Tuple[float, ...] = ()
    blocked_bars: Tuple[int, ...] = ()
    rollover_bars: Tuple[int, ...] = ()
    rollover_mult: float = 1.0


class PairedFamilyReplay:
    """Paired incumbent/candidate replay for any allow-listed adapter.

    Emits the per-bar rows consumed by
    ``recursive_self_improvement.evaluation.EvaluationEngine.evaluate_verified``
    and ``multi_objective``. Signals are computed only from strictly-prior
    bars; fills use the next bar's open->close. Turnover charges only when
    the position changes. Costs are explicit and identical for both sides.
    """

    def __init__(self, adapter: Any, cost_bps: float, fraction: float = 0.01,
                 cost_model: Optional[BarCostModel] = None) -> None:
        if not math.isfinite(cost_bps) or cost_bps <= 0 or not 0 < fraction <= 1:
            raise ValueError("positive cost and bounded exposure required")
        if cost_model is not None:
            if not math.isfinite(cost_model.base_bps) or cost_model.base_bps <= 0:
                raise ValueError("cost model base_bps must be positive")
            if not math.isfinite(cost_model.rollover_mult) or cost_model.rollover_mult < 1.0:
                raise ValueError("rollover_mult must be >= 1.0")
        self.adapter = adapter
        self.cost_bps = float(cost_bps)
        self.fraction = float(fraction)
        self.cost_model = cost_model
        self._blocked = frozenset(cost_model.blocked_bars) if cost_model else frozenset()
        self._rollover = frozenset(cost_model.rollover_bars) if cost_model else frozenset()

    def _bar_cost(self, i: int) -> float:
        m = self.cost_model
        if m is None:
            return self.cost_bps
        cost = m.per_bar_bps[i] if i < len(m.per_bar_bps) else m.base_bps
        if i in self._rollover:
            cost *= m.rollover_mult
        return float(cost)

    def _groups(self, frames: Dict[str, Any]) -> Dict[str, Any]:
        if self.adapter.pairs:
            from trading_bot.recursive_self_improvement.candidate_adapters import make_pairs

            groups: Dict[str, Any] = {}
            symbols = tuple(sorted(frames))
            ts_sets = {s: tuple(frames[s]["timestamp"]) for s in symbols}
            if len(set(ts_sets.values())) != 1:
                raise ValueError("instrument timelines are not aligned")
            for a, b in make_pairs(symbols):
                groups[f"{a}/{b}"] = (frames[a], frames[b])
            return groups
        return {s: frames[s] for s in sorted(frames)}

    def _signal_dir(self, strategy: Any, hist: Any) -> Tuple[Optional[int], float]:
        if self.adapter.pairs:
            sig = strategy.generate_signal(hist[0], hist[1])
            hedge = getattr(strategy, "hedge_ratio", None)
            return self.adapter.direction_of(sig), float(hedge if hedge else 1.0)
        sig = strategy.generate_signal(hist)
        return self.adapter.direction_of(sig), 1.0

    def run(
        self,
        frames: Dict[str, Any],
        *,
        baseline_params: Dict[str, Any],
        candidate_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        min_hist = self.adapter.min_history(
            {**baseline_params, **candidate_params}
        )
        rows: List[Dict[str, Any]] = []
        for label, group in self._groups(frames).items():
            primary = group[0] if self.adapter.pairs else group
            n = len(primary)
            if self.cost_model is not None and self.cost_model.per_bar_bps \
                    and len(self.cost_model.per_bar_bps) != n:
                raise ValueError(
                    "per_bar_bps length must match the frame's bar count")
            if self._blocked or self._rollover:
                bad = [i for i in (*self._blocked, *self._rollover)
                       if i < 0 or i >= n]
                if bad:
                    raise ValueError(f"cost-model bar index out of range: {bad[0]}")
            timestamps = list(primary["timestamp"]) if "timestamp" in primary else list(range(n))
            strats = {
                "baseline": self.adapter.build(baseline_params),
                "candidate": self.adapter.build(candidate_params),
            }
            prev: Dict[str, int] = {"baseline": 0, "candidate": 0}
            for i in range(1, n):
                if self.adapter.pairs:
                    hist = (group[0].iloc[:i], group[1].iloc[:i])
                    ra = float(group[0]["close"].iloc[i]) / float(group[0]["open"].iloc[i]) - 1.0
                    rb = float(group[1]["close"].iloc[i]) / float(group[1]["open"].iloc[i]) - 1.0
                else:
                    hist = group.iloc[:i]
                    ra = float(group["close"].iloc[i]) / float(group["open"].iloc[i]) - 1.0
                    rb = 0.0
                bar_cost = self._bar_cost(i)
                row: Dict[str, Any] = {
                    "symbol": label,
                    "timestamp": timestamps[i],
                    "cost_bps": bar_cost,
                }
                for name, strat in strats.items():
                    hedge = 1.0
                    position = prev[name]
                    # Position semantics: entry/exit actions set a target
                    # position; "hold"/no-directive preserves the position
                    # rather than behaving like a close. Session-break bars
                    # are no-trade windows: the directive is ignored so the
                    # held position rides through with zero turnover.
                    if i >= min_hist and i not in self._blocked:
                        directive, hedge = self._signal_dir(strat, hist)
                        if directive is not None:
                            position = directive
                    turnover = abs(position - prev[name]) * self.fraction
                    prev[name] = position
                    exposure = self.fraction * abs(position)
                    leg = (ra - hedge * rb) if self.adapter.pairs else ra
                    gross = position * leg * exposure
                    net = gross - turnover * bar_cost / 10000.0
                    row[f"{name}_gross"] = gross
                    row[f"{name}_turnover"] = turnover
                    row[f"{name}_exposure"] = exposure
                    row[f"{name}_net"] = net
                    row[f"{name}_direction"] = position
                rows.append(row)
        return {
            "promotion_eligible": False,
            "evidence_source": "unsealed_paired_family_replay",
            "cost_bps": self.cost_bps,
            "bars": rows,
        }


class BoundedMeanReversionReplay:
    def __init__(self, cost_bps: float, fraction: float = 0.01):
        if not math.isfinite(cost_bps) or cost_bps <= 0 or not 0 < fraction <= 1:
            raise ValueError("positive observed or conservative cost and bounded exposure required")
        self.cost_bps = cost_bps
        self.fraction = fraction

    def run(self, df: Any, *, symbol: str, baseline_lookback: int,
            candidate_lookback: int) -> Dict[str, Any]:
        from trading_bot.strategies.institutional_strategies import MeanReversionStrategy
        # Lazy: the rsi package __init__ imports engine_v2, which imports this
        # module — a top-level import would create a cycle.
        from trading_bot.recursive_self_improvement.candidate_adapters import get_adapter

        if (not symbol or not 2 <= baseline_lookback <= 50 or not 2 <= candidate_lookback <= 50 or
                baseline_lookback == candidate_lookback or len(df) < 3):
            raise ValueError("invalid or unchanged bounded strategy parameter")
        direction_of = get_adapter("mean_reversion").direction_of
        baseline = MeanReversionStrategy(lookback=baseline_lookback, entry_threshold=1.0)
        candidate = MeanReversionStrategy(lookback=candidate_lookback, entry_threshold=1.0)
        prev = {"baseline": 0, "candidate": 0}
        rows = []
        for i in range(1, len(df)):
            current = df.iloc[i]
            price_open, price_close = float(current["open"]), float(current["close"])
            if not all(math.isfinite(v) and v > 0 for v in (price_open, price_close)):
                raise ValueError("invalid executable OHLCV price")
            history = df.iloc[:i]
            row: Dict[str, Any] = {"symbol": symbol, "timestamp": current["timestamp"],
                                   "cost_bps": self.cost_bps}
            for name, strategy in (("baseline", baseline), ("candidate", candidate)):
                position = prev[name]
                if i >= strategy.lookback:
                    # Same position semantics as PairedFamilyReplay: "hold"
                    # preserves the position; "close" exits to flat.
                    directive = direction_of(strategy.generate_signal(history))
                    if directive is not None:
                        position = directive
                row[f"{name}_turnover"] = abs(position - prev[name]) * self.fraction
                prev[name] = position
                row[f"{name}_exposure"] = self.fraction * abs(position)
                row[f"{name}_gross"] = position * (price_close / price_open - 1) * row[f"{name}_exposure"]
            rows.append(_paired_bar(
                symbol, row["timestamp"], self.cost_bps,
                baseline_gross=row["baseline_gross"], candidate_gross=row["candidate_gross"],
                baseline_turnover=row["baseline_turnover"], candidate_turnover=row["candidate_turnover"],
                baseline_exposure=row["baseline_exposure"], candidate_exposure=row["candidate_exposure"],
            ))
        return _diagnostic_result(symbol, rows)

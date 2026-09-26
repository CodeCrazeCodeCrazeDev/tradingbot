"""Replay-backed simulation runner for recursive improvement experiments."""

from __future__ import annotations

import inspect
import math
from pathlib import Path
from typing import Any, Callable, Dict, Optional

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


class BoundedMeanReversionReplay:
    def __init__(self, cost_bps: float, fraction: float = 0.01):
        if not math.isfinite(cost_bps) or cost_bps <= 0 or not 0 < fraction <= 1:
            raise ValueError("positive observed or conservative cost and bounded exposure required")
        self.cost_bps = cost_bps
        self.fraction = fraction

    def run(self, df: Any, *, symbol: str, baseline_lookback: int,
            candidate_lookback: int) -> Dict[str, Any]:
        from trading_bot.strategies.institutional_strategies import MeanReversionStrategy

        if (not symbol or not 2 <= baseline_lookback <= 50 or not 2 <= candidate_lookback <= 50 or
                baseline_lookback == candidate_lookback or len(df) < 3):
            raise ValueError("invalid or unchanged bounded strategy parameter")
        baseline = MeanReversionStrategy(lookback=baseline_lookback, entry_threshold=1.0)
        candidate = MeanReversionStrategy(lookback=candidate_lookback, entry_threshold=1.0)
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
                direction = 0
                if i >= strategy.lookback:
                    action = strategy.generate_signal(history)["action"]
                    direction = {"buy": 1, "sell": -1}.get(action, 0)
                row[f"{name}_exposure"] = self.fraction if direction else 0.0
                row[f"{name}_turnover"] = row[f"{name}_exposure"] * 2
                row[f"{name}_gross"] = direction * (price_close / price_open - 1) * row[f"{name}_exposure"]
            rows.append(_paired_bar(
                symbol, row["timestamp"], self.cost_bps,
                baseline_gross=row["baseline_gross"], candidate_gross=row["candidate_gross"],
                baseline_turnover=row["baseline_turnover"], candidate_turnover=row["candidate_turnover"],
                baseline_exposure=row["baseline_exposure"], candidate_exposure=row["candidate_exposure"],
            ))
        return _diagnostic_result(symbol, rows)

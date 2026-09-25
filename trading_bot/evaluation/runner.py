"""Replay-backed simulation runner for recursive improvement experiments."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .walk_forward import WalkForwardEvaluator


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
            "sharpe_ratio": float(test.total_return),
            "total_return": float(test.total_return),
            "max_drawdown": float(test.max_drawdown),
            "win_rate": float(test.win_rate),
            "oos_score": float(test.total_return),
            "train_score": float(train.total_return),
            "ece_raw": float(test.ece_raw),
            "ece_calibrated": float(test.ece_calibrated),
            "evidence_source": "chronological_walk_forward",
            "promotion_eligible": True,
            "provenance": {
                "symbol": self.symbol,
                "db_path": str(self.db_path) if self.db_path else "default",
                "train_split": "chronological",
                "test_split": "chronological_oos",
            },
        }

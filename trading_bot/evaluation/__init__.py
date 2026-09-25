"""Evaluation subsystem — grounded out-of-sample measurement.

Owns the walk-forward harness that answers "does the brain actually work"
on held-out real data rather than synthetic or in-sample evidence.
"""

from .walk_forward import WalkForwardEvaluator, EvaluationReport, TradeRecord
from .runner import WalkForwardSimulationRunner

__all__ = [
    "WalkForwardSimulationRunner",
    "WalkForwardEvaluator",
    "EvaluationReport",
    "TradeRecord",
]

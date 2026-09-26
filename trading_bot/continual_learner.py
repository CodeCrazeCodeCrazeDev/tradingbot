"""Continual Learner - flat-path compatibility shim.

continual learning loop
"""

import warnings as _warnings
_warnings.warn(
    "trading_bot.continual_learner is deprecated: not on the canonical runtime path and carries no improvement authority; use trading_bot.recursive_self_improvement instead.",
    DeprecationWarning,
    stacklevel=2,
)

from typing import Any, Dict


def _noop(*a, **k):
    return None



class ContinualLearner:
    """Minimal reconstruction of the deleted ``ContinualLearner`` (merge loss)."""

    def __init__(self, *args: Any, **kwargs: Any):
        self.config = kwargs.get("config", dict(kwargs))
        self.running = False
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "running": self.running}

    def to_dict(self) -> Dict[str, Any]:
        return self.get_status()


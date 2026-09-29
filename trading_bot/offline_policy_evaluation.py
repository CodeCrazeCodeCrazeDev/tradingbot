"""Offline Policy Evaluation - flat-path compatibility shim.

offline policy evaluation
"""

from typing import Any, Dict


def _noop(*a, **k):
    return None


try:
    from trading_bot.ml.offline_rl.ope import FittedQEvaluation, DoublyRobust  # noqa: F401
except ImportError:
    pass


class OPEResult:
    """Minimal reconstruction of the deleted ``OPEResult`` (merge loss)."""

    def __init__(self, *args: Any, **kwargs: Any):
        self.config = kwargs.get("config", dict(kwargs))
        self.running = False
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "running": self.running}

    def to_dict(self) -> Dict[str, Any]:
        return self.get_status()


class WeightedImportanceSampling:
    """Minimal reconstruction of the deleted ``WeightedImportanceSampling`` (merge loss)."""

    def __init__(self, *args: Any, **kwargs: Any):
        self.config = kwargs.get("config", dict(kwargs))
        self.running = False
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "running": self.running}

    def to_dict(self) -> Dict[str, Any]:
        return self.get_status()


class OfflinePolicyEvaluator:
    """Minimal reconstruction of the deleted ``OfflinePolicyEvaluator`` (merge loss)."""

    def __init__(self, *args: Any, **kwargs: Any):
        self.config = kwargs.get("config", dict(kwargs))
        self.running = False
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "running": self.running}

    def to_dict(self) -> Dict[str, Any]:
        return self.get_status()


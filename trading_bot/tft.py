"""Tft - flat-path compatibility shim.

TFT alias module
"""

from typing import Any, Dict


def _noop(*a, **k):
    return None


try:
    from trading_bot.skills.ai_ml_enhancements.temporal_fusion import TemporalFusionTransformer  # noqa: F401
except ImportError:
    pass


class Tft:
    """Minimal reconstruction of the deleted ``Tft`` (merge loss)."""

    def __init__(self, *args: Any, **kwargs: Any):
        self.config = kwargs.get("config", dict(kwargs))
        self.running = False
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "running": self.running}

    def to_dict(self) -> Dict[str, Any]:
        return self.get_status()

try:
    Tft = TemporalFusionTransformer  # noqa: F821
except NameError:
    pass


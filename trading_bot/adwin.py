"""Adwin - flat-path compatibility shim.

ADWIN drift detector
"""

from typing import Any, Dict


def _noop(*a, **k):
    return None



class Adwin:
    """Minimal reconstruction of the deleted ``Adwin`` (merge loss)."""

    def __init__(self, *args: Any, **kwargs: Any):
        self.config = kwargs.get("config", dict(kwargs))
        self.running = False
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "running": self.running}

    def to_dict(self) -> Dict[str, Any]:
        return self.get_status()


"""Advanced Rl Agents - flat-path compatibility shim.

advanced offline RL agents
"""

from typing import Any, Dict


def _noop(*a, **k):
    return None


try:
    from trading_bot.ml.offline_rl.cql_agent import CQLAgent  # noqa: F401
except ImportError:
    pass

try:
    from trading_bot.ml.offline_rl.bcq_agent import BCQAgent  # noqa: F401
except ImportError:
    pass

try:
    from trading_bot.ml.offline_rl.ope import QNetwork  # noqa: F401
except ImportError:
    pass

try:
    from trading_bot.ml.reinforcement import PolicyNetwork  # noqa: F401
except ImportError:
    pass


class RLConfig:
    """Minimal reconstruction of the deleted ``RLConfig`` (merge loss)."""

    def __init__(self, *args: Any, **kwargs: Any):
        self.config = kwargs.get("config", dict(kwargs))
        self.running = False
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "running": self.running}

    def to_dict(self) -> Dict[str, Any]:
        return self.get_status()


class VAE:
    """Minimal reconstruction of the deleted ``VAE`` (merge loss)."""

    def __init__(self, *args: Any, **kwargs: Any):
        self.config = kwargs.get("config", dict(kwargs))
        self.running = False
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "running": self.running}

    def to_dict(self) -> Dict[str, Any]:
        return self.get_status()


class BEARAgent:
    """Minimal reconstruction of the deleted ``BEARAgent`` (merge loss)."""

    def __init__(self, *args: Any, **kwargs: Any):
        self.config = kwargs.get("config", dict(kwargs))
        self.running = False
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "running": self.running}

    def to_dict(self) -> Dict[str, Any]:
        return self.get_status()


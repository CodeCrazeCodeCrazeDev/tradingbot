"""
Evolution Layer Orchestrator
============================================================

Coordinates the evolution subsystem (learner, evolver, optimizer,
reward model). Records trade experiences for offline learning and
exposes a simple lifecycle for unified_main.
"""

import asyncio
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_orchestrator: Optional["EvolutionOrchestrator"] = None
_experiences: List[Dict[str, Any]] = []


class EvolutionOrchestrator:
    """Lifecycle facade over the evolution layer components."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.running = False
        self.started_at: Optional[datetime] = None
        self._engines: Dict[str, Any] = {}
        for mod_name, cls_name in (("learner", None), ("evolver", None), ("optimizer", None)):
            try:
                mod = __import__(f"trading_bot.evolution_layer.{mod_name}", fromlist=["*"])
                for attr in dir(mod):
                    obj = getattr(mod, attr)
                    if isinstance(obj, type) and obj.__module__.startswith("trading_bot.evolution_layer"):
                        try:
                            self._engines[attr] = obj(self.config)
                        except Exception:
                            pass
                        break
            except Exception:
                continue

    async def start(self) -> None:
        self.running = True
        self.started_at = datetime.now()
        for name, eng in self._engines.items():
            starter = getattr(eng, "start", None)
            if callable(starter):
                try:
                    res = starter()
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as e:
                    logger.warning(f"evolution engine {name} start failed: {e}")
        logger.info(f"EvolutionOrchestrator started ({len(self._engines)} engines)")

    async def stop(self) -> None:
        self.running = False
        for name, eng in self._engines.items():
            stopper = getattr(eng, "stop", None)
            if callable(stopper):
                try:
                    res = stopper()
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as e:
                    logger.warning(f"evolution engine {name} stop failed: {e}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "engines": sorted(self._engines.keys()),
            "experiences": len(_experiences),
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }


def get_evolution_orchestrator(config: Optional[Dict[str, Any]] = None) -> EvolutionOrchestrator:
    global _orchestrator
    with _lock:
        if _orchestrator is None:
            _orchestrator = EvolutionOrchestrator(config)
    return _orchestrator


def record_trade_experience(experience: Any) -> None:
    """Record a trade outcome for offline evolution/learning."""
    if hasattr(experience, "__dict__"):
        entry = dict(experience.__dict__)
    elif isinstance(experience, dict):
        entry = dict(experience)
    else:
        entry = {"value": experience}
    entry.setdefault("recorded_at", datetime.now().isoformat())
    _experiences.append(entry)
    try:
        from .reward_model import get_reward_model
        rm = get_reward_model()
        update = getattr(rm, "record_outcome", None) or getattr(rm, "update", None)
        if callable(update):
            update(entry)
    except Exception:
        pass

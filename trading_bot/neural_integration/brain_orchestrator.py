"""
Neural Brain Orchestrator
============================================================

Lightweight "neural hub" that lets modules register as neurons
and exchange stimulation signals. Global singleton accessor plus
functional helpers mirror the original public API.
"""

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModuleNeuron:
    """A registered module participating in the neural hub."""
    name: str
    handler: Optional[Callable] = None
    weight: float = 1.0
    activations: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class NeuralBrainOrchestrator:
    """Routes stimulation signals between registered module neurons."""

    def __init__(self):
        self._neurons: Dict[str, ModuleNeuron] = {}
        self._signals: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def register_module(self, name: str, handler: Optional[Callable] = None,
                        weight: float = 1.0, **metadata) -> ModuleNeuron:
        neuron = ModuleNeuron(name=name, handler=handler, weight=weight,
                              metadata=dict(metadata))
        with self._lock:
            self._neurons[name] = neuron
        logger.debug(f"NeuralBrain: registered neuron {name}")
        return neuron

    async def stimulate(self, name: str, signal: Any = None) -> Any:
        neuron = self._neurons.get(name)
        if neuron is None:
            return None
        neuron.activations += 1
        self._signals.append({"target": name, "signal": signal})
        if callable(neuron.handler):
            res = neuron.handler(signal)
            if asyncio.iscoroutine(res):
                return await res
            return res
        return {"stimulated": name}

    async def query(self, name: str, payload: Any = None) -> Any:
        return await self.stimulate(name, payload)

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "neurons": len(self._neurons),
                "signals_routed": len(self._signals),
                "activations": {n: nr.activations for n, nr in self._neurons.items()},
            }

    def focus(self, names: List[str]) -> List[str]:
        """Restrict attention to a subset of neurons (returns found names)."""
        return [n for n in names if n in self._neurons]


_orchestrator: Optional[NeuralBrainOrchestrator] = None


def get_neural_orchestrator() -> NeuralBrainOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = NeuralBrainOrchestrator()
    return _orchestrator


async def quick_start_neural_brain(modules: Optional[List[str]] = None) -> NeuralBrainOrchestrator:
    orch = get_neural_orchestrator()
    for name in modules or []:
        orch.register_module(name)
    return orch


async def stimulate(name: str, signal: Any = None) -> Any:
    return await get_neural_orchestrator().stimulate(name, signal)


async def query(name: str, payload: Any = None) -> Any:
    return await get_neural_orchestrator().query(name, payload)


def brain_stats() -> Dict[str, Any]:
    return get_neural_orchestrator().stats()


def focus(names: List[str]) -> List[str]:
    return get_neural_orchestrator().focus(names)

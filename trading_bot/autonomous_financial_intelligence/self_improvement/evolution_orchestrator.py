"""
Evolution Orchestrator
============================================================

Runs self-improvement evolution cycles for the
autonomous_financial_intelligence subsystem: evaluates candidate
changes against promotion gates and records cycle history.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EvolutionMetrics:
    """Outcome metrics for one evolution cycle."""
    candidates_evaluated: int = 0
    candidates_promoted: int = 0
    candidates_rejected: int = 0
    duration_seconds: float = 0.0
    notes: List[str] = field(default_factory=list)


@dataclass
class EvolutionCycle:
    """A single improvement cycle record."""
    cycle_id: str
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    metrics: EvolutionMetrics = field(default_factory=EvolutionMetrics)
    status: str = "pending"


class EvolutionOrchestrator:
    """Coordinates bounded self-improvement cycles."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._cycles: List[EvolutionCycle] = []
        self._gates: List[Any] = []
        self._counter = 0

    def register_gate(self, gate: Any) -> None:
        self._gates.append(gate)

    async def run_cycle(self, candidates: Optional[List[Any]] = None) -> EvolutionCycle:
        """Evaluate candidates through registered promotion gates."""
        self._counter += 1
        cycle = EvolutionCycle(cycle_id=f"evo_{self._counter}", status="running")
        self._cycles.append(cycle)
        start = datetime.now()
        for cand in candidates or []:
            cycle.metrics.candidates_evaluated += 1
            approved = True
            for gate in self._gates:
                fn = getattr(gate, "validate", None) or getattr(gate, "validate_improvement", None)
                if callable(fn):
                    try:
                        res = fn(cand)
                        ok = await res if asyncio.iscoroutine(res) else res
                        if ok is False:
                            approved = False
                            break
                    except Exception as e:
                        logger.warning(f"EvolutionOrchestrator: gate failed: {e}")
                        approved = False
                        break
            if approved:
                cycle.metrics.candidates_promoted += 1
            else:
                cycle.metrics.candidates_rejected += 1
        cycle.finished_at = datetime.now()
        cycle.metrics.duration_seconds = (cycle.finished_at - start).total_seconds()
        cycle.status = "completed"
        return cycle

    def history(self) -> List[EvolutionCycle]:
        return list(self._cycles)


import asyncio  # noqa: E402

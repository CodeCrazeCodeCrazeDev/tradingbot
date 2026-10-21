"""SRE advisory bridge — wires the Scientific Reasoning Engine into the
CSC as a subordinate advisory cognition service.

The SRE's 19-stage lifecycle is heavy (hypothesis generation can invoke
the verification swarm), so the adapter throttles: one full lifecycle
cycle per CYCLE_INTERVAL calls; other calls report the current tracked
hypothesis's lifecycle state. Output is advisory evidence — the SRE
carries no decision authority.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, Optional

logger = logging.getLogger(__name__)

_CYCLE_INTERVAL = 25     # one lifecycle per 25 advisory calls
_MAX_REGISTRY = 200      # bound the hypothesis registry


class SREAdvisoryService:
    """analyze()-compatible adapter over ScientificReasoningEngine."""

    capability_id = "sre_lifecycle"

    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self._calls = 0
        self._last_id: Optional[str] = None

    async def analyze(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        self._calls += 1
        if self._calls % _CYCLE_INTERVAL == 1 or self._last_id is None:
            try:
                # Bound the registry — the engine tracks lifecycles, it
                # does not grow without limit.
                if len(self.engine.registry) >= _MAX_REGISTRY:
                    oldest = next(iter(self.engine.registry))
                    self.engine.registry.pop(oldest, None)
                self._last_id = await self.engine.run_cycle(
                    dict(context or {}))
            except Exception as exc:  # noqa: BLE001
                logger.debug("SRE advisory cycle failed: %s", exc)
        return self._artifact()

    def _artifact(self) -> Dict[str, Any]:
        hyp = (self.engine.get_hypothesis(self._last_id)
               if self._last_id else None)
        if hyp is None:
            return {"capability_id": self.capability_id,
                    "advisory_only": True,
                    "evidence": {"status": "no_hypothesis"}}
        return {
            "capability_id": self.capability_id,
            "advisory_only": True,
            "evidence": {
                "status": "lifecycle",
                "hypothesis_id": hyp.id,
                "name": hyp.name,
                "state": hyp.state.name,
                "level": hyp.level.name,
                "posterior": round(float(hyp.posterior), 4),
                "uncertainty": round(float(hyp.uncertainty), 4),
                "credal_bounds": [round(float(hyp.p_lower), 4),
                                  round(float(hyp.p_upper), 4)],
                "validation_score": round(float(hyp.validation_score), 4),
                "calibration_error": round(float(hyp.calibration_error), 4),
                "expected_value": round(float(hyp.expected_value or 0.0), 6),
                "debate": hyp.boundary_conditions.get("debate"),
                "target_action": hyp.model_params.get("target_action"),
                "registry_size": len(self.engine.registry),
                "sre_cycles": self._calls // _CYCLE_INTERVAL,
            },
        }

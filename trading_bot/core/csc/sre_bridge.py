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
_RETRY_GAP = 5           # min advisory calls between cold-start retries


class SREAdvisoryService:
    """analyze()-compatible adapter over ScientificReasoningEngine.

    Neuro-symbolic gate: when the tracked hypothesis declares a
    target_action, the artifact also carries the NSR policy verdict —
    specialist review + gate decision + sealed flag. The SRE proposes;
    the policy layer classifies what the proposal is allowed to be."""

    capability_id = "sre_lifecycle"
    # The 19-stage lifecycle can invoke the verification swarm — far
    # heavier than a normal advisory call, so declare the ceiling
    # budget instead of timing out at the 5s default every cycle.
    timeout_s = 20.0

    def __init__(self, engine: Any, reasoner: Any = None) -> None:
        self.engine = engine
        self._calls = 0
        self._last_id: Optional[str] = None
        self._pending: Optional["asyncio.Task"] = None
        self._next_retry_call = 1
        if reasoner is None:
            try:
                from .neuro_symbolic import build as _nsr_build
                reasoner = _nsr_build()
            except Exception:  # noqa: BLE001
                reasoner = None
        self._reasoner = reasoner

    def _run_lifecycle_sync(self, context: Mapping[str, Any]) -> None:
        """Worker-thread entry: runs the lifecycle on a private event
        loop so a hang or deadlock inside it can never stall the main
        loop — worst case the task simply never completes and the
        service keeps reporting the last finished hypothesis."""
        import asyncio
        try:
            # Bound the registry — the engine tracks lifecycles, it
            # does not grow without limit.
            if len(self.engine.registry) >= _MAX_REGISTRY:
                oldest = next(iter(self.engine.registry))
                self.engine.registry.pop(oldest, None)
            self._last_id = asyncio.run(
                self.engine.run_cycle(dict(context or {})))
        except Exception as exc:  # noqa: BLE001
            logger.debug("SRE advisory cycle failed: %s", exc)

    async def analyze(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        import asyncio
        self._calls += 1
        # Steady state: one lifecycle per _CYCLE_INTERVAL calls. Cold
        # start (no hypothesis yet): retry on a shorter gap so a fast
        # failure doesn't spawn a worker thread on every advisory call.
        boundary = self._calls % _CYCLE_INTERVAL == 1
        cold_retry = (self._last_id is None
                      and self._calls >= self._next_retry_call)
        if (boundary or cold_retry) and (
                self._pending is None or self._pending.done()):
            # Stale-while-revalidate: the 19-stage lifecycle (which can
            # invoke the verification swarm) routinely outlasts the
            # advisory timeout ceiling, so run it in a worker thread and
            # report the last completed hypothesis instead of awaiting —
            # an advisory read must never stall the pipeline.
            self._pending = asyncio.ensure_future(asyncio.to_thread(
                self._run_lifecycle_sync, context))
            if self._last_id is None:
                self._next_retry_call = self._calls + _RETRY_GAP
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
                "policy": self._policy_verdict(hyp),
            },
        }

    def _policy_verdict(self, hyp: Any) -> Dict[str, Any]:
        """Route the hypothesis's declared action through the
        neuro-symbolic gate. Failure -> ungated marker, never a pass."""
        if self._reasoner is None:
            return {"status": "ungated", "reason": "nsr unavailable"}
        action = (hyp.model_params or {}).get("target_action")
        if not action:
            return {"status": "not_applicable"}
        try:
            d = self._reasoner.route({
                "id": f"sre:{hyp.id}", "action_class": action,
                "action": action,
                "channel": hyp.model_params.get(
                    "channel", "benchmark"),
                "untrusted": bool(
                    hyp.model_params.get("untrusted")),
                "vulnerability": bool(
                    hyp.model_params.get("vulnerability")),
                "sends_orders": action in ("live_exec", "order",
                                           "trade")})
            return {"status": "gated", "gate": d.gate,
                    "verdict": d.verdict, "sealed": d.sealed,
                    "action_class": d.action_class.value}
        except Exception as exc:  # noqa: BLE001
            return {"status": "ungated", "reason": str(exc)}

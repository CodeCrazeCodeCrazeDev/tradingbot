"""WorldModelPort adapter over the legacy scenario simulator.

Wraps ``v2_core.FutureScenarioSimulator`` (torch tensors in, typed scenario
stats out) so the simulator is consumable only as advisory evidence through
the canonical port — never as an execution or sizing authority.
"""

from __future__ import annotations

import inspect
from typing import Any, List, Mapping, Optional

from ..foundation.ports import WorldModelPort


class ScenarioWorldModelAdapter:
    """``WorldModelPort`` over ``FutureScenarioSimulator``.

    ``simulate`` accepts a mapping with a ``latent`` sequence (or tensor) and
    returns serializable scenario statistics — no torch objects escape the
    port boundary. ``intervene`` refuses: the legacy simulator has no
    intervention authority.
    """

    def __init__(self, simulator: Any, capability_id: str = "world_model.scenarios") -> None:
        if simulator is None:
            raise ValueError("simulator is required")
        self.simulator = simulator
        self.capability_id = capability_id

    async def simulate(
        self, state: Mapping[str, Any], horizon: int = 1
    ) -> Mapping[str, Any]:
        import torch

        latent = state.get("latent")
        if latent is None:
            return {"scenarios": [], "advisory_only": True,
                    "reason": "no latent state provided"}
        tensor = torch.as_tensor(latent, dtype=torch.float32)
        if tensor.dim() == 1:
            tensor = tensor.unsqueeze(0)
        result = self.simulator.simulate(tensor)
        if inspect.isawaitable(result):
            result = await result
        scenarios = []
        for scenario in result or []:
            trajectory = getattr(scenario, "trajectory", None)
            rewards = getattr(scenario, "rewards", None)
            scenarios.append({
                "name": getattr(scenario, "name", "unknown"),
                "confidence": float(getattr(scenario, "confidence", 0.0) or 0.0),
                "reasoning": getattr(scenario, "reasoning", ""),
                "trajectory_points": int(trajectory.shape[-2])
                if hasattr(trajectory, "shape") else 0,
                "expected_reward": float(rewards.mean())
                if hasattr(rewards, "mean") else 0.0,
            })
        return {"scenarios": scenarios, "advisory_only": True, "horizon": horizon}

    async def intervene(
        self, state: Mapping[str, Any], intervention: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        raise PermissionError(
            "ScenarioWorldModelAdapter is advisory-only: interventions are not "
            "permitted through the legacy scenario simulator"
        )

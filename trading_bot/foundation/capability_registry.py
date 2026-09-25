"""Canonical registry for non-authoritative AI and agent capabilities."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from .ports import AgentCapabilityPort


@dataclass(frozen=True)
class CapabilityRegistration:
    capability_id: str
    capability: AgentCapabilityPort
    domain: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    enabled: bool = True


class CapabilityRegistry:
    """Registry for advisory capabilities; no capital-moving API is exposed."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, CapabilityRegistration] = {}

    def register(
        self,
        capability: AgentCapabilityPort,
        *,
        capability_id: Optional[str] = None,
        domain: str = "intelligence",
        metadata: Optional[Mapping[str, Any]] = None,
        overwrite: bool = False,
    ) -> CapabilityRegistration:
        name = capability_id or getattr(capability, "capability_id", "")
        if not name:
            raise ValueError("Capabilities require a capability_id")
        if not callable(getattr(capability, "analyze", None)):
            raise TypeError("Capabilities must implement analyze()")
        if name in self._capabilities and not overwrite:
            raise ValueError(f"Capability '{name}' is already registered")
        registration = CapabilityRegistration(name, capability, domain, dict(metadata or {}))
        self._capabilities[name] = registration
        return registration

    def get(self, capability_id: str) -> CapabilityRegistration:
        return self._capabilities[capability_id]

    def list(self) -> List[CapabilityRegistration]:
        return list(self._capabilities.values())

    async def analyze(self, capability_id: str, context: Mapping[str, Any]) -> Mapping[str, Any]:
        registration = self.get(capability_id)
        if not registration.enabled:
            return {"capability_id": capability_id, "advisory_only": True, "disabled": True}
        result = registration.capability.analyze(context)
        if inspect.isawaitable(result):
            result = await result
        if not isinstance(result, Mapping):
            return {"capability_id": capability_id, "advisory_only": True, "evidence": result}
        return dict(result)

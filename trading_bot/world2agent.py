"""
World-to-agent bridge built on top of the local A2A transport.

The bridge stores the latest world-state snapshots and republishes them over the
shared agent bus so downstream coordinators can enrich tasks, approvals, and
decisions with consistent context.
"""

from __future__ import annotations

import copy
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from .a2a import A2AMessageBus


def _utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _coerce_payload(value: Any) -> Dict[str, Any]:
    """Convert supported objects into serializable dictionaries."""
    if isinstance(value, dict):
        return copy.deepcopy(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return copy.deepcopy(value.to_dict())
    return {"value": copy.deepcopy(value)}


@dataclass
class WorldStateSnapshot:
    """A published world-state payload for one or more agents."""

    context_id: str
    source: str
    world_state: Dict[str, Any]
    audience: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    context_type: str = "market"
    timestamp: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the snapshot into a dictionary."""
        return {
            "context_id": self.context_id,
            "source": self.source,
            "world_state": copy.deepcopy(self.world_state),
            "audience": list(self.audience),
            "tags": list(self.tags),
            "context_type": self.context_type,
            "timestamp": self.timestamp,
        }


class World2AgentBridge:
    """Shared bridge that publishes world context into the A2A message bus."""

    def __init__(self, a2a_bus: Optional[A2AMessageBus] = None):
        self.a2a_bus = a2a_bus or A2AMessageBus()
        self._snapshots: List[WorldStateSnapshot] = []
        self._lock = threading.RLock()

    def publish_world_state(
        self,
        source: str,
        world_state: Dict[str, Any],
        *,
        audience: Optional[Sequence[str]] = None,
        tags: Optional[Sequence[str]] = None,
        context_type: str = "market",
    ) -> WorldStateSnapshot:
        """Store and publish a world-state snapshot."""
        snapshot = WorldStateSnapshot(
            context_id=f"ctx-{uuid.uuid4().hex[:12]}",
            source=source,
            world_state=copy.deepcopy(world_state),
            audience=list(audience or []),
            tags=list(tags or []),
            context_type=context_type,
        )
        with self._lock:
            self._snapshots.append(snapshot)

        recipients = list(audience) if audience is not None else None
        self.a2a_bus.broadcast(
            sender=source,
            intent="world_state",
            payload=snapshot.to_dict(),
            recipients=recipients,
            channel="world2agent",
            metadata={
                "context_id": snapshot.context_id,
                "context_type": snapshot.context_type,
                "tags": list(snapshot.tags),
            },
        )
        return snapshot

    def publish_simulation_result(
        self,
        source: str,
        simulation_result: Any,
        *,
        audience: Optional[Sequence[str]] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> WorldStateSnapshot:
        """Publish a simulation result as a world-state snapshot."""
        return self.publish_world_state(
            source=source,
            world_state=_coerce_payload(simulation_result),
            audience=audience,
            tags=list(tags or []) + ["simulation"],
            context_type="simulation",
        )

    def get_latest_snapshot(
        self,
        *,
        source: Optional[str] = None,
        context_type: Optional[str] = None,
    ) -> Optional[WorldStateSnapshot]:
        """Return the newest snapshot, optionally filtered."""
        with self._lock:
            for snapshot in reversed(self._snapshots):
                if source is not None and snapshot.source != source:
                    continue
                if context_type is not None and snapshot.context_type != context_type:
                    continue
                return snapshot
        return None

    def build_agent_context(
        self,
        agent_id: str,
        base_payload: Optional[Dict[str, Any]] = None,
        *,
        source: Optional[str] = None,
        context_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enrich a payload with the latest known world snapshot for an agent.

        If no world snapshot exists yet, the original payload is returned.
        """
        payload = copy.deepcopy(base_payload or {})
        snapshot = self.get_latest_snapshot(source=source, context_type=context_type)
        if snapshot is None:
            payload.setdefault("target_agent", agent_id)
            return payload

        payload.setdefault("target_agent", agent_id)
        payload.setdefault("world_context_id", snapshot.context_id)
        payload.setdefault("world_context_source", snapshot.source)
        payload.setdefault("world_context", snapshot.to_dict())
        return payload

    def attach_world_context(
        self,
        agent_id: str,
        payload: Dict[str, Any],
        *,
        source: Optional[str] = None,
        context_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Alias for build_agent_context for call sites that prefer imperative naming."""
        return self.build_agent_context(
            agent_id=agent_id,
            base_payload=payload,
            source=source,
            context_type=context_type,
        )

    def snapshot_count(self) -> int:
        """Return how many snapshots have been published."""
        with self._lock:
            return len(self._snapshots)

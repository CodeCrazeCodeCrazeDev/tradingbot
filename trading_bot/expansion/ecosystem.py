"""Ecosystem health — the measurable version of 'a living AI ecosystem'.

A living ecosystem is not a vibe: it is a population of advisory nodes
with a measured lifecycle — nodes discovered into SHADOW, graduated to
ATTACHED on measured output, demoted to DORMANT when they go
degenerate, quarantined when probation fails. This report reads the
SelfWiringSupervisor's real node inventory and the engineered-model
pipeline's real candidate states; every number it emits was counted,
not imagined.
"""

from __future__ import annotations

from typing import Any, Dict


class EcosystemHealth:
    """Aggregates real lifecycle state from the CSC electorate."""

    def __init__(self, csc: Any) -> None:
        self.csc = csc

    def report(self) -> Dict[str, Any]:
        sup = getattr(self.csc, "_self_wiring", None)
        nodes = getattr(sup, "nodes", {}) if sup is not None else {}
        by_state: Dict[str, int] = {}
        emits = substantive = degenerate = 0
        for n in nodes.values():
            st = getattr(getattr(n, "state", ""), "value",
                         getattr(n, "state", "unknown"))
            by_state[st] = by_state.get(st, 0) + 1
            emits += getattr(n, "emits", 0) or 0
            substantive += getattr(n, "substantive", 0) or 0
            degenerate += getattr(n, "degenerate_streak", 0) or 0
        rewires = len(getattr(sup, "events", ()) or ()) \
            if sup is not None else 0
        engineered = getattr(self.csc, "_engineered_models", {}) or {}
        eng_by_status: Dict[str, int] = {}
        for c in engineered.values():
            st = getattr(c, "status", "unknown")
            eng_by_status[st] = eng_by_status.get(st, 0) + 1
        services = getattr(self.csc, "_advisory_services", ()) or ()
        total = max(sum(by_state.values()), 1)
        vitality = round(substantive / max(emits, 1), 4)
        return {
            "status": "active" if services or nodes else "empty",
            "advisory_services": len(services),
            "electorate_nodes": len(nodes),
            "nodes_by_state": by_state,
            "lifecycle_rewires": rewires,
            "emits_measured": emits,
            "substantive_share": vitality,
            "shadow_share": round(by_state.get("shadow", 0) / total, 4),
            "engineered_candidates": eng_by_status,
            "note": ("a population with a measured lifecycle: discover "
                     "-> shadow -> graduate/demote — the measurable "
                     "form of a living ecosystem"),
        }

    def advisory(self, ctx: Any = None) -> Dict[str, Any]:
        return self.report()

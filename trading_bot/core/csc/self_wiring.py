"""Self-wiring supervisor — the organism rewires its own advisory
electorate by measured evidence, never by assertion.

Nodes are advisory cognition services registered with the CSC. Each
node carries a lifecycle state:

- SHADOW: newly discovered or re-probed — emits, gets measured, casts
  no influence until it graduates.
- ATTACHED: full electorate member — its calls tilt branch ranking.
- DORMANT: demoted for sustained degenerate output — detached from the
  consult loop; periodically re-probed as SHADOW.
- QUARANTINED: failed shadow probation — detached until an operator or
  a new candidate version registers it again.

Rewiring is bounded to the advisory electorate. The authority chain —
CSC, risk, shield, governance, decision bus, execution service,
verification swarm, reliability tracker — is invariant and unreachable
from this module.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Wiring policy — all thresholds are measured-cycle counts, not scores.
DEMOTE_AFTER_DEGENERATE = 8      # consecutive degenerate emits -> DORMANT
SHADOW_GRADUATE_CYCLES = 10      # measured cycles before promotion possible
SHADOW_GRADUATE_SUBSTANTIVE = 0.4  # share of substantive emits required
SHADOW_FAIL_CYCLES = 20          # shadow probation expires -> QUARANTINED
DORMANT_PROBE_INTERVAL = 40      # cycles between dormant re-probes
REWIRE_INTERVAL = 10             # supervisor evaluates every N obs cycles
MAX_SHADOW = 8                   # bounded: probes never flood the loop
MAX_INVENTORY = 256

# Components the supervisor may NEVER touch — the authority chain is not
# part of the electorate it rewires.
INVARIANT_IDS = frozenset({
    "csc", "csc_v6", "risk", "risk_engine", "risk_service", "shield",
    "immutable_shield", "governance", "governance_gate", "decision_bus",
    "execution_service", "execution_planner", "verifier_swarm",
    "verification_swarm", "reliability_tracker", "world_model", "hms",
    "swarm_intelligence", "self_wiring",
})


class NodeState(str, Enum):
    SHADOW = "shadow"
    ATTACHED = "attached"
    DORMANT = "dormant"
    QUARANTINED = "quarantined"


@dataclass
class ServiceNode:
    """One advisory service in the organism's wiring inventory."""

    node_id: str
    state: NodeState = NodeState.SHADOW
    domain: str = "other"
    degenerate_streak: int = 0
    substantive_streak: int = 0
    emits: int = 0
    substantive: int = 0
    # Predictive tracking: directional emits scored against realized
    # next-cycle moves. Output presence alone must not promote a
    # node — 'substantive' counts garbage that emits confidently.
    dir_hits: int = 0
    dir_total: int = 0
    shadow_cycles: int = 0
    last_rewired_cycle: int = 0
    rewires: int = 0
    probe_backoff: int = 0       # extra cycles added per failed probe
    service: Any = field(default=None, repr=False, compare=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "state": self.state.value,
            "domain": self.domain,
            "degenerate_streak": self.degenerate_streak,
            "substantive_streak": self.substantive_streak,
            "emits": self.emits,
            "substantive": self.substantive,
            "dir_hits": self.dir_hits,
            "dir_total": self.dir_total,
            "shadow_cycles": self.shadow_cycles,
            "last_rewired_cycle": self.last_rewired_cycle,
            "rewires": self.rewires,
            "probe_backoff": self.probe_backoff,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ServiceNode":
        return cls(
            node_id=d["node_id"],
            state=NodeState(d.get("state", "shadow")),
            domain=d.get("domain", "other"),
            degenerate_streak=int(d.get("degenerate_streak", 0)),
            substantive_streak=int(d.get("substantive_streak", 0)),
            emits=int(d.get("emits", 0)),
            substantive=int(d.get("substantive", 0)),
            dir_hits=int(d.get("dir_hits", 0)),
            dir_total=int(d.get("dir_total", 0)),
            shadow_cycles=int(d.get("shadow_cycles", 0)),
            last_rewired_cycle=int(d.get("last_rewired_cycle", 0)),
            rewires=int(d.get("rewires", 0)),
            probe_backoff=int(d.get("probe_backoff", 0)))


@dataclass
class RewireEvent:
    """One wiring transition — emitted as a SELF_WIRE audit event."""

    kind: str          # demote / promote / discover / quarantine / probe
    node_id: str
    reason: str
    cycle: int
    from_state: str
    to_state: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind, "node_id": self.node_id,
            "reason": self.reason, "cycle": self.cycle,
            "from_state": self.from_state, "to_state": self.to_state,
        }


class SelfWiringSupervisor:
    """Bounded self-wiring for the CSC advisory electorate.

    Observes per-service emit quality each cycle; every REWIRE_INTERVAL
    cycles it applies measured transitions and returns RewireEvents the
    controller persists as audit events. The supervisor holds no
    execution, risk, or decision surface.
    """

    def __init__(
        self,
        rewire_interval: int = REWIRE_INTERVAL,
        max_shadow: int = MAX_SHADOW,
        demote_after: int = DEMOTE_AFTER_DEGENERATE,
        graduate_cycles: int = SHADOW_GRADUATE_CYCLES,
        graduate_substantive: float = SHADOW_GRADUATE_SUBSTANTIVE,
        fail_cycles: int = SHADOW_FAIL_CYCLES,
        probe_interval: int = DORMANT_PROBE_INTERVAL,
    ) -> None:
        self.rewire_interval = rewire_interval
        self.max_shadow = max_shadow
        self.demote_after = demote_after
        self.graduate_cycles = graduate_cycles
        self.graduate_substantive = graduate_substantive
        self.fail_cycles = fail_cycles
        self.probe_interval = probe_interval
        self.nodes: Dict[str, ServiceNode] = {}
        self.events: List[RewireEvent] = []
        self._persistence_path: Optional[str] = None

    # -- inventory ------------------------------------------------------

    def register(
        self, node_id: str, service: Any = None,
        state: NodeState = NodeState.ATTACHED,
        domain: str = "other",
    ) -> Optional[ServiceNode]:
        node_id = str(node_id)
        if node_id in INVARIANT_IDS:
            return None
        node = self.nodes.get(node_id)
        if node is None:
            if len(self.nodes) >= MAX_INVENTORY:
                return None
            node = ServiceNode(node_id=node_id, state=state, domain=domain)
            self.nodes[node_id] = node
        else:
            node.state = state
        if service is not None:
            node.service = service
        return node

    def discover(
        self, node_id: str, service: Any = None,
        domain: str = "other", cycle: int = 0,
    ) -> Optional[RewireEvent]:
        """Self-discovery: a service the organism has never seen enters
        SHADOW — it emits and is measured before it earns influence."""
        if str(node_id) in self.nodes:
            return None
        if self._shadow_count() >= self.max_shadow:
            return None
        node = self.register(
            node_id, service, state=NodeState.SHADOW, domain=domain)
        if node is None:
            return None
        ev = RewireEvent("discover", str(node_id),
                         "new advisory service entered shadow",
                         cycle, "none", NodeState.SHADOW.value)
        self.events.append(ev)
        return ev

    def _shadow_count(self) -> int:
        return sum(1 for n in self.nodes.values()
                   if n.state == NodeState.SHADOW)

    def shadow_ids(self) -> set:
        return {n.node_id for n in self.nodes.values()
                if n.state == NodeState.SHADOW}

    def invariant_violation(self, node_id: str) -> bool:
        return str(node_id) in INVARIANT_IDS

    # -- observation ----------------------------------------------------

    def observe(self, node_id: str, status: str, cycle: int = 0) -> None:
        """Per-cycle emit-quality observation: directional/substantive
        feeds the substantive streak; degenerate resets it."""
        node = self.nodes.get(str(node_id))
        if node is None or node.state in (
                NodeState.DORMANT, NodeState.QUARANTINED):
            return
        node.emits += 1
        if status == "degenerate":
            node.degenerate_streak += 1
            node.substantive_streak = 0
        else:
            node.degenerate_streak = 0
            node.substantive_streak += 1
            node.substantive += 1
        if node.state == NodeState.SHADOW:
            node.shadow_cycles += 1

    def observe_outcome(self, node_id: str, hit: bool) -> None:
        """Record whether a node's directional emit was correct."""
        node = self.nodes.get(str(node_id))
        if node is None:
            return
        node.dir_total += 1
        if hit:
            node.dir_hits += 1

    def _predictive_ok(self, node: ServiceNode) -> bool:
        """Promotion needs measured predictive value, not just
        emit presence. No directional calls yet -> can't block on it
        (many advisors legitimately emit non-directional evidence);
        enough calls and >=55% correct -> qualified."""
        if node.dir_total < 10:
            return True
        return node.dir_hits / node.dir_total >= 0.55

    # -- evaluation -----------------------------------------------------

    def reevaluate(self, cycle: int) -> List[RewireEvent]:
        """Apply measured wiring transitions; returns the new events."""
        new_events: List[RewireEvent] = []
        for node in list(self.nodes.values()):
            if node.state == NodeState.ATTACHED:
                if node.degenerate_streak >= self.demote_after:
                    ev = self._transition(
                        node, NodeState.DORMANT, "demote", cycle,
                        f"{node.degenerate_streak} consecutive "
                        f"degenerate emits")
                    new_events.append(ev)
            elif node.state == NodeState.SHADOW:
                share = (node.substantive / max(1, node.emits))
                if (node.shadow_cycles >= self.graduate_cycles
                        and share >= self.graduate_substantive
                        and self._predictive_ok(node)):
                    ev = self._transition(
                        node, NodeState.ATTACHED, "promote", cycle,
                        f"graduated shadow: {node.emits} emits, "
                        f"{share:.0%} substantive")
                    new_events.append(ev)
                elif node.shadow_cycles >= self.fail_cycles:
                    ev = self._transition(
                        node, NodeState.QUARANTINED, "quarantine", cycle,
                        f"shadow probation expired: {share:.0%} "
                        f"substantive over {node.shadow_cycles} cycles")
                    new_events.append(ev)
            elif node.state == NodeState.DORMANT:
                due = (self.probe_interval + node.probe_backoff
                       + node.last_rewired_cycle)
                if cycle >= due and self._shadow_count() < self.max_shadow:
                    ev = self._transition(
                        node, NodeState.SHADOW, "probe", cycle,
                        f"dormant re-probe after "
                        f"{cycle - node.last_rewired_cycle} cycles")
                    node.shadow_cycles = 0
                    node.emits = 0
                    node.substantive = 0
                    new_events.append(ev)
        self.events.extend(new_events)
        if new_events:
            self._persist()
        return new_events

    def _transition(
        self, node: ServiceNode, to_state: NodeState, kind: str,
        cycle: int, reason: str,
    ) -> RewireEvent:
        ev = RewireEvent(kind, node.node_id, reason, cycle,
                         node.state.value, to_state.value)
        node.state = to_state
        node.last_rewired_cycle = cycle
        node.rewires += 1
        if kind == "quarantine":
            node.probe_backoff += self.probe_interval
        elif kind == "probe":
            pass
        elif kind == "demote":
            node.probe_backoff += self.probe_interval // 2
        return ev

    # -- transparency ---------------------------------------------------

    def report(self) -> Dict[str, Any]:
        by_state: Dict[str, int] = {}
        for n in self.nodes.values():
            by_state[n.state.value] = by_state.get(n.state.value, 0) + 1
        return {
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "by_state": by_state,
            "events_total": len(self.events),
            "recent_events": [e.to_dict() for e in self.events[-10:]],
        }

    # -- persistence ----------------------------------------------------

    def set_persistence(self, path: str) -> None:
        self._persistence_path = path
        loaded = self.load(path)
        if loaded.nodes:
            # Restore measured state; live service objects are re-registered
            # by configure_cognition as the runtime re-attaches them.
            self.nodes = loaded.nodes
            self.events = loaded.events

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "events": [e.to_dict() for e in self.events[-100:]],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SelfWiringSupervisor":
        sup = cls()
        for nid, nd in (d.get("nodes") or {}).items():
            sup.nodes[nid] = ServiceNode.from_dict(nd)
        for ed in (d.get("events") or []):
            sup.events.append(RewireEvent(
                ed["kind"], ed["node_id"], ed.get("reason", ""),
                int(ed.get("cycle", 0)), ed.get("from_state", ""),
                ed.get("to_state", "")))
        return sup

    def _persist(self) -> None:
        if not self._persistence_path:
            return
        try:
            directory = os.path.dirname(self._persistence_path) or "."
            os.makedirs(directory, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self.to_dict(), fh)
            os.replace(tmp, self._persistence_path)
        except OSError as exc:
            logger.warning("self-wiring persist failed: %s", exc)

    @classmethod
    def load(cls, path: str) -> "SelfWiringSupervisor":
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return cls.from_dict(json.load(fh))
        except (OSError, ValueError, KeyError, TypeError,
                AttributeError):
            # valid JSON with a malformed schema is as unsafe to
            # trust as missing state — fail to a fresh base.
            return cls()

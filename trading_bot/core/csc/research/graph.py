"""Cumulative scientific knowledge graph.

Not a pile of documents — typed nodes and relationships so the system
reasons cumulatively instead of rediscovering the same idea:

    Question ──> Claim ──> Evidence ──> Experiment ──> Result
                    │                        │
                    └<── Contradiction ──────┘
                    └──> Replication / Boundary condition

Edges: supports | contradicts | replicates | extends | depends_on |
invalidates | generalizes | specializes | fails_under | derived_from.

Persistence goes through a sink callback (the controller's audit writer):
every node/edge lands in the durable event log, and the graph can be
rebuilt from it after restart.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .state import ConfidenceProfile, EvidenceTier, ReplicationLevel

NodeId = str

_RELATIONS = {
    "supports", "contradicts", "replicates", "extends", "depends_on",
    "invalidates", "generalizes", "specializes", "fails_under",
    "derived_from", "tests", "produced_by", "measured_on",
}


@dataclass
class KGNode:
    node_id: NodeId
    kind: str          # question|claim|evidence|experiment|result|
                       # replication|contradiction|assumption|boundary
    content: str
    created_at: float = field(default_factory=time.time)
    tier: EvidenceTier = EvidenceTier.THEORETICAL
    level: ReplicationLevel = ReplicationLevel.SIMULATION
    confidence: float = 0.5
    # Boundary conditions — where the claim holds, stops, turns harmful.
    conditions: List[str] = field(default_factory=list)
    limits: List[str] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "active"   # active | superseded | retired — knowledge
                           # hygiene: falsified claims retire from the
                           # working set but stay in the graph for audit


class KnowledgeGraph:
    def __init__(self, persist_fn: Optional[Callable[[str, Dict], None]] = None):
        self.nodes: Dict[NodeId, KGNode] = {}
        self.edges: Set[Tuple[NodeId, str, NodeId]] = set()
        self._persist = persist_fn

    # -- writes ----------------------------------------------------------

    def add_node(self, node: KGNode) -> KGNode:
        self.nodes[node.node_id] = node
        # Full-fidelity payload — the audit event is the durable record the
        # graph is rebuilt from via replay(), so nothing may be truncated.
        self._emit("KG_NODE", {
            "node_id": node.node_id, "kind": node.kind,
            "content": node.content, "tier": int(node.tier),
            "level": int(node.level), "confidence": node.confidence,
            "created_at": node.created_at,
            "conditions": list(node.conditions),
            "limits": list(node.limits),
            "failure_modes": list(node.failure_modes),
            "metadata": dict(node.metadata),
            "status": node.status})
        return node

    def retire(self, node_id: NodeId) -> None:
        """Remove a claim from the working knowledge set — the node and
        its edges stay queryable for audit, but nothing builds on it."""
        node = self.nodes.get(node_id)
        if node is not None:
            node.status = "retired"
            self._emit("KG_RETIRE", {"node_id": node_id})

    def add_edge(self, src: NodeId, relation: str, dst: NodeId) -> None:
        if relation not in _RELATIONS:
            raise ValueError(f"unknown KG relation '{relation}'")
        if src not in self.nodes or dst not in self.nodes:
            raise KeyError("edge endpoints must exist in the graph")
        self.edges.add((src, relation, dst))
        self._emit("KG_EDGE", {"src": src, "relation": relation,
                               "dst": dst})

    def _emit(self, kind: str, payload: Dict[str, Any]) -> None:
        if self._persist is not None:
            try:
                self._persist(kind, payload)
            except Exception:
                pass  # persistence failure never blocks reasoning

    # -- replay (rehydration from the durable audit stream) ---------------

    def replay_events(self, events: List[Any]) -> Dict[str, int]:
        """Rebuild the graph from persisted RESEARCH_KG events, oldest
        first. Idempotent: nodes/edges dedupe on ids — replaying the same
        stream twice produces the same graph."""
        restored = {"nodes": 0, "edges": 0, "skipped": 0}
        for event in events:
            action = str(self._ev_field(event, "action") or "")
            payload = self._ev_payload(event)
            try:
                if action == "KG_NODE":
                    node = self._node_from_payload(payload)
                    if node.node_id not in self.nodes:
                        self.nodes[node.node_id] = node
                        restored["nodes"] += 1
                elif action == "KG_RETIRE":
                    nid = payload.get("node_id")
                    if nid in self.nodes:
                        self.nodes[nid].status = "retired"
                        restored["nodes"] += 0  # counted via node events
                elif action == "KG_EDGE":
                    src, dst = payload.get("src"), payload.get("dst")
                    rel = payload.get("relation")
                    if (rel in _RELATIONS and src in self.nodes
                            and dst in self.nodes):
                        self.edges.add((src, rel, dst))
                        restored["edges"] += 1
                    else:
                        restored["skipped"] += 1
                else:
                    restored["skipped"] += 1
            except Exception:
                restored["skipped"] += 1
        return restored

    @staticmethod
    def _ev_field(event: Any, key: str) -> Any:
        """Events arrive as dicts (repository rows) or AuditEvent objects."""
        if isinstance(event, dict):
            if key in event:
                return event[key]
            inner = event.get("event_json")
            if isinstance(inner, str):
                import json as _json
                try:
                    inner = _json.loads(inner)
                except (ValueError, TypeError):
                    inner = {}
            if isinstance(inner, dict):
                return inner.get(key)
            return None
        return getattr(event, key, None)

    @classmethod
    def _ev_payload(cls, event: Any) -> Dict[str, Any]:
        details = cls._ev_field(event, "details")
        return dict(details) if hasattr(details, "keys") else {}

    @staticmethod
    def _node_from_payload(p: Dict[str, Any]) -> KGNode:
        return KGNode(
            node_id=str(p.get("node_id") or ""),
            kind=str(p.get("kind") or "claim"),
            content=str(p.get("content") or ""),
            created_at=float(p.get("created_at") or time.time()),
            tier=EvidenceTier(int(p.get("tier", 0))),
            level=ReplicationLevel(int(p.get("level", 0))),
            confidence=float(p.get("confidence", 0.5)),
            conditions=[str(c) for c in p.get("conditions") or []],
            limits=[str(c) for c in p.get("limits") or []],
            failure_modes=[str(c) for c in p.get("failure_modes") or []],
            metadata=dict(p.get("metadata") or {}),
            status=str(p.get("status") or "active"))

    # -- replay -----------------------------------------------------------

    @classmethod
    def replay(cls, events: List[Dict[str, Any]],
               persist_fn: Optional[Callable[[str, Dict], None]] = None
               ) -> "KnowledgeGraph":
        """Rebuild the graph from durable RESEARCH_KG audit events.

        Replayed writes must not re-emit (they'd duplicate into the audit
        log) — nodes/edges are inserted directly. Idempotent: replaying the
        same stream twice converges to the same graph."""
        graph = cls(persist_fn=persist_fn)
        for ev in events:
            action = ev.get("action") or ""
            payload = ev.get("details") or ev.get("payload") or {}
            if not isinstance(payload, dict):
                continue
            if action == "KG_NODE":
                try:
                    node = KGNode(
                        node_id=str(payload["node_id"]),
                        kind=str(payload.get("kind", "evidence")),
                        content=str(payload.get("content", "")),
                        created_at=float(
                            payload.get("created_at") or time.time()),
                        tier=EvidenceTier(int(payload.get("tier", 0))),
                        level=ReplicationLevel(int(payload.get("level", 0))),
                        confidence=float(payload.get("confidence", 0.5)),
                        conditions=list(payload.get("conditions") or []),
                        limits=list(payload.get("limits") or []),
                        failure_modes=list(payload.get("failure_modes") or []),
                        metadata=dict(payload.get("metadata") or {}))
                    graph.nodes[node.node_id] = node
                except (KeyError, ValueError, TypeError):
                    continue
            elif action == "KG_EDGE":
                src, dst = payload.get("src"), payload.get("dst")
                rel = payload.get("relation")
                if (src in graph.nodes and dst in graph.nodes
                        and rel in _RELATIONS):
                    graph.edges.add((src, rel, dst))
        return graph

    # -- reads -----------------------------------------------------------

    def claims_for(self, question_id: NodeId) -> List[KGNode]:
        return [self.nodes[s] for (s, r, d) in self.edges
                if r == "derived_from" and d == question_id
                and s in self.nodes and self.nodes[s].kind == "claim"]

    def evidence_for(self, claim_id: NodeId) -> List[KGNode]:
        return [self.nodes[s] for (s, r, d) in self.edges
                if d == claim_id and r in ("supports", "contradicts")]

    def replications_of(self, claim_id: NodeId) -> List[KGNode]:
        return [self.nodes[s] for (s, r, d) in self.edges
                if d == claim_id and r == "replicates"]

    def contradictions(self) -> List[Tuple[NodeId, NodeId, NodeId]]:
        """Claims/evidence pairs that disagree — never averaged away,
        each contradiction is itself a research object."""
        out = []
        for (s, r, d) in self.edges:
            if r == "contradicts" and s in self.nodes and d in self.nodes:
                out.append((s, d, r))
        return out

    def boundary_conditions(self, claim_id: NodeId) -> Dict[str, List[str]]:
        node = self.nodes.get(claim_id)
        if node is None:
            return {}
        return {"conditions": node.conditions, "limits": node.limits,
                "failure_modes": node.failure_modes}

    def assess_claim(self, claim_id: NodeId) -> ConfidenceProfile:
        """Aggregate the claim's evidence into a confidence profile —
        replication count, effect CI via the recorded effect estimates,
        OOD/adversarial performance, evidence tier."""
        profile = ConfidenceProfile()
        node = self.nodes.get(claim_id)
        if node is None:
            return profile
        supports, contradicts, effects = [], [], []
        for (s, r, d) in self.edges:
            if d != claim_id or s not in self.nodes:
                continue
            src = self.nodes[s]
            if r == "supports":
                supports.append(src)
                eff = src.metadata.get("effect")
                if isinstance(eff, (int, float)):
                    effects.append(float(eff))
                if src.tier > profile.max_tier:
                    profile.max_tier = src.tier
                if src.tier == EvidenceTier.REAL_WORLD:
                    profile.real_world_venues.append(
                        str(src.metadata.get("venue", "unknown")))
            elif r == "contradicts":
                contradicts.append(src)
            elif r == "replicates":
                profile.n_replications += 1
                if src.level > node.level:
                    pass
                if src.tier > profile.max_tier:
                    profile.max_tier = src.tier
        profile.n_experiments = len(supports) + len(contradicts)
        total = len(supports) + len(contradicts)
        profile.replication_ratio = (len(supports) / total
                                     if total else 0.0)
        if effects:
            mean = sum(effects) / len(effects)
            var = (sum((e - mean) ** 2 for e in effects) / max(1, len(effects) - 1))
            se = (var / len(effects)) ** 0.5
            profile.effect_estimate = mean
            profile.ci_low, profile.ci_high = mean - 1.96 * se, mean + 1.96 * se
        ood = [self.nodes[s].metadata.get("effect")
               for (s, r, d) in self.edges
               if d == claim_id and r == "generalizes"
               and s in self.nodes
               and isinstance(self.nodes[s].metadata.get("effect"), (int, float))]
        if ood:
            profile.ood_effect = sum(ood) / len(ood)
        profile.compute_level()
        return profile

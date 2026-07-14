"""
Operational Services for Cognitive OS.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Set, Tuple
from uuid import uuid4
from .os_core import *
import numpy as np

logger = logging.getLogger(__name__)

class PropertyKnowledgeGraphBase:
    """In-memory property graph with strict typed nodes and relations."""

    def __init__(self, clock: Optional[Callable[[], datetime]] = None) -> None:
        self.clock = clock or datetime.utcnow
        self.nodes: Dict[str, KGNode] = {}
        self.edges: List[KGEdge] = []
        self._outgoing: Dict[str, List[KGEdge]] = defaultdict(list)
        self._incoming: Dict[str, List[KGEdge]] = defaultdict(list)

    def add_node(
        self,
        node_type: COSNodeType | str,
        properties: Mapping[str, Any],
        confidence: float = 0.5,
        source: str = "system",
        tags: Optional[Sequence[str]] = None,
        node_id: Optional[str] = None,
    ) -> str:
        """Add a typed node and return its id."""
        node_type_enum = COSNodeType(node_type)
        clean_properties = self._validate_properties(properties)
        confidence = _clamp(confidence, 0.0, 1.0)
        node_id = node_id or self._node_id(node_type_enum, clean_properties)
        node = KGNode(
            node_id=node_id,
            node_type=node_type_enum,
            properties=clean_properties,
            confidence=confidence,
            last_updated=self.clock(),
            source=source,
            tags=list(tags or []),
        )
        self.nodes[node_id] = node
        return node_id

    def add_relation(
        self,
        subject: str,
        predicate: COSEdgeType | str,
        object: str,
        confidence: float = 0.5,
        source: str = "system",
    ) -> KGEdge:
        if subject not in self.nodes:
            raise KeyError(f"unknown subject node: {subject}")
        if object not in self.nodes:
            raise KeyError(f"unknown object node: {object}")
        edge = KGEdge(
            subject=subject,
            predicate=COSEdgeType(predicate),
            object=object,
            confidence=_clamp(confidence, 0.0, 1.0),
            last_updated=self.clock(),
            source=source,
        )
        self.edges.append(edge)
        self._outgoing[subject].append(edge)
        self._incoming[object].append(edge)
        return edge

    def query_kg(
        self,
        cypher_pattern: str = "",
        context_filters: Optional[Mapping[str, Any]] = None,
    ) -> KGSubgraph:
        filters = dict(context_filters or {})
        candidate_ids = set(self.nodes)

        node_types = filters.get("node_types")
        if node_types:
            allowed = {COSNodeType(item) for item in node_types}
            candidate_ids = {nid for nid in candidate_ids if self.nodes[nid].node_type in allowed}

        tags = set(filters.get("tags", []))
        if tags:
            candidate_ids = {nid for nid in candidate_ids if tags.intersection(self.nodes[nid].tags)}

        source = filters.get("source")
        if source:
            candidate_ids = {nid for nid in candidate_ids if self.nodes[nid].source == source}

        min_confidence = float(filters.get("min_confidence", 0.0))
        candidate_ids = {nid for nid in candidate_ids if self.nodes[nid].confidence >= min_confidence}

        start_nodes = list(filters.get("start_nodes", []))
        max_hops = int(filters.get("max_hops", 0))
        if start_nodes and max_hops > 0:
            traversed = self.expand(start_nodes, max_hops=max_hops)
            candidate_ids &= set(traversed.nodes)

        relation_types = filters.get("relation_types")
        if relation_types:
            allowed_edges = {COSEdgeType(item) for item in relation_types}
        else:
            allowed_edges = set(COSEdgeType)

        nodes = {nid: self.nodes[nid] for nid in candidate_ids}
        edges = [
            edge
            for edge in self.edges
            if edge.subject in candidate_ids
            and edge.object in candidate_ids
            and edge.predicate in allowed_edges
        ]
        return KGSubgraph(nodes=nodes, edges=edges)

    def expand(self, start_nodes: Sequence[str], max_hops: int = 2) -> KGSubgraph:
        visited: Set[str] = set()
        selected_edges: List[KGEdge] = []
        q: deque[Tuple[str, int]] = deque((nid, 0) for nid in start_nodes if nid in self.nodes)

        while q:
            node_id, depth = q.popleft()
            if node_id in visited or depth > max_hops:
                continue
            visited.add(node_id)
            if depth == max_hops:
                continue
            for edge in self._outgoing.get(node_id, []) + self._incoming.get(node_id, []):
                selected_edges.append(edge)
                neighbor = edge.object if edge.subject == node_id else edge.subject
                if neighbor not in visited:
                    q.append((neighbor, depth + 1))

        nodes = {nid: self.nodes[nid] for nid in visited}
        edges = [edge for edge in selected_edges if edge.subject in visited and edge.object in visited]
        return KGSubgraph(nodes=nodes, edges=edges)

    def update_confidence(self, node_id: str, confidence: float) -> None:
        if node_id not in self.nodes:
            return
        node = self.nodes[node_id]
        self.nodes[node_id] = KGNode(
            node_id=node.node_id,
            node_type=node.node_type,
            properties=dict(node.properties),
            confidence=_clamp(confidence, 0.0, 1.0),
            last_updated=self.clock(),
            source=node.source,
            tags=list(node.tags),
        )

    def prune(self, min_confidence: float = 0.1, max_age_days: int = 90) -> List[str]:
        cutoff = self.clock() - timedelta(days=max_age_days)
        from collections import Counter
        incoming = Counter(edge.object for edge in self.edges)
        outgoing = Counter(edge.subject for edge in self.edges)
        removed: List[str] = []
        for node_id, node in list(self.nodes.items()):
            degree = incoming[node_id] + outgoing[node_id]
            if node.confidence < min_confidence and degree == 0 and node.last_updated < cutoff:
                removed.append(node_id)
                self.nodes.pop(node_id, None)
        if removed:
            self.edges = [edge for edge in self.edges if edge.subject not in removed and edge.object not in removed]
            self._rebuild_adjacency()
        return removed

    def _rebuild_adjacency(self) -> None:
        self._outgoing.clear()
        self._incoming.clear()
        for edge in self.edges:
            self._outgoing[edge.subject].append(edge)
            self._incoming[edge.object].append(edge)

    def _node_id(self, node_type: COSNodeType, properties: Mapping[str, Any]) -> str:
        digest = _stable_hash({"type": node_type.value, "properties": _jsonable(properties)})[:16]
        return f"{node_type.value.lower()}-{digest}"

    def _validate_properties(self, properties: Mapping[str, Any]) -> Dict[str, Any]:
        clean: Dict[str, Any] = {}
        for key, value in properties.items():
            normalized_key = str(key).strip()
            if normalized_key.lower() in BLOCKED_TEXT_KEYS:
                raise ValueError(f"raw text property is not allowed in KG node: {normalized_key}")
            clean[normalized_key] = _jsonable(value)
        return clean


class PropertyKnowledgeGraph(PropertyKnowledgeGraphBase):
    pass

class DecisionMemory:
    """Decision audit backbone."""

    def __init__(self) -> None:
        self.records: Dict[str, DecisionRecord] = {}

    def log_decision(self, record: DecisionRecord) -> str:
        self.records[record.id] = record
        return record.id

    def update_actual_outcome(
        self,
        decision_id: str,
        actual_outcome: Mapping[str, Any],
        confidence_post: Optional[float] = None,
    ) -> DecisionRecord:
        record = self.records[decision_id]
        record.actual_outcome = dict(actual_outcome)
        if confidence_post is not None:
            record.confidence_post = _clamp(confidence_post, 0.0, 1.0)
        return record

    def query_similar_decisions(self, context_embedding: Mapping[str, float], k: int = 5) -> List[DecisionRecord]:
        scored: List[Tuple[float, DecisionRecord]] = []
        for record in self.records.values():
            record_embedding = _embedding(record.context)
            scored.append((_cosine(context_embedding, record_embedding), record))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [record for _, record in scored[:k]]


class FailureMemory:
    """Explicit store of strategies and assumptions that failed."""

    def __init__(self) -> None:
        self.records: Dict[str, FailureRecord] = {}

    def log_failure(self, record: FailureRecord) -> str:
        record.severity = int(max(1, min(5, record.severity)))
        self.records[record.id] = record
        return record.id

    def check_preconditions(self, current_context: Mapping[str, Any]) -> List[FailureRecord]:
        matches: Dict[str, FailureRecord] = {}
        for record in self.records.values():
            if _conditions_match(record.edge_case_conditions, current_context):
                matches[record.id] = record
            else:
                avoid_if = record.derived_constraint.get("avoid_if")
                if isinstance(avoid_if, Mapping) and _conditions_match(avoid_if, current_context):
                    matches[record.id] = record
                elif _conditions_match(record.derived_constraint, current_context):
                    matches[record.id] = record
        return list(matches.values())


class StrategyLibrary:
    """Reusable, versioned strategy templates."""

    def __init__(self, kg: PropertyKnowledgeGraph) -> None:
        self.kg = kg
        self.strategies: Dict[str, Strategy] = {}

    def add_strategy(self, strategy: Strategy, source: str = "strategy_library") -> str:
        if not strategy.name:
            raise ValueError("strategy name is required")
        if strategy.strategy_node_ref is None:
            strategy.strategy_node_ref = self.kg.add_node(
                COSNodeType.STRATEGY,
                properties={
                    "name": strategy.name,
                    "version": strategy.version,
                    "precondition": strategy.precondition,
                    "success_metrics": strategy.success_metrics,
                },
                confidence=0.5,
                source=source,
                tags=["strategy"],
            )
        self.strategies[strategy.id] = strategy
        return strategy.id

    def match_strategies(self, context: Mapping[str, Any], k: int = 5) -> List[Strategy]:
        candidates: List[Tuple[float, Strategy]] = []
        context_embedding = _embedding(context)
        for strategy in self.strategies.values():
            if strategy.deprecated:
                continue
            if not _precondition_passes(strategy.precondition, context):
                continue
            text_context = {
                "name": strategy.name,
                "precondition": strategy.precondition,
                "playbook": strategy.playbook,
                "metrics": strategy.success_metrics,
            }
            semantic = _cosine(context_embedding, _embedding(text_context))
            successes = float(strategy.performance.get("successes", 0))
            failures = float(strategy.performance.get("failures", 0))
            performance = 0.5 if successes + failures == 0 else successes / max(successes + failures, 1.0)
            candidates.append((semantic * 0.6 + performance * 0.4, strategy))
        candidates.sort(key=lambda item: item[0], reverse=True)
        return [strategy for _, strategy in candidates[:k]]

    def playbook_render(self, strategy: Strategy, parameters: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "strategy_id": strategy.id,
            "strategy_name": strategy.name,
            "version": strategy.version,
            "steps": list(strategy.playbook.get("steps", [])),
            "parameters": dict(parameters),
            "action_schema": dict(strategy.action_schema),
        }

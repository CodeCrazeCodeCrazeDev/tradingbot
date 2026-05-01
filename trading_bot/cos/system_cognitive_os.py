"""System-level Cognitive Operating System.

This is the stricter COS layer requested for AlphaAlgo:

observe -> think -> test -> learn

The implementation is intentionally typed and auditable. Knowledge is stored as
property-graph nodes and explicit relations, not as markdown notes or raw text
logs. Decisions, failures, strategies, retrieval, integration hooks, and
evolution rules are separate first-class layers.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import time
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
from uuid import uuid4


class COSNodeType(str, Enum):
    """Allowed knowledge graph node types."""

    CONCEPT = "Concept"
    ENTITY = "Entity"
    STRATEGY = "Strategy"
    OUTCOME = "Outcome"
    ASSUMPTION = "Assumption"
    BELIEF = "Belief"


class COSEdgeType(str, Enum):
    """Allowed knowledge graph edge types."""

    CAUSES = "causes"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    PRECEDES = "precedes"
    IS_A = "is_a"
    USED_IN = "used_in"
    LED_TO = "led_to"


class COSActionMode(str, Enum):
    """Integration action mode."""

    SHADOW = "shadow"
    DRY_RUN = "dry_run"
    EXTERNAL = "external"


class COSOutcomeStatus(str, Enum):
    """Outcome comparison status."""

    EXPECTED = "expected"
    DEVIATED = "deviated"
    FAILED = "failed"
    UNKNOWN = "unknown"


BLOCKED_TEXT_KEYS = {"content", "raw_text", "markdown", "note", "notes", "log", "transcript"}


@dataclass(frozen=True)
class KGNode:
    """Typed knowledge graph node."""

    node_id: str
    node_type: COSNodeType
    properties: Dict[str, Any]
    confidence: float
    last_updated: datetime
    source: str
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class KGEdge:
    """Typed knowledge graph relation."""

    subject: str
    predicate: COSEdgeType
    object: str
    confidence: float
    last_updated: datetime
    source: str = "system"


@dataclass(frozen=True)
class KGSubgraph:
    """Small query result from the property graph."""

    nodes: Dict[str, KGNode]
    edges: List[KGEdge]


@dataclass
class DecisionRecord:
    """Audit record for a decision and its realized outcome."""

    id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)
    decision: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: Dict[str, Any] = field(default_factory=dict)
    actual_outcome: Dict[str, Any] = field(default_factory=dict)
    confidence_pre: float = 0.0
    confidence_post: float = 0.0


@dataclass
class FailureRecord:
    """Explicit failure memory record."""

    id: str = field(default_factory=lambda: uuid4().hex)
    failed_strategy_ref: str = ""
    invalid_assumption_refs: List[str] = field(default_factory=list)
    edge_case_conditions: Dict[str, Any] = field(default_factory=dict)
    observed_outcome: Dict[str, Any] = field(default_factory=dict)
    severity: int = 1
    closed_loop: bool = False
    derived_constraint: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Strategy:
    """Reusable versioned decision template."""

    id: str = field(default_factory=lambda: uuid4().hex)
    name: str = ""
    version: int = 1
    precondition: str | Dict[str, Any] = field(default_factory=dict)
    action_schema: Dict[str, Any] = field(default_factory=dict)
    success_metrics: List[str] = field(default_factory=list)
    playbook: Dict[str, Any] = field(default_factory=dict)
    provenance: List[str] = field(default_factory=list)
    performance: Dict[str, Any] = field(
        default_factory=lambda: {"successes": 0, "failures": 0, "avg_outcome": 0.0}
    )
    deprecated: bool = False
    strategy_node_ref: Optional[str] = None


@dataclass(frozen=True)
class RetrievalBundle:
    """Context-aware retrieval result."""

    relevant_concepts: List[str]
    past_decisions: List[DecisionRecord]
    applicable_failures: List[FailureRecord]
    matching_strategies: List[Strategy]
    subgraph: KGSubgraph


@dataclass(frozen=True)
class COSPlan:
    """Plan produced by think()."""

    plan_id: str
    context: Dict[str, Any]
    retrieved: RetrievalBundle
    strategy: Optional[Strategy]
    parameters: Dict[str, Any]
    expected_outcome: Dict[str, Any]
    blocked_by_failures: List[str]
    confidence: float


@dataclass(frozen=True)
class IntegrationResult:
    """Result returned by the integration layer."""

    plan_id: str
    mode: COSActionMode
    accepted: bool
    external_ref: Optional[str]
    measured_result: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class COSCycleResult:
    """Full observe-think-test-learn cycle output."""

    observed_event_id: str
    plan: COSPlan
    decision_record: DecisionRecord
    integration_result: IntegrationResult
    learned_failures: List[str]
    updated_beliefs: List[str]


class PropertyKnowledgeGraph:
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
        """Add a typed relation between two existing nodes."""

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
        """Query the graph using simple filters.

        ``cypher_pattern`` is accepted for API compatibility. This in-memory
        MVP uses explicit filters rather than parsing Cypher.
        """

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
        """Traverse 1-3 hops from context nodes."""

        visited: Set[str] = set()
        selected_edges: List[KGEdge] = []
        queue: deque[Tuple[str, int]] = deque((nid, 0) for nid in start_nodes if nid in self.nodes)

        while queue:
            node_id, depth = queue.popleft()
            if node_id in visited or depth > max_hops:
                continue
            visited.add(node_id)
            if depth == max_hops:
                continue
            for edge in self._outgoing.get(node_id, []) + self._incoming.get(node_id, []):
                selected_edges.append(edge)
                neighbor = edge.object if edge.subject == node_id else edge.subject
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))

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
        """Remove low-confidence orphan nodes older than max_age_days."""

        cutoff = self.clock() - timedelta(days=max_age_days)
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


class RetrievalEngine:
    """Hybrid graph and semantic retrieval."""

    def __init__(
        self,
        kg: PropertyKnowledgeGraph,
        decision_memory: DecisionMemory,
        failure_memory: FailureMemory,
        strategy_library: StrategyLibrary,
    ) -> None:
        self.kg = kg
        self.decision_memory = decision_memory
        self.failure_memory = failure_memory
        self.strategy_library = strategy_library

    def retrieve(
        self,
        context: KGSubgraph | Mapping[str, Any],
        objectives: Sequence[str],
        top_k: int = 5,
    ) -> RetrievalBundle:
        if isinstance(context, KGSubgraph):
            subgraph = context
            context_payload = _subgraph_payload(context)
        else:
            context_payload = dict(context)
            start_nodes = list(context_payload.get("context_nodes", []))
            subgraph = self.kg.expand(start_nodes, max_hops=3) if start_nodes else self.kg.query_kg()

        objective_payload = {"objectives": list(objectives), "context": context_payload}
        query_embedding = _embedding(objective_payload)

        ranked_nodes: List[Tuple[float, str]] = []
        now = datetime.utcnow()
        for node_id, node in subgraph.nodes.items():
            graph_distance_score = 1.0
            semantic = _cosine(query_embedding, _embedding(node.properties | {"type": node.node_type.value}))
            age_days = max(0.0, (now - node.last_updated).total_seconds() / 86400.0)
            freshness = 1.0 / (1.0 + age_days)
            score = graph_distance_score * 0.4 + semantic * 0.4 + freshness * 0.2
            ranked_nodes.append((score, node_id))
        ranked_nodes.sort(key=lambda item: item[0], reverse=True)

        decisions = self.decision_memory.query_similar_decisions(query_embedding, k=top_k)
        failures = sorted(
            self.failure_memory.check_preconditions(context_payload),
            key=lambda record: record.severity,
            reverse=True,
        )
        strategies = self.strategy_library.match_strategies(context_payload, k=top_k)

        return RetrievalBundle(
            relevant_concepts=[node_id for _, node_id in ranked_nodes[:top_k]],
            past_decisions=decisions,
            applicable_failures=failures,
            matching_strategies=strategies,
            subgraph=subgraph,
        )


class IntegrationLayer:
    """Connectors for actions, observations, and feedback.

    External actions are disabled by default. Shadow and dry-run modes are the
    normal operating mode for trading research.
    """

    def __init__(self, default_mode: COSActionMode = COSActionMode.SHADOW) -> None:
        self.default_mode = default_mode
        self.action_connectors: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self.observation_events: List[Dict[str, Any]] = []
        self.feedback_events: List[Dict[str, Any]] = []

    def register_action_connector(self, name: str, connector: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        self.action_connectors[name] = connector

    def observe_event(self, event: Mapping[str, Any]) -> str:
        event_id = str(event.get("event_id") or uuid4().hex)
        payload = dict(event)
        payload["event_id"] = event_id
        payload.setdefault("observed_at", datetime.utcnow().isoformat())
        self.observation_events.append(payload)
        return event_id

    def execute_plan(self, plan: COSPlan, mode: Optional[COSActionMode | str] = None) -> IntegrationResult:
        mode_enum = COSActionMode(mode or self.default_mode)
        if plan.strategy is None:
            return IntegrationResult(
                plan_id=plan.plan_id,
                mode=mode_enum,
                accepted=False,
                external_ref=None,
                measured_result={"status": "blocked", "reason": "no strategy selected"},
                warnings=[],
            )

        rendered = {
            "plan_id": plan.plan_id,
            "strategy_id": plan.strategy.id,
            "parameters": dict(plan.parameters),
            "expected_outcome": dict(plan.expected_outcome),
        }
        if mode_enum in {COSActionMode.SHADOW, COSActionMode.DRY_RUN}:
            result = {
                "status": mode_enum.value,
                "accepted": True,
                "simulated": True,
                "action": rendered,
            }
            return IntegrationResult(plan.plan_id, mode_enum, True, None, result, warnings=["no external execution"])

        connector_name = str(plan.strategy.action_schema.get("connector", "default"))
        connector = self.action_connectors.get(connector_name)
        if connector is None:
            return IntegrationResult(
                plan_id=plan.plan_id,
                mode=mode_enum,
                accepted=False,
                external_ref=None,
                measured_result={"status": "blocked", "reason": f"missing connector {connector_name}"},
                warnings=[],
            )
        measured = connector(rendered)
        return IntegrationResult(
            plan_id=plan.plan_id,
            mode=mode_enum,
            accepted=bool(measured.get("accepted", True)),
            external_ref=measured.get("external_ref"),
            measured_result=measured,
        )

    def receive_feedback(self, feedback: Mapping[str, Any]) -> str:
        feedback_id = str(feedback.get("feedback_id") or uuid4().hex)
        payload = dict(feedback)
        payload["feedback_id"] = feedback_id
        payload.setdefault("received_at", datetime.utcnow().isoformat())
        self.feedback_events.append(payload)
        return feedback_id


class EvolutionLayer:
    """Outcome-driven belief and strategy evolution."""

    def __init__(
        self,
        kg: PropertyKnowledgeGraph,
        decision_memory: DecisionMemory,
        failure_memory: FailureMemory,
        strategy_library: StrategyLibrary,
    ) -> None:
        self.kg = kg
        self.decision_memory = decision_memory
        self.failure_memory = failure_memory
        self.strategy_library = strategy_library

    def learn_from_outcome(
        self,
        decision_id: str,
        actual_outcome: Mapping[str, Any],
        success_threshold: float = 0.0,
    ) -> Tuple[List[str], List[str]]:
        record = self.decision_memory.update_actual_outcome(decision_id, actual_outcome)
        measured = float(actual_outcome.get("measured_result", actual_outcome.get("pnl", 0.0)) or 0.0)
        expected_goal = float(record.expected_outcome.get("quantified_goal", 0.0) or 0.0)
        success = bool(actual_outcome.get("success_flag", measured >= success_threshold))
        deviation = measured - expected_goal
        confidence_post = _clamp(record.confidence_pre + (0.08 if success else -0.15), 0.0, 1.0)
        record.confidence_post = confidence_post
        record.actual_outcome = {
            **dict(actual_outcome),
            "deviation": deviation,
            "success_flag": success,
        }

        updated_beliefs: List[str] = []
        learned_failures: List[str] = []
        strategy_id = str(record.decision.get("chosen_strategy_ref", ""))
        strategy = self.strategy_library.strategies.get(strategy_id)

        if strategy is not None:
            if success:
                self._reinforce_strategy(strategy, measured)
                if strategy.strategy_node_ref:
                    self._bump_node(strategy.strategy_node_ref, +0.08)
                    updated_beliefs.append(strategy.strategy_node_ref)
            else:
                self._weaken_strategy(strategy, measured)
                failure_id = self._create_failure(record, strategy, actual_outcome)
                learned_failures.append(failure_id)
                if strategy.strategy_node_ref:
                    self._bump_node(strategy.strategy_node_ref, -0.12)
                    updated_beliefs.append(strategy.strategy_node_ref)

        for node_id in record.context.get("retrieved_strategies", []):
            if node_id in self.kg.nodes:
                self._bump_node(node_id, +0.03 if success else -0.05)
                updated_beliefs.append(node_id)

        if not success:
            outcome_node = self.kg.add_node(
                COSNodeType.OUTCOME,
                properties={
                    "decision_id": decision_id,
                    "measured_result": measured,
                    "success_flag": success,
                    "deviation": deviation,
                },
                confidence=0.8,
                source="cos_evolution",
                tags=["outcome", "failure"],
            )
            if strategy and strategy.strategy_node_ref:
                self.kg.add_relation(strategy.strategy_node_ref, COSEdgeType.LED_TO, outcome_node, confidence=0.8)

        return learned_failures, sorted(set(updated_beliefs))

    def bayesian_update_belief(
        self,
        belief_node_id: str,
        likelihood_outcome_given_belief: float,
        probability_outcome: float,
        invalid_threshold: float = 0.3,
    ) -> float:
        node = self.kg.nodes[belief_node_id]
        prior = node.confidence
        if probability_outcome <= 0:
            posterior = 0.0
        else:
            posterior = _clamp((likelihood_outcome_given_belief * prior) / probability_outcome, 0.0, 1.0)
        self.kg.update_confidence(belief_node_id, posterior)
        if posterior < invalid_threshold:
            invalid_node = self.kg.add_node(
                COSNodeType.OUTCOME,
                properties={"belief_ref": belief_node_id, "status": "invalidated"},
                confidence=1.0,
                source="cos_bayesian_revision",
                tags=["invalid_belief"],
            )
            self.kg.add_relation(belief_node_id, COSEdgeType.CONTRADICTS, invalid_node, confidence=1.0)
        return posterior

    def scheduled_prune(self) -> List[str]:
        return self.kg.prune(min_confidence=0.1, max_age_days=90)

    def _reinforce_strategy(self, strategy: Strategy, measured: float) -> None:
        successes = int(strategy.performance.get("successes", 0)) + 1
        failures = int(strategy.performance.get("failures", 0))
        previous = float(strategy.performance.get("avg_outcome", 0.0))
        total = successes + failures
        strategy.performance["successes"] = successes
        strategy.performance["avg_outcome"] = (previous * (total - 1) + measured) / max(total, 1)

    def _weaken_strategy(self, strategy: Strategy, measured: float) -> None:
        failures = int(strategy.performance.get("failures", 0)) + 1
        successes = int(strategy.performance.get("successes", 0))
        previous = float(strategy.performance.get("avg_outcome", 0.0))
        total = successes + failures
        strategy.performance["failures"] = failures
        strategy.performance["avg_outcome"] = (previous * (total - 1) + measured) / max(total, 1)
        if failures >= 3 and failures > successes:
            strategy.deprecated = True

    def _create_failure(self, record: DecisionRecord, strategy: Strategy, actual_outcome: Mapping[str, Any]) -> str:
        failure = FailureRecord(
            failed_strategy_ref=strategy.strategy_node_ref or strategy.id,
            invalid_assumption_refs=list(record.context.get("assumption_refs", [])),
            edge_case_conditions=dict(record.context.get("scenario", {})),
            observed_outcome=dict(actual_outcome),
            severity=int(actual_outcome.get("severity", 3)),
            closed_loop=False,
            derived_constraint={
                "strategy_id": strategy.id,
                "avoid_if": dict(record.context.get("scenario", {})),
            },
        )
        return self.failure_memory.log_failure(failure)

    def _bump_node(self, node_id: str, delta: float) -> None:
        node = self.kg.nodes.get(node_id)
        if node is not None:
            self.kg.update_confidence(node_id, node.confidence + delta)


class SystemCognitiveOperatingSystem:
    """Typed COS orchestrator for observe-think-test-learn loops."""

    def __init__(
        self,
        kg: Optional[PropertyKnowledgeGraph] = None,
        decision_memory: Optional[DecisionMemory] = None,
        failure_memory: Optional[FailureMemory] = None,
        strategy_library: Optional[StrategyLibrary] = None,
        integration_layer: Optional[IntegrationLayer] = None,
    ) -> None:
        self.kg = kg or PropertyKnowledgeGraph()
        self.decision_memory = decision_memory or DecisionMemory()
        self.failure_memory = failure_memory or FailureMemory()
        self.strategy_library = strategy_library or StrategyLibrary(self.kg)
        self.retrieval_engine = RetrievalEngine(
            self.kg,
            self.decision_memory,
            self.failure_memory,
            self.strategy_library,
        )
        self.integration_layer = integration_layer or IntegrationLayer()
        self.evolution_layer = EvolutionLayer(
            self.kg,
            self.decision_memory,
            self.failure_memory,
            self.strategy_library,
        )

    def observe(self, event: Mapping[str, Any]) -> Tuple[str, KGSubgraph]:
        """Ingest a structured event and return context subgraph."""

        event_id = self.integration_layer.observe_event(event)
        entity_id = self.kg.add_node(
            COSNodeType.ENTITY,
            properties={
                "event_id": event_id,
                "kind": event.get("kind", "observation"),
                "symbol": event.get("symbol", ""),
                "timestamp": event.get("timestamp", time.time()),
            },
            confidence=float(event.get("confidence", 0.5)),
            source=str(event.get("source", "observation")),
            tags=list(event.get("tags", ["observation"])),
        )

        for concept in event.get("concepts", []):
            concept_id = self.kg.add_node(
                COSNodeType.CONCEPT,
                properties={"name": concept},
                confidence=0.5,
                source="observation",
                tags=["context"],
            )
            self.kg.add_relation(entity_id, COSEdgeType.USED_IN, concept_id, confidence=0.5)

        return event_id, self.kg.expand([entity_id], max_hops=2)

    def think(self, context: Mapping[str, Any] | KGSubgraph, objectives: Sequence[str]) -> COSPlan:
        """Retrieve memory, block known failures, and select a strategy."""

        bundle = self.retrieval_engine.retrieve(context, objectives=objectives)
        context_payload = _subgraph_payload(context) if isinstance(context, KGSubgraph) else dict(context)
        blockers = [failure.id for failure in bundle.applicable_failures if failure.severity >= 4]
        strategy = None if blockers else (bundle.matching_strategies[0] if bundle.matching_strategies else None)
        parameters = self._parameters_from_context(context_payload, strategy)
        confidence = self._plan_confidence(bundle, strategy, blockers)
        expected = {
            "description": "strategy outcome estimate",
            "quantified_goal": confidence,
            "probability": confidence,
        }
        return COSPlan(
            plan_id=uuid4().hex,
            context=context_payload,
            retrieved=bundle,
            strategy=strategy,
            parameters=parameters,
            expected_outcome=expected,
            blocked_by_failures=blockers,
            confidence=confidence,
        )

    def test(self, plan: COSPlan, mode: COSActionMode | str = COSActionMode.SHADOW) -> Tuple[IntegrationResult, DecisionRecord]:
        """Run the plan through integration in shadow/dry-run/external mode."""

        result = self.integration_layer.execute_plan(plan, mode=mode)
        decision = DecisionRecord(
            context={
                "scenario_id": plan.context.get("scenario_id"),
                "kg_snapshot_id": self._kg_snapshot_id(),
                "retrieved_strategies": [
                    strategy.strategy_node_ref or strategy.id for strategy in plan.retrieved.matching_strategies
                ],
                "assumption_refs": plan.context.get("assumption_refs", []),
                "scenario": plan.context,
            },
            decision={
                "action": "BLOCKED" if plan.strategy is None else plan.strategy.action_schema.get("action", "EXECUTE_PLAYBOOK"),
                "parameters": plan.parameters,
                "chosen_strategy_ref": plan.strategy.id if plan.strategy else None,
            },
            expected_outcome=plan.expected_outcome,
            actual_outcome=result.measured_result,
            confidence_pre=plan.confidence,
            confidence_post=plan.confidence,
        )
        self.decision_memory.log_decision(decision)
        if plan.strategy is not None:
            plan.strategy.provenance.append(decision.id)
        return result, decision

    def learn(
        self,
        decision_id: str,
        actual_outcome: Mapping[str, Any],
    ) -> Tuple[List[str], List[str]]:
        """Update beliefs, strategy performance, and failures from outcome."""

        return self.evolution_layer.learn_from_outcome(decision_id, actual_outcome)

    def run_cycle(
        self,
        event: Mapping[str, Any],
        objectives: Sequence[str],
        mode: COSActionMode | str = COSActionMode.SHADOW,
        actual_outcome: Optional[Mapping[str, Any]] = None,
    ) -> COSCycleResult:
        """Execute observe -> think -> test -> learn."""

        event_id, context = self.observe(event)
        think_context = dict(event)
        think_context["context_nodes"] = list(context.nodes)
        plan = self.think(think_context, objectives)
        integration_result, decision = self.test(plan, mode=mode)
        outcome = actual_outcome or integration_result.measured_result
        learned_failures, updated_beliefs = self.learn(decision.id, outcome)
        return COSCycleResult(
            observed_event_id=event_id,
            plan=plan,
            decision_record=decision,
            integration_result=integration_result,
            learned_failures=learned_failures,
            updated_beliefs=updated_beliefs,
        )

    def _parameters_from_context(self, context: Mapping[str, Any], strategy: Optional[Strategy]) -> Dict[str, Any]:
        if strategy is None:
            return {}
        allowed = set(strategy.action_schema.get("properties", {}).keys())
        if not allowed:
            return dict(context)
        return {key: value for key, value in context.items() if key in allowed}

    def _plan_confidence(self, bundle: RetrievalBundle, strategy: Optional[Strategy], blockers: Sequence[str]) -> float:
        if blockers or strategy is None:
            return 0.0
        strategy_successes = float(strategy.performance.get("successes", 0))
        strategy_failures = float(strategy.performance.get("failures", 0))
        performance = 0.5 if strategy_successes + strategy_failures == 0 else strategy_successes / max(strategy_successes + strategy_failures, 1.0)
        graph_support = min(len(bundle.relevant_concepts) / 5.0, 1.0)
        failure_penalty = min(len(bundle.applicable_failures) * 0.15, 0.45)
        return _clamp(0.35 + performance * 0.35 + graph_support * 0.20 - failure_penalty, 0.0, 1.0)

    def _kg_snapshot_id(self) -> str:
        payload = {
            "nodes": sorted(self.kg.nodes),
            "edges": [(edge.subject, edge.predicate.value, edge.object) for edge in self.kg.edges],
        }
        return _stable_hash(payload)[:16]


def create_system_cos() -> SystemCognitiveOperatingSystem:
    """Factory for the typed system-level COS."""

    return SystemCognitiveOperatingSystem()


def _conditions_match(conditions: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
    if not conditions:
        return False
    for key, expected in conditions.items():
        if key == "strategy_id":
            continue
        actual = _lookup_path(context, key)
        if isinstance(expected, Mapping):
            for operator, threshold in expected.items():
                if not _compare(actual, str(operator), threshold):
                    return False
        elif actual != expected:
            return False
    return True


def _precondition_passes(precondition: str | Mapping[str, Any], context: Mapping[str, Any]) -> bool:
    if isinstance(precondition, Mapping):
        return _conditions_match(precondition, context) if precondition else True
    if not precondition:
        return True
    return _safe_eval_expression(precondition, context)


def _safe_eval_expression(expression: str, context: Mapping[str, Any]) -> bool:
    tree = ast.parse(expression, mode="eval")
    return bool(_eval_ast(tree.body, context))


def _eval_ast(node: ast.AST, context: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.BoolOp):
        values = [_eval_ast(value, context) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
    if isinstance(node, ast.Compare):
        left = _eval_ast(node.left, context)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_ast(comparator, context)
            if not _compare(left, op.__class__.__name__, right):
                return False
            left = right
        return True
    if isinstance(node, ast.Name):
        return context.get(node.id)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _eval_ast(node.operand, context)
    raise ValueError(f"unsupported precondition expression: {ast.dump(node)}")


def _compare(actual: Any, operator: str, expected: Any) -> bool:
    if operator in {"lt", "Lt"}:
        return actual < expected
    if operator in {"lte", "LtE"}:
        return actual <= expected
    if operator in {"gt", "Gt"}:
        return actual > expected
    if operator in {"gte", "GtE"}:
        return actual >= expected
    if operator in {"eq", "Eq"}:
        return actual == expected
    if operator in {"ne", "NotEq"}:
        return actual != expected
    if operator == "in":
        return actual in expected
    raise ValueError(f"unsupported condition operator: {operator}")


def _lookup_path(payload: Mapping[str, Any], key: str) -> Any:
    value: Any = payload
    for part in str(key).split("."):
        if not isinstance(value, Mapping):
            return None
        value = value.get(part)
    return value


def _embedding(payload: Mapping[str, Any]) -> Dict[str, float]:
    text = json.dumps(_jsonable(payload), sort_keys=True)
    tokens = [token.lower() for token in _tokenize(text)]
    counts = Counter(tokens)
    norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {token: value / norm for token, value in counts.items()}


def _cosine(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def _tokenize(text: str) -> List[str]:
    token = []
    tokens = []
    for char in text:
        if char.isalnum() or char == "_":
            token.append(char)
        elif token:
            tokens.append("".join(token))
            token = []
    if token:
        tokens.append("".join(token))
    return tokens


def _subgraph_payload(subgraph: KGSubgraph) -> Dict[str, Any]:
    return {
        "nodes": {node_id: node.properties for node_id, node in subgraph.nodes.items()},
        "node_types": {node_id: node.node_type.value for node_id, node in subgraph.nodes.items()},
        "edges": [(edge.subject, edge.predicate.value, edge.object) for edge in subgraph.edges],
    }


def _stable_hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(inner) for inner in value]
    return value


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))

"""
Core Data Models and Utilities for Cognitive OS.
"""

from __future__ import annotations

from uuid import uuid4
import ast
import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple


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
    from uuid import uuid4
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
    from uuid import uuid4
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
    from uuid import uuid4
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

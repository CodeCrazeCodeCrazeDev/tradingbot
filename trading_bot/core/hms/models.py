"""
Scientific Traceability and Evidence Models - UCA-2026 HMS
=========================================================

Authoritative data models for evidence-first reasoning, scientific traceability,
and persistent research memory.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union, Tuple
import uuid
from ..governance.determinism import determinism

class EvidenceSourceType(Enum):
    MARKET_DATA = auto()
    ALTERNATIVE_DATA = auto()
    MACRO_INDICATOR = auto()
    ORDER_FLOW = auto()
    SENTIMENT_ANALYSIS = auto()
    LITERAL_RESEARCH = auto()
    SIMULATION_RESULT = auto()

class RelationType(Enum):
    SUPPORTS = "SUPPORTS"
    REFUTES = "REFUTES"
    CAUSES = "CAUSES"
    CORRELATES = "CORRELATES"
    STRENGTHENS = "STRENGTHENS"
    WEAKENS = "WEAKENS"

@dataclass
class EvidencePackage:
    """A single piece of verified market evidence."""
    evidence_id: str = field(default_factory=lambda: determinism.get_uuid())
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source_type: EvidenceSourceType = EvidenceSourceType.MARKET_DATA
    source_name: str = ""
    raw_data: Any = None
    processed_value: Any = None
    confidence: float = 0.0
    provenance: str = ""  # URI or specific data source reference
    falsifiable_claim: str = ""
    verification_method: str = ""
    is_verified: bool = False

@dataclass
class EvidenceNode:
    """A node in the Causal Evidence Graph with decay and regime awareness."""
    node_id: str
    content: Union[EvidencePackage, str]
    node_type: str  # "EVIDENCE", "CLAIM", "HYPOTHESIS", "VERDICT"

    # Causal Graph additions
    confidence: float = 1.0
    uncertainty: float = 0.0
    market_regime: str = "unknown"
    causal_parents: List[str] = field(default_factory=list)
    freshness_score: float = 1.0  # 1.0 (new) to 0.0 (obsolete)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class EvidenceEdge:
    """
    A directed, typed relationship in the Evidence Graph.
    Implements QKG (Quantum Knowledge Graph) context-dependent validity (arXiv:2604.23972).
    """
    source_id: str
    target_id: str
    relation: RelationType
    weight: float = 1.0
    evidence_package_id: Optional[str] = None
    is_causal: bool = False
    # QKG context-dependent validity: the set of context keys under which this
    # edge's relation holds (arXiv:2604.23972).
    context_validity_mask: Optional[Dict[str, Any]] = None

    def is_valid_in_context(self, context: Dict[str, Any]) -> bool:
        """QKG: the edge is valid iff every masked context key agrees with
        the supplied context. No mask means unconditionally valid."""
        if not self.context_validity_mask:
            return True
        context = context or {}
        return all(
            context.get(k) == v for k, v in self.context_validity_mask.items()
        )

@dataclass
class EvidenceGraph:
    """A snapshot of the Causal Evidence Graph for a specific decision."""
    graph_id: str = field(default_factory=lambda: determinism.get_uuid())
    nodes: Dict[str, EvidenceNode] = field(default_factory=dict)
    edges: List[EvidenceEdge] = field(default_factory=list)

    def add_node(self, node: EvidenceNode):
        self.nodes[node.node_id] = node

    def add_edge(self, edge: EvidenceEdge):
        self.edges.append(edge)

    def query_counterfactual(self, intervention: Dict[str, Any],
                             context: Optional[Dict[str, Any]] = None
                             ) -> 'EvidenceGraph':
        """
        do(X=x): Pearl graph surgery on the causal evidence graph
        (UCA V4 do-calculus).

        Intervened nodes are forced to the supplied values and their
        incoming causal edges are severed — under do(), a node no longer
        depends on its parents. The intervention then propagates downstream
        along causal edges whose QKG ``context_validity_mask`` holds in
        ``context``, attenuated by edge weight and by the ratio between the
        intervened and prior parent confidence.

        ``intervention`` maps ``node_id`` to a scalar confidence override
        (``{"node_a": 0.9}``) or a field dict
        (``{"node_a": {"confidence": 0.9}}``).
        """
        import copy

        counterfactual = EvidenceGraph(graph_id=f"{self.graph_id}-cf")
        counterfactual.nodes = copy.deepcopy(self.nodes)
        counterfactual.edges = copy.deepcopy(self.edges)

        severed: set = set()
        factors: Dict[str, float] = {}
        ctx = dict(context or {})

        for node_id, value in intervention.items():
            node = counterfactual.nodes.get(str(node_id))
            if node is None:
                continue
            # sever incoming causal edges INTO the intervened node
            counterfactual.edges = [
                e for e in counterfactual.edges
                if not (e.is_causal and e.target_id == node.node_id)]
            prior = float(node.confidence or 0.0)
            if isinstance(value, dict):
                for k, v in value.items():
                    if hasattr(node, k):
                        setattr(node, k, v)
                new_conf = float(node.confidence)
            else:
                new_conf = float(value)
                node.confidence = new_conf
            factors[node.node_id] = new_conf / max(prior, 1e-9)
            severed.add(node.node_id)
            node.metadata["counterfactual"] = True

        # BFS downstream along context-valid causal edges; each child is
        # attenuated once by parent factor * edge weight.
        queue = list(severed)
        seen: set = set()
        while queue:
            parent = queue.pop(0)
            for edge in counterfactual.edges:
                if (not edge.is_causal or edge.source_id != parent
                        or edge.target_id in severed
                        or edge.target_id in seen):
                    continue
                if not edge.is_valid_in_context(ctx):
                    continue
                child = counterfactual.nodes.get(edge.target_id)
                if child is None:
                    continue
                child.confidence = max(0.0, min(1.0, child.confidence
                                                * factors.get(parent, 1.0)
                                                * edge.weight))
                child.metadata["counterfactual_propagated_from"] = parent
                seen.add(edge.target_id)
                queue.append(edge.target_id)

        return counterfactual

@dataclass
class Hypothesis:
    """A falsifiable market hypothesis."""
    hypothesis_id: str = field(default_factory=lambda: determinism.get_uuid())
    description: str = ""
    base_assumptions: List[str] = field(default_factory=list)
    predicted_outcome: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    confidence_interval: Tuple[float, float] = (0.0, 0.0)

    # UCA V4 Structured Metadata
    probability: float = 0.0
    epistemic_uncertainty: float = 0.0  # Knowledge gap
    aleatoric_uncertainty: float = 0.0  # Market noise
    expected_return: float = 0.0
    expected_drawdown: float = 0.0
    expected_holding_time_bars: int = 0
    invalidation_conditions: List[str] = field(default_factory=list)
    execution_feasibility: float = 1.0

    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class VerifierReport:
    """Result from an independent verification agent."""
    agent_name: str
    is_valid: bool
    confidence: float
    critique: str
    detected_hallucinations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class InstitutionalProvenance:
    """
    Immutable provenance record for bit-for-bit decision reproduction.
    UCA V5 Requirement: Institutional Accountability.
    """
    git_sha: str = "unknown"
    config_hash: str = ""
    model_versions: Dict[str, str] = field(default_factory=dict)
    feature_hash: str = ""
    input_snapshot_hash: str = ""
    memory_snapshot_id: str = ""
    random_seed: int = 0
    cuda_deterministic: bool = True
    torch_version: str = ""
    numpy_version: str = ""
    pipeline_version: str = "UCA-V5"
    risk_policy_version: str = "v1.0"
    verification_signatures: Dict[str, str] = field(default_factory=dict)
    source_feed: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    raw_payload_checksum: str = ""

@dataclass
class ResearchLedgerEntry:
    """Permanent audit trail for a single trading decision."""
    entry_id: str = field(default_factory=lambda: determinism.get_uuid())
    trade_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Reasoning Trace
    hypothesis: Hypothesis = field(default_factory=Hypothesis)
    reasoning_steps: List[str] = field(default_factory=list)

    # Evidence & Verification
    evidence_graph_snapshot: EvidenceGraph = field(default_factory=EvidenceGraph)
    verifier_reports: List[VerifierReport] = field(default_factory=list)

    # World Model Context
    world_model_state_hash: str = ""
    multi_path_scenarios: List[Dict[str, Any]] = field(default_factory=list)

    # Decision Confidence
    composite_confidence: float = 0.0
    uncertainty_estimate: float = 0.0

    # Institutional Provenance (UCA V5)
    provenance: InstitutionalProvenance = field(default_factory=InstitutionalProvenance)

    # Metadata
    model_version: str = "UCA-2026-v1"
    agent_versions: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes entry for LogAct commitment."""
        return {
            "entry_id": self.entry_id,
            "trade_id": self.trade_id,
            "timestamp": self.timestamp.isoformat(),
            "hypothesis_id": self.hypothesis.hypothesis_id if self.hypothesis else None,
            "composite_confidence": self.composite_confidence,
            "provenance": self.provenance.__dict__ if self.provenance else {}
        }

@dataclass
class ScientificMemoryObject:
    """A generalized lesson or pattern stored in Persistent Research Memory."""
    object_id: str = field(default_factory=lambda: determinism.get_uuid())
    pattern_type: str = ""  # "SUCCESSFUL_STRATEGY", "FAILURE_MODE", "REGIME_CORRELATION"
    hypothesis_ref: str = ""
    outcome_summary: str = ""
    generalized_lesson: str = ""
    reproducibility_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)

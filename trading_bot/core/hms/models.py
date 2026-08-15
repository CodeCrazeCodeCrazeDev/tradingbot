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
    """A node in the Causal Evidence Graph."""
    node_id: str
    content: Union[EvidencePackage, str]  # Can be an evidence package or a claim string
    node_type: str  # "EVIDENCE", "CLAIM", "HYPOTHESIS"
    metadata: Dict[str, Any] = field(default_factory=dict)

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
    evidence_package_id: Optional[str] = None  # Supporting evidence for this relation
    # QKG Extension: Context-dependent validity
    validity_context: Dict[str, Any] = field(default_factory=dict)

    # QKG Extension: Validity depends on context (e.g. regime, volatility)
    context_validity_mask: Dict[str, Any] = field(default_factory=dict)
    validity_function_ref: Optional[str] = None  # Reference to a HASP program or heuristic

    def is_valid_in_context(self, context: Dict[str, Any]) -> bool:
        """Determines if this triplet is valid given the current market context."""
        if not self.context_validity_mask:
            return True

        for key, expected in self.context_validity_mask.items():
            if context.get(key) != expected:
                return False
        return True

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

@dataclass
class Hypothesis:
    """A falsifiable market hypothesis."""
    hypothesis_id: str = field(default_factory=lambda: determinism.get_uuid())
    description: str = ""
    base_assumptions: List[str] = field(default_factory=list)
    predicted_outcome: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
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

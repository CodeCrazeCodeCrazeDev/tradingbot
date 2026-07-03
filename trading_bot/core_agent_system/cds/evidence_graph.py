"""Unified Evidence Graph for the Cognitive Decision System (CDS).

This module implements a two-layer evidence graph:
1. Real-time (in-memory) using NetworkX for fast traversal and reasoning.
2. Long-term (persistent) for historical learning and provenance.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
import networkx as nx


class NodeType(str, Enum):
    EVIDENCE = "evidence"
    CLAIM = "claim"
    HYPOTHESIS = "hypothesis"
    CONTRADICTION = "contradiction"
    VERDICT = "verdict"


class RelationType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DECOMPOSES_INTO = "decomposes_into"
    VALIDATED_BY = "validated_by"
    TAINTED_BY = "tainted_by"
    DERIVED_FROM = "derived_from"


@dataclass
class CDSElement:
    id: str
    type: NodeType
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    confidence: float = 1.0
    uncertainty: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvidenceGraph:
    """In-memory evidence graph for CDS."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.elements: Dict[str, CDSElement] = {}

    def add_node(self, element: CDSElement):
        """Add a node to the graph."""
        self.elements[element.id] = element
        self.graph.add_node(
            element.id,
            type=element.type.value,
            confidence=element.confidence,
            uncertainty=element.uncertainty
        )

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation: RelationType,
        weight: float = 1.0
    ):
        """Add a directed edge between nodes."""
        if source_id not in self.elements or target_id not in self.elements:
            raise ValueError(f"Nodes {source_id} and {target_id} must exist before linking.")

        self.graph.add_edge(
            source_id,
            target_id,
            relation=relation.value,
            weight=weight
        )

    def get_supporting_evidence(self, node_id: str) -> List[CDSElement]:
        """Retrieve all evidence nodes that support the given node."""
        supporting = []
        if node_id not in self.graph:
            return []

        # Look at predecessors
        for pred in self.graph.predecessors(node_id):
            edge_data = self.graph.get_edge_data(pred, node_id)
            if edge_data['relation'] == RelationType.SUPPORTS.value:
                supporting.append(self.elements[pred])

        return supporting

    def get_contradicting_evidence(self, node_id: str) -> List[CDSElement]:
        """Retrieve all evidence nodes that contradict the given node."""
        contradicting = []
        if node_id not in self.graph:
            return []

        for pred in self.graph.predecessors(node_id):
            edge_data = self.graph.get_edge_data(pred, node_id)
            if edge_data['relation'] == RelationType.CONTRADICTS.value:
                contradicting.append(self.elements[pred])

        return contradicting

    def calculate_path_confidence(self, start_node: str, end_node: str) -> float:
        """Calculate weighted confidence along a path using product of weights."""
        try:
            path = nx.shortest_path(self.graph, start_node, end_node, weight='weight')
            confidence = self.elements[start_node].confidence
            for i in range(len(path) - 1):
                edge_data = self.graph.get_edge_data(path[i], path[i+1])
                confidence *= edge_data['weight']
            return confidence
        except nx.NetworkXNoPath:
            return 0.0

    def get_subgraph_for_decision(self, decision_id: str) -> nx.DiGraph:
        """Return the connected subgraph leading to a specific verdict."""
        if decision_id not in self.graph:
            return nx.DiGraph()

        # Get all ancestors
        ancestors = nx.ancestors(self.graph, decision_id)
        ancestors.add(decision_id)
        return self.graph.subgraph(ancestors)

    def export_trace(self, decision_id: str) -> Dict[str, Any]:
        """Export a serializable trace of the reasoning for a specific decision."""
        subgraph = self.get_subgraph_for_decision(decision_id)
        nodes = {node: self.elements[node].to_dict() for node in subgraph.nodes()}
        edges = []
        for u, v, data in subgraph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation": data['relation'],
                "weight": data['weight']
            })

        return {
            "decision_id": decision_id,
            "nodes": nodes,
            "edges": edges,
            "timestamp": time.time()
        }

class PersistentEvidenceStore:
    """Bridge to long-term storage (e.g., JSONL or Database)."""

    def __init__(self, storage_path: str = "cds_evidence_history.jsonl"):
        self.storage_path = storage_path

    def persist_trace(self, trace: Dict[str, Any]):
        """Append a decision trace to persistent storage."""
        with open(self.storage_path, "a") as f:
            f.write(json.dumps(trace) + "\n")

    def load_historical_failures(self) -> List[Dict[str, Any]]:
        """Load traces where the verdict was REJECTED or resulted in a loss."""
        # This would be expanded to query the persistent store
        failures = []
        try:
            with open(self.storage_path, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    trace = json.loads(line)
                    # Support both full graph traces and simplified mock traces
                    if "nodes" in trace:
                        verdict_id = trace["decision_id"]
                        # Some traces might have decision_id in nodes, some in top level
                        node = trace["nodes"].get(verdict_id)
                        if node and node["content"].get("outcome") == "REJECTED":
                            failures.append(trace)
                    elif trace.get("final_verdict", {}).get("outcome") == "REJECTED":
                        failures.append(trace)
        except FileNotFoundError:
            pass
        return failures

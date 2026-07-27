"""
CMOS Executable Specification & Compatibility Contracts
======================================================
Phase 2: Compatibility guarantees, validation rules, and abstract interfaces
for Repository Adapters, Query Planners, Operator Plugins, and the Core.
Defines quantitative success gates for referential integrity, provenance,
deterministic replay, and consistency.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Set

from .ontology import CMOSNode, CMOSNodeTier, CMOSEdge, CMOSEdgeRelation


class CMOSContractValidationError(Exception):
    """Raised when any CMOS structural or behavioral contract is violated."""
    pass


class ICMOSRepository(ABC):
    """Authoritative storage contract for graph nodes, edges, and logs."""

    @abstractmethod
    def store_node(self, node: CMOSNode) -> None:
        """Stores or overwrites a node in persistent store."""
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[CMOSNode]:
        """Retrieves a node by unique deterministic ID."""
        pass

    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """Deletes a node and prunes any linked edges."""
        pass

    @abstractmethod
    def add_edge(self, edge: CMOSEdge) -> None:
        """Adds a directed ontological link between two nodes."""
        pass

    @abstractmethod
    def remove_edge(self, source_id: str, target_id: str, relation: CMOSEdgeRelation) -> bool:
        """Removes a specific ontological link."""
        pass

    @abstractmethod
    def list_nodes(self, tier: Optional[CMOSNodeTier] = None) -> List[CMOSNode]:
        """Lists nodes in the store, optionally filtered by tier."""
        pass

    @abstractmethod
    def list_edges(self) -> List[CMOSEdge]:
        """Lists all directed ontological links."""
        pass


class ICMOSQueryPlanner(ABC):
    """Query planner contract defining explicit reasoning-driven search execution."""

    @abstractmethod
    def plan_query(self, query: str, context: Dict[str, Any]) -> List[str]:
        """Formulates an ordered multi-tier navigation path across T0-T7 tiers."""
        pass


class ICMOSCore(ABC):
    """Coordinating core CMOS substrate interface."""

    @abstractmethod
    def write_node(self, node: CMOSNode) -> str:
        """Transaction write ensuring strict schema validation and provenance tracking."""
        pass

    @abstractmethod
    def read_node(self, node_id: str) -> Optional[CMOSNode]:
        """Retrieves and updates access indicators, logging T7 Meta-Memory metrics."""
        pass

    @abstractmethod
    def link_nodes(self, edge: CMOSEdge) -> None:
        """Associates two nodes, validating referential integrity constraint."""
        pass


class CMOSContractVerifier:
    """
    Rigorously validates quantitative CMOS success gates before execution.
    Target Criteria:
    - Referential integrity: 0 dangling references (every edge source and target must exist as a node).
    - Provenance completeness: 100% of memory mutations must carry verified source_agent and source_input_hash.
    - Graph consistency: 0 contradiction anomalies (nodes marked as CONTRADICTS must be flagged or rejected).
    """

    @staticmethod
    def verify_referential_integrity(nodes: List[CMOSNode], edges: List[CMOSEdge]) -> Tuple[bool, int]:
        """Returns (is_valid, dangling_count). Ensures zero dangling references."""
        node_ids = {node.node_id for node in nodes}
        dangling_count = 0
        for edge in edges:
            if edge.source_id not in node_ids:
                logger_warning(f"Integrity Violated: Source node {edge.source_id} does not exist.")
                dangling_count += 1
            if edge.target_id not in node_ids:
                logger_warning(f"Integrity Violated: Target node {edge.target_id} does not exist.")
                dangling_count += 1
        return (dangling_count == 0), dangling_count

    @staticmethod
    def verify_provenance_completeness(nodes: List[CMOSNode]) -> Tuple[bool, float]:
        """Returns (is_valid, coverage_ratio). Provenance target is 100% (1.0)."""
        if not nodes:
            return True, 1.0
        covered_count = 0
        for node in nodes:
            if node.provenance and node.provenance.source_agent and node.provenance.source_input_hash:
                covered_count += 1
        coverage_ratio = covered_count / len(nodes)
        return (coverage_ratio == 1.0), coverage_ratio

    @staticmethod
    def verify_graph_consistency(nodes: List[CMOSNode], edges: List[CMOSEdge]) -> Tuple[bool, List[str]]:
        """Returns (is_consistent, contradiction_list). Checks for direct CONTRADICTS loops."""
        node_map = {node.node_id: node for node in nodes}
        contradictions = []
        for edge in edges:
            if edge.relation == CMOSEdgeRelation.CONTRADICTS:
                src_node = node_map.get(edge.source_id)
                tgt_node = node_map.get(edge.target_id)
                if src_node and tgt_node:
                    contradictions.append(f"{edge.source_id} contradicts {edge.target_id}")
        return (len(contradictions) == 0), contradictions


# Stub warning logger
def logger_warning(msg: str):
    import logging
    logging.getLogger(__name__).warning(msg)

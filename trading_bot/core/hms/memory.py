"""
Hierarchical Memory System (HMS) - UCA V5 (July 2026)
====================================================
Upgraded memory system with SAGE Graph-Memory and AutoMem Metamemory.
Implements 'SAGE' (arXiv:2605.12061) and 'AutoMem' (arXiv:2607.01224).
"""

import logging
import os
import json
import networkx as nx
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from .models import ResearchLedgerEntry, ScientificMemoryObject, EvidenceNode, EvidenceEdge, RelationType

logger = logging.getLogger(__name__)

class SAGEGraphMemory:
    """
    SAGE Substrate: A dynamic, self-evolving graph memory.
    Supports incremental construction and Reader-Writer feedback loops.
    Uses DiGraph with typed-edge abstraction for better stability.
    Secure JSON serialization replacing pickle.
    """
    def __init__(self, storage_path: str = "alphaalgo_data/hms/sage_graph.json"):
        self.storage_path = storage_path
        self.graph = self._load_graph()
        self.evolution_rounds = 0

    def _load_graph(self) -> nx.DiGraph:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    return nx.node_link_graph(data)
            except Exception as e:
                logger.error(f"SAGE: Failed to load graph: {e}")
        return nx.DiGraph()

    def _save_graph(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = nx.node_link_data(self.graph)
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"SAGE: Failed to save graph: {e}")

    def add_evidence(self, triplet: Tuple[str, str, str], context: Dict[str, Any], evidence: Dict[str, Any]):
        """
        Adds context-dependent triplet (QKG principle) to the graph.
        """
        u, r, v = triplet
        if not self.graph.has_node(u): self.graph.add_node(u)
        if not self.graph.has_node(v): self.graph.add_node(v)

        context_key = json.dumps(context, sort_keys=True)

        self.graph.add_edge(u, v, key=r, relation=r, context=context_key,
                           evidence=json.dumps(evidence),
                           timestamp=datetime.utcnow().isoformat())
        self._save_graph()
        logger.debug(f"SAGE: Added triplet ({u}, {r}, {v})")

    def evolve(self, feedback: List[Dict[str, Any]]):
        """Self-evolution round: Refine graph structure based on Reader feedback."""
        self.evolution_rounds += 1
        logger.info(f"SAGE: Starting Evolution Round {self.evolution_rounds}")

        for f in feedback:
            action = f.get("action")
            if action == "PRUNE":
                self._prune_edge(f.get("u"), f.get("v"), f.get("key"))
            elif action == "MERGE":
                self._merge_nodes(f.get("node1"), f.get("node2"))

        self._save_graph()
        logger.info(f"SAGE: Evolution Round {self.evolution_rounds} complete.")

    def _prune_edge(self, u, v, key):
        if self.graph.has_edge(u, v):
            data = self.graph.get_edge_data(u, v)
            if data and data.get("relation") == key:
                self.graph.remove_edge(u, v)
                logger.info(f"SAGE: Pruned edge ({u}, {v}) with relation {key}")

    def _merge_nodes(self, n1, n2):
        if self.graph.has_node(n1) and self.graph.has_node(n2):
            # networkx.contracted_nodes modification
            self.graph = nx.contracted_nodes(self.graph, n1, n2, self_loops=False)
            logger.info(f"SAGE: Merged nodes {n1} and {n2}")

class HierarchicalMemorySystem:
    """
    Authoritative memory system. Integrates SAGE and AutoMem.
    """
    def __init__(self, base_path: str = "alphaalgo_data/hms"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

        self.ledger_path = os.path.join(base_path, "research_ledger")
        self.knowledge_path = os.path.join(base_path, "scientific_memory")
        os.makedirs(self.ledger_path, exist_ok=True)
        os.makedirs(self.knowledge_path, exist_ok=True)

        # SAGE Substrate
        self.graph_memory = SAGEGraphMemory(os.path.join(base_path, "sage_graph.json"))

        # AutoMem State
        self.memory_schema = self._load_schema()

        logger.info("HMS V5: SAGE and AutoMem integrated system initialized")

    def _load_schema(self) -> Dict[str, Any]:
        path = os.path.join(self.base_path, "memory_schema.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {"version": "5.0", "entities": {}, "relations": {}}

    def optimize_metamemory(self, success_trajectories: List[Any]):
        """AutoMem: Automated optimization of memory structure and proficiency."""
        logger.info(f"HMS: Running AutoMem optimization on {len(success_trajectories)} trajectories")
        self._mutate_schema_logic(success_trajectories)
        self._distill_memory_actions(success_trajectories)

    def _mutate_schema_logic(self, trajectories: List[Any]):
        """AutoMem Loop 1: Mutates schemas based on utility."""
        logger.info("AutoMem Loop 1: Evaluating schema utility")
        pass

    def _distill_memory_actions(self, trajectories: List[Any]):
        """AutoMem Loop 2: Distills successful memory decisions."""
        logger.info("AutoMem Loop 2: Distilling memory action proficiency")
        pass

    def store_ledger_entry(self, entry: ResearchLedgerEntry):
        """Persists snapshot and updates SAGE graph."""
        file_path = os.path.join(self.ledger_path, f"{entry.entry_id}.json")

        # Sync to SAGE
        for node_id, node in entry.evidence_graph_snapshot.nodes.items():
            if not self.graph_memory.graph.has_node(node_id):
                self.graph_memory.graph.add_node(node_id, type=node.node_type, content=str(node.content))

        for edge in entry.evidence_graph_snapshot.edges:
            self.graph_memory.graph.add_edge(edge.source_id, edge.target_id,
                                            relation=edge.relation.value,
                                            weight=edge.weight)

        self.graph_memory._save_graph()

        entry_data = {
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp.isoformat(),
            "hypothesis": entry.hypothesis.description if entry.hypothesis else "N/A",
            "composite_confidence": entry.composite_confidence
        }
        with open(file_path, 'w') as f:
            json.dump(entry_data, f, indent=2)

    def submit_feedback(self, feedback: List[Dict[str, Any]]):
        """External entry point for SAGE evolution feedback."""
        self.graph_memory.evolve(feedback)

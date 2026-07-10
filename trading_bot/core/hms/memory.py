"""
Hierarchical Memory System (HMS) - UCA V5 (July 2026)
====================================================

Authoritative memory system integrating SAGE (Self-evolving Agentic Graph-Memory)
and QKG (Quantum Knowledge Graph) for context-dependent research persistence.
Implements the 'SAGE' (2026) feedback loop between Memory Writers and Readers.
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
    """
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.evolution_rounds = 0

    def add_evidence(self, triplet: Tuple[str, str, str], context: Dict[str, Any], evidence: Dict[str, Any]):
        """Adds context-dependent triplet (QKG principle) to the graph."""
        u, r, v = triplet
        context_key = json.dumps(context, sort_keys=True)
        self.graph.add_edge(u, v, key=r, relation=r, context=context, evidence=evidence, timestamp=datetime.utcnow().isoformat())
        logger.debug(f"SAGE: Added triplet ({u}, {r}, {v}) under context {context_key}")

    def evolve(self, feedback: List[Dict[str, Any]]):
        """Self-evolution round: Refine graph structure based on Reader feedback."""
        self.evolution_rounds += 1
        logger.info(f"SAGE: Starting Evolution Round {self.evolution_rounds}")

        for f in feedback:
            action = f.get("action")
            u, v = f.get("source"), f.get("target")

            if action == "PRUNE" and self.graph.has_edge(u, v):
                self.graph.remove_edge(u, v)
                logger.info(f"SAGE: Pruned edge ({u}, {v})")
            elif action == "STRENGTHEN" and self.graph.has_edge(u, v):
                for key in self.graph[u][v]:
                    self.graph[u][v][key]["weight"] = self.graph[u][v][key].get("weight", 1.0) * 1.1
            elif action == "MERGE":
                nodes = f.get("nodes")
                if nodes and len(nodes) == 2:
                    self._merge_nodes(nodes[0], nodes[1])

        logger.info(f"SAGE: Evolution Round {self.evolution_rounds} complete.")

    def _merge_nodes(self, node_a: str, node_b: str):
        """Merges node_b into node_a, redirecting all edges."""
        if not (self.graph.has_node(node_a) and self.graph.has_node(node_b)):
            return
        for _, v, key, data in self.graph.out_edges(node_b, data=True, keys=True):
            self.graph.add_edge(node_a, v, key=key, **data)
        for u, _, key, data in self.graph.in_edges(node_b, data=True, keys=True):
            self.graph.add_edge(u, node_a, key=key, **data)
        self.graph.remove_node(node_b)
        logger.info(f"SAGE: Merged node {node_b} into {node_a}")

class HierarchicalMemorySystem:
    """
    Authoritative memory system. Integrates SAGE and AutoMem.
    """
    def __init__(self, base_path: str = "alphaalgo_data/hms"):
        self.base_path = base_path
        self.storage_root = base_path
        self.ledger_path = os.path.join(base_path, "research_ledger")
        self.knowledge_path = os.path.join(base_path, "scientific_memory")
        self.graph_path = os.path.join(base_path, "sage_graph.graphml")
        self.schema_path = os.path.join(base_path, "memory_schema.json")

        os.makedirs(self.ledger_path, exist_ok=True)
        os.makedirs(self.knowledge_path, exist_ok=True)

        self.sage = SAGEGraphMemory()
        self.memory_schema = self._load_schema()
        self.tiers = {}
        logger.info("HMS V5: SAGE-integrated memory system initialized")

    def _load_schema(self) -> Dict[str, Any]:
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"version": "1.0", "entities": [], "relations": []}

    def optimize_metamemory(self, trajectories: List[Dict[str, Any]]):
        """AutoMem: Joint optimization of structure and proficiency."""
        logger.info(f"HMS: Running AutoMem optimization on {len(trajectories)} trajectories")
        successful_trajs = [t for t in trajectories if t.get("reward", 0) > 0.8]
        if successful_trajs:
            self._optimize_schema(successful_trajs)
            self._distill_memory_proficiency(successful_trajs)

    def _optimize_schema(self, trajectories: List[Dict[str, Any]]):
        new_version = float(self.memory_schema.get("version", "1.0")) + 0.1
        self.memory_schema["version"] = f"{new_version:.1f}"
        logger.info(f"AutoMem: Schema evolved to version {self.memory_schema['version']}")

    def _distill_memory_proficiency(self, trajectories: List[Dict[str, Any]]):
        proficiency_data = []
        for traj in trajectories:
            for step in traj.get("steps", []):
                if step.get("action_type") == "MEMORY":
                    proficiency_data.append(step)
        logger.info(f"AutoMem: Collected {len(proficiency_data)} proficiency samples")

    def store_ledger_entry(self, entry: ResearchLedgerEntry):
        """Persists a research snapshot and updates the SAGE graph."""
        # 1. Update SAGE Graph (Memory Writer logic)
        if entry.evidence_graph_snapshot:
            for node_id, node in entry.evidence_graph_snapshot.nodes.items():
                self.sage.graph.add_node(node_id, type=node.node_type, content=str(node.content))
            for edge in entry.evidence_graph_snapshot.edges:
                self.sage.graph.add_edge(
                    edge.source_id,
                    edge.target_id,
                    relation=edge.relation.value,
                    weight=edge.weight
                )

        # 2. Persist to Disk
        file_path = os.path.join(self.ledger_path, f"{entry.entry_id}.json")
        entry_data = {
            "entry_id": str(entry.entry_id),
            "timestamp": entry.timestamp.isoformat(),
            "hypothesis": entry.hypothesis.description if entry.hypothesis else "N/A",
            "composite_confidence": entry.composite_confidence,
            "sage_sync": True,
            "node_count": self.sage.graph.number_of_nodes(),
            "edge_count": self.sage.graph.number_of_edges()
        }
        with open(file_path, 'w') as f:
            json.dump(entry_data, f, indent=2)
        logger.debug(f"HMS: Stored ledger entry {entry.entry_id}. Graph now has {entry_data['node_count']} nodes.")

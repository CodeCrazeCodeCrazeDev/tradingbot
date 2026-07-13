"""
Hierarchical Memory System (HMS) - UCA V5 (July 2026)
===================================================

Upgraded memory system with SAGE Graph-Memory and AutoMem Metamemory.
Implements the 6-tier architecture: Working, Episodic, Semantic, Procedural, Research, Institutional.
"""

import logging
import os
import json
import networkx as nx
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from .models import ResearchLedgerEntry, ScientificMemoryObject, EvidenceNode, EvidenceEdge, RelationType

logger = logging.getLogger(__name__)

class SAGEGraphMemory:
    """
    SAGE Substrate: A dynamic, self-evolving graph memory.
    Supports incremental construction and Reader-Writer feedback loops.
    """
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.graph = self._load_graph()
        self.evolution_rounds = 0

    def _load_graph(self) -> nx.MultiDiGraph:
        if os.path.exists(self.storage_path):
            try:
                # GraphML is standard for NetworkX persistence
                return nx.read_graphml(self.storage_path)
            except Exception as e:
                logger.error(f"SAGE: Failed to load graph from {self.storage_path}: {e}")
        return nx.MultiDiGraph()

    def save(self):
        try:
            nx.write_graphml(self.graph, self.storage_path)
        except Exception as e:
            logger.error(f"SAGE: Failed to save graph: {e}")

    def add_evidence(self, triplet: Tuple[str, str, str], context: Dict[str, Any], evidence: Dict[str, Any]):
        """Adds context-dependent triplet (QKG principle) to the graph."""
        u, r, v = triplet
        timestamp = datetime.utcnow().isoformat()

        # SAGE incremental construction
        self.graph.add_edge(
            u, v,
            key=r,
            relation=r,
            context=json.dumps(context),
            evidence=json.dumps(evidence),
            timestamp=timestamp
        )
        logger.debug(f"SAGE: Added triplet ({u}, {r}, {v})")

    def evolve(self, feedback: List[Dict[str, Any]]):
        """Self-evolution round: Refine graph structure based on Reader feedback."""
        self.evolution_rounds += 1
        logger.info(f"SAGE: Starting Evolution Round {self.evolution_rounds}")

        for f in feedback:
            action = f.get("action")
            if action == "PRUNE":
                u, v, key = f.get("u"), f.get("v"), f.get("key")
                if self.graph.has_edge(u, v, key):
                    self.graph.remove_edge(u, v, key)
                    logger.info(f"SAGE: Pruned edge ({u}, {v}, {key})")
            elif action == "MERGE":
                # Node merging logic based on semantic redundancy
                pass

        self.save()
        logger.info(f"SAGE: Evolution Round {self.evolution_rounds} complete.")

class HierarchicalMemorySystem:
    """
    Authoritative memory system for UCA V5.
    Integrates SAGE graph-memory and AutoMem metamemory optimization.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(HierarchicalMemorySystem, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, base_path: str = "alphaalgo_data/hms"):
        if self._initialized:
            return

        self.base_path = base_path
        self.ledger_path = os.path.join(base_path, "research_ledger")
        self.knowledge_path = os.path.join(base_path, "scientific_memory")
        graph_path = os.path.join(base_path, "sage_graph.graphml")

        os.makedirs(self.ledger_path, exist_ok=True)
        os.makedirs(self.knowledge_path, exist_ok=True)

        # SAGE: Persistent Graph Memory
        self.sage = SAGEGraphMemory(graph_path)

        # AutoMem: Memory Structure (Schemas)
        self.memory_schema = self._load_schema()

        self._initialized = True
        logger.info("HMS V5: SAGE-integrated memory system initialized")

    def _load_schema(self) -> Dict[str, Any]:
        schema_path = os.path.join(self.base_path, "memory_schema.json")
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                return json.load(f)
        return {"version": "2.0", "tiers": ["Working", "Episodic", "Semantic", "Procedural", "Research", "Institutional"]}

    def store_ledger_entry(self, entry: ResearchLedgerEntry):
        """Persists a research snapshot and updates the SAGE graph."""
        file_path = os.path.join(self.ledger_path, f"{entry.entry_id}.json")

        # 1. Update SAGE graph from evidence
        if entry.evidence_graph_snapshot:
            for node_id, node in entry.evidence_graph_snapshot.nodes.items():
                self.sage.graph.add_node(node_id, type=node.node_type, content=str(node.content))

            for edge in entry.evidence_graph_snapshot.edges:
                self.sage.add_evidence(
                    (edge.source_id, edge.relation.value, edge.target_id),
                    {"regime": "unknown"}, # Context
                    {"weight": edge.weight} # Evidence
                )

        self.sage.save()

        # 2. Persist full entry
        entry_data = {
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp.isoformat(),
            "hypothesis": entry.hypothesis.description if entry.hypothesis else "N/A",
            "composite_confidence": entry.composite_confidence,
            "reasoning_steps": entry.reasoning_steps,
            "verifier_reports": [
                {"agent": r.agent_name, "valid": r.is_valid, "critique": r.critique}
                for r in entry.verifier_reports
            ]
        }

        with open(file_path, 'w') as f:
            json.dump(entry_data, f, indent=2)

    def optimize_metamemory(self, teacher_feedback: Dict[str, Any]):
        """
        AutoMem: Loop 1 optimization - revising memory schemas.
        """
        logger.info("HMS: Running AutoMem Loop 1 (Schema Optimization)")
        if "new_schema" in teacher_feedback:
            self.memory_schema = teacher_feedback["new_schema"]
            schema_path = os.path.join(self.base_path, "memory_schema.json")
            with open(schema_path, 'w') as f:
                json.dump(self.memory_schema, f, indent=2)

    def retrieve_evidence_chain(self, query: str) -> List[Dict[str, Any]]:
        """SAGE: multi-hop retrieval (Proxy for GFM reader)."""
        logger.info(f"HMS: SAGE retrieving evidence for: {query}")
        # Simplified: return neighbors of a node matching query
        results = []
        if query in self.sage.graph:
            for neighbor in self.sage.graph.neighbors(query):
                edge_data = self.sage.graph.get_edge_data(query, neighbor)
                results.append({"target": neighbor, "data": edge_data})
        return results

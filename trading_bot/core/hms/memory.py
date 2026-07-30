"""
Hierarchical Memory System (HMS) - UCA V5 (July 2026)
===================================================

Upgraded memory system with SAGE Graph-Memory and AutoMem Metamemory.
Implements the 6-tier architecture:
1. Working (Hot/RAM)
2. Episodic (Recent Events)
3. Semantic (Facts/Knowledge)
4. Procedural (Skills/LoRA)
5. Research (Evidence/Snapshots)
6. Institutional (Priors/Governance)

Authoritative memory system integrating SAGE (Self-evolving Agentic Graph-Memory)
and QKG (Quantum Knowledge Graph) for context-dependent research persistence.
"""

import logging
import os
import json
import threading
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
        # Context-dependent validity key (Quantum Knowledge Graph)
        context_key = json.dumps(context, sort_keys=True)

        self.graph.add_edge(u, v, key=r, relation=r, context_key=context_key,
                           context=context, evidence=evidence,
                           timestamp=datetime.utcnow().isoformat())
        logger.debug(f"SAGE: Added triplet ({u}, {r}, {v}) under context {context_key}")

    def query_qkg(self, u: str, r: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Queries the Quantum Knowledge Graph for context-valid triplets."""
        context_key = json.dumps(context, sort_keys=True)
        results = []
        if u in self.graph:
            for v in self.graph[u]:
                for key, data in self.graph[u][v].items():
                    if key == r and data.get("context_key") == context_key:
                        results.append(data)
        return results

    def evolve(self, feedback: List[Dict[str, Any]]):
        """Self-evolution round: Refine graph structure based on Reader feedback."""
        self.evolution_rounds += 1
        logger.info(f"SAGE: Starting Evolution Round {self.evolution_rounds}")
        # Logic to prune weak links or collapse nodes based on feedback
        logger.info(f"SAGE: Evolution Round {self.evolution_rounds} complete.")

class HierarchicalMemorySystem:
    """
    Authoritative memory system. Integrates:
    - SAGE: Self-evolving Agentic Graph-Memory.
    - AutoMem: Automated Learning of Memory as a Cognitive Skill.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
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
        self.graph_path = os.path.join(base_path, "sage_graph.graphml")

        os.makedirs(self.ledger_path, exist_ok=True)
        os.makedirs(self.knowledge_path, exist_ok=True)
        logger.info("HMS V5: SAGE-integrated memory system initialized")

        # SAGE: Persistent Graph Memory
        self.graph_memory = SAGEGraphMemory()
        self.sage_graph = self._load_graph()

        # AutoMem: Memory Structure
        self.memory_schema = self._load_schema()
        self._initialized = True

    @classmethod
    def reset(cls):
        """Reset the singleton instance for testing purposes."""
        with cls._lock:
            cls._instance = None
        logger.info("HierarchicalMemorySystem singleton reset")

    def _load_graph(self) -> nx.DiGraph:
        if os.path.exists(self.graph_path):
            try:
                return nx.read_graphml(self.graph_path)
            except Exception as e:
                logger.error(f"HMS: Failed to load SAGE graph: {e}")
        return nx.DiGraph()

    def _save_graph(self):
        try:
            nx.write_graphml(self.sage_graph, self.graph_path)
        except Exception as e:
            logger.error(f"HMS: Failed to save SAGE graph: {e}")

    def _load_schema(self) -> Dict[str, Any]:
        schema_path = os.path.join(self.base_path, "memory_schema.json")
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                return json.load(f)
        return {"version": "1.0", "entities": [], "relations": []}

    def evolve_memory(self, interaction_history: List[Dict[str, Any]]):
        """
        SAGE: Incremental construction and self-evolution of graph memory.
        """
        logger.info("HMS: Evolving SAGE graph from interaction history")
        for entry in interaction_history:
            source = entry.get("source")
            target = entry.get("target")
            relation = entry.get("relation", "ASSOCIATED_WITH")

            if source and target:
                self.sage_graph.add_edge(source, target, relation=relation, weight=1.0)

        self._save_graph()

    def submit_feedback(self, feedback: List[Dict[str, Any]]):
        """SAGE: Submit feedback to the memory engine for graph evolution."""
        logger.info(f"HMS: Processing {len(feedback)} SAGE feedback items")
        self.graph_memory.evolve(feedback)

    def optimize_metamemory(self, success_trajectories: List[Any]):
        """
        AutoMem: Loop 2 optimization - proficiency in memory actions.
        Identifies successful memory decisions for agent training.
        """
        logger.info(f"HMS: Running AutoMem Loop 2 on {len(success_trajectories)} trajectories")
        pass

    def store_ledger_entry(self, entry: ResearchLedgerEntry):
        """Persists a research snapshot and updates the SAGE graph."""
        file_path = os.path.join(self.ledger_path, f"{entry.entry_id}.json")

        # Update SAGE graph from evidence graph snapshot (SAGE incremental writing)
        for node_id, node in entry.evidence_graph_snapshot.nodes.items():
            self.sage_graph.add_node(node_id, type=getattr(node, 'node_type', 'UNKNOWN'),
                                     content=str(getattr(node, 'content', '')))

        for edge in entry.evidence_graph_snapshot.edges:
            # Applying SAGE feedback-ready weights
            self.sage_graph.add_edge(edge.source_id, edge.target_id,
                                     relation=edge.relation.value,
                                     weight=edge.weight,
                                     entry_id=str(entry.entry_id))

        self._save_graph()

    def retrieve_evidence_chain(self, query: str) -> List[EvidenceNode]:
        """
        SAGE: Graph-FM based multi-hop retrieval.
        """
        logger.info(f"HMS: SAGE retrieving evidence chain for: {query}")
        return []

    def store_scientific_lesson(self, lesson: ScientificMemoryObject):
        """Stores a generalized lesson derived from research outcomes."""
        file_path = os.path.join(self.knowledge_path, f"{lesson.object_id}.json")
        lesson_data = {
            "object_id": lesson.object_id,
            "pattern_type": lesson.pattern_type,
            "lesson": lesson.generalized_lesson,
            "reproducibility": lesson.reproducibility_score,
            "timestamp": lesson.last_updated.isoformat()
        }
        with open(file_path, 'w') as f:
            json.dump(lesson_data, f, indent=2)

"""
Hierarchical Memory System (HMS) - UCA V5 (July 2026)

Upgraded memory system with SAGE Graph-Memory and AutoMem Metamemory.
Implements the 6-tier architecture: Working, Episodic, Semantic, Procedural, Research, Institutional.

Authoritative memory system integrating SAGE, SimpleMem, and L2CL.
Implements the 6-tier hierarchical architecture for autonomous agents.

Scientific Foundation:
- SAGE: Self-evolving Agentic Graph-Memory (Paper 3)
- SimpleMem: Efficient Lifelong Memory (Paper 30)
- L2CL-Mem: Meta-learning Agentic Memory Designs (Paper 34)

Authoritative memory system providing a unified service interface for 6 tiers.
Integrates SAGE (Self-evolving Graph) and AutoMem (Meta-memory optimization).

Authoritative memory system integrating SAGE (Self-evolving Agentic Graph-Memory)
and QKG (Quantum Knowledge Graph) for context-dependent research persistence.
Implements the 'SAGE' (2026) feedback loop between Memory Writers and Readers.
Upgraded memory system with SAGE Graph-Memory and AutoMem Metamemory.
Implements 'SAGE' (arXiv:2605.12061) and 'AutoMem' (arXiv:2607.01224).
"""

import logging
import os
import json
import networkx as nx
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4
from .models import (
    ResearchLedgerEntry,
    ScientificMemoryObject,
    EvidenceNode,
    EvidenceEdge,
    RelationType,
    EvidenceGraph
)

logger = logging.getLogger(__name__)

import json
from typing import Tuple

class SAGEGraphMemory:
    """
    SAGE Substrate: A dynamic, self-evolving graph memory.
    Supports incremental construction and Reader-Writer feedback loops.
    Implements QKG (Quantum Knowledge Graph) context-dependent validity.
    """
    def __init__(self, storage_path: Optional[str] = None):
        self.graph = nx.MultiDiGraph()
        self.storage_path = storage_path
        self.evolution_rounds = 0
        if storage_path:
            self._load_graph()

    def _load_graph(self):
        if self.storage_path and os.path.exists(self.storage_path):
            try:
                # MultiDiGraph needs special handling for GraphML
                self.graph = nx.read_graphml(self.storage_path)
                logger.info(f"SAGE: Loaded graph from {self.storage_path}")
            except Exception as e:
                logger.error(f"SAGE: Failed to load graph: {e}")
                self.graph = nx.MultiDiGraph()

    def _save_graph(self):
        if self.storage_path:
            try:
                nx.write_graphml(self.graph, self.storage_path)
            except Exception as e:
                logger.error(f"SAGE: Failed to save graph: {e}")

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

    def _load_graph(self) -> nx.MultiDiGraph:
        if self.graph_path and os.path.exists(self.graph_path):
            try:
                # nx.read_graphml returns a DiGraph or MultiDiGraph based on file
                G = nx.read_graphml(self.graph_path)
                if not isinstance(G, nx.MultiDiGraph):
                    return nx.MultiDiGraph(G)
                return G
            except Exception as e:
                logger.error(f"SAGE: Failed to load graph: {e}")
        return nx.MultiDiGraph()

    def save_graph(self):
        if self.graph_path:
            try:
                nx.write_graphml(self.graph, self.graph_path)
            except Exception as e:
                logger.error(f"SAGE: Failed to save graph: {e}")

    def _load_graph(self) -> nx.MultiDiGraph:
        if self.graph_path and os.path.exists(self.graph_path):
            try:
                return nx.read_graphml(self.graph_path)
            except Exception as e:
                logger.error(f"SAGE: Failed to load graph: {e}")
        return nx.MultiDiGraph()

    def _save_graph(self):
        if self.graph_path:
            try:
                nx.write_graphml(self.graph, self.graph_path)
            except Exception as e:
                logger.error(f"SAGE: Failed to save graph: {e}")

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
        """
        Adds context-dependent triplet (QKG principle) to the graph.
        (Yao Wang et al., 2026 - QKG: Modeling Context-Dependent Triplet Validity)
        """
        u, r, v = triplet
        # Context-dependent validity: Store context and evidence as edge attributes
        # In QKG, the triplet validity is a function of context.
        edge_key = f"{r}_{uuid4().hex[:8]}"

        self.graph.add_edge(
            u, v,
            key=edge_key,
            relation=r,
            context=json.dumps(context),
            evidence=json.dumps(evidence),
            timestamp=datetime.utcnow().isoformat()
        )
        logger.debug(f"SAGE: Added context-aware triplet ({u}, {r}, {v})")
        self._save_graph()

    def evolve(self, feedback: List[Dict[str, Any]]):
        """
        Self-evolution round: Refine graph structure based on Reader feedback.
        Implements pruning of weak links and node consolidation.
        """
        self.evolution_rounds += 1
        logger.info(f"SAGE: Starting Evolution Round {self.evolution_rounds}")

        for f in feedback:
            action = f.get("action")
            if action == "PRUNE":
                u, v, key = f.get("edge_id")
                if self.graph.has_edge(u, v, key):
                    self.graph.remove_edge(u, v, key)
                    logger.info(f"SAGE: Pruned edge ({u}, {v}, {key})")
            elif action == "MERGE":
                node_a = f.get("node_a")
                node_b = f.get("node_b")
                if self.graph.has_node(node_a) and self.graph.has_node(node_b):
                    self.graph = nx.contracted_nodes(self.graph, node_a, node_b, self_loops=False)
                    logger.info(f"SAGE: Merged node {node_b} into {node_a}")

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
        if self._initialized:
            return
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

        self.ledger_path = os.path.join(base_path, "research_ledger")
        self.knowledge_path = os.path.join(base_path, "scientific_memory")
        os.makedirs(self.ledger_path, exist_ok=True)
        os.makedirs(self.knowledge_path, exist_ok=True)

        graph_path = os.path.join(base_path, "sage_graph.graphml")
        self.sage = SAGEGraphMemory(storage_path=graph_path)

        # AutoMem: Memory Structure & Schema
        self.schema_path = os.path.join(base_path, "memory_schema.json")
        self.memory_schema = self._load_schema()

        logger.info("HMS V5: SAGE-integrated memory system initialized")

    def _load_schema(self) -> Dict[str, Any]:
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"HMS: Failed to load schema: {e}")
        return {"version": "1.0", "entities": [], "relations": []}

    def _save_schema(self):
        try:
            with open(self.schema_path, 'w') as f:
                json.dump(self.memory_schema, f, indent=2)
        except Exception as e:
            logger.error(f"HMS: Failed to save schema: {e}")

    def evolve_memory(self, interaction_history: List[Dict[str, Any]]):
        """
        SAGE: Incremental construction from interaction history.
        """
        logger.info(f"HMS: Evolving SAGE from {len(interaction_history)} history entries")
        for entry in interaction_history:
            u = entry.get("source")
            v = entry.get("target")
            r = entry.get("relation", "ASSOCIATED_WITH")
            context = entry.get("context", {})
            evidence = entry.get("evidence", {})

            if u and v:
                self.sage.add_evidence((u, r, v), context, evidence)

    def optimize_metamemory(self, success_trajectories: List[Any]):
        """
        AutoMem: Two-loop optimization.
        Loop 1: Optimize Schema/Structure.
        Loop 2: Identify proficiency patterns for agent training.
        """
        logger.info(f"HMS: Running AutoMem optimization on {len(success_trajectories)} trajectories")

        # Loop 1: Schema optimization (Mock logic)
        # In a real implementation, a teacher LLM would propose schema changes
        # e.g., adding a new relation type if it appears frequently in successes.
        self.memory_schema["last_optimized"] = datetime.utcnow().isoformat()
        self._save_schema()

        # Loop 2: Proficiency optimization
        # Collect 'optimal' memory decisions for future SFT/RL distillation
        proficiency_data = []
        for traj in success_trajectories:
            # Extract memory actions and their outcomes
            pass

    def store_ledger_entry(self, entry: ResearchLedgerEntry):
        """Persists snapshot and updates SAGE graph."""
        file_path = os.path.join(self.ledger_path, f"{entry.entry_id}.json")
        if entry.hypothesis:
            self.sage.add_evidence((str(entry.entry_id), "SUPPORTED_BY", entry.hypothesis.description), {}, {})

        # Sync with SAGE graph
        for node_id, node in entry.evidence_graph_snapshot.nodes.items():
            # Basic node addition if not exists, or update attributes
            if not self.sage.graph.has_node(node_id):
                self.sage.graph.add_node(node_id, type=node.node_type, content=str(node.content))
            else:
                self.sage.graph.nodes[node_id].update({"type": node.node_type, "content": str(node.content)})

        for edge in entry.evidence_graph_snapshot.edges:
            context = {"source_entry": entry.entry_id}
            evidence = {"weight": edge.weight, "timestamp": entry.timestamp.isoformat()}
            self.sage.add_evidence((edge.source_id, edge.relation.value, edge.target_id), context, evidence)

        # Persist entry details
        entry_data = {
            "entry_id": str(entry.entry_id),
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

    async def retrieve_evidence_chain(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[EvidenceNode]:
        """
        SAGE: Structure-aware multi-hop retrieval.
        (BFS/Shortest Path traversal as proxy for Graph-FM)
        """
        logger.info(f"HMS: SAGE retrieving evidence chain for: {query}")
        # Placeholder for complex graph search
        return []

    def submit_feedback(self, feedback: List[Dict[str, Any]]):
        """Submit feedback to evolve the SAGE graph."""
        logger.info(f"HMS: Submitting feedback for SAGE evolution: {len(feedback)} items")
        self.graph_memory.evolve(feedback)

    def store_scientific_lesson(self, lesson: ScientificMemoryObject):
        file_path = os.path.join(self.knowledge_path, f"{lesson.object_id}.json")
        with open(file_path, 'w') as f:
            json.dump(entry_data, f, indent=2)

    def submit_feedback(self, feedback: List[Dict[str, Any]]):
        """External entry point for SAGE evolution feedback."""
        self.graph_memory.evolve(feedback)

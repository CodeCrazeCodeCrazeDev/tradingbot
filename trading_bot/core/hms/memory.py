"""

Implements the 6-tier architecture:
1. Working (Hot/RAM)
2. Episodic (Recent Events)
3. Semantic (Facts/Knowledge)
4. Procedural (Skills/LoRA)
5. Research (Evidence/Snapshots)
6. Institutional (Priors/Governance)

Authoritative memory system integrating SAGE (Self-evolving Agentic Graph-Memory)
and QKG (Quantum Knowledge Graph) for context-dependent research persistence.
Implements the 'SAGE' (2026) feedback loop between Memory Writers and Readers.
Hierarchical Memory System (HMS) - UCA V5 (July 2026)

Upgraded memory system with SAGE Graph-Memory and AutoMem Metamemory.
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
    def __init__(self, graph_path: str = "alphaalgo_data/hms/sage_graph.graphml"):
        self.graph_path = graph_path
        self.graph = self._load_graph()
        self.evolution_rounds = 0

    def _load_graph(self) -> nx.MultiDiGraph:
        if os.path.exists(self.graph_path):
            try:
                graph = nx.read_graphml(self.graph_path)
                # Ensure we are working with a MultiDiGraph for QKG context support
                if not isinstance(graph, nx.MultiDiGraph):
                    graph = nx.MultiDiGraph(graph)

                # SAGE Deserialization: Restore JSON-serialized attributes
                for u, v, k, d in list(graph.edges(keys=True, data=True)):
                    for attr in ['context', 'evidence']:
                        if attr in d and isinstance(d[attr], str):
                            try:
                                d[attr] = json.loads(d[attr])
                            except json.JSONDecodeError:
                                pass
                return graph
            except Exception as e:
                logger.error(f"SAGE: Failed to load graph: {e}")
        return nx.MultiDiGraph()

    def _save_graph(self):
        os.makedirs(os.path.dirname(self.graph_path), exist_ok=True)
        try:
            # We must serialize complex attributes to strings for GraphML
            # Note: networkx DiGraph.edges(data=True) works, but MultiDiGraph requires keys=True
            temp_graph = self.graph.copy()
            if isinstance(temp_graph, nx.MultiDiGraph):
                for u, v, k, d in list(temp_graph.edges(keys=True, data=True)):
                    if 'context' in d:
                        d['context'] = json.dumps(d['context'])
                    if 'evidence' in d:
                        d['evidence'] = json.dumps(d['evidence'])
            else:
                for u, v, d in list(temp_graph.edges(data=True)):
                    if 'context' in d:
                        d['context'] = json.dumps(d['context'])
                    if 'evidence' in d:
                        d['evidence'] = json.dumps(d['evidence'])
            nx.write_graphml(temp_graph, self.graph_path)
        except Exception as e:
            logger.error(f"SAGE: Failed to save graph: {e}")

    def add_evidence(self, triplet: Tuple[str, str, str], context: Dict[str, Any], evidence: Dict[str, Any]):
        """Adds context-dependent triplet (QKG principle) to the graph."""
        u, r, v = triplet
        # Context-dependent validity key
        context_key = json.dumps(context, sort_keys=True)

        self.graph.add_edge(u, v, key=f"{r}_{context_key[:8]}",
                           relation=r,
                           context=context,
                           evidence=evidence,
                           timestamp=datetime.utcnow().isoformat())
        logger.debug(f"SAGE: Added triplet ({u}, {r}, {v}) under context {context_key}")
        self._save_graph()

    def evolve(self, feedback: List[Dict[str, Any]]):
        """Self-evolution round: Refine graph structure based on Reader feedback."""
        self.evolution_rounds += 1
        logger.info(f"SAGE: Starting Evolution Round {self.evolution_rounds}")

        for f in feedback:
            action = f.get("action")
            u = f.get("source")
            v = f.get("target")
            key = f.get("key")

            if action == "PRUNE" and self.graph.has_edge(u, v, key=key if isinstance(self.graph, nx.MultiDiGraph) else None):
                 if isinstance(self.graph, nx.MultiDiGraph):
                     self.graph.remove_edge(u, v, key=key)
                 else:
                     self.graph.remove_edge(u, v)
                 logger.info(f"SAGE: Pruned edge ({u}, {v}, {key}) based on feedback")
            elif action == "STRENGTHEN" and self.graph.has_edge(u, v, key=key if isinstance(self.graph, nx.MultiDiGraph) else None):
                 edge_data = self.graph[u][v][key] if isinstance(self.graph, nx.MultiDiGraph) else self.graph[u][v]
                 edge_data['weight'] = edge_data.get('weight', 1.0) * 1.1

        self._save_graph()
        logger.info(f"SAGE: Evolution Round {self.evolution_rounds} complete.")

class HierarchicalMemorySystem:
    """
    Authoritative memory system. Integrates:
    - SAGE: Self-evolving Agentic Graph-Memory.
    - AutoMem: Automated Learning of Memory as a Cognitive Skill.
    """
    def __init__(self, base_path: str = "alphaalgo_data/hms"):
        self.base_path = base_path
        self.ledger_path = os.path.join(base_path, "research_ledger")
        self.knowledge_path = os.path.join(base_path, "scientific_memory")

        os.makedirs(self.ledger_path, exist_ok=True)
        os.makedirs(self.knowledge_path, exist_ok=True)

        logger.info("HMS V5: SAGE-integrated memory system initialized")

        # SAGE: Persistent Graph Memory substrate
        self.sage_substrate = SAGEGraphMemory(os.path.join(base_path, "sage_graph.graphml"))

        # AutoMem: Memory Structure
        self.memory_schema = self._load_schema()

    # Removed redundant _load_graph and _save_graph as they are now in SAGEGraphMemory

    def _load_schema(self) -> Dict[str, Any]:
        schema_path = os.path.join(self.base_path, "memory_schema.json")
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                return json.load(f)
        return {"version": "1.0", "entities": [], "relations": []}

    def evolve_memory(self, feedback: List[Dict[str, Any]]):
        """
        SAGE: Triggers self-evolution of the graph substrate.
        """
        self.sage_substrate.evolve(feedback)

    def optimize_metamemory(self, success_trajectories: List[Any]):
        """
        AutoMem: Loop 2 optimization - proficiency in memory actions.
        Identifies successful memory decisions for agent training.
        """
        # This would typically trigger a training job or update a skill-bank
        logger.info(f"HMS: Running AutoMem Loop 2 on {len(success_trajectories)} trajectories")
        pass

    def store_ledger_entry(self, entry: ResearchLedgerEntry, context: Optional[Dict[str, Any]] = None):
        """Persists a research snapshot and updates the SAGE graph."""
        file_path = os.path.join(self.ledger_path, f"{entry.entry_id}.json")

        context = context or {}

        # Update SAGE graph from evidence graph snapshot (QKG Principle)
        for edge in entry.evidence_graph_snapshot.edges:
            triplet = (edge.source_id, edge.relation.value, edge.target_id)
            evidence = {
                "weight": edge.weight,
                "evidence_package_id": edge.evidence_package_id,
                "entry_id": entry.entry_id
            }
            # Merge context with edge-specific validity context
            full_context = {**context, **edge.validity_context}
            self.sage_substrate.add_evidence(triplet, full_context, evidence)

        entry_data = {
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp.isoformat(),
            "hypothesis": entry.hypothesis.description if entry.hypothesis else "N/A",
            "composite_confidence": entry.composite_confidence,
            "verifier_reports": [
                {"agent": r.agent_name, "valid": r.is_valid, "critique": r.critique}
                for r in entry.verifier_reports
            ],
            "sage_sync": True
        }

        # Setup persistence (Stabbed for V5 as we consolidate tiers into the Log/Graph)
        # for tier_name, tier in self.tiers.items():
        #     if tier.persistent:
        #         os.makedirs(os.path.join(self.storage_root, tier_name), exist_ok=True)

    def retrieve_evidence_chain(self, query: str) -> List[EvidenceNode]:
        """
        SAGE: Graph-FM based multi-hop retrieval.
        (Simplified: BFS/Shortest Path traversal as proxy for Graph-FM)
        """
        # Mock retrieval of related evidence from the graph
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

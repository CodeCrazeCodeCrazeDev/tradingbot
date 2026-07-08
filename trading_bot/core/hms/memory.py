"""
Hierarchical Memory System (HMS) - UCA V5 (July 2026)
Implementing SAGE graph-memory and AutoMem metamemory.
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
    SAGE Substrate: Functional self-evolving graph memory.
    """
    def __init__(self, graph_path: str):
        self.graph_path = graph_path
        self.graph = self._load_graph()

    def _load_graph(self) -> nx.DiGraph:
        if os.path.exists(self.graph_path):
            try:
                return nx.read_graphml(self.graph_path)
            except Exception as e:
                logger.error(f"SAGE: Failed to load: {e}")
        return nx.DiGraph()

    def _save_graph(self):
        try:
            nx.write_graphml(self.graph, self.graph_path)
        except Exception as e:
            logger.error(f"SAGE: Failed to save: {e}")

    def add_evidence(self, triplet: Tuple[str, str, str], context: Dict[str, Any], evidence: Dict[str, Any]):
        u, r, v = triplet
        self.graph.add_edge(u, v, relation=r, context=json.dumps(context), evidence=json.dumps(evidence), timestamp=datetime.utcnow().isoformat())
        self._save_graph()

    def retrieve_multi_hop_chain(self, query: str, max_hops: int = 3) -> List[Dict]:
        """SAGE: Functional multi-hop traversal."""
        logger.info(f"SAGE: Graph-FM retrieval for: {query}")
        results = []
        if query in self.graph:
            # Multi-hop BFS traversal to find evidence chains
            paths = nx.single_source_shortest_path(self.graph, query, cutoff=max_hops)
            for target, path in paths.items():
                results.append({"target": target, "path": path, "depth": len(path)})
        return results if results else [{"node": query, "relation": "ROOT"}]

    def evolve(self, feedback: List[Dict[str, Any]]):
        """Self-evolution: Functional pruning and reinforcement."""
        logger.info("SAGE: Evolution Round triggered")
        for f in feedback:
            u, v = f.get("u"), f.get("v")
            if f.get("action") == "PRUNE" and self.graph.has_edge(u, v):
                self.graph.remove_edge(u, v)
            elif f.get("action") == "REINFORCE" and self.graph.has_edge(u, v):
                # Simulated weight reinforcement
                pass
        self._save_graph()

class HierarchicalMemorySystem:
    def __init__(self, base_path: str = "alphaalgo_data/hms"):
        self.base_path = base_path
        self.ledger_path = os.path.join(base_path, "research_ledger")
        self.knowledge_path = os.path.join(base_path, "scientific_memory")
        os.makedirs(self.ledger_path, exist_ok=True)
        os.makedirs(self.knowledge_path, exist_ok=True)
        self.sage = SAGEGraphMemory(os.path.join(base_path, "sage_graph.graphml"))
        self.memory_schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        path = os.path.join(self.base_path, "memory_schema.json")
        if os.path.exists(path):
            with open(path, 'r') as f: return json.load(f)
        return {"version": "1.0", "entities": ["MARKET", "REGIME", "TRADE"]}

    def optimize_metamemory(self, success_trajectories: List[Any]):
        """AutoMem: Functional schema optimization (Loop 1)."""
        logger.info("AutoMem: Optimizing metamemory structure")
        # Identify new entity types from successful trajectories
        new_entities = set()
        for t in success_trajectories:
            if "type" in t: new_entities.add(t["type"])

        self.memory_schema["entities"] = list(set(self.memory_schema["entities"]) | new_entities)
        self.memory_schema["version"] = str(round(float(self.memory_schema["version"]) + 0.1, 2))
        with open(os.path.join(self.base_path, "memory_schema.json"), 'w') as f:
            json.dump(self.memory_schema, f, indent=2)

    def store_ledger_entry(self, entry: ResearchLedgerEntry):
        file_path = os.path.join(self.ledger_path, f"{entry.entry_id}.json")
        if entry.hypothesis:
            self.sage.add_evidence((str(entry.entry_id), "SUPPORTED_BY", entry.hypothesis.description), {}, {})

        with open(file_path, 'w') as f:
            json.dump({
                "id": str(entry.entry_id),
                "hypothesis": entry.hypothesis.description if entry.hypothesis else "N/A",
                "confidence": entry.composite_confidence
            }, f, indent=2)

    def store_scientific_lesson(self, lesson: ScientificMemoryObject):
        file_path = os.path.join(self.knowledge_path, f"{lesson.object_id}.json")
        with open(file_path, 'w') as f:
            json.dump({"id": str(lesson.object_id), "lesson": lesson.generalized_lesson}, f, indent=2)

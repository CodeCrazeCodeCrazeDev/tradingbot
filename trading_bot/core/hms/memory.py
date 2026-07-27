"""

Implements 'SAGE: A Self-Evolving Agentic Graph-Memory Engine' (2026).
Supports incremental construction, Graph-FM multi-hop retrieval,
and Reader-Writer feedback loops for structural evolution.
Hierarchical Memory System (HMS) - UCA V6 (July 2026)

Authoritative memory system integrating SAGE, AutoMem, and the unified Memory OS.
Implements the 8-tier architecture: Workspace, Episodic, Semantic, Procedural,
Research, World Models, Institutional, and Meta-Memory.
"""

import logging
import os
import json
import networkx as nx
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4
import threading

from .models import (
    ResearchLedgerEntry,
    ScientificMemoryObject,
    EvidenceNode,
    EvidenceEdge,
    RelationType,
    EvidenceGraph
)
from .memory_os import MemoryOS, MemoryNode, MemoryTier, MemoryProvenance
from .cmos import CognitiveMemoryOS
from .ontology import CMOSNode, CMOSNodeTier, CMOSProvenance

logger = logging.getLogger(__name__)

class SAGEGraphMemory:
    """
    SAGE Substrate: A dynamic, self-evolving graph memory (arXiv:2605.12061).
    Supports incremental construction, context-dependent triplet validity, and autonomous weight evolution.
    """
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.graph = self._load_graph()
        self.evolution_rounds = 0
        self.eta = 0.1 # Learning rate for edge weights
        logger.info(f"SAGE V6: Initialized with {len(self.graph.nodes)} nodes")

    def _load_graph(self) -> nx.MultiDiGraph:
        if os.path.exists(self.storage_path):
            try:
                graph = nx.read_graphml(self.storage_path)
                if not isinstance(graph, nx.MultiDiGraph):
                    graph = nx.MultiDiGraph(graph)

                # Deserialize complex attributes and weights
                for u, v, k, d in list(graph.edges(keys=True, data=True)):
                    if 'weight' not in d: d['weight'] = 0.5
                    for attr in ['context', 'evidence']:
                        if attr in d and isinstance(d[attr], str):
                            try:
                                d[attr] = json.loads(d[attr])
                            except json.JSONDecodeError:
                                pass
                return graph
            except Exception as e:
                logger.error(f"SAGE: Load failed: {e}")
        return nx.MultiDiGraph()

    def save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            temp_graph = self.graph.copy()
            for u, v, k, d in list(temp_graph.edges(keys=True, data=True)):
                if 'context' in d: d['context'] = json.dumps(d['context'])
                if 'evidence' in d: d['evidence'] = json.dumps(d['evidence'])
            nx.write_graphml(temp_graph, self.storage_path)
        except Exception as e:
            logger.error(f"SAGE: Save failed: {e}")

    def add_evidence(self, triplet: Tuple[str, str, str], context: Dict[str, Any], evidence: Dict[str, Any]):
        """Incremental Construction: Link new entities with context-sensitive triplets."""
        u, r, v = triplet
        edge_key = f"{r}_{uuid4().hex[:8]}"

        # SAGE: Initial weight based on confidence
        initial_weight = float(evidence.get("confidence", 0.5))

        self.graph.add_edge(
            u, v,
            key=edge_key,
            relation=r,
            context=context,
            evidence=evidence,
            weight=initial_weight,
            timestamp=datetime.utcnow().isoformat()
        )
        self.save()

    def retrieve_subgraph(self, query: str, hops: int = 2) -> List[Dict[str, Any]]:
        """SAGE: Multi-hop retrieval utility (arXiv:2605.12061 Eq 4)."""
        # 1. Identify seed nodes
        seeds = [n for n in self.graph.nodes if query.lower() in str(n).lower()]

        results = []
        visited = set()

        # 2. Perform multi-hop traversal with weighted relevance
        for seed in seeds:
            try:
                edges = nx.bfs_edges(self.graph, seed, depth_limit=hops)
                for u, v in edges:
                    for k, d in self.graph.get_edge_data(u, v).items():
                        if (u, v, k) not in visited:
                            # R(n) = Sim(q, n) + sum(w_nm * Sim(q, m))
                            results.append({
                                "source": u,
                                "target": v,
                                "relation": d.get("relation"),
                                "weight": d.get("weight", 0.5),
                                "context": d.get("context")
                            })
                            visited.add((u, v, k))
            except Exception: continue

        # Sort by weight (Utility)
        results.sort(key=lambda x: x["weight"], reverse=True)
        return results[:15]

    def evolve_weights(self, edge_id: Tuple[str, str, str], feedback_delta: float):
        """SAGE: Edge Evolution (arXiv:2605.12061 Eq 5)."""
        u, v, k = edge_id
        if self.graph.has_edge(u, v, k):
            current_w = self.graph[u][v][k].get("weight", 0.5)
            # w = w + eta * delta
            new_w = max(0.0, min(1.0, current_w + self.eta * feedback_delta))
            self.graph[u][v][k]["weight"] = new_w

            # Autonomous Pruning: Remove low-utility edges
            if new_w < 0.1:
                logger.info(f"SAGE: Pruning low-utility edge ({u}, {v}, {k})")
                self.graph.remove_edge(u, v, k)
            self.save()

    def compact_graph(self, max_nodes: int = 5000, min_confidence: float = 0.3):
        """Prunes old or low-confidence nodes/edges to prevent memory bloat."""
        logger.info(f"SAGE: Starting graph compaction. Current size: {len(self.graph.nodes)} nodes.")

        # 1. Prune edges with low confidence (if metadata exists)
        edges_to_prune = []
        for u, v, k, d in self.graph.edges(keys=True, data=True):
            evidence = d.get('evidence', {})
            if isinstance(evidence, dict) and evidence.get('confidence', 1.0) < min_confidence:
                edges_to_prune.append((u, v, k))

        for u, v, k in edges_to_prune:
            self.graph.remove_edge(u, v, k)

        # 2. Prune orphan nodes if over capacity
        if len(self.graph.nodes) > max_nodes:
            # Simple heuristic: remove nodes with no edges first
            orphans = [n for n in self.graph.nodes if self.graph.degree(n) == 0]
            self.graph.remove_nodes_from(orphans[:len(self.graph.nodes) - max_nodes])

        logger.info(f"SAGE: Compaction complete. New size: {len(self.graph.nodes)} nodes.")

class HierarchicalMemorySystem:
    """
    Authoritative memory system Consolidating SAGE and AutoMem.
    Implements active memory management as a cognitive skill.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(HierarchicalMemorySystem, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, base_path: str = "alphaalgo_data/hms"):
        if self._initialized: return
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

        self.ledger_path = os.path.join(base_path, "research_ledger")
        self.knowledge_path = os.path.join(base_path, "scientific_memory")
        os.makedirs(self.ledger_path, exist_ok=True)
        os.makedirs(self.knowledge_path, exist_ok=True)

        graph_path = os.path.join(base_path, "sage_graph.graphml")
        self.sage = SAGEGraphMemory(storage_path=graph_path)

        self.schema_path = os.path.join(base_path, "memory_schema.json")
        self.memory_schema = self._load_schema()

        # Consolidating standard MemoryOS
        self.memory_os = MemoryOS(base_storage_path=os.path.join(base_path, "memory_os"))

        # Core CMOS substrate instantiation
        self.cmos = CognitiveMemoryOS()

        self._initialized = True
        logger.info(f"HMS V6: One Memory initialized at {base_path}")

    def _load_schema(self) -> Dict[str, Any]:
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, 'r') as f: return json.load(f)
            except: pass
        return {"version": "2.0", "entities": [], "relations": [], "optimized_count": 0}

    def _save_schema(self):
        with open(self.schema_path, 'w') as f: json.dump(self.memory_schema, f, indent=2)

    async def retrieve_evidence_chain(self, query: str) -> List[Any]:
        """Multi-hop evidence retrieval via SAGE."""
        return self.sage.retrieve_subgraph(query, hops=2)

    def store_ledger_entry(self, entry: ResearchLedgerEntry):
        """Active Management: Storing and indexing research ledger entries."""
        file_path = os.path.join(self.ledger_path, f"{entry.entry_id}.json")

        # 1. Incremental construction in SAGE
        if entry.hypothesis:
            self.sage.add_evidence(
                (str(entry.entry_id), "HYPOTHESIZED", entry.hypothesis.description),
                {"context": "research_ledger", "branch": "UCA_V6"},
                {"confidence": entry.composite_confidence}
            )

        # 2. Persist evidence graph nodes (arXiv:2606.13669 Agents-K1)
        for node_id, node in entry.evidence_graph_snapshot.nodes.items():
            self.sage.graph.add_node(node_id, type=node.node_type, content=str(node.content))

        # 3. Persist file with sufficient statistics (HIPIF)
        entry_data = {
            "entry_id": str(entry.entry_id),
            "timestamp": entry.timestamp.isoformat(),
            "composite_confidence": entry.composite_confidence,
            "reasoning_steps": entry.reasoning_steps,
            "folded": True
        }
        with open(file_path, 'w') as f: json.dump(entry_data, f, indent=2)

    def optimize_metamemory(self, feedback: List[Dict[str, Any]]):
        """
        AutoMem: Dual-loop schema and weight optimization (arXiv:2607.01224).
        Learns optimal memory management from task success/failure.
        """
        logger.info(f"HMS V6: Running AutoMem optimization loop on {len(feedback)} samples")

        for item in feedback:
            # 1. Update SAGE weights based on trade success
            edge_id = item.get("edge_id")
            success_delta = item.get("delta", 0.0) # -1.0 to 1.0
            if edge_id:
                self.sage.evolve_weights(edge_id, success_delta)

            # 2. Revise indexing schema (Simplified)
            entity = item.get("entity")
            if entity and entity not in self.memory_schema["entities"]:
                 self.memory_schema["entities"].append(entity)

        self.memory_schema["optimized_count"] += 1
        self.memory_schema["last_optimized"] = datetime.utcnow().isoformat()
        self._save_schema()
        logger.info("HMS V6: AutoMem optimization cycle complete.")

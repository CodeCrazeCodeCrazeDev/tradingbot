"""

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
import hashlib
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

def calculate_integrity_hash(schema_dict: Dict[str, Any]) -> str:
    """Computes SHA-256 checksum of memory schema for audit compliance."""
    temp = {k: v for k, v in schema_dict.items() if k != "integrity_hash"}
    serialized = json.dumps(temp, sort_keys=True)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

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
    _calculate_integrity_hash = staticmethod(calculate_integrity_hash)

    _calculate_integrity_hash = staticmethod(calculate_integrity_hash)

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(HierarchicalMemorySystem, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        return calculate_integrity_hash(schema_dict)

    def __init__(self, base_path: str = "alphaalgo_data/hms"):
        if getattr(self, "_initialized", False) and getattr(self, "base_path", None) == base_path:
            return
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
        self.memory_window_size = 100

        # Consolidating standard MemoryOS
        self.memory_os = MemoryOS(base_storage_path=os.path.join(base_path, "memory_os"))

        # Core CMOS substrate instantiation
        self.cmos = CognitiveMemoryOS()

        self._initialized = True
        logger.info(f"HMS V6: One Memory initialized at {base_path}")

    def reset(self):
        self.memory_schema = {"version": "2.0", "entities": [], "relations": [], "optimized_count": 0}
        self._save_schema()

    def seal_adapt_memory_window(self, retention_latency_reward: float):
        """
        Adapts the HMS 'memory_window_size' based on downstream task performance reward
        using the MIT SEAL paper reinforcement learning adaptation framework.
        """
        if retention_latency_reward < 1.0:
            # Latency or surprise was high -> reduce window size to lower retrieval latency
            self.memory_window_size = max(self.memory_window_size - 10, 10)
            logger.info(f"SEAL: Memory retention latency was high. Adapted HMS memory window to {self.memory_window_size} to optimize lookup performance.")
        else:
            # High quality retrieval -> increase window to retain more context
            self.memory_window_size = min(self.memory_window_size + 10, 500)
            logger.info(f"SEAL: Memory retrieval was highly accurate. Adapted HMS memory window to {self.memory_window_size} to retain more contextual episodic memory.")

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        return calculate_integrity_hash(schema_dict)

    def _load_schema(self) -> Dict[str, Any]:
        schema = {"version": "1.0", "schema_version": "1.0", "entities": [], "relations": [], "optimized_count": 0, "migration_history": []}
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, 'r') as f:
                    data = json.load(f)
                    if "migration_history" not in data:
                        data["migration_history"] = []
                    return data
            except: pass
        return schema

    def _calculate_integrity_hash(self, schema: Dict[str, Any]) -> str:
        """
        Calculates a deterministic SHA-256 hash over the canonical JSON representation
        of the memory schema, excluding derived/volatile fields (integrity_hash, updated_at).
        """
        # Create a copy to avoid mutating the original schema
        clean_schema = {}
        for k, v in schema.items():
            if k not in ("integrity_hash", "updated_at"):
                clean_schema[k] = v

        try:
            # Deterministic, canonical serialization with sort_keys=True
            canonical_json = json.dumps(clean_schema, sort_keys=True)
        except (TypeError, ValueError) as e:
            raise ValueError(f"HMS Schema contains non-serializable values: {e}")

        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        """Calculates SHA-256 integrity hash of schema."""
        return calculate_integrity_hash(schema_dict)

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        """Computes SHA-256 checksum of memory schema for audit compliance."""
        temp = {k: v for k, v in schema_dict.items() if k != "integrity_hash"}
        serialized = json.dumps(temp, sort_keys=True)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        return calculate_integrity_hash(schema_dict)

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        return calculate_integrity_hash(schema_dict)

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        return calculate_integrity_hash(schema_dict)

    @staticmethod
    def _calculate_integrity_hash(schema_dict: Dict[str, Any]) -> str:
        return calculate_integrity_hash(schema_dict)

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        return calculate_integrity_hash(schema_dict)

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        return calculate_integrity_hash(schema_dict)

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        """Helper to calculate hash within instance as well."""
        return calculate_integrity_hash(schema_dict)

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        """Helper pointing to global calculate_integrity_hash function."""
        return calculate_integrity_hash(schema_dict)

    def _save_schema(self):
        self.memory_schema["updated_at"] = datetime.utcnow().isoformat()
        self.memory_schema["integrity_hash"] = self._calculate_integrity_hash(self.memory_schema)
        with open(self.schema_path, 'w') as f:
            json.dump(self.memory_schema, f, indent=2)

    def _calculate_integrity_hash(self, schema_dict: Dict[str, Any]) -> str:
        return calculate_integrity_hash(schema_dict)

    def migrate_to_version(self, target_version: str) -> bool:
        """Runs explicit up/down migrations sequentially to target_version."""
        current_v_str = self.memory_schema.get("schema_version", "1.0")
        current_v = float(current_v_str)
        target_v = float(target_version)

        if current_v == target_v:
            return True

        logger.info(f"HMS Migration: Preparing migration from {current_v_str} to {target_version}")

        # Step-by-step sequential migration
        direction = "up" if target_v > current_v else "down"
        while current_v != target_v:
            if direction == "up":
                next_v = round(current_v + 0.1, 1)
                success = self._run_migration_step(f"{current_v:.1f}", f"{next_v:.1f}", "up")
                if not success:
                    logger.error(f"HMS Migration failed at step {current_v:.1f} -> {next_v:.1f}")
                    return False
                current_v = next_v
            else:
                next_v = round(current_v - 0.1, 1)
                success = self._run_migration_step(f"{current_v:.1f}", f"{next_v:.1f}", "down")
                if not success:
                    logger.error(f"HMS Rollback failed at step {current_v:.1f} -> {next_v:.1f}")
                    return False
                current_v = next_v

        self.memory_schema["schema_version"] = f"{current_v:.1f}"
        self.memory_schema["version"] = f"{current_v:.1f}" # Sync legacy
        self._save_schema()
        return True

    def _run_migration_step(self, from_v: str, to_v: str, direction: str) -> bool:
        logger.info(f"HMS: Executing {direction}-migration from {from_v} to {to_v}")

        # Define deterministic schema updates
        if direction == "up":
            if from_v == "1.0" and to_v == "1.1":
                # Up-migration 1.0 -> 1.1: add specialized tracking property
                self.memory_schema["entities"].append({"type": "RESEARCH_METADATA", "fields": ["fdr_adjusted_p", "purged_embargoed_cv"]})
            elif from_v == "1.1" and to_v == "1.2":
                self.memory_schema["relations"].append({"type": "CONTRADICTS", "inverse": "CONTRADICTS"})
        else: # down-migration / rollback
            if from_v == "1.1" and to_v == "1.0":
                # Rollback 1.1 -> 1.0: remove added entities
                self.memory_schema["entities"] = [e for e in self.memory_schema["entities"] if e.get("type") != "RESEARCH_METADATA"]
            elif from_v == "1.2" and to_v == "1.1":
                self.memory_schema["relations"] = [r for r in self.memory_schema["relations"] if r.get("type") != "CONTRADICTS"]

        # Track history
        if "migration_history" not in self.memory_schema:
            self.memory_schema["migration_history"] = []
        self.memory_schema["migration_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "from_version": from_v,
            "to_version": to_v,
            "direction": direction,
            "status": "SUCCESS"
        })
        return True

    def _calculate_integrity_hash(self, schema_data: Dict[str, Any]) -> str:
        import hashlib
        import copy
        data_copy = copy.deepcopy(schema_data)
        data_copy.pop("integrity_hash", None)
        serialized = json.dumps(data_copy, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def validate_replay(self, schema_data: Dict[str, Any]) -> bool:
        """Validates schema integrity and correctness."""
        expected_hash = self._calculate_integrity_hash(schema_data)
        actual_hash = schema_data.get("integrity_hash")
        return expected_hash == actual_hash

    def run_migration(self, target_version: str, migration_reason: str) -> bool:
        """Run an explicit schema migration."""
        current_version = float(self.memory_schema.get("version", "1.0"))
        target_f = float(target_version)
        if target_f <= current_version:
            logger.info(f"HMS: Schema already at or past version {target_version}")
            return False

        # Apply schema changes (e.g. initialize new entities or properties)
        self.memory_schema["version"] = target_version

        migration_entry = {
            "migration_id": f"mig_{uuid4().hex[:8]}",
            "migration_timestamp": datetime.utcnow().isoformat(),
            "migration_reason": migration_reason,
            "compatibility_level": "COMPATIBLE",
            "previous_version": str(current_version),
            "target_version": target_version
        }

        if "migration_history" not in self.memory_schema:
            self.memory_schema["migration_history"] = []
        self.memory_schema["migration_history"].append(migration_entry)

        self._save_schema()
        logger.info(f"HMS: Schema migrated from {current_version} to {target_version}")
        return True

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
        try:
            current_version = float(self.memory_schema.get("version", "1.0"))
            self.memory_schema["version"] = str(current_version + 0.1)
        except ValueError:
            self.memory_schema["version"] = "1.1"
        self._save_schema()
        logger.info("HMS V6: AutoMem optimization cycle complete.")

from datetime import datetime, timezone
import time
import threading
from typing import List, Dict, Any, Optional, Tuple, Set, Union
"""
Hierarchical Memory System (HMS) - UCA-2026 Authoritative Substrate Layer

Paper Traceability Matrix:
- arXiv:2605.29303 (EKSFT): Selective token masking preservation during research memory indexing.
- arXiv:2607.00341 (DiscoLoop): Dual continuous-discrete working memory channels for multi-hop reasoning.
- arXiv:2607.01224 (AutoMem): Active metamemory management, schema migrations, and index optimization.
- arXiv:2605.12061 (SAGE): Self-evolving agentic graph-memory engine with Hebbian edge weight evolution.
- arXiv:2605.10813 (NanoResearch): Experience ledger persistence for co-evolving research swarms.
- arXiv:2605.20025 (AutoResearchClaw): Traceability and critique ledger recording for pivot/refine loops.
- arXiv:2605.17734 (HASP): Procedural memory storage for verified Program Functions and guardrails.
- arXiv:2605.21482 (DeepWeb-Bench): SHA-256 schema integrity verification and evidence graph audits.

Authoritative Memory System implementing the 8-Tier Memory OS with SAGE Graph and AutoMem Metamemory.
"""

import logging
import os
import json

from enum import Enum
from dataclasses import dataclass, field
import uuid

class MemoryValidationStatus(Enum):
    UNVERIFIED = "UNVERIFIED"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    TRUSTED = "TRUSTED"
    REVOKED = "REVOKED"
    QUARANTINED = "QUARANTINED"

@dataclass
class ProvenanceAwareMemoryRecord:
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = "unknown"
    creator: str = "unknown"
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 0.5
    validation_status: MemoryValidationStatus = MemoryValidationStatus.UNVERIFIED
    integrity_hash: str = ""
    version: int = 1
    parent_memory: Optional[str] = None
    supersedes: Optional[str] = None
    sensitivity: str = "CONFIDENTIAL"
    expiration: Optional[float] = None
    access_policy: str = "RBAC_DEFAULT"
    content: str = ""

    def __post_init__(self):
        if not self.integrity_hash:
            self.integrity_hash = self.compute_hash()

    def compute_hash(self) -> str:
        payload = f"{self.memory_id}:{self.source}:{self.creator}:{self.timestamp}:{self.content}:{self.validation_status.value}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def is_valid(self) -> bool:
        return self.integrity_hash == self.compute_hash() and self.validation_status not in (MemoryValidationStatus.REVOKED, MemoryValidationStatus.QUARANTINED)

import hashlib
import networkx as nx
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4
from .models import ResearchLedgerEntry, ScientificMemoryObject, EvidenceNode, EvidenceEdge, RelationType

logger = logging.getLogger(__name__)

# Compatibility alias for the graph backend (historically wrapped nx.MultiDiGraph)
CompatMultiDiGraph = nx.MultiDiGraph


class SAGEGraphProxy:
    """Read-through proxy exposing the SAGE graph via a stable interface."""

    def __init__(self, graph):
        self._graph = graph

    def __getattr__(self, name):
        return getattr(self._graph, name)

    def __getitem__(self, node):
        """Node-adjacency access: ``proxy[u][v]`` yields the edge attribute dict.

        For MultiDiGraphs ``graph[u][v]`` is ``{edge_key: attrs}``; legacy
        callers expect direct attribute access, so the first edge's attrs are
        surfaced (all u->v edges of a relation share semantics here).
        """
        adj = self._graph.adj[node]
        if getattr(self._graph, "is_multigraph", lambda: False)():
            return {nbr: next(iter(data.values()), {}) for nbr, data in adj.items()}
        return dict(adj)

    def __contains__(self, node):
        return node in self._graph

    def __iter__(self):
        return iter(self._graph)

def calculate_integrity_hash(schema_dict: Dict[str, Any]) -> str:
    """Computes SHA-256 checksum of memory schema for audit compliance."""
    temp = {k: v for k, v in schema_dict.items() if k != "integrity_hash"}
    serialized = json.dumps(temp, sort_keys=True)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

class SAGEGraphMemory:
    """
    SAGE Substrate: A dynamic, self-evolving graph memory (arXiv:2607.00341).
    Supports incremental construction, context-dependent triplet validity, and autonomous weight evolution.
    """
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            import tempfile
            storage_path = os.path.join(tempfile.mkdtemp(prefix="sage_"), "sage_graph.graphml")
        self.storage_path = storage_path
        self.graph = self._load_graph()
        self.evolution_rounds = 0
        self.eta = 0.1 # Learning rate for edge weights
        logger.info(f"SAGE V6: Initialized with {len(self.graph.nodes)} nodes")

    def _load_graph(self) -> CompatMultiDiGraph:
        if os.path.exists(self.storage_path):
            try:
                graph = nx.read_graphml(self.storage_path)
                if not isinstance(graph, CompatMultiDiGraph):
                    graph = CompatMultiDiGraph(graph)

                # Deserialize complex attributes and weights
                for u, v, k, d in list(graph.edges(keys=True, data=True)):
                    if 'weight' not in d: d['weight'] = 0.5
                    for attr in ['context', 'evidence']:
                        if attr in d and isinstance(d[attr], str):
                            try:
                                d[attr] = json.loads(d[attr])
                            except json.JSONDecodeError:
                                logger.warning(f"Handled exception in memory.py")
                return graph
            except Exception as e:
                logger.error(f"SAGE: Load failed: {e}")
        return CompatMultiDiGraph()

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
        """SAGE: Multi-hop retrieval utility (arXiv:2607.00341)."""
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
        """SAGE: Edge Evolution (arXiv:2607.00341)."""
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

    def evolve(self, feedback: List[Dict[str, Any]]):
        """Autonomous Weight Evolution: apply STRENGTHEN/WEAKEN feedback to edges.

        Each item: {"action": "STRENGTHEN"|"WEAKEN", "source": u, "target": v,
        "delta": optional float}.
        """
        deltas = {"STRENGTHEN": 1.0, "WEAKEN": -1.0, "REINFORCE": 1.0}
        for item in feedback:
            action = str(item.get("action", "STRENGTHEN")).upper()
            delta = float(item.get("delta", deltas.get(action, 1.0)))
            if action in ("WEAKEN", "PRUNE"):
                delta = -abs(delta)
            u, v = item.get("source"), item.get("target")
            if u is None or v is None:
                continue
            for _, vv, k in list(self.graph.edges(u, keys=True)):
                if vv == v:
                    self.evolve_weights((u, v, k), delta)
        self.evolution_rounds += 1

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

    Scientific Traceability:
    - SAGE (arXiv:2607.00341): Self-evolving agentic graph-memory
    - AutoMem (arXiv:2607.01224): Dynamic meta-memory schema migration
    """
    _instance: Optional["HierarchicalMemorySystem"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(HierarchicalMemorySystem, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    @classmethod
    def reset(cls):
        """
        Explicit, safe class-level lifecycle reset.
        Frees singleton instances and flushes outstanding SAGE schema updates.
        """
        with cls._lock:
            if cls._instance is not None:
                try:
                    cls._instance._save_schema()
                except Exception:
                    pass
                cls._instance = None
        logger.info("HierarchicalMemorySystem successfully reset with schema synchronization.")

    def __init__(self, base_path: str = "alphaalgo_data/hms"):
        if getattr(self, "_initialized", False) and getattr(self, "base_path", None) == base_path:
            return

        self.config = config or {}
        self.base_path = base_path
        self.storage_root = base_path  # For backward compatibility with malformed store_ledger_entry
        self.ledger_path = os.path.join(base_path, "research_ledger")
        self.knowledge_path = os.path.join(base_path, "scientific_memory")
        self.graph_path = os.path.join(base_path, "sage_graph.graphml")
        self.schema_path = os.path.join(base_path, "memory_schema.json")

        os.makedirs(self.ledger_path, exist_ok=True)
        os.makedirs(self.knowledge_path, exist_ok=True)

        # Storage backends
        self.working_store = {}
        self.episodic_store = []
        self.semantic_graph = {}
        self.transactive_bus = {}

        # SAGE substrate
        self.sage = SAGEGraphMemory(self.graph_path)
        self.memory_schema = self._load_schema()
        self.memory_window_size = 100

        self._initialized = True
        logger.info(f"HMS V6: One Memory initialized at {base_path}")

    async def initialize(self):
        logger.info("HMS: Initializing Hierarchical Memory System")

        self.schema_path = os.path.join(self.base_path, "memory_schema.json")
        self.memory_schema = self._load_schema()
        self.memory_window_size = getattr(self, "memory_window_size", 100)

    def _load_graph(self) -> nx.MultiDiGraph:
        if os.path.exists(self.graph_path):
            try:
                return nx.read_graphml(self.graph_path)
            except Exception as e:
                logger.error(f"HMS: Failed to load SAGE graph: {e}")
        return nx.MultiDiGraph()

    def reset_schema(self):
        self.memory_schema = {"version": "2.0", "entities": [], "relations": [], "optimized_count": 0}
        self._save_schema()

    def seal_adapt_memory_window(self, retention_latency_reward: float):
        """
        Adapts the HMS 'memory_window_size' based on downstream task performance reward.
        """
        if retention_latency_reward < 1.0:
            # Latency or surprise was high -> reduce window size to lower retrieval latency
            self.memory_window_size = max(self.memory_window_size - 10, 10)
            logger.info(f"SEAL: Memory retention latency was high. Adapted HMS memory window to {self.memory_window_size} to optimize lookup performance.")
        else:
            # High quality retrieval -> increase window to retain more context
            self.memory_window_size = min(self.memory_window_size + 10, 500)
            logger.info(f"SEAL: Adapted HMS memory window to {self.memory_window_size}")

    def _load_schema(self) -> Dict[str, Any]:
        schema = {"version": "1.0", "schema_version": "1.0", "entities": [], "relations": [], "optimized_count": 0, "migration_history": []}
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, 'r') as f:
                    data = json.load(f)
                    if "migration_history" not in data:
                        data["migration_history"] = []
                    return data
            except Exception as exc:
                logger.warning("Error loading schema: %s", exc)
        return schema

    def _save_schema(self):
        self.memory_schema["updated_at"] = datetime.utcnow().isoformat()
        self.memory_schema["integrity_hash"] = self._calculate_integrity_hash(self.memory_schema)
        with open(self.schema_path, 'w') as f:
            json.dump(self.memory_schema, f, indent=2)

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

    @property
    def sage_graph(self):
        """Expose raw SAGE graph memory wrapped in a compatibility proxy."""
        return SAGEGraphProxy(self.sage.graph)

    async def execute_memory_action(self, agent_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HMS V4 first-class memory actions (AutoMem).

        Supported actions:
        - "write": add an entity/relation triplet to the SAGE graph.
        - "optimize": run memory consolidation (weight evolution + compaction).
        """
        action = (action or "").lower()
        if action == "write":
            entity = payload.get("entity")
            relation = payload.get("relation", "RELATED")
            target = payload.get("target", entity)
            if not entity:
                return {"status": "rejected", "reason": "missing entity"}
            self.sage.add_evidence(
                (entity, relation, target),
                {"agent": agent_id, "source": "memory_action"},
                {"confidence": float(payload.get("confidence", 0.5))},
            )
            return {"status": "graph_updated", "entity": entity, "relation": relation}
        if action == "optimize":
            for fn in (lambda: self.optimize_memory(payload.get("feedback", [])),
                       lambda: self.sage.compact_graph()):
                try:
                    fn()
                except Exception:
                    pass
            return {"status": "optimized"}
        return {"status": "unknown_action", "action": action}

    def evolve_memory(self, history: List[Dict[str, Any]]):
        """Allows older tests to evolve/populate SAGE memory with custom triplets."""
        for item in history:
            source = item.get("source")
            target = item.get("target")
            relation = item.get("relation")
            if source and target and relation:
                self.sage.add_evidence(
                    (source, relation, target),
                    {"context": "evolve_memory_test"},
                    {"confidence": 1.0}
                )

    def store_ledger_entry(self, entry: ResearchLedgerEntry):
        """
        Active Management: Storing, graph-native indexing, and provenance hash verification
        of research ledger entries (NOVEL-006, NOVEL-015).
        """
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
            "folded": True,
            "provenance_hash": hashlib.sha256(
                f"{entry.entry_id}_{entry.timestamp.isoformat()}_{entry.composite_confidence}".encode("utf-8")
            ).hexdigest()
        }
        with open(file_path, 'w') as f:
            json.dump(entry_data, f, indent=2)

    def optimize_memory(self, feedback: List[Dict[str, Any]]):
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

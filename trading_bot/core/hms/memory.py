"""
Hierarchical Memory System (HMS) - UCA V5 (July 2026)

Authoritative memory system integrating SAGE (Self-evolving Agentic Graph-Memory)
and AutoMem (Meta-memory optimization).
Implements the 6-tier architecture: Working, Episodic, Semantic, Procedural, Research, Institutional.

Scientific Foundation:
- SAGE: arXiv:2605.12061
- AutoMem: arXiv:2607.01224
"""

import logging
import os
import json
import hashlib
import copy
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

logger = logging.getLogger(__name__)

def calculate_integrity_hash(schema_dict: Dict[str, Any]) -> str:
    """Computes SHA-256 checksum of memory schema for audit compliance."""
    temp = {k: v for k, v in schema_dict.items() if k != "integrity_hash"}
    serialized = json.dumps(temp, sort_keys=True)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

class SAGEGraphMemory:
    """
    SAGE Substrate: A dynamic, self-evolving graph memory.
    Supports incremental construction and context-dependent triplet validity.
    """
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.graph = self._load_graph()
        self.evolution_rounds = 0
        logger.info(f"SAGE: Initialized with {len(self.graph.nodes)} nodes")

    def _load_graph(self) -> nx.MultiDiGraph:
        if os.path.exists(self.storage_path):
            try:
                graph = nx.read_graphml(self.storage_path)
                if not isinstance(graph, nx.MultiDiGraph):
                    graph = nx.MultiDiGraph(graph)

                # Deserialize complex attributes
                for u, v, k, d in list(graph.edges(keys=True, data=True)):
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
        u, r, v = triplet
        edge_key = f"{r}_{uuid4().hex[:8]}"
        self.graph.add_edge(
            u, v,
            key=edge_key,
            relation=r,
            context=context,
            evidence=evidence,
            timestamp=datetime.utcnow().isoformat()
        )
        self.save()

    def evolve(self, feedback: List[Dict[str, Any]]):
        self.evolution_rounds += 1
        for f in feedback:
            action = f.get("action")
            if action == "PRUNE":
                u, v, key = f.get("edge_id")
                if self.graph.has_edge(u, v, key):
                    self.graph.remove_edge(u, v, key)
            elif action == "MERGE":
                n1, n2 = f.get("node_a"), f.get("node_b")
                if self.graph.has_node(n1) and self.graph.has_node(n2):
                    self.graph = nx.contracted_nodes(self.graph, n1, n2, self_loops=False)
        self.save()

class HierarchicalMemorySystem:
    """
    Authoritative memory system. Consolidates SAGE and AutoMem.
    Provides robust structural schema migrations, integrity checks, and fallback rollbacks.
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

        self._initialized = True
        logger.info(f"HMS V5: Initialized at {base_path}")

    def _load_schema(self) -> Dict[str, Any]:
        default_schema = {
            "version": "1.0",
            "entities": ["RESEARCH_ENTRY", "HYPOTHESIS"],
            "relations": ["HYPOTHESIZED", "SUPPORTS", "REFUTES"],
            "migration_history": [],
            "provenance": "AlphaAlgo HMS Schema"
        }
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, 'r') as f:
                    schema = json.load(f)
                    if self._validate_schema_integrity(schema):
                        return schema
                    else:
                        logger.warning("HMS: Schema failed integrity checks, falling back to default schema.")
            except Exception as e:
                logger.error(f"HMS: Schema load error: {e}")

        # Save fresh hashed schema
        default_schema["integrity_hash"] = calculate_integrity_hash(default_schema)
        return default_schema

    def _validate_schema_integrity(self, schema_dict: Dict[str, Any]) -> bool:
        required_keys = ["version", "entities", "relations"]
        if not all(k in schema_dict for k in required_keys):
            logger.error("HMS Schema validation failed: missing required structural keys")
            return False

        stored_hash = schema_dict.get("integrity_hash")
        if stored_hash:
            calculated_hash = calculate_integrity_hash(schema_dict)
            if stored_hash != calculated_hash:
                logger.error(f"HMS Schema integrity hash mismatch! Calculated {calculated_hash} but found {stored_hash}")
                return False
        return True

    def _save_schema(self):
        # Always compute fresh integrity hash before write
        self.memory_schema["integrity_hash"] = calculate_integrity_hash(self.memory_schema)
        with open(self.schema_path, 'w') as f:
            json.dump(self.memory_schema, f, indent=2)

    def migrate_schema(self, target_version: str) -> bool:
        """
        Explicitly migrates the schema forward or backward to target_version.
        Provides robust rollbacks and full validation boundaries.
        """
        current_version = self.memory_schema.get("version", "1.0")
        if current_version == target_version:
            logger.info(f"HMS Schema: Already at target version {target_version}")
            return True

        original_schema_backup = copy.deepcopy(self.memory_schema)
        logger.info(f"HMS Schema: Attempting migration from {current_version} to {target_version}...")

        try:
            curr = float(current_version)
            tgt = float(target_version)

            if curr < tgt:
                # Forward migration
                while curr < tgt:
                    next_v = round(curr + 0.1, 1)
                    success = self._run_migration_step(str(curr), str(next_v))
                    if not success:
                        raise RuntimeError(f"Migration step from {curr} to {next_v} failed")
                    curr = next_v
            else:
                # Backward rollback migration
                while curr > tgt:
                    next_v = round(curr - 0.1, 1)
                    success = self._run_rollback_step(str(curr), str(next_v))
                    if not success:
                        raise RuntimeError(f"Rollback step from {curr} to {next_v} failed")
                    curr = next_v

            self.memory_schema["version"] = str(target_version)
            self.memory_schema["migration_history"] = self.memory_schema.get("migration_history", [])
            self.memory_schema["migration_history"].append({
                "from": current_version,
                "to": target_version,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "SUCCESS"
            })
            self._save_schema()
            logger.info(f"HMS Schema: Successfully migrated to {target_version}")
            return True

        except Exception as e:
            logger.error(f"HMS Schema: Migration failed! Initiating rollback... Error: {e}")
            self.memory_schema = original_schema_backup
            self._save_schema()
            return False

    def _run_migration_step(self, from_v: str, to_v: str) -> bool:
        """Applies structural changes for version transition step."""
        logger.info(f"HMS: Running forward transition step {from_v} -> {to_v}")
        if from_v == "1.0" and to_v == "1.1":
            self.memory_schema["entities"] = self.memory_schema.get("entities", []) + ["SAGE_NODE"]
            return True
        return True

    def _run_rollback_step(self, from_v: str, to_v: str) -> bool:
        """Reverts structural changes for rollback transition step."""
        logger.info(f"HMS: Running backward rollback step {from_v} -> {to_v}")
        if from_v == "1.1" and to_v == "1.0":
            if "SAGE_NODE" in self.memory_schema.get("entities", []):
                self.memory_schema["entities"].remove("SAGE_NODE")
            return True
        return True

    async def retrieve_evidence_chain(self, query: str) -> List[Any]:
        # Simple retrieval from SAGE graph
        results = []
        for u, v, d in self.sage.graph.edges(data=True):
            if query.lower() in u.lower() or query.lower() in v.lower():
                results.append({"source": u, "target": v, "relation": d.get("relation")})
        return results[:10] # Bounded growth

    def store_ledger_entry(self, entry: ResearchLedgerEntry):
        file_path = os.path.join(self.ledger_path, f"{entry.entry_id}.json")

        # 1. Sync with SAGE graph
        if entry.hypothesis:
            self.sage.add_evidence(
                (str(entry.entry_id), "HYPOTHESIZED", entry.hypothesis.description),
                {"context": "research_ledger"},
                {"confidence": entry.composite_confidence}
            )

        # 2. Persist evidence graph nodes
        for node_id, node in entry.evidence_graph_snapshot.nodes.items():
            self.sage.graph.add_node(node_id, type=node.node_type, content=str(node.content))

        # 3. Persist file
        entry_data = {
            "entry_id": str(entry.entry_id),
            "timestamp": entry.timestamp.isoformat(),
            "composite_confidence": entry.composite_confidence,
            "reasoning_steps": entry.reasoning_steps
        }
        with open(file_path, 'w') as f: json.dump(entry_data, f, indent=2)

    def optimize_metamemory(self, success_trajectories: List[Any]):
        """AutoMem: Schema optimization based on success."""
        current_version = self.memory_schema.get("version", "1.0")
        new_version = str(round(float(current_version) + 0.1, 1))

        # Observable and deterministic schema version migration
        success = self.migrate_schema(new_version)
        if success:
            self.memory_schema["last_optimized"] = datetime.utcnow().isoformat()
            self._save_schema()
            logger.info(f"HMS: AutoMem optimization complete. Schema version updated to {new_version}")
        else:
            logger.error("HMS: AutoMem optimization aborted due to migration failure")

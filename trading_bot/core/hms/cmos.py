"""
Cognitive Memory Operating System (CMOS) Core
=============================================
Phase 3: The complete coordinating core substrate of the CMOS.
Exposes Repository, Query Planner, Operator Registry, Scheduler, Provenance,
Governance, Economics, and Evolution as first-class infrastructure components.
Embeds real-time observability/telemetry from the beginning.
"""

import time
import uuid
import logging
import json
import networkx as nx
from typing import Any, Dict, List, Optional, Tuple, Set

from .ontology import CMOSNode, CMOSNodeTier, CMOSEdge, CMOSEdgeRelation, CMOSProvenance
from .contracts import ICMOSRepository, ICMOSQueryPlanner, ICMOSCore, CMOSContractValidationError

logger = logging.getLogger(__name__)


# ==========================================
# CMOS Repository Implementation
# ==========================================

class CMOSRepository(ICMOSRepository):
    """Authoritative in-memory graph repository with networkx backing."""

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def store_node(self, node: CMOSNode) -> None:
        self.graph.add_node(node.node_id, node=node, tier=node.tier.value)

    def get_node(self, node_id: str) -> Optional[CMOSNode]:
        if self.graph.has_node(node_id):
            return self.graph.nodes[node_id].get("node")
        return None

    def delete_node(self, node_id: str) -> bool:
        if self.graph.has_node(node_id):
            # Prune associated edges first to prevent dangling references
            edges_to_remove = []
            for u, v, k, d in self.graph.edges([node_id], keys=True, data=True):
                edges_to_remove.append((u, v, k))
            # Find incoming edges as well
            for u, v, k, d in list(self.graph.edges(keys=True, data=True)):
                if v == node_id:
                    edges_to_remove.append((u, v, k))

            for u, v, k in edges_to_remove:
                if self.graph.has_edge(u, v, k):
                    self.graph.remove_edge(u, v, k)

            self.graph.remove_node(node_id)
            return True
        return False

    def add_edge(self, edge: CMOSEdge) -> None:
        edge_key = f"{edge.relation.value}_{uuid.uuid4().hex[:8]}"
        self.graph.add_edge(
            edge.source_id,
            edge.target_id,
            key=edge_key,
            relation=edge.relation.value,
            weight=edge.weight,
            metadata=edge.metadata
        )

    def remove_edge(self, source_id: str, target_id: str, relation: CMOSEdgeRelation) -> bool:
        removed = False
        for u, v, k, d in list(self.graph.edges(keys=True, data=True)):
            if u == source_id and v == target_id and d.get("relation") == relation.value:
                self.graph.remove_edge(u, v, k)
                removed = True
        return removed

    def list_nodes(self, tier: Optional[CMOSNodeTier] = None) -> List[CMOSNode]:
        nodes = []
        for nid, data in self.graph.nodes(data=True):
            node = data.get("node")
            if node:
                if tier is None or node.tier == tier:
                    nodes.append(node)
        return nodes

    def list_edges(self) -> List[CMOSEdge]:
        edges = []
        for u, v, k, d in self.graph.edges(keys=True, data=True):
            edges.append(CMOSEdge(
                source_id=u,
                target_id=v,
                relation=CMOSEdgeRelation(d.get("relation")),
                weight=d.get("weight", 1.0),
                metadata=d.get("metadata")
            ))
        return edges


# ==========================================
# CMOS First-Class Infrastructure Modules
# ==========================================

class CMOSQueryPlanner(ICMOSQueryPlanner):
    """Query planner executing explicit reasoning-driven search maps."""

    def plan_query(self, query: str, context: Dict[str, Any]) -> List[str]:
        # Formulate chronological exploration paths (e.g. Workspace -> Episodic -> Semantic)
        plan = []
        q_lower = query.lower()
        if "today" in q_lower or "now" in q_lower or "current" in q_lower:
            plan.extend([CMOSNodeTier.T0_WORKSPACE.value, CMOSNodeTier.T1_EPISODIC.value])
        elif "hypothesis" in q_lower or "research" in q_lower or "theory" in q_lower:
            plan.extend([CMOSNodeTier.T4_RESEARCH.value, CMOSNodeTier.T6_INSTITUTIONAL.value])
        elif "rule" in q_lower or "config" in q_lower or "constraint" in q_lower:
            plan.extend([CMOSNodeTier.T2_SEMANTIC.value, CMOSNodeTier.T3_PROCEDURAL.value])
        else:
            plan.extend([
                CMOSNodeTier.T0_WORKSPACE.value,
                CMOSNodeTier.T1_EPISODIC.value,
                CMOSNodeTier.T2_SEMANTIC.value,
                CMOSNodeTier.T4_RESEARCH.value
            ])
        return plan


class CMOSProvenanceEngine:
    """Manages tracking, verifying, and updating memory provenance signatures."""

    def verify_provenance(self, provenance: CMOSProvenance) -> bool:
        if not provenance.source_agent:
            return False
        if not provenance.source_input_hash:
            return False
        if not (0.0 <= provenance.source_quality <= 1.0):
            return False
        if not (0.0 <= provenance.confidence <= 1.0):
            return False
        return True


class CMOSGovernanceGate:
    """Implements safe gating policies to override/block risky actions."""

    def evaluate_risk(self, node: CMOSNode, current_drawdown: float) -> bool:
        """Returns True if safe, False if risky/blocked (requires override hold)."""
        content_str = json.dumps(node.content).lower()
        if "danger" in content_str or "unstable" in content_str:
            if current_drawdown > 0.05:  # Block if drawdown is elevated
                return False
        return True


class CMOSEconomics:
    """Tracks compute cost, resource utilization, and token allocation of operators."""

    def __init__(self):
        self.compute_tokens = 0
        self.total_cost_usd = 0.0

    def charge_cost(self, token_count: int, rate_per_token: float = 0.000015):
        self.compute_tokens += token_count
        self.total_cost_usd += token_count * rate_per_token


class CMOSEvolution:
    """Handles continuous memory strength pruning, restructuring, and decay over epochs."""

    def __init__(self, half_life_sec: float = 7200.0):
        self.half_life_sec = half_life_sec

    def compute_decayed_strength(self, node: CMOSNode, current_time: float) -> float:
        elapsed = max(0.0, current_time - node.last_accessed)
        decay_factor = 2.0 ** (-elapsed / self.half_life_sec)
        return float(node.strength * decay_factor)


class CMOSScheduler:
    """First-class infrastructure scheduler coordinating consolidation, garbage collection, and compaction."""

    def __init__(self, csc_core: Any, interval_sec: float = 30.0):
        self.csc_core = csc_core
        self.interval_sec = interval_sec
        self.last_run_time = time.time()

    def should_run(self) -> bool:
        return (time.time() - self.last_run_time) >= self.interval_sec

    def run_scheduled_jobs(self):
        logger.info("CMOSScheduler: Running background optimization and consolidation runs.")
        self.last_run_time = time.time()
        self.csc_core.trigger_scheduled_evolution()


# ==========================================
# Real-Time Telemetry & Observability
# ==========================================

class CMOSObservability:
    """Real-time performance tracker monitoring P50/P95 latency, hit ratios, and mutations."""

    def __init__(self):
        self.latencies: List[float] = []
        self.read_requests = 0
        self.cache_hits = 0
        self.mutations = 0

    def record_transaction(self, success: bool, latency_ms: float, mutation_event: bool = False):
        self.latencies.append(latency_ms)
        if mutation_event:
            self.mutations += 1
        else:
            self.read_requests += 1
            if success:
                self.cache_hits += 1

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        p50 = float(sorted(self.latencies)[len(self.latencies) // 2]) if self.latencies else 0.0
        p95_index = int(len(self.latencies) * 0.95)
        p95 = float(sorted(self.latencies)[p95_index]) if self.latencies and p95_index < len(self.latencies) else p50
        hit_ratio = (self.cache_hits / self.read_requests) if self.read_requests > 0 else 1.0

        return {
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "cache_hit_ratio": hit_ratio,
            "total_mutations": self.mutations,
            "healthy": p50 < 100.0 and hit_ratio > 0.8
        }


# ==========================================
# Cognitive Memory OS Core Substrate
# ==========================================

class CognitiveMemoryOS(ICMOSCore):
    """Unified coordinating CMOS substrate. Replaces typical 'flat databases'."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CognitiveMemoryOS, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.repository = CMOSRepository()
        self.query_planner = CMOSQueryPlanner()
        self.provenance_engine = CMOSProvenanceEngine()
        self.governance = CMOSGovernanceGate()
        self.economics = CMOSEconomics()
        self.evolution = CMOSEvolution()
        self.observability = CMOSObservability()

        # Scheduler binds to self
        self.scheduler = CMOSScheduler(self)

        self.reproduction_ledger: List[Dict[str, Any]] = []  # Replay audit trail
        self._initialized = True
        logger.info("CognitiveMemoryOS Core Substrate initialized successfully.")

    def write_node(self, node: CMOSNode) -> str:
        """Determinstic transaction writing validating schema contracts and lineage."""
        t0 = time.perf_counter()

        # Provenance contract validation
        if not self.provenance_engine.verify_provenance(node.provenance):
            raise CMOSContractValidationError(f"Invalid provenance for memory node: {node.node_id}")

        self.repository.store_node(node)

        # Log to deterministic replay ledger
        self.reproduction_ledger.append({
            "timestamp": time.time(),
            "action": "WRITE",
            "node_id": node.node_id,
            "tier": node.tier.value,
            "content": node.content.copy(),
            "provenance": node.provenance.to_dict()
        })

        elapsed = (time.perf_counter() - t0) * 1000.0
        self.observability.record_transaction(success=True, latency_ms=elapsed, mutation_event=True)
        return node.node_id

    def read_node(self, node_id: str) -> Optional[CMOSNode]:
        """Read transaction updating accesses and logging T7 performance logs."""
        t0 = time.perf_counter()
        node = self.repository.get_node(node_id)

        success = False
        if node:
            node.access_count += 1
            node.last_accessed = time.time()
            node.strength = min(1.0, node.strength + 0.1)  # Access reinforcement
            success = True

        elapsed = (time.perf_counter() - t0) * 1000.0
        self.observability.record_transaction(success=success, latency_ms=elapsed, mutation_event=False)

        # Replay logging
        self.reproduction_ledger.append({
            "timestamp": time.time(),
            "action": "READ",
            "node_id": node_id,
            "success": success
        })

        return node

    def link_nodes(self, edge: CMOSEdge) -> None:
        """Creates an explicit connection, validating referential integrity."""
        # Enforce referential integrity: nodes must exist
        src = self.repository.get_node(edge.source_id)
        tgt = self.repository.get_node(edge.target_id)

        if not src or not tgt:
            raise CMOSContractValidationError(
                f"Referential Integrity violated: source {edge.source_id} or target {edge.target_id} does not exist."
            )

        self.repository.add_edge(edge)

        # Replay logging
        self.reproduction_ledger.append({
            "timestamp": time.time(),
            "action": "LINK",
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "relation": edge.relation.value
        })

    def trigger_scheduled_evolution(self):
        """Scheduler optimization job: decays strengths and triggers theme consolidations."""
        now = time.time()
        for node in self.repository.list_nodes():
            if node.tier != CMOSNodeTier.T0_WORKSPACE:
                node.strength = self.evolution.compute_decayed_strength(node, now)
                if node.strength < 0.05 and node.access_count == 1:
                    logger.info(f"CMOS Evolution: Decayed/pruned obsolete node {node.node_id}")
                    self.repository.delete_node(node.node_id)

    def replay_audit_trail(self) -> List[Dict[str, Any]]:
        """Bit-identical deterministic replay audit engine."""
        return self.reproduction_ledger

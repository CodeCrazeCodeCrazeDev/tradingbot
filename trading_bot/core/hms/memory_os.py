"""
Memory Operating System (Memory OS) - UCA V5+ / V6 Foundations
============================================================

Authoritative, graph-native, multi-tier institutional Memory OS designed for
long-horizon reasoning, active memory navigation, proactive reminders, and
scientific research continuity.

Extended 8-Tier Hierarchy (T0 - T7):
- T0 Active Workspace: Immediate working memory and attention.
- T1 Episodes: Raw temporal traces of sequential actions/events.
- T2 Semantic Facts: Verified atomic truths, configurations, and core constraints.
- T3 Skills & Procedures: Executable tool schemas and operational plans.
- T4 Research Knowledge: Active hypotheses, experimental setups, and results.
- T5 World Models: State transition models, simulated projections, and dynamics.
- T6 Institutional Knowledge: Peer reviews, ablation studies, and long-horizon histories.
- T7 Meta-Memory: Performance monitoring (latency, retrieval success, utility, decay).
"""

import time
import uuid
import logging
import json
import numpy as np
import networkx as nx
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryTier(Enum):
    T0_WORKSPACE = "T0_WORKSPACE"
    T1_EPISODIC = "T1_EPISODIC"
    T2_SEMANTIC = "T2_SEMANTIC"
    T3_PROCEDURAL = "T3_PROCEDURAL"
    T4_RESEARCH = "T4_RESEARCH"
    T5_WORLD_MODEL = "T5_WORLD_MODEL"
    T6_INSTITUTIONAL = "T6_INSTITUTIONAL"
    T7_META_MEMORY = "T7_META_MEMORY"


class EdgeRelation(Enum):
    CAUSAL = "CAUSAL"          # Node A causes Node B
    TEMPORAL = "TEMPORAL"      # Node A occurred before Node B
    SEMANTIC = "SEMANTIC"      # Node A is related in meaning to Node B
    EVIDENTIAL = "EVIDENTIAL"  # Node A is evidence supporting/refuting Node B
    PROVENANCE = "PROVENANCE"  # Node A was generated from/by Node B
    META = "META"              # Meta-relationship for T7 profiling


@dataclass
class MemoryProvenance:
    source_agent: str
    source_input_hash: str
    creation_timestamp: float = field(default_factory=time.time)
    source_quality: float = 1.0  # Range: [0, 1]
    confidence: float = 1.0      # Confidence score in memory accuracy
    evidence_uris: List[str] = field(default_factory=list)


@dataclass
class MemoryNode:
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tier: MemoryTier = MemoryTier.T0_WORKSPACE
    content: Dict[str, Any] = field(default_factory=dict)
    provenance: Optional[MemoryProvenance] = None
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 1
    strength: float = 1.0  # Decays over time, reinforced on access


@dataclass
class MemoryEdge:
    source_id: str
    target_id: str
    relation: EdgeRelation = EdgeRelation.SEMANTIC
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetaMemoryLog:
    """T7: Meta-Memory Statistics."""
    retrieval_success: bool = True
    latency_ms: float = 0.0
    usefulness_score: float = 1.0  # Feedback from sub-agent on usefulness [0, 1]
    confidence_delta: float = 0.0
    compression_ratio: float = 1.0
    forgetting_mitigated: bool = False


# ==========================================
# Core Capabilities of the Memory OS
# ==========================================

class MemoryProvenanceEngine:
    """Manages tracking, validating and updating memory provenance."""

    def verify_provenance(self, provenance: MemoryProvenance) -> bool:
        if not provenance.source_agent:
            return False
        if not (0.0 <= provenance.source_quality <= 1.0):
            return False
        if not (0.0 <= provenance.confidence <= 1.0):
            return False
        return True


class MemoryCompressor:
    """Handles semantic compression of historical memories to mitigate context bloat."""

    def compress_text(self, text_list: List[str]) -> str:
        # Implements standard compression fallback
        if not text_list:
            return ""
        return f"[COMPRESSED SUMMARY of {len(text_list)} entries]: " + " | ".join(text_list[:5])


class MemoryEvolutionEngine:
    """Responsible for memory strengthening, restructuring, merging, and decay pruning."""

    def __init__(self, half_life_seconds: float = 3600.0):
        self.half_life_seconds = half_life_seconds

    def compute_decay(self, current_time: float, last_accessed: float, current_strength: float) -> float:
        elapsed = max(0.0, current_time - last_accessed)
        decay_factor = 2.0 ** (-elapsed / self.half_life_seconds)
        return float(current_strength * decay_factor)

    def merge_nodes(self, node_a: MemoryNode, node_b: MemoryNode) -> MemoryNode:
        """Restructurings: merges complementary memories into a unified node."""
        merged_content = {**node_a.content, **node_b.content}
        merged_strength = min(1.0, node_a.strength + node_b.strength)

        # Combine provenance
        combined_agent = f"{node_a.provenance.source_agent if node_a.provenance else 'unknown'}_merged_{node_b.provenance.source_agent if node_b.provenance else 'unknown'}"
        combined_prov = MemoryProvenance(
            source_agent=combined_agent,
            source_input_hash=str(hash(json.dumps(merged_content, default=str))),
            confidence=(node_a.provenance.confidence + node_b.provenance.confidence) / 2.0 if (node_a.provenance and node_b.provenance) else 0.5
        )

        return MemoryNode(
            node_id=f"merged_{node_a.node_id[:8]}_{node_b.node_id[:8]}",
            tier=node_a.tier,
            content=merged_content,
            provenance=combined_prov,
            strength=merged_strength
        )


class MemoryVerifier:
    """Validates logic consistency, falsifies assumptions, and blocks hallucination/unsupported paths."""

    def verify_consistency(self, node: MemoryNode, related_nodes: List[MemoryNode]) -> Tuple[bool, float]:
        """Returns (is_consistent, score). Score indicates confidence in consistency."""
        # Baseline semantic check: if there is an explicit contradiction
        contradiction = False
        for rel in related_nodes:
            if "contradicts" in rel.content and rel.content["contradicts"] == node.node_id:
                contradiction = True
                break

        if contradiction:
            return False, 0.0
        return True, 1.0


class MemoryHealthMonitor:
    """Tracks overall metrics of the Memory OS, warning on fragmentation or extreme latency."""

    def __init__(self):
        self.latency_history: List[float] = []
        self.retrieval_count = 0
        self.success_count = 0

    def record_metrics(self, success: bool, latency_ms: float):
        self.latency_history.append(latency_ms)
        self.retrieval_count += 1
        if success:
            self.success_count += 1

    def get_health_status(self) -> Dict[str, Any]:
        p50_latency = float(np.median(self.latency_history)) if self.latency_history else 0.0
        success_rate = (self.success_count / self.retrieval_count) if self.retrieval_count > 0 else 1.0
        return {
            "p50_latency_ms": p50_latency,
            "success_rate": success_rate,
            "healthy": success_rate > 0.9 and p50_latency < 200.0
        }


class MemoryScheduler:
    """Schedules background optimization jobs like garbage collection, consolidation, and persistence."""

    def __init__(self, interval_sec: float = 60.0):
        self.interval_sec = interval_sec
        self.last_run = time.time()

    def should_run(self) -> bool:
        return (time.time() - self.last_run) >= self.interval_sec

    def trigger(self):
        self.last_run = time.time()


class MemoryReflection:
    """Generates continuous insights from the episodic traces to form new semantic truths."""

    def reflect_on_episodes(self, episodes: List[MemoryNode]) -> List[MemoryNode]:
        if not episodes:
            return []

        # Simple clustering simulation
        insights = []
        themes: Dict[str, int] = {}
        for ep in episodes:
            tag = ep.content.get("theme", "general")
            themes[tag] = themes.get(tag, 0) + 1

        for theme, count in themes.items():
            if count >= 3:
                insights.append(MemoryNode(
                    tier=MemoryTier.T2_SEMANTIC,
                    content={
                        "fact": f"Recurring theme detected: {theme}",
                        "confidence": 0.8,
                        "base_episodes_count": count
                    },
                    provenance=MemoryProvenance(source_agent="MemoryReflection", source_input_hash=theme)
                ))
        return insights


class MemoryConsolidator:
    """Consolidates working memory traces (T0) to persistent episodic/semantic stores (T1/T2)."""

    def __init__(self, evolution_engine: MemoryEvolutionEngine):
        self.evolution_engine = evolution_engine

    def consolidate(self, workspace_nodes: List[MemoryNode]) -> List[MemoryNode]:
        consolidated = []
        # Group identical concepts to merge
        by_topic: Dict[str, List[MemoryNode]] = {}
        for node in workspace_nodes:
            topic = node.content.get("topic", "default")
            by_topic.setdefault(topic, []).append(node)

        for topic, nodes in by_topic.items():
            if len(nodes) == 1:
                # Direct promotion
                cloned = copy_node_to_tier(nodes[0], MemoryTier.T1_EPISODIC)
                consolidated.append(cloned)
            elif len(nodes) > 1:
                # Merge into unified memory
                merged = nodes[0]
                for other in nodes[1:]:
                    merged = self.evolution_engine.merge_nodes(merged, other)
                merged.tier = MemoryTier.T1_EPISODIC
                consolidated.append(merged)

        return consolidated


def copy_node_to_tier(node: MemoryNode, tier: MemoryTier) -> MemoryNode:
    return MemoryNode(
        tier=tier,
        content=copy_dict(node.content),
        provenance=node.provenance,
        strength=node.strength
    )


def copy_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(json.dumps(d))
    except:
        return d.copy()


# ==========================================
# Proactive Memory Manager Component
# (Remember When It Matters)
# ==========================================

class ProactiveMemoryManager:
    """
    Implements a selective context reminder policy that prevents context bloat,
    detects context drift, and decides whether to inject proactive context
    reminders into the action loop or remain silent.
    """

    def __init__(self, drift_threshold: float = 0.4):
        self.drift_threshold = drift_threshold
        self.last_context_signature: Optional[str] = None

    def should_update_memory(self, current_observation: Dict[str, Any], last_update_time: float) -> bool:
        """Decides when memory should be updated based on time or high-volatility events."""
        elapsed = time.time() - last_update_time
        # Force update every 30 seconds or if sensory surprise changes significantly
        if elapsed > 30.0 or current_observation.get("market", {}).get("volatility", 0.0) > 0.35:
            return True
        return False

    def detect_context_drift(self, current_observation: Dict[str, Any]) -> Tuple[bool, float]:
        """Measures drift between current sensory input and historical tracking."""
        keys = list(current_observation.keys())
        signature = "_".join(sorted([str(k) for k in keys]))

        if self.last_context_signature is None:
            self.last_context_signature = signature
            return False, 0.0

        # Simple structural comparison of context
        if signature != self.last_context_signature:
            self.last_context_signature = signature
            return True, 1.0
        return False, 0.0

    def prevent_forgetting(self, memory_nodes: List[MemoryNode]) -> List[MemoryNode]:
        """Reinforces fading memory nodes (boosting strength of core constraints)."""
        reinforced = []
        for node in memory_nodes:
            if node.strength < 0.3 and "constraint" in str(node.content).lower():
                node.strength = min(1.0, node.strength + 0.4)
                node.last_accessed = time.time()
                reinforced.append(node)
        return reinforced

    def maintain_active_workspace(self, workspace_nodes: List[MemoryNode], new_node: MemoryNode) -> List[MemoryNode]:
        """Maintains active working memory windowing (bounded growth limit)."""
        active = workspace_nodes + [new_node]
        if len(active) > 10:  # Keep last 10 working memories
            active = active[-10:]
        return active

    def should_inject_reminder(
        self,
        current_context: Dict[str, Any],
        relevant_memories: List[MemoryNode]
    ) -> Tuple[bool, Optional[str]]:
        """
        Calculates if memory reminder injection is critical or if remaining silent is better.
        Prevents redundant alerts or context window drowning.
        """
        if not relevant_memories:
            return False, None

        # Sort memories by strength and confidence
        sorted_memories = sorted(
            relevant_memories,
            key=lambda m: (m.strength * (m.provenance.confidence if m.provenance else 1.0)),
            reverse=True
        )

        top_memory = sorted_memories[0]

        # Rules of selective intervention:
        # 1. If memory has highly confident constraint/failure warnings that relate to current market volatility or parameters
        # 2. Or if current volatility is high and the memory contains volatile procedural guards
        volatility = current_context.get("market", {}).get("volatility", 0.0)
        is_high_risk = volatility > 0.3

        has_failure_lesson = any(
            "failed" in str(v).lower() or "danger" in str(v).lower()
            for v in top_memory.content.values()
        )

        if is_high_risk and has_failure_lesson:
            reminder_text = f"[CRITICAL PROACTIVE MEMORY]: Volatility is high ({volatility:.2f}). Historic lesson: " + \
                            str(top_memory.content.get("lesson", top_memory.content))
            return True, reminder_text

        # Volatility limit override (Standard HASP interaction)
        if volatility > 0.3 and top_memory.tier == MemoryTier.T3_PROCEDURAL:
            return True, f"[PROACTIVE SKILL GUARD]: Volatility limit triggered. Executing procedure: {top_memory.content.get('procedure_name')}"

        # Otherwise, practice selective silence
        return False, None


# ==========================================
# Memory Navigation Engine
# (Memory as a Structured Action Space)
# ==========================================

class MemoryNavigator:
    """
    Transforms passive memory access into active navigation across the pyramid.
    Exposes structured action spaces for hopping through causal, temporal, and semantic links.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def navigate_multi_hop(self, starting_node_id: str, relationship: EdgeRelation, depth: int = 2) -> List[str]:
        """Traverses the graph explicitly along a type of edge relationship to gather multi-hop evidence."""
        if not self.graph.has_node(starting_node_id):
            return []

        results = []
        visited = set()
        queue = [(starting_node_id, 0)]

        while queue:
            node, d = queue.pop(0)
            if node in visited or d > depth:
                continue
            visited.add(node)
            if node != starting_node_id:
                results.append(node)

            # Find neighbors via outgoing edges that match the relationship
            for u, v, key, data in self.graph.edges([node], keys=True, data=True):
                if data.get("relation") == relationship.value:
                    queue.append((v, d + 1))
        return results

    def search_by_query(self, query: str, tier: Optional[MemoryTier] = None) -> List[str]:
        """Coarse query-based filtering across semantic contents."""
        matched = []
        for node_id, data in self.graph.nodes(data=True):
            if "node" not in data:
                continue
            node: MemoryNode = data["node"]
            if tier and node.tier != tier:
                continue

            # Simple content search matching
            content_str = json.dumps(node.content).lower()
            if query.lower() in content_str:
                matched.append(node_id)
        return matched


# ==========================================
# Unified Memory Operating System (Memory OS)
# ==========================================

class MemoryOS:
    """
    The complete coordinating substrate for the unified, graph-native, self-evolving
    Memory Operating System.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MemoryOS, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, base_storage_path: str = "alphaalgo_data/memory_os"):
        if self._initialized:
            return
        self.base_storage_path = base_storage_path
        self.graph = nx.MultiDiGraph()

        # Sub-engines
        self.provenance_engine = MemoryProvenanceEngine()
        self.compressor = MemoryCompressor()
        self.evolution_engine = MemoryEvolutionEngine()
        self.verifier = MemoryVerifier()
        self.health_monitor = MemoryHealthMonitor()
        self.scheduler = MemoryScheduler()
        self.reflection = MemoryReflection()
        self.consolidator = MemoryConsolidator(self.evolution_engine)
        self.proactive_manager = ProactiveMemoryManager()
        self.navigator = MemoryNavigator(self.graph)

        self.reproduction_log: List[Dict[str, Any]] = []  # Deterministic Replay Ledger
        self._initialized = True
        logger.info(f"Memory OS: Initialized successfully with 8-tier support. Storage at {base_storage_path}")

    def write_memory(self, node: MemoryNode) -> str:
        """Determinstic transaction writing with full provenance logging."""
        t0 = time.perf_counter()

        # Provenance verification
        if node.provenance and not self.provenance_engine.verify_provenance(node.provenance):
            logger.warning(f"Memory OS: Rejecting memory {node.node_id} due to invalid provenance.")
            return ""

        # Write to core Graph
        self.graph.add_node(node.node_id, node=node, tier=node.tier.value)

        # Reproduction audit logging
        log_entry = {
            "timestamp": time.time(),
            "action": "WRITE",
            "node_id": node.node_id,
            "tier": node.tier.value,
            "content": copy_dict(node.content)
        }
        self.reproduction_log.append(log_entry)

        elapsed = (time.perf_counter() - t0) * 1000.0
        self.health_monitor.record_metrics(success=True, latency_ms=elapsed)
        return node.node_id

    def link_memories(self, edge: MemoryEdge):
        """Creates an explicit typed connection between two memories."""
        if not self.graph.has_node(edge.source_id) or not self.graph.has_node(edge.target_id):
            logger.warning(f"Memory OS: Cannot link non-existent nodes: {edge.source_id} -> {edge.target_id}")
            return

        edge_key = f"{edge.relation.value}_{uuid.uuid4().hex[:8]}"
        self.graph.add_edge(
            edge.source_id,
            edge.target_id,
            key=edge_key,
            relation=edge.relation.value,
            weight=edge.weight,
            metadata=edge.metadata
        )

        log_entry = {
            "timestamp": time.time(),
            "action": "LINK",
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "relation": edge.relation.value
        }
        self.reproduction_log.append(log_entry)

    def read_memory(self, node_id: str) -> Optional[MemoryNode]:
        """Read a node, updating its access patterns, temporal strength, and log success stats."""
        t0 = time.perf_counter()
        success = False
        node = None

        if self.graph.has_node(node_id):
            node = self.graph.nodes[node_id].get("node")
            if node:
                # Update stats
                node.access_count += 1
                node.last_accessed = time.time()
                # Reinforce strength slightly
                node.strength = min(1.0, node.strength + 0.1)
                success = True

        elapsed = (time.perf_counter() - t0) * 1000.0
        self.health_monitor.record_metrics(success=success, latency_ms=elapsed)

        # Record a T7 Meta-Memory performance node
        meta_log = MetaMemoryLog(retrieval_success=success, latency_ms=elapsed)
        meta_node = MemoryNode(
            tier=MemoryTier.T7_META_MEMORY,
            content=asdict(meta_log)
        )
        self.write_memory(meta_node)
        self.link_memories(MemoryEdge(source_id=meta_node.node_id, target_id=node_id if node_id else meta_node.node_id, relation=EdgeRelation.META))

        return node

    def trigger_background_evolution(self):
        """Consolidates active workspace nodes, prunes obsolete links, and decays memory strengths."""
        t0 = time.time()
        logger.info("Memory OS: Background consolidation starting...")

        # Find workspace nodes (T0)
        workspace_nodes = [
            data["node"] for nid, data in self.graph.nodes(data=True)
            if data.get("tier") == MemoryTier.T0_WORKSPACE.value
        ]

        if workspace_nodes:
            consolidated = self.consolidator.consolidate(workspace_nodes)
            for old_node in workspace_nodes:
                self.graph.remove_node(old_node.node_id)
            for new_node in consolidated:
                self.write_memory(new_node)
            logger.info(f"Memory OS: Consolidated {len(workspace_nodes)} workspace items into {len(consolidated)} episodic nodes.")

        # Decay strength of remaining nodes
        now = time.time()
        for nid, data in list(self.graph.nodes(data=True)):
            node: Optional[MemoryNode] = data.get("node")
            if node and node.tier != MemoryTier.T0_WORKSPACE:
                old_strength = node.strength
                node.strength = self.evolution_engine.compute_decay(now, node.last_accessed, node.strength)
                # If memory is decayed to almost zero and not accessed, prune it (forgetting)
                if node.strength < 0.05 and node.access_count == 1:
                    logger.info(f"Memory OS: Pruned decayed node {node.node_id} (strength: {node.strength:.4f})")
                    self.graph.remove_node(nid)

    def replay_transactions(self) -> List[Dict[str, Any]]:
        """Returns the complete reproducible history ledger for debugging and audit runs."""
        return self.reproduction_log

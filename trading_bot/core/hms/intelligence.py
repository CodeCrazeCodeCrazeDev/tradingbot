"""
CMOS Proactive Memory Intelligence & Navigation
================================================
Phase 5: Proactive memory management and explicit reasoning-driven active
navigation over the CMOS multi-granularity graph-native memory hierarchy.
"""

import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Set

from .ontology import CMOSNode, CMOSNodeTier, CMOSEdge, CMOSEdgeRelation, CMOSProvenance
from .cmos import CognitiveMemoryOS

logger = logging.getLogger(__name__)


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
        """Decides when memory should be updated based on elapsed time or volatility spikes."""
        elapsed = time.time() - last_update_time
        # Force update every 30 seconds or if market volatility gets dangerously high (>0.35)
        volatility = current_observation.get("market", {}).get("volatility", 0.0)
        if elapsed > 30.0 or volatility > 0.35:
            return True
        return False

    def detect_context_drift(self, current_observation: Dict[str, Any]) -> Tuple[bool, float]:
        """Measures structural context drift from baseline parameters."""
        keys = list(current_observation.keys())
        signature = "_".join(sorted([str(k) for k in keys]))

        if self.last_context_signature is None:
            self.last_context_signature = signature
            return False, 0.0

        if signature != self.last_context_signature:
            self.last_context_signature = signature
            return True, 1.0
        return False, 0.0

    def prevent_forgetting(self, memory_nodes: List[CMOSNode]) -> List[CMOSNode]:
        """Reinforces fading memory nodes (boosting strength of core constraints)."""
        reinforced = []
        for node in memory_nodes:
            # If memory strength is decaying below threshold, and is a constraint, reinforce it
            if node.strength < 0.3 and "constraint" in str(node.content).lower():
                node.strength = min(1.0, node.strength + 0.4)
                node.last_accessed = time.time()
                reinforced.append(node)
        return reinforced

    def maintain_active_workspace(self, workspace_nodes: List[CMOSNode], new_node: CMOSNode) -> List[CMOSNode]:
        """Maintains active working memory windowing (bounded growth limit)."""
        active = workspace_nodes + [new_node]
        if len(active) > 10:  # Bound workspace size to last 10 entries
            active = active[-10:]
        return active

    def should_inject_reminder(
        self,
        current_context: Dict[str, Any],
        relevant_memories: List[CMOSNode]
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
        if volatility > 0.3 and top_memory.tier == CMOSNodeTier.T3_PROCEDURAL:
            return True, f"[PROACTIVE SKILL GUARD]: Volatility limit triggered. Executing procedure: {top_memory.content.get('procedure_name')}"

        # Otherwise, practice selective silence (silence is better than distraction)
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

    def __init__(self, cmos_core: CognitiveMemoryOS):
        self.cmos = cmos_core

    def navigate_multi_hop(self, starting_node_id: str, relationship: CMOSEdgeRelation, depth: int = 2) -> List[str]:
        """Traverses the graph explicitly along a type of edge relationship to gather multi-hop evidence."""
        graph = self.cmos.repository.graph
        if not graph.has_node(starting_node_id):
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
            for u, v, key, data in graph.edges([node], keys=True, data=True):
                if data.get("relation") == relationship.value:
                    queue.append((v, d + 1))
        return results

    def search_by_query(self, query: str, tier: Optional[CMOSNodeTier] = None) -> List[str]:
        """Coarse query-based filtering across semantic contents."""
        graph = self.cmos.repository.graph
        matched = []
        for node_id, data in graph.nodes(data=True):
            node: Optional[CMOSNode] = data.get("node")
            if not node:
                continue
            if tier and node.tier != tier:
                continue

            content_str = str(node.content).lower()
            if query.lower() in content_str:
                matched.append(node_id)
        return matched

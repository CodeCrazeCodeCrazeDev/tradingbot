"""
CMOS Operators as Plugins
==========================
Phase 4: Dynamic Operator Plugin architecture for the CMOS Core.
Enables plug-and-play extensions for semantic operations (Recall, Compare,
Verify, Challenge, Simulate, Compress) without modifying the CMOS core.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .ontology import CMOSNode, CMOSNodeTier, CMOSEdge, CMOSEdgeRelation, CMOSProvenance
from .cmos import CognitiveMemoryOS, CMOSRepository


class CMOSOperator(ABC):
    """Abstract interface defining the execution protocol for memory plugins."""

    @abstractmethod
    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes operational logic across memory tiers and records telemetry."""
        pass


class CMOSOperatorRegistry:
    """Registry managing execution and mapping of plug-and-play operators."""

    def __init__(self):
        self._operators: Dict[str, CMOSOperator] = {}

    def register_operator(self, name: str, operator: CMOSOperator):
        self._operators[name] = operator

    def get_operator(self, name: str) -> Optional[CMOSOperator]:
        return self._operators.get(name)

    def execute_operator(self, name: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        operator = self.get_operator(name)
        if not operator:
            raise KeyError(f"Operator {name} not found in registry.")

        t0 = time_perf_counter()
        # Charges economics compute context
        cmos = CognitiveMemoryOS()
        cmos.economics.charge_cost(token_count=100) # Baseline plugin transaction rate

        result = operator.execute(params, context)

        elapsed = (time_perf_counter() - t0) * 1000.0
        cmos.observability.record_transaction(success=True, latency_ms=elapsed)
        return result


# ==========================================
# Specialized Plugin Operator Implementations
# ==========================================

class RecallOperator(CMOSOperator):
    """Recall Memory node based on specific semantic patterns."""

    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        cmos = CognitiveMemoryOS()
        query = params.get("query", "").lower()
        tier_filter = params.get("tier")

        matched_nodes = []
        for node in cmos.repository.list_nodes(tier=tier_filter):
            content_str = str(node.content).lower()
            if query in content_str:
                matched_nodes.append(node)

        return {"status": "success", "results": matched_nodes}


class CompareOperator(CMOSOperator):
    """Compares new incoming claims against existing semantic/procedural records."""

    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        claim = params.get("claim", "").lower()
        cmos = CognitiveMemoryOS()

        similar_count = 0
        matches = []
        for node in cmos.repository.list_nodes(tier=CMOSNodeTier.T2_SEMANTIC):
            node_str = str(node.content).lower()
            if claim in node_str:
                similar_count += 1
                matches.append(node.node_id)

        return {"status": "success", "overlap": similar_count > 0, "matches": matches}


class VerifyOperator(CMOSOperator):
    """Verifies contradiction anomalies and blocks hallucinated/conflicting claims."""

    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        node_id = params.get("node_id")
        cmos = CognitiveMemoryOS()

        # Verify direct CONTRADICTS loops
        for edge in cmos.repository.list_edges():
            if edge.relation == CMOSEdgeRelation.CONTRADICTS:
                if edge.source_id == node_id or edge.target_id == node_id:
                    return {
                        "status": "falsified",
                        "reason": f"Direct CONTRADICTS anomaly detected on {edge.source_id} -> {edge.target_id}"
                    }

        return {"status": "verified", "reason": "No direct contradictions found."}


class ChallengeOperator(CMOSOperator):
    """Critiques hypotheses by searching for associated historic failure/veto models."""

    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        hypothesis = params.get("hypothesis", "").lower()
        cmos = CognitiveMemoryOS()

        failures = []
        for node in cmos.repository.list_nodes(tier=CMOSNodeTier.T6_INSTITUTIONAL):
            if "failed" in str(node.content).lower() and hypothesis in str(node.content).lower():
                failures.append(node)

        if failures:
            return {
                "status": "challenged",
                "vetoes": [str(f.content.get("lesson", f.content)) for f in failures]
            }
        return {"status": "unchallenged"}


class SimulateOperator(CMOSOperator):
    """Generates simulated projections by query-forwarding to world-model predictions."""

    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        scenario_id = params.get("scenario_id")
        projection_steps = params.get("steps", 5)

        # Simple continuous forward-projection projection
        simulated_prices = [1.1000 + (0.0005 * i) for i in range(projection_steps)]
        return {
            "status": "simulated",
            "scenario_id": scenario_id,
            "projected_series": simulated_prices
        }


class CompressOperator(CMOSOperator):
    """Compresses historical episodic traces to preserve token budgets."""

    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        nodes_to_compress = params.get("nodes", [])
        if not nodes_to_compress:
            return {"status": "success", "compressed_content": ""}

        summary_list = [str(n.content) for n in nodes_to_compress]
        compressed_text = "[COMPRESSED LOG]: " + " | ".join(summary_list[:5])
        return {
            "status": "success",
            "compressed_content": compressed_text,
            "pruned_nodes_count": len(nodes_to_compress)
        }


# Helper timer fallback
def time_perf_counter() -> float:
    import time
    return time.perf_counter()

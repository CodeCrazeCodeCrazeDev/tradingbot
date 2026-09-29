"""CDS Orchestrator — The Unified Cognitive Decision System Core.

This module unifies TALOS, PHCE-D, and the Adversarial engines into a single pipeline.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from .evidence_graph import EvidenceGraph, CDSElement, NodeType, RelationType, PersistentEvidenceStore
from .epistemology_engine import EpistemologyEngine
from .verdict_engine import VerdictEngine, FinalVerdictOutcome
from .governance_gate import GovernanceGate, GovernanceStatus


class CDSOrchestrator:
    """The Unified Cognitive Decision System Orchestrator."""

    def __init__(
        self,
        epistemology_config: Optional[Dict[str, Any]] = None,
        verdict_config: Optional[Dict[str, Any]] = None,
        storage_path: str = "cds_evidence_history.jsonl"
    ):
        self.epistemology = EpistemologyEngine(epistemology_config)
        self.verdict_engine = VerdictEngine()
        self.governance = GovernanceGate()
        self.evidence_store = PersistentEvidenceStore(storage_path)
        self.logger = logging.getLogger("cds.orchestrator")

    async def decide(
        self,
        symbol: str,
        hypothesis_data: Dict[str, Any],
        evidence_list: List[Dict[str, Any]],
        market_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the full 11-stage CDS pipeline."""

        start_time = time.time()
        decision_id = f"cds-{uuid.uuid4().hex[:12]}"

        # Initialize Graph
        graph = EvidenceGraph()

        # 1-4. Evidence & Hypothesis (TALOS/PHCE-D context)
        h_element = CDSElement(
            id=f"h-{decision_id}",
            type=NodeType.HYPOTHESIS,
            content=hypothesis_data,
            metadata={"symbol": symbol}
        )
        graph.add_node(h_element)

        for i, ev in enumerate(evidence_list):
            ev_id = f"e-{decision_id}-{i}"
            ev_element = CDSElement(
                id=ev_id,
                type=NodeType.EVIDENCE,
                content=ev,
                confidence=ev.get("confidence", 1.0),
                metadata={"evidence_type": ev.get("type", "unknown")}
            )
            graph.add_node(ev_element)

            relation = RelationType.SUPPORTS if ev.get("direction") == hypothesis_data.get("direction") else RelationType.CONTRADICTS
            graph.add_relation(ev_id, h_element.id, relation, weight=ev.get("weight", 1.0))

        # 5-6. Adversarial Epistemology
        epistemic_report = self.epistemology.analyze_hypothesis(h_element.id, graph)

        # 7-10. Adversarial Verdict Engine (Debate & Governance)
        final_verdict = await self.verdict_engine.synthesize(hypothesis_data, evidence_list)

        governance_report = self.governance.check(final_verdict, market_context or {})

        # 11. Final Decision Construction
        execution_allowed = (
            final_verdict.outcome == FinalVerdictOutcome.APPROVED and
            governance_report.status == GovernanceStatus.PASSED
        )

        # Proof Trace
        trace = graph.export_trace(h_element.id)
        trace["epistemic_report"] = epistemic_report.__dict__
        trace["final_verdict"] = final_verdict.__dict__
        trace["governance_report"] = governance_report.__dict__
        trace["decision_id"] = decision_id

        # Persist for self-improvement
        self.evidence_store.persist_trace(trace)

        latency = (time.time() - start_time) * 1000

        self.logger.info(f"CDS Decision {decision_id}: {final_verdict.outcome} for {symbol} ({latency:.2f}ms)")

        return {
            "decision_id": decision_id,
            "symbol": symbol,
            "outcome": final_verdict.outcome.value,
            "approved": execution_allowed,
            "belief_score": final_verdict.belief_score,
            "uncertainty": final_verdict.uncertainty,
            "explanation": final_verdict.explanation,
            "trace": trace,
            "latency_ms": latency
        }

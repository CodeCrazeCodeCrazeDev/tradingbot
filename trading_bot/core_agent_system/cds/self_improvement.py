"""Self-Improvement Engine for the CDS.

Uses historical decision traces and outcomes to re-calibrate evidence weights
and reviewer calibration.
"""

from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Optional
from .evidence_graph import PersistentEvidenceStore

class CDSSelfImprovement:
    """Analyzes historical decisions to improve future decision quality."""

    def __init__(self, storage_path: str = "cds_evidence_history.jsonl"):
        self.store = PersistentEvidenceStore(storage_path)
        self.logger = logging.getLogger("cds.self_improvement")

    def run_calibration_cycle(self) -> Dict[str, Any]:
        """Analyze historical traces and outcomes to recommend weight updates."""
        traces = self.store.load_historical_failures()
        if not traces:
            return {"status": "no_data", "message": "Insufficient historical data for calibration."}

        # 1. Analyze Reviewer Accuracy
        # (In a real system, we would match these against realized PnL from Outcome Memory)
        reviewer_performance = {}

        for trace in traces:
            verdict = trace.get("final_verdict", {})
            for rv in verdict.get("reviewer_verdicts", []):
                role = rv.get("role")
                if role not in reviewer_performance:
                    reviewer_performance[role] = {"count": 0, "rejected_correctly": 0}

                reviewer_performance[role]["count"] += 1
                if rv.get("verdict") == "REJECT" and verdict.get("outcome") == "REJECTED":
                    reviewer_performance[role]["rejected_correctly"] += 1

        # 2. Generate Calibration Proposals
        proposals = []
        for role, stats in reviewer_performance.items():
            accuracy = stats["rejected_correctly"] / stats["count"]
            if accuracy > 0.8:
                proposals.append({
                    "target": f"reviewer.{role}",
                    "action": "increase_weight",
                    "reason": f"High rejection accuracy: {accuracy:.2%}"
                })
            elif accuracy < 0.4:
                proposals.append({
                    "target": f"reviewer.{role}",
                    "action": "decrease_weight",
                    "reason": f"Low rejection accuracy: {accuracy:.2%}"
                })

        return {
            "status": "success",
            "num_traces_analyzed": len(traces),
            "reviewer_performance": reviewer_performance,
            "proposals": proposals
        }

    def learn_from_failure(self, decision_id: str, actual_outcome: Dict[str, Any]):
        """Specialized learning from a catastrophic failure or significant loss."""
        # This would be called by the Unified Swarm Intelligence System (USIS)
        # after a trade outcome is realized.
        self.logger.info(f"Learning from decision {decision_id} failure: {actual_outcome.get('reason')}")
        # In practice: Update long-term failure memory graph

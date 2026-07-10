"""
Folding Operator - HIPIF Strategy
================================

Responsible for compressing high-resolution episodic traces into
low-resolution semantic knowledge.
Implements 'HIPIF: Hierarchical Planning and Information Folding' (arXiv:2606.10507).
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class InformationFolder:
    """
    Compresses execution history into semantic strategic updates.
    Prevents 'Strategic Drift' in long-horizon tasks by extracting sufficient statistics.
    """

    def __init__(self, fold_interval: int = 10):
        self.fold_interval = fold_interval
        self.step_counter = 0
        self.folded_summaries: List[Dict[str, Any]] = []

    async def fold_step(self, episodic_trace: List[Dict[str, Any]]):
        """Processes a single execution step and triggers folding if interval reached."""
        self.step_counter += 1
        if self.step_counter % self.fold_interval == 0:
            return await self.perform_folding(episodic_trace)
        return None

    def fold_history(self, ledger_entry: Any) -> str:
        """
        Folds the current research snapshot into a semantic summary.
        Extracts patterns, success/failure status, and calibration info.
        """
        logger.info(f"HIPIF: Folding research snapshot {getattr(ledger_entry, 'entry_id', 'unknown')}")

        # 1. Extract sufficient statistics
        stats = self._extract_sufficient_statistics(ledger_entry)

        # 2. Generate semantic summary
        summary = self._generate_semantic_summary(stats)

        # 3. Store in internal folded history
        self.folded_summaries.append({
            "timestamp": datetime.utcnow().isoformat(),
            "summary": summary,
            "stats": stats
        })

        return summary

    async def perform_folding(self, episodic_trace: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Implements Information Folding on a trace of episodic events:
        1. Extract 'Sufficient Statistics' (Patterns, Success/Failure, Calibration).
        2. Generate semantic update.
        3. Prune/Compress source Episodic entries conceptually.
        """
        logger.info(f"HIPIF: Folding episodic trace of {len(episodic_trace)} entries")

        summary = self._summarize_trace(episodic_trace)
        stats = {
            "num_entries": len(episodic_trace),
            "dominant_event_type": self._get_dominant_type(episodic_trace),
            "success_rate": self._calculate_success_rate(episodic_trace)
        }

        result = {
            'semantic_update': summary,
            'sufficient_statistics': stats,
            'tokens_saved': sum(len(str(s)) for s in episodic_trace) - len(summary),
            'status': 'folded'
        }

        self.folded_summaries.append(result)
        return result

    def _extract_sufficient_statistics(self, ledger_entry: Any) -> Dict[str, Any]:
        """Extracts core numerical and categorical indicators from a ledger entry."""
        return {
            "hypothesis_id": getattr(ledger_entry.hypothesis, "hypothesis_id", "N/A") if ledger_entry.hypothesis else "N/A",
            "confidence": getattr(ledger_entry, "composite_confidence", 0.0),
            "num_verifier_reports": len(getattr(ledger_entry, "verifier_reports", [])),
            "consensus_reached": all(r.is_valid for r in getattr(ledger_entry, "verifier_reports", [])) if getattr(ledger_entry, "verifier_reports", []) else False
        }

    def _generate_semantic_summary(self, stats: Dict[str, Any]) -> str:
        """Converts statistics into a concise natural language summary."""
        consensus_str = "with consensus" if stats["consensus_reached"] else "without consensus"
        return f"Research step for {stats['hypothesis_id']} completed {consensus_str}. Confidence: {stats['confidence']:.2f}."

    def _summarize_trace(self, trace: List[Dict[str, Any]]) -> str:
        """Generic trace summarization."""
        if not trace: return "Empty trace."
        return f"Trace of {len(trace)} events. Last action: {trace[-1].get('action_type', 'unknown')}."

    def _get_dominant_type(self, trace: List[Dict[str, Any]]) -> str:
        types = [t.get('action_type', 'unknown') for t in trace]
        if not types: return "unknown"
        return max(set(types), key=types.count)

    def _calculate_success_rate(self, trace: List[Dict[str, Any]]) -> float:
        successes = [1 for t in trace if t.get('status') == 'success' or t.get('status') == 'approved']
        if not trace: return 0.0
        return len(successes) / len(trace)

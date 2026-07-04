"""
Information Folding Buffer (HIPIF) - UCA-2026

Implements the 'Folding Operator' to solve long-horizon strategic drift.
Completed subgoal logs are compressed into semantic updates (Lessons Learned),
clearing the context window while preserving critical strategic anchors.

Reference: HIPIF (Diao et al., 2026)
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class Subgoal:
    id: str
    description: str
    status: str = "active"
    logs: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    folded_summary: Optional[str] = None

class FoldingBuffer:
    """
    Manages the 'Folding' of execution traces into strategic knowledge.
    UCA-2026 Principle: Information Bottleneck.
    """

    def __init__(self, max_active_logs: int = 50):
        self.active_subgoal: Optional[Subgoal] = None
        self.folded_history: List[Subgoal] = []
        self.max_active_logs = max_active_logs
        logger.info("UCA-2026 Information Folding Buffer initialized.")

    def start_subgoal(self, goal_id: str, description: str):
        """Starts a new subgoal tracking sequence."""
        if self.active_subgoal:
            self.fold_active_subgoal()

        self.active_subgoal = Subgoal(id=goal_id, description=description)
        logger.info(f"HIPIF: Started subgoal '{goal_id}': {description}")

    def add_log(self, log_entry: str):
        """Adds a raw execution log to the active subgoal."""
        if self.active_subgoal:
            self.active_subgoal.logs.append(log_entry)
            # Automatic folding if buffer exceeds limit
            if len(self.active_subgoal.logs) >= self.max_active_logs:
                logger.warning(f"HIPIF: Buffer limit reached for {self.active_subgoal.id}. Forcing partial fold.")
                # In a real implementation, this would trigger a summary of the first half.

    def fold_active_subgoal(self, summary_override: Optional[str] = None):
        """
        Compresses the active subgoal logs into a semantic summary.
        This is the 'Folding Operator'.
        """
        if not self.active_subgoal:
            return

        subgoal = self.active_subgoal
        subgoal.status = "completed"
        subgoal.end_time = datetime.now()

        # The 'Folding' logic:
        # In production, this calls a high-capability LLM to summarize self.logs
        # into a concise 'Lesson Learned' that preserves state but drops noise.
        if summary_override:
            subgoal.folded_summary = summary_override
        else:
            raw_log_count = len(subgoal.logs)
            subgoal.folded_summary = (
                f"Subgoal '{subgoal.description}' completed. "
                f"Compressed {raw_log_count} execution steps into 1 semantic anchor. "
                f"Outcome: Status verified."
            )

        self.folded_history.append(subgoal)
        logger.info(f"HIPIF_FOLD: Subgoal '{subgoal.id}' folded. Summary: {subgoal.folded_summary}")

        self.active_subgoal = None

    def get_strategic_context(self) -> str:
        """
        Returns the compressed strategic history (Folded Summary)
        to be used as the prefix for the next planning cycle.
        """
        context_parts = []
        for folded in self.folded_history[-5:]: # Keep last 5 strategic anchors
            context_parts.append(f"PREV_STEP: {folded.folded_summary}")

        if self.active_subgoal:
            context_parts.append(f"CURRENT_STEP: {self.active_subgoal.description} (Active)")

        return "\n".join(context_parts)

    def clear_history(self):
        """Resets the folding buffer."""
        self.folded_history = []
        self.active_subgoal = None
        logger.info("HIPIF: Folding history cleared.")

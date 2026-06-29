"""
Hypothesis Engine for Multidimensional Intelligence.
Handles generation, prioritization, and tracking of scientific hypotheses.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import IntelligenceDomain, Hypothesis

logger = logging.getLogger(__name__)


class HypothesisEngine:
    """
    Hypothesis Engine
    Responsible for managing cross-domain hypotheses.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.hypotheses: Dict[str, Hypothesis] = {}

    async def pose_hypothesis(
        self,
        domain: IntelligenceDomain,
        concept: str,
        mathematical_representation: str,
        description: str,
        expected_outcome: str,
        priority: float = 0.5
    ) -> Hypothesis:
        """Create and register a new hypothesis."""
        hypothesis_id = f"hyp_{domain.value[:3]}_{uuid.uuid4().hex[:8]}"
        hypothesis = Hypothesis(
            hypothesis_id=hypothesis_id,
            domain=domain,
            concept=concept,
            mathematical_representation=mathematical_representation,
            description=description,
            expected_outcome=expected_outcome,
            priority=priority,
            created_at=datetime.now(),
            status="pending"
        )

        self.hypotheses[hypothesis_id] = hypothesis
        logger.info(f"Posed new hypothesis: {hypothesis_id} - {concept}")
        return hypothesis

    def get_pending_hypotheses(self, min_priority: float = 0.0) -> List[Hypothesis]:
        """Get list of pending hypotheses above a priority threshold."""
        return [
            h for h in self.hypotheses.values()
            if h.status == "pending" and h.priority >= min_priority
        ]

    def update_hypothesis_status(self, hypothesis_id: str, status: str):
        """Update the status of a hypothesis."""
        if hypothesis_id in self.hypotheses:
            self.hypotheses[hypothesis_id].status = status
            logger.info(f"Hypothesis {hypothesis_id} status updated to {status}")

    def get_all_hypotheses(self) -> List[Hypothesis]:
        """Return all registered hypotheses."""
        return list(self.hypotheses.values())

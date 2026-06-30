"""
Improvement Gatekeeper
Enforces safety and human-in-the-loop approval for system improvements.
"""

import logging
from typing import Any, Dict, List, Optional
from .registry import ImprovementRegistry, ImprovementStatus, ImprovementType

logger = logging.getLogger(__name__)

class ImprovementGatekeeper:
    """
    Final validation gate before promotion to production.
    """
    def __init__(self, registry: ImprovementRegistry, config: Optional[Dict] = None):
        self.registry = registry
        self.config = config or {}
        self.require_human_approval = self.config.get('require_human_approval', True)

    async def check_promotion_eligibility(self, improvement_id: str) -> Dict[str, Any]:
        """
        Check if an improvement is eligible for promotion.
        """
        record = self.registry.get_record(improvement_id)
        if not record:
            return {"eligible": False, "reason": "Record not found"}

        if record.status != ImprovementStatus.SHADOW:
            return {"eligible": False, "reason": "Not in SHADOW status"}

        # Safety Logic
        if record.type == ImprovementType.CODE and self.require_human_approval:
            return {
                "eligible": False,
                "reason": "CODE improvement requires manual approval signal",
                "action_required": "APPROVE_IMPROVEMENT"
            }

        # Check performance in shadow
        shadow_pnl = record.evidence.get('shadow_pnl', 0)
        baseline_pnl = record.evidence.get('baseline_pnl', 0)

        if shadow_pnl > baseline_pnl:
            return {"eligible": True, "confidence": 0.9}

        return {"eligible": False, "reason": "Shadow performance did not exceed baseline"}

    async def approve_improvement(self, improvement_id: str, approver_id: str):
        """
        Manually approve an improvement for promotion.
        """
        record = self.registry.get_record(improvement_id)
        if record:
            logger.info(f"Improvement {improvement_id} APPROVED by {approver_id}")
            self.registry.update_status(improvement_id, ImprovementStatus.PRODUCTION, {"approved_by": approver_id})
            return True
        return False

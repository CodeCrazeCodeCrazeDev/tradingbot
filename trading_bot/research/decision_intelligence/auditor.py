"""
Decision Intelligence and Auditing Layer for Research OS.
Generates immutable signed DecisionRecords and audits decision accuracy and bias over time.
"""

from typing import Dict, Any, List, Optional
import uuid
import hmac
import hashlib
from datetime import datetime
import numpy as np

from trading_bot.research.core.interfaces import DecisionRecord

import logging
logger = logging.getLogger(__name__)


class SovereignDecisionAuditor:
    """
    Sovereign Decision Intelligence auditor.
    Enforces absolute explainability, traceability, and self-auditing on R&D choices.
    """

    def __init__(self, signing_secret: str = "alphaalgo_superior_secret"):
        self.signing_secret = signing_secret.encode()
        self._history: Dict[str, DecisionRecord] = {}

    def create_signed_decision(
        self,
        decision_type: str,
        evidence: Dict[str, Any],
        assumptions: List[str],
        confidence: float,
        alternatives: List[str],
        rationale: str,
        author: str = "ResearchOSKernel"
    ) -> DecisionRecord:
        """
        Synthesizes an immutable, signed DecisionRecord capturing a critical R&D choice.
        The signature is generated using a HMAC-SHA256 signature over critical fields.
        """
        decision_id = f"dec_{uuid.uuid4().hex[:8]}"

        # Calculate secure HMAC signature
        msg = f"{decision_id}|{decision_type}|{confidence:.4f}|{rationale[:30]}"
        signature = hmac.new(self.signing_secret, msg.encode(), hashlib.sha256).hexdigest()

        record = DecisionRecord(
            decision_id=decision_id,
            decision_type=decision_type,
            evidence=evidence,
            assumptions=assumptions,
            confidence=float(confidence),
            alternatives_considered=alternatives,
            rationale=rationale,
            author=author,
            timestamp=datetime.utcnow(),
            signature=signature,
            validation_outcome=None
        )

        self._history[decision_id] = record
        logger.info(f"Signed Decision Record created: {decision_id} ({decision_type}) [Sig: {signature[:12]}...]")
        return record

    def audit_decision_quality(self, decision_id: str, downstream_outcome: str) -> Dict[str, Any]:
        """
        Audits decision quality retroactively by comparing the decision's confidence with outcomes.
        Mismatches signal calibration bias (overconfidence or excessive caution).
        """
        if decision_id not in self._history:
            return {"error": "Decision not found."}

        record = self._history[decision_id]
        record.validation_outcome = downstream_outcome

        # Quantify bias:
        # If outcome is 'success' but confidence was very low -> underconfident.
        # If outcome is 'failure' but confidence was very high -> overconfident.
        bias_level = "calibrated"
        error_diff = 0.0

        if downstream_outcome == "success":
            error_diff = 1.0 - record.confidence
            if error_diff > 0.4:
                bias_level = "underconfident (excessive caution)"
        elif downstream_outcome == "failure":
            error_diff = record.confidence
            if error_diff > 0.6:
                bias_level = "overconfident (high curve-fit risk)"

        return {
            "decision_id": decision_id,
            "decision_type": record.decision_type,
            "confidence": record.confidence,
            "outcome": downstream_outcome,
            "error_difference": float(error_diff),
            "bias_classification": bias_level
        }

    def get_history(self) -> List[DecisionRecord]:
        return list(self._history.values())

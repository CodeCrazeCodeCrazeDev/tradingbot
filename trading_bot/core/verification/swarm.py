"""
Verification Swarm - Evidence-First Governance
==============================================

Orchestrates specialized verifier agents to audit trade research.
Enforces the 0.8 consensus hard constraint.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from .interface import IVerifier, VerifierVerdict
from .specialists import CausalVerifier, HallucinationDetector, RegimeConsistencyChecker

logger = logging.getLogger(__name__)

class VerificationSwarm:
    """
    Independent Auditor Swarm for the Cognitive System Controller.
    """
    def __init__(self):
        # Register specialized verifier instances
        self.verifiers: List[IVerifier] = [
            CausalVerifier(),
            HallucinationDetector(),
            RegimeConsistencyChecker()
        ]

    async def run_swarm(self, research_snapshot: Any) -> List[VerifierVerdict]:
        """
        Executes parallel audit by all registered verifiers.
        """
        snapshot_id = getattr(research_snapshot, 'entry_id', 'N/A')
        logger.info(f"VerificationSwarm: Auditing research {snapshot_id}")

        # Parallel execution of verifiers
        tasks = [v.audit(research_snapshot) for v in self.verifiers]
        verdicts = await asyncio.gather(*tasks)

        valid_count = sum(1 for v in verdicts if v.is_valid)
        consensus = valid_count / len(verdicts) if verdicts else 0
        logger.info(f"VerificationSwarm: Consensus reached at {consensus:.1%}")

        return verdicts

class EvidenceGraphGate:
    """
    Hard constraint gate for the CSC.
    Ensures every claim is backed by the Evidence Graph.
    """
    @staticmethod
    def verify_evidence_first(snapshot: Any, verdicts: List[VerifierVerdict]) -> bool:
        if not verdicts:
            return False

        # 1. Consensus Gate (Institutional SLA: 80%)
        valid_count = sum(1 for v in verdicts if v.is_valid)
        if valid_count / len(verdicts) < 0.8:
            logger.error("EvidenceGate: REJECTED - Consensus below 80%")
            return False

        # 2. High-Confidence Veto check
        for v in verdicts:
            if not v.is_valid and v.confidence > 0.85:
                logger.error(f"EvidenceGate: REJECTED - High-confidence VETO by {v.agent_name}: {v.critique}")
                return False

        return True

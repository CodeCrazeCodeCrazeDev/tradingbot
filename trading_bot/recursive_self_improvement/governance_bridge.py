import logging
from typing import Any, Dict, Optional, Tuple
from ..core_agent_system.governance_system import GovernanceSystem

logger = logging.getLogger(__name__)

class RSIGovernanceBridge:
    """
    Bridge between Recursive Self-Improvement and the core GovernanceSystem.
    Enforces safety boundaries and constitutional checks on all autonomous deployments.
    """

    def __init__(self, governance_system: GovernanceSystem):
        self.governance = governance_system

    async def validate_improvement(self, domain: str, proposal: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """
        Validate a proposed improvement against governance policies.
        """
        logger.info(f"RSI Governance Bridge validating {domain} improvement")

        # 1. Basic Risk Check (Level 1: Configuration)
        # Construct an 'action' for governance to verify
        action = {
            "type": "rsi_deployment",
            "domain": domain,
            "parameters": proposal["parameters"],
            "confidence": result["evaluation"].get("confidence_score", 0.0),
            "expected_impact": result["evaluation"].get("overall_score", 0.0)
        }

        is_compliant, violations = await self.governance.check_compliance(
            agent_id="RSI_Engine",
            action=action,
            context={"market_regime": "unknown"} # Simplified context
        )

        if not is_compliant:
            logger.warning(f"RSI Improvement rejected by governance: {violations}")
            return False

        # 2. Performance Threshold Check (Immutable Rule)
        if result["evaluation"]["overall_score"] < 0:
            logger.warning("RSI Improvement rejected: Negative overall impact score")
            return False

        # 3. Critical Component Check
        if domain in ["core", "security", "risk"]:
            logger.info("RSI Improvement requires manual approval for critical domains")
            # In a real system, this would trigger an approval request
            return False

        return True

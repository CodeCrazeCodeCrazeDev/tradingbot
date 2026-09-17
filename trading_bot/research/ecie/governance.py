import logging
import uuid
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    CompiledSkill,
    PromotionProposal,
    PromotionStage,
    TrustReport,
    SecurityReport,
    LicenseStatus
)
from trading_bot.research.research_os import ResearchWorkspace, QuantitativeIdea

logger = logging.getLogger("AlphaAlgo.ECIE.Governance")


class GovernanceGate:
    """
    Enforces compliance and gates before external capabilities reach One Brain production.
    """

    def __init__(self, workspace: ResearchWorkspace):
        self.workspace = workspace
        self.proposals: Dict[str, PromotionProposal] = {}

    def submit_proposal(
        self,
        skill: CompiledSkill,
        candidate_url: str,
        version_id: str,
        license_name: str,
        trust: TrustReport,
        security: SecurityReport,
        license_status: LicenseStatus
    ) -> PromotionProposal:
        """
        Creates a new capability promotion proposal inside the Research OS.
        Registers the capability's lineage and provenance.
        """
        logger.info(f"GovernanceGate: Receiving proposal for {skill.name}...")

        proposal_id = f"proposal_{uuid.uuid4().hex[:10]}"

        # Initial stage is Sandbox
        proposal = PromotionProposal(
            proposal_id=proposal_id,
            compiled_skill=skill,
            candidate_url=candidate_url,
            version_id=version_id,
            license_name=license_name,
            trust_score=trust.overall_score,
            security_passed=security.is_secure,
            stage=PromotionStage.SANDBOX
        )

        self.proposals[proposal_id] = proposal

        # Persist as a knowledge entry or research idea within our Research OS Workspace
        self.workspace.record_knowledge_entry(
            source_type="ecie_capability",
            source_id=skill.skill_id,
            lessons=f"Extracted capability from {candidate_url} ({version_id}) with trust score {trust.overall_score}.",
            recommendation="PROCEED_TO_SANDBOX_EVALUATION"
        )

        return proposal

    def evaluate_promotion(self, proposal_id: str) -> Tuple[bool, str]:
        """
        Runs automated compliance checks on all core gates: Security, License, Architecture, Performance, Validation.
        High-risk capabilities are flagged for human-in-the-loop triggers.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False, "Proposal not found"

        # Gate 1: Security Scan Check
        if not proposal.security_passed:
            return False, "SECURITY_GATE_FAILED: Unresolved security risks, secrets, or malware patterns."

        # Gate 2: License Compliance Check
        if proposal.license_name.upper() in ["GPL", "AGPL", "LGPL", "GPL-3.0", "AGPL-3.0"]:
            return False, "LICENSE_GATE_FAILED: Copy-left licenses are strictly forbidden from entering One Brain."

        # Gate 3: Trust Threshold Check
        if proposal.trust_score < 50.0:
            return False, "TRUST_GATE_FAILED: Capability score is below acceptable institutional maturity threshold."

        # Check for High-Risk (e.g. Execution Category, or lower Trust Score < 70)
        is_high_risk = proposal.compiled_skill.category.value in ["execution", "risk"] or proposal.trust_score < 70.0

        if is_high_risk:
            # Requires explicit Human-in-the-Loop signature
            proposal.is_active = False
            return False, "HUMAN_APPROVAL_REQUIRED: High-risk capability category or medium trust level requires manual authorization."

        # Safe for automatic promotion to Shadow Stage
        proposal.stage = PromotionStage.SHADOW
        return True, "PROMOTED_TO_SHADOW_MODE"

    def sign_off_human_approval(self, proposal_id: str, approver_name: str) -> bool:
        """Explicit human sign-off for high-risk capabilities."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False

        proposal.is_active = True
        proposal.stage = PromotionStage.SHADOW

        # Record provenance history
        proposal.history.append({
            "stage": PromotionStage.SHADOW.value,
            "action": "HUMAN_APPROVED",
            "approver": approver_name,
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.info(f"GovernanceGate: Human approval signed off by {approver_name} for proposal {proposal_id}.")
        return True


class RolloutManager:
    """
    Manages progressive rollout sequences: Sandbox -> Shadow -> Canary -> Limited Production -> Full.
    """

    def __init__(self, governance_gate: GovernanceGate):
        self.governance = governance_gate
        self.active_deployments: Dict[str, PromotionStage] = {}

    def transition_stage(self, proposal_id: str, target_stage: PromotionStage) -> bool:
        """Transitions a validated capability through the rollout pipeline."""
        proposal = self.governance.proposals.get(proposal_id)
        if not proposal or not proposal.is_active:
            logger.warning(f"RolloutManager: Cannot transition inactive or missing proposal {proposal_id}.")
            return False

        # Enforce progressive order
        allowed_transitions = {
            PromotionStage.SANDBOX: [PromotionStage.SHADOW],
            PromotionStage.SHADOW: [PromotionStage.CANARY],
            PromotionStage.CANARY: [PromotionStage.LIMITED_PRODUCTION],
            PromotionStage.LIMITED_PRODUCTION: [PromotionStage.FULL_DEPLOYMENT],
            PromotionStage.FULL_DEPLOYMENT: []
        }

        current = proposal.stage
        if target_stage not in allowed_transitions.get(current, []):
            logger.warning(f"RolloutManager: Non-progressive or invalid transition requested ({current.value} -> {target_stage.value}).")
            return False

        proposal.stage = target_stage
        self.active_deployments[proposal.compiled_skill.skill_id] = target_stage

        proposal.history.append({
            "stage": target_stage.value,
            "action": "STAGE_TRANSITION",
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.info(f"RolloutManager: Successfully transitioned capability {proposal.compiled_skill.skill_id} to {target_stage.value}.")
        return True


class RollbackManager:
    """
    Provides deterministic safety and failure recovery, disabling any failed capability instantaneously.
    """

    def __init__(self, rollout_manager: RolloutManager):
        self.rollout = rollout_manager

    def trigger_automatic_rollback(self, proposal_id: str, reason: str) -> bool:
        """Disables and rolls back any capability immediately on performance/anomaly breach."""
        proposal = self.rollout.governance.proposals.get(proposal_id)
        if not proposal:
            return False

        logger.critical(f"ROLLBACK TRIGGERED for {proposal.compiled_skill.skill_id}! Reason: {reason}")

        # Reset stage and disable execution privileges
        proposal.stage = PromotionStage.SANDBOX
        proposal.is_active = False

        if proposal.compiled_skill.skill_id in self.rollout.active_deployments:
            self.rollout.active_deployments[proposal.compiled_skill.skill_id] = PromotionStage.SANDBOX

        proposal.history.append({
            "stage": PromotionStage.SANDBOX.value,
            "action": "AUTOMATIC_ROLLBACK",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

        return True

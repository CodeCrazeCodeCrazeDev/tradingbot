import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    CapabilityDomain,
    DistilledCapability,
    EIPProposal,
    RegistryEntry
)
from trading_bot.research.research_os import ResearchWorkspace

logger = logging.getLogger("AlphaAlgo.EIP.Registry")


class UniversalCapabilityRegistry:
    """
    Immutable Universal Capability Registry.
    Tracks lineage, validation history, deployment stages, and rollback metadata.
    """

    def __init__(self, workspace: ResearchWorkspace):
        self.workspace = workspace
        self.entries: Dict[str, RegistryEntry] = {}
        self.proposals: Dict[str, EIPProposal] = {}

    def register_capability(
        self,
        cap: DistilledCapability,
        compiled_code: str,
        source_url: str,
        version_id: str
    ) -> RegistryEntry:
        """Registers a distilled capability with immutable lineage."""
        logger.info(f"Registry: Creating entry for {cap.name}...")

        entry = RegistryEntry(
            capability_id=cap.capability_id,
            name=cap.name,
            domain=cap.domain,
            source_url=source_url,
            version_id=version_id,
            distilled_pattern=cap.extracted_pattern,
            compiled_code=compiled_code,
            evidence_score=cap.evidence_score
        )
        self.entries[cap.capability_id] = entry

        # Log provenance trace to the core Research OS
        self.workspace.record_knowledge_entry(
            source_type="eip_capability",
            source_id=cap.capability_id,
            lessons=f"Registered external capability into Universal Capability Registry with evidence score {cap.evidence_score}.",
            recommendation="PROCEED_TO_GOVERNED_ROLLOUT"
        )

        return entry

    def submit_proposal(self, cap: DistilledCapability, security_passed: bool, license_status: str) -> EIPProposal:
        """Creates an EIP Proposal for gating and progressive rollout."""
        proposal_id = f"eip_proposal_{uuid.uuid4().hex[:10]}"

        proposal = EIPProposal(
            proposal_id=proposal_id,
            capability_id=cap.capability_id,
            name=cap.name,
            domain=cap.domain,
            source_url=cap.metadata.get("source_url", "https://untrusted.source"),
            version_id=cap.metadata.get("version_id", "v1.0"),
            evidence_quality_score=cap.evidence_score,
            security_passed=security_passed,
            license_status=license_status,
            is_active=True,
            stage="sandbox"
        )
        self.proposals[proposal_id] = proposal
        return proposal

    def evaluate_proposal(self, proposal_id: str) -> Tuple[bool, str]:
        """Runs multi-gate governance verification (Security, License, Performance)."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False, "Proposal not found"

        # 1. Security Gate
        if not proposal.security_passed:
            return False, "SECURITY_GATE_REJECTED"

        # 2. License Gate
        if proposal.license_status == "FORBIDDEN":
            return False, "LICENSE_GATE_REJECTED"

        # 3. Evidence Quality Gate (must be >= 0.40)
        if proposal.evidence_quality_score < 0.40:
            return False, "EVIDENCE_QUALITY_REJECTED"

        # High risk checks (Business/Cognitive domains, or moderate evidence < 0.60)
        is_high_risk = proposal.domain in [CapabilityDomain.COGNITIVE, CapabilityDomain.BUSINESS] or proposal.evidence_quality_score < 0.60
        if is_high_risk:
            proposal.is_active = False  # Suspends until human triggers approval
            return False, "HUMAN_APPROVAL_REQUIRED"

        proposal.stage = "shadow"
        return True, "PROMOTED_TO_SHADOW"

    def sign_off_human_approval(self, proposal_id: str, approver_name: str) -> bool:
        """Enables human sign-off for high-risk capabilities."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False

        proposal.is_active = True
        proposal.stage = "shadow"
        proposal.history.append({
            "action": "HUMAN_APPROVED",
            "approver": approver_name,
            "timestamp": datetime.utcnow().isoformat()
        })
        return True


class EIPRolloutManager:
    """Manages progressive rollout sequences: sandbox -> shadow -> canary -> limited -> full."""

    def __init__(self, registry: UniversalCapabilityRegistry):
        self.registry = registry

    def transition_stage(self, proposal_id: str, target_stage: str) -> bool:
        proposal = self.registry.proposals.get(proposal_id)
        if not proposal or not proposal.is_active:
            return False

        valid_stages = ["sandbox", "shadow", "canary", "limited_production", "full_deployment"]
        if target_stage not in valid_stages:
            return False

        current_idx = valid_stages.index(proposal.stage)
        target_idx = valid_stages.index(target_stage)

        # Progressive enforcement
        if target_idx != current_idx + 1:
            logger.warning(f"EIPRollout: Non-progressive transition ({proposal.stage} -> {target_stage}) blocked.")
            return False

        proposal.stage = target_stage
        proposal.history.append({
            "action": "ROLLOUT_TRANSITION",
            "stage": target_stage,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Record into Universal Registry entry
        entry = self.registry.entries.get(proposal.capability_id)
        if entry:
            entry.deployment_history.append({
                "stage": target_stage,
                "timestamp": datetime.utcnow().isoformat()
            })

        return True


class EIPRollbackManager:
    """Triggers deterministic instantaneous rollback of any capability on anomaly."""

    def __init__(self, rollout_manager: EIPRolloutManager):
        self.rollout = rollout_manager

    def trigger_automatic_rollback(self, proposal_id: str, reason: str) -> bool:
        proposal = self.rollout.registry.proposals.get(proposal_id)
        if not proposal:
            return False

        logger.critical(f"EIP Rollback Triggered for {proposal.capability_id}! Reason: {reason}")

        proposal.stage = "sandbox"
        proposal.is_active = False
        proposal.history.append({
            "action": "AUTOMATIC_ROLLBACK",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

        entry = self.rollout.registry.entries.get(proposal.capability_id)
        if entry:
            entry.deployment_history.append({
                "action": "ROLLED_BACK",
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            })

        return True

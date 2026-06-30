"""
RSIE Governance and Approval Workflow

Handles the lifecycle of improvement proposals, especially Level 6-7
which require explicit human approval via pending_approvals.json.
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from .recursive_core import ImprovementProposal, ImprovementDimension
from .infrastructure import GovernanceController

logger = logging.getLogger(__name__)

class ApprovalWorkflow:
    """
    Manages the file-based approval process for high-level self-modifications.
    """

    def __init__(self, storage_path: str = "recursive_improvement_data"):
        self.storage_path = Path(storage_path)
        self.approval_file = self.storage_path / "pending_approvals.json"
        self.audit_file = self.storage_path / "approval_audit.json"
        self.gov_controller = GovernanceController()

        self.storage_path.mkdir(parents=True, exist_ok=True)
        if not self.approval_file.exists():
            self._save_approvals({})

    async def submit_for_approval(self, proposal: ImprovementProposal) -> str:
        """
        Submit a proposal for human review.
        Pauses if Level 6-7 or if Governance flags it.
        """
        # 1. Internal Governance Check first
        compliant, violations = await self.gov_controller.check_proposal(proposal)

        # 2. Level 6-7 always go to pending_approvals
        requires_human = proposal.level >= 6 or not compliant

        if requires_human:
            logger.info(f"Proposal {proposal.proposal_id} (Level {proposal.level}) requires HUMAN APPROVAL.")
            await self._add_to_pending(proposal, violations)
            return "PENDING"

        return "AUTO_APPROVED"

    async def check_approval_status(self, proposal_id: str) -> str:
        """Check if a proposal has been approved/rejected by a human"""
        approvals = self._load_approvals()
        entry = approvals.get(proposal_id)

        if not entry:
            return "NOT_FOUND"

        status = entry.get('status', 'PENDING')

        if status in ['APPROVED', 'REJECTED']:
            # Move to audit and remove from pending
            await self._archive_proposal(proposal_id, status)

        return status

    async def _add_to_pending(self, proposal: ImprovementProposal, violations: List[str]):
        """Add proposal to the pending_approvals.json file"""
        approvals = self._load_approvals()

        approvals[proposal.proposal_id] = {
            'proposal_id': proposal.proposal_id,
            'dimension': proposal.dimension.value,
            'level': proposal.level,
            'description': proposal.description,
            'reasoning': proposal.reasoning,
            'expected_benefit': proposal.expected_benefit,
            'risk_analysis': proposal.risk_analysis,
            'governance_violations': violations,
            'proposed_changes': proposal.proposed_changes,
            'status': 'PENDING',
            'submitted_at': datetime.utcnow().isoformat(),
            'instructions': "Set status to 'APPROVED' or 'REJECTED' to proceed."
        }

        self._save_approvals(approvals)

    async def _archive_proposal(self, proposal_id: str, status: str):
        """Move an actioned proposal to the audit log"""
        approvals = self._load_approvals()
        entry = approvals.pop(proposal_id, {})

        if entry:
            entry['actioned_at'] = datetime.utcnow().isoformat()
            entry['status'] = status

            audit_log = self._load_json(self.audit_file)
            if 'history' not in audit_log:
                audit_log['history'] = []
            audit_log['history'].append(entry)

            self._save_json(self.audit_file, audit_log)
            self._save_approvals(approvals)

    def _load_approvals(self) -> Dict:
        return self._load_json(self.approval_file)

    def _save_approvals(self, data: Dict):
        self._save_json(self.approval_file, data)

    def _load_json(self, path: Path) -> Dict:
        if path.exists():
            with open(path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _save_json(self, path: Path, data: Dict):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

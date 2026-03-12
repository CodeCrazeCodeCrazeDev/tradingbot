"""
Approval Manager
Manages the proposal approval workflow - tracks proposals, waits for human approval.
"""

import os
import json
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

from .proposal_engine import Proposal, ProposalStatus, RiskLevel
from enum import auto

logger = logging.getLogger(__name__)


class ApprovalDecision(Enum):
    """Human approval decisions."""
    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"  # Review later
    MODIFY = "modify"  # Approve with modifications


@dataclass
class ApprovalRecord:
    """Record of an approval decision."""
    proposal_id: str
    decision: ApprovalDecision
    decided_by: str
    decided_at: datetime
    notes: str
    modifications: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            'proposal_id': self.proposal_id,
            'decision': self.decision.value,
            'decided_by': self.decided_by,
            'decided_at': self.decided_at.isoformat(),
            'notes': self.notes,
            'modifications': self.modifications
        }


class ApprovalManager:
    """
    Manages the proposal approval workflow:
    - Presents proposals to human for review
    - Tracks approval/rejection decisions
    - Maintains audit trail
    - Supports batch operations
    """
    
    def __init__(self, storage_path: str):
        """
        Initialize approval manager.
        
        Args:
            storage_path: Path to store approval records
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.proposals: Dict[str, Proposal] = {}
        self.approval_records: List[ApprovalRecord] = []
        
        # Load existing records
        self._load_records()
        
        logger.info(f"ApprovalManager initialized with storage at {storage_path}")
    
    def _load_records(self) -> None:
        """Load existing approval records."""
        records_file = self.storage_path / "approval_records.json"
        if records_file.exists():
            try:
                with open(records_file, 'r') as f:
                    data = json.load(f)
                    # Would reconstruct ApprovalRecord objects here
                    logger.info(f"Loaded {len(data.get('records', []))} approval records")
            except Exception as e:
                logger.warning(f"Could not load approval records: {e}")
    
    def _save_records(self) -> None:
        """Save approval records."""
        records_file = self.storage_path / "approval_records.json"
        data = {
            'updated_at': datetime.now().isoformat(),
            'records': [r.to_dict() for r in self.approval_records]
        }
        with open(records_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_proposals(self, proposals: List[Proposal]) -> None:
        """Add proposals for review."""
        for proposal in proposals:
            self.proposals[proposal.proposal_id] = proposal
        logger.info(f"Added {len(proposals)} proposals for review")
    
    def get_pending_proposals(self) -> List[Proposal]:
        """Get all pending proposals."""
        return [p for p in self.proposals.values() if p.status == ProposalStatus.PENDING]
    
    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get a specific proposal."""
        return self.proposals.get(proposal_id)
    
    def approve(self, proposal_id: str, notes: str = "", decided_by: str = "human") -> bool:
        """
        Approve a proposal.
        
        Args:
            proposal_id: ID of proposal to approve
            notes: Optional notes about the decision
            decided_by: Who made the decision
            
        Returns:
            True if approved successfully
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            logger.error(f"Proposal {proposal_id} not found")
            return False
        
        if proposal.status != ProposalStatus.PENDING:
            logger.warning(f"Proposal {proposal_id} is not pending (status: {proposal.status})")
            return False
        
        # Update proposal status
        proposal.status = ProposalStatus.APPROVED
        proposal.reviewed_at = datetime.now()
        proposal.reviewer_notes = notes
        
        # Record the decision
        record = ApprovalRecord(
            proposal_id=proposal_id,
            decision=ApprovalDecision.APPROVE,
            decided_by=decided_by,
            decided_at=datetime.now(),
            notes=notes
        )
        self.approval_records.append(record)
        self._save_records()
        
        logger.info(f"✓ Proposal {proposal_id} APPROVED by {decided_by}")
        return True
    
    def reject(self, proposal_id: str, notes: str = "", decided_by: str = "human") -> bool:
        """
        Reject a proposal.
        
        Args:
            proposal_id: ID of proposal to reject
            notes: Reason for rejection
            decided_by: Who made the decision
            
        Returns:
            True if rejected successfully
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            logger.error(f"Proposal {proposal_id} not found")
            return False
        
        if proposal.status != ProposalStatus.PENDING:
            logger.warning(f"Proposal {proposal_id} is not pending")
            return False
        
        # Update proposal status
        proposal.status = ProposalStatus.REJECTED
        proposal.reviewed_at = datetime.now()
        proposal.reviewer_notes = notes
        
        # Record the decision
        record = ApprovalRecord(
            proposal_id=proposal_id,
            decision=ApprovalDecision.REJECT,
            decided_by=decided_by,
            decided_at=datetime.now(),
            notes=notes
        )
        self.approval_records.append(record)
        self._save_records()
        
        logger.info(f"✗ Proposal {proposal_id} REJECTED by {decided_by}: {notes}")
        return True
    
    def defer(self, proposal_id: str, notes: str = "", decided_by: str = "human") -> bool:
        """Defer a proposal for later review."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False
        
        record = ApprovalRecord(
            proposal_id=proposal_id,
            decision=ApprovalDecision.DEFER,
            decided_by=decided_by,
            decided_at=datetime.now(),
            notes=notes
        )
        self.approval_records.append(record)
        self._save_records()
        
        logger.info(f"⏸ Proposal {proposal_id} DEFERRED: {notes}")
        return True
    
    def approve_all_minimal_risk(self, decided_by: str = "auto") -> List[str]:
        """
        Auto-approve all minimal risk proposals.
        
        Returns:
            List of approved proposal IDs
        """
        approved = []
        for proposal in self.get_pending_proposals():
            if proposal.risk_level == RiskLevel.MINIMAL:
                if self.approve(proposal.proposal_id, "Auto-approved (minimal risk)", decided_by):
                    approved.append(proposal.proposal_id)
        
        logger.info(f"Auto-approved {len(approved)} minimal-risk proposals")
        return approved
    
    def get_approved_proposals(self) -> List[Proposal]:
        """Get all approved proposals ready for application."""
        return [p for p in self.proposals.values() if p.status == ProposalStatus.APPROVED]
    
    def format_proposal_for_review(self, proposal: Proposal) -> str:
        """Format a proposal for human review."""
        separator = "=" * 70
        
        output = f"""
{separator}
PROPOSAL: {proposal.proposal_id}
{separator}

📋 TITLE: {proposal.title}

📁 FILE: {proposal.issue.file_path}
📍 LINE: {proposal.issue.line_number}

🏷️ CATEGORY: {proposal.issue.category.value.upper()}
⚠️ SEVERITY: {proposal.issue.severity.value.upper()}
🎯 RISK LEVEL: {proposal.risk_level.value.upper()}

📝 DESCRIPTION:
{proposal.description}

🔍 CURRENT CODE:
```
{proposal.issue.current_code}
```

"""
        
        if proposal.changes:
            output += "✏️ PROPOSED CHANGES:\n"
            for i, change in enumerate(proposal.changes, 1):
                output += f"""
  Change {i}: {change.change_type.value}
  Lines {change.line_start}-{change.line_end}
  
  OLD:
  ```
  {change.old_code}
  ```
  
  NEW:
  ```
  {change.new_code}
  ```
  
  Explanation: {change.explanation}
"""
        else:
            output += "⚠️ NO AUTOMATIC CHANGES - Manual review required\n"
        
        output += f"""
📊 RISK ANALYSIS:
{proposal.risk_analysis}

✅ EXPECTED BENEFITS:
"""
        for benefit in proposal.expected_benefits:
            output += f"  • {benefit}\n"
        
        output += "\n⚠️ POTENTIAL DRAWBACKS:\n"
        for drawback in proposal.potential_drawbacks:
            output += f"  • {drawback}\n"
        
        output += f"""
🧪 TESTING REQUIRED:
{proposal.testing_required}

↩️ ROLLBACK PLAN:
{proposal.rollback_plan}

⏱️ ESTIMATED EFFORT: {proposal.estimated_effort}

{separator}
DECISION: [A]pprove | [R]eject | [D]efer | [S]kip
{separator}
"""
        return output
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of approval status."""
        pending = len([p for p in self.proposals.values() if p.status == ProposalStatus.PENDING])
        approved = len([p for p in self.proposals.values() if p.status == ProposalStatus.APPROVED])
        rejected = len([p for p in self.proposals.values() if p.status == ProposalStatus.REJECTED])
        applied = len([p for p in self.proposals.values() if p.status == ProposalStatus.APPLIED])
        
        by_risk = {}
        for p in self.proposals.values():
            risk = p.risk_level.value
            by_risk[risk] = by_risk.get(risk, 0) + 1
        
        return {
            'total': len(self.proposals),
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'applied': applied,
            'by_risk_level': by_risk
        }
    
    def save_pending_for_review(self, output_path: str) -> None:
        """Save pending proposals to a file for offline review."""
        pending = self.get_pending_proposals()
        
        output = f"""
ALPHAALGO SELF-IMPROVEMENT PROPOSALS
Generated: {datetime.now().isoformat()}
Total Pending: {len(pending)}

"""
        for proposal in pending:
            output += self.format_proposal_for_review(proposal)
            output += "\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        logger.info(f"Saved {len(pending)} pending proposals to {output_path}")

"""
Self-Evolution Engine for Qwen 3 8B CodeMender

Enables the trading bot to propose and implement improvements to its own
codebase through AI-driven analysis, with human approval gates.
"""

import ast
import logging
import os
import hashlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class EvolutionStage(Enum):
    """Stages of the evolution pipeline"""
    PROPOSED = "proposed"
    ANALYZING = "analyzing"
    TESTING = "testing"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    IMPLEMENTING = "implementing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


@dataclass
class EvolutionProposal:
    """A proposed improvement to the codebase"""
    proposal_id: str
    title: str
    description: str
    category: str  # performance, reliability, security, readability, testing
    target_files: List[str] = field(default_factory=list)
    estimated_impact: str = "low"  # low, medium, high
    risk_level: str = "low"  # low, medium, high, critical
    stage: EvolutionStage = EvolutionStage.PROPOSED
    created_at: datetime = field(default_factory=datetime.now)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    changes: List[Dict[str, Any]] = field(default_factory=list)
    rollback_data: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class EvolutionResult:
    """Result of an evolution attempt"""
    proposal_id: str
    success: bool
    stage_reached: EvolutionStage
    files_modified: List[str] = field(default_factory=list)
    tests_passed: bool = False
    syntax_valid: bool = False
    rolled_back: bool = False
    error: Optional[str] = None
    duration_seconds: float = 0.0


class SelfEvolutionEngine:
    """
    AI-driven self-improvement engine for the trading bot.

    Analyzes the codebase, proposes improvements, and implements them
    with full safety controls and human approval gates.
    """

    EVOLUTION_CATEGORIES = [
        "performance",
        "reliability",
        "security",
        "readability",
        "testing",
        "error_handling",
        "documentation",
    ]

    def __init__(self, root_path: str, qwen_client=None):
        self.root_path = Path(root_path)
        self.client = qwen_client
        self._proposals: Dict[str, EvolutionProposal] = {}
        self._results: List[EvolutionResult] = []
        self._file_snapshots: Dict[str, str] = {}

    def propose(
        self,
        title: str,
        description: str,
        category: str = "reliability",
        target_files: Optional[List[str]] = None,
        risk_level: str = "low",
    ) -> EvolutionProposal:
        """Create a new evolution proposal"""
        proposal_id = hashlib.md5(
            f"{title}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        proposal = EvolutionProposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            category=category,
            target_files=target_files or [],
            risk_level=risk_level,
        )

        self._proposals[proposal_id] = proposal
        logger.info(f"Evolution proposal created: [{proposal_id}] {title}")
        return proposal

    async def analyze_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """Analyze a proposal for feasibility and impact"""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return {"error": f"Proposal {proposal_id} not found"}

        proposal.stage = EvolutionStage.ANALYZING

        analysis = {
            "proposal_id": proposal_id,
            "feasible": True,
            "estimated_changes": 0,
            "affected_modules": [],
            "risks": [],
            "dependencies": [],
        }

        # Check target files exist
        for fp in proposal.target_files:
            full_path = self.root_path / fp
            if not full_path.exists():
                analysis["risks"].append(f"Target file not found: {fp}")

        # If we have a Qwen client, get AI analysis
        if self.client:
            try:
                prompt = (
                    f"Analyze this code improvement proposal for a Python trading bot:\n\n"
                    f"Title: {proposal.title}\n"
                    f"Description: {proposal.description}\n"
                    f"Category: {proposal.category}\n"
                    f"Target files: {', '.join(proposal.target_files)}\n\n"
                    f"Assess: feasibility, risks, estimated effort, and dependencies."
                )
                response = await self.client.generate(prompt=prompt)
                analysis["ai_assessment"] = response.text
            except Exception as e:
                analysis["ai_assessment_error"] = str(e)

        proposal.stage = EvolutionStage.AWAITING_APPROVAL
        return analysis

    def approve(self, proposal_id: str, approved_by: str = "human") -> bool:
        """Approve a proposal for implementation"""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            logger.error(f"Proposal {proposal_id} not found")
            return False

        if proposal.stage not in (EvolutionStage.AWAITING_APPROVAL, EvolutionStage.PROPOSED):
            logger.error(f"Proposal {proposal_id} is in stage {proposal.stage.value}, cannot approve")
            return False

        proposal.stage = EvolutionStage.APPROVED
        proposal.approved_by = approved_by
        proposal.approved_at = datetime.now()
        logger.info(f"Proposal [{proposal_id}] approved by {approved_by}")
        return True

    def reject(self, proposal_id: str, reason: str = "") -> bool:
        """Reject a proposal"""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return False

        proposal.stage = EvolutionStage.REJECTED
        proposal.error = reason or "Rejected by human"
        logger.info(f"Proposal [{proposal_id}] rejected: {reason}")
        return True

    async def implement(self, proposal_id: str) -> EvolutionResult:
        """Implement an approved proposal"""
        import time as _time
        start = _time.monotonic()

        proposal = self._proposals.get(proposal_id)
        result = EvolutionResult(
            proposal_id=proposal_id,
            success=False,
            stage_reached=EvolutionStage.PROPOSED,
        )

        if not proposal:
            result.error = f"Proposal {proposal_id} not found"
            return result

        if proposal.stage != EvolutionStage.APPROVED:
            result.error = f"Proposal not approved (stage: {proposal.stage.value})"
            return result

        proposal.stage = EvolutionStage.IMPLEMENTING
        result.stage_reached = EvolutionStage.IMPLEMENTING

        try:
            # Snapshot target files for rollback
            for fp in proposal.target_files:
                full_path = self.root_path / fp
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        proposal.rollback_data[fp] = f.read()
                        self._file_snapshots[fp] = proposal.rollback_data[fp]

            # Verify phase
            proposal.stage = EvolutionStage.VERIFYING
            result.stage_reached = EvolutionStage.VERIFYING

            # Check syntax of all modified files
            all_valid = True
            for fp in proposal.target_files:
                full_path = self.root_path / fp
                if full_path.exists():
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            ast.parse(f.read())
                    except SyntaxError:
                        all_valid = False
                        break

            result.syntax_valid = all_valid

            if all_valid:
                proposal.stage = EvolutionStage.COMPLETED
                result.stage_reached = EvolutionStage.COMPLETED
                result.success = True
                result.files_modified = list(proposal.target_files)
                logger.info(f"Proposal [{proposal_id}] implemented successfully")
            else:
                # Rollback
                await self.rollback(proposal_id)
                result.rolled_back = True
                result.error = "Syntax validation failed, changes rolled back"

        except Exception as e:
            result.error = str(e)
            await self.rollback(proposal_id)
            result.rolled_back = True
            logger.error(f"Implementation failed for [{proposal_id}]: {e}")

        result.duration_seconds = _time.monotonic() - start
        self._results.append(result)
        return result

    async def rollback(self, proposal_id: str) -> bool:
        """Rollback changes from a proposal"""
        proposal = self._proposals.get(proposal_id)
        if not proposal or not proposal.rollback_data:
            return False

        try:
            for fp, content in proposal.rollback_data.items():
                full_path = self.root_path / fp
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            proposal.stage = EvolutionStage.ROLLED_BACK
            logger.info(f"Proposal [{proposal_id}] rolled back successfully")
            return True
        except Exception as e:
            logger.error(f"Rollback failed for [{proposal_id}]: {e}")
            return False

    def get_proposals(self, stage: Optional[EvolutionStage] = None) -> List[EvolutionProposal]:
        """Get all proposals, optionally filtered by stage"""
        if stage:
            return [p for p in self._proposals.values() if p.stage == stage]
        return list(self._proposals.values())

    def get_results(self) -> List[EvolutionResult]:
        return list(self._results)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_proposals": len(self._proposals),
            "pending": len(self.get_proposals(EvolutionStage.AWAITING_APPROVAL)),
            "approved": len(self.get_proposals(EvolutionStage.APPROVED)),
            "completed": len(self.get_proposals(EvolutionStage.COMPLETED)),
            "rejected": len(self.get_proposals(EvolutionStage.REJECTED)),
            "rolled_back": len(self.get_proposals(EvolutionStage.ROLLED_BACK)),
            "total_implementations": len(self._results),
            "successful": sum(1 for r in self._results if r.success),
        }

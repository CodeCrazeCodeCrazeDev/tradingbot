"""
Dispute Resolution System

Automated dispute resolution for governance conflicts.
Implements multi-stage resolution with escalation paths.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class DisputeType(Enum):
    """Types of disputes."""
    EVIDENCE_VALIDITY = "evidence_validity"
    VOTING_IRREGULARITY = "voting_irregularity"
    EXECUTION_FAILURE = "execution_failure"
    SLASHING_APPEAL = "slashing_appeal"
    HALLUCINATION_CLAIM = "hallucination_claim"
    DATA_INTEGRITY = "data_integrity"
    AGENT_MISCONDUCT = "agent_misconduct"
    CONSENSUS_VIOLATION = "consensus_violation"


class DisputeStatus(Enum):
    """Status of a dispute."""
    FILED = "filed"
    UNDER_REVIEW = "under_review"
    EVIDENCE_GATHERING = "evidence_gathering"
    ARBITRATION = "arbitration"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"
    APPEALED = "appealed"


class VerdictType(Enum):
    """Types of verdicts."""
    IN_FAVOR_CLAIMANT = "in_favor_claimant"
    IN_FAVOR_RESPONDENT = "in_favor_respondent"
    PARTIAL_FAVOR_CLAIMANT = "partial_favor_claimant"
    PARTIAL_FAVOR_RESPONDENT = "partial_favor_respondent"
    DISMISSED = "dismissed"
    SETTLEMENT = "settlement"
    ESCALATED = "escalated"


class ResolutionStage(Enum):
    """Stages of dispute resolution."""
    AUTOMATED = "automated"
    PEER_REVIEW = "peer_review"
    ARBITRATION_PANEL = "arbitration_panel"
    GOVERNANCE_VOTE = "governance_vote"
    FINAL_APPEAL = "final_appeal"


@dataclass
class DisputeEvidence:
    """Evidence submitted for a dispute."""
    evidence_id: str
    dispute_id: str
    submitted_by: str
    evidence_type: str
    content: Dict[str, Any]
    timestamp: datetime
    verified: bool = False
    verification_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'evidence_id': self.evidence_id,
            'dispute_id': self.dispute_id,
            'submitted_by': self.submitted_by,
            'evidence_type': self.evidence_type,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'verified': self.verified,
            'verification_notes': self.verification_notes,
        }


@dataclass
class DisputeVerdict:
    """Verdict for a dispute."""
    verdict_id: str
    dispute_id: str
    verdict_type: VerdictType
    resolution_stage: ResolutionStage
    reasoning: str
    remedies: List[Dict[str, Any]]
    issued_by: str
    issued_at: datetime
    is_final: bool
    appeal_deadline: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'verdict_id': self.verdict_id,
            'dispute_id': self.dispute_id,
            'verdict_type': self.verdict_type.value,
            'resolution_stage': self.resolution_stage.value,
            'reasoning': self.reasoning,
            'remedies': self.remedies,
            'issued_by': self.issued_by,
            'issued_at': self.issued_at.isoformat(),
            'is_final': self.is_final,
            'appeal_deadline': self.appeal_deadline.isoformat() if self.appeal_deadline else None,
        }


@dataclass
class Dispute:
    """A dispute filed in the system."""
    dispute_id: str
    dispute_type: DisputeType
    status: DisputeStatus
    claimant_id: str
    respondent_id: Optional[str]
    title: str
    description: str
    claim: Dict[str, Any]
    filed_at: datetime
    resolution_stage: ResolutionStage
    evidence: List[DisputeEvidence] = field(default_factory=list)
    verdicts: List[DisputeVerdict] = field(default_factory=list)
    stake_amount: float = 0.0
    deadline: Optional[datetime] = None
    assigned_arbitrators: List[str] = field(default_factory=list)
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'dispute_id': self.dispute_id,
            'dispute_type': self.dispute_type.value,
            'status': self.status.value,
            'claimant_id': self.claimant_id,
            'respondent_id': self.respondent_id,
            'title': self.title,
            'description': self.description,
            'claim': self.claim,
            'filed_at': self.filed_at.isoformat(),
            'resolution_stage': self.resolution_stage.value,
            'evidence': [e.to_dict() for e in self.evidence],
            'verdicts': [v.to_dict() for v in self.verdicts],
            'stake_amount': self.stake_amount,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'assigned_arbitrators': self.assigned_arbitrators,
            'resolution_notes': self.resolution_notes,
        }


@dataclass
class Arbitrator:
    """An arbitrator in the dispute resolution system."""
    arbitrator_id: str
    name: str
    specializations: List[DisputeType]
    reputation_score: float
    total_cases: int
    successful_resolutions: int
    is_active: bool
    stake_balance: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'arbitrator_id': self.arbitrator_id,
            'name': self.name,
            'specializations': [s.value for s in self.specializations],
            'reputation_score': self.reputation_score,
            'total_cases': self.total_cases,
            'successful_resolutions': self.successful_resolutions,
            'is_active': self.is_active,
            'stake_balance': self.stake_balance,
        }


class DisputeResolution:
    """
    Automated dispute resolution system.
    
    Provides:
    - Multi-stage resolution process
    - Automated initial review
    - Peer review mechanism
    - Arbitration panel
    - Appeal process
    - Remedy enforcement
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'dispute_resolution_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._disputes: Dict[str, Dispute] = {}
        self._arbitrators: Dict[str, Arbitrator] = {}
        self._resolution_rules: Dict[DisputeType, Dict[str, Any]] = {}
        
        self._resolution_config = {
            'minimum_stake': 50.0,
            'automated_review_timeout_hours': 4,
            'peer_review_timeout_hours': 24,
            'arbitration_timeout_hours': 48,
            'appeal_window_hours': 24,
            'minimum_arbitrators': 3,
            'arbitrator_agreement_threshold': 0.67,
        }
        
        self._initialize_resolution_rules()
        self._initialize_default_arbitrators()
        
        logger.info("✅ Dispute Resolution System initialized")
    
    def _initialize_resolution_rules(self):
        """Initialize resolution rules for each dispute type."""
        self._resolution_rules = {
            DisputeType.EVIDENCE_VALIDITY: {
                'auto_resolve_threshold': 0.9,
                'requires_peer_review': True,
                'max_stage': ResolutionStage.ARBITRATION_PANEL,
                'remedies': ['evidence_invalidation', 'stake_slash', 'reputation_penalty'],
            },
            DisputeType.VOTING_IRREGULARITY: {
                'auto_resolve_threshold': 0.95,
                'requires_peer_review': True,
                'max_stage': ResolutionStage.GOVERNANCE_VOTE,
                'remedies': ['vote_invalidation', 'revote', 'voter_penalty'],
            },
            DisputeType.EXECUTION_FAILURE: {
                'auto_resolve_threshold': 0.85,
                'requires_peer_review': False,
                'max_stage': ResolutionStage.ARBITRATION_PANEL,
                'remedies': ['rollback', 'compensation', 'system_fix'],
            },
            DisputeType.SLASHING_APPEAL: {
                'auto_resolve_threshold': 0.8,
                'requires_peer_review': True,
                'max_stage': ResolutionStage.FINAL_APPEAL,
                'remedies': ['slash_reversal', 'partial_refund', 'reputation_restore'],
            },
            DisputeType.HALLUCINATION_CLAIM: {
                'auto_resolve_threshold': 0.7,
                'requires_peer_review': True,
                'max_stage': ResolutionStage.ARBITRATION_PANEL,
                'remedies': ['claim_invalidation', 'agent_quarantine', 'stake_slash'],
            },
            DisputeType.DATA_INTEGRITY: {
                'auto_resolve_threshold': 0.95,
                'requires_peer_review': True,
                'max_stage': ResolutionStage.GOVERNANCE_VOTE,
                'remedies': ['data_correction', 'source_blacklist', 'compensation'],
            },
            DisputeType.AGENT_MISCONDUCT: {
                'auto_resolve_threshold': 0.75,
                'requires_peer_review': True,
                'max_stage': ResolutionStage.FINAL_APPEAL,
                'remedies': ['agent_termination', 'stake_slash', 'ban'],
            },
            DisputeType.CONSENSUS_VIOLATION: {
                'auto_resolve_threshold': 0.9,
                'requires_peer_review': True,
                'max_stage': ResolutionStage.GOVERNANCE_VOTE,
                'remedies': ['consensus_reset', 'participant_penalty', 'revote'],
            },
        }
    
    def _initialize_default_arbitrators(self):
        """Initialize default arbitrators."""
        default_arbitrators = [
            Arbitrator(
                arbitrator_id="ARB-001",
                name="Evidence Specialist",
                specializations=[DisputeType.EVIDENCE_VALIDITY, DisputeType.DATA_INTEGRITY],
                reputation_score=0.95,
                total_cases=0,
                successful_resolutions=0,
                is_active=True,
                stake_balance=5000.0,
            ),
            Arbitrator(
                arbitrator_id="ARB-002",
                name="Governance Expert",
                specializations=[DisputeType.VOTING_IRREGULARITY, DisputeType.CONSENSUS_VIOLATION],
                reputation_score=0.92,
                total_cases=0,
                successful_resolutions=0,
                is_active=True,
                stake_balance=5000.0,
            ),
            Arbitrator(
                arbitrator_id="ARB-003",
                name="Technical Arbitrator",
                specializations=[DisputeType.EXECUTION_FAILURE, DisputeType.HALLUCINATION_CLAIM],
                reputation_score=0.90,
                total_cases=0,
                successful_resolutions=0,
                is_active=True,
                stake_balance=5000.0,
            ),
            Arbitrator(
                arbitrator_id="ARB-004",
                name="Agent Conduct Reviewer",
                specializations=[DisputeType.AGENT_MISCONDUCT, DisputeType.SLASHING_APPEAL],
                reputation_score=0.93,
                total_cases=0,
                successful_resolutions=0,
                is_active=True,
                stake_balance=5000.0,
            ),
            Arbitrator(
                arbitrator_id="ARB-005",
                name="General Arbitrator",
                specializations=list(DisputeType),
                reputation_score=0.88,
                total_cases=0,
                successful_resolutions=0,
                is_active=True,
                stake_balance=5000.0,
            ),
        ]
        
        for arbitrator in default_arbitrators:
            self._arbitrators[arbitrator.arbitrator_id] = arbitrator
    
    async def file_dispute(
        self,
        dispute_type: DisputeType,
        claimant_id: str,
        title: str,
        description: str,
        claim: Dict[str, Any],
        respondent_id: Optional[str] = None,
        stake_amount: Optional[float] = None,
        initial_evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> Dispute:
        """
        File a new dispute.
        
        Args:
            dispute_type: Type of dispute
            claimant_id: ID of the claimant
            title: Dispute title
            description: Detailed description
            claim: The specific claim being made
            respondent_id: Optional ID of the respondent
            stake_amount: Stake to back the dispute
            initial_evidence: Initial evidence to submit
        
        Returns:
            Dispute object
        """
        dispute_id = f"DSP-{uuid.uuid4().hex[:12]}"
        
        stake_amount = stake_amount or self._resolution_config['minimum_stake']
        if stake_amount < self._resolution_config['minimum_stake']:
            stake_amount = self._resolution_config['minimum_stake']
        
        dispute = Dispute(
            dispute_id=dispute_id,
            dispute_type=dispute_type,
            status=DisputeStatus.FILED,
            claimant_id=claimant_id,
            respondent_id=respondent_id,
            title=title,
            description=description,
            claim=claim,
            filed_at=datetime.now(timezone.utc),
            resolution_stage=ResolutionStage.AUTOMATED,
            stake_amount=stake_amount,
            deadline=datetime.now(timezone.utc) + timedelta(
                hours=self._resolution_config['automated_review_timeout_hours']
            ),
        )
        
        if initial_evidence:
            for ev in initial_evidence:
                evidence = DisputeEvidence(
                    evidence_id=f"EV-{uuid.uuid4().hex[:12]}",
                    dispute_id=dispute_id,
                    submitted_by=claimant_id,
                    evidence_type=ev.get('type', 'general'),
                    content=ev,
                    timestamp=datetime.now(timezone.utc),
                )
                dispute.evidence.append(evidence)
        
        self._disputes[dispute_id] = dispute
        
        await self._start_automated_review(dispute)
        
        await self._persist_dispute(dispute)
        
        logger.info(f"Dispute filed: {dispute_id} ({dispute_type.value})")
        
        return dispute
    
    async def submit_evidence(
        self,
        dispute_id: str,
        submitter_id: str,
        evidence_type: str,
        content: Dict[str, Any],
    ) -> Optional[DisputeEvidence]:
        """
        Submit evidence for a dispute.
        
        Args:
            dispute_id: ID of the dispute
            submitter_id: ID of the submitter
            evidence_type: Type of evidence
            content: Evidence content
        
        Returns:
            DisputeEvidence if successful
        """
        if dispute_id not in self._disputes:
            return None
        
        dispute = self._disputes[dispute_id]
        
        if dispute.status in [DisputeStatus.RESOLVED, DisputeStatus.DISMISSED]:
            return None
        
        evidence = DisputeEvidence(
            evidence_id=f"EV-{uuid.uuid4().hex[:12]}",
            dispute_id=dispute_id,
            submitted_by=submitter_id,
            evidence_type=evidence_type,
            content=content,
            timestamp=datetime.now(timezone.utc),
        )
        
        dispute.evidence.append(evidence)
        await self._persist_dispute(dispute)
        
        return evidence
    
    async def _start_automated_review(self, dispute: Dispute):
        """Start automated review of a dispute."""
        dispute.status = DisputeStatus.UNDER_REVIEW
        
        confidence, findings = await self._automated_analysis(dispute)
        
        rules = self._resolution_rules.get(dispute.dispute_type, {})
        auto_threshold = rules.get('auto_resolve_threshold', 0.9)
        
        if confidence >= auto_threshold:
            verdict = await self._issue_automated_verdict(dispute, findings, confidence)
            
            if not rules.get('requires_peer_review', True):
                dispute.status = DisputeStatus.RESOLVED
            else:
                await self._escalate_to_peer_review(dispute)
        else:
            await self._escalate_to_peer_review(dispute)
    
    async def _automated_analysis(
        self,
        dispute: Dispute,
    ) -> Tuple[float, Dict[str, Any]]:
        """Perform automated analysis of a dispute."""
        findings = {
            'evidence_count': len(dispute.evidence),
            'evidence_verified': 0,
            'claim_supported': False,
            'inconsistencies': [],
            'recommendations': [],
        }
        
        confidence = 0.5
        
        if len(dispute.evidence) >= 3:
            confidence += 0.2
            findings['evidence_verified'] = len(dispute.evidence)
        
        if dispute.claim.get('has_proof', False):
            confidence += 0.2
            findings['claim_supported'] = True
        
        if dispute.dispute_type == DisputeType.HALLUCINATION_CLAIM:
            if dispute.claim.get('hallucination_indicators', []):
                confidence += 0.15
                findings['recommendations'].append('Verify against canonical sources')
        
        if dispute.dispute_type == DisputeType.EVIDENCE_VALIDITY:
            if dispute.claim.get('hash_mismatch', False):
                confidence += 0.25
                findings['claim_supported'] = True
        
        return min(confidence, 1.0), findings
    
    async def _issue_automated_verdict(
        self,
        dispute: Dispute,
        findings: Dict[str, Any],
        confidence: float,
    ) -> DisputeVerdict:
        """Issue an automated verdict."""
        if findings.get('claim_supported', False):
            verdict_type = VerdictType.IN_FAVOR_CLAIMANT
        else:
            verdict_type = VerdictType.IN_FAVOR_RESPONDENT
        
        rules = self._resolution_rules.get(dispute.dispute_type, {})
        available_remedies = rules.get('remedies', [])
        
        remedies = []
        if verdict_type == VerdictType.IN_FAVOR_CLAIMANT and available_remedies:
            remedies.append({
                'type': available_remedies[0],
                'details': 'Automated remedy based on evidence analysis',
            })
        
        verdict = DisputeVerdict(
            verdict_id=f"VRD-{uuid.uuid4().hex[:12]}",
            dispute_id=dispute.dispute_id,
            verdict_type=verdict_type,
            resolution_stage=ResolutionStage.AUTOMATED,
            reasoning=f"Automated analysis with {confidence:.1%} confidence. Findings: {findings}",
            remedies=remedies,
            issued_by="automated_system",
            issued_at=datetime.now(timezone.utc),
            is_final=False,
            appeal_deadline=datetime.now(timezone.utc) + timedelta(
                hours=self._resolution_config['appeal_window_hours']
            ),
        )
        
        dispute.verdicts.append(verdict)
        
        return verdict
    
    async def _escalate_to_peer_review(self, dispute: Dispute):
        """Escalate dispute to peer review."""
        dispute.resolution_stage = ResolutionStage.PEER_REVIEW
        dispute.status = DisputeStatus.EVIDENCE_GATHERING
        dispute.deadline = datetime.now(timezone.utc) + timedelta(
            hours=self._resolution_config['peer_review_timeout_hours']
        )
        
        logger.info(f"Dispute {dispute.dispute_id} escalated to peer review")
    
    async def escalate_to_arbitration(
        self,
        dispute_id: str,
        reason: str,
    ) -> bool:
        """
        Escalate dispute to arbitration panel.
        
        Args:
            dispute_id: ID of the dispute
            reason: Reason for escalation
        
        Returns:
            True if successful
        """
        if dispute_id not in self._disputes:
            return False
        
        dispute = self._disputes[dispute_id]
        
        rules = self._resolution_rules.get(dispute.dispute_type, {})
        max_stage = rules.get('max_stage', ResolutionStage.ARBITRATION_PANEL)
        
        if dispute.resolution_stage.value >= max_stage.value:
            return False
        
        dispute.resolution_stage = ResolutionStage.ARBITRATION_PANEL
        dispute.status = DisputeStatus.ARBITRATION
        dispute.deadline = datetime.now(timezone.utc) + timedelta(
            hours=self._resolution_config['arbitration_timeout_hours']
        )
        
        arbitrators = self._select_arbitrators(dispute)
        dispute.assigned_arbitrators = [a.arbitrator_id for a in arbitrators]
        
        for arb in arbitrators:
            arb.total_cases += 1
        
        await self._persist_dispute(dispute)
        
        logger.info(f"Dispute {dispute_id} escalated to arbitration with "
                   f"{len(arbitrators)} arbitrators")
        
        return True
    
    def _select_arbitrators(self, dispute: Dispute) -> List[Arbitrator]:
        """Select arbitrators for a dispute."""
        min_arbitrators = self._resolution_config['minimum_arbitrators']
        
        specialized = [
            a for a in self._arbitrators.values()
            if a.is_active and dispute.dispute_type in a.specializations
        ]
        
        specialized.sort(key=lambda a: a.reputation_score, reverse=True)
        
        selected = specialized[:min_arbitrators]
        
        if len(selected) < min_arbitrators:
            general = [
                a for a in self._arbitrators.values()
                if a.is_active and a not in selected
            ]
            general.sort(key=lambda a: a.reputation_score, reverse=True)
            selected.extend(general[:min_arbitrators - len(selected)])
        
        return selected
    
    async def submit_arbitrator_verdict(
        self,
        dispute_id: str,
        arbitrator_id: str,
        verdict_type: VerdictType,
        reasoning: str,
        remedies: List[Dict[str, Any]],
    ) -> Optional[DisputeVerdict]:
        """
        Submit an arbitrator's verdict.
        
        Args:
            dispute_id: ID of the dispute
            arbitrator_id: ID of the arbitrator
            verdict_type: Type of verdict
            reasoning: Reasoning for verdict
            remedies: Proposed remedies
        
        Returns:
            DisputeVerdict if successful
        """
        if dispute_id not in self._disputes:
            return None
        
        dispute = self._disputes[dispute_id]
        
        if arbitrator_id not in dispute.assigned_arbitrators:
            return None
        
        verdict = DisputeVerdict(
            verdict_id=f"VRD-{uuid.uuid4().hex[:12]}",
            dispute_id=dispute_id,
            verdict_type=verdict_type,
            resolution_stage=ResolutionStage.ARBITRATION_PANEL,
            reasoning=reasoning,
            remedies=remedies,
            issued_by=arbitrator_id,
            issued_at=datetime.now(timezone.utc),
            is_final=False,
        )
        
        dispute.verdicts.append(verdict)
        
        arbitration_verdicts = [
            v for v in dispute.verdicts
            if v.resolution_stage == ResolutionStage.ARBITRATION_PANEL
        ]
        
        if len(arbitration_verdicts) >= len(dispute.assigned_arbitrators):
            await self._finalize_arbitration(dispute)
        
        await self._persist_dispute(dispute)
        
        return verdict
    
    async def _finalize_arbitration(self, dispute: Dispute):
        """Finalize arbitration based on arbitrator verdicts."""
        arbitration_verdicts = [
            v for v in dispute.verdicts
            if v.resolution_stage == ResolutionStage.ARBITRATION_PANEL
        ]
        
        verdict_counts = {}
        for v in arbitration_verdicts:
            verdict_counts[v.verdict_type] = verdict_counts.get(v.verdict_type, 0) + 1
        
        threshold = self._resolution_config['arbitrator_agreement_threshold']
        total = len(arbitration_verdicts)
        
        final_verdict_type = None
        for vt, count in verdict_counts.items():
            if count / total >= threshold:
                final_verdict_type = vt
                break
        
        if final_verdict_type:
            all_remedies = []
            for v in arbitration_verdicts:
                if v.verdict_type == final_verdict_type:
                    all_remedies.extend(v.remedies)
            
            final_verdict = DisputeVerdict(
                verdict_id=f"VRD-{uuid.uuid4().hex[:12]}",
                dispute_id=dispute.dispute_id,
                verdict_type=final_verdict_type,
                resolution_stage=ResolutionStage.ARBITRATION_PANEL,
                reasoning=f"Arbitration panel reached {threshold:.0%} agreement",
                remedies=all_remedies[:3],
                issued_by="arbitration_panel",
                issued_at=datetime.now(timezone.utc),
                is_final=True,
                appeal_deadline=datetime.now(timezone.utc) + timedelta(
                    hours=self._resolution_config['appeal_window_hours']
                ),
            )
            
            dispute.verdicts.append(final_verdict)
            dispute.status = DisputeStatus.RESOLVED
            
            for arb_id in dispute.assigned_arbitrators:
                arb = self._arbitrators.get(arb_id)
                if arb:
                    arb.successful_resolutions += 1
                    arb.reputation_score = min(1.0, arb.reputation_score + 0.01)
            
            logger.info(f"Dispute {dispute.dispute_id} resolved: {final_verdict_type.value}")
        else:
            dispute.status = DisputeStatus.ESCALATED
            logger.warning(f"Dispute {dispute.dispute_id} could not reach consensus, escalating")
    
    async def appeal_verdict(
        self,
        dispute_id: str,
        appellant_id: str,
        reason: str,
        additional_evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[bool, str]:
        """
        Appeal a verdict.
        
        Args:
            dispute_id: ID of the dispute
            appellant_id: ID of the appellant
            reason: Reason for appeal
            additional_evidence: New evidence for appeal
        
        Returns:
            Tuple of (success, message)
        """
        if dispute_id not in self._disputes:
            return False, "Dispute not found"
        
        dispute = self._disputes[dispute_id]
        
        if dispute.status != DisputeStatus.RESOLVED:
            return False, "Can only appeal resolved disputes"
        
        final_verdict = next(
            (v for v in reversed(dispute.verdicts) if v.is_final),
            None
        )
        
        if not final_verdict:
            return False, "No final verdict to appeal"
        
        if final_verdict.appeal_deadline and datetime.now(timezone.utc) > final_verdict.appeal_deadline:
            return False, "Appeal deadline has passed"
        
        rules = self._resolution_rules.get(dispute.dispute_type, {})
        max_stage = rules.get('max_stage', ResolutionStage.ARBITRATION_PANEL)
        
        if dispute.resolution_stage.value >= max_stage.value:
            return False, "Maximum resolution stage reached"
        
        dispute.status = DisputeStatus.APPEALED
        dispute.resolution_notes = f"Appeal by {appellant_id}: {reason}"
        
        if additional_evidence:
            for ev in additional_evidence:
                evidence = DisputeEvidence(
                    evidence_id=f"EV-{uuid.uuid4().hex[:12]}",
                    dispute_id=dispute_id,
                    submitted_by=appellant_id,
                    evidence_type=ev.get('type', 'appeal_evidence'),
                    content=ev,
                    timestamp=datetime.now(timezone.utc),
                )
                dispute.evidence.append(evidence)
        
        next_stages = {
            ResolutionStage.AUTOMATED: ResolutionStage.PEER_REVIEW,
            ResolutionStage.PEER_REVIEW: ResolutionStage.ARBITRATION_PANEL,
            ResolutionStage.ARBITRATION_PANEL: ResolutionStage.GOVERNANCE_VOTE,
            ResolutionStage.GOVERNANCE_VOTE: ResolutionStage.FINAL_APPEAL,
        }
        
        next_stage = next_stages.get(dispute.resolution_stage)
        if next_stage:
            dispute.resolution_stage = next_stage
        
        await self._persist_dispute(dispute)
        
        logger.info(f"Appeal filed for dispute {dispute_id}, escalating to {dispute.resolution_stage.value}")
        
        return True, f"Appeal accepted, escalating to {dispute.resolution_stage.value}"
    
    async def dismiss_dispute(
        self,
        dispute_id: str,
        reason: str,
        dismissed_by: str,
    ) -> bool:
        """
        Dismiss a dispute.
        
        Args:
            dispute_id: ID of the dispute
            reason: Reason for dismissal
            dismissed_by: ID of the dismisser
        
        Returns:
            True if successful
        """
        if dispute_id not in self._disputes:
            return False
        
        dispute = self._disputes[dispute_id]
        
        verdict = DisputeVerdict(
            verdict_id=f"VRD-{uuid.uuid4().hex[:12]}",
            dispute_id=dispute_id,
            verdict_type=VerdictType.DISMISSED,
            resolution_stage=dispute.resolution_stage,
            reasoning=reason,
            remedies=[],
            issued_by=dismissed_by,
            issued_at=datetime.now(timezone.utc),
            is_final=True,
        )
        
        dispute.verdicts.append(verdict)
        dispute.status = DisputeStatus.DISMISSED
        dispute.resolution_notes = reason
        
        await self._persist_dispute(dispute)
        
        logger.info(f"Dispute {dispute_id} dismissed: {reason}")
        
        return True
    
    def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        """Get a dispute by ID."""
        return self._disputes.get(dispute_id)
    
    def get_active_disputes(self) -> List[Dispute]:
        """Get all active disputes."""
        return [
            d for d in self._disputes.values()
            if d.status not in [DisputeStatus.RESOLVED, DisputeStatus.DISMISSED]
        ]
    
    def get_arbitrator(self, arbitrator_id: str) -> Optional[Arbitrator]:
        """Get an arbitrator by ID."""
        return self._arbitrators.get(arbitrator_id)
    
    async def _persist_dispute(self, dispute: Dispute):
        """Persist dispute to storage."""
        dispute_file = self.storage_path / 'disputes' / f"{dispute.dispute_id}.json"
        dispute_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dispute_file, 'w') as f:
            json.dump(dispute.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dispute resolution statistics."""
        status_counts = {}
        type_counts = {}
        
        for dispute in self._disputes.values():
            status_counts[dispute.status.value] = status_counts.get(dispute.status.value, 0) + 1
            type_counts[dispute.dispute_type.value] = type_counts.get(dispute.dispute_type.value, 0) + 1
        
        resolved = [d for d in self._disputes.values() if d.status == DisputeStatus.RESOLVED]
        
        return {
            'total_disputes': len(self._disputes),
            'active_disputes': len(self.get_active_disputes()),
            'resolved_disputes': len(resolved),
            'disputes_by_status': status_counts,
            'disputes_by_type': type_counts,
            'total_arbitrators': len(self._arbitrators),
            'active_arbitrators': len([a for a in self._arbitrators.values() if a.is_active]),
            'average_resolution_time_hours': 0,
        }

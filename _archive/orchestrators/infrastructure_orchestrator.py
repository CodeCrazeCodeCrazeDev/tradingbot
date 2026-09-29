"""
Financial Intelligence Infrastructure Orchestrator

Main orchestrator that integrates all verification layers into a unified
Autonomous Financial Intelligence Infrastructure with Verified Evidence Reasoning
and Multi-Layer Anti-Hallucination Governance.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import uuid

from .evidence_verification import (
    EvidenceProvenance,
    MerkleVerifier,
    DataCanonicalizer,
    EvidenceStake,
)

from .adversarial_verification import (
    ValidatorPool,
    FormalProver,
    ClaimChallenger,
    VerificationMarket,
)

from .governance_consensus import (
    ConsensusEngine,
    GovernanceToken,
    VotingContractManager,
    DisputeResolution,
)

from .verified_reasoning import (
    EvidenceReasoner,
    CitationValidator,
    LogicalVerifier,
    UncertaintyQuantifier,
)

from .anti_hallucination import (
    HallucinationDetector,
    FactChecker,
    ConfidenceCalibrator,
    AnomalyDetector,
)

logger = logging.getLogger(__name__)


@dataclass
class VerificationPipeline:
    """Configuration for the verification pipeline."""
    require_evidence: bool = True
    require_consensus: bool = True
    require_formal_proof: bool = False
    hallucination_check: bool = True
    fact_check: bool = True
    minimum_confidence: float = 0.7
    minimum_validators: int = 3
    consensus_threshold: float = 0.67


@dataclass
class InfrastructureStatus:
    """Status of the infrastructure."""
    is_operational: bool
    components_active: Dict[str, bool]
    total_verifications: int
    total_decisions_processed: int
    hallucinations_blocked: int
    consensus_rounds_completed: int
    overall_health: float
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_operational': self.is_operational,
            'components_active': self.components_active,
            'total_verifications': self.total_verifications,
            'total_decisions_processed': self.total_decisions_processed,
            'hallucinations_blocked': self.hallucinations_blocked,
            'consensus_rounds_completed': self.consensus_rounds_completed,
            'overall_health': self.overall_health,
            'last_updated': self.last_updated.isoformat(),
        }


@dataclass
class VerifiedDecision:
    """A decision that has passed through the verification pipeline."""
    decision_id: str
    original_decision: Dict[str, Any]
    verification_status: str
    evidence_chain_id: Optional[str]
    consensus_round_id: Optional[str]
    hallucination_report_id: Optional[str]
    confidence_score: float
    calibrated_confidence: float
    is_approved: bool
    execution_allowed: bool
    verification_timestamp: datetime
    verification_details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'original_decision': self.original_decision,
            'verification_status': self.verification_status,
            'evidence_chain_id': self.evidence_chain_id,
            'consensus_round_id': self.consensus_round_id,
            'hallucination_report_id': self.hallucination_report_id,
            'confidence_score': self.confidence_score,
            'calibrated_confidence': self.calibrated_confidence,
            'is_approved': self.is_approved,
            'execution_allowed': self.execution_allowed,
            'verification_timestamp': self.verification_timestamp.isoformat(),
            'verification_details': self.verification_details,
        }


class FinancialIntelligenceOrchestrator:
    """
    Main orchestrator for the Autonomous Financial Intelligence Infrastructure.
    
    Integrates:
    - Evidence Verification Layer (EVL)
    - Adversarial Verification Layer (AVL)
    - Governance Consensus Layer (GCL)
    - Verified Reasoning Framework (VRF)
    - Anti-Hallucination Governance (AHG)
    
    Provides:
    - Unified verification pipeline
    - Decision governance
    - Evidence-backed reasoning
    - Hallucination prevention
    - Consensus-based approval
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'financial_intelligence_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._pipeline_config = VerificationPipeline(
            require_evidence=self.config.get('require_evidence', True),
            require_consensus=self.config.get('require_consensus', True),
            require_formal_proof=self.config.get('require_formal_proof', False),
            hallucination_check=self.config.get('hallucination_check', True),
            fact_check=self.config.get('fact_check', True),
            minimum_confidence=self.config.get('minimum_confidence', 0.7),
            minimum_validators=self.config.get('minimum_validators', 3),
            consensus_threshold=self.config.get('consensus_threshold', 0.67),
        )
        
        self._evidence_provenance: Optional[EvidenceProvenance] = None
        self._merkle_verifier: Optional[MerkleVerifier] = None
        self._data_canonicalizer: Optional[DataCanonicalizer] = None
        self._evidence_stake: Optional[EvidenceStake] = None
        
        self._validator_pool: Optional[ValidatorPool] = None
        self._formal_prover: Optional[FormalProver] = None
        self._claim_challenger: Optional[ClaimChallenger] = None
        self._verification_market: Optional[VerificationMarket] = None
        
        self._consensus_engine: Optional[ConsensusEngine] = None
        self._governance_token: Optional[GovernanceToken] = None
        self._voting_contracts: Optional[VotingContractManager] = None
        self._dispute_resolution: Optional[DisputeResolution] = None
        
        self._evidence_reasoner: Optional[EvidenceReasoner] = None
        self._citation_validator: Optional[CitationValidator] = None
        self._logical_verifier: Optional[LogicalVerifier] = None
        self._uncertainty_quantifier: Optional[UncertaintyQuantifier] = None
        
        self._hallucination_detector: Optional[HallucinationDetector] = None
        self._fact_checker: Optional[FactChecker] = None
        self._confidence_calibrator: Optional[ConfidenceCalibrator] = None
        self._anomaly_detector: Optional[AnomalyDetector] = None
        
        self._verified_decisions: Dict[str, VerifiedDecision] = {}
        self._statistics = {
            'total_verifications': 0,
            'total_decisions_processed': 0,
            'hallucinations_blocked': 0,
            'consensus_rounds_completed': 0,
        }
        
        self._initialized = False
        
        logger.info("Financial Intelligence Orchestrator created")
    
    async def initialize(self):
        """Initialize all infrastructure components."""
        logger.info("=" * 80)
        logger.info("INITIALIZING AUTONOMOUS FINANCIAL INTELLIGENCE INFRASTRUCTURE")
        logger.info("=" * 80)
        
        evl_config = {'storage_path': self.storage_path / 'evidence_verification'}
        self._evidence_provenance = EvidenceProvenance(evl_config)
        self._merkle_verifier = MerkleVerifier(evl_config)
        self._data_canonicalizer = DataCanonicalizer(evl_config)
        self._evidence_stake = EvidenceStake(evl_config)
        logger.info("✅ Evidence Verification Layer initialized")
        
        avl_config = {'storage_path': self.storage_path / 'adversarial_verification'}
        self._validator_pool = ValidatorPool(avl_config)
        self._formal_prover = FormalProver(avl_config)
        self._claim_challenger = ClaimChallenger(avl_config)
        self._verification_market = VerificationMarket(avl_config)
        logger.info("✅ Adversarial Verification Layer initialized")
        
        gcl_config = {'storage_path': self.storage_path / 'governance_consensus'}
        self._consensus_engine = ConsensusEngine(gcl_config)
        self._governance_token = GovernanceToken(gcl_config)
        self._voting_contracts = VotingContractManager(gcl_config)
        self._dispute_resolution = DisputeResolution(gcl_config)
        logger.info("✅ Governance Consensus Layer initialized")
        
        vrf_config = {'storage_path': self.storage_path / 'verified_reasoning'}
        self._evidence_reasoner = EvidenceReasoner(vrf_config)
        self._citation_validator = CitationValidator(vrf_config)
        self._logical_verifier = LogicalVerifier(vrf_config)
        self._uncertainty_quantifier = UncertaintyQuantifier(vrf_config)
        logger.info("✅ Verified Reasoning Framework initialized")
        
        ahg_config = {'storage_path': self.storage_path / 'anti_hallucination'}
        self._hallucination_detector = HallucinationDetector(ahg_config)
        self._fact_checker = FactChecker(ahg_config)
        self._confidence_calibrator = ConfidenceCalibrator(ahg_config)
        self._anomaly_detector = AnomalyDetector(ahg_config)
        logger.info("✅ Anti-Hallucination Governance initialized")
        
        self._initialized = True
        
        logger.info("=" * 80)
        logger.info("AUTONOMOUS FINANCIAL INTELLIGENCE INFRASTRUCTURE READY")
        logger.info("=" * 80)
    
    async def verify_and_approve_decision(
        self,
        decision: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        agent_id: str,
        context: Optional[Dict[str, Any]] = None,
        is_high_impact: bool = False,
    ) -> VerifiedDecision:
        """
        Process a decision through the full verification pipeline.
        
        Args:
            decision: The decision to verify
            evidence: Supporting evidence
            agent_id: ID of the agent making the decision
            context: Additional context
            is_high_impact: Whether this is a high-impact decision
        
        Returns:
            VerifiedDecision with verification results
        """
        if not self._initialized:
            await self.initialize()
        
        decision_id = decision.get('decision_id', f"DEC-{uuid.uuid4().hex[:12]}")
        verification_details = {
            'stages_completed': [],
            'stages_failed': [],
            'warnings': [],
        }
        
        evidence_chain_id = None
        consensus_round_id = None
        hallucination_report_id = None
        
        is_approved = True
        execution_allowed = True
        confidence_score = decision.get('confidence', 0.5)
        
        if self._pipeline_config.hallucination_check:
            hall_report = await self._hallucination_detector.detect_hallucinations(
                decision, context
            )
            hallucination_report_id = hall_report.report_id
            
            if not hall_report.is_safe:
                is_approved = False
                execution_allowed = False
                self._statistics['hallucinations_blocked'] += 1
                verification_details['stages_failed'].append('hallucination_check')
                verification_details['hallucination_issues'] = [
                    i.to_dict() for i in hall_report.indicators
                ]
            else:
                verification_details['stages_completed'].append('hallucination_check')
        
        if is_approved and self._pipeline_config.require_evidence:
            evidence_records = []
            for ev in evidence:
                from .evidence_verification.evidence_provenance import EvidenceType
                record = await self._evidence_provenance.create_evidence_record(
                    evidence_type=EvidenceType(ev.get('type', 'market_data')),
                    source_id=ev.get('source_id', 'unknown'),
                    source_name=ev.get('source_name', 'unknown'),
                    content=ev.get('content', ev),
                    metadata=ev.get('metadata', {}),
                )
                evidence_records.append(record)
            
            if evidence_records:
                chain = await self._evidence_provenance.create_provenance_chain(
                    decision_id=decision_id,
                    evidence_ids=[r.evidence_id for r in evidence_records],
                )
                evidence_chain_id = chain.chain_id
                
                is_valid, validation_report = await self._evidence_provenance.validate_provenance_chain(
                    chain.chain_id
                )
                
                if not is_valid:
                    verification_details['warnings'].append('Evidence chain validation incomplete')
                
                verification_details['stages_completed'].append('evidence_verification')
                verification_details['evidence_validation'] = validation_report
            else:
                verification_details['warnings'].append('No evidence provided')
        
        if is_approved and self._pipeline_config.fact_check:
            from .anti_hallucination.fact_checker import FactType
            
            if 'claims' in decision:
                for claim in decision['claims']:
                    fact_result = await self._fact_checker.check_fact(
                        claim=claim.get('statement', ''),
                        value=claim.get('value'),
                        fact_type=FactType(claim.get('type', 'categorical')),
                        source_claimed=claim.get('source'),
                        context=context,
                    )
                    
                    if fact_result.status.value == 'false':
                        is_approved = False
                        verification_details['stages_failed'].append('fact_check')
                        break
            
            if is_approved:
                verification_details['stages_completed'].append('fact_check')
        
        if is_approved:
            challenge_result = await self._claim_challenger.challenge_claim(
                claim=decision,
                evidence=[e for e in evidence],
                context=context,
            )
            
            if challenge_result.overall_status == "BLOCKED":
                is_approved = False
                execution_allowed = False
                verification_details['stages_failed'].append('adversarial_challenge')
            elif challenge_result.overall_status == "REJECTED":
                is_approved = False
                verification_details['stages_failed'].append('adversarial_challenge')
            else:
                verification_details['stages_completed'].append('adversarial_challenge')
            
            confidence_score += challenge_result.confidence_adjustment
            verification_details['challenge_result'] = challenge_result.to_dict()
        
        if is_approved:
            validated, consensus_report = await self._validator_pool.validate_with_consensus(
                claim=decision,
                evidence=evidence,
                required_validators=self._pipeline_config.minimum_validators,
                is_high_impact=is_high_impact,
                context=context,
            )
            
            if not validated:
                is_approved = False
                verification_details['stages_failed'].append('validator_consensus')
            else:
                verification_details['stages_completed'].append('validator_consensus')
            
            verification_details['validator_consensus'] = consensus_report
            self._statistics['total_verifications'] += 1
        
        if is_approved and self._pipeline_config.require_consensus and is_high_impact:
            from .governance_consensus.consensus_engine import ConsensusType
            
            round = await self._consensus_engine.create_consensus_round(
                proposal_id=decision_id,
                proposal_content=decision,
                consensus_type=ConsensusType.STAKE_WEIGHTED,
            )
            consensus_round_id = round.round_id
            
            verification_details['stages_completed'].append('governance_consensus_initiated')
            verification_details['consensus_round_id'] = consensus_round_id
            self._statistics['consensus_rounds_completed'] += 1
        
        calibrated_confidence = await self._confidence_calibrator.get_calibrated_confidence(
            agent_id=agent_id,
            raw_confidence=max(0.01, min(0.99, confidence_score)),
        )
        
        if calibrated_confidence < self._pipeline_config.minimum_confidence:
            execution_allowed = False
            verification_details['warnings'].append(
                f'Calibrated confidence {calibrated_confidence:.2f} below threshold {self._pipeline_config.minimum_confidence}'
            )
        
        if is_approved:
            verification_status = "APPROVED"
        elif verification_details['stages_failed']:
            verification_status = "REJECTED"
        else:
            verification_status = "PENDING"
        
        verified_decision = VerifiedDecision(
            decision_id=decision_id,
            original_decision=decision,
            verification_status=verification_status,
            evidence_chain_id=evidence_chain_id,
            consensus_round_id=consensus_round_id,
            hallucination_report_id=hallucination_report_id,
            confidence_score=confidence_score,
            calibrated_confidence=calibrated_confidence,
            is_approved=is_approved,
            execution_allowed=execution_allowed,
            verification_timestamp=datetime.now(timezone.utc),
            verification_details=verification_details,
        )
        
        self._verified_decisions[decision_id] = verified_decision
        self._statistics['total_decisions_processed'] += 1
        
        await self._persist_verified_decision(verified_decision)
        
        logger.info(f"Decision {decision_id} verification complete: {verification_status} "
                   f"(confidence: {calibrated_confidence:.2f}, execution: {execution_allowed})")
        
        return verified_decision
    
    async def reason_with_verification(
        self,
        objective: str,
        premises: List[Dict[str, Any]],
        reasoning_steps: List[Dict[str, Any]],
        agent_id: str,
    ) -> Dict[str, Any]:
        """
        Perform verified reasoning with evidence requirements.
        
        Args:
            objective: The reasoning objective
            premises: Initial premises with evidence
            reasoning_steps: Steps to reach conclusion
            agent_id: ID of the agent
        
        Returns:
            Verified reasoning result
        """
        if not self._initialized:
            await self.initialize()
        
        reasoning_result = await self._evidence_reasoner.reason_with_evidence(
            objective=objective,
            premises=premises,
            reasoning_steps=reasoning_steps,
        )
        
        logical_results = await self._logical_verifier.verify_reasoning_chain(
            steps=[{
                'premises': [s.premise],
                'conclusion': s.conclusion,
            } for s in reasoning_result.chain.steps]
        )
        
        step_uncertainties = []
        for step in reasoning_result.chain.steps:
            step_uncertainties.append({
                'uncertainty': step.uncertainty,
                'sources': [{'name': c.source_name, 'magnitude': 1 - c.relevance_score} 
                           for c in step.citations],
            })
        
        propagated = await self._uncertainty_quantifier.propagate_through_chain(
            chain_id=reasoning_result.chain.chain_id,
            step_uncertainties=step_uncertainties,
        )
        
        return {
            'reasoning_result': reasoning_result.to_dict(),
            'logical_verification': [r.to_dict() for r in logical_results],
            'uncertainty_propagation': propagated.to_dict(),
            'is_verified': reasoning_result.is_verified,
            'final_confidence': reasoning_result.confidence,
            'final_uncertainty': propagated.final_uncertainty,
        }
    
    async def get_status(self) -> InfrastructureStatus:
        """Get current infrastructure status."""
        components_active = {
            'evidence_provenance': self._evidence_provenance is not None,
            'merkle_verifier': self._merkle_verifier is not None,
            'data_canonicalizer': self._data_canonicalizer is not None,
            'evidence_stake': self._evidence_stake is not None,
            'validator_pool': self._validator_pool is not None,
            'formal_prover': self._formal_prover is not None,
            'claim_challenger': self._claim_challenger is not None,
            'verification_market': self._verification_market is not None,
            'consensus_engine': self._consensus_engine is not None,
            'governance_token': self._governance_token is not None,
            'voting_contracts': self._voting_contracts is not None,
            'dispute_resolution': self._dispute_resolution is not None,
            'evidence_reasoner': self._evidence_reasoner is not None,
            'citation_validator': self._citation_validator is not None,
            'logical_verifier': self._logical_verifier is not None,
            'uncertainty_quantifier': self._uncertainty_quantifier is not None,
            'hallucination_detector': self._hallucination_detector is not None,
            'fact_checker': self._fact_checker is not None,
            'confidence_calibrator': self._confidence_calibrator is not None,
            'anomaly_detector': self._anomaly_detector is not None,
        }
        
        active_count = sum(1 for v in components_active.values() if v)
        total_count = len(components_active)
        overall_health = active_count / total_count if total_count > 0 else 0
        
        return InfrastructureStatus(
            is_operational=self._initialized and overall_health > 0.9,
            components_active=components_active,
            total_verifications=self._statistics['total_verifications'],
            total_decisions_processed=self._statistics['total_decisions_processed'],
            hallucinations_blocked=self._statistics['hallucinations_blocked'],
            consensus_rounds_completed=self._statistics['consensus_rounds_completed'],
            overall_health=overall_health,
            last_updated=datetime.now(timezone.utc),
        )
    
    async def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all components."""
        stats = {
            'infrastructure': self._statistics.copy(),
            'verified_decisions': len(self._verified_decisions),
        }
        
        if self._evidence_provenance:
            stats['evidence_provenance'] = self._evidence_provenance.get_statistics()
        if self._validator_pool:
            stats['validator_pool'] = await self._validator_pool.get_validator_statistics()
        if self._hallucination_detector:
            stats['hallucination_detector'] = self._hallucination_detector.get_statistics()
        if self._fact_checker:
            stats['fact_checker'] = self._fact_checker.get_statistics()
        if self._confidence_calibrator:
            stats['confidence_calibrator'] = self._confidence_calibrator.get_statistics()
        if self._anomaly_detector:
            stats['anomaly_detector'] = self._anomaly_detector.get_statistics()
        if self._consensus_engine:
            stats['consensus_engine'] = self._consensus_engine.get_statistics()
        
        return stats
    
    def get_verified_decision(self, decision_id: str) -> Optional[VerifiedDecision]:
        """Get a verified decision by ID."""
        return self._verified_decisions.get(decision_id)
    
    async def _persist_verified_decision(self, decision: VerifiedDecision):
        """Persist verified decision to storage."""
        decision_file = self.storage_path / 'verified_decisions' / f"{decision.decision_id}.json"
        decision_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(decision_file, 'w') as f:
            json.dump(decision.to_dict(), f, indent=2, default=str)
    
    @property
    def evidence_provenance(self) -> EvidenceProvenance:
        return self._evidence_provenance
    
    @property
    def validator_pool(self) -> ValidatorPool:
        return self._validator_pool
    
    @property
    def consensus_engine(self) -> ConsensusEngine:
        return self._consensus_engine
    
    @property
    def hallucination_detector(self) -> HallucinationDetector:
        return self._hallucination_detector
    
    @property
    def fact_checker(self) -> FactChecker:
        return self._fact_checker
    
    @property
    def confidence_calibrator(self) -> ConfidenceCalibrator:
        return self._confidence_calibrator
    
    @property
    def evidence_reasoner(self) -> EvidenceReasoner:
        return self._evidence_reasoner
    
    @property
    def claim_challenger(self) -> ClaimChallenger:
        return self._claim_challenger

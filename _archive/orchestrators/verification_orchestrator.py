"""
Verification Orchestrator - Unified Decision Verification System

Orchestrates all verification components into a single, comprehensive
verification pipeline that ensures decision integrity and prevents hallucinations.

VERIFICATION PIPELINE:
1. Pre-Verification Checks (data freshness, completeness)
2. Decision Verification Chain (8 stages)
3. Cross-Source Validation
4. Confidence Calibration
5. Adversarial Analysis
6. Final Verdict Generation
7. Audit Trail Recording

Author: AlphaAlgo Team
Date: 2026-01-28
Priority: P0 - CRITICAL
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import json

from .decision_verification_chain import (
    DecisionVerificationChain,
    VerificationChainResult,
    VerificationStatus,
    DecisionAction,
)
from .cross_validator import (
    CrossValidator,
    CrossValidationResult,
    SourceOpinion,
)
from .confidence_calibrator import (
    ConfidenceCalibrator,
    CalibrationResult,
)
from .adversarial_checker import (
    AdversarialChecker,
    AdversarialResult,
)

logger = logging.getLogger(__name__)


class FinalVerdict(Enum):
    """Final verdict on decision"""
    APPROVED = "approved"
    APPROVED_WITH_MODIFICATIONS = "approved_with_modifications"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"
    ESCALATE_TO_HUMAN = "escalate_to_human"


@dataclass
class VerificationSummary:
    """Summary of all verification results"""
    decision_id: str
    original_decision: Dict[str, Any]
    
    # Component results
    chain_result: Optional[VerificationChainResult] = None
    cross_validation_result: Optional[CrossValidationResult] = None
    calibration_result: Optional[CalibrationResult] = None
    adversarial_result: Optional[AdversarialResult] = None
    
    # Final verdict
    final_verdict: FinalVerdict = FinalVerdict.NEEDS_REVIEW
    final_confidence: float = 0.0
    modified_decision: Optional[Dict[str, Any]] = None
    
    # Aggregated findings
    total_hallucinations: int = 0
    total_challenges: int = 0
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    verification_hash: str = ""
    total_duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'final_verdict': self.final_verdict.value,
            'final_confidence': self.final_confidence,
            'total_hallucinations': self.total_hallucinations,
            'total_challenges': self.total_challenges,
            'critical_issues_count': len(self.critical_issues),
            'warnings_count': len(self.warnings),
            'verification_hash': self.verification_hash,
            'total_duration_ms': self.total_duration_ms,
            'timestamp': self.timestamp.isoformat(),
            'chain_status': self.chain_result.overall_status.value if self.chain_result else None,
            'cross_validation_validated': self.cross_validation_result.validated if self.cross_validation_result else None,
            'adversarial_should_proceed': self.adversarial_result.should_proceed if self.adversarial_result else None,
        }
    
    def get_executive_summary(self) -> str:
        """Get a brief executive summary"""
        lines = [
            f"Decision {self.decision_id}: {self.final_verdict.value.upper()}",
            f"Confidence: {self.final_confidence:.1%}",
            f"Hallucinations: {self.total_hallucinations}, Challenges: {self.total_challenges}",
        ]
        if self.critical_issues:
            lines.append(f"CRITICAL: {self.critical_issues[0]}")
        return " | ".join(lines)


class VerificationOrchestrator:
    """
    Unified verification orchestrator that coordinates all verification
    components to provide comprehensive decision validation.
    
    This is the main entry point for decision verification in the trading bot.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize all verification components
        self.chain = DecisionVerificationChain(self.config.get('chain', {}))
        self.cross_validator = CrossValidator(self.config.get('cross_validator', {}))
        self.calibrator = ConfidenceCalibrator(self.config.get('calibrator', {}))
        self.adversarial = AdversarialChecker(self.config.get('adversarial', {}))
        
        # Thresholds for final verdict
        self.min_confidence_for_approval = self.config.get('min_confidence_for_approval', 0.7)
        self.max_hallucinations_for_approval = self.config.get('max_hallucinations_for_approval', 0)
        self.min_robustness_for_approval = self.config.get('min_robustness_for_approval', 0.6)
        
        # Verification history
        self.verification_history: List[VerificationSummary] = []
        
        # Statistics
        self.stats = {
            'total_verifications': 0,
            'approved': 0,
            'rejected': 0,
            'modified': 0,
            'escalated': 0,
        }
        
        logger.info("VerificationOrchestrator initialized with all components")
    
    async def verify(
        self,
        decision: Dict[str, Any],
        market_data: Optional[Dict[str, Any]] = None,
        additional_sources: Optional[List[SourceOpinion]] = None,
        skip_components: Optional[List[str]] = None
    ) -> VerificationSummary:
        """
        Run complete verification pipeline on a decision.
        
        Args:
            decision: The decision to verify
            market_data: Current market data for grounding
            additional_sources: Additional sources for cross-validation
            skip_components: Components to skip (e.g., ['adversarial', 'cross_validator'])
            
        Returns:
            VerificationSummary with complete verification results
        """
        start_time = datetime.now()
        skip = skip_components or []
        
        decision_id = self._generate_decision_id(decision)
        logger.info(f"Starting verification pipeline for decision {decision_id}")
        
        # Initialize summary
        summary = VerificationSummary(
            decision_id=decision_id,
            original_decision=decision
        )
        
        # Stage 1: Decision Verification Chain
        if 'chain' not in skip:
            try:
                chain_result = await self.chain.verify_decision(
                    decision, market_data, additional_sources
                )
                summary.chain_result = chain_result
                summary.total_hallucinations = len(chain_result.hallucinations_detected)
                
                # Collect critical issues from chain
                for h in chain_result.hallucinations_detected:
                    if h.severity >= 0.8:
                        summary.critical_issues.append(f"Hallucination: {h.claim}")
                
            except Exception as e:
                logger.error(f"Chain verification failed: {e}")
                summary.warnings.append(f"Chain verification error: {str(e)}")
        
        # Stage 2: Cross-Source Validation
        if 'cross_validator' not in skip:
            try:
                cross_result = await self.cross_validator.validate(
                    decision, additional_sources, market_data
                )
                summary.cross_validation_result = cross_result
                summary.warnings.extend(cross_result.warnings)
                summary.recommendations.extend(cross_result.recommendations)
                
            except Exception as e:
                logger.error(f"Cross-validation failed: {e}")
                summary.warnings.append(f"Cross-validation error: {str(e)}")
        
        # Stage 3: Confidence Calibration
        if 'calibrator' not in skip:
            try:
                original_confidence = decision.get('confidence', 0.5)
                calibration_result = self.calibrator.calibrate(original_confidence)
                summary.calibration_result = calibration_result
                summary.recommendations.extend(calibration_result.recommendations)
                
            except Exception as e:
                logger.error(f"Calibration failed: {e}")
                summary.warnings.append(f"Calibration error: {str(e)}")
        
        # Stage 4: Adversarial Analysis
        if 'adversarial' not in skip:
            try:
                adversarial_result = self.adversarial.analyze(decision)
                summary.adversarial_result = adversarial_result
                summary.total_challenges = len(adversarial_result.challenges)
                summary.critical_issues.extend(adversarial_result.critical_weaknesses)
                summary.recommendations.extend(adversarial_result.recommendations)
                
            except Exception as e:
                logger.error(f"Adversarial analysis failed: {e}")
                summary.warnings.append(f"Adversarial analysis error: {str(e)}")
        
        # Stage 5: Generate Final Verdict
        summary.final_verdict, summary.final_confidence = self._generate_verdict(summary)
        
        # Stage 6: Generate Modified Decision if needed
        if summary.final_verdict == FinalVerdict.APPROVED_WITH_MODIFICATIONS:
            summary.modified_decision = self._generate_modified_decision(decision, summary)
        
        # Stage 7: Generate Verification Hash
        summary.verification_hash = self._generate_verification_hash(summary)
        
        # Calculate duration
        summary.total_duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Update statistics
        self._update_stats(summary.final_verdict)
        
        # Store in history
        self.verification_history.append(summary)
        
        logger.info(
            f"Verification complete for {decision_id}: "
            f"verdict={summary.final_verdict.value}, confidence={summary.final_confidence:.2f}"
        )
        
        return summary
    
    def _generate_verdict(
        self,
        summary: VerificationSummary
    ) -> tuple:
        """Generate final verdict based on all verification results"""
        
        # Start with base confidence
        confidence = summary.original_decision.get('confidence', 0.5)
        
        # Adjust based on chain result
        if summary.chain_result:
            if summary.chain_result.overall_status == VerificationStatus.HALLUCINATION_DETECTED:
                return FinalVerdict.REJECTED, confidence * 0.3
            elif summary.chain_result.overall_status == VerificationStatus.SUSPICIOUS:
                confidence *= 0.7
            elif summary.chain_result.overall_status == VerificationStatus.VERIFIED:
                confidence *= 1.1
        
        # Adjust based on cross-validation
        if summary.cross_validation_result:
            if not summary.cross_validation_result.validated:
                confidence *= 0.6
            confidence = summary.cross_validation_result.adjusted_confidence
        
        # Adjust based on calibration
        if summary.calibration_result:
            confidence = summary.calibration_result.calibrated_confidence
        
        # Adjust based on adversarial analysis
        if summary.adversarial_result:
            confidence *= summary.adversarial_result.confidence_adjustment
            if not summary.adversarial_result.should_proceed:
                confidence *= 0.5
        
        # Cap confidence
        confidence = max(0.0, min(1.0, confidence))
        
        # Determine verdict
        if summary.total_hallucinations > self.max_hallucinations_for_approval:
            return FinalVerdict.REJECTED, confidence
        
        if summary.critical_issues:
            if len(summary.critical_issues) >= 3:
                return FinalVerdict.REJECTED, confidence
            else:
                return FinalVerdict.ESCALATE_TO_HUMAN, confidence
        
        if summary.adversarial_result and not summary.adversarial_result.should_proceed:
            return FinalVerdict.NEEDS_REVIEW, confidence
        
        if confidence >= self.min_confidence_for_approval:
            if summary.warnings:
                return FinalVerdict.APPROVED_WITH_MODIFICATIONS, confidence
            else:
                return FinalVerdict.APPROVED, confidence
        elif confidence >= 0.5:
            return FinalVerdict.NEEDS_REVIEW, confidence
        else:
            return FinalVerdict.REJECTED, confidence
    
    def _generate_modified_decision(
        self,
        original: Dict[str, Any],
        summary: VerificationSummary
    ) -> Dict[str, Any]:
        """Generate modified decision based on verification results"""
        modified = original.copy()
        
        # Apply calibrated confidence
        if summary.calibration_result:
            modified['confidence'] = summary.calibration_result.calibrated_confidence
            modified['_original_confidence'] = original.get('confidence')
        
        # Apply chain corrections
        if summary.chain_result and summary.chain_result.corrected_decision:
            for key, value in summary.chain_result.corrected_decision.items():
                if not key.startswith('_'):
                    modified[key] = value
        
        # Apply cross-validation adjustments
        if summary.cross_validation_result:
            if summary.cross_validation_result.adjusted_direction:
                modified['_suggested_direction'] = summary.cross_validation_result.adjusted_direction
        
        # Add verification metadata
        modified['_verification_id'] = summary.decision_id
        modified['_verification_hash'] = summary.verification_hash
        modified['_modifications_applied'] = True
        
        return modified
    
    def _generate_decision_id(self, decision: Dict[str, Any]) -> str:
        """Generate unique decision ID"""
        content = json.dumps(decision, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_verification_hash(self, summary: VerificationSummary) -> str:
        """Generate verification hash for audit trail"""
        content = f"{summary.decision_id}:{summary.final_verdict.value}:{summary.final_confidence:.4f}"
        content += f":{summary.total_hallucinations}:{summary.total_challenges}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _update_stats(self, verdict: FinalVerdict):
        """Update verification statistics"""
        self.stats['total_verifications'] += 1
        
        if verdict == FinalVerdict.APPROVED:
            self.stats['approved'] += 1
        elif verdict == FinalVerdict.APPROVED_WITH_MODIFICATIONS:
            self.stats['modified'] += 1
        elif verdict == FinalVerdict.REJECTED:
            self.stats['rejected'] += 1
        elif verdict == FinalVerdict.ESCALATE_TO_HUMAN:
            self.stats['escalated'] += 1
    
    def record_outcome(
        self,
        decision_id: str,
        was_correct: bool,
        confidence: float
    ):
        """Record the outcome of a verified decision for calibration"""
        self.calibrator.record_outcome(confidence, was_correct)
        self.chain.record_prediction_outcome("trade", confidence, was_correct)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        total = self.stats['total_verifications']
        
        return {
            **self.stats,
            'approval_rate': self.stats['approved'] / total if total > 0 else 0,
            'rejection_rate': self.stats['rejected'] / total if total > 0 else 0,
            'modification_rate': self.stats['modified'] / total if total > 0 else 0,
            'escalation_rate': self.stats['escalated'] / total if total > 0 else 0,
            'calibration_stats': self.calibrator.get_calibration_stats(),
            'adversarial_stats': self.adversarial.get_analysis_stats(),
            'cross_validation_stats': self.cross_validator.get_validation_stats(),
        }
    
    def get_recent_verifications(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent verification summaries"""
        recent = self.verification_history[-count:]
        return [v.to_dict() for v in recent]


def create_verification_orchestrator(
    config: Optional[Dict[str, Any]] = None
) -> VerificationOrchestrator:
    """Create a new verification orchestrator instance"""
    return VerificationOrchestrator(config)


async def quick_verify(
    decision: Dict[str, Any],
    market_data: Optional[Dict[str, Any]] = None
) -> VerificationSummary:
    """Quick verification of a single decision"""
    orchestrator = VerificationOrchestrator()
    return await orchestrator.verify(decision, market_data)


__all__ = [
    'VerificationOrchestrator',
    'VerificationSummary',
    'FinalVerdict',
    'create_verification_orchestrator',
    'quick_verify',
]

"""
Verification Package - Decision Verification and Hallucination Prevention

This package provides comprehensive verification systems for the trading bot,
including fact-checking, hallucination detection, and decision validation.

MODULES:
- decision_verification_chain: Multi-stage verification with 8 stages
- cross_validator: Cross-validation between multiple analysis sources
- confidence_calibrator: Confidence calibration and uncertainty quantification
- adversarial_checker: Adversarial self-questioning mechanism

VERIFICATION STAGES:
1. Data Grounding - Verify claims against actual market data
2. Logical Consistency - Detect contradictions in reasoning
3. Cross-Source Validation - Validate against multiple sources
4. Historical Accuracy - Compare with past accuracy
5. Adversarial Questioning - Challenge conclusions
6. Confidence Calibration - Ensure calibrated confidence
7. Reality Anchor - Verify values are physically possible
8. Audit Trail - Create immutable records

Author: AlphaAlgo Team
Date: 2026-01-28
"""

try:
    from .decision_verification_chain import (
        DecisionVerificationChain,
        VerificationChainResult,
        VerificationStage,
        VerificationStatus,
        HallucinationType,
        HallucinationAlert,
        StageResult,
        FactCheckResult,
        DecisionAction,
        VerificationEvidence,
        create_verification_chain,
        verify_decision,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed: {e}')

try:
    from .cross_validator import (
        CrossValidator,
        CrossValidationResult,
        SourceAgreement,
        SourceOpinion,
        SourceType,
        AgreementLevel,
        create_cross_validator,
    )
except ImportError:
    pass

try:
    from .confidence_calibrator import (
        ConfidenceCalibrator,
        CalibrationResult,
        CalibrationMethod,
        CalibrationStatus,
        PredictionRecord,
        create_calibrator,
    )
except ImportError:
    pass

try:
    from .adversarial_checker import (
        AdversarialChecker,
        AdversarialResult,
        AdversarialTechnique,
        Challenge,
        ChallengeLevel,
        BiasAlert,
        CognitiveBias,
        create_adversarial_checker,
    )
except ImportError:
    pass

try:
    from .verification_orchestrator import (
        VerificationOrchestrator,
        VerificationSummary,
        FinalVerdict,
        create_verification_orchestrator,
        quick_verify,
    )
except ImportError:
    pass

__all__ = [
    # Decision Verification Chain
    'DecisionVerificationChain',
    'VerificationChainResult',
    'VerificationStage',
    'VerificationStatus',
    'HallucinationType',
    'HallucinationAlert',
    'StageResult',
    'FactCheckResult',
    'DecisionAction',
    'VerificationEvidence',
    'create_verification_chain',
    'verify_decision',
    # Cross Validator
    'CrossValidator',
    'CrossValidationResult',
    'SourceAgreement',
    'SourceOpinion',
    'SourceType',
    'AgreementLevel',
    'create_cross_validator',
    # Confidence Calibrator
    'ConfidenceCalibrator',
    'CalibrationResult',
    'CalibrationMethod',
    'CalibrationStatus',
    'PredictionRecord',
    'create_calibrator',
    # Adversarial Checker
    'AdversarialChecker',
    'AdversarialResult',
    'AdversarialTechnique',
    'Challenge',
    'ChallengeLevel',
    'BiasAlert',
    'CognitiveBias',
    'create_adversarial_checker',
    # Verification Orchestrator
    'VerificationOrchestrator',
    'VerificationSummary',
    'FinalVerdict',
    'create_verification_orchestrator',
    'quick_verify',
]

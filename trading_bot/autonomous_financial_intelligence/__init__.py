"""
Autonomous Financial Intelligence Infrastructure

A comprehensive framework for verified evidence reasoning and 
multi-layer anti-hallucination governance in autonomous trading systems.

This infrastructure provides:
- Evidence Verification Layer (EVL): Cryptographic provenance chains
- Adversarial Verification Layer (AVL): Independent claim validation
- Governance Consensus Layer (GCL): Distributed decision-making
- Verified Reasoning Framework (VRF): Evidence-backed reasoning
- Anti-Hallucination Governance (AHG): Detection and prevention systems
- Self-Improvement System: Continuous evolution and recursive optimization
"""

from .evidence_verification import (
    EvidenceProvenance,
    MerkleVerifier,
    DataCanonicalizer,
    EvidenceStake,
)

from .adversarial_verification import (
    ValidatorAgent,
    FormalProver,
    ClaimChallenger,
    VerificationMarket,
)

from .governance_consensus import (
    ConsensusEngine,
    GovernanceToken,
    VotingContract,
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

from .self_improvement import (
    ExperimentRegistry,
    PromotionGates,
    RiskGovernance,
    ComputeBudgetController,
    SelfImprovementEngine,
    EvolutionOrchestrator,
)

from .infrastructure_orchestrator import FinancialIntelligenceOrchestrator

__all__ = [
    # Evidence Verification Layer
    'EvidenceProvenance',
    'MerkleVerifier',
    'DataCanonicalizer',
    'EvidenceStake',
    
    # Adversarial Verification Layer
    'ValidatorAgent',
    'FormalProver',
    'ClaimChallenger',
    'VerificationMarket',
    
    # Governance Consensus Layer
    'ConsensusEngine',
    'GovernanceToken',
    'VotingContract',
    'DisputeResolution',
    
    # Verified Reasoning Framework
    'EvidenceReasoner',
    'CitationValidator',
    'LogicalVerifier',
    'UncertaintyQuantifier',
    
    # Anti-Hallucination Governance
    'HallucinationDetector',
    'FactChecker',
    'ConfidenceCalibrator',
    'AnomalyDetector',
    
    # Self-Improvement and Evolution
    'ExperimentRegistry',
    'PromotionGates',
    'RiskGovernance',
    'ComputeBudgetController',
    'SelfImprovementEngine',
    'EvolutionOrchestrator',
    
    # Main Orchestrator
    'FinancialIntelligenceOrchestrator',
]

__version__ = '2.0.0'

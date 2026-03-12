"""
Adversarial Decision Framework - 9-Step Rigorous Trade Validation

This module implements a comprehensive adversarial decision-making system that:
1. Pre-checks hard reality conditions
2. Decomposes trades into falsifiable claims
3. Verifies claims using orthogonal methods
4. Applies adversarial kill phase
5. Calculates calibrated confidence vectors
6. Matches against historical failure modes
7. Enforces strict decision gates
8. Sizes positions using confidence weighting
9. Tracks post-decision outcomes

The system rejects trades by default and only approves when ALL conditions pass.
"""

from .adversarial_core import (
    AdversarialDecisionEngine,
    TradeDecision,
    DecisionOutcome,
    RejectionReason,
)
from .claim_system import (
    TradeClaim,
    ClaimType,
    ClaimVerification,
    ClaimDecomposer,
)
from .verification_system import (
    OrthogonalVerifier,
    VerificationMethod,
    VerificationResult,
)
from .adversarial_roles import (
    AdversarialRole,
    TradeKiller,
    Historian,
    RiskProsecutor,
    ExecutionSaboteur,
    AdversarialKillPhase,
)
from .confidence_vector import (
    ConfidenceVector,
    ConfidenceCalculator,
    ConfidenceThresholds,
)
from .failure_matcher import (
    FailureMode,
    FailureMatcher,
    HistoricalFailureDatabase,
)
from .decision_gate import (
    DecisionGate,
    GateCondition,
    GateResult,
)
from .position_sizer import (
    AdversarialPositionSizer,
    SizingFactors,
)

__all__ = [
    'AdversarialDecisionEngine',
    'TradeDecision',
    'DecisionOutcome',
    'RejectionReason',
    'TradeClaim',
    'ClaimType',
    'ClaimVerification',
    'ClaimDecomposer',
    'OrthogonalVerifier',
    'VerificationMethod',
    'VerificationResult',
    'AdversarialRole',
    'TradeKiller',
    'Historian',
    'RiskProsecutor',
    'ExecutionSaboteur',
    'AdversarialKillPhase',
    'ConfidenceVector',
    'ConfidenceCalculator',
    'ConfidenceThresholds',
    'FailureMode',
    'FailureMatcher',
    'HistoricalFailureDatabase',
    'DecisionGate',
    'GateCondition',
    'GateResult',
    'AdversarialPositionSizer',
    'SizingFactors',
]

def quick_start(config: dict = None):
    """
    Quick start factory for adversarial decision engine.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured AdversarialDecisionEngine instance
    """
    return AdversarialDecisionEngine(config or {})

"""
Adversarial Verification Layer (AVL)

Independent validation that challenges claims before execution.
Provides formal proof requirements and multi-agent verification.
"""

from .validator_agents import ValidatorAgent, ValidatorPool, ValidationResult
from .formal_prover import FormalProver, Proof, ProofStatus, LogicalStatement
from .claim_challenger import ClaimChallenger, Challenge, ChallengeResult
from .verification_market import VerificationMarket, VerificationBounty, VerificationBid

__all__ = [
    'ValidatorAgent',
    'ValidatorPool',
    'ValidationResult',
    'FormalProver',
    'Proof',
    'ProofStatus',
    'LogicalStatement',
    'ClaimChallenger',
    'Challenge',
    'ChallengeResult',
    'VerificationMarket',
    'VerificationBounty',
    'VerificationBid',
]

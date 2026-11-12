"""
Verified Reasoning Framework (VRF)

Evidence-backed reasoning with citation validation and logical verification.
Ensures all reasoning chains are grounded in verifiable evidence.
"""

from .evidence_reasoner import EvidenceReasoner, ReasoningChain, ReasoningStep, ReasoningResult
from .citation_validator import CitationValidator, Citation, CitationStatus, ValidationReport
from .logical_verifier import LogicalVerifier, LogicalStructure, VerificationResult
from .uncertainty_quantifier import UncertaintyQuantifier, UncertaintyEstimate, PropagatedUncertainty

__all__ = [
    'EvidenceReasoner',
    'ReasoningChain',
    'ReasoningStep',
    'ReasoningResult',
    'CitationValidator',
    'Citation',
    'CitationStatus',
    'ValidationReport',
    'LogicalVerifier',
    'LogicalStructure',
    'VerificationResult',
    'UncertaintyQuantifier',
    'UncertaintyEstimate',
    'PropagatedUncertainty',
]

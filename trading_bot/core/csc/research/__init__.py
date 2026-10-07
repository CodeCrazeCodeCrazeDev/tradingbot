"""Unified research capability — the Research Operating System.

All cognition that produces *knowledge* (not trades) flows through here,
under the CognitiveSystemController's authority. Reports and proposals are
advisory-only by construction.
"""

from .state import (
    ConfidenceProfile, EvidenceTier, ReplicationLevel,
    UncertaintyEntry, UncertaintyMap,
)
from .graph import KnowledgeGraph, KGNode
from .questions import ResearchQuestion, generate_questions
from .experiments import (
    ExperimentCandidate, ExperimentContract, VoIEngine, make_contract,
)
from .policy import ResearchPolicy
from .sources import SourceDocument, ExtractedClaim, extract_claims, load_documents
from .engine import CapabilityProposal, ResearchEngine, ResearchReport

__all__ = [
    "CapabilityProposal", "ConfidenceProfile", "EvidenceTier",
    "ExperimentCandidate", "ExperimentContract", "KGNode",
    "KnowledgeGraph", "ReplicationLevel", "ResearchEngine",
    "ResearchPolicy", "ResearchQuestion", "ResearchReport",
    "UncertaintyEntry", "UncertaintyMap", "VoIEngine",
    "SourceDocument", "ExtractedClaim", "extract_claims", "load_documents",
    "generate_questions", "make_contract",
]

"""
Evidence Verification Layer (EVL)

Ensures every decision is backed by verifiable, immutable evidence
through cryptographic provenance chains and Merkle-tree verification.
"""

from .evidence_provenance import EvidenceProvenance, EvidenceRecord, ProvenanceChain
from .merkle_verifier import MerkleVerifier, MerkleTree, MerkleProof
from .data_canonicalizer import DataCanonicalizer, CanonicalDataSource, DataIntegrityReport
from .evidence_stake import EvidenceStake, StakeRecord, SlashingEvent

__all__ = [
    'EvidenceProvenance',
    'EvidenceRecord',
    'ProvenanceChain',
    'MerkleVerifier',
    'MerkleTree',
    'MerkleProof',
    'DataCanonicalizer',
    'CanonicalDataSource',
    'DataIntegrityReport',
    'EvidenceStake',
    'StakeRecord',
    'SlashingEvent',
]

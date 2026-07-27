"""
CMOS Formal Semantic Model & Ontology
=====================================
Phase 1: Formal Semantic Ontology definition for the Cognitive Memory OS.
Specifies node and edge taxonomies, identity/versioning rules, temporal,
provenance, confidence, and contradiction semantics to ensure zero drift
and strict validation.
"""

import hashlib
import json
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class CMOSNodeTier(Enum):
    T0_WORKSPACE = "T0_WORKSPACE"
    T1_EPISODIC = "T1_EPISODIC"
    T2_SEMANTIC = "T2_SEMANTIC"
    T3_PROCEDURAL = "T3_PROCEDURAL"
    T4_RESEARCH = "T4_RESEARCH"
    T5_WORLD_MODEL = "T5_WORLD_MODEL"
    T6_INSTITUTIONAL = "T6_INSTITUTIONAL"
    T7_META_MEMORY = "T7_META_MEMORY"


class CMOSEdgeRelation(Enum):
    CAUSAL = "CAUSAL"          # Node A causes/explains Node B
    TEMPORAL = "TEMPORAL"      # Node A occurred before Node B
    SEMANTIC = "SEMANTIC"      # Node A has conceptual similarity to Node B
    EVIDENTIAL = "EVIDENTIAL"  # Node A supports/refutes Node B
    PROVENANCE = "PROVENANCE"  # Node A was derived from/by Node B
    CONTRADICTS = "CONTRADICTS"# Node A directly contradicts Node B
    META = "META"              # Meta-relationship (e.g. tracks retrieval metrics)


class CMOSProvenance:
    """Strict provenance semantics tracking memory lineage."""
    def __init__(
        self,
        source_agent: str,
        source_input_hash: str,
        source_quality: float = 1.0,  # Range: [0.0, 1.0]
        confidence: float = 1.0,      # Range: [0.0, 1.0]
        evidence_uris: Optional[List[str]] = None,
        creation_time: Optional[float] = None
    ):
        self.source_agent = source_agent
        self.source_input_hash = source_input_hash
        self.source_quality = max(0.0, min(1.0, source_quality))
        self.confidence = max(0.0, min(1.0, confidence))
        self.evidence_uris = evidence_uris or []
        self.creation_time = creation_time or time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_agent": self.source_agent,
            "source_input_hash": self.source_input_hash,
            "source_quality": self.source_quality,
            "confidence": self.confidence,
            "evidence_uris": self.evidence_uris,
            "creation_time": self.creation_time
        }


class CMOSNode:
    """Ontology Node wrapping identity, versioning, temporal decay, and confidence semantics."""
    def __init__(
        self,
        node_id: Optional[str],
        tier: CMOSNodeTier,
        content: Dict[str, Any],
        provenance: CMOSProvenance,
        version: int = 1,
        previous_version_id: Optional[str] = None,
        strength: float = 1.0,
        expiry_time: Optional[float] = None
    ):
        self.tier = tier
        self.content = content
        self.provenance = provenance
        self.version = version
        self.previous_version_id = previous_version_id
        self.strength = strength
        self.expiry_time = expiry_time
        self.created_at = provenance.creation_time
        self.last_accessed = self.created_at
        self.access_count = 1

        # Identity Rule: If node_id is not provided, generate deterministically from content + lineage
        self.node_id = node_id or self.generate_deterministic_id()

    def generate_deterministic_id(self) -> str:
        """Deterministic Identity: prevents duplicates based on content hash and provenance."""
        hasher = hashlib.sha256()
        # Canonical representation of content
        canonical_content = json.dumps(self.content, sort_keys=True)
        hasher.update(canonical_content.encode("utf-8"))
        hasher.update(self.provenance.source_input_hash.encode("utf-8"))
        hasher.update(self.tier.value.encode("utf-8"))
        return f"node_{hasher.hexdigest()[:24]}"

    def create_new_version(self, updated_content: Dict[str, Any], provenance: CMOSProvenance) -> 'CMOSNode':
        """Versioning Rules: Node schemas update creates a new immutable version node linked to previous."""
        return CMOSNode(
            node_id=None,  # Generates deterministically for the new version
            tier=self.tier,
            content=updated_content,
            provenance=provenance,
            version=self.version + 1,
            previous_version_id=self.node_id,
            strength=self.strength,
            expiry_time=self.expiry_time
        )

    def is_expired(self, current_time: float) -> bool:
        """Temporal Semantics: checks whether memory has reached its TTL (expiry)."""
        if self.expiry_time is not None:
            return current_time >= self.expiry_time
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "tier": self.tier.value,
            "content": self.content,
            "provenance": self.provenance.to_dict(),
            "version": self.version,
            "previous_version_id": self.previous_version_id,
            "strength": self.strength,
            "expiry_time": self.expiry_time,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count
        }


class CMOSEdge:
    """Ontology Edge wrapping connection relationships and context-dependent weights."""
    def __init__(
        self,
        source_id: str,
        target_id: str,
        relation: CMOSEdgeRelation,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.relation = relation
        self.weight = max(0.0, weight)
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation.value,
            "weight": self.weight,
            "metadata": self.metadata
        }

"""Hierarchical Memory Engine with Working, Episodic, Semantic, and Procedural tiers."""

import time
import logging
from typing import Dict, Any, List, Optional
from .contracts import MemoryItem, MemoryTier, MemoryValidationStatus

logger = logging.getLogger("alphaalgo.cognition.memory")


class HierarchicalMemoryEngine:
    """Memory manager enforcing tier hierarchy and anti-hallucination governance."""

    def __init__(self, working_capacity: int = 100):
        self.working_capacity = working_capacity
        self.working_memory: List[MemoryItem] = []
        self.episodic_memory: Dict[str, MemoryItem] = {}
        self.semantic_memory: Dict[str, MemoryItem] = {}
        self.procedural_memory: Dict[str, MemoryItem] = {}

    def store_working_observation(self, key: str, content: Any, source: str = "perception") -> MemoryItem:
        """Stores item in Working Memory with auto-eviction."""
        item = MemoryItem(
            memory_id=f"work_{key}_{int(time.time()*1000)}",
            tier=MemoryTier.WORKING,
            content=content,
            source=source,
            timestamp=time.time(),
            confidence=1.0,
            validation_status=MemoryValidationStatus.VALIDATED
        )
        self.working_memory.append(item)
        if len(self.working_memory) > self.working_capacity:
            self.working_memory.pop(0)
        return item

    def store_episodic_event(self, event_id: str, content: Any, source: str, provenance: Dict[str, Any]) -> MemoryItem:
        """Stores an event/decision in Episodic Memory."""
        item = MemoryItem(
            memory_id=f"epi_{event_id}",
            tier=MemoryTier.EPISODIC,
            content=content,
            source=source,
            timestamp=time.time(),
            confidence=1.0,
            validation_status=MemoryValidationStatus.UNVERIFIED,
            provenance=provenance
        )
        self.episodic_memory[event_id] = item
        return item

    def promote_to_semantic(self, key: str, concept: Any, source: str, validation_evidence: Dict[str, Any]) -> MemoryItem:
        """Promotes validated research/pattern knowledge to Semantic Memory."""
        item = MemoryItem(
            memory_id=f"sem_{key}",
            tier=MemoryTier.SEMANTIC,
            content=concept,
            source=source,
            timestamp=time.time(),
            confidence=0.95,
            validation_status=MemoryValidationStatus.VALIDATED,
            provenance=validation_evidence
        )
        self.semantic_memory[key] = item
        return item

    def store_procedural_rule(self, rule_id: str, procedure: Any, source: str) -> MemoryItem:
        """Stores execution/risk procedures in Procedural Memory."""
        item = MemoryItem(
            memory_id=f"proc_{rule_id}",
            tier=MemoryTier.PROCEDURAL,
            content=procedure,
            source=source,
            timestamp=time.time(),
            confidence=1.0,
            validation_status=MemoryValidationStatus.VALIDATED
        )
        self.procedural_memory[rule_id] = item
        return item

    def query_semantic_knowledge(self, key: str) -> Optional[MemoryItem]:
        """Queries authoritative Semantic Memory, suppressing unverified hallucinations."""
        item = self.semantic_memory.get(key)
        if item and item.validation_status == MemoryValidationStatus.VALIDATED:
            return item
        return None

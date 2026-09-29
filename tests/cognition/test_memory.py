"""Tests for Hierarchical Memory Architecture."""

import time
import pytest
from trading_bot.cognition.memory import (
    MemoryItem,
    MemoryTier,
    MemoryValidationStatus,
    HierarchicalMemoryEngine,
)


def test_memory_tier_storage():
    mem = HierarchicalMemoryEngine(working_capacity=3)

    # Working memory
    mem.store_working_observation("obs1", {"price": 1.0850})
    mem.store_working_observation("obs2", {"price": 1.0855})
    mem.store_working_observation("obs3", {"price": 1.0860})
    mem.store_working_observation("obs4", {"price": 1.0865})

    assert len(mem.working_memory) == 3  # Capacity evicted oldest

    # Semantic memory
    mem.promote_to_semantic("regime_pattern", {"pattern": "bull_flag"}, "research", {"p_value": 0.01})

    result = mem.query_semantic_knowledge("regime_pattern")
    assert result is not None
    assert result.content == {"pattern": "bull_flag"}
    assert result.validation_status == MemoryValidationStatus.VALIDATED


def test_unverified_semantic_query():
    mem = HierarchicalMemoryEngine()
    unverified_item = MemoryItem(
        memory_id="sem_unverified",
        tier=MemoryTier.SEMANTIC,
        content={"hallucination": "fake"},
        source="llm",
        timestamp=time.time(),
        validation_status=MemoryValidationStatus.UNVERIFIED
    )
    mem.semantic_memory["unverified"] = unverified_item

    # Should return None because it is not VALIDATED
    assert mem.query_semantic_knowledge("unverified") is None

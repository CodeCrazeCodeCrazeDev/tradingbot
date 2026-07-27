"""
Comprehensive Memory Systems for World Model
===========================================
- Episodic: Specific trade events
- Semantic: General market knowledge/rules
- Regime: Historical market regimes
- Execution: Slippage/Impact history
- Failure: Known edge cases/errors
- Strategy: Historical performance of strategies
"""

from typing import Dict, List, Any, Optional
import torch
import logging

logger = logging.getLogger(__name__)

class SpecializedMemory:
    """
    Base class for specialized memory modules.
    """
    def __init__(self, name: str, capacity: int = 1000):
        self.name = name
        self.capacity = capacity
        self.buffer = []

    def store(self, item: Any):
        self.buffer.append(item)
        if len(self.buffer) > self.capacity:
            self.buffer.pop(0)

    def retrieve(self, query: Any) -> List[Any]:
        # Simple retrieval logic: return most recent items
        return self.buffer[-5:]

class WorldModelMemorySystem:
    """
    Unified memory system for the World Model.
    """
    def __init__(self):
        self.memories = {
            "episodic": SpecializedMemory("episodic", 5000),
            "semantic": SpecializedMemory("semantic", 1000),
            "regime": SpecializedMemory("regime", 500),
            "execution": SpecializedMemory("execution", 2000),
            "failure": SpecializedMemory("failure", 500),
            "strategy": SpecializedMemory("strategy", 1000)
        }
        logger.info("🧠 World Model Memory Systems initialized")

    def record_event(self, memory_type: str, data: Any):
        if memory_type in self.memories:
            self.memories[memory_type].store(data)

    def query_memory(self, memory_type: str, query: Any) -> List[Any]:
        if memory_type in self.memories:
            return self.memories[memory_type].retrieve(query)
        return []

"""Memory contracts and governance schemas."""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional


class MemoryTier(Enum):
    WORKING = "WORKING"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"


class MemoryValidationStatus(Enum):
    UNVERIFIED = "UNVERIFIED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"


@dataclass
class MemoryItem:
    """Typed memory item with full governance attributes."""
    memory_id: str
    tier: MemoryTier
    content: Any
    source: str
    timestamp: float
    confidence: float = 1.0
    validation_status: MemoryValidationStatus = MemoryValidationStatus.UNVERIFIED
    provenance: Dict[str, Any] = field(default_factory=dict)
    decay_rate: float = 0.01  # Per hour
    relevance_score: float = 1.0
    version: str = "1.0.0"

    def compute_decayed_relevance(self, current_time: float) -> float:
        """Calculates time-decayed relevance score."""
        age_hours = max(0.0, (current_time - self.timestamp) / 3600.0)
        decay_factor = math.exp(-self.decay_rate * age_hours)
        self.relevance_score = round(self.confidence * decay_factor, 4)
        return self.relevance_score

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

class SwarmLayer(Enum):
    MICRO = "micro"
    EXPERT = "expert"
    EVOLUTION = "evolution"

class SwarmTaskType(Enum):
    ANALYSIS = "analysis"
    CONSENSUS = "consensus"
    DEBATE = "debate"
    RESEARCH = "research"

@dataclass
class SwarmSignal:
    """Standardized signal from any swarm component"""
    source_id: str
    layer: SwarmLayer
    direction: float  # -1 to 1
    confidence: float # 0 to 1
    evidence: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SwarmConsensus:
    """Aggregated consensus from the swarm"""
    direction: float
    confidence: float
    dissent_ratio: float
    contributing_signals: List[SwarmSignal]
    dominant_factors: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'direction': self.direction,
            'confidence': self.confidence,
            'dissent_ratio': self.dissent_ratio,
            'dominant_factors': self.dominant_factors,
            'timestamp': self.timestamp.isoformat(),
            'signal_count': len(self.contributing_signals)
        }

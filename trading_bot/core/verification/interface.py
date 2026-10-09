from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class VerifierVerdict:
    agent_name: str
    is_valid: bool
    confidence: float
    evidence: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    recommendation: str = ""
    critique: str = ""
    # Evidence items actually examined — a verdict with items_checked=0
    # passed vacuously and must not be reported as substantive consensus.
    items_checked: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

class IVerifier(ABC):
    @abstractmethod
    async def audit(self, research_snapshot: Any) -> VerifierVerdict:
        """Perform an independent audit of the research snapshot."""
        pass

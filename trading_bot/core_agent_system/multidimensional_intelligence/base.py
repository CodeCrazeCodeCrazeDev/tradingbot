"""
Base interfaces for Multidimensional Intelligence modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable


class IntelligenceDomain(Enum):
    BIOLOGY = "biology"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    MATHEMATICS = "mathematics"
    NATURE = "nature"


@dataclass
class Hypothesis:
    hypothesis_id: str
    domain: IntelligenceDomain
    concept: str
    mathematical_representation: str
    description: str
    expected_outcome: str
    priority: float
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, testing, validated, rejected


@dataclass
class MultidimensionalExperiment:
    experiment_id: str
    hypothesis_id: str
    parameters: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"


class MultidimensionalModule(ABC):
    """Base class for domain-specific intelligence modules."""

    def __init__(self, domain: IntelligenceDomain, config: Optional[Dict] = None):
        self.domain = domain
        self.config = config or {}
        self.active_hypotheses: List[Hypothesis] = []

    @abstractmethod
    async def generate_hypotheses(self, market_context: Dict[str, Any]) -> List[Hypothesis]:
        """Generate new hypotheses based on domain principles and market context."""
        pass

    @abstractmethod
    async def create_mathematical_model(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Translate a hypothesis into a measurable mathematical model."""
        pass

    @abstractmethod
    async def get_feature_generators(self) -> List[Callable]:
        """Return a list of feature generator functions derived from this domain."""
        pass

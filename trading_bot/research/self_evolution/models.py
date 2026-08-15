from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class MutantStrategy:
    """Represents a mutated strategy candidate inside the evolution sandbox."""
    mutant_id: str
    parent_id: str
    code_patch: str
    parameters: Dict[str, Any]
    mutated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class InvariantReport:
    """The compliance audit output of the Invariant Gate."""
    is_valid: bool
    security_passed: bool
    risk_passed: bool
    license_passed: bool
    validation_passed: bool
    violations: List[str] = field(default_factory=list)


@dataclass
class TournamentResult:
    """The outcome of a CEDA multi-regime tournament."""
    is_promoted: bool
    wins: int
    losses: int
    regimes_tested: List[str]
    explanation: str
    compared_at: datetime = field(default_factory=datetime.utcnow)

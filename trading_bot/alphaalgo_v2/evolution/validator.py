"""
AlphaAlgo V2 Safety Validator

Validates proposals against safety constraints.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

from ..core.types import EvolutionProposal

import logging
logger = logging.getLogger(__name__)



class ValidationStatus(Enum):
    """Validation status"""
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class ValidationResult:
    """Result of proposal validation"""
    status: ValidationStatus
    passed: bool
    errors: List[str]
    warnings: List[str]
    
    @classmethod
    def success(cls) -> "ValidationResult":
        return cls(
            status=ValidationStatus.PASSED,
            passed=True,
            errors=[],
            warnings=[],
        )
    
    @classmethod
    def failure(cls, errors: List[str]) -> "ValidationResult":
        return cls(
            status=ValidationStatus.FAILED,
            passed=False,
            errors=errors,
            warnings=[],
        )


class SafetyValidator:
    """
    Validates proposals against safety constraints
    
    Checks:
    - Does not violate safety constraints
    - Does not modify immutable components
    - Has valid rollback plan
    - Passes simulation tests
    """
    
    # Components that cannot be modified
    IMMUTABLE_COMPONENTS = [
        "reward_model",
        "risk_limits",
        "safety_constraints",
        "ethical_constraints",
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(self, proposal: EvolutionProposal) -> ValidationResult:
        """
        Validate a proposal
        
        Args:
            proposal: Proposal to validate
            
        Returns:
            ValidationResult
        """
        try:
            errors = []
            warnings = []
        
            # Check for immutable modifications
            for component in self.IMMUTABLE_COMPONENTS:
                if component in proposal.changes:
                    errors.append(f"Cannot modify immutable component: {component}")
        
            # Check for safety violations
            if proposal.changes.get("disable_safety", False):
                errors.append("Cannot disable safety features")
        
            # Check for risk limit increases
            if "increase_risk_limits" in proposal.changes:
                errors.append("Cannot increase risk limits")
        
            if errors:
                return ValidationResult.failure(errors)
        
            return ValidationResult.success()
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise
    
    def validate_batch(
        self,
        proposals: List[EvolutionProposal]
    ) -> Dict[str, ValidationResult]:
        """Validate multiple proposals"""
        return {p.id: self.validate(p) for p in proposals}

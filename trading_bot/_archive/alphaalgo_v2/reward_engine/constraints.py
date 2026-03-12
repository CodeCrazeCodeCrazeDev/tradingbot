"""
AlphaAlgo V2 Constraint Checker

Validates that trading activity stays within safety constraints.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

from ..core.constants import (
    MAX_RISK_PER_TRADE,
    MAX_DAILY_LOSS,
    MAX_DRAWDOWN,
    MAX_LEVERAGE,
    MAX_POSITION_SIZE,
)


class ConstraintSeverity(Enum):
    """Constraint violation severity"""
    WARNING = "warning"
    CRITICAL = "critical"
    FATAL = "fatal"


@dataclass
class ConstraintViolation:
    """Record of a constraint violation"""
    constraint_name: str
    current_value: float
    limit_value: float
    severity: ConstraintSeverity
    message: str
    
    def to_dict(self) -> Dict:
        return {
            "constraint": self.constraint_name,
            "current": self.current_value,
            "limit": self.limit_value,
            "severity": self.severity.value,
            "message": self.message,
        }


class ConstraintChecker:
    """
    Checks trading activity against safety constraints
    
    Constraints are IMMUTABLE and cannot be modified.
    """
    
    def __init__(self):
        self._constraints = {
            "max_risk_per_trade": MAX_RISK_PER_TRADE,
            "max_daily_loss": MAX_DAILY_LOSS,
            "max_drawdown": MAX_DRAWDOWN,
            "max_leverage": MAX_LEVERAGE,
            "max_position_size": MAX_POSITION_SIZE,
        }
    
    def check_all(self, metrics: Dict[str, float]) -> List[ConstraintViolation]:
        """
        Check all constraints
        
        Args:
            metrics: Current metrics to check
            
        Returns:
            List of violations (empty if all pass)
        """
        violations = []
        
        # Check risk per trade
        if "risk_per_trade" in metrics:
            if metrics["risk_per_trade"] > self._constraints["max_risk_per_trade"]:
                violations.append(ConstraintViolation(
                    constraint_name="max_risk_per_trade",
                    current_value=metrics["risk_per_trade"],
                    limit_value=self._constraints["max_risk_per_trade"],
                    severity=ConstraintSeverity.CRITICAL,
                    message=f"Risk per trade {metrics['risk_per_trade']:.1%} exceeds limit {self._constraints['max_risk_per_trade']:.1%}",
                ))
        
        # Check daily loss
        if "daily_loss" in metrics:
            if metrics["daily_loss"] > self._constraints["max_daily_loss"]:
                violations.append(ConstraintViolation(
                    constraint_name="max_daily_loss",
                    current_value=metrics["daily_loss"],
                    limit_value=self._constraints["max_daily_loss"],
                    severity=ConstraintSeverity.FATAL,
                    message=f"Daily loss {metrics['daily_loss']:.1%} exceeds limit {self._constraints['max_daily_loss']:.1%}",
                ))
        
        # Check drawdown
        if "drawdown" in metrics:
            if metrics["drawdown"] > self._constraints["max_drawdown"]:
                violations.append(ConstraintViolation(
                    constraint_name="max_drawdown",
                    current_value=metrics["drawdown"],
                    limit_value=self._constraints["max_drawdown"],
                    severity=ConstraintSeverity.FATAL,
                    message=f"Drawdown {metrics['drawdown']:.1%} exceeds limit {self._constraints['max_drawdown']:.1%}",
                ))
        
        # Check leverage
        if "leverage" in metrics:
            if metrics["leverage"] > self._constraints["max_leverage"]:
                violations.append(ConstraintViolation(
                    constraint_name="max_leverage",
                    current_value=metrics["leverage"],
                    limit_value=self._constraints["max_leverage"],
                    severity=ConstraintSeverity.CRITICAL,
                    message=f"Leverage {metrics['leverage']:.1f}x exceeds limit {self._constraints['max_leverage']:.1f}x",
                ))
        
        # Check position size
        if "position_size" in metrics:
            if metrics["position_size"] > self._constraints["max_position_size"]:
                violations.append(ConstraintViolation(
                    constraint_name="max_position_size",
                    current_value=metrics["position_size"],
                    limit_value=self._constraints["max_position_size"],
                    severity=ConstraintSeverity.CRITICAL,
                    message=f"Position size {metrics['position_size']:.1%} exceeds limit {self._constraints['max_position_size']:.1%}",
                ))
        
        return violations
    
    def has_fatal_violations(self, violations: List[ConstraintViolation]) -> bool:
        """Check if any violations are fatal"""
        return any(v.severity == ConstraintSeverity.FATAL for v in violations)
    
    def has_critical_violations(self, violations: List[ConstraintViolation]) -> bool:
        """Check if any violations are critical or fatal"""
        return any(
            v.severity in [ConstraintSeverity.CRITICAL, ConstraintSeverity.FATAL]
            for v in violations
        )

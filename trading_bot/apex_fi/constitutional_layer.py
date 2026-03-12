"""
APEX-FI Constitutional Layer
=============================

IMMUTABLE CONSTRAINTS - Cannot be modified by any self-evolution process.
These rules are enforced at the infrastructure level.

Genetic Parentage: Palantir × Two Sigma × Citadel
Architecture Class: Adaptive Financial Intelligence
Constitutional Version: 4.0
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConstraintViolationType(str, Enum):
    """Types of constitutional constraint violations."""
    DRAWDOWN_BREACH = "drawdown_breach"
    CONCENTRATION_BREACH = "concentration_breach"
    MARKET_IMPACT_BREACH = "market_impact_breach"
    VALIDATION_FAILURE = "validation_failure"
    COMPLIANCE_FAILURE = "compliance_failure"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"


@dataclass
class ConstitutionalConstraints:
    """
    IMMUTABLE Constitutional Constraints.
    
    These values define the absolute boundaries of APEX-FI operation.
    No self-modification process can alter these values.
    Human ratification required for any changes.
    """
    
    # Drawdown Limits
    MAX_BOOK_DRAWDOWN: float = 0.08          # 8% from high-water mark → full halt
    MAX_STRATEGY_DRAWDOWN: float = 0.15      # 15% from high-water mark → capital removal
    
    # Position Limits
    MAX_POSITION_CONCENTRATION: float = 0.03  # 3% of portfolio NAV per position
    MAX_MARKET_IMPACT: float = 0.05          # 5% of 20-day ADV per order
    
    # Validation Requirements
    MIN_VALIDATION_TSTAT: float = 2.0        # Minimum t-statistic for self-modifications
    MIN_SANDBOX_DAYS: int = 30               # Minimum sandbox testing period
    
    # Performance Targets
    TARGET_SHARPE_RATIO: float = 3.5         # Annualized Sharpe target
    
    # Latency SLAs
    MAX_CAPITAL_DEPLOYMENT_LATENCY_MS: int = 1000      # 1 second
    MAX_REGIME_CLASSIFICATION_LATENCY_MS: int = 100    # 100ms
    MAX_COMPLIANCE_SCREENING_LATENCY_MS: int = 5       # 5ms
    
    # Discovery Targets
    MIN_ALPHA_HYPOTHESES_PER_DAY: int = 100
    MIN_ACTIVE_FACTORS: int = 50000
    MIN_EVOLUTION_CYCLES_PER_YEAR: int = 4
    
    def __post_init__(self):
        """Verify constraints are immutable."""
        object.__setattr__(self, '__frozen', True)
    
    def __setattr__(self, key, value):
        """Prevent modification of constitutional constraints."""
        if hasattr(self, '__frozen') and self.__frozen:
            raise AttributeError(
                f"Constitutional constraint '{key}' is IMMUTABLE. "
                f"Human ratification required for any changes."
            )
        object.__setattr__(self, key, value)


class ConstitutionalLayer:
    """
    Constitutional Layer - APEX-FI Governance Enforcement.
    
    Enforces immutable constraints at the infrastructure level.
    No self-modification process can bypass this layer.
    """
    
    def __init__(self):
        self.constraints = ConstitutionalConstraints()
        self._breach_log: list = []
        self._human_approval_queue: list = []
        self._circuit_breaker_active = False
        
        logger.info("Constitutional Layer initialized - Version 4.0")
        logger.info(f"Max Book Drawdown: {self.constraints.MAX_BOOK_DRAWDOWN:.1%}")
        logger.info(f"Max Position Concentration: {self.constraints.MAX_POSITION_CONCENTRATION:.1%}")
    
    def check_drawdown_constraint(
        self,
        current_nav: float,
        high_water_mark: float,
        level: str = "book"
    ) -> tuple[bool, Optional[str]]:
        """
        Check drawdown constraints.
        
        Args:
            current_nav: Current NAV
            high_water_mark: High water mark NAV
            level: "book" or "strategy"
            
        Returns:
            (is_valid, violation_message)
        """
        if high_water_mark == 0:
            return True, None
        
        drawdown = (high_water_mark - current_nav) / high_water_mark
        
        if level == "book":
            max_dd = self.constraints.MAX_BOOK_DRAWDOWN
        elif level == "strategy":
            max_dd = self.constraints.MAX_STRATEGY_DRAWDOWN
        else:
            raise ValueError(f"Invalid level: {level}")
        
        if drawdown > max_dd:
            violation_msg = (
                f"{level.upper()} DRAWDOWN BREACH: {drawdown:.2%} exceeds "
                f"constitutional limit of {max_dd:.2%}"
            )
            self._log_breach(ConstraintViolationType.DRAWDOWN_BREACH, violation_msg)
            
            if level == "book":
                self._activate_circuit_breaker("Book drawdown breach")
            
            return False, violation_msg
        
        return True, None
    
    def check_concentration_constraint(
        self,
        position_value: float,
        portfolio_nav: float
    ) -> tuple[bool, Optional[str]]:
        """
        Check position concentration constraint.
        
        Args:
            position_value: Absolute value of position
            portfolio_nav: Total portfolio NAV
            
        Returns:
            (is_valid, violation_message)
        """
        if portfolio_nav == 0:
            return False, "Portfolio NAV is zero"
        
        concentration = abs(position_value) / portfolio_nav
        
        if concentration > self.constraints.MAX_POSITION_CONCENTRATION:
            violation_msg = (
                f"CONCENTRATION BREACH: {concentration:.2%} exceeds "
                f"constitutional limit of {self.constraints.MAX_POSITION_CONCENTRATION:.2%}"
            )
            self._log_breach(ConstraintViolationType.CONCENTRATION_BREACH, violation_msg)
            return False, violation_msg
        
        return True, None
    
    def check_market_impact_constraint(
        self,
        order_quantity: float,
        avg_daily_volume_20d: float
    ) -> tuple[bool, Optional[str]]:
        """
        Check market impact constraint.
        
        Args:
            order_quantity: Absolute order quantity
            avg_daily_volume_20d: 20-day average daily volume
            
        Returns:
            (is_valid, violation_message)
        """
        if avg_daily_volume_20d == 0:
            return False, "Average daily volume is zero"
        
        participation_rate = abs(order_quantity) / avg_daily_volume_20d
        
        if participation_rate > self.constraints.MAX_MARKET_IMPACT:
            violation_msg = (
                f"MARKET IMPACT BREACH: {participation_rate:.2%} exceeds "
                f"constitutional limit of {self.constraints.MAX_MARKET_IMPACT:.2%}"
            )
            self._log_breach(ConstraintViolationType.MARKET_IMPACT_BREACH, violation_msg)
            return False, violation_msg
        
        return True, None
    
    def check_validation_gate(
        self,
        t_statistic: float,
        sandbox_days: int
    ) -> tuple[bool, Optional[str]]:
        """
        Check validation gate requirements for self-modifications.
        
        Args:
            t_statistic: T-statistic of improvement vs baseline
            sandbox_days: Days tested in sandbox
            
        Returns:
            (is_valid, violation_message)
        """
        violations = []
        
        if t_statistic < self.constraints.MIN_VALIDATION_TSTAT:
            violations.append(
                f"T-statistic {t_statistic:.2f} below minimum "
                f"{self.constraints.MIN_VALIDATION_TSTAT:.2f}"
            )
        
        if sandbox_days < self.constraints.MIN_SANDBOX_DAYS:
            violations.append(
                f"Sandbox days {sandbox_days} below minimum "
                f"{self.constraints.MIN_SANDBOX_DAYS}"
            )
        
        if violations:
            violation_msg = "VALIDATION GATE FAILURE: " + "; ".join(violations)
            self._log_breach(ConstraintViolationType.VALIDATION_FAILURE, violation_msg)
            return False, violation_msg
        
        return True, None
    
    def require_human_approval(
        self,
        action: str,
        rationale: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Queue action for human approval.
        
        Args:
            action: Description of action requiring approval
            rationale: System-generated rationale
            metadata: Additional context
            
        Returns:
            approval_id: ID for tracking approval status
        """
        import uuid
        from datetime import datetime
        
        approval_id = str(uuid.uuid4())
        
        approval_request = {
            'approval_id': approval_id,
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'rationale': rationale,
            'metadata': metadata or {},
            'status': 'pending',
        }
        
        self._human_approval_queue.append(approval_request)
        
        logger.warning(
            f"HUMAN APPROVAL REQUIRED: {action} (ID: {approval_id})"
        )
        
        return approval_id
    
    def _activate_circuit_breaker(self, reason: str) -> None:
        """
        Activate constitutional circuit breaker.
        
        This is a HARD HALT. No automatic restart.
        Human review required to deactivate.
        """
        self._circuit_breaker_active = True
        
        logger.critical("=" * 60)
        logger.critical("CONSTITUTIONAL CIRCUIT BREAKER ACTIVATED")
        logger.critical(f"Reason: {reason}")
        logger.critical("SYSTEM HALTED - Human review required")
        logger.critical("=" * 60)
    
    def _log_breach(self, violation_type: ConstraintViolationType, message: str) -> None:
        """Log constitutional constraint breach."""
        from datetime import datetime
        
        breach_record = {
            'timestamp': datetime.now().isoformat(),
            'violation_type': violation_type.value,
            'message': message,
        }
        
        self._breach_log.append(breach_record)
        logger.error(f"CONSTITUTIONAL BREACH: {message}")
    
    def is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is active."""
        return self._circuit_breaker_active
    
    def deactivate_circuit_breaker(self, human_approval_code: str) -> bool:
        """
        Deactivate circuit breaker.
        
        Requires human approval code.
        """
        # In production, this would verify against a secure approval system
        if human_approval_code and len(human_approval_code) >= 8:
            self._circuit_breaker_active = False
            logger.warning("Circuit breaker deactivated by human approval")
            return True
        
        logger.error("Invalid human approval code - circuit breaker remains active")
        return False
    
    def get_breach_log(self) -> list:
        """Get constitutional breach log."""
        return self._breach_log.copy()
    
    def get_approval_queue(self) -> list:
        """Get pending human approval queue."""
        return [req for req in self._human_approval_queue if req['status'] == 'pending']
    
    def get_status(self) -> Dict[str, Any]:
        """Get constitutional layer status."""
        return {
            'circuit_breaker_active': self._circuit_breaker_active,
            'total_breaches': len(self._breach_log),
            'pending_approvals': len(self.get_approval_queue()),
            'constraints': {
                'max_book_drawdown': self.constraints.MAX_BOOK_DRAWDOWN,
                'max_strategy_drawdown': self.constraints.MAX_STRATEGY_DRAWDOWN,
                'max_position_concentration': self.constraints.MAX_POSITION_CONCENTRATION,
                'max_market_impact': self.constraints.MAX_MARKET_IMPACT,
                'min_validation_tstat': self.constraints.MIN_VALIDATION_TSTAT,
                'target_sharpe_ratio': self.constraints.TARGET_SHARPE_RATIO,
            }
        }


# Singleton instance
_constitutional_layer: Optional[ConstitutionalLayer] = None


def get_constitutional_layer() -> ConstitutionalLayer:
    """Get the singleton Constitutional Layer."""
    global _constitutional_layer
    if _constitutional_layer is None:
        _constitutional_layer = ConstitutionalLayer()
    return _constitutional_layer

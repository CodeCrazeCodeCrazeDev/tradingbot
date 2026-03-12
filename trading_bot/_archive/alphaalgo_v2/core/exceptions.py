"""
AlphaAlgo V2 Core Exceptions

STABILITY GUARANTEE: These exceptions are FROZEN and will NEVER change.
All components use these exceptions for error handling.

Exception Hierarchy:
- AlphaAlgoError (base)
  - DataError
    - DataValidationError
    - DataStalenessError
  - ExecutionError
    - OrderRejectedError
    - BrokerConnectionError
  - RiskError
    - RiskLimitExceededError
    - DrawdownLimitError
  - ValidationError
  - ConfigurationError
  - EvolutionError
"""

from typing import Any, Dict, Optional
from dataclasses import field

import logging
logger = logging.getLogger(__name__)



class AlphaAlgoError(Exception):
    """
    Base exception for all AlphaAlgo errors
    
    Attributes:
        message: Error message
        code: Error code
        details: Additional error details
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or "ALPHAALGO_ERROR"
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# ============================================================================
# DATA ERRORS
# ============================================================================

class DataError(AlphaAlgoError):
    """Base exception for data-related errors"""
    
    def __init__(
        self,
        message: str,
        symbol: Optional[str] = None,
        source: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, code="DATA_ERROR", **kwargs)
        self.symbol = symbol
        self.source = source
        self.details.update({
            "symbol": symbol,
            "source": source,
        })


class DataValidationError(DataError):
    """Raised when data fails validation"""
    
    def __init__(
        self,
        message: str,
        validation_errors: Optional[list] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.code = "DATA_VALIDATION_ERROR"
        self.validation_errors = validation_errors or []
        self.details["validation_errors"] = self.validation_errors


class DataStalenessError(DataError):
    """Raised when data is stale/outdated"""
    
    def __init__(
        self,
        message: str,
        age_seconds: Optional[float] = None,
        max_age_seconds: Optional[float] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.code = "DATA_STALENESS_ERROR"
        self.age_seconds = age_seconds
        self.max_age_seconds = max_age_seconds
        self.details.update({
            "age_seconds": age_seconds,
            "max_age_seconds": max_age_seconds,
        })


# ============================================================================
# EXECUTION ERRORS
# ============================================================================

class ExecutionError(AlphaAlgoError):
    """Base exception for execution-related errors"""
    
    def __init__(
        self,
        message: str,
        order_id: Optional[str] = None,
        symbol: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, code="EXECUTION_ERROR", **kwargs)
        self.order_id = order_id
        self.symbol = symbol
        self.details.update({
            "order_id": order_id,
            "symbol": symbol,
        })


class OrderRejectedError(ExecutionError):
    """Raised when order is rejected by broker"""
    
    def __init__(
        self,
        message: str,
        rejection_reason: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.code = "ORDER_REJECTED_ERROR"
        self.rejection_reason = rejection_reason
        self.details["rejection_reason"] = rejection_reason


class BrokerConnectionError(ExecutionError):
    """Raised when broker connection fails"""
    
    def __init__(
        self,
        message: str,
        broker: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.code = "BROKER_CONNECTION_ERROR"
        self.broker = broker
        self.details["broker"] = broker


class SlippageError(ExecutionError):
    """Raised when slippage exceeds threshold"""
    
    def __init__(
        self,
        message: str,
        expected_price: Optional[float] = None,
        actual_price: Optional[float] = None,
        slippage_pips: Optional[float] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.code = "SLIPPAGE_ERROR"
        self.expected_price = expected_price
        self.actual_price = actual_price
        self.slippage_pips = slippage_pips
        self.details.update({
            "expected_price": expected_price,
            "actual_price": actual_price,
            "slippage_pips": slippage_pips,
        })


# ============================================================================
# RISK ERRORS
# ============================================================================

class RiskError(AlphaAlgoError):
    """Base exception for risk-related errors"""
    
    def __init__(
        self,
        message: str,
        risk_type: Optional[str] = None,
        current_value: Optional[float] = None,
        limit_value: Optional[float] = None,
        **kwargs
    ):
        super().__init__(message, code="RISK_ERROR", **kwargs)
        self.risk_type = risk_type
        self.current_value = current_value
        self.limit_value = limit_value
        self.details.update({
            "risk_type": risk_type,
            "current_value": current_value,
            "limit_value": limit_value,
        })


class RiskLimitExceededError(RiskError):
    """Raised when risk limit is exceeded"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.code = "RISK_LIMIT_EXCEEDED_ERROR"


class DrawdownLimitError(RiskError):
    """Raised when drawdown limit is exceeded"""
    
    def __init__(
        self,
        message: str,
        current_drawdown: Optional[float] = None,
        max_drawdown: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            message,
            risk_type="drawdown",
            current_value=current_drawdown,
            limit_value=max_drawdown,
            **kwargs
        )
        self.code = "DRAWDOWN_LIMIT_ERROR"
        self.current_drawdown = current_drawdown
        self.max_drawdown = max_drawdown


class DailyLossLimitError(RiskError):
    """Raised when daily loss limit is exceeded"""
    
    def __init__(
        self,
        message: str,
        current_loss: Optional[float] = None,
        max_loss: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            message,
            risk_type="daily_loss",
            current_value=current_loss,
            limit_value=max_loss,
            **kwargs
        )
        self.code = "DAILY_LOSS_LIMIT_ERROR"


class PositionSizeError(RiskError):
    """Raised when position size exceeds limits"""
    
    def __init__(
        self,
        message: str,
        requested_size: Optional[float] = None,
        max_size: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            message,
            risk_type="position_size",
            current_value=requested_size,
            limit_value=max_size,
            **kwargs
        )
        self.code = "POSITION_SIZE_ERROR"


# ============================================================================
# VALIDATION ERRORS
# ============================================================================

class ValidationError(AlphaAlgoError):
    """Raised when validation fails"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)
        self.field = field
        self.value = value
        self.details.update({
            "field": field,
            "value": str(value) if value is not None else None,
        })


class SignalValidationError(ValidationError):
    """Raised when signal validation fails"""
    
    def __init__(self, message: str, signal_id: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.code = "SIGNAL_VALIDATION_ERROR"
        self.signal_id = signal_id
        self.details["signal_id"] = signal_id


# ============================================================================
# CONFIGURATION ERRORS
# ============================================================================

class ConfigurationError(AlphaAlgoError):
    """Raised when configuration is invalid"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, code="CONFIGURATION_ERROR", **kwargs)
        self.config_key = config_key
        self.details["config_key"] = config_key


# ============================================================================
# EVOLUTION ERRORS
# ============================================================================

class EvolutionError(AlphaAlgoError):
    """Base exception for evolution-related errors"""
    
    def __init__(
        self,
        message: str,
        proposal_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, code="EVOLUTION_ERROR", **kwargs)
        self.proposal_id = proposal_id
        self.details["proposal_id"] = proposal_id


class ProposalRejectedError(EvolutionError):
    """Raised when evolution proposal is rejected"""
    
    def __init__(
        self,
        message: str,
        rejection_reason: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.code = "PROPOSAL_REJECTED_ERROR"
        self.rejection_reason = rejection_reason
        self.details["rejection_reason"] = rejection_reason


class SafetyViolationError(EvolutionError):
    """Raised when proposal violates safety constraints"""
    
    def __init__(
        self,
        message: str,
        violated_constraints: Optional[list] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.code = "SAFETY_VIOLATION_ERROR"
        self.violated_constraints = violated_constraints or []
        self.details["violated_constraints"] = self.violated_constraints


class HumanApprovalRequiredError(EvolutionError):
    """Raised when human approval is required"""
    
    def __init__(
        self,
        message: str,
        approval_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.code = "HUMAN_APPROVAL_REQUIRED_ERROR"
        self.approval_type = approval_type
        self.details["approval_type"] = approval_type


# ============================================================================
# SYSTEM ERRORS
# ============================================================================

class SystemError(AlphaAlgoError):
    """Base exception for system-level errors"""
    
    def __init__(self, message: str, component: Optional[str] = None, **kwargs):
        super().__init__(message, code="SYSTEM_ERROR", **kwargs)
        self.component = component
        self.details["component"] = component


class ComponentNotFoundError(SystemError):
    """Raised when required component is not found"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.code = "COMPONENT_NOT_FOUND_ERROR"


class InitializationError(SystemError):
    """Raised when component initialization fails"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.code = "INITIALIZATION_ERROR"


class ShutdownError(SystemError):
    """Raised when shutdown fails"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.code = "SHUTDOWN_ERROR"

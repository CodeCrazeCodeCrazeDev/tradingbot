"""
AlphaAlgo Core Exceptions - STABLE EXCEPTION HIERARCHY

These exceptions are FROZEN and should NEVER change.
All modules must use these exceptions for error handling.

Version: 1.0.0 (FROZEN)
"""

from typing import Any, Dict, Optional
from dataclasses import field

import logging
logger = logging.getLogger(__name__)



# =============================================================================
# BASE EXCEPTION - FROZEN
# =============================================================================

class AlphaAlgoError(Exception):
    """
    Base exception for all AlphaAlgo errors - FROZEN
    
    All custom exceptions must inherit from this class.
    """
    
    def __init__(
        self, 
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.recoverable = recoverable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'code': self.code,
            'details': self.details,
            'recoverable': self.recoverable,
        }
    
    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


# =============================================================================
# DATA EXCEPTIONS - FROZEN
# =============================================================================

class DataError(AlphaAlgoError):
    """Base exception for data-related errors - FROZEN"""
    pass


class DataConnectionError(DataError):
    """Error connecting to data source - FROZEN"""
    
    def __init__(self, source: str, message: str = "Failed to connect to data source"):
        super().__init__(
            message=f"{message}: {source}",
            code="DATA_CONNECTION_ERROR",
            details={'source': source}
        )


class DataValidationError(DataError):
    """Error validating data - FROZEN"""
    
    def __init__(self, field: str, reason: str, value: Any = None):
        super().__init__(
            message=f"Data validation failed for '{field}': {reason}",
            code="DATA_VALIDATION_ERROR",
            details={'field': field, 'reason': reason, 'value': str(value)}
        )


class DataStalenessError(DataError):
    """Error when data is stale - FROZEN"""
    
    def __init__(self, symbol: str, age_seconds: float, max_age_seconds: float):
        super().__init__(
            message=f"Data for {symbol} is stale ({age_seconds:.1f}s > {max_age_seconds:.1f}s)",
            code="DATA_STALENESS_ERROR",
            details={
                'symbol': symbol,
                'age_seconds': age_seconds,
                'max_age_seconds': max_age_seconds
            }
        )


class DataNotFoundError(DataError):
    """Error when data is not found - FROZEN"""
    
    def __init__(self, symbol: str, data_type: str = "data"):
        super().__init__(
            message=f"{data_type} not found for {symbol}",
            code="DATA_NOT_FOUND",
            details={'symbol': symbol, 'data_type': data_type}
        )


# =============================================================================
# SIGNAL EXCEPTIONS - FROZEN
# =============================================================================

class SignalError(AlphaAlgoError):
    """Base exception for signal-related errors - FROZEN"""
    pass


class SignalGenerationError(SignalError):
    """Error generating signal - FROZEN"""
    
    def __init__(self, generator: str, reason: str):
        super().__init__(
            message=f"Signal generation failed in {generator}: {reason}",
            code="SIGNAL_GENERATION_ERROR",
            details={'generator': generator, 'reason': reason}
        )


class SignalValidationError(SignalError):
    """Error validating signal - FROZEN"""
    
    def __init__(self, signal_id: str, reasons: list):
        super().__init__(
            message=f"Signal {signal_id} failed validation: {', '.join(reasons)}",
            code="SIGNAL_VALIDATION_ERROR",
            details={'signal_id': signal_id, 'reasons': reasons}
        )


class SignalExpiredError(SignalError):
    """Error when signal is expired - FROZEN"""
    
    def __init__(self, signal_id: str):
        super().__init__(
            message=f"Signal {signal_id} has expired",
            code="SIGNAL_EXPIRED",
            details={'signal_id': signal_id}
        )


class SignalConflictError(SignalError):
    """Error when signals conflict - FROZEN"""
    
    def __init__(self, signal_ids: list, reason: str):
        super().__init__(
            message=f"Conflicting signals detected: {reason}",
            code="SIGNAL_CONFLICT",
            details={'signal_ids': signal_ids, 'reason': reason}
        )


# =============================================================================
# RISK EXCEPTIONS - FROZEN
# =============================================================================

class RiskError(AlphaAlgoError):
    """Base exception for risk-related errors - FROZEN"""
    pass


class RiskLimitBreachError(RiskError):
    """Error when risk limit is breached - FROZEN"""
    
    def __init__(
        self, 
        limit_type: str, 
        current_value: float, 
        limit_value: float
    ):
        super().__init__(
            message=f"Risk limit breached: {limit_type} ({current_value:.2%} > {limit_value:.2%})",
            code="RISK_LIMIT_BREACH",
            details={
                'limit_type': limit_type,
                'current_value': current_value,
                'limit_value': limit_value
            },
            recoverable=False
        )


class DrawdownLimitError(RiskError):
    """Error when drawdown limit is breached - FROZEN"""
    
    def __init__(self, current_drawdown: float, max_drawdown: float):
        super().__init__(
            message=f"Drawdown limit breached: {current_drawdown:.2%} > {max_drawdown:.2%}",
            code="DRAWDOWN_LIMIT_BREACH",
            details={
                'current_drawdown': current_drawdown,
                'max_drawdown': max_drawdown
            },
            recoverable=False
        )


class PositionLimitError(RiskError):
    """Error when position limit is reached - FROZEN"""
    
    def __init__(self, symbol: str, current_positions: int, max_positions: int):
        super().__init__(
            message=f"Position limit reached for {symbol}: {current_positions}/{max_positions}",
            code="POSITION_LIMIT_REACHED",
            details={
                'symbol': symbol,
                'current_positions': current_positions,
                'max_positions': max_positions
            }
        )


class DailyLossLimitError(RiskError):
    """Error when daily loss limit is breached - FROZEN"""
    
    def __init__(self, current_loss: float, max_loss: float):
        super().__init__(
            message=f"Daily loss limit breached: {current_loss:.2%} > {max_loss:.2%}",
            code="DAILY_LOSS_LIMIT_BREACH",
            details={
                'current_loss': current_loss,
                'max_loss': max_loss
            },
            recoverable=False
        )


class CircuitBreakerError(RiskError):
    """Error when circuit breaker is triggered - FROZEN"""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"Circuit breaker triggered: {reason}",
            code="CIRCUIT_BREAKER_TRIGGERED",
            details={'reason': reason},
            recoverable=False
        )


# =============================================================================
# EXECUTION EXCEPTIONS - FROZEN
# =============================================================================

class ExecutionError(AlphaAlgoError):
    """Base exception for execution-related errors - FROZEN"""
    pass


class OrderRejectedError(ExecutionError):
    """Error when order is rejected - FROZEN"""
    
    def __init__(self, order_id: str, reason: str):
        super().__init__(
            message=f"Order {order_id} rejected: {reason}",
            code="ORDER_REJECTED",
            details={'order_id': order_id, 'reason': reason}
        )


class OrderTimeoutError(ExecutionError):
    """Error when order times out - FROZEN"""
    
    def __init__(self, order_id: str, timeout_seconds: float):
        super().__init__(
            message=f"Order {order_id} timed out after {timeout_seconds}s",
            code="ORDER_TIMEOUT",
            details={'order_id': order_id, 'timeout_seconds': timeout_seconds}
        )


class InsufficientFundsError(ExecutionError):
    """Error when insufficient funds - FROZEN"""
    
    def __init__(self, required: float, available: float):
        super().__init__(
            message=f"Insufficient funds: required {required:.2f}, available {available:.2f}",
            code="INSUFFICIENT_FUNDS",
            details={'required': required, 'available': available}
        )


class BrokerConnectionError(ExecutionError):
    """Error connecting to broker - FROZEN"""
    
    def __init__(self, broker: str, reason: str):
        super().__init__(
            message=f"Failed to connect to broker {broker}: {reason}",
            code="BROKER_CONNECTION_ERROR",
            details={'broker': broker, 'reason': reason}
        )


class SlippageError(ExecutionError):
    """Error when slippage exceeds limit - FROZEN"""
    
    def __init__(self, expected_price: float, actual_price: float, max_slippage: float):
        slippage = abs(actual_price - expected_price) / expected_price
        super().__init__(
            message=f"Slippage exceeded limit: {slippage:.2%} > {max_slippage:.2%}",
            code="SLIPPAGE_EXCEEDED",
            details={
                'expected_price': expected_price,
                'actual_price': actual_price,
                'slippage': slippage,
                'max_slippage': max_slippage
            }
        )


# =============================================================================
# VALIDATION EXCEPTIONS - FROZEN
# =============================================================================

class ValidationError(AlphaAlgoError):
    """Base exception for validation errors - FROZEN"""
    pass


class ConfigValidationError(ValidationError):
    """Error validating configuration - FROZEN"""
    
    def __init__(self, config_key: str, reason: str):
        super().__init__(
            message=f"Invalid configuration for '{config_key}': {reason}",
            code="CONFIG_VALIDATION_ERROR",
            details={'config_key': config_key, 'reason': reason}
        )


class ParameterValidationError(ValidationError):
    """Error validating parameters - FROZEN"""
    
    def __init__(self, parameter: str, value: Any, expected: str):
        super().__init__(
            message=f"Invalid parameter '{parameter}': got {value}, expected {expected}",
            code="PARAMETER_VALIDATION_ERROR",
            details={'parameter': parameter, 'value': str(value), 'expected': expected}
        )


class SchemaValidationError(ValidationError):
    """Error validating against schema - FROZEN"""
    
    def __init__(self, schema_name: str, errors: list):
        super().__init__(
            message=f"Schema validation failed for '{schema_name}': {len(errors)} errors",
            code="SCHEMA_VALIDATION_ERROR",
            details={'schema_name': schema_name, 'errors': errors}
        )


# =============================================================================
# CONFIGURATION EXCEPTIONS - FROZEN
# =============================================================================

class ConfigurationError(AlphaAlgoError):
    """Base exception for configuration errors - FROZEN"""
    pass


class ConfigNotFoundError(ConfigurationError):
    """Error when configuration is not found - FROZEN"""
    
    def __init__(self, config_path: str):
        super().__init__(
            message=f"Configuration not found: {config_path}",
            code="CONFIG_NOT_FOUND",
            details={'config_path': config_path}
        )


class ConfigParseError(ConfigurationError):
    """Error parsing configuration - FROZEN"""
    
    def __init__(self, config_path: str, reason: str):
        super().__init__(
            message=f"Failed to parse configuration {config_path}: {reason}",
            code="CONFIG_PARSE_ERROR",
            details={'config_path': config_path, 'reason': reason}
        )


class MissingConfigError(ConfigurationError):
    """Error when required configuration is missing - FROZEN"""
    
    def __init__(self, required_keys: list):
        super().__init__(
            message=f"Missing required configuration: {', '.join(required_keys)}",
            code="MISSING_CONFIG",
            details={'required_keys': required_keys}
        )


# =============================================================================
# SYSTEM EXCEPTIONS - FROZEN
# =============================================================================

class SystemError(AlphaAlgoError):
    """Base exception for system errors - FROZEN"""
    pass


class ComponentNotFoundError(SystemError):
    """Error when component is not found - FROZEN"""
    
    def __init__(self, component_name: str):
        super().__init__(
            message=f"Component not found: {component_name}",
            code="COMPONENT_NOT_FOUND",
            details={'component_name': component_name}
        )


class ComponentInitializationError(SystemError):
    """Error initializing component - FROZEN"""
    
    def __init__(self, component_name: str, reason: str):
        super().__init__(
            message=f"Failed to initialize component {component_name}: {reason}",
            code="COMPONENT_INIT_ERROR",
            details={'component_name': component_name, 'reason': reason}
        )


class DependencyError(SystemError):
    """Error with dependency - FROZEN"""
    
    def __init__(self, dependency: str, reason: str):
        super().__init__(
            message=f"Dependency error for {dependency}: {reason}",
            code="DEPENDENCY_ERROR",
            details={'dependency': dependency, 'reason': reason}
        )


class ShutdownError(SystemError):
    """Error during shutdown - FROZEN"""
    
    def __init__(self, component: str, reason: str):
        super().__init__(
            message=f"Error shutting down {component}: {reason}",
            code="SHUTDOWN_ERROR",
            details={'component': component, 'reason': reason}
        )


# =============================================================================
# EVOLUTION EXCEPTIONS - FROZEN
# =============================================================================

class EvolutionError(AlphaAlgoError):
    """Base exception for evolution errors - FROZEN"""
    pass


class ImprovementRejectedError(EvolutionError):
    """Error when improvement is rejected - FROZEN"""
    
    def __init__(self, improvement_id: str, reason: str):
        super().__init__(
            message=f"Improvement {improvement_id} rejected: {reason}",
            code="IMPROVEMENT_REJECTED",
            details={'improvement_id': improvement_id, 'reason': reason}
        )


class EvolutionConstraintError(EvolutionError):
    """Error when evolution violates constraints - FROZEN"""
    
    def __init__(self, constraint: str, violation: str):
        super().__init__(
            message=f"Evolution constraint violated: {constraint} - {violation}",
            code="EVOLUTION_CONSTRAINT_VIOLATION",
            details={'constraint': constraint, 'violation': violation},
            recoverable=False
        )


# =============================================================================
# HUMAN LAYER EXCEPTIONS - FROZEN
# =============================================================================

class HumanLayerError(AlphaAlgoError):
    """Base exception for human layer errors - FROZEN"""
    pass


class ApprovalTimeoutError(HumanLayerError):
    """Error when approval times out - FROZEN"""
    
    def __init__(self, request_id: str, timeout_seconds: float):
        super().__init__(
            message=f"Approval request {request_id} timed out after {timeout_seconds}s",
            code="APPROVAL_TIMEOUT",
            details={'request_id': request_id, 'timeout_seconds': timeout_seconds}
        )


class ApprovalDeniedError(HumanLayerError):
    """Error when approval is denied - FROZEN"""
    
    def __init__(self, request_id: str, reason: str):
        super().__init__(
            message=f"Approval request {request_id} denied: {reason}",
            code="APPROVAL_DENIED",
            details={'request_id': request_id, 'reason': reason}
        )


class ManualOverrideError(HumanLayerError):
    """Error during manual override - FROZEN"""
    
    def __init__(self, action: str, reason: str):
        super().__init__(
            message=f"Manual override failed for {action}: {reason}",
            code="MANUAL_OVERRIDE_ERROR",
            details={'action': action, 'reason': reason}
        )

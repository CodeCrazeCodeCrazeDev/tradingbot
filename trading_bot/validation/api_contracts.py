"""
API Contract Validation Module
Ensures that all components adhere to their expected interfaces
"""

import inspect
import importlib
import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
from functools import wraps
from datetime import datetime
import traceback

from trading_bot.schemas.validation import ValidationResult

logger = logging.getLogger(__name__)


class ContractViolationError(Exception):
    """Exception raised when an API contract is violated"""
    pass


class APIContract:
    """Defines an API contract for a component"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.methods: Dict[str, Dict[str, Any]] = {}
        self.required_methods: Set[str] = set()
        self.optional_methods: Set[str] = set()
    
    def add_method(self, 
                  name: str, 
                  params: List[Dict[str, Any]], 
                  return_type: Any,
                  is_async: bool = False,
                  is_required: bool = True,
                  description: str = ""):
        """Add a method to the contract"""
        self.methods[name] = {
            'params': params,
            'return_type': return_type,
            'is_async': is_async,
            'description': description
        }
        
        if is_required:
            self.required_methods.add(name)
        else:
            self.optional_methods.add(name)
    
    def validate_implementation(self, implementation: Any) -> ValidationResult:
        """Validate that an implementation adheres to this contract"""
        errors = []
        warnings = []
        
        # Check required methods
        for method_name in self.required_methods:
            if not hasattr(implementation, method_name):
                errors.append(f"Required method '{method_name}' is missing")
                continue
            
            method = getattr(implementation, method_name)
            if not callable(method):
                errors.append(f"'{method_name}' is not callable")
                continue
            
            # Validate method signature
            self._validate_method_signature(method_name, method, errors, warnings)
        
        # Check optional methods
        for method_name in self.optional_methods:
            if hasattr(implementation, method_name):
                method = getattr(implementation, method_name)
                if callable(method):
                    self._validate_method_signature(method_name, method, errors, warnings)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={
                'contract_name': self.name,
                'implementation_type': type(implementation).__name__
            }
        )
    
    def _validate_method_signature(self, 
                                 method_name: str, 
                                 method: Callable, 
                                 errors: List[str], 
                                 warnings: List[str]):
        """Validate a method's signature against the contract"""
        contract_method = self.methods[method_name]
        
        # Check if async status matches
        is_async = asyncio.iscoroutinefunction(method)
        if is_async != contract_method['is_async']:
            if contract_method['is_async']:
                errors.append(f"Method '{method_name}' should be async but isn't")
            else:
                errors.append(f"Method '{method_name}' shouldn't be async but is")
        
        # Check parameters
        sig = inspect.signature(method)
        contract_params = contract_method['params']
        
        # Skip self/cls parameter for instance/class methods
        param_names = list(sig.parameters.keys())
        if param_names and param_names[0] in ('self', 'cls'):
            param_names = param_names[1:]
        
        # Check parameter count
        if len(param_names) != len(contract_params):
            errors.append(
                f"Method '{method_name}' has {len(param_names)} parameters, "
                f"but contract specifies {len(contract_params)}"
            )
        
        # Check parameter names and types
        for i, param_name in enumerate(param_names):
            if i >= len(contract_params):
                break
                
            contract_param = contract_params[i]
            if param_name != contract_param['name']:
                warnings.append(
                    f"Parameter name mismatch in '{method_name}': "
                    f"'{param_name}' vs '{contract_param['name']}'"
                )
            
            # Type checking is best-effort since Python's type hints are optional
            param = sig.parameters[param_name]
            if param.annotation != inspect.Parameter.empty:
                if 'type' in contract_param and not self._is_compatible_type(
                    param.annotation, contract_param['type']
                ):
                    warnings.append(
                        f"Parameter type mismatch in '{method_name}' for '{param_name}': "
                        f"{param.annotation} vs {contract_param['type']}"
                    )
        
        # Check return type
        if sig.return_annotation != inspect.Parameter.empty:
            if not self._is_compatible_type(sig.return_annotation, contract_method['return_type']):
                warnings.append(
                    f"Return type mismatch in '{method_name}': "
                    f"{sig.return_annotation} vs {contract_method['return_type']}"
                )
    
    def _is_compatible_type(self, actual: Any, expected: Any) -> bool:
        """Check if types are compatible (best-effort)"""
        # This is a simplified check - in a real system, you'd want more sophisticated type checking
        if actual == expected:
            return True
        
        # Handle Union types
        if hasattr(expected, '__origin__') and expected.__origin__ is Union:
            return any(self._is_compatible_type(actual, arg) for arg in expected.__args__)
        
        # Handle Optional types (Union[T, None])
        if hasattr(expected, '__origin__') and expected.__origin__ is Union and type(None) in expected.__args__:
            return self._is_compatible_type(actual, next(arg for arg in expected.__args__ if arg is not type(None)))
        
        return False


def contract_validator(contract: APIContract):
    """Decorator to validate a class against an API contract"""
    def decorator(cls):
        original_init = cls.__init__
        
        @wraps(original_init)
        def init_wrapper(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Validate after initialization
            result = contract.validate_implementation(self)
            if not result.valid:
                for error in result.errors:
                    logger.error(f"Contract violation in {cls.__name__}: {error}")
                
                for warning in result.warnings:
                    logger.warning(f"Contract warning in {cls.__name__}: {warning}")
                
                if result.errors:
                    raise ContractViolationError(
                        f"{cls.__name__} violates the {contract.name} contract: "
                        f"{'; '.join(result.errors)}"
                    )
        
        cls.__init__ = init_wrapper
        cls.__api_contract__ = contract
        return cls
    
    return decorator


def async_method_validator(method=None, *, expected_async=True):
    """Decorator to validate async/sync method calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if expected_async and not asyncio.iscoroutinefunction(func):
                logger.error(f"Method {func.__name__} should be async but isn't")
                raise ContractViolationError(f"Method {func.__name__} should be async but isn't")
            elif not expected_async and asyncio.iscoroutinefunction(func):
                logger.error(f"Method {func.__name__} shouldn't be async but is")
                raise ContractViolationError(f"Method {func.__name__} shouldn't be async but is")
            return func(*args, **kwargs)
        return wrapper
    
    if method is None:
        return decorator
    return decorator(method)


def method_timing(method=None, *, threshold_ms=100):
    """Decorator to measure method execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                execution_time = (time.time() - start_time) * 1000  # ms
                if execution_time > threshold_ms:
                    logger.warning(
                        f"Method {func.__name__} took {execution_time:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = (time.time() - start_time) * 1000  # ms
                if execution_time > threshold_ms:
                    logger.warning(
                        f"Method {func.__name__} took {execution_time:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    if method is None:
        return decorator
    return decorator(method)


# Define API contracts for key components
opportunity_scanner_contract = APIContract(
    name="OpportunityScanner",
    description="Interface for opportunity scanning components"
)

opportunity_scanner_contract.add_method(
    name="initialize",
    params=[
        {'name': 'market_stream', 'type': Any},
        {'name': 'data_processor', 'type': Any},
        {'name': 'microstructure', 'type': Any},
        {'name': 'order_flow', 'type': Any}
    ],
    return_type=None,
    is_async=True,
    description="Initialize scanner with data pipeline components"
)

opportunity_scanner_contract.add_method(
    name="scan_opportunities",
    params=[
        {'name': 'symbol', 'type': str},
        {'name': 'market_data', 'type': Dict}
    ],
    return_type=List,
    is_async=True,
    description="Scan for opportunities based on market data"
)

opportunity_scanner_contract.add_method(
    name="get_opportunity_metrics",
    params=[],
    return_type=Dict,
    is_async=False,
    description="Get opportunity scanning metrics"
)

# Define API contract for execution engine
execution_engine_contract = APIContract(
    name="ExecutionEngine",
    description="Interface for order execution components"
)

execution_engine_contract.add_method(
    name="execute",
    params=[
        {'name': 'decision', 'type': Any}
    ],
    return_type=Any,
    is_async=True,
    description="Execute a trading decision"
)

execution_engine_contract.add_method(
    name="execute_order",
    params=[
        {'name': 'order', 'type': Dict}
    ],
    return_type=Dict,
    is_async=True,
    description="Execute a specific order"
)

# Define API contract for master orchestrator
orchestrator_contract = APIContract(
    name="MasterOrchestrator",
    description="Interface for trading orchestration components"
)

orchestrator_contract.add_method(
    name="orchestrate_trading",
    params=[
        {'name': 'market_data', 'type': Dict}
    ],
    return_type=List,
    is_async=True,
    description="Orchestrate trading based on market data"
)

orchestrator_contract.add_method(
    name="execute_decisions",
    params=[],
    return_type=None,
    is_async=True,
    description="Execute queued trading decisions"
)

# Define API contract for risk manager
risk_manager_contract = APIContract(
    name="RiskManager",
    description="Interface for risk management components"
)

risk_manager_contract.add_method(
    name="assess_portfolio_risk",
    params=[
        {'name': 'positions', 'type': Dict},
        {'name': 'market_data', 'type': Dict}
    ],
    return_type=Any,
    is_async=True,
    description="Assess portfolio risk based on positions and market data"
)

risk_manager_contract.add_method(
    name="validate_trade",
    params=[
        {'name': 'trade', 'type': Dict}
    ],
    return_type=tuple,
    is_async=True,
    description="Validate if a trade fits within risk limits"
)



# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


def validate_module_contracts(module_path: str) -> Dict[str, List[Any]]:
    """Validate all API contracts for a module."""
    results = {}
    
    try:
        module = importlib.import_module(module_path)
        
        # Find all contracts
        contracts = [
            (name, obj) for name, obj in globals().items()
            if isinstance(obj, APIContract)
        ]
        
        # Find all classes in the module
        classes = inspect.getmembers(module, inspect.isclass)
        
        # Validate each class against each contract
        for contract_name, contract in contracts:
            contract_results = []
            
            for class_name, cls in classes:
                # Skip if class is imported from another module
                if cls.__module__ != module.__name__:
                    continue
                
                result = contract.validate_implementation(cls)
                if not result.valid or result.warnings:
                    contract_results.append(result)
            
            results[contract_name] = contract_results
        
        return results
        
    except ImportError:
        logger.error(f"Could not import module {module_path}")
        return {}
    except Exception as e:
        logger.error(f"Error validating API contracts: {e}")
        return {}

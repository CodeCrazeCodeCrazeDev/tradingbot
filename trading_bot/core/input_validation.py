"""
Input Validation Decorators
Provides decorators for validating function inputs
"""

import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime
import inspect

from trading_bot.constants import (
    MIN_PRICE, MAX_PRICE, MIN_POSITION_SIZE, MAX_POSITION_SIZE,
    MIN_CONFIDENCE, MAX_STRING_LENGTH, MAX_ARRAY_SIZE
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Input validation error"""
    pass


def validate_positive(value: Union[int, float], name: str = "value") -> None:
    """Validate value is positive"""
    if value <= 0:
        raise ValidationError(f"{name} must be positive, got {value}")


def validate_non_negative(value: Union[int, float], name: str = "value") -> None:
    """Validate value is non-negative"""
    if value < 0:
        raise ValidationError(f"{name} must be non-negative, got {value}")


def validate_range(
    value: Union[int, float],
    min_val: Union[int, float],
    max_val: Union[int, float],
    name: str = "value"
) -> None:
    """Validate value is within range"""
    if not (min_val <= value <= max_val):
        raise ValidationError(
            f"{name} must be between {min_val} and {max_val}, got {value}"
        )


def validate_not_none(value: Any, name: str = "value") -> None:
    """Validate value is not None"""
    if value is None:
        raise ValidationError(f"{name} cannot be None")


def validate_string(
    value: str,
    name: str = "value",
    min_length: int = 0,
    max_length: int = MAX_STRING_LENGTH,
    pattern: Optional[str] = None
) -> None:
    """Validate string value"""
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be string, got {type(value).__name__}")
    
    if len(value) < min_length:
        raise ValidationError(f"{name} length must be >= {min_length}")
    
    if len(value) > max_length:
        raise ValidationError(f"{name} length must be <= {max_length}")
    
    if pattern:
        import re
        if not re.match(pattern, value):
            raise ValidationError(f"{name} does not match pattern {pattern}")


def validate_symbol(symbol: str) -> None:
    """Validate trading symbol"""
    validate_string(symbol, "symbol", min_length=3, max_length=20)
    if not symbol.replace('/', '').replace('-', '').isalnum():
        raise ValidationError(f"Invalid symbol format: {symbol}")


def validate_price(price: float, name: str = "price") -> None:
    """Validate price value"""
    validate_positive(price, name)
    validate_range(price, MIN_PRICE, MAX_PRICE, name)


def validate_quantity(quantity: float, name: str = "quantity") -> None:
    """Validate quantity value"""
    validate_positive(quantity, name)
    validate_range(quantity, MIN_POSITION_SIZE, MAX_POSITION_SIZE, name)


def validate_confidence(confidence: float) -> None:
    """Validate confidence score"""
    validate_range(confidence, 0.0, 1.0, "confidence")


def validate_percentage(value: float, name: str = "percentage") -> None:
    """Validate percentage value (0-1)"""
    validate_range(value, 0.0, 1.0, name)


def validate_list(
    value: List,
    name: str = "list",
    min_length: int = 0,
    max_length: int = MAX_ARRAY_SIZE,
    item_type: Optional[type] = None
) -> None:
    """Validate list value"""
    if not isinstance(value, list):
        raise ValidationError(f"{name} must be list, got {type(value).__name__}")
    
    if len(value) < min_length:
        raise ValidationError(f"{name} length must be >= {min_length}")
    
    if len(value) > max_length:
        raise ValidationError(f"{name} length must be <= {max_length}")
    
    if item_type:
        for i, item in enumerate(value):
            if not isinstance(item, item_type):
                raise ValidationError(
                    f"{name}[{i}] must be {item_type.__name__}, got {type(item).__name__}"
                )


def validate_dict(value: Dict, name: str = "dict", required_keys: Optional[List[str]] = None) -> None:
    """Validate dictionary value"""
    if not isinstance(value, dict):
        raise ValidationError(f"{name} must be dict, got {type(value).__name__}")
    
    if required_keys:
        missing = set(required_keys) - set(value.keys())
        if missing:
            raise ValidationError(f"{name} missing required keys: {missing}")


def validate_datetime(value: datetime, name: str = "datetime") -> None:
    """Validate datetime value"""
    if not isinstance(value, datetime):
        raise ValidationError(f"{name} must be datetime, got {type(value).__name__}")


def validate_enum(value: Any, allowed_values: List[Any], name: str = "value") -> None:
    """Validate value is in allowed set"""
    if value not in allowed_values:
        raise ValidationError(f"{name} must be one of {allowed_values}, got {value}")


# Decorators

def validate_inputs(**validators: Dict[str, Callable]) -> Callable:
    """
    Decorator to validate function inputs
    
    Usage:
        @validate_inputs(
            symbol=validate_symbol,
            price=validate_price,
            quantity=validate_quantity
        )
        def place_order(symbol: str, price: float, quantity: float):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each specified parameter
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    try:
                        validator(value)
                    except ValidationError as e:
                        logger.error(f"Validation error in {func.__name__}: {e}")
                        raise
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_inputs_async(**validators: Dict[str, Callable]) -> Callable:
    """
    Async version of validate_inputs decorator
    
    Usage:
        @validate_inputs_async(
            symbol=validate_symbol,
            price=validate_price
        )
        async def place_order_async(symbol: str, price: float):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each specified parameter
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    try:
                        validator(value)
                    except ValidationError as e:
                        logger.error(f"Validation error in {func.__name__}: {e}")
                        raise
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_not_none(*param_names: str) -> Callable:
    """
    Decorator to ensure specified parameters are not None
    
    Usage:
        @require_not_none('symbol', 'price')
        def place_order(symbol: str, price: float, quantity: float = None):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            for param_name in param_names:
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if value is None:
                        raise ValidationError(f"{param_name} cannot be None in {func.__name__}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_trading_params(func: Callable) -> Callable:
    """
    Convenience decorator for common trading parameters
    
    Validates: symbol, price, quantity, confidence (if present)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        params = bound_args.arguments
        
        if 'symbol' in params:
            validate_symbol(params['symbol'])
        
        if 'price' in params and params['price'] is not None:
            validate_price(params['price'])
        
        if 'quantity' in params and params['quantity'] is not None:
            validate_quantity(params['quantity'])
        
        if 'confidence' in params and params['confidence'] is not None:
            validate_confidence(params['confidence'])
        
        return func(*args, **kwargs)
    return wrapper


def validate_trading_params_async(func: Callable) -> Callable:
    """Async version of validate_trading_params"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        params = bound_args.arguments
        
        if 'symbol' in params:
            validate_symbol(params['symbol'])
        
        if 'price' in params and params['price'] is not None:
            validate_price(params['price'])
        
        if 'quantity' in params and params['quantity'] is not None:
            validate_quantity(params['quantity'])
        
        if 'confidence' in params and params['confidence'] is not None:
            validate_confidence(params['confidence'])
        
        return await func(*args, **kwargs)
    return wrapper


# Example usage:
"""
from trading_bot.core.input_validation import (
    validate_inputs,
    validate_trading_params,
    require_not_none,
    validate_symbol,
    validate_price,
    validate_quantity
)

@validate_trading_params
def place_order(symbol: str, price: float, quantity: float):
    # All parameters are validated automatically
    pass

@validate_inputs(
    symbol=validate_symbol,
    price=validate_price,
    stop_loss=lambda x: validate_range(x, 0, 10000, 'stop_loss')
)
def place_order_with_sl(symbol: str, price: float, stop_loss: float):
    pass

@require_not_none('symbol', 'broker')
def connect_broker(symbol: str, broker: Any):
    pass
"""

"""
Input Validation Module
Provides comprehensive input validation for trading operations.

This module addresses the HIGH priority issue of missing input validation.
"""

import re
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import inspect
from dataclasses import field

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"{field}: {message}")


class ValidationType(Enum):
    """Types of validation"""
    REQUIRED = "required"
    TYPE = "type"
    RANGE = "range"
    PATTERN = "pattern"
    LENGTH = "length"
    ENUM = "enum"
    CUSTOM = "custom"


@dataclass
class ValidationRule:
    """Validation rule definition"""
    field: str
    validation_type: ValidationType
    params: Dict[str, Any]
    message: Optional[str] = None
    
    def validate(self, value: Any) -> bool:
        """Execute validation"""
        if self.validation_type == ValidationType.REQUIRED:
            return value is not None and value != ""
        
        elif self.validation_type == ValidationType.TYPE:
            expected_type = self.params.get('type')
            return isinstance(value, expected_type)
        
        elif self.validation_type == ValidationType.RANGE:
            min_val = self.params.get('min')
            max_val = self.params.get('max')
            if min_val is not None and value < min_val:
                return False
            if max_val is not None and value > max_val:
                return False
            return True
        
        elif self.validation_type == ValidationType.PATTERN:
            pattern = self.params.get('pattern')
            return bool(re.match(pattern, str(value)))
        
        elif self.validation_type == ValidationType.LENGTH:
            min_len = self.params.get('min', 0)
            max_len = self.params.get('max', float('inf'))
            return min_len <= len(value) <= max_len
        
        elif self.validation_type == ValidationType.ENUM:
            allowed = self.params.get('values', [])
            return value in allowed
        
        elif self.validation_type == ValidationType.CUSTOM:
            validator = self.params.get('validator')
            return validator(value) if validator else True
        
        return True


class InputValidator:
    """
    Comprehensive input validator for trading operations.
    """
    
    # Common trading symbols pattern
    SYMBOL_PATTERN = r'^[A-Z]{6}$|^[A-Z]{3}/[A-Z]{3}$|^[A-Z]{2,10}(USD|EUR|GBP|JPY|BTC|ETH)?$'
    
    # Valid order types
    VALID_ORDER_TYPES = ['market', 'limit', 'stop', 'stop_limit']
    
    # Valid order sides
    VALID_ORDER_SIDES = ['buy', 'sell', 'long', 'short']
    
    # Valid timeframes
    VALID_TIMEFRAMES = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN1',
                       '1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
    
    def __init__(self):
        self.errors: List[ValidationError] = []
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate trading symbol"""
        if not symbol:
            self._add_error('symbol', 'Symbol is required')
            return False
        
        if not isinstance(symbol, str):
            self._add_error('symbol', 'Symbol must be a string', symbol)
            return False
        
        symbol = symbol.upper().strip()
        
        if not re.match(self.SYMBOL_PATTERN, symbol):
            self._add_error('symbol', f'Invalid symbol format: {symbol}', symbol)
            return False
        
        return True
    
    def validate_quantity(self, quantity: Union[int, float], 
                         min_qty: float = 0.0001,
                         max_qty: float = 1000000) -> bool:
        """Validate order quantity"""
        if quantity is None:
            self._add_error('quantity', 'Quantity is required')
            return False
        
        if not isinstance(quantity, (int, float)):
            self._add_error('quantity', 'Quantity must be a number', quantity)
            return False
        
        if quantity <= 0:
            self._add_error('quantity', 'Quantity must be positive', quantity)
            return False
        
        if quantity < min_qty:
            self._add_error('quantity', f'Quantity below minimum ({min_qty})', quantity)
            return False
        
        if quantity > max_qty:
            self._add_error('quantity', f'Quantity exceeds maximum ({max_qty})', quantity)
            return False
        
        return True
    
    def validate_price(self, price: Union[int, float],
                      min_price: float = 0.0,
                      max_price: float = float('inf')) -> bool:
        """Validate price"""
        if price is None:
            self._add_error('price', 'Price is required')
            return False
        
        if not isinstance(price, (int, float)):
            self._add_error('price', 'Price must be a number', price)
            return False
        
        if price < min_price:
            self._add_error('price', f'Price below minimum ({min_price})', price)
            return False
        
        if price > max_price:
            self._add_error('price', f'Price exceeds maximum ({max_price})', price)
            return False
        
        return True
    
    def validate_order_type(self, order_type: str) -> bool:
        """Validate order type"""
        if not order_type:
            self._add_error('order_type', 'Order type is required')
            return False
        
        if order_type.lower() not in self.VALID_ORDER_TYPES:
            self._add_error('order_type', 
                          f'Invalid order type. Must be one of: {self.VALID_ORDER_TYPES}',
                          order_type)
            return False
        
        return True
    
    def validate_order_side(self, side: str) -> bool:
        """Validate order side"""
        if not side:
            self._add_error('side', 'Order side is required')
            return False
        
        if side.lower() not in self.VALID_ORDER_SIDES:
            self._add_error('side',
                          f'Invalid order side. Must be one of: {self.VALID_ORDER_SIDES}',
                          side)
            return False
        
        return True
    
    def validate_timeframe(self, timeframe: str) -> bool:
        """Validate timeframe"""
        if not timeframe:
            self._add_error('timeframe', 'Timeframe is required')
            return False
        
        if timeframe not in self.VALID_TIMEFRAMES:
            self._add_error('timeframe',
                          f'Invalid timeframe. Must be one of: {self.VALID_TIMEFRAMES}',
                          timeframe)
            return False
        
        return True
    
    def validate_percentage(self, value: Union[int, float], 
                           field_name: str = 'percentage') -> bool:
        """Validate percentage value (0-1 or 0-100)"""
        if value is None:
            self._add_error(field_name, 'Value is required')
            return False
        
        if not isinstance(value, (int, float)):
            self._add_error(field_name, 'Value must be a number', value)
            return False
        
        # Accept both 0-1 and 0-100 ranges
        if not (0 <= value <= 1 or 0 <= value <= 100):
            self._add_error(field_name, 'Percentage must be between 0-1 or 0-100', value)
            return False
        
        return True
    
    def validate_capital(self, capital: Union[int, float],
                        min_capital: float = 100,
                        max_capital: float = 100000000) -> bool:
        """Validate capital amount"""
        if capital is None:
            self._add_error('capital', 'Capital is required')
            return False
        
        if not isinstance(capital, (int, float)):
            self._add_error('capital', 'Capital must be a number', capital)
            return False
        
        if capital < min_capital:
            self._add_error('capital', f'Capital below minimum (${min_capital})', capital)
            return False
        
        if capital > max_capital:
            self._add_error('capital', f'Capital exceeds maximum (${max_capital})', capital)
            return False
        
        return True
    
    def validate_order(self, order: Dict[str, Any]) -> bool:
        """Validate complete order"""
        self.clear_errors()
        
        valid = True
        
        # Required fields
        if 'symbol' in order:
            valid &= self.validate_symbol(order['symbol'])
        else:
            self._add_error('symbol', 'Symbol is required')
            valid = False
        
        if 'quantity' in order:
            valid &= self.validate_quantity(order['quantity'])
        else:
            self._add_error('quantity', 'Quantity is required')
            valid = False
        
        if 'side' in order:
            valid &= self.validate_order_side(order['side'])
        else:
            self._add_error('side', 'Order side is required')
            valid = False
        
        # Optional fields
        if 'order_type' in order:
            valid &= self.validate_order_type(order['order_type'])
        
        if 'price' in order:
            valid &= self.validate_price(order['price'])
        
        if 'stop_price' in order:
            valid &= self.validate_price(order['stop_price'])
        
        return valid
    
    def validate_risk_params(self, params: Dict[str, Any]) -> bool:
        """Validate risk parameters"""
        self.clear_errors()
        
        valid = True
        
        if 'max_position_size' in params:
            valid &= self.validate_percentage(params['max_position_size'], 'max_position_size')
        
        if 'max_portfolio_risk' in params:
            valid &= self.validate_percentage(params['max_portfolio_risk'], 'max_portfolio_risk')
        
        if 'max_daily_loss' in params:
            valid &= self.validate_percentage(params['max_daily_loss'], 'max_daily_loss')
        
        if 'max_drawdown' in params:
            valid &= self.validate_percentage(params['max_drawdown'], 'max_drawdown')
        
        if 'max_positions' in params:
            max_pos = params['max_positions']
            if not isinstance(max_pos, int) or max_pos < 1 or max_pos > 100:
                self._add_error('max_positions', 'Must be integer between 1-100', max_pos)
                valid = False
        
        if 'stop_loss_pct' in params:
            valid &= self.validate_percentage(params['stop_loss_pct'], 'stop_loss_pct')
        
        if 'take_profit_pct' in params:
            valid &= self.validate_percentage(params['take_profit_pct'], 'take_profit_pct')
        
        return valid
    
    def _add_error(self, field: str, message: str, value: Any = None):
        """Add validation error"""
        error = ValidationError(field, message, value)
        self.errors.append(error)
        logger.warning(f"Validation error: {error}")
    
    def clear_errors(self):
        """Clear all errors"""
        self.errors.clear()
    
    def get_errors(self) -> List[ValidationError]:
        """Get all validation errors"""
        return self.errors.copy()
    
    def get_error_messages(self) -> List[str]:
        """Get error messages as strings"""
        return [str(e) for e in self.errors]


# Validation decorators
def validate_inputs(**validators):
    """
    Decorator to validate function inputs.
    
    Usage:
        @validate_inputs(
            symbol=lambda x: InputValidator().validate_symbol(x),
            quantity=lambda x: InputValidator().validate_quantity(x)
        )
        def place_order(symbol: str, quantity: float):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # Validate each parameter
            errors = []
            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not validator(value):
                        errors.append(f"Invalid {param_name}: {value}")
            
            if errors:
                raise ValidationError('input', '; '.join(errors))
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_order_params(func: Callable) -> Callable:
    """Decorator to validate order parameters"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        validator = InputValidator()
        
        # Extract order-related parameters
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        
        params = bound.arguments
        
        # Validate common order parameters
        if 'symbol' in params:
            validator.validate_symbol(params['symbol'])
        
        if 'quantity' in params:
            validator.validate_quantity(params['quantity'])
        
        if 'side' in params:
            validator.validate_order_side(params['side'])
        
        if 'order_type' in params:
            validator.validate_order_type(params['order_type'])
        
        if 'price' in params and params['price'] is not None:
            validator.validate_price(params['price'])
        
        if validator.errors:
            raise ValidationError('order', '; '.join(validator.get_error_messages()))
        
        return func(*args, **kwargs)
    
    return wrapper


def validate_risk_params_decorator(func: Callable) -> Callable:
    """Decorator to validate risk parameters"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        validator = InputValidator()
        
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        
        params = bound.arguments
        
        # Look for risk-related parameters
        risk_params = {}
        for key in ['max_position_size', 'max_portfolio_risk', 'max_daily_loss',
                   'max_drawdown', 'max_positions', 'stop_loss_pct', 'take_profit_pct']:
            if key in params:
                risk_params[key] = params[key]
        
        if risk_params:
            validator.validate_risk_params(risk_params)
        
        if validator.errors:
            raise ValidationError('risk_params', '; '.join(validator.get_error_messages()))
        
        return func(*args, **kwargs)
    
    return wrapper


# Sanitization functions
def sanitize_symbol(symbol: str) -> str:
    """Sanitize and normalize trading symbol"""
    if not symbol:
        return ""
    
    # Remove whitespace and convert to uppercase
    symbol = symbol.strip().upper()
    
    # Remove common separators
    symbol = symbol.replace('/', '').replace('-', '').replace('_', '')
    
    # Remove any non-alphanumeric characters
    symbol = re.sub(r'[^A-Z0-9]', '', symbol)
    
    return symbol


def sanitize_quantity(quantity: Any) -> float:
    """Sanitize quantity to float"""
    if quantity is None:
        return 0.0
    
    if isinstance(quantity, str):
        try:
            # Remove commas and whitespace
            quantity = quantity.replace(',', '').strip()

            return float(quantity)
        except (ValueError, TypeError):
            return 0.0


def sanitize_price(price: Any) -> float:
    """Sanitize price to float"""
    if price is None:
        return 0.0
    
    if isinstance(price, str):
        try:
            # Remove currency symbols and commas
            price = re.sub(r'[$€£¥,]', '', price).strip()

            return float(price)
        except (ValueError, TypeError):
            return 0.0


# Global validator instance
_validator: Optional[InputValidator] = None


def get_validator() -> InputValidator:
    """Get global validator instance"""
    global _validator
    if _validator is None:
        _validator = InputValidator()
    return _validator


def validate(value: Any, rules: List[ValidationRule]) -> bool:
    """
    Validate a value against multiple rules.
    
    Args:
        value: Value to validate
        rules: List of validation rules
        
    Returns:
        True if all rules pass
    """
    validator = get_validator()
    validator.clear_errors()
    
    for rule in rules:
        if not rule.validate(value):
            message = rule.message or f"Validation failed for {rule.field}"
            validator._add_error(rule.field, message, value)
    
    return len(validator.errors) == 0

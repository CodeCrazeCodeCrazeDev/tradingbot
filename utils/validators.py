"""
Data validation utilities
"""

import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


def validate_ohlcv(bar: Dict) -> tuple:
    """
    Validate OHLCV bar data.
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = ['open', 'high', 'low', 'close', 'volume']
    
    # Check required fields
    for field in required_fields:
        if field not in bar:
            return False, f"Missing field: {field}"
    
    o, h, l, c, v = bar['open'], bar['high'], bar['low'], bar['close'], bar['volume']
    
    # Check for NaN or None
    if any(x is None or (isinstance(x, float) and np.isnan(x)) for x in [o, h, l, c, v]):
        return False, "Contains NaN or None values"
    
    # Check high >= low
    if h < l:
        return False, f"High ({h}) < Low ({l})"
    
    # Check high >= open, close
    if h < o or h < c:
        return False, f"High ({h}) < Open ({o}) or Close ({c})"
    
    # Check low <= open, close
    if l > o or l > c:
        return False, f"Low ({l}) > Open ({o}) or Close ({c})"
    
    # Check volume >= 0
    if v < 0:
        return False, f"Negative volume: {v}"
    
    # Check for extreme values
    if any(abs(x) > 1e10 for x in [o, h, l, c]):
        return False, "Extreme price values detected"
    
    return True, ""


def validate_price(price: float, symbol: str = "") -> tuple:
    """
    Validate price value.
    
    Returns:
        (is_valid, error_message)
    """
    if price is None:
        return False, "Price is None"
    
    if isinstance(price, float) and np.isnan(price):
        return False, "Price is NaN"
    
    if price <= 0:
        return False, f"Non-positive price: {price}"
    
    if abs(price) > 1e10:
        return False, f"Extreme price value: {price}"
    
    return True, ""


def validate_quantity(quantity: float) -> tuple:
    """
    Validate order quantity.
    
    Returns:
        (is_valid, error_message)
    """
    if quantity is None:
        return False, "Quantity is None"
    
    if isinstance(quantity, float) and np.isnan(quantity):
        return False, "Quantity is NaN"
    
    if quantity <= 0:
        return False, f"Non-positive quantity: {quantity}"
    
    if abs(quantity) > 1e10:
        return False, f"Extreme quantity value: {quantity}"
    
    return True, ""


def validate_symbol(symbol: str) -> tuple:
    """
    Validate trading symbol.
    
    Returns:
        (is_valid, error_message)
    """
    if not symbol:
        return False, "Empty symbol"
    
    if not isinstance(symbol, str):
        return False, "Symbol must be string"
    
    if len(symbol) < 2 or len(symbol) > 20:
        return False, f"Invalid symbol length: {len(symbol)}"
    
    if not symbol.replace('/', '').replace('-', '').replace('_', '').isalnum():
        return False, f"Invalid symbol characters: {symbol}"
    
    return True, ""


def validate_timeframe(timeframe: str) -> tuple:
    """
    Validate timeframe string.
    
    Returns:
        (is_valid, error_message)
    """
    valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
    
    if timeframe not in valid_timeframes:
        return False, f"Invalid timeframe: {timeframe}. Valid: {valid_timeframes}"
    
    return True, ""


def validate_order_params(params: Dict) -> tuple:
    """
    Validate order parameters.
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = ['symbol', 'side', 'quantity']
    
    # Check required fields
    for field in required_fields:
        if field not in params:
            return False, f"Missing field: {field}"
    
    # Validate symbol
    is_valid, error = validate_symbol(params['symbol'])
    if not is_valid:
        return False, error
    
    # Validate side
    if params['side'] not in ['BUY', 'SELL', 'buy', 'sell']:
        return False, f"Invalid side: {params['side']}"
    
    # Validate quantity
    is_valid, error = validate_quantity(params['quantity'])
    if not is_valid:
        return False, error
    
    # Validate price if present
    if 'price' in params and params['price'] is not None:
        is_valid, error = validate_price(params['price'], params['symbol'])
        if not is_valid:
            return False, error
    
    return True, ""


def validate_risk_params(params: Dict) -> tuple:
    """
    Validate risk management parameters.
    
    Returns:
        (is_valid, error_message)
    """
    if 'max_position_size' in params:
        if params['max_position_size'] <= 0:
            return False, "max_position_size must be positive"
    
    if 'max_portfolio_risk' in params:
        if not 0 < params['max_portfolio_risk'] < 1:
            return False, "max_portfolio_risk must be between 0 and 1"
    
    if 'max_drawdown' in params:
        if not 0 < params['max_drawdown'] < 1:
            return False, "max_drawdown must be between 0 and 1"
    
    if 'max_correlation' in params:
        if not -1 <= params['max_correlation'] <= 1:
            return False, "max_correlation must be between -1 and 1"
    
    return True, ""


def validate_timestamp(timestamp: Any) -> tuple:
    """
    Validate timestamp.
    
    Returns:
        (is_valid, error_message)
    """
    if timestamp is None:
        return False, "Timestamp is None"
    
    if isinstance(timestamp, datetime):
        return True, ""
    
    if isinstance(timestamp, (int, float)):
        if timestamp < 0:
            return False, "Negative timestamp"
        if timestamp > 2e9:  # Year 2033
            return False, "Timestamp too far in future"
        return True, ""
    
    return False, f"Invalid timestamp type: {type(timestamp)}"


def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> tuple:
    """
    Validate DataFrame structure.
    
    Returns:
        (is_valid, error_message)
    """
    if df is None or df.empty:
        return False, "DataFrame is None or empty"
    
    # Check required columns
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        return False, f"Missing columns: {missing_columns}"
    
    # Check for NaN values
    if df[required_columns].isnull().any().any():
        return False, "DataFrame contains NaN values"
    
    return True, ""


def validate_model_input(data: np.ndarray, expected_shape: tuple) -> tuple:
    """
    Validate model input data.
    
    Returns:
        (is_valid, error_message)
    """
    if data is None:
        return False, "Data is None"
    
    if not isinstance(data, np.ndarray):
        return False, f"Data must be numpy array, got {type(data)}"
    
    if data.shape != expected_shape:
        return False, f"Shape mismatch: expected {expected_shape}, got {data.shape}"
    
    if np.isnan(data).any():
        return False, "Data contains NaN values"
    
    if np.isinf(data).any():
        return False, "Data contains infinite values"
    
    return True, ""


def validate_config(config: Dict, required_keys: List[str]) -> tuple:
    """
    Validate configuration dictionary.
    
    Returns:
        (is_valid, error_message)
    """
    if not isinstance(config, dict):
        return False, "Config must be dictionary"
    
    # Check required keys
    missing_keys = set(required_keys) - set(config.keys())
    if missing_keys:
        return False, f"Missing config keys: {missing_keys}"
    
    return True, ""


def sanitize_symbol(symbol: str) -> str:
    """Sanitize trading symbol."""
    return symbol.upper().strip().replace(' ', '')


def sanitize_price(price: float) -> float:
    """Sanitize price value."""
    return max(0.0, float(price))


def sanitize_quantity(quantity: float) -> float:
    """Sanitize quantity value."""
    return max(0.0, float(quantity))


def check_data_staleness(timestamp: datetime, max_age_seconds: int = 60) -> bool:
    """
    Check if data is stale.
    
    Returns:
        True if data is fresh, False if stale
    """
    age = (datetime.now() - timestamp).total_seconds()
    return age <= max_age_seconds


def check_price_spike(
    current_price: float,
    previous_price: float,
    max_change_pct: float = 0.1
) -> bool:
    """
    Check for abnormal price spike.
    
    Returns:
        True if price change is normal, False if spike detected
    """
    if previous_price == 0:
        return True
    
    change_pct = abs(current_price - previous_price) / previous_price
    return change_pct <= max_change_pct


def check_volume_spike(
    current_volume: float,
    avg_volume: float,
    max_multiplier: float = 10.0
) -> bool:
    """
    Check for abnormal volume spike.
    
    Returns:
        True if volume is normal, False if spike detected
    """
    if avg_volume == 0:
        return True
    
    multiplier = current_volume / avg_volume
    return multiplier <= max_multiplier

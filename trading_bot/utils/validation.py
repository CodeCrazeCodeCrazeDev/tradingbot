import logging
logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
"""Strategy validation utilities."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np
from loguru import logger
from dataclasses import field
import numpy
import pandas

@dataclass
class ValidationResult:
    """Result of strategy validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, float]


def validate_strategy(
    strategy_name: str,
    strategy_params: Dict[str, Any],
    historical_data: pd.DataFrame,
    min_trades: int = 20,
    min_win_rate: float = 0.4,
    min_profit_factor: float = 1.2,
    max_drawdown: float = 0.2
) -> ValidationResult:
    """
    Validate a trading strategy against historical data and performance criteria.
    
    Args:
        strategy_name: Name of the strategy to validate
        strategy_params: Strategy parameters to validate
        historical_data: Historical price data for validation
        min_trades: Minimum number of trades required
        min_win_rate: Minimum required win rate
        min_profit_factor: Minimum required profit factor
        max_drawdown: Maximum allowed drawdown
        
    Returns:
        ValidationResult with validation status and metrics
    """
    errors = []
    warnings = []
    metrics = {}
    
    try:
        # Validate strategy parameters
        if not strategy_params:
            errors.append("Strategy parameters cannot be empty")
            return ValidationResult(False, errors, warnings, metrics)
        
        # Validate required parameters
        required_params = {
            'timeframe': str,
            'risk_per_trade': float,
            'stop_loss': float,
            'take_profit': float
        }
        
        for param, param_type in required_params.items():
            if param not in strategy_params:
                errors.append(f"Missing required parameter: {param}")
            elif not isinstance(strategy_params[param], param_type):
                errors.append(f"Invalid type for {param}. Expected {param_type}")
        
        if errors:
            return ValidationResult(False, errors, warnings, metrics)
        
        # Validate historical data
        if len(historical_data) < 1000:  # Minimum required data points
            errors.append("Insufficient historical data for validation")
            return ValidationResult(False, errors, warnings, metrics)
        
        # Simulate strategy on historical data
        trades = _simulate_strategy(strategy_name, strategy_params, historical_data)
        
        if not trades:
            errors.append("Strategy did not generate any trades")
            return ValidationResult(False, errors, warnings, metrics)
        
        # Calculate performance metrics
        metrics = _calculate_metrics(trades, historical_data)
        
        # Validate performance criteria
        if len(trades) < min_trades:
            errors.append(f"Insufficient trades ({len(trades)} < {min_trades})")
        
        if metrics['win_rate'] < min_win_rate:
            errors.append(f"Win rate too low ({metrics['win_rate']:.2%} < {min_win_rate:.2%})")
        
        if metrics['profit_factor'] < min_profit_factor:
            errors.append(f"Profit factor too low ({metrics['profit_factor']:.2f} < {min_profit_factor})")
        
        if metrics['max_drawdown'] > max_drawdown:
            errors.append(f"Maximum drawdown too high ({metrics['max_drawdown']:.2%} > {max_drawdown:.2%})")
        
        # Add warnings for borderline cases
        if len(trades) < min_trades * 2:
            warnings.append("Low number of trades for reliable validation")
        
        if metrics['win_rate'] < min_win_rate * 1.2:
            warnings.append("Win rate close to minimum threshold")
        
        if metrics['profit_factor'] < min_profit_factor * 1.2:
            warnings.append("Profit factor close to minimum threshold")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metrics=metrics
        )
        
    except Exception as e:
        logger.error(f"Error validating strategy: {e}")
        errors.append(f"Validation error: {str(e)}")
        return ValidationResult(False, errors, warnings, metrics)


def _simulate_strategy(
    strategy_name: str,
    strategy_params: Dict[str, Any],
    historical_data: pd.DataFrame
) -> List[Dict[str, Any]]:
    """Simulate strategy on historical data."""
    trades = []
    
    try:
        # Basic simulation - can be extended with actual strategy logic
        for i in range(len(historical_data) - 1):
            if _should_enter_trade(strategy_name, strategy_params, historical_data.iloc[:i+1]):
                trade = _execute_trade(strategy_params, historical_data.iloc[i:])
                if trade:
                    trades.append(trade)
        
        return trades
        
    except Exception as e:
        logger.error(f"Error simulating strategy: {e}")
        return []


def _should_enter_trade(
    strategy_name: str,
    strategy_params: Dict[str, Any],
    data: pd.DataFrame
) -> bool:
    """Determine if strategy should enter a trade."""
    try:
        # Basic entry logic - can be extended with actual strategy rules
        if len(data) < 20:  # Need minimum data for indicators
            return False
            
        # Calculate basic indicators
        close = data['close'].values
        sma_20 = np.mean(close[-20:])
        sma_50 = np.mean(close[-50:]) if len(close) >= 50 else sma_20
        
        # Simple trend following logic
        return close[-1] > sma_20 > sma_50
        
    except Exception as e:
        logger.error(f"Error checking trade entry: {e}")
        return False


def _execute_trade(
    strategy_params: Dict[str, Any],
    data: pd.DataFrame
) -> Optional[Dict[str, Any]]:
    """Execute simulated trade."""
    try:
        entry_price = data['open'].iloc[1]  # Enter on next bar open
        stop_loss = entry_price * (1 - strategy_params['stop_loss'])
        take_profit = entry_price * (1 + strategy_params['take_profit'])
        
        for i in range(1, len(data)):
            low = data['low'].iloc[i]
            high = data['high'].iloc[i]
            
            if low <= stop_loss:
                return {
                    'entry_price': entry_price,
                    'exit_price': stop_loss,
                    'profit': (stop_loss - entry_price) / entry_price,
                    'bars_held': i,
                    'exit_type': 'stop_loss'
                }
            
            if high >= take_profit:
                return {
                    'entry_price': entry_price,
                    'exit_price': take_profit,
                    'profit': (take_profit - entry_price) / entry_price,
                    'bars_held': i,
                    'exit_type': 'take_profit'
                }
        
        return None  # Trade didn't reach stop loss or take profit
        
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return None


def validate_signal(signal: Dict[str, Any], min_confidence: float = 0.6) -> ValidationResult:
    """Validate a trading signal.
    
    Args:
        signal: Trading signal to validate
        min_confidence: Minimum required confidence level
        
    Returns:
        ValidationResult with validation status
    """
    errors = []
    warnings = []
    metrics = {}
    
    try:
        # Validate required fields
        required_fields = {
            'direction': str,
            'confidence': float,
            'timestamp': (int, float),
            'symbol': str,
            'source': str
        }
        
        for field, field_type in required_fields.items():
            if field not in signal:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(signal[field], field_type):
                errors.append(f"Invalid type for {field}. Expected {field_type}")
        
        if errors:
            return ValidationResult(False, errors, warnings, metrics)
        
        # Validate direction
        if signal['direction'] not in ['buy', 'sell']:
            errors.append(f"Invalid direction: {signal['direction']}. Must be 'buy' or 'sell'")
        
        # Validate confidence
        confidence = signal.get('confidence', 0.0)
        if confidence < min_confidence:
            errors.append(f"Confidence too low: {confidence:.2f} < {min_confidence:.2f}")
        elif confidence < min_confidence * 1.2:
            warnings.append("Confidence close to minimum threshold")
        
        # Validate timestamp
        timestamp = signal.get('timestamp', 0)
        current_time = datetime.now().timestamp()
        if timestamp > current_time:
            errors.append("Signal timestamp is in the future")
        elif timestamp < current_time - 3600:  # 1 hour old
            warnings.append("Signal may be stale (over 1 hour old)")
        
        # Add metrics
        metrics = {
            'confidence': confidence,
            'age_seconds': current_time - timestamp
        }
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metrics=metrics
        )
        
    except Exception as e:
        logger.error(f"Error validating signal: {e}")
        errors.append(f"Validation error: {str(e)}")
        return ValidationResult(False, errors, warnings, metrics)


def _calculate_metrics(
    trades: List[Dict[str, Any]],
    historical_data: pd.DataFrame
) -> Dict[str, float]:
    """Calculate performance metrics from trades."""
    try:
        if not trades:
            return {
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 1.0,
                'avg_trade': 0.0,
                'sharpe_ratio': 0.0
            }
        
        profits = [t['profit'] for t in trades]
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p <= 0]
        
        # Calculate metrics
        win_rate = len(wins) / len(trades)
        
        profit_factor = (
            abs(sum(wins)) / abs(sum(losses))
            if losses and sum(losses) != 0
            else float('inf')
        )
        
        # Calculate running equity curve
        equity_curve = np.cumsum([0] + profits)
        peak = np.maximum.accumulate(equity_curve)
        drawdowns = (peak - equity_curve) / peak
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
        # Calculate Sharpe ratio (annualized)
        returns = pd.Series(profits)
        sharpe_ratio = (
            np.sqrt(252) * returns.mean() / returns.std()
            if len(returns) > 1 and returns.std() != 0
            else 0
        )
        
        return {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'avg_trade': np.mean(profits),
            'sharpe_ratio': sharpe_ratio,
            'total_trades': len(trades),
            'avg_bars_held': np.mean([t['bars_held'] for t in trades])
        }
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        return {
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 1.0,
            'avg_trade': 0.0,
            'sharpe_ratio': 0.0
        }

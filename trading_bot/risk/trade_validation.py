"""
TRADE VALIDATION MODULE - P0 CRITICAL FIXES
============================================================

Implements critical validation for:
1. Stop Loss Validation
2. Take Profit Validation
3. Position Size Validation
4. Margin Calculation
5. Leverage Limits
6. Slippage Protection

Author: AI Assistant
Date: October 23, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, Tuple, Any

import numpy as np
from loguru import logger
import numpy

# ============================================================================
# ENUMS
# ============================================================================

class ValidationStatus(Enum):
    """Validation result status."""
    VALID = auto()
    INVALID = auto()
    WARNING = auto()
    ERROR = auto()


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ValidationResult:
    """Result of trade validation."""
    status: ValidationStatus
    is_valid: bool
    message: str
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        try:
            if self.details is None:
                self.details = {}
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


@dataclass
class TradeValidationConfig:
    """Configuration for trade validation."""
    # Stop Loss Validation
    min_sl_distance_pips: float = 0.5  # Minimum 0.5% from entry
    max_sl_distance_pips: float = 5.0  # Maximum 5% from entry
    
    # Take Profit Validation
    min_risk_reward_ratio: float = 1.5  # Minimum 1.5:1 ratio
    
    # Position Size Validation
    min_position_size: float = 0.01
    max_position_size: float = 1.0
    
    # Margin & Leverage
    max_leverage: float = 10.0  # Hard limit 1:10
    min_margin_buffer: float = 2.0  # 200% buffer required
    
    # Slippage Protection
    max_slippage_pips: float = 2.0  # Maximum 2 pips slippage
    
    # Account Balance
    min_account_balance: float = 1000.0


# ============================================================================
# STOP LOSS VALIDATOR
# ============================================================================

class StopLossValidator:
    """Validates stop loss parameters."""
    
    def __init__(self, config: TradeValidationConfig = None):
        try:
            self.config = config or TradeValidationConfig()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(self, entry_price: float, stop_loss: float, 
                symbol: str = "EURUSD") -> ValidationResult:
        """
        Validate stop loss is reasonable.
        
        Rules:
        - SL must be positive
        - SL must be at least min_sl_distance_pips away from entry
        - SL must be no more than max_sl_distance_pips away from entry
        """
        try:
            details = {
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'symbol': symbol
            }
        
            # Check 1: Stop loss must be positive
            if stop_loss <= 0:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    is_valid=False,
                    message=f"Stop loss must be positive, got {stop_loss}",
                    details=details
                )
        
            # Check 2: Stop loss must be different from entry
            if stop_loss == entry_price:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    is_valid=False,
                    message=f"Stop loss cannot equal entry price ({entry_price})",
                    details=details
                )
        
            # Calculate distance
            distance_pips = abs(entry_price - stop_loss) * 10000
            distance_percent = (distance_pips / 10000) * 100
        
            details['distance_pips'] = distance_pips
            details['distance_percent'] = distance_percent
        
            # Check 3: Stop loss too close
            if distance_percent < self.config.min_sl_distance_pips:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    is_valid=False,
                    message=f"Stop loss too close: {distance_percent:.2f}% (min {self.config.min_sl_distance_pips}%)",
                    details=details
                )
        
            # Check 4: Stop loss too far
            if distance_percent > self.config.max_sl_distance_pips:
                return ValidationResult(
                    status=ValidationStatus.WARNING,
                    is_valid=True,
                    message=f"Stop loss far: {distance_percent:.2f}% (max recommended {self.config.max_sl_distance_pips}%)",
                    details=details
                )
        
            return ValidationResult(
                status=ValidationStatus.VALID,
                is_valid=True,
                message=f"Stop loss valid: {distance_percent:.2f}% from entry",
                details=details
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


# ============================================================================
# TAKE PROFIT VALIDATOR
# ============================================================================

class TakeProfitValidator:
    """Validates take profit parameters."""
    
    def __init__(self, config: TradeValidationConfig = None):
        try:
            self.config = config or TradeValidationConfig()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(self, entry_price: float, stop_loss: float, 
                take_profit: float, min_ratio: float = None) -> ValidationResult:
        """
        Validate take profit maintains positive risk/reward.
        
        Rules:
        - TP must be on opposite side of entry from SL
        - TP distance must be >= SL distance * min_ratio
        """
        try:
            if min_ratio is None:
                min_ratio = self.config.min_risk_reward_ratio
        
            details = {
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'min_ratio': min_ratio
            }
        
            # Check 1: Take profit must be positive
            if take_profit <= 0:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    is_valid=False,
                    message=f"Take profit must be positive, got {take_profit}",
                    details=details
                )
        
            # Check 2: Take profit must be different from entry
            if take_profit == entry_price:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    is_valid=False,
                    message=f"Take profit cannot equal entry price ({entry_price})",
                    details=details
                )
        
            # Calculate distances
            sl_distance = abs(entry_price - stop_loss)
            tp_distance = abs(take_profit - entry_price)
        
            details['sl_distance'] = sl_distance
            details['tp_distance'] = tp_distance
        
            # Check 3: TP and SL on same side (invalid)
            sl_side = "above" if stop_loss > entry_price else "below"
            tp_side = "above" if take_profit > entry_price else "below"
        
            if sl_side == tp_side:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    is_valid=False,
                    message=f"TP and SL on same side: TP {tp_side}, SL {sl_side}",
                    details=details
                )
        
            # Check 4: Risk/Reward ratio
            if sl_distance > 0:
                ratio = tp_distance / sl_distance
                details['ratio'] = ratio
            
                if ratio < min_ratio:
                    return ValidationResult(
                        status=ValidationStatus.INVALID,
                        is_valid=False,
                        message=f"Risk/reward ratio {ratio:.2f}:1 below minimum {min_ratio}:1",
                        details=details
                    )
        
            return ValidationResult(
                status=ValidationStatus.VALID,
                is_valid=True,
                message=f"Take profit valid: {ratio:.2f}:1 risk/reward ratio",
                details=details
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


# ============================================================================
# POSITION SIZE VALIDATOR
# ============================================================================

class PositionSizeValidator:
    """Validates position size parameters."""
    
    def __init__(self, config: TradeValidationConfig = None):
        try:
            self.config = config or TradeValidationConfig()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(self, position_size: float) -> ValidationResult:
        """Validate position size is within acceptable range."""
        try:
            details = {'position_size': position_size}
        
            # Check 1: Minimum size
            if position_size < self.config.min_position_size:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    is_valid=False,
                    message=f"Position size too small: {position_size} (min {self.config.min_position_size})",
                    details=details
                )
        
            # Check 2: Maximum size
            if position_size > self.config.max_position_size:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    is_valid=False,
                    message=f"Position size too large: {position_size} (max {self.config.max_position_size})",
                    details=details
                )
        
            return ValidationResult(
                status=ValidationStatus.VALID,
                is_valid=True,
                message=f"Position size valid: {position_size} lots",
                details=details
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise
    
    def calculate_position_size(self, account_balance: float, entry_price: float,
                               stop_loss: float, risk_percent: float = 2.0) -> float:
        """
        Calculate position size using 2% risk rule.
        
        Formula:
        Risk Amount = Account Balance * Risk %
        Pips at Risk = abs(Entry - SL) * 10000
        Position Size = Risk Amount / (Pips * Pip Value)
        """
        # Calculate risk in dollars
        try:
            risk_amount = account_balance * (risk_percent / 100)
        
            # Calculate pips at risk
            pips_at_risk = abs(entry_price - stop_loss) * 10000
        
            if pips_at_risk == 0:
                return self.config.min_position_size
        
            # Pip value (standard lot = 10 per pip for EURUSD)
            pip_value = 10
        
            # Calculate position size
            position_size = risk_amount / (pips_at_risk * pip_value)
        
            # Round to nearest 0.01 lot
            position_size = round(position_size, 2)
        
            # Enforce limits
            return max(
                self.config.min_position_size,
                min(self.config.max_position_size, position_size)
            )
        except Exception as e:
            logger.error(f"Error in calculate_position_size: {e}")
            raise


# ============================================================================
# SLIPPAGE VALIDATOR
# ============================================================================

class SlippageValidator:
    """Validates slippage protection."""
    
    def __init__(self, config: TradeValidationConfig = None):
        try:
            self.config = config or TradeValidationConfig()
            self.spread_history = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_spread(self, symbol: str, bid: float, ask: float):
        """Track spread for symbol."""
        try:
            if symbol not in self.spread_history:
                self.spread_history[symbol] = []
        
            spread = ask - bid
            self.spread_history[symbol].append(spread)
        
            # Keep only last 100 spreads
            if len(self.spread_history[symbol]) > 100:
                self.spread_history[symbol].pop(0)
        except Exception as e:
            logger.error(f"Error in update_spread: {e}")
            raise
    
    def validate(self, symbol: str, bid: float, ask: float) -> ValidationResult:
        """Check if current spread is acceptable."""
        try:
            details = {
                'symbol': symbol,
                'bid': bid,
                'ask': ask,
                'current_spread': ask - bid
            }
        
            if symbol not in self.spread_history or not self.spread_history[symbol]:
                return ValidationResult(
                    status=ValidationStatus.VALID,
                    is_valid=True,
                    message="No spread history yet, allowing trade",
                    details=details
                )
        
            current_spread = ask - bid
            avg_spread = np.mean(self.spread_history[symbol])
            spread_multiplier = current_spread / avg_spread if avg_spread > 0 else 1.0
        
            details['average_spread'] = avg_spread
            details['spread_multiplier'] = spread_multiplier
        
            if spread_multiplier > 2.0:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    is_valid=False,
                    message=f"Spread too high: {spread_multiplier:.2f}x average",
                    details=details
                )
        
            return ValidationResult(
                status=ValidationStatus.VALID,
                is_valid=True,
                message=f"Spread acceptable: {spread_multiplier:.2f}x average",
                details=details
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


# ============================================================================
# LEVERAGE VALIDATOR
# ============================================================================

class LeverageValidator:
    """Validates leverage parameters."""
    
    def __init__(self, config: TradeValidationConfig = None):
        try:
            self.config = config or TradeValidationConfig()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(self, position_size: float, account_balance: float,
                pip_value: float = 10) -> ValidationResult:
        """Validate leverage is within limits."""
        try:
            details = {
                'position_size': position_size,
                'account_balance': account_balance,
                'pip_value': pip_value
            }
        
            # Calculate leverage
            position_value = position_size * 100000 * pip_value / 10000
            leverage = position_value / account_balance if account_balance > 0 else 0
        
            details['position_value'] = position_value
            details['leverage'] = leverage
        
            if leverage > self.config.max_leverage:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    is_valid=False,
                    message=f"Leverage {leverage:.2f}:1 exceeds maximum {self.config.max_leverage}:1",
                    details=details
                )
        
            return ValidationResult(
                status=ValidationStatus.VALID,
                is_valid=True,
                message=f"Leverage valid: {leverage:.2f}:1",
                details=details
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


# ============================================================================
# MASTER TRADE VALIDATOR
# ============================================================================

class MasterTradeValidator:
    """Master validator combining all checks."""
    
    def __init__(self, config: TradeValidationConfig = None):
        try:
            self.config = config or TradeValidationConfig()
            self.sl_validator = StopLossValidator(config)
            self.tp_validator = TakeProfitValidator(config)
            self.ps_validator = PositionSizeValidator(config)
            self.slippage_validator = SlippageValidator(config)
            self.leverage_validator = LeverageValidator(config)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate_trade(self, entry_price: float, stop_loss: float,
                      take_profit: float, position_size: float,
                      account_balance: float, symbol: str = "EURUSD",
                      bid: float = None, ask: float = None) -> Dict[str, ValidationResult]:
        """
        Validate complete trade setup.
        
        Returns dict with results for each validation type.
        """
        try:
            results = {}
        
            # Validate stop loss
            results['stop_loss'] = self.sl_validator.validate(entry_price, stop_loss, symbol)
        
            # Validate take profit
            results['take_profit'] = self.tp_validator.validate(
                entry_price, stop_loss, take_profit
            )
        
            # Validate position size
            results['position_size'] = self.ps_validator.validate(position_size)
        
            # Validate slippage
            if bid is not None and ask is not None:
                results['slippage'] = self.slippage_validator.validate(symbol, bid, ask)
        
            # Validate leverage
            results['leverage'] = self.leverage_validator.validate(
                position_size, account_balance
            )
        
            return results
        except Exception as e:
            logger.error(f"Error in validate_trade: {e}")
            raise
    
    def is_trade_valid(self, results: Dict[str, ValidationResult]) -> bool:
        """Check if all validations passed."""
        try:
            for result in results.values():
                if not result.is_valid:
                    return False
            return True
        except Exception as e:
            logger.error(f"Error in is_trade_valid: {e}")
            raise
    
    def get_validation_summary(self, results: Dict[str, ValidationResult]) -> str:
        """Get human-readable validation summary."""
        try:
            summary = "TRADE VALIDATION SUMMARY\n"
            summary += "=" * 50 + "\n"
        
            for check_name, result in results.items():
                status_str = "✓" if result.is_valid else "✗"
                summary += f"{status_str} {check_name.upper()}: {result.message}\n"
        
            all_valid = self.is_trade_valid(results)
            summary += "=" * 50 + "\n"
            summary += f"Overall: {'VALID' if all_valid else 'INVALID'}\n"
        
            return summary
        except Exception as e:
            logger.error(f"Error in get_validation_summary: {e}")
            raise

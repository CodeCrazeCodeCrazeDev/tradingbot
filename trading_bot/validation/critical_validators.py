"""
Critical Trading Validators

MUST-HAVE validation before any trade execution:
- Stop Loss validation (prevents unlimited losses)
- Take Profit validation (ensures positive risk/reward)
- Position sizing validation (prevents over-leverage)
- Drawdown protection (prevents account wipeout)
- Daily loss limits (circuit breaker)
- Margin validation (prevents margin calls)

Author: Trading Bot Team
Date: 2025-10-18
Priority: P0 - CRITICAL
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Validation result status"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class ValidationError:
    """Validation error details"""
    validator: str
    message: str
    severity: str
    details: Dict[str, Any]


class StopLossValidator:
    """
    CRITICAL: Validates stop loss to prevent unlimited losses
    
    Rules:
    1. SL must be positive and non-zero
    2. SL must be reasonable (0.5% - 5% of price)
    3. SL must be closer than TP (for positive risk/reward)
    4. SL must be on correct side of entry price
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.min_sl_percent = self.config.get('min_sl_percent', 0.5)  # 0.5%
            self.max_sl_percent = self.config.get('max_sl_percent', 5.0)  # 5%
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def validate(self, trade: Dict[str, Any]) -> Tuple[ValidationResult, Optional[ValidationError]]:
        """
        Validate stop loss
        
        Args:
            trade: Trade dict with keys: direction, entry_price, stop_loss, take_profit
            
        Returns:
            (ValidationResult, Optional[ValidationError])
        """
        try:
            direction = trade.get('direction', '').upper()
            entry_price = trade.get('entry_price', 0)
            stop_loss = trade.get('stop_loss', 0)
            take_profit = trade.get('take_profit', 0)
        
            # Rule 1: SL must be positive and non-zero
            if stop_loss <= 0:
                return ValidationResult.FAIL, ValidationError(
                    validator='StopLossValidator',
                    message='Stop loss must be positive and non-zero',
                    severity='CRITICAL',
                    details={
                        'stop_loss': stop_loss,
                        'reason': 'Zero or negative stop loss allows unlimited losses'
                    }
                )
        
            # Rule 2: SL must be reasonable
            if entry_price > 0:
                sl_distance = abs(entry_price - stop_loss)
                sl_percent = (sl_distance / entry_price) * 100
            
                if sl_percent < self.min_sl_percent:
                    return ValidationResult.FAIL, ValidationError(
                        validator='StopLossValidator',
                        message=f'Stop loss too tight: {sl_percent:.2f}% < {self.min_sl_percent}%',
                        severity='CRITICAL',
                        details={
                            'sl_percent': sl_percent,
                            'min_required': self.min_sl_percent,
                            'reason': 'Too tight SL will be hit by normal market noise'
                        }
                    )
            
                if sl_percent > self.max_sl_percent:
                    return ValidationResult.FAIL, ValidationError(
                        validator='StopLossValidator',
                        message=f'Stop loss too wide: {sl_percent:.2f}% > {self.max_sl_percent}%',
                        severity='CRITICAL',
                        details={
                            'sl_percent': sl_percent,
                            'max_allowed': self.max_sl_percent,
                            'reason': 'Too wide SL risks excessive losses'
                        }
                    )
        
            # Rule 3: SL must be closer than TP (positive risk/reward)
            if take_profit > 0 and entry_price > 0:
                sl_distance = abs(entry_price - stop_loss)
                tp_distance = abs(take_profit - entry_price)
            
                if tp_distance < sl_distance:
                    return ValidationResult.FAIL, ValidationError(
                        validator='StopLossValidator',
                        message='Take profit closer than stop loss (negative risk/reward)',
                        severity='CRITICAL',
                        details={
                            'sl_distance': sl_distance,
                            'tp_distance': tp_distance,
                            'risk_reward': tp_distance / sl_distance if sl_distance > 0 else 0,
                            'reason': 'Risk/reward ratio < 1.0 guarantees losses over time'
                        }
                    )
        
            # Rule 4: SL must be on correct side of entry
            if direction == 'BUY':
                if stop_loss >= entry_price:
                    return ValidationResult.FAIL, ValidationError(
                        validator='StopLossValidator',
                        message='BUY stop loss must be below entry price',
                        severity='CRITICAL',
                        details={
                            'direction': direction,
                            'entry_price': entry_price,
                            'stop_loss': stop_loss,
                            'reason': 'SL above entry for BUY will trigger immediately'
                        }
                    )
            elif direction == 'SELL':
                if stop_loss <= entry_price:
                    return ValidationResult.FAIL, ValidationError(
                        validator='StopLossValidator',
                        message='SELL stop loss must be above entry price',
                        severity='CRITICAL',
                        details={
                            'direction': direction,
                            'entry_price': entry_price,
                            'stop_loss': stop_loss,
                            'reason': 'SL below entry for SELL will trigger immediately'
                        }
                    )
        
            return ValidationResult.PASS, None
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class TakeProfitValidator:
    """
    CRITICAL: Validates take profit for positive risk/reward
    
    Rules:
    1. TP must be positive and non-zero
    2. TP must be further than SL (minimum 1.5:1 risk/reward)
    3. TP must be on correct side of entry price
    4. TP must be reasonable (not too far)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.min_risk_reward = self.config.get('min_risk_reward', 1.5)
            self.max_tp_percent = self.config.get('max_tp_percent', 10.0)  # 10%
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def validate(self, trade: Dict[str, Any]) -> Tuple[ValidationResult, Optional[ValidationError]]:
        """Validate take profit"""
        try:
            direction = trade.get('direction', '').upper()
            entry_price = trade.get('entry_price', 0)
            stop_loss = trade.get('stop_loss', 0)
            take_profit = trade.get('take_profit', 0)
        
            # Rule 1: TP must be positive and non-zero
            if take_profit <= 0:
                return ValidationResult.FAIL, ValidationError(
                    validator='TakeProfitValidator',
                    message='Take profit must be positive and non-zero',
                    severity='CRITICAL',
                    details={
                        'take_profit': take_profit,
                        'reason': 'Zero or negative TP means no profit target'
                    }
                )
        
            # Rule 2: TP must be further than SL
            if entry_price > 0 and stop_loss > 0:
                sl_distance = abs(entry_price - stop_loss)
                tp_distance = abs(take_profit - entry_price)
                risk_reward = tp_distance / sl_distance if sl_distance > 0 else 0
            
                if risk_reward < self.min_risk_reward:
                    return ValidationResult.FAIL, ValidationError(
                        validator='TakeProfitValidator',
                        message=f'Risk/reward too low: {risk_reward:.2f} < {self.min_risk_reward}',
                        severity='CRITICAL',
                        details={
                            'risk_reward': risk_reward,
                            'min_required': self.min_risk_reward,
                            'sl_distance': sl_distance,
                            'tp_distance': tp_distance,
                            'reason': f'Need minimum {self.min_risk_reward}:1 risk/reward for profitability'
                        }
                    )
        
            # Rule 3: TP must be on correct side of entry
            if direction == 'BUY':
                if take_profit <= entry_price:
                    return ValidationResult.FAIL, ValidationError(
                        validator='TakeProfitValidator',
                        message='BUY take profit must be above entry price',
                        severity='CRITICAL',
                        details={
                            'direction': direction,
                            'entry_price': entry_price,
                            'take_profit': take_profit,
                            'reason': 'TP below entry for BUY means immediate loss'
                        }
                    )
            elif direction == 'SELL':
                if take_profit >= entry_price:
                    return ValidationResult.FAIL, ValidationError(
                        validator='TakeProfitValidator',
                        message='SELL take profit must be below entry price',
                        severity='CRITICAL',
                        details={
                            'direction': direction,
                            'entry_price': entry_price,
                            'take_profit': take_profit,
                            'reason': 'TP above entry for SELL means immediate loss'
                        }
                    )
        
            # Rule 4: TP must be reasonable
            if entry_price > 0:
                tp_distance = abs(take_profit - entry_price)
                tp_percent = (tp_distance / entry_price) * 100
            
                if tp_percent > self.max_tp_percent:
                    return ValidationResult.WARNING, ValidationError(
                        validator='TakeProfitValidator',
                        message=f'Take profit very far: {tp_percent:.2f}% > {self.max_tp_percent}%',
                        severity='WARNING',
                        details={
                            'tp_percent': tp_percent,
                            'max_recommended': self.max_tp_percent,
                            'reason': 'Very far TP may never be reached'
                        }
                    )
        
            return ValidationResult.PASS, None
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class PositionSizingValidator:
    """
    CRITICAL: Validates position size to prevent over-leverage
    
    Rules:
    1. Position size must be positive
    2. Position size must respect 2% risk rule
    3. Position size must not exceed account balance
    4. Position size must respect leverage limits
    5. Total exposure must not exceed limits
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.max_risk_percent = self.config.get('max_risk_percent', 2.0)  # 2% per trade
            self.max_leverage = self.config.get('max_leverage', 10)  # 10x max
            self.max_total_exposure_percent = self.config.get('max_total_exposure_percent', 30.0)  # 30%
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def validate(self, trade: Dict[str, Any], account: Dict[str, Any]) -> Tuple[ValidationResult, Optional[ValidationError]]:
        """Validate position size"""
        try:
            position_size = trade.get('position_size', 0)
            entry_price = trade.get('entry_price', 0)
            stop_loss = trade.get('stop_loss', 0)
        
            account_balance = account.get('balance', 0)
            account_equity = account.get('equity', 0)
            open_positions = account.get('open_positions', [])
        
            # Rule 1: Position size must be positive
            if position_size <= 0:
                return ValidationResult.FAIL, ValidationError(
                    validator='PositionSizingValidator',
                    message='Position size must be positive',
                    severity='CRITICAL',
                    details={
                        'position_size': position_size,
                        'reason': 'Zero or negative position size'
                    }
                )
        
            # Rule 2: Respect 2% risk rule
            if entry_price > 0 and stop_loss > 0 and account_balance > 0:
                sl_distance = abs(entry_price - stop_loss)
                risk_amount = position_size * sl_distance * 100000  # Convert to base currency
                risk_percent = (risk_amount / account_balance) * 100
            
                if risk_percent > self.max_risk_percent:
                    return ValidationResult.FAIL, ValidationError(
                        validator='PositionSizingValidator',
                        message=f'Position size risks {risk_percent:.2f}% > {self.max_risk_percent}%',
                        severity='CRITICAL',
                        details={
                            'risk_percent': risk_percent,
                            'max_allowed': self.max_risk_percent,
                            'risk_amount': risk_amount,
                            'account_balance': account_balance,
                            'reason': f'Exceeds {self.max_risk_percent}% risk rule'
                        }
                    )
        
            # Rule 3: Position size must not exceed account balance
            position_value = position_size * entry_price * 100000
            if position_value > account_balance * self.max_leverage:
                return ValidationResult.FAIL, ValidationError(
                    validator='PositionSizingValidator',
                    message='Position size exceeds account capacity',
                    severity='CRITICAL',
                    details={
                        'position_value': position_value,
                        'max_allowed': account_balance * self.max_leverage,
                        'reason': 'Insufficient account balance for position'
                    }
                )
        
            # Rule 4: Check leverage
            if account_equity > 0:
                leverage = position_value / account_equity
                if leverage > self.max_leverage:
                    return ValidationResult.FAIL, ValidationError(
                        validator='PositionSizingValidator',
                        message=f'Leverage {leverage:.1f}x > {self.max_leverage}x',
                        severity='CRITICAL',
                        details={
                            'leverage': leverage,
                            'max_allowed': self.max_leverage,
                            'reason': 'Excessive leverage risks margin call'
                        }
                    )
        
            # Rule 5: Check total exposure
            total_exposure = position_value
            for pos in open_positions:
                total_exposure += pos.get('value', 0)
        
            exposure_percent = (total_exposure / account_balance) * 100 if account_balance > 0 else 0
        
            if exposure_percent > self.max_total_exposure_percent:
                return ValidationResult.FAIL, ValidationError(
                    validator='PositionSizingValidator',
                    message=f'Total exposure {exposure_percent:.1f}% > {self.max_total_exposure_percent}%',
                    severity='CRITICAL',
                    details={
                        'total_exposure': total_exposure,
                        'exposure_percent': exposure_percent,
                        'max_allowed': self.max_total_exposure_percent,
                        'reason': 'Too much capital at risk'
                    }
                )
        
            return ValidationResult.PASS, None
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class DrawdownProtectionValidator:
    """
    CRITICAL: Prevents account wipeout through drawdown protection
    
    Rules:
    1. Stop trading if drawdown > 20%
    2. Reduce position sizes if drawdown > 10%
    3. Track daily drawdown
    4. Track peak-to-valley drawdown
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.max_drawdown_percent = self.config.get('max_drawdown_percent', 20.0)  # 20%
            self.warning_drawdown_percent = self.config.get('warning_drawdown_percent', 10.0)  # 10%
            self.peak_balance = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def validate(self, account: Dict[str, Any]) -> Tuple[ValidationResult, Optional[ValidationError]]:
        """Validate drawdown protection"""
        try:
            current_balance = account.get('balance', 0)
            starting_balance = account.get('starting_balance', current_balance)
        
            # Update peak balance
            if current_balance > self.peak_balance:
                self.peak_balance = current_balance
        
            # Use starting balance if no peak yet
            if self.peak_balance == 0:
                self.peak_balance = starting_balance
        
            # Calculate drawdown from peak
            if self.peak_balance > 0:
                drawdown = ((self.peak_balance - current_balance) / self.peak_balance) * 100
            else:
                drawdown = 0
        
            # Rule 1: Stop trading if drawdown > 20%
            if drawdown >= self.max_drawdown_percent:
                return ValidationResult.FAIL, ValidationError(
                    validator='DrawdownProtectionValidator',
                    message=f'CRITICAL: Drawdown {drawdown:.2f}% >= {self.max_drawdown_percent}%',
                    severity='CRITICAL',
                    details={
                        'drawdown_percent': drawdown,
                        'max_allowed': self.max_drawdown_percent,
                        'peak_balance': self.peak_balance,
                        'current_balance': current_balance,
                        'loss_amount': self.peak_balance - current_balance,
                        'reason': 'Maximum drawdown reached - STOP TRADING IMMEDIATELY'
                    }
                )
        
            # Rule 2: Warning if drawdown > 10%
            if drawdown >= self.warning_drawdown_percent:
                return ValidationResult.WARNING, ValidationError(
                    validator='DrawdownProtectionValidator',
                    message=f'WARNING: Drawdown {drawdown:.2f}% >= {self.warning_drawdown_percent}%',
                    severity='WARNING',
                    details={
                        'drawdown_percent': drawdown,
                        'warning_threshold': self.warning_drawdown_percent,
                        'peak_balance': self.peak_balance,
                        'current_balance': current_balance,
                        'reason': 'Approaching maximum drawdown - reduce position sizes'
                    }
                )
        
            return ValidationResult.PASS, None
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class DailyLossLimitValidator:
    """
    CRITICAL: Enforces daily loss limits (circuit breaker)
    
    Rules:
    1. Stop trading if daily loss > limit
    2. Track daily P&L
    3. Reset at start of new day
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.max_daily_loss_percent = self.config.get('max_daily_loss_percent', 5.0)  # 5% per day
            self.daily_start_balance = 0
            self.current_day = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def validate(self, account: Dict[str, Any]) -> Tuple[ValidationResult, Optional[ValidationError]]:
        """Validate daily loss limit"""
        try:
            current_balance = account.get('balance', 0)
            current_date = datetime.now().date()
        
            # Reset at start of new day
            if self.current_day != current_date:
                self.current_day = current_date
                self.daily_start_balance = current_balance
        
            # Calculate daily loss
            if self.daily_start_balance > 0:
                daily_loss = self.daily_start_balance - current_balance
                daily_loss_percent = (daily_loss / self.daily_start_balance) * 100
            else:
                daily_loss = 0
                daily_loss_percent = 0
        
            # Check limit
            if daily_loss_percent >= self.max_daily_loss_percent:
                return ValidationResult.FAIL, ValidationError(
                    validator='DailyLossLimitValidator',
                    message=f'Daily loss limit reached: {daily_loss_percent:.2f}% >= {self.max_daily_loss_percent}%',
                    severity='CRITICAL',
                    details={
                        'daily_loss_percent': daily_loss_percent,
                        'max_allowed': self.max_daily_loss_percent,
                        'daily_start_balance': self.daily_start_balance,
                        'current_balance': current_balance,
                        'loss_amount': daily_loss,
                        'reason': 'Daily loss limit reached - STOP TRADING FOR TODAY'
                    }
                )
        
            return ValidationResult.PASS, None
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class MarginValidator:
    """
    CRITICAL: Prevents margin calls
    
    Rules:
    1. Ensure sufficient margin before trade
    2. Maintain 200% margin buffer
    3. Check margin level after trade
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.min_margin_level_percent = self.config.get('min_margin_level_percent', 200.0)  # 200%
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def validate(self, trade: Dict[str, Any], account: Dict[str, Any]) -> Tuple[ValidationResult, Optional[ValidationError]]:
        """Validate margin requirements"""
        try:
            position_size = trade.get('position_size', 0)
            entry_price = trade.get('entry_price', 0)
            leverage = trade.get('leverage', 1)
        
            account_equity = account.get('equity', 0)
            used_margin = account.get('used_margin', 0)
            free_margin = account.get('free_margin', 0)
        
            # Calculate required margin for new position
            position_value = position_size * entry_price * 100000
            required_margin = position_value / leverage
        
            # Check if sufficient free margin
            if required_margin > free_margin:
                return ValidationResult.FAIL, ValidationError(
                    validator='MarginValidator',
                    message='Insufficient free margin',
                    severity='CRITICAL',
                    details={
                        'required_margin': required_margin,
                        'free_margin': free_margin,
                        'shortfall': required_margin - free_margin,
                        'reason': 'Not enough free margin for position'
                    }
                )
        
            # Calculate margin level after trade
            new_used_margin = used_margin + required_margin
            if new_used_margin > 0:
                margin_level = (account_equity / new_used_margin) * 100
            else:
                margin_level = 0
        
            # Check margin level
            if margin_level < self.min_margin_level_percent:
                return ValidationResult.FAIL, ValidationError(
                    validator='MarginValidator',
                    message=f'Margin level too low: {margin_level:.1f}% < {self.min_margin_level_percent}%',
                    severity='CRITICAL',
                    details={
                        'margin_level': margin_level,
                        'min_required': self.min_margin_level_percent,
                        'account_equity': account_equity,
                        'new_used_margin': new_used_margin,
                        'reason': 'Risk of margin call'
                    }
                )
        
            return ValidationResult.PASS, None
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class CriticalValidatorSuite:
    """
    Master validator that runs all critical validations
    
    ALL validations must pass before trade execution
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Initialize all validators
            self.stop_loss_validator = StopLossValidator(self.config)
            self.take_profit_validator = TakeProfitValidator(self.config)
            self.position_sizing_validator = PositionSizingValidator(self.config)
            self.drawdown_validator = DrawdownProtectionValidator(self.config)
            self.daily_loss_validator = DailyLossLimitValidator(self.config)
            self.margin_validator = MarginValidator(self.config)
        
            logger.info("Critical validator suite initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate_trade(self, trade: Dict[str, Any], account: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """
        Run all critical validations
        
        Returns:
            (all_passed: bool, errors: List[ValidationError])
        """
        try:
            errors = []
        
            # 1. Stop Loss validation
            result, error = self.stop_loss_validator.validate(trade)
            if result == ValidationResult.FAIL:
                errors.append(error)
                logger.error(f"❌ Stop Loss validation FAILED: {error.message}")
        
            # 2. Take Profit validation
            result, error = self.take_profit_validator.validate(trade)
            if result == ValidationResult.FAIL:
                errors.append(error)
                logger.error(f"❌ Take Profit validation FAILED: {error.message}")
            elif result == ValidationResult.WARNING:
                logger.warning(f"⚠️  Take Profit warning: {error.message}")
        
            # 3. Position Sizing validation
            result, error = self.position_sizing_validator.validate(trade, account)
            if result == ValidationResult.FAIL:
                errors.append(error)
                logger.error(f"❌ Position Sizing validation FAILED: {error.message}")
        
            # 4. Drawdown Protection validation
            result, error = self.drawdown_validator.validate(account)
            if result == ValidationResult.FAIL:
                errors.append(error)
                logger.critical(f"🚨 Drawdown Protection FAILED: {error.message}")
            elif result == ValidationResult.WARNING:
                logger.warning(f"⚠️  Drawdown warning: {error.message}")
        
            # 5. Daily Loss Limit validation
            result, error = self.daily_loss_validator.validate(account)
            if result == ValidationResult.FAIL:
                errors.append(error)
                logger.critical(f"🚨 Daily Loss Limit FAILED: {error.message}")
        
            # 6. Margin validation
            result, error = self.margin_validator.validate(trade, account)
            if result == ValidationResult.FAIL:
                errors.append(error)
                logger.error(f"❌ Margin validation FAILED: {error.message}")
        
            # All validations must pass
            all_passed = len(errors) == 0
        
            if all_passed:
                logger.info("✅ All critical validations PASSED")
            else:
                logger.error(f"❌ {len(errors)} critical validation(s) FAILED")
        
            return all_passed, errors
        except Exception as e:
            logger.error(f"Error in validate_trade: {e}")
            raise


if __name__ == '__main__':
    # Example usage
    validator = CriticalValidatorSuite({
        'max_risk_percent': 2.0,
        'min_risk_reward': 1.5,
        'max_drawdown_percent': 20.0,
        'max_daily_loss_percent': 5.0
    })
    
    # Test trade
    trade = {
        'direction': 'BUY',
        'entry_price': 1.1000,
        'stop_loss': 1.0950,  # 50 pips = 0.45%
        'take_profit': 1.1100,  # 100 pips = 0.91%
        'position_size': 0.1,
        'leverage': 10
    }
    
    # Test account
    account = {
        'balance': 10000,
        'equity': 10000,
        'starting_balance': 10000,
        'used_margin': 0,
        'free_margin': 10000,
        'open_positions': []
    }
    
    # Validate
    passed, errors = validator.validate_trade(trade, account)
    
    if not passed:
        logger.info("\n❌ VALIDATION FAILED:")
        for error in errors:
            logger.info(f"\n{error.validator}:")
            logger.info(f"  Message: {error.message}")
            logger.info(f"  Severity: {error.severity}")
            logger.info(f"  Details: {error.details}")
    else:
        logger.info("\n✅ ALL VALIDATIONS PASSED - Trade approved")

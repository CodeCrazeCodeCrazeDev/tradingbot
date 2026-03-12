import logging
"""
Comprehensive trade parameter validation to prevent catastrophic losses.
Validates all trade parameters before execution.
"""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np
from loguru import logger
logger = logging.getLogger(__name__)


@dataclass
class ValidationRules:
    """Trade validation rules configuration."""
    max_lot_size: float = 1.0
    min_lot_size: float = 0.01
    max_stop_loss_pct: float = 0.10  # 10%
    min_stop_loss_pct: float = 0.001  # 0.1%
    max_take_profit_pct: float = 0.50  # 50%
    min_risk_reward: float = 1.0
    max_risk_per_trade_pct: float = 0.02  # 2%
    max_total_exposure_pct: float = 0.15  # 15%
    allowed_symbols: Optional[List[str]] = None
    max_price_deviation_pct: float = 0.05  # 5% from market
    min_margin_level: float = 200.0  # 200%


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


class TradeValidator:
    """Comprehensive trade parameter validation."""
    
    def __init__(self, rules: ValidationRules = None):
        try:
            self.rules = rules or ValidationRules()
            self.validation_history = []
            logger.info("TradeValidator initialized with comprehensive rules")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate_trade(self, symbol: str, lot: float, price: float, 
                      sl: float, tp: float, account_equity: float,
                      current_market_price: float = None) -> bool:
        """
        Validate all trade parameters comprehensively.
        
        Args:
            symbol: Trading symbol
            lot: Lot size
            price: Entry price
            sl: Stop loss price
            tp: Take profit price
            account_equity: Current account equity
            current_market_price: Current market price for deviation check
            
        Returns:
            True if validation passes
            
        Raises:
            ValidationError: If any validation fails
        """
        try:
            errors = []
        
            # Symbol validation
            if self.rules.allowed_symbols and symbol not in self.rules.allowed_symbols:
                errors.append(f"Symbol '{symbol}' not in allowed list: {self.rules.allowed_symbols}")
        
            # Lot size validation
            if lot <= 0:
                errors.append(f"Lot size must be positive: {lot}")
            elif lot < self.rules.min_lot_size:
                errors.append(f"Lot size {lot} below minimum {self.rules.min_lot_size}")
            elif lot > self.rules.max_lot_size:
                errors.append(f"Lot size {lot} exceeds maximum {self.rules.max_lot_size}")
        
            # Price validation
            if price <= 0:
                errors.append(f"Price must be positive: {price}")
        
            # Market price deviation check
            if current_market_price and current_market_price > 0:
                deviation = abs(price - current_market_price) / current_market_price
                if deviation > self.rules.max_price_deviation_pct:
                    errors.append(
                        f"Entry price {price} deviates {deviation:.2%} from market {current_market_price} "
                        f"(max: {self.rules.max_price_deviation_pct:.2%})"
                    )
        
            # Stop loss validation
            if sl <= 0:
                errors.append(f"Stop loss must be positive: {sl}")
            else:
                sl_distance_pct = abs(price - sl) / price
            
                if sl_distance_pct < self.rules.min_stop_loss_pct:
                    errors.append(
                        f"Stop loss too tight: {sl_distance_pct:.3%} "
                        f"(min: {self.rules.min_stop_loss_pct:.3%})"
                    )
                elif sl_distance_pct > self.rules.max_stop_loss_pct:
                    errors.append(
                        f"Stop loss too wide: {sl_distance_pct:.2%} "
                        f"(max: {self.rules.max_stop_loss_pct:.2%})"
                    )
            
                # Check SL direction
                direction = "long" if tp > price else "short"
                if direction == "long" and sl >= price:
                    errors.append(f"Long trade: stop loss {sl} must be below entry {price}")
                elif direction == "short" and sl <= price:
                    errors.append(f"Short trade: stop loss {sl} must be above entry {price}")
        
            # Take profit validation
            if tp <= 0:
                errors.append(f"Take profit must be positive: {tp}")
            else:
                tp_distance_pct = abs(tp - price) / price
            
                if tp_distance_pct > self.rules.max_take_profit_pct:
                    errors.append(
                        f"Take profit too far: {tp_distance_pct:.2%} "
                        f"(max: {self.rules.max_take_profit_pct:.2%})"
                    )
            
                # Check TP direction
                direction = "long" if tp > price else "short"
                if direction == "long" and tp <= price:
                    errors.append(f"Long trade: take profit {tp} must be above entry {price}")
                elif direction == "short" and tp >= price:
                    errors.append(f"Short trade: take profit {tp} must be below entry {price}")
        
            # Risk-reward validation
            if sl > 0 and tp > 0:
                risk = abs(price - sl)
                reward = abs(tp - price)
            
                if risk > 0:
                    rr_ratio = reward / risk
                    if rr_ratio < self.rules.min_risk_reward:
                        errors.append(
                            f"Poor risk-reward ratio: {rr_ratio:.2f} "
                            f"(min: {self.rules.min_risk_reward:.2f})"
                        )
        
            # Risk per trade validation
            if account_equity > 0:
                # Assuming forex: 1 lot = 100,000 units
                contract_size = 100000
                pip_value = 10  # Simplified for major pairs
                risk_pips = abs(price - sl) * 10000  # Convert to pips
                risk_usd = lot * risk_pips * pip_value
                risk_pct = (risk_usd / account_equity) * 100
            
                if risk_pct > self.rules.max_risk_per_trade_pct * 100:
                    errors.append(
                        f"Risk per trade {risk_pct:.2f}% exceeds maximum "
                        f"{self.rules.max_risk_per_trade_pct * 100:.2f}%"
                    )
        
            # Log validation attempt
            validation_result = {
                'symbol': symbol,
                'lot': lot,
                'price': price,
                'sl': sl,
                'tp': tp,
                'passed': len(errors) == 0,
                'errors': errors
            }
            self.validation_history.append(validation_result)
        
            # Raise exception if validation failed
            if errors:
                error_msg = f"Trade validation failed for {symbol}: " + "; ".join(errors)
                logger.error(error_msg)
                raise ValidationError(error_msg)
        
            logger.info(f"Trade validation passed for {symbol}: {lot} lots @ {price}")
            return True
        except Exception as e:
            logger.error(f"Error in validate_trade: {e}")
            raise
    
    def validate_portfolio_exposure(self, new_trade_value: float, 
                                   current_exposure: float, 
                                   account_equity: float) -> bool:
        """Validate total portfolio exposure."""
        try:
            total_exposure = current_exposure + new_trade_value
            exposure_pct = (total_exposure / account_equity) * 100
        
            if exposure_pct > self.rules.max_total_exposure_pct * 100:
                raise ValidationError(
                    f"Total exposure {exposure_pct:.2f}% would exceed maximum "
                    f"{self.rules.max_total_exposure_pct * 100:.2f}%"
                )
        
            return True
        except Exception as e:
            logger.error(f"Error in validate_portfolio_exposure: {e}")
            raise
    
    def validate_margin_level(self, margin_level: float) -> bool:
        """Validate margin level is sufficient."""
        try:
            if margin_level < self.rules.min_margin_level:
                raise ValidationError(
                    f"Margin level {margin_level:.2f}% below minimum "
                    f"{self.rules.min_margin_level:.2f}%"
                )
            return True
        except Exception as e:
            logger.error(f"Error in validate_margin_level: {e}")
            raise
    
    def get_validation_stats(self) -> dict:
        """Get validation statistics."""
        try:
            if not self.validation_history:
                return {'total': 0, 'passed': 0, 'failed': 0, 'pass_rate': 0}
        
            total = len(self.validation_history)
            passed = sum(1 for v in self.validation_history if v['passed'])
            failed = total - passed
        
            return {
                'total': total,
                'passed': passed,
                'failed': failed,
                'pass_rate': (passed / total) * 100 if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error in get_validation_stats: {e}")
            raise
    
    def reset_history(self):
        """Reset validation history."""
        try:
            self.validation_history = []
            logger.info("Validation history reset")
        except Exception as e:
            logger.error(f"Error in reset_history: {e}")
            raise


class OrderSafetyCheck:
    """Additional safety checks for order execution."""
    
    @staticmethod
    def check_duplicate_order(new_order: dict, recent_orders: List[dict], 
                             time_window: float = 1.0) -> bool:
        """Check for duplicate orders within time window."""
        try:
            import time
            current_time = time.time()
        
            for order in recent_orders:
                if (current_time - order.get('timestamp', 0) < time_window and
                    order.get('symbol') == new_order.get('symbol') and
                    order.get('lot') == new_order.get('lot')):
                    raise ValidationError(
                        f"Duplicate order detected for {new_order.get('symbol')} "
                        f"within {time_window}s window"
                    )
            return True
        except Exception as e:
            logger.error(f"Error in check_duplicate_order: {e}")
            raise
    
    @staticmethod
    def check_flash_crash_protection(current_price: float, 
                                     historical_prices: List[float],
                                     threshold: float = 0.05) -> bool:
        """Prevent trading during flash crashes."""
        try:
            if len(historical_prices) < 10:
                return True
        
            avg_price = np.mean(historical_prices[-10:])
            deviation = abs(current_price - avg_price) / avg_price
        
            if deviation > threshold:
                raise ValidationError(
                    f"Flash crash protection triggered: price deviation {deviation:.2%} "
                    f"exceeds threshold {threshold:.2%}"
                )
            return True
        except Exception as e:
            logger.error(f"Error in check_flash_crash_protection: {e}")
            raise
    
    @staticmethod
    def check_circuit_breaker(volatility: float, max_volatility: float = 0.10) -> bool:
        """Circuit breaker for extreme volatility."""
        try:
            if volatility > max_volatility:
                raise ValidationError(
                    f"Circuit breaker triggered: volatility {volatility:.2%} "
                    f"exceeds maximum {max_volatility:.2%}"
                )
            return True
        except Exception as e:
            logger.error(f"Error in check_circuit_breaker: {e}")
            raise

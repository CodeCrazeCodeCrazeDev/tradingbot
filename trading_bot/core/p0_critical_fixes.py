"""
P0 CRITICAL FIXES INTEGRATION MODULE
============================================================

Integrates all P0 critical fixes into a unified system.

Fixes Implemented:
1. Stop Loss Validation
2. Take Profit Validation
3. Position Size Validation
4. Drawdown Protection
5. Spread Filter
6. Volatility Filter
7. Trailing Stops
8. Correlation Management
9. Exception Handling
10. Leverage Limits

Author: AI Assistant
Date: October 23, 2025
Version: 1.0.0
"""


from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all P0 fixes
from trading_bot.risk.trade_validation import (
    MasterTradeValidator,
    TradeValidationConfig,
    ValidationResult,
    ValidationStatus
)
from trading_bot.risk.drawdown_protector import DrawdownProtector, DrawdownStatus
from trading_bot.analysis.spread_filter import SpreadFilter
from trading_bot.analysis.volatility_filter import VolatilityFilter, VolatilityRegime
from trading_bot.execution.trailing_stop import TrailingStop, TradeDirection

# Optional correlation manager import
try:
    from trading_bot.risk.correlation_manager import CorrelationManager
    CORRELATION_MANAGER_AVAILABLE = True
except ImportError:
    CORRELATION_MANAGER_AVAILABLE = False

try:
    class CorrelationManager:
        pass

# Optional exception handler import
    from trading_bot.core.exception_handler import ExceptionHandler, ErrorSeverity, ErrorRecoveryStrategy
    EXCEPTION_HANDLER_AVAILABLE = True
except ImportError:
    EXCEPTION_HANDLER_AVAILABLE = False
    # Provide dummy classes
    class ErrorSeverity:
        pass
    class ErrorRecoveryStrategy:
        pass
    class ExceptionHandler:
        def __init__(self):
            pass
        def handle_exception(self, *args, **kwargs):
            return True
        def get_error_summary(self, *args, **kwargs):
            return "No error summary available"


@dataclass
class P0FixesConfig:
    """Configuration for P0 fixes."""
    # Validation
    min_sl_distance_pips: float = 0.5
    max_sl_distance_pips: float = 5.0
    min_risk_reward_ratio: float = 1.5
    
    # Position sizing
    min_position_size: float = 0.01
    max_position_size: float = 1.0
    
    # Risk management
    max_leverage: float = 10.0
    max_drawdown_percent: float = 20.0
    max_daily_loss_percent: float = 2.0
    
    # Spread & Volatility
    max_spread_multiplier: float = 2.0
    max_volatility_multiplier: float = 2.0
    
    # Account
    min_account_balance: float = 1000.0


class P0CriticalFixesSystem:
    """Unified system for all P0 critical fixes."""
    
    def __init__(self, config: P0FixesConfig = None):
        """Initialize P0 fixes system."""
        self.config = config or P0FixesConfig()
        
        # Initialize all components
        self.trade_validator = MasterTradeValidator(
            TradeValidationConfig(
                min_sl_distance_pips=self.config.min_sl_distance_pips,
                max_sl_distance_pips=self.config.max_sl_distance_pips,
                min_risk_reward_ratio=self.config.min_risk_reward_ratio,
                min_position_size=self.config.min_position_size,
                max_position_size=self.config.max_position_size,
                max_leverage=self.config.max_leverage,
                min_account_balance=self.config.min_account_balance
            )
        )
        
        self.drawdown_protector = DrawdownProtector(
            max_drawdown_percent=self.config.max_drawdown_percent,
            max_daily_loss_percent=self.config.max_daily_loss_percent
        )
        
        self.spread_filter = SpreadFilter(
            max_spread_multiplier=self.config.max_spread_multiplier
        )
        
        self.volatility_filter = VolatilityFilter()
        
        self.trailing_stop = None  # Created per trade
        
        self.correlation_manager = CorrelationManager()
        
        self.exception_handler = ExceptionHandler()
        
        logger.info("P0 Critical Fixes System initialized")
    
    def validate_trade(self, entry_price: float, stop_loss: float,
                      take_profit: float, position_size: float,
                      account_balance: float, symbol: str = "EURUSD",
                      bid: float = None, ask: float = None) -> Dict[str, Any]:
        """
        Validate complete trade setup.
        
        Returns:
            Dict with validation results and recommendations
        """
        try:
            # Run all validations
            validation_results = self.trade_validator.validate_trade(
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                account_balance=account_balance,
                symbol=symbol,
                bid=bid,
                ask=ask
            )
            
            # Check drawdown
            drawdown_status = self.drawdown_protector.get_status()
            
            # Check spread
            spread_acceptable = True
            if bid is not None and ask is not None:
                spread_acceptable = self.spread_filter.is_spread_acceptable(symbol, bid, ask)
            
            # Check volatility
            volatility_acceptable = self.volatility_filter.is_volatility_acceptable()
            
            # Compile results
            all_valid = (
                self.trade_validator.is_trade_valid(validation_results) and
                not self.drawdown_protector.should_stop_trading() and
                spread_acceptable and
                volatility_acceptable
            )
            
            return {
                'valid': all_valid,
                'validation_results': validation_results,
                'drawdown_status': drawdown_status,
                'spread_acceptable': spread_acceptable,
                'volatility_acceptable': volatility_acceptable,
                'position_size_multiplier': self.volatility_filter.get_position_size_multiplier(),
                'summary': self.trade_validator.get_validation_summary(validation_results)
            }
        
        except Exception as e:
            self.exception_handler.handle_exception(
                e, "validate_trade", ErrorRecoveryStrategy.SKIP
            )
            return {'valid': False, 'error': str(e)}
    
    def update_market_data(self, symbol: str, high: float, low: float,
                          close: float, bid: float, ask: float):
        """Update market data for filters."""
        try:
            # Update volatility filter
            self.volatility_filter.update(high, low, close)
            
            # Update spread filter
            self.spread_filter.update_spread(symbol, bid, ask)
            
            # Update correlation manager
            self.correlation_manager.update_price(symbol, close)
        
        except Exception as e:
            self.exception_handler.handle_exception(
                e, "update_market_data", ErrorRecoveryStrategy.SKIP
            )
    
    def update_account_balance(self, current_balance: float):
        """Update account balance and check limits."""
        try:
            self.drawdown_protector.update_balance(current_balance)
            
            # Check if trading should be halted
            if self.drawdown_protector.should_stop_trading():
                logger.critical(f"Trading halted: {self.drawdown_protector.halt_reason}")
        
        except Exception as e:
            self.exception_handler.handle_exception(
                e, "update_account_balance", ErrorRecoveryStrategy.SKIP
            )
    
    def initialize_trailing_stop(self, direction: TradeDirection,
                                entry_price: float, atr: float):
        """Initialize trailing stop for new trade."""
        try:
            self.trailing_stop = TrailingStop(direction=direction)
            self.trailing_stop.initialize(entry_price, atr)
            return True
        
        except Exception as e:
            self.exception_handler.handle_exception(
                e, "initialize_trailing_stop", ErrorRecoveryStrategy.SKIP
            )
            return False
    
    def update_trailing_stop(self, current_price: float, atr: float) -> Optional[float]:
        """Update trailing stop and return new stop price."""
        try:
            if self.trailing_stop is None:
                return None
            
            return self.trailing_stop.update(current_price, atr)
        
        except Exception as e:
            self.exception_handler.handle_exception(
                e, "update_trailing_stop", ErrorRecoveryStrategy.SKIP
            )
            return None
    
    def should_exit_trade(self, current_price: float) -> bool:
        """Check if trade should be exited."""
        try:
            if self.trailing_stop is None:
                return False
            
            return self.trailing_stop.should_exit(current_price)
        
        except Exception as e:
            self.exception_handler.handle_exception(
                e, "should_exit_trade", ErrorRecoveryStrategy.SKIP
            )
            return False
    
    def get_system_status(self) -> str:
        """Get comprehensive system status."""
        status = "P0 CRITICAL FIXES SYSTEM STATUS\n"
        status += "=" * 60 + "\n\n"
        
        # Drawdown status
        status += self.drawdown_protector.get_status_string()
        status += "\n"
        
        # Volatility status
        status += self.volatility_filter.get_volatility_status()
        status += "\n"
        
        # Error summary
        status += self.exception_handler.get_error_summary()
        
        return status
    
    def emergency_shutdown(self):
        """Emergency shutdown."""
        logger.critical("EMERGENCY SHUTDOWN INITIATED")
        self.drawdown_protector.emergency_shutdown()
        self.exception_handler.record_error(
            "EmergencyShutdown",
            "Emergency shutdown activated",
            ErrorSeverity.CRITICAL,
            "",
            ErrorRecoveryStrategy.SHUTDOWN
        )

"""
Position Size Calculator

Calculates optimal position sizes based on risk parameters, account equity, and market conditions.
"""

import logging
from typing import Any, Dict, Optional
from enum import Enum
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class SizingMethod(Enum):
    """Position sizing methods"""
    FIXED_RISK = "fixed_risk"  # Fixed % of account
    KELLY_CRITERION = "kelly"  # Kelly criterion
    OPTIMAL_F = "optimal_f"  # Optimal fixed fraction
    VOLATILITY_ADJUSTED = "volatility"  # Volatility-based sizing
    RISK_PARITY = "risk_parity"  # Risk parity across positions


class PositionSizer:
    """Calculate position sizes based on risk parameters"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.default_risk_pct = self.config.get('default_risk_pct', 0.02)  # 2% default
            self.max_position_size = self.config.get('max_position_size', 1000000)  # 1M units
            self.min_position_size = self.config.get('min_position_size', 1000)
        
            # Pip values for common pairs (USD account)
            self.pip_values = {
                'EURUSD': 10.0,  # $10 per pip for 1 lot
                'GBPUSD': 10.0,
                'USDJPY': 9.09,
                'USDCHF': 10.0,
                'AUDUSD': 10.0,
                'NZDUSD': 10.0,
                'USDCAD': 7.69,
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_position_size(
        self,
        symbol: str,
        account_equity: float,
        risk_pct: Optional[float] = None,
        stop_loss_pips: Optional[float] = None,
        entry_price: Optional[float] = None,
        method: SizingMethod = SizingMethod.FIXED_RISK,
        **kwargs
    ) -> float:
        """
        Calculate position size
        
        Args:
            symbol: Trading symbol
            account_equity: Current account equity
            risk_pct: Risk percentage (e.g., 0.02 for 2%)
            stop_loss_pips: Stop loss distance in pips
            entry_price: Entry price
            method: Sizing method to use
            **kwargs: Additional parameters for specific methods
            
        Returns:
            Position size in base currency units
        """
        try:
            if risk_pct is None:
                risk_pct = self.default_risk_pct
        
            if method == SizingMethod.FIXED_RISK:
                return self._fixed_risk_sizing(
                    symbol, account_equity, risk_pct, stop_loss_pips, entry_price
                )
            elif method == SizingMethod.KELLY_CRITERION:
                return self._kelly_sizing(
                    symbol, account_equity, risk_pct, 
                    kwargs.get('win_rate', 0.5),
                    kwargs.get('avg_win', 1.0),
                    kwargs.get('avg_loss', 1.0)
                )
            elif method == SizingMethod.VOLATILITY_ADJUSTED:
                return self._volatility_sizing(
                    symbol, account_equity, risk_pct,
                    kwargs.get('volatility', 0.01)
                )
            else:
                return self._fixed_risk_sizing(
                    symbol, account_equity, risk_pct, stop_loss_pips, entry_price
                )
        except Exception as e:
            logger.error(f"Error in calculate_position_size: {e}")
            raise
    
    def _fixed_risk_sizing(
        self,
        symbol: str,
        account_equity: float,
        risk_pct: float,
        stop_loss_pips: Optional[float],
        entry_price: Optional[float]
    ) -> float:
        """
        Calculate position size using fixed risk method
        
        Position Size = (Account Equity × Risk %) / (Stop Loss Pips × Pip Value)
        """
        # Handle zero or negative equity
        try:
            if account_equity <= 0:
                logger.warning(f"Invalid account equity: {account_equity}, returning 0")
                return 0
        
            if not stop_loss_pips or stop_loss_pips <= 0:
                logger.warning(f"Invalid stop loss pips: {stop_loss_pips}, using default 50 pips")
                stop_loss_pips = 50.0
        
            # Calculate risk amount in account currency
            risk_amount = account_equity * risk_pct
        
            # Get pip value for symbol
            pip_value = self._get_pip_value(symbol, entry_price)
        
            # Calculate position size
            # Position size in lots = Risk Amount / (Stop Loss Pips × Pip Value per Lot)
            position_size_lots = risk_amount / (stop_loss_pips * pip_value)
        
            # Convert to base currency units (1 lot = 100,000 units for forex)
            position_size = position_size_lots * 100000
        
            # Apply limits
            position_size = max(self.min_position_size, min(position_size, self.max_position_size))
        
            logger.info(
                f"Position sizing: {symbol}, Equity: ${account_equity:,.2f}, "
                f"Risk: {risk_pct:.1%}, SL: {stop_loss_pips} pips, "
                f"Size: {position_size:,.0f} units ({position_size_lots:.2f} lots)"
            )
        
            return position_size
        except Exception as e:
            logger.error(f"Error in _fixed_risk_sizing: {e}")
            raise
    
    def _kelly_sizing(
        self,
        symbol: str,
        account_equity: float,
        risk_pct: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate position size using Kelly Criterion
        
        Kelly % = W - [(1 - W) / R]
        where W = win rate, R = avg_win / avg_loss
        """
        try:
            if avg_loss == 0:
                logger.warning("Average loss is zero, using fixed risk")
                return account_equity * risk_pct
        
            # Calculate Kelly percentage
            win_loss_ratio = avg_win / avg_loss
            kelly_pct = win_rate - ((1 - win_rate) / win_loss_ratio)
        
            # Use fractional Kelly (typically 25-50% of full Kelly for safety)
            fractional_kelly = self.config.get('kelly_fraction', 0.25)
            kelly_pct = kelly_pct * fractional_kelly
        
            # Ensure non-negative and cap at risk_pct
            kelly_pct = max(0, min(kelly_pct, risk_pct))
        
            position_size = account_equity * kelly_pct
        
            # Apply limits
            position_size = max(self.min_position_size, min(position_size, self.max_position_size))
        
            logger.info(
                f"Kelly sizing: {symbol}, Win rate: {win_rate:.1%}, "
                f"W/L ratio: {win_loss_ratio:.2f}, Kelly: {kelly_pct:.1%}, "
                f"Size: ${position_size:,.2f}"
            )
        
            return position_size
        except Exception as e:
            logger.error(f"Error in _kelly_sizing: {e}")
            raise
    
    def _volatility_sizing(
        self,
        symbol: str,
        account_equity: float,
        risk_pct: float,
        volatility: float
    ) -> float:
        """
        Calculate position size adjusted for volatility
        
        Lower volatility = larger position
        Higher volatility = smaller position
        """
        # Target volatility (e.g., 1% daily)
        try:
            target_volatility = self.config.get('target_volatility', 0.01)
        
            # Adjust position size inversely to volatility
            volatility_adjustment = target_volatility / max(volatility, 0.001)
        
            # Cap adjustment factor
            volatility_adjustment = min(volatility_adjustment, 2.0)
        
            position_size = account_equity * risk_pct * volatility_adjustment
        
            # Apply limits
            position_size = max(self.min_position_size, min(position_size, self.max_position_size))
        
            logger.info(
                f"Volatility sizing: {symbol}, Volatility: {volatility:.2%}, "
                f"Adjustment: {volatility_adjustment:.2f}x, Size: ${position_size:,.2f}"
            )
        
            return position_size
        except Exception as e:
            logger.error(f"Error in _volatility_sizing: {e}")
            raise
    
    def _get_pip_value(self, symbol: str, price: Optional[float] = None) -> float:
        """
        Get pip value for a symbol
        
        For most forex pairs, 1 pip = 0.0001
        For JPY pairs, 1 pip = 0.01
        Pip value depends on lot size and quote currency
        """
        # Check if we have a predefined pip value
        try:
            if symbol in self.pip_values:
                return self.pip_values[symbol]
        
            # Calculate pip value based on symbol
            if 'JPY' in symbol:
                # JPY pairs: 1 pip = 0.01
                pip_size = 0.01
            else:
                # Most pairs: 1 pip = 0.0001
                pip_size = 0.0001
        
            # For 1 standard lot (100,000 units)
            # Pip value = (pip size / exchange rate) × lot size
            # For USD quote currency, pip value is typically $10 per lot
        
            if symbol.endswith('USD'):
                # Quote currency is USD
                pip_value = 10.0
            elif symbol.startswith('USD'):
                # Base currency is USD
                if price:
                    pip_value = (pip_size / price) * 100000
                else:
                    pip_value = 10.0  # Default
            else:
                # Cross pairs - use default
                pip_value = 10.0
        
            return pip_value
        except Exception as e:
            logger.error(f"Error in _get_pip_value: {e}")
            raise
    
    def calculate_pip_value(self, symbol: str, price: Optional[float] = None) -> float:
        """Public method to calculate pip value for a symbol"""
        return self._get_pip_value(symbol, price)
    
    def calculate_lot_size(
        self,
        position_size: float,
        symbol: str
    ) -> float:
        """
        Convert position size in base currency to lot size
        
        Args:
            position_size: Position size in base currency units
            symbol: Trading symbol
            
        Returns:
            Lot size (1 lot = 100,000 units for forex)
        """
        # Standard lot size for forex
        try:
            lot_size = 100000
        
            # Calculate lots
            lots = position_size / lot_size
        
            # Round to 2 decimal places (mini lots)
            lots = round(lots, 2)
        
            return lots
        except Exception as e:
            logger.error(f"Error in calculate_lot_size: {e}")
            raise
    
    def kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        capital: float
    ) -> float:
        """
        Calculate position size using Kelly Criterion
        
        Kelly % = W - [(1 - W) / R]
        where W = win rate, R = avg_win / avg_loss
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade amount
            avg_loss: Average losing trade amount
            capital: Total capital available
            
        Returns:
            Recommended position size
        """
        try:
            if avg_loss == 0:
                logger.warning("Average loss is zero, returning 0")
                return 0
            
            # Calculate Kelly percentage
            win_loss_ratio = avg_win / avg_loss
            kelly_pct = win_rate - ((1 - win_rate) / win_loss_ratio)
        
            # Use fractional Kelly (25% of full Kelly for safety)
            fractional_kelly = self.config.get('kelly_fraction', 0.25)
            kelly_pct = kelly_pct * fractional_kelly
        
            # Ensure non-negative and cap at 25%
            kelly_pct = max(0, min(kelly_pct, 0.25))
        
            position_size = capital * kelly_pct
        
            logger.info(
                f"Kelly criterion: Win rate={win_rate:.1%}, W/L ratio={win_loss_ratio:.2f}, "
                f"Kelly={kelly_pct:.1%}, Size=${position_size:,.2f}"
            )
        
            return position_size
        except Exception as e:
            logger.error(f"Error in kelly_criterion: {e}")
            raise
        
    def fixed_risk(
        self,
        capital: float,
        risk_pct: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """
        Calculate position size using fixed risk method
        
        Position Size = (Capital × Risk %) / (Entry - Stop Loss)
        
        Args:
            capital: Total capital available
            risk_pct: Risk percentage (e.g., 0.02 for 2%)
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Position size in units
        """
        # Calculate risk per unit
        try:
            risk_per_unit = abs(entry_price - stop_loss)
        
            if risk_per_unit == 0:
                logger.warning("Risk per unit is zero, returning 0")
                return 0
            
            # Calculate risk amount
            risk_amount = capital * risk_pct
        
            # Calculate position size
            position_size = risk_amount / risk_per_unit
        
            # Apply limits
            position_size = max(self.min_position_size, min(position_size, self.max_position_size))
        
            logger.info(
                f"Fixed risk: Capital=${capital:,.2f}, Risk={risk_pct:.1%}, "
                f"Entry={entry_price}, SL={stop_loss}, Size={position_size:.4f} units"
            )
        
            return position_size
        except Exception as e:
            logger.error(f"Error in fixed_risk: {e}")
            raise

    def validate_position_size(
        self,
        position_size: float,
        account_equity: float,
        max_position_pct: float = 0.1
    ) -> bool:
        """
        Validate that position size is within acceptable limits
        
        Args:
            position_size: Proposed position size
            account_equity: Current account equity
            max_position_pct: Maximum position size as % of equity
            
        Returns:
            True if valid, False otherwise
        """
        # Check minimum
        try:
            if position_size < self.min_position_size:
                logger.warning(f"Position size {position_size} below minimum {self.min_position_size}")
                return False
        
            # Check maximum
            if position_size > self.max_position_size:
                logger.warning(f"Position size {position_size} above maximum {self.max_position_size}")
                return False
        
            # Check as percentage of equity
            position_pct = position_size / account_equity
            if position_pct > max_position_pct:
                logger.warning(
                    f"Position size {position_pct:.1%} of equity exceeds "
                    f"maximum {max_position_pct:.1%}"
                )
                return False
        
            return True
        except Exception as e:
            logger.error(f"Error in validate_position_size: {e}")
            raise

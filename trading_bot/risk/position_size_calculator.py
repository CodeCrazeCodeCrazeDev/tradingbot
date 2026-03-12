"""
Position Size Calculator

Converts risk percentage to actual position size in lots/contracts.
"""

import logging
from typing import Any, Dict, Optional
from enum import Enum
from typing import Set

logger = logging.getLogger(__name__)


class PositionSizeMethod(Enum):
    """Position sizing methods"""
    FIXED_RISK = "fixed_risk"  # Risk fixed % per trade
    KELLY_CRITERION = "kelly"  # Kelly criterion
    RISK_PARITY = "risk_parity"  # Risk parity
    VOLATILITY_ADJUSTED = "volatility"  # Volatility-based
    OPTIMAL_F = "optimal_f"  # Optimal f


class PositionSizeCalculator:
    """
    Calculate position sizes based on risk parameters
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Default parameters
            self.default_risk_pct = self.config.get('default_risk_pct', 0.01)  # 1%
            self.min_position_size = self.config.get('min_position_size', 0.01)
            self.max_position_size = self.config.get('max_position_size', 100.0)
        
            # Symbol specifications (can be loaded from broker)
            self.symbol_specs = self.config.get('symbol_specs', {})
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_position_size(
        self,
        symbol: str,
        account_equity: float,
        risk_pct: Optional[float] = None,
        stop_loss_pips: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        entry_price: Optional[float] = None,
        method: PositionSizeMethod = PositionSizeMethod.FIXED_RISK
    ) -> float:
        """
        Calculate position size
        
        Args:
            symbol: Trading symbol
            account_equity: Account equity
            risk_pct: Risk percentage (e.g., 0.01 for 1%)
            stop_loss_pips: Stop loss in pips
            stop_loss_price: Stop loss price level
            entry_price: Entry price
            method: Position sizing method
        
        Returns:
            Position size in lots
        """
        try:
            risk_pct = risk_pct or self.default_risk_pct
        
            if method == PositionSizeMethod.FIXED_RISK:
                return self._fixed_risk_size(
                    symbol, account_equity, risk_pct, 
                    stop_loss_pips, stop_loss_price, entry_price
                )
        
            elif method == PositionSizeMethod.KELLY_CRITERION:
                return self._kelly_size(symbol, account_equity, risk_pct)
        
            elif method == PositionSizeMethod.RISK_PARITY:
                return self._risk_parity_size(symbol, account_equity, risk_pct)
        
            elif method == PositionSizeMethod.VOLATILITY_ADJUSTED:
                return self._volatility_adjusted_size(symbol, account_equity, risk_pct)
        
            else:
                logger.warning(f"Unknown method {method}, using fixed risk")
                return self._fixed_risk_size(
                    symbol, account_equity, risk_pct,
                    stop_loss_pips, stop_loss_price, entry_price
                )
        except Exception as e:
            logger.error(f"Error in calculate_position_size: {e}")
            raise
    
    def _fixed_risk_size(
        self,
        symbol: str,
        account_equity: float,
        risk_pct: float,
        stop_loss_pips: Optional[float],
        stop_loss_price: Optional[float],
        entry_price: Optional[float]
    ) -> float:
        """
        Calculate position size using fixed risk method
        
        Formula: Position Size = (Account Equity * Risk %) / (Stop Loss in Pips * Pip Value)
        """
        # Calculate risk amount in currency
        try:
            risk_amount = account_equity * risk_pct
        
            # Get pip value
            pip_value = self._get_pip_value(symbol)
        
            # Calculate stop loss in pips if not provided
            if stop_loss_pips is None:
                if stop_loss_price and entry_price:
                    stop_loss_pips = abs(entry_price - stop_loss_price) / self._get_pip_size(symbol)
                else:
                    # Use default stop loss
                    stop_loss_pips = self.config.get('default_stop_loss_pips', 50)
                    logger.warning(f"No stop loss provided, using default {stop_loss_pips} pips")
        
            # Calculate position size
            # risk_amount = position_size * stop_loss_pips * pip_value
            position_size = risk_amount / (stop_loss_pips * pip_value)
        
            # Apply limits
            position_size = max(self.min_position_size, min(position_size, self.max_position_size))
        
            # Round to valid lot size
            position_size = self._round_to_lot_size(symbol, position_size)
        
            logger.info(
                f"Position size for {symbol}: {position_size:.2f} lots "
                f"(risk: {risk_pct*100:.1f}%, SL: {stop_loss_pips:.1f} pips, "
                f"risk amount: ${risk_amount:.2f})"
            )
        
            return position_size
        except Exception as e:
            logger.error(f"Error in _fixed_risk_size: {e}")
            raise
    
    def _kelly_size(
        self,
        symbol: str,
        account_equity: float,
        risk_pct: float
    ) -> float:
        """
        Calculate position size using Kelly Criterion
        
        Kelly % = (Win Rate * Avg Win - Loss Rate * Avg Loss) / Avg Win
        """
        # Get historical performance (would come from performance tracker)
        try:
            win_rate = self.config.get('win_rate', 0.55)
            avg_win = self.config.get('avg_win', 100)
            avg_loss = self.config.get('avg_loss', 50)
        
            # Calculate Kelly percentage
            kelly_pct = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        
            # Use fractional Kelly (typically 0.25 to 0.5 of full Kelly)
            fractional_kelly = kelly_pct * self.config.get('kelly_fraction', 0.25)
        
            # Don't exceed max risk
            kelly_pct = min(fractional_kelly, risk_pct)
        
            # Calculate position size
            position_size = (account_equity * kelly_pct) / self._get_pip_value(symbol)
        
            # Apply limits
            position_size = max(self.min_position_size, min(position_size, self.max_position_size))
            position_size = self._round_to_lot_size(symbol, position_size)
        
            logger.info(f"Kelly position size for {symbol}: {position_size:.2f} lots (Kelly: {kelly_pct*100:.1f}%)")
        
            return position_size
        except Exception as e:
            logger.error(f"Error in _kelly_size: {e}")
            raise
    
    def _risk_parity_size(
        self,
        symbol: str,
        account_equity: float,
        risk_pct: float
    ) -> float:
        """
        Calculate position size using risk parity
        
        Each position contributes equal risk to portfolio
        """
        # Get symbol volatility (would come from market data)
        try:
            volatility = self.config.get('symbol_volatility', {}).get(symbol, 0.01)
        
            # Calculate position size to equalize risk
            # Higher volatility = smaller position
            position_size = (account_equity * risk_pct) / (volatility * self._get_pip_value(symbol))
        
            # Apply limits
            position_size = max(self.min_position_size, min(position_size, self.max_position_size))
            position_size = self._round_to_lot_size(symbol, position_size)
        
            logger.info(f"Risk parity size for {symbol}: {position_size:.2f} lots (vol: {volatility*100:.2f}%)")
        
            return position_size
        except Exception as e:
            logger.error(f"Error in _risk_parity_size: {e}")
            raise
    
    def _volatility_adjusted_size(
        self,
        symbol: str,
        account_equity: float,
        risk_pct: float
    ) -> float:
        """
        Calculate position size adjusted for volatility
        
        Increases size in low volatility, decreases in high volatility
        """
        # Get current and average volatility
        try:
            current_vol = self.config.get('current_volatility', {}).get(symbol, 0.01)
            avg_vol = self.config.get('avg_volatility', {}).get(symbol, 0.01)
        
            # Calculate volatility ratio
            vol_ratio = avg_vol / current_vol if current_vol > 0 else 1.0
        
            # Adjust risk based on volatility
            adjusted_risk = risk_pct * vol_ratio
        
            # Calculate position size
            position_size = (account_equity * adjusted_risk) / self._get_pip_value(symbol)
        
            # Apply limits
            position_size = max(self.min_position_size, min(position_size, self.max_position_size))
            position_size = self._round_to_lot_size(symbol, position_size)
        
            logger.info(
                f"Volatility adjusted size for {symbol}: {position_size:.2f} lots "
                f"(vol ratio: {vol_ratio:.2f})"
            )
        
            return position_size
        except Exception as e:
            logger.error(f"Error in _volatility_adjusted_size: {e}")
            raise
    
    def _get_pip_value(self, symbol: str) -> float:
        """
        Get pip value for symbol
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Pip value in account currency
        """
        # Check if we have symbol specs
        try:
            if symbol in self.symbol_specs:
                return self.symbol_specs[symbol].get('pip_value', 10.0)
        
            # Default pip values for common forex pairs
            if 'JPY' in symbol:
                return 10.0  # For JPY pairs, 1 pip = 0.01
            else:
                return 10.0  # For other pairs, 1 pip = 0.0001
        except Exception as e:
            logger.error(f"Error in _get_pip_value: {e}")
            raise
    
    def _get_pip_size(self, symbol: str) -> float:
        """
        Get pip size for symbol
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Pip size (e.g., 0.0001 for EUR/USD, 0.01 for USD/JPY)
        """
        try:
            if symbol in self.symbol_specs:
                return self.symbol_specs[symbol].get('pip_size', 0.0001)
        
            if 'JPY' in symbol:
                return 0.01
            else:
                return 0.0001
        except Exception as e:
            logger.error(f"Error in _get_pip_size: {e}")
            raise
    
    def _round_to_lot_size(self, symbol: str, position_size: float) -> float:
        """
        Round position size to valid lot size
        
        Args:
            symbol: Trading symbol
            position_size: Calculated position size
        
        Returns:
            Rounded position size
        """
        # Get lot step (minimum increment)
        try:
            if symbol in self.symbol_specs:
                lot_step = self.symbol_specs[symbol].get('lot_step', 0.01)
            else:
                lot_step = 0.01  # Default to 0.01 lots (micro lots)
        
            # Round to nearest lot step
            rounded_size = round(position_size / lot_step) * lot_step
        
            return rounded_size
        except Exception as e:
            logger.error(f"Error in _round_to_lot_size: {e}")
            raise
    
    def set_symbol_specs(self, symbol: str, specs: Dict[str, Any]):
        """
        Set symbol specifications
        
        Args:
            symbol: Trading symbol
            specs: Symbol specifications (pip_value, pip_size, lot_step, etc.)
        """
        try:
            self.symbol_specs[symbol] = specs
            logger.info(f"Updated specs for {symbol}: {specs}")
        except Exception as e:
            logger.error(f"Error in set_symbol_specs: {e}")
            raise
    
    def calculate_risk_amount(
        self,
        position_size: float,
        symbol: str,
        stop_loss_pips: float
    ) -> float:
        """
        Calculate risk amount for a position
        
        Args:
            position_size: Position size in lots
            symbol: Trading symbol
            stop_loss_pips: Stop loss in pips
        
        Returns:
            Risk amount in account currency
        """
        try:
            pip_value = self._get_pip_value(symbol)
            risk_amount = position_size * stop_loss_pips * pip_value
        
            return risk_amount
        except Exception as e:
            logger.error(f"Error in calculate_risk_amount: {e}")
            raise
    
    def calculate_position_value(
        self,
        position_size: float,
        symbol: str,
        price: float
    ) -> float:
        """
        Calculate total position value
        
        Args:
            position_size: Position size in lots
            symbol: Trading symbol
            price: Current price
        
        Returns:
            Position value in account currency
        """
        # Get contract size (typically 100,000 for standard lot)
        try:
            if symbol in self.symbol_specs:
                contract_size = self.symbol_specs[symbol].get('contract_size', 100000)
            else:
                contract_size = 100000  # Standard lot
        
            position_value = position_size * contract_size * price
        
            return position_value
        except Exception as e:
            logger.error(f"Error in calculate_position_value: {e}")
            raise


# Export
__all__ = [
    'PositionSizeCalculator',
    'PositionSizeMethod'
]

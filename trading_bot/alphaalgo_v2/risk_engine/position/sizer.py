"""
AlphaAlgo V2 Position Sizer

Position sizing algorithms.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum
import math

from ...core.types import Signal, SignalType
from ...core.constants import MAX_RISK_PER_TRADE, MAX_POSITION_SIZE

logger = logging.getLogger(__name__)


class SizingMethod(Enum):
    """Position sizing methods"""
    FIXED = "fixed"
    FIXED_FRACTIONAL = "fixed_fractional"
    KELLY = "kelly"
    VOLATILITY = "volatility"
    ATR = "atr"


@dataclass
class SizingResult:
    """Position sizing result"""
    size: float
    method: SizingMethod
    risk_amount: float
    risk_percent: float
    reasoning: str


class PositionSizer:
    """
    Position sizing calculator
    
    Methods:
    - Fixed: Fixed lot size
    - Fixed Fractional: Risk fixed % of account
    - Kelly: Kelly criterion optimal sizing
    - Volatility: Volatility-adjusted sizing
    - ATR: ATR-based sizing
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Default settings
            self._default_method = SizingMethod(
                self.config.get("default_method", "fixed_fractional")
            )
            self._fixed_size = self.config.get("fixed_size", 0.1)
            self._risk_per_trade = min(
                self.config.get("risk_per_trade", 0.02),
                MAX_RISK_PER_TRADE
            )
            self._max_position_size = min(
                self.config.get("max_position_size", 0.1),
                MAX_POSITION_SIZE
            )
        
            # Kelly settings
            self._kelly_fraction = self.config.get("kelly_fraction", 0.25)  # Quarter Kelly
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(
        self,
        signal: Signal,
        account_balance: float,
        method: Optional[SizingMethod] = None,
        win_rate: float = 0.5,
        avg_win: float = 1.0,
        avg_loss: float = 1.0,
        volatility: float = 1.0
    ) -> SizingResult:
        """
        Calculate position size
        
        Args:
            signal: Trading signal
            account_balance: Current account balance
            method: Sizing method (uses default if not specified)
            win_rate: Historical win rate
            avg_win: Average winning trade
            avg_loss: Average losing trade
            volatility: Current volatility
            
        Returns:
            SizingResult with calculated size
        """
        try:
            method = method or self._default_method
        
            if method == SizingMethod.FIXED:
                return self._fixed_sizing(signal, account_balance)
            elif method == SizingMethod.FIXED_FRACTIONAL:
                return self._fixed_fractional_sizing(signal, account_balance)
            elif method == SizingMethod.KELLY:
                return self._kelly_sizing(
                    signal, account_balance, win_rate, avg_win, avg_loss
                )
            elif method == SizingMethod.VOLATILITY:
                return self._volatility_sizing(signal, account_balance, volatility)
            elif method == SizingMethod.ATR:
                return self._atr_sizing(signal, account_balance)
            else:
                return self._fixed_fractional_sizing(signal, account_balance)
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise
    
    def _fixed_sizing(
        self,
        signal: Signal,
        account_balance: float
    ) -> SizingResult:
        """Fixed lot size"""
        try:
            size = min(self._fixed_size, self._max_position_size * account_balance)
            risk_amount = self._calculate_risk_amount(signal, size)
            risk_percent = risk_amount / account_balance if account_balance > 0 else 0
        
            return SizingResult(
                size=size,
                method=SizingMethod.FIXED,
                risk_amount=risk_amount,
                risk_percent=risk_percent,
                reasoning=f"Fixed size: {size}",
            )
        except Exception as e:
            logger.error(f"Error in _fixed_sizing: {e}")
            raise
    
    def _fixed_fractional_sizing(
        self,
        signal: Signal,
        account_balance: float
    ) -> SizingResult:
        """Fixed fractional (risk fixed % of account)"""
        try:
            risk_amount = account_balance * self._risk_per_trade
        
            # Calculate size based on stop loss distance
            if signal.stop_loss and signal.price:
                stop_distance = abs(signal.price - signal.stop_loss)
                if stop_distance > 0:
                    size = risk_amount / stop_distance
                else:
                    size = self._fixed_size
            else:
                # Default to fixed size if no stop loss
                size = self._fixed_size
        
            # Apply maximum
            max_size = account_balance * self._max_position_size
            size = min(size, max_size)
        
            actual_risk = self._calculate_risk_amount(signal, size)
            risk_percent = actual_risk / account_balance if account_balance > 0 else 0
        
            return SizingResult(
                size=size,
                method=SizingMethod.FIXED_FRACTIONAL,
                risk_amount=actual_risk,
                risk_percent=risk_percent,
                reasoning=f"Risk {self._risk_per_trade:.1%} of account = ${risk_amount:.2f}",
            )
        except Exception as e:
            logger.error(f"Error in _fixed_fractional_sizing: {e}")
            raise
    
    def _kelly_sizing(
        self,
        signal: Signal,
        account_balance: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> SizingResult:
        """Kelly criterion sizing"""
        # Kelly formula: f* = (bp - q) / b
        # where b = avg_win/avg_loss, p = win_rate, q = 1 - p
        
        try:
            if avg_loss == 0:
                avg_loss = 1.0
        
            b = avg_win / avg_loss
            p = win_rate
            q = 1 - p
        
            kelly = (b * p - q) / b if b > 0 else 0
        
            # Apply fraction (quarter Kelly is common)
            kelly = kelly * self._kelly_fraction
        
            # Ensure non-negative and capped
            kelly = max(0, min(kelly, self._max_position_size))
        
            size = account_balance * kelly
            risk_amount = self._calculate_risk_amount(signal, size)
            risk_percent = kelly
        
            return SizingResult(
                size=size,
                method=SizingMethod.KELLY,
                risk_amount=risk_amount,
                risk_percent=risk_percent,
                reasoning=f"Kelly: {kelly:.1%} (win_rate={win_rate:.1%}, RR={b:.2f})",
            )
        except Exception as e:
            logger.error(f"Error in _kelly_sizing: {e}")
            raise
    
    def _volatility_sizing(
        self,
        signal: Signal,
        account_balance: float,
        volatility: float
    ) -> SizingResult:
        """Volatility-adjusted sizing"""
        # Reduce size in high volatility
        try:
            base_size = account_balance * self._risk_per_trade
        
            # Inverse relationship with volatility
            vol_factor = 1.0 / max(volatility, 0.5)
            vol_factor = min(vol_factor, 2.0)  # Cap at 2x
        
            size = base_size * vol_factor
            size = min(size, account_balance * self._max_position_size)
        
            risk_amount = self._calculate_risk_amount(signal, size)
            risk_percent = risk_amount / account_balance if account_balance > 0 else 0
        
            return SizingResult(
                size=size,
                method=SizingMethod.VOLATILITY,
                risk_amount=risk_amount,
                risk_percent=risk_percent,
                reasoning=f"Volatility factor: {vol_factor:.2f}",
            )
        except Exception as e:
            logger.error(f"Error in _volatility_sizing: {e}")
            raise
    
    def _atr_sizing(
        self,
        signal: Signal,
        account_balance: float
    ) -> SizingResult:
        """ATR-based sizing"""
        # Use ATR from signal metadata if available
        try:
            atr = signal.metadata.get("atr", 0.001)
        
            risk_amount = account_balance * self._risk_per_trade
        
            # Size based on ATR
            if atr > 0:
                size = risk_amount / (atr * 2)  # 2 ATR stop
            else:
                size = self._fixed_size
        
            size = min(size, account_balance * self._max_position_size)
        
            actual_risk = self._calculate_risk_amount(signal, size)
            risk_percent = actual_risk / account_balance if account_balance > 0 else 0
        
            return SizingResult(
                size=size,
                method=SizingMethod.ATR,
                risk_amount=actual_risk,
                risk_percent=risk_percent,
                reasoning=f"ATR-based: ATR={atr:.5f}",
            )
        except Exception as e:
            logger.error(f"Error in _atr_sizing: {e}")
            raise
    
    def _calculate_risk_amount(self, signal: Signal, size: float) -> float:
        """Calculate risk amount for position"""
        try:
            if signal.stop_loss and signal.price:
                stop_distance = abs(signal.price - signal.stop_loss)
                return stop_distance * size
            else:
                # Assume 2% risk if no stop loss
                return signal.price * size * 0.02 if signal.price else 0
        except Exception as e:
            logger.error(f"Error in _calculate_risk_amount: {e}")
            raise

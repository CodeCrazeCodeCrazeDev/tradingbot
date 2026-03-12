"""
Dynamic Position Sizing
=======================

Implements optimal position sizing through:
1. Kelly Criterion for optimal growth
2. Volatility-adjusted sizing
3. Drawdown-responsive reduction
4. Correlation-aware portfolio sizing

Target: Maximize capital growth while managing risk
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class SizingMode(Enum):
    """Position sizing modes"""
    FIXED = "fixed"                    # Fixed percentage
    KELLY = "kelly"                    # Kelly Criterion
    VOLATILITY = "volatility"          # Volatility-adjusted
    ADAPTIVE = "adaptive"              # Adaptive based on performance
    CONSERVATIVE = "conservative"      # Reduced sizing


@dataclass
class PositionSizeResult:
    """Result of position size calculation"""
    symbol: str
    recommended_size: float
    max_size: float
    risk_amount: float
    sizing_mode: SizingMode
    adjustments: List[str]
    confidence: float
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'recommended_size': self.recommended_size,
            'max_size': self.max_size,
            'risk_amount': self.risk_amount,
            'sizing_mode': self.sizing_mode.value,
            'adjustments': self.adjustments,
            'confidence': self.confidence,
        }


class KellyCriterion:
    """
    Kelly Criterion position sizing for optimal capital growth.
    
    Formula: f* = (bp - q) / b
    Where:
        f* = fraction of capital to bet
        b = odds received on the bet (win/loss ratio)
        p = probability of winning
        q = probability of losing (1 - p)
    
    PRINCIPLE: Maximize long-term growth rate.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Kelly fraction (use half-Kelly for safety)
        self.kelly_fraction = self.config.get('kelly_fraction', 0.5)
        
        # Minimum trades for reliable calculation
        self.min_trades = self.config.get('min_trades', 30)
        
        # Maximum position size (safety cap)
        self.max_size = self.config.get('max_size', 0.05)  # 5% max
        
        # Minimum position size
        self.min_size = self.config.get('min_size', 0.005)  # 0.5% min
        
        logger.info(f"KellyCriterion initialized: fraction={self.kelly_fraction}")
    
    def calculate(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        num_trades: int = 100
    ) -> Tuple[float, str]:
        """
        Calculate optimal position size using Kelly Criterion.
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade amount
            avg_loss: Average losing trade amount (positive number)
            num_trades: Number of trades in sample
        
        Returns:
            Tuple of (kelly_size, explanation)
        """
        # Validate inputs
        if win_rate <= 0 or win_rate >= 1:
            return self.min_size, "Invalid win rate"
        
        if avg_loss <= 0:
            return self.min_size, "Invalid average loss"
        
        if num_trades < self.min_trades:
            return self.min_size, f"Insufficient trades ({num_trades} < {self.min_trades})"
        
        # Calculate win/loss ratio (odds)
        b = avg_win / avg_loss
        
        # Probability of winning and losing
        p = win_rate
        q = 1 - win_rate
        
        # Kelly formula
        kelly = (b * p - q) / b
        
        # Apply Kelly fraction (half-Kelly for safety)
        kelly_adjusted = kelly * self.kelly_fraction
        
        # Apply bounds
        if kelly_adjusted <= 0:
            return self.min_size, f"Negative Kelly ({kelly:.4f}) - strategy unprofitable"
        
        final_size = max(self.min_size, min(self.max_size, kelly_adjusted))
        
        explanation = (
            f"Kelly: {kelly:.4f}, Adjusted: {kelly_adjusted:.4f}, "
            f"Final: {final_size:.4f} (WR: {win_rate:.2%}, W/L: {b:.2f})"
        )
        
        return final_size, explanation
    
    def calculate_from_trades(
        self,
        trade_results: List[float]
    ) -> Tuple[float, str]:
        """
        Calculate Kelly from list of trade P&L results.
        
        Args:
            trade_results: List of trade P&L (positive = win, negative = loss)
        
        Returns:
            Tuple of (kelly_size, explanation)
        """
        if len(trade_results) < self.min_trades:
            return self.min_size, f"Insufficient trades ({len(trade_results)})"
        
        wins = [t for t in trade_results if t > 0]
        losses = [abs(t) for t in trade_results if t < 0]
        
        if not wins or not losses:
            return self.min_size, "Need both wins and losses for calculation"
        
        win_rate = len(wins) / len(trade_results)
        avg_win = np.mean(wins)
        avg_loss = np.mean(losses)
        
        return self.calculate(win_rate, avg_win, avg_loss, len(trade_results))


class VolatilityAdjustedSizer:
    """
    Adjusts position size based on market volatility.
    
    PRINCIPLE: Trade smaller when volatility is high, larger when low.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Base position size
        self.base_size = self.config.get('base_size', 0.02)  # 2%
        
        # ATR period for volatility calculation
        self.atr_period = self.config.get('atr_period', 14)
        
        # Volatility thresholds
        self.low_vol_threshold = self.config.get('low_vol_threshold', 0.5)
        self.high_vol_threshold = self.config.get('high_vol_threshold', 1.5)
        
        # Size multipliers
        self.low_vol_multiplier = self.config.get('low_vol_multiplier', 1.5)
        self.high_vol_multiplier = self.config.get('high_vol_multiplier', 0.5)
        
        logger.info(f"VolatilityAdjustedSizer initialized: base={self.base_size}")
    
    def calculate_atr(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray
    ) -> float:
        """Calculate Average True Range"""
        if len(highs) < self.atr_period + 1:
            return 0.0
        
        tr = np.zeros(len(highs))
        
        for i in range(1, len(highs)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr[i] = max(hl, hc, lc)
        
        atr = np.mean(tr[-self.atr_period:])
        return atr
    
    def calculate(
        self,
        current_atr: float,
        average_atr: float,
        account_balance: float
    ) -> Tuple[float, str]:
        """
        Calculate volatility-adjusted position size.
        
        Args:
            current_atr: Current ATR value
            average_atr: Long-term average ATR
            account_balance: Current account balance
        
        Returns:
            Tuple of (position_size_percent, explanation)
        """
        if average_atr <= 0:
            return self.base_size, "No ATR data - using base size"
        
        # Calculate volatility ratio
        vol_ratio = current_atr / average_atr
        
        # Determine multiplier
        if vol_ratio < self.low_vol_threshold:
            multiplier = self.low_vol_multiplier
            vol_state = "LOW"
        elif vol_ratio > self.high_vol_threshold:
            multiplier = self.high_vol_multiplier
            vol_state = "HIGH"
        else:
            # Linear interpolation between thresholds
            range_size = self.high_vol_threshold - self.low_vol_threshold
            position_in_range = (vol_ratio - self.low_vol_threshold) / range_size
            multiplier = self.low_vol_multiplier - (
                (self.low_vol_multiplier - self.high_vol_multiplier) * position_in_range
            )
            vol_state = "NORMAL"
        
        adjusted_size = self.base_size * multiplier
        
        explanation = (
            f"Volatility {vol_state} (ratio: {vol_ratio:.2f}), "
            f"multiplier: {multiplier:.2f}, size: {adjusted_size:.4f}"
        )
        
        return adjusted_size, explanation
    
    def calculate_position_units(
        self,
        account_balance: float,
        risk_percent: float,
        stop_loss_pips: float,
        pip_value: float
    ) -> Tuple[float, str]:
        """
        Calculate position size in units based on risk.
        
        Args:
            account_balance: Account balance
            risk_percent: Risk percentage (0-1)
            stop_loss_pips: Stop loss distance in pips
            pip_value: Value per pip per unit
        
        Returns:
            Tuple of (units, explanation)
        """
        if stop_loss_pips <= 0 or pip_value <= 0:
            return 0.0, "Invalid stop loss or pip value"
        
        risk_amount = account_balance * risk_percent
        units = risk_amount / (stop_loss_pips * pip_value)
        
        explanation = (
            f"Risk ${risk_amount:.2f} ({risk_percent:.2%}), "
            f"SL: {stop_loss_pips} pips, Units: {units:.2f}"
        )
        
        return units, explanation


class DynamicPositionSizer:
    """
    Master position sizing system combining all methods.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.kelly = KellyCriterion(self.config.get('kelly', {}))
        self.volatility = VolatilityAdjustedSizer(self.config.get('volatility', {}))
        
        # Default sizing mode
        self.default_mode = SizingMode(self.config.get('default_mode', 'adaptive'))
        
        # Risk limits
        self.max_risk_per_trade = self.config.get('max_risk_per_trade', 0.02)  # 2%
        self.max_total_risk = self.config.get('max_total_risk', 0.10)  # 10%
        
        # Drawdown adjustment
        self.drawdown_threshold = self.config.get('drawdown_threshold', 0.10)  # 10%
        self.drawdown_reduction = self.config.get('drawdown_reduction', 0.5)  # 50% reduction
        
        # Performance tracking
        self.trade_history: List[float] = []
        self.max_balance = 0.0
        
        logger.info(f"DynamicPositionSizer initialized: mode={self.default_mode.value}")
    
    def calculate_size(
        self,
        symbol: str,
        account_balance: float,
        current_drawdown: float = 0.0,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None,
        current_atr: Optional[float] = None,
        average_atr: Optional[float] = None,
        open_positions_risk: float = 0.0,
        mode: Optional[SizingMode] = None
    ) -> PositionSizeResult:
        """
        Calculate optimal position size.
        
        Args:
            symbol: Trading symbol
            account_balance: Current account balance
            current_drawdown: Current drawdown percentage (0-1)
            win_rate: Historical win rate
            avg_win: Average winning trade
            avg_loss: Average losing trade
            current_atr: Current ATR
            average_atr: Average ATR
            open_positions_risk: Risk from open positions
            mode: Sizing mode to use
        
        Returns:
            PositionSizeResult with recommended size
        """
        mode = mode or self.default_mode
        adjustments = []
        base_size = self.max_risk_per_trade
        
        # 1. Calculate base size based on mode
        if mode == SizingMode.KELLY and win_rate and avg_win and avg_loss:
            kelly_size, kelly_reason = self.kelly.calculate(
                win_rate, avg_win, avg_loss, len(self.trade_history)
            )
            base_size = kelly_size
            adjustments.append(f"Kelly: {kelly_reason}")
        
        elif mode == SizingMode.VOLATILITY and current_atr and average_atr:
            vol_size, vol_reason = self.volatility.calculate(
                current_atr, average_atr, account_balance
            )
            base_size = vol_size
            adjustments.append(f"Volatility: {vol_reason}")
        
        elif mode == SizingMode.ADAPTIVE:
            # Combine Kelly and Volatility
            sizes = []
            
            if win_rate and avg_win and avg_loss:
                kelly_size, _ = self.kelly.calculate(win_rate, avg_win, avg_loss)
                sizes.append(kelly_size)
            
            if current_atr and average_atr:
                vol_size, _ = self.volatility.calculate(
                    current_atr, average_atr, account_balance
                )
                sizes.append(vol_size)
            
            if sizes:
                base_size = np.mean(sizes)
                adjustments.append(f"Adaptive: avg of {len(sizes)} methods")
            else:
                adjustments.append("Adaptive: using default size")
        
        elif mode == SizingMode.CONSERVATIVE:
            base_size = self.max_risk_per_trade * 0.5
            adjustments.append("Conservative: 50% of max risk")
        
        else:  # FIXED
            base_size = self.max_risk_per_trade
            adjustments.append(f"Fixed: {base_size:.2%}")
        
        # 2. Apply drawdown adjustment
        if current_drawdown >= self.drawdown_threshold:
            reduction = self.drawdown_reduction
            base_size *= (1 - reduction)
            adjustments.append(
                f"Drawdown adjustment: -{reduction:.0%} (DD: {current_drawdown:.1%})"
            )
        
        # 3. Check total risk limit
        available_risk = self.max_total_risk - open_positions_risk
        if base_size > available_risk:
            base_size = max(0, available_risk)
            adjustments.append(f"Total risk limit: capped at {available_risk:.2%}")
        
        # 4. Apply absolute maximum
        max_size = self.max_risk_per_trade
        if base_size > max_size:
            base_size = max_size
            adjustments.append(f"Max risk cap: {max_size:.2%}")
        
        # Calculate risk amount
        risk_amount = account_balance * base_size
        
        # Calculate confidence based on data quality
        confidence = 0.5
        if win_rate and avg_win and avg_loss:
            confidence += 0.2
        if current_atr and average_atr:
            confidence += 0.2
        if len(self.trade_history) >= 30:
            confidence += 0.1
        
        return PositionSizeResult(
            symbol=symbol,
            recommended_size=base_size,
            max_size=max_size,
            risk_amount=risk_amount,
            sizing_mode=mode,
            adjustments=adjustments,
            confidence=min(1.0, confidence)
        )
    
    def record_trade(self, pnl: float):
        """Record a trade result for performance tracking"""
        self.trade_history.append(pnl)
        
        # Keep last 100 trades
        if len(self.trade_history) > 100:
            self.trade_history = self.trade_history[-100:]
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics from trade history"""
        if not self.trade_history:
            return {}
        
        wins = [t for t in self.trade_history if t > 0]
        losses = [abs(t) for t in self.trade_history if t < 0]
        
        return {
            'total_trades': len(self.trade_history),
            'win_rate': len(wins) / len(self.trade_history) if self.trade_history else 0,
            'avg_win': np.mean(wins) if wins else 0,
            'avg_loss': np.mean(losses) if losses else 0,
            'profit_factor': (sum(wins) / sum(losses)) if losses and sum(losses) > 0 else 0,
            'total_pnl': sum(self.trade_history),
        }
    
    def calculate_units(
        self,
        account_balance: float,
        risk_percent: float,
        entry_price: float,
        stop_loss_price: float,
        pip_value: float = 10.0
    ) -> Tuple[float, float]:
        """
        Calculate position size in units/lots.
        
        Returns:
            Tuple of (units, lots)
        """
        if entry_price == stop_loss_price:
            return 0.0, 0.0
        
        # Calculate stop loss in pips
        stop_loss_pips = abs(entry_price - stop_loss_price) * 10000  # For forex
        
        # Risk amount
        risk_amount = account_balance * risk_percent
        
        # Units
        units = risk_amount / (stop_loss_pips * pip_value / 10000)
        
        # Convert to lots (1 lot = 100,000 units)
        lots = units / 100000
        
        return units, lots

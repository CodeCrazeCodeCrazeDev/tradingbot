import logging
logger = logging.getLogger(__name__)
"""Adaptive Risk Management System.

This module implements dynamic risk management that automatically adjusts
position sizes, stop losses, and risk parameters based on market conditions.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
from .market_regime import MarketRegime, MarketRegimeDetector
import numpy
import pandas


@dataclass
class RiskParameters:
    """Risk parameters for different market conditions."""
    max_risk_per_trade: float
    position_size_multiplier: float
    stop_loss_multiplier: float
    take_profit_multiplier: float
    max_positions: int
    correlation_limit: float
    drawdown_limit: float


class AdaptiveRiskManager:
    """Dynamic risk management system that adapts to market conditions."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the adaptive risk manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.base_risk = self.config.get('base_risk_per_trade', 0.02)  # 2%
        self.account_balance = self.config.get('initial_balance', 10000)
        self.max_drawdown = self.config.get('max_drawdown', 0.15)  # 15%
        
        # Risk parameters for different regimes
        self.regime_risk_params = self._initialize_regime_parameters()
        
        # Performance tracking
        self.performance_history = []
        self.current_drawdown = 0.0
        self.peak_balance = self.account_balance
        self.consecutive_losses = 0
        self.win_rate = 0.5
        
        # Position tracking
        self.open_positions = {}
        self.position_correlations = {}
        
        logger.info("AdaptiveRiskManager initialized")
    
    def _initialize_regime_parameters(self) -> Dict[MarketRegime, RiskParameters]:
        """Initialize risk parameters for different market regimes."""
        return {
            MarketRegime.TRENDING_BULL: RiskParameters(
                max_risk_per_trade=self.base_risk * 1.2,  # Increase risk in trending markets
                position_size_multiplier=1.1,
                stop_loss_multiplier=0.8,  # Tighter stops in trends
                take_profit_multiplier=1.5,  # Larger targets
                max_positions=6,
                correlation_limit=0.7,
                drawdown_limit=0.12
            ),
            MarketRegime.TRENDING_BEAR: RiskParameters(
                max_risk_per_trade=self.base_risk * 0.8,  # Reduce risk in bear markets
                position_size_multiplier=0.8,
                stop_loss_multiplier=0.9,
                take_profit_multiplier=1.2,
                max_positions=4,
                correlation_limit=0.6,
                drawdown_limit=0.10
            ),
            MarketRegime.RANGING: RiskParameters(
                max_risk_per_trade=self.base_risk,
                position_size_multiplier=1.0,
                stop_loss_multiplier=1.0,
                take_profit_multiplier=1.0,
                max_positions=5,
                correlation_limit=0.8,
                drawdown_limit=0.15
            ),
            MarketRegime.HIGH_VOLATILITY: RiskParameters(
                max_risk_per_trade=self.base_risk * 0.6,  # Significantly reduce risk
                position_size_multiplier=0.6,
                stop_loss_multiplier=1.5,  # Wider stops for volatility
                take_profit_multiplier=0.8,  # Smaller targets
                max_positions=3,
                correlation_limit=0.5,
                drawdown_limit=0.08
            ),
            MarketRegime.LOW_VOLATILITY: RiskParameters(
                max_risk_per_trade=self.base_risk * 1.1,
                position_size_multiplier=1.1,
                stop_loss_multiplier=0.9,
                take_profit_multiplier=1.1,
                max_positions=6,
                correlation_limit=0.8,
                drawdown_limit=0.15
            ),
            MarketRegime.BREAKOUT: RiskParameters(
                max_risk_per_trade=self.base_risk * 1.3,  # Higher risk for breakouts
                position_size_multiplier=1.2,
                stop_loss_multiplier=0.7,  # Tight stops
                take_profit_multiplier=2.0,  # Large targets
                max_positions=4,
                correlation_limit=0.6,
                drawdown_limit=0.12
            ),
            MarketRegime.CRISIS: RiskParameters(
                max_risk_per_trade=self.base_risk * 0.3,  # Minimal risk
                position_size_multiplier=0.3,
                stop_loss_multiplier=2.0,  # Very wide stops
                take_profit_multiplier=0.5,  # Quick profits
                max_positions=2,
                correlation_limit=0.3,
                drawdown_limit=0.05
            )
        }
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss: float, regime: MarketRegime) -> float:
        """Calculate optimal position size based on risk parameters and market regime.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price for the position
            stop_loss: Stop loss price
            regime: Current market regime
            
        Returns:
            Position size in units
        """
        # Validate input
        if not isinstance(entry_price, (int, float)) or not isinstance(stop_loss, (int, float)):
            logger.error(f"Invalid entry/stop values for {symbol}: entry={entry_price}, stop={stop_loss}")
            return 0.0
        if entry_price <= 0 or stop_loss <= 0:
            logger.error(f"Non-positive entry/stop for {symbol}: entry={entry_price}, stop={stop_loss}")
            return 0.0
        
        risk_params = self.regime_risk_params.get(regime, self.regime_risk_params[MarketRegime.RANGING])
        base_risk_amount = self.account_balance * risk_params.max_risk_per_trade
        performance_multiplier = self._calculate_performance_multiplier()
        adjusted_risk_amount = base_risk_amount * performance_multiplier
        drawdown_multiplier = self._calculate_drawdown_multiplier(risk_params.drawdown_limit)
        final_risk_amount = adjusted_risk_amount * drawdown_multiplier
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance == 0:
            logger.warning(f"Zero stop distance for {symbol}, using minimal position size")
            return 0.01
        try:
            position_size = final_risk_amount / stop_distance
        except Exception as e:
            logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0.0
        position_size *= risk_params.position_size_multiplier
        correlation_multiplier = self._calculate_correlation_multiplier(symbol, risk_params.correlation_limit)
        position_size *= correlation_multiplier
        min_size = self.config.get('min_position_size', 0.01)
        max_size = self.account_balance * 0.1
        if not isinstance(position_size, (int, float)) or position_size < 0:
            logger.error(f"Negative or invalid position size for {symbol}: {position_size}")
            return 0.0
        position_size = max(min_size, min(position_size, max_size))
        logger.info(f"Calculated position size for {symbol}: {position_size:.4f} (regime: {regime.value}, risk: {final_risk_amount:.2f})")
        return position_size
    
    def adjust_stop_loss(self, symbol: str, entry_price: float, 
                        initial_stop: float, regime: MarketRegime) -> float:
        """Adjust stop loss based on market regime and volatility.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            initial_stop: Initial stop loss price
            regime: Current market regime
            
        Returns:
            Adjusted stop loss price
        """
        risk_params = self.regime_risk_params.get(regime, self.regime_risk_params[MarketRegime.RANGING])
        
        # Calculate stop distance
        stop_distance = abs(entry_price - initial_stop)
        
        # Apply regime-specific multiplier
        adjusted_distance = stop_distance * risk_params.stop_loss_multiplier
        
        # Apply volatility adjustment
        volatility_multiplier = self._get_volatility_multiplier(symbol)
        final_distance = adjusted_distance * volatility_multiplier
        
        # Calculate final stop loss
        if entry_price > initial_stop:  # Long position
            adjusted_stop = entry_price - final_distance
        else:  # Short position
            adjusted_stop = entry_price + final_distance
        
        logger.info(f"Adjusted stop loss for {symbol}: {initial_stop:.5f} -> {adjusted_stop:.5f}")
        return adjusted_stop
    
    def adjust_take_profit(self, symbol: str, entry_price: float, 
                          stop_loss: float, regime: MarketRegime) -> float:
        """Calculate take profit based on risk-reward ratio and market regime.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            regime: Current market regime
            
        Returns:
            Take profit price
        """
        risk_params = self.regime_risk_params.get(regime, self.regime_risk_params[MarketRegime.RANGING])
        
        # Calculate risk distance
        risk_distance = abs(entry_price - stop_loss)
        
        # Apply regime-specific multiplier
        reward_distance = risk_distance * risk_params.take_profit_multiplier
        
        # Calculate take profit
        if entry_price > stop_loss:  # Long position
            take_profit = entry_price + reward_distance
        else:  # Short position
            take_profit = entry_price - reward_distance
        
        logger.info(f"Calculated take profit for {symbol}: {take_profit:.5f} "
                   f"(R:R = 1:{risk_params.take_profit_multiplier})")
        
        return take_profit
    
    def can_open_position(self, symbol: str, regime: MarketRegime) -> bool:
        """Check if a new position can be opened based on risk limits.
        
        Args:
            symbol: Trading symbol
            regime: Current market regime
            
        Returns:
            True if position can be opened
        """
        risk_params = self.regime_risk_params.get(regime, self.regime_risk_params[MarketRegime.RANGING])
        
        # Check maximum positions limit
        if len(self.open_positions) >= risk_params.max_positions:
            logger.warning(f"Maximum positions limit reached: {len(self.open_positions)}/{risk_params.max_positions}")
            return False
        
        # Check drawdown limit
        if self.current_drawdown > risk_params.drawdown_limit:
            logger.warning(f"Drawdown limit exceeded: {self.current_drawdown:.2%} > {risk_params.drawdown_limit:.2%}")
            return False
        
        # Check correlation limits
        if not self._check_correlation_limits(symbol, risk_params.correlation_limit):
            logger.warning(f"Correlation limit exceeded for {symbol}")
            return False
        
        return True
    
    def update_performance(self, trade_result: Dict[str, Any]):
        """Update performance metrics with new trade result.
        
        Args:
            trade_result: Dictionary with trade outcome data
        """
        self.performance_history.append(trade_result)
        
        # Update account balance
        pnl = trade_result.get('pnl', 0)
        self.account_balance += pnl
        
        # Update drawdown tracking
        if self.account_balance > self.peak_balance:
            self.peak_balance = self.account_balance
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = (self.peak_balance - self.account_balance) / self.peak_balance
        
        # Update consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # Update win rate
        recent_trades = self.performance_history[-50:]  # Last 50 trades
        wins = sum(1 for trade in recent_trades if trade.get('pnl', 0) > 0)
        self.win_rate = wins / len(recent_trades) if recent_trades else 0.5
        
        # Remove position from tracking
        symbol = trade_result.get('symbol')
        if symbol in self.open_positions:
            del self.open_positions[symbol]
        
        logger.info(f"Performance updated: Balance={self.account_balance:.2f}, "
                   f"Drawdown={self.current_drawdown:.2%}, WinRate={self.win_rate:.2%}")
    
    def _calculate_performance_multiplier(self) -> float:
        """Calculate performance-based risk multiplier."""
        # Reduce risk after consecutive losses
        if self.consecutive_losses >= 3:
            return 0.5
        elif self.consecutive_losses >= 2:
            return 0.7
        
        # Adjust based on win rate
        if self.win_rate > 0.6:
            return 1.2
        elif self.win_rate < 0.4:
            return 0.8
        
        return 1.0
    
    def _calculate_drawdown_multiplier(self, limit: float) -> float:
        """Calculate drawdown-based risk multiplier."""
        if self.current_drawdown > limit * 0.8:  # 80% of limit
            return 0.3
        elif self.current_drawdown > limit * 0.6:  # 60% of limit
            return 0.6
        elif self.current_drawdown > limit * 0.4:  # 40% of limit
            return 0.8
        
        return 1.0
    
    def _calculate_correlation_multiplier(self, symbol: str, limit: float) -> float:
        """Calculate correlation-based position size multiplier."""
        if not self.open_positions:
            return 1.0
        
        # Simplified correlation check (in real implementation, use actual correlation data)
        similar_positions = 0
        for existing_symbol in self.open_positions:
            # Check if symbols are from same market/currency pair
            if self._symbols_correlated(symbol, existing_symbol):
                similar_positions += 1
        
        if similar_positions >= 2:
            return 0.5
        elif similar_positions >= 1:
            return 0.8
        
        return 1.0
    
    def _check_correlation_limits(self, symbol: str, limit: float) -> bool:
        """Check if opening position would exceed correlation limits."""
        # Simplified implementation
        correlated_positions = sum(1 for existing in self.open_positions 
                                 if self._symbols_correlated(symbol, existing))
        return correlated_positions < 3
    
    def _symbols_correlated(self, symbol1: str, symbol2: str) -> bool:
        """Check if two symbols are correlated (simplified)."""
        # Basic correlation check based on currency pairs
        if symbol1 == symbol2:
            return True
        
        # Check for common currencies
        if len(symbol1) == 6 and len(symbol2) == 6:  # Forex pairs
            base1, quote1 = symbol1[:3], symbol1[3:]
            base2, quote2 = symbol2[:3], symbol2[3:]
            
            if base1 == base2 or quote1 == quote2:
                return True
        
        return False
    
    def _get_volatility_multiplier(self, symbol: str) -> float:
        """Get volatility-based multiplier for stop loss adjustment."""
        # Placeholder - in real implementation, calculate from recent price data
        return 1.0
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get current risk management summary."""
        return {
            'account_balance': self.account_balance,
            'current_drawdown': self.current_drawdown,
            'peak_balance': self.peak_balance,
            'consecutive_losses': self.consecutive_losses,
            'win_rate': self.win_rate,
            'open_positions': len(self.open_positions),
            'recent_performance': self.performance_history[-10:] if self.performance_history else []
        }

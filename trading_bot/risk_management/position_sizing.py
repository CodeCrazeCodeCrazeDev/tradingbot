"""
Elite Trading Bot - Position Sizing Algorithms

This module provides advanced position sizing algorithms for the Elite Trading Bot,
implementing various methods including Kelly Criterion, Fixed Fractional, and Volatility-based sizing.
"""

import enum
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import math

import numpy as np
import pandas as pd
try:
    from scipy import optimize
except ImportError:
    scipy = None
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class SizingMethod(enum.Enum):
    """Position sizing methods."""
    FIXED_AMOUNT = "fixed_amount"           # Fixed dollar amount
    FIXED_PERCENTAGE = "fixed_percentage"   # Fixed percentage of portfolio
    KELLY_CRITERION = "kelly_criterion"     # Kelly Criterion optimal sizing
    FIXED_FRACTIONAL = "fixed_fractional"   # Fixed fractional risk
    VOLATILITY_BASED = "volatility_based"   # Volatility-adjusted sizing
    OPTIMAL_F = "optimal_f"                 # Optimal F sizing
    RISK_PARITY = "risk_parity"            # Risk parity sizing
    MONTE_CARLO = "monte_carlo"            # Monte Carlo optimization
    ADAPTIVE = "adaptive"                   # Adaptive sizing based on performance


@dataclass
class PositionSize:
    """Position size calculation result."""
    method: SizingMethod
    symbol: str
    recommended_size: float     # Recommended position size in dollars
    max_size: float            # Maximum allowed size
    min_size: float            # Minimum viable size
    risk_amount: float         # Dollar amount at risk
    risk_percentage: float     # Risk as percentage of portfolio
    confidence: float          # Confidence in sizing recommendation
    kelly_fraction: Optional[float] = None  # Kelly fraction if applicable
    volatility_adjustment: Optional[float] = None  # Volatility adjustment factor
    notes: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class KellyCalculator:
    """
    Kelly Criterion calculator for optimal position sizing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Kelly calculator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        logger.info("KellyCalculator initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "max_kelly_fraction": 0.25,  # Maximum Kelly fraction to use
            "min_win_rate": 0.35,        # Minimum win rate to calculate Kelly
            "min_sample_size": 30,       # Minimum trades for reliable Kelly
            "kelly_multiplier": 0.5,     # Conservative Kelly multiplier
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def calculate_kelly_fraction(self, 
                                win_rate: float,
                                avg_win: float,
                                avg_loss: float,
                                trade_history: Optional[List[float]] = None) -> float:
        """
        Calculate Kelly fraction for optimal position sizing.
        
        Args:
            win_rate: Historical win rate (0.0 to 1.0)
            avg_win: Average winning trade return
            avg_loss: Average losing trade return (positive value)
            trade_history: Optional list of historical trade returns
            
        Returns:
            Kelly fraction (0.0 to 1.0)
        """
        # Validate inputs
        if win_rate < self.config["min_win_rate"] or win_rate >= 1.0:
            logger.warning(f"Win rate {win_rate} outside valid range")
            return 0.0
        
        if avg_win <= 0 or avg_loss <= 0:
            logger.warning("Invalid average win/loss values")
            return 0.0
        
        # Calculate Kelly fraction: f = (bp - q) / b
        # where b = odds received (avg_win/avg_loss), p = win_rate, q = loss_rate
        b = avg_win / avg_loss  # Odds ratio
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b * p - q) / b
        
        # Apply conservative multiplier
        kelly_fraction *= self.config["kelly_multiplier"]
        
        # Cap at maximum allowed fraction
        kelly_fraction = min(kelly_fraction, self.config["max_kelly_fraction"])
        
        # Ensure non-negative
        kelly_fraction = max(0.0, kelly_fraction)
        
        # Additional validation with trade history if available
        if trade_history and len(trade_history) >= self.config["min_sample_size"]:
            # Calculate empirical Kelly using historical returns
            empirical_kelly = self._calculate_empirical_kelly(trade_history)
            
            # Use more conservative estimate
            kelly_fraction = min(kelly_fraction, empirical_kelly)
        
        return kelly_fraction
    
    def _calculate_empirical_kelly(self, returns: List[float]) -> float:
        """Calculate Kelly fraction using empirical method."""
        if len(returns) < 10:
            return 0.0
        
        returns_array = np.array(returns)
        
        # Calculate mean and variance
        mean_return = np.mean(returns_array)
        variance = np.var(returns_array)
        
        if variance <= 0:
            return 0.0
        
        # Empirical Kelly: f = mean / variance
        empirical_kelly = mean_return / variance
        
        # Apply constraints
        empirical_kelly = max(0.0, min(empirical_kelly, self.config["max_kelly_fraction"]))
        
        return empirical_kelly
    
    def calculate_optimal_size(self, 
                             portfolio_value: float,
                             win_rate: float,
                             avg_win: float,
                             avg_loss: float,
                             max_position_pct: float = 0.1) -> float:
        """
        Calculate optimal position size using Kelly Criterion.
        
        Args:
            portfolio_value: Total portfolio value
            win_rate: Historical win rate
            avg_win: Average winning trade return
            avg_loss: Average losing trade return
            max_position_pct: Maximum position size as percentage
            
        Returns:
            Optimal position size in dollars
        """
        kelly_fraction = self.calculate_kelly_fraction(win_rate, avg_win, avg_loss)
        
        # Calculate position size
        optimal_size = portfolio_value * kelly_fraction
        
        # Apply maximum position constraint
        max_size = portfolio_value * max_position_pct
        optimal_size = min(optimal_size, max_size)
        
        return optimal_size


class FixedFractionalSizer:
    """
    Fixed fractional position sizing based on risk percentage.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize fixed fractional sizer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        logger.info("FixedFractionalSizer initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "default_risk_pct": 1.0,     # Default risk percentage
            "max_risk_pct": 3.0,         # Maximum risk percentage
            "min_position_size": 100.0,  # Minimum position size in dollars
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def calculate_position_size(self, 
                              portfolio_value: float,
                              entry_price: float,
                              stop_loss: float,
                              risk_pct: Optional[float] = None) -> float:
        """
        Calculate position size based on fixed fractional risk.
        
        Args:
            portfolio_value: Total portfolio value
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_pct: Risk percentage (uses default if None)
            
        Returns:
            Position size in dollars
        """
        if risk_pct is None:
            risk_pct = self.config["default_risk_pct"]
        
        # Cap risk percentage
        risk_pct = min(risk_pct, self.config["max_risk_pct"])
        
        # Calculate risk amount
        risk_amount = portfolio_value * (risk_pct / 100)
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share <= 0:
            logger.warning("Invalid risk per share calculation")
            return self.config["min_position_size"]
        
        # Calculate number of shares
        shares = risk_amount / risk_per_share
        
        # Calculate position size
        position_size = shares * entry_price
        
        # Apply minimum position size
        position_size = max(position_size, self.config["min_position_size"])
        
        return position_size


class VolatilityBasedSizer:
    """
    Volatility-based position sizing that adjusts size based on market volatility.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize volatility-based sizer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        logger.info("VolatilityBasedSizer initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "base_risk_pct": 1.0,        # Base risk percentage
            "volatility_lookback": 20,    # Days for volatility calculation
            "volatility_target": 0.02,    # Target daily volatility (2%)
            "max_volatility_adjustment": 2.0,  # Maximum volatility adjustment factor
            "min_volatility_adjustment": 0.5,  # Minimum volatility adjustment factor
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def calculate_position_size(self, 
                              portfolio_value: float,
                              entry_price: float,
                              stop_loss: float,
                              market_data: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate position size adjusted for volatility.
        
        Args:
            portfolio_value: Total portfolio value
            entry_price: Entry price
            stop_loss: Stop loss price
            market_data: Historical market data
            
        Returns:
            Tuple of (position_size, volatility_adjustment)
        """
        # Calculate current volatility
        current_volatility = self._calculate_volatility(market_data)
        
        # Calculate volatility adjustment factor
        volatility_adjustment = self.config["volatility_target"] / current_volatility
        
        # Apply adjustment limits
        volatility_adjustment = max(
            self.config["min_volatility_adjustment"],
            min(volatility_adjustment, self.config["max_volatility_adjustment"])
        )
        
        # Calculate adjusted risk percentage
        adjusted_risk_pct = self.config["base_risk_pct"] * volatility_adjustment
        
        # Calculate position size using adjusted risk
        risk_amount = portfolio_value * (adjusted_risk_pct / 100)
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share <= 0:
            return 0.0, volatility_adjustment
        
        shares = risk_amount / risk_per_share
        position_size = shares * entry_price
        
        return position_size, volatility_adjustment
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate current volatility."""
        if len(df) < self.config["volatility_lookback"]:
            return self.config["volatility_target"]  # Default volatility
        
        # Calculate returns
        returns = df['close'].pct_change().dropna()
        
        # Calculate rolling volatility
        volatility = returns.rolling(window=self.config["volatility_lookback"]).std().iloc[-1]
        
        return volatility if not np.isnan(volatility) else self.config["volatility_target"]


class OptimalFSizer:
    """
    Optimal F position sizing based on historical trade outcomes.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Optimal F sizer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        logger.info("OptimalFSizer initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "min_trades": 30,            # Minimum trades for calculation
            "max_f_fraction": 0.25,      # Maximum F fraction
            "f_multiplier": 0.6,         # Conservative F multiplier
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def calculate_optimal_f(self, trade_results: List[float]) -> float:
        """
        Calculate Optimal F fraction.
        
        Args:
            trade_results: List of trade P&L results
            
        Returns:
            Optimal F fraction
        """
        if len(trade_results) < self.config["min_trades"]:
            logger.warning(f"Insufficient trade history: {len(trade_results)} < {self.config['min_trades']}")
            return 0.0
        
        # Find the largest loss (for normalization)
        largest_loss = abs(min(trade_results))
        
        if largest_loss <= 0:
            return 0.0
        
        # Normalize trade results by largest loss
        normalized_results = [result / largest_loss for result in trade_results]
        
        # Define objective function for optimization
        def objective(f):
            pass
        try:
            if f <= 0:
                return -float('inf')
            
            # Calculate geometric mean of (1 + f * normalized_result)
            products = []
            for result in normalized_results:
                value = 1 + f * result
                if value <= 0:
                    return -float('inf')
                products.append(value)
            
            # Geometric mean
            geometric_mean = np.prod(products) ** (1.0 / len(products))
            return -geometric_mean  # Negative because we're minimizing
        
        # Optimize F
            result = optimize.minimize_scalar(
                objective,
                bounds=(0.001, 1.0),
                method='bounded'
            )
            
            optimal_f = result.x if result.success else 0.0
        except Exception:
            optimal_f = 0.0
        
        # Apply conservative multiplier and cap
        optimal_f *= self.config["f_multiplier"]
        optimal_f = min(optimal_f, self.config["max_f_fraction"])
        
        return max(0.0, optimal_f)
    
    def calculate_position_size(self, 
                              portfolio_value: float,
                              trade_results: List[float],
                              largest_historical_loss: float) -> float:
        """
        Calculate position size using Optimal F.
        
        Args:
            portfolio_value: Total portfolio value
            trade_results: Historical trade results
            largest_historical_loss: Largest historical loss
            
        Returns:
            Position size in dollars
        """
        optimal_f = self.calculate_optimal_f(trade_results)
        
        if optimal_f <= 0 or largest_historical_loss <= 0:
            return 0.0
        
        # Position size = Portfolio Value * F / Largest Loss
        position_size = portfolio_value * optimal_f / largest_historical_loss
        
        return position_size


class RiskParitySizer:
    """
    Risk parity position sizing for portfolio construction.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize risk parity sizer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        logger.info("RiskParitySizer initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "lookback_days": 60,         # Days for volatility calculation
            "min_weight": 0.01,          # Minimum position weight
            "max_weight": 0.2,           # Maximum position weight
            "rebalance_threshold": 0.05,  # Rebalance threshold
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def calculate_risk_parity_weights(self, 
                                    symbols: List[str],
                                    market_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Calculate risk parity weights for multiple assets.
        
        Args:
            symbols: List of symbols
            market_data: Dictionary of symbol -> market data
            
        Returns:
            Dictionary of symbol -> weight
        """
        # Calculate volatilities
        volatilities = {}
        
        for symbol in symbols:
            if symbol in market_data:
                vol = self._calculate_volatility(market_data[symbol])
                volatilities[symbol] = vol
        
        if not volatilities:
            return {}
        
        # Calculate inverse volatility weights
        inv_vol_sum = sum(1.0 / vol for vol in volatilities.values())
        
        weights = {}
        for symbol, vol in volatilities.items():
            weight = (1.0 / vol) / inv_vol_sum
            
            # Apply weight constraints
            weight = max(self.config["min_weight"], 
                        min(weight, self.config["max_weight"]))
            
            weights[symbol] = weight
        
        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {symbol: weight / total_weight 
                      for symbol, weight in weights.items()}
        
        return weights
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate annualized volatility."""
        if len(df) < self.config["lookback_days"]:
            return 0.2  # Default volatility
        
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        return volatility if not np.isnan(volatility) else 0.2


class PositionSizer:
    """
    Main position sizing engine that combines multiple sizing methods.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize position sizer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Initialize sizing components
        self.kelly_calculator = KellyCalculator(self.config.get("kelly_config"))
        self.fixed_fractional = FixedFractionalSizer(self.config.get("fixed_fractional_config"))
        self.volatility_sizer = VolatilityBasedSizer(self.config.get("volatility_config"))
        self.optimal_f = OptimalFSizer(self.config.get("optimal_f_config"))
        self.risk_parity = RiskParitySizer(self.config.get("risk_parity_config"))
        
        logger.info("PositionSizer initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "default_method": SizingMethod.FIXED_FRACTIONAL,
            "portfolio_value": 100000.0,
            "max_position_pct": 0.1,     # 10% max position size
            "min_position_size": 100.0,   # Minimum position size
            "enable_size_validation": True,
            "enable_risk_overlay": True,
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def calculate_position_size(self, 
                              method: SizingMethod,
                              symbol: str,
                              entry_price: float,
                              stop_loss: float,
                              portfolio_value: Optional[float] = None,
                              market_data: Optional[pd.DataFrame] = None,
                              trade_history: Optional[List[float]] = None,
                              **kwargs) -> PositionSize:
        """
        Calculate position size using specified method.
        
        Args:
            method: Position sizing method
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            portfolio_value: Portfolio value (uses default if None)
            market_data: Market data for volatility calculations
            trade_history: Historical trade results
            **kwargs: Additional method-specific parameters
            
        Returns:
            PositionSize object with recommendations
        """
        if portfolio_value is None:
            portfolio_value = self.config["portfolio_value"]
        
        # Initialize result
        result = PositionSize(
            method=method,
            symbol=symbol,
            recommended_size=0.0,
            max_size=portfolio_value * self.config["max_position_pct"],
            min_size=self.config["min_position_size"],
            risk_amount=0.0,
            risk_percentage=0.0,
            confidence=0.5
        )
        
        try:
            if method == SizingMethod.FIXED_AMOUNT:
                # Fixed dollar amount
                fixed_amount = kwargs.get("fixed_amount", 1000.0)
                result.recommended_size = fixed_amount
                result.confidence = 1.0
                result.notes = f"Fixed amount: ${fixed_amount}"
                
            elif method == SizingMethod.FIXED_PERCENTAGE:
                # Fixed percentage of portfolio
                fixed_pct = kwargs.get("fixed_percentage", 5.0)
                result.recommended_size = portfolio_value * (fixed_pct / 100)
                result.confidence = 1.0
                result.notes = f"Fixed percentage: {fixed_pct}%"
                
            elif method == SizingMethod.KELLY_CRITERION:
                # Kelly Criterion
                win_rate = kwargs.get("win_rate", 0.5)
                avg_win = kwargs.get("avg_win", 0.02)
                avg_loss = kwargs.get("avg_loss", 0.01)
                
                kelly_fraction = self.kelly_calculator.calculate_kelly_fraction(
                    win_rate, avg_win, avg_loss, trade_history
                )
                
                result.recommended_size = portfolio_value * kelly_fraction
                result.kelly_fraction = kelly_fraction
                result.confidence = 0.8 if trade_history and len(trade_history) > 30 else 0.6
                result.notes = f"Kelly fraction: {kelly_fraction:.3f}"
                
            elif method == SizingMethod.FIXED_FRACTIONAL:
                # Fixed fractional risk
                risk_pct = kwargs.get("risk_pct", 1.0)
                result.recommended_size = self.fixed_fractional.calculate_position_size(
                    portfolio_value, entry_price, stop_loss, risk_pct
                )
                result.confidence = 0.9
                result.notes = f"Fixed fractional risk: {risk_pct}%"
                
            elif method == SizingMethod.VOLATILITY_BASED:
                # Volatility-based sizing
                if market_data is not None:
                    size, vol_adj = self.volatility_sizer.calculate_position_size(
                        portfolio_value, entry_price, stop_loss, market_data
                    )
                    result.recommended_size = size
                    result.volatility_adjustment = vol_adj
                    result.confidence = 0.8
                    result.notes = f"Volatility adjustment: {vol_adj:.2f}x"
                else:
                    # Fallback to fixed fractional
                    result.recommended_size = self.fixed_fractional.calculate_position_size(
                        portfolio_value, entry_price, stop_loss
                    )
                    result.confidence = 0.5
                    result.notes = "Fallback to fixed fractional (no market data)"
                
            elif method == SizingMethod.OPTIMAL_F:
                # Optimal F sizing
                if trade_history and len(trade_history) > 10:
                    largest_loss = abs(min(trade_history)) if trade_history else 1.0
                    result.recommended_size = self.optimal_f.calculate_position_size(
                        portfolio_value, trade_history, largest_loss
                    )
                    result.confidence = 0.7
                    result.notes = f"Optimal F with {len(trade_history)} trades"
                else:
                    # Fallback to fixed fractional
                    result.recommended_size = self.fixed_fractional.calculate_position_size(
                        portfolio_value, entry_price, stop_loss
                    )
                    result.confidence = 0.4
                    result.notes = "Insufficient trade history for Optimal F"
                
            else:
                # Default to fixed fractional
                result.recommended_size = self.fixed_fractional.calculate_position_size(
                    portfolio_value, entry_price, stop_loss
                )
                result.confidence = 0.7
                result.notes = "Default fixed fractional sizing"
            
            # Apply size constraints
            result.recommended_size = max(result.min_size, 
                                        min(result.recommended_size, result.max_size))
            
            # Calculate risk metrics
            shares = result.recommended_size / entry_price
            result.risk_amount = shares * abs(entry_price - stop_loss)
            result.risk_percentage = (result.risk_amount / portfolio_value) * 100
            
            # Validate size if enabled
            if self.config["enable_size_validation"]:
                self._validate_position_size(result)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            result.recommended_size = result.min_size
            result.confidence = 0.1
            result.notes = f"Error in calculation: {str(e)}"
        
        return result
    
    def _validate_position_size(self, position_size: PositionSize):
        """Validate position size against risk parameters."""
        # Check if risk percentage is reasonable
        if position_size.risk_percentage > 5.0:
            position_size.confidence *= 0.5
            position_size.notes += " (High risk warning)"
        
        # Check if position size is too small to be meaningful
        if position_size.recommended_size < position_size.min_size * 2:
            position_size.confidence *= 0.8
            position_size.notes += " (Small position warning)"
    
    def get_sizing_recommendation(self, 
                                symbol: str,
                                entry_price: float,
                                stop_loss: float,
                                portfolio_value: Optional[float] = None,
                                market_data: Optional[pd.DataFrame] = None,
                                trade_history: Optional[List[float]] = None) -> Dict[SizingMethod, PositionSize]:
        """
        Get position size recommendations from multiple methods.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            portfolio_value: Portfolio value
            market_data: Market data
            trade_history: Trade history
            
        Returns:
            Dictionary of method -> PositionSize
        """
        recommendations = {}
        
        # Methods to evaluate
        methods = [
            SizingMethod.FIXED_FRACTIONAL,
            SizingMethod.VOLATILITY_BASED,
            SizingMethod.KELLY_CRITERION,
        ]
        
        # Add Optimal F if we have trade history
        if trade_history and len(trade_history) > 20:
            methods.append(SizingMethod.OPTIMAL_F)
        
        for method in methods:
            try:
                size = self.calculate_position_size(
                    method=method,
                    symbol=symbol,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    portfolio_value=portfolio_value,
                    market_data=market_data,
                    trade_history=trade_history,
                    win_rate=0.55,  # Default assumptions
                    avg_win=0.025,
                    avg_loss=0.015
                )
                recommendations[method] = size
            except Exception as e:
                logger.error(f"Error calculating {method.value}: {e}")
        
        return recommendations
    
    def get_consensus_size(self, 
                         recommendations: Dict[SizingMethod, PositionSize]) -> PositionSize:
        """
        Get consensus position size from multiple recommendations.
        
        Args:
            recommendations: Dictionary of method -> PositionSize
            
        Returns:
            Consensus PositionSize
        """
        if not recommendations:
            return PositionSize(
                method=SizingMethod.FIXED_FRACTIONAL,
                symbol="",
                recommended_size=self.config["min_position_size"],
                max_size=0,
                min_size=0,
                risk_amount=0,
                risk_percentage=0,
                confidence=0
            )
        
        # Calculate weighted average based on confidence
        total_weight = sum(rec.confidence for rec in recommendations.values())
        
        if total_weight == 0:
            # Use simple average
            avg_size = sum(rec.recommended_size for rec in recommendations.values()) / len(recommendations)
            avg_confidence = sum(rec.confidence for rec in recommendations.values()) / len(recommendations)
        else:
            # Weighted average
            avg_size = sum(rec.recommended_size * rec.confidence 
                          for rec in recommendations.values()) / total_weight
            avg_confidence = sum(rec.confidence for rec in recommendations.values()) / len(recommendations)
        
        # Get representative values from first recommendation
        first_rec = next(iter(recommendations.values()))
        
        consensus = PositionSize(
            method=SizingMethod.ADAPTIVE,
            symbol=first_rec.symbol,
            recommended_size=avg_size,
            max_size=first_rec.max_size,
            min_size=first_rec.min_size,
            risk_amount=first_rec.risk_amount,
            risk_percentage=first_rec.risk_percentage,
            confidence=avg_confidence,
            notes=f"Consensus from {len(recommendations)} methods"
        )
        
        return consensus

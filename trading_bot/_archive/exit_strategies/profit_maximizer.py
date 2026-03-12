"""
Elite Trading Bot - Profit Maximizer

This module provides profit maximization capabilities for the Elite Trading Bot,
optimizing exit strategies for maximum profitability while managing risk.
"""

import enum
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import uuid

import numpy as np
import pandas as pd

from .exit_strategy import ExitStrategy, ExitType, ExitSignal, ExitReason
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class MaximizationStrategy(enum.Enum):
    """Profit maximization strategies."""
    TRAILING_PROFIT = "trailing_profit"           # Trail profits with dynamic stops
    MOMENTUM_RIDING = "momentum_riding"           # Ride momentum until exhaustion
    VOLATILITY_BREAKOUT = "volatility_breakout"   # Exit on volatility breakout
    TREND_FOLLOWING = "trend_following"           # Follow trend until reversal
    MEAN_REVERSION = "mean_reversion"             # Exit on mean reversion signals
    SUPPORT_RESISTANCE = "support_resistance"     # Exit at key S/R levels
    FIBONACCI_EXTENSION = "fibonacci_extension"   # Target Fibonacci extensions
    CUSTOM = "custom"                             # Custom maximization strategy


@dataclass
class MarketCondition:
    """Market condition assessment."""
    trend_strength: float        # -1.0 (strong bearish) to 1.0 (strong bullish)
    volatility_level: float      # 0.0 (low) to 1.0 (high)
    momentum_strength: float     # -1.0 (strong bearish) to 1.0 (strong bullish)
    volume_strength: float       # 0.0 (low) to 1.0 (high)
    support_resistance_nearby: bool  # True if near key S/R level
    timestamp: datetime


class MarketConditionExit:
    """
    Exit strategy based on market condition analysis.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize market condition exit strategy.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        logger.info("MarketConditionExit initialized")
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "trend_strength_threshold": 0.7,      # Strong trend threshold
            "momentum_exhaustion_threshold": 0.3,  # Momentum exhaustion threshold
            "volatility_expansion_threshold": 0.8, # High volatility threshold
            "volume_confirmation_threshold": 0.6,  # Volume confirmation threshold
            "support_resistance_buffer": 0.002,   # 0.2% buffer around S/R levels
            "trend_reversal_confirmation": True,   # Require confirmation for trend reversal
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def assess_market_condition(self, df: pd.DataFrame) -> MarketCondition:
        """
        Assess current market conditions.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            MarketCondition object
        """
        # Calculate trend strength using multiple indicators
        trend_strength = self._calculate_trend_strength(df)
        
        # Calculate volatility level
        volatility_level = self._calculate_volatility_level(df)
        
        # Calculate momentum strength
        momentum_strength = self._calculate_momentum_strength(df)
        
        # Calculate volume strength
        volume_strength = self._calculate_volume_strength(df)
        
        # Check for nearby support/resistance
        support_resistance_nearby = self._check_support_resistance(df)
        
        return MarketCondition(
            trend_strength=trend_strength,
            volatility_level=volatility_level,
            momentum_strength=momentum_strength,
            volume_strength=volume_strength,
            support_resistance_nearby=support_resistance_nearby,
            timestamp=datetime.now()
        )
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate trend strength (-1.0 to 1.0)."""
        if len(df) < 50:
            return 0.0
            
        # Use multiple moving averages
        df = df.copy()
        df['sma20'] = df['close'].rolling(window=20).mean()
        df['sma50'] = df['close'].rolling(window=50).mean()
        df['ema12'] = df['close'].ewm(span=12).mean()
        df['ema26'] = df['close'].ewm(span=26).mean()
        
        # Calculate trend indicators
        current_price = df['close'].iloc[-1]
        sma20 = df['sma20'].iloc[-1]
        sma50 = df['sma50'].iloc[-1]
        ema12 = df['ema12'].iloc[-1]
        ema26 = df['ema26'].iloc[-1]
        
        # Score based on price position relative to MAs
        scores = []
        
        # Price vs SMAs
        if current_price > sma20 > sma50:
            scores.append(1.0)
        elif current_price < sma20 < sma50:
            scores.append(-1.0)
        else:
            scores.append(0.0)
        
        # EMA crossover
        if ema12 > ema26:
            scores.append(0.5)
        else:
            scores.append(-0.5)
        
        # MA slope
        sma20_slope = (df['sma20'].iloc[-1] - df['sma20'].iloc[-5]) / df['sma20'].iloc[-5]
        if sma20_slope > 0.001:
            scores.append(0.5)
        elif sma20_slope < -0.001:
            scores.append(-0.5)
        else:
            scores.append(0.0)
        
        return np.mean(scores)
    
    def _calculate_volatility_level(self, df: pd.DataFrame) -> float:
        """Calculate volatility level (0.0 to 1.0)."""
        if len(df) < 20:
            return 0.5
            
        # Calculate ATR
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        
        # Normalize ATR relative to price
        current_atr = atr.iloc[-1]
        current_price = df['close'].iloc[-1]
        
        atr_percent = (current_atr / current_price) * 100
        
        # Map to 0-1 scale (assuming 0-5% ATR range)
        volatility_level = min(1.0, atr_percent / 5.0)
        
        return volatility_level
    
    def _calculate_momentum_strength(self, df: pd.DataFrame) -> float:
        """Calculate momentum strength (-1.0 to 1.0)."""
        if len(df) < 14:
            return 0.0
            
        # Calculate RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        
        # Map RSI to -1 to 1 scale
        momentum_strength = (current_rsi - 50) / 50
        
        return momentum_strength
    
    def _calculate_volume_strength(self, df: pd.DataFrame) -> float:
        """Calculate volume strength (0.0 to 1.0)."""
        if 'volume' not in df.columns or len(df) < 20:
            return 0.5
            
        # Calculate relative volume
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
        
        if avg_volume == 0:
            return 0.5
            
        relative_volume = current_volume / avg_volume
        
        # Map to 0-1 scale (capped at 3x average volume)
        volume_strength = min(1.0, relative_volume / 3.0)
        
        return volume_strength
    
    def _check_support_resistance(self, df: pd.DataFrame) -> bool:
        """Check if price is near key support/resistance levels."""
        if len(df) < 50:
            return False
            
        current_price = df['close'].iloc[-1]
        buffer = self.config["support_resistance_buffer"]
        
        # Find recent highs and lows
        highs = df['high'].rolling(window=10, center=True).max()
        lows = df['low'].rolling(window=10, center=True).min()
        
        # Check if current price is near any significant level
        for i in range(len(df) - 20, len(df)):
            if pd.notna(highs.iloc[i]):
                level = highs.iloc[i]
                if abs(current_price - level) / level <= buffer:
                    return True
                    
            if pd.notna(lows.iloc[i]):
                level = lows.iloc[i]
                if abs(current_price - level) / level <= buffer:
                    return True
        
        return False
    
    def should_exit_based_on_conditions(self, 
                                      market_condition: MarketCondition,
                                      direction: str,
                                      entry_time: datetime) -> Tuple[bool, Optional[ExitReason]]:
        """
        Determine if exit should be triggered based on market conditions.
        
        Args:
            market_condition: Current market condition
            direction: Trade direction ("long" or "short")
            entry_time: Trade entry time
            
        Returns:
            Tuple of (should_exit, exit_reason)
        """
        # Check for trend reversal
        if direction == "long" and market_condition.trend_strength < -self.config["trend_strength_threshold"]:
            return True, ExitReason.TREND_CHANGE
        elif direction == "short" and market_condition.trend_strength > self.config["trend_strength_threshold"]:
            return True, ExitReason.TREND_CHANGE
        
        # Check for momentum exhaustion
        if direction == "long" and market_condition.momentum_strength < -self.config["momentum_exhaustion_threshold"]:
            return True, ExitReason.INDICATOR_SIGNAL
        elif direction == "short" and market_condition.momentum_strength > self.config["momentum_exhaustion_threshold"]:
            return True, ExitReason.INDICATOR_SIGNAL
        
        # Check for volatility expansion (risk management)
        if market_condition.volatility_level > self.config["volatility_expansion_threshold"]:
            return True, ExitReason.VOLATILITY_EVENT
        
        # Check for support/resistance levels
        if market_condition.support_resistance_nearby:
            # Exit at resistance for long positions, support for short positions
            if direction == "long" and market_condition.trend_strength < 0.5:
                return True, ExitReason.MARKET_STRUCTURE_CHANGE
            elif direction == "short" and market_condition.trend_strength > -0.5:
                return True, ExitReason.MARKET_STRUCTURE_CHANGE
        
        return False, None


class RiskRewardOptimizer:
    """
    Optimizer for risk-reward ratios based on market conditions and trade performance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize risk-reward optimizer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        logger.info("RiskRewardOptimizer initialized")
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "base_risk_reward_ratio": 2.0,        # Base risk-reward ratio
            "max_risk_reward_ratio": 5.0,         # Maximum risk-reward ratio
            "min_risk_reward_ratio": 1.5,         # Minimum risk-reward ratio
            "trend_strength_multiplier": 1.5,     # Multiplier for strong trends
            "volatility_adjustment_factor": 0.8,  # Factor for high volatility
            "momentum_bonus": 0.5,                 # Bonus for strong momentum
            "volume_confirmation_bonus": 0.3,      # Bonus for volume confirmation
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def optimize_risk_reward(self, 
                           market_condition: MarketCondition,
                           direction: str,
                           entry_price: float,
                           stop_loss: float) -> Tuple[float, float]:
        """
        Optimize risk-reward ratio based on market conditions.
        
        Args:
            market_condition: Current market condition
            direction: Trade direction
            entry_price: Entry price
            stop_loss: Stop loss level
            
        Returns:
            Tuple of (optimized_risk_reward_ratio, take_profit_level)
        """
        # Start with base ratio
        risk_reward = self.config["base_risk_reward_ratio"]
        
        # Adjust based on trend strength
        if direction == "long" and market_condition.trend_strength > 0.5:
            risk_reward *= self.config["trend_strength_multiplier"]
        elif direction == "short" and market_condition.trend_strength < -0.5:
            risk_reward *= self.config["trend_strength_multiplier"]
        
        # Adjust based on momentum
        if direction == "long" and market_condition.momentum_strength > 0.5:
            risk_reward += self.config["momentum_bonus"]
        elif direction == "short" and market_condition.momentum_strength < -0.5:
            risk_reward += self.config["momentum_bonus"]
        
        # Adjust based on volume
        if market_condition.volume_strength > self.config["volume_confirmation_threshold"]:
            risk_reward += self.config["volume_confirmation_bonus"]
        
        # Adjust based on volatility (reduce target in high volatility)
        if market_condition.volatility_level > 0.7:
            risk_reward *= self.config["volatility_adjustment_factor"]
        
        # Apply limits
        risk_reward = max(self.config["min_risk_reward_ratio"], 
                         min(self.config["max_risk_reward_ratio"], risk_reward))
        
        # Calculate take profit level
        risk = abs(entry_price - stop_loss)
        
        if direction == "long":
            take_profit = entry_price + (risk * risk_reward)
        else:
            take_profit = entry_price - (risk * risk_reward)
        
        return risk_reward, take_profit


class ProfitMaximizer(ExitStrategy):
    """
    Advanced profit maximization system that combines multiple strategies
    to optimize trade exits for maximum profitability.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize profit maximizer.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        
        # Initialize components
        self.market_condition_exit = MarketConditionExit(
            self.config.get("market_condition_config")
        )
        self.risk_reward_optimizer = RiskRewardOptimizer(
            self.config.get("risk_reward_config")
        )
        
        # Active profit maximization trades
        self.active_trades: Dict[str, Dict[str, Any]] = {}
        
        logger.info("ProfitMaximizer initialized")
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        super()._init_default_config()
        
        defaults = {
            "maximization_strategy": MaximizationStrategy.TRAILING_PROFIT,
            "enable_dynamic_targets": True,        # Enable dynamic target adjustment
            "enable_momentum_riding": True,        # Enable momentum riding
            "momentum_threshold": 0.7,             # Threshold for momentum riding
            "profit_protection_threshold": 1.0,    # Protect profits above this %
            "trailing_profit_distance": 0.5,      # Trailing distance for profits
            "enable_fibonacci_targets": True,      # Enable Fibonacci extension targets
            "fibonacci_extensions": [1.272, 1.618, 2.0, 2.618],  # Fibonacci extension levels
            "max_hold_time_hours": 72,             # Maximum hold time for profit maximization
            "profit_acceleration_factor": 1.2,    # Factor to accelerate profit taking in strong moves
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def register_trade_for_maximization(self, 
                                      trade_id: str,
                                      symbol: str,
                                      entry_price: float,
                                      direction: str,
                                      stop_loss: float,
                                      initial_take_profit: float,
                                      entry_time: datetime,
                                      market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Register a trade for profit maximization.
        
        Args:
            trade_id: Unique trade identifier
            symbol: Trading symbol
            entry_price: Entry price
            direction: Trade direction
            stop_loss: Initial stop loss
            initial_take_profit: Initial take profit
            entry_time: Entry time
            market_data: Market data for analysis
            
        Returns:
            Trade maximization info
        """
        # Assess market conditions
        market_condition = self.market_condition_exit.assess_market_condition(market_data)
        
        # Optimize risk-reward ratio
        optimized_rr, optimized_tp = self.risk_reward_optimizer.optimize_risk_reward(
            market_condition=market_condition,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss
        )
        
        # Calculate Fibonacci extension targets if enabled
        fib_targets = []
        if self.config["enable_fibonacci_targets"]:
            risk = abs(entry_price - stop_loss)
            
            for extension in self.config["fibonacci_extensions"]:
                if direction == "long":
                    target = entry_price + (risk * extension)
                else:
                    target = entry_price - (risk * extension)
                
                fib_targets.append({
                    "level": extension,
                    "price": target,
                    "hit": False
                })
        
        # Create trade maximization info
        max_info = {
            "id": trade_id,
            "symbol": symbol,
            "entry_price": entry_price,
            "direction": direction,
            "initial_stop_loss": stop_loss,
            "current_stop_loss": stop_loss,
            "initial_take_profit": initial_take_profit,
            "optimized_take_profit": optimized_tp,
            "current_take_profit": optimized_tp,
            "entry_time": entry_time,
            "market_condition": market_condition,
            "optimized_risk_reward": optimized_rr,
            "fibonacci_targets": fib_targets,
            "highest_profit": 0.0,
            "trailing_profit_active": False,
            "momentum_riding_active": False,
            "profit_milestones": [],
            "last_update": entry_time
        }
        
        # Store trade
        self.active_trades[trade_id] = max_info
        
        logger.info(f"Registered trade {trade_id} for profit maximization with RR {optimized_rr:.2f}")
        
        return max_info
    
    def update_profit_maximization(self, 
                                 trade_id: str,
                                 current_price: float,
                                 current_time: datetime,
                                 market_data: pd.DataFrame) -> List[ExitSignal]:
        """
        Update profit maximization for a trade.
        
        Args:
            trade_id: Trade identifier
            current_price: Current price
            current_time: Current time
            market_data: Current market data
            
        Returns:
            List of exit signals
        """
        if trade_id not in self.active_trades:
            logger.warning(f"Trade {trade_id} not found in profit maximization")
            return []
        
        trade = self.active_trades[trade_id]
        exit_signals = []
        
        # Update market conditions
        trade["market_condition"] = self.market_condition_exit.assess_market_condition(market_data)
        trade["last_update"] = current_time
        
        # Calculate current profit
        entry_price = trade["entry_price"]
        direction = trade["direction"]
        
        if direction == "long":
            profit_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            profit_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Update highest profit achieved
        if profit_pct > trade["highest_profit"]:
            trade["highest_profit"] = profit_pct
            
            # Record profit milestone
            if profit_pct >= 1.0 and len([m for m in trade["profit_milestones"] if m["profit"] >= profit_pct]) == 0:
                trade["profit_milestones"].append({
                    "time": current_time,
                    "price": current_price,
                    "profit": profit_pct
                })
        
        # Check for market condition exits
        should_exit, exit_reason = self.market_condition_exit.should_exit_based_on_conditions(
            market_condition=trade["market_condition"],
            direction=direction,
            entry_time=trade["entry_time"]
        )
        
        if should_exit:
            signal = self.create_exit_signal(
                symbol=trade["symbol"],
                exit_reason=exit_reason,
                exit_price=current_price,
                position_id=trade_id,
                direction=direction
            )
            exit_signals.append(signal)
            
            # Remove from active trades
            del self.active_trades[trade_id]
            return exit_signals
        
        # Check Fibonacci targets
        if self.config["enable_fibonacci_targets"]:
            for target in trade["fibonacci_targets"]:
                if not target["hit"]:
                    target_hit = False
                    
                    if direction == "long" and current_price >= target["price"]:
                        target_hit = True
                    elif direction == "short" and current_price <= target["price"]:
                        target_hit = True
                    
                    if target_hit:
                        target["hit"] = True
                        
                        # Create partial exit signal at Fibonacci level
                        signal = ExitSignal(
                            id=f"fib_max_{trade_id}_{target['level']}",
                            symbol=trade["symbol"],
                            timestamp=current_time,
                            exit_type=ExitType.FIBONACCI_EXIT,
                            exit_reason=ExitReason.TARGET_REACHED,
                            price=target["price"],
                            position_id=trade_id,
                            direction=direction,
                            size_percentage=25.0,  # Exit 25% at each Fibonacci level
                            confidence=1.0,
                            notes=f"Fibonacci extension {target['level']} reached"
                        )
                        
                        exit_signals.append(signal)
                        
                        logger.info(f"Fibonacci target {target['level']} hit for trade {trade_id}")
        
        # Activate trailing profit if threshold reached
        if (not trade["trailing_profit_active"] and 
            profit_pct >= self.config["profit_protection_threshold"]):
            
            trade["trailing_profit_active"] = True
            logger.info(f"Activated trailing profit for trade {trade_id}")
        
        # Update trailing profit stop
        if trade["trailing_profit_active"]:
            trailing_distance = self.config["trailing_profit_distance"]
            
            if direction == "long":
                new_stop = current_price * (1 - trailing_distance / 100)
                if new_stop > trade["current_stop_loss"]:
                    trade["current_stop_loss"] = new_stop
            else:
                new_stop = current_price * (1 + trailing_distance / 100)
                if new_stop < trade["current_stop_loss"]:
                    trade["current_stop_loss"] = new_stop
        
        # Activate momentum riding if conditions are met
        if (self.config["enable_momentum_riding"] and 
            not trade["momentum_riding_active"] and
            abs(trade["market_condition"].momentum_strength) >= self.config["momentum_threshold"]):
            
            trade["momentum_riding_active"] = True
            
            # Extend take profit target for momentum riding
            risk = abs(entry_price - trade["initial_stop_loss"])
            extended_rr = trade["optimized_risk_reward"] * self.config["profit_acceleration_factor"]
            
            if direction == "long":
                extended_tp = entry_price + (risk * extended_rr)
            else:
                extended_tp = entry_price - (risk * extended_rr)
            
            trade["current_take_profit"] = extended_tp
            
            logger.info(f"Activated momentum riding for trade {trade_id}, extended TP to {extended_tp}")
        
        # Check for maximum hold time
        hold_time = current_time - trade["entry_time"]
        max_hold_time = timedelta(hours=self.config["max_hold_time_hours"])
        
        if hold_time >= max_hold_time:
            signal = self.create_exit_signal(
                symbol=trade["symbol"],
                exit_reason=ExitReason.TIME_EXIT,
                exit_price=current_price,
                position_id=trade_id,
                direction=direction
            )
            exit_signals.append(signal)
            
            # Remove from active trades
            del self.active_trades[trade_id]
            
            logger.info(f"Maximum hold time reached for trade {trade_id}")
        
        return exit_signals
    
    def get_maximization_summary(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        Get profit maximization summary for a trade.
        
        Args:
            trade_id: Trade identifier
            
        Returns:
            Maximization summary or None if not found
        """
        if trade_id not in self.active_trades:
            return None
        
        trade = self.active_trades[trade_id]
        
        # Calculate current performance
        current_profit = 0.0
        if trade["market_condition"]:
            # This would be calculated based on current price
            # For now, use highest profit as approximation
            current_profit = trade["highest_profit"]
        
        summary = {
            "id": trade["id"],
            "symbol": trade["symbol"],
            "direction": trade["direction"],
            "entry_price": trade["entry_price"],
            "current_stop_loss": trade["current_stop_loss"],
            "current_take_profit": trade["current_take_profit"],
            "optimized_risk_reward": trade["optimized_risk_reward"],
            "highest_profit_pct": trade["highest_profit"],
            "current_profit_pct": current_profit,
            "trailing_profit_active": trade["trailing_profit_active"],
            "momentum_riding_active": trade["momentum_riding_active"],
            "fibonacci_targets_hit": len([t for t in trade["fibonacci_targets"] if t["hit"]]),
            "total_fibonacci_targets": len(trade["fibonacci_targets"]),
            "profit_milestones": len(trade["profit_milestones"]),
            "market_condition": {
                "trend_strength": trade["market_condition"].trend_strength,
                "volatility_level": trade["market_condition"].volatility_level,
                "momentum_strength": trade["market_condition"].momentum_strength,
                "volume_strength": trade["market_condition"].volume_strength
            }
        }
        
        return summary
    
    def get_all_maximization_summaries(self) -> List[Dict[str, Any]]:
        """
        Get profit maximization summaries for all active trades.
        
        Returns:
            List of maximization summaries
        """
        summaries = []
        
        for trade_id in self.active_trades:
            summary = self.get_maximization_summary(trade_id)
            if summary:
                summaries.append(summary)
        
        return summaries
    
    def remove_trade_from_maximization(self, trade_id: str) -> bool:
        """
        Remove a trade from profit maximization.
        
        Args:
            trade_id: Trade identifier
            
        Returns:
            True if trade was removed, False if not found
        """
        if trade_id in self.active_trades:
            del self.active_trades[trade_id]
            logger.info(f"Removed trade {trade_id} from profit maximization")
            return True
        
        return False

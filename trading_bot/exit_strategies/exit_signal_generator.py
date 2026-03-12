"""
from datetime import timedelta
Elite Trading Bot - Exit Signal Generator

This module provides exit signal generation capabilities for the Elite Trading Bot,
creating comprehensive exit signals based on multiple analysis methods.
"""

import enum
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import uuid

import numpy as np
import pandas as pd

from .exit_strategy import ExitStrategy, ExitType, ExitSignal, ExitReason
from .adaptive_exits import AdaptiveExitStrategy
from .dynamic_management import DynamicTradeManager
from .profit_maximizer import ProfitMaximizer
from enum import Enum
import datetime
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class ExitStrength(enum.Enum):
    """Strength levels for exit signals."""
    VERY_STRONG = "very_strong"    # Very strong exit signal
    STRONG = "strong"              # Strong exit signal
    MODERATE = "moderate"          # Moderate exit signal
    WEAK = "weak"                  # Weak exit signal
    VERY_WEAK = "very_weak"        # Very weak exit signal


class ExitConfirmation(enum.Enum):
    """Types of exit confirmations."""
    PRICE_ACTION = "price_action"                    # Price action confirmation
    VOLUME_CONFIRMATION = "volume_confirmation"      # Volume confirmation
    INDICATOR_DIVERGENCE = "indicator_divergence"    # Indicator divergence
    TREND_REVERSAL = "trend_reversal"               # Trend reversal confirmation
    SUPPORT_RESISTANCE = "support_resistance"        # Support/resistance level
    TIME_BASED = "time_based"                       # Time-based confirmation
    VOLATILITY_EXPANSION = "volatility_expansion"    # Volatility expansion
    MOMENTUM_EXHAUSTION = "momentum_exhaustion"      # Momentum exhaustion
    FIBONACCI_LEVEL = "fibonacci_level"             # Fibonacci level reached
    MARKET_STRUCTURE = "market_structure"           # Market structure change
    MULTI_TIMEFRAME = "multi_timeframe"             # Multi-timeframe alignment
    CUSTOM = "custom"                               # Custom confirmation


class MultiTimeframeExitAnalyzer:
    """
    Analyzes exit conditions across multiple timeframes.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize multi-timeframe exit analyzer.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            logger.info("MultiTimeframeExitAnalyzer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            defaults = {
                "timeframes": ["5m", "15m", "1h", "4h"],
                "primary_timeframe": "1h",
                "confirmation_timeframes": ["15m", "4h"],
                "min_confirmations": 2,
                "trend_sma_period": 50,
                "momentum_rsi_period": 14,
                "volume_ma_period": 20
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def analyze_exit_conditions(self, 
                              symbol: str,
                              direction: str,
                              data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Analyze exit conditions across multiple timeframes.
        
        Args:
            symbol: Symbol to analyze
            direction: Trade direction ("long" or "short")
            data: Dictionary of timeframe -> OHLCV DataFrame
            
        Returns:
            Dictionary with analysis results
        """
        try:
            results = {
                "symbol": symbol,
                "direction": direction,
                "timestamp": datetime.now(),
                "timeframe_analysis": {},
                "confirmations": [],
                "overall_strength": ExitStrength.WEAK,
                "should_exit": False
            }
        
            confirmation_count = 0
            total_strength = 0.0
        
            # Analyze each timeframe
            for timeframe in self.config["timeframes"]:
                if timeframe not in data or data[timeframe].empty:
                    continue
                
                df = data[timeframe]
            
                # Analyze this timeframe
                tf_analysis = self._analyze_timeframe(df, direction, timeframe)
                results["timeframe_analysis"][timeframe] = tf_analysis
            
                # Count confirmations
                if tf_analysis["exit_signal"]:
                    confirmation_count += 1
                    results["confirmations"].extend(tf_analysis["confirmations"])
                    total_strength += tf_analysis["strength_score"]
        
            # Calculate overall strength
            if len(results["timeframe_analysis"]) > 0:
                avg_strength = total_strength / len(results["timeframe_analysis"])
                results["overall_strength"] = self._map_strength_score(avg_strength)
        
            # Determine if should exit
            results["should_exit"] = confirmation_count >= self.config["min_confirmations"]
        
            return results
        except Exception as e:
            logger.error(f"Error in analyze_exit_conditions: {e}")
            raise
    
    def _analyze_timeframe(self, 
                         df: pd.DataFrame, 
                         direction: str,
                         timeframe: str) -> Dict[str, Any]:
        """
        Analyze exit conditions for a single timeframe.
        
        Args:
            df: OHLCV DataFrame
            direction: Trade direction
            timeframe: Timeframe
            
        Returns:
            Timeframe analysis results
        """
        try:
            analysis = {
                "timeframe": timeframe,
                "exit_signal": False,
                "confirmations": [],
                "strength_score": 0.0,
                "reasons": []
            }
        
            # Calculate indicators
            df = df.copy()
        
            # Trend indicators
            df['sma'] = df['close'].rolling(window=self.config["trend_sma_period"]).mean()
        
            # Momentum indicators
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
        
            avg_gain = gain.rolling(window=self.config["momentum_rsi_period"]).mean()
            avg_loss = loss.rolling(window=self.config["momentum_rsi_period"]).mean()
        
            rs = avg_gain / avg_loss
            df['rsi'] = 100 - (100 / (1 + rs))
        
            # Volume indicators
            if 'volume' in df.columns:
                df['vol_ma'] = df['volume'].rolling(window=self.config["volume_ma_period"]).mean()
                df['rel_volume'] = df['volume'] / df['vol_ma']
        
            # Get latest values
            if len(df) < self.config["trend_sma_period"]:
                return analysis
            
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
        
            # Check trend reversal
            trend_reversal = False
            if direction == "long":
                # Check for bearish reversal
                if (latest['close'] < latest['sma'] and 
                    prev['close'] >= prev['sma']):
                    trend_reversal = True
                    analysis["confirmations"].append(ExitConfirmation.TREND_REVERSAL)
                    analysis["reasons"].append("Bearish trend reversal")
            else:
                # Check for bullish reversal
                if (latest['close'] > latest['sma'] and 
                    prev['close'] <= prev['sma']):
                    trend_reversal = True
                    analysis["confirmations"].append(ExitConfirmation.TREND_REVERSAL)
                    analysis["reasons"].append("Bullish trend reversal")
        
            # Check momentum exhaustion
            momentum_exhaustion = False
            if direction == "long" and latest['rsi'] > 70:
                momentum_exhaustion = True
                analysis["confirmations"].append(ExitConfirmation.MOMENTUM_EXHAUSTION)
                analysis["reasons"].append("Overbought conditions")
            elif direction == "short" and latest['rsi'] < 30:
                momentum_exhaustion = True
                analysis["confirmations"].append(ExitConfirmation.MOMENTUM_EXHAUSTION)
                analysis["reasons"].append("Oversold conditions")
        
            # Check volume confirmation
            volume_confirmation = False
            if 'rel_volume' in df.columns and latest['rel_volume'] > 1.5:
                # High volume on potential reversal candle
                if direction == "long" and latest['close'] < latest['open']:
                    volume_confirmation = True
                    analysis["confirmations"].append(ExitConfirmation.VOLUME_CONFIRMATION)
                    analysis["reasons"].append("High volume bearish candle")
                elif direction == "short" and latest['close'] > latest['open']:
                    volume_confirmation = True
                    analysis["confirmations"].append(ExitConfirmation.VOLUME_CONFIRMATION)
                    analysis["reasons"].append("High volume bullish candle")
        
            # Calculate strength score
            strength_factors = []
        
            if trend_reversal:
                strength_factors.append(0.4)
            if momentum_exhaustion:
                strength_factors.append(0.3)
            if volume_confirmation:
                strength_factors.append(0.3)
        
            analysis["strength_score"] = sum(strength_factors)
            analysis["exit_signal"] = len(analysis["confirmations"]) > 0
        
            return analysis
        except Exception as e:
            logger.error(f"Error in _analyze_timeframe: {e}")
            raise
    
    def _map_strength_score(self, score: float) -> ExitStrength:
        """Map numerical strength score to enum."""
        try:
            if score >= 0.8:
                return ExitStrength.VERY_STRONG
            elif score >= 0.6:
                return ExitStrength.STRONG
            elif score >= 0.4:
                return ExitStrength.MODERATE
            elif score >= 0.2:
                return ExitStrength.WEAK
            else:
                return ExitStrength.VERY_WEAK
        except Exception as e:
            logger.error(f"Error in _map_strength_score: {e}")
            raise


class ExitSignalGenerator:
    """
    Comprehensive exit signal generator that combines multiple exit strategies
    and analysis methods to create high-quality exit signals.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize exit signal generator.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            # Initialize components
            self.adaptive_exit = AdaptiveExitStrategy(self.config.get("adaptive_exit_config"))
            self.dynamic_manager = DynamicTradeManager(self.config.get("dynamic_manager_config"))
            self.profit_maximizer = ProfitMaximizer(self.config.get("profit_maximizer_config"))
            self.mtf_analyzer = MultiTimeframeExitAnalyzer(self.config.get("mtf_analyzer_config"))
        
            # Signal history
            self.signal_history: Dict[str, List[ExitSignal]] = {}
        
            logger.info("ExitSignalGenerator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            defaults = {
                "enable_adaptive_exits": True,
                "enable_dynamic_management": True,
                "enable_profit_maximization": True,
                "enable_multi_timeframe_analysis": True,
                "min_signal_strength": ExitStrength.MODERATE,
                "min_confirmations": 2,
                "signal_expiration_minutes": 30,
                "enable_signal_filtering": True,
                "filter_conflicting_signals": True,
                "max_signals_per_trade": 5
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def register_trade(self, 
                     trade_id: str,
                     symbol: str,
                     entry_price: float,
                     direction: str,
                     stop_loss: float,
                     take_profit: float,
                     entry_time: datetime,
                     position_size: float = 1.0,
                     market_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
        """
        Register a trade for exit signal generation.
        
        Args:
            trade_id: Unique trade identifier
            symbol: Trading symbol
            entry_price: Entry price
            direction: Trade direction
            stop_loss: Stop loss level
            take_profit: Take profit level
            entry_time: Entry time
            position_size: Position size
            market_data: Optional market data for analysis
            
        Returns:
            Registration summary
        """
        try:
            registration_summary = {
                "trade_id": trade_id,
                "registered_strategies": []
            }
        
            # Register with adaptive exits
            if self.config["enable_adaptive_exits"]:
                self.adaptive_exit.register_trade(
                    trade_id=trade_id,
                    symbol=symbol,
                    entry_price=entry_price,
                    direction=direction,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    entry_time=entry_time,
                    size=position_size
                )
                registration_summary["registered_strategies"].append("adaptive_exits")
        
            # Register with dynamic management
            if self.config["enable_dynamic_management"]:
                self.dynamic_manager.register_trade(
                    trade_id=trade_id,
                    symbol=symbol,
                    entry_price=entry_price,
                    direction=direction,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    entry_time=entry_time,
                    position_size=position_size
                )
                registration_summary["registered_strategies"].append("dynamic_management")
        
            # Register with profit maximizer
            if self.config["enable_profit_maximization"] and market_data:
                primary_tf = "1h"  # Default primary timeframe
                if primary_tf in market_data:
                    self.profit_maximizer.register_trade_for_maximization(
                        trade_id=trade_id,
                        symbol=symbol,
                        entry_price=entry_price,
                        direction=direction,
                        stop_loss=stop_loss,
                        initial_take_profit=take_profit,
                        entry_time=entry_time,
                        market_data=market_data[primary_tf]
                    )
                    registration_summary["registered_strategies"].append("profit_maximization")
        
            # Initialize signal history
            self.signal_history[trade_id] = []
        
            logger.info(f"Registered trade {trade_id} with strategies: {registration_summary['registered_strategies']}")
        
            return registration_summary
        except Exception as e:
            logger.error(f"Error in register_trade: {e}")
            raise
    
    def generate_exit_signals(self, 
                            trade_id: str,
                            current_price: float,
                            current_time: datetime,
                            market_data: Dict[str, pd.DataFrame]) -> List[ExitSignal]:
        """
        Generate exit signals for a trade.
        
        Args:
            trade_id: Trade identifier
            current_price: Current price
            current_time: Current time
            market_data: Market data for analysis
            
        Returns:
            List of exit signals
        """
        try:
            all_signals = []
        
            # Get signals from adaptive exits
            if self.config["enable_adaptive_exits"]:
                adaptive_signals = self.adaptive_exit.update_trade(
                    trade_id=trade_id,
                    current_price=current_price,
                    current_time=current_time,
                    market_data=market_data
                )
                all_signals.extend(adaptive_signals)
        
            # Get signals from dynamic management
            if self.config["enable_dynamic_management"]:
                dynamic_signals = self.dynamic_manager.update_trade(
                    trade_id=trade_id,
                    current_price=current_price,
                    current_time=current_time,
                    market_data=market_data.get("1h")  # Use 1h timeframe for dynamic management
                )
                all_signals.extend(dynamic_signals)
        
            # Get signals from profit maximizer
            if self.config["enable_profit_maximization"]:
                profit_signals = self.profit_maximizer.update_profit_maximization(
                    trade_id=trade_id,
                    current_price=current_price,
                    current_time=current_time,
                    market_data=market_data.get("1h", pd.DataFrame())
                )
                all_signals.extend(profit_signals)
        
            # Generate multi-timeframe analysis signals
            if self.config["enable_multi_timeframe_analysis"]:
                mtf_signals = self._generate_mtf_signals(
                    trade_id=trade_id,
                    current_price=current_price,
                    current_time=current_time,
                    market_data=market_data
                )
                all_signals.extend(mtf_signals)
        
            # Filter and enhance signals
            if self.config["enable_signal_filtering"]:
                all_signals = self._filter_signals(all_signals, trade_id)
        
            # Add signals to history
            if trade_id not in self.signal_history:
                self.signal_history[trade_id] = []
        
            self.signal_history[trade_id].extend(all_signals)
        
            # Limit signal history
            max_signals = self.config["max_signals_per_trade"]
            if len(self.signal_history[trade_id]) > max_signals:
                self.signal_history[trade_id] = self.signal_history[trade_id][-max_signals:]
        
            return all_signals
        except Exception as e:
            logger.error(f"Error in generate_exit_signals: {e}")
            raise
    
    def _generate_mtf_signals(self, 
                            trade_id: str,
                            current_price: float,
                            current_time: datetime,
                            market_data: Dict[str, pd.DataFrame]) -> List[ExitSignal]:
        """
        Generate signals based on multi-timeframe analysis.
        
        Args:
            trade_id: Trade identifier
            current_price: Current price
            current_time: Current time
            market_data: Market data
            
        Returns:
            List of exit signals
        """
        try:
            signals = []
        
            # Get trade info from one of the strategies
            trade_info = None
            if self.config["enable_adaptive_exits"]:
                trade_info = self.adaptive_exit.get_trade_info(trade_id)
            elif self.config["enable_dynamic_management"]:
                trade_info = self.dynamic_manager.active_trades.get(trade_id)
        
            if not trade_info:
                return signals
        
            # Analyze multi-timeframe conditions
            mtf_analysis = self.mtf_analyzer.analyze_exit_conditions(
                symbol=trade_info["symbol"],
                direction=trade_info["direction"],
                data=market_data
            )
        
            # Generate signal if conditions are met
            if (mtf_analysis["should_exit"] and 
                mtf_analysis["overall_strength"] != ExitStrength.VERY_WEAK):
            
                # Determine exit reason based on confirmations
                exit_reason = ExitReason.INDICATOR_SIGNAL
                if ExitConfirmation.TREND_REVERSAL in mtf_analysis["confirmations"]:
                    exit_reason = ExitReason.TREND_CHANGE
                elif ExitConfirmation.SUPPORT_RESISTANCE in mtf_analysis["confirmations"]:
                    exit_reason = ExitReason.MARKET_STRUCTURE_CHANGE
                elif ExitConfirmation.VOLATILITY_EXPANSION in mtf_analysis["confirmations"]:
                    exit_reason = ExitReason.VOLATILITY_EVENT
            
                # Create exit signal
                signal = ExitSignal(
                    id=f"mtf_{trade_id}_{int(current_time.timestamp())}",
                    symbol=trade_info["symbol"],
                    timestamp=current_time,
                    exit_type=ExitType.INDICATOR_BASED,
                    exit_reason=exit_reason,
                    price=current_price,
                    position_id=trade_id,
                    direction=trade_info["direction"],
                    size_percentage=100.0,  # Full exit for MTF signals
                    confidence=self._map_strength_to_confidence(mtf_analysis["overall_strength"]),
                    notes=f"Multi-timeframe exit: {', '.join([c.value for c in mtf_analysis['confirmations']])}"
                )
            
                signals.append(signal)
        
            return signals
        except Exception as e:
            logger.error(f"Error in _generate_mtf_signals: {e}")
            raise
    
    def _filter_signals(self, signals: List[ExitSignal], trade_id: str) -> List[ExitSignal]:
        """
        Filter and enhance exit signals.
        
        Args:
            signals: List of exit signals
            trade_id: Trade identifier
            
        Returns:
            Filtered list of exit signals
        """
        try:
            if not signals:
                return signals
        
            filtered_signals = []
        
            # Remove expired signals
            current_time = datetime.now()
            expiration_time = timedelta(minutes=self.config["signal_expiration_minutes"])
        
            for signal in signals:
                if current_time - signal.timestamp <= expiration_time:
                    filtered_signals.append(signal)
        
            # Filter by minimum strength
            min_strength = self.config["min_signal_strength"]
            strength_filtered = []
        
            for signal in filtered_signals:
                signal_strength = self._estimate_signal_strength(signal)
                if signal_strength.value >= min_strength.value:
                    strength_filtered.append(signal)
        
            # Remove conflicting signals if enabled
            if self.config["filter_conflicting_signals"]:
                strength_filtered = self._remove_conflicting_signals(strength_filtered)
        
            # Sort by confidence (highest first)
            strength_filtered.sort(key=lambda x: x.confidence, reverse=True)
        
            return strength_filtered
        except Exception as e:
            logger.error(f"Error in _filter_signals: {e}")
            raise
    
    def _estimate_signal_strength(self, signal: ExitSignal) -> ExitStrength:
        """
        Estimate signal strength based on signal properties.
        
        Args:
            signal: Exit signal
            
        Returns:
            Estimated signal strength
        """
        # Map confidence to strength
        try:
            if signal.confidence >= 0.9:
                return ExitStrength.VERY_STRONG
            elif signal.confidence >= 0.75:
                return ExitStrength.STRONG
            elif signal.confidence >= 0.6:
                return ExitStrength.MODERATE
            elif signal.confidence >= 0.4:
                return ExitStrength.WEAK
            else:
                return ExitStrength.VERY_WEAK
        except Exception as e:
            logger.error(f"Error in _estimate_signal_strength: {e}")
            raise
    
    def _remove_conflicting_signals(self, signals: List[ExitSignal]) -> List[ExitSignal]:
        """
        Remove conflicting signals (e.g., multiple full exits).
        
        Args:
            signals: List of exit signals
            
        Returns:
            List without conflicting signals
        """
        # Group signals by type
        try:
            full_exits = [s for s in signals if s.size_percentage >= 100.0]
            partial_exits = [s for s in signals if s.size_percentage < 100.0]
        
            # Keep only the highest confidence full exit
            if full_exits:
                best_full_exit = max(full_exits, key=lambda x: x.confidence)
                return [best_full_exit] + partial_exits
        
            return signals
        except Exception as e:
            logger.error(f"Error in _remove_conflicting_signals: {e}")
            raise
    
    def _map_strength_to_confidence(self, strength: ExitStrength) -> float:
        """Map exit strength to confidence value."""
        try:
            strength_map = {
                ExitStrength.VERY_STRONG: 0.95,
                ExitStrength.STRONG: 0.8,
                ExitStrength.MODERATE: 0.65,
                ExitStrength.WEAK: 0.45,
                ExitStrength.VERY_WEAK: 0.25
            }
            return strength_map.get(strength, 0.5)
        except Exception as e:
            logger.error(f"Error in _map_strength_to_confidence: {e}")
            raise
    
    def get_signal_history(self, trade_id: str) -> List[ExitSignal]:
        """
        Get signal history for a trade.
        
        Args:
            trade_id: Trade identifier
            
        Returns:
            List of historical exit signals
        """
        return self.signal_history.get(trade_id, [])
    
    def get_trade_summary(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive trade summary from all strategies.
        
        Args:
            trade_id: Trade identifier
            
        Returns:
            Trade summary or None if not found
        """
        try:
            summary = {
                "trade_id": trade_id,
                "strategies": {}
            }
        
            # Get adaptive exit info
            if self.config["enable_adaptive_exits"]:
                adaptive_info = self.adaptive_exit.get_trade_info(trade_id)
                if adaptive_info:
                    summary["strategies"]["adaptive_exits"] = adaptive_info
        
            # Get dynamic management info
            if self.config["enable_dynamic_management"]:
                dynamic_info = self.dynamic_manager.get_trade_summary(trade_id)
                if dynamic_info:
                    summary["strategies"]["dynamic_management"] = dynamic_info
        
            # Get profit maximization info
            if self.config["enable_profit_maximization"]:
                profit_info = self.profit_maximizer.get_maximization_summary(trade_id)
                if profit_info:
                    summary["strategies"]["profit_maximization"] = profit_info
        
            # Get signal history
            summary["signal_history"] = self.get_signal_history(trade_id)
            summary["total_signals"] = len(summary["signal_history"])
        
            return summary if summary["strategies"] else None
        except Exception as e:
            logger.error(f"Error in get_trade_summary: {e}")
            raise
    
    def remove_trade(self, trade_id: str) -> Dict[str, bool]:
        """
        Remove trade from all strategies.
        
        Args:
            trade_id: Trade identifier
            
        Returns:
            Dictionary of strategy -> removal success
        """
        try:
            removal_results = {}
        
            # Remove from adaptive exits
            if self.config["enable_adaptive_exits"]:
                removal_results["adaptive_exits"] = self.adaptive_exit.remove_trade(trade_id)
        
            # Remove from dynamic management
            if self.config["enable_dynamic_management"]:
                removal_results["dynamic_management"] = self.dynamic_manager.remove_trade(trade_id)
        
            # Remove from profit maximizer
            if self.config["enable_profit_maximization"]:
                removal_results["profit_maximization"] = self.profit_maximizer.remove_trade_from_maximization(trade_id)
        
            # Remove signal history
            if trade_id in self.signal_history:
                del self.signal_history[trade_id]
                removal_results["signal_history"] = True
            else:
                removal_results["signal_history"] = False
        
            logger.info(f"Removed trade {trade_id} from exit signal generation")
        
            return removal_results
        except Exception as e:
            logger.error(f"Error in remove_trade: {e}")
            raise

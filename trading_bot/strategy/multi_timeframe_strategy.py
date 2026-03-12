"""
MULTI-TIMEFRAME STRATEGY - PHASE 3 CORE
============================================================

Implements multi-timeframe entry signals for improved win rate.

Features:
- Multi-timeframe confirmation (4H, 1H, 15M)
- Trend alignment across timeframes
- Entry signal generation
- Exit signal generation
- Win rate optimization

Author: AI Assistant
Date: October 24, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional

import numpy as np
import numpy

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend direction."""
    BULLISH = auto()
    BEARISH = auto()
    NEUTRAL = auto()


class TimeFrame(Enum):
    """Trading timeframes."""
    DAILY = "D"
    FOUR_HOUR = "4H"
    ONE_HOUR = "1H"
    FIFTEEN_MIN = "15M"
    FIVE_MIN = "5M"


@dataclass
class TimeFrameAnalysis:
    """Analysis for single timeframe."""
    timeframe: TimeFrame
    trend: TrendDirection
    strength: float  # 0-1
    support: float
    resistance: float
    momentum: float  # -1 to 1
    timestamp: datetime = None
    
    def __post_init__(self):
        try:
            if self.timestamp is None:
                self.timestamp = datetime.now()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


@dataclass
class MultiTimeFrameSignal:
    """Multi-timeframe trading signal."""
    symbol: str
    direction: TrendDirection
    confidence: float  # 0-1
    entry_price: float
    stop_loss: float
    take_profit: float
    timeframes: List[TimeFrameAnalysis]
    timestamp: datetime = None
    
    def __post_init__(self):
        try:
            if self.timestamp is None:
                self.timestamp = datetime.now()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


class MultiTimeFrameStrategy:
    """Multi-timeframe strategy for improved win rate."""
    
    def __init__(self, primary_tf: TimeFrame = TimeFrame.ONE_HOUR,
                 secondary_tf: TimeFrame = TimeFrame.FIFTEEN_MIN,
                 tertiary_tf: TimeFrame = TimeFrame.FIVE_MIN):
        """
        Initialize multi-timeframe strategy.
        
        Args:
            primary_tf: Primary timeframe (1H)
            secondary_tf: Secondary timeframe (15M)
            tertiary_tf: Tertiary timeframe (5M)
        """
        try:
            self.primary_tf = primary_tf
            self.secondary_tf = secondary_tf
            self.tertiary_tf = tertiary_tf
        
            # Analysis storage
            self.analyses: Dict[str, Dict[TimeFrame, TimeFrameAnalysis]] = {}
            self.signals: List[MultiTimeFrameSignal] = []
        
            logger.info(f"Multi-timeframe strategy initialized: {primary_tf.value}/{secondary_tf.value}/{tertiary_tf.value}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_analysis(self, symbol: str, timeframe: TimeFrame, 
                    analysis: TimeFrameAnalysis):
        """Add timeframe analysis."""
        try:
            if symbol not in self.analyses:
                self.analyses[symbol] = {}
        
            self.analyses[symbol][timeframe] = analysis
            logger.debug(f"{symbol} {timeframe.value}: {analysis.trend.name} (strength: {analysis.strength:.2f})")
        except Exception as e:
            logger.error(f"Error in add_analysis: {e}")
            raise
    
    def generate_signal(self, symbol: str) -> Optional[MultiTimeFrameSignal]:
        """
        Generate trading signal from multi-timeframe analysis.
        
        Returns:
            Signal if all timeframes align, None otherwise
        """
        try:
            if symbol not in self.analyses:
                return None
        
            analyses = self.analyses[symbol]
        
            # Check if all required timeframes present
            required_tfs = [self.primary_tf, self.secondary_tf, self.tertiary_tf]
            if not all(tf in analyses for tf in required_tfs):
                return None
        
            # Get analyses
            primary = analyses[self.primary_tf]
            secondary = analyses[self.secondary_tf]
            tertiary = analyses[self.tertiary_tf]
        
            # Check trend alignment
            if not self._trends_aligned(primary, secondary, tertiary):
                return None
        
            # Calculate confidence
            confidence = self._calculate_confidence(primary, secondary, tertiary)
        
            if confidence < 0.6:  # Minimum confidence threshold
                return None
        
            # Determine direction
            direction = primary.trend
        
            # Calculate entry, SL, TP
            entry_price = self._calculate_entry(symbol, direction, tertiary)
            stop_loss = self._calculate_stop_loss(symbol, direction, primary)
            take_profit = self._calculate_take_profit(symbol, direction, primary)
        
            # Create signal
            signal = MultiTimeFrameSignal(
                symbol=symbol,
                direction=direction,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                timeframes=[primary, secondary, tertiary]
            )
        
            self.signals.append(signal)
            logger.info(f"Signal generated for {symbol}: {direction.name} (confidence: {confidence:.2f})")
        
            return signal
        except Exception as e:
            logger.error(f"Error in generate_signal: {e}")
            raise
    
    def _trends_aligned(self, primary: TimeFrameAnalysis,
                       secondary: TimeFrameAnalysis,
                       tertiary: TimeFrameAnalysis) -> bool:
        """Check if trends are aligned across timeframes."""
        # Primary and secondary must align
        try:
            if primary.trend != secondary.trend:
                return False
        
            # Tertiary should not be opposite
            if tertiary.trend == TrendDirection.NEUTRAL:
                return True
        
            if primary.trend == TrendDirection.NEUTRAL:
                return False
        
            # If tertiary is opposite, reject
            if primary.trend != tertiary.trend:
                return False
        
            return True
        except Exception as e:
            logger.error(f"Error in _trends_aligned: {e}")
            raise
    
    def _calculate_confidence(self, primary: TimeFrameAnalysis,
                             secondary: TimeFrameAnalysis,
                             tertiary: TimeFrameAnalysis) -> float:
        """Calculate signal confidence."""
        # Base confidence from primary trend strength
        try:
            confidence = primary.strength
        
            # Boost if secondary confirms
            if secondary.trend == primary.trend:
                confidence += secondary.strength * 0.2
        
            # Boost if tertiary confirms
            if tertiary.trend == primary.trend:
                confidence += tertiary.strength * 0.1
        
            # Cap at 1.0
            return min(1.0, confidence)
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise
    
    def _calculate_entry(self, symbol: str, direction: TrendDirection,
                        tertiary: TimeFrameAnalysis) -> float:
        """Calculate entry price."""
        try:
            if direction == TrendDirection.BULLISH:
                # Enter on support level
                return tertiary.support
            else:
                # Enter on resistance level
                return tertiary.resistance
        except Exception as e:
            logger.error(f"Error in _calculate_entry: {e}")
            raise
    
    def _calculate_stop_loss(self, symbol: str, direction: TrendDirection,
                            primary: TimeFrameAnalysis) -> float:
        """Calculate stop loss."""
        try:
            if direction == TrendDirection.BULLISH:
                # Stop below support
                return primary.support * 0.995
            else:
                # Stop above resistance
                return primary.resistance * 1.005
        except Exception as e:
            logger.error(f"Error in _calculate_stop_loss: {e}")
            raise
    
    def _calculate_take_profit(self, symbol: str, direction: TrendDirection,
                              primary: TimeFrameAnalysis) -> float:
        """Calculate take profit."""
        try:
            if direction == TrendDirection.BULLISH:
                # Target at resistance
                return primary.resistance * 1.01
            else:
                # Target at support
                return primary.support * 0.99
        except Exception as e:
            logger.error(f"Error in _calculate_take_profit: {e}")
            raise
    
    def get_signal_summary(self, symbol: str) -> str:
        """Get signal summary."""
        try:
            if symbol not in self.analyses:
                return f"No analysis for {symbol}"
        
            analyses = self.analyses[symbol]
        
            summary = f"MULTI-TIMEFRAME ANALYSIS - {symbol}\n"
            summary += "=" * 50 + "\n"
        
            for tf in [self.primary_tf, self.secondary_tf, self.tertiary_tf]:
                if tf in analyses:
                    analysis = analyses[tf]
                    summary += f"{tf.value}: {analysis.trend.name} (strength: {analysis.strength:.2f})\n"
        
            summary += "=" * 50 + "\n"
        
            # Check for signal
            signal = self.generate_signal(symbol)
            if signal:
                summary += f"SIGNAL: {signal.direction.name}\n"
                summary += f"Confidence: {signal.confidence:.1%}\n"
                summary += f"Entry: {signal.entry_price:.5f}\n"
                summary += f"SL: {signal.stop_loss:.5f}\n"
                summary += f"TP: {signal.take_profit:.5f}\n"
            else:
                summary += "No signal generated\n"
        
            return summary
        except Exception as e:
            logger.error(f"Error in get_signal_summary: {e}")
            raise
    
    def reset(self):
        """Reset strategy."""
        try:
            self.analyses.clear()
            self.signals.clear()
            logger.info("Multi-timeframe strategy reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise

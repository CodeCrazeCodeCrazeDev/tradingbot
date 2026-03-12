"""
SPREAD FILTER MODULE - P0 CRITICAL FIX
============================================================

Implements spread filtering to prevent trading during high spread periods.

Features:
- Real-time spread tracking
- Average spread calculation
- Spread multiplier detection
- Automatic trade rejection on high spread

Author: AI Assistant
Date: October 23, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

import numpy as np
from loguru import logger
import numpy


@dataclass
class SpreadMetrics:
    """Spread metrics for a symbol."""
    symbol: str
    current_spread: float
    average_spread: float
    spread_multiplier: float
    is_acceptable: bool
    timestamp: datetime


class SpreadFilter:
    """Filters trades based on spread conditions."""
    
    def __init__(self, max_spread_multiplier: float = 2.0, 
                 lookback_period: int = 100):
        """
        Initialize spread filter.
        
        Args:
            max_spread_multiplier: Maximum allowed spread multiplier (default 2.0x)
            lookback_period: Number of spreads to track (default 100)
        """
        try:
            self.max_spread_multiplier = max_spread_multiplier
            self.lookback_period = lookback_period
            self.spread_history: Dict[str, deque] = {}
            self.metrics_history: Dict[str, deque] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_spread(self, symbol: str, bid: float, ask: float):
        """
        Update spread for symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            bid: Bid price
            ask: Ask price
        """
        try:
            if symbol not in self.spread_history:
                self.spread_history[symbol] = deque(maxlen=self.lookback_period)
                self.metrics_history[symbol] = deque(maxlen=self.lookback_period)
        
            spread = ask - bid
            self.spread_history[symbol].append(spread)
        
            logger.debug(f"{symbol} spread updated: {spread:.5f} (bid: {bid}, ask: {ask})")
        except Exception as e:
            logger.error(f"Error in update_spread: {e}")
            raise
    
    def is_spread_acceptable(self, symbol: str, bid: float, ask: float) -> bool:
        """
        Check if current spread is acceptable.
        
        Args:
            symbol: Trading symbol
            bid: Bid price
            ask: Ask price
            
        Returns:
            True if spread is acceptable, False otherwise
        """
        try:
            metrics = self.get_metrics(symbol, bid, ask)
            return metrics.is_acceptable
        except Exception as e:
            logger.error(f"Error in is_spread_acceptable: {e}")
            raise
    
    def get_metrics(self, symbol: str, bid: float, ask: float) -> SpreadMetrics:
        """
        Get spread metrics for symbol.
        
        Args:
            symbol: Trading symbol
            bid: Bid price
            ask: Ask price
            
        Returns:
            SpreadMetrics object
        """
        try:
            current_spread = ask - bid
        
            # No history yet
            if symbol not in self.spread_history or not self.spread_history[symbol]:
                metrics = SpreadMetrics(
                    symbol=symbol,
                    current_spread=current_spread,
                    average_spread=current_spread,
                    spread_multiplier=1.0,
                    is_acceptable=True,
                    timestamp=datetime.now()
                )
                return metrics
        
            # Calculate average
            avg_spread = np.mean(list(self.spread_history[symbol]))
        
            # Calculate multiplier
            spread_multiplier = current_spread / avg_spread if avg_spread > 0 else 1.0
        
            # Check if acceptable
            is_acceptable = spread_multiplier <= self.max_spread_multiplier
        
            metrics = SpreadMetrics(
                symbol=symbol,
                current_spread=current_spread,
                average_spread=avg_spread,
                spread_multiplier=spread_multiplier,
                is_acceptable=is_acceptable,
                timestamp=datetime.now()
            )
        
            # Store metrics
            if symbol not in self.metrics_history:
                self.metrics_history[symbol] = deque(maxlen=self.lookback_period)
            self.metrics_history[symbol].append(metrics)
        
            return metrics
        except Exception as e:
            logger.error(f"Error in get_metrics: {e}")
            raise
    
    def get_average_spread(self, symbol: str) -> float:
        """Get average spread for symbol."""
        try:
            if symbol not in self.spread_history or not self.spread_history[symbol]:
                return 0
        
            return np.mean(list(self.spread_history[symbol]))
        except Exception as e:
            logger.error(f"Error in get_average_spread: {e}")
            raise
    
    def get_spread_status(self, symbol: str, bid: float, ask: float) -> str:
        """Get human-readable spread status."""
        try:
            metrics = self.get_metrics(symbol, bid, ask)
        
            status = "✓ ACCEPTABLE" if metrics.is_acceptable else "✗ TOO HIGH"
        
            return f"""
    SPREAD STATUS - {symbol}
    {'=' * 50}
    Status: {status}
    Current Spread: {metrics.current_spread:.5f}
    Average Spread: {metrics.average_spread:.5f}
    Multiplier: {metrics.spread_multiplier:.2f}x (Max: {self.max_spread_multiplier:.2f}x)
    {'=' * 50}
    """
        except Exception as e:
            logger.error(f"Error in get_spread_status: {e}")
            raise
    
    def get_all_metrics(self) -> Dict[str, SpreadMetrics]:
        """Get latest metrics for all symbols."""
        try:
            result = {}
        
            for symbol in self.metrics_history:
                if self.metrics_history[symbol]:
                    result[symbol] = self.metrics_history[symbol][-1]
        
            return result
        except Exception as e:
            logger.error(f"Error in get_all_metrics: {e}")
            raise
    
    def reset_symbol(self, symbol: str):
        """Reset history for symbol."""
        try:
            if symbol in self.spread_history:
                self.spread_history[symbol].clear()
            if symbol in self.metrics_history:
                self.metrics_history[symbol].clear()
        
            logger.info(f"Spread history reset for {symbol}")
        except Exception as e:
            logger.error(f"Error in reset_symbol: {e}")
            raise
    
    def reset_all(self):
        """Reset all history."""
        try:
            self.spread_history.clear()
            self.metrics_history.clear()
            logger.info("All spread history reset")
        except Exception as e:
            logger.error(f"Error in reset_all: {e}")
            raise

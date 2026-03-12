"""
Base Strategy Module - Compatibility Wrapper
Provides base classes for trading strategies
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import pandas as pd

import logging

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"

@dataclass
class TradingSignal:
    """Trading signal data structure"""
    signal_type: SignalType
    symbol: str
    confidence: float
    timestamp: pd.Timestamp
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        try:
            if self.metadata is None:
                self.metadata = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __post_init__: {e}")
            raise

class BaseStrategy(ABC):
    """
    Base class for all trading strategies
    
    All strategies should inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy
        
        Args:
            config: Strategy configuration dictionary
        """
        try:
            self.config = config or {}
            self.name = self.__class__.__name__
            self.is_initialized = False
            self.parameters = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    @abstractmethod
    def analyze_market(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze market data
        
        Args:
            data: Market data DataFrame with OHLCV columns
            
        Returns:
            Dictionary with analysis results
        """
        pass
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame, 
                       analysis: Optional[Dict[str, Any]] = None) -> TradingSignal:
        """
        Generate trading signal
        
        Args:
            data: Market data DataFrame
            analysis: Optional pre-computed analysis results
            
        Returns:
            TradingSignal object
        """
        pass
    
    def filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Filter and validate signals
        
        Args:
            signals: List of trading signals
            
        Returns:
            Filtered list of signals
        """
        # Default implementation: return all signals
        return signals
    
    def update_parameters(self, parameters: Dict[str, Any]):
        """
        Update strategy parameters
        
        Args:
            parameters: Dictionary of parameters to update
        """
        try:
            self.parameters.update(parameters)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update_parameters: {e}")
            raise
    
    def initialize(self):
        """Initialize strategy (called before first use)"""
        try:
            self.is_initialized = True
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in initialize: {e}")
            raise
    
    def shutdown(self):
        """Cleanup strategy resources"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'parameters': self.parameters,
            'is_initialized': self.is_initialized
        }

# Export for compatibility
__all__ = ['BaseStrategy', 'TradingSignal', 'SignalType']

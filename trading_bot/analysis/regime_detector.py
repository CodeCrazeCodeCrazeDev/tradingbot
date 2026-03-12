"""
Regime Detector - Alias module for market_regime_detector.

This module provides backward-compatible imports for the regime detection
functionality documented in the system architecture.
"""

# Re-export everything from the actual implementation
from trading_bot.analysis.market_regime_detector import *  # noqa: F401, F403

try:
    from trading_bot.analysis.market_regime_detector import (
        MarketRegimeDetector,
        RegimeType,
    )
except ImportError:
    pass

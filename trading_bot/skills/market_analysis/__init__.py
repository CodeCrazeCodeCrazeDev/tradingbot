"""
Market Analysis Module
============================================================

Auto-generated integration file.
"""

# auction_market
try:
    from .auction_market import (
        AuctionMarketTheoryEngine,
    )
except ImportError as e:
    # auction_market not available
    pass

# sweep_detection
try:
    from .sweep_detection import (
        SweepDetectionSystem,
    )
except ImportError as e:
    # sweep_detection not available
    pass

__all__ = [
    'AuctionMarketTheoryEngine',
    'SweepDetectionSystem',
]

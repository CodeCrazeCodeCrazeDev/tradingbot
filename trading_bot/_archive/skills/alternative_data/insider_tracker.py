"""
Skill #81: Insider Trading Tracker
==================================

Tracks insider trading activity for signals.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class InsiderResult:
    """Insider trading result."""
    net_insider_activity: float
    buy_transactions: int
    sell_transactions: int
    notable_insiders: List[str]
    trading_signal: str


class InsiderTradingTracker:
    """Tracks insider trading."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("InsiderTradingTracker initialized")
    
    def track(self, transactions: List[Dict]) -> InsiderResult:
        """Track insider transactions."""
        if not transactions:
            return InsiderResult(0, 0, 0, [], "No insider data")
        
        buys = sum(1 for t in transactions if t.get('type') == 'buy')
        sells = sum(1 for t in transactions if t.get('type') == 'sell')
        net = (buys - sells) / (buys + sells + 1)
        
        notable = list(set(t.get('insider', '') for t in transactions[:5]))
        signal = "INSIDER BUYING" if net > 0.3 else "INSIDER SELLING" if net < -0.3 else "MIXED"
        
        return InsiderResult(
            net_insider_activity=net, buy_transactions=buys, sell_transactions=sells,
            notable_insiders=notable, trading_signal=f"{signal}: Net activity {net:.2f}"
        )

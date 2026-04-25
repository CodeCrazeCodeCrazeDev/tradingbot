"""
Idea #45: Insider Trading Monitor
===================================
Track insider transactions for sentiment signals.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InsiderTradingMonitor:
    """Monitor insider trading activity."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.transactions: Dict[str, List[Dict]] = {}
        self.initialized = False
        self.metrics = {"transactions_tracked": 0}
        
    async def initialize(self):
        logger.info("Initializing Insider Trading Monitor")
        self.initialized = True
        
    async def track_transaction(self, company: str, insider: str, action: str, shares: int) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        if company not in self.transactions:
            self.transactions[company] = []
        self.transactions[company].append({"insider": insider, "action": action, "shares": shares, "timestamp": datetime.now()})
        self.metrics["transactions_tracked"] += 1
        return {"company": company, "signal": "bullish" if action == "buy" else "bearish"}
    
    async def analyze_sentiment(self, company: str) -> Dict[str, Any]:
        txns = self.transactions.get(company, [])
        buys = sum(1 for t in txns if t["action"] == "buy")
        sells = sum(1 for t in txns if t["action"] == "sell")
        return {"company": company, "buy_count": buys, "sell_count": sells, "net_sentiment": buys - sells}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.transactions.clear()
        self.initialized = False

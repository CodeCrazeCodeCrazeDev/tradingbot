"""
Idea #179: Chat Room Monitoring
=================================
Monitor trading chat rooms for sentiment.
"""

import numpy as np
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ChatMonitor:
    """Monitor trading chat rooms."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False
        self.metrics = {"messages_monitored": 0}
        
    async def initialize(self):
        logger.info("Initializing Chat Monitor")
        self.initialized = True
        
    async def monitor(self, messages: List[str], room: str) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        sentiments = [np.random.uniform(-1, 1) for _ in messages]
        avg_sentiment = np.mean(sentiments) if sentiments else 0
        tickers = {}
        for msg in messages:
            if "$" in msg:
                ticker = msg.split("$")[1][:4].upper()
                tickers[ticker] = tickers.get(ticker, 0) + 1
        self.metrics["messages_monitored"] += len(messages)
        return {"room": room, "avg_sentiment": float(avg_sentiment), "top_tickers": sorted(tickers.items(), key=lambda x: x[1], reverse=True)[:5], "message_count": len(messages)}
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
    
    async def shutdown(self):
        self.initialized = False

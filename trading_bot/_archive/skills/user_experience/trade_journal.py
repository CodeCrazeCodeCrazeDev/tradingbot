"""
Skill #98: Trade Journal Analyzer
=================================

Analyzes trade journal for patterns and insights.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class JournalInsight:
    """Trade journal insight."""
    insight_type: str
    description: str
    impact: float


@dataclass
class JournalResult:
    """Trade journal analysis result."""
    total_trades: int
    insights: List[JournalInsight]
    best_performing_setup: str
    worst_performing_setup: str
    trading_signal: str


class TradeJournalAnalyzer:
    """Analyzes trade journals."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.trades: List[Dict] = []
        logger.info("TradeJournalAnalyzer initialized")
    
    def add_trade(self, trade: Dict):
        """Add trade to journal."""
        self.trades.append(trade)
    
    def analyze(self) -> JournalResult:
        """Analyze trade journal."""
        if not self.trades:
            return JournalResult(0, [], "", "", "No trades to analyze")
        
        insights = []
        
        # Win rate by setup
        setups = {}
        for trade in self.trades:
            setup = trade.get('setup', 'unknown')
            pnl = trade.get('pnl', 0)
            if setup not in setups:
                setups[setup] = []
            setups[setup].append(pnl)
        
        best_setup = max(setups, key=lambda s: np.mean(setups[s])) if setups else ""
        worst_setup = min(setups, key=lambda s: np.mean(setups[s])) if setups else ""
        
        insights.append(JournalInsight('setup', f"Best setup: {best_setup}", np.mean(setups.get(best_setup, [0]))))
        
        return JournalResult(
            total_trades=len(self.trades), insights=insights,
            best_performing_setup=best_setup, worst_performing_setup=worst_setup,
            trading_signal=f"JOURNAL: {len(self.trades)} trades, best setup: {best_setup}"
        )

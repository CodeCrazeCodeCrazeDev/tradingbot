"""
Skill #71: Strategy Tournament System
=====================================

Runs tournaments between strategies to select winners.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class TournamentResult:
    """Tournament result."""
    winner: str
    rankings: List[tuple]
    scores: Dict[str, float]
    trading_signal: str


class StrategyTournamentSystem:
    """Runs strategy tournaments."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            logger.info("StrategyTournamentSystem initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def run_tournament(self, strategy_returns: Dict[str, np.ndarray]) -> TournamentResult:
        """Run tournament between strategies."""
        try:
            if not strategy_returns:
                return TournamentResult("", [], {}, "No strategies")
        
            scores = {}
            for name, returns in strategy_returns.items():
                sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
                max_dd = self._max_drawdown(returns)
                scores[name] = sharpe - max_dd
        
            rankings = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            winner = rankings[0][0] if rankings else ""
        
            return TournamentResult(
                winner=winner, rankings=rankings, scores=scores,
                trading_signal=f"WINNER: {winner} with score {scores.get(winner, 0):.2f}"
            )
        except Exception as e:
            logger.error(f"Error in run_tournament: {e}")
            raise
    
    def _max_drawdown(self, returns: np.ndarray) -> float:
        try:
            cumulative = np.cumprod(1 + returns)
            peak = np.maximum.accumulate(cumulative)
            dd = (cumulative - peak) / peak
            return abs(np.min(dd))
        except Exception as e:
            logger.error(f"Error in _max_drawdown: {e}")
            raise

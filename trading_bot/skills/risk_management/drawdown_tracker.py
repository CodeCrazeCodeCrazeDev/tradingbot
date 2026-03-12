"""
Skill #55: Drawdown Duration Tracker
====================================

Tracks drawdown depth and duration for risk monitoring.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class DrawdownResult:
    """Drawdown tracking result."""
    current_drawdown: float
    max_drawdown: float
    drawdown_duration: int
    avg_drawdown_duration: float
    recovery_needed: float
    trading_signal: str


class DrawdownDurationTracker:
    """Tracks drawdown depth and duration."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.peak = 0
            self.drawdown_start = 0
            self.drawdown_durations: List[int] = []
            logger.info("DrawdownDurationTracker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def track(self, equity_curve: np.ndarray) -> DrawdownResult:
        """Track drawdowns in equity curve."""
        try:
            if len(equity_curve) < 2:
                return self._create_empty_result()
        
            # Calculate drawdowns
            peaks = np.maximum.accumulate(equity_curve)
            drawdowns = (equity_curve - peaks) / peaks
        
            current_dd = drawdowns[-1]
            max_dd = np.min(drawdowns)
        
            # Duration
            in_drawdown = drawdowns < 0
            duration = 0
            for i in range(len(in_drawdown) - 1, -1, -1):
                if in_drawdown[i]:
                    duration += 1
                else:
                    break
        
            # Average duration
            durations = []
            current_dur = 0
            for dd in in_drawdown:
                if dd:
                    current_dur += 1
                elif current_dur > 0:
                    durations.append(current_dur)
                    current_dur = 0
            avg_dur = np.mean(durations) if durations else 0
        
            # Recovery needed
            recovery = -current_dd / (1 + current_dd) if current_dd < 0 else 0
        
            signal = self._generate_signal(current_dd, max_dd, duration)
        
            return DrawdownResult(
                current_drawdown=current_dd,
                max_drawdown=max_dd,
                drawdown_duration=duration,
                avg_drawdown_duration=avg_dur,
                recovery_needed=recovery,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in track: {e}")
            raise
    
    def _generate_signal(self, current: float, max_dd: float, duration: int) -> str:
        try:
            if current < -0.2:
                return f"SEVERE DRAWDOWN: {current:.1%}, duration {duration} periods"
            elif current < -0.1:
                return f"MODERATE DRAWDOWN: {current:.1%}, max was {max_dd:.1%}"
            return f"HEALTHY: Current DD {current:.1%}"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> DrawdownResult:
        return DrawdownResult(0, 0, 0, 0, 0, "Insufficient data")

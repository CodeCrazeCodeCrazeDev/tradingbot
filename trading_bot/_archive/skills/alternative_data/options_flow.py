"""
Skill #82: Options Flow Analyzer
================================

Analyzes options flow for directional signals.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class OptionsFlowResult:
    """Options flow analysis result."""
    call_volume: float
    put_volume: float
    put_call_ratio: float
    unusual_activity: List[Dict]
    smart_money_direction: str
    trading_signal: str


class OptionsFlowAnalyzer:
    """Analyzes options flow."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("OptionsFlowAnalyzer initialized")
    
    def analyze(self, options_data: List[Dict]) -> OptionsFlowResult:
        """Analyze options flow."""
        if not options_data:
            return self._create_empty_result()
        
        calls = sum(o.get('volume', 0) for o in options_data if o.get('type') == 'call')
        puts = sum(o.get('volume', 0) for o in options_data if o.get('type') == 'put')
        
        pc_ratio = puts / (calls + 1) if calls > 0 else 1
        
        # Unusual activity
        avg_vol = np.mean([o.get('volume', 0) for o in options_data])
        unusual = [o for o in options_data if o.get('volume', 0) > avg_vol * 3]
        
        direction = "bullish" if pc_ratio < 0.7 else "bearish" if pc_ratio > 1.3 else "neutral"
        
        return OptionsFlowResult(
            call_volume=calls, put_volume=puts, put_call_ratio=pc_ratio,
            unusual_activity=unusual[:5], smart_money_direction=direction,
            trading_signal=f"OPTIONS: P/C ratio {pc_ratio:.2f}, {direction}"
        )
    
    def _create_empty_result(self) -> OptionsFlowResult:
        return OptionsFlowResult(0, 0, 1, [], "unknown", "No options data")

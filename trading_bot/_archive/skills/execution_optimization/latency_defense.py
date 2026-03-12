"""
Skill #38: Latency Arbitrage Defense
====================================

Protects against latency arbitrage and predatory HFT strategies.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class LatencyDefenseResult:
    """Latency defense analysis result."""
    threat_level: str
    detected_patterns: List[str]
    recommended_delay: float
    safe_execution_window: bool
    trading_signal: str


class LatencyArbitrageDefense:
    """Defends against latency arbitrage."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.quote_history: List[tuple] = []
        logger.info("LatencyArbitrageDefense initialized")
    
    def analyze(
        self,
        current_bid: float,
        current_ask: float,
        timestamp: datetime,
        recent_trades: List[Dict]
    ) -> LatencyDefenseResult:
        """Analyze for latency arbitrage threats."""
        self.quote_history.append((timestamp, current_bid, current_ask))
        
        patterns = []
        threat = "low"
        
        # Check for quote flickering
        if self._detect_flickering():
            patterns.append("quote_flickering")
            threat = "medium"
        
        # Check for momentum ignition
        if self._detect_momentum_ignition(recent_trades):
            patterns.append("momentum_ignition")
            threat = "high"
        
        # Check for quote stuffing
        if self._detect_quote_stuffing():
            patterns.append("quote_stuffing")
            threat = "high"
        
        # Recommended delay
        delay = 0.1 if threat == "high" else 0.05 if threat == "medium" else 0
        
        # Safe window
        safe = threat == "low"
        
        signal = self._generate_signal(threat, patterns, delay)
        
        return LatencyDefenseResult(
            threat_level=threat,
            detected_patterns=patterns,
            recommended_delay=delay,
            safe_execution_window=safe,
            trading_signal=signal
        )
    
    def _detect_flickering(self) -> bool:
        """Detect quote flickering."""
        if len(self.quote_history) < 10:
            return False
        recent = self.quote_history[-10:]
        changes = sum(1 for i in range(1, len(recent)) 
                     if recent[i][1] != recent[i-1][1] or recent[i][2] != recent[i-1][2])
        return changes > 7
    
    def _detect_momentum_ignition(self, trades: List[Dict]) -> bool:
        """Detect momentum ignition."""
        if len(trades) < 5:
            return False
        prices = [t.get('price', 0) for t in trades[-5:]]
        return abs(prices[-1] - prices[0]) / prices[0] > 0.005
    
    def _detect_quote_stuffing(self) -> bool:
        """Detect quote stuffing."""
        if len(self.quote_history) < 20:
            return False
        return len(self.quote_history) > 100
    
    def _generate_signal(self, threat: str, patterns: List[str], delay: float) -> str:
        """Generate signal."""
        if threat == "high":
            return f"HIGH THREAT: {', '.join(patterns)}. Delay {delay}s recommended"
        elif threat == "medium":
            return f"CAUTION: {', '.join(patterns)} detected"
        return "SAFE: No latency threats detected"

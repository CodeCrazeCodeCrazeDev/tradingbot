"""
Trading Orchestrator Base Definitions
===================================
Defines TradingSignal, SignalType, and Position compatibility layers.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class TradingSignal:
    symbol: str
    signal_type: SignalType
    confidence: float = 0.5
    price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    reasons: List[str] = field(default_factory=list)

@dataclass
class Position:
    symbol: str
    side: str
    entry_price: float
    quantity: float
    entry_time: datetime = field(default_factory=datetime.now)
    current_price: Optional[float] = None

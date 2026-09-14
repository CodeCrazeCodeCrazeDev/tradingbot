"""Data contracts and schemas for Perception Layer."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
import time


class DataQualityStatus(Enum):
    VALID = "VALID"
    STALE = "STALE"
    CORRUPTED = "CORRUPTED"
    MISSING_FIELDS = "MISSING_FIELDS"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    UNTRUSTED_SOURCE = "UNTRUSTED_SOURCE"


@dataclass
class Observation:
    """Typed contract for incoming market, macro, and news observations."""
    timestamp: float
    instrument: str
    timeframe: str
    source: str
    ohlcv: Dict[str, float]
    order_book: Optional[Dict[str, Any]] = None
    trade_flow: Optional[Dict[str, Any]] = None
    news_sentiment: Optional[Dict[str, Any]] = None
    macro_events: Optional[List[Dict[str, Any]]] = None
    data_version: str = "1.0.0"
    confidence: float = 1.0
    freshness_seconds: float = 0.0
    quality_score: float = 1.0
    status: DataQualityStatus = DataQualityStatus.VALID
    validation_messages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        return self.status == DataQualityStatus.VALID

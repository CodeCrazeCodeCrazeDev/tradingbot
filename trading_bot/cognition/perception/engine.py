"""Data Integrity Firewall and Unified Perception Engine."""

import time
import logging
from typing import Dict, Any, Optional, List
from .contracts import Observation, DataQualityStatus

logger = logging.getLogger("alphaalgo.cognition.perception")


class DataIntegrityFirewall:
    """Firewall to inspect, validate, and sanitize incoming market data observations."""

    def __init__(
        self,
        max_stale_seconds: float = 300.0,
        allowed_sources: Optional[List[str]] = None,
        price_sanity_bounds: Optional[Dict[str, tuple]] = None
    ):
        self.max_stale_seconds = max_stale_seconds
        self.allowed_sources = set(allowed_sources) if allowed_sources else {"mt5", "bloomberg", "reuters", "simulated", "paper_feed"}
        self.price_sanity_bounds = price_sanity_bounds or {
            "EURUSD": (0.5, 2.5),
            "GBPUSD": (0.5, 2.5),
            "USDJPY": (50.0, 300.0),
        }

    def inspect(self, obs: Observation, current_time: Optional[float] = None) -> Observation:
        """Inspects and attaches quality score, freshness, and status to an observation."""
        now = current_time if current_time is not None else time.time()
        messages = []

        # 1. Freshness Check
        freshness = max(0.0, now - obs.timestamp)
        obs.freshness_seconds = freshness
        if freshness > self.max_stale_seconds:
            obs.status = DataQualityStatus.STALE
            messages.append(f"Observation stale by {freshness:.2f}s (max allowed: {self.max_stale_seconds}s)")

        # 2. Source Check
        if obs.source not in self.allowed_sources:
            obs.status = DataQualityStatus.UNTRUSTED_SOURCE
            messages.append(f"Source '{obs.source}' not in allowed sources list")

        # 3. OHLCV Structural Integrity Check
        required_keys = {"open", "high", "low", "close", "volume"}
        if not required_keys.issubset(obs.ohlcv.keys()):
            obs.status = DataQualityStatus.MISSING_FIELDS
            messages.append(f"Missing required OHLCV keys: {required_keys - set(obs.ohlcv.keys())}")
        else:
            o, h, l, c, v = (
                obs.ohlcv["open"],
                obs.ohlcv["high"],
                obs.ohlcv["low"],
                obs.ohlcv["close"],
                obs.ohlcv["volume"],
            )
            # Check price relations
            if not (l <= o <= h and l <= c <= h and l <= h) or o <= 0 or h <= 0 or l <= 0 or c <= 0 or v < 0:
                obs.status = DataQualityStatus.CORRUPTED
                messages.append(f"Invalid OHLCV relationship or non-positive price: O={o}, H={h}, L={l}, C={c}, V={v}")

            # Check price sanity bounds
            if obs.instrument in self.price_sanity_bounds:
                min_p, max_p = self.price_sanity_bounds[obs.instrument]
                if not (min_p <= c <= max_p):
                    obs.status = DataQualityStatus.OUT_OF_BOUNDS
                    messages.append(f"Price {c} out of bounds ({min_p}, {max_p}) for {obs.instrument}")

        # Compute Quality Score
        quality_score = 1.0
        if obs.status != DataQualityStatus.VALID:
            quality_score = 0.0
        else:
            # Decay score based on staleness
            quality_score = max(0.0, 1.0 - (freshness / self.max_stale_seconds) * 0.5)

        obs.quality_score = round(quality_score, 4)
        obs.validation_messages.extend(messages)
        return obs


class PerceptionEngine:
    """Unified Perception Layer for consuming and validating market information."""

    def __init__(self, firewall: Optional[DataIntegrityFirewall] = None):
        self.firewall = firewall or DataIntegrityFirewall()

    def process_raw_market_data(
        self,
        instrument: str,
        timeframe: str,
        ohlcv: Dict[str, float],
        timestamp: Optional[float] = None,
        source: str = "mt5",
        order_book: Optional[Dict[str, Any]] = None,
        trade_flow: Optional[Dict[str, Any]] = None,
        news_sentiment: Optional[Dict[str, Any]] = None,
        macro_events: Optional[List[Dict[str, Any]]] = None,
        current_time: Optional[float] = None,
    ) -> Observation:
        """Constructs and validates an Observation through the Data Integrity Firewall."""
        ts = timestamp if timestamp is not None else time.time()
        obs = Observation(
            timestamp=ts,
            instrument=instrument,
            timeframe=timeframe,
            source=source,
            ohlcv=ohlcv,
            order_book=order_book,
            trade_flow=trade_flow,
            news_sentiment=news_sentiment,
            macro_events=macro_events,
        )
        validated_obs = self.firewall.inspect(obs, current_time=current_time)
        if not validated_obs.is_valid():
            logger.warning(
                f"DataIntegrityFirewall rejected observation for {instrument} [{timeframe}]: "
                f"Status={validated_obs.status.value}, Errors={validated_obs.validation_messages}"
            )
        return validated_obs

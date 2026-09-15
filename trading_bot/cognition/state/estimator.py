"""Probabilistic State Estimator and Multi-Timescale Engine."""

import math
import logging
from typing import Dict, Any, List, Optional
from trading_bot.cognition.perception.contracts import Observation
from .contracts import MarketState

logger = logging.getLogger("alphaalgo.cognition.state")


class StateEstimator:
    """Estimates market state and multi-timescale structure from observations."""

    def __init__(self, default_timeframes: Optional[List[str]] = None):
        self.timeframes = default_timeframes or ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]

    def estimate_state(
        self,
        instrument: str,
        observations: Dict[str, Observation],
        current_time: Optional[float] = None
    ) -> MarketState:
        """Computes MarketState from multi-timeframe observations."""
        ts = current_time or max((obs.timestamp for obs in observations.values()), default=0.0)
        primary_tf = "M15" if "M15" in observations else list(observations.keys())[0] if observations else "M15"

        # Multi-timescale analysis
        timescale_struct = {}
        bullish_count = 0
        bearish_count = 0
        total_weight = 0.0

        tf_weights = {"M1": 0.05, "M5": 0.1, "M15": 0.2, "M30": 0.2, "H1": 0.25, "H4": 0.1, "D1": 0.1}

        for tf, obs in observations.items():
            if not obs.is_valid():
                continue

            c = obs.ohlcv.get("close", 0.0)
            o = obs.ohlcv.get("open", 0.0)
            h = obs.ohlcv.get("high", 0.0)
            l = obs.ohlcv.get("low", 0.0)

            tf_trend = "NEUTRAL"
            tf_return = (c - o) / o if o > 0 else 0.0
            if tf_return > 0.0005:
                tf_trend = "BULLISH"
                bullish_count += tf_weights.get(tf, 0.1)
            elif tf_return < -0.0005:
                tf_trend = "BEARISH"
                bearish_count += tf_weights.get(tf, 0.1)

            total_weight += tf_weights.get(tf, 0.1)

            timescale_struct[tf] = {
                "trend": tf_trend,
                "return": round(tf_return, 6),
                "range": round((h - l) / o if o > 0 else 0.0, 6),
                "quality": obs.quality_score
            }

        # Determine dominant trend & strength
        if total_weight > 0:
            net_bullish = bullish_count / total_weight
            net_bearish = bearish_count / total_weight
        else:
            net_bullish = net_bearish = 0.0

        if net_bullish > 0.55:
            trend_dir = "BULLISH"
            trend_str = net_bullish
        elif net_bearish > 0.55:
            trend_dir = "BEARISH"
            trend_str = net_bearish
        else:
            trend_dir = "NEUTRAL"
            trend_str = max(net_bullish, net_bearish)

        # Probabilistic Regime Estimation
        if trend_str > 0.70:
            regime_dist = {"trending": round(trend_str, 2), "ranging": round((1.0 - trend_str) * 0.6, 2), "transitional": round((1.0 - trend_str) * 0.4, 2)}
        elif trend_str < 0.40:
            regime_dist = {"trending": 0.20, "ranging": 0.65, "transitional": 0.15}
        else:
            regime_dist = {"trending": 0.35, "ranging": 0.35, "transitional": 0.30}

        # Normalize regime distribution
        total_prob = sum(regime_dist.values())
        regime_dist = {k: round(v / total_prob, 4) for k, v in regime_dist.items()}

        # Quality and uncertainty
        avg_quality = (
            sum(obs.quality_score for obs in observations.values()) / len(observations)
            if observations else 0.0
        )
        uncertainty = round(max(0.05, 1.0 - avg_quality + (0.3 if trend_dir == "NEUTRAL" else 0.0)), 4)

        return MarketState(
            timestamp=ts,
            instrument=instrument,
            primary_timeframe=primary_tf,
            regime_distribution=regime_dist,
            trend_direction=trend_dir,
            trend_strength=round(trend_str, 4),
            volatility_state="NORMAL",
            volatility_percentile=0.50,
            liquidity_state="NORMAL",
            liquidity_score=0.50,
            momentum_score=round(net_bullish - net_bearish, 4),
            timescale_structure=timescale_struct,
            event_risk_level="LOW",
            uncertainty=uncertainty,
            data_quality_score=round(avg_quality, 4)
        )

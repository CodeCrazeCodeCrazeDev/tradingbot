"""
Models and Schemas for Cognitive System Controller (CSC)
UCA-2026 Canonical Market State Contracts.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class NormalizedMarketContext:
    """
    Canonical, immutable schema for market state representation across UCA-2026.
    Eliminates heterogeneous dictionaries and formats downstream.
    """
    volatility: float = 0.0
    price_action: str = "NEUTRAL"
    features: List[float] = field(default_factory=list)
    raw_source: Dict[str, Any] = field(default_factory=dict)


class MarketContextAdapter:
    """
    Normalizes heterogeneous raw observations into canonical NormalizedMarketContext.
    """
    @staticmethod
    def normalize(observation: Any) -> NormalizedMarketContext:
        if isinstance(observation, NormalizedMarketContext):
            return observation

        if not isinstance(observation, dict):
            return NormalizedMarketContext()

        # Extract volatility safely from different levels/names
        vol = observation.get("volatility")
        if vol is None:
            vol = observation.get("market", {}).get("volatility")
        if vol is None:
            vol = 0.0

        # Extract price action safely
        pa = observation.get("price_action")
        if pa is None:
            pa = observation.get("market", {}).get("price_action")
        if pa is None:
            pa = "NEUTRAL"

        # Extract features safely
        feats = observation.get("features")
        if feats is None:
            feats = []
        elif not isinstance(feats, list):
            try:
                feats = [float(feats)]
            except (ValueError, TypeError):
                feats = []
        else:
            cleaned_feats = []
            for f in feats:
                try:
                    cleaned_feats.append(float(f))
                except (ValueError, TypeError):
                    pass
            feats = cleaned_feats

        return NormalizedMarketContext(
            volatility=float(vol),
            price_action=str(pa),
            features=feats,
            raw_source=observation
        )

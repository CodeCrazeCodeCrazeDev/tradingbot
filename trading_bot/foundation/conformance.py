"""Non-invasive contract checks for legacy adapters entering the monolith."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Mapping

from .contracts import DataQuality, MarketEvent


@dataclass(frozen=True)
class ConformanceResult:
    component: str
    passed: bool
    missing: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)


BROKER_ADAPTER_METHODS = (
    "connect",
    "disconnect",
    "submit_order",
    "cancel_order",
    "get_order",
    "get_positions",
    "reconcile",
)


MARKET_DATA_ADAPTER_METHODS = (
    "connect",
    "disconnect",
    "snapshot",
    "stream",
)


def check_broker_adapter(adapter: Any) -> ConformanceResult:
    """Check shape only; never connects or submits an order."""
    missing = [name for name in BROKER_ADAPTER_METHODS if not callable(getattr(adapter, name, None))]
    if not isinstance(getattr(adapter, "venue_id", None), str) or not adapter.venue_id:
        missing.append("venue_id")
    return ConformanceResult(
        component=type(adapter).__name__,
        passed=not missing,
        missing=missing,
    )


def check_market_data_adapter(adapter: Any) -> ConformanceResult:
    """Check market-feed shape without opening a network connection."""
    missing = [name for name in MARKET_DATA_ADAPTER_METHODS if not callable(getattr(adapter, name, None))]
    return ConformanceResult(
        component=type(adapter).__name__,
        passed=not missing,
        missing=missing,
    )


def check_market_event(event: MarketEvent) -> ConformanceResult:
    """Validate the minimum quality/provenance contract before cognition."""
    violations: List[str] = []
    if event.quality in {DataQuality.INVALID, DataQuality.STALE}:
        violations.append(f"market quality is {event.quality.value}")
    if not event.provenance:
        violations.append("market provenance is missing")
    if not event.instrument.symbol:
        violations.append("instrument symbol is missing")
    return ConformanceResult(
        component="MarketEvent",
        passed=not violations,
        violations=violations,
    )

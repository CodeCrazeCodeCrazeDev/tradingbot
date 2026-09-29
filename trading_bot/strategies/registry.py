"""Canonical strategy capability registry.

Strategies produce typed signals only. Risk, governance, portfolio sizing, and
execution remain outside this registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from trading_bot.foundation.ports import StrategyPort


@dataclass(frozen=True)
class StrategyRegistration:
    strategy_id: str
    adapter: StrategyPort
    metadata: Mapping[str, Any] = field(default_factory=dict)
    enabled: bool = True


class StrategyRegistry:
    """Discoverable strategy capabilities with no capital-moving methods."""

    def __init__(self) -> None:
        self._strategies: Dict[str, StrategyRegistration] = {}

    def register(
        self,
        strategy: StrategyPort,
        *,
        strategy_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        overwrite: bool = False,
    ) -> StrategyRegistration:
        name = strategy_id or getattr(strategy, "strategy_id", "")
        if not name:
            raise ValueError("Strategies require a non-empty strategy_id")
        if not callable(getattr(strategy, "generate_signal", None)):
            raise TypeError("Strategy must implement generate_signal()")
        if name in self._strategies and not overwrite:
            raise ValueError(f"Strategy '{name}' is already registered")
        registration = StrategyRegistration(name, strategy, dict(metadata or {}))
        self._strategies[name] = registration
        return registration

    def unregister(self, strategy_id: str) -> None:
        self._strategies.pop(strategy_id, None)

    def get(self, strategy_id: str) -> StrategyRegistration:
        return self._strategies[strategy_id]

    def list(self) -> List[StrategyRegistration]:
        return list(self._strategies.values())

    async def generate_signals(
        self,
        strategy_id: str,
        market: Mapping[str, Any],
    ) -> list:
        registration = self.get(strategy_id)
        if not registration.enabled:
            return []
        signals = registration.adapter.generate_signal(market)
        if hasattr(signals, "__await__"):
            signals = await signals
        return list(signals or [])

"""Bridge the legacy brokers.broker_adapter API to foundation BrokerAdapter."""

from __future__ import annotations

from typing import Any

from trading_bot.execution.service import LegacyBrokerAdapter


class FoundationBrokerAdapter(LegacyBrokerAdapter):
    """Typed foundation adapter around ``trading_bot.brokers.broker_adapter``.

    The wrapped broker is never connected implicitly. This is safe for paper and
    testnet conformance tests and remains opt-in for production profiles.
    """

    def __init__(self, legacy_adapter: Any, venue_id: str = "legacy-broker-adapter") -> None:
        super().__init__(legacy_adapter, venue_id=venue_id)
        self.legacy_adapter = legacy_adapter

    @classmethod
    def from_legacy(cls, legacy_adapter: Any, venue_id: str = "legacy-broker-adapter"):
        return cls(legacy_adapter, venue_id=venue_id)

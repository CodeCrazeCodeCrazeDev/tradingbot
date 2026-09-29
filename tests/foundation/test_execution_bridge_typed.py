"""Compatibility bridge tests for the typed execution-service migration."""

from dataclasses import dataclass

import pytest

from trading_bot.core.execution_bridge import PaperExecutionBridge
from trading_bot.execution.service import CanonicalExecutionService


@dataclass
class _Action:
    payload: dict
    action_id: str = "action-1"


@pytest.mark.asyncio
async def test_paper_bridge_delegates_to_typed_service_idempotently(tmp_path) -> None:
    service = CanonicalExecutionService()
    bridge = PaperExecutionBridge(
        persist_path=str(tmp_path / "fills.jsonl"),
        slippage=None,
        execution_service=service,
    )
    action = _Action({
        "trade_id": "trade-1",
        "symbol": "EURUSD",
        "action": "BUY",
        "quantity": 1.0,
        "price": 1.1,
    })

    first = await bridge.execute(action)
    second = await bridge.execute(action)

    assert first["status"] == "filled"
    assert second == first
    assert len(bridge.fills) == 1
    assert bridge.positions["EURUSD"] == 1.0


@pytest.mark.asyncio
async def test_typed_bridge_rejects_without_reference_price(tmp_path) -> None:
    bridge = PaperExecutionBridge(
        persist_path=str(tmp_path / "fills.jsonl"),
        execution_service=CanonicalExecutionService(),
    )

    result = await bridge.execute(_Action({
        "trade_id": "trade-2",
        "symbol": "EURUSD",
        "action": "BUY",
        "quantity": 1.0,
    }))

    assert result["status"] == "rejected"
    assert "price" in result["reason"]

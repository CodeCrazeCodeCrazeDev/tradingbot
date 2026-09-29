"""Wave-5 boundary tests: cognition is advisory-only and cannot authorize."""

import pytest

from trading_bot.cognition.advisory_adapter import AdvisoryCognitiveBrain


class _FakeBrain:
    """Fake brain emitting the real brain's authority fields."""

    def process_cycle(self, **kwargs):
        return {
            "cycle_id": "cog_x",
            "authorized_action": "BUY",
            "authorized_size": 9.99,
            "risk_authorized": True,
            "rejection_reason": None,
            "market_state": {"regime": "trend", "uncertainty": 0.2},
            "adversarial_passed": True,
            "calibrated_probability": 0.61,
            "nested": {"approved": False, "authorized_size": 5.0},
        }


@pytest.mark.asyncio
async def test_advisory_brain_strips_all_authority_fields() -> None:
    adapter = AdvisoryCognitiveBrain(brain=_FakeBrain())
    out = await adapter.analyze({"symbol": "EURUSD", "signal": "BUY"})

    assert out["advisory_only"] is True
    evidence = out["evidence"]
    assert "authorized_action" not in evidence
    assert "authorized_size" not in evidence
    assert "risk_authorized" not in evidence
    # Nested authority fields are stripped too.
    assert "authorized_size" not in evidence["nested"]
    # Evidence content survives.
    assert evidence["market_state"]["regime"] == "trend"
    assert evidence["calibrated_probability"] == 0.61


@pytest.mark.asyncio
async def test_advisory_output_carries_no_order_capable_fields() -> None:
    """Forged capability output must not contain fields the execution path
    would read (action/quantity/symbol at top level for order routing)."""
    adapter = AdvisoryCognitiveBrain(brain=_FakeBrain())
    out = await adapter.analyze({"symbol": "EURUSD", "signal": "BUY"})
    evidence = out["evidence"]
    for field in ("authorized_size", "authorized_action", "quantity",
                  "order", "execution", "veto", "approve"):
        assert field not in evidence

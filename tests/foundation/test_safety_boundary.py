"""Hard-gate tests for the canonical immutable safety boundary."""

import pytest

from trading_bot.core.immutable_shield import GovernanceDecision, shield


def _valid_params():
    return {
        "instrument": {"symbol": "EURUSD", "instrument_type": "fx"},
        "quantity": 1.0,
        "confidence": 0.9,
        "action": "BUY",
    }


@pytest.mark.asyncio
async def test_shield_blocks_invalid_normalized_market_data() -> None:
    report = await shield.validate_action(
        "TRADE_EXECUTION",
        _valid_params(),
        {"market": {"data_quality": "invalid", "data_is_fresh": False}},
    )

    assert report.decision is GovernanceDecision.BLOCKED
    assert "data" in report.reason.lower()


@pytest.mark.asyncio
async def test_shield_applies_symbol_denylist_to_typed_order_payload() -> None:
    old_config = dict(shield.config)
    shield.config["blocked_symbols"] = ["EURUSD"]
    try:
        report = await shield.validate_action("TRADE_EXECUTION", _valid_params(), {})
    finally:
        shield.config.clear()
        shield.config.update(old_config)

    assert report.decision is GovernanceDecision.BLOCKED
    assert "EURUSD" in report.reason


@pytest.mark.asyncio
async def test_extreme_volatility_allows_only_exit_intents() -> None:
    buy_report = await shield.validate_action(
        "TRADE_EXECUTION",
        _valid_params(),
        {"market": {"regime": "EXTREME_VOLATILITY"}},
    )
    exit_params = {**_valid_params(), "action": "EXIT"}
    exit_report = await shield.validate_action(
        "TRADE_EXECUTION",
        exit_params,
        {"market": {"regime": "EXTREME_VOLATILITY"}},
    )

    assert buy_report.decision is GovernanceDecision.BLOCKED
    assert exit_report.decision is GovernanceDecision.APPROVED

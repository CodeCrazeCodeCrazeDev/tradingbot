#!/usr/bin/env python3
"""Focused tests for expanded TAMIC control gates."""

import asyncio
import importlib.util
import sys
import time
from pathlib import Path


MODULE_PATH = Path(__file__).parent.parent / "trading_bot" / "tamic.py"
SPEC = importlib.util.spec_from_file_location("tamic_expanded_direct", MODULE_PATH)
tamic = importlib.util.module_from_spec(SPEC)
sys.modules["tamic_expanded_direct"] = tamic
SPEC.loader.exec_module(tamic)


def _run(coro):
    return asyncio.run(coro)


def _base_market(**overrides):
    payload = {
        "symbol": "AAPL",
        "timestamp": time.time(),
        "close": [100.0, 100.8, 101.5, 102.2, 103.0],
        "volume": [1000, 1100, 1150, 1200],
        "volatility": 0.01,
        "liquidity": 2.0,
        "spread": 0.01,
        "market_regime": "trending",
    }
    payload.update(overrides)
    return payload


def test_tamic_recommends_trade_only_when_time_risk_is_clean():
    system = _run(tamic.quick_start())

    decision = _run(
        system.evaluate_market(
            symbol="AAPL",
            horizon=tamic.TimeHorizon.INTRADAY,
            market_data=_base_market(signal_confidence=0.86),
        )
    )

    assert decision.is_trade_recommended
    assert decision.exposure_recommendation > 0
    assert decision.market_time_state == tamic.MarketTimeState.NORMAL
    assert decision.signal_half_life == tamic.SignalHalfLife.FRESH


def test_tamic_blocks_expired_signals_and_mixed_horizons():
    system = _run(tamic.quick_start())

    expired = _run(
        system.evaluate_market(
            symbol="AAPL",
            horizon=tamic.TimeHorizon.INTRADAY,
            market_data=_base_market(signal_timestamp=time.time() - 86400),
        )
    )
    mixed = _run(
        system.evaluate_market(
            symbol="AAPL",
            horizon=tamic.TimeHorizon.INTRADAY,
            market_data=_base_market(microstructure_data={}, intraday_data={}),
        )
    )

    assert not expired.is_trade_recommended
    assert "expired signal" in expired.no_trade_reason
    assert expired.signal_half_life == tamic.SignalHalfLife.EXPIRED
    assert not mixed.is_trade_recommended
    assert "mixes incompatible time horizons" in mixed.no_trade_reason


def test_tamic_blocks_loss_chasing_and_leverage_after_losses():
    system = _run(tamic.quick_start())

    chase = _run(
        system.evaluate_market(
            symbol="AAPL",
            horizon=tamic.TimeHorizon.INTRADAY,
            market_data=_base_market(recent_performance=0.20),
        )
    )
    leverage = _run(
        system.evaluate_market(
            symbol="AAPL",
            horizon=tamic.TimeHorizon.INTRADAY,
            market_data=_base_market(loss_streak=3, previous_leverage=1.0, current_leverage=2.0),
        )
    )

    assert not chase.is_trade_recommended
    assert "recent performance impulse" in chase.no_trade_reason
    assert not leverage.is_trade_recommended
    assert "leverage increase after a loss streak" in leverage.no_trade_reason


def test_tamic_reduces_confidence_and_exposure_when_market_time_accelerates():
    system = _run(tamic.quick_start())

    normal = _run(
        system.evaluate_market(
            symbol="AAPL",
            horizon=tamic.TimeHorizon.INTRADAY,
            market_data=_base_market(signal_confidence=0.90, volatility=0.01),
        )
    )
    accelerated = _run(
        system.evaluate_market(
            symbol="AAPL",
            horizon=tamic.TimeHorizon.INTRADAY,
            market_data=_base_market(signal_confidence=0.90, volatility=0.03),
        )
    )

    assert accelerated.market_time_state == tamic.MarketTimeState.ACCELERATED
    assert accelerated.confidence_level < normal.confidence_level
    assert accelerated.exposure_recommendation <= normal.exposure_recommendation


def test_tamic_sync_analyze_process_and_governance_integration():
    system = tamic.create_tamic()
    result = system.analyze(_base_market(signal_confidence=0.86))
    processed = system.process(_base_market(signal_confidence=0.86))
    integration = tamic.create_tamic_integration()
    governed = integration.integrate_with_capital_governance(_base_market(signal_confidence=0.86))

    assert result["market_time_state"] == "normal"
    assert processed["symbol"] == "AAPL"
    assert "approved" in governed
    assert "tamic" in governed

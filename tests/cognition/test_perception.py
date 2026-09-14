"""Tests for Perception Layer and Data Integrity Firewall."""

import time
import pytest
from trading_bot.cognition.perception import (
    Observation,
    DataQualityStatus,
    DataIntegrityFirewall,
    PerceptionEngine,
)


def test_data_integrity_firewall_valid():
    firewall = DataIntegrityFirewall(max_stale_seconds=300.0)
    now = time.time()
    obs = Observation(
        timestamp=now - 10.0,
        instrument="EURUSD",
        timeframe="M15",
        source="mt5",
        ohlcv={"open": 1.0850, "high": 1.0890, "low": 1.0840, "close": 1.0870, "volume": 1250.0},
    )
    inspected = firewall.inspect(obs, current_time=now)
    assert inspected.status == DataQualityStatus.VALID
    assert inspected.is_valid()
    assert inspected.quality_score > 0.90


def test_data_integrity_firewall_stale():
    firewall = DataIntegrityFirewall(max_stale_seconds=60.0)
    now = time.time()
    obs = Observation(
        timestamp=now - 120.0,
        instrument="EURUSD",
        timeframe="M15",
        source="mt5",
        ohlcv={"open": 1.0850, "high": 1.0890, "low": 1.0840, "close": 1.0870, "volume": 1250.0},
    )
    inspected = firewall.inspect(obs, current_time=now)
    assert inspected.status == DataQualityStatus.STALE
    assert not inspected.is_valid()
    assert inspected.quality_score == 0.0


def test_data_integrity_firewall_corrupted_ohlcv():
    firewall = DataIntegrityFirewall()
    now = time.time()
    # High is lower than Close
    obs = Observation(
        timestamp=now,
        instrument="EURUSD",
        timeframe="M15",
        source="mt5",
        ohlcv={"open": 1.0850, "high": 1.0860, "low": 1.0840, "close": 1.0890, "volume": 1250.0},
    )
    inspected = firewall.inspect(obs, current_time=now)
    assert inspected.status == DataQualityStatus.CORRUPTED
    assert not inspected.is_valid()


def test_perception_engine_processing():
    engine = PerceptionEngine()
    now = time.time()
    obs = engine.process_raw_market_data(
        instrument="GBPUSD",
        timeframe="H1",
        ohlcv={"open": 1.2600, "high": 1.2650, "low": 1.2580, "close": 1.2620, "volume": 3400.0},
        timestamp=now,
        source="mt5",
        current_time=now,
    )
    assert obs.is_valid()
    assert obs.instrument == "GBPUSD"
    assert obs.timeframe == "H1"

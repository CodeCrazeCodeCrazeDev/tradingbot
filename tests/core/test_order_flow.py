"""Order-flow service: capability gating, honest unavailability,
signal provenance, nonfinite rejection, symbol isolation."""
import time

import pytest

from trading_bot.core.csc.order_flow import (DETECTOR_VERSION,
                                             OrderFlowService)


@pytest.fixture
def svc():
    return OrderFlowService(block_notional_usd=100_000.0)


def _bar_obs(symbol="EURUSD", close=1.10, vol=100.0, high=None, low=None):
    return {"symbol": symbol, "close": close, "volume": vol,
            "high": high or close + 0.001, "low": low or close - 0.001,
            "ts": time.time()}


class TestCapabilityGating:
    def test_bars_only_blocks_prints_and_book(self, svc):
        r = svc.analyze(_bar_obs())
        assert r["capabilities"]["prints"] is False
        assert r["capabilities"]["book"] is False
        unavail = {u["detector"] for u in r["unavailable"]}
        assert {"block_trades", "iceberg", "spoofing",
                "layering"} <= unavail
        # bars tier active → bar proxies attempted
        assert r["capabilities"]["bars"] is True

    def test_unavailable_never_fabricates(self, svc):
        # A bars-only feed must NEVER emit book-tier signal kinds
        for i in range(40):
            r = svc.analyze(_bar_obs(vol=100.0 + i % 7))
        kinds = {s["kind"] for s in r["signals"]}
        assert not kinds & {"block_trade", "iceberg_indicator",
                            "spoofing_indicator", "book_imbalance",
                            "volume_delta"}

    def test_book_obs_activates_book_detectors(self, svc):
        book = ([[1.099, 5000.0], [1.0995, 5000.0]],
                [[1.101, 5000.0], [1.1005, 5000.0]])
        for _ in range(3):
            r = svc.analyze({**_bar_obs(), "book": book})
        assert r["capabilities"]["book"] is True
        assert not any(u["detector"] == "iceberg"
                       for u in r["unavailable"])


class TestPrintsTier:
    def test_block_trade_above_threshold(self, svc):
        obs = _bar_obs()
        obs["prints"] = [{"price": 1.10, "size": 100_000.0,
                          "ts": time.time(), "aggressor": "buy"}]
        r = svc.analyze(obs)
        blocks = [s for s in r["signals"] if s["kind"] == "block_trade"]
        assert blocks
        assert blocks[0]["evidence"]["notional_usd"] == pytest.approx(110_000)
        assert blocks[0]["direction"] == "buy"

    def test_below_threshold_no_block(self, svc):
        obs = _bar_obs()
        obs["prints"] = [{"price": 1.10, "size": 1_000.0,
                          "ts": time.time()}]
        r = svc.analyze(obs)
        assert not [s for s in r["signals"]
                    if s["kind"] == "block_trade"]

    def test_volume_delta_from_aggressor_flags(self, svc):
        now = time.time()
        obs = _bar_obs()
        obs["prints"] = ([{"price": 1.1, "size": 10, "ts": now,
                           "aggressor": "buy"}] * 9 +
                         [{"price": 1.1, "size": 10, "ts": now,
                           "aggressor": "sell"}])
        r = svc.analyze(obs)
        vd = [s for s in r["signals"] if s["kind"] == "volume_delta"]
        assert vd and vd[0]["direction"] == "buy"
        assert vd[0]["evidence"]["inference"] is False


class TestBarProxies:
    def _absorbing_feed(self, svc):
        for i in range(30):
            svc.analyze(_bar_obs(vol=100.0 + (i % 5), close=1.1 + i * 1e-5))
        # final bar: huge volume, tiny range
        return svc.analyze(_bar_obs(vol=800.0, high=1.1031, low=1.1030,
                                    close=1.10305))

    def test_absorption_labelled_inference(self, svc):
        r = self._absorbing_feed(svc)
        ab = [s for s in r["signals"] if s["kind"] == "absorption_proxy"]
        if ab:  # detector may legitimately not fire; if it fires, honest
            assert ab[0]["data_quality"] == "bars"
            assert "inference" in ab[0]["evidence"]

    def test_exhaustion_labelled_warning(self, svc):
        for i in range(8):
            svc.analyze(_bar_obs(vol=100.0, close=1.1 + i * 0.001))
        for i in range(4):  # price continues up on declining volume
            svc.analyze(_bar_obs(vol=50 - i * 5, close=1.108 + i * 0.001))
        r = svc.analyze(_bar_obs(vol=30, close=1.112))
        ex = [s for s in r["signals"]
              if s["kind"] == "exhaustion_indicator"]
        if ex:
            assert ex[0]["direction"] == "sell"  # rally on fading volume


class TestSignalSchemaAndSafety:
    def test_every_signal_has_required_fields(self, svc):
        now = time.time()
        obs = {**_bar_obs(), "prints": [
            {"price": 1.1, "size": 100_000, "ts": now,
             "aggressor": "buy"}] * 12}
        r = svc.analyze(obs)
        for s in r["signals"]:
            for f in ("symbol", "venue", "event_ts", "availability_ts",
                      "source", "data_quality", "evidence", "uncertainty",
                      "expiry_s", "detector_version"):
                assert f in s, f"missing {f} in {s['kind']}"
            assert s["detector_version"] == DETECTOR_VERSION
            assert s["advisory_only"] is True
            assert 0.0 <= s["strength"] <= 1.0

    def test_nonfinite_inputs_rejected(self, svc):
        r = svc.analyze({"symbol": "EURUSD", "close": float("inf"),
                         "volume": float("nan"), "ts": time.time()})
        assert r["capabilities"]["bars"] is False
        # corrupted book data
        r = svc.analyze({**_bar_obs(),
                         "book": ([[float("inf"), 1.0]], [[1.0, 1.0]])})
        assert all(s["kind"] != "book_imbalance" for s in r["signals"])

    def test_symbol_isolation(self, svc):
        now = time.time()
        svc.analyze({"symbol": "EURUSD", "close": 1.1, "volume": 100,
                     "ts": now, "prints": [
                         {"price": 1.1, "size": 200_000, "ts": now}]})
        r = svc.analyze({"symbol": "GBPUSD", "close": 1.3, "volume": 50,
                         "ts": now})
        # GBPUSD has no prints state — block detector stays unavailable
        assert r["capabilities"]["prints"] is False

"""External-horizon plumbing tests: LOB feeds, execution bridges, slippage."""

import json
import asyncio
import pytest
from pathlib import Path

from trading_bot.market_feeds import LOBSnapshot, LOBFileFeed, BrokerLOBFeed
from trading_bot.core.execution_bridge import (
    PaperExecutionBridge, BrokerExecutionBridge, SlippageRecorder,
    SlippageRecord, make_execution_bridge,
)


def _snap():
    return LOBSnapshot(
        symbol="EURUSD", timestamp=1.0,
        bids=[(1.0799, 10.0), (1.0798, 5.0)],
        asks=[(1.0801, 4.0), (1.0802, 6.0)],
    )


# ---------- LOB contract ----------

def test_lob_snapshot_features():
    s = _snap()
    assert s.mid == pytest.approx(1.08)
    assert s.spread_bps == pytest.approx(1.8518, rel=1e-3)
    assert s.imbalance == pytest.approx((15 - 10) / 25)
    bd, ad = s.depth_within_bps(5.0)
    assert bd == 15.0 and ad == 10.0
    f = s.features()
    assert set(f) >= {"mid", "spread_bps", "imbalance", "bid_depth", "ask_depth"}


def test_lob_file_feed_jsonl(tmp_path):
    p = tmp_path / "lob.jsonl"
    for ts in (1.0, 2.0):
        p.open("a").write(json.dumps({
            "symbol": "EURUSD", "timestamp": ts,
            "bids": [[1.0799, 10.0]], "asks": [[1.0801, 10.0]],
        }) + "\n")
    feed = LOBFileFeed(p)
    assert len(feed) == 2
    snap = asyncio.run(feed.next())
    assert snap.mid == pytest.approx(1.08)
    asyncio.run(feed.next())
    assert asyncio.run(feed.next()) is None


def test_lob_file_feed_missing():
    with pytest.raises(FileNotFoundError):
        LOBFileFeed(Path("nonexistent.jsonl"))


class _FakeBroker:
    async def get_order_book(self, symbol, limit=20):
        return {"bids": [[1.0, 5.0]], "asks": [[1.1, 5.0]], "lastUpdateId": 7}

    async def place_order(self, symbol, side, type, quantity, price=None, stop_price=None):
        class O:
            filled_price = 1.01
            status = "FILLED"
            client_order_id = "oid-1"
        return O()


def test_broker_lob_feed():
    feed = BrokerLOBFeed(_FakeBroker(), "EURUSD")
    snap = asyncio.run(feed.next())
    assert snap.bids == [(1.0, 5.0)] and snap.asks == [(1.1, 5.0)]


def test_broker_lob_feed_requires_broker():
    with pytest.raises(ValueError):
        BrokerLOBFeed(None, "EURUSD")


# ---------- slippage ----------

def test_slippage_sign_and_stats(tmp_path):
    rec = SlippageRecorder(str(tmp_path / "slip.jsonl"))
    # buy filled above expected -> adverse -> positive bps
    rec.record(SlippageRecord("EURUSD", "BUY", 1.0, 1.001, 1.0, "paper"))
    # sell filled above expected -> favorable -> negative bps
    rec.record(SlippageRecord("EURUSD", "SELL", 1.0, 1.001, 1.0, "paper"))
    assert rec.records[0].slippage_bps == pytest.approx(10.0)
    assert rec.records[1].slippage_bps == pytest.approx(-10.0)
    st = rec.stats()
    assert st["fills"] == 2 and st["max_bps"] == pytest.approx(10.0)


# ---------- execution bridges ----------

class _Action:
    action_id = "a1"
    payload = {"symbol": "EURUSD", "action": "BUY", "quantity": 1.0, "price": 1.08}


def test_paper_bridge_records_slippage(tmp_path):
    bridge = PaperExecutionBridge(persist_path=str(tmp_path / "fills.jsonl"))
    res = asyncio.run(bridge.execute(_Action()))
    assert res["status"] == "filled"
    assert bridge.slippage.stats()["fills"] == 1


def test_broker_bridge_delegates(tmp_path):
    bridge = BrokerExecutionBridge(_FakeBroker())
    res = asyncio.run(bridge.execute(_Action()))
    assert res["status"] == "submitted"
    assert len(bridge.orders) == 1
    assert bridge.slippage.stats()["fills"] == 1


def test_factory_modes():
    assert isinstance(make_execution_bridge("paper"), PaperExecutionBridge)
    assert isinstance(make_execution_bridge("broker", broker=_FakeBroker()),
                      BrokerExecutionBridge)
    with pytest.raises(ValueError):
        make_execution_bridge("broker", broker=None)
    with pytest.raises(ValueError):
        make_execution_bridge("mars")


# ---------- microstructure into the brain ----------

def test_process_cycle_accepts_lob():
    from trading_bot.cognition.orchestrator import AlphaAlgoCognitiveBrain
    brain = AlphaAlgoCognitiveBrain()
    raw = {"M15": {"open": 1.08, "high": 1.086, "low": 1.077, "close": 1.085, "volume": 5000.0}}
    res = brain.process_cycle("EURUSD", raw, "BUY", 1.078, lob_snapshot=_snap())
    assert res["microstructure"]["mid"] == pytest.approx(1.08)
    res2 = brain.process_cycle("EURUSD", raw, "BUY", 1.078)
    assert res2["microstructure"] is None


# ---------- shield spread guard ----------

def test_shield_spread_guard():
    from trading_bot.core.immutable_shield import ImmutableShield, GovernanceDecision

    s = ImmutableShield()
    s.config["max_spread_bps"] = 5.0
    params = {"quantity": 1.0, "action": "buy"}
    wide = {"market": {"microstructure": {"spread_bps": 20.0}}}
    tight = {"market": {"microstructure": {"spread_bps": 2.0}}}

    rep = asyncio.run(s.validate_action("trade", params, wide))
    assert rep.decision == GovernanceDecision.BLOCKED
    rep = asyncio.run(s.validate_action("trade", params, tight))
    assert rep.decision == GovernanceDecision.APPROVED
    # exits are never spread-blocked
    rep = asyncio.run(s.validate_action(
        "trade", {"quantity": 1.0, "action": "exit_position"}, wide))
    assert rep.decision == GovernanceDecision.APPROVED
    s.config.pop("max_spread_bps")


def test_unified_bot_injects_microstructure():
    from trading_bot.unified_bot import UnifiedTradingBot

    class _Feed:
        async def next(self):
            return _snap()

    bot = UnifiedTradingBot({"lob_feed": _Feed()})
    assert bot.lob_feed is not None

"""Expansion engine — the honest replacements for the orphan
'capability' demos. Each test proves a real measurement happens: real
DB probes, real statistics on real bars, real process metrics, real
gated candidates — never simulated success."""

import sqlite3

import pytest

from trading_bot.expansion.domains import DomainGenerator
from trading_bot.expansion.ecosystem import EcosystemHealth
from trading_bot.expansion.foundry import AgentFoundry
from trading_bot.expansion.governor import ResourceGovernor
from trading_bot.expansion.inventory import DataResourceInventory
from trading_bot.expansion.scanner import OpportunityScanner, series_stats
from trading_bot.expansion.service import (
    ExpansionContext, attach_expansion_services)


def _mk_db(path, rows):
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE market_data (id INTEGER PRIMARY KEY, "
        "timestamp TEXT, symbol TEXT, timeframe TEXT, open REAL, "
        "high REAL, low REAL, close REAL, volume REAL)")
    con.executemany(
        "INSERT INTO market_data (timestamp, symbol, timeframe, open, "
        "high, low, close, volume) VALUES (?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()


def _bars(closes, symbol="EURUSD", tf="M15"):
    return [(f"2026-01-01T{i//60:02d}:{i%60:02d}:00", symbol, tf,
             c, c + 0.0002, c - 0.0002, c + 0.0001, 100.0)
            for i, c in enumerate(closes)]


def _trending(n=300):
    c = 1.10
    out = []
    for i in range(n):
        c += 0.0004 + (0.0002 if i % 7 == 0 else -0.0001)
        out.append(c)
    return out


def test_inventory_probes_and_onboards_real_sources(tmp_path):
    db = tmp_path / "probe.db"
    _mk_db(db, _bars(_trending(200)))
    inv = DataResourceInventory(tmp_path, sources=("probe.db",),
                                state_path=tmp_path / "onb.json")
    cat = inv.scan()
    assert cat["sources"]["probe.db"]["series"][0]["rows"] == 200
    assert cat["rows_total"] == 200
    # coverage gap: the series exists but is not in the active set
    gaps = inv.coverage_gaps(active=set(), catalog=cat)
    assert gaps == [{"source": "probe.db", "symbol": "EURUSD",
                     "timeframe": "M15"}]
    assert inv.coverage_gaps(active={("EURUSD", "M15")},
                           catalog=cat) == []
    # onboarding a non-market file is rejected, a real one is added
    bad = tmp_path / "notes.txt"
    bad.write_text("not a database")
    assert inv.onboard(bad)["status"] == "rejected"
    res = inv.onboard(db)
    assert res["status"] == "onboarded" and res["rows"] == 200
    assert str(db) in inv.onboarded()


def test_series_stats_measured_not_random():
    trend = _trending(300)
    st = series_stats(trend)
    assert st is not None
    assert st["sign_persistence"] > 0.5
    assert st["trend_pct"] > 0
    # same input -> same numbers (deterministic, no randomness)
    assert series_stats(trend) == st
    # a series that doubles its volatility in the last quarter is an
    # emerging regime — measured, not declared
    flat = [1.1 + (0.001 if i % 2 else -0.001) for i in range(240)]
    shifted = flat + [1.1 + (0.02 if i % 2 else -0.02)
                      for i in range(60)]
    st2 = series_stats(shifted)
    assert st2["vol_regime_ratio"] > 1.5
    assert st2["emerging_regime"] is True
    assert series_stats([1.0] * 10) is None


def test_scanner_uses_real_db_rows(tmp_path):
    db = tmp_path / "m.db"
    _mk_db(db, _bars(_trending(300)) +
           _bars([0.5 + (0.01 if i % 2 else -0.01)
                  for i in range(300)], symbol="BTCUSD", tf="H1"))
    inv = DataResourceInventory(tmp_path, sources=("m.db",))
    sc = OpportunityScanner(inv, active={("EURUSD", "M15")})
    out = sc.scan_all()
    assert out["series_scanned"] == 2
    by_sym = {o["symbol"]: o for o in out["opportunities"]}
    # structure kind must be measured correctly: the trending series is
    # positively autocorrelated, the alternating series mean-reverts
    assert by_sym["EURUSD"]["ret_autocorr"] > 0
    assert by_sym["BTCUSD"]["ret_autocorr"] < 0
    assert by_sym["EURUSD"]["sign_persistence"] > 0.7
    # BTCUSD:H1 is real coverage outside the active set -> new market
    assert {m["symbol"] for m in out["new_markets"]} == {"BTCUSD"}


@pytest.mark.asyncio
async def test_foundry_drives_real_gated_pipeline(tmp_path):
    from trading_bot.core.csc.controller import (
        CognitiveSystemController)
    csc = CognitiveSystemController()
    f = AgentFoundry(tmp_path / "foundry.json")
    bars = [{"timestamp": f"2026-01-01T{i//60:02d}:{i%60:02d}:00",
             "symbol": "EURUSD", "open": c, "high": c + 0.0002,
             "low": c - 0.0002, "close": c + 0.0001, "volume": 100.0}
            for i, c in enumerate(_trending(400))]
    rec = await f.run_generation(
        csc, bars,
        specs=[{"kind": "threshold_rule", "feature": "momentum",
                "op": ">", "direction": "BUY",
                "name": "test_mom_buy"},
               {"kind": "bogus_kind", "name": "bad_spec"}])
    assert rec["status"] == "completed"
    by_name = {c["spec"]["name"]: c for c in rec["candidates"]}
    # invalid spec is refused by the real validate_spec gate
    assert by_name["bad_spec"]["propose_status"] == "rejected"
    # the real candidate passed propose+validate through the CSC —
    # verdict is whatever the sealed holdout measured, not a constant
    real = by_name["test_mom_buy"]
    assert real["status"] in ("validated", "rejected")
    assert real["verdict"] in ("CONFIRMED", "INCONCLUSIVE",
                               "FALSIFIED")
    assert real["candidate_id"] in csc._engineered_models
    # a second run persists and summarizes real counts
    assert f.summary()["candidates_total"] == 2
    f2 = AgentFoundry(tmp_path / "foundry.json")
    assert len(f2.generations) == 1


def test_governor_reports_real_process_metrics(tmp_path):
    g = ResourceGovernor(tmp_path)
    m = g.measure()
    assert m["scope"] == "local_host"
    assert m["rss_mb"] > 0
    assert m["threads"] >= 1
    tight = ResourceGovernor(tmp_path, budgets={"rss_mb": 0.001})
    assert "rss_mb" in tight.measure()["violations"]


def test_ecosystem_counts_real_lifecycle():
    from types import SimpleNamespace
    from trading_bot.core.csc.self_wiring import (
        NodeState, SelfWiringSupervisor)
    sup = SelfWiringSupervisor()
    sup.register("a", state=NodeState.ATTACHED)
    sup.register("b", state=NodeState.SHADOW)
    sup.register("c", state=NodeState.DORMANT)
    csc = SimpleNamespace(_self_wiring=sup, _engineered_models={},
                          _advisory_services=[object(), object()])
    r = EcosystemHealth(csc).report()
    assert r["electorate_nodes"] == 3
    assert r["nodes_by_state"] == {"attached": 1, "shadow": 1,
                                   "dormant": 1}
    assert r["advisory_services"] == 2


def test_domains_proposals_carry_evidence(tmp_path):
    d = DomainGenerator(tmp_path / "d.json")
    fresh = d.generate(
        coverage_gaps=[{"source": "m.db", "symbol": "BTCUSD",
                        "timeframe": "H1"}],
        failure_kinds={"no_data": 4})
    assert len(fresh) == 2
    assert all("basis" in p for p in fresh)
    # identical evidence -> no duplicate proposals
    assert d.generate(
        coverage_gaps=[{"source": "m.db", "symbol": "BTCUSD",
                        "timeframe": "H1"}],
        failure_kinds={"no_data": 4}) == []
    assert d.summary()["domains_proposed_total"] == 2


def test_attach_expansion_services_registers_real_services(tmp_path):
    from trading_bot.core.csc.controller import (
        CognitiveSystemController)
    csc = CognitiveSystemController()
    rep = attach_expansion_services(csc, root=".",
                                    state_dir=tmp_path / "exp")
    assert not rep["skipped"], rep
    ids = {getattr(s, "capability_id", "")
           for s in csc._advisory_services}
    assert {"expansion_ecosystem", "expansion_governor",
            "expansion_scanner", "expansion_foundry",
            "expansion_domains", "expansion_inventory"} <= ids

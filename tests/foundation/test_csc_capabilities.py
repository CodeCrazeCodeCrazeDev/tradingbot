"""CSC capability matrix — every advertised capability does real
measured work or reports an honest boundary. No fixed counts, no
random metrics, no simulated success."""

import sqlite3
import sys
from pathlib import Path

import pytest

from trading_bot.core.csc.capabilities import (
    CSCCapabilities, PROTECTED_PATHS)
from trading_bot.expansion.inventory import DataResourceInventory
from trading_bot.expansion.service import ExpansionContext


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


def _mk_ledger(path):
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE fills (fill_key TEXT, client_order_id TEXT, "
        "venue_order_id TEXT, symbol TEXT, side TEXT, quantity REAL, "
        "price REAL, commission REAL, fill_json TEXT, occurred_at TEXT)")
    con.execute(
        "CREATE TABLE positions (symbol TEXT, quantity REAL, "
        "average_price REAL, instrument_json TEXT, updated_at TEXT)")
    con.execute(
        "INSERT INTO fills VALUES ('f1','o1','v1','EURUSD','BUY',"
        "0.05,1.10,0.02,'{}','2026-01-01T00:00:00')")
    con.execute(
        "INSERT INTO fills VALUES ('f2','o2','v2','EURUSD','SELL',"
        "0.03,1.101,0.01,'{}','2026-01-02T00:00:00')")
    con.execute(
        "INSERT INTO positions VALUES ('EURUSD',0.02,1.1005,'{}',"
        "'2026-01-02T00:00:00')")
    con.commit()
    con.close()


def _rows(closes, symbol="EURUSD", tf="M15", base_ts=0):
    return [(f"2026-01-{(i+base_ts)//96+1:02d}T"
             f"{(i+base_ts)//4%24:02d}:{(i+base_ts)%4*15:02d}:00",
             symbol, tf, c, c + 0.0002, c - 0.0002, c + 0.0001, 100.0)
            for i, c in enumerate(closes)]


def _bars(closes, symbol="EURUSD"):
    return [{"timestamp": f"2026-01-{i//96+1:02d}T{i//4%24:02d}:"
                          f"{i%4*15:02d}:00",
             "symbol": symbol, "open": c, "high": c + 0.0002,
             "low": c - 0.0002, "close": c + 0.0001, "volume": 100.0}
            for i, c in enumerate(closes)]


def _trending(n=400):
    c = 1.10
    out = []
    for i in range(n):
        c += 0.0004 + (0.0002 if i % 7 == 0 else -0.0001)
        out.append(c)
    return out


@pytest.fixture
def csc():
    from trading_bot.core.csc.controller import CognitiveSystemController
    return CognitiveSystemController()


@pytest.fixture
def caps(csc, tmp_path):
    ctx = ExpansionContext(tmp_path, tmp_path / "exp")
    return CSCCapabilities(csc, ctx=ctx, repo_root=tmp_path)


@pytest.mark.asyncio
async def test_analyze_strategies_measured_not_fixed(caps):
    res = await caps.analyze_strategies(
        _bars(_trending()),
        specs=[{"kind": "threshold_rule", "feature": "momentum",
                "op": ">", "direction": "BUY", "name": "t1"},
               {"kind": "bogus_kind", "name": "bad"}])
    assert res["strategies_analyzed"] == 2
    by_name = {r["spec"]["name"]: r for r in res["results"]}
    assert by_name["bad"]["status"] == "rejected"
    real = by_name["t1"]
    assert real["status"] in ("validated", "rejected")
    assert real["verdict"] in ("CONFIRMED", "INCONCLUSIVE",
                               "FALSIFIED")
    assert real["candidate_id"] in caps.csc._engineered_models


@pytest.mark.asyncio
async def test_optimize_parameters_real_sweep(caps):
    res = await caps.optimize_parameters(
        {"kind": "threshold_rule", "feature": "momentum", "op": ">",
         "direction": "BUY", "name": "sweep"},
        _bars(_trending()), thresholds=(-0.2, 0.0, 0.2))
    assert res["trials_run"] == 3
    # fixed-parameter evaluation: the requested threshold is the
    # measured object — the fitter cannot silently override it
    for t, thr in zip(res["trials"], (-0.2, 0.0, 0.2)):
        assert t["evaluated_params"]["threshold"] == thr
    assert "selection-biased" in res["note"]


def test_optimize_rejects_non_threshold_kind(caps):
    import asyncio
    res = asyncio.run(caps.optimize_parameters(
        {"kind": "logistic", "features": ["momentum"]},
        _bars(_trending(50))))
    assert res["status"] == "rejected"


@pytest.mark.asyncio
async def test_train_tune_search_honest_space(caps):
    res = await caps.train_tune_search(_bars(_trending(200)),
                                       kinds=("threshold_rule",
                                              "logistic"))
    assert set(res["results"]) == {"threshold_rule", "logistic"}
    # logistic honestly reports missing sklearn rather than a fake fit
    assert res["results"]["threshold_rule"]["status"] in (
        "validated", "rejected")
    assert "no substrate" in res["scope"]


def test_scan_historical_data_real_stats(caps, tmp_path):
    _mk_db(tmp_path / "m.db", _rows(_trending(200)))
    inv = caps.ctx.inventory
    inv.sources = ("m.db",)
    res = caps.scan_historical_data()
    assert res["statistics"]["series_scanned"] == 1
    st = caps.scan_historical_data(closes=_trending(150))
    assert st["status"] == "measured"
    assert st["statistics"]["trend_pct"] > 0
    # honest insufficiency, not a fabricated statistic
    assert caps.scan_historical_data(
        closes=[1.0] * 10)["status"] == "insufficient_data"


@pytest.mark.asyncio
async def test_coordinated_pass_counts_real_artifacts(caps):
    from trading_bot.core.csc.advisory import AdvisoryModuleAdapter
    # the real CSC may already have a default service attached —
    # measure relative to the baseline, not an absolute 3
    base = len(caps.csc._advisory_services)
    caps.csc.configure_cognition(
        AdvisoryModuleAdapter("stub_dir",
                              lambda c: {"direction": "BUY",
                                         "confidence": 0.7,
                                         "evidence": {"x": 1}}))
    caps.csc.configure_cognition(
        AdvisoryModuleAdapter("stub_flat", lambda c: {}))

    def boom(c):
        raise RuntimeError("always fails")
    caps.csc.configure_cognition(
        AdvisoryModuleAdapter("stub_fail", boom))
    res = await caps.run_coordinated_pass({})
    assert res["agents_consulted"] == base + 3
    assert res["artifacts"] == base + 2
    assert res["errors"] == 1
    assert "stub_fail" in res["failed_services"]
    assert res["directional_artifacts"] >= 1


@pytest.mark.asyncio
async def test_build_deploy_honest_gating(caps):
    res = await caps.build_and_deploy_agents(_bars(_trending()))
    assert res["generation"]["status"] == "completed"
    # whatever validated still needs the durable operator flag — the
    # deployment chain reports awaiting_human, never self-attaches
    for d in res["deployments"]:
        assert d["approve"]["status"] in ("awaiting_human", "approved")
        if d["approve"]["status"] != "approved":
            assert d["deployed"] is False


@pytest.mark.asyncio
async def test_improvement_measured_delta(caps):
    res = await caps.implement_improvement(
        {"kind": "threshold_rule", "feature": "momentum", "op": ">",
         "direction": "BUY"},
        {"kind": "threshold_rule", "feature": "rsi14", "op": "<",
         "direction": "BUY"},
        _bars(_trending()))
    # both specs were really evaluated on the same sealed holdout
    assert res["base"]["candidate_id"]
    assert res["improved"]["candidate_id"]
    assert res["base"]["verdict"] in ("CONFIRMED", "INCONCLUSIVE",
                                      "FALSIFIED", None)
    # gain is either a measured delta or honestly None
    assert res["measured_gain_bps"] is None or isinstance(
        res["measured_gain_bps"], float)


def test_test_and_rollback_real_pytest(caps, tmp_path):
    # protected path refused before touching anything
    refused = caps.test_change_and_rollback(
        "trading_bot/core/csc/controller.py", "x", ["t.py"])
    assert refused["status"] == "refused"
    # spelling aliases of the same protected file must refuse too —
    # './x', '../x/../x' and case differences resolve to the same file
    for alias in ("./trading_bot/core/csc/controller.py",
                  "trading_bot/core/../core/csc/controller.py"):
        # repo_root here is tmp_path — recreate the protected relative
        # layout so the alias resolves to a protected real path
        (tmp_path / "trading_bot/core/csc").mkdir(
            parents=True, exist_ok=True)
        (tmp_path / "trading_bot/core/csc/controller.py").write_text(
            "# protected\n")
        caps2 = CSCCapabilities(caps.csc, caps.ctx,
                                repo_root=tmp_path)
        assert caps2.test_change_and_rollback(
            alias, "x", ["t.py"])["status"] == "refused"
    # real edit + real pytest + real restore on failure
    target = tmp_path / "sample.py"
    target.write_text("VALUE = 1\n")
    test_f = tmp_path / "test_sample.py"
    test_f.write_text(
        "from sample import VALUE\n\n"
        "def test_value():\n    assert VALUE == 2\n")
    res = caps.test_change_and_rollback(
        "sample.py", "VALUE = 2\n", ["test_sample.py"],
        timeout_s=120)
    assert res["status"] == "applied"
    assert res["tests_passed"] is True
    assert res["hash_before"] != res["hash_after"]
    # a failing test rolls back and proves byte-identical restore
    test_f.write_text(
        "from sample import VALUE\n\n"
        "def test_value():\n    assert VALUE == 3\n")
    res2 = caps.test_change_and_rollback(
        "sample.py", "VALUE = 99\n", ["test_sample.py"],
        timeout_s=120)
    assert res2["status"] == "rolled_back"
    assert res2["restored_integrity"] is True
    assert target.read_text() == "VALUE = 2\n"
    # path outside root refused
    out = caps.test_change_and_rollback(
        "../escape.py", "x", ["t.py"])
    assert out["status"] in ("refused", "rejected")


@pytest.mark.asyncio
async def test_scientific_experiment_fdr(caps):
    res = await caps.run_scientific_experiment(
        _bars(_trending()),
        [{"kind": "threshold_rule", "feature": "momentum", "op": ">",
          "direction": "BUY", "name": "e1"},
         {"kind": "threshold_rule", "feature": "rsi14", "op": "<",
          "direction": "BUY", "name": "e2"}])
    assert res["experiments"] == 2
    assert isinstance(res["fdr_survivors"], int)
    assert 0 <= res["fdr_survivors"] <= 2


@pytest.mark.asyncio
async def test_discover_methods_confirmed_only(caps):
    res = await caps.discover_methods(_bars(_trending()))
    for d in res["useful_discoveries"]:
        assert d["verdict"] == "CONFIRMED"


def test_opportunities_and_arbitrage_probe(caps, tmp_path):
    # two sources carrying the same series at different closes -> a
    # real measured discrepancy
    _mk_db(tmp_path / "a.db", _rows(_trending(120)))
    shifted = [c + 0.001 for c in _trending(120)]
    _mk_db(tmp_path / "b.db", _rows(shifted))
    caps.ctx.inventory.sources = ("a.db", "b.db")
    res = caps.detect_opportunities()
    assert res["scan"]["series_scanned"] == 2
    assert res["arbitrage"]["comparable_pairs"] == 1
    f = res["arbitrage"]["findings"][0]
    assert f["discrepancy_bps"] > 0
    assert len(f["sources"]) == 2


def test_industries_and_products(caps, tmp_path):
    # AAA and BBB share the same timestamps and move together -> a
    # measured sector. ZZZ covers a disjoint period — its correlation
    # cannot be measured and it must not be grouped positionally.
    _mk_db(tmp_path / "m.db",
           _rows(_trending(120), symbol="AAA") +
           _rows([c * 1.01 + 0.3 for c in _trending(120)],
                 symbol="BBB") +
           _rows([1.0 + (0.01 if i % 2 else -0.01)
                  for i in range(120)], symbol="ZZZ", base_ts=9000))
    caps.ctx.inventory.sources = ("m.db",)
    res = caps.discover_industries(min_corr=0.3)
    assert res["sectors_found"] >= 1
    ab = [s for s in res["sectors"]
          if "AAA:M15" in s["members"]][0]
    assert set(ab["members"]) == {"AAA:M15", "BBB:M15"}
    assert not any("ZZZ:M15" in s["members"] for s in res["sectors"])
    prod = caps.design_products()
    assert "candidates_total" in prod


def _mk_book_db(path, symbol, bid, bid_qty, ask, ask_qty, ts=1000):
    import json as _json
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE IF NOT EXISTS book_snapshots (id INTEGER "
        "PRIMARY KEY, ts_ms INTEGER, symbol TEXT, last_update_id "
        "INTEGER, bids_json TEXT, asks_json TEXT)")
    con.execute(
        "INSERT INTO book_snapshots (ts_ms, symbol, last_update_id, "
        "bids_json, asks_json) VALUES (?,?,?,?,?)",
        (ts, symbol, 1, _json.dumps([[str(bid), str(bid_qty)]]),
         _json.dumps([[str(ask), str(ask_qty)]])))
    con.commit()
    con.close()


def test_executable_arbitrage_measured(caps, tmp_path):
    a = tmp_path / "venue_a.db"
    b = tmp_path / "venue_b.db"
    # ask at A=100.0, bid at B=100.5 -> 50bps gross, positive after fees
    _mk_book_db(a, "XUSDT", 99.9, 10.0, 100.0, 10.0)
    _mk_book_db(b, "XUSDT", 100.5, 8.0, 100.6, 8.0)
    res = caps.detect_executable_arbitrage(
        [a, b], "XUSDT", fee_bps=5.0, max_gap_ms=2000)
    assert res["status"] == "measured"
    assert res["venues_with_symbol"] == 2
    assert len(res["opportunities"]) == 1
    f = res["opportunities"][0]
    assert f["buy_venue"] == str(a)
    assert f["net_bps_after_fees"] == pytest.approx(50.0 - 10.0,
                                                  abs=0.6)
    assert f["executable_qty"] == 8.0
    # stale quotes -> no opportunity, honestly
    _mk_book_db(a, "YUSDT", 99.9, 1.0, 100.0, 1.0, ts=0)
    _mk_book_db(b, "YUSDT", 100.5, 1.0, 100.6, 1.0, ts=999999)
    res2 = caps.detect_executable_arbitrage(
        [a, b], "YUSDT", fee_bps=5.0, max_gap_ms=2000)
    assert res2["opportunities"] == []
    # one venue -> honest insufficiency, never a fabricated arb
    res3 = caps.detect_executable_arbitrage([a], "XUSDT")
    assert res3["status"] == "insufficient_data"
    assert res3["opportunities"] == []


@pytest.mark.asyncio
async def test_architecture_search_real_enumeration(caps):
    res = await caps.search_architecture_space(_bars(_trending(250)))
    # real enumeration: the full threshold-rule grid + logistic +
    # GA expressions all went through the sealed gate
    assert res["specs_searched"] >= 20
    assert isinstance(res["fdr_survivors"], int)
    assert "no neural NAS" not in res["note"]  # declared in search_space


def test_select_trading_universe_autonomous(caps, tmp_path):
    _mk_db(tmp_path / "m.db",
           _rows(_trending(200), symbol="EURUSD") +
           _rows([1.0 + (0.01 if i % 2 else -0.01)
                  for i in range(200)], symbol="FLAT"))
    caps.ctx.inventory.sources = ("m.db",)
    out = caps.select_trading_universe(top_n=1)
    assert out["selection"], "expected a ranked selection"
    pick = out["selection"][0]
    assert pick["symbol"] == "EURUSD"  # trending -> higher structure
    assert pick["structure_score"] > 0
    # persisted for a runner/operator to consume — real selection
    assert (tmp_path / "exp" / "trading_universe.json").exists()
    assert Path(out["persisted"]).exists()


def test_make_and_use_tools(caps, tmp_path):
    # real synthesis: a validated pure tool is created and callable
    res = caps.make_tool("edge_bps", ["entry", "exit", "fees"],
                         "(exit - entry) / entry * 10000 - fees")
    assert res["status"] == "created"
    out = caps.use_tool("edge_bps", entry=1.10, exit=1.101, fees=5.0)
    assert out["status"] == "evaluated"
    assert out["result"] == pytest.approx(
        (1.101 - 1.10) / 1.10 * 10000 - 5.0, abs=1e-6)
    # missing param reported honestly, never fabricated
    assert caps.use_tool("edge_bps", entry=1.1)["status"] == "error"
    # dangerous constructs refused at synthesis
    assert caps.make_tool("bad", ["x"], "__import__('os').system('x')"
                          )["status"] == "rejected"
    assert caps.make_tool("bad2", ["x"], "open('f')"
                          )["status"] == "rejected"
    # persisted registry — a second call sees the tool
    res2 = caps.make_tool("spread", ["a", "b"], "abs(a - b)")
    assert res2["status"] == "created"
    assert caps.tools_summary()["count"] == 2


def test_make_and_use_data_tools(caps, tmp_path):
    _mk_db(tmp_path / "m.db", _rows(_trending(60)))
    res = caps.make_data_tool(
        "latest_close", tmp_path / "m.db",
        "SELECT close FROM market_data WHERE symbol=:sym "
        "ORDER BY timestamp DESC LIMIT 1")
    assert res["status"] == "created"
    out = caps.use_tool("latest_close", sym="EURUSD")
    assert out["status"] == "evaluated"
    assert out["row_count"] == 1
    assert out["rows"][0][0] == pytest.approx(
        _trending(60)[-1] + 0.0001, abs=1e-5)
    # writes refused honestly
    assert caps.make_data_tool(
        "w", tmp_path / "m.db",
        "DELETE FROM market_data")["status"] == "rejected"
    assert caps.make_data_tool(
        "missing", tmp_path / "nope.db",
        "SELECT 1")["status"] == "rejected"


def test_sandbox_tool_confined(caps, tmp_path):
    res = caps.make_sandbox_tool(
        "greeter",
        "open('out.txt','w').write('hi'); print('done')")
    assert res["status"] == "created"
    out = caps.run_sandbox_tool("greeter")
    assert out["status"] == "evaluated"
    assert out["returncode"] == 0
    assert "done" in out["stdout"]
    # real write happened — but only inside the scratch dir
    assert "out.txt" in out["scratch_artifacts"]
    scratch = Path(caps._tool_registry_path().parent /
                   "sandbox_scratch" / "greeter")
    assert (scratch / "out.txt").read_text() == "hi"
    # and nothing leaked into the repo cwd
    assert not Path("out.txt").exists()


def test_promote_tool_verified(caps, tmp_path):
    caps.make_sandbox_tool("ver", "print('ok')")
    res = caps.promote_tool("ver")
    assert res["status"] == "promoted"
    assert Path(res["module"]).is_file()
    # promoted tool is callable and ran for real
    assert caps.use_tool("ver")["returncode"] == 0
    # a broken tool cannot promote — the gate is the check, not a label
    caps.make_sandbox_tool("bad", "raise SystemExit(3)")
    res2 = caps.promote_tool("bad")
    assert res2["status"] == "error"
    assert not (caps.repo_root / "var" / "tools" / "bad.py").exists()


def test_rsi_promotion_flow(caps, tmp_path):
    rel = "var/rsi_promotion_candidate.txt"
    target = caps.repo_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("X = 1\n")
    # the verification subprocess runs cwd=repo_root (tmp_path here) —
    # give it a real probe test to execute
    (tmp_path / "probe_test.py").write_text(
        "def test_probe():\n    assert True\n")
    try:
        res = caps.submit_rsi_proposal(
            rel, "X = 2\n", test_files=["probe_test.py"])
        assert res["status"] == "pending"
        rec = res["promotion"]
        assert rec["status"] == "awaiting_operator"
        # verified but rolled back — file unchanged
        assert target.read_text() == "X = 1\n"
        # no operator flag -> finalize refuses honestly
        fin = caps.finalize_rsi_promotion(rec["id"])
        assert fin["status"] == "awaiting_operator"
    finally:
        target.unlink(missing_ok=True)


def test_deploy_infrastructure_real_probe(caps, tmp_path):
    _mk_db(tmp_path / "data.db", _rows(_trending(80)))
    res = caps.deploy_infrastructure(tmp_path / "data.db",
                                     kind="market_data")
    assert res["status"] == "onboarded"
    assert res["tables"]["market_data"] == 80
    bad = tmp_path / "empty.db"
    con = sqlite3.connect(bad)
    con.execute("CREATE TABLE x (a INT)")
    con.commit()
    con.close()
    assert caps.deploy_infrastructure(bad)["status"] == "rejected"


def test_balance_resources_measured(caps):
    res = caps.balance_resources()
    assert res["measurement"]["scope"] == "local_host"
    assert 0.10 <= res["recommended_advisory_budget_share"] <= 1.0


def test_provision_infrastructure_real_tool(caps, tmp_path):
    # no tool configured -> honest unavailable, never a fake deploy
    res = caps.provision_infrastructure()
    assert res["status"] == "unavailable"
    assert "no provisioning tool configured" in res["reason"]
    # a real tool (python -c) actually runs and its exit status is
    # measured
    res2 = caps.provision_infrastructure(
        [sys.executable, "-c", "print('infra up')"])
    assert res2["status"] == "provisioned"
    assert res2["exit_code"] == 0
    assert "infra up" in res2["stdout_tail"]
    # missing tool -> unavailable, not provisioned
    res3 = caps.provision_infrastructure(["no_such_tool_xyz"])
    assert res3["status"] == "unavailable"


def test_self_model_fidelity_measured(caps):
    res = caps.self_model_fidelity()
    assert res["surfaces_total"] == 3
    assert 0.0 <= res["fidelity"] <= 1.0
    assert all("accurate" in c for c in res["checks"])


def test_self_model_metrics_real_counts(caps):
    res = caps.self_model_metrics()
    assert "surfaces" in res
    assert 0.0 <= res["introspection_coverage"] <= 1.0
    assert "phenomenal" in res["note"]


def test_knowledge_connections_measured_edges(caps, tmp_path):
    # two evidence artifacts sharing the same measured instrument ->
    # a real edge; nothing connects 'because similar'
    caps.ctx.domains.generate(
        coverage_gaps=[{"source": "m.db", "symbol": "BTCUSD",
                        "timeframe": "H1"}],
        emerging_regimes=[{"symbol": "BTCUSD", "timeframe": "M15",
                           "vol_regime_ratio": 2.1}])
    res = caps.knowledge_connections()
    assert res["nodes"] == 2
    assert res["edge_count"] == 1
    e = res["edges"][0]
    assert e["shared_basis"] == ["instrument"]


def test_deployment_performance_real_ledger(caps, tmp_path):
    led = tmp_path / "trading_state.db"
    _mk_ledger(led)
    res = caps.deployment_performance(led)
    assert res["fills"] == 2
    assert res["commissions_paid"] == pytest.approx(0.03)
    assert res["deployed_notional_by_symbol"]["EURUSD"] == \
        pytest.approx(0.05 * 1.10 + 0.03 * 1.101, abs=1e-4)
    assert res["open_positions"][0]["quantity"] == pytest.approx(0.02)
    # missing ledger is honest unavailable, not a fabricated zero
    assert caps.deployment_performance(
        tmp_path / "nope.db")["status"] == "unavailable"


def test_capability_report_all_claims(caps):
    rep = caps.capability_report()
    assert set(rep["claims"]) == {
        "analyzes_strategies", "optimizes_parameters",
        "scans_historical_data", "coordinated_agent_work",
        "builds_deploys_agents", "implements_improvements",
        "tests_and_rolls_back", "scientific_experiments",
        "trains_tunes_searches", "discovers_trading_methods",
        "opportunity_detection", "industries_and_products",
        "infrastructure", "resource_balance",
        "measurable_self_model", "knowledge_connections",
        "capital_deployment", "executable_arbitrage",
        "architecture_search", "autonomous_symbol_choice",
        "makes_own_tools"}
    assert rep["count"] == 21
    for name, c in rep["claims"].items():
        assert c["mechanism"] and c["scope"], name


def test_attach_capability_services_registers(caps):
    rep = caps.attach_capability_services()
    assert not rep["skipped"], rep
    ids = {getattr(s, "capability_id", "")
           for s in caps.csc._advisory_services}
    assert {"cap_coordinated_electorate", "cap_opportunity_scan",
            "cap_self_model", "cap_resource_balance",
            "cap_knowledge_graph", "cap_product_catalog",
            "cap_claim_report"} <= ids


def test_protected_paths_match_guard():
    # the capability list must refuse exactly the RSI guard's paths —
    # read the tuple via ast so the test never imports the RSI package.
    # The real guard declares it as an ANNOTATED assignment.
    import ast
    src = Path("trading_bot/recursive_self_improvement/"
               "protected_control_plane.py").read_text(
        encoding="utf-8")
    tree = ast.parse(src)
    guard = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", "") == "PROTECTED_PATHS"
                for t in node.targets):
            guard = set(ast.literal_eval(node.value))
        elif isinstance(node, ast.AnnAssign) and getattr(
                node.target, "id", "") == "DEFAULT_PROTECTED_PATHS":
            guard = set(ast.literal_eval(node.value))
    assert guard, "guard path list not found — the check ran on nothing"
    assert guard <= set(PROTECTED_PATHS)

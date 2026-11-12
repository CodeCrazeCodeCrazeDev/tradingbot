"""Research lab: router interface-matching, measured-evidence score
adaptation, agent honest fallbacks, manifest parseability, bounded
queue. No real DBs needed — LabContext is injected."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from trading_bot.core.csc.research_lab import (  # noqa: E402
    AdaptiveRouter, LabContext, ResearchLab, ResearchTask,
    RiskEngineerAgent, build)


def _ctx(tmp_path):
    return LabContext(root=tmp_path, macro_db=tmp_path / "m.db",
                      market_db=tmp_path / "md.db",
                      out_dir=tmp_path / "var")


def test_router_routes_by_provides(tmp_path):
    lab = ResearchLab(_ctx(tmp_path))
    ids = lab.router.route(ResearchTask("risk_memo"))
    assert ids == ["risk_engineer"]
    ids = lab.router.route(ResearchTask("unknown_kind"))
    assert ids == []


def test_router_adapts_on_measured_outcome(tmp_path):
    lab = ResearchLab(_ctx(tmp_path))
    for _ in range(5):
        lab.router.record("risk_engineer", False)
    assert lab.router.table()["risk_engineer"] < 0.7
    for _ in range(5):
        lab.router.record("researcher", True)
    assert lab.router.table()["researcher"] > 0.99


def test_risk_memo_unprovisioned_is_honest(tmp_path):
    art = RiskEngineerAgent().analyze(
        ResearchTask("risk_memo", {"symbol": "EURUSD"}), _ctx(tmp_path))
    assert art.confidence in ("partial", "measured")
    assert "rv_note" in art.data or "rv_20d_bps_daily_eq" in art.data
    assert art.data["symbol"] == "EURUSD"


def test_lab_full_cycle_bounded(tmp_path):
    lab = ResearchLab(_ctx(tmp_path))
    rep = lab.run([ResearchTask(k) for k in
                   ("risk_memo", "opportunity_radar", "bogus")] +
                  [ResearchTask("research")] * 40)
    assert len(rep["artifacts"]) == 32  # MAX_TASKS_PER_CYCLE cap
    assert rep["authority"] == "advisory_only"
    kinds = {a.get("kind") for a in rep["artifacts"]}
    assert "risk_memo" in kinds


def test_manifest_is_discovery_parseable():
    import ast
    src = (ROOT / "trading_bot/core/csc/research_lab.py").read_text()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(
                node.targets[0], "id", "") == "CSC_MANIFEST":
            d = ast.literal_eval(node.value)
            assert d["id"] == "research_lab"
            assert d["kind"] == "advisory"
            assert "opportunity_radar" in d["provides"]
            return
    raise AssertionError("no CSC_MANIFEST found")


def test_build_factory_returns_advisory(tmp_path):
    lab = build(_ctx(tmp_path))
    rep = lab.analyze()
    assert rep["advisory_only"] is True
    assert "routing" in rep

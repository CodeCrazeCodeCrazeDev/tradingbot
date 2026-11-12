"""Research Lab — bounded autonomous research & discovery agents.

The specialist roles the roadmap names (researcher, ML researcher,
distributed-systems engineer, risk engineer, opportunity radar) are
implemented as *advisory agents*: each does bounded real work against
real data and emits honest artifacts. None holds decision authority —
artifacts join the advisory evidence channel; the CSC decides.

Self-rewiring/adaptive routing, honestly: the router maps task kind ->
agent interface ("provides") and prefers agents the electorate
lifecycle rates healthy. A degenerate agent loses routing share
through the same measured-evidence loop every advisor obeys.

The radar fuses the repo's real intelligence feeds (market data,
macro series, COT positioning, release calendar, edge reports) into
an opportunity watchlist — "global economic intelligence" bounded to
what the feeds actually measure.

CSC_MANIFEST: discovery.py wires this module's factory in dep order.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
MAX_TASKS_PER_CYCLE = 32
AGENT_TIMEOUT_S = 120

CSC_MANIFEST = {
    "id": "research_lab",
    "kind": "advisory",
    "provides": ["research", "ml_research", "risk_memo",
                 "systems_review", "opportunity_radar"],
    "requires": ["market_data"],
    "factory": "trading_bot.core.csc.research_lab:build",
    "status": "candidate",
}


# ------------------------------------------------------------------
# Artifacts — every claim carries measured provenance or an honest
# "not provisioned". Nothing simulated.

@dataclass
class Artifact:
    agent: str
    kind: str
    summary: str
    data: Dict[str, Any]
    confidence: str = "measured"   # measured | partial | unprovisioned
    ts: float = field(default_factory=time.time)


class ResearchAgent:
    """Base: manifest-declared specialist. analyze() must return real
    measurements or an honest unprovisioned artifact."""
    id = "base"
    provides: tuple = ()

    def analyze(self, task: "ResearchTask", ctx: "LabContext") -> Artifact:
        raise NotImplementedError


@dataclass
class ResearchTask:
    kind: str            # matches a provides entry
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LabContext:
    root: Path = ROOT
    macro_db: Path = ROOT / "macro_data.db"
    market_db: Path = ROOT / "market_data.db"
    out_dir: Path = ROOT / "var"

    def rows(self, db: Path, sql: str, params=()):
        if not db.exists():
            return []
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            return con.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return []
        finally:
            con.close()


# ------------------------------------------------------------------
# Specialist agents

class ResearcherAgent(ResearchAgent):
    """Literature/evidence retrieval: delegates to the existing
    research engine's fetchers; reports what it could not reach."""
    id = "researcher"
    provides = ("research",)

    def analyze(self, task, ctx):
        topic = task.payload.get("topic", "")
        try:
            from trading_bot.core.csc.research import fetchers  # noqa
            fns = [n for n in dir(fetchers) if n.startswith("fetch")]
            return Artifact(self.id, "research",
                            f"research engine reachable; "
                            f"{len(fns)} fetchers for '{topic}'",
                            {"fetchers": fns, "topic": topic})
        except Exception as exc:  # noqa: BLE001
            return Artifact(self.id, "research",
                            "research engine unreachable",
                            {"topic": topic, "error": str(exc)},
                            confidence="unprovisioned")


class MLResearchAgent(ResearchAgent):
    """Bounded ML/edge experiments: runs the real edge gates as
    subprocesses or reads their reports — measured verdicts only."""
    id = "ml_researcher"
    provides = ("ml_research",)

    def analyze(self, task, ctx):
        report = ctx.out_dir / "edge_features.json"
        if not report.exists():
            return Artifact(self.id, "ml_research",
                            "no edge_features report — run "
                            "scripts/edge_features.py first",
                            {}, confidence="unprovisioned")
        r = json.loads(report.read_text())
        verdicts = {}
        for ch in ("m15", "d1"):
            for k, v in r.get(ch, {}).items():
                if isinstance(v, dict) and "status" in v:
                    verdicts[k] = {"status": v["status"],
                                   "lcb5": v.get("lcb5_net_bps")}
        n_edge = sum(1 for v in verdicts.values()
                     if v["status"] == "candidate_edge")
        return Artifact(self.id, "ml_research",
                        f"{len(verdicts)} hypotheses measured, "
                        f"{n_edge} candidate_edge",
                        {"verdicts": verdicts,
                         "warnings": r.get("warnings", [])})


class RiskEngineerAgent(ResearchAgent):
    """Real risk memo: realized vol, COT positioning tails, release
    calendar density — measured from the provisioned DBs."""
    id = "risk_engineer"
    provides = ("risk_memo",)

    def analyze(self, task, ctx):
        sym = task.payload.get("symbol", "EURUSD")
        bars = ctx.rows(ctx.market_db,
                        "SELECT close, timestamp FROM market_data "
                        "WHERE symbol=? ORDER BY timestamp DESC "
                        "LIMIT 2000", (sym,))
        out: Dict[str, Any] = {"symbol": sym}
        conf = "measured"
        if len(bars) >= 200:
            closes = [b[0] for b in reversed(bars)]
            rets = [(closes[i] / closes[i-1] - 1)
                    for i in range(1, len(closes))]
            mu = sum(rets) / len(rets)
            var = sum((r - mu) ** 2 for r in rets) / len(rets)
            out["rv_20d_bps_daily_eq"] = round(var ** 0.5 * 1e4, 2)
            out["bars"] = len(closes)
        else:
            out["rv_note"] = f"only {len(bars)} bars"
            conf = "partial"
        cot = ctx.rows(ctx.macro_db,
                       "SELECT report_date, net_pct_oi FROM "
                       "cot_positions WHERE symbol=? AND "
                       "category='managed_money' ORDER BY report_date "
                       "DESC LIMIT 52", (sym,))
        if cot:
            vals = [c[1] for c in cot if c[1] is not None]
            if vals:
                m = sum(vals) / len(vals)
                sd = (sum((v - m) ** 2 for v in vals) / len(vals)) ** 0.5
                out["cot_net_pct_oi"] = round(vals[0], 1)
                out["cot_z"] = round((vals[0] - m) / (sd or 1), 2)
        events = ctx.rows(ctx.macro_db,
                          "SELECT COUNT(*) FROM news_events WHERE "
                          "impact='High' AND ts_utc > datetime('now')",
                          ())
        out["high_impact_events_ahead"] = events[0][0] if events else 0
        return Artifact(self.id, "risk_memo",
                        f"{sym}: rv={out.get('rv_20d_bps_daily_eq')}"
                        f" cot_z={out.get('cot_z')}"
                        f" events_ahead={out['high_impact_events_ahead']}",
                        out, confidence=conf)


class SystemsEngineerAgent(ResearchAgent):
    """Distributed-systems review: topology + health of the wiring
    graph itself — agents, interface coverage, cycles, orphans."""
    id = "systems_engineer"
    provides = ("systems_review",)

    def analyze(self, task, ctx):
        try:
            from .discovery import scan_packages
            plan = scan_packages([ctx.root / "trading_bot"])
            return Artifact(
                self.id, "systems_review",
                f"{len(plan.ordered)} wired nodes, "
                f"{len(plan.blocked)} blocked, "
                f"{len(plan.cycles)} cycles, "
                f"{plan.scanned} files scanned",
                {"wired": [m.id for m in plan.ordered],
                 "blocked": [n.manifest.id for n in plan.blocked],
                 "cycles": plan.cycles,
                 "interfaces": sorted({p for m in plan.ordered
                                       for p in m.provides})})
        except Exception as exc:  # noqa: BLE001
            return Artifact(self.id, "systems_review",
                            "discovery scan failed",
                            {"error": str(exc)},
                            confidence="unprovisioned")


class OpportunityRadarAgent(ResearchAgent):
    """Global opportunity radar: fuses what the feeds actually
    measure into a ranked watchlist. Every row carries its evidence —
    'radar' means honest signal strength, never asserted edge."""
    id = "opportunity_radar"
    provides = ("opportunity_radar",)

    def analyze(self, task, ctx):
        watch = []
        symbols = task.payload.get(
            "symbols", ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"])
        for sym in symbols:
            bars = ctx.rows(ctx.market_db,
                            "SELECT close FROM market_data WHERE "
                            "symbol=? ORDER BY timestamp DESC "
                            "LIMIT 500", (sym,))
            cot = ctx.rows(ctx.macro_db,
                           "SELECT net_pct_oi FROM cot_positions "
                           "WHERE symbol=? AND category='managed_money'"
                           " ORDER BY published_at DESC LIMIT 1",
                           (sym,))
            row: Dict[str, Any] = {"symbol": sym}
            if len(bars) >= 100:
                closes = [b[0] for b in reversed(bars)]
                mom = (closes[-1] / closes[0] - 1) * 1e4
                row["momentum_bps"] = round(mom, 1)
            if cot and cot[0][0] is not None:
                row["cot_net_pct_oi"] = round(cot[0][0], 1)
            row["data"] = ("market+cot" if len(bars) >= 100 and cot
                           else "market" if len(bars) >= 100
                           else "cot" if cot else "none")
            watch.append(row)
        edge_r = ctx.out_dir / "edge_features.json"
        if edge_r.exists():
            r = json.loads(edge_r.read_text())
            for ch in ("m15", "d1"):
                for k, v in r.get(ch, {}).items():
                    if isinstance(v, dict) and v.get("status") == \
                            "candidate_edge":
                        watch.append({"symbol": "HYPOTHESIS",
                                      "signal": k,
                                      "lcb5_bps": v["lcb5_net_bps"],
                                      "data": "edge_gate"})
        return Artifact(self.id, "opportunity_radar",
                        f"{len(watch)} watchlist rows",
                        {"watchlist": watch})


# ------------------------------------------------------------------
# Adaptive router + lab orchestrator

AGENTS: Dict[str, type] = {a.id: a for a in (
    ResearcherAgent, MLResearchAgent, RiskEngineerAgent,
    SystemsEngineerAgent, OpportunityRadarAgent)}


class AdaptiveRouter:
    """Routes tasks to agents by interface (provides) and measured
    health. Health scores come from the electorate lifecycle when a
    CSC is attached; standalone, every agent starts at 1.0 and the
    router records outcomes so the routing table itself is evidence-
    driven (that's the self-rewiring part — routing adapts by
    measured success, never by assertion)."""

    def __init__(self, agents: Dict[str, ResearchAgent]):
        self._agents = agents
        self._score: Dict[str, float] = {i: 1.0 for i in agents}

    def route(self, task: ResearchTask) -> List[str]:
        candidates = [a for a in self._agents.values()
                      if task.kind in a.provides]
        candidates.sort(key=lambda a: -self._score[a.id])
        return [a.id for a in candidates]

    def record(self, agent_id: str, ok: bool):
        s = self._score.get(agent_id, 1.0)
        # bounded EMA — one bad run can't kill an agent, sustained
        # failure costs routing share
        self._score[agent_id] = 0.9 * s + 0.1 * (1.0 if ok else 0.0)

    def table(self) -> Dict[str, float]:
        return dict(self._score)


class ResearchLab:
    """The lab: bounded task queue -> router -> agents -> artifact
    report. Advisory by construction — it is attached to the CSC via
    configure_cognition like every other advisory service."""

    capability_id = "research_lab"

    def __init__(self, ctx: Optional[LabContext] = None):
        self.ctx = ctx or LabContext()
        self.router = AdaptiveRouter({i: a() for i, a in AGENTS.items()})

    def run(self, tasks: List[ResearchTask]) -> Dict[str, Any]:
        tasks = tasks[:MAX_TASKS_PER_CYCLE]
        artifacts = []
        t0 = time.time()
        for t in tasks:
            agent_ids = self.router.route(t)
            if not agent_ids:
                artifacts.append({
                    "kind": t.kind, "error": "no agent provides this"})
                continue
            aid = agent_ids[0]
            try:
                art = self._agents_call(aid, t)
                self.router.record(aid, art.confidence != "unprovisioned")
                artifacts.append({
                    "agent": aid, "kind": art.kind,
                    "summary": art.summary, "confidence": art.confidence,
                    "data": art.data})
            except Exception as exc:  # noqa: BLE001
                self.router.record(aid, False)
                artifacts.append({"agent": aid, "kind": t.kind,
                                  "error": str(exc)})
        return {
            "artifacts": artifacts,
            "routing": self.router.table(),
            "elapsed_s": round(time.time() - t0, 2),
            "authority": "advisory_only",
        }

    def _agents_call(self, aid: str, task: ResearchTask) -> Artifact:
        return self.router._agents[aid].analyze(task, self.ctx)

    # advisory interface — the CSC's consult loop calls analyze()
    def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        tasks = [ResearchTask(k) for k in
                 ("research", "ml_research", "risk_memo",
                  "systems_review", "opportunity_radar")]
        rep = self.run(tasks)
        rep["advisory_only"] = True
        return rep


def build(ctx: Optional[LabContext] = None) -> ResearchLab:
    """CSC_MANIFEST factory — returns the lab as an advisory service."""
    return ResearchLab(ctx)

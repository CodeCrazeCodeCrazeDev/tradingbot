"""AFI research-state advisory service for the CSC.

Exposes the Autonomous Financial Intelligence artifacts — analyst
classifications, live probe outcomes, data-quality flags, claims
funnel — as advisory evidence the CSC can weigh during
deliberation. Advisory ONLY: this module reads artifacts and
returns evidence; it holds no decision, sizing, or execution
authority. Promotion/deployment remains behind the canonical
gates + signed OperatorAuthorization.

Register via DEFAULT_ADVISORY_FACTORIES in csc/advisory.py:
    ("afi_research", _afi_research_service)
"""

import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[4]
VAR = ROOT / "var"


def _load(name: str) -> Any:
    p = VAR / name
    try:
        return json.loads(p.read_text()) if p.exists() else None
    except Exception:
        return None


def afi_research_evidence(ctx: Mapping[str, Any]) -> dict:
    """fn(context) -> evidence dict for AdvisoryModuleAdapter.

    Summarizes the research pipeline state relevant to the current
    observation's symbol when possible; always advisory-only.
    """
    symbol = str(ctx.get("symbol") or "").upper()
    out: dict[str, Any] = {"service": "afi_research"}

    # Analyst classifications — the judgment layer
    q = _load("analyst_queue.json") or {}
    counts = q.get("counts") or {}
    live = [s for s in (q.get("specs") or [])
            if s.get("classification") != "DEAD"]
    if live:
        out["live_signals"] = [
            {"spec_id": s.get("spec_id"),
             "family": s.get("family"),
             "classification": s.get("classification"),
             "headroom_bps": s.get("cost_headroom_bps"),
             "reasons": (s.get("reasons") or [])[:2]}
            for s in live[:5]]
    out["analyst_counts"] = counts
    out["analyst_alerts"] = (q.get("alerts") or [])[:5]

    # Live probe outcomes — the spine's own trading evidence
    cands = VAR / "method_candidates"
    live_recs = []
    if cands.is_dir():
        for f in sorted(cands.glob("live_*.json"))[-5:]:
            try:
                r = json.loads(f.read_text())
                ov = (r.get("verdict") or {}).get("overall") or {}
                live_recs.append({
                    "run": f.stem,
                    "trades": ov.get("trades"),
                    "mean_net_bps": ov.get("mean_net_bps"),
                    "lcb5_net_bps": ov.get("lcb5_net_bps"),
                    "verdict": (r.get("verdict") or {}).get("verdict")})
            except Exception:
                continue
    if live_recs:
        out["live_probe_outcomes"] = live_recs

    # Data-quality flags relevant to this symbol's dataset
    dq = _load("data_quality.json") or {}
    flags = []
    for d in dq.get("dbs", []):
        for s in d.get("series", []):
            if symbol and s.get("symbol") != symbol:
                continue
            bad = {k: s.get(k) for k in
                   ("off_grid", "non_monotonic", "extreme_ret",
                    "dup_ts") if s.get(k)}
            if bad:
                flags.append({"db": d.get("db"),
                              "symbol": s.get("symbol"),
                              "timeframe": s.get("timeframe"),
                              "rows": s.get("rows"), "flags": bad})
    if flags:
        out["data_quality_flags"] = flags[:8]

    # Open data/spec requests — what the system needs
    dr = _load("data_requests.json") or {}
    reqs = list((dr.get("requests") or {}).values())
    if reqs:
        out["open_requests"] = [
            {"kind": r.get("kind"), "need": r.get("need"),
             "count": r.get("count")} for r in reqs[:5]]

    # Direction: neutral — research state informs, never directs
    out["direction"] = "NEUTRAL"
    out["advisory_only"] = True
    return out


def _afi_research_service():
    """Factory for DEFAULT_ADVISORY_FACTORIES registration."""
    from trading_bot.core.csc.advisory import AdvisoryModuleAdapter
    return AdvisoryModuleAdapter("afi_research", afi_research_evidence,
                                 timeout_s=3.0)

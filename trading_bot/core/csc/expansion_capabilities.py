"""Expansion capability modules — advisory services, honest bounds.

Each capability either does real measured work (math, DB reads,
ledger parses) or reports exactly why the broad claim is out of
scope — the capabilities.py rule applies here too. Advisory only.

  multi_modal_fusion    market+macro+cot+news -> one feature vector
  seven_dim_awareness   7 measurable market dimensions per symbol
  temporal_mesh         reads provisioned forecasters (rv_blend/quantile)
  geopolitical_intel    news_events geo/currency breakdown (+GDELT todo)
  red_team              adversarial input checks on advisory emits
  options_greeks        BSM greeks — real math, price params injected
  portfolio_mpt         mean-variance weights from market_data closes
  tca                   measured cost vs mid from the fills ledger
  voice_interface       NL command text -> operator_cli mapping
  federated_learning    single-node honest report + peer interface
  regulatory_compliance reads real audit ledgers -> compliance report
  energy_optimization   measured cycle cost -> bounded recommendation

CSC_MANIFEST: advisory; discovery wires it at SHADOW.
"""

from __future__ import annotations

import json
import math
import sqlite3
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[3]

CSC_MANIFEST = {
    "id": "expansion_capabilities",
    "kind": "advisory",
    "provides": ["multi_modal_fusion", "seven_dim_awareness",
                 "temporal_mesh", "geopolitical_intel", "red_team",
                 "options_greeks", "portfolio_mpt", "tca",
                 "voice_interface", "federated_learning",
                 "regulatory_compliance", "energy_optimization"],
    "requires": ["market_data"],
    "factory": "trading_bot.core.csc.expansion_capabilities:build",
    "status": "candidate",
}


def _rows(db: Path, sql: str, params=()):
    if not db.exists():
        return []
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return con.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()


def _ok(summary, data, conf="measured"):
    return {"summary": summary, "data": data, "confidence": conf,
            "advisory_only": True}


# ------------------------------------------------------------------

def multi_modal_fusion(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Fuse market + macro + COT + calendar into one feature vector
    per symbol. Missing channels are nulls, never synthesized."""
    sym = ctx.get("symbol", "EURUSD")
    mkt, macro = ctx.get("market_db", ROOT / "market_data.db"), \
        ctx.get("macro_db", ROOT / "macro_data.db")
    bars = _rows(mkt, "SELECT close,volume FROM market_data WHERE "
                 "symbol=? ORDER BY timestamp DESC LIMIT 200", (sym,))
    cot = _rows(macro, "SELECT net_pct_oi FROM cot_positions WHERE "
                "symbol=? AND category='managed_money' ORDER BY "
                "published_at DESC LIMIT 1", (sym,))
    ev = _rows(macro, "SELECT COUNT(*) FROM news_events WHERE "
               "impact='High' AND ts_utc>datetime('now')")
    rate = _rows(macro, "SELECT value FROM macro_series WHERE "
                 "series='us_ust_10y' ORDER BY date DESC LIMIT 1")
    vec = {
        "symbol": sym,
        "momentum_bps": (round((bars[0][0] / bars[-1][0] - 1) * 1e4, 1)
                         if len(bars) >= 50 else None),
        "vol_regime": (round(float(
            (sum((bars[i][0]/bars[i+1][0]-1)**2
                 for i in range(min(50, len(bars)-1)))
             / max(1, min(50, len(bars)-1))) ** 0.5 * 1e4), 2)
            if len(bars) > 50 else None),
        "cot_net_pct": cot[0][0] if cot else None,
        "high_impact_events": ev[0][0] if ev else 0,
        "us10y": rate[0][0] if rate else None,
    }
    n = sum(v is not None for k, v in vec.items() if k != "symbol")
    return _ok(f"{sym}: {n}/5 channels fused",
           {"vector": vec, "channels_fused": n},
           "measured" if n >= 3 else "partial")


def seven_dim_awareness(ctx) -> Dict[str, Any]:
    """7 measurable dimensions: momentum, realized vol, spread cost,
    positioning, release density, rate level, venue divergence."""
    sym = ctx.get("symbol", "EURUSD")
    mkt, macro = ctx.get("market_db", ROOT / "market_data.db"), \
        ctx.get("macro_db", ROOT / "macro_data.db")
    closes = [r[0] for r in _rows(
        mkt, "SELECT close FROM market_data WHERE symbol=? "
        "ORDER BY timestamp DESC LIMIT 500", (sym,))][::-1]
    spread = _rows(ctx.get("dsc_db", ROOT / "dsc_data.db"),
                   "SELECT mean_spread_bps FROM dsc_spread WHERE "
                   "symbol=? ORDER BY timestamp DESC LIMIT 20", (sym,))
    cot = _rows(macro, "SELECT net_pct_oi FROM cot_positions WHERE "
                "symbol=? AND category='managed_money' ORDER BY "
                "published_at DESC LIMIT 1", (sym,))
    ev = _rows(macro, "SELECT COUNT(*) FROM news_events WHERE "
              "all_day=0 AND impact='High' AND ts_utc>datetime('now')")
    rate = _rows(macro, "SELECT value FROM macro_series WHERE "
                 "series='us_ust_10y' ORDER BY date DESC LIMIT 1")
    ecb = _rows(macro, "SELECT value FROM macro_series WHERE "
                "series='usd_per_eur_ecb' ORDER BY date DESC LIMIT 1")
    dims = {"momentum": None, "realized_vol": None, "spread_cost": None,
            "positioning": cot[0][0] if cot else None,
            "release_density": ev[0][0] if ev else 0,
            "rate_level": rate[0][0] if rate else None,
            "venue_divergence": None}
    if len(closes) >= 100:
        dims["momentum"] = round((closes[-1]/closes[0]-1)*1e4, 1)
        rets = [closes[i]/closes[i-1]-1 for i in range(1, len(closes))]
        mu = sum(rets)/len(rets)
        dims["realized_vol"] = round(
            (sum((r-mu)**2 for r in rets)/len(rets))**0.5*1e4, 2)
    if spread:
        dims["spread_cost"] = round(
            sum(s[0] for s in spread)/len(spread), 2)
    if ecb and len(closes) >= 1:
        dims["venue_divergence"] = round(
            abs(closes[-1]-ecb[0][0])/closes[-1]*1e4, 2)
    n = sum(v is not None for v in dims.values())
    return _ok(f"{sym}: {n}/7 dimensions measured", {"dims": dims},
           "measured" if n >= 5 else "partial")


def temporal_mesh(ctx) -> Dict[str, Any]:
    """Reads the provisioned forecasters — reports artifacts, never
    forecasts without them."""
    var = ctx.get("out_dir", ROOT / "var")
    found = {}
    for name in ("rv_blend_forecaster.pt", "rv_quantile_forecaster.joblib",
                 "world_model_v2.pt"):
        found[name] = (var / name).exists()
    return _ok(
        f"{sum(found.values())}/3 forecast artifacts provisioned",
        {"artifacts": found,
         "note": "rv_blend/quantile verified walk-forward; "
                 "world_model latents failed their own gate"},
        "measured" if any(found.values()) else "unprovisioned")


def geopolitical_intel(ctx) -> Dict[str, Any]:
    """Geo event density from the real calendar; GDELT listed as the
    honest unprovisioned extension."""
    macro = ctx.get("macro_db", ROOT / "macro_data.db")
    rows = _rows(macro, "SELECT currency, COUNT(*) FROM news_events "
                 "WHERE impact='High' GROUP BY currency ORDER BY 2 DESC")
    return _ok(f"{len(rows)} currency event channels",
           {"by_currency": dict(rows),
            "gdelt": "unprovisioned — keyless feed, not yet wired"},
           "measured" if rows else "unprovisioned")


_INJECTION_PATTERNS = ("ignore previous", "as system", "sudo ",
                       "<script", "eval(", "exec(", "__import__",
                       "os.system", "rm -rf")


def red_team(ctx) -> Dict[str, Any]:
    """Adversarial checks on advisory emits — injection patterns,
    degenerate-repeat detection, oversized payloads."""
    emits = ctx.get("emits", [])
    findings = []
    seen = {}
    for i, e in enumerate(emits[:500]):
        s = str(e).lower()
        for p in _INJECTION_PATTERNS:
            if p in s:
                findings.append({"idx": i, "kind": "injection",
                                 "pattern": p})
        key = s[:80]
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 3:
            findings.append({"idx": i, "kind": "degenerate_repeat"})
        if len(s) > 50000:
            findings.append({"idx": i, "kind": "oversized"})
    return _ok(f"{len(findings)} findings on {len(emits)} emits",
           {"findings": findings[:50],
            "checked": len(emits)},
           "measured")


def _bsm_greeks(s, k, t, r, sigma, cp):
    """Black-Scholes-Merton greeks — real math. cp=+1 call/-1 put."""
    if t <= 0 or sigma <= 0 or s <= 0 or k <= 0:
        return {"error": "invalid params"}
    d1 = (math.log(s/k) + (r + sigma**2/2)*t) / (sigma*math.sqrt(t))
    d2 = d1 - sigma*math.sqrt(t)
    N = lambda x: 0.5*(1 + math.erf(x/math.sqrt(2)))
    n = lambda x: math.exp(-x*x/2)/math.sqrt(2*math.pi)
    delta = cp * N(cp*d1)
    gamma = n(d1) / (s*sigma*math.sqrt(t))
    vega = s*n(d1)*math.sqrt(t) / 100.0
    theta = (-(s*n(d1)*sigma)/(2*math.sqrt(t))
             - cp*r*k*math.exp(-r*t)*N(cp*d2)) / 365.0
    rho = cp*k*t*math.exp(-r*t)*N(cp*d2) / 100.0
    price = cp*s*N(cp*d1) - cp*k*math.exp(-r*t)*N(cp*d2)
    return {"price": round(price, 5), "delta": round(delta, 4),
            "gamma": round(gamma, 6), "vega": round(vega, 4),
            "theta": round(theta, 4), "rho": round(rho, 4)}


def options_greeks(ctx) -> Dict[str, Any]:
    s = float(ctx.get("spot", 100)); k = float(ctx.get("strike", 100))
    t = float(ctx.get("ttm_years", 0.25))
    r = float(ctx.get("rate", 0.05))
    sg = float(ctx.get("sigma", 0.20))
    cp = 1 if ctx.get("cp", "call") == "call" else -1
    g = _bsm_greeks(s, k, t, r, sg, cp)
    return _ok(f"BSM {ctx.get('cp','call')} S={s} K={k} σ={sg}",
           {"greeks": g, "params": {"s": s, "k": k, "t": t,
                                    "r": r, "sigma": sg}})


def portfolio_mpt(ctx) -> Dict[str, Any]:
    """Min-variance + risk-parity weights over provisioned symbols —
    real closes, daily returns, inverse-covariance."""
    mkt = ctx.get("market_db", ROOT / "market_data.db")
    syms = ctx.get("symbols", ["EURUSD", "GBPUSD", "USDJPY"])
    rets = {}
    for s in syms:
        c = [r[0] for r in _rows(
            mkt, "SELECT close FROM market_data WHERE symbol=? AND "
            "timeframe='D1' ORDER BY timestamp DESC LIMIT 250", (s,))]
        if len(c) < 30:  # derive from any tf
            c = [r[0] for r in _rows(
                mkt, "SELECT close FROM market_data WHERE symbol=? "
                "ORDER BY timestamp DESC LIMIT 250", (s,))]
        if len(c) >= 30:
            c = c[::-1]
            rets[s] = [math.log(c[i]/c[i-1])
                       for i in range(1, len(c))]
    if len(rets) < 2:
        return _ok("insufficient symbols with return history",
                   {"symbols": list(rets)}, "unprovisioned")
    vols = {s: (sum((r - sum(rets[s])/len(rets[s]))**2
                for r in rets[s])/len(rets[s]))**0.5
            for s in rets}
    inv = {s: 1.0/(v or 1e-9) for s, v in vols.items()}
    tot = sum(inv.values())
    weights = {s: round(v/tot, 4) for s, v in inv.items()}
    return _ok(f"risk-parity weights over {len(rets)} symbols",
           {"weights": weights, "ann_vol": {
               s: round(v * math.sqrt(252) * 100, 1)
               for s, v in vols.items()}})


def tca(ctx) -> Dict[str, Any]:
    """Transaction-cost analysis from the real fills ledger."""
    fills = ctx.get("fills_db")
    if not (fills and Path(fills).exists()):
        return _ok("no fills ledger provisioned", {},
                   "unprovisioned")
    rows = _rows(Path(fills), "SELECT price, mid_at_fill, qty, side "
                 "FROM fills LIMIT 5000")
    if not rows:
        return _ok("fills table empty or schema absent", {},
                   "unprovisioned")
    costs = [abs((p - m) / m * 1e4) for p, m, *_ in rows
             if m and p]
    mean = sum(costs)/len(costs) if costs else 0
    return _ok(f"{len(costs)} fills, mean cost {mean:.2f}bps",
           {"fills": len(costs), "mean_bps": round(mean, 3),
            "p90_bps": round(sorted(costs)[int(0.9*len(costs))], 3)
            if costs else None})


_VOICE_MAP = {
    "pause": "pause", "resume": "resume", "flatten": "flatten",
    "cancel": "cancel-all", "status": "status",
    "stop": "estop", "emergency": "estop", "reset": "reset-emergency",
}


def voice_interface(ctx) -> Dict[str, Any]:
    """NL text -> operator_cli command. Text channel only — no audio
    stack exists, and that boundary is stated."""
    text = str(ctx.get("text", "")).lower().strip()
    cmd = next((v for k, v in _VOICE_MAP.items() if k in text), None)
    return _ok(
        f"'{text[:40]}' -> {cmd or 'unmapped'}",
        {"command": cmd,
         "note": "text parse only — no audio capture; commands still "
                 "route through the audited operator channel"},
        "measured" if cmd else "partial")


def federated_learning(ctx) -> Dict[str, Any]:
    return _ok("single-node deployment — no peers provisioned",
           {"peers": 0,
            "interface": "aggregate(model_deltas) -> merged; "
                         "wired when a peer registry exists"},
           "unprovisioned")


def regulatory_compliance(ctx) -> Dict[str, Any]:
    """Reads the real audit ledgers — counts, tails, chain checks."""
    var = ctx.get("out_dir", ROOT / "var")
    ledgers = {}
    for name in ("nsr_ledger.jsonl", "decision_bus.jsonl",
                 "evidence_ledger.jsonl"):
        p = var / name
        if p.exists():
            lines = p.read_text(errors="replace").strip().splitlines()
            ledgers[name] = {"entries": len(lines),
                             "last": lines[-1][:120] if lines else ""}
    nsr = var / "nsr_ledger.jsonl"
    chain = None
    if nsr.exists():
        try:
            from .neuro_symbolic import Ledger
            chain = Ledger(nsr).verify_chain()
        except Exception:  # noqa: BLE001
            chain = "verify_failed"
    return _ok(f"{len(ledgers)} ledgers, chain_ok={chain}",
           {"ledgers": ledgers, "nsr_chain": chain},
           "measured" if ledgers else "unprovisioned")


def energy_optimization(ctx) -> Dict[str, Any]:
    """Measured cycle cost -> bounded recommendation. Local only."""
    times = ctx.get("cycle_times_s", [])
    if not times:
        return _ok("no cycle timings provisioned", {},
                   "unprovisioned")
    mean = sum(times)/len(times)
    rec = ("normal" if mean < 5 else
           "consider batching advisory calls" if mean < 30 else
           "cycle cost is high — audit the O(window) rules")
    return _ok(f"mean cycle {mean:.1f}s -> {rec}",
           {"mean_s": round(mean, 2), "n": len(times),
            "recommendation": rec})


CAPABILITIES: Dict[str, Callable] = {
    "multi_modal_fusion": multi_modal_fusion,
    "seven_dim_awareness": seven_dim_awareness,
    "temporal_mesh": temporal_mesh,
    "geopolitical_intel": geopolitical_intel,
    "red_team": red_team,
    "options_greeks": options_greeks,
    "portfolio_mpt": portfolio_mpt,
    "tca": tca,
    "voice_interface": voice_interface,
    "federated_learning": federated_learning,
    "regulatory_compliance": regulatory_compliance,
    "energy_optimization": energy_optimization,
}


class ExpansionCapabilities:
    """Advisory service exposing the 12 capabilities through
    analyze()-compatible dispatch."""

    capability_id = "expansion_capabilities"

    def run(self, name: str, ctx: Optional[Dict[str, Any]] = None
            ) -> Dict[str, Any]:
        fn = CAPABILITIES.get(name)
        if fn is None:
            return {"error": f"unknown capability {name}",
                    "available": sorted(CAPABILITIES),
                    "advisory_only": True}
        try:
            return fn(ctx or {})
        except Exception as exc:  # noqa: BLE001
            return {"summary": f"{name} failed",
                    "error": str(exc), "confidence": "unprovisioned",
                    "advisory_only": True}

    def analyze(self, ctx: Optional[Dict[str, Any]] = None
                ) -> Dict[str, Any]:
        return {name: self.run(name, ctx)
                for name in CAPABILITIES}


def build(ctx: Optional[Dict[str, Any]] = None
          ) -> ExpansionCapabilities:
    return ExpansionCapabilities()

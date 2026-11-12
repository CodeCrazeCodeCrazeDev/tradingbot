"""Method evaluation — closes the knowledge->candidate->verdict loop (M1).

Takes a bounded method spec (allow-listed strategy families only —
mean_reversion / momentum / stat_arb, numeric params inside fixed
bounds), compiles it into a position series over REAL local data with
no lookahead (signal at bar t earns return t+1), charges turnover the
real cost model, and writes an auditable verdict row.

Specs come from:
  --spec file.json        hand-authored (or extractor-emitted) spec
  --from-ledger FILE      auto-propose specs from a scout ledger
                          (var/ecie/scout_ledger.jsonl rows) via keyword
                          extraction — proposals are marked
                          auto_extracted and use family defaults
  --family F --symbol SYM --db DB --tf TF   inline spec

Verdicts append to var/methods/ledger.jsonl:
  PASS        net Sharpe > 1 and net total > 0 after costs
  MARGINAL    gross edge exists but dies under costs
  FAIL        no edge even gross
  REJECTED    spec invalid / out of bounds / data missing

Everything is advisory: this evaluates methods, it cannot emit orders.

    .venv/Scripts/python.exe scripts/method_eval.py --family momentum \
        --db binance_data.db --symbol BTC --tf 15m --cost-bps 13
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

try:  # scripts/ on sys.path when run as a file, repo root under pytest
    from scripts.edge_baseline import quarantine_flags
except ImportError:
    from edge_baseline import quarantine_flags

OUT = Path("var/methods/ledger.jsonl")

# --- bounded parameter envelope (Level-1 candidate space) -------------------
FAMILIES = ("mean_reversion", "momentum", "stat_arb")
BOUNDS = {"lookback": (5, 500), "entry_z": (0.5, 4.0),
          "exit_z": (0.0, 3.0), "vol_lookback": (10, 200)}
DEFAULTS = {"lookback": 20, "entry_z": 1.5, "exit_z": 0.0,
            "vol_lookback": 50, "vol_scale": True}


def validate_spec(spec: dict) -> tuple[bool, str]:
    fam = spec.get("family")
    if fam not in FAMILIES:
        return False, f"family {fam!r} not in {FAMILIES}"
    p = {**DEFAULTS, **(spec.get("params") or {})}
    for k, (lo, hi) in BOUNDS.items():
        v = p.get(k)
        if v is None or not (lo <= float(v) <= hi):
            return False, f"param {k}={v} out of bounds [{lo},{hi}]"
    if not spec.get("db") or not spec.get("symbol"):
        return False, "spec needs db + symbol"
    return True, ""


# --- data -------------------------------------------------------------------

def _ohlcv_table(con: sqlite3.Connection) -> str | None:
    for (name,) in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"):
        cols = {r[1] for r in con.execute(f"PRAGMA table_info({name})")}
        if {"symbol", "timestamp", "close"} <= cols:
            return name
    return None


def load_closes(db_path: str, symbol: str, tf: str) -> np.ndarray:
    con = sqlite3.connect(db_path)
    try:
        table = _ohlcv_table(con)
        if not table:
            return np.array([])
        rows = con.execute(
            f"SELECT close FROM {table} WHERE symbol=? "
            f"AND (timeframe=? OR ? IS NULL) ORDER BY timestamp",
            (symbol, tf, tf)).fetchall()
        return np.array([r[0] for r in rows if r[0]])
    finally:
        con.close()


# --- compilation: spec -> (signal, returns) with no lookahead ---------------

def zscore(x: np.ndarray, w: int) -> np.ndarray:
    z = np.full_like(x, np.nan, dtype=float)
    for i in range(w, len(x)):
        s = x[i - w:i]
        sd = s.std()
        z[i] = (x[i] - s.mean()) / sd if sd > 0 else 0.0
    return z


def compile_positions(family: str, params: dict,
                      closes_a: np.ndarray,
                      closes_b: np.ndarray | None = None,
                      ) -> tuple[np.ndarray, np.ndarray]:
    """Return (signal, eval_returns): target position in [-1,1] per bar
    timestamped at the bar it is computed on (caller shifts for PnL),
    plus the return series the position earns — the hedged spread
    return for stat_arb."""
    lb = int(params["lookback"]); ez = float(params["entry_z"])
    n = len(closes_a)
    ret = np.diff(np.log(closes_a), prepend=np.log(closes_a[0]))
    if n <= lb + 2:
        return np.zeros(n), ret

    if family == "stat_arb":
        if closes_b is None or len(closes_b) != n:
            return np.zeros(n), ret
        ret_b = np.diff(np.log(closes_b), prepend=np.log(closes_b[0]))
        k = min(n, 10000)
        cov = np.cov(ret[-k:], ret_b[-k:])
        var_b = np.var(ret_b[-k:])
        beta = cov[0, 1] / var_b if var_b > 1e-12 else 0.0
        spread = np.log(closes_a) - beta * np.log(closes_b)
        z = zscore(spread, lb)
        sig = -np.clip(z / ez, -1, 1)          # fade spread extremes
        ret = ret - beta * ret_b               # PnL on hedged spread
    else:
        mom = np.concatenate([[0], np.diff(np.log(closes_a))])
        cs = np.concatenate([[0], np.cumsum(mom)])
        lb_ret = (cs[lb:] - cs[:-lb])          # trailing lb-bar return
        z = np.concatenate([np.zeros(lb - 1), zscore(lb_ret, lb)])
        raw = np.clip(np.nan_to_num(z) / ez, -1, 1)
        sig = -raw if family == "mean_reversion" else raw

    if params.get("vol_scale"):
        rv = np.array([ret[max(0, i - int(params["vol_lookback"])):i].std()
                       if i > 10 else np.nan for i in range(n)])
        med = np.nanmedian(rv)
        scale = np.where((rv > 0) & np.isfinite(rv), med / rv, 0.0)
        sig = np.clip(sig * scale, -1, 1)
    return np.nan_to_num(sig), ret


# --- evaluation: honest net-of-cost statistics ------------------------------

def evaluate(sig: np.ndarray, ret: np.ndarray,
             cost_bps: float) -> dict:
    pos = np.roll(sig, 1); pos[0] = 0.0           # signal t -> earns t+1
    turn = np.abs(np.diff(pos, prepend=0.0))
    gross = pos * ret
    net = gross - turn * cost_bps / 1e4
    nb = net.shape[0]
    sharpe = (net.mean() / net.std() * math.sqrt(nb)
              if net.std() > 0 and nb > 10 else 0.0)
    g_sharpe = (gross.mean() / gross.std() * math.sqrt(nb)
                if gross.std() > 0 and nb > 10 else 0.0)
    eq = np.cumsum(net)
    dd = float(np.max(np.maximum.accumulate(eq) - eq)) if nb else 0.0
    return {"n_bars": nb,
            "gross_total_bps": round(float(gross.sum()) * 1e4, 1),
            "net_total_bps": round(float(net.sum()) * 1e4, 1),
            "net_sharpe_period": round(sharpe, 3),
            "gross_sharpe_period": round(g_sharpe, 3),
            "max_drawdown_bps": round(dd * 1e4, 1),
            "turnover": round(float(turn.sum()), 1),
            "hit_rate": round(float((net > 0).mean()), 3)}


def verdict(stats: dict) -> str:
    if stats["net_sharpe_period"] > 1.0 and stats["net_total_bps"] > 0:
        return "PASS"
    if stats["gross_total_bps"] > 0 >= stats["net_total_bps"]:
        return "MARGINAL"
    return "FAIL"


# --- extraction: candidate text -> proposed spec (heuristic, marked) --------

KW = {"stat_arb": r"stat[\s-]?arb|cointegrat|pairs trad|spread",
      "mean_reversion": r"mean[\s-]?revert|reversion|fade|contrarian",
      "momentum": r"momentum|trend|breakout|follow"}


def extract_spec(candidate: dict) -> dict | None:
    text = " ".join(str(candidate.get(k, "")) for k in
                    ("name", "description", "final")) + " " + \
           str((candidate.get("gates") or {}).get("category", ""))
    text = text.lower()
    fam = next((f for f, kw in KW.items() if re.search(kw, text)), None)
    if fam is None:
        fam = "momentum" if "momentum" in text else None
    if fam is None:
        return None
    return {"family": fam, "params": dict(DEFAULTS),
            "hypothesis": f"auto-extracted from {candidate.get('name')}",
            "source": candidate.get("url", ""), "auto_extracted": True}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec")
    ap.add_argument("--from-ledger")
    ap.add_argument("--family", choices=FAMILIES)
    ap.add_argument("--db", default="binance_data.db")
    ap.add_argument("--symbol", default="BTC")
    ap.add_argument("--symbol2", default=None, help="stat_arb second leg")
    ap.add_argument("--tf", default="15m")
    ap.add_argument("--cost-bps", type=float, default=6.5)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    specs: list[dict] = []
    if args.spec:
        specs.append(json.loads(Path(args.spec).read_text()))
    elif args.from_ledger:
        for line in Path(args.from_ledger).read_text().splitlines():
            try:
                cand = json.loads(line)
            except json.JSONDecodeError:
                continue
            s = extract_spec(cand)
            if s:
                s.update(db=args.db, symbol=args.symbol, tf=args.tf,
                         symbol2=args.symbol2)
                specs.append(s)
    elif args.family:
        specs.append({"family": args.family, "params": dict(DEFAULTS),
                      "db": args.db, "symbol": args.symbol, "tf": args.tf,
                      "symbol2": args.symbol2, "hypothesis": "inline"})

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in specs:
        spec.setdefault("db", args.db); spec.setdefault("symbol", args.symbol)
        spec.setdefault("tf", args.tf); spec.setdefault("symbol2", args.symbol2)
        ok, why = validate_spec(spec)
        rec = {"ts": datetime.now(timezone.utc).isoformat(),
               "spec": spec, "cost_bps": args.cost_bps}
        if not ok:
            rec.update(verdict="REJECTED", reason=why)
            print(f"REJECTED  {why}")
        else:
            qf = quarantine_flags(spec["db"], spec["symbol"], spec["tf"])
            qf2 = (quarantine_flags(spec["db"], spec["symbol2"], spec["tf"])
                   if spec.get("symbol2") else None)
            if (qf and qf["quarantined"]) or (qf2 and qf2["quarantined"]):
                flags = (qf or qf2)["flags"]
                rec.update(verdict="REJECTED",
                           reason=f"quarantined: data_quality {flags} — "
                                  f"repair is operator-gated")
                print(f"REJECTED  quarantined {spec['symbol']}@"
                      f"{spec['tf']} flags={flags}")
                rows.append(rec)
                continue
            a = load_closes(spec["db"], spec["symbol"], spec["tf"])
            b = (load_closes(spec["db"], spec["symbol2"], spec["tf"])
                 if spec.get("symbol2") else None)
            if len(a) < 600:
                rec.update(verdict="REJECTED",
                           reason=f"only {len(a)} bars")
                print(f"REJECTED  only {len(a)} bars for "
                      f"{spec['symbol']}@{spec['tf']}")
            else:
                sig, ret = compile_positions(
                    spec["family"], {**DEFAULTS, **spec["params"]}, a, b)
                stats = evaluate(sig, ret, args.cost_bps)
                v = verdict(stats)
                rec.update(verdict=v, stats=stats)
                print(f"{v:9s} {spec['family']:15s} "
                      f"{spec['symbol']}@{spec['tf']} "
                      f"net={stats['net_total_bps']:+8.1f}bps "
                      f"gross={stats['gross_total_bps']:+8.1f}bps "
                      f"sharpe={stats['net_sharpe_period']:+.2f} "
                      f"dd={stats['max_drawdown_bps']:.0f}bps "
                      f"turn={stats['turnover']:.0f}")
        rows.append(rec)

    with out.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"\nledger -> {out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

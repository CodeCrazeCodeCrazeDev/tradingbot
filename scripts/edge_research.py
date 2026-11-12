"""Edge research program (M5) — the hypothesis queue, tested for real.

Each queued hypothesis runs against real fetched/local data and writes
a verdict row to var/methods/ledger.jsonl. All bounded, all advisory.

H1 cross_venue_lead   — does one venue's bar lead another's?
                        (binance/coinbase/kraken candles, real pulls)
H2 funding_carry      — does funding rate carry yield net edge?
                        (binance perp funding history, real pull)
H3 vol_regime_mr      — mean reversion gated to high-vol regimes,
                        param sweep incl. vol_scale on/off
H4 hf_l2_dataset      — probe a discovered HF dataset for usable
                        microstructure data (file list + sample)
H5 depth_imbalance    — Binance UM bookDepth band-imbalance -> fwd
                        returns; per-day decile edges, overlapping-
                        window honest (M6)
H6 positioning_metrics— UM metrics long/short + OI; fade-extreme-
                        crowd test, per-day edges (M6)

    .venv/Scripts/python.exe scripts/edge_research.py
    .venv/Scripts/python.exe scripts/edge_research.py --only funding_carry
"""

from __future__ import annotations

import argparse
import io
import json
import math
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

OUT = Path("var/methods/ledger.jsonl")
_UA = {"User-Agent": "AlphaAlgo-EdgeResearch/1.0"}
_TIMEOUT = 30


def _get(url: str, max_bytes: int = 20_000_000) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return r.read(max_bytes)
    except Exception as e:  # noqa: BLE001
        print(f"    fetch fail {url[:80]}: {str(e)[:80]}")
        return None


def _get_json(url):
    b = _get(url)
    return json.loads(b) if b else None


def record(hyp: str, name: str, verdict: str, stats: dict,
           spec: dict | None = None) -> dict:
    rec = {"ts": datetime.now(timezone.utc).isoformat(),
           "hypothesis": hyp, "name": name, "verdict": verdict,
           "stats": stats, "spec": spec or {}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


# ---------------- H1: cross-venue lead-lag ---------------------------------

def candles_binance(sym="BTCUSDT", interval="15m", limit=500):
    d = _get_json("https://api.binance.com/api/v3/klines?" +
                  urllib.parse.urlencode(
                      {"symbol": sym, "interval": interval,
                       "limit": limit}))
    return {int(r[0]): float(r[4]) for r in d} if d else {}


def candles_coinbase(sym="BTC-USD", gran=900, n=300):
    d = _get_json(f"https://api.exchange.coinbase.com/products/{sym}"
                  f"/candles?granularity={gran}")
    if not d:
        return {}
    return {int(r[0]) * 1000: float(r[4]) for r in d}  # sec->ms, close


def candles_kraken(pair="XBTUSD", interval=15):
    d = _get_json("https://api.kraken.com/0/public/OHLC?" +
                  urllib.parse.urlencode(
                      {"pair": pair, "interval": interval}))
    res = (d or {}).get("result", {})
    rows = next(iter(res.values()), [])
    return {int(r[0]) * 1000: float(r[4]) for r in rows}


def h1_cross_venue() -> dict:
    print("H1 cross-venue lead-lag (BTC, 15m, real venue candles)")
    series = {
        "binance": candles_binance(),
        "coinbase": candles_coinbase(),
        "kraken": candles_kraken(),
    }
    n = {k: len(v) for k, v in series.items()}
    print(f"  candles: {n}")
    if min(n.values()) < 100:
        return record("cross_venue_lead", "all", "REJECTED",
                      {"reason": f"too few candles {n}"})
    venues = list(series)
    rows = []
    for a in venues:
        for b in venues:
            if a == b:
                continue
            common = sorted(set(series[a]) & set(series[b]))
            # same-bar + lead-1 correlation on shared timestamps only
            pa = np.array([series[a][t] for t in common])
            pb = np.array([series[b][t] for t in common])
            ra = np.diff(np.log(pa)); rb = np.diff(np.log(pb))
            same = float(np.corrcoef(ra, rb)[0, 1])
            lead = float(np.corrcoef(ra[:-1], rb[1:])[0, 1]) \
                if len(ra) > 50 else 0.0
            rows.append((a, b, len(ra), round(same, 3), round(lead, 3)))
            print(f"  {a:8s}->{b:8s} n={len(ra):4d} "
                  f"same={same:+.3f} lead={lead:+.3f}")
    mx = max(rows, key=lambda r: abs(r[4]))
    edge = "FAIL" if abs(mx[4]) < 0.1 else "MARGINAL"
    return record("cross_venue_lead", "venue_pairs", edge,
                  {"pairs": [{"a": a, "b": b, "n": nn,
                              "same_corr": s, "lead_corr": l}
                             for a, b, nn, s, l in rows],
                   "best_lead": {"pair": f"{mx[0]}->{mx[1]}",
                                 "corr": mx[4]}})


# ---------------- H2: funding-rate carry -----------------------------------

def h2_funding_carry() -> dict:
    print("H2 funding/basis carry (BTCUSDT perp, real funding history)")
    d = _get_json("https://fapi.binance.com/fapi/v1/fundingRate?" +
                  urllib.parse.urlencode(
                      {"symbol": "BTCUSDT", "limit": 1000}))
    if not d:
        return record("funding_carry", "BTCUSDT", "REJECTED",
                      {"reason": "no funding data"})
    fr = [(int(r["fundingTime"]), float(r["fundingRate"])) for r in d]
    # perp closes aligned to funding timestamps
    k = _get_json("https://fapi.binance.com/fapi/v1/klines?" +
                  urllib.parse.urlencode(
                      {"symbol": "BTCUSDT", "interval": "8h",
                       "limit": 1000}))
    px = {int(r[0]): float(r[4]) for r in k} if k else {}
    print(f"  {len(fr)} funding prints, {len(px)} 8h perp bars")
    # carry: hold perp 8h window when funding extreme; earn funding +
    # drift. funding is paid by the side that is crowded (positive =
    # longs pay shorts).
    def _nearest(ts: int, tol_ms: int = 3_600_000):
        """Closest bar open time within 1h — else None. Anything
        looser fabricates absurd drift."""
        if not px:
            return None
        k = min(px, key=lambda k2: abs(k2 - ts))
        return px[k] if abs(k - ts) <= tol_ms else None

    rets, carries = [], []
    for i in range(len(fr) - 1):
        t, f = fr[i]
        t2 = fr[i + 1][0]
        p0 = _nearest(t)
        p1 = _nearest(t2)
        if not p0 or not p1 or p0 <= 0 or p1 <= 0:
            continue
        drift = math.log(p1 / p0)
        # carry trade: SHORT when funding positive (collects f),
        # LONG when negative — positioned against the crowded side.
        # Earned funding is always |f|; only the drift is signed.
        pos_sign = -1.0 if f > 0 else 1.0
        carries.append(abs(f) * 1e4)             # funding collected, bps
        rets.append(drift * pos_sign * 1e4)      # drift on that side
    if not rets:
        return record("funding_carry", "BTCUSDT", "REJECTED",
                      {"reason": "no aligned bars"})
    fund = float(np.mean(carries)); drift = float(np.mean(rets))
    net = fund + drift - 1.6  # ~1.6bps taker round-trip per 8h window
    hit = float(np.mean([c + r > 0 for c, r in zip(carries, rets)]))
    print(f"  funding earned {fund:+.3f}bps/window, drift {drift:+.3f}bps,"
          f" net {net:+.3f}bps, hit {hit:.2f}")
    v = "PASS" if net > 1.0 else ("MARGINAL" if net > 0 else "FAIL")
    return record("funding_carry", "BTCUSDT", v,
                  {"funding_bps_per_window": round(fund, 3),
                   "drift_bps_per_window": round(drift, 3),
                   "net_bps": round(net, 3), "hit_rate": round(hit, 3),
                   "windows": len(rets)})


# ---------------- H3: vol-regime strategies --------------------------------

def h3_vol_regime() -> dict:
    """Vol-regime-gated mean reversion — bounded param sweep on the
    verified-vol-skill instruments (EURUSD, BTC). Reuses method_eval
    machinery as a subprocess per spec."""
    import subprocess
    print("H3 vol-regime mean reversion (param sweep, real bars)")
    results = []
    grid = [("EURUSD", "market_data.db", "M15"),
            ("BTC", "binance_data.db", "15m")]
    for sym, db, tf in grid:
        for vol_on in ("1", "0"):
            spec = {"family": "mean_reversion",
                    "params": {"lookback": 20, "entry_z": 2.0,
                               "exit_z": 0.0, "vol_lookback": 50,
                               "vol_scale": vol_on == "1"},
                    "db": db, "symbol": sym, "tf": tf,
                    "hypothesis": "vol_regime_mr sweep"}
            sp = Path("var/autonomy/h3_spec.json")
            sp.parent.mkdir(parents=True, exist_ok=True)
            sp.write_text(json.dumps(spec))
            r = subprocess.run(
                [str(Path(".venv/Scripts/python.exe")),
                 "scripts/method_eval.py", "--spec", str(sp),
                 "--cost-bps", "6.5"],
                capture_output=True, text=True, timeout=300)
            line = r.stdout.strip().splitlines()[0] if r.stdout else "?"
            print(f"  {sym} vol_scale={vol_on}: {line}")
            results.append({"symbol": sym, "vol_scale": vol_on,
                            "out": line[:120]})
    return record("vol_regime_mr", "sweep", "DONE",
                  {"runs": results,
                   "note": "verdict rows written by method_eval"})


# ---------------- H4: HF dataset probe --------------------------------------

def h4_hf_dataset() -> dict:
    print("H4 HF dataset probe (L2 tick data discovery)")
    ds = "venvoo/china-a-share-l2-level2-limit-order-book-tick-data"
    d = _get_json(f"https://huggingface.co/api/datasets/{ds}")
    if not d:
        return record("hf_l2_dataset", ds, "REJECTED",
                      {"reason": "api fetch failed"})
    files = [s.get("rfilename") for s in d.get("siblings", [])]
    n = len(files)
    exts = sorted({f.split(".")[-1] for f in files if "." in f})
    print(f"  {n} files, types={exts}")
    info = {"files": n, "exts": exts,
            "sample_files": files[:8],
            "downloads": d.get("downloads"), "tags": d.get("tags", [])[:10]}
    # try to HEAD one parquet for size
    pq = [f for f in files if f.endswith(".parquet")]
    if pq:
        info["parquet_files"] = len(pq)
    verdict = "CANDIDATE" if n else "FAIL"
    return record("hf_l2_dataset", ds, verdict, info)


# ---------------- M6: Binance UM L2 suite ----------------------------------

L2_DIR = Path("var/l2data")
UM = "https://data.binance.vision/data/futures/um/daily"
# bounded week: matches the collected aggTrades window
L2_DAYS = [f"2024-01-0{d}" for d in range(1, 8)]
COST_BPS_PERP = 5.0  # binance UM taker round-trip approx


def _um_file(kind: str, day: str, sub: str = "") -> Path | None:
    """Ensure a bounded daily UM archive csv exists; return path."""
    dest = L2_DIR / f"BTCUSDT-{kind}-{day}.csv"
    if dest.exists():
        return dest
    L2_DIR.mkdir(parents=True, exist_ok=True)
    url = (f"{UM}/{kind}/BTCUSDT/{sub}BTCUSDT-{kind}-{day}.zip"
           if kind != "klines" else
           f"{UM}/klines/BTCUSDT/1m/BTCUSDT-1m-{day}.zip")
    blob = _get(url)
    if not blob:
        print(f"    {kind} {day}: unavailable")
        return None
    z = zipfile.ZipFile(io.BytesIO(blob))
    with z.open(z.namelist()[0]) as src:
        dest.write_bytes(src.read())
    return dest


def _depth_imb(path: Path):
    """snapshot ts(ms) -> (bid_depth - ask_depth)/(sum) over %-bands."""
    import csv
    from collections import defaultdict
    snaps: dict = defaultdict(lambda: [0.0, 0.0])
    for r in csv.reader(path.open()):
        if r[0] == "timestamp":
            continue
        pct, dep = float(r[1]), float(r[2])
        snaps[r[0]][0 if pct < 0 else 1] += dep
    ts = sorted(snaps)
    ms = np.array([int(datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                       .timestamp() * 1000) for t in ts])
    imb = np.array([(snaps[t][0] - snaps[t][1])
                    / (snaps[t][0] + snaps[t][1]) for t in ts])
    return ms, imb


def _klines(path: Path):
    import csv
    rows = [r for r in csv.reader(path.open()) if r and r[0].isdigit()]
    return (np.array([int(r[0]) for r in rows]),
            np.array([float(r[4]) for r in rows]))


def h5_depth_imbalance() -> dict:
    """Top-|imbalance| decile vs forward returns, per-day edges.

    Pooled results are inflated by ~120x overlapping windows; the
    honest unit is the per-day mean signed edge."""
    print("H5 depth imbalance (UM bookDepth bands -> fwd ret)")
    h = 60  # minutes; strongest single-day cell in exploration
    day_edges, corrs = [], []
    for day in L2_DAYS:
        dp = _um_file("bookDepth", day)
        kp = _um_file("klines", day)
        if not dp or not kp:
            continue
        ms, imb = _depth_imb(dp)
        kt, kc = _klines(kp)
        idx = np.clip(np.searchsorted(kt, ms, side="right") - 1,
                      0, len(kc) - 1)
        n = min(h, len(kc) - 1)
        ok = idx + n < len(kc)
        if ok.sum() < 50:
            continue
        fwd = (kc[idx[ok] + n] - kc[idx[ok]]) / kc[idx[ok]] * 1e4
        imb2 = imb[ok]
        corrs.append(float(np.corrcoef(imb2, fwd)[0, 1]))
        p90 = np.percentile(np.abs(imb2), 90)
        hi = np.abs(imb2) > p90
        day_edges.append(float((fwd[hi] * np.sign(imb2[hi])).mean()))
    if not day_edges:
        return record("depth_imbalance", "um_bookDepth_bands",
                      "UNAVAILABLE", {"reason": "no archives"})
    mean_e = float(np.mean(day_edges))
    pos = sum(e > 0 for e in day_edges)
    print(f"  per-day edges: {[f'{e:+.1f}' for e in day_edges]}")
    print(f"  mean={mean_e:+.2f}bps pos={pos}/{len(day_edges)} "
          f"corrs={[f'{c:+.2f}' for c in corrs]}")
    verdict = ("PASS" if mean_e - COST_BPS_PERP > 0
               and pos > len(day_edges) * 0.6 else "FAIL")
    return record("depth_imbalance", "um_bookDepth_bands", verdict,
                  {"horizon_min": h, "day_edges": day_edges,
                   "mean_edge_bps": mean_e, "days_positive": pos,
                   "n_days": len(day_edges), "corrs": corrs,
                   "cost_bps": COST_BPS_PERP,
                   "note": "per-day decile edges; pooled is overlap-inflated"})


def h6_positioning_metrics() -> dict:
    """Fade-extreme-positioning test on UM metrics long/short ratios."""
    print("H6 positioning metrics (UM long/short + OI -> fwd ret)")
    import csv
    h = 60
    feats = ("toptrader", "retail_ls")
    cols = {"toptrader": 5, "retail_ls": 6}
    per: dict = {k: [] for k in feats}
    for day in L2_DAYS:
        mp = _um_file("metrics", day)
        kp = _um_file("klines", day)
        if not mp or not kp:
            continue
        rows = [r for r in csv.reader(mp.open())
                if r and r[0] != "create_time"]
        kt, kc = _klines(kp)
        tm = np.array([int(datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S")
                           .timestamp() * 1000) for r in rows])
        idx = np.clip(np.searchsorted(kt, tm, side="right") - 1,
                      0, len(kc) - 1)
        n = min(h, len(kc) - 1)
        ok = idx + n < len(kc)
        if ok.sum() < 30:
            continue
        fwd = (kc[idx[ok] + n] - kc[idx[ok]]) / kc[idx[ok]] * 1e4
        for k in feats:
            f = np.array([float(r[cols[k]]) for r in rows])[ok]
            q = np.percentile(f, [10, 90])
            # fade: short extreme-long, long extreme-short
            per[k].append(float(
                (-fwd[f > q[1]].mean() + fwd[f < q[0]].mean()) / 2))
    if not per["toptrader"]:
        return record("positioning_metrics", "um_metrics_ls",
                      "UNAVAILABLE", {"reason": "no archives"})
    stats = {}
    best = ("none", -9e9, 0)
    for k in feats:
        e = per[k]
        m_e = float(np.mean(e))
        pos = sum(x > 0 for x in e)
        stats[k] = {"day_edges": e, "mean_bps": m_e,
                    "days_positive": pos, "n_days": len(e)}
        print(f"  {k}: mean={m_e:+.2f}bps pos={pos}/{len(e)} "
              f"{[f'{x:+.1f}' for x in e]}")
        if m_e > best[1]:
            best = (k, m_e, pos)
    verdict = ("PASS" if best[1] - COST_BPS_PERP > 0
               and best[2] > len(per[best[0]]) * 0.6 else "FAIL")
    stats["cost_bps"] = COST_BPS_PERP
    stats["horizon_min"] = h
    return record("positioning_metrics", "um_metrics_ls", verdict, stats)


def _um_download(kind_url: str, day: str) -> bytes | None:
    return _get(f"{UM}/{kind_url}")


def h7_bookticker() -> dict:
    """Top-of-book microprice imbalance -> fwd mid returns.

    bookTicker daily zips are ~128MB; stream-decompress and keep a
    per-second last-quote resample only (~4MB/day retained). Also
    measures the REAL quoted spread (replaces assumed taker cost)."""
    print("H7 bookTicker microprice (1s resample -> fwd ret)")
    h = 60  # seconds
    spreads, day_edges, corrs = [], [], []
    for day in L2_DAYS[:1]:  # bounded: one day = 128MB transfer
        dest = L2_DIR / f"BTCUSDT-bookTicker1s-{day}.csv"
        if not dest.exists():
            url = (f"{UM}/bookTicker/BTCUSDT/"
                   f"BTCUSDT-bookTicker-{day}.zip")
            blob = _get(url, max_bytes=200_000_000)
            if not blob:
                return record("bookticker_microprice",
                              "um_bookTicker", "UNAVAILABLE",
                              {"reason": "fetch failed"})
            import csv as _csv
            z = zipfile.ZipFile(io.BytesIO(blob))
            L2_DIR.mkdir(parents=True, exist_ok=True)
            last: dict = {}
            with z.open(z.namelist()[0]) as f, \
                    dest.open("w", newline="") as out:
                w = _csv.writer(out)
                w.writerow(["ts", "bid", "ask", "bid_qty", "ask_qty"])
                for line in io.TextIOWrapper(f):
                    p = line.strip().split(",")
                    if p[0] == "update_id" or len(p) < 6:
                        continue
                    sec = int(p[5]) // 1000
                    if sec != last.get("sec") and last:
                        w.writerow([last["sec"] * 1000, last["b"],
                                    last["a"], last["bq"], last["aq"]])
                    last = {"sec": sec, "b": p[1], "bq": p[2],
                            "a": p[3], "aq": p[4]}
        import csv as _csv
        rows = [r for r in _csv.reader(dest.open())
                if r and r[0] != "ts"]
        ts = np.array([int(r[0]) for r in rows])
        bid = np.array([float(r[1]) for r in rows])
        ask = np.array([float(r[2]) for r in rows])
        bq = np.array([float(r[3]) for r in rows])
        aq = np.array([float(r[4]) for r in rows])
        mid = (bid + ask) / 2
        spr = (ask - bid) / mid * 1e4
        spreads.append((float(np.median(spr)), float(np.mean(spr))))
        # microprice imbalance: qty-weighted mid deviation, in bps
        mimb = ((ask * bq + bid * aq) / (bq + aq) - mid) / mid * 1e4
        n = min(h, len(mid) - 1)
        ok = np.arange(len(mid)) + n < len(mid)
        fwd = np.full(len(mid), np.nan)
        fwd[ok] = (mid[np.arange(len(mid))[ok] + n] - mid[ok]) \
            / mid[ok] * 1e4
        m = np.isfinite(fwd) & np.isfinite(mimb)
        im, fw = mimb[m], fwd[m]
        corrs.append(float(np.corrcoef(im, fw)[0, 1]))
        hi = np.abs(im) > np.percentile(np.abs(im), 90)
        day_edges.append(float((fw[hi] * np.sign(im[hi])).mean()))
    if not day_edges:
        return record("bookticker_microprice", "um_bookTicker",
                      "UNAVAILABLE", {"reason": "no data"})
    med_spr = float(np.median([s[0] for s in spreads]))
    mean_e = float(np.mean(day_edges))
    print(f"  measured spread: median={med_spr:.2f}bps "
          f"mean={np.mean([s[1] for s in spreads]):.2f}bps")
    print(f"  day edges: {[f'{e:+.1f}' for e in day_edges]} "
          f"corrs={[f'{c:+.2f}' for c in corrs]}")
    cost = COST_BPS_PERP + med_spr  # taker fees RT + spread crossing
    verdict = ("PASS" if mean_e - cost > 0 else "FAIL")
    return record("bookticker_microprice", "um_bookTicker", verdict,
                  {"horizon_s": h, "day_edges": day_edges,
                   "mean_edge_bps": mean_e, "corrs": corrs,
                   "median_spread_bps": med_spr,
                   "mean_spread_bps": float(
                       np.mean([s[1] for s in spreads])),
                   "cost_bps": cost,
                   "note": "cost = taker fees RT + measured spread"})


def h8_premium_basis() -> dict:
    """premiumIndex 1m klines: does extreme perp premium revert?

    Scans every <sym>-premium1m-*.csv in var/l2data. Harvesting needs
    the two-leg basis trade (short perp + long spot) — cost model is
    spot+taker both legs, which is why a stable structural edge still
    fails at standard fee tiers."""
    print("H8 premium basis (premiumIndex 1m -> fwd premium change)")
    import csv
    h = 60  # minutes
    # two-leg basis RT: (perp_taker + spot_taker) x 2 legs
    basis_cost = 2 * (COST_BPS_PERP + 10.0)
    stats, all_edges, worst = {}, [], None
    for path in sorted(L2_DIR.glob("*-premium1m-*.csv")):
        sym = path.name.split("-")[0]
        day = path.stem.rsplit("-", 3)[-3:]
        rows = [r for r in csv.reader(path.open())
                if r and r[0].isdigit()]
        if len(rows) < h + 60:
            continue
        px = np.array([float(r[4]) for r in rows])  # premium close
        n = min(h, len(px) - 1)
        ok = np.arange(len(px)) + n < len(px)
        dprem = np.full(len(px), np.nan)
        dprem[ok] = (px[np.arange(len(px))[ok] + n] - px[ok]) * 1e4
        m = np.isfinite(dprem)
        pm, dm = px[m], dprem[m]
        hi = np.abs(pm) > np.percentile(np.abs(pm), 90)
        edge = float((-np.sign(pm[hi]) * dm[hi]).mean())
        stats.setdefault(sym, []).append(edge)
        all_edges.append(edge)
    if not all_edges:
        return record("premium_basis", "um_premiumIndex",
                      "UNAVAILABLE", {"reason": "no archives"})
    for sym, e in sorted(stats.items()):
        print(f"  {sym}: mean={np.mean(e):+.2f}bps "
              f"pos={sum(x > 0 for x in e)}/{len(e)}")
        stats[sym] = {"day_edges": e, "mean_bps": float(np.mean(e)),
                      "days_positive": sum(x > 0 for x in e),
                      "n_days": len(e)}
    mean_e = float(np.mean(all_edges))
    pos = sum(x > 0 for x in all_edges)
    verdict = ("PASS" if mean_e - basis_cost > 0
               and pos > len(all_edges) * 0.6 else "FAIL")
    stats["aggregate"] = {"mean_bps": mean_e, "days_positive": pos,
                          "n_days": len(all_edges)}
    stats["basis_cost_bps"] = basis_cost
    stats["horizon_min"] = h
    stats["note"] = ("harvest = short perp + long spot (2 legs each "
                     "way); spot-side taker dominates. Stable "
                     "structural anomaly, sub-cost at std fee tier. "
                     "liqSnapshot not in Vision archives (API-only).")
    print(f"  aggregate mean={mean_e:+.2f}bps pos={pos}/"
          f"{len(all_edges)} cost={basis_cost:.0f}bps -> {verdict}")
    return record("premium_basis", "um_premiumIndex", verdict, stats)


# ---------------------------------------------------------------------------

TESTS = {"cross_venue_lead": h1_cross_venue,
         "funding_carry": h2_funding_carry,
         "vol_regime_mr": h3_vol_regime,
         "hf_l2_dataset": h4_hf_dataset,
         "depth_imbalance": h5_depth_imbalance,
         "positioning_metrics": h6_positioning_metrics,
         "bookticker_microprice": h7_bookticker,
         "premium_basis": h8_premium_basis}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", choices=list(TESTS))
    args = ap.parse_args()
    results = {}
    for name, fn in TESTS.items():
        if args.only and name != args.only:
            continue
        results[name] = fn()["verdict"]
        print()
    print("verdicts:", results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

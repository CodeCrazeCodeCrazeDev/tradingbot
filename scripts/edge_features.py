#!/usr/bin/env python
"""Feature-conditioned edge evaluation.

edge_baseline/edge_gate only see closes — they cannot express the
hypotheses that motivated the alt-data collection. This script joins
market_data bars to macro_data.db (FRED/ECB series, COT positioning,
news calendar) and dsc_data.db (measured spreads) and scores each
hypothesis with the same honest machinery: chronological eval window,
net-of-cost returns, circular block-bootstrap 5% LCB, declared
statuses.

Hypotheses evaluated (declared, not tuned):
  1. news_blackout   — re-scores every baseline rule with bars inside
     +-pad minutes of high/medium-impact events for the symbol's
     currencies REMOVED. Reports LCB delta, not just raw LCB: does
     the scheduled-release exclusion add or destroy net bps?
  2. london_sweep    — the documented "first edge": during 11:00-15:00
     UTC a bar sweeps the completed 07:00-11:00 UTC session extreme by
     >= --breach-bps then closes back inside -> fade. Cost = measured
     Dukascopy spread for that bar when available.
  3. cot_fade        — D1 bars; when COT managed-money net%OI is in
     the tails of its own trailing distribution, fade the crowd.
  4. rate_diff_trend — D1 bars; follow the 20-observation change in
     the (us_ust_10y - eu_aaa_10y) differential: EUR strengthens when
     the US-EU gap narrows.

Point-in-time discipline: macro joins use published_at <= bar time
(COT positions usable Friday for the Tuesday snapshot), never as-of
dates. Feature hypotheses need D1 bars — provision with
mt5_data_sync.py --timeframes D1 or dsc_candles.py --timeframes D1.

    python scripts/edge_features.py --symbol EURUSD \
        --m15-db market_data.db --d1-db market_data.db
"""

from __future__ import annotations

import argparse
import bisect
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from scripts.edge_baseline import (  # noqa: E402
    RULES, block_bootstrap_lcb, load_bars, roll_spread_bps)


def _parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _epoch(s: str) -> float:
    return _parse_ts(s).timestamp()


# -----------------------------------------------------------------
# Feature access (point-in-time)

def load_news(db_path: Path, currencies, impacts) -> list[float]:
    """Event epochs for the symbol's currencies at the requested
    impact levels; timed events only (all_day rows can't bracket a
    15m bar)."""
    if not db_path.exists():
        return []
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    ph_c = ",".join("?" * len(currencies))
    ph_i = ",".join("?" * len(impacts))
    try:
        rows = con.execute(
            f"SELECT ts_utc FROM news_events WHERE all_day=0 AND "
            f"currency IN ({ph_c}) AND impact IN ({ph_i})",
            (*currencies, *impacts)).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()
    return sorted(_epoch(r[0]) for r in rows)


def load_series(db_path: Path, name: str) -> list[tuple[float, float]]:
    """[(published_epoch, value)] sorted — the join key is when the
    number was usable, not the observation date."""
    if not db_path.exists():
        return []
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT published_at, value FROM macro_series "
            "WHERE series=? ORDER BY published_at", (name,)).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()
    return sorted((_epoch(r[0]), r[1]) for r in rows)


def load_cot(db_path: Path, symbol: str,
             category="managed_money") -> list[tuple[float, float]]:
    """[(published_epoch, net_pct_oi)]."""
    if not db_path.exists():
        return []
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT published_at, net_pct_oi FROM cot_positions "
            "WHERE symbol=? AND category=? AND net_pct_oi IS NOT NULL "
            "ORDER BY published_at", (symbol, category)).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()
    return sorted((_epoch(r[0]), r[1]) for r in rows)


def _series_asof(points: list[tuple[float, float]]):
    """value-as-of(ts): last point published at or before ts."""
    pubs = [p for p, _ in points]

    def f(ts_epoch: float):
        j = bisect.bisect_right(pubs, ts_epoch) - 1
        return points[j][1] if j >= 0 else None
    return f


def _history_asof(points: list[tuple[float, float]]):
    pubs = [p for p, _ in points]

    def f(ts_epoch: float, k: int):
        j = bisect.bisect_right(pubs, ts_epoch)
        return [v for _, v in points[max(0, j - k):j]]
    return f


# -----------------------------------------------------------------
# Signal functions — signature (ctx, i) -> -1/0/+1 at bar i

def blackout_mask(ts_ep, events_ep, pad_s):
    """bar t is blacked out iff an event epoch lands in
    [t - pad, t + pad]."""
    mask = []
    for t in ts_ep:
        j = bisect.bisect_left(events_ep, t - pad_s)
        mask.append(j < len(events_ep)
                    and events_ep[j] <= t + pad_s)
    return mask


def make_blackout(rule_name: str, mask):  # noqa: D103 - unused helper kept for hypothesis authors
    fn = RULES[rule_name]

    def g(ctx, i):
        if mask[i]:
            return 0
        return fn(ctx["closes"], i)
    return g


def _session_extremes(dts, highs, lows):
    """Per-bar running 07:00-11:00 UTC high/low for that bar's day,
    shifted so a 10:00+ bar sees only completed-session extremes.
    Returns (sess_key, sh_arr, sl_arr) where sh/sl are the session
    extremes visible at each bar."""
    keys = [d.date() for d in dts]
    sh = [None] * len(dts)
    sl = [None] * len(dts)
    cur_key, hi, lo = None, None, None
    for i, d in enumerate(dts):
        hh = d.hour + d.minute / 60.0
        if keys[i] != cur_key:
            cur_key, hi, lo = keys[i], None, None
        sh[i], sl[i] = hi, lo
        if 7.0 <= hh < 11.0:
            hi = highs[i] if hi is None else max(hi, highs[i])
            lo = lows[i] if lo is None else min(lo, lows[i])
    return keys, sh, sl


def london_sweep_rule(ctx, i):
    """Fade a sweep+reclaim of the completed 07:00-11:00 UTC session
    extreme: trigger window 11:00-15:00 UTC, breach >= breach_bps,
    close back inside the range."""
    ts = ctx["dts"][i]
    hh = ts.hour + ts.minute / 60.0
    if not (11.0 <= hh < 15.0):
        return 0
    sh, sl = ctx["sess_hi"][i], ctx["sess_lo"][i]
    if sh is None:
        return 0
    h, l, c = ctx["highs"][i], ctx["lows"][i], ctx["closes"][i]
    if h > sh + ctx["breach"] * sh and c < sh:
        return -1
    if l < sl - ctx["breach"] * sl and c > sl:
        return 1
    return 0


def cot_fade(ctx, i):
    """Crowded-positioning fade: |z| of managed-money net%OI above
    --cot-z over its trailing history -> trade against the crowd."""
    hist = ctx["cot_hist"](ctx["ep"][i], ctx["cot_lookback"])
    if len(hist) < ctx["cot_lookback"] * 2 // 3:
        return 0
    z = (hist[-1] - float(np.mean(hist))) / (float(np.std(hist)) or 1)
    if abs(z) < ctx["cot_z"]:
        return 0
    return -1 if z > 0 else 1


def rate_diff_trend(ctx, i):
    """Follow the differential trend: EURUSD long when the US-EU 10y
    spread narrows over --rate-look observations (carry narrowing)."""
    hist = ctx["rate_hist"](ctx["ep"][i], ctx["rate_look"] + 1)
    if len(hist) < ctx["rate_look"] + 1:
        return 0
    mom = hist[-1] - hist[0]
    if abs(mom) < ctx["rate_min_move"]:
        return 0
    return -1 if mom > 0 else 1


# -----------------------------------------------------------------

def evaluate_ctx(ctx, sig_fn, eval_start, eval_end, horizon, cost_fn):
    closes = ctx["closes"]
    nets = []
    for i in range(max(eval_start, 1),
                   min(eval_end, len(closes) - horizon)):
        s = sig_fn(ctx, i)
        if s == 0:
            continue
        fwd = (closes[i + horizon] - closes[i]) / closes[i] * 1e4
        nets.append(s * fwd - cost_fn(i))
    return np.asarray(nets)


def collect_signals(fn, closes, eval_start, eval_end, horizon):
    """Rule signals once: [(bar_idx, direction)]. Single pass so the
    blackout A/B evaluates on the IDENTICAL signal set — the only
    thing that changes is which signals are taken."""
    sigs = []
    for i in range(max(eval_start, 1),
                   min(eval_end, len(closes) - horizon)):
        s = fn(closes, i)
        if s:
            sigs.append((i, s))
    return sigs


def score_signals(sigs, mask, closes, horizon, cost_fn):
    """net bps for the unmasked subset of pre-computed signals."""
    nets = [s * (closes[i + horizon] - closes[i]) / closes[i] * 1e4
            - cost_fn(i)
            for i, s in sigs if not mask[i]]
    return np.asarray(nets)


def verdict(nets, min_trades, margin):
    trades = len(nets)
    if trades < min_trades:
        return {"status": "insufficient_evidence", "trades": trades,
                "mean_net_bps": None, "lcb5_net_bps": None}
    mean_b, lcb = block_bootstrap_lcb(nets)
    return {"status": ("candidate_edge" if lcb > margin
                       else "no_edge"),
            "trades": trades, "mean_net_bps": round(mean_b, 3),
            "lcb5_net_bps": round(lcb, 3),
            "win_rate": round(float(np.mean(nets > 0)), 3)}


def _on_grid(ts_list, tf_minutes):
    """Keep only bars that open exactly on the timeframe grid.
    market_data.db EURUSD M15 carries ~1,000 spliced rows with
    fractional-second/off-grid timestamps producing fake +-6.7%
    returns (see AGENTS.md); evaluating on them is contamination."""
    keep = []
    for i, t in enumerate(ts_list):
        try:
            d = _parse_ts(t)
        except ValueError:
            continue
        if (d.minute % tf_minutes == 0 and d.second == 0
                and d.microsecond == 0):
            keep.append(i)
    return keep


def _aggregate_d1(ts_list, bars):
    """H1/H4 bars -> D1 candles (real OHLCV roll-up, UTC day)."""
    groups = {}
    for t, b in zip(ts_list, bars):
        groups.setdefault(_parse_ts(t).date(), []).append(b)
    ts_out, rows = [], []
    for d in sorted(groups):
        g = groups[d]
        ts_out.append(f"{d.isoformat()}T00:00:00+00:00")
        rows.append([g[0][0], max(x[1] for x in g),
                     min(x[2] for x in g), g[-1][3],
                     sum(x[4] or 0 for x in g)])
    return ts_out, np.asarray(rows, dtype=float)


def _tf_minutes(tf: str) -> int:
    return {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60,
            "H4": 240, "D1": 1440}.get(tf, 15)


def _symbol_currencies(sym: str):
    if len(sym) == 6:
        return [sym[:3], sym[3:]]
    return [sym]


def _measured_cost(dsc_db: Path, symbol: str, timeframe: str):
    """bar-index -> cost in bps using the candle's own measured mean
    spread; falls back to None (caller uses flat cost)."""
    if not dsc_db.exists():
        return {}
    con = sqlite3.connect(f"file:{dsc_db}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT timestamp, mean_spread_bps FROM dsc_spread "
            "WHERE symbol=? AND timeframe=?",
            (symbol, timeframe)).fetchall()
    except sqlite3.OperationalError:
        return {}
    finally:
        con.close()
    return {r[0]: r[1] for r in rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--m15-db", default="market_data.db")
    ap.add_argument("--m15-timeframe", default="M15")
    ap.add_argument("--d1-db", default="market_data.db")
    ap.add_argument("--d1-timeframe", default="D1")
    ap.add_argument("--macro-db", default="macro_data.db")
    ap.add_argument("--dsc-db", default="dsc_data.db")
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--eval-frac", type=float, default=0.40)
    ap.add_argument("--embargo", type=int, default=20)
    ap.add_argument("--cost-bps", type=float, default=None)
    ap.add_argument("--pad-min", type=int, default=30)
    ap.add_argument("--impacts", default="High,Medium")
    ap.add_argument("--blackout-rules", default="",
                    help="comma list; default = all baseline rules. "
                         "On 60k+ M15 bars the two O(window) rules "
                         "(vol_squeeze, lowvol_trend) take minutes "
                         "each — restrict to speed iteration")
    ap.add_argument("--breach-bps", type=float, default=2.0,
                    help="sweep breach beyond session extreme")
    ap.add_argument("--cot-z", type=float, default=2.0)
    ap.add_argument("--cot-lookback", type=int, default=104)
    ap.add_argument("--rate-look", type=int, default=20)
    ap.add_argument("--rate-min-move", type=float, default=0.05)
    ap.add_argument("--min-trades", type=int, default=30)
    ap.add_argument("--required-margin-bps", type=float, default=2.0)
    ap.add_argument("--out", default="var/edge_features.json")
    args = ap.parse_args()

    macro_db, dsc_db = ROOT / args.macro_db, ROOT / args.dsc_db
    report = {"generated_at": time.time(), "symbol": args.symbol,
              "hypotheses": {}, "warnings": []}

    # ---------- M15 channel: blackout + london sweep ----------
    ts15, bars15 = load_bars(ROOT / args.m15_db, args.symbol,
                             args.m15_timeframe)
    keep = _on_grid(ts15, _tf_minutes(args.m15_timeframe))
    dropped = len(ts15) - len(keep)
    if dropped:
        ts15 = [ts15[i] for i in keep]
        bars15 = bars15[keep]
        report["warnings"].append(
            f"dropped {dropped} off-grid {args.m15_timeframe} bars "
            "(spliced/contaminated rows)")
    n = len(bars15)
    rep15 = {"offgrid_dropped": dropped}
    if n:
        closes = bars15[:, 3]
        dts = [_parse_ts(t) for t in ts15]
        ep = [d.timestamp() for d in dts]
        disc_end = int(n * (1.0 - args.eval_frac))
        eval_start, eval_end = disc_end + args.embargo, n
        roll = roll_spread_bps(closes)
        flat_cost = args.cost_bps if args.cost_bps is not None \
            else max(roll or 0.0, 5.0)
        meas = _measured_cost(dsc_db, args.symbol, args.m15_timeframe)

        def cost_fn(i):
            if ts15[i] in meas and meas[ts15[i]] is not None:
                return max(meas[ts15[i]], flat_cost * 0.5)
            return flat_cost

        ctx = {"closes": closes, "highs": bars15[:, 1],
               "lows": bars15[:, 2], "dts": dts, "ep": ep,
               "breach": args.breach_bps / 1e4}
        keys, shi, slo = _session_extremes(dts, ctx["highs"],
                                         ctx["lows"])
        ctx["sess_key"], ctx["sess_hi"], ctx["sess_lo"] = keys, shi, slo

        # 1) news blackout delta on every baseline rule
        ev = load_news(macro_db, _symbol_currencies(args.symbol),
                       [i.strip() for i in args.impacts.split(",")])
        pad = args.pad_min * 60
        if ev:
            mask = blackout_mask(ep, ev, pad)
            rep15["news_events"] = len(ev)
            rep15["blackout_bars_removed"] = int(sum(
                mask[eval_start:eval_end]))
            rep15["blackout"] = {}
            no_mask = [False] * n
            rule_names = ([r.strip() for r in
                           args.blackout_rules.split(",") if r.strip()]
                          or list(RULES))
            for name in rule_names:
                if name not in RULES:
                    continue
                t0 = time.time()
                sigs = collect_signals(
                    RULES[name], closes, eval_start, eval_end,
                    args.horizon)
                raw = verdict(score_signals(
                    sigs, no_mask, closes, args.horizon,
                    lambda i: flat_cost), args.min_trades,
                    args.required_margin_bps)
                blk = verdict(score_signals(
                    sigs, mask, closes, args.horizon,
                    lambda i: flat_cost), args.min_trades,
                    args.required_margin_bps)
                rep15["blackout"][name] = {
                    "all": raw, "blackout": blk,
                    "lcb_delta": (round(blk["lcb5_net_bps"]
                                        - raw["lcb5_net_bps"], 3)
                                  if blk["lcb5_net_bps"] is not None
                                  and raw["lcb5_net_bps"] is not None
                                  else None)}
                print(f"  blackout[{name}] "
                      f"{time.time()-t0:.0f}s", flush=True)
        else:
            rep15["news_events"] = 0
            report["warnings"].append(
                "no timed news events — run collect_macro.py "
                "--sources calendar before judging the blackout rule")

        # 2) london sweep with measured-spread cost
        rep15["london_sweep"] = verdict(
            evaluate_ctx(ctx, london_sweep_rule, eval_start, eval_end,
                         args.horizon, cost_fn),
            args.min_trades, args.required_margin_bps)
        rep15["london_sweep"]["cost_note"] = (
            "measured dsc spread where available, else flat "
            f"{flat_cost:.1f}bps" if meas else
            f"flat {flat_cost:.1f}bps (dsc_spread not provisioned)")
        rep15["eval_window"] = [ts15[eval_start], ts15[-1]]
        rep15["bars"] = n
    else:
        report["warnings"].append(
            f"no {args.m15_timeframe} {args.symbol} bars in "
            f"{args.m15_db}")

    # ---------- D1 channel: cot_fade + rate_diff_trend ----------
    ts1, bars1 = load_bars(ROOT / args.d1_db, args.symbol,
                           args.d1_timeframe)
    rep1 = {}
    d1_src = args.d1_timeframe
    if not len(bars1):
        # derive D1 from the deepest intraday series available —
        # real OHLCV roll-up, provenance recorded
        for tf in ("H4", "H1", "M30"):
            tsa, ba = load_bars(ROOT / args.d1_db, args.symbol, tf)
            if len(ba) >= 200:
                ts1, bars1 = _aggregate_d1(tsa, ba)
                d1_src = f"{tf}_rollup"
                break
    rep1["d1_source"] = d1_src
    if len(bars1):
        closes = bars1[:, 3]
        n1 = len(closes)
        ep1 = [_epoch(t) for t in ts1]
        disc_end = int(n1 * (1.0 - args.eval_frac))
        ev_start, ev_end = disc_end + args.embargo, n1
        cost1 = args.cost_bps if args.cost_bps is not None else max(
            roll_spread_bps(closes) or 0.0, 5.0)
        ctx1 = {"closes": closes, "ep": ep1,
                "cot_z": args.cot_z, "cot_lookback": args.cot_lookback,
                "rate_look": args.rate_look,
                "rate_min_move": args.rate_min_move}
        ctx1["cot_hist"] = _history_asof(
            load_cot(macro_db, args.symbol))
        us = {d: v for d, v in load_series(macro_db, "us_ust_10y")}
        eu = {d: v for d, v in load_series(macro_db, "eu_aaa_10y")}
        shared = sorted(set(us) & set(eu))
        ctx1["rate_hist"] = _history_asof(
            [(d, us[d] - eu[d]) for d in shared])
        if not ctx1["rate_hist"](ep1[-1], 1):
            report["warnings"].append(
                "no us_ust_10y/eu_aaa_10y overlap — run "
                "collect_macro.py --sources fred,ecb")
        rep1["cot_fade"] = verdict(
            evaluate_ctx(ctx1, cot_fade, ev_start, ev_end,
                         args.horizon, lambda i: cost1),
            args.min_trades, args.required_margin_bps)
        rep1["rate_diff_trend"] = verdict(
            evaluate_ctx(ctx1, rate_diff_trend, ev_start, ev_end,
                         args.horizon, lambda i: cost1),
            args.min_trades, args.required_margin_bps)
        rep1["eval_window"] = [ts1[ev_start], ts1[-1]]
        rep1["bars"] = n1
    else:
        report["warnings"].append(
            f"no {args.d1_timeframe} {args.symbol} bars — provision "
            "via mt5_data_sync.py --timeframes D1 or "
            "dsc_candles.py --timeframes D1")

    report["m15"] = rep15
    report["d1"] = rep1
    rp = ROOT / args.out
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items()
                      if k in ("warnings",)}, indent=2))
    print(f"report: {rp}")
    if rep15.get("london_sweep"):
        print("london_sweep:", rep15["london_sweep"])
    if rep1.get("cot_fade"):
        print("cot_fade:", rep1["cot_fade"])
        print("rate_diff_trend:", rep1["rate_diff_trend"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

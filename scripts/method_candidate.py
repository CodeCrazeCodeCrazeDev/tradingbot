#!/usr/bin/env python
"""Method -> candidate -> verdict runner (M1 loop, script surface).

Takes a MethodSpec (JSON file, or --family/--param flags), compiles it
through the allow-listed bounded families in
trading_bot/core/csc/research/method_spec.py, evaluates it on real
bars with the edge-gate protocol (chronological split, per-segment
block-bootstrap LCB, all-segments-must-clear), and writes a verdict
artifact. With --csc-eval it additionally pushes the
(candidate_positions, baseline_positions, bar_returns) triple through
ResearchEngine.evaluate_strategy so the verdict lands as a KG claim.

The candidate is advisory evidence only — promotion stays behind the
signed RSI evaluator / OperatorAuthorization.

Usage:
    python scripts/method_candidate.py \
        --spec examples/method_spec_momentum.json \
        --db market_data.db --symbol EURUSD --timeframe M15 \
        --horizon 4 --segments 3 --out var/method_candidates/

    python scripts/method_candidate.py \
        --family momentum --param lookback=10 --param threshold_bps=15 \
        --db fx_data.db --symbol USDJPY --timeframe D1 --csc-eval
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from scripts.edge_baseline import (  # noqa: E402
    block_bootstrap_lcb, evaluate, load_bars, roll_spread_bps)
from trading_bot.core.csc.research.method_spec import (  # noqa: E402
    PAIR_FAMILIES, MethodSpec, SpecError, align_pair, compile_rule,
    pair_pnl_bps, pair_triple, positions_triple, spec_from_dict)


def segmented_verdict(closes, rule_fn, horizon, n_segments,
                      eval_frac, embargo, cost_bps, margin_bps):
    """edge_gate semantics: eval tail split into n_segments contiguous
    blocks; candidate only if EVERY evaluated segment clears LCB."""
    n = len(closes)
    disc_end = int(n * (1.0 - eval_frac))
    eval_start = disc_end + embargo
    eval_end = n
    seg_len = max(1, (eval_end - eval_start) // n_segments)
    segs = []
    for k in range(n_segments):
        a = eval_start + k * seg_len
        b = eval_start + (k + 1) * seg_len if k < n_segments - 1 \
            else eval_end
        _, net = evaluate(closes, rule_fn, horizon, a, b, cost_bps)
        trades = len(net)
        if trades < 30:
            segs.append({"segment": k, "status": "insufficient_evidence",
                         "trades": trades})
            continue
        mean_b, lcb = block_bootstrap_lcb(net)
        segs.append({"segment": k, "status": "evaluated",
                     "trades": trades,
                     "mean_net_bps": round(mean_b, 3),
                     "lcb5_net_bps": round(lcb, 3)})
    evaluated = [s for s in segs if s["status"] == "evaluated"]
    passes = (len(evaluated) == len(segs)
              and all(s["lcb5_net_bps"] > margin_bps for s in evaluated))
    all_net = []
    _, net_all = evaluate(closes, rule_fn, horizon,
                          eval_start, eval_end, cost_bps)
    if len(net_all) >= 30:
        m, l = block_bootstrap_lcb(net_all)
        overall = {"trades": len(net_all), "mean_net_bps": round(m, 3),
                   "lcb5_net_bps": round(l, 3)}
    else:
        overall = {"trades": len(net_all), "status": "insufficient_evidence"}
    return {"eval_window": [eval_start, eval_end],
            "segments": segs,
            "overall": overall,
            "verdict": "candidate" if passes else "rejected"}


def verdict_from_pnl(pnl, n_segments, eval_frac, embargo,
                     margin_bps, label=""):
    """Segmented all-LCB verdict on a precomputed per-bar net-bps
    series (used by PAIR families where the instrument is a synthetic
    spread, not a single close series)."""
    import numpy as _np
    pnl = _np.asarray(pnl, dtype=float)
    n = len(pnl)
    disc_end = int(n * (1.0 - eval_frac))
    eval_start = disc_end + embargo
    eval_end = n
    seg_len = max(1, (eval_end - eval_start) // n_segments)
    segs = []
    for k in range(n_segments):
        a = eval_start + k * seg_len
        b = eval_start + (k + 1) * seg_len if k < n_segments - 1 \
            else eval_end
        seg = pnl[a:b]
        if len(seg) < 30:
            segs.append({"segment": k, "status": "insufficient_evidence",
                         "trades": int(len(seg))})
            continue
        mean_b, lcb = block_bootstrap_lcb(seg)
        segs.append({"segment": k, "status": "evaluated",
                     "trades": int(len(seg)),
                     "mean_net_bps": round(mean_b, 3),
                     "lcb5_net_bps": round(lcb, 3)})
    evaluated = [s for s in segs if s["status"] == "evaluated"]
    passes = (len(evaluated) == len(segs)
              and all(s["lcb5_net_bps"] > margin_bps for s in evaluated))
    ev = pnl[eval_start:eval_end]
    if len(ev) >= 30:
        m, l = block_bootstrap_lcb(ev)
        overall = {"trades": int(len(ev)), "mean_net_bps": round(m, 3),
                   "lcb5_net_bps": round(l, 3)}
    else:
        overall = {"trades": int(len(ev)),
                   "status": "insufficient_evidence"}
    return {"label": label, "eval_window": [eval_start, eval_end],
            "segments": segs, "overall": overall,
            "verdict": "candidate" if passes else "rejected"}


def funding_eval(spec, rule_fn, db, symbol, timeframe, cost_bps,
                 segments=3, eval_frac=0.40, embargo=2, margin_bps=0.0):
    """required_data='funding' path: funding prints (funding_data.db)
    joined to the dataset's closes. rule_fn(rate_bps) -> position
    (-1/0/+1); per-window net = funding income + signed drift - cost.
    Returns the segmented all-LCB verdict PLUS the honest
    mechanism decomposition — unhedged funding-signed directional,
    not delta-neutral carry."""
    import math as _math

    from scripts.funding_carry_eval import (  # noqa: E402
        FUNDING_DB, load_closes, load_funding, nearest_close)

    name = Path(db).name
    src = ("binance" if name.startswith("binance") else
           "hyperliquid" if name.startswith("hl") else None)
    if src is None:
        return {"status": "no_funding_source",
                "dataset": str(db)}
    # funding_data.db stores venue-native symbols (binance BTCUSDT,
    # hyperliquid BTC); market_data stores bare symbols (BTC)
    fsym = (symbol if symbol.endswith("USDT") else symbol + "USDT") \
        if src == "binance" else symbol
    fr = load_funding(FUNDING_DB, src, fsym)
    if len(fr) < 11:
        return {"status": "insufficient_funding_prints",
                "prints": len(fr), "source": src, "symbol": fsym}
    dbpath = Path(db) if Path(db).is_absolute() else ROOT / db
    series = load_closes(dbpath, symbol, timeframe)
    if len(series) < 50 and symbol.endswith("USDT"):
        series = load_closes(dbpath, symbol[:-4], timeframe)
    if len(series) < 50:
        return {"status": "insufficient_closes",
                "closes": len(series)}
    cadence = int(np.median(np.diff([t for t, _ in fr])))
    tol_ms = max(cadence // 2, 15 * 60 * 1000)

    drifts, carries, nets = [], [], []
    skipped = 0
    for i in range(len(fr) - 1):
        t0, f = fr[i]
        pos = float(rule_fn(float(f) * 1e4))
        if pos == 0.0:
            continue  # flat — not a trade, no cost
        t1 = fr[i + 1][0]
        p0 = nearest_close(series, t0, tol_ms)
        p1 = nearest_close(series, t1, tol_ms)
        if not p0 or not p1:
            skipped += 1
            continue
        signed = _math.log(p1 / p0) * pos * 1e4
        carry = abs(float(f)) * 1e4
        drifts.append(signed)
        carries.append(carry)
        nets.append(carry + signed - cost_bps)
    if len(nets) < 10:
        return {"status": "insufficient_windows",
                "windows": len(nets), "skipped": skipped}

    v = verdict_from_pnl(np.asarray(nets), segments, eval_frac,
                         embargo, margin_bps,
                         label=f"{fsym}:{src}")
    v.update({
        "mechanism": "unhedged funding-signed directional — "
                     "NOT delta-neutral carry",
        "windows": len(nets), "skipped_no_close": skipped,
        "funding_prints": len(fr), "cadence_ms": cadence,
        "funding_bps_per_window": round(float(np.mean(carries)), 3),
        "drift_bps_per_window": round(float(np.mean(drifts)), 3),
        "net_bps_per_window": round(float(np.mean(nets)), 3)})
    return v


def pair_eval(spec, rule2, pair_ref, db, symbol, timeframe,
              horizon, cost_bps, segments, eval_frac, embargo,
              margin_bps):
    """Load leg A (primary dataset) + leg B (spec.pair or --pair),
    align on timestamps, run the segmented gate on spread PnL."""
    a_ts, a_bars = load_bars(db, symbol, timeframe)
    b_ts, b_bars = load_bars(pair_ref["db"], pair_ref["symbol"],
                             pair_ref["timeframe"])
    a_closes, b_closes = a_bars[:, 3], b_bars[:, 3]
    a_al, b_al = align_pair(a_ts, a_closes, b_ts, b_closes)
    if len(a_al) < 200:
        return {"status": "insufficient_aligned_bars",
                "aligned": len(a_al)}
    hedge = float(spec.params.get("hedge", 1.0))
    pnl = pair_pnl_bps(rule2, a_al, b_al, hedge, cost_bps)
    v = verdict_from_pnl(pnl, segments, eval_frac, embargo, margin_bps,
                         label=f"{symbol}~{pair_ref['symbol']}")
    v["aligned_bars"] = len(a_al)
    v["hedge"] = hedge
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", help="JSON MethodSpec file")
    ap.add_argument("--family")
    ap.add_argument("--param", action="append", default=[],
                    help="key=value, repeatable")
    ap.add_argument("--spec-id", default=None)
    ap.add_argument("--hypothesis", default="")
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--pair", default=None,
                    help="db:symbol:timeframe hedge leg for PAIR "
                         "families (stat_arb); overrides nothing if "
                         "the spec already declares spec.pair")
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--segments", type=int, default=3)
    ap.add_argument("--eval-frac", type=float, default=0.40)
    ap.add_argument("--embargo", type=int, default=20)
    ap.add_argument("--cost-bps", type=float, default=None,
                    help="default max(Roll estimate, 5bps)")
    ap.add_argument("--margin-bps", type=float, default=0.0,
                    help="LCB must exceed this to be a candidate")
    ap.add_argument("--csc-eval", action="store_true",
                    help="also run ResearchEngine.evaluate_strategy on "
                         "the positions/baseline/returns triple")
    ap.add_argument("--out", default="var/method_candidates")
    args = ap.parse_args()

    if args.spec:
        spec = spec_from_dict(json.loads(Path(args.spec).read_text()))
    else:
        if not args.family:
            ap.error("provide --spec or --family")
        params = {}
        for kv in args.param:
            k, _, v = kv.partition("=")
            try:
                params[k.strip()] = float(v)
            except ValueError:
                ap.error(f"--param {kv!r} not numeric")
        spec = MethodSpec(
            spec_id=args.spec_id or f"cli_{args.family}",
            hypothesis=args.hypothesis or
            f"CLI-declared {args.family} candidate",
            family=args.family, params=params,
            provenance={"origin": "method_candidate.py"})

    if spec.pair is None and args.pair:
        try:
            pdb, psym, ptf = args.pair.split(":")
            spec.pair = {"db": pdb, "symbol": psym, "timeframe": ptf}
        except ValueError:
            ap.error("--pair must be db:symbol:timeframe")

    try:
        rule_fn = compile_rule(spec)
    except SpecError as e:
        print(f"SPEC REJECTED: {e}", file=sys.stderr)
        return 2

    pair_ref = spec.pair
    hedge = float(spec.params.get("hedge", 1.0))

    ts, bars = load_bars(args.db, args.symbol, args.timeframe)
    closes = bars[:, 3]
    if len(closes) < 200:
        print(f"insufficient bars: {len(closes)}", file=sys.stderr)
        return 2
    cost_bps = args.cost_bps
    if cost_bps is None:
        cost_bps = max(roll_spread_bps(closes) or 0.0, 5.0)

    pair_arrays = None
    if spec.family in PAIR_FAMILIES:
        verdict = pair_eval(spec, rule_fn, pair_ref, args.db,
                            args.symbol, args.timeframe, args.horizon,
                            cost_bps, args.segments, args.eval_frac,
                            args.embargo, args.margin_bps)
        # stash aligned arrays for the optional CSC triple
        try:
            a_ts, a_b = load_bars(args.db, args.symbol, args.timeframe)
            b_ts, b_b = load_bars(pair_ref["db"], pair_ref["symbol"],
                                  pair_ref["timeframe"])
            pair_arrays = align_pair(a_ts, a_b[:, 3], b_ts, b_b[:, 3])
        except Exception:
            pair_arrays = None
    else:
        verdict = segmented_verdict(
            closes, rule_fn, args.horizon, args.segments,
            args.eval_frac, args.embargo, cost_bps, args.margin_bps)

    report = {
        "spec": {"spec_id": spec.spec_id, "spec_hash": spec.spec_hash,
                 "hypothesis": spec.hypothesis, "family": spec.family,
                 "params": spec.params, "provenance": spec.provenance,
                 "falsification": spec.falsification},
        "dataset": {"db": args.db, "symbol": args.symbol,
                    "timeframe": args.timeframe, "bars": len(closes),
                    "first_ts": ts[0], "last_ts": ts[-1]},
        "gate": {"horizon": args.horizon, "cost_bps": cost_bps,
                 "segments": args.segments, "margin_bps": args.margin_bps,
                 "eval_frac": args.eval_frac, "embargo": args.embargo},
        "verdict": verdict,
        "promotion_eligible": False,
        "note": "advisory evidence only — promotion requires the signed "
                "RSI evaluator / OperatorAuthorization",
    }

    if args.csc_eval:
        try:
            if spec.family in PAIR_FAMILIES:
                if pair_arrays is None:
                    raise SpecError("pair alignment unavailable")
                pos, base, rets = pair_triple(
                    rule_fn, pair_arrays[0], pair_arrays[1], hedge)
            else:
                pos, base, rets = positions_triple(rule_fn, closes)
            from trading_bot.core.csc.research.engine import (
                ResearchEngine)
            engine = ResearchEngine(hypothesis_gen=None,
                                    verifier_swarm=None)
            rr = engine.evaluate_strategy(
                question=f"{spec.spec_id}: {spec.hypothesis}",
                candidate_positions=pos, baseline_positions=base,
                bar_returns=rets, cost_bps=cost_bps,
                dataset_id=f"{args.db}:{args.symbol}:{args.timeframe}",
                origin="method_candidate.py")
            report["csc_eval"] = {
                "verdict": rr.verdict,
                "comparison": rr.comparison,
                "reward": getattr(rr, "reward", None),
                "research_id": rr.research_id,
            }
        except Exception as e:  # honest failure, not silent skip
            report["csc_eval"] = {"error": f"{type(e).__name__}: {e}"}

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    fname = f"{spec.spec_id}_{spec.spec_hash}.json"
    out = outdir / fname
    out.write_text(json.dumps(report, indent=2, default=str))
    v = verdict["verdict"]
    ov = verdict.get("overall", {})
    print(f"{spec.spec_id} [{spec.family} {spec.params}] "
          f"-> {v}  mean={ov.get('mean_net_bps')}bps "
          f"lcb5={ov.get('lcb5_net_bps')}bps trades={ov.get('trades')}")
    for s in verdict["segments"]:
        print(f"   seg{s['segment']}: {s['status']} "
              f"mean={s.get('mean_net_bps')} lcb={s.get('lcb5_net_bps')} "
              f"trades={s.get('trades')}")
    if "csc_eval" in report:
        ce = report["csc_eval"]
        print(f"   csc_eval: {ce.get('verdict', ce.get('error'))}")
    print(f"report: {out}")
    return 0 if v == "candidate" else 1


if __name__ == "__main__":
    sys.exit(main())

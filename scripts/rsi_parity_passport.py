"""Produce an Algory-style A–F venue-parity passport for an RSI candidate.

Compares the *simulated* per-bar net path (the exact PairedFamilyReplay
path the signed verifier uses) against an independent *venue* replay —
MT5 Strategy Tester output, paper-runner fills, or any fill model that
can emit per-bar net rows.

Venue input contract (JSONL, one object per line)::

    {"symbol": "EURUSD", "timestamp": 123.0, "net": 0.0004}

The sim side is rebuilt from the same frames/params the contract was
issued against, so the passport answers "does the venue reproduce the
simulation?" — per market, worst symbol governs.

    python scripts/rsi_parity_passport.py \
        --family mean_reversion --params '{"lookback":50,"entry_threshold":1.0}' \
        --seed 7 --bars 160 --venue-rows venue.jsonl --out parity.json

NOTE: feeding real MT5 output requires extracting per-bar venue equity
from the demo runner's fill records (decision_log/trading_state) — that
plumbing needs the Hermes env and provisioned demo credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from trading_bot.evaluation.synthetic_market import (  # noqa: E402
    RegimeSpec, SqliteSource, SyntheticMarketGenerator, SyntheticMarketSpec)
from trading_bot.evaluation.runner import PairedFamilyReplay  # noqa: E402
from trading_bot.recursive_self_improvement.candidate_adapters import (  # noqa: E402
    ADAPTERS)
from trading_bot.recursive_self_improvement.venue_parity import (  # noqa: E402
    parity_from_bar_rows)


def _frames(args) -> Dict[str, Any]:
    if args.db:
        return SqliteSource(args.db, args.instruments).load()
    spec = SyntheticMarketSpec(
        seed=args.seed, instruments=tuple(args.instruments),
        regimes=(RegimeSpec("mean_revert", args.bars, vol=0.0002,
                            sine_amp=0.01, sine_period=8),))
    return SyntheticMarketGenerator(spec).generate()


def _sim_rows(frames, adapter, baseline, candidate, cost_bps, fraction):
    out = PairedFamilyReplay(adapter, cost_bps=cost_bps,
                             fraction=fraction).run(
        dict(frames), baseline_params=dict(baseline),
        candidate_params=dict(candidate))
    return [{"symbol": r["symbol"], "timestamp": r["timestamp"],
             "net": r["candidate_net"]} for r in out["bars"]]


def _load_venue_rows(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        for k in ("symbol", "timestamp", "net"):
            if k not in rec:
                raise ValueError(f"{path}:{i+1} missing key {k!r}")
        rows.append(rec)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", default="mean_reversion",
                    choices=sorted(ADAPTERS))
    ap.add_argument("--params", required=True,
                    help="candidate params JSON, e.g. '{\"lookback\":50}'")
    ap.add_argument("--baseline", default=None,
                    help="incumbent params JSON (default: params minus the "
                         "first changed key is NOT inferred — pass explicitly)")
    ap.add_argument("--venue-rows", required=True,
                    help="JSONL of {symbol, timestamp, net} venue bars")
    ap.add_argument("--db", default=None)
    ap.add_argument("--instruments", nargs="+", default=["EURUSD", "GBPUSD"])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--bars", type=int, default=160)
    ap.add_argument("--cost-bps", type=float, default=5.0)
    ap.add_argument("--fraction", type=float, default=0.01)
    ap.add_argument("--rel-tol", type=float, default=0.5)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    candidate = json.loads(args.params)
    baseline = json.loads(args.baseline) if args.baseline else dict(candidate)
    frames = _frames(args)
    sim = _sim_rows(frames, ADAPTERS[args.family], baseline, candidate,
                    args.cost_bps, args.fraction)
    venue = _load_venue_rows(Path(args.venue_rows))
    passport = parity_from_bar_rows(sim, venue, rel_tol=args.rel_tol)
    passport["family"] = args.family
    passport["candidate_parameters"] = candidate
    text = json.dumps(passport, indent=2, default=str)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

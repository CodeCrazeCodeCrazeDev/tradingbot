"""H9: China A-share L2 (venvoo dataset, HF-gated) microstructure test.

Requires HF_TOKEN in env (upload via secrets mechanism — never hardcode).
Schema: <date>/行情.parquet (quotes), 逐笔委托.parquet (order events),
逐笔成交.parquet (executed trades). A-share microstructure differs from
crypto: T+1 settlement, +/-10% daily limit, no retail shorting, stamp tax
~10bps on sells. Cost model: ~15bps round trip (comm ~5 + stamp ~10).

Tests: trade-side OFI and quote imbalance -> short-horizon forward returns,
per-day splits (never pooled). Ledgers to var/methods/ledger.jsonl.

Usage: HF_TOKEN=... python scripts/hf_l2_test.py [--days 3]
"""
import io
import json
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import numpy as np

REPO = "venvoo/china-a-share-l2-level2-limit-order-book-tick-data"
CACHE = Path("var/hf_l2")
LEDGER = Path("var/methods/ledger.jsonl")

COST_BPS = 15.0  # conservative A-share round trip


def record(verdict: str, metrics: dict):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    rec = {"hypothesis": "ashare_l2_ofi", "verdict": verdict,
           "ts": "2026-11-12", "detail": json.dumps(metrics)[:800]}
    LEDGER.open("a").write(json.dumps(rec) + "\n")
    print("ledgered:", verdict)


def fetch(days):
    from huggingface_hub import hf_hub_download
    out = {}
    for d in days:
        for kind in ("行情", "逐笔成交"):
            fn = f"{d}/{kind}.parquet"
            try:
                p = hf_hub_download(REPO, fn, repo_type="dataset",
                                    cache_dir=str(CACHE))
                out.setdefault(d, {})[kind] = p
                print(" got", fn)
            except Exception as e:
                print(" FAIL", fn, repr(e)[:160])
    return out


def analyze(path_quotes, path_trades, day):
    import pyarrow.parquet as pq
    t = pq.read_table(path_trades).to_pandas()
    q = pq.read_table(path_quotes).to_pandas()
    print(f"  {day}: trades {t.shape} cols={list(t.columns)[:12]}")
    print(f"  {day}: quotes {q.shape} cols={list(q.columns)[:12]}")
    return t, q


def main():
    if not os.environ.get("HF_TOKEN") and not os.environ.get("HUGGING_FACE_HUB_TOKEN"):
        print("HF_TOKEN not set — dataset is gated. "
              "Mint a read token and upload via secrets mechanism.")
        return 2
    days = sys.argv[sys.argv.index("--days") + 1:] \
        if "--days" in sys.argv else ["20170103", "20170104", "20170105"]
    got = fetch(days)
    if not got:
        record("UNAVAILABLE", {"reason": "no files downloaded"})
        return 1
    for d, paths in got.items():
        if "行情" in paths and "逐笔成交" in paths:
            analyze(paths["行情"], paths["逐笔成交"], d)
    print("\nNext: adapt OFI/imbalance -> fwd-return test to the actual "
          "schema (printed above), per-day splits, cost %.0fbps." % COST_BPS)


if __name__ == "__main__":
    sys.exit(main())

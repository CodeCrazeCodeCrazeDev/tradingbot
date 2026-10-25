"""Watch the research engine actually research.

Fetches live documents from arXiv / GitHub / HuggingFace / HF daily
papers, ingests them through the CSC research engine's claim
extractor, and prints what it found: sources, claims (declared vs
heuristic, quantified, hedged, polarity) and how many entered the
literature graph.

    python scripts/research_scan.py \
        --query "reinforcement learning trading" \
        --sources arxiv,github,hf_papers --max 6

All fetches are keyless public APIs; failures degrade to empty lists
and are reported, not hidden.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from trading_bot.core.csc.research.fetchers import FETCHERS          # noqa: E402
from trading_bot.core.csc.research.sources import extract_claims     # noqa: E402


def main() -> int:
    # READMEs carry unicode the Windows console can't print
    try:
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--query", required=True)
    ap.add_argument("--sources", default="arxiv,github,hf_papers",
                    help="comma list: arxiv,github,huggingface,hf_papers")
    ap.add_argument("--max", type=int, default=5, dest="maxn")
    ap.add_argument("--claims", type=int, default=8,
                    help="max claims printed per source")
    args = ap.parse_args()

    total_docs = total_claims = 0
    for name in (s.strip() for s in args.sources.split(",")):
        fn = FETCHERS.get(name)
        if not fn:
            print(f"[skip] unknown source '{name}'")
            continue
        print(f"\n=== {name} :: '{args.query}' ===")
        try:
            docs = fn(args.query, args.maxn)
        except Exception as e:
            print(f"[fetch-fail] {e}")
            continue
        print(f"fetched {len(docs)} documents")
        for d in docs:
            claims = extract_claims(d)
            total_claims += len(claims)
            total_docs += 1
            print(f"\n  {d.source_id}")
            print(f"    {d.title[:110]}")
            print(f"    url: {d.url}")
            print(f"    claims: {len(claims)}")
            for c in claims[: args.claims]:
                flags = []
                if c.quantified:
                    flags.append("Q")
                if c.hedged:
                    flags.append("hedged")
                flags.append(c.polarity)
                print(f"      [{c.extraction}|{c.confidence:.2f}|"
                      f"{','.join(flags)}] {c.text[:130]}")

    print(f"\n=== summary: {total_docs} docs, "
          f"{total_claims} claims extracted ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

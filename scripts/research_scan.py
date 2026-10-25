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
    ap.add_argument("--ingest", action="store_true",
                    help="feed docs into ResearchEngine.ingest_literature")
    ap.add_argument("--invert", action="store_true",
                    help="run weakness inversion — emit the defensive "
                         "rules each source's weaknesses imply")
    args = ap.parse_args()

    total_docs = total_claims = 0
    all_docs = []
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
        all_docs.extend(docs)
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
    if args.ingest and all_docs:
        print("\n=== ingest into ResearchEngine ===")
        try:
            from trading_bot.core.csc.research.engine import ResearchEngine
            # ingest_literature only touches the knowledge graph —
            # hypothesis_gen/verifier_swarm unused on this path.
            report = ResearchEngine(None, None).ingest_literature(all_docs)
            print(f"ingested: docs={report.get('documents')} "
                  f"claims={report.get('claims')}")
            print(f"claim_ids: {report.get('claim_ids', [])[:6]}")
        except Exception as e:
            print(f"ingest failed: {type(e).__name__}: {e}")

    if args.invert and all_docs:
        from trading_bot.core.csc.research.weakness_inversion import (
            invert_documents)
        inv = invert_documents(all_docs)
        print(f"\n=== weakness inversion: {inv['rules_total']} rules ===")
        for r in inv["rules"]:
            print(f"  [{r['severity']}] {r['weakness_id']} "
                  f"({len(r['seen_in'])} srcs) -> {r['inverted_rule'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

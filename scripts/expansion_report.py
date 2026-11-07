"""Expansion capability report — truthful per-claim status, measured
against the real data and the real host. Writes
``var/expansion_capabilities.json``.

Replaces the fiction of CAPABILITIES_SUMMARY.md for claims 7-15: every
entry names the real mechanism and what it actually measured in this
run. Numbers that could not be measured are reported as unavailable,
never estimated.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from trading_bot.expansion.service import (  # noqa: E402
    ExpansionContext, expansion_status)


def main() -> int:
    state = ROOT / "var" / "expansion"
    ctx = ExpansionContext(ROOT, state)
    scan = ctx.scan(force=True)
    status = expansion_status(ctx=ctx)
    status["scan_headline"] = {
        "series_scanned": scan["series_scanned"],
        "rows_total": ctx.inventory.scan()["rows_total"],
        "opportunities": len(scan["opportunities"]),
        "emerging_regimes": len(scan["emerging_regimes"]),
        "new_markets": len(scan["new_markets"]),
    }
    out = ROOT / "var" / "expansion_capabilities.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(status, indent=2, default=str))
    print(json.dumps(status["scan_headline"], indent=2))
    for claim, c in status["claims"].items():
        print(f"{claim:26} {c['status']:14} {c['mechanism']}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

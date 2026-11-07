"""Research-domain generation — new research areas derived from
measured evidence, not appended from a buzzword list.

A new domain is only honest if it comes from something the system
actually observed: a data-coverage gap it can investigate, a measured
regime shift, a recurring failure kind in the HMS, or a falsified
candidate family whose rejection pattern deserves explanation. Each
proposal carries its evidence basis so a reader can see why it exists.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class DomainGenerator:
    """Derives candidate research domains from measured evidence."""

    def __init__(self, state_path: Any) -> None:
        self.state_path = Path(state_path)
        self.proposed: List[Dict[str, Any]] = self._load()

    def generate(
        self,
        *,
        coverage_gaps: Iterable[Dict[str, Any]] = (),
        emerging_regimes: Iterable[Dict[str, Any]] = (),
        failure_kinds: Optional[Dict[str, int]] = None,
        falsified_families: Iterable[str] = (),
    ) -> List[Dict[str, Any]]:
        """Produce deduplicated domain proposals. Each proposal names
        the evidence that justifies researching it — a domain without a
        basis is just a word."""
        out: List[Dict[str, Any]] = []
        for g in coverage_gaps:
            out.append({
                "domain": "unexplored_instrument",
                "question": (f"does {g['symbol']}:{g['timeframe']} on "
                             f"{g['source']} carry exploitable "
                             f"structure after costs?"),
                "basis": {"coverage_gap": dict(g)}})
        for r in emerging_regimes:
            out.append({
                "domain": "regime_shift_adaptation",
                "question": (f"does the {r['symbol']}:{r['timeframe']} "
                             f"volatility-regime expansion "
                             f"(ratio={r.get('vol_regime_ratio')}) "
                             "persist or revert?"),
                "basis": {"emerging_regime": dict(r)}})
        for kind, count in sorted((failure_kinds or {}).items()):
            if count <= 0:
                continue
            out.append({
                "domain": "failure_mode_research",
                "question": (f"what causal factor drives {count} "
                             f"recorded '{kind}' failures — data, "
                             "model, or gate design?"),
                "basis": {"failure_kind": kind, "count": count}})
        for fam in falsified_families:
            out.append({
                "domain": "falsification_followup",
                "question": (f"why was candidate family '{fam}' "
                             "falsified — wrong feature, wrong "
                             "regime, or wrong cost model?"),
                "basis": {"falsified_family": str(fam)}})
        seen = {(d["domain"], d["question"]) for d in self.proposed}
        fresh = [d for d in out
                 if (d["domain"], d["question"]) not in seen]
        self.proposed.extend(fresh)
        self.proposed = self.proposed[-200:]
        self._save()
        return fresh

    def summary(self) -> Dict[str, Any]:
        return {
            "domains_proposed_total": len(self.proposed),
            "recent": self.proposed[-8:],
            "note": ("every domain names the measured evidence that "
                     "spawned it — gaps, regime shifts, failures, "
                     "falsifications"),
        }

    def _load(self) -> List[Dict[str, Any]]:
        if self.state_path.exists():
            try:
                return list(json.loads(self.state_path.read_text())
                            .get("proposed", []))
            except Exception:  # noqa: BLE001
                return []
        return []

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"proposed": self.proposed},
                                  indent=2))
        tmp.replace(self.state_path)

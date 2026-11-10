"""Self-innovation engine — arXiv:2504.01990 self-enhancement loop.

The paper's adaptive-evolution paradigm, grounded in this runtime's
existing gates instead of aspirational plumbing:

  SYNTHESIZE  bounded candidate specs from measured evidence —
              weakest skills, failure-memory kinds, frontier pattern
              hints — over the derivable-feature space only.
  EVALUATE    every candidate through ``validate_model``: 70% fit,
              30% held-out scoring, net-of-cost expectancy.
  SELECT      only candidates the holdout measured as positive are
              left in VALIDATED state for operator/RSI review.
  INTEGRATE   never automatic — ``approve_model``/``attach`` stay
              behind OperatorAuthorization like every promotion.

Nothing here fabricates results: a candidate that can't clear the
holdout is recorded as evidence of a failed hypothesis — the loop's
value is measured selection, not candidate volume.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from .model_engineering import DERIVABLE_FEATURES, validate_spec

logger = logging.getLogger(__name__)

CATEGORICAL_FEATURES = frozenset({
    "trend", "regime", "htf_trend", "trend_effective", "session"})
# Numeric features sane to threshold without scale context — bounded
# operating points, holdout validation kills the bad ones.
_NUMERIC_DEFAULTS: Dict[str, Tuple[float, ...]] = {
    "rsi": (55.0, 45.0), "rsi14": (55.0, 45.0),
    "htf_rsi14": (55.0, 45.0),
    "volatility": (0.002, 0.006),
    "trend_strength": (0.5, 0.7),
    "volume_ratio": (1.3, 1.8),
    "momentum": (0.0005, -0.0005),
    "peer_return": (0.0005, -0.0005),
    "peer_corr": (0.5, -0.5),
    "ret_autocorr": (0.05, -0.05),
    "trend_reliability": (0.6, 0.75),
    "advisory_disagreement": (0.3, 0.6),
    "spread_bps": (2.0, 5.0),
    "session_hour": (8.0, 14.0),
    "system_health_score": (60.0, 75.0),
}
_REGIME_EQUALS = ("trend", "range", "high_volatility", "low_volatility")
MAX_CANDIDATES_PER_CYCLE = int(os.environ.get(
    "TB_INNOVATE_MAX_CANDIDATES", "4"))


def _seeded_order(items: List[Any], salt: str) -> List[Any]:
    return sorted(items, key=lambda x: hashlib.md5(
        f"{salt}:{x}".encode()).hexdigest())


class SelfInnovationEngine:
    """Bounded candidate synthesizer + gated evaluator."""

    def __init__(self) -> None:
        self.candidates_proposed = 0
        self.candidates_validated = 0
        self.candidates_rejected = 0
        self.cycles_run = 0

    # -- synthesize -----------------------------------------------------

    def synthesize(self, weakest_skills: List[str],
                   failure_kinds: List[str],
                   frontier_hints: List[str],
                   salt: str = "") -> List[Dict[str, Any]]:
        """Evidence-seeded bounded specs — numeric thresholds +
        categorical equals only. ``validate_spec`` is re-checked so a
        spec bug can never smuggle an invalid candidate downstream."""
        specs: List[Dict[str, Any]] = []
        hints = {h.lower() for h in frontier_hints}
        feats = sorted(f for f in DERIVABLE_FEATURES
                       if f not in CATEGORICAL_FEATURES
                       and f in _NUMERIC_DEFAULTS)
        # Evidence-directed subset first: features named by weak skills
        # or frontier pattern text lead the queue.
        directed = [f for f in feats
                    if any(f in s for s in weakest_skills)
                    or f in hints]
        ordered = _seeded_order(
            list(dict.fromkeys(directed + feats)), salt)
        i = 0
        for feat in ordered:
            for direction in ("BUY", "SELL"):
                for j, th in enumerate(_NUMERIC_DEFAULTS[feat]):
                    op = ">" if j % 2 == 0 else "<"
                    spec = {
                        "kind": "threshold_rule",
                        "name": f"innovate-{feat}-{direction.lower()}-{j}",
                        "feature": feat, "op": op,
                        "threshold": th, "direction": direction,
                        "horizon": 8,
                        "provenance": "self_innovation",
                        "evidence": {
                            "weak_skills": weakest_skills[:3],
                            "failure_kinds": failure_kinds[:3],
                            "frontier_hints": frontier_hints[:3]},
                    }
                    if not validate_spec(spec):
                        specs.append(spec)
                        i += 1
                    if i >= MAX_CANDIDATES_PER_CYCLE * 4:
                        break
                if i >= MAX_CANDIDATES_PER_CYCLE * 4:
                    break
            if i >= MAX_CANDIDATES_PER_CYCLE * 4:
                break
        # Failure-kind regime equals — categorical candidates seeded by
        # the regime the failure memory implicates.
        for kind in failure_kinds:
            for reg in _REGIME_EQUALS:
                if reg in kind:
                    spec = {
                        "kind": "threshold_rule",
                        "name": f"innovate-regime-{reg}-{kind[:20]}",
                        "feature": "regime", "equals": reg,
                        "direction": "BUY", "horizon": 8,
                        "provenance": "self_innovation",
                        "evidence": {"failure_kinds": [kind]}}
                    if not validate_spec(spec):
                        specs.append(spec)
                    break
        # Deterministic selection: measured-diversity cap.
        return _seeded_order(specs, salt or str(time.time_ns()) // 10 ** 9
                             )[:MAX_CANDIDATES_PER_CYCLE]

    def _evidence(self, csc: Any) -> Tuple[List[str], List[str], List[str]]:
        weak: List[str] = []
        failures: List[str] = []
        hints: List[str] = []
        try:
            evo = getattr(csc, "_evolution", None)
            mastery = getattr(evo, "_mastery", None)
            if mastery is not None:
                for s in mastery.consolidator.get_weakest_skills(3):
                    weak.append(str(s.name).lower())
        except Exception:  # noqa: BLE001
            pass
        try:
            hms = getattr(csc, "hms", None)
            if hms is not None and hasattr(hms, "failure_summary"):
                failures = list(
                    (hms.failure_summary() or {}).get("by_kind", {})
                    .keys())[:5]
        except Exception:  # noqa: BLE001
            pass
        try:
            if evo is not None:
                hints = [str(t) for t in
                         (evo._last_intel or {}).get("topics", ())][:3]
        except Exception:  # noqa: BLE001
            pass
        return weak, failures, hints

    # -- evaluate ---------------------------------------------------------

    async def innovate(self, csc: Any,
                       bars_by_symbol: Dict[str, List[Dict[str, Any]]]
                       ) -> Dict[str, Any]:
        """One bounded innovation pass. Returns a truthful report —
        counts, per-candidate verdicts, nothing claimed unmeasured."""
        weak, failures, hints = self._evidence(csc)
        specs = self.synthesize(
            weak, failures, hints, salt=str(self.cycles_run))
        report: Dict[str, Any] = {"proposed": 0, "validated": 0,
                                  "rejected": 0, "candidates": []}
        bars = next(iter(bars_by_symbol.values()), [])
        if not specs or len(bars) < 80:
            report["status"] = "insufficient_evidence"
            report["bars"] = len(bars)
            return report
        for spec in specs:
            entry: Dict[str, Any] = {"name": spec["name"]}
            try:
                prop = await csc.propose_model(
                    spec, proposed_by="self_innovation")
                entry["proposed"] = prop.get("status")
                if prop.get("status") != "proposed":
                    report["rejected"] += 1
                    entry["errors"] = prop.get("errors")
                    report["candidates"].append(entry)
                    continue
                val = await csc.validate_model(
                    prop["candidate_id"], bars)
                verdict = str(val.get("verdict") or val.get("status"))
                entry["verdict"] = verdict
                entry["candidate_id"] = prop["candidate_id"]
                if verdict.upper().startswith("VALIDATED"):
                    report["validated"] += 1
                    self.candidates_validated += 1
                else:
                    report["rejected"] += 1
                    self.candidates_rejected += 1
                report["proposed"] += 1
                self.candidates_proposed += 1
            except Exception as exc:  # noqa: BLE001
                entry["verdict"] = "error"
                entry["error"] = str(exc)[:120]
                report["rejected"] += 1
            report["candidates"].append(entry)
        report["status"] = "ok"
        self.cycles_run += 1
        return report

    def status(self) -> Dict[str, Any]:
        return {"cycles_run": self.cycles_run,
                "candidates_proposed": self.candidates_proposed,
                "candidates_validated": self.candidates_validated,
                "candidates_rejected": self.candidates_rejected}

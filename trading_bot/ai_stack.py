"""Canonical AI stack — read-only introspection facade over the CSC.

Implements the three-plane view defined in
``DOCS/CANONICAL_RUNTIME_DATAFLOW.md`` §4:

- **State plane**    — what the system believes: VFE/surprise, DiscoLoop
  latent + discrete channel, derived-feature history, memory.
- **Evidence plane** — what advisors contribute: PCA agents, advisory
  services (normalized, authority-stripped), research artifacts.
- **Selection plane** — how a proposal survives: branches, simulation,
  pivot/refine tilt, verification, synthesis, ledger fold.

Authority boundary: this module is a *read model*. It exposes no method
that approves, sizes, vetoes, or executes — it only snapshots and explains
what the CognitiveSystemController already computed. CSC remains the sole
decision authority.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

__all__ = ["AIStack", "AIStackSnapshot"]


class AIStackSnapshot(Dict[str, Any]):
    """Typed dict subclass for IDE-friendliness; pure data."""


class AIStack:
    """Read-only projection of a running CognitiveSystemController.

    Wraps a CSC instance and exposes the §4 planes as structured,
    JSON-safe dictionaries. All accessors are defensive — a partially
    wired CSC (paper mode, missing advisory services, no HMS) still
    returns a complete snapshot with empty sections rather than raising.
    """

    def __init__(self, csc: Any) -> None:
        self._csc = csc

    # -- State plane -----------------------------------------------------

    def state_plane(self) -> Dict[str, Any]:
        """Belief state: surprise history, recurrence, uncertainty."""
        csc = self._csc
        latent = None
        lat = getattr(csc, "continuous_state", {}).get("latent")
        if lat is not None:
            try:
                arr = np.asarray(lat, dtype=float)
                latent = {
                    "dim": int(arr.size),
                    "norm": float(np.linalg.norm(arr)),
                    "mean": float(arr.mean()),
                }
            except Exception:  # noqa: BLE001 - introspection must not fail
                latent = {"dim": 0, "norm": None, "mean": None}
        return {
            "vfe": _safe_num(getattr(csc, "variational_free_energy", None)),
            "vfe_history_len": len(getattr(csc, "vfe_history", []) or []),
            "epistemic_uncertainty": _safe_num(
                getattr(getattr(csc, "state", None),
                        "epistemic_uncertainty", None)),
            "discoloop": {
                "latent": latent,
                "discrete_channel_len": len(
                    getattr(csc, "discrete_channel", []) or []),
                "last_tokens": list(
                    getattr(csc, "discrete_channel", []) or [])[-8:],
            },
            "observation_history": {
                sym: len(closes)
                for sym, closes in getattr(
                    csc, "_obs_history", {}).items()},
            "last_prediction": getattr(csc, "last_prediction", None),
        }

    # -- Evidence plane --------------------------------------------------

    def evidence_plane(self) -> Dict[str, Any]:
        """Advisory surface: attached services, this cycle's calls,
        measured reliability. Read-only — see csc.advisory_report()."""
        csc = self._csc
        report = {}
        if hasattr(csc, "advisory_report"):
            try:
                report = csc.advisory_report()
            except Exception:  # noqa: BLE001
                report = {}
        return {
            "attached": list(report.get("attached", [])),
            "measured": dict(report.get("measured", {})),
            "last_advisory_calls": list(
                getattr(csc, "_last_advisory_calls", []) or []),
            "last_advisory_ids": list(
                getattr(csc, "_last_advisory_ids", []) or []),
            "pending_research_artifacts": len(
                getattr(csc, "_research_artifacts", []) or []),
            "pca_population": [
                getattr(a, "name", type(a).__name__)
                for a in getattr(csc, "agent_population", [])],
        }

    # -- Reflection plane -------------------------------------------------

    def reflection_plane(self) -> Dict[str, Any]:
        """Failure memory + self-improvement memory (HMS reflective
        stores): what the system got wrong and what the RSI loop learned."""
        hms = getattr(self._csc, "hms", None)
        plane: Dict[str, Any] = {
            "failures": {"total": 0, "by_kind": {}, "by_regime": {}},
            "recent_failures": [],
            "improvements": {"total": 0, "by_domain": {},
                             "decisions_by_status": {}},
            "recent_lessons": [],
        }
        if hms is None:
            return plane
        try:
            if hasattr(hms, "failure_summary"):
                plane["failures"] = hms.failure_summary()
            if hasattr(hms, "recall_failures"):
                plane["recent_failures"] = hms.recall_failures(limit=5)
            if hasattr(hms, "improvement_summary"):
                plane["improvements"] = hms.improvement_summary()
            if hasattr(hms, "recall_lessons"):
                plane["recent_lessons"] = hms.recall_lessons(limit=5)
        except Exception:  # noqa: BLE001 - introspection must not fail
            pass
        return plane

    # -- Selection plane -------------------------------------------------

    def selection_plane(self) -> Dict[str, Any]:
        """Selection state: pending predictions, churn budget, EV
        calibration pairs, decision journal tail."""
        csc = self._csc
        journal = {}
        if hasattr(csc, "get_decision_journal"):
            try:
                journal = csc.get_decision_journal() or {}
            except Exception:  # noqa: BLE001
                journal = {}
        churn = getattr(csc, "_churn_budget", 0)
        used = sum(
            1 for s in getattr(csc, "_recent_trade_seqs", [])
            if s > getattr(csc, "_observation_seq", 0)
            - getattr(csc, "_churn_window", 0))
        ev_pairs = list(getattr(csc, "_ev_pairs", []) or [])
        return {
            "open_positions": dict(journal.get("open_positions", {})),
            "pending_predictions": len(
                journal.get("pending_predictions", {})),
            "folded_summaries": len(
                journal.get("folded_summaries", [])),
            "churn": {
                "budget": churn,
                "window": getattr(csc, "_churn_window", 0),
                "used_in_window": used,
            },
            "ev_calibration": {
                "pairs": len(ev_pairs),
                "min_samples": getattr(csc, "_ev_min_samples", 0),
                "factor": _safe_num(getattr(
                    csc, "_ev_calibration_factor", lambda: None)()),
                "cost_bps": getattr(csc, "_default_cost_bps", None),
            },
            "decision_stride": getattr(csc, "_decision_stride", 1),
            "advisory_tilt_bound": getattr(csc, "_ADVISORY_TILT", 0.25),
        }

    # -- Whole-stack snapshot --------------------------------------------

    def snapshot(self) -> AIStackSnapshot:
        """One JSON-safe frame of the whole AI stack."""
        status = {}
        if hasattr(self._csc, "get_status"):
            try:
                status = self._csc.get_status() or {}
            except Exception:  # noqa: BLE001
                status = {}
        return AIStackSnapshot(
            status=status,
            state=self.state_plane(),
            evidence=self.evidence_plane(),
            selection=self.selection_plane(),
            reflection=self.reflection_plane(),
        )

    def explain(self) -> Dict[str, str]:
        """Human-readable one-liner per plane — for logs/CLI."""
        s, e, sel, r = (
            self.state_plane(), self.evidence_plane(),
            self.selection_plane(), self.reflection_plane())
        return {
            "state": (
                f"VFE={s['vfe']} · uncertainty="
                f"{s['epistemic_uncertainty']} · discoloop tokens="
                f"{s['discoloop']['discrete_channel_len']}"),
            "evidence": (
                f"{len(e['attached'])} advisors attached · "
                f"{len(e['measured'])} measured · "
                f"{len(e['last_advisory_calls'])} calls this cycle"),
            "selection": (
                f"{sel['pending_predictions']} pending predictions · "
                f"churn {sel['churn']['used_in_window']}/"
                f"{sel['churn']['budget']} · "
                f"EV-calibration {sel['ev_calibration']['factor']} "
                f"({sel['ev_calibration']['pairs']} pairs)"),
            "reflection": (
                f"{r['failures'].get('total', 0)} failures recorded · "
                f"{r['improvements'].get('total', 0)} RSI artifacts"),
        }


def _safe_num(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None

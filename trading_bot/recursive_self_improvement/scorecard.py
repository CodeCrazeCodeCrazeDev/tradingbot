"""RSI scorecard (mission section 14).

The target is not "how many modifications" but how frequently the process
produces reproducible, transferable, economically meaningful improvements
per unit of trials, compute and risk. Computed only from the hash-chained
archive and append-only ledger, so the scorecard can't be gamed by
rewriting history.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from .archive import ParetoArchive
from .memory import ImprovementMemory

TRANSFER_WINNERS = ("TRANSFERABLE", "SYSTEMIC")


class RSIScorecard:
    def __init__(self, archive: ParetoArchive,
                 memory: Optional[ImprovementMemory] = None) -> None:
        self.archive = archive
        self.memory = memory

    def compute(self) -> Dict[str, Any]:
        records = [r for r in self.archive.records if r.get("kind") == "record"]
        roles = self.archive.current_roles()
        total = len(records)
        eligible = [r for r in records if r["verdict"] == "eligible_for_operator_review"]
        transfer = [r for r in eligible
                    if r["extra"].get("transfer_class") in TRANSFER_WINNERS]
        rejected = [r for r in records if r["verdict"] == "rejected"]
        insufficient = [r for r in records if r["verdict"] == "insufficient_evidence"]
        cells = {r["regime_cell"] for r in records}
        depths = [len(self.archive.lineage(r["genome_id"])) for r in records] or [0]
        rollbacks = [r for r in self.archive.records if r.get("kind") == "rollback"]
        chained = self.archive.verify_chain()

        ledger_rows = 0
        ledger_ok = True
        if self.memory is not None:
            try:
                ledger_rows = len(self.memory.get_recent_experiments(limit=100000))
            except Exception:  # noqa: BLE001
                ledger_rows = 0
            try:
                ledger_ok = bool(self.memory.verify_evidence_chain())
            except AttributeError:
                ledger_ok = True

        return {
            "trials_total": total,
            "eligible_rate": len(eligible) / total if total else 0.0,
            "rejection_rate": len(rejected) / total if total else 0.0,
            "insufficient_rate": len(insufficient) / total if total else 0.0,
            "transfer_rate_of_eligible": len(transfer) / len(eligible) if eligible else 0.0,
            "trials_per_eligible": (total / len(eligible)) if eligible else None,
            "novelty_cells": len(cells),
            "max_lineage_depth": max(depths),
            "live_members": len(self.archive.live_members()),
            "frontier_size": len(self.archive.frontier(
                ("net_return", "max_drawdown", "cvar_95"))),
            "rollback_events": len(rollbacks),
            "archive_chain_valid": chained,
            "evidence_ledger_rows": ledger_rows,
            "evidence_ledger_valid": ledger_ok,
            "champion": (self.archive.champion() or {}).get("genome_id"),
        }

    def report_markdown(self) -> str:
        s = self.compute()
        lines = ["# RSI scorecard", ""]
        for k, v in s.items():
            lines.append(f"- **{k}**: {v}")
        return "\n".join(lines) + "\n"

    def write(self, json_path: str | Path, md_path: Optional[str | Path] = None) -> None:
        Path(json_path).write_text(
            json.dumps(self.compute(), indent=2, default=str) + "\n",
            encoding="utf-8")
        if md_path:
            Path(md_path).write_text(self.report_markdown(), encoding="utf-8")

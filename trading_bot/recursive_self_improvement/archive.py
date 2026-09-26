"""Append-only Pareto improvement archive (mission section 7).

Not naive hill climbing: champions, challengers, regime specialists,
informative failures and ancestors are all retained with full lineage.
The file is a JSONL hash chain — each record carries the previous record's
hash, so silent tampering or deletion breaks ``verify_chain``.
Role changes are themselves appended records; nothing is ever rewritten.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .metric_registry import direction

ROLES = ("champion", "challenger", "specialist", "stepping_stone",
         "failed_informative", "ancestor")
LIVE_ROLES = ("champion", "challenger", "specialist", "stepping_stone")


def _canon(data: Mapping[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, default=str).encode("utf-8")


def _record_hash(record: Mapping[str, Any]) -> str:
    body = {k: v for k, v in record.items() if k != "record_hash"}
    return hashlib.sha256(_canon(body)).hexdigest()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ParetoArchive:
    """Hash-chained append-only archive of evaluated candidates."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: List[Dict[str, Any]] = []
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self.records.append(json.loads(line))
        self._last_hash = self.records[-1]["record_hash"] if self.records else "GENESIS"
        if not self.verify_chain():
            raise ValueError(f"archive chain broken: {self.path}")

    # -- writing ------------------------------------------------------------
    def _append(self, kind: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        rec: Dict[str, Any] = {
            "kind": kind,
            "created_at": _utcnow(),
            "prev_hash": self._last_hash,
            **dict(payload),
        }
        rec["record_hash"] = _record_hash(rec)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
        self.records.append(rec)
        self._last_hash = rec["record_hash"]
        return rec

    def record_candidate(
        self,
        *,
        genome_id: str,
        parent_id: str,
        contract_hash: str,
        dataset_hash: str,
        strategy_family: str,
        metric_vector: Mapping[str, float],
        delta: Mapping[str, float],
        verdict: str,
        role: str,
        regime_cell: str = "all",
        trial_index: int = 0,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        if role not in ROLES:
            raise ValueError(f"unknown archive role {role!r}")
        return self._append("record", {
            "genome_id": genome_id, "parent_id": parent_id,
            "contract_hash": contract_hash, "dataset_hash": dataset_hash,
            "strategy_family": strategy_family,
            "metric_vector": dict(metric_vector), "delta": dict(delta),
            "verdict": verdict, "role": role, "regime_cell": regime_cell,
            "trial_index": trial_index, "extra": dict(extra or {}),
        })

    def record_role(self, genome_id: str, new_role: str, reason: str) -> Dict[str, Any]:
        if new_role not in ROLES:
            raise ValueError(f"unknown archive role {new_role!r}")
        return self._append("role", {"genome_id": genome_id,
                                     "new_role": new_role, "reason": reason})

    def record_rollback(self, from_genome: str, to_snapshot: str, reason: str) -> Dict[str, Any]:
        return self._append("rollback", {"from_genome": from_genome,
                                         "to_snapshot": to_snapshot,
                                         "reason": reason})

    # -- reading --------------------------------------------------------------
    def verify_chain(self) -> bool:
        prev = "GENESIS"
        for rec in self.records:
            if rec.get("prev_hash") != prev or _record_hash(rec) != rec.get("record_hash"):
                return False
            prev = rec["record_hash"]
        return True

    def _records(self) -> List[Dict[str, Any]]:
        return [r for r in self.records if r.get("kind") == "record"]

    def current_roles(self) -> Dict[str, str]:
        roles = {r["genome_id"]: r["role"] for r in self._records()}
        for r in self.records:
            if r.get("kind") == "role":
                roles[r["genome_id"]] = r["new_role"]
        return roles

    def by_id(self, genome_id: str) -> Optional[Dict[str, Any]]:
        for r in self._records():
            if (r["genome_id"] == genome_id
                    or r["extra"].get("fingerprint") == genome_id):
                return r
        return None

    def champion(self) -> Optional[Dict[str, Any]]:
        roles = self.current_roles()
        for r in reversed(self._records()):
            if roles.get(r["genome_id"]) == "champion":
                return r
        return None

    def live_members(self) -> List[Dict[str, Any]]:
        roles = self.current_roles()
        return [r for r in self._records() if roles.get(r["genome_id"]) in LIVE_ROLES]

    def frontier(self, objectives: Sequence[str]) -> List[Dict[str, Any]]:
        members = self.live_members()
        out: List[Dict[str, Any]] = []
        for rec in members:
            dominated = False
            for other in members:
                if other is rec:
                    continue
                if _dominates(other["metric_vector"], rec["metric_vector"], objectives):
                    dominated = True
                    break
            if not dominated:
                out.append(rec)
        return out

    def lineage(self, genome_id: str) -> List[Dict[str, Any]]:
        """Parent chain from root ancestor down to the given genome."""
        chain: List[Dict[str, Any]] = []
        seen = set()
        current: Optional[Dict[str, Any]] = self.by_id(genome_id)
        while current is not None and current["genome_id"] not in seen:
            seen.add(current["genome_id"])
            chain.append(current)
            parent = current.get("parent_id")
            current = self.by_id(parent) if parent else None
        return list(reversed(chain))

    def sample_parent(self, rng: random.Random,
                      strategy: str = "frontier",
                      objectives: Sequence[str] = ()) -> Optional[str]:
        pool = self.frontier(objectives) if strategy == "frontier" and objectives else self.live_members()
        if not pool:
            return None
        if strategy == "uniform":
            return rng.choice(pool)["genome_id"]
        if strategy == "novelty":
            rarest = min(pool, key=lambda r: sum(
                1 for m in self.live_members() if m["regime_cell"] == r["regime_cell"]))
            return rarest["genome_id"]
        weights = [max(r["metric_vector"].get("paired_mean_diff", 0.0), 0.0) + 1e-9
                   for r in pool]
        return rng.choices(pool, weights=weights, k=1)[0]["genome_id"]


def _dominates(a: Mapping[str, float], b: Mapping[str, float],
               objectives: Sequence[str]) -> bool:
    better = False
    for o in objectives:
        d = direction(o)
        av, bv = a.get(o, 0.0), b.get(o, 0.0)
        if (d == "max" and av < bv - 1e-12) or (d == "min" and av > bv + 1e-12):
            return False
        if (d == "max" and av > bv + 1e-12) or (d == "min" and av < bv - 1e-12):
            better = True
    return better

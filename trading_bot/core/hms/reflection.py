"""Reflective memory for the HMS — failure memory + self-improvement memory.

Two append-mostly stores under the HMS base path that make the system's own
history queryable by the evidence plane:

- ``FailureMemory`` — categorized failure records: incorrect predictions,
  trade rejections, advisor errors, execution faults. The CSC writes into it
  at decision/outcome time; the evidence stage recalls relevant failures so
  repeated mistakes are visible *before* the next decision, not only after.
- ``SelfImprovementMemory`` — RSI artifacts: improvement proposals,
  promotion decisions and generalized lessons. Human-gated by construction —
  this store records what the RSI cycle concluded; it never authorizes a
  change by itself.

Both stores mirror their entries into the SAGE graph so the existing
``retrieve_evidence_chain`` multi-hop query picks them up as evidence.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Failure memory
# ---------------------------------------------------------------------------

# Closed taxonomy — a free-form ``kind`` would scatter retrieval. Anything
# outside this set is normalized to "other".
FAILURE_KINDS = frozenset({
    "prediction_incorrect",   # realized move contradicted the CSC call
    "decision_rejected",      # TRADE_REJECTED at any gate
    "advisor_error",          # advisory service raised / timed out
    "execution_fault",        # order submit/fill path fault
    "verification_failed",    # verifier swarm / evidence gate failure
    "other",
})

_FAILURE_CONFIDENCE = {
    # SAGE edge weight for the indexed triplet — how strongly a failure
    # should surface in evidence retrieval. An incorrect high-confidence
    # prediction is the most informative failure the system has.
    "prediction_incorrect": 0.9,
    "decision_rejected": 0.5,
    "advisor_error": 0.6,
    "execution_fault": 0.8,
    "verification_failed": 0.7,
    "other": 0.4,
}


@dataclass
class FailureRecord:
    """One categorized failure observation."""
    kind: str
    summary: str
    failure_id: str = field(default_factory=lambda: f"FAIL-{uuid4().hex[:10]}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    trade_id: Optional[str] = None
    symbol: Optional[str] = None
    regime: str = "unknown"
    stage: Optional[str] = None       # pipeline stage that produced it
    confidence: float = 0.0           # confidence of the failed decision
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "kind": self.kind,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "regime": self.regime,
            "stage": self.stage,
            "confidence": self.confidence,
            "context": dict(self.context),
        }


class FailureMemory:
    """Bounded, durable store of categorized failures.

    In-memory: a bounded deque for fast recall + per-kind/per-regime counts.
    Durable: one JSON object per line under ``<path>/failures.jsonl``, and a
    SAGE triplet ``(subject, FAILED_IN_KIND, kind)`` /
    ``(subject, FAILED_IN_REGIME, regime)`` so failures join the causal
    evidence graph that ``retrieve_evidence_chain`` traverses.
    """

    def __init__(self, path: str, sage: Any = None, maxlen: int = 4096) -> None:
        self.path = path
        self.sage = sage
        os.makedirs(path, exist_ok=True)
        self._jsonl = os.path.join(path, "failures.jsonl")
        self._records: deque = deque(maxlen=maxlen)
        self._kind_counts: Dict[str, int] = {}
        self._regime_counts: Dict[str, int] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        """Rehydrate the bounded window + counters from the JSONL tail."""
        if not os.path.exists(self._jsonl):
            return
        try:
            with open(self._jsonl, "r", encoding="utf-8") as fh:
                lines = fh.readlines()[-self._records.maxlen:]
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._index(rec)
                self._records.append(rec)
        except OSError as exc:
            logger.warning("FailureMemory: reload failed: %s", exc)

    def _index(self, rec: Dict[str, Any]) -> None:
        kind = str(rec.get("kind") or "other")
        regime = str(rec.get("regime") or "unknown")
        self._kind_counts[kind] = self._kind_counts.get(kind, 0) + 1
        self._regime_counts[regime] = self._regime_counts.get(regime, 0) + 1

    def record(self, failure: FailureRecord) -> str:
        """Persist a failure; returns the failure_id. Never raises."""
        if failure.kind not in FAILURE_KINDS:
            failure.kind = "other"
        rec = failure.to_dict()
        subject = failure.trade_id or failure.symbol or failure.failure_id
        with self._lock:
            try:
                with open(self._jsonl, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, sort_keys=True) + "\n")
            except OSError as exc:
                logger.warning("FailureMemory: persist failed: %s", exc)
            self._records.append(rec)
            self._index(rec)
        if self.sage is not None:
            try:
                conf = _FAILURE_CONFIDENCE.get(failure.kind, 0.4)
                self.sage.add_evidence(
                    (f"failure:{failure.failure_id}", "FAILED_IN_KIND",
                     f"kind:{failure.kind}"),
                    {"regime": failure.regime, "stage": failure.stage or ""},
                    {"confidence": conf})
                self.sage.add_evidence(
                    (f"failure:{failure.failure_id}", "FAILED_ON",
                     f"subject:{subject}"),
                    {"regime": failure.regime},
                    {"confidence": conf})
            except Exception as exc:  # noqa: BLE001 - indexing must not break recording
                logger.debug("FailureMemory: SAGE index failed: %s", exc)
        return failure.failure_id

    def recall(self, *, kind: Optional[str] = None, regime: Optional[str] = None,
               symbol: Optional[str] = None, limit: int = 20
               ) -> List[Dict[str, Any]]:
        """Most-recent-first recall filtered by kind/regime/symbol."""
        out: List[Dict[str, Any]] = []
        for rec in reversed(self._records):
            if kind is not None and rec.get("kind") != kind:
                continue
            if regime is not None and rec.get("regime") != regime:
                continue
            if symbol is not None and rec.get("symbol") != symbol:
                continue
            out.append(rec)
            if len(out) >= limit:
                break
        return out

    def summary(self) -> Dict[str, Any]:
        """Aggregate counts — the shape the RSI observer consumes."""
        with self._lock:
            return {
                "total": sum(self._kind_counts.values()),
                "by_kind": dict(self._kind_counts),
                "by_regime": dict(self._regime_counts),
            }


# ---------------------------------------------------------------------------
# Self-improvement memory
# ---------------------------------------------------------------------------

@dataclass
class ImprovementRecord:
    """One RSI artifact: proposal, decision, or generalized lesson."""
    record_type: str              # proposal | decision | lesson
    domain: str
    summary: str
    record_id: str = field(default_factory=lambda: f"IMP-{uuid4().hex[:10]}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = ""              # e.g. eligible_for_operator_review / rejected
    genome_id: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "domain": self.domain,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "status": self.status,
            "genome_id": self.genome_id,
            "evidence": dict(self.evidence),
        }


class SelfImprovementMemory:
    """Durable store of RSI proposals/decisions/lessons.

    Record-only: promotion authority stays with the signed
    ``OperatorAuthorization`` at the ``PromotionLadder`` — nothing here can
    move a candidate to live config.
    """

    _RECORD_TYPES = frozenset({"proposal", "decision", "lesson"})

    def __init__(self, path: str, sage: Any = None, maxlen: int = 2048) -> None:
        self.path = path
        self.sage = sage
        os.makedirs(path, exist_ok=True)
        self._jsonl = os.path.join(path, "improvements.jsonl")
        self._records: deque = deque(maxlen=maxlen)
        self._domain_counts: Dict[str, int] = {}
        self._status_counts: Dict[str, int] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._jsonl):
            return
        try:
            with open(self._jsonl, "r", encoding="utf-8") as fh:
                lines = fh.readlines()[-self._records.maxlen:]
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._index(rec)
                self._records.append(rec)
        except OSError as exc:
            logger.warning("SelfImprovementMemory: reload failed: %s", exc)

    def _index(self, rec: Dict[str, Any]) -> None:
        domain = str(rec.get("domain") or "unknown")
        status = str(rec.get("status") or "none")
        self._domain_counts[domain] = self._domain_counts.get(domain, 0) + 1
        if rec.get("record_type") == "decision":
            self._status_counts[status] = self._status_counts.get(status, 0) + 1

    def record(self, item: ImprovementRecord) -> str:
        """Persist an improvement artifact; returns the record_id."""
        if item.record_type not in self._RECORD_TYPES:
            item.record_type = "lesson"
        rec = item.to_dict()
        with self._lock:
            try:
                with open(self._jsonl, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, sort_keys=True) + "\n")
            except OSError as exc:
                logger.warning("SelfImprovementMemory: persist failed: %s", exc)
            self._records.append(rec)
            self._index(rec)
        if self.sage is not None:
            try:
                self.sage.add_evidence(
                    (f"improvement:{item.record_id}",
                     "LESSON_IN_DOMAIN", f"domain:{item.domain}"),
                    {"status": item.status},
                    {"confidence": 0.7})
            except Exception as exc:  # noqa: BLE001
                logger.debug("SelfImprovementMemory: SAGE index failed: %s", exc)
        return item.record_id

    def lessons(self, *, domain: Optional[str] = None, limit: int = 20
                ) -> List[Dict[str, Any]]:
        """Most-recent lessons (and any record) filtered by domain."""
        out: List[Dict[str, Any]] = []
        for rec in reversed(self._records):
            if domain is not None and rec.get("domain") != domain:
                continue
            out.append(rec)
            if len(out) >= limit:
                break
        return out

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total": len(self._records),
                "by_domain": dict(self._domain_counts),
                "decisions_by_status": dict(self._status_counts),
            }

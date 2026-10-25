"""Institutional AI-for-AI Research System.

Wraps the existing research engine into the full EIP/ECIE/CSE-CEDA
loop, one governed call:

    question
      -> fetch (16 keyless source adapters, disk-cached)
      -> EQE score + floor-filter claims
      -> weakness inversion (defensive rules from source flaws)
      -> ingest into KG as THEORETICAL-tier + unvalidated assumptions
      -> engine.investigate(question)  (hypothesis->debate->experiment)
      -> structured report with provenance, no authority

The CSC calls ``ask(question)`` — research output is evidence, never
decision authority. Failed/degraded stages are reported honestly.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from .evidence_quality import filter_documents
from .fetchers import FETCHERS
from .weakness_inversion import invert_documents

logger = logging.getLogger(__name__)

_DEFAULT_SOURCES = ("arxiv", "openalex", "github", "hf_papers")


class InstitutionalResearchSystem:
    """Question -> falsifiable-evidence pipeline for the CSC."""

    def __init__(self, engine: Any = None, sources=None,
                 max_per_source: int = 5,
                 quality_floor: float = None) -> None:
        self.engine = engine          # ResearchEngine; None = fetch-only
        self.sources = list(sources or _DEFAULT_SOURCES)
        self.max_per_source = int(max_per_source)
        self.quality_floor = quality_floor or float(
            os.environ.get("TB_EQE_FLOOR", "0.30"))
        self.questions_asked = 0
        self.reports: List[Dict[str, Any]] = []

    # --------------------------------------------------------------
    def fetch(self, question: str,
              sources=None) -> Dict[str, Any]:
        """Stage 1+2: pull docs from the source adapters and score them
        through the Evidence Quality Engine."""
        docs = []
        per_source = {}
        for name in (sources or self.sources):
            fn = FETCHERS.get(name)
            if not fn:
                per_source[name] = "unknown_fetcher"
                continue
            try:
                got = fn(question, self.max_per_source)
                per_source[name] = len(got)
                docs.extend(got)
            except Exception as e:
                per_source[name] = f"fetch_failed:{type(e).__name__}"
        eqe = filter_documents(docs, floor=self.quality_floor)
        failed = [k for k, v in per_source.items()
                  if isinstance(v, str)]
        silent = [k for k, v in per_source.items() if v == 0]
        return {"documents": docs, "per_source": per_source,
                "sources_failed": failed, "sources_silent": silent,
                "coverage_ok": len(docs) > 0,
                "eqe": {k: eqe[k] for k in
                        ("documents", "claims_total", "claims_kept",
                         "claims_dropped")}}

    def ask(self, question: str, sources=None,
            investigate: bool = True) -> Dict[str, Any]:
        """The full loop. ``investigate=False`` stops after ingestion
        (cheap probe — no hypothesis work)."""
        self.questions_asked += 1
        out: Dict[str, Any] = {
            "question": question,
            "question_id": f"q-{self.questions_asked}",
            "stages": {},
        }

        # fetch + EQE
        try:
            fetched = self.fetch(question, sources)
            out["stages"]["fetch"] = {
                "documents": len(fetched["documents"]),
                "per_source": fetched["per_source"],
                "eqe": fetched["eqe"]}
            docs = fetched["documents"]
        except Exception as e:
            out["stages"]["fetch"] = {"error": str(e)}
            docs = []

        # weakness inversion — every doc's flaws become defensive rules
        try:
            inv = invert_documents(docs) if docs else {"rules_total": 0}
            out["stages"]["weakness_inversion"] = {
                "rules_total": inv["rules_total"],
                "rules": [r["weakness_id"] for r in inv["rules"]]}
        except Exception as e:
            out["stages"]["weakness_inversion"] = {"error": str(e)}

        # contradiction detection — opposite-polarity claims on the
        # same subject get flagged before they land as independent nodes
        try:
            from .evidence_quality import detect_contradictions
            con = detect_contradictions(docs) if docs else []
            out["stages"]["contradictions"] = {
                "pairs": len(con),
                "flags": [c["flag"] for c in con][:10],
                "detail": con[:5]}
        except Exception as e:
            out["stages"]["contradictions"] = {"error": str(e)}

        # ingest -> KG as theoretical-tier claims
        if self.engine is not None and docs:
            try:
                rep = self.engine.ingest_literature(docs)
                out["stages"]["ingest"] = {
                    "documents": rep.get("documents"),
                    "claims": rep.get("claims"),
                    "claim_ids": rep.get("claim_ids", [])[:10]}
            except Exception as e:
                out["stages"]["ingest"] = {"error": str(e)}

        # investigate -> hypothesis/debate/experiment via the engine
        if self.engine is not None and investigate and \
                hasattr(self.engine, "investigate"):
            try:
                import asyncio
                coro = self.engine.investigate(question)
                try:
                    loop = asyncio.get_running_loop()
                    # inside the async pipeline — schedule, don't block
                    # persist the outcome when the task lands — the
                    # report shouldn't lose the investigation result
                    task = asyncio.ensure_future(coro)
                    rep = out  # closure over the live report dict

                    def _stash(t):
                        try:
                            rep["stages"]["investigate"] = {
                                "result": t.result()}
                        except Exception as exc:
                            rep["stages"]["investigate"] = {
                                "error": str(exc)}
                    task.add_done_callback(_stash)
                    out["stages"]["investigate"] = {
                        "scheduled": True,
                        "note": "result stashes back into this report "
                                "when the task lands"}
                except RuntimeError:
                    out["stages"]["investigate"] = asyncio.run(coro) \
                        if asyncio.iscoroutine(coro) else coro
            except Exception as e:
                out["stages"]["investigate"] = {"error": str(e)}

        out["authority"] = "advisory_only"   # research never decides
        self.reports.append(out)
        return out

    def status(self) -> Dict[str, Any]:
        return {"questions_asked": self.questions_asked,
                "reports": len(self.reports),
                "sources": self.sources}

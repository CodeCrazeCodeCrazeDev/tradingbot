"""Evidence Quality Engine — weighted claim scoring BEFORE ingestion.

EIP spec: external claims enter as untrusted intelligence; each is
scored on independent signals so a flashy README can't outrank a
quantified replication. Runs between the fetchers and
``extract_claims``/``ingest_literature`` — claims below the floor are
marked ``dropped_low_quality`` rather than polluting the KG.

Signals (each 0-1, weighted):
  source_prior    — per-source trust prior (peer-reviewed > repo README)
  recency         — exponential decay on published date
  quantified      — claim carries numbers (better than vibes)
  unhedged        — hedged language scores lower, not higher
  declared        — pre-declared claims beat regex-mined heuristics
  corroboration   — same claim appearing across independent sources
"""

from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .sources import ExtractedClaim, SourceDocument

_SOURCE_PRIOR = {
    "arxiv": 0.70, "s2": 0.70, "openalex": 0.70, "crossref": 0.70,
    "pubmed": 0.70, "dblp": 0.70, "openreview": 0.65,
    "hfpaper": 0.65, "edgar": 0.80,   # legal filings
    "zenodo": 0.55, "wikipedia": 0.50,
    "hf": 0.45, "github": 0.40, "hn": 0.30,
}

_WEIGHTS = {
    "source_prior": 0.25, "recency": 0.10, "quantified": 0.20,
    "unhedged": 0.10, "declared": 0.15, "corroboration": 0.20,
}


def _recency(published: str, half_life_days: float = 365.0) -> float:
    if not published:
        return 0.5  # unknown age — neutral, not punished
    try:
        s = str(published)[:19].replace("Z", "")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - dt).days
        return math.exp(-math.log(2) * age / half_life_days)
    except (ValueError, TypeError):
        return 0.5


def _corroboration(claim_text: str, all_claims: List[str],
                   my_source: str = "",
                   claim_sources: Optional[List[str]] = None) -> float:
    """Cheap cross-source corroboration: shared content words with any
    other claim. Real corroboration needs embeddings — this counts
    non-trivial token overlap as a bounded proxy."""
    toks = {t for t in re.findall(r"[a-z]{5,}", claim_text.lower())}
    if not toks:
        return 0.0
    best = 0.0
    for i, other in enumerate(all_claims):
        if other is claim_text:
            continue
        # source-identity dedup: a repo quoting its own abstract is
        # NOT independent corroboration
        if claim_sources is not None and i < len(claim_sources)                 and claim_sources[i] == my_source and my_source:
            continue
        ot = {t for t in re.findall(r"[a-z]{5,}", other.lower())}
        if not ot:
            continue
        j = len(toks & ot) / max(1, len(toks | ot))
        best = max(best, j)
    return min(1.0, best * 3.0)  # scale: j~0.33 -> ~1.0


def score_claim(doc: SourceDocument, claim: ExtractedClaim,
                all_claims: List[str],
                claim_sources: Optional[List[str]] = None) -> Dict[str, Any]:
    """Weighted quality score for one claim. Returns score + per-signal
    breakdown for audit."""
    src = doc.source_id.split(":", 1)[0]
    # retraction/correction check: a retracted source scores 0
    # regardless of every other signal — the cache can't see
    # corrections, so the text itself must carry the signal
    blob = f"{doc.title} {doc.text[:400]}".lower()
    # Gate on retraction-specific PHRASES, not the bare word —
    # "we retract our earlier assumption" is methodology, not a
    # retraction notice.
    if re.search(r"(has been|this (article|paper|work) (was|is|has"
                 r" been))\s+retract|retraction notice|"
                 r"withdrawn from|notice of retraction|"
                 r"erratum|corrigendum", blob):
        return {"score": 0.0, "signals": {"retracted": 1.0},
                "extraction": claim.extraction,
                "note": "retraction_or_correction_detected"}
    sig = {
        "source_prior": _SOURCE_PRIOR.get(src, 0.35),
        "recency": _recency(doc.published),
        "quantified": 1.0 if claim.quantified else 0.0,
        "unhedged": 0.0 if claim.hedged else 1.0,
        "declared": 1.0 if claim.extraction == "declared" else 0.0,
        "corroboration": _corroboration(
            claim.text, all_claims,
            my_source=doc.source_id.split(":", 1)[0],
            claim_sources=claim_sources),
    }
    score = sum(_WEIGHTS[k] * sig[k] for k in _WEIGHTS)
    # Negation parses are the least reliable signal — discount them.
    if claim.polarity == "negative":
        score *= 0.85
    return {"score": round(score, 4), "signals": sig,
            "extraction": claim.extraction}


def filter_documents(docs: List[SourceDocument],
                     floor: float = 0.30) -> Dict[str, Any]:
    """Score every extractable claim in the batch; return the filtered
    docs plus a quality report. Drops claims below ``floor`` from the
    text passed downstream (docs' text is not mutated — the report
    lists what would be dropped)."""
    from .sources import extract_claims
    report: List[Dict[str, Any]] = []
    all_texts: List[str] = []
    claims_per_doc = []
    for d in docs:
        cs = extract_claims(d)
        claims_per_doc.append(cs)
        all_texts.extend(c.text for c in cs)
    claim_sources = [d.source_id.split(":", 1)[0]
                     for d, cs in zip(docs, claims_per_doc)
                     for _ in cs]
    for d, cs in zip(docs, claims_per_doc):
        scored = [score_claim(d, c, all_texts,
                              claim_sources=claim_sources)
                  for c in cs]
        kept = [c for c, s in zip(cs, scored) if s["score"] >= floor]
        report.append({
            "source_id": d.source_id,
            "claims_total": len(cs),
            "claims_kept": len(kept),
            "claims_dropped": len(cs) - len(kept),
            "top_score": max((s["score"] for s in scored), default=0.0),
        })
    # Calibration ledger: every keep/drop decision is journaled so a
    # later calibration pass can compare kept-claim outcomes against
    # dropped-claim outcomes. The floor stays seeded at 0.30 until
    # KG verdict history exists to measure it against.
    try:
        led = os.environ.get("TB_EQE_LEDGER",
                             "var/research_cache/eqe_ledger.jsonl")
        os.makedirs(os.path.dirname(led), exist_ok=True)
        with open(led, "a", encoding="utf-8") as fh:
            for d, cs in zip(docs, claims_per_doc):
                for c in cs:
                    s_ = score_claim(d, c, all_texts)
                    fh.write(json.dumps({
                        "src": d.source_id, "claim": c.text[:80],
                        "score": s_["score"],
                        "kept": s_["score"] >= floor,
                        "polarity": c.polarity,
                        "validated": None}) + "\n")
    except Exception:
        pass  # journaling must never break the fetch path
    return {
        "documents": len(docs),
        "claims_total": sum(r["claims_total"] for r in report),
        "claims_kept": sum(r["claims_kept"] for r in report),
        "claims_dropped": sum(r["claims_dropped"] for r in report),
        "floor": floor,
        "per_doc": report,
    }


def detect_contradictions(docs: List[SourceDocument],
                          min_overlap: float = 0.30) -> List[Dict[str, Any]]:
    """Cross-source contradiction detector. Two claims about the same
    subject with OPPOSITE polarity are a contradiction — the KG should
    link them as conflict edges rather than independent nodes.
    Polarity comes from extract_claims (negation-aware); overlap is
    token-Jaccard on content words."""
    from .sources import extract_claims
    claims = []  # (doc_id, claim)
    for d in docs:
        for c in extract_claims(d):
            claims.append((d.source_id, c))
    pairs = []
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            (da, ca), (db, cb) = claims[i], claims[j]
            if ca.polarity == cb.polarity:
                continue                       # same polarity: no conflict
            ta = set(re.findall(r"[a-z]{5,}", ca.text.lower()))
            tb = set(re.findall(r"[a-z]{5,}", cb.text.lower()))
            if not ta or not tb:
                continue
            j_ = len(ta & tb) / max(1, len(ta | tb))
            if j_ < min_overlap:
                continue                       # different subject
            pairs.append({
                "a": {"source_id": da, "polarity": ca.polarity,
                      "text": ca.text[:120]},
                "b": {"source_id": db, "polarity": cb.polarity,
                      "text": cb.text[:120]},
                "overlap": round(j_, 3),
                "flag": "literature_conflict",
            })
    return pairs

def calibrate_floor(verdicts_by_claim: dict = None,
                    ledger_path: str = None) -> dict:
    """Close the loop: given KG verdicts keyed by claim text prefix,
    pick the floor that maximizes validated-claim recall at fixed
    false-positive budget. Returns the calibrated floor + evidence —
    seed stays 0.30 when history is too thin to measure."""
    led = ledger_path or os.environ.get(
        "TB_EQE_LEDGER", "var/research_cache/eqe_ledger.jsonl")
    rows = []
    try:
        for line in open(led, encoding="utf-8"):
            rows.append(json.loads(line))
    except OSError:
        return {"floor": 0.30, "evidence": "no_ledger"}
    if verdicts_by_claim:
        for r in rows:
            key = r["claim"][:80]
            if key in verdicts_by_claim:
                r["validated"] = bool(verdicts_by_claim[key])
    measured = [r for r in rows if r["validated"] is not None]
    if len(measured) < 20:
        return {"floor": 0.30, "evidence": "insufficient_history",
                "measured": len(measured), "journaled": len(rows)}
    # walk the candidate floors; pick the one keeping >=90% of
    # validated claims while minimizing kept-unvalidated
    best = {"floor": 0.30, "recall": 0.0, "precision": 0.0}
    for cand in (x / 20 for x in range(2, 15)):
        kept = [r for r in measured if r["score"] >= cand]
        val = sum(1 for r in kept if r["validated"])
        tot = sum(1 for r in measured if r["validated"]) or 1
        recall = val / tot
        prec = val / max(1, len(kept))
        if recall >= 0.9 and prec > best["precision"]:
            best = {"floor": cand, "recall": recall,
                    "precision": prec}
    best["evidence"] = "calibrated"
    best["measured"] = len(measured)
    return best

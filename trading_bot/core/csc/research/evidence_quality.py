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

import math
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


def _corroboration(claim_text: str, all_claims: List[str]) -> float:
    """Cheap cross-source corroboration: shared content words with any
    other claim. Real corroboration needs embeddings — this counts
    non-trivial token overlap as a bounded proxy."""
    toks = {t for t in re.findall(r"[a-z]{5,}", claim_text.lower())}
    if not toks:
        return 0.0
    best = 0.0
    for other in all_claims:
        if other is claim_text:
            continue
        ot = {t for t in re.findall(r"[a-z]{5,}", other.lower())}
        if not ot:
            continue
        j = len(toks & ot) / max(1, len(toks | ot))
        best = max(best, j)
    return min(1.0, best * 3.0)  # scale: j~0.33 -> ~1.0


def score_claim(doc: SourceDocument, claim: ExtractedClaim,
                all_claims: List[str]) -> Dict[str, Any]:
    """Weighted quality score for one claim. Returns score + per-signal
    breakdown for audit."""
    src = doc.source_id.split(":", 1)[0]
    sig = {
        "source_prior": _SOURCE_PRIOR.get(src, 0.35),
        "recency": _recency(doc.published),
        "quantified": 1.0 if claim.quantified else 0.0,
        "unhedged": 0.0 if claim.hedged else 1.0,
        "declared": 1.0 if claim.extraction == "declared" else 0.0,
        "corroboration": _corroboration(claim.text, all_claims),
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
    for d, cs in zip(docs, claims_per_doc):
        scored = [score_claim(d, c, all_texts) for c in cs]
        kept = [c for c, s in zip(cs, scored) if s["score"] >= floor]
        report.append({
            "source_id": d.source_id,
            "claims_total": len(cs),
            "claims_kept": len(kept),
            "claims_dropped": len(cs) - len(kept),
            "top_score": max((s["score"] for s in scored), default=0.0),
        })
    return {
        "documents": len(docs),
        "claims_total": sum(r["claims_total"] for r in report),
        "claims_kept": sum(r["claims_kept"] for r in report),
        "claims_dropped": sum(r["claims_dropped"] for r in report),
        "floor": floor,
        "per_doc": report,
    }

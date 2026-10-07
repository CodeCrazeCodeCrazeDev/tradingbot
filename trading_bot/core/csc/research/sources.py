"""External-source ingestion — claim-centric literature research.

The system asks "what exact claim does this source establish?", not "what
does it say?". Ingested documents are decomposed into claims; each claim
enters the knowledge graph at THEORETICAL tier — an external assertion is
untested until the internal pipeline reproduces it, so external claims are
never silently promoted to measured evidence.

Extraction is deliberately honest about its limits: without an LLM the
extractor is heuristic (causal/comparative sentence patterns +
quantification detection) and every extracted claim is labelled
``extraction="heuristic"`` with low confidence. Structured documents that
already declare ``claims: [...]`` are trusted as stated — extraction
label ``"declared"`` — but still enter at THEORETICAL tier.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from trading_bot.core.governance.determinism import determinism as _determinism

from .state import EvidenceTier, UncertaintyMap
from .graph import KnowledgeGraph, KGNode

# Claim-shaped sentence patterns: causal or comparative assertions with
# measurable or directional content. Hedged or unquantified sentences are
# extracted at lower confidence.
_CAUSAL = re.compile(
    r"\b(improves?|increases?|reduces?|decreases?|causes?|prevents?|"
    r"outperforms?|underperforms?|predicts?|correlates?|leads? to|"
    r"results? in|associated with)\b", re.I)
_QUANTIFIED = re.compile(
    r"([+-]?\d+(?:\.\d+)?\s*(?:%|bps|bp|basis points|x|fold|percent))"
    r"|p\s*[<≤]\s*0?\.\d+", re.I)
_HEDGED = re.compile(
    r"\b(may|might|could|suggests?|appears?|possibly|tends? to)\b", re.I)
# Negation cues — a causal verb inside negation scope flips the claim's
# polarity. "does not improve" extracted as positive would be a silent
# inversion of the source's actual claim.
_NEGATED = re.compile(
    r"\b(no|not|n't|never|neither|nor|without|lacks?|lacked|fails? to|"
    r"failed to|does not|did not|do not|cannot|ineffective|insufficient|"
    r"little (?:evidence|effect|support)|no (?:evidence|effect|significant)"
    r")\b", re.I)


@dataclass
class SourceDocument:
    """One external source — a paper abstract, a note, a structured record."""
    source_id: str
    title: str
    text: str = ""
    claims: List[str] = field(default_factory=list)  # pre-declared claims
    author: str = ""
    published: str = ""
    url: str = ""


@dataclass
class ExtractedClaim:
    text: str
    extraction: str          # declared | heuristic
    confidence: float
    quantified: bool
    hedged: bool
    polarity: str = "positive"   # positive | negative


# Correlative constructions that LOOK like negation but assert — "not
# only does X improve Y" is emphatic agreement, not a denial.
_CORRELATIVE = re.compile(r"\bnot (?:only|just|merely)\b", re.I)


def _detect_polarity(sentence: str, causal_match) -> str:
    """Negation within ~40 chars before the causal verb flips polarity.
    An odd number of negation cues negates the claim; correlative
    'not only/just/merely' is stripped first — it asserts rather than
    negates. Residual ambiguity lowers confidence downstream."""
    window = sentence[max(0, causal_match.start() - 40):
                      causal_match.end()]
    window = _CORRELATIVE.sub(" ", window)
    cues = len(_NEGATED.findall(window))
    return "negative" if cues % 2 == 1 else "positive"


def extract_claims(doc: SourceDocument) -> List[ExtractedClaim]:
    """Claim extraction: declared claims pass through labelled; raw text is
    mined for causal/comparative sentences. Everything is marked by how it
    was obtained — the label is part of the evidence."""
    out: List[ExtractedClaim] = []
    for claim in doc.claims or []:
        m = _CAUSAL.search(claim)
        out.append(ExtractedClaim(
            text=str(claim), extraction="declared",
            confidence=0.6, quantified=bool(_QUANTIFIED.search(claim)),
            hedged=bool(_HEDGED.search(claim)),
            polarity=(_detect_polarity(claim, m) if m else "positive")))
    for sent in re.split(r"(?<=[.!?])\s+", doc.text or ""):
        sent = sent.strip()
        if not sent or len(sent) < 25:
            continue
        m = _CAUSAL.search(sent)
        if not m:
            continue
        quantified = bool(_QUANTIFIED.search(sent))
        hedged = bool(_HEDGED.search(sent))
        polarity = _detect_polarity(sent, m)
        conf = 0.15 + (0.15 if quantified else 0.0) - (0.05 if hedged else 0.0)
        if polarity == "negative":
            conf = max(0.05, conf - 0.05)  # negation parses are less reliable
        out.append(ExtractedClaim(
            text=sent[:500], extraction="heuristic",
            confidence=max(0.05, conf), quantified=quantified,
            hedged=hedged, polarity=polarity))
    return out


def load_documents(path: str) -> List[SourceDocument]:
    """Load a directory or file of sources.

    ``.json`` files may carry structured records (title, text/abstract,
    claims[]); ``.txt``/``.md`` become raw-text documents."""
    p = Path(path)
    docs: List[SourceDocument] = []
    files = [p] if p.is_file() else sorted(p.glob("**/*")) if p.is_dir() else []
    for f in files:
        try:
            if f.suffix == ".json":
                recs = json.loads(f.read_text(encoding="utf-8"))
                recs = recs if isinstance(recs, list) else [recs]
                for i, r in enumerate(recs):
                    if not isinstance(r, dict):
                        continue
                    docs.append(SourceDocument(
                        source_id=str(r.get("id") or f"{f.stem}:{i}"),
                        title=str(r.get("title") or f.stem),
                        text=str(r.get("text") or r.get("abstract") or ""),
                        claims=[str(c) for c in r.get("claims") or []],
                        author=str(r.get("author") or ""),
                        published=str(r.get("published") or ""),
                        url=str(r.get("url") or "")))
            elif f.suffix in (".txt", ".md"):
                docs.append(SourceDocument(
                    source_id=f.stem, title=f.stem,
                    text=f.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return docs

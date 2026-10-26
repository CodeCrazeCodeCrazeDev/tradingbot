"""Ten additional keyless research fetchers — same SourceDocument
contract as fetchers.py, all public APIs, failures -> []."""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
from typing import List

from .fetchers import _get
from .sources import SourceDocument

logger = logging.getLogger(__name__)


def _docs(items, source, id_of, title_of, text_of, url_of, date_of=None):
    out: List[SourceDocument] = []
    for it in items:
        try:
            t, x = title_of(it), text_of(it)
            # Crossref/edgar items often carry no abstract/highlight —
            # a title-only document is still evidence (weak, but real)
            if t and not x:
                x = t
            if t and x:
                out.append(SourceDocument(
                    source_id=f"{source}:{id_of(it)}", title=str(t),
                    text=re.sub(r"\s+", " ", str(x))[:6000],
                    url=url_of(it),
                    published=str(date_of(it) or "") if date_of else ""))
        except Exception:
            continue
    return out


def fetch_semantic_scholar(query: str, max_results: int = 10):
    q = urllib.parse.quote(query)
    try:
        d = json.loads(_get(
            "https://api.semanticscholar.org/graph/v1/paper/search"
            f"?query={q}&limit={max_results}"
            "&fields=title,abstract,year,url,paperId"))
    except Exception as e:
        logger.warning("semantic_scholar failed: %s", e)
        return []
    return _docs(d.get("data", [])[:max_results], "s2",
                 lambda p: p.get("paperId", ""),
                 lambda p: p.get("title", ""),
                 lambda p: p.get("abstract") or "",
                 lambda p: p.get("url") or "",
                 lambda p: p.get("year", ""))


def fetch_openalex(query: str, max_results: int = 10):
    q = urllib.parse.quote(query)
    try:
        d = json.loads(_get(
            f"https://api.openalex.org/works?search={q}"
            f"&per-page={max_results}&sort=relevance_score:desc"))
    except Exception as e:
        logger.warning("openalex failed: %s", e)
        return []

    def _abs(w):
        inv = w.get("abstract_inverted_index") or {}
        pos = {i: wd for wd, ii in inv.items() for i in ii}
        return " ".join(pos[i] for i in sorted(pos)) if pos else ""

    return _docs(d.get("results", [])[:max_results], "openalex",
                 lambda w: (w.get("id") or "").rsplit("/", 1)[-1],
                 lambda w: w.get("title") or w.get("display_name") or "",
                 _abs,
                 lambda w: w.get("id") or "",
                 lambda w: w.get("publication_date", ""))


def fetch_crossref(query: str, max_results: int = 10):
    q = urllib.parse.quote(query)
    try:
        d = json.loads(_get(
            f"https://api.crossref.org/works?query={q}&rows={max_results}"
            "&select=DOI,title,abstract,URL,published"))
    except Exception as e:
        logger.warning("crossref failed: %s", e)
        return []
    return _docs(
        d.get("message", {}).get("items", [])[:max_results],
        "crossref",
        lambda w: w.get("DOI", ""),
        lambda w: (w.get("title") or [""])[0],
        lambda w: re.sub(r"<[^>]+>", " ", w.get("abstract") or ""),
        lambda w: w.get("URL") or "",
        lambda w: (w.get("published") or {})
        .get("date-parts", [[""]])[0][0])


def fetch_pubmed(query: str, max_results: int = 10):
    q = urllib.parse.quote(query)
    try:
        ids = json.loads(_get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={q}&retmax={max_results}&retmode=json")
        ).get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        sm = json.loads(_get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            f"?db=pubmed&id={','.join(ids)}&retmode=json"))
    except Exception as e:
        logger.warning("pubmed failed: %s", e)
        return []
    res = sm.get("result", {})
    return _docs([res.get(i, {}) for i in ids], "pubmed",
                 lambda w: w.get("uid", ""),
                 lambda w: w.get("title", ""),
                 lambda w: w.get("description") or w.get("title", ""),
                 lambda w: "https://pubmed.ncbi.nlm.nih.gov/"
                           f"{w.get('uid','')}/",
                 lambda w: w.get("pubdate", ""))


def fetch_dblp(query: str, max_results: int = 10):
    q = urllib.parse.quote(query)
    try:
        d = json.loads(_get(
            f"https://dblp.org/search/publ/api?q={q}"
            f"&h={max_results}&format=json"))
    except Exception as e:
        logger.warning("dblp failed: %s", e)
        return []
    hits = d.get("result", {}).get("hits", {}).get("hit", [])
    return _docs([h.get("info", {}) for h in hits], "dblp",
                 lambda w: w.get("key", "").rsplit("/", 1)[-1],
                 lambda w: w.get("title", ""),
                 lambda w: f"{w.get('title','')}. {w.get('venue','')} "
                           f"{w.get('year','')}",
                 lambda w: w.get("url") or "",
                 lambda w: w.get("year", ""))


def fetch_openreview(query: str, max_results: int = 10):
    q = urllib.parse.quote(query)
    try:
        # api.openreview.net (v1) returns content as plain strings;
        # api2 returns {value: ...} dicts — try v1 first, fall back.
        try:
            d = json.loads(_get(
                f"https://api.openreview.net/notes/search?term={q}"
                f"&limit={max_results}"))
        except Exception:
            d = json.loads(_get(
                f"https://api2.openreview.net/notes/search?term={q}"
                f"&limit={max_results}"))
    except Exception as e:
        logger.warning("openreview failed: %s", e)
        return []

    def _c(n, k):
        v = (n.get("content") or {}).get(k, "")
        return v if isinstance(v, str) else (v or {}).get("value", "")

    return _docs(d.get("notes", [])[:max_results], "openreview",
                 lambda n: n.get("id", ""),
                 lambda n: _c(n, "title"),
                 lambda n: _c(n, "abstract"),
                 lambda n: "https://openreview.net/forum?id="
                           f"{n.get('id','')}")


def fetch_edgar(query: str, max_results: int = 10):
    q = urllib.parse.quote(query)
    try:
        d = json.loads(_get(
            "https://efts.sec.gov/LATEST/search-index"
            f"?q=%22{q}%22&forms=10-K,10-Q,8-K"))
    except Exception as e:
        logger.warning("edgar failed: %s", e)
        return []
    return _docs(
        d.get("hits", {}).get("hits", [])[:max_results], "edgar",
        lambda h: h.get("_id", "")[:40],
        lambda h: (f"{h.get('_source', {}).get('display_names', ['?'])[0]}"
                   f" {h.get('_source', {}).get('form', '')}"),
        lambda h: re.sub(r"<[^>]+>", " ", " ".join(
            h.get("highlight", {}).get("text", [])) or " ".join(
            f"{k}={v}" for k, v in
            h.get("_source", {}).items()
            if k in ("display_names", "form", "file_date",
                     "root_form"))),
        lambda h: ("https://www.sec.gov/cgi-bin/browse-edgar?action="
                   "getcompany&CIK="
                   f"{h.get('_source', {}).get('ciks', [''])[0]}"),
        lambda h: h.get("_source", {}).get("file_date", ""))


def fetch_hackernews(query: str, max_results: int = 10):
    q = urllib.parse.quote(query)
    try:
        d = json.loads(_get(
            f"https://hn.algolia.com/api/v1/search?query={q}"
            f"&tags=(story,comment)&hitsPerPage={max_results}"))
    except Exception as e:
        logger.warning("hackernews failed: %s", e)
        return []
    return _docs(d.get("hits", [])[:max_results], "hn",
                 lambda h: h.get("objectID", ""),
                 lambda h: h.get("title") or
                 f"comment by {h.get('author','')}",
                 lambda h: re.sub(
                     r"<[^>]+>", " ",
                     h.get("story_text") or h.get("comment_text")
                     or h.get("title") or ""),
                 lambda h: "https://news.ycombinator.com/item?id="
                           f"{h.get('objectID','')}",
                 lambda h: h.get("created_at", ""))


def fetch_zenodo(query: str, max_results: int = 10):
    q = urllib.parse.quote(query)
    try:
        d = json.loads(_get(
            f"https://zenodo.org/api/records?q={q}"
            f"&size={max_results}&sort=mostrecent"))
    except Exception as e:
        logger.warning("zenodo failed: %s", e)
        return []
    return _docs(
        d.get("hits", {}).get("hits", [])[:max_results], "zenodo",
        lambda r: str(r.get("id", "")),
        lambda r: (r.get("metadata") or {}).get("title", ""),
        lambda r: re.sub(r"<[^>]+>", " ",
                         (r.get("metadata") or {})
                         .get("description", "")),
        lambda r: (r.get("links") or {}).get("html", ""),
        lambda r: r.get("created", ""))


def fetch_wikipedia(query: str, max_results: int = 10):
    q = urllib.parse.quote(query)
    try:
        sr = json.loads(_get(
            "https://en.wikipedia.org/w/api.php?action=opensearch"
            f"&search={q}&limit={max_results}&namespace=0&format=json"))
        titles = sr[1] if len(sr) > 1 else []
    except Exception as e:
        logger.warning("wikipedia failed: %s", e)
        return []
    docs = []
    for t in titles[:max_results]:
        try:
            s = json.loads(_get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/"
                + urllib.parse.quote(t.replace(" ", "_"))))
            if s.get("extract"):
                docs.append(SourceDocument(
                    source_id=f"wiki:{t.replace(' ', '_')}", title=t,
                    text=s["extract"],
                    url=(s.get("content_urls", {}).get("desktop", {})
                         .get("page", ""))))
        except Exception:
            continue
    return docs


EXTRA_FETCHERS = {
    "semantic_scholar": fetch_semantic_scholar,
    "openalex": fetch_openalex,
    "crossref": fetch_crossref,
    "pubmed": fetch_pubmed,
    "dblp": fetch_dblp,
    "openreview": fetch_openreview,
    "edgar": fetch_edgar,
    "hackernews": fetch_hackernews,
    "zenodo": fetch_zenodo,
    "wikipedia": fetch_wikipedia,
}


def fetch_creator(query: str, max_results: int = 10):
    """Creator Intelligence — keyless dev.to + Reddit JSON. Extracts
    operational/workflow blueprints from creator content rather than
    content copying (EIP adapter #3)."""
    q = urllib.parse.quote(query)
    docs = []
    try:
        # dev.to tags are single-word — a multi-word query 404s the
        # endpoint. Use the first keyword as tag, then client-filter
        # the rest of the query terms against title/description.
        kw = (query.split() or [""])[0]
        arts = json.loads(_get(
            f"https://dev.to/api/articles?tag={urllib.parse.quote(kw)}"
            f"&per_page={max_results * 4}"))
        if not arts:
            arts = json.loads(_get(
                "https://dev.to/api/articles"
                f"?per_page={max_results * 4}&top=14"))
        terms = {t.lower() for t in query.split() if len(t) > 3}
        scored = []
        for a in arts:
            hay = f"{a.get('title','')} {a.get('description','')}".lower()
            scored.append((len(terms & set(hay.split())), a))
        scored.sort(key=lambda x: -x[0])
        for _, a in scored[:max_results]:
            t = a.get("title", "")
            x = a.get("description") or " ".join(
                a.get("tag_list", []))
            if t and x:
                docs.append(SourceDocument(
                    source_id=f"creator:devto:{a.get('id','')}",
                    title=t, text=f"{t}. {x}",
                    author=(a.get("user") or {}).get("name", ""),
                    published=a.get("published_at", ""),
                    url=a.get("url", "")))
    except Exception as e:
        logger.warning("creator devto failed: %s", e)
    try:
        rd = json.loads(_get(
            f"https://www.reddit.com/search.json?q={q}"
            f"&limit={max_results}&sort=relevance&t=year"))
        for c in rd.get("data", {}).get("children", [])[:max_results]:
            d = c.get("data", {})
            t = d.get("title", "")
            x = d.get("selftext") or d.get("title", "")
            if t and x:
                docs.append(SourceDocument(
                    source_id=f"creator:reddit:{d.get('id','')}",
                    title=t, text=x[:6000],
                    author=d.get("author", ""),
                    published=str(d.get("created_utc", "")),
                    url="https://reddit.com" + d.get("permalink", "")))
    except Exception as e:
        logger.warning("creator reddit failed: %s", e)
    return docs


def fetch_frontier_models(query: str, max_results: int = 10):
    """Frontier Model observation (EIP adapter #4) — keyless HF model
    metadata. 'Reverse engineers' capability patterns from public
    card fields: params, pipeline_tag, license, downloads, tags —
    never weights. A 7B 'trading' model card reveals its pattern
    without the weights."""
    q = urllib.parse.quote(query)
    try:
        items = json.loads(_get(
            "https://huggingface.co/api/models?search="
            f"{q}&sort=downloads&direction=-1&limit={max_results}"
            "&full=true"))
    except Exception as e:
        logger.warning("frontier_models failed: %s", e)
        return []
    docs = []
    for it in items[:max_results]:
        mid = it.get("id") or it.get("modelId") or ""
        if not mid:
            continue
        tags = it.get("tags", [])
        cfg = it.get("config", {}) or {}
        # Capability pattern: what the metadata reveals about the arch
        pattern = {
            "pipeline_tag": it.get("pipeline_tag"),
            "params_b": (cfg.get("num_parameters") or 0) / 1e9
            if isinstance(cfg.get("num_parameters"), (int, float))
            else None,
            "license": next((t for t in tags if t.startswith("license:")),
                            None),
            "library": it.get("library_name"),
            "downloads": it.get("downloads"),
        }
        text = (f"Model {mid} pattern: "
                + "; ".join(f"{k}={v}" for k, v in pattern.items()
                            if v is not None)
                + "; tags: " + " ".join(tags[:12]))
        docs.append(SourceDocument(
            source_id=f"frontier:{mid}", title=f"{mid} (frontier obs)",
            text=text, published=it.get("lastModified", ""),
            url=f"https://huggingface.co/{mid}"))
    return docs


EXTRA_FETCHERS.update({
    "creator": fetch_creator,
    "frontier_models": fetch_frontier_models,
})

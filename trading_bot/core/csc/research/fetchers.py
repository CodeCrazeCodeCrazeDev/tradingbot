"""Live research-source fetchers — arXiv, GitHub, HuggingFace.

Each returns SourceDocument objects ready for
ResearchEngine.ingest_literature. All three APIs are public and
keyless; failures degrade to an empty list, never an exception into
the pipeline. Rate-friendly: small result counts, real User-Agent.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from typing import List
from xml.etree import ElementTree as ET

from .sources import SourceDocument

logger = logging.getLogger(__name__)
_UA = {"User-Agent": "trading-bot-research/1.0"}
_TIMEOUT = 30

_NS = {"a": "http://www.w3.org/2005/Atom"}


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
        return r.read()


def fetch_arxiv(query: str, max_results: int = 10
                ) -> List[SourceDocument]:
    """arXiv Atom search -> paper abstracts as documents."""
    q = urllib.parse.quote(query)
    url = ("http://export.arxiv.org/api/query?search_query=all:"
           f"{q}&start=0&max_results={max_results}"
           "&sortBy=submittedDate&sortOrder=descending")
    try:
        root = ET.fromstring(_get(url))
    except Exception as e:
        logger.warning("arxiv fetch failed: %s", e)
        return []
    docs = []
    for e in root.findall("a:entry", _NS):
        try:
            title = (e.findtext("a:title", "", _NS) or "").strip()
            abstract = re.sub(
                r"\s+", " ",
                (e.findtext("a:summary", "", _NS) or "")).strip()
            link = e.findtext("a:id", "", _NS) or ""
            pub = e.findtext("a:published", "", _NS) or ""
            authors = ", ".join(
                (a.findtext("a:name", "", _NS) or "")
                for a in e.findall("a:author", _NS))[:200]
            if title and abstract:
                docs.append(SourceDocument(
                    source_id=f"arxiv:{link.rsplit('/', 1)[-1]}",
                    title=title, text=abstract, author=authors,
                    published=pub, url=link))
        except Exception:
            continue
    return docs


def fetch_github(query: str, max_results: int = 10
                 ) -> List[SourceDocument]:
    """GitHub repo search -> repo READMEs as documents."""
    q = urllib.parse.quote(query)
    url = ("https://api.github.com/search/repositories?q="
           f"{q}&sort=updated&order=desc&per_page={max_results}")
    try:
        data = json.loads(_get(url))
    except Exception as e:
        logger.warning("github fetch failed: %s", e)
        return []
    docs = []
    for item in data.get("items", [])[:max_results]:
        try:
            full = item["full_name"]
            desc = item.get("description") or ""
            # README carries the real claims; description alone is thin.
            readme = ""
            try:
                rd = json.loads(_get(
                    f"https://api.github.com/repos/{full}/readme"))
                dl = rd.get("download_url")
                if dl:
                    readme = _get(dl).decode(
                        "utf-8", "replace")[:6000]
            except Exception:
                readme = desc
            text = readme or desc
            if text:
                docs.append(SourceDocument(
                    source_id=f"github:{full}",
                    title=f"{full} — {desc}",
                    text=text,
                    author=item.get("owner", {}).get("login", ""),
                    published=item.get("updated_at", ""),
                    url=item.get("html_url", "")))
        except Exception:
            continue
    return docs


def fetch_huggingface(query: str, max_results: int = 10
                      ) -> List[SourceDocument]:
    """HuggingFace model search -> model cards metadata as docs."""
    q = urllib.parse.quote(query)
    url = ("https://huggingface.co/api/models?search="
           f"{q}&sort=lastModified&direction=-1&limit={max_results}")
    try:
        items = json.loads(_get(url))
    except Exception as e:
        logger.warning("huggingface fetch failed: %s", e)
        return []
    docs = []
    for it in items[:max_results]:
        try:
            mid = it.get("id") or it.get("modelId") or ""
            if not mid:
                continue
            card = ""
            try:
                card = _get(
                    f"https://huggingface.co/{mid}/raw/main/README.md"
                    ).decode("utf-8", "replace")[:6000]
            except Exception:
                card = " ".join(str(t) for t in it.get("tags", []))
            text = card or " ".join(str(t) for t in it.get("tags", []))
            if text:
                docs.append(SourceDocument(
                    source_id=f"hf:{mid}",
                    title=f"{mid} (HF model)",
                    text=text,
                    author=mid.split("/")[0] if "/" in mid else "",
                    published=it.get("lastModified", ""),
                    url=f"https://huggingface.co/{mid}"))
        except Exception:
            continue
    return docs


def fetch_huggingface_papers(max_results: int = 10
                             ) -> List[SourceDocument]:
    """HF daily-papers feed -> paper titles+abstracts as docs."""
    try:
        items = json.loads(_get(
            "https://huggingface.co/api/daily_papers?limit="
            f"{max_results}"))
    except Exception as e:
        logger.warning("hf papers fetch failed: %s", e)
        return []
    docs = []
    for it in items[:max_results]:
        p = it.get("paper", {}) if isinstance(it, dict) else {}
        title = p.get("title", "")
        abstract = p.get("summary") or p.get("abstract") or ""
        pid = p.get("id", "")
        if title and abstract:
            docs.append(SourceDocument(
                source_id=f"hfpaper:{pid}", title=title,
                text=re.sub(r"\s+", " ", abstract),
                author=", ".join(
                    (a.get("name") or "") for a in
                    (p.get("authors") or [])[:5])[:200],
                published=p.get("publishedAt", ""),
                url=f"https://huggingface.co/papers/{pid}"))
    return docs


FETCHERS = {
    "arxiv": fetch_arxiv,
    "github": fetch_github,
    "huggingface": fetch_huggingface,
    "hf_papers": lambda q, n=10: fetch_huggingface_papers(n),
}

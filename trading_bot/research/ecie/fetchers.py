"""Real external-source fetchers for the ECIE pipeline.

Each function produces ExternalCandidate objects populated with REAL
data — readme text, code samples, license, commit recency — so the
pipeline's trust/license/security/distill gates operate on genuine
artifacts instead of the simulated fixtures in scouts.py.

Uses urllib (OS resolver) rather than aiohttp: on hosts where aiodns's
c-ares resolver cannot reach DNS, urllib still works.

All fetches are bounded: per-request timeouts, byte caps, and capped
candidate counts. Failures return empty lists — callers record the
shortfall honestly rather than fabricating candidates.
"""

from __future__ import annotations

import base64
import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from .models import ExternalCandidate, SourceType

logger = logging.getLogger("AlphaAlgo.ECIE.Fetchers")

_UA = {"User-Agent": "AlphaAlgo-ECIE/1.0 (gated research scout)"}
_TIMEOUT = 15
_MAX_TEXT = 8000        # bytes per fetched text artifact
_MAX_CODE_SAMPLES = 3   # files per repo scanned for code samples


def _get(url: str, *, max_bytes: int = _MAX_TEXT,
         timeout: int = _TIMEOUT) -> Optional[bytes]:
    """Bounded HTTP GET. Returns raw bytes or None on any failure."""
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(max_bytes)
    except Exception as exc:  # noqa: BLE001 — any fetch failure is a miss
        logger.debug("fetch failed %s: %s", url[:90], str(exc)[:90])
        return None


def _get_json(url: str) -> Optional[Any]:
    raw = _get(url, max_bytes=2_000_000)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8", "replace"))
    except (ValueError, UnicodeDecodeError):
        return None


def _get_text(url: str) -> str:
    raw = _get(url)
    return raw.decode("utf-8", "replace") if raw else ""


# --------------------------------------------------------------------------
# GitHub — real repo search + README/license/code-sample fetch
# --------------------------------------------------------------------------

def _github_readme(full_name: str) -> str:
    """README via the API (base64) — works regardless of default branch."""
    data = _get_json(
        f"https://api.github.com/repos/{full_name}/readme")
    if isinstance(data, dict) and data.get("content"):
        try:
            return base64.b64decode(data["content"]).decode(
                "utf-8", "replace")[:_MAX_TEXT]
        except Exception:  # noqa: BLE001
            pass
    return ""


def _github_tree_flags(full_name: str,
                       ) -> Dict[str, Any]:
    """One tree listing → has_tests / has_docs / python file paths."""
    data = _get_json(
        f"https://api.github.com/repos/{full_name}/git/trees/HEAD"
        f"?recursive=1")
    flags: Dict[str, Any] = {"has_tests": False, "has_docs": False,
                             "py_files": []}
    if not isinstance(data, dict):
        return flags
    for item in data.get("tree", [])[:5000]:
        path = (item.get("path") or "").lower()
        if item.get("type") != "blob":
            continue
        if re.search(r"(^|/)(tests?|testing)/", path) or \
                re.search(r"test_.*\.py$|_test\.py$", path):
            flags["has_tests"] = True
        if re.search(r"(^|/)(docs?|documentation)/", path) or \
                path.endswith((".md", ".rst")):
            flags["has_docs"] = True
        if path.endswith(".py") and not path.startswith(("test", ".")):
            flags["py_files"].append(item["path"])
    flags["py_files"] = flags["py_files"][:_MAX_CODE_SAMPLES]
    return flags


def _github_code_samples(full_name: str, branch: str,
                         paths: List[str]) -> List[str]:
    samples = []
    for path in paths[:_MAX_CODE_SAMPLES]:
        url = (f"https://raw.githubusercontent.com/{full_name}/{branch}/"
               + urllib.parse.quote(path))
        text = _get_text(url)
        if text:
            samples.append(text)
    return samples


def fetch_github_candidates(query: str, max_results: int = 5,
                            ) -> List[ExternalCandidate]:
    """Real GitHub search → per-repo README, license, tree flags,
    and bounded real code samples."""
    q = urllib.parse.urlencode({
        "q": query, "sort": "stars", "order": "desc",
        "per_page": str(max_results)})
    data = _get_json(f"https://api.github.com/search/repositories?{q}")
    items = (data or {}).get("items") or []
    candidates: List[ExternalCandidate] = []
    for item in items[:max_results]:
        full = item.get("full_name", "")
        branch = item.get("default_branch", "main")
        readme = _github_readme(full)
        flags = _github_tree_flags(full)
        samples = _github_code_samples(full, branch, flags["py_files"])
        lic = (item.get("license") or {}).get("spdx_id") or "Unknown"
        if lic == "NOASSERTION":
            lic = "Unknown"
        candidates.append(ExternalCandidate(
            source_type=SourceType.GITHUB,
            name=full,
            url=item.get("html_url", ""),
            version_id=item.get("default_branch", "main"),
            author=full.split("/")[0] if "/" in full else full,
            description=item.get("description") or "",
            readme_content=readme,
            license_name=lic,
            stars=item.get("stargazers_count", 0),
            forks=item.get("forks_count", 0),
            metadata={
                "has_tests": flags["has_tests"],
                "has_docs": flags["has_docs"] or bool(readme),
                "pushed_at": item.get("pushed_at", ""),
                "code_samples": samples,
                "language": item.get("language", ""),
                "open_issues": item.get("open_issues_count", 0),
            }))
        logger.info("github candidate: %s (stars=%d, samples=%d)",
                    full, item.get("stargazers_count", 0), len(samples))
    return candidates


# --------------------------------------------------------------------------
# arXiv — real API search → abstract becomes the "readme"
# --------------------------------------------------------------------------

def fetch_arxiv_candidates(query: str, max_results: int = 5,
                           ) -> List[ExternalCandidate]:
    """Real arXiv API search. Papers carry no code — code_samples stays
    empty and the abstract feeds classification instead."""
    # Same query shape InternetResearcher uses — all:<terms> with
    # spaces (arXiv implicit-ANDs them). A quoted phrase stalls the
    # export API past any reasonable timeout.
    q = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": "0", "max_results": str(max_results),
        "sortBy": "relevance", "sortOrder": "descending"})
    raw = _get(f"https://export.arxiv.org/api/query?{q}",
               max_bytes=500_000, timeout=45)
    if raw is None:
        return []
    xml = raw.decode("utf-8", "replace")
    candidates: List[ExternalCandidate] = []
    for entry in re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL):
        title = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        summary = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        pid = re.search(r"<id>(.*?)</id>", entry)
        authors = re.findall(r"<name>(.*?)</name>", entry)
        published = re.search(r"<published>(.*?)</published>", entry)
        if not (title and summary):
            continue
        ver = "v1"
        if pid:
            m = re.search(r"(v\d+)$", pid.group(1))
            if m:
                ver = m.group(1)
        candidates.append(ExternalCandidate(
            source_type=SourceType.ARXIV,
            name=(title.group(1).strip().replace("\n", " "))[:120],
            url=pid.group(1).strip() if pid else "",
            version_id=ver,
            author=", ".join(authors[:3]),
            description=(summary.group(1).strip()
                         .replace("\n", " "))[:400],
            readme_content=(summary.group(1).strip()
                            .replace("\n", " ")),
            license_name="arXiv (non-exclusive)",
            stars=0, forks=0,
            metadata={
                "has_tests": False,
                "has_docs": True,
                "pushed_at": (published.group(1) if published else ""),
                "code_samples": [],
            }))
    logger.info("arxiv candidates: %d", len(candidates))
    return candidates[:max_results]


# --------------------------------------------------------------------------
# HuggingFace — real model search + model-card fetch (no weights pulled)
# --------------------------------------------------------------------------

def fetch_hf_candidates(query: str, max_results: int = 5,
                        ) -> List[ExternalCandidate]:
    """Real HF model search → model card text as readme. Weights are
    never downloaded — the card is metadata, gated like everything
    else."""
    q = urllib.parse.urlencode({
        "search": query, "limit": str(max_results),
        "sort": "downloads", "direction": "-1"})
    data = _get_json(f"https://huggingface.co/api/models?{q}")
    if not isinstance(data, list):
        return []
    candidates: List[ExternalCandidate] = []
    for item in data[:max_results]:
        mid = item.get("id", "")
        card = _get_text(
            f"https://huggingface.co/{mid}/raw/main/README.md")
        lic = "Unknown"
        for tag in item.get("tags", []) or []:
            if str(tag).startswith("license:"):
                lic = str(tag).split(":", 1)[1]
        candidates.append(ExternalCandidate(
            source_type=SourceType.HUGGING_FACE,
            name=mid,
            url=f"https://huggingface.co/{mid}",
            version_id=item.get("sha", "")[:12] or "main",
            author=mid.split("/")[0] if "/" in mid else mid,
            description=card[:400],
            readme_content=card,
            license_name=lic,
            stars=item.get("likes", 0),
            forks=item.get("downloads", 0) // 100,
            metadata={
                "has_tests": False,
                "has_docs": bool(card),
                "pushed_at": item.get("lastModified", ""),
                "code_samples": [],
                "pipeline_tag": item.get("pipeline_tag", ""),
                "downloads": item.get("downloads", 0),
            }))
        logger.info("hf candidate: %s (likes=%s, card=%d bytes)",
                    mid, item.get("likes"), len(card))
    return candidates


FETCHERS = {
    "github": fetch_github_candidates,
    "arxiv": fetch_arxiv_candidates,
    "hf": fetch_hf_candidates,
}

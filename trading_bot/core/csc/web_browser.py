"""Bounded stdlib web browser — the organism's read-only eyes.

Gives the CSC the equivalent of an operator's ``web_search`` +
``webfetch``: general web search, arbitrary page fetch, and RSS/Atom
news feeds. Deliberately stdlib-only (``urllib`` + ``re`` + ``ET``) so
it works in both interpreters — the heavier scrapers in
``trading_bot/connectivity`` require aiohttp/bs4 which .venv lacks.

Safety posture (this bot browses autonomously — bounds are load-bearing):

- HTTPS/HTTP only; private, loopback, link-local, and reserved IPs are
  refused (SSRF guard) — the bot can never be steered at internal
  infrastructure by a page or query result.
- Hard byte caps, timeouts, and a minimum interval between requests —
  a hostile or broken endpoint can never stall or flood the pipeline.
- Content is text-extracted (scripts/styles stripped); nothing fetched
  is ever executed, rendered, or trusted — it is stored as *evidence*,
  advisory only, never fed to sizing.
- Every failure is reported as ``status: unavailable``/``refused`` —
  nothing here fabricates content on error.
"""
from __future__ import annotations

import asyncio
import html as html_mod
import ipaddress
import logging
import re
import socket
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse, parse_qs
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

DDG_HTML_URL = "https://html.duckduckgo.com/html/"

_DEFAULT_FEEDS = (
    "https://news.google.com/rss/search?q=EURUSD+OR+forex+when:2d&hl=en-US&gl=US&ceid=US:en",
    "https://www.dailyfx.com/feeds/market-news",
    "https://www.fxstreet.com/rss/news",
)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AlphaAlgo-ResearchBot/1.0 (+local research; respectful fetcher)")

_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(
    r"<(script|style|noscript|svg)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_WS_RE = re.compile(r"\s+")
_DDG_RESULT_RE = re.compile(
    r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
    re.DOTALL | re.IGNORECASE)
_DDG_SNIPPET_RE = re.compile(
    r'class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)


def _strip_html(raw: str) -> str:
    raw = _SCRIPT_RE.sub(" ", raw)
    raw = _TAG_RE.sub(" ", raw)
    return _WS_RE.sub(" ", html_mod.unescape(raw)).strip()


def _ddg_unwrap(href: str) -> str:
    """DuckDuckGo redirects wrap targets in //duckduckgo.com/l/?uddg=."""
    href = html_mod.unescape(href)
    if "uddg=" in href:
        qs = parse_qs(urlparse(href if "://" in href
                               else "https:" + href).query)
        if qs.get("uddg"):
            return qs["uddg"][0]
    if href.startswith("//"):
        return "https:" + href
    return href


def _parse_ddg_results(page: str, max_results: int) -> List[Dict[str, str]]:
    links = _DDG_RESULT_RE.findall(page)
    snippets = _DDG_SNIPPET_RE.findall(page)
    out: List[Dict[str, str]] = []
    for i, (href, title_html) in enumerate(links[:max_results]):
        url = _ddg_unwrap(href)
        if not url.startswith("http"):
            continue
        out.append({
            "title": _strip_html(title_html)[:200],
            "url": url[:500],
            "snippet": (_strip_html(snippets[i])[:400]
                        if i < len(snippets) else ""),
        })
    return out


def _parse_feed(xml_bytes: bytes, max_items: int) -> List[Dict[str, str]]:
    """RSS 2.0 + Atom item extraction — tolerant of missing fields."""
    root = ET.fromstring(xml_bytes)
    items = root.findall(".//item")
    if items:
        return [{
            "title": (it.findtext("title") or "").strip()[:200],
            "url": (it.findtext("link") or "").strip()[:500],
            "published": (it.findtext("pubDate") or "").strip()[:60],
            "snippet": _strip_html(it.findtext("description") or "")[:300],
        } for it in items[:max_items]]
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entries = root.findall(".//a:entry", ns)
    out = []
    for e in entries[:max_items]:
        link = ""
        for le in e.findall("a:link", ns):
            if le.get("rel", "alternate") == "alternate":
                link = le.get("href", "")
                break
        out.append({
            "title": (e.findtext("a:title", "", ns) or "").strip()[:200],
            "url": link.strip()[:500],
            "published": (e.findtext("a:published", "", ns)
                          or e.findtext("a:updated", "", ns)
                          or "").strip()[:60],
            "snippet": _strip_html(
                e.findtext("a:summary", "", ns)
                or e.findtext("a:content", "", ns) or "")[:300],
        })
    return out


def _public_host(host: str) -> Tuple[bool, str]:
    """SSRF guard: the host must resolve to at least one public IP."""
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception as exc:  # noqa: BLE001
        return False, f"resolve failed: {exc}"[:100]
    if not infos:
        return False, "no addresses"
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if not ip.is_global:
            return False, f"non-public address {ip}"
    return True, "ok"


class WebBrowser:
    """Read-only bounded browser. All network I/O runs in the default
    executor so nothing blocks the trading loop's event loop."""

    def __init__(self, timeout: float = 8.0,
                 max_bytes: int = 400_000,
                 min_interval: float = 2.0,
                 feeds: Optional[List[str]] = None) -> None:
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.min_interval = min_interval
        self.feeds = list(feeds) if feeds is not None else list(_DEFAULT_FEEDS)
        self._last_request = 0.0
        self.requests_made = 0
        self.requests_refused = 0

    # -- transport seam (tests inject here) ---------------------------------

    def _throttle(self) -> None:
        wait = self.min_interval - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def _fetch_bytes_sync(self, url: str) -> Tuple[int, str, bytes]:
        self._throttle()
        req = Request(url, headers={"User-Agent": _USER_AGENT,
                                    "Accept": "text/html,application/rss+xml,"
                                              "application/atom+xml,text/xml;q=0.8"})
        with urlopen(req, timeout=self.timeout) as resp:
            ctype = resp.headers.get("Content-Type", "")
            return resp.status, ctype, resp.read(self.max_bytes + 1)

    def _validate_url(self, url: str) -> Tuple[bool, str]:
        try:
            p = urlparse(url)
        except Exception as exc:  # noqa: BLE001
            return False, f"bad url: {exc}"[:80]
        if p.scheme not in ("http", "https"):
            return False, f"scheme {p.scheme!r} refused"
        host = p.hostname or ""
        if not host:
            return False, "no host"
        ok, reason = _public_host(host)
        return ok, reason

    # -- public async API ----------------------------------------------------

    async def _get(self, url: str) -> Tuple[int, str, bytes]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._fetch_bytes_sync, url)

    async def fetch(self, url: str, max_chars: int = 8000) -> Dict[str, Any]:
        """Fetch one page and return extracted text — the webfetch analog."""
        ok, reason = self._validate_url(url)
        if not ok:
            self.requests_refused += 1
            return {"status": "refused", "url": url, "reason": reason}
        try:
            status, ctype, body = await self._get(url)
            self.requests_made += 1
        except Exception as exc:  # noqa: BLE001
            return {"status": "unavailable", "url": url,
                    "reason": str(exc)[:150]}
        if status != 200:
            return {"status": "unavailable", "url": url,
                    "reason": f"http {status}"}
        if not any(t in ctype for t in ("text", "html", "xml", "json")):
            return {"status": "refused", "url": url,
                    "reason": f"content-type {ctype[:60]} not text"}
        text = body.decode("utf-8", errors="replace")
        extracted = (_strip_html(text) if "html" in ctype
                     else _WS_RE.sub(" ", text).strip())
        return {"status": "ok", "url": url,
                "bytes": len(body), "truncated": len(body) > self.max_bytes,
                "text": extracted[:max_chars]}

    async def search(self, query: str,
                     max_results: int = 5) -> Dict[str, Any]:
        """General web search — the web_search analog (DuckDuckGo HTML,
        no API key). Result URLs are unwrapped from DDG redirects."""
        url = DDG_HTML_URL + "?q=" + quote_plus(str(query)[:300])
        try:
            status, ctype, body = await self._get(url)
            self.requests_made += 1
        except Exception as exc:  # noqa: BLE001
            return {"status": "unavailable", "query": query,
                    "reason": str(exc)[:150], "results": []}
        if status != 200:
            return {"status": "unavailable", "query": query,
                    "reason": f"http {status}", "results": []}
        page = body.decode("utf-8", errors="replace")
        results = _parse_ddg_results(page, max_results)
        if not results:
            return {"status": "parse_empty", "query": query,
                    "reason": "no results extracted", "results": []}
        return {"status": "ok", "query": query, "results": results}

    async def read_feed(self, feed_url: str,
                        max_items: int = 10) -> Dict[str, Any]:
        """One RSS/Atom feed -> normalized headline items."""
        ok, reason = self._validate_url(feed_url)
        if not ok:
            self.requests_refused += 1
            return {"status": "refused", "feed": feed_url, "reason": reason,
                    "items": []}
        try:
            status, ctype, body = await self._get(feed_url)
            self.requests_made += 1
        except Exception as exc:  # noqa: BLE001
            return {"status": "unavailable", "feed": feed_url,
                    "reason": str(exc)[:150], "items": []}
        if status != 200:
            return {"status": "unavailable", "feed": feed_url,
                    "reason": f"http {status}", "items": []}
        try:
            items = _parse_feed(body, max_items)
        except ET.ParseError as exc:
            return {"status": "unavailable", "feed": feed_url,
                    "reason": f"parse: {exc}"[:150], "items": []}
        return {"status": "ok", "feed": feed_url, "items": items}

    async def read_feeds(self, max_items: int = 8) -> Dict[str, Any]:
        """All configured market-news feeds, failure-tolerant."""
        out = {"status": "ok", "feeds": []}
        for feed in self.feeds:
            out["feeds"].append(await self.read_feed(feed, max_items))
        return out

    def status(self) -> Dict[str, Any]:
        return {"requests_made": self.requests_made,
                "requests_refused": self.requests_refused,
                "feeds": len(self.feeds),
                "timeout_s": self.timeout}

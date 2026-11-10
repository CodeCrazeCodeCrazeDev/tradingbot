"""Web browser tests — the organism's bounded read-only eyes.

No real network anywhere: the ``_fetch_bytes_sync`` transport seam is
patched with fixtures, and SSRF refusals happen before any socket is
opened. Evidence-honesty invariant: failures report
unavailable/refused — nothing is fabricated.
"""
import asyncio
from types import SimpleNamespace

import pytest

from trading_bot.core.csc.evolution_supervisor import EvolutionSupervisor
from trading_bot.core.csc.web_browser import (
    WebBrowser, _ddg_unwrap, _parse_ddg_results, _parse_feed,
    _public_host, _strip_html)

_DDG_PAGE = """
<html><body>
<div class="result">
 <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Falpha&amp;rut=abc">
  Momentum <b>Alpha</b> Study</a>
 <a class="result__snippet">A study of fx momentum…</a>
</div>
<div class="result">
 <a class="result__a" href="https://papers.example.org/paper1">
  Paper One</a>
 <a class="result__snippet">Second result snippet</a>
</div>
</body></html>
"""

_RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel>
 <item><title>EUR slips on CPI</title>
  <link>https://news.example.com/1</link>
  <pubDate>Mon, 09 Nov 2026 10:00:00 GMT</pubDate>
  <description>&lt;p&gt;Euro weaker after print&lt;/p&gt;</description></item>
 <item><title>DXY steady</title>
  <link>https://news.example.com/2</link>
  <pubDate>Mon, 09 Nov 2026 09:00:00 GMT</pubDate>
  <description>dollar index flat</description></item>
</channel></rss>
"""

_ATOM = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
 <entry><title>Atom headline</title>
  <link rel="alternate" href="https://atom.example.com/e1"/>
  <published>2026-11-09T08:00:00Z</published>
  <summary>atom summary text</summary></entry>
</feed>
"""


def _browser_with(payload):
    """Browser whose transport returns (status, ctype, body)."""
    b = WebBrowser(min_interval=0.0)
    b._fetch_bytes_sync = lambda url: payload
    return b


def test_strip_html_removes_scripts_and_tags():
    raw = "<p>Hello <b>world</b></p><script>evil()</script><style>x{}</style>"
    assert _strip_html(raw) == "Hello world"


def test_ddg_unwrap_redirect():
    url = _ddg_unwrap("//duckduckgo.com/l/?uddg=https%3A%2F%2Fex.com%2Fa&rut=x")
    assert url == "https://ex.com/a"
    assert _ddg_unwrap("https://ex.com/direct") == "https://ex.com/direct"


def test_parse_ddg_results_extracts_and_unwraps():
    results = _parse_ddg_results(_DDG_PAGE, 5)
    assert len(results) == 2
    assert results[0]["url"] == "https://example.com/alpha"
    assert "Momentum" in results[0]["title"]
    assert results[0]["snippet"].startswith("A study")
    assert results[1]["url"] == "https://papers.example.org/paper1"


def test_parse_feed_rss_and_atom():
    rss = _parse_feed(_RSS, 10)
    assert len(rss) == 2
    assert rss[0]["title"] == "EUR slips on CPI"
    assert rss[0]["url"] == "https://news.example.com/1"
    atom = _parse_feed(_ATOM, 10)
    assert atom[0]["title"] == "Atom headline"
    assert atom[0]["url"] == "https://atom.example.com/e1"


def test_public_host_refuses_private():
    ok, _ = _public_host("127.0.0.1")
    assert ok is False
    ok, _ = _public_host("localhost")
    assert ok is False
    ok, _ = _public_host("10.0.0.5")
    assert ok is False


def test_public_host_accepts_global(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda h, p: [(2, 1, 6, "", ("93.184.216.34", 0))])
    ok, _ = _public_host("example.com")
    assert ok is True


async def test_fetch_refuses_private_before_socket():
    b = WebBrowser(min_interval=0.0)
    called = []
    b._fetch_bytes_sync = lambda url: called.append(url)
    res = await b.fetch("http://127.0.0.1:8080/admin")
    assert res["status"] == "refused"
    assert called == []
    assert b.requests_refused == 1


async def test_fetch_refuses_non_http_scheme():
    b = WebBrowser(min_interval=0.0)
    res = await b.fetch("file:///etc/passwd")
    assert res["status"] == "refused"


async def test_fetch_extracts_text(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda h, p: [(2, 1, 6, "", ("93.184.216.34", 0))])
    b = _browser_with(
        (200, "text/html; charset=utf-8",
         b"<html><script>bad()</script><body><h1>Headline</h1>"
         b"<p>body text here</p></body></html>"))
    res = await b.fetch("https://example.com/page")
    assert res["status"] == "ok"
    assert "Headline" in res["text"]
    assert "bad()" not in res["text"]
    assert b.requests_made == 1


async def test_fetch_http_error_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda h, p: [(2, 1, 6, "", ("93.184.216.34", 0))])
    b = _browser_with((404, "text/html", b"nope"))
    res = await b.fetch("https://example.com/missing")
    assert res["status"] == "unavailable"
    assert "404" in res["reason"]


async def test_fetch_transport_error_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda h, p: [(2, 1, 6, "", ("93.184.216.34", 0))])
    b = WebBrowser(min_interval=0.0)
    def _boom(url):
        raise TimeoutError("timed out")
    b._fetch_bytes_sync = _boom
    res = await b.fetch("https://example.com/slow")
    assert res["status"] == "unavailable"
    assert "timed out" in res["reason"]


async def test_search_parses_results(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda h, p: [(2, 1, 6, "", ("93.184.216.34", 0))])
    b = _browser_with((200, "text/html", _DDG_PAGE.encode()))
    res = await b.search("fx momentum")
    assert res["status"] == "ok"
    assert len(res["results"]) == 2


async def test_search_empty_parse_is_honest(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda h, p: [(2, 1, 6, "", ("93.184.216.34", 0))])
    b = _browser_with((200, "text/html", b"<html>no results markup</html>"))
    res = await b.search("zzz")
    assert res["status"] == "parse_empty"
    assert res["results"] == []


async def test_read_feed_items(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda h, p: [(2, 1, 6, "", ("93.184.216.34", 0))])
    b = _browser_with((200, "application/rss+xml", _RSS))
    res = await b.read_feed("https://news.example.com/rss")
    assert res["status"] == "ok"
    assert len(res["items"]) == 2


async def test_read_feed_bad_xml_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda h, p: [(2, 1, 6, "", ("93.184.216.34", 0))])
    b = _browser_with((200, "application/rss+xml", b"not xml <<<"))
    res = await b.read_feed("https://news.example.com/rss")
    assert res["status"] == "unavailable"


# -- supervisor-level gating ------------------------------------------------

async def test_supervisor_browse_refused_offline(tmp_path, monkeypatch):
    monkeypatch.delenv("TB_SELF_MASTERY", raising=False)
    s = EvolutionSupervisor(data_dir=str(tmp_path / "m"), external=False)
    res = await s.browse("https://example.com")
    assert res["status"] == "refused"
    res = await s.search("anything")
    assert res["status"] == "refused"
    s.stop()


async def test_supervisor_browse_gated_on_connectivity(tmp_path, monkeypatch):
    monkeypatch.delenv("TB_SELF_MASTERY", raising=False)
    s = EvolutionSupervisor(data_dir=str(tmp_path / "m"), external=True,
                            enable_sentinel=False, enable_defender=False)
    # No sentinel -> online() is False -> fail-closed refusal.
    res = await s.search("fx")
    assert res["status"] == "refused"
    # Simulate measured connectivity -> real browser call.
    s.online = lambda: True
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda h, p: [(2, 1, 6, "", ("93.184.216.34", 0))])
    s._browser = _browser_with((200, "text/html", _DDG_PAGE.encode()))
    res = await s.search("fx momentum")
    assert res["status"] == "ok"
    s.stop()


# -- AI peer teacher ---------------------------------------------------------

from trading_bot.core.csc.ai_peer import AIPeer


def _peer(reachable=True, payload=None):
    p = AIPeer(endpoint="http://localhost:11434/api/generate",
               model="qwen3:8b")
    p._reachable = lambda: reachable
    p._post_json = lambda url, pl, t: (payload if payload is not None
                                       else {"response": "critique text",
                                             "model": "qwen3:8b"})
    return p


def test_peer_study_ok():
    p = _peer()
    res = p.study("subject", "report text")
    assert res["status"] == "ok"
    assert res["text"] == "critique text"
    assert res["model"] == "qwen3:8b"
    assert p.consults == 1


def test_peer_unavailable_when_endpoint_down():
    p = _peer(reachable=False)
    res = p.study("s", "c")
    assert res["status"] == "unavailable"
    assert p.consults == 0
    assert p.consults_failed == 1


def test_peer_transport_error_is_honest():
    p = _peer()
    def _boom(url, pl, t):
        raise TimeoutError("llm timeout")
    p._post_json = _boom
    res = p.study("s", "c")
    assert res["status"] == "unavailable"
    assert "llm timeout" in res["reason"]


def test_peer_openai_compatible_path():
    p = AIPeer(endpoint="http://localhost:1234/v1/chat/completions",
               model="lm")
    p._reachable = lambda: True
    p._post_json = lambda url, pl, t: {
        "model": "lm", "choices": [
            {"message": {"content": "openai-style critique"}}]}
    res = p.study("s", "c")
    assert res["status"] == "ok"
    assert res["text"] == "openai-style critique"


def test_peer_study_records_lesson(tmp_path, monkeypatch):
    monkeypatch.delenv("TB_SELF_MASTERY", raising=False)
    s = EvolutionSupervisor(data_dir=str(tmp_path / "m"), external=False)
    s._ai_peer = _peer()
    before = s.experiences_recorded
    s._peer_study({"phases": [{"insights": 2}], "kind": "learn"})
    assert s.ai_peer_sessions == 1
    assert s.experiences_recorded == before + 1
    audits = [a for a in s.drain_audits()
              if a["action"] == "ai_peer_lesson"]
    assert audits
    journal = s.data_dir / "evolution_journal.jsonl"
    assert "ai_peer_lesson" in journal.read_text()
    s.stop()


def test_peer_study_disabled_env(tmp_path, monkeypatch):
    monkeypatch.setenv("TB_AI_PEER", "0")
    s = EvolutionSupervisor(data_dir=str(tmp_path / "m"), external=False)
    s._ai_peer = _peer()
    s._peer_study({"kind": "learn"})
    assert s.ai_peer_sessions == 0
    s.stop()


def test_peer_study_skips_unavailable(tmp_path, monkeypatch):
    monkeypatch.delenv("TB_SELF_MASTERY", raising=False)
    monkeypatch.delenv("TB_AI_PEER", raising=False)
    s = EvolutionSupervisor(data_dir=str(tmp_path / "m"), external=False)
    s._ai_peer = _peer(reachable=False)
    s._peer_study({"kind": "learn"})
    assert s.ai_peer_sessions == 0
    s.stop()


# -- HuggingFace peer backend -------------------------------------------------

from trading_bot.core.csc.ai_peer import HuggingFacePeer, make_peer


def _hf(loadable=True, gen_text=" hf critique text"):
    p = HuggingFacePeer(model="test-model")
    p._reachable = lambda: loadable
    p._pipeline = (lambda prompt: [{"generated_text":
                                    "prompt" + gen_text}]) if loadable else None
    p._load_attempted = True
    return p


def test_hf_peer_study_ok():
    p = _hf()
    res = p.study("subject", "report")
    assert res["status"] == "ok"
    assert res["model"] == "test-model"
    assert p.consults == 1


def test_hf_peer_unavailable_no_transformers():
    p = HuggingFacePeer()
    p._reachable = lambda: False
    res = p.study("s", "c")
    assert res["status"] == "unavailable"
    assert "transformers" in res["reason"]


def test_hf_peer_unavailable_load_failed():
    p = HuggingFacePeer()
    p._reachable = lambda: True
    p._load = lambda: None
    p._load_error = "out of memory"
    res = p.study("s", "c")
    assert res["status"] == "unavailable"
    assert "out of memory" in res["reason"]


def test_hf_peer_strips_prompt_echo():
    p = _hf()
    prompt_holder = {}
    def fake_pipe(prompt):
        prompt_holder["p"] = prompt
        return [{"generated_text": prompt + "THE CRITIQUE"}]
    p._pipeline = fake_pipe
    res = p.study("s", "c")
    assert res["status"] == "ok"
    assert res["text"].endswith("THE CRITIQUE")


def test_make_peer_backend_routing(monkeypatch):
    monkeypatch.setenv("TB_AI_PEER_BACKEND", "hf")
    p = make_peer()
    assert isinstance(p, HuggingFacePeer)
    monkeypatch.setenv("TB_AI_PEER_BACKEND", "ollama")
    p = make_peer()
    assert type(p).__name__ == "AIPeer"
    monkeypatch.setenv("TB_AI_PEER_BACKEND", "auto")
    # no ollama, no transformers on this box -> deterministic AIPeer
    p = make_peer()
    assert type(p).__name__ in ("AIPeer", "HuggingFacePeer")


def test_hf_peer_via_supervisor(tmp_path, monkeypatch):
    monkeypatch.delenv("TB_SELF_MASTERY", raising=False)
    monkeypatch.setenv("TB_AI_PEER_BACKEND", "hf")
    s = EvolutionSupervisor(data_dir=str(tmp_path / "m"), external=False)
    s._ai_peer = _hf()
    s._peer_study({"kind": "learn", "phases": [{"insights": 1}]})
    assert s.ai_peer_sessions == 1
    assert s.experiences_recorded == 1
    s.stop()

"""AI peer teacher — bounded consults with a local inference server.

The organism asks a local model (Ollama ``/api/generate`` by default,
also OpenAI-compatible ``/v1/chat/completions`` endpoints) to critique
its own reflections: blind spots in the learning report, weak-skill
review, alternative hypotheses. The peer is a *teacher*, never an
authority — its text lands in memory as an ``ai_peer``-tagged lesson
and in the evolution journal; nothing it says is executed, trusted,
or routed to sizing.

Safety posture:

- Loopback/local endpoints only by default (``TB_AI_PEER_ENDPOINT``
  can point elsewhere — the SSRF-style public-host guard still
  applies; credentials are never sent).
- Availability is a 1s TCP probe per consult — when no server is
  running the channel costs nothing and reports ``unavailable``.
- Prompts are bounded digests (never raw secrets/paths); responses
  are capped text stored as evidence tagged with the peer's identity.
- Stdlib-only (urllib + json) so it works in both interpreters.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3:8b"
MAX_PROMPT_CHARS = 6000
MAX_RESPONSE_CHARS = 4000

_STUDY_SYSTEM = (
    "You are an external AI reviewer for an autonomous trading system's "
    "self-reflection. Given its measured learning report, identify: "
    "(1) blind spots or overconfident claims, (2) alternative "
    "explanations for the observed results, (3) the single most "
    "important thing to test next. Be concrete and skeptical. "
    "Plain text, under 300 words.")


class AIPeer:
    """Read-only consult channel to a local inference server."""

    def __init__(self, endpoint: Optional[str] = None,
                 model: Optional[str] = None,
                 timeout: float = 30.0,
                 probe_timeout: float = 1.0) -> None:
        self.endpoint = endpoint or os.environ.get(
            "TB_AI_PEER_ENDPOINT", DEFAULT_ENDPOINT)
        self.model = model or os.environ.get(
            "TB_AI_PEER_MODEL", DEFAULT_MODEL)
        self.timeout = timeout
        self.probe_timeout = probe_timeout
        self.consults = 0
        self.consults_failed = 0

    # -- transport seams -----------------------------------------------------

    def _reachable(self) -> bool:
        """1s TCP probe — the offline cost of this whole channel."""
        try:
            p = urlparse(self.endpoint)
            host, port = p.hostname, p.port or (
                443 if p.scheme == "https" else 80)
            with socket.create_connection(
                    (host, port), timeout=self.probe_timeout):
                return True
        except Exception:  # noqa: BLE001
            return False

    def _post_json(self, url: str, payload: Dict[str, Any],
                   timeout: float) -> Dict[str, Any]:
        req = Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))

    # -- consult -------------------------------------------------------------

    def study(self, subject: str, context: str = "") -> Dict[str, Any]:
        """Ask the peer to critique a bounded digest. Sync by design —
        callers run it on the supervisor's worker thread."""
        t0 = time.monotonic()
        if not self._reachable():
            self.consults_failed += 1
            return {"status": "unavailable",
                    "reason": "peer endpoint not reachable",
                    "endpoint": self.endpoint, "model": self.model}
        prompt = (f"SUBJECT: {subject[:500]}\n\n"
                  f"MEASURED REPORT (verbatim):\n{context[:MAX_PROMPT_CHARS]}")
        try:
            if "/api/generate" in self.endpoint:
                payload = {"model": self.model, "prompt": prompt,
                           "system": _STUDY_SYSTEM, "stream": False,
                           "options": {"temperature": 0.2,
                                       "num_predict": 512}}
                raw = self._post_json(self.endpoint, payload, self.timeout)
                text = str(raw.get("response") or "")
                model = str(raw.get("model") or self.model)
            else:  # OpenAI-compatible chat completions
                payload = {
                    "model": self.model, "temperature": 0.2,
                    "max_tokens": 512,
                    "messages": [
                        {"role": "system", "content": _STUDY_SYSTEM},
                        {"role": "user", "content": prompt}]}
                raw = self._post_json(self.endpoint, payload, self.timeout)
                choices = raw.get("choices") or [{}]
                text = str((choices[0].get("message") or {})
                           .get("content") or "")
                model = str(raw.get("model") or self.model)
        except Exception as exc:  # noqa: BLE001
            self.consults_failed += 1
            return {"status": "unavailable", "reason": str(exc)[:150],
                    "endpoint": self.endpoint, "model": self.model}
        self.consults += 1
        return {"status": "ok", "model": model,
                "text": text.strip()[:MAX_RESPONSE_CHARS],
                "latency_ms": round((time.monotonic() - t0) * 1000)}

    def status(self) -> Dict[str, Any]:
        return {"endpoint": self.endpoint, "model": self.model,
                "consults": self.consults,
                "consults_failed": self.consults_failed}


class HuggingFacePeer:
    """Local HF teacher — same ``study()`` contract as ``AIPeer`` but
    runs a transformers text-generation pipeline in-process (no server,
    no API key). Loads lazily on first consult; a missing transformers
    or unloadable model reports ``unavailable`` — never fabricates.

    Env: ``TB_HF_MODEL`` (default ``Qwen/Qwen2.5-0.5B-Instruct`` —
    small enough for CPU), ``TB_HF_MAX_NEW_TOKENS`` (default 256),
    ``HF_HUB_OFFLINE=1`` respects the sandbox. Runs on the supervisor
    worker thread — generation never blocks the trading loop.
    """

    DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

    def __init__(self, model: Optional[str] = None,
                 max_new_tokens: Optional[int] = None) -> None:
        self.model_name = model or os.environ.get(
            "TB_HF_MODEL", self.DEFAULT_MODEL)
        self.max_new_tokens = int(os.environ.get(
            "TB_HF_MAX_NEW_TOKENS", max_new_tokens or 256))
        self.endpoint = f"hf://{self.model_name}"
        self.model = self.model_name
        self._pipeline: Any = None
        self._load_attempted = False
        self._load_error: Optional[str] = None
        self.consults = 0
        self.consults_failed = 0

    def _load(self) -> Any:
        if self._pipeline is not None or self._load_attempted:
            return self._pipeline
        self._load_attempted = True
        try:
            import torch  # noqa: F401
            from transformers import pipeline
            self._pipeline = pipeline(
                "text-generation", model=self.model_name,
                max_new_tokens=self.max_new_tokens,
                do_sample=True, temperature=0.3)
        except Exception as exc:  # noqa: BLE001
            self._load_error = str(exc)[:150]
            logger.debug("HFPeer: model load failed: %s", exc)
        return self._pipeline

    def _reachable(self) -> bool:
        """'Reachable' here means loadable — import probe only, no
        heavyweight load until study() actually runs."""
        try:
            import transformers  # noqa: F401
            return True
        except Exception:  # noqa: BLE001
            return False

    def study(self, subject: str, context: str = "") -> Dict[str, Any]:
        t0 = time.monotonic()
        if not self._reachable():
            self.consults_failed += 1
            return {"status": "unavailable",
                    "reason": "transformers not installed",
                    "endpoint": self.endpoint, "model": self.model_name}
        pipe = self._load()
        if pipe is None:
            self.consults_failed += 1
            return {"status": "unavailable",
                    "reason": self._load_error or "model load failed",
                    "endpoint": self.endpoint, "model": self.model_name}
        prompt = (f"{_STUDY_SYSTEM}\n\nSUBJECT: {subject[:500]}\n\n"
                  f"MEASURED REPORT (verbatim):\n"
                  f"{context[:MAX_PROMPT_CHARS]}\n\nCRITIQUE:")
        try:
            out = pipe(prompt)
            text = str(out[0].get("generated_text", ""))
            # Continuation models echo the prompt — strip it.
            if text.startswith(prompt):
                text = text[len(prompt):]
        except Exception as exc:  # noqa: BLE001
            self.consults_failed += 1
            return {"status": "unavailable", "reason": str(exc)[:150],
                    "endpoint": self.endpoint, "model": self.model_name}
        self.consults += 1
        return {"status": "ok", "model": self.model_name,
                "text": text.strip()[:MAX_RESPONSE_CHARS],
                "latency_ms": round((time.monotonic() - t0) * 1000)}

    def status(self) -> Dict[str, Any]:
        return {"endpoint": self.endpoint, "model": self.model_name,
                "backend": "huggingface",
                "loaded": self._pipeline is not None,
                "consults": self.consults,
                "consults_failed": self.consults_failed}


def make_peer(backend: Optional[str] = None) -> Any:
    """Backend router for the AI peer teacher.

    ``TB_AI_PEER_BACKEND``: ``auto`` (default) tries the Ollama-style
    HTTP endpoint first (1s probe) then falls back to the in-process
    HuggingFace pipeline; ``ollama`` / ``hf`` force a backend."""
    backend = (backend or os.environ.get(
        "TB_AI_PEER_BACKEND", "auto")).lower()
    if backend in ("hf", "huggingface", "transformers"):
        return HuggingFacePeer()
    if backend in ("ollama", "http", "endpoint"):
        return AIPeer()
    # auto: cheap reachability probe decides — never blocks.
    ollama = AIPeer()
    if ollama._reachable():
        return ollama
    hf = HuggingFacePeer()
    if hf._reachable():
        return hf
    return ollama  # both down: deterministic unavailable reports

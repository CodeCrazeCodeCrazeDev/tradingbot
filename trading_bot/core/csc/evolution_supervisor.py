"""Evolution supervisor — the organism's learn/evolve/defend loop.

Wires the existing self-mastery, connectivity, and self-defense
subsystems into the CSC cycle as one bounded, audited supervisor:

- EXPERIENCE: every terminal decision (executed, abstained, rejected)
  is recorded to ``ExperienceMemory`` with the decision context — the
  why, not just the what. Settled outcomes attach measured results;
  failures are first-class experience.
- REFLECT/CONSOLIDATE/EVOLVE/VERIFY: the ``MasteryOrchestrator`` cycle
  runs on a single bounded worker thread at a measured cadence.
  ``CodeEvolver`` output is journaled as *proposals* — nothing here
  calls ``apply_modification``; promotion still routes through the RSI
  gates and signed ``OperatorAuthorization``.
- CONNECTIVITY: a read-only ``NetworkSentinel`` measures internet
  reachability; external activities (intel sweeps) auto-activate when
  connected and suspend when offline. The sentinel manages no systems
  and switches no trading mode — it measures, the supervisor gates.
- DEFENSE: a read-only ``SelfDefender`` monitor reports threat level;
  elevated levels raise SECURITY audit events. Its credential store is
  relocated under ``var/`` and never feeds the canonical provider.
- INTEL: bounded arxiv/github research sweeps via the CSC's
  ``_fetch_internet_evidence`` — honest evidence only (the
  ``internet_access`` engine fabricates mock feeds on fetch failure
  and is deliberately not used).

Authority: none over capital, risk, shield, governance, or execution.
Every ingest/scheduling choice lands in the audit trail or the
evolution journal.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
import warnings
import weakref
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cadence (observation cycles) — all bounded and env-tunable.
# ---------------------------------------------------------------------------
def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


REFLECT_EVERY = _env_int("TB_EVO_REFLECT_EVERY", 250)
LEARN_EVERY = _env_int("TB_EVO_LEARN_EVERY", 1000)
INTEL_EVERY = _env_int("TB_EVO_INTEL_EVERY", 150)
SEC_EVERY = _env_int("TB_EVO_SEC_EVERY", 50)
AUDIT_EVERY = _env_int("TB_EVO_AUDIT_EVERY", 25)
MAX_OPEN_EXPERIENCES = 4096
MAX_INTEL_PER_SWEEP = 3
FRONTIER_MIN_OBS = _env_int("TB_FRONTIER_MIN_OBS", 5)
FRONTIER_PER_MODEL_CAP = 50
MAX_FRONTIER_OBS_PER_SWEEP = 4
# Watchlist: names that mark a fetched doc as evidence about an
# external frontier system. Env-overridable.
_FRONTIER_WATCH = tuple(w.strip().lower() for w in os.environ.get(
    "TB_FRONTIER_WATCH",
    "gpt,claude,gemini,deepseek,qwen,llama,mistral,grok").split(",")
    if w.strip())

# Rotating research curriculum — bounded external study of how other
# systems trade (institutional algos, funds, strategies, models).
_INTEL_CURRICULUM = (
    "institutional algorithmic trading execution algorithms",
    "market making inventory control strategy research",
    "fx momentum mean reversion hedge fund study",
    "reinforcement learning trading policy research",
    "portfolio risk parity institutional asset allocation",
    "order flow market microstructure alpha research",
)

_EXECUTED_OUTCOMES = frozenset({
    "EXECUTED", "FILLED", "PAPER_FILLED", "TRADE_EXECUTED", "PAPER",
    "ORDER_FILLED", "POSITION_OPENED",
})
_SKIPPED_OUTCOMES = frozenset({
    "ABSTAIN", "HOLD", "WAIT", "NO_TRADE", "SKIPPED",
})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EvolutionSupervisor:
    """Bounded self-evolution supervisor for the CSC.

    Constructor is side-effect-free: no threads, no sockets, no files.
    Monitors and stores activate lazily on first use so importing or
    instantiating the CSC in tests never touches the network.
    """

    def __init__(
        self,
        data_dir: Optional[str] = None,
        external: Optional[bool] = None,
        enable_sentinel: bool = True,
        enable_defender: bool = True,
    ) -> None:
        self.data_dir = Path(
            data_dir or os.environ.get(
                "TB_SELF_MASTERY_DIR", "var/self_mastery"))
        if external is None:
            external = os.environ.get(
                "TB_AUTONOMY_EXTERNAL", "1").lower() not in (
                    "0", "false", "off", "no")
        self.external_enabled = bool(external)
        self._want_sentinel = enable_sentinel
        self._want_defender = enable_defender

        self.cycles = 0
        self.experiences_recorded = 0
        self.outcomes_recorded = 0
        self.reflections_run = 0
        self.learning_cycles_run = 0
        self.intel_sweeps = 0
        self.security_reports = 0

        self._mastery: Any = None
        self._sentinel: Any = None
        self._defender: Any = None
        self._browser: Any = None
        self._ai_peer: Any = None
        self.ai_peer_sessions = 0
        self._monitors_started = False

        # Frontier-distillation feed: structured observations about
        # external systems, buffered per model until enough evidence
        # exists to run the gated distillation pipeline.
        self._frontier_obs: Dict[str, List[Dict[str, Any]]] = {}
        self._frontier_distilled: Dict[str, int] = {}
        self._frontier_loaded = False
        self.frontier_observations = 0
        self.frontier_runs = 0
        self._csc_ref: Any = None

        self._lock = threading.Lock()
        # trade_id -> experience_id for open experiences awaiting outcomes
        self._open_experiences: Dict[str, str] = {}
        self._settled_ids: deque = deque(maxlen=4096)
        self._settled_set: set = set()

        self._worker: Optional[threading.Thread] = None
        self._intel_task: Any = None
        self._intel_cursor = 0

        self._last_learning: Optional[Dict[str, Any]] = None
        self._last_intel: Optional[Dict[str, Any]] = None
        self._last_security: Optional[Dict[str, Any]] = None
        self._audit_outbox: List[Dict[str, Any]] = []

    # -- lazy subsystem handles -------------------------------------------

    def _mastery_orch(self) -> Any:
        if self._mastery is None:
            from trading_bot.self_mastery.mastery_orchestrator import (
                MasteryOrchestrator)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self._mastery = MasteryOrchestrator(
                data_dir=str(self.data_dir))
        return self._mastery

    def _ensure_monitors(self) -> None:
        """Start the read-only monitors once. Both are legacy/quarantined
        components — used strictly as measured environment input; they
        register no systems and carry no trading authority."""
        if self._monitors_started or not self.external_enabled:
            return
        self._monitors_started = True
        if self._want_sentinel and self._sentinel is None:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", DeprecationWarning)
                    from trading_bot.sentient_core.network_sentinel import (
                        NetworkSentinel)
                    self._sentinel = NetworkSentinel()
                self._sentinel.start()
            except Exception as exc:  # noqa: BLE001
                logger.debug("evolution: sentinel unavailable: %s", exc)
                self._sentinel = None
        if self._want_defender and self._defender is None:
            try:
                sec_dir = self.data_dir / "self_defense"
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", DeprecationWarning)
                    from trading_bot.sentient_core.self_defender import (
                        SelfDefender)
                    self._defender = SelfDefender(
                        secrets_path=str(sec_dir / "secrets"),
                        log_path=str(sec_dir / "logs"))
                self._defender.start()
            except Exception as exc:  # noqa: BLE001
                logger.debug("evolution: defender unavailable: %s", exc)
                self._defender = None

    def _web_browser(self) -> Any:
        if self._browser is None:
            from .web_browser import WebBrowser
            feeds_env = os.environ.get("TB_INTEL_FEEDS", "").strip()
            feeds = ([f.strip() for f in feeds_env.split(",") if f.strip()]
                     if feeds_env else None)
            self._browser = WebBrowser(feeds=feeds)
        return self._browser

    def _peer(self) -> Any:
        if self._ai_peer is None:
            from .ai_peer import make_peer
            self._ai_peer = make_peer()
        return self._ai_peer

    def _peer_enabled(self) -> bool:
        return os.environ.get("TB_AI_PEER", "1").lower() not in (
            "0", "false", "off", "no")

    def _peer_study(self, report: Dict[str, Any]) -> None:
        """After a learn pass, let a local AI teacher critique the
        report. Runs on the worker thread; a stored lesson is evidence
        tagged ai_peer — never instructions."""
        if not self._peer_enabled():
            return
        try:
            peer = self._peer()
            res = peer.study(
                subject="trading-system self-reflection critique",
                context=json.dumps(report, default=str))
            if res.get("status") != "ok":
                return
            self.ai_peer_sessions += 1
            lesson = {"ts": _utcnow().isoformat(),
                      "model": res.get("model"),
                      "latency_ms": res.get("latency_ms"),
                      "critique": res.get("text")}
            # The peer's critique becomes a remembered LESSON — tagged
            # so reflection can weigh untrusted external input honestly.
            try:
                self._record_experience(
                    "LESSON_LEARNED", "peer_review",
                    {"symbol": "self", "regime": "introspection"},
                    _PeerLesson(lesson),
                    ["ai_peer", str(res.get("model") or "peer")], 0.6)
            except Exception as exc:  # noqa: BLE001
                logger.debug("evolution: peer lesson ingest: %s", exc)
            self._journal({"kind": "ai_peer_lesson", **lesson})
            self._audit_outbox.append({
                "event_type": "EVOLUTION", "action": "ai_peer_lesson",
                "outcome": "ok",
                "correlation_id": f"peer-{self.ai_peer_sessions}",
                "details": {"model": res.get("model"),
                            "latency_ms": res.get("latency_ms"),
                            "excerpt": (res.get("text") or "")[:300]}})
        except Exception as exc:  # noqa: BLE001
            logger.debug("evolution: peer study failed: %s", exc)

    # -- frontier observation feed ------------------------------------------

    def _frontier_journal_path(self) -> Path:
        return self.data_dir / "frontier_observations.jsonl"

    def _load_frontier_journal(self) -> None:
        """Replay persisted observations once — the buffer survives
        restarts like the rest of memory."""
        if self._frontier_loaded:
            return
        self._frontier_loaded = True
        path = self._frontier_journal_path()
        if not path.exists():
            return
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                rec = json.loads(line)
                if rec.get("kind") != "frontier_observation":
                    continue
                model = rec.get("model_name")
                if not model:
                    continue
                buf = self._frontier_obs.setdefault(model, [])
                buf.append(rec)
                del buf[:-FRONTIER_PER_MODEL_CAP]
        except Exception as exc:  # noqa: BLE001
            logger.debug("evolution: frontier journal load: %s", exc)

    def observe_frontier(self, model_name: str, observation_type: str,
                         summary: str, observed_behavior: str = "",
                         metrics: Optional[Dict[str, float]] = None,
                         failure_modes: Optional[List[str]] = None,
                         source_uri: Optional[str] = None) -> Optional[str]:
        """Buffer one structured observation about an external system.
        Distillation runs when a model accumulates FRONTIER_MIN_OBS."""
        try:
            self._load_frontier_journal()
            obs = {
                "kind": "frontier_observation",
                "observation_id": f"fo-{self.frontier_observations}-"
                                  f"{int(time.time())}",
                "model_name": str(model_name)[:80].lower(),
                "observation_type": str(observation_type),
                "summary": str(summary)[:300],
                "observed_behavior": str(observed_behavior)[:500],
                "metrics": dict(metrics or {}),
                "failure_modes": list(failure_modes or ()),
                "source_uri": (str(source_uri)[:500]
                               if source_uri else None),
                "observed_at": time.time(),
            }
            buf = self._frontier_obs.setdefault(obs["model_name"], [])
            buf.append(obs)
            del buf[:-FRONTIER_PER_MODEL_CAP]
            self.frontier_observations += 1
            self._journal_to(self._frontier_journal_path(), obs)
            return obs["observation_id"]
        except Exception as exc:  # noqa: BLE001
            logger.debug("evolution: observe_frontier failed: %s", exc)
            return None

    def _harvest_frontier_obs(self, topic: str,
                              entry: Dict[str, Any]) -> int:
        """Turn fetched intel into FrontierObservations when the text
        names a watched external system. Heuristic evidence — the
        distillation engine's own gates decide what transfers."""
        made = 0
        texts = [topic]
        for r in (entry.get("web") or {}).get("results") or []:
            texts.append(f"{r.get('title', '')} {r.get('snippet', '')}")
            texts.append(r.get("url", ""))
        texts.append((entry.get("page") or {}).get("excerpt", ""))
        blob = " ".join(texts).lower()
        for name in _FRONTIER_WATCH:
            if made >= MAX_FRONTIER_OBS_PER_SWEEP:
                break
            if name not in blob:
                continue
            self.observe_frontier(
                name, self._frontier_obs_type(blob),
                summary=(entry.get("web") or {})
                .get("results", [{}])[0].get("title", topic)[:200],
                observed_behavior=blob[:400],
                source_uri=(entry.get("page") or {}).get("url"))
            made += 1
        return made

    @staticmethod
    def _frontier_obs_type(text: str) -> str:
        for keys, otype in (
                (("benchmark", "eval", "score", "mmlu", "humaneval",
                  "swe-bench"), "eval_result"),
                (("fail", "incident", "bug", "jailbreak", "vulnerab"),
                 "failure_report"),
                (("api", "tool use", "function calling", "plugin"),
                 "api_behavior"),
                (("release", "launch", "announce", "unveil"),
                 "model_release")):
            if any(k in text for k in keys):
                return otype
        return "paper"

    def _maybe_distill_frontier(self) -> None:
        """Run the gated distillation pipeline per model with enough
        buffered evidence — on the worker thread, one model pass per
        learn window. Artifacts stay playbook/policy/invariant kinds;
        nothing reaches propose_model automatically."""
        ref = self._csc_ref() if self._csc_ref is not None else None
        if ref is None or not self._frontier_obs:
            return
        distill = getattr(ref, "distill_frontier", None)
        if distill is None:
            return
        for model, buf in list(self._frontier_obs.items()):
            if len(buf) < FRONTIER_MIN_OBS:
                continue
            if self.cycles - self._frontier_distilled.get(
                    model, -10 ** 9) < LEARN_EVERY:
                continue
            try:
                from trading_bot.core.frontier_capability_distillation \
                    import FrontierObservation, FrontierObservationType
                obs_objs = []
                for o in buf:
                    try:
                        otype = FrontierObservationType(
                            o["observation_type"])
                    except ValueError:
                        otype = FrontierObservationType.PAPER
                    obs_objs.append(FrontierObservation(
                        observation_id=o["observation_id"],
                        model_name=model, observation_type=otype,
                        summary=o["summary"],
                        observed_behavior=o["observed_behavior"],
                        metrics=o.get("metrics") or {},
                        failure_modes=tuple(
                            o.get("failure_modes") or ()),
                        source_uri=o.get("source_uri"),
                        observed_at=o.get("observed_at") or time.time()))
                summary = distill(model, obs_objs, [], [])
                self._frontier_distilled[model] = self.cycles
                self.frontier_runs += 1
                self._journal({"kind": "frontier_distill",
                               "model": model,
                               "observations": len(obs_objs),
                               "summary": summary})
                self._audit_outbox.append({
                    "event_type": "EVOLUTION",
                    "action": "frontier_distill",
                    "outcome": "ok",
                    "correlation_id":
                        f"frontier-{model}-{self.frontier_runs}",
                    "details": {
                        "model": model,
                        "observations": len(obs_objs),
                        "patterns": summary.get("patterns"),
                        "artifacts": summary.get("artifacts"),
                        "rejected": summary.get("rejected")}})
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "evolution: frontier distill %s failed: %s",
                    model, exc)

    def _maybe_innovate(self) -> None:
        """arXiv:2504.01990 self-enhancement pass: bounded evidence-
        seeded candidates through the gated propose/validate path.
        VALIDATED candidates wait for OperatorAuthorization — the
        engine never auto-approves."""
        ref = self._csc_ref() if self._csc_ref is not None else None
        if ref is None or self._mastery_disabled():
            return
        try:
            from .self_innovation import SelfInnovationEngine
            if not hasattr(self, "_innovator"):
                self._innovator = SelfInnovationEngine()
            bars: Dict[str, List[Dict[str, Any]]] = {}
            obs_hist = getattr(ref, "observation_history", None)
            syms = list((getattr(ref, "_open_positions", None) or {})
                        .keys()) or ["EURUSD"]
            for sym in syms[:2]:
                closes = obs_hist(sym)[-400:] if obs_hist else []
                if closes:
                    bars[sym] = [{"close": float(c)} for c in closes]
            if not bars:
                return
            rep = asyncio.run(
                self._innovator.innovate(ref, bars))
            rep["kind"] = "self_innovation"
            rep["ts"] = _utcnow().isoformat()
            self._last_learning = dict(self._last_learning or {})
            self._last_learning["innovation"] = rep
            self._journal(rep)
            self._audit_outbox.append({
                "event_type": "EVOLUTION", "action": "self_innovation",
                "outcome": rep.get("status", "ok"),
                "correlation_id":
                    f"innovate-{self._innovator.cycles_run}",
                "details": {k: rep.get(k) for k in
                            ("proposed", "validated", "rejected",
                             "status")}})
        except Exception as exc:  # noqa: BLE001
            logger.debug("evolution: innovate failed: %s", exc)

    async def browse(self, url: str) -> Dict[str, Any]:
        """Operator-visible webfetch analog — connectivity-gated."""
        if not self.external_enabled or self.online() is not True:
            return {"status": "refused", "url": url,
                    "reason": "offline or external disabled"}
        return await self._web_browser().fetch(url)

    async def search(self, query: str,
                     max_results: int = 5) -> Dict[str, Any]:
        """Operator-visible web_search analog — connectivity-gated."""
        if not self.external_enabled or self.online() is not True:
            return {"status": "refused", "query": query,
                    "reason": "offline or external disabled",
                    "results": []}
        return await self._web_browser().search(query, max_results)

    # -- connectivity ------------------------------------------------------

    def online(self) -> Optional[bool]:
        """Measured connectivity: True/False from the sentinel, None when
        the probe is unavailable. External activities require True —
        fail-closed on uncertainty."""
        sent = self._sentinel
        if sent is None:
            return False if self.external_enabled else None
        try:
            state = getattr(sent, "current_state", None)
            name = getattr(state, "name", "")
            return bool(name.startswith("CONNECTED"))
        except Exception:  # noqa: BLE001
            return False

    def connectivity_status(self) -> Dict[str, Any]:
        sent = self._sentinel
        if sent is None:
            return {"monitor": "unavailable",
                    "external_enabled": self.external_enabled,
                    "online": self.online()}
        try:
            status = sent.get_status()
        except Exception:  # noqa: BLE001
            status = {}
        return {
            "monitor": "network_sentinel",
            "state": getattr(getattr(sent, "current_state", None),
                             "name", "unknown"),
            "trading_mode": getattr(
                getattr(sent, "current_mode", None), "name", "unknown"),
            "online": self.online(),
            "ready_for_trading": bool(status.get("ready_for_trading")),
            "quality_score": status.get("connection_quality_score"),
        }

    # -- experience ingestion (decision side) -------------------------------

    def ingest_decision(self, obs_dict: Dict[str, Any],
                        decision: Any) -> Optional[str]:
        """Record a terminal decision as an experience. Returns the
        experience_id (also tracked under trade_id for outcome join)."""
        if self._mastery_disabled():
            return None
        try:
            outcome = getattr(decision, "outcome", None)
            outcome_name = str(getattr(outcome, "name", None)
                               or getattr(outcome, "value", outcome)
                               or "").upper()
            if not outcome_name:
                return None  # not a terminal decision — nothing to learn
            action = str(getattr(decision, "action", "") or
                         (obs_dict.get("action") or "HOLD")).upper()
            trade_id = str(getattr(decision, "trade_id", "") or "")
            if outcome_name in _EXECUTED_OUTCOMES:
                etype_name = "TRADE_EXECUTED"
                importance = 0.7
            elif outcome_name in _SKIPPED_OUTCOMES:
                etype_name = "TRADE_SKIPPED"
                importance = 0.5  # skipped decisions teach as much
            else:
                etype_name = "TRADE_SKIPPED"
                importance = 0.5
            tags = ["terminal:" + (outcome_name or "UNKNOWN")]
            reason = getattr(decision, "dominant_rejection_reason", None)
            if reason:
                tags.append("rejected:" + str(reason)[:60])
            exp_id = self._record_experience(
                etype_name, action, obs_dict, decision, tags, importance)
            if exp_id and trade_id:
                if len(self._open_experiences) >= MAX_OPEN_EXPERIENCES:
                    self._open_experiences.pop(
                        next(iter(self._open_experiences)))
                self._open_experiences[trade_id] = exp_id
            return exp_id
        except Exception as exc:  # noqa: BLE001 — learning never breaks trading
            logger.debug("evolution: ingest_decision failed: %s", exc)
            return None

    def _record_experience(self, etype_name: str, action: str,
                           obs_dict: Dict[str, Any], decision: Any,
                           tags: List[str], importance: float) -> Optional[str]:
        from trading_bot.self_mastery.experience_memory import (
            DecisionContext, ExperienceType)
        orch = self._mastery_orch()
        ctx = DecisionContext(
            timestamp=_utcnow(),
            price=float(obs_dict.get("close") or obs_dict.get("price")
                        or 0.0),
            volume=float(obs_dict.get("volume") or 0.0),
            volatility=float(obs_dict.get("volatility")
                             or obs_dict.get("atr") or 0.0),
            spread=float(obs_dict.get("spread") or 0.0),
            regime=str(obs_dict.get("regime") or "unknown"),
            trend=str(obs_dict.get("trend") or "sideways"),
            confidence=float(getattr(decision, "confidence", 0.0) or 0.0),
            risk_level=float(obs_dict.get("risk_level") or 0.0),
            current_position=float(obs_dict.get("position") or 0.0),
            unrealized_pnl=float(obs_dict.get("unrealized_pnl") or 0.0),
            drawdown=float(obs_dict.get("drawdown") or 0.0),
            signals={k: v for k, v in obs_dict.items()
                     if isinstance(v, (int, float))
                     and not isinstance(v, bool)},
        )
        reasoning = str(getattr(decision, "reasoning", "") or
                        getattr(decision, "rationale", "") or "")[:400]
        with self._lock:
            exp_id = orch.record_trade(
                action=action,
                symbol=str(obs_dict.get("symbol") or "unknown"),
                quantity=float(getattr(decision, "quantity", 0.0)
                               or obs_dict.get("quantity") or 0.0),
                context=ctx,
                experience_type=getattr(
                    ExperienceType, etype_name, None),
                reasoning=reasoning,
                confidence=ctx.confidence,
                tags=tags,
                importance=importance)
        self.experiences_recorded += 1
        return exp_id

    # -- outcome ingestion (settlement side) --------------------------------

    def ingest_outcome(self, trade_id: str, pending: Dict[str, Any],
                       was_correct: bool, realized_return: Optional[float],
                       exit_price: Optional[float] = None) -> bool:
        """Attach a measured outcome to the matching open experience."""
        if self._mastery_disabled():
            return False
        try:
            exp_id = self._open_experiences.pop(str(trade_id), None)
            if exp_id is None:
                # Trade opened before this supervisor session — create
                # the experience from pending evidence so the outcome
                # still lands in memory.
                exp_id = self._record_experience(
                    "TRADE_EXECUTED",
                    str(pending.get("action") or "HOLD").upper(),
                    {"symbol": pending.get("symbol"),
                     "regime": pending.get("regime"),
                     "price": pending.get("entry_price")},
                    _PendingDecision(pending), ["rehydrated"], 0.6)
            if not exp_id:
                return False
            analysis = self._outcome_analysis(
                pending, was_correct, realized_return, exit_price)
            with self._lock:
                ok = self._mastery_orch().record_outcome(
                    exp_id, analysis)
            self.outcomes_recorded += int(bool(ok))
            return bool(ok)
        except Exception as exc:  # noqa: BLE001
            logger.debug("evolution: ingest_outcome failed: %s", exc)
            return False

    def ingest_settlement(self, settlement: Dict[str, Any]) -> bool:
        """Attach paper-fill economics to an experience. Deduped by
        settlement_id — receipts may replay across restarts."""
        if self._mastery_disabled():
            return False
        sid = str(settlement.get("settlement_id") or "")
        if sid and sid in self._settled_set:
            return False
        try:
            key = str(settlement.get("decision_id")
                      or settlement.get("entry_order_id") or "")
            exp_id = self._open_experiences.pop(key, None)
            if exp_id is None:
                return False
            gross = settlement.get("gross_return")
            net = settlement.get("cost_return", gross)
            was_correct = isinstance(net, (int, float)) and net > 0
            pending = {"action": settlement.get("action") or "BUY",
                       "entry_price": settlement.get("entry_price"),
                       "confidence": settlement.get("confidence") or 0.5}
            analysis = self._outcome_analysis(
                pending, was_correct,
                net if isinstance(net, (int, float)) else None,
                settlement.get("exit_price"))
            with self._lock:
                ok = self._mastery_orch().record_outcome(exp_id, analysis)
            if ok:
                self.outcomes_recorded += 1
                if sid:
                    if len(self._settled_set) >= self._settled_ids.maxlen:
                        self._settled_set.discard(self._settled_ids[0])
                    self._settled_ids.append(sid)
                    self._settled_set.add(sid)
            return bool(ok)
        except Exception as exc:  # noqa: BLE001
            logger.debug("evolution: ingest_settlement failed: %s", exc)
            return False

    def _outcome_analysis(self, pending: Dict[str, Any], was_correct: bool,
                          realized_return: Optional[float],
                          exit_price: Optional[float]) -> Any:
        from trading_bot.self_mastery.experience_memory import (
            OutcomeAnalysis, OutcomeQuality)
        r = float(realized_return) if isinstance(
            realized_return, (int, float)) else 0.0
        entry = float(pending.get("entry_price") or 0.0)
        if r > 0.002:
            quality = OutcomeQuality.EXCELLENT
        elif r > 0:
            quality = OutcomeQuality.GOOD
        elif abs(r) <= 0.0002:
            quality = OutcomeQuality.NEUTRAL
        elif r > -0.002:
            quality = OutcomeQuality.POOR
        else:
            quality = OutcomeQuality.TERRIBLE
        exit_p = float(exit_price) if isinstance(
            exit_price, (int, float)) else entry
        lessons: List[str] = []
        mistakes: List[str] = []
        successes: List[str] = []
        if was_correct:
            successes.append(
                f"{pending.get('action')} {pending.get('regime', '')} "
                f"resolved r={r:+.4f}")
        else:
            mistakes.append(
                f"{pending.get('action')} {pending.get('regime', '')} "
                f"lost r={r:+.4f} conf={pending.get('confidence', 0):.2f}")
            lessons.append("review entry context for this regime/action pair")
        now = _utcnow()
        return OutcomeAnalysis(
            decision_time=now, outcome_time=now, duration_seconds=0.0,
            pnl=r, pnl_percent=r * 100.0,
            max_favorable_excursion=0.0, max_adverse_excursion=0.0,
            quality=quality,
            price_at_decision=entry, price_at_outcome=exit_p,
            price_change_percent=r * 100.0,
            prediction_correct=bool(was_correct),
            prediction_confidence=float(pending.get("confidence") or 0.0),
            risk_reward_ratio=0.0, sharpe_contribution=0.0,
            lessons=lessons, mistakes=mistakes, successes=successes)

    # -- per-cycle scheduling -----------------------------------------------

    def on_cycle(self, csc: Any, obs_dict: Dict[str, Any]) -> Dict[str, Any]:
        """One bounded tick per observation. Starts monitors lazily,
        polls defense, and schedules worker activities by cadence."""
        self.cycles += 1
        did: List[str] = []
        if self._csc_ref is None and csc is not None:
            try:
                self._csc_ref = weakref.ref(csc)
            except TypeError:  # non-weakrefable stubs in tests
                pass
        self._ensure_monitors()

        if self._want_defender and self.cycles % SEC_EVERY == 0:
            self._poll_defense()
            did.append("security_poll")

        if self.cycles % LEARN_EVERY == 0:
            if self._start_worker("learn"):
                did.append("learn")
        elif self.cycles % REFLECT_EVERY == 0:
            if self._start_worker("reflect"):
                did.append("reflect")

        if (self.external_enabled and self.cycles % INTEL_EVERY == 0
                and self.online() is True):
            if self._schedule_intel(csc, obs_dict):
                did.append("intel_sweep")

        if self.cycles % AUDIT_EVERY == 0:
            self._audit_outbox.append({
                "event_type": "EVOLUTION", "action": "tick",
                "outcome": "scheduled",
                "correlation_id": f"evolution-{self.cycles}",
                "details": {
                    "did": did,
                    "connectivity": self.connectivity_status(),
                    "experiences": self.experiences_recorded,
                    "outcomes": self.outcomes_recorded,
                }})
        return {"cycle": self.cycles, "did": did}

    def _poll_defense(self) -> None:
        defender = self._defender
        if defender is None:
            return
        try:
            status = defender.get_security_status()
            threat = getattr(defender.get_threat_level(), "name", "NONE")
        except Exception as exc:  # noqa: BLE001
            logger.debug("evolution: defense poll failed: %s", exc)
            return
        self.security_reports += 1
        self._last_security = {"threat_level": threat, "status": status}
        if threat in ("HIGH", "CRITICAL"):
            self._audit_outbox.append({
                "event_type": "SECURITY", "action": "threat_elevated",
                "outcome": threat,
                "correlation_id": f"sec-{self.cycles}",
                "details": {"status": status}})

    def _start_worker(self, kind: str) -> bool:
        """Run one mastery pass on a daemon thread — the trading loop
        never blocks on learning. One worker at a time; a busy worker
        defers to the next interval rather than queuing."""
        if self._mastery_disabled():
            return False
        w = self._worker
        if w is not None and w.is_alive():
            return False
        self._worker = threading.Thread(
            target=self._worker_run, args=(kind,),
            daemon=True, name=f"EvolutionSupervisor-{kind}")
        self._worker.start()
        return True

    def _worker_run(self, kind: str) -> None:
        try:
            orch = self._mastery_orch()
            if kind == "reflect":
                with self._lock:
                    insights = orch.reflect()
                    summary = orch.reflector.get_reflection_summary()
                self.reflections_run += 1
                report = {"kind": "reflect",
                          "insights": len(insights or []),
                          "summary": summary}
            else:
                with self._lock:
                    report = orch.run_continuous_learning(cycles=1)
                    recs = orch.get_learning_recommendations()
                    pending = len(
                        orch.evolver.get_pending_modifications() or [])
                report["kind"] = "learn"
                report["recommendations"] = recs[:5]
                report["pending_proposals"] = pending
                self.learning_cycles_run += 1
            report["ts"] = _utcnow().isoformat()
            self._last_learning = report
            if kind == "learn":
                # Innovation first — it's the load-bearing step and is
                # bounded; peer critique can block minutes on first
                # model load and must never starve it.
                self._maybe_innovate()
                self._maybe_distill_frontier()
                self._peer_study(report)
            self._journal(report)
            self._audit_outbox.append({
                "event_type": "EVOLUTION", "action": f"{kind}_complete",
                "outcome": "ok",
                "correlation_id": f"evo-{kind}-{self.cycles}",
                "details": report})
        except Exception as exc:  # noqa: BLE001
            logger.debug("evolution: %s worker failed: %s", kind, exc)

    def _schedule_intel(self, csc: Any, obs_dict: Dict[str, Any]) -> bool:
        """One bounded external research sweep at a time, as a background
        task — like the research cycle, a slow sweep never queues."""
        task = self._intel_task
        if task is not None and not task.done():
            return False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return False
        topics = self._intel_topics(csc)
        if not topics:
            return False
        self._intel_task = loop.create_task(
            self._intel_sweep(csc, topics))
        return True

    def _intel_topics(self, csc: Any) -> List[str]:
        topics: List[str] = []
        try:
            orch = self._mastery_orch()
            for s in orch.consolidator.get_weakest_skills(2):
                topics.append(f"trading skill improvement {s.name}")
        except Exception:  # noqa: BLE001
            pass
        try:
            q = csc._self_question() if csc is not None else None
            if q:
                topics.append(str(q[0])[:120])
        except Exception:  # noqa: BLE001
            pass
        topic = _INTEL_CURRICULUM[
            self._intel_cursor % len(_INTEL_CURRICULUM)]
        self._intel_cursor += 1
        topics.append(topic)
        return topics[:MAX_INTEL_PER_SWEEP]

    async def _intel_sweep(self, csc: Any, topics: List[str]) -> None:
        results: List[Dict[str, Any]] = []
        fetch = getattr(csc, "_fetch_internet_evidence", None)
        browser = self._web_browser()
        for topic in topics:
            entry: Dict[str, Any] = {"topic": topic}
            # Academic/code evidence — arxiv + github (unavailable in
            # .venv without aiohttp; recorded honestly, never faked).
            if fetch is not None:
                try:
                    entry["research"] = await fetch(topic)
                except Exception as exc:  # noqa: BLE001
                    entry["research"] = {"status": "unavailable",
                                         "reason": str(exc)[:120]}
            # General web — search, then read the top hit's page.
            try:
                web = await browser.search(topic, max_results=3)
                entry["web"] = web
                hits = [r for r in (web.get("results") or [])
                        if str(r.get("url", "")).startswith("http")]
                if hits:
                    page = await browser.fetch(hits[0]["url"],
                                               max_chars=3000)
                    entry["page"] = {"url": hits[0]["url"],
                                     "status": page.get("status"),
                                     "excerpt": (page.get("text") or "")
                                     [:600]}
            except Exception as exc:  # noqa: BLE001
                entry["web"] = {"status": "unavailable",
                                "reason": str(exc)[:120]}
            entry["status"] = ("ok" if any(
                (entry.get(k) or {}).get("status") == "ok"
                for k in ("research", "web")) else "unavailable")
            # Evidence about watched frontier systems becomes structured
            # observations feeding the gated distillation pipeline.
            try:
                made = self._harvest_frontier_obs(topic, entry)
                if made:
                    entry["frontier_observations"] = made
            except Exception as exc:  # noqa: BLE001
                logger.debug("evolution: frontier harvest: %s", exc)
            results.append(entry)
        # Market-news feeds — headline evidence for the same sweep.
        try:
            news = await browser.read_feeds(max_items=6)
        except Exception as exc:  # noqa: BLE001
            news = {"status": "unavailable", "reason": str(exc)[:120],
                    "feeds": []}
        record = {"ts": _utcnow().isoformat(), "results": results,
                  "news": news}
        self.intel_sweeps += 1
        self._last_intel = {
            "ts": record["ts"],
            "topics": [r["topic"] for r in results],
            "ok": sum(1 for r in results if r.get("status") == "ok"),
            "feeds_ok": sum(
                1 for f in (news.get("feeds") or [])
                if f.get("status") == "ok")}
        try:
            intel_dir = self.data_dir / "intel"
            intel_dir.mkdir(parents=True, exist_ok=True)
            fname = intel_dir / (
                "sweep_" + record["ts"].replace(":", "-") + ".json")
            tmp = fname.with_suffix(".tmp")
            tmp.write_text(json.dumps(record, indent=2, default=str))
            os.replace(tmp, fname)
        except Exception as exc:  # noqa: BLE001
            logger.debug("evolution: intel persist failed: %s", exc)
        try:
            await csc._persist_audit_event(
                event_type="EVOLUTION", action="intel_sweep",
                outcome="ok",
                correlation_id=f"intel-{self.intel_sweeps}",
                details=self._last_intel)
        except Exception as exc:  # noqa: BLE001
            logger.debug("evolution: intel audit failed: %s", exc)

    # -- persistence ---------------------------------------------------------

    def _journal_to(self, path: Path, record: Dict[str, Any]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, default=str) + "\n")
        except Exception as exc:  # noqa: BLE001
            logger.debug("evolution: journal write failed: %s", exc)

    def _journal(self, record: Dict[str, Any]) -> None:
        self._journal_to(
            self.data_dir / "evolution_journal.jsonl", record)

    def drain_audits(self) -> List[Dict[str, Any]]:
        out, self._audit_outbox = self._audit_outbox, []
        return out

    def _mastery_disabled(self) -> bool:
        return os.environ.get("TB_SELF_MASTERY", "1").lower() in (
            "0", "false", "off", "no")

    def stop(self) -> None:
        for mon in (self._sentinel, self._defender):
            try:
                if mon is not None:
                    mon.stop()
            except Exception:  # noqa: BLE001
                pass

    # -- transparency ---------------------------------------------------------

    def report(self) -> Dict[str, Any]:
        mastery: Dict[str, Any] = {"status": "not_started"}
        if self._mastery is not None:
            try:
                mastery = self._mastery.to_dict()
            except Exception:  # noqa: BLE001
                mastery = {"status": "error"}
        return {
            "cycles": self.cycles,
            "external_enabled": self.external_enabled,
            "experiences_recorded": self.experiences_recorded,
            "outcomes_recorded": self.outcomes_recorded,
            "reflections_run": self.reflections_run,
            "learning_cycles_run": self.learning_cycles_run,
            "intel_sweeps": self.intel_sweeps,
            "security_reports": self.security_reports,
            "connectivity": self.connectivity_status(),
            "last_security": self._last_security,
            "last_learning": self._last_learning,
            "last_intel": self._last_intel,
            "browser": (self._browser.status()
                        if self._browser is not None
                        else {"status": "not_started"}),
            "ai_peer": {"enabled": self._peer_enabled(),
                        "sessions": self.ai_peer_sessions,
                        **(self._ai_peer.status()
                           if self._ai_peer is not None
                           else {"status": "not_started"})},
            "frontier": {
                "observations": self.frontier_observations,
                "models_buffered": {
                    m: len(b) for m, b in self._frontier_obs.items()},
                "distillation_runs": self.frontier_runs,
                "min_obs": FRONTIER_MIN_OBS},
            "innovation": (self._innovator.status()
                           if getattr(self, "_innovator", None)
                           is not None
                           else {"status": "not_started"}),
            "cadence": {"reflect_every": REFLECT_EVERY,
                        "learn_every": LEARN_EVERY,
                        "intel_every": INTEL_EVERY,
                        "security_every": SEC_EVERY},
            "mastery": mastery,
        }


class _PeerLesson:
    """Decision-shaped shim carrying a peer critique into the
    experience pipeline — outcome class marks it a lesson."""

    def __init__(self, lesson: Dict[str, Any]) -> None:
        self.outcome = "LESSON"
        self.action = "peer_review"
        self.confidence = 0.5
        self.quantity = 0.0
        self.trade_id = ""
        self.reasoning = str(lesson.get("critique") or "")[:400]
        self.dominant_rejection_reason = None


class _PendingDecision:
    """Decision-shaped shim for outcome-attached experiences when the
    original terminal decision is unavailable (cross-session settle)."""

    def __init__(self, pending: Dict[str, Any]) -> None:
        self.outcome = "TRADE_EXECUTED"
        self.action = pending.get("action") or "HOLD"
        self.confidence = float(pending.get("confidence") or 0.5)
        self.quantity = 0.0
        self.trade_id = ""
        self.reasoning = "rehydrated pending prediction"
        self.dominant_rejection_reason = None

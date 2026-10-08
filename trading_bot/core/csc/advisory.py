"""Universal advisory wiring — every AI-adjacent module under CSC.

One AI means exactly two statuses for every AI-named module in the
repository:

- ``attached``: wrapped by ``AdvisoryModuleAdapter`` and registered via
  ``configure_cognition`` — its output joins the evidence channel as
  ``advisory_only`` artifacts with every authority field stripped.
- ``unwired``: explicitly listed in the manifest with a reason — the
  module cannot hold decision authority because nothing reaches it from
  the decision path at all.

The manifest therefore doubles as the audit map: a reader can enumerate
the whole orphan-AI surface and see, per module, either its advisory
capability or why it is inert.
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from trading_bot.cognition.advisory_adapter import AUTHORITY_FIELDS

logger = logging.getLogger("alphaalgo.csc.advisory")


_DIRECTION_MAP = {
    "BUY": "BUY", "LONG": "BUY", "UP": "BUY", "BULLISH": "BUY",
    "SELL": "SELL", "SHORT": "SELL", "DOWN": "SELL", "BEARISH": "SELL",
    "HOLD": None, "NEUTRAL": None, "FLAT": None, "NONE": None,
}
_DIRECTION_KEYS = (
    "direction", "signal", "action", "bias", "recommendation", "verdict")
_CONFIDENCE_KEYS = (
    "confidence", "calibrated_probability", "probability",
    "win_probability", "score", "certainty")


def normalize_advisory(payload: Any) -> Dict[str, Any]:
    """Extract the advisory contract from a stripped payload.

    Returns ``{direction, confidence, evidence}`` — direction is
    BUY/SELL when the module expresses one (None for HOLD/NEUTRAL or
    non-directional output), confidence is [0,1] when expressed. The
    full stripped payload is preserved in ``evidence`` for audit.
    Top-level keys are searched first, then one level of nesting."""
    evidence = payload if isinstance(payload, dict) else {"result": payload}
    direction: Optional[str] = None
    confidence: Optional[float] = None

    def _scan(m: Mapping) -> Tuple[Optional[str], Optional[float]]:
        d: Optional[str] = None
        c: Optional[float] = None
        for key, value in m.items():
            k = str(key).lower()
            if d is None and k in _DIRECTION_KEYS and isinstance(
                    value, str) and value.upper() in _DIRECTION_MAP:
                d = _DIRECTION_MAP[value.upper()]
            if c is None and k in _CONFIDENCE_KEYS and isinstance(
                    value, (int, float)) and not isinstance(value, bool) \
                    and 0.0 <= float(value) <= 1.0:
                c = float(value)
        return d, c

    direction, confidence = _scan(evidence)
    if direction is None and confidence is None:
        for value in evidence.values():
            if isinstance(value, Mapping):
                direction, confidence = _scan(value)
                if direction is not None or confidence is not None:
                    break
    return {"direction": direction, "confidence": confidence,
            "evidence": evidence}


def _strip_authority(payload: Any) -> Any:
    """Recursively remove authority-bearing fields — same policy as
    ``AdvisoryCognitiveBrain``: advisory evidence must not carry approval,
    sizing, or execution vocabulary."""
    if isinstance(payload, Mapping):
        out: Dict[str, Any] = {}
        for key, value in payload.items():
            if key in AUTHORITY_FIELDS or str(key).startswith(
                    ("authorized", "risk_")):
                continue
            out[key] = _strip_authority(value)
        return out
    if isinstance(payload, (list, tuple)):
        return [_strip_authority(item) for item in payload]
    return payload


class AdvisoryModuleAdapter:
    """Wrap any callable ``fn(context) -> result`` as advisory-only.

    The callable may be sync or async; results are converted via
    ``to_dict`` when present, mappings pass through, anything else is
    wrapped as ``{"result": ...}``. Authority fields are stripped before
    the artifact ever reaches the evidence channel.
    """

    def __init__(self, capability_id: str,
                 fn: Callable[[Mapping[str, Any]], Any]) -> None:
        self.capability_id = capability_id
        self._fn = fn

    async def analyze(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        result = self._fn(context)
        if inspect.isawaitable(result):
            result = await result
        if hasattr(result, "to_dict"):
            result = result.to_dict()
        evidence = _strip_authority(result if isinstance(result, Mapping)
                                    else {"result": result})
        norm = normalize_advisory(evidence)
        return {
            "capability_id": self.capability_id,
            "direction": norm["direction"],
            "confidence": norm["confidence"],
            "evidence": norm["evidence"],
            "advisory_only": True,
        }


def _debate_service() -> AdvisoryModuleAdapter:
    """Legacy multi-agent debate as advisory evidence — translated into
    its typed DebateTopic/MarketContext from a raw observation."""
    from trading_bot.agents.multi_agent_debate import (
        DebateTopic, MarketContext, MultiAgentDebateSystem)

    system = MultiAgentDebateSystem()
    _trend_map = {"UP": "UP", "BULLISH": "UP",
                  "DOWN": "DOWN", "BEARISH": "DOWN"}

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        trend = _trend_map.get(
            str(ctx.get("trend") or ctx.get("regime") or "").upper(),
            "SIDEWAYS")
        mc = MarketContext(
            symbol=symbol,
            current_price=float(
                ctx.get("price") or ctx.get("close") or 0.0) or 1.0,
            htf_trend=trend, ltf_trend=trend,
            volatility=float(ctx.get("volatility") or 0.0),
            volume_ratio=float(ctx.get("volume_ratio") or 1.0),
            key_levels={"support": [], "resistance": []},
            news_sentiment=float(ctx.get("sentiment") or 0.0),
            portfolio_exposure=0.0, correlation_risk=0.0)
        return await system.debate(
            DebateTopic(id=f"obs:{symbol}", content=f"market update {symbol}"),
            mc)

    return AdvisoryModuleAdapter("multi_agent_debate", analyze)


def _anomaly_service() -> AdvisoryModuleAdapter:
    """Statistical anomaly detection on the observation's price/vol fields."""
    from trading_bot.market_intelligence.event_detection import (
        AnomalyDetector)

    detector = AnomalyDetector()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        price = ctx.get("price") or ctx.get("close")
        if not isinstance(price, (int, float)):
            return {"status": "no_numeric_price"}
        fn = (getattr(detector, "detect", None)
              or getattr(detector, "analyze", None)
              or getattr(detector, "detect_anomalies", None))
        if fn is None:
            return {"status": "no_detector_entry"}
        return fn({"price": float(price),
                   "volatility": ctx.get("volatility"),
                   "volume": ctx.get("volume"),
                   "symbol": ctx.get("symbol")})

    return AdvisoryModuleAdapter("market_anomaly_detection", analyze)


def _regime_classifier_service() -> AdvisoryModuleAdapter:
    """alphaalgo_core ensemble regime classifier → advisory regime call."""
    from trading_bot.alphaalgo_core.alphaalgo_core import MarketStateEngine

    engine = MarketStateEngine()
    _DIR = {"trending_bull": "BUY", "trending_bear": "SELL"}

    def analyze(ctx: Mapping[str, Any]) -> Any:
        # The engine expects a numeric trend scalar; the observation
        # carries a label. Feed it trend_strength (ER, [0,1]) signed by
        # the label's direction so sign and magnitude both land.
        data = dict(ctx)
        label = str(ctx.get("trend") or "").upper()
        sign = 1.0 if label in ("UP", "BULLISH") else (
            -1.0 if label in ("DOWN", "BEARISH") else 0.0)
        strength = ctx.get("trend_strength")
        data["trend"] = sign * float(strength) if isinstance(
            strength, (int, float)) else float(
                ctx.get("momentum") or 0.0)
        c = engine.classify_regime(data)
        label = getattr(getattr(c, "label", None), "value",
                        str(getattr(c, "label", "")))
        return {
            "label": label,
            "direction": _DIR.get(str(label).lower()),
            "confidence": float(getattr(c, "confidence", 0.0) or 0.0),
            "stability": getattr(c, "stability", None),
            "ensemble_agreement": getattr(c, "ensemble_agreement", None),
            "transition_probability": getattr(
                c, "transition_probability", None),
        }

    return AdvisoryModuleAdapter("regime_classification", analyze)


def _adversarial_trade_service() -> AdvisoryModuleAdapter:
    """adversarial_decision's 9-step red-team evaluated on *both*
    directions — reports which survives; asymmetry is the signal."""
    from trading_bot.adversarial_decision.adversarial_core import (
        AdversarialDecisionEngine)

    engine = AdversarialDecisionEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        price = float(ctx.get("price") or ctx.get("close") or 0.0) or 1.0
        vol = float(ctx.get("volatility") or 0.005) or 0.005
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        results = {}
        for d in ("BUY", "SELL"):
            dec = engine.evaluate_trade(
                symbol=symbol, direction=d, entry_price=price,
                stop_loss=price * (1 - 2 * vol) if d == "BUY"
                else price * (1 + 2 * vol),
                take_profit=price * (1 + 3 * vol) if d == "BUY"
                else price * (1 - 3 * vol),
                market_data=dict(ctx), signal_data=dict(ctx),
                portfolio_state={}, historical_data={})
            results[d.lower()] = {
                "approved": bool(getattr(dec, "approved", False)),
                "outcome": str(getattr(
                    getattr(dec, "outcome", None), "value",
                    getattr(dec, "outcome", ""))),
            }
        direction = (
            "BUY" if results["buy"]["approved"]
            and not results["sell"]["approved"]
            else "SELL" if results["sell"]["approved"]
            and not results["buy"]["approved"] else None)
        return {
            "direction": direction,
            "confidence": 0.6 if direction else None,
            "buy_eval": results["buy"], "sell_eval": results["sell"],
        }

    return AdvisoryModuleAdapter("adversarial_trade_eval", analyze)


def _trend_agent_service() -> AdvisoryModuleAdapter:
    """core_agent_system legacy trend-following agent → AgentProposal."""
    from trading_bot.core_agent_system.migrated_agents.legacy_agents import (
        TrendFollowingAgent)

    agent = TrendFollowingAgent()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return agent.analyze_market(dict(ctx))

    return AdvisoryModuleAdapter("trend_following_agent", analyze)


def _failure_mode_service() -> AdvisoryModuleAdapter:
    """intelligence_core model-degradation detector — evidence-only
    (no direction; still scored for audit completeness)."""
    from trading_bot.intelligence_core.failure_detector import (
        ModelDegradationDetector)

    detector = ModelDegradationDetector()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        outs = detector.detect(dict(ctx), []) or []
        return {"detections": [str(o) for o in outs][:5],
                "count": len(outs)}

    return AdvisoryModuleAdapter("failure_mode_detection", analyze)


# radar_ai is intentionally absent: its OntologyDrivenAgent declares
# analyze/learn abstract — nothing in the package is directly
# observation-callable without writing a stub subclass (fabricated
# analysis is worse than no advisor). Kept in UNWIRED_ORPHAN_MODULES.

# Factories for services that are genuinely observation-callable. Each
# entry is attached at assembly time inside a probe; failures skip the
# service rather than break the runtime.
DEFAULT_ADVISORY_FACTORIES: Tuple[Tuple[str, Callable[[], Any]], ...] = (
    ("multi_agent_debate", _debate_service),
    ("market_anomaly_detection", _anomaly_service),
    ("regime_classification", _regime_classifier_service),
    ("adversarial_trade_eval", _adversarial_trade_service),
    ("trend_following_agent", _trend_agent_service),
    ("failure_mode_detection", _failure_mode_service),
)

# Modules imported by the live path but with no advisory decision role —
# wired as dependencies, not as cognition (kept separate from orphans so
# the audit map stays honest).
LIVE_IMPORTED_NON_ADVISORY: Tuple[Tuple[str, str], ...] = (
    ("world_model", "imported by unified_bot.py — live dependency, "
     "not an advisory service"),
    ("alpha_engine", "imported by execution/__init__.py — live "
     "dependency, sentiment stack not in the decision path"),
    ("autonomous_financial_intelligence", "imported by "
     "core/chainofthoughtreasoner.py — legacy compat, no decision role"),
)

# Orphan modules that are NOT observation-callable advisory services —
# recorded so the audit map is total rather than silently partial.
UNWIRED_ORPHAN_MODULES: Tuple[Tuple[str, str], ...] = (
    ("advanced_intelligence", "monolithic research framework; not an "
     "observation service"),
    ("autonomous_superintelligence", "parallel brain concept; superseded "
     "by CSC assembly"),
    ("core_agent_system", "TrendFollowingAgent attached as "
     "trend_following_agent; framework remainder subsumed by PCA"),
    ("adaptive_systems", "deprecated duplicate improvement systems"),
    ("alpha_research", "research tooling; not a per-observation analyzer"),
    ("alphaalgo_core", "MarketStateEngine attached as "
     "regime_classification; institutional pipeline remainder superseded "
     "by cognition advisory"),
    ("alphaalgo_institutional", "institutional pipeline; superseded"),
    ("brain", "legacy brain dir; superseded by CSC"),
    ("cognitive_architecture", "layered architecture experiments; "
     "superseded by cognition/"),
    ("elite_ai_system", "framework; no per-observation API"),
    ("improvement_agent", "code-analysis agent; not a market advisory"),
    ("intel", "news/macro ingestion; external data dependencies"),
    ("intelligence", "framework; superseded"),
    ("intelligence_core", "ModelDegradationDetector attached as "
     "failure_mode_detection (evidence-only); framework remainder "
     "superseded"),
    ("adversarial_decision", "AdversarialDecisionEngine attached as "
     "adversarial_trade_eval (dual-direction probe); remainder "
     "superseded"),
    ("market_intelligence(other)", "series-hungry analyzers; only "
     "AnomalyDetector is obs-callable"),
    ("meta_learning", "deprecated learner; RSI is canonical"),
    ("neural_integration", "torch-dependent integration layer"),
    ("radar_ai", "agents are abstract (analyze/learn abstract methods); "
     "nothing directly observation-callable without fabricated stubs"),
    ("self_concepts", "self-model scaffolding; not a market advisory"),
    ("self_diagnostic", "system self-checks; not a market advisory"),
    ("self_healing_ai", "framework; superseded"),
    ("self_learning", "deprecated learner; RSI is canonical"),
    ("self_mastery", "framework; superseded"),
    ("sentient_core", "parallel sentience scaffold; superseded"),
    ("signal_discovery", "offline research tooling"),
    ("superintelligence", "framework; superseded"),
    ("superpowerful_ai", "framework; superseded"),
    ("systems_ai", "framework; superseded"),
    ("tamic", "multi-agent framework; superseded"),
    ("ai", "loose modules; superseded"),
    ("ai_core", "framework; superseded"),
    ("ai_engineer", "framework; superseded"),
    ("aads", "alternative decision system; advisory-only path exists "
     "via cognition"),
    ("aamis_v3", "alternate market intelligence; superseded"),
    ("learning", "RL learners; offline training, not advisory"),
    ("agents", "debate attached; remaining framework pieces superseded"),
    ("agents2", "duplicate agent framework; superseded"),
    ("autonomous_learner", "deprecated RSI duplicate per AGENTS.md"),
    ("explainability", "post-hoc explainer; not an advisory service"),
    ("aletheia_autonomous", "framework; superseded"),
)


_DISCOVERY_METHODS = ("analyze", "detect", "classify", "predict",
                      "assess", "estimate", "evaluate")
_DISCOVERY_TIMEOUT_S = 0.5
_DISCOVERY_CAP = 40


def discover_advisory_callables(
        packages: Tuple[str, ...],
        max_services: int = _DISCOVERY_CAP,
        probe: bool = True) -> Tuple[List[AdvisoryModuleAdapter], List[str]]:
    """Long-tail wiring: scan orphan packages for observation-callable
    analyzers and wrap them as advisory services.

    For each ``trading_bot.<pkg>`` top-level module (no recursion): find
    zero-arg-constructible classes exposing one of
    analyze/detect/classify/predict/assess/estimate/evaluate(ctx). The
    method is called with the observation dict only — modules needing
    series or external data fail the probe and are skipped. Every import
    and probe is inside try/except — discovery can never break the
    runtime; it can only add evidence or report a skip.

    Discovered services get ``capability_id = "discovered:<cls>"`` and a
    per-call timeout so a hanging advisor cannot stall the pipeline.
    """
    import asyncio
    import importlib
    import inspect as _inspect
    import pkgutil

    found: List[AdvisoryModuleAdapter] = []
    skipped: List[str] = []
    probe_ctx = {
        "symbol": "EURUSD", "price": 1.09, "close": 1.09,
        "volatility": 0.01, "trend": "FLAT", "trend_strength": 0.1,
        "sentiment": 0.0, "momentum": 0.0,
    }

    async def _probe(svc):
        res = svc.analyze(probe_ctx)
        if _inspect.isawaitable(res):
            res = await asyncio.wait_for(res, _DISCOVERY_TIMEOUT_S)
        return res

    def _probe_sync(svc) -> None:
        try:
            asyncio.get_event_loop().run_until_complete(_probe(svc))
        except RuntimeError:
            asyncio.new_event_loop().run_until_complete(_probe(svc))

    for pkg_name in packages:
        if len(found) >= max_services:
            break
        try:
            pkg = importlib.import_module(f"trading_bot.{pkg_name}")
        except Exception:
            skipped.append(pkg_name)
            continue
        try:
            mod_infos = list(pkgutil.iter_modules(
                pkg.__path__)) if hasattr(pkg, "__path__") else []
        except Exception:
            mod_infos = []
        for mi in mod_infos:
            if len(found) >= max_services:
                break
            try:
                mod = importlib.import_module(
                    f"trading_bot.{pkg_name}.{mi.name}")
            except Exception:
                continue
            for _, cls in vars(mod).items():
                if len(found) >= max_services:
                    break
                if not isinstance(cls, type) or cls.__module__ != mod.__name__:
                    continue
                method = next(
                    (getattr(cls, m) for m in _DISCOVERY_METHODS
                     if callable(getattr(cls, m, None))), None)
                if method is None:
                    continue
                try:
                    if len(_inspect.signature(cls.__init__).parameters) > 1:
                        continue
                    inst = cls()
                except Exception:
                    continue

                cap_id = f"discovered:{cls.__name__}"
                _meth = getattr(inst, next(
                    m for m in _DISCOVERY_METHODS
                    if callable(getattr(inst, m, None))))

                async def _call(ctx, _m=_meth):
                    out = _m(dict(ctx))
                    if _inspect.isawaitable(out):
                        out = await asyncio.wait_for(
                            out, _DISCOVERY_TIMEOUT_S)
                    return out

                svc = AdvisoryModuleAdapter(cap_id, _call)
                try:
                    if probe:
                        _probe_sync(svc)
                    found.append(svc)
                except Exception:
                    skipped.append(cap_id)
    return found, skipped


def attach_advisory_modules(
    csc: Any,
    factories: Optional[Tuple[Tuple[str, Callable[[], Any]], ...]] = None,
    probe: bool = True,
    discover: bool = False,
) -> Tuple[List[str], List[str]]:
    """Attach every wireable advisory service to the CSC.

    Each factory is constructed inside try/except; when ``probe`` is set
    the service is exercised once with a synthetic observation so a
    malformed signature fails at attach time, not mid-pipeline. Returns
    ``(attached_capability_ids, skipped_capability_ids)``.
    """
    import asyncio

    attached: List[str] = []
    skipped: List[str] = []
    for capability_id, factory in (factories or DEFAULT_ADVISORY_FACTORIES):
        try:
            service = factory()
            if probe:
                probe_ctx = {
                    "symbol": "EURUSD", "price": 1.09, "close": 1.09,
                    "volatility": 0.01, "trend": "FLAT", "sentiment": 0.0,
                }
                result = service.analyze(probe_ctx)
                if inspect.isawaitable(result):
                    asyncio.get_event_loop().run_until_complete(result)
            csc.configure_cognition(service)
            attached.append(capability_id)
            logger.info("advisory module attached: %s", capability_id)
        except Exception as exc:
            skipped.append(capability_id)
            logger.warning("advisory module skipped: %s (%s)",
                           capability_id, exc)

    if discover:
        orphan_pkgs = tuple(
            name.split("(")[0] for name, _ in UNWIRED_ORPHAN_MODULES)
        try:
            found, disc_skipped = discover_advisory_callables(orphan_pkgs)
            for svc in found:
                try:
                    csc.configure_cognition(svc)
                    attached.append(svc.capability_id)
                    logger.info("advisory module attached: %s",
                                svc.capability_id)
                except Exception as exc:
                    skipped.append(svc.capability_id)
                    logger.warning("advisory module skipped: %s (%s)",
                                   svc.capability_id, exc)
            skipped.extend(disc_skipped)
        except Exception as exc:
            logger.warning("advisory discovery failed: %s", exc)

    return attached, skipped

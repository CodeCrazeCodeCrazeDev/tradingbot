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
        return {
            "capability_id": self.capability_id,
            "evidence": evidence,
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


# Factories for services that are genuinely observation-callable. Each
# entry is attached at assembly time inside a probe; failures skip the
# service rather than break the runtime.
DEFAULT_ADVISORY_FACTORIES: Tuple[Tuple[str, Callable[[], Any]], ...] = (
    ("multi_agent_debate", _debate_service),
    ("market_anomaly_detection", _anomaly_service),
)

# Orphan modules that are NOT observation-callable advisory services —
# recorded so the audit map is total rather than silently partial.
UNWIRED_ORPHAN_MODULES: Tuple[Tuple[str, str], ...] = (
    ("advanced_intelligence", "monolithic research framework; not an "
     "observation service"),
    ("autonomous_financial_intelligence", "framework; heavyweight "
     "agent fleet, no per-observation API"),
    ("autonomous_superintelligence", "parallel brain concept; superseded "
     "by CSC assembly"),
    ("core_agent_system", "agent framework; subsumed by PCA channel"),
    ("adaptive_systems", "deprecated duplicate improvement systems"),
    ("alpha_research", "research tooling; not a per-observation analyzer"),
    ("alpha_engine", "sentiment/alpha pipeline; heavyweight, external "
     "data dependencies"),
    ("alphaalgo_core", "institutional pipeline; superseded by cognition "
     "advisory"),
    ("alphaalgo_institutional", "institutional pipeline; superseded"),
    ("brain", "legacy brain dir; superseded by CSC"),
    ("cognitive_architecture", "layered architecture experiments; "
     "superseded by cognition/"),
    ("elite_ai_system", "framework; no per-observation API"),
    ("improvement_agent", "code-analysis agent; not a market advisory"),
    ("intel", "news/macro ingestion; external data dependencies"),
    ("intelligence", "framework; superseded"),
    ("intelligence_core", "framework; superseded"),
    ("market_intelligence(other)", "series-hungry analyzers; only "
     "AnomalyDetector is obs-callable"),
    ("meta_learning", "deprecated learner; RSI is canonical"),
    ("neural_integration", "torch-dependent integration layer"),
    ("radar_ai", "strategy evaluation framework; not per-observation"),
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
    ("explainability", "post-hoc explainer; not an advisory service"),
    ("aletheia_autonomous", "framework; superseded"),
)


def attach_advisory_modules(
    csc: Any,
    factories: Optional[Tuple[Tuple[str, Callable[[], Any]], ...]] = None,
    probe: bool = True,
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
    return attached, skipped

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

import asyncio
import collections
import dataclasses
import enum
import inspect
import logging
from datetime import date, datetime
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

import numpy as np

from trading_bot.cognition.advisory_adapter import AUTHORITY_FIELDS

logger = logging.getLogger("alphaalgo.csc.advisory")


def _run_coro_sync(coro: Any, timeout_s: float = 5.0) -> Any:
    """Run a probe coroutine whether or not an event loop is already
    running. Assembly is called from async runtime entry points —
    run_until_complete() would fail inside a live loop, so the probe
    goes to a short-lived thread with its own loop when needed."""
    import asyncio
    import threading
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # Fresh loop instead of asyncio.run() — asyncio.run() calls
        # set_event_loop(None) on exit, which would leave the calling
        # thread with no current loop for downstream callers.
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    box: Dict[str, Any] = {}

    def _worker() -> None:
        try:
            box["r"] = asyncio.run(coro)
        except Exception as exc:  # noqa: BLE001 - re-raised below
            box["e"] = exc

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        raise TimeoutError("advisory probe timed out")
    if "e" in box:
        raise box["e"]
    return box.get("r")


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
                 fn: Callable[[Mapping[str, Any]], Any],
                 timeout_s: float = 5.0) -> None:
        self.capability_id = capability_id
        self._fn = fn
        self.timeout_s = timeout_s

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
        # The engine reads numerics raw — observations can carry
        # strings/sequences under those keys. Coerce or drop.
        for key in ("volatility", "volatility_percentile", "momentum",
                    "momentum_change", "data_quality", "price", "volume"):
            v = data.get(key)
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                data.pop(key, None)
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


# ---------------------------------------------------------------------------
# Shared wiring helpers
# ---------------------------------------------------------------------------


def _num(value: Any) -> Optional[float]:
    """Best-effort float coercion; rejects bools/nan/inf/strings."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


class _BarHistory:
    """Rolling OHLCV window accumulated from per-observation scalars.

    Many legacy analyzers expect a Series/DataFrame of bars while the
    advisory channel delivers one observation dict at a time. Accumulating
    a bounded window makes them honestly observation-callable — they emit
    ``{"status": "warming"}`` until enough real bars exist. No data is
    fabricated: the window is exactly the observations the CSC has seen.
    """

    def __init__(self, maxlen: int = 512) -> None:
        self._bars: "collections.deque" = collections.deque(maxlen=maxlen)

    def add(self, ctx: Mapping[str, Any]) -> int:
        close = _num(ctx.get("close") or ctx.get("price"))
        if close is None:
            return len(self._bars)
        # Analyzers that compute time-deltas or annotate levels expect a
        # numeric "time" column; use the observation's own timestamp when
        # numeric, else the monotonically increasing bar index — never a
        # fabricated wall-clock.
        t = _num(ctx.get("time") or ctx.get("timestamp"))
        self._bars.append({
            "time": float(t) if t is not None else float(len(self._bars)),
            "open": _num(ctx.get("open")) or close,
            "high": _num(ctx.get("high")) or close,
            "low": _num(ctx.get("low")) or close,
            "close": close,
            "volume": _num(ctx.get("volume")) or 0.0,
        })
        return len(self._bars)

    def __len__(self) -> int:
        return len(self._bars)

    def bars(self, last: Optional[int] = None) -> List[Dict[str, float]]:
        bars = list(self._bars)
        return bars[-last:] if last else bars

    def frame(self) -> Any:
        import pandas as pd
        return pd.DataFrame(list(self._bars))

    def prices(self) -> List[float]:
        return [b["close"] for b in self._bars]

    def volumes(self) -> List[float]:
        return [b["volume"] for b in self._bars]

    def returns(self) -> List[float]:
        p = self.prices()
        return [p[i] / p[i - 1] - 1.0 for i in range(1, len(p)) if p[i - 1]]


def _primitive(value: Any) -> Any:
    """Coerce analyzer outputs (enum/datetime/numpy/dataclass) into
    JSON-safe values so advisory evidence survives audit persistence."""
    if isinstance(value, Mapping):
        return {str(k): _primitive(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_primitive(v) for v in value[:50]]
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return value.item()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _payload(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _payload(result: Any) -> Any:
    """Normalize an analyzer return value into a plain mapping."""
    if result is None:
        return {"result": None}
    if hasattr(result, "to_dict"):
        try:
            result = result.to_dict()
        except Exception:  # noqa: BLE001 - fall through to field extraction
            pass
    if dataclasses.is_dataclass(result) and not isinstance(result, type):
        result = {f.name: getattr(result, f.name)
                  for f in dataclasses.fields(result)}
    elif not isinstance(result, Mapping) and hasattr(result, "__dict__"):
        result = {k: v for k, v in vars(result).items()
                  if not k.startswith("_")}
    if isinstance(result, Mapping):
        return _primitive(result)
    if isinstance(result, (list, tuple)):
        return {"items": _primitive(list(result))}
    return {"result": _primitive(result)}


def _market_context(ctx: Mapping[str, Any]) -> Any:
    """Build the debate system's typed MarketContext from a raw obs."""
    from trading_bot.agents.multi_agent_debate import MarketContext
    trend_map = {"UP": "UP", "BULLISH": "UP", "DOWN": "DOWN",
                 "BEARISH": "DOWN"}
    symbol = str(ctx.get("symbol") or "UNKNOWN")
    trend = trend_map.get(
        str(ctx.get("trend") or ctx.get("regime") or "").upper(),
        "SIDEWAYS")
    return MarketContext(
        symbol=symbol,
        current_price=_num(ctx.get("price") or ctx.get("close")) or 1.0,
        htf_trend=trend, ltf_trend=trend,
        volatility=_num(ctx.get("volatility")) or 0.0,
        volume_ratio=_num(ctx.get("volume_ratio")) or 1.0,
        key_levels={"support": [], "resistance": []},
        news_sentiment=_num(ctx.get("sentiment")) or 0.0,
        portfolio_exposure=0.0, correlation_risk=0.0)


def _numeric_fields(ctx: Mapping[str, Any]) -> Dict[str, float]:
    return {str(k): _num(v) for k, v in ctx.items()
            if _num(v) is not None}


def _feature_vector(ctx: Mapping[str, Any]) -> List[float]:
    """Canonical numeric feature order for vector-input advisors."""
    return [
        _num(ctx.get("close") or ctx.get("price")) or 0.0,
        _num(ctx.get("volatility")) or 0.0,
        _num(ctx.get("trend_strength")) or 0.0,
        _num(ctx.get("momentum")) or 0.0,
        _num(ctx.get("rsi")) or 50.0,
        _num(ctx.get("sentiment")) or 0.0,
        _num(ctx.get("volume_ratio")) or 1.0,
    ]


# ---------------------------------------------------------------------------
# Bucket A — previously-unwired orphan packages
# ---------------------------------------------------------------------------


def _alpha_research_state_service() -> AdvisoryModuleAdapter:
    """alpha_research MarketStateClassifier over accumulated real bars."""
    import scipy.stats  # noqa: F401 - module guards scipy; without it
    # the classifier NameErrors mid-run, so skip at attach instead.
    from trading_bot.alpha_research.market_state_classifier import (
        MarketStateClassifier)

    clf = MarketStateClassifier()
    hist = _BarHistory()
    _DIR = {"up": "BUY", "bullish": "BUY", "trending_up": "BUY",
            "down": "SELL", "bearish": "SELL", "trending_down": "SELL"}

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        state = clf.classify(hist.frame())
        regime = str(getattr(getattr(state, "regime", None), "value",
                             getattr(state, "regime", "")))
        direction = _DIR.get(regime.lower())
        td = _num(getattr(state, "trend_direction", None))
        if direction is None and td is not None:
            direction = "BUY" if td > 0.25 else (
                "SELL" if td < -0.25 else None)
        out = _payload(state)
        out["direction"] = direction
        out["bars"] = len(hist)
        return out

    return AdvisoryModuleAdapter("alpha_research_market_state", analyze)


def _alpha_research_risk_service() -> AdvisoryModuleAdapter:
    """alpha_research RiskPredictor on RiskFactors synthesized from ctx."""
    import numpy as _np
    from trading_bot.alpha_research.dynamic_risk_matrix import (
        RiskFactors, RiskPredictor)

    predictor = RiskPredictor()
    _probe_factors = RiskFactors(
        volatility=0.01, volatility_regime="normal", trend_strength=0.2,
        market_regime="ranging", current_drawdown=0.0, portfolio_heat=0.0,
        correlation_risk=0.0, concentration_risk=0.0, recent_win_rate=0.5,
        sharpe_ratio=0.0, vix_level=20.0)
    # predict() scales inputs before checking is_trained, so an unfitted
    # scaler raises; fit it on a neutral factor matrix at attach.
    scaler = getattr(predictor, "scaler", None)
    if scaler is not None:
        n = len(predictor._factors_to_array(_probe_factors))
        scaler.fit(_np.zeros((4, n)))

    def analyze(ctx: Mapping[str, Any]) -> Any:
        trend = str(ctx.get("trend") or "").upper()
        factors = RiskFactors(
            volatility=_num(ctx.get("volatility")) or 0.0,
            volatility_regime="high" if (
                _num(ctx.get("volatility")) or 0.0) > 0.02 else "normal",
            trend_strength=_num(ctx.get("trend_strength")) or 0.0,
            market_regime=("trending" if trend in ("UP", "DOWN")
                           else "ranging"),
            current_drawdown=_num(ctx.get("drawdown")) or 0.0,
            portfolio_heat=_num(ctx.get("portfolio_heat")) or 0.0,
            correlation_risk=_num(ctx.get("correlation_risk")) or 0.0,
            concentration_risk=_num(ctx.get("concentration_risk")) or 0.0,
            recent_win_rate=_num(ctx.get("win_rate")) or 0.5,
            sharpe_ratio=_num(ctx.get("sharpe")) or 0.0,
            vix_level=_num(ctx.get("vix")) or 20.0,
        )
        return _payload(predictor.predict(factors))

    return AdvisoryModuleAdapter("alpha_research_risk_matrix", analyze)


def _alpha_research_predator_service() -> AdvisoryModuleAdapter:
    """alpha_research PredatorDefenseSystem — stream-fed per observation.

    Each observation updates quote/trade/candle state with real values;
    detectors fire only once their internal windows fill — honest
    streaming evidence, never fabricated ticks.
    """
    from trading_bot.alpha_research.predator_defense import (
        PredatorDefenseSystem)

    system = PredatorDefenseSystem()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        price = _num(ctx.get("close") or ctx.get("price"))
        if price is None:
            return {"status": "no_price"}
        spread = _num(ctx.get("spread")) or price * 1e-4
        ts = datetime.now()
        try:
            system.update_quote(price - spread / 2, price + spread / 2, ts)
        except Exception:  # noqa: BLE001 - optional feed
            pass
        vol = _num(ctx.get("volume"))
        if vol:
            try:
                system.update_trade(price, vol, str(
                    ctx.get("trend") or "buy").lower(), ts)
            except Exception:  # noqa: BLE001 - optional feed
                pass
        hist_bar = {
            "open": _num(ctx.get("open")) or price,
            "high": _num(ctx.get("high")) or price,
            "low": _num(ctx.get("low")) or price,
        }
        try:
            system.update_candle(hist_bar["open"], hist_bar["high"],
                                 hist_bar["low"], price, vol or 0.0)
        except Exception:  # noqa: BLE001 - optional feed
            pass
        signals = system.detect_predators() or []
        return {"signals": [_payload(s) for s in signals[:5]],
                "count": len(signals)}

    return AdvisoryModuleAdapter("alpha_research_predator_defense", analyze)


def _alpha_research_footprint_service() -> AdvisoryModuleAdapter:
    """alpha_research market-impact predator read: footprint + stop-hunt."""
    from trading_bot.alpha_research.market_impact_predator import (
        InstitutionalFootprintAnalyzer, StopHuntPredictor)

    footprint = InstitutionalFootprintAnalyzer()
    stop_hunt = StopHuntPredictor()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        return {
            "footprint": _payload(footprint.analyze(symbol)),
            "stop_hunt": _payload(stop_hunt.predict(symbol)),
        }

    return AdvisoryModuleAdapter("alpha_research_footprint", analyze)


def _institutional_selection_service() -> AdvisoryModuleAdapter:
    """alphaalgo_institutional layer-1 analyzers on a MarketCharacteristics
    synthesized from the observation's real liquidity/quality fields."""
    from trading_bot.alphaalgo_institutional.core_types import MarketType
    from trading_bot.alphaalgo_institutional.layer1_market_selection import (
        InefficiencyAnalyzer, LiquidityAnalyzer, MarketCharacteristics,
        StructuralAnalyzer)

    analyzers = {"liquidity": LiquidityAnalyzer(),
                 "inefficiency": InefficiencyAnalyzer(),
                 "structural": StructuralAnalyzer()}

    def analyze(ctx: Mapping[str, Any]) -> Any:
        ch = MarketCharacteristics(
            market_type=MarketType.FX,
            avg_daily_volume=_num(ctx.get("volume")) or 0.0,
            bid_ask_spread_bps=(
                (_num(ctx.get("spread")) or 0.0)
                / max(_num(ctx.get("close") or ctx.get("price")) or 1.0,
                      1e-9)) * 1e4,
            volume_stability=1.0 - min(
                abs((_num(ctx.get("volume_ratio")) or 1.0) - 1.0), 1.0),
            data_completeness=_num(ctx.get("data_quality")) or 0.0,
        )
        return {name: _payload(a.analyze(ch))
                for name, a in analyzers.items()}

    return AdvisoryModuleAdapter("institutional_market_selection", analyze)


def _brain_technical_service() -> AdvisoryModuleAdapter:
    """brain tier-1 momentum + volatility analysis over accumulated bars."""
    from trading_bot.brain.tier1_technical import (
        MomentumAnalysis, VolatilityAnalysis)

    momentum, vol = MomentumAnalysis(), VolatilityAnalysis()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        df = hist.frame()
        out = {"momentum": _payload(momentum.analyze(df)),
               "volatility": _payload(vol.analyze(df))}
        sig = _num((out["momentum"] or {}).get("momentum_signal"))
        if sig is not None:
            out["direction"] = "BUY" if sig > 0.2 else (
                "SELL" if sig < -0.2 else None)
            out["confidence"] = min(abs(sig), 1.0)
        return out

    return AdvisoryModuleAdapter("brain_technical_analysis", analyze)


def _brain_regime_service() -> AdvisoryModuleAdapter:
    """brain tier-4 regime + phase classifiers over accumulated bars."""
    from trading_bot.brain.tier4_regime import (
        MarketPhaseClassifier, VolatilityRegimeClassifier)

    vol_clf, phase_clf = VolatilityRegimeClassifier(), MarketPhaseClassifier()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        df = hist.frame()
        return {"volatility_regime": _payload(vol_clf.classify(df)),
                "market_phase": _payload(phase_clf.classify(df))}

    return AdvisoryModuleAdapter("brain_regime_classification", analyze)


def _cognitive_regime_service() -> AdvisoryModuleAdapter:
    """cognitive_architecture layer-1 regime classifier + transition
    detector over accumulated real bars."""
    from trading_bot.cognitive_architecture.layer1_market_state_detection import (  # noqa: E501
        RegimeClassifier, TransitionDetector)

    clf, transitions = RegimeClassifier(), TransitionDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        df = hist.frame()
        out = {"regime": _payload(clf.classify(df, None))}
        try:
            out["transition"] = _payload(transitions.detect(
                _numeric_fields(ctx), df))
        except Exception:  # noqa: BLE001 - optional second opinion
            out["transition"] = None
        return out

    return AdvisoryModuleAdapter("cognitive_architecture_regime", analyze)


def _cognitive_perf_service() -> AdvisoryModuleAdapter:
    """cognitive_architecture layer-7 PerformanceEvaluator on the
    observation's numeric fields (evidence-only self-evaluation)."""
    from trading_bot.cognitive_architecture.layer7_self_healing import (
        PerformanceEvaluator)

    evaluator = PerformanceEvaluator()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(evaluator.evaluate(_numeric_fields(ctx)))

    return AdvisoryModuleAdapter("cognitive_performance_eval", analyze)


def _elite_factor_service() -> AdvisoryModuleAdapter:
    """elite_ai_system multi-factor confirmation evaluated on BOTH
    directions — asymmetry is the advisory signal."""
    from trading_bot.elite_ai_system.multi_factor_matrix import (
        MultiFactorConfirmationMatrix)

    matrix = MultiFactorConfirmationMatrix()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        market = dict(ctx)
        out = {}
        for label, direction in (("long", "LONG"), ("short", "SHORT")):
            res = matrix.evaluate(symbol, direction, market, dict(ctx))
            p = _payload(res)
            out[label] = p
        def _score(p):
            for k in ("overall_score", "total_score", "score",
                      "confirmation_score", "weighted_score"):
                v = _num((p or {}).get(k)) if isinstance(p, Mapping) else None
                if v is not None:
                    return v
            return None
        ls, ss = _score(out["long"]), _score(out["short"])
        # A saturated matrix (identical scores both directions — e.g. all
        # factors at the 50.0 error/default) discriminates nothing; report
        # the indeterminate result, not two fake STRONG recommendations.
        if ls is None or ss is None or ls == ss:
            return {"status": "indeterminate",
                    "long_score": ls, "short_score": ss}
        out["direction"] = "BUY" if ls > ss else "SELL"
        return out

    return AdvisoryModuleAdapter("elite_factor_matrix", analyze)


def _adaptive_regime_service() -> AdvisoryModuleAdapter:
    """adaptive_systems MarketRegimeDetector over accumulated bars."""
    from trading_bot.adaptive_systems.market_regime import (
        MarketRegimeDetector)

    detector = MarketRegimeDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        signal = detector.detect_regime(hist.frame())
        out = _payload(signal)
        regime = str(out.get("regime") or out.get("regime_type") or ""
                       ).lower()
        if "bull" in regime or regime.endswith("up"):
            out["direction"] = "BUY"
        elif "bear" in regime or regime.endswith("down"):
            out["direction"] = "SELL"
        return out

    return AdvisoryModuleAdapter("adaptive_market_regime", analyze)


def _adaptive_learning_service() -> AdvisoryModuleAdapter:
    """adaptive_systems AdaptiveLearningEngine.predict — returns None
    until a model is trained; evidence-only."""
    from trading_bot.adaptive_systems.adaptive_learning import (
        AdaptiveLearningEngine, ModelType)

    engine = AdaptiveLearningEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        from sklearn.exceptions import NotFittedError
        from sklearn.utils.validation import check_is_fitted
        preds = {}
        trained = 0
        for mt in ModelType:
            model = engine.models.get(mt)
            if model is None:
                preds[mt.value] = None
                continue
            try:
                check_is_fitted(model)
            except NotFittedError:
                preds[mt.value] = "untrained"
                continue
            except Exception:  # noqa: BLE001 - odd model, try predict
                pass
            try:
                preds[mt.value] = engine.predict(mt, _feature_vector(ctx))
            except Exception:  # noqa: BLE001 - per-model failures skip
                preds[mt.value] = None
            else:
                trained += isinstance(preds[mt.value], (int, float))
        return {"predictions": preds, "models_trained": trained}

    return AdvisoryModuleAdapter("adaptive_learning_predict", analyze)


def _intelligence_strategy_service() -> AdvisoryModuleAdapter:
    """intelligence SelfLearningEngine — best-known strategy per
    (symbol, regime) from its own journal DB; evidence-only."""
    from trading_bot.intelligence.self_learning_engine import (
        SelfLearningEngine)

    engine = SelfLearningEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        regime = str(ctx.get("trend") or ctx.get("regime") or "FLAT")
        try:
            best = engine.get_best_strategy(symbol, regime)
        except Exception:  # noqa: BLE001 - db may be empty
            best = None
        try:
            insights = [str(i) for i in (engine.analyze() or [])][:5]
        except Exception:  # noqa: BLE001
            insights = []
        return {"best_strategy": _primitive(best), "insights": insights}

    return AdvisoryModuleAdapter("intelligence_strategy_stats", analyze)


def _self_learning_ensemble_service() -> AdvisoryModuleAdapter:
    """self_learning EnsembleLearner.predict on the canonical feature
    vector — untrained models predict zeros; evidence-only."""
    from trading_bot.self_learning.core_learning_engine import (
        EnsembleLearner, ModelType)

    ensemble = EnsembleLearner()
    try:
        ensemble.initialize(ModelType.PRICE_DIRECTION)
    except Exception:  # noqa: BLE001 - predict tolerates uninitialized
        pass

    def analyze(ctx: Mapping[str, Any]) -> Any:
        out = ensemble.predict(np.asarray([_feature_vector(ctx)]))
        if isinstance(out, tuple):
            preds, conf = out
        else:
            preds, conf = out, None
        # Evidence-only: untrained models return zeros, and a zero vector
        # must not be misread as a directional call — no direction field.
        return {"predictions": _primitive(
                    list(preds) if hasattr(preds, "__iter__") else preds),
                "confidence": _num(conf)}

    return AdvisoryModuleAdapter("self_learning_ensemble", analyze)


def _signal_regime_change_service() -> AdvisoryModuleAdapter:
    """signal_discovery RegimeChangeDetector over accumulated closes."""
    from trading_bot.signal_discovery.anomaly_detection.regime_change import (  # noqa: E501
        RegimeChangeDetector)

    detector = RegimeChangeDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 20:
            return {"status": "warming", "bars": n}
        changes = detector.detect(hist.prices(), hist.volumes()) or []
        return {"regime_changes": [_payload(c) for c in changes[:5]],
                "count": len(changes),
                "current_regime": _primitive(
                    detector.get_current_regime(hist.prices()))}

    return AdvisoryModuleAdapter("signal_regime_change", analyze)


def _signal_outlier_service() -> AdvisoryModuleAdapter:
    """signal_discovery StatisticalOutlierDetector over accumulated
    closes — flags the tail of the real price window."""
    from trading_bot.signal_discovery.anomaly_detection.statistical_outliers import (  # noqa: E501
        StatisticalOutlierDetector)

    detector = StatisticalOutlierDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 20:
            return {"status": "warming", "bars": n}
        outs = detector.detect(hist.prices()) or []
        return {"outliers": [_primitive(o) for o in outs[:10]],
                "count": len(outs)}

    return AdvisoryModuleAdapter("signal_statistical_outliers", analyze)


def _tamic_market_time_service() -> AdvisoryModuleAdapter:
    """tamic MarketTimeEngine — registers real obs baselines and reports
    active market-time acceleration events for the symbol."""
    from trading_bot.tamic.market_time import MarketTimeEngine

    engine = MarketTimeEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        for metric in ("price", "volatility", "volume"):
            v = _num(ctx.get(metric) or ctx.get("close")
                     if metric == "price" else ctx.get(metric))
            if v is not None:
                try:
                    engine.register_baseline(symbol, metric, v)
                except Exception:  # noqa: BLE001
                    pass
        try:
            events = engine.get_active_events(symbol) or []
        except Exception:  # noqa: BLE001
            events = []
        return {"active_events": [_payload(e) for e in events[:5]],
                "count": len(events)}

    return AdvisoryModuleAdapter("tamic_market_time", analyze)

def _institutional_time_service() -> AdvisoryModuleAdapter:
    """tamic InstitutionalTimeEngine — calendar-driven flow flags
    (month/quarter-end rebalancing, expiry, roll, central-bank windows).
    Honest derivable context: obs timestamp → institutional calendar."""
    from trading_bot.tamic.institutional_time import (
        InstitutionalTimeEngine)

    engine = InstitutionalTimeEngine()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        result = await engine.check_institutional_flows(
            symbol, dict(ctx))
        flows = getattr(result, "active_flows", None) or \
            getattr(result, "flows", None) or []
        payload = _payload(result) if isinstance(result, Mapping) else {}
        flow_dicts = [_payload(f) for f in list(flows)[:6]]
        strong = [f for f in flow_dicts
                  if str(f.get("strength", "")).upper()
                  in ("STRONG", "EXTREME")]
        return {"institutional_flows": flow_dicts,
                "strong_flow_count": len(strong),
                "flow_types": [str(f.get("flow_type") or f.get("type"))
                               for f in flow_dicts],
                **({"result": payload} if payload else {})}

    return AdvisoryModuleAdapter("tamic_institutional_time", analyze)


def _optionality_service() -> AdvisoryModuleAdapter:
    """tamic OptionalityPreservationEngine — preservation-pressure
    evidence: low optionality value means the current setup offers poor
    asymmetric opportunity. Evidence only — it may not size or veto."""
    from trading_bot.tamic.optionality import (
        OptionalityPreservationEngine)
    from trading_bot.tamic.core import TimeHorizon

    engine = OptionalityPreservationEngine()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        try:
            result = await engine.evaluate_optionality(
                symbol, TimeHorizon.INTRADAY, dict(ctx))
        except Exception as exc:  # noqa: BLE001
            return {"status": "no_data", "reason": str(exc)[:100]}
        value = getattr(result, "optionality_value", None)
        metrics = getattr(result, "metrics", None)
        payload = _payload(result) if isinstance(result, Mapping) else {}
        cat = getattr(value, "value", value)
        return {"optionality_value": str(cat),
                "preservation_pressure":
                    str(cat).upper() in ("LOW", "MINIMAL"),
                "metrics": _payload(metrics) if metrics else payload}

    return AdvisoryModuleAdapter("tamic_optionality", analyze)

def _time_risk_service() -> AdvisoryModuleAdapter:
    """tamic DrawdownSpeedMonitor + RecoveryDurationTracker — time-based
    risk evidence: drawdown velocity, recovery duration, loss clustering.
    Accumulates real price history itself (warm-up seeding fills it);
    evidence only — it may not size or veto."""
    from trading_bot.tamic.time_risk import (
        DrawdownSpeedMonitor, RecoveryDurationTracker)
    from trading_bot.tamic.core import TimeHorizon

    monitor = DrawdownSpeedMonitor()
    recovery = RecoveryDurationTracker()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        price = _num(ctx.get("close") or ctx.get("price"))
        if price is None or price <= 0:
            return {"status": "no_data", "reason": "no price"}
        try:
            dd = await monitor.update(
                symbol, TimeHorizon.INTRADAY, float(price))
            rec = await recovery.update(
                symbol, TimeHorizon.INTRADAY, float(price), dd or {})
        except Exception as exc:  # noqa: BLE001
            return {"status": "no_data", "reason": str(exc)[:100]}
        return {
            "drawdown": _payload(dd) if isinstance(
                dd, Mapping) else {},
            "recovery": _payload(rec) if isinstance(
                rec, Mapping) else {},
            "drawdown_velocity": str((dd or {}).get(
                "drawdown_speed") or (dd or {}).get("speed") or ""),
            "loss_clustering": (dd or {}).get("loss_clustering"),
            "recovery_state": (rec or {}).get(
                "recovery_classification") or (rec or {}).get("state"),
        }

    return AdvisoryModuleAdapter("tamic_time_risk", analyze)


def _self_diagnostic_service() -> AdvisoryModuleAdapter:
    """self_diagnostic ComprehensiveDiagnosticSuite health score —
    evidence-only system-health read alongside the market obs."""
    from trading_bot.self_diagnostic.comprehensive_diagnostics import (
        ComprehensiveDiagnosticSuite)

    suite = ComprehensiveDiagnosticSuite()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return {"health_score": _primitive(suite.get_health_score())}

    return AdvisoryModuleAdapter("self_diagnostic_health", analyze)


def _aletheia_audit_service() -> AdvisoryModuleAdapter:
    """aletheia_autonomous decision auditor — audits the observation
    framed as a hypothetical paper-stage proposal (never approved)."""
    from trading_bot.aletheia_autonomous.financial_decision_auditor import (  # noqa: E501
        AletheiaFinancialDecisionAuditor)

    auditor = AletheiaFinancialDecisionAuditor()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        proposal = {
            "symbol": str(ctx.get("symbol") or "UNKNOWN"),
            "action": "observe",
            "price": _num(ctx.get("close") or ctx.get("price")),
            "metrics": _numeric_fields(ctx),
        }
        audit = auditor.audit_decision(proposal, target_stage="paper")
        return _payload(audit)

    return AdvisoryModuleAdapter("aletheia_decision_audit", analyze)


def _superintel_regime_service() -> AdvisoryModuleAdapter:
    """superintelligence RegimeStrategyEngine.analyze_and_activate over
    accumulated real closes — regime + strategy-fit evidence."""
    import pandas as pd
    from trading_bot.superintelligence.regime_strategy_engine import (
        RegimeStrategyEngine)

    engine = RegimeStrategyEngine()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 30:
            return {"status": "warming", "bars": n}
        prices = pd.Series(hist.prices())
        volumes = pd.Series(hist.volumes())
        chars, activation = engine.analyze_and_activate(prices, volumes)
        regime = str(getattr(getattr(chars, "regime", None), "value",
                             getattr(chars, "regime", "")))
        out = {"regime": _payload(chars), "activation": _payload(activation)}
        rl = regime.lower()
        if "bull" in rl or "up" in rl:
            out["direction"] = "BUY"
        elif "bear" in rl or "down" in rl:
            out["direction"] = "SELL"
        return out

    return AdvisoryModuleAdapter("superintelligence_regime_strategy",
                                 analyze)


def _systems_stress_service() -> AdvisoryModuleAdapter:
    """systems_ai SyntheticStressSimulator — stresses a naive buy-and-hold
    return stream built from accumulated real closes."""
    from trading_bot.systems_ai.advanced_features import (
        StressScenario, SyntheticStressSimulator)

    sim = SyntheticStressSimulator()
    hist = _BarHistory()

    def _buy_hold(prices, volumes):
        return [prices[i] / prices[i - 1] - 1.0
                for i in range(1, len(prices)) if prices[i - 1]]

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 30:
            return {"status": "warming", "bars": n}
        results = {}
        for scenario in (StressScenario.VOLATILITY_SPIKE,
                         StressScenario.FLASH_CRASH):
            try:
                res = sim.run_stress_test(
                    scenario, hist.prices(), hist.volumes(), _buy_hold)
                results[scenario.value] = _payload(res)
            except Exception as exc:  # noqa: BLE001
                results[scenario.value] = {"error": str(exc)}
        return results

    return AdvisoryModuleAdapter("systems_ai_stress_test", analyze)


# ---------------------------------------------------------------------------
# Bucket B — additional capabilities from partially-wired packages
# ---------------------------------------------------------------------------


def _make_legacy_agent_service(capability_id: str, cls_name: str
                               ) -> Callable[[], AdvisoryModuleAdapter]:
    """core_agent_system legacy agents share analyze_market(dict) ->
    AgentProposal; bind one factory per agent class."""
    def factory() -> AdvisoryModuleAdapter:
        from trading_bot.core_agent_system.migrated_agents import (
            legacy_agents)
        agent = getattr(legacy_agents, cls_name)()

        def analyze(ctx: Mapping[str, Any]) -> Any:
            return _payload(agent.analyze_market(dict(ctx)))

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _make_agents2_service(capability_id: str, cls_name: str
                          ) -> Callable[[], AdvisoryModuleAdapter]:
    """agents2 specialized agents expose the same analyze_market(dict)
    surface under their own base_agent — wire as distinct capabilities."""
    def factory() -> AdvisoryModuleAdapter:
        from trading_bot.agents2 import specialized_agents
        agent = getattr(specialized_agents, cls_name)()

        def analyze(ctx: Mapping[str, Any]) -> Any:
            return _payload(agent.analyze_market(dict(ctx)))

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _make_failure_detector_service(capability_id: str, cls_name: str
                                   ) -> Callable[[], AdvisoryModuleAdapter]:
    """intelligence_core detectors share detect(current_state,
    historical_states) — feed the obs plus a rolling history window."""
    def factory() -> AdvisoryModuleAdapter:
        from trading_bot.intelligence_core import failure_detector
        detector = getattr(failure_detector, cls_name)()
        history: "collections.deque" = collections.deque(maxlen=50)

        def analyze(ctx: Mapping[str, Any]) -> Any:
            state = dict(ctx)
            history.append(state)
            outs = detector.detect(state, list(history)) or []
            return {"detections": [_payload(o) for o in outs[:5]],
                    "count": len(outs)}

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _make_anomaly_classifier_service(
        capability_id: str, module: str, cls_name: str
        ) -> Callable[[], AdvisoryModuleAdapter]:
    """market_intelligence Layer-2 classifiers consume MarketAnomaly —
    synthesize one honestly from the observation's real fields."""
    def factory() -> AdvisoryModuleAdapter:
        import importlib
        from trading_bot.signal_discovery.agents.base_agent import (
            AnomalyType, DataSource, MarketAnomaly)
        classifier = getattr(importlib.import_module(module), cls_name)()

        def analyze(ctx: Mapping[str, Any]) -> Any:
            symbol = str(ctx.get("symbol") or "UNKNOWN")
            desc = " ".join(
                f"{k}={v}" for k, v in sorted(ctx.items())
                if isinstance(v, (int, float, str)))[:400]
            anomaly = MarketAnomaly(
                agent_id="csc_advisory", agent_type="observation",
                data_source=DataSource.TRADINGVIEW,
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                confidence=_num(ctx.get("trend_strength")) or 0.5,
                primary_asset=symbol, raw_data=dict(ctx),
                description=f"{symbol} market observation: {desc}",
                detection_method="csc_observation",
                statistical_significance=_num(
                    ctx.get("volatility")) or 0.0)
            res = classifier.classify(anomaly)
            return {"classification": _payload(res)}

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _make_debate_agent_service(capability_id: str, cls_name: str
                               ) -> Callable[[], AdvisoryModuleAdapter]:
    """Individual multi_agent_debate agents take the typed MarketContext
    — the same builder the debate service uses."""
    def factory() -> AdvisoryModuleAdapter:
        from trading_bot.agents import multi_agent_debate
        agent = getattr(multi_agent_debate, cls_name)()

        def analyze(ctx: Mapping[str, Any]) -> Any:
            return _payload(agent.analyze(_market_context(ctx)))

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _adversarial_failure_match_service() -> AdvisoryModuleAdapter:
    """adversarial_decision FailureMatcher — current conditions vs the
    recorded failure-mode database; evidence-only."""
    from trading_bot.adversarial_decision.failure_matcher import (
        FailureMatcher)

    matcher = FailureMatcher()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(matcher.check_failure_match(
            market_data=dict(ctx), signal_data=dict(ctx),
            portfolio_state={}, historical_data={}))

    return AdvisoryModuleAdapter("adversarial_failure_match", analyze)


def _alphaalgo_perf_sensor_service() -> AdvisoryModuleAdapter:
    """alphaalgo_core MultiMetricPerformanceSensor — records the realized
    per-observation return under the obs's regime label, then reports
    computed metrics once the window fills."""
    from trading_bot.alphaalgo_core.alphaalgo_core import (
        MultiMetricPerformanceSensor, RegimeLabel)

    sensor = MultiMetricPerformanceSensor()
    hist = _BarHistory()
    _REGIME = {"UP": RegimeLabel.TRENDING_BULL,
               "BULLISH": RegimeLabel.TRENDING_BULL,
               "DOWN": RegimeLabel.TRENDING_BEAR,
               "BEARISH": RegimeLabel.TRENDING_BEAR}

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        rets = hist.returns()
        if rets:
            label = _REGIME.get(
                str(ctx.get("trend") or "").upper(), RegimeLabel.RANGING)
            try:
                sensor.record_return(rets[-1], label)
            except Exception:  # noqa: BLE001 - optional feed
                pass
        return _payload(sensor.compute_metrics())

    return AdvisoryModuleAdapter("alphaalgo_performance_sensor", analyze)


def _market_physics_service() -> AdvisoryModuleAdapter:
    """alphaalgo_core MarketPhysicsFilter — structural tradability read
    on a market_data dict synthesized from the observation."""
    from trading_bot.alphaalgo_core.market_physics_filter import (
        MarketPhysicsFilter)

    filt = MarketPhysicsFilter()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        bars = hist.bars(20)
        # Module expects ohlcv as a dict of column lists, not bar dicts.
        market_data = {
            "ohlcv": {k: [b[k] for b in bars]
                      for k in ("open", "high", "low", "close", "volume")},
            "orderbook": {},
            "trades": [],
            "liquidity": {"volume": _num(ctx.get("volume")) or 0.0},
            "volatility": {"current": _num(ctx.get("volatility")) or 0.0},
            "microstructure": {
                "spread": _num(ctx.get("spread")) or 0.0,
                "volume_ratio": _num(ctx.get("volume_ratio")) or 1.0,
            },
        }
        out = filt.process(
            str(ctx.get("symbol") or "UNKNOWN"), market_data)
        if inspect.isawaitable(out):
            out = await out
        return _payload(out)

    return AdvisoryModuleAdapter("market_physics_filter", analyze)


# ---------------------------------------------------------------------------
# Bucket C — loose orphan root files
# ---------------------------------------------------------------------------


def _alphaalgo_5star_risk_service() -> AdvisoryModuleAdapter:
    """alphaalgo_5star.calculate_risk_metrics over realized returns —
    lazy ctor leaves torch models un-initialized; only the numpy risk
    path is exercised."""
    import numpy as _np
    import trading_bot.alphaalgo_5star as _a5

    # Module calls loguru-style logger.success() on a stdlib logger;
    # shim it so construction succeeds.
    _log = getattr(_a5, "logger", None)
    if _log is not None and not hasattr(_log, "success"):
        _log.success = _log.info
    from trading_bot.alphaalgo_5star import AlphaAlgo5Star

    system = AlphaAlgo5Star({})
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        rets = hist.returns()
        if len(rets) < 10:
            return {"status": "warming", "bars": len(hist)}
        return _payload(system.calculate_risk_metrics(
            _np.asarray(rets, dtype=float)))

    return AdvisoryModuleAdapter("alphaalgo_5star_risk_metrics", analyze)


def _world2agent_bridge_service() -> AdvisoryModuleAdapter:
    """world2agent bridge — publishes the observation as a world-state
    snapshot on a private bus and reports the enriched agent context;
    evidence-only provenance wiring."""
    from trading_bot.a2a import A2AMessageBus
    from trading_bot.world2agent import World2AgentBridge

    bridge = World2AgentBridge(A2AMessageBus())

    def analyze(ctx: Mapping[str, Any]) -> Any:
        snapshot = bridge.publish_world_state(
            source="csc_advisory", world_state=dict(ctx))
        enriched = bridge.build_agent_context(
            "csc", base_payload={"symbol": ctx.get("symbol")})
        return {"snapshot": _payload(snapshot),
                "context": _payload(enriched)}

    return AdvisoryModuleAdapter("world2agent_bridge", analyze)


# without writing a stub subclass.

# ---------------------------------------------------------------------------
# Bucket A2 — second-pass wiring: the remaining orphan packages and the
# additional capabilities audit found obs-callable. Same conventions:
# _BarHistory accumulates real bars ({"status": "warming"} until full),
# _payload normalizes returns, every factory is probe-gated.
# ---------------------------------------------------------------------------


def _enum_direction(value: Any) -> Optional[str]:
    """Map an enum-or-string market label to BUY/SELL/None."""
    s = str(getattr(value, "value", value) or "").upper()
    if s in _DIRECTION_MAP:
        return _DIRECTION_MAP[s]
    if any(k in s for k in ("BULL", "UPTREND", "LONG", "UP")):
        return "BUY"
    if any(k in s for k in ("BEAR", "DOWNTREND", "SHORT", "DOWN")):
        return "SELL"
    return None


def _moe_router_service() -> AdvisoryModuleAdapter:
    """advanced_intelligence MixtureOfExpertsRouter — action probability
    distribution on the canonical feature vector (numpy-only path; the
    deep-model remainder of the package stays tensor-bound)."""
    from trading_bot.advanced_intelligence.advanced_ai_ml.\
        mixture_of_experts import MixtureOfExpertsRouter

    router = MixtureOfExpertsRouter()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        feats = np.asarray(_feature_vector(ctx)[:4], dtype=float)
        out = router.predict(feats)
        regime = router.detect_regime(feats)
        if inspect.isawaitable(out):
            out = await out
        if inspect.isawaitable(regime):
            regime = await regime
        payload = _payload(out)
        payload["regime"] = str(regime)
        return payload

    return AdvisoryModuleAdapter("mixture_of_experts", analyze)


def _microstructure_service() -> AdvisoryModuleAdapter:
    """adaptive_systems MarketMicrostructureAnalyzer over real bars."""
    from trading_bot.adaptive_systems.market_microstructure import (
        MarketMicrostructureAnalyzer)

    analyzer = MarketMicrostructureAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        df = hist.frame()
        df["price"] = df["close"]
        signals = analyzer.analyze_microstructure(df) or []
        inst = analyzer.detect_institutional_activity(df) or []
        return {"signals": [_payload(s) for s in signals[:5]],
                "institutional": [_payload(s) for s in inst[:5]]}

    return AdvisoryModuleAdapter("market_microstructure", analyze)


def _economy_agent_service(
        capability_id: str, agent_name: str
        ) -> Callable[[], AdvisoryModuleAdapter]:
    """cognitive_architecture layer-3 economy agents share
    analyze(dict) -> AgentDecision."""
    def factory() -> AdvisoryModuleAdapter:
        from trading_bot.cognitive_architecture import (
            layer3_cognitive_economy as econ)
        agent = getattr(econ, agent_name)()

        def analyze(ctx: Mapping[str, Any]) -> Any:
            # Agents read fixed typed keys; coerce from the observation
            # where present, honest defaults otherwise.
            sig = ctx.get("signal")
            data = {
                "data_quality": _num(ctx.get("data_quality")) or 0.8,
                "signal": dict(sig) if isinstance(sig, Mapping) else {
                    "direction": str(ctx.get("direction") or "hold"),
                    "confidence": _num(ctx.get("confidence")) or 0.5},
                "risk_score": (_num(ctx.get("risk_score"))
                               or _num(ctx.get("volatility")) or 0.5),
                "position_size": _num(ctx.get("position_size")) or 0.0,
                "pattern_confidence": (
                    _num(ctx.get("pattern_confidence"))
                    or _num(ctx.get("trend_strength")) or 0.5),
                "system_health": _num(ctx.get("system_health")) or 1.0,
            }
            return _payload(agent.analyze(data))

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _regime_transition_service() -> AdvisoryModuleAdapter:
    """cognitive_architecture CUSUM change-point detector on real closes."""
    from trading_bot.cognitive_architecture.\
        layer1_market_state_detection import TransitionDetector

    detector = TransitionDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 44:
            return {"status": "warming", "bars": n}
        import pandas as pd
        return {"change_point": bool(detector.detect_change_point(
            pd.Series(hist.prices())))}

    return AdvisoryModuleAdapter("regime_transition_detector", analyze)


def _market_psychology_service() -> AdvisoryModuleAdapter:
    """elite_ai_system MarketPsychologyEngine — crowd-psychology state;
    only a clear |sentiment|>0.2 expresses a direction."""
    from trading_bot.elite_ai_system.market_psychology_engine import (
        MarketPsychologyEngine)

    engine = MarketPsychologyEngine()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        state = engine.analyze_psychology(dict(ctx))
        if inspect.isawaitable(state):
            state = await state
        s = _num(getattr(getattr(state, "sentiment", None),
                         "overall_sentiment", None)) or 0.0
        out = _payload(state)
        out["direction"] = ("BUY" if s > 0.2 else
                            "SELL" if s < -0.2 else None)
        out["confidence"] = min(abs(s), 1.0) or None
        return out

    return AdvisoryModuleAdapter("market_psychology", analyze)


def _improvement_findings_service() -> AdvisoryModuleAdapter:
    """improvement_agent analyzer — its findings on the obs dict are
    honest (usually empty on non-code input); evidence-only."""
    from trading_bot.improvement_agent.agent_orchestrator import (
        ImprovementAgent)

    agent = ImprovementAgent()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(await agent.analyze(dict(ctx)))

    return AdvisoryModuleAdapter("improvement_findings", analyze)


def _neural_hub_service() -> AdvisoryModuleAdapter:
    """neural_integration hub — topology report is the honest callable
    surface (no modules register off the canonical path)."""
    from trading_bot.neural_integration.neural_hub import (
        NeuralIntegrationHub)

    hub = NeuralIntegrationHub()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(hub.get_neural_topology())

    return AdvisoryModuleAdapter("neural_hub_topology", analyze)


def _hivemind_analyst_service() -> AdvisoryModuleAdapter:
    """radar_ai MarketAnalystAgent — async swarm analyst on the obs."""
    from trading_bot.radar_ai.hivemind_controller import (
        MarketAnalystAgent)

    agent = MarketAnalystAgent()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        d = await agent.analyze(dict(ctx))
        out = _payload(d)
        for key in ("action", "decision", "recommendation", "signal"):
            direction = _enum_direction(out.get(key))
            if direction:
                out["direction"] = direction
                break
        return out

    return AdvisoryModuleAdapter("hivemind_analyst", analyze)


def _radar_regime_service() -> AdvisoryModuleAdapter:
    """radar_ai understanding_engine RegimeDetector over real bars."""
    from trading_bot.radar_ai.understanding_engine import RegimeDetector

    detector = RegimeDetector()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 30:
            return {"status": "warming", "bars": n}
        r = await detector.detect_regime(hist.frame())
        out = _payload(r)
        regime = getattr(r, "current_regime", getattr(r, "regime", None))
        out["direction"] = _enum_direction(regime)
        return out

    return AdvisoryModuleAdapter("radar_regime", analyze)


def _self_concept_service() -> AdvisoryModuleAdapter:
    """self_concepts engine — pre-trade concept pass over the obs."""
    from trading_bot.self_concepts.self_concept_engine import (
        SelfConceptEngine)

    engine = SelfConceptEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(engine.pre_trade_process(dict(ctx)))

    return AdvisoryModuleAdapter("self_concept_guard", analyze)


def _self_healing_health_service() -> AdvisoryModuleAdapter:
    """self_healing_ai orchestrator — system health evidence."""
    from trading_bot.self_healing_ai.orchestrator import (
        SelfHealingOrchestrator)

    orch = SelfHealingOrchestrator()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        h = orch.get_system_health()
        return {"health": str(getattr(h, "value", h))}

    return AdvisoryModuleAdapter("system_health", analyze)


def _self_learning_health_service() -> AdvisoryModuleAdapter:
    """self_learning SelfHealingSystem — issue-detection health dict."""
    from trading_bot.self_learning.self_healing_system import (
        SelfHealingSystem)

    system = SelfHealingSystem()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(system.get_system_health())

    return AdvisoryModuleAdapter("self_learning_health", analyze)


def _mastery_reflection_service() -> AdvisoryModuleAdapter:
    """self_mastery MasteryOrchestrator.reflect — self-review insights
    (empty until trades are recorded; honest evidence)."""
    from trading_bot.self_mastery.mastery_orchestrator import (
        MasteryOrchestrator)

    orch = MasteryOrchestrator()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        insights = orch.reflect() or []
        return {"insights": [_payload(i) for i in insights[:5]],
                "count": len(insights)}

    return AdvisoryModuleAdapter("mastery_reflection", analyze)


def _introspection_service() -> AdvisoryModuleAdapter:
    """sentient_core Introspector — code health score evidence."""
    from trading_bot.sentient_core.introspector import Introspector

    intro = Introspector()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return {"code_health_score": _primitive(
            intro.get_code_health_score())}

    return AdvisoryModuleAdapter("codebase_introspection", analyze)


def _regime_memory_service() -> AdvisoryModuleAdapter:
    """superintelligence MemorySystem — lessons for the current regime."""
    from trading_bot.superintelligence.memory_systems import MemorySystem

    memory = MemorySystem()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        regime = str(ctx.get("trend") or ctx.get("regime") or "unknown")
        lessons = memory.recall_lessons_for_regime(regime) or []
        return {"regime": regime,
                "lessons": [_payload(l) for l in lessons[:5]],
                "count": len(lessons)}

    return AdvisoryModuleAdapter("regime_memory", analyze)


def _trend_reversal_service() -> AdvisoryModuleAdapter:
    """superpowerful_ai PredictiveIntelligence — reversal probability
    over accumulated real bars."""
    from trading_bot.superpowerful_ai.predictive_intelligence import (
        PredictiveIntelligence)

    intel = PredictiveIntelligence()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        p = await intel.predict_trend_reversal(
            hist.frame(), str(ctx.get("symbol") or "UNKNOWN"))
        return _payload(p)

    return AdvisoryModuleAdapter("trend_reversal", analyze)


def _regime_discovery_service() -> AdvisoryModuleAdapter:
    """superpowerful_ai SelfDiscoveryEngine — unsupervised regime +
    anomaly pass over accumulated real bars."""
    from trading_bot.superpowerful_ai.self_discovery_engine import (
        SelfDiscoveryEngine)

    engine = SelfDiscoveryEngine()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        frame = hist.frame()
        state = await engine.detect_regime(frame, symbol)
        anomalies = await engine.detect_anomalies(frame, symbol)
        out = _payload(state)
        out["anomalies"] = _primitive(list(anomalies or [])[:5])
        regime = getattr(state, "regime", None)
        out["direction"] = _enum_direction(regime)
        return out

    return AdvisoryModuleAdapter("regime_discovery", analyze)


def _strategy_selector_service() -> AdvisoryModuleAdapter:
    """superpowerful_ai StrategicIntelligence — strategy selection on
    the observation as market_state (evidence, never an order)."""
    from trading_bot.superpowerful_ai.strategic_intelligence import (
        StrategicIntelligence)

    intel = StrategicIntelligence()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(await intel.select_optimal_strategy(dict(ctx)))

    return AdvisoryModuleAdapter("strategy_selector", analyze)


def _data_drift_service() -> AdvisoryModuleAdapter:
    """systems_ai DriftDetector — feature-distribution drift evidence
    (first calls establish the baseline; returns None => no drift)."""
    from trading_bot.systems_ai.self_improvement import DriftDetector

    detector = DriftDetector()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        dists = {k: {"mean": v, "std": 0.0}
                 for k, v in _numeric_fields(ctx).items()}
        out = detector.detect_data_drift(dists)
        if out is None:
            return {"drift_detected": False}
        return {"drift_detected": True, "detail": _payload(out)}

    return AdvisoryModuleAdapter("data_drift", analyze)


def _performance_decay_service() -> AdvisoryModuleAdapter:
    """systems_ai PerformanceTracker — decay check on obs metrics."""
    from trading_bot.systems_ai.self_improvement import PerformanceTracker

    tracker = PerformanceTracker()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        decayed, detail = tracker.detect_decay(_numeric_fields(ctx))
        return {"decay_detected": bool(decayed),
                "detail": _payload(detail)}

    return AdvisoryModuleAdapter("performance_decay", analyze)


def _signal_decay_service() -> AdvisoryModuleAdapter:
    """tamic SignalDecay — extracted-signal decay analysis on real bars."""
    from trading_bot.tamic.signal_decay import SignalDecay

    decay = SignalDecay()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        r = await decay.analyze_signals(
            str(ctx.get("symbol") or "UNKNOWN"),
            str(ctx.get("timeframe") or "M15"), hist.frame())
        return _payload(r)

    return AdvisoryModuleAdapter("signal_decay", analyze)


def _autonomous_tuner_service() -> AdvisoryModuleAdapter:
    """ai AutonomousTuner — tuner-state summary evidence (its hub is
    torch-bound; the tuner is not)."""
    from trading_bot.ai.autonomous_tuner import AutonomousTuner

    tuner = AutonomousTuner()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(tuner.get_tuning_summary())

    return AdvisoryModuleAdapter("autonomous_tuner", analyze)


def _planner_agent_service() -> AdvisoryModuleAdapter:
    """ai_core PlannerAgent — plan list on the obs dict."""
    from trading_bot.ai_core.agents.orchestrator import PlannerAgent

    agent = PlannerAgent()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        out = await agent.process(dict(ctx)) or []
        return {"plans": [_payload(o) for o in out[:5]],
                "count": len(out)}

    return AdvisoryModuleAdapter("planner_agent", analyze)


def _alpha_evolve_service() -> AdvisoryModuleAdapter:
    """aads AlphaEvolveEngine — evolved signal genome as evidence (the
    deploy/backtest surface is never invoked)."""
    from types import SimpleNamespace
    from trading_bot.aads.core.alpha_evolve_engine import (
        AlphaEvolveEngine)

    engine = AlphaEvolveEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        evo_ctx = SimpleNamespace(
            asset_class="fx", previous_best_code=None,
            previous_best_sharpe=0.0,
            regime=str(ctx.get("trend") or ctx.get("regime") or "unknown"),
            timeframe=str(ctx.get("timeframe") or "M15"),
            rejection_history=[])
        return _payload(engine.generate_signal(evo_ctx))

    return AdvisoryModuleAdapter("alpha_evolve_signal", analyze)


def _polymarket_service() -> AdvisoryModuleAdapter:
    """aads PolymarketModule — probability estimate on a contract
    synthesized from the obs; capital path untouched."""
    from types import SimpleNamespace
    from trading_bot.aads.core.polymarket import PolymarketModule

    module = PolymarketModule()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        contract = SimpleNamespace(
            category="macro", confidence=0.5, contract_id="obs",
            edge=0.0, implied_probability=0.5, liquidity=10000.0,
            no_price=0.5, our_probability=None,
            question=f"{ctx.get('symbol') or 'EURUSD'} up next bar?",
            resolution_date=None, resolved_outcome=None, status="open",
            volume_=10000.0, yes_price=0.5)
        est = module.estimate_probability(contract, dict(ctx))
        trade = module.evaluate_trade(contract)
        out = _payload(est)
        if isinstance(trade, Mapping):
            out["edge"] = _primitive(trade.get("edge"))
            out["side"] = str(trade.get("side"))
        return out

    return AdvisoryModuleAdapter("polymarket_estimate", analyze)


def _maven_stats_service() -> AdvisoryModuleAdapter:
    """aads MavenDecisionEngine — wargame decision statistics evidence."""
    from trading_bot.aads.core.maven_decision import MavenDecisionEngine

    engine = MavenDecisionEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(engine.get_statistics())

    return AdvisoryModuleAdapter("maven_stats", analyze)


def _aamis_service() -> AdvisoryModuleAdapter:
    """aamis_v3 master orchestrator — its (deliberately abstaining)
    consolidated report is real advisory evidence."""
    from trading_bot.aamis_v3.aamis_master_orchestrator import (
        AAMISMasterOrchestrator)

    orch = AAMISMasterOrchestrator()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        report = await orch.analyze_market(dict(ctx))
        out = _payload(report)
        decision = getattr(report, "decision", None)
        out["direction"] = _enum_direction(
            getattr(decision, "action", None))
        return out

    return AdvisoryModuleAdapter("aamis_market", analyze)


def _learner_knowledge_service() -> AdvisoryModuleAdapter:
    """autonomous_learner KnowledgeBuilder — curriculum summary evidence
    (module is deprecated for authority, not for evidence)."""
    from trading_bot.autonomous_learner.knowledge_builder import (
        KnowledgeBuilder)

    builder = KnowledgeBuilder()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(builder.get_knowledge_summary())

    return AdvisoryModuleAdapter("learner_knowledge", analyze)


def _decision_explainer_service() -> AdvisoryModuleAdapter:
    """explainability TradingExplainer — NL read on the obs framed as a
    hypothetical decision (evidence text, never a directive)."""
    from trading_bot.explainability import TradingExplainer

    explainer = TradingExplainer()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return {"explanation": str(
            explainer.explain_decision(dict(ctx)))[:400]}

    return AdvisoryModuleAdapter("decision_explainer", analyze)


def _alpha_weakness_service() -> AdvisoryModuleAdapter:
    """alpha_research VolatilityRegimeDetector — |returns| history vs
    current volatility; weakness-severity evidence."""
    from trading_bot.alpha_research.weakness_detection import (
        VolatilityRegimeDetector)

    detector = VolatilityRegimeDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 12:
            return {"status": "warming", "bars": n}
        vol_hist = [abs(r) for r in hist.returns()[:-1]]
        current = _num(ctx.get("volatility")) or abs(
            hist.returns()[-1] or 0.0)
        flag, message, severity = detector.detect(vol_hist, current)
        return {"weakness_detected": bool(flag), "message": str(message),
                "severity": str(getattr(severity, "value", severity))}

    return AdvisoryModuleAdapter("alpha_weakness_detector", analyze)


# --- Bucket B additions ---


def _regime_hostility_service() -> AdvisoryModuleAdapter:
    """alphaalgo_core RegimeHostilityEngine — hostile-regime scenarios
    for a reference mean_reversion config on obs-derived market data."""
    from trading_bot.alphaalgo_core.regime_hostility_engine import (
        RegimeHostilityEngine)

    engine = RegimeHostilityEngine()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        market_data = {
            "regime": {
                "current": str(ctx.get("trend") or ctx.get("regime")
                               or "unknown"),
                "transition_probability": 0.1},
            "volatility": {
                "current": _num(ctx.get("volatility")) or 0.01,
                "percentile": _num(ctx.get("volatility_percentile"))
                or 0.5},
            "correlation": {"stability": 0.5},
            "liquidity": {"score": 0.5},
            "signals": {"strength": _num(ctx.get("trend_strength"))
                        or 0.5},
        }
        r = await engine.process(
            "advisory_probe",
            {"family": "mean_reversion",
             "timeframe": str(ctx.get("timeframe") or "M15")},
            market_data)
        return _payload(r)

    return AdvisoryModuleAdapter("regime_hostility", analyze)


def _policy_network_service() -> AdvisoryModuleAdapter:
    """core_agent_system PolicyNetwork — action distribution evidence."""
    from trading_bot.core_agent_system.policy_value_network import (
        PolicyNetwork)

    net = PolicyNetwork()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        out = net.predict(dict(ctx))
        if inspect.isawaitable(out):
            out = await out
        actions = getattr(out, "actions", None) or []
        ranked = sorted(
            (a for a in actions if isinstance(a, Mapping)),
            key=lambda a: a.get("probability") or 0.0, reverse=True)
        top = ranked[0] if ranked else {}
        return {"top_action": str(top.get("type", "")),
                "direction": _enum_direction(top.get("type")),
                "confidence": _num(top.get("probability")),
                "actions": {str(a.get("type")): _num(a.get("probability"))
                            for a in ranked[:6]}}

    return AdvisoryModuleAdapter("policy_network", analyze)


def _value_network_service() -> AdvisoryModuleAdapter:
    """core_agent_system ValueNetwork — state-value estimate evidence."""
    from trading_bot.core_agent_system.policy_value_network import (
        ValueNetwork)

    net = ValueNetwork()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        value = net.evaluate(dict(ctx))
        if inspect.isawaitable(value):
            value = await value
        return {"state_value": _primitive(value)}

    return AdvisoryModuleAdapter("value_network", analyze)


def _hardening_score_service() -> AdvisoryModuleAdapter:
    """intelligence_core AdversarialHardening — hardening posture."""
    from trading_bot.intelligence_core.adversarial_hardening import (
        AdversarialHardening)

    hard = AdversarialHardening()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return {"hardening_score": _primitive(hard.get_hardening_score())}

    return AdvisoryModuleAdapter("adversarial_hardening", analyze)


def _hypothesis_generator_service() -> AdvisoryModuleAdapter:
    """intelligence_core MarketBehaviorGenerator — concrete hypothesis
    generator (HypothesisGenerator ABC itself stays abstract)."""
    from trading_bot.intelligence_core.hypothesis_engine import (
        MarketBehaviorGenerator)

    gen = MarketBehaviorGenerator()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hyps = gen.generate(dict(ctx)) or []
        return {"hypotheses": [_payload(h) for h in hyps[:5]],
                "count": len(hyps)}

    return AdvisoryModuleAdapter("hypothesis_generator", analyze)


def _bloomberg_benchmark_service() -> AdvisoryModuleAdapter:
    """intelligence_core BloombergBenchmark — domain benchmark score
    evidence (self-assessment, not market direction)."""
    from trading_bot.intelligence_core.self_improvement import (
        BloombergBenchmark)

    bench = BloombergBenchmark()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return {"benchmark_score": _primitive(
            bench.get_overall_score())}

    return AdvisoryModuleAdapter("bloomberg_benchmark", analyze)


def _directional_bias_service() -> AdvisoryModuleAdapter:
    """market_intelligence MarketBiasDetector — directional bias over
    accumulated real bars."""
    from trading_bot.market_intelligence.bias_analysis import (
        MarketBiasDetector)

    detector = MarketBiasDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        bias = detector.detect_directional_bias(hist.frame()) or {}
        overall = bias.get("overall_bias") or {}
        direction = overall.get("direction")
        return {"bias": _primitive(bias),
                "direction": _enum_direction(direction),
                "strength": str(getattr(overall.get("strength"), "value",
                                        overall.get("strength", "")))}

    return AdvisoryModuleAdapter("directional_bias", analyze)


def _orderbook_imbalance_service() -> AdvisoryModuleAdapter:
    """market_intelligence MarketDataMonitor — order-book imbalance and
    volume-spike reads on the symbol's monitored stream."""
    from trading_bot.market_intelligence.data_monitoring import (
        MarketDataMonitor)

    monitor = MarketDataMonitor()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "EURUSD")
        imbalances = monitor.detect_order_book_imbalances(symbol) or []
        spikes = monitor.detect_volume_spikes(
            symbol, str(ctx.get("timeframe") or "M15")) or []
        return {"imbalances": [_payload(i) for i in imbalances[:5]],
                "volume_spikes": [_payload(s) for s in spikes[:5]],
                "imbalance_count": len(imbalances),
                "spike_count": len(spikes)}

    return AdvisoryModuleAdapter("orderbook_imbalance", analyze)


# --- Bucket C additions ---


# unified_ai_brain is deliberately absent: it is a QUARANTINED parallel
# brain (tests/foundation/test_brain_quarantine.py) — the canonical path,
# including this module, may not import it at all.


def _aean_cycle_service() -> AdvisoryModuleAdapter:
    """aean_meta_intelligence_layer — bounded meta-cycle report. The
    cycle consumes FrontierObservation/BenchmarkTask objects the market
    obs cannot supply, so an empty cycle is the honest callable surface."""
    from trading_bot.aean_meta_intelligence_layer import (
        AEANMetaIntelligenceLayer)

    layer = AEANMetaIntelligenceLayer(monthly_infra_spend_usd=1000.0)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(layer.run_cycle(
            observations=[], benchmark_tasks=[]))

    return AdvisoryModuleAdapter("aean_meta_cycle", analyze)


def _elite_master_service() -> AdvisoryModuleAdapter:
    """elite_master_system.py — feeds the observation through
    update_market_data and reports analyze_market's real subsystem
    analyses (empty until its engines register; its execute_trade
    surface is never touched)."""
    from trading_bot.elite_master_system import EliteMasterSystem

    system = EliteMasterSystem()

    def _sync_round(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        try:
            res = system.update_market_data(symbol, dict(ctx))
            if inspect.isawaitable(res):
                res = _run_coro_sync(res)
        except Exception:  # noqa: BLE001 - optional feed
            pass
        result = system.analyze_market(symbol)
        if inspect.isawaitable(result):
            result = _run_coro_sync(result)
        return result

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        # Run in an executor: with torch present this module spins up heavy
        # subsystems synchronously — a direct await would block the whole
        # loop past the per-service timeout and stall the pipeline.
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _sync_round, ctx)
        return _payload(result)

    return AdvisoryModuleAdapter("elite_master_analysis", analyze)


def _complete_impl_service() -> AdvisoryModuleAdapter:
    """complete_implementation.py — MarketRegimeDetector fed real closes
    plus SessionManager session multiplier; evidence-only."""
    from trading_bot.complete_implementation import (
        MarketRegimeDetector, SessionManager)

    detector, sessions = MarketRegimeDetector(), SessionManager()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        close = _num(ctx.get("close") or ctx.get("price"))
        if close is not None:
            detector.update(close)
        out = {"bars": n}
        try:
            regime = detector.get_regime()
            out["regime"] = str(regime)
            out["direction"] = _enum_direction(regime)
        except Exception:  # noqa: BLE001 - detector may need warmup
            out["regime"] = None
        try:
            out["session_multiplier"] = _primitive(
                sessions.get_session_risk_multiplier(
                    str(ctx.get("symbol") or "EURUSD")))
        except Exception:  # noqa: BLE001
            out["session_multiplier"] = None
        return out

    return AdvisoryModuleAdapter("complete_impl_market_intel", analyze)


# radar_ai note: MarketAnalystAgent + understanding_engine.RegimeDetector
# are wired above; OntologyDrivenAgent declares analyze/learn abstract —
# that part stays quarantined since nothing is directly
# observation-callable without fabricated stubs.


# ---------------------------------------------------------------------------
# Bucket D — non-AI-named orphan dirs (obs-callable surfaces found by audit)
# ---------------------------------------------------------------------------

def _hivemind_collective_service() -> AdvisoryModuleAdapter:
    """hivemind TradingHiveMind — collective vote over real OHLCV bars."""
    from trading_bot.hivemind.coordinator import TradingHiveMind

    mind = TradingHiveMind()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        out = mind.analyze(
            str(ctx.get("symbol") or "UNKNOWN"),
            {"ohlcv": hist.bars(50),
             "sentiment": {"score": _num(ctx.get("sentiment")) or 0.0}},
            str(ctx.get("timeframe") or "M15"))
        if inspect.isawaitable(out):
            out = await out
        return _payload(out)

    return AdvisoryModuleAdapter("hivemind_collective", analyze, timeout_s=20.0)


def _hivemind_threat_service() -> AdvisoryModuleAdapter:
    """hivemind military ThreatAssessor — pure dict math on obs fields."""
    from trading_bot.hivemind.military_protocols import ThreatAssessor

    assessor = ThreatAssessor()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        market_data = {
            "volatility_ratio": _num(ctx.get("volatility_ratio")) or 1.0,
            "liquidity_score": _num(ctx.get("liquidity_score"))
                or _num(ctx.get("volume_ratio")) or 0.8,
            "high_impact_events_24h": _num(ctx.get("high_impact_events")) or 0,
        }
        portfolio_state = {
            "current_drawdown": _num(ctx.get("current_drawdown")) or 0.0,
        }
        return _payload(assessor.assess(market_data, portfolio_state))

    return AdvisoryModuleAdapter("hivemind_threat_assessment", analyze)


def _apex_regime_service() -> AdvisoryModuleAdapter:
    """apex_fi RegimeSurveillanceAI — feed obs indicators, classify regimes."""
    from trading_bot.apex_fi.layer6_risk_governance import RegimeSurveillanceAI

    surv = RegimeSurveillanceAI()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        vol = _num(ctx.get("volatility"))
        surv.update_indicators({
            "vix": (vol * 100.0) if vol is not None else 15.0,
            "liquidity_score": _num(ctx.get("volume_ratio")) or 1.0,
        })
        out = {}
        for name in ("volatility", "correlation", "liquidity", "trend"):
            fn = getattr(surv, f"classify_{name}_regime", None)
            if callable(fn):
                try:
                    regime, conf = fn()
                    out[f"{name}_regime"] = str(regime)
                    out[f"{name}_confidence"] = _num(conf)
                except Exception:  # noqa: BLE001
                    out[f"{name}_regime"] = None
        trans = getattr(surv, "detect_regime_transition", None)
        if callable(trans):
            try:
                out["transition"] = _primitive(trans())
            except Exception:  # noqa: BLE001
                out["transition"] = None
        return out

    return AdvisoryModuleAdapter("apex_regime_surveillance", analyze)


def _apex_cost_service() -> AdvisoryModuleAdapter:
    """apex_fi TransactionCostEngine — predicted cost bps from obs fields."""
    from trading_bot.apex_fi.layer5_execution_intelligence import (
        TransactionCostEngine)

    engine = TransactionCostEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        price = _num(ctx.get("close") or ctx.get("price")) or 0.0
        spread = _num(ctx.get("spread"))
        spread_bps = (spread / price * 1e4) if (spread and price) else 5.0
        cost = engine.predict_cost(
            str(ctx.get("symbol") or "UNKNOWN"),
            _num(ctx.get("quantity")) or 0.01,
            spread_bps,
            _num(ctx.get("market_depth")) or 1.0,
            _num(ctx.get("volatility")) or 0.01,
            _num(ctx.get("participation_rate")) or 0.05)
        return {"predicted_cost_bps": _num(cost), "spread_bps": spread_bps}

    return AdvisoryModuleAdapter("apex_transaction_cost", analyze)


def _dg_volatility_service() -> AdvisoryModuleAdapter:
    """decision_governance VolatilityRegimeDetector — feed realized vol
    computed from accumulated bars, then classify."""
    from trading_bot.decision_governance.layer4_regime_engine import (
        VolatilityRegimeDetector)

    det = VolatilityRegimeDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        closes = [b["close"] for b in hist.bars(30)]
        if len(closes) >= 2:
            rets = [closes[i] / closes[i - 1] - 1.0
                    for i in range(1, len(closes)) if closes[i - 1]]
            if rets:
                mean = sum(rets) / len(rets)
                var = sum((r - mean) ** 2 for r in rets) / len(rets)
                det.update_realized_vol("1d", var ** 0.5)
                det.update_realized_vol("5d", var ** 0.5)
                det.update_realized_vol("20d", var ** 0.5)
        return _payload(det.detect_volatility_regime())

    return AdvisoryModuleAdapter("dg_volatility_regime", analyze)


def _gets_structure_service() -> AdvisoryModuleAdapter:
    """gets MarketStructureAnalyzer — needs a MarketData dataclass built
    from the observation."""
    from trading_bot.gets.multimodal_awareness import MarketStructureAnalyzer
    from trading_bot.gets.types import MarketData

    analyzer = MarketStructureAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        last = hist.bars(1)
        close = _num(ctx.get("close") or ctx.get("price")) or 0.0
        bar = last[0] if last else {
            "open": close, "high": close, "low": close,
            "close": close, "volume": 0.0}
        md = MarketData(
            symbol=str(ctx.get("symbol") or "UNKNOWN"),
            timestamp=datetime.now(),
            ohlcv=bar,
            bid_ask_spread=_num(ctx.get("spread")),
            realized_volatility=_num(ctx.get("volatility")))
        return _payload(analyzer.analyze(md))

    return AdvisoryModuleAdapter("gets_market_structure", analyze)


def _feedback_perf_service() -> AdvisoryModuleAdapter:
    """feedback FeedbackAnalyzer — realized performance evidence read from
    its sqlite store; returns an error dict honestly when empty."""
    from trading_bot.feedback.analyzer import FeedbackAnalyzer

    analyzer = FeedbackAnalyzer()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        del ctx
        return _payload(analyzer.analyze_performance(lookback_days=30))

    return AdvisoryModuleAdapter("feedback_performance", analyze)


def _alpha_evolve_regime_service() -> AdvisoryModuleAdapter:
    """alpha_evolve RegimeClassifier — classify_regime on a DataFrame of
    accumulated real closes. Deprecated RSI duplicate wired evidence-only."""
    import pandas as pd
    from trading_bot.alpha_evolve.regime_aware_backtester import (
        RegimeClassifier)

    clf = RegimeClassifier()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        bars = hist.bars(60)
        if len(bars) < 10:
            return {"status": "warming", "bars": len(bars)}
        df = pd.DataFrame(bars)
        regime = clf.classify_regime(df)
        return {"regime": str(regime),
                "direction": _enum_direction(regime),
                "bars": len(bars)}

    return AdvisoryModuleAdapter("alpha_evolve_regime", analyze)


# neuros_evolution note: research_agents.MicrostructureExpert fabricates
# analysis via np.random — quarantined like aads aip_agents.
# LoadBalancingIntelligence needs a `network` ctor arg — no obs surface.
# perplexity_trading note: QuantAgent needs an AgentContext task graph and
# the orchestrator calls the external Perplexity API — external dep.
# cos note: DecisionSupportSystem requires cognition_store +
# simulation_engine ctor collaborators — not constructible standalone.
# services note: AAMISService.analyze_symbol delegates to a started
# orchestrator; IntelligenceDirectorateService.evaluate_signal needs a
# Signal object — no obs-dict surface.
# adversarial_verification note: RedTeam.analyze_strategy needs strategy
# source code — operates on candidates, not observations.
# events/metrics/registry/orchestration/master_system/meta_governance/
# golden_path/realtime_trading_core/deepseek_engineer/tests note: plumbing,
# authority surfaces, code tools or test packages — no obs-callable
# analyzer exists to wire.


# ---------------------------------------------------------------------------
# Bucket E — analysis/ package + cross-dir obs-feedable analyzers (audit
# pass: 44 real technical analyzers orphaned under legacy_main/main_v1)
# ---------------------------------------------------------------------------

def _bars_df(hist: "_BarHistory", last: int):
    """Accumulated bars as a DataFrame — the input shape every analysis/
    analyzer expects. Returns None until enough real bars exist."""
    bars = hist.bars(last)
    if len(bars) < 20:
        return None
    import pandas as pd
    return pd.DataFrame(bars)


def _md_dict(ctx: Mapping[str, Any], hist: "_BarHistory") -> Dict[str, Any]:
    """market_data dict shape used by analysis/* dict-consumers."""
    bars = hist.bars(50)
    return {
        "symbol": str(ctx.get("symbol") or "UNKNOWN"),
        "ohlcv": bars,
        "close": _num(ctx.get("close") or ctx.get("price")),
        "spread": _num(ctx.get("spread")) or 0.0,
        "volume": _num(ctx.get("volume")) or 0.0,
        "volatility": _num(ctx.get("volatility")) or 0.0,
        "volume_ratio": _num(ctx.get("volume_ratio")) or 1.0,
        "trend": ctx.get("trend"),
    }


def _analysis_patterns_service() -> AdvisoryModuleAdapter:
    """analysis/candlestick_validation PatternDetector — candle patterns
    over accumulated bars."""
    from trading_bot.analysis.candlestick_validation import PatternDetector

    det = PatternDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 50)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        for name in ("detect_single_patterns", "detect_double_patterns",
                     "detect_triple_patterns"):
            fn = getattr(det, name, None)
            if callable(fn):
                try:
                    out[name.removeprefix("detect_")] = _primitive(
                        fn(df, len(df) - 1))
                except Exception:  # noqa: BLE001
                    out[name.removeprefix("detect_")] = None
        return out

    return AdvisoryModuleAdapter("analysis_patterns", analyze)


def _analysis_market_intel_service() -> AdvisoryModuleAdapter:
    """analysis/market_intelligence MarketIntelligenceSystem — composite
    market intel on a synthesized market_data dict."""
    from trading_bot.analysis.market_intelligence import (
        MarketIntelligenceSystem)

    system = MarketIntelligenceSystem()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = system.analyze_market(
            df,
            str(ctx.get("symbol") or "UNKNOWN"),
            str(ctx.get("timeframe") or "M15"))
        if inspect.isawaitable(out):
            out = await out
        return _payload(out)

    return AdvisoryModuleAdapter("analysis_market_intel", analyze, timeout_s=20.0)


def _analysis_ict_service() -> AdvisoryModuleAdapter:
    """analysis/ict_concepts — order blocks, FVGs, liquidity pools,
    market structure on real bars."""
    from trading_bot.analysis.ict_concepts import ICTConceptsAnalyzer

    analyzer = ICTConceptsAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        for name in ("identify_order_blocks", "identify_fvg",
                     "identify_liquidity", "identify_market_structure"):
            fn = getattr(analyzer, name, None)
            if callable(fn):
                try:
                    out[name.replace("identify_", "")] = _primitive(fn(df))
                except Exception:  # noqa: BLE001
                    out[name.replace("identify_", "")] = None
        return out

    return AdvisoryModuleAdapter("analysis_ict_concepts", analyze)


def _analysis_liquidity_service() -> AdvisoryModuleAdapter:
    """analysis/liquidity LiquidityAnalyzer — liquidity grabs + order
    blocks on real bars."""
    from trading_bot.analysis.liquidity import LiquidityAnalyzer

    analyzer = LiquidityAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        tf = str(ctx.get("timeframe") or "M15")
        out = {"bars": len(df)}
        for name, args in (("detect_grabs", (df, None, tf)),
                           ("detect_order_blocks", (df, tf)),
                           ("detect_fair_value_gaps", (df, tf))):
            fn = getattr(analyzer, name, None)
            if callable(fn):
                try:
                    out[name.replace("detect_", "")] = _primitive(fn(*args))
                except Exception:  # noqa: BLE001
                    out[name.replace("detect_", "")] = None
        return out

    return AdvisoryModuleAdapter("analysis_liquidity", analyze)


def _analysis_mtf_service() -> AdvisoryModuleAdapter:
    """analysis/multi_timeframe_confirmation TimeframeAnalyzer — EMA/RSI/
    ATR trend read on real bars."""
    from trading_bot.analysis.multi_timeframe_confirmation import (
        TimeframeAnalyzer)

    analyzer = TimeframeAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = analyzer.analyze(df, str(ctx.get("timeframe") or "M15"))
        if inspect.isawaitable(out):
            out = _run_coro_sync(out)
        return _payload(out)

    return AdvisoryModuleAdapter("analysis_mtf_confirmation", analyze)


def _analysis_liq_radar_service() -> AdvisoryModuleAdapter:
    """analysis/liquidity_radar LiquidityRadar — resting-liquidity zones
    on real OHLCV."""
    from trading_bot.analysis.liquidity_radar import LiquidityRadar

    radar = LiquidityRadar()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = radar.detect_liquidity_zones(
            df, str(ctx.get("symbol") or "UNKNOWN"),
            str(ctx.get("timeframe") or "M15"))
        return _payload(out)

    return AdvisoryModuleAdapter("analysis_liquidity_radar", analyze)


def _analysis_price_action_service() -> AdvisoryModuleAdapter:
    """analysis/price_action — candlestick analysis + support/resistance
    on real bars."""
    from trading_bot.analysis.price_action import PriceActionAnalyzer

    analyzer = PriceActionAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        for name in ("analyze_candlesticks", "detect_support_resistance",
                     "analyze_trend"):
            fn = getattr(analyzer, name, None)
            if callable(fn):
                try:
                    out[name] = _primitive(fn(df))
                except Exception:  # noqa: BLE001
                    out[name] = None
        return out

    return AdvisoryModuleAdapter("analysis_price_action", analyze)


def _analysis_regime_service() -> AdvisoryModuleAdapter:
    """analysis/market_regime_detector — second independent regime read
    (features extracted from market_data)."""
    from trading_bot.analysis.market_regime_detector import (
        MarketRegimeDetector)

    det = MarketRegimeDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 20:
            return {"status": "warming", "bars": len(hist)}
        return _payload(det.detect_regime(_md_dict(ctx, hist)))

    return AdvisoryModuleAdapter("analysis_market_regime", analyze)


def _analysis_anomaly_service() -> AdvisoryModuleAdapter:
    """analysis/anomaly_detection AdvancedAnomalyDetector — statistical
    anomalies on accumulated bars."""
    from trading_bot.analysis.anomaly_detection import (
        AdvancedAnomalyDetector)

    det = AdvancedAnomalyDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        return _payload(det.detect_anomalies(df))

    return AdvisoryModuleAdapter("analysis_anomaly", analyze)


def _analysis_traps_service() -> AdvisoryModuleAdapter:
    """analysis/pattern_failure_detection — bull/bear trap detection on
    real bars."""
    from trading_bot.analysis.pattern_failure_detection import (
        PatternFailureDetector)

    det = PatternFailureDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        for name in ("detect_bull_trap", "detect_bear_trap"):
            fn = getattr(det, name, None)
            if callable(fn):
                try:
                    out[name.replace("detect_", "")] = _primitive(fn(df))
                except Exception:  # noqa: BLE001
                    out[name.replace("detect_", "")] = None
        return out

    return AdvisoryModuleAdapter("analysis_traps", analyze)


def _analysis_volume_flow_service() -> AdvisoryModuleAdapter:
    """analysis/obv_money_flow — OBV + MFI divergence on real bars."""
    from trading_bot.analysis.obv_money_flow import (
        MFICalculator, OBVCalculator)

    obv, mfi = OBVCalculator(), MFICalculator()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        try:
            out["obv_divergence"] = _primitive(obv.detect_obv_divergence(df))
        except Exception:  # noqa: BLE001
            out["obv_divergence"] = None
        try:
            out["mfi_divergence"] = _primitive(mfi.detect_mfi_divergence(df))
        except Exception:  # noqa: BLE001
            out["mfi_divergence"] = None
        return out

    return AdvisoryModuleAdapter("analysis_volume_flow", analyze)


def _analysis_context_service() -> AdvisoryModuleAdapter:
    """analysis/market_context — full context classification on a
    synthesized market_data dict."""
    from trading_bot.analysis.market_context import MarketContextAnalyzer

    analyzer = MarketContextAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = analyzer.analyze(
            df, str(ctx.get("timeframe") or "M15"))
        if inspect.isawaitable(out):
            out = _run_coro_sync(out)
        return _payload(out)

    return AdvisoryModuleAdapter("analysis_market_context", analyze)


# --- cross-dir ---

def _black_swan_service() -> AdvisoryModuleAdapter:
    """advanced_features BlackSwanProtection — tail-risk conditions from
    real returns + obs indicators."""
    from trading_bot.advanced_features.black_swan_protection import (
        BlackSwanProtection)

    shield = BlackSwanProtection({})
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        closes = [b["close"] for b in hist.bars(50)]
        returns = [closes[i] / closes[i - 1] - 1.0
                   for i in range(1, len(closes)) if closes[i - 1]]
        market_data = {
            "returns": returns,
            "current_return": returns[-1] if returns else 0.0,
            "volatility": _num(ctx.get("volatility")) or 0.0,
            "volume_ratio": _num(ctx.get("volume_ratio")) or 1.0,
            "spread": _num(ctx.get("spread")) or 0.0,
        }
        out = shield.assess_market_conditions(market_data)
        if inspect.isawaitable(out):
            out = await out
        return _payload(out)

    return AdvisoryModuleAdapter("black_swan_conditions", analyze)


def _pullback_detector_service() -> AdvisoryModuleAdapter:
    """improvements PullbackDetector — pullback quality on real
    highs/lows/closes."""
    from trading_bot.improvements.entry_optimizer import PullbackDetector

    det = PullbackDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        bars = hist.bars(40)
        if len(bars) < 10:
            return {"status": "warming", "bars": len(bars)}
        trend = str(ctx.get("trend") or "")
        direction = "up" if "UP" in trend.upper() or "BULL" in trend.upper() \
            else "down"
        out = det.detect_pullback(
            direction,
            [b["high"] for b in bars],
            [b["low"] for b in bars],
            [b["close"] for b in bars])
        return _payload(out)

    return AdvisoryModuleAdapter("pullback_detector", analyze)


def _alpha_decay_service() -> AdvisoryModuleAdapter:
    """analytics AlphaDecayAnalyzer — the asset's own returns vs a
    flat-drift null benchmark (no strategy PnL exists at obs time)."""
    from trading_bot.analytics.alpha_attribution import AlphaDecayAnalyzer

    analyzer = AlphaDecayAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        closes = [b["close"] for b in hist.bars(60)]
        returns = [closes[i] / closes[i - 1] - 1.0
                   for i in range(1, len(closes)) if closes[i - 1]]
        if len(returns) < 20:
            return {"status": "warming", "bars": len(returns)}
        import pandas as _pd
        return _payload(analyzer.analyze_decay(
            _pd.Series(returns),
            _pd.Series([0.0] * len(returns))))

    return AdvisoryModuleAdapter("alpha_decay", analyze)


def _iceberg_detector_service() -> AdvisoryModuleAdapter:
    """indicators IcebergDetector — hidden-liquidity signature on real
    price/volume bars."""
    from trading_bot.indicators.advanced_liquidity import IcebergDetector

    det = IcebergDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = det.detect(df)
        if inspect.isawaitable(out):
            out = _run_coro_sync(out)
        return _payload(out)

    return AdvisoryModuleAdapter("iceberg_detector", analyze)


def _momentum_specialist_service() -> AdvisoryModuleAdapter:
    """market_teacher MomentumSpecialist — momentum read on the
    market_data dict."""
    from trading_bot.market_teacher.agent_collective import (
        MomentumSpecialist)

    agent = MomentumSpecialist("advisory_momentum", {})
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        out = agent.analyze(_md_dict(ctx, hist))
        if inspect.isawaitable(out):
            out = _run_coro_sync(out)
        return _payload(out)

    return AdvisoryModuleAdapter("momentum_specialist", analyze)


def _intelligence_brain_v2_service() -> AdvisoryModuleAdapter:
    """alphaalgo_v2 IntelligenceBrain — regime + forecast + signal on a
    MarketData built from accumulated bars. Evidence only."""
    import pandas as pd
    from trading_bot.alphaalgo_v2.core.types import MarketData as V2MarketData
    from trading_bot.alphaalgo_v2.models.brain import IntelligenceBrain

    brain = IntelligenceBrain()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        md = V2MarketData(
            symbol=str(ctx.get("symbol") or "UNKNOWN"),
            timeframe=str(ctx.get("timeframe") or "M15"),
            ohlcv=df)
        out = brain.analyze(md.symbol, md)
        if inspect.isawaitable(out):
            out = await out
        return _payload(out)

    return AdvisoryModuleAdapter("intelligence_brain_v2", analyze)



# ---------------------------------------------------------------------------
# Bucket F - DOCS/CSC_WIRING_AUDIT.md: observation-callable analyzers
# ---------------------------------------------------------------------------


def _rsi_series(prices: List[float], period: int = 14) -> List[float]:
    """Simple RSI series from real closes - honest indicator input for
    divergence-style detectors (never fabricated)."""
    out: List[float] = []
    for i in range(1, len(prices)):
        window = prices[max(0, i - period):i + 1]
        gains = losses = 0.0
        for j in range(1, len(window)):
            ch = window[j] - window[j - 1]
            if ch > 0:
                gains += ch
            else:
                losses -= ch
        out.append(100.0 if losses <= 0
                   else 100.0 - 100.0 / (1.0 + gains / losses))
    return out


def _swing_levels(bars: List[Dict[str, float]], k: int = 3
                  ) -> Tuple[List[float], List[float]]:
    """Local swing highs/lows over the accumulated bar window."""
    highs: List[float] = []
    lows: List[float] = []
    for i in range(k, len(bars) - k):
        if all(bars[i]["high"] >= bars[j]["high"]
               for j in range(i - k, i + k + 1)):
            highs.append(bars[i]["high"])
        if all(bars[i]["low"] <= bars[j]["low"]
               for j in range(i - k, i + k + 1)):
            lows.append(bars[i]["low"])
    return highs[-20:], lows[-20:]


def _probe_all(probes: Iterable[Tuple[str, Callable[[], Any]]]
               ) -> Dict[str, Any]:
    """Run independent detector probes; each failure is contained per-key
    so one bad module can't void the whole advisory payload."""
    out: Dict[str, Any] = {}
    for key, fn in probes:
        try:
            res = fn()
            if res is not None and res != [] and res != {}:
                out[key] = _primitive(
                    res[-10:] if isinstance(res, list) else res)
        except Exception as exc:  # noqa: BLE001 - per-detector isolation
            out[key] = {"error": str(exc)[:200]}
    return out


def _upgrades_structure_service() -> AdvisoryModuleAdapter:
    """upgrades/ candle-shape detectors - order blocks, fair value gaps,
    market structure, price-action patterns, liquidity sweeps. All read
    the accumulated real bar window."""
    from trading_bot.upgrades.core_upgrades_001_025 import (
        OrderBlockDetector, FairValueGapDetector, MarketStructureAnalyzer,
        PriceActionPatternDetector)
    from trading_bot.upgrades.core_upgrades_026_050 import (
        LiquiditySweepDetector)

    obs_det = OrderBlockDetector()
    fvg = FairValueGapDetector()
    msa = MarketStructureAnalyzer()
    pa = PriceActionPatternDetector()
    sweep = LiquiditySweepDetector()
    hist = _BarHistory(256)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 30:
            return {"status": "warming", "bars": len(hist)}
        bars = hist.bars()
        highs = [b["high"] for b in bars]
        lows = [b["low"] for b in bars]
        sh, sl = _swing_levels(bars)
        out = _probe_all((
            ("order_blocks", lambda: obs_det.detect(bars)),
            ("fair_value_gaps", lambda: fvg.detect(bars)),
            ("market_structure", lambda: msa.analyze(highs, lows)),
            ("price_patterns", lambda: pa.analyze(
                bars[-1]["open"], bars[-1]["high"],
                bars[-1]["low"], bars[-1]["close"])),
            ("liquidity_sweeps", lambda: sweep.detect(bars, sh, sl)),
        ))
        return out or {"status": "no_structures"}

    return AdvisoryModuleAdapter("upgrades_price_structure", analyze)


def _upgrades_regime_service() -> AdvisoryModuleAdapter:
    """upgrades/ VolatilityRegimeDetector + TradeClassifier +
    DivergenceDetector - regime/classification/divergence evidence from
    real returns and a computed RSI series."""
    from trading_bot.upgrades.core_upgrades_001_025 import (
        VolatilityRegimeDetector, TradeClassifier)
    from trading_bot.upgrades.core_upgrades_026_050 import (
        DivergenceDetector)

    vol = VolatilityRegimeDetector()
    tclf = TradeClassifier()
    dv = DivergenceDetector()
    hist = _BarHistory(256)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        prices = hist.prices()
        if len(prices) < 21:
            return {"status": "warming", "bars": len(prices)}
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        rsi = _rsi_series(prices)
        out = _probe_all((
            ("volatility_regime",
             lambda: vol.detect(symbol, hist.returns())),
            ("divergence", lambda: dv.detect(prices, rsi)),
            ("trade_classification",
             lambda: tclf.classify(symbol, prices[-1])),
        ))
        return out or {"status": "no_signals"}

    return AdvisoryModuleAdapter("upgrades_regime_divergence", analyze)


def _institutional_footprint_service() -> AdvisoryModuleAdapter:
    """institutional_entry - AbsorptionDetector + InstitutionalFootprint
    + WyckoffICTFusion over the accumulated OHLCV window. The module's
    timeframe labels map onto the single real feed; the bars are genuine
    observations, the key is only a label."""
    from trading_bot.institutional_entry.institutional_footprint import (
        AbsorptionDetector, InstitutionalFootprint)
    from trading_bot.institutional_entry.wyckoff_ict_fusion import (
        WyckoffICTFusion)

    absorb = AbsorptionDetector()
    fp = InstitutionalFootprint({"high_volume_threshold": 1.5})
    wyck = WyckoffICTFusion({"primary_timeframe": "primary",
                             "confirmation_timeframes": ["primary"],
                             "min_confirmations": 0})
    hist = _BarHistory(256)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 30:
            return {"status": "warming", "bars": len(hist)}
        df = hist.frame()
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        sh, sl = _swing_levels(hist.bars())
        out = _probe_all((
            ("absorption", lambda: absorb.detect_absorption(df)),
            ("footprint", lambda: fp.analyze_footprint(df, "primary")),
            ("institutional_sweep",
             lambda: fp.detect_institutional_sweep(
                 df, {"support": sl, "resistance": sh})),
            ("wyckoff", lambda: wyck.analyze_market_structure(
                symbol, {"primary": df})),
        ))
        return out or {"status": "no_footprint"}

    return AdvisoryModuleAdapter("institutional_entry_footprint", analyze)


def _volume_profile_service() -> AdvisoryModuleAdapter:
    """forecast_improvements VolumeProfile — volume-at-price from real
    OHLCV: Point of Control + Value Area as measured structure. Direction
    = mean-reversion lean toward POC only when price sits OUTSIDE the
    value area; inside VA it emits the profile, not a vote."""
    from trading_bot.improvements.forecast_improvements.data_feed_quality import (
        OHLCV)

    hist = _BarHistory(128)
    analyzer = [None]

    def _bars_obj():
        now = datetime.now()
        return [OHLCV(symbol="EURUSD", timeframe="M15",
                      open=b["open"], high=b["high"], low=b["low"],
                      close=b["close"], volume=b.get("volume") or 0.0,
                      timestamp=now)
                for b in hist.bars()]

    def analyze(ctx: Mapping[str, Any]) -> Any:
        nonlocal analyzer
        hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": len(hist)}
        if analyzer[0] is None:
            from trading_bot.improvements.forecast_improvements import (
                data_feed_quality as dfq)
            import inspect as _in
            # find the analyzer class that owns calculate_volume_profile
            for _, obj in vars(dfq).items():
                if isinstance(obj, type) and hasattr(
                        obj, "calculate_volume_profile"):
                    try:
                        analyzer[0] = obj()
                    except Exception:
                        analyzer[0] = obj({})
                    break
            if analyzer[0] is None:
                return {"status": "no_analyzer"}
        prof = analyzer[0].calculate_volume_profile(_bars_obj())
        if prof is None:
            return {"status": "no_profile"}
        price = _num(ctx.get("close") or ctx.get("price")) or 0.0
        in_va = prof.value_area_low <= price <= prof.value_area_high
        direction = None
        if price and not in_va:
            direction = "BUY" if price < prof.value_area_low else "SELL"
        return {
            "poc": prof.poc,
            "value_area_high": prof.value_area_high,
            "value_area_low": prof.value_area_low,
            "in_value_area": in_va,
            "dist_to_poc_pct": round(
                (prof.poc - price) / price * 100, 4) if price else None,
            "direction": direction,
        }

    return AdvisoryModuleAdapter("volume_profile", analyze)



def _peer_correlation_service() -> AdvisoryModuleAdapter:
    """Peer-symbol correlation + lead/lag — the first cross-asset
    analyzer. Consumes obs['peer_close'] fed by the runners
    (--peer-symbol GBPUSD); absent -> missing_data, never fabricated.
    Direction = drift toward the peer's direction when the peer moved
    and we have not followed yet (measured lead/lag, not assumed)."""
    import numpy as _np

    own = _BarHistory(96)
    peer = _BarHistory(96)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        peer_price = _num(ctx.get("peer_close"))
        own.add(ctx)
        if peer_price is None:
            return {"status": "missing_data",
                    "needs": "obs.peer_close (--peer-symbol)"}
        peer._bars.append({"close": peer_price})
        if len(own) < 30 or len(peer) < 30:
            return {"status": "warming", "bars": len(peer)}
        a = _np.asarray(own.prices()[-30:], dtype=float)
        b = _np.asarray(peer.prices()[-30:], dtype=float)
        ra = _np.diff(a) / a[:-1]
        rb = _np.diff(b) / b[:-1]
        if _np.std(ra) == 0 or _np.std(rb) == 0:
            return {"status": "degenerate"}
        corr = float(_np.corrcoef(ra, rb)[0, 1])
        peer_ret = float((b[-1] - b[-11]) / b[-11]) if len(b) > 11 else 0.0
        own_ret = float((a[-1] - a[-11]) / a[-11]) if len(a) > 11 else 0.0
        # Lead/lag: peer moved, we haven't followed (correlated pair)
        direction = None
        if corr > 0.4 and abs(peer_ret) > 0.0005 and abs(own_ret) < abs(peer_ret) * 0.3:
            direction = "BUY" if peer_ret > 0 else "SELL"
        return {
            "corr_30": round(corr, 4),
            "peer_return_10": round(peer_ret, 6),
            "own_return_10": round(own_ret, 6),
            "lead_lag_gap": round(peer_ret - own_ret, 6),
            "peer_symbol": ctx.get("peer_symbol"),
            "direction": direction,
        }

    return AdvisoryModuleAdapter("peer_correlation", analyze)



def _indicators_liquidity_service() -> AdvisoryModuleAdapter:
    """indicators CVD + AbsorptionExhaustionRatio — cumulative volume
    delta approximated honestly from bar direction (close>open -> +vol)
    and absorption-vs-exhaustion balance. Direction = sign of the CVD
    slope over the last 10 bars; slope near zero abstains."""
    import pandas as _pd
    from trading_bot.indicators.advanced_liquidity import (
        CVDMultiTimeframe, AbsorptionExhaustionRatio)

    cvd = CVDMultiTimeframe()
    aer = AbsorptionExhaustionRatio()
    hist = _BarHistory(128)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 30:
            return {"status": "warming", "bars": len(hist)}
        df = _pd.DataFrame(hist.bars())
        cvd_series = cvd.calculate_cvd(df)
        slope = (float(cvd_series.iloc[-1]) - float(cvd_series.iloc[-10]))             if len(cvd_series) >= 10 else 0.0
        vols = df["volume"].astype(float)
        vsum = float(vols.iloc[-10:].sum()) or 1.0
        rel = slope / vsum
        aer_val = aer.calculate(df)
        last_aer = float(aer_val.iloc[-1]) if len(aer_val) else 0.0
        direction = None
        if rel > 0.05:
            direction = "BUY"
        elif rel < -0.05:
            direction = "SELL"
        return {
            "cvd_slope_rel_10": round(rel, 4),
            "absorption_exhaustion_ratio": round(last_aer, 4),
            "note": "cvd approximated from bar direction",
            "direction": direction,
        }

    return AdvisoryModuleAdapter("indicators_liquidity", analyze)



def _indicators_adv_technical_service() -> AdvisoryModuleAdapter:
    """indicators AdvancedTechnicalIndicators — Hurst regime, SuperTrend
    direction, TTM squeeze momentum, KAMA/Kalman on real OHLC bars.
    Direction = SuperTrend and squeeze-momentum agreement; disagreement
    emits the indicator values without a vote."""
    import pandas as _pd
    from trading_bot.indicators.advanced_technical import (
        AdvancedTechnicalIndicators)

    ind = AdvancedTechnicalIndicators()
    hist = _BarHistory(128)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 35:
            return {"status": "warming", "bars": len(hist)}
        df = _pd.DataFrame(hist.bars())
        res = ind.calculate_all(df)
        last = res.iloc[-1]
        st_dir = last.get("supertrend_direction")
        mom = last.get("ttm_momentum") or last.get("ttm_histogram")
        squeeze_on = bool(last.get("ttm_squeeze_on"))
        hurst = last.get("hurst_exponent")
        regime = last.get("hurst_regime")
        st_sig = None
        if isinstance(st_dir, (int, float)):
            st_sig = "BUY" if st_dir > 0 else "SELL" if st_dir < 0 else None
        elif isinstance(st_dir, str):
            st_sig = {"up": "BUY", "down": "SELL"}.get(st_dir.lower())
        direction = None
        if st_sig and isinstance(mom, (int, float)):
            agree = (mom > 0 and st_sig == "BUY") or                     (mom < 0 and st_sig == "SELL")
            direction = st_sig if agree else None
        return {
            "hurst_exponent": float(hurst) if hurst is not None else None,
            "hurst_regime": regime,
            "supertrend_direction": st_sig,
            "squeeze_on": squeeze_on,
            "squeeze_momentum": float(mom)
                if isinstance(mom, (int, float)) else None,
            "direction": direction,
        }

    return AdvisoryModuleAdapter("indicators_adv_technical", analyze)



def _upgrades_change_detect_service() -> AdvisoryModuleAdapter:
    """upgrades RegimeChangeDetector + AnomalyDetector — mean-shift
    (>2 sigma over 2x window) and z-score anomaly flags on the close
    stream. Change-point evidence; non-directional by design."""
    from trading_bot.upgrades.core_upgrades_051_075 import (
        RegimeChangeDetector, AnomalyDetector)

    regime_det = RegimeChangeDetector()
    anom_det = AnomalyDetector()
    _n = [0]

    def analyze(ctx: Mapping[str, Any]) -> Any:
        price = _num(ctx.get("close") or ctx.get("price"))
        if price is None:
            return {"status": "no_price"}
        _n[0] += 1
        regime_change = bool(regime_det.detect(price))
        anomaly = bool(anom_det.check(price))
        return {
            "regime_change": regime_change,
            "anomaly": anomaly,
            "bars_seen": _n[0],
            "direction": None,
        }

    return AdvisoryModuleAdapter("upgrades_change_detect", analyze)



def _deepchart_price_response_service() -> AdvisoryModuleAdapter:
    """deepchart PriceResponseCurveEngine — fits a power-law price-
    response-to-volume curve (elasticity, linearity, saturation point)
    from real bars. Market-impact structure evidence; non-directional."""
    from trading_bot.deepchart.execution_forecast_engine import (
        PriceResponseCurveEngine)
    from trading_bot.deepchart.market_intelligence_core import (
        MarketIntelligenceConfig)

    eng = PriceResponseCurveEngine(MarketIntelligenceConfig())
    _last = [None]

    def analyze(ctx: Mapping[str, Any]) -> Any:
        price = _num(ctx.get("close") or ctx.get("price"))
        if price is None:
            return {"status": "no_price"}
        change = price - _last[0] if _last[0] else 0.0
        _last[0] = price
        curve = eng.update(price, _num(ctx.get("volume")) or 0.0, abs(change))
        out = _payload(curve)
        if isinstance(out, dict):
            out["direction"] = None
        return out

    return AdvisoryModuleAdapter("deepchart_price_response", analyze)



def _black_swan_threat_service() -> AdvisoryModuleAdapter:
    """advanced_features BlackSwanProtection — tail-risk threat level.
    vol_ratio and drawdown are COMPUTED from the real bar window
    (realized vol 20 vs 100, close drawdown vs 128-bar max). No VIX feed
    exists, so it uses the module default — the dominant measured inputs
    are ours. Non-directional risk evidence, never a direction."""
    import numpy as _np
    from trading_bot.advanced_features.black_swan_protection import (
        BlackSwanProtection)

    prot = BlackSwanProtection({})
    hist = _BarHistory(128)

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": len(hist)}
        closes = _np.asarray(hist.prices(), dtype=float)
        rets = _np.diff(closes) / closes[:-1]
        vol_20 = float(_np.std(rets[-20:])) if len(rets) >= 20 else 0.0
        vol_100 = float(_np.std(rets[-100:])) if len(rets) >= 100 else vol_20
        peak = float(_np.max(closes))
        ev = await prot.assess_market_conditions({
            "volatility_ratio": vol_20 / vol_100 if vol_100 > 0 else 1.0,
            "current_drawdown": (peak - closes[-1]) / peak if peak else 0.0,
            "correlation_breakdown": False,
        })
        out = _payload(ev)
        if isinstance(out, dict):
            out["vol_ratio_measured"] = round(
                vol_20 / vol_100, 4) if vol_100 > 0 else None
            out["direction"] = None  # threat evidence, not a direction
        return out

    return AdvisoryModuleAdapter("black_swan_threat", analyze)


def _spai_trend_reversal_service() -> AdvisoryModuleAdapter:
    """superpowerful_ai PredictiveIntelligence.predict_trend_reversal —
    divergence/sr-test/vol-expansion reversal score on OHLC. Direction is
    the counter-trend lean ONLY when reversal_probability > 0.5; the
    current trend is measured from the bar window, not assumed."""
    import pandas as _pd
    from trading_bot.superpowerful_ai.predictive_intelligence import (
        PredictiveIntelligence)

    pi = PredictiveIntelligence()
    hist = _BarHistory(128)

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 55:
            return {"status": "warming", "bars": len(hist)}
        df = _pd.DataFrame(hist.bars())
        res = await pi.predict_trend_reversal(str(ctx.get("symbol") or "UNKNOWN"), df)
        out = _payload(res)
        if not isinstance(out, dict):
            return out
        prob = out.get("reversal_probability") or 0.0
        closes = [b["close"] for b in hist.bars()]
        trend = 1 if closes[-1] > closes[-30] else -1
        direction = None
        if prob > 0.5:
            direction = "SELL" if trend > 0 else "BUY"
        out["direction"] = direction
        out["measured_trend"] = "up" if trend > 0 else "down"
        return out

    return AdvisoryModuleAdapter("spai_trend_reversal", analyze)



def _improvements_regime_service() -> AdvisoryModuleAdapter:
    """improvements MarketRegimeDetector — ADX trend regime, ATR
    volatility regime, momentum regime from raw OHLCV. Structure
    evidence; direction comes only from a NON-neutral momentum regime
    aligned with the trend."""
    import numpy as _np
    from trading_bot.improvements.market_regime import MarketRegimeDetector

    det = MarketRegimeDetector()
    hist = _BarHistory(128)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 60:
            return {"status": "warming", "bars": len(hist)}
        bars = hist.bars()
        highs = _np.asarray([b["high"] for b in bars], dtype=float)
        lows = _np.asarray([b["low"] for b in bars], dtype=float)
        closes = _np.asarray([b["close"] for b in bars], dtype=float)
        vols = _np.asarray([b.get("volume") or 0.0 for b in bars],
                           dtype=float)
        res = det.detect(str(ctx.get("symbol") or "UNKNOWN"),
                         highs, lows, closes, vols)
        out = _payload(res)
        if isinstance(out, dict):
            mom = str(out.get("momentum_regime") or "").upper()
            trend = str(out.get("regime") or out.get("regime_type") or "")
            direction = None
            if "BULL" in mom and "TREND" in trend.upper():
                direction = "BUY"
            elif "BEAR" in mom and "TREND" in trend.upper():
                direction = "SELL"
            out["direction"] = direction
        return out

    return AdvisoryModuleAdapter("improvements_regime", analyze)


def _improvements_pullback_service() -> AdvisoryModuleAdapter:
    """improvements EntryOptimizer — pullback detection in the direction
    of the fast/slow EMA trend. Emits direction only when a pullback is
    actually present AND trend-aligned; flat trend emits no direction."""
    import numpy as _np
    from trading_bot.improvements.entry_optimizer import PullbackDetector

    opt = PullbackDetector()
    hist = _BarHistory(128)

    def _ema(vals, period):
        if len(vals) < period:
            return None
        k = 2.0 / (period + 1)
        e = float(vals[0])
        for v in vals[1:]:
            e = v * k + e * (1 - k)
        return e

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 55:
            return {"status": "warming", "bars": len(hist)}
        bars = hist.bars()
        highs = _np.asarray([b["high"] for b in bars], dtype=float)
        lows = _np.asarray([b["low"] for b in bars], dtype=float)
        closes = _np.asarray([b["close"] for b in bars], dtype=float)
        fast, slow = _ema(closes, 10), _ema(closes, 50)
        if fast is None or slow is None or fast == slow:
            return {"status": "flat", "direction": None}
        direction = "BUY" if fast > slow else "SELL"
        is_pb, target, reason = opt.detect_pullback(
            direction, highs, lows, closes)
        return {
            "trend_direction": direction,
            "is_pullback": bool(is_pb),
            "pullback_target": target,
            "reason": reason,
            # entry evidence exists only inside a live pullback
            "direction": direction if is_pb else None,
        }

    return AdvisoryModuleAdapter("improvements_pullback", analyze)


def _improvements_session_service() -> AdvisoryModuleAdapter:
    """improvements SessionSpreadFilter — which trading session the
    observation timestamp falls in and whether it's an optimal window.
    Timing evidence (like time_to_move): never directional."""
    from trading_bot.improvements.session_spread_filter import (
        SessionFilter)

    filt = SessionFilter()
    _seen = [None]

    def analyze(ctx: Mapping[str, Any]) -> Any:
        ts = ctx.get("timestamp")
        dt = None
        if isinstance(ts, datetime):
            dt = ts
        elif isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                dt = None
        ok, reason = filt.should_trade(
            str(ctx.get("symbol") or "UNKNOWN"), dt)
        info = filt.get_current_session(dt)
        out = _payload(info)
        if not isinstance(out, dict):
            out = {"info": str(info)}
        out["should_trade"] = bool(ok)
        out["reason"] = reason
        out["direction"] = None  # timing evidence, never direction
        return out

    return AdvisoryModuleAdapter("improvements_session", analyze)



def _tda_topology_service() -> AdvisoryModuleAdapter:
    """advanced_analysis TopologicalAnalyzer — persistent homology of the
    price trajectory: consolidation/trending/reversal/breakout/range
    pattern classification with Betti numbers. Non-directional structure
    evidence — a TRENDING pattern does not say which way."""
    from trading_bot.advanced_analysis.topological_data_analysis import (
        TopologicalAnalyzer)

    tda = TopologicalAnalyzer({"window_size": 50})
    hist = _BarHistory(96)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 50:
            return {"status": "warming", "bars": len(hist)}
        try:
            sig = tda.analyze(hist.prices()[-50:])
        except Exception as exc:
            return {"status": "no_signal", "reason": str(exc)[:120]}
        out = _payload(sig)
        if isinstance(out, dict):
            out["direction"] = None  # structure, not direction
        return out

    return AdvisoryModuleAdapter("tda_topology", analyze)


def _ricci_momentum_service() -> AdvisoryModuleAdapter:
    """advanced_analysis RicciFlowMomentum — price-curvature momentum
    (second derivative of the series). Emits BUY/SELL only on the
    indicator's own signal; NEUTRAL maps to no direction."""
    import numpy as _np
    from trading_bot.advanced_analysis.proprietary_indicators import (
        RicciFlowMomentum)

    ind = RicciFlowMomentum()
    hist = _BarHistory(96)
    _DIR = {"BUY": "BUY", "BULLISH": "BUY",
            "SELL": "SELL", "BEARISH": "SELL"}

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 25:
            return {"status": "warming", "bars": len(hist)}
        res = ind.calculate(_np.asarray(hist.prices(), dtype=float))
        out = _payload(res)
        if isinstance(out, dict):
            sig = str(out.get("signal") or "").upper()
            out["direction"] = _DIR.get(sig)
        return out

    return AdvisoryModuleAdapter("ricci_momentum", analyze)


def _fractal_momentum_div_service() -> AdvisoryModuleAdapter:
    """advanced_analysis FractalMomentumDivergence — divergence confirmed
    across 3 timeframes. We hold M15 bars; tf2/tf3 are honest resamples of
    the SAME real bars (3-bar -> M45, 4-bar -> H1 closes), not fabricated
    data. Signals only on confirmed divergence."""
    import numpy as _np
    from trading_bot.advanced_analysis.proprietary_indicators import (
        FractalMomentumDivergence)

    ind = FractalMomentumDivergence()
    hist = _BarHistory(256)
    _DIR = {"BUY": "BUY", "BULLISH": "BUY",
            "SELL": "SELL", "BEARISH": "SELL"}

    def _resample(closes, n):
        k = len(closes) // n
        return closes[len(closes) - k * n:][::n] if k else closes[-1:]

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 60:
            return {"status": "warming", "bars": len(hist)}
        closes = hist.prices()
        tf1 = _np.asarray(closes[-60:], dtype=float)
        tf2 = _np.asarray(_resample(closes, 3)[-40:], dtype=float)
        tf3 = _np.asarray(_resample(closes, 4)[-30:], dtype=float)
        res = ind.calculate(tf1, tf2, tf3)
        out = _payload(res)
        if isinstance(out, dict):
            sig = str(out.get("signal") or "").upper()
            out["direction"] = _DIR.get(sig)
            out["timeframes"] = "M15/M45/H1 resampled"
        return out

    return AdvisoryModuleAdapter("fractal_momentum_div", analyze)



def _deepchart_ttm_service() -> AdvisoryModuleAdapter:
    """deepchart TimeToMovePredictor — bars-to-breakout/reversion timing
    estimates from price+volume alone. Explicitly non-directional: it
    predicts WHEN a move happens, not which way — so it emits substantive
    timing/volatility evidence and never a direction."""
    from trading_bot.deepchart.time_to_move_engine import TimeToMovePredictor
    from trading_bot.deepchart.market_intelligence_core import (
        MarketIntelligenceConfig)

    pred = TimeToMovePredictor(MarketIntelligenceConfig())

    def analyze(ctx: Mapping[str, Any]) -> Any:
        price = _num(ctx.get("close") or ctx.get("price"))
        if price is None:
            return {"status": "no_price"}
        est = pred.update(price, _num(ctx.get("volume")) or 0.0)
        if est is None:
            return {"status": "warming"}
        out = _payload(est)
        if isinstance(out, dict):
            out["interpretation"] = (
                "compression" if out.get("compression_score", 0) < 0.5
                else "expansion")
        return out

    return AdvisoryModuleAdapter("deepchart_time_to_move", analyze)


def _deepchart_sr_memory_service() -> AdvisoryModuleAdapter:
    """deepchart MarketMemoryEngine — support/resistance levels that decay
    with learned reaction probabilities. Direction is a mean-reversion
    lean ONLY when price sits within ~0.1% of a strong level: at strong
    support lean BUY, at strong resistance lean SELL. Away from levels it
    emits the level map without direction."""
    from trading_bot.deepchart.memory_sr_engine import MarketMemoryEngine
    from trading_bot.deepchart.market_intelligence_core import (
        MarketIntelligenceConfig)

    eng = MarketMemoryEngine(MarketIntelligenceConfig())

    def analyze(ctx: Mapping[str, Any]) -> Any:
        price = _num(ctx.get("close") or ctx.get("price"))
        if price is None:
            return {"status": "no_price"}
        levels = eng.update(price, _num(ctx.get("volume")) or 0.0)
        if not levels:
            return {"status": "warming", "levels": 0}
        levels = list(levels)
        nearest = min(
            levels,
            key=lambda l: abs(float(getattr(l, "price", 0.0)) - price))
        np_ = float(getattr(nearest, "price", 0.0))
        strength = float(getattr(nearest, "current_strength", 0.0))
        react_p = float(getattr(nearest, "reaction_probability", 0.0))
        prox = abs(np_ - price) / price if price else 1.0
        direction = None
        if prox <= 0.001 and strength > 0.0 and react_p > 0.3:
            if getattr(nearest, "level_type", "") == "support":
                direction = "BUY"
            elif getattr(nearest, "level_type", "") == "resistance":
                direction = "SELL"
        return {
            "levels": len(levels),
            "nearest_level_price": np_,
            "nearest_level_type": getattr(nearest, "level_type", None),
            "nearest_level_strength": strength,
            "reaction_probability": react_p,
            "proximity_pct": round(prox * 100, 4),
            "direction": direction,
        }

    return AdvisoryModuleAdapter("deepchart_sr_memory", analyze)



def _unified_analyzer_service() -> AdvisoryModuleAdapter:
    """analysis_unified UnifiedAnalyzer - its own sub-analysis loop is
    already failure-tolerant; feed it the real bar window plus the raw
    observation fields."""
    from trading_bot.analysis_unified.unified_analyzer import (
        UnifiedAnalyzer)

    ua = UnifiedAnalyzer()
    hist = _BarHistory(256)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 200)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        md = dict(ctx)
        md["ohlcv"] = df
        for col in ("open", "high", "low", "close", "volume"):
            md[col] = df[col].tolist()
        return _payload(ua.analyze(
            str(ctx.get("symbol") or "UNKNOWN"), md))

    return AdvisoryModuleAdapter("analysis_unified_analyzer", analyze)


def _hypernetwork_regime_service() -> AdvisoryModuleAdapter:
    """advanced_analysis HypernetworkAdapter - regime classification on
    real prices/volatility (detect_regime only; predict() expects a
    fixed-width model input the observation can't honestly supply)."""
    from trading_bot.advanced_analysis.hypernetwork_adaptation import (
        HypernetworkAdapter)

    hn = HypernetworkAdapter()
    hist = _BarHistory(128)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        prices = hist.prices()
        if len(prices) < 20:
            return {"status": "warming", "bars": len(prices)}
        arr = np.asarray(prices, dtype=float)
        rets = np.diff(arr) / np.maximum(arr[:-1], 1e-12)
        return {"regime": _primitive(hn.detect_regime({
            "prices": arr,
            "volatility": (_num(ctx.get("volatility"))
                           or float(np.std(rets))),
            "trend_strength": _num(ctx.get("trend_strength")) or 0.0}))}

    return AdvisoryModuleAdapter("hypernetwork_regime", analyze)


def _marl_strategists_service() -> AdvisoryModuleAdapter:
    """advanced_analysis multi_agent_rl - MacroStrategist +
    TacticalExecutioner arguments on the market_data dict. AgentArgument
    outputs are evidence; ConsensusDecision machinery is never reached."""
    from trading_bot.advanced_analysis.multi_agent_rl import (
        MacroStrategist, TacticalExecutioner)

    macro = MacroStrategist()
    tact = TacticalExecutioner()
    hist = _BarHistory(128)

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 20:
            return {"status": "warming", "bars": len(hist)}
        md = dict(_numeric_fields(ctx))
        md.update({"symbol": ctx.get("symbol"),
                   "prices": hist.prices(),
                   "ohlcv": hist.bars(60)})
        out: Dict[str, Any] = {}
        for key, agent in (("macro_strategist", macro),
                           ("tactical_executioner", tact)):
            try:
                res = agent.analyze(md)
                if inspect.isawaitable(res):
                    res = await res
                if res is not None:
                    out[key] = _payload(res)
            except Exception as exc:  # noqa: BLE001 - per-agent isolation
                out[key] = {"error": str(exc)[:200]}
        return out or {"status": "no_arguments"}

    return AdvisoryModuleAdapter("marl_strategists", analyze)


def _realtime_ensemble_service() -> AdvisoryModuleAdapter:
    """realtime_ml EnsembleModel - online momentum/mean-reversion/trend/
    volatility models voted on the observation's numeric fields. Models
    start unfitted; the ensemble returns bounded-confidence predictions
    that improve as update() calls land - evidence, not authority."""
    from trading_bot.realtime.realtime_ml import (
        EnsembleModel, FeatureVector, MomentumModel, MeanReversionModel,
        TrendModel, VolatilityModel)

    ens = EnsembleModel([MomentumModel(), MeanReversionModel(),
                         TrendModel(), VolatilityModel()], {})
    hist = _BarHistory(64)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        fv = FeatureVector(
            symbol=str(ctx.get("symbol") or "UNKNOWN"),
            timestamp=datetime.utcnow(),
            features=_numeric_fields(ctx))
        try:
            value, conf = ens.predict(fv)
        except Exception as exc:  # noqa: BLE001 - contained
            return {"status": "predict_failed", "error": str(exc)[:200]}
        return {"ensemble_value": float(value),
                "ensemble_confidence": float(conf),
                "feature_count": len(fv.features)}

    return AdvisoryModuleAdapter("realtime_ensemble", analyze)


def _feature_discovery_service() -> AdvisoryModuleAdapter:
    """research FeatureDiscoveryEngine - generates microstructure features
    from the real bar window and scores them by mutual information against
    realized next-bar returns. Pure evidence about which features carry
    signal right now."""
    from trading_bot.research.features.engine import FeatureDiscoveryEngine
    from trading_bot.research.core.interfaces import StandardizedDataset

    eng = FeatureDiscoveryEngine()
    hist = _BarHistory(256)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 60:
            return {"status": "warming", "bars": len(hist)}
        symbol = str(ctx.get("symbol") or "SYMBOL")
        prices = np.asarray(hist.prices(), dtype=float)
        vols = np.asarray(hist.volumes(), dtype=float)
        ds = StandardizedDataset(
            dataset_id="advisory_live", asset_class="fx",
            symbols=[symbol], timeframe="obs",
            start_time=datetime.utcnow(), end_time=datetime.utcnow(),
            data={f"{symbol}_close": prices,
                  f"{symbol}_volume": vols},
            timestamps=np.arange(len(prices)))
        feats = eng.generate_features(ds, symbol)
        # Realized next-bar return - the honest target the features
        # are scored against.
        fwd = np.empty(len(prices))
        fwd[:-1] = prices[1:] / prices[:-1] - 1.0
        fwd[-1] = 0.0
        scores = eng.score_features(feats, fwd)
        return {"generated": len(feats),
                "mi_scores": dict(list(scores.items())[:20]),
                "top_features": sorted(scores.items(),
                                       key=lambda kv: -kv[1])[:5]}

    return AdvisoryModuleAdapter("feature_discovery", analyze)


def _quant_regime_service() -> AdvisoryModuleAdapter:
    """research quant_pipeline RegimeAndMicrostructureAnalyzer - regime
    classification on the bar frame, plus classical OBI when the
    observation carries bid/ask quantities."""
    from trading_bot.research.orchestration.quant_pipeline import (
        RegimeAndMicrostructureAnalyzer)

    analyzer = RegimeAndMicrostructureAnalyzer()
    hist = _BarHistory(256)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 10:
            return {"status": "warming", "bars": len(hist)}
        out: Dict[str, Any] = {
            "regime": analyzer.classify_regime(hist.frame())}
        bid = _num(ctx.get("bid_size") or ctx.get("bid_volume")
                   or ctx.get("bid_qty"))
        ask = _num(ctx.get("ask_size") or ctx.get("ask_volume")
                   or ctx.get("ask_qty"))
        if bid is not None and ask is not None:
            out["order_book_imbalance"] = (
                analyzer.calculate_order_book_imbalance(bid, ask))
        return out

    return AdvisoryModuleAdapter("quant_regime_microstructure", analyze)


def _concept_drift_service() -> AdvisoryModuleAdapter:
    """skills/ai_ml_enhancements ConceptDriftDetector - drift read on the
    accumulated price/volume series."""
    from trading_bot.skills.ai_ml_enhancements.concept_drift import (
        ConceptDriftDetector)

    det = ConceptDriftDetector()
    hist = _BarHistory(256)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 50:
            return {"status": "warming", "bars": len(hist)}
        return _payload(det.detect(hist.prices(), hist.volumes()))

    return AdvisoryModuleAdapter("concept_drift", analyze)


def _profit_max_regime_service() -> AdvisoryModuleAdapter:
    """profit_maximizer MarketRegimeAdapter - regime + confidence on the
    bar frame. Sizing/stop adaptation fields are stripped by the shared
    authority filter before they reach evidence."""
    from trading_bot.profit_maximizer.market_regime_adapter import (
        MarketRegimeAdapter)

    adapter = MarketRegimeAdapter()
    hist = _BarHistory(256)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 30:
            return {"status": "warming", "bars": len(hist)}
        return _payload(adapter.analyze_regime(hist.frame()))

    return AdvisoryModuleAdapter("profit_max_market_regime", analyze)


def _confluence_session_service() -> AdvisoryModuleAdapter:
    """profit_maximizer SignalConfluenceScorer + SessionFilter -
    confluence score on the observation's own trend label (fed the real
    bar frame) and session-appropriateness read. Scores only."""
    from trading_bot.profit_maximizer.profit_maximizer_core import (
        SessionFilter, SignalConfluenceScorer)

    scorer = SignalConfluenceScorer()
    sess = SessionFilter()
    hist = _BarHistory(64)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        direction = str(ctx.get("trend") or ctx.get("regime")
                        or "FLAT").upper()
        md = _numeric_fields(ctx)
        out = _probe_all((
            ("confluence", lambda: _payload(scorer.score_signal(
                direction, df, 0.5))),
            ("session", lambda: _payload(
                sess.assess_session(market_data=md))),
        ))
        return out or {"status": "no_read"}

    return AdvisoryModuleAdapter("confluence_session", analyze)


def _deep_agent_system_service() -> AdvisoryModuleAdapter:
    """ultimate_system DeepAgentSystem - multi-agent market analyses on
    the observation dict; analyze only, the ensemble decision machinery
    is never invoked."""
    from trading_bot.ultimate_system.deep_agent_system import (
        DeepAgentSystem)

    system = DeepAgentSystem()
    hist = _BarHistory(64)

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        if len(hist) < 20:
            return {"status": "warming", "bars": len(hist)}
        md = dict(_numeric_fields(ctx))
        md.update({"symbol": ctx.get("symbol"),
                   "close": hist.prices(),
                   "high": [b["high"] for b in hist.bars(50)],
                   "low": [b["low"] for b in hist.bars(50)],
                   "volume": [b["volume"] for b in hist.bars(50)],
                   "ohlcv": hist.bars(50)})
        out = system.analyze_market(md)
        if inspect.isawaitable(out):
            out = await out
        return _payload(out)

    return AdvisoryModuleAdapter("deep_agent_market", analyze)


def _hft_orderbook_service() -> AdvisoryModuleAdapter:
    """hft OrderBookImbalanceDetector + upgrades LiquidityAnalyzer - only
    emits when the observation actually carries an order book; honest
    no-data status otherwise."""
    from trading_bot.hft.tick_data_handler import (
        OrderBookImbalanceDetector)
    from trading_bot.upgrades.core_upgrades_001_025 import LiquidityAnalyzer

    det = OrderBookImbalanceDetector()
    liq = LiquidityAnalyzer()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        ob = (ctx.get("order_book") or ctx.get("orderbook")
              or ctx.get("microstructure"))
        bids = ctx.get("bids")
        asks = ctx.get("asks")
        has_levels = (isinstance(bids, (list, tuple))
                      and isinstance(asks, (list, tuple))
                      and len(bids) > 0 and len(asks) > 0)
        probes = []
        if ob is not None:
            probes.append(("imbalance", lambda: det.analyze(ob)))
        if has_levels:
            probes.append(
                ("liquidity", lambda: liq.analyze(list(bids), list(asks))))
        out = _probe_all(probes)
        return out or {"status": "no_order_book_in_observation"}

    return AdvisoryModuleAdapter("hft_orderbook_imbalance", analyze)


# ml/ + elite_system note: predictors ship unfitted — they'd emit noise,
# not evidence. Wire only after a training/loading path exists.
# analysis/ remainder note: sec_13f, cot_analysis, dark_pool, options_flow,
# news_event_trading, sentiment/social, cross_asset, sector — all need
# external data feeds the bot doesn't ingest.
# opportunity_scanner note: spread analyzer needs two symbols; the
# observation is single-symbol.
# strategy/self_improvement/orchestrator/unified_architecture/
# ultimate_production note: promotion + execution authority surfaces —
# never advisory by design.


# ---------------------------------------------------------------------------
# Bucket G — second audit pass: Wyckoff / swing-structure / session-pattern
# detectors still obs-feedable and unwired
# ---------------------------------------------------------------------------

def _swing_levels(bars: List[Dict[str, float]], k: int = 3
                  ) -> Tuple[List[float], List[float]]:
    """Local swing highs/lows over the accumulated bar window."""
    highs: List[float] = []
    lows: List[float] = []
    for i in range(k, len(bars) - k):
        if all(bars[i]["high"] >= bars[j]["high"]
               for j in range(i - k, i + k + 1)):
            highs.append(bars[i]["high"])
        if all(bars[i]["low"] <= bars[j]["low"]
               for j in range(i - k, i + k + 1)):
            lows.append(bars[i]["low"])
    return highs[-20:], lows[-20:]


def _analysis_wyckoff_service() -> AdvisoryModuleAdapter:
    """analysis/wyckoff — Wyckoff phase + phase changes on real bars."""
    from trading_bot.analysis.wyckoff import WyckoffAnalyzer

    w = WyckoffAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        for name in ("detect_phase", "detect_phase_changes"):
            fn = getattr(w, name, None)
            if callable(fn):
                try:
                    out[name.replace("detect_", "")] = _primitive(fn(df))
                except Exception:  # noqa: BLE001
                    out[name.replace("detect_", "")] = None
        return out

    return AdvisoryModuleAdapter("analysis_wyckoff", analyze)


def _analysis_wyckoff_full_service() -> AdvisoryModuleAdapter:
    """analysis/wyckoff_complete — accumulation/distribution events on
    real bars."""
    from trading_bot.analysis.wyckoff_complete import (
        WyckoffCompleteAnalyzer)

    w = WyckoffCompleteAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        for name in ("detect_phase", "detect_accumulation_events",
                     "detect_distribution_events"):
            fn = getattr(w, name, None)
            if callable(fn):
                try:
                    out[name.replace("detect_", "")] = _primitive(fn(df))
                except Exception:  # noqa: BLE001
                    out[name.replace("detect_", "")] = None
        return out

    return AdvisoryModuleAdapter("analysis_wyckoff_events", analyze)


def _analysis_structure_service() -> AdvisoryModuleAdapter:
    """analysis/market_structure — swing structure on real bars."""
    from trading_bot.analysis.market_structure import (
        MarketStructureAnalyzer, TimeFrame)

    analyzer = MarketStructureAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = analyzer.detect_structure(df, TimeFrame.M15)
        if inspect.isawaitable(out):
            out = _run_coro_sync(out)
        return _payload(out)

    return AdvisoryModuleAdapter("analysis_market_structure", analyze)


def _analysis_mtf_intel_service() -> AdvisoryModuleAdapter:
    """analysis/multi_timeframe_intelligence — MTF confluence on real
    bars."""
    from trading_bot.analysis.multi_timeframe_intelligence import (
        MultiTimeframeIntelligence, TimeFrame)

    mtf = MultiTimeframeIntelligence()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = mtf.analyze_timeframe(df, TimeFrame.M15)
        if inspect.isawaitable(out):
            out = _run_coro_sync(out)
        return _payload(out)

    return AdvisoryModuleAdapter("analysis_mtf_intelligence", analyze)


def _analysis_liq_simplified_service() -> AdvisoryModuleAdapter:
    """analysis/liquidity_simplified — dict-feedable liquidity read."""
    from trading_bot.analysis.liquidity_simplified import LiquidityAnalysis

    analyzer = LiquidityAnalysis()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = analyzer.analyze(
            df, {}, str(ctx.get("timeframe") or "M15"))
        if inspect.isawaitable(out):
            out = _run_coro_sync(out)
        return _payload(out)

    return AdvisoryModuleAdapter("analysis_liquidity_simple", analyze)


def _vpin_service() -> AdvisoryModuleAdapter:
    """analysis/vpin_analysis — feed each bar, then informed-trading
    read."""
    from trading_bot.analysis.vpin_analysis import VPINCalculator

    calc = VPINCalculator()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        bars = hist.bars(60)
        if len(bars) < 10:
            return {"status": "warming", "bars": len(bars)}
        for b in bars:
            try:
                calc.process_bar(b)
            except Exception:  # noqa: BLE001 - per-bar skip
                pass
        out = {"bars": len(bars)}
        for name, call in (
                ("informed_trading", lambda: calc.detect_informed_trading()),
                ("vpin", lambda: calc.get_current_vpin()),
                ("flash_crash_risk", lambda: calc.assess_flash_crash_risk(
                    _num(ctx.get("volatility")) or 0.0,
                    _num(ctx.get("volume_ratio")) or 1.0))):
            try:
                out[name] = _primitive(call())
            except Exception:  # noqa: BLE001
                out[name] = None
        return out

    return AdvisoryModuleAdapter("vpin_informed_trading", analyze)


def _gravity_well_service() -> AdvisoryModuleAdapter:
    """analysis/liquidity_gravity_well — swing highs/lows registered as
    real liquidity pools, then path prediction."""
    from trading_bot.analysis.liquidity_gravity_well import (
        LiquidityGravityWell)

    well = LiquidityGravityWell()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        bars = hist.bars(60)
        if len(bars) < 20:
            return {"status": "warming", "bars": len(bars)}
        highs, lows = _swing_levels(bars)
        for lv in highs:
            try:
                well.add_liquidity_level(lv, "resistance", strength=1.0)
            except Exception:  # noqa: BLE001
                pass
        for lv in lows:
            try:
                well.add_liquidity_level(lv, "support", strength=1.0)
            except Exception:  # noqa: BLE001
                pass
        out = well.predict_path(
            _num(ctx.get("close") or ctx.get("price")) or 0.0,
            _num(ctx.get("volatility")) or 0.01)
        return _payload(out)

    return AdvisoryModuleAdapter("liquidity_gravity_path", analyze)


def _elite_equal_levels_service() -> AdvisoryModuleAdapter:
    """elite_system EqualHighsLowsDetector — sweep levels on real
    bars."""
    from trading_bot.elite_system.liquidity_warfare import (
        EqualHighsLowsDetector)

    det = EqualHighsLowsDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        return _payload(det.detect_equal_levels(df))

    return AdvisoryModuleAdapter("elite_equal_levels", analyze)


def _elite_swing_points_service() -> AdvisoryModuleAdapter:
    """elite_system SwingPointDetector — swing highs/lows on real
    bars."""
    from trading_bot.elite_system.market_structure_oracle import (
        SwingPointDetector)

    det = SwingPointDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        return _payload(det.detect_swing_points(df))

    return AdvisoryModuleAdapter("elite_swing_points", analyze)


def _elite_price_action_service() -> AdvisoryModuleAdapter:
    """elite_system EliteMarketAnalyzer — load_data(df) then
    analyze_price_action on real bars."""
    from trading_bot.elite_system.market_analysis import (
        EliteMarketAnalyzer, TimeFrame)

    analyzer = EliteMarketAnalyzer("EURUSD")
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        try:
            analyzer.load_data(TimeFrame.M15, df)
        except Exception:  # noqa: BLE001
            return {"status": "load_failed"}
        out = {"bars": len(df)}
        for name in ("analyze_price_action",
                     "identify_smart_money_concepts",
                     "get_trading_opportunities"):
            fn = getattr(analyzer, name, None)
            if callable(fn):
                try:
                    out[name] = _primitive(fn(TimeFrame.M15))
                except Exception:  # noqa: BLE001
                    try:
                        out[name] = _primitive(fn())
                    except Exception:  # noqa: BLE001
                        out[name] = None
        return out

    return AdvisoryModuleAdapter("elite_price_action", analyze)


def _elite_patterns_service() -> AdvisoryModuleAdapter:
    """elite_system ElitePatternRecognizer — candlestick + chart
    patterns on real bars."""
    from trading_bot.elite_system.pattern_recognition import (
        ElitePatternRecognizer)

    rec = ElitePatternRecognizer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        for name in ("detect_candlestick_patterns",
                     "detect_chart_patterns"):
            fn = getattr(rec, name, None)
            if callable(fn):
                try:
                    out[name.replace("detect_", "")] = _primitive(fn(df))
                except Exception:  # noqa: BLE001
                    out[name.replace("detect_", "")] = None
        return out

    return AdvisoryModuleAdapter("elite_patterns", analyze)


def _brain_structure_service() -> AdvisoryModuleAdapter:
    """brain tier3 — S/R + liquidity + statistical reads on real
    bars."""
    from trading_bot.brain.tier3_structure import (
        LiquidityAnalysis, MarketStructureAnalysis, StatisticalAnalysis)

    ms, la, sa = (MarketStructureAnalysis(), LiquidityAnalysis(),
                  StatisticalAnalysis())
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        for label, fn in (("structure", lambda: ms.analyze(df)),
                          ("liquidity", lambda: la.analyze(df)),
                          ("statistical", lambda: sa.analyze(df))):
            try:
                out[label] = _primitive(fn())
            except Exception:  # noqa: BLE001
                out[label] = None
        return out

    return AdvisoryModuleAdapter("brain_tier3_structure", analyze)


def _brain_orderflow_service() -> AdvisoryModuleAdapter:
    """brain tier2 — volume climax + pressure + institutional detection
    on real bars."""
    from trading_bot.brain.tier2_orderflow import (
        AdvancedVolumeAnalysis, BasicVolumeAnalysis,
        InstitutionalDetection, PressureAnalysis)

    basic, adv_vol, press, inst = (BasicVolumeAnalysis(),
                                   AdvancedVolumeAnalysis(),
                                   PressureAnalysis(),
                                   InstitutionalDetection())
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        for label, fn in (("volume", lambda: basic.analyze(df)),
                          ("advanced_volume", lambda: adv_vol.analyze(df)),
                          ("pressure", lambda: press.analyze(df, None)),
                          ("institutional", lambda: inst.analyze(df))):
            try:
                out[label] = _primitive(fn())
            except Exception:  # noqa: BLE001
                out[label] = None
        return out

    return AdvisoryModuleAdapter("brain_tier2_orderflow", analyze)


def _brain_condition_service() -> AdvisoryModuleAdapter:
    """REMOVED — measured dead weight: emitted empty evidence on all
    bars under all conditions in the real-envelope probe. Stub kept so
    stale registry entries fail loudly rather than silently attach."""
    raise RuntimeError("brain_market_condition removed — dead weight")


def _fractal_divergence_service() -> AdvisoryModuleAdapter:
    """advanced_features FractalMomentumDivergence — divergence on real
    bars."""
    from trading_bot.advanced_features.fractal_momentum_divergence \
        import FractalMomentumDivergence

    div = FractalMomentumDivergence()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = div.analyze_divergence(
            df, str(ctx.get("timeframe") or "M15"))
        if inspect.isawaitable(out):
            out = _run_coro_sync(out)
        return _payload(out)

    return AdvisoryModuleAdapter("fractal_divergence", analyze)


def _volatility_impulse_service() -> AdvisoryModuleAdapter:
    """advanced_features VolatilityImpulseVector — volume surge on real
    volume series."""
    from trading_bot.advanced_features.volatility_impulse import (
        VolatilityImpulseVector)

    vec = VolatilityImpulseVector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        import pandas as pd
        hist.add(ctx)
        vols = [b["volume"] for b in hist.bars(60)]
        if len(vols) < 10:
            return {"status": "warming", "bars": len(vols)}
        surge = np.asarray(
            vec.detect_volume_surge(pd.Series(vols, dtype=float)),
            dtype=float)
        return {"bars": len(vols),
                "surge_ratio_last": float(surge[-1]),
                "surge_ratio_max": float(np.nanmax(surge))}

    return AdvisoryModuleAdapter("volatility_impulse", analyze)


def _liquidity_holography_service() -> AdvisoryModuleAdapter:
    """advanced_features TemporalLiquidityAnalyzer — liquidity
    evolution on real bars."""
    from trading_bot.advanced_features.liquidity_holography import (
        TemporalLiquidityAnalyzer)

    analyzer = TemporalLiquidityAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = analyzer.analyze_liquidity_evolution(df)
        if inspect.isawaitable(out):
            out = _run_coro_sync(out)
        return _payload(out)

    return AdvisoryModuleAdapter("liquidity_holography", analyze)


def _mi_absorption_service() -> AdvisoryModuleAdapter:
    """market_intelligence AbsorptionPatterns — absorption + iceberg
    signatures on real bars."""
    from trading_bot.market_intelligence.liquidity_absorption import (
        AbsorptionPatterns)

    det = AbsorptionPatterns()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        for name in ("detect_absorption_patterns",
                     "detect_iceberg_orders"):
            fn = getattr(det, name, None)
            if callable(fn):
                try:
                    out[name.replace("detect_", "")] = _primitive(fn(df))
                except Exception:  # noqa: BLE001
                    out[name.replace("detect_", "")] = None
        return out

    return AdvisoryModuleAdapter("mi_absorption", analyze)


def _mi_manipulation_service() -> AdvisoryModuleAdapter:
    """market_intelligence ManipulationPatterns — stop hunts +
    liquidity grabs on real bars."""
    from trading_bot.market_intelligence.manipulation_analysis import (
        ManipulationPatterns)

    det = ManipulationPatterns()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = {"bars": len(df)}
        for name in ("detect_stop_hunts", "detect_liquidity_grabs"):
            fn = getattr(det, name, None)
            if callable(fn):
                try:
                    out[name.replace("detect_", "")] = _primitive(fn(df))
                except Exception:  # noqa: BLE001
                    out[name.replace("detect_", "")] = None
        return out

    return AdvisoryModuleAdapter("mi_manipulation", analyze)


def _mi_structure_service() -> AdvisoryModuleAdapter:
    """market_intelligence MarketStructureAnalysis — market structure
    on real bars."""
    from trading_bot.market_intelligence.pattern_recognition import (
        MarketStructureAnalysis)

    det = MarketStructureAnalysis()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        return _payload(det.detect_market_structure(df))

    return AdvisoryModuleAdapter("mi_market_structure", analyze)


def _mi_time_price_service() -> AdvisoryModuleAdapter:
    """market_intelligence TimeAnalysisComponents — session +
    day-of-week patterns on timestamped real bars."""
    from trading_bot.market_intelligence.time_price_analysis import (
        TimeAnalysisComponents)

    analyzer = TimeAnalysisComponents()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        df = df.copy()
        df["timestamp"] = ctx.get("timestamp") or datetime.utcnow()
        out = {"bars": len(df)}
        for name in ("analyze_session_patterns", "detect_time_cycles",
                     "analyze_day_of_week_patterns"):
            fn = getattr(analyzer, name, None)
            if callable(fn):
                try:
                    out[name] = _primitive(fn(df))
                except Exception:  # noqa: BLE001
                    out[name] = None
        return out

    return AdvisoryModuleAdapter("mi_time_price", analyze)


def _mi_wyckoff_service() -> AdvisoryModuleAdapter:
    """market_intelligence WyckoffAccumulationDetector — accumulation
    phase on real bars."""
    from trading_bot.market_intelligence.wyckoff_analysis import (
        WyckoffAccumulationDetector)

    det = WyckoffAccumulationDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        return _payload(det.detect_accumulation_phase(df))

    return AdvisoryModuleAdapter("mi_wyckoff_accumulation", analyze)


def _session_awareness_service() -> AdvisoryModuleAdapter:
    """improvements SessionAwareness — session tagging from the obs
    timestamp."""
    from trading_bot.improvements.forecast_improvements.\
session_awareness import SessionAwareness

    sa = SessionAwareness()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        ts = ctx.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except ValueError:
                ts = None
        out = sa.analyze_session(
            str(ctx.get("symbol") or "EURUSD"),
            ts if isinstance(ts, datetime) else datetime.utcnow())
        if inspect.isawaitable(out):
            out = _run_coro_sync(out)
        return _payload(out)

    return AdvisoryModuleAdapter("session_awareness", analyze)


def _signal_enhancement_mtf_service() -> AdvisoryModuleAdapter:
    """improvements MultiTimeframeAnalyzer — MTF read on the real
    close series."""
    from trading_bot.improvements.signal_enhancement import (
        MultiTimeframeAnalyzer)

    analyzer = MultiTimeframeAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        prices = [b["close"] for b in hist.bars(60)]
        if len(prices) < 10:
            return {"status": "warming", "bars": len(prices)}
        out = analyzer.analyze_timeframe(
            prices, str(ctx.get("timeframe") or "M15"))
        if inspect.isawaitable(out):
            out = _run_coro_sync(out)
        return _payload(out)

    return AdvisoryModuleAdapter("signal_enhancement_mtf", analyze)


def _fourier_service() -> AdvisoryModuleAdapter:
    """innovations FourierPriceAnalyzer — real FFT on the close
    series. Only innovations category with real math on real data."""
    from trading_bot.innovations.category_09_musical_trading import (
        FourierPriceAnalyzer)

    fa = FourierPriceAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        prices = [b["close"] for b in hist.bars(60)]
        if len(prices) < 16:
            return {"status": "warming", "bars": len(prices)}
        return _payload(fa.analyze_frequencies(prices))

    return AdvisoryModuleAdapter("fourier_price", analyze)


# improvements/forecast_improvements/spread_slippage note:
# CostAdjustedFilter needs live spread_monitor + slippage_tracker
# collaborators — not constructible from obs.
# EliteMarketAnalyzer analyze_volume_profile/order_flow need tick/
# footprint data the bars don't carry.



# ---------------------------------------------------------------------------
# Bucket H - follow-on audit remainder: hawkes events, signal fusion,
# feature mining (deepchart/tda/ricci/indicators already wired above)
# ---------------------------------------------------------------------------


def _hawkes_service() -> AdvisoryModuleAdapter:
    """advanced_analysis HawkesProcessDetector - each real bar is an
    aggregated trade event (TRADE / LARGE_ORDER on volume spikes /
    AGGRESSIVE_* on directional bursts); the detector's event intensity
    and next-event prediction are evidence only."""
    from trading_bot.advanced_analysis.hawkes_process import (
        EventType, HawkesProcessDetector, MarketEvent)

    det = HawkesProcessDetector()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        close = _num(ctx.get("close") or ctx.get("price"))
        if close is None:
            return {"status": "no_price"}
        vol = _num(ctx.get("volume")) or 0.0
        vol_ratio = _num(ctx.get("volume_ratio")) or 1.0
        opn = _num(ctx.get("open")) or close
        side = "BUY" if close >= opn else "SELL"
        if vol_ratio >= 2.0:
            etype = (EventType.AGGRESSIVE_BUY if side == "BUY"
                     else EventType.AGGRESSIVE_SELL)
        elif vol_ratio >= 1.5:
            etype = EventType.LARGE_ORDER
        else:
            etype = EventType.TRADE
        ts = ctx.get("timestamp")
        _parsed = (datetime.fromisoformat(str(ts)).replace(tzinfo=None)
                   if ts else datetime.utcnow())
        det.add_event(MarketEvent(
            timestamp=_parsed,
            event_type=etype, price=close, volume=vol,
            side=side, is_aggressive=vol_ratio >= 1.5))
        return {"hawkes_state": _payload(det.get_current_state()),
                "recent_signals": _primitive(det.get_recent_signals(5)),
                "next_event": _payload(det.predict_next_event(300))}

    return AdvisoryModuleAdapter("hawkes_event_intensity", analyze)


def _alpha_fusion_service() -> AdvisoryModuleAdapter:
    """alpha_research AlphaFusionGraph - trend/momentum/volume/volatility
    generators run on real market_data; lob/sentiment/macro/alt-data
    inputs left None (not fabricated)."""
    from trading_bot.alpha_research.alpha_fusion_graph import (
        AlphaFusionGraph)

    fusion = AlphaFusionGraph()
    hist = _BarHistory(256)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 200)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        return _payload(fusion.generate_and_fuse(
            df, str(ctx.get("symbol") or "UNKNOWN")))

    return AdvisoryModuleAdapter("alpha_fusion_graph", analyze)


# feature_mining note: FeatureMiningSystem.get_live_features needs a
# saved selected_features.parquet (prior fit run) - vacuous without
# training artifacts; not wired.



# ---------------------------------------------------------------------------
# Bucket I - self-state + conditional-feed + online-fit adapters.
# self_state channel: controller injects real CSC internals
# (open positions, settled outcomes, advisor health, prev advisory calls)
# into the observation - these modules need state, not market fields.
# ---------------------------------------------------------------------------


def _self_state(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    """Read the controller-injected self_state block; empty when the
    observation is probed outside the CSC pipeline."""
    st = ctx.get("self_state")
    return st if isinstance(st, Mapping) else {}


def _position_state_service() -> AdvisoryModuleAdapter:
    """position/ CorrelationExposureMonitor + PositionAgingTracker on
    CSC's real open positions (self_state.open_positions)."""
    from trading_bot.position.position_management import (
        CorrelationExposureMonitor, Position, PositionAgingTracker,
        PositionSide)

    corr = CorrelationExposureMonitor()
    aging = PositionAgingTracker()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        raw = _self_state(ctx).get("open_positions") or {}
        if not raw:
            return {"status": "no_open_positions"}
        positions = []
        for sym, p in raw.items():
            positions.append(Position(
                position_id=str(p.get("trade_ids", sym)),
                account_id="csc", symbol=str(sym),
                side=(PositionSide.LONG
                      if p.get("direction") == "BUY" else PositionSide.SHORT),
                quantity=1.0,
                entry_price=float(p.get("entry_price") or 0.0),
                current_price=float(
                    ctx.get("close") or ctx.get("price")
                    or p.get("entry_price") or 0.0),
                open_time=datetime.utcnow()))
        out = _probe_all((
            ("correlation_exposure", lambda: corr.analyze(positions)),
            ("position_aging", lambda: aging.analyze(positions)),
        ))
        return out or {"status": "no_position_read"}

    return AdvisoryModuleAdapter("position_state_monitor", analyze)


def _psychology_service() -> AdvisoryModuleAdapter:
    """psychology/ CognitiveBiasDetector + TiltDetector fed the real
    settled-outcome journal - trade history IS the observation here."""
    from trading_bot.psychology.behavioral_features import (
        CognitiveBiasDetector, EmotionalState, TiltDetector, TradeRecord)

    bias = CognitiveBiasDetector()
    tilt = TiltDetector()
    fed: set = set()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        st = _self_state(ctx)
        settled = st.get("settled_outcomes") or []
        for o in settled:
            key = (o.get("symbol"), o.get("entry_seq"), o.get("exit_seq"))
            if key in fed:
                continue
            fed.add(key)
            t = TradeRecord(
                trade_id="%s_%s" % (key[0], key[2]),
                symbol=str(key[0]), direction=str(o.get("direction")),
                entry_time=datetime.utcnow(), exit_time=datetime.utcnow(),
                entry_price=float(o.get("entry_price") or 0.0),
                exit_price=float(o.get("exit_price") or 0.0),
                planned_stop=0.0, actual_stop=0.0,
                planned_target=0.0, actual_target=0.0,
                pnl=float(o.get("realized_return") or 0.0),
                followed_plan=True,
                emotional_state=EmotionalState.CALM,
                notes=str(o.get("reason") or ""))
            for d in (bias, tilt):
                try:
                    d.add_trade(t)
                except Exception:
                    pass
        run_pnl = sum(float(o.get("realized_return") or 0.0)
                      for o in settled[-10:])
        out = _probe_all((
            ("bias_report", lambda: bias.get_bias_report()),
            ("tilt", lambda: tilt.assess_tilt(
                run_pnl, EmotionalState.CALM,
                rule_violations=int(
                    st.get("funnel", {}).get("risk_rejected", 0) or 0))),
        ))
        out["trades_seen"] = len(fed)
        return out

    return AdvisoryModuleAdapter("psychology_bias_tilt", analyze)


def _counterfactual_service() -> AdvisoryModuleAdapter:
    """skills CounterfactualAnalyzer on the real action/outcome journal:
    prices = real closes, actions = settled decisions, outcomes =
    realized returns."""
    from trading_bot.skills.ai_ml_enhancements.counterfactual_analyzer import (
        CounterfactualAnalyzer)

    ca = CounterfactualAnalyzer()
    hist = _BarHistory(256)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        prices = hist.prices()
        settled = _self_state(ctx).get("settled_outcomes") or []
        if len(prices) < 10 or not settled:
            return {"status": "warming_or_no_outcomes",
                    "bars": len(prices), "outcomes": len(settled)}
        actions = [str(o.get("direction") or "HOLD") for o in settled]
        outcomes = [float(o.get("realized_return") or 0.0) for o in settled]
        import numpy as np
        return _payload(ca.analyze(
            np.asarray(prices[-len(settled):]),
            actions[-len(prices[-len(settled):]):]
            if len(settled) > len(prices) else actions,
            outcomes[-len(prices[-len(settled):]):]
            if len(settled) > len(prices) else outcomes))

    return AdvisoryModuleAdapter("counterfactual_outcomes", analyze)


def _hf_decay_service() -> AdvisoryModuleAdapter:
    """hedge_fund_safety HiddenRiskDetection - ModelDecayDetector fed real
    settled predictions (predicted direction vs realized return sign)."""
    from trading_bot.hedge_fund_safety.hidden_risk_detection import (
        HiddenRiskDetection)

    hrd = HiddenRiskDetection({})
    fed: set = set()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        st = _self_state(ctx)
        for o in st.get("settled_outcomes") or []:
            key = (o.get("symbol"), o.get("exit_seq"))
            if key in fed:
                continue
            fed.add(key)
            try:
                hrd.record_prediction(
                    "csc_direction",
                    1.0 if o.get("direction") == "BUY" else -1.0,
                    1.0 if float(o.get("realized_return") or 0) > 0
                    else -1.0,
                    0.6)
            except Exception:
                pass
        out = _probe_all((
            ("model_health", lambda: hrd.get_status()),
            ("decay", lambda: hrd.run_full_scan(["csc_direction"],
                                              [ctx.get("symbol")])),
        ))
        out["predictions_fed"] = len(fed)
        return out

    return AdvisoryModuleAdapter("hf_model_decay", analyze)


def _alpha_brain_service() -> AdvisoryModuleAdapter:
    """alpha_research UnifiedAlphaBrain - register advisory capabilities
    as strategies, submit last cycle's real advisory calls as signals,
    read the collective aggregate. Evidence aggregation of advisor
    outputs; CSC remains the sole decision authority."""
    from trading_bot.alpha_research.unified_alpha_brain import (
        SignalStrength, StrategySignal, UnifiedAlphaBrain)

    brain = UnifiedAlphaBrain()
    known: set = set()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        calls = _self_state(ctx).get("last_advisory_calls") or []
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        submitted = 0
        for c in calls:
            cap = str(c.get("capability_id") or c.get("agent") or "")
            if not cap:
                continue
            if cap not in known:
                try:
                    brain.register_strategy(cap, "advisory")
                    known.add(cap)
                except Exception:
                    pass
            d = c.get("direction")
            if d not in ("BUY", "SELL"):
                continue
            try:
                conf = float(c.get("confidence") or 0.3)
                brain.submit_signal(StrategySignal(
                    signal_id="%s_%s" % (cap,
                                         _self_state(ctx).get(
                                             "observation_seq")),
                    strategy_name=cap, timestamp=datetime.utcnow(),
                    symbol=symbol,
                    direction="long" if d == "BUY" else "short",
                    strength=(SignalStrength.STRONG if conf > 0.6
                              else SignalStrength.MODERATE),
                    confidence=min(max(conf, 0.0), 1.0)))
                submitted += 1
            except Exception:
                pass
        try:
            dec = brain.get_collective_decision(symbol)
            brain.clear_pending_signals()
            out = _payload(dec)
            out["signals_submitted"] = submitted
            out["strategies_registered"] = len(known)
            return out
        except Exception as e:
            return {"status": "aggregate_error", "error": str(e)[:200]}

    return AdvisoryModuleAdapter("alpha_brain_collective", analyze)


def _ml_online_service() -> AdvisoryModuleAdapter:
    """ml/ PricePredictor.detect_anomalies + PatternRecognizer.scan -
    statistical reads on the real bar frame; no training required."""
    from trading_bot.ml.predictive_models import (
        PatternRecognizer, PricePredictor)

    pp = PricePredictor()
    pr = PatternRecognizer()
    hist = _BarHistory(128)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        df = _bars_df(hist, 60)
        if df is None:
            return {"status": "warming", "bars": len(hist)}
        out = _probe_all((
            ("price_anomalies",
             lambda: pp.detect_anomalies(df.copy())),
            ("chart_patterns", lambda: pr.scan(df.copy())),
        ))
        return out or {"status": "no_ml_read"}

    return AdvisoryModuleAdapter("ml_statistical", analyze)


def _ensemble_meta_service() -> AdvisoryModuleAdapter:
    """alpha_research EnsembleMetaLearner - lazily fits sklearn models on
    (feature vector -> next-bar direction) once enough real samples
    exist. Hermes-only (sklearn)."""
    import numpy as np
    from trading_bot.alpha_research.ensemble_meta_learner import (
        EnsembleMetaLearner)

    meta = EnsembleMetaLearner()
    X: list = []
    y: list = []
    pending: Dict[str, Any] = {}
    fitted = {"ok": False}

    def analyze(ctx: Mapping[str, Any]) -> Any:
        close = _num(ctx.get("close") or ctx.get("price"))
        feats = list(_feature_vector(ctx))
        # label the pending sample with this bar's realized move
        if pending and close is not None:
            y.append(1.0 if close > pending["price"] else -1.0)
        if close is not None:
            X.append(feats)
            pending["price"] = close
        if not fitted["ok"]:
            n = min(len(X), len(y))
            if n >= 60:
                try:
                    meta.fit(np.asarray(X[:n]), np.asarray(y[:n]))
                    fitted["ok"] = True
                except Exception:
                    pass
            else:
                return {"status": "fitting", "samples": n}
        try:
            pred = meta.predict(np.asarray([feats]))
            return {"prediction": _primitive(pred),
                    "samples": len(y)}
        except Exception as e:
            return {"status": "predict_error", "error": str(e)[:200]}

    return AdvisoryModuleAdapter("ensemble_meta_online", analyze)


def _conditional_feed_service() -> AdvisoryModuleAdapter:
    """Conditional external-feed adapters - each emits ONLY when the
    observation carries the real feed field; abstains otherwise.
    arbitrage: venue_prices; central_bank_tracker: cb_rates;
    market_microbiome: order_flow; news sentiment: news_items;
    social sentiment: sentiment."""
    from trading_bot.arbitrage.arbitrage_network import (
        CrossExchangeArbitrage)
    from trading_bot.advanced_analysis.central_bank_tracker import (
        CentralBankTracker)
    from trading_bot.advanced_analysis.market_microbiome import (
        MarketMicrobiome)
    arb = CrossExchangeArbitrage()
    cb = CentralBankTracker()
    micro = MarketMicrobiome()
    news_state: Dict[str, Any] = {"agg": None}
    # lazy: NewsAggregator needs aiohttp (hermes)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        probes = []
        venues = ctx.get("venue_prices")
        if isinstance(venues, Mapping) and len(venues) >= 2:
            probes.append(("arbitrage", lambda: _payload(
                arb.detect_opportunities(dict(venues)))))
        rates = ctx.get("cb_rates")
        if isinstance(rates, Mapping) and rates:
            for bank, rate in list(rates.items())[:8]:
                try:
                    cb.update_rate(str(bank), float(rate))
                except Exception:
                    pass
            probes.append(("central_bank", lambda: _payload(
                cb.get_trading_signals())))
        flow = ctx.get("order_flow")
        if isinstance(flow, (list, tuple)) and flow:
            try:
                micro.process_order_flow(list(flow))
            except Exception:
                pass
            probes.append(("microbiome", lambda: _payload(
                micro.get_ecosystem_state())))
        items = ctx.get("news_items")
        if isinstance(items, (list, tuple)) and items:
            if news_state["agg"] is None:
                try:
                    from trading_bot.sentiment.realtime_sentiment_engine import (
                        NewsAggregator)
                    news_state["agg"] = NewsAggregator()
                except Exception:
                    news_state["agg"] = False
            news = news_state["agg"]
            for art in items[:10] if news else ():
                if isinstance(art, Mapping):
                    try:
                        news.process_news(
                            str(art.get("title") or ""),
                            str(art.get("description")
                                or art.get("summary") or ""),
                            str((art.get("source") or {}).get("name")
                                if isinstance(art.get("source"), Mapping)
                                else art.get("source") or "unknown"))
                    except Exception:
                        pass
            cache = list(news.news_cache) if news else []
            probes.append(("news_sentiment", lambda: {
                "articles_processed": len(cache),
                "mean_sentiment": (sum(
                    float(getattr(e, "sentiment", 0) or 0)
                    for e in cache) / len(cache)) if cache else None,
                "top_impact": [
                    {"headline": getattr(e, "headline", "")[:80],
                     "sentiment": getattr(e, "sentiment", None),
                     "impact": getattr(e, "impact_score", None)}
                    for e in sorted(
                        cache, key=lambda e: abs(
                            getattr(e, "impact_score", 0) or 0),
                        reverse=True)[:3]],
            }))
        social = ctx.get("sentiment")
        if isinstance(social, Mapping) and social:
            probes.append(("social_sentiment", lambda: _primitive(social)))
        f13 = ctx.get("sec_13f")
        if isinstance(f13, Mapping) and f13.get("holdings"):
            probes.append(("sec_13f_filings", lambda: _primitive(f13)))
        cot = ctx.get("cot")
        if isinstance(cot, Mapping) and cot.get("report_date"):
            probes.append(("cot_positioning", lambda: _primitive(cot)))
        dp = ctx.get("dark_pool")
        if isinstance(dp, Mapping) and dp.get("total_ats_volume"):
            probes.append(("dark_pool_volume", lambda: _primitive(dp)))
        if not probes:
            return {"status": "no_external_feeds"}
        return _probe_all(probes) or {"status": "no_external_feeds"}

    return AdvisoryModuleAdapter("external_feed_conditional", analyze)


# Factories for services that are genuinely observation-callable. Each
# entry is attached at assembly time inside a probe; failures skip the
# service rather than break the runtime.
DEFAULT_ADVISORY_FACTORIES: Tuple[Tuple[str, Callable[[], Any]], ...] = (
    ("multi_agent_debate", _debate_service),
    ("market_anomaly_detection", _anomaly_service),
    ("regime_classification", _regime_classifier_service),
    ("trend_following_agent", _trend_agent_service),
    ("failure_mode_detection", _failure_mode_service),
    # Bucket A — orphan packages with genuinely obs-callable analyzers
    ("alpha_research_market_state", _alpha_research_state_service),
    ("alpha_research_risk_matrix", _alpha_research_risk_service),
    ("alpha_research_predator_defense", _alpha_research_predator_service),
    ("alpha_research_footprint", _alpha_research_footprint_service),
    ("institutional_market_selection", _institutional_selection_service),
    ("brain_technical_analysis", _brain_technical_service),
    ("brain_regime_classification", _brain_regime_service),
    ("cognitive_architecture_regime", _cognitive_regime_service),
    ("cognitive_performance_eval", _cognitive_perf_service),
    ("elite_factor_matrix", _elite_factor_service),
    ("adaptive_market_regime", _adaptive_regime_service),
    ("adaptive_learning_predict", _adaptive_learning_service),
    ("intelligence_strategy_stats", _intelligence_strategy_service),
    ("self_learning_ensemble", _self_learning_ensemble_service),
    ("signal_regime_change", _signal_regime_change_service),
    ("signal_statistical_outliers", _signal_outlier_service),
    ("tamic_market_time", _tamic_market_time_service),
    ("tamic_institutional_time", _institutional_time_service),
    ("tamic_optionality", _optionality_service),
    ("tamic_time_risk", _time_risk_service),
    ("self_diagnostic_health", _self_diagnostic_service),
    ("aletheia_decision_audit", _aletheia_audit_service),
    ("superintelligence_regime_strategy", _superintel_regime_service),
    ("systems_ai_stress_test", _systems_stress_service),
    # Bucket B — additional capabilities from partially-wired packages
    ("mean_reversion_agent",
     _make_legacy_agent_service("mean_reversion_agent",
                                "MeanReversionAgent")),
    ("volatility_agent",
     _make_legacy_agent_service("volatility_agent", "VolatilityAgent")),
    ("risk_manager_agent",
     _make_legacy_agent_service("risk_manager_agent", "RiskManagerAgent")),
    ("agents2_mean_reversion",
     _make_agents2_service("agents2_mean_reversion",
                           "MeanReversionAgent")),
    ("agents2_volatility",
     _make_agents2_service("agents2_volatility", "VolatilityAgent")),
    ("regime_shift_detection",
     _make_failure_detector_service("regime_shift_detection",
                                    "RegimeShiftDetector")),
    ("liquidity_evaporation_detection",
     _make_failure_detector_service("liquidity_evaporation_detection",
                                    "LiquidityEvaporationDetector")),
    ("uncertainty_explosion_detection",
     _make_failure_detector_service("uncertainty_explosion_detection",
                                    "UncertaintyExplosionDetector")),
    ("institutional_accumulation",
     _make_anomaly_classifier_service(
         "institutional_accumulation",
         "trading_bot.market_intelligence.categories."
         "institutional_accumulation",
         "InstitutionalAccumulationClassifier")),
    ("macro_regime_shifts",
     _make_anomaly_classifier_service(
         "macro_regime_shifts",
         "trading_bot.market_intelligence.categories.macro_regime_shifts",
         "MacroRegimeShiftsClassifier")),
    ("macro_strategist_agent",
     _make_debate_agent_service("macro_strategist_agent",
                                "MacroStrategist")),
    ("risk_sentinel_agent",
     _make_debate_agent_service("risk_sentinel_agent", "RiskSentinel")),
    ("adversarial_failure_match", _adversarial_failure_match_service),
    ("alphaalgo_performance_sensor", _alphaalgo_perf_sensor_service),
    # Bucket C — loose orphan root files
    ("alphaalgo_5star_risk_metrics", _alphaalgo_5star_risk_service),
    ("world2agent_bridge", _world2agent_bridge_service),
    # Bucket A2 — second-pass: newly obs-callable orphan packages
    ("mixture_of_experts", _moe_router_service),
    ("market_microstructure", _microstructure_service),
    ("cognitive_economy_supervisor",
     _economy_agent_service("cognitive_economy_supervisor",
                            "SupervisorAgent")),
    ("cognitive_economy_risk",
     _economy_agent_service("cognitive_economy_risk", "RiskAgent")),
    ("cognitive_economy_data",
     _economy_agent_service("cognitive_economy_data", "DataAgent")),
    ("cognitive_economy_learning",
     _economy_agent_service("cognitive_economy_learning",
                            "LearningAgent")),
    ("cognitive_economy_strategy",
     _economy_agent_service("cognitive_economy_strategy",
                            "StrategyAgent")),
    ("regime_transition_detector", _regime_transition_service),
    ("market_psychology", _market_psychology_service),
    ("improvement_findings", _improvement_findings_service),
    ("neural_hub_topology", _neural_hub_service),
    ("hivemind_analyst", _hivemind_analyst_service),
    ("radar_regime", _radar_regime_service),
    ("self_concept_guard", _self_concept_service),
    ("system_health", _self_healing_health_service),
    ("self_learning_health", _self_learning_health_service),
    ("mastery_reflection", _mastery_reflection_service),
    ("codebase_introspection", _introspection_service),
    ("regime_memory", _regime_memory_service),
    ("trend_reversal", _trend_reversal_service),
    ("regime_discovery", _regime_discovery_service),
    ("strategy_selector", _strategy_selector_service),
    ("data_drift", _data_drift_service),
    ("performance_decay", _performance_decay_service),
    ("signal_decay", _signal_decay_service),
    ("autonomous_tuner", _autonomous_tuner_service),
    ("planner_agent", _planner_agent_service),
    ("alpha_evolve_signal", _alpha_evolve_service),
    ("polymarket_estimate", _polymarket_service),
    ("maven_stats", _maven_stats_service),
    ("aamis_market", _aamis_service),
    ("learner_knowledge", _learner_knowledge_service),
    ("decision_explainer", _decision_explainer_service),
    ("alpha_weakness_detector", _alpha_weakness_service),
    # Bucket B additions — second capabilities in wired packages
    ("regime_hostility", _regime_hostility_service),
    ("policy_network", _policy_network_service),
    ("value_network", _value_network_service),
    ("adversarial_hardening", _hardening_score_service),
    ("hypothesis_generator", _hypothesis_generator_service),
    ("bloomberg_benchmark", _bloomberg_benchmark_service),
    ("directional_bias", _directional_bias_service),
    ("orderbook_imbalance", _orderbook_imbalance_service),
    ("tactical_executioner_agent",
     _make_debate_agent_service("tactical_executioner_agent",
                                "TacticalExecutioner")),
    ("agents2_market_maker",
     _make_agents2_service("agents2_market_maker", "MarketMakerAgent")),
    # Bucket C additions — loose root files
    ("aean_meta_cycle", _aean_cycle_service),
    ("elite_master_analysis", _elite_master_service),
    ("complete_impl_market_intel", _complete_impl_service),
    # Bucket D — non-AI-named orphan dirs
    ("hivemind_collective", _hivemind_collective_service),
    ("hivemind_threat_assessment", _hivemind_threat_service),
    ("apex_regime_surveillance", _apex_regime_service),
    ("apex_transaction_cost", _apex_cost_service),
    ("dg_volatility_regime", _dg_volatility_service),
    ("gets_market_structure", _gets_structure_service),
    ("feedback_performance", _feedback_perf_service),
    ("alpha_evolve_regime", _alpha_evolve_regime_service),
    # Bucket E — analysis/ package + cross-dir obs-feedable analyzers
    ("analysis_patterns", _analysis_patterns_service),
    ("analysis_market_intel", _analysis_market_intel_service),
    ("analysis_ict_concepts", _analysis_ict_service),
    ("analysis_liquidity", _analysis_liquidity_service),
    ("analysis_mtf_confirmation", _analysis_mtf_service),
    ("analysis_liquidity_radar", _analysis_liq_radar_service),
    ("analysis_price_action", _analysis_price_action_service),
    ("analysis_market_regime", _analysis_regime_service),
    ("analysis_anomaly", _analysis_anomaly_service),
    ("analysis_traps", _analysis_traps_service),
    ("analysis_volume_flow", _analysis_volume_flow_service),
    ("analysis_market_context", _analysis_context_service),
    ("black_swan_conditions", _black_swan_service),
    ("pullback_detector", _pullback_detector_service),
    ("alpha_decay", _alpha_decay_service),
    ("iceberg_detector", _iceberg_detector_service),
    ("momentum_specialist", _momentum_specialist_service),
    ("intelligence_brain_v2", _intelligence_brain_v2_service),
    # Bucket G - second audit pass: Wyckoff / structure / session
    ("analysis_wyckoff", _analysis_wyckoff_service),
    ("analysis_wyckoff_events", _analysis_wyckoff_full_service),
    ("analysis_market_structure", _analysis_structure_service),
    ("analysis_mtf_intelligence", _analysis_mtf_intel_service),
    ("analysis_liquidity_simple", _analysis_liq_simplified_service),
    ("vpin_informed_trading", _vpin_service),
    ("liquidity_gravity_path", _gravity_well_service),
    ("elite_equal_levels", _elite_equal_levels_service),
    ("elite_swing_points", _elite_swing_points_service),
    ("elite_price_action", _elite_price_action_service),
    ("elite_patterns", _elite_patterns_service),
    ("brain_tier3_structure", _brain_structure_service),
    ("brain_tier2_orderflow", _brain_orderflow_service),
    ("fractal_divergence", _fractal_divergence_service),
    ("volatility_impulse", _volatility_impulse_service),
    ("liquidity_holography", _liquidity_holography_service),
    ("mi_absorption", _mi_absorption_service),
    ("mi_manipulation", _mi_manipulation_service),
    ("mi_market_structure", _mi_structure_service),
    ("mi_time_price", _mi_time_price_service),
    ("mi_wyckoff_accumulation", _mi_wyckoff_service),
    ("session_awareness", _session_awareness_service),
    ("signal_enhancement_mtf", _signal_enhancement_mtf_service),
    ("fourier_price", _fourier_service),
    # Bucket F - DOCS/CSC_WIRING_AUDIT.md candidates
    ("upgrades_price_structure", _upgrades_structure_service),
    ("upgrades_regime_divergence", _upgrades_regime_service),
    ("institutional_entry_footprint", _institutional_footprint_service),
    ("deepchart_time_to_move", _deepchart_ttm_service),
    ("deepchart_sr_memory", _deepchart_sr_memory_service),
    ("tda_topology", _tda_topology_service),
    ("ricci_momentum", _ricci_momentum_service),
    ("fractal_momentum_div", _fractal_momentum_div_service),
    ("improvements_regime", _improvements_regime_service),
    ("improvements_pullback", _improvements_pullback_service),
    ("improvements_session", _improvements_session_service),
    ("black_swan_threat", _black_swan_threat_service),
    ("spai_trend_reversal", _spai_trend_reversal_service),
    ("deepchart_price_response", _deepchart_price_response_service),
    ("indicators_adv_technical", _indicators_adv_technical_service),
    ("indicators_liquidity", _indicators_liquidity_service),
    ("peer_correlation", _peer_correlation_service),
    ("volume_profile", _volume_profile_service),
    ("upgrades_change_detect", _upgrades_change_detect_service),
    ("analysis_unified_analyzer", _unified_analyzer_service),
    ("hypernetwork_regime", _hypernetwork_regime_service),
    ("marl_strategists", _marl_strategists_service),
    ("realtime_ensemble", _realtime_ensemble_service),
    ("feature_discovery", _feature_discovery_service),
    ("quant_regime_microstructure", _quant_regime_service),
    ("concept_drift", _concept_drift_service),
    ("profit_max_market_regime", _profit_max_regime_service),
    ("confluence_session", _confluence_session_service),
    ("deep_agent_market", _deep_agent_system_service),
    ("hft_orderbook_imbalance", _hft_orderbook_service),
    # Bucket H - follow-on audit remainder
    ("hawkes_event_intensity", _hawkes_service),
    ("alpha_fusion_graph", _alpha_fusion_service),
    # Bucket I - self-state + conditional-feed + online-fit
    ("position_state_monitor", _position_state_service),
    ("psychology_bias_tilt", _psychology_service),
    ("counterfactual_outcomes", _counterfactual_service),
    ("hf_model_decay", _hf_decay_service),
    ("alpha_brain_collective", _alpha_brain_service),
    ("ml_statistical", _ml_online_service),
    ("ensemble_meta_online", _ensemble_meta_service),
    ("external_feed_conditional", _conditional_feed_service),
)

# Services measured substantive or directional on real EURUSD bars
# (scripts/advisor_degeneracy_report.py, 60-bar replay): 18/172.
# Everything else emitted only degenerate/missing_data statuses - safe
# to exclude by construction, no outcome history required.
MEASURED_ACTIVE_SET = frozenset((
    "aean_meta_cycle", "alpha_evolve_signal", "analysis_mtf_confirmation",
    "brain_technical_analysis", "deepchart_sr_memory",
    "dg_volatility_regime", "directional_bias", "elite_factor_matrix",
    "hft_orderbook_imbalance", "improvements_pullback",
    "improvements_regime", "indicators_adv_technical",
    "indicators_liquidity", "market_anomaly_detection",
    "mixture_of_experts", "ricci_momentum", "self_learning_health",
    "volume_profile",
))

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
    ("ml", "imported by core/csc/model_engineering.py "
     "(confidence_calibration + data_leakage_guard) - canonical "
     "dependency, statistical analyzers attached via advisory seam"),
)

# Orphan modules that are NOT observation-callable advisory services —
# recorded so the audit map is total rather than silently partial.
# Attached dirs are covered by DEFAULT_ADVISORY_FACTORIES and therefore
# deliberately absent here.
UNWIRED_ORPHAN_MODULES: Tuple[Tuple[str, str], ...] = (
    ("advanced_intelligence", "mixture_of_experts attached; deep-model "
     "remainder (diffusion, capsule, contrastive, energy-based) takes "
     "trained tensors, not observation dicts"),
    ("autonomous_superintelligence", "package __init__ chains "
     "torch-dependent self_modifier; analyzers are fleet/research "
     "coordinators, not obs-callable"),
    ("core_agent_system", "legacy agents + policy/value networks "
     "attached; framework remainder subsumed by PCA"),
    ("improvement_agent", "improvement_findings attached; "
     "codebase self-modification machinery (ChangeManager) is not "
     "obs-callable"),
    ("intel", "news/macro ingestion; external data dependencies"),
    ("meta_learning", "maml.Maml.process is an identity passthrough stub "
     "(_process_internal returns input); no signal to wire"),
    ("neural_integration", "neural_hub_topology attached; model "
     "integration layer is torch-dependent"),
    ("radar_ai", "hivemind_analyst + radar_regime attached; "
     "OntologyDrivenAgent declares analyze/learn abstract — no "
     "obs-callable surface without fabricated stubs"),
    ("self_concepts", "self_concept_guard attached; concept catalogs "
     "proper are self-model bookkeeping, not market analyzers"),
    ("self_healing_ai", "system_health attached; healing workflow "
     "proper is state validation, not an obs-callable market analyzer"),
    ("self_mastery", "mastery_reflection attached; skill/knowledge "
     "bookkeeping remainder has no obs-callable analyzer"),
    ("sentient_core", "codebase_introspection attached; introspection "
     "facades (get_performance_report, get_threat_level) report internal "
     "state only"),
    ("superpowerful_ai", "trend_reversal + regime_discovery + "
     "strategy_selector attached; get_*_statistics facades are not "
     "obs-callable"),
    ("ai", "autonomous_tuner attached; BayesianOptimizer + torch-bound "
     "hub are not obs-callable"),
    ("ai_core", "planner_agent attached; verifier agents expose "
     "get_status only"),
    ("ai_engineer", "code-change safeguard machinery (safeguards, "
     "sandbox, compliance audit); approval semantics, not a market "
     "advisory"),
    ("adversarial_decision", "adversarial_trade_eval + adversarial_ — "
     "failure_match attached - the 7-stage red-team runs on both "
     "directions with evidence-only output; decision_gate and "
     "position_sizer stages stay inside the adapter, authority "
     "surfaces"),
    ("alphaalgo_core", "market_physics_filter removed — process() "
     "requires orderbook bids/asks (L2 data) the observation does not "
     "carry; 'spread inf / liquidity 0' verdicts were missing-data "
     "noise, not market assessment"),
    ("aads", "alpha_evolve_signal + polymarket_estimate + maven_stats "
     "attached; aip_agents synthesize bull/bear cases via np.random — "
     "fabricated analysis, stays quarantined"),
    ("aamis_v3", "aamis_market attached; consolidated-engine status "
     "facades are not obs-callable"),
    ("learning", "RL learners (DistributionalQLearning, EKSFTTrainer) "
     "are offline training loops, not obs-callable advisors"),
    ("agents", "multi_agent_debate attached (system + MacroStrategist + "
     "RiskSentinel + TacticalExecutioner); prosecutor roles need an "
     "in-flight DebateTopic"),
    ("autonomous_learner", "learner_knowledge attached (evidence only); "
     "deprecated RSI duplicate carries no authority per AGENTS.md"),
    ("explainability", "decision_explainer attached; SHAPExplainer is "
     "post-hoc — needs a fitted model and its training data"),
    # Loose orphan root files (bucket C audit entries)
    ("unified_ai_brain.py", "quarantined parallel brain — the canonical "
     "path may not import it (brain quarantine test); subsystem registry "
     "façade, not an obs-callable analyzer"),
    ("agent_orchestrator.py", "flat-path shim re-exporting "
     "services.tier4_services; no analyzer"),
    ("ai_learner.py", "deprecated bridge to sentient_core.ai_learner "
     "per AGENTS.md"),
    ("neural_network.py", "merge-loss compatibility stub (no-op "
     "methods)"),
    ("maml_trainer.py", "merge-loss compatibility stub re-exporting "
     "ml.meta_learning.maml"),
    ("continual_learner.py", "deprecated shim; RSI is canonical"),
    ("advanced_rl_agents.py", "flat-path shim re-exporting ml.offline_rl "
     "agents — offline RL needs trained policies, not observations"),
    ("bear_agent.py", "merge-loss compatibility stub (no-op methods)"),
    ("magic_agent.py", "merge-loss compatibility stub (no-op methods)"),
    ("mbop_agent.py", "merge-loss compatibility stub (no-op methods)"),
    ("aean_meta_intelligence_layer.py", "aean_meta_cycle attached — "
     "empty-cycle report; market obs cannot supply FrontierObservation/"
     "BenchmarkTask inputs"),
    ("reward_model.py", "flat-path shim re-exporting "
     "evolution_layer.reward_model"),
    ("adaptive_retrainer.py", "merge-loss compatibility stub (no-op "
     "methods)"),
    ("auto_rollback.py", "deprecated shim; RSI is canonical"),
    ("code_evolver.py", "deprecated bridge; RSI is canonical per "
     "AGENTS.md"),
    ("performance_optimizer.py", "deprecated shim; RSI is canonical"),
    ("experiment_tracker.py", "deprecated shim; RSI is canonical"),
    ("world2agent.py", "world2agent_bridge attached — adapter module "
     "a2a.py stays a live dep of that seam"),
    ("alphaalgo_5star.py", "alphaalgo_5star_risk_metrics attached — "
     "probe-gated on the module's logger API"),
    ("elite_master_system.py", "elite_master_analysis attached — "
     "analyze_market only; execute paths never touched"),
    ("complete_implementation.py", "complete_impl_market_intel attached "
     "— regime detector fed real closes plus session multiplier"),
    ("a2a.py", "live dep — imported by the world2agent_bridge adapter"),
    # --- package-shadowed root files (import resolves to the
    #     same-named package; the .py file is unreachable) ---
    # --- package-shadowed root files (import resolves to the
    #     same-named package; the .py file is unreachable) ---
    ("adaptive_systems.py", "shadowed by trading_bot/adaptive_systems/ package — file unreachable"),
    ("agents.py", "shadowed by trading_bot/agents/ package — file unreachable"),
    ("agents2.py", "shadowed by trading_bot/agents2/ package — file unreachable"),
    ("analysis.py", "shadowed by trading_bot/analysis/ package — file unreachable"),
    ("api.py", "shadowed by trading_bot/api/ package — file unreachable"),
    ("approval.py", "shadowed by trading_bot/approval/ package — file unreachable"),
    ("arbitrage.py", "shadowed by trading_bot/arbitrage/ package — file unreachable"),
    ("audit.py", "shadowed by trading_bot/audit/ package — file unreachable"),
    ("autonomous.py", "shadowed by trading_bot/autonomous/ package — file unreachable"),
    ("backtesting.py", "shadowed by trading_bot/backtesting/ package — file unreachable"),
    ("blockchain.py", "shadowed by trading_bot/blockchain/ package — file unreachable"),
    ("broker.py", "shadowed by trading_bot/broker/ package — file unreachable"),
    ("connectivity.py", "shadowed by trading_bot/connectivity/ package — file unreachable"),
    ("critical_fixes.py", "shadowed by trading_bot/critical_fixes/ package — file unreachable"),
    ("data.py", "shadowed by trading_bot/data/ package — file unreachable"),
    ("documentation.py", "shadowed by trading_bot/documentation/ package — file unreachable"),
    ("evolution_layer.py", "shadowed by trading_bot/evolution_layer/ package — file unreachable"),
    ("exit_strategies.py", "shadowed by trading_bot/exit_strategies/ package — file unreachable"),
    ("exits.py", "shadowed by trading_bot/exits/ package — file unreachable"),
    ("explainability.py", "shadowed by trading_bot/explainability/ package — file unreachable"),
    ("features.py", "shadowed by trading_bot/features/ package — file unreachable"),
    ("filters.py", "shadowed by trading_bot/filters/ package — file unreachable"),
    ("governance.py", "shadowed by trading_bot/governance/ package — file unreachable"),
    ("indicators.py", "shadowed by trading_bot/indicators/ package — file unreachable"),
    ("integration.py", "shadowed by trading_bot/integration/ package — file unreachable"),
    ("integrations.py", "shadowed by trading_bot/integrations/ package — file unreachable"),
    ("mobile_app.py", "shadowed by trading_bot/mobile_app/ package — file unreachable"),
    ("models.py", "shadowed by trading_bot/models/ package — file unreachable"),
    ("multimodal.py", "shadowed by trading_bot/multimodal/ package — file unreachable"),
    ("portfolio.py", "shadowed by trading_bot/portfolio/ package — file unreachable"),
    ("quantum.py", "shadowed by trading_bot/quantum/ package — file unreachable"),
    ("qwen_codemender.py", "shadowed by trading_bot/qwen_codemender/ package — file unreachable"),
    ("realtime_trading_core.py", "shadowed by trading_bot/realtime_trading_core/ package — file unreachable"),
    ("risk.py", "shadowed by trading_bot/risk/ package — file unreachable"),
    ("schemas.py", "shadowed by trading_bot/schemas/ package — file unreachable"),
    ("sentiment.py", "shadowed by trading_bot/sentiment/ package — file unreachable"),
    ("signals.py", "shadowed by trading_bot/signals/ package — file unreachable"),
    ("system.py", "shadowed by trading_bot/system/ package — file unreachable"),
    ("tamic.py", "shadowed by trading_bot/tamic/ package — file unreachable"),
    ("trade_journal.py", "shadowed by trading_bot/trade_journal/ package — file unreachable"),
    ("ultimate_approval.py", "shadowed by trading_bot/ultimate_approval/ package — file unreachable"),
    ("unified_approval.py", "shadowed by trading_bot/unified_approval/ package — file unreachable"),
    ("upgrades.py", "shadowed by trading_bot/upgrades/ package — file unreachable"),
    ("utils.py", "shadowed by trading_bot/utils/ package — file unreachable"),
    ("voice_assistant.py", "shadowed by trading_bot/voice_assistant/ package — file unreachable"),
    ("wealth.py", "shadowed by trading_bot/wealth/ package — file unreachable"),
    # --- merge-era deprecation stubs (subsystem removed during
    #     convergence; no behavior lives here) ---
    ("apply_and_fix.py", "merge-era deprecation stub — no behavior"),
    ("apply_approved.py", "merge-era deprecation stub — no behavior"),
    ("autonomy_levels.py", "merge-era deprecation stub — no behavior"),
    ("behavior_monitor.py", "merge-era deprecation stub — no behavior"),
    ("change_applier.py", "merge-era deprecation stub — no behavior"),
    ("chart_analyzer.py", "merge-era deprecation stub — no behavior"),
    ("classa.py", "merge-era deprecation stub — no behavior"),
    ("classb.py", "merge-era deprecation stub — no behavior"),
    ("deepseek_core.py", "merge-era deprecation stub — no behavior"),
    ("deepseek_engineer_demo.py", "merge-era deprecation stub — no behavior"),
    ("deepseek_integration.py", "merge-era deprecation stub — no behavior"),
    ("deepseek_orchestrator.py", "merge-era deprecation stub — no behavior"),
    ("deepseek_r1_8b_integration.py", "merge-era deprecation stub — no behavior"),
    ("freetradingbot.py", "merge-era deprecation stub — no behavior"),
    ("generator_verifier.py", "merge-era deprecation stub — no behavior"),
    ("governance_orchestrator.py", "merge-era deprecation stub — no behavior"),
    ("guardrails.py", "merge-era deprecation stub — no behavior"),
    ("hardware_manager.py", "merge-era deprecation stub — no behavior"),
    ("human_collaboration.py", "merge-era deprecation stub — no behavior"),
    ("human_protocol.py", "merge-era deprecation stub — no behavior"),
    ("immutable_purpose.py", "merge-era deprecation stub — no behavior"),
    ("live_engineer.py", "merge-era deprecation stub — no behavior"),
    ("mytradingbot.py", "merge-era deprecation stub — no behavior"),
    ("pipeline_orchestrator.py", "merge-era deprecation stub — no behavior"),
    ("positive_impact.py", "merge-era deprecation stub — no behavior"),
    ("pre_commit_hook.py", "merge-era deprecation stub — no behavior"),
    ("proposal_system.py", "merge-era deprecation stub — no behavior"),
    ("protected_registry.py", "merge-era deprecation stub — no behavior"),
    ("quant_research_engine.py", "merge-era deprecation stub — no behavior"),
    ("risk_mitigation.py", "merge-era deprecation stub — no behavior"),
    ("security_hardening.py", "merge-era deprecation stub — no behavior"),
    ("self_evolution_engine.py", "merge-era deprecation stub — no behavior"),
    ("self_improvement_loop.py", "merge-era deprecation stub — no behavior"),
    ("self_improvement_orchestrator.py", "merge-era deprecation stub — no behavior"),
    ("testyourclass.py", "merge-era deprecation stub — no behavior"),
    ("tradingbot.py", "merge-era deprecation stub — no behavior"),
    ("unifiedtradingsystem.py", "merge-era deprecation stub — no behavior"),
    ("verification_engine.py", "merge-era deprecation stub — no behavior"),
    ("workflow_engine.py", "merge-era deprecation stub — no behavior"),
    # --- auto-generated stubs ---
    ("adaptive.py", "auto-generated stub — start/stop/get_status only"),
    ("advanced_exits.py", "auto-generated stub — start/stop/get_status only"),
    ("calendar.py", "auto-generated stub — start/stop/get_status only"),
    ("market_regime.py", "auto-generated stub — start/stop/get_status only"),
    ("scanners.py", "auto-generated stub — start/stop/get_status only"),
    ("transformer.py", "auto-generated stub — start/stop/get_status only"),
    # --- flat-path re-export shims ---
    ("code_analyzer.py", "flat-path re-export shim — no analyzer surface"),
    ("diagnostic_engine.py", "flat-path re-export shim — no analyzer surface"),
    ("exit_strategy.py", "flat-path re-export shim — no analyzer surface"),
    ("experience_memory.py", "flat-path re-export shim — no analyzer surface"),
    ("health_monitor.py", "flat-path re-export shim — no analyzer surface"),
    ("institutional_github_scout.py", "flat-path re-export shim — no analyzer surface"),
    ("knowledge_consolidator.py", "flat-path re-export shim — no analyzer surface"),
    ("knowledge_harvester.py", "flat-path re-export shim — no analyzer surface"),
    ("market_microstructure.py", "flat-path re-export shim — no analyzer surface"),
    ("mastery_orchestrator.py", "flat-path re-export shim — no analyzer surface"),
    ("network_sentinel.py", "flat-path re-export shim — no analyzer surface"),
    ("self_defender.py", "flat-path re-export shim — no analyzer surface"),
    ("self_reflection.py", "flat-path re-export shim — no analyzer surface"),
    ("sentient_orchestrator.py", "flat-path re-export shim — no analyzer surface"),
    ("strategy_genome.py", "flat-path re-export shim — no analyzer surface"),
    # --- status facades (get_status/to_dict only; no
    #     observation-callable analyzer) ---
    ("adwin.py", "status facade only — get_status/to_dict"),
    ("adwin_detector.py", "status facade only — get_status/to_dict"),
    ("alphaalgo_orchestrator.py", "status facade only — get_status/to_dict"),
    ("attention_viz.py", "status facade only — get_status/to_dict"),
    ("causal_analyzer.py", "status facade only — get_status/to_dict"),
    ("deepar.py", "status facade only — get_status/to_dict"),
    ("forecast_ensemble.py", "status facade only — get_status/to_dict"),
    ("hierarchical_rl.py", "status facade only — get_status/to_dict"),
    ("informer.py", "status facade only — get_status/to_dict"),
    ("monitor.py", "status facade only — get_status/to_dict"),
    ("nbeats.py", "status facade only — get_status/to_dict"),
    ("offline_policy_eval.py", "status facade only — get_status/to_dict"),
    ("offline_policy_evaluation.py", "status facade only — get_status/to_dict"),
    ("page_hinkley.py", "status facade only — get_status/to_dict"),
    ("rl_executor.py", "status facade only — get_status/to_dict"),
    ("temporal_fusion_transformer.py", "status facade only — get_status/to_dict"),
    ("tft.py", "status facade only — get_status/to_dict"),
    ("trade_attributor.py", "status facade only — get_status/to_dict"),
    ("uncertainty.py", "status facade only — get_status/to_dict"),
    # --- parallel capital / integration paths (load, wire,
    #     or execute other systems — authority surface) ---
    ("auto_dependency_installer.py", "dependency installer — side-effect tool, never advisory"),
    ("background.py", "parallel capital/integration path — authority surface"),
    ("complete_integrator.py", "parallel capital/integration path — authority surface"),
    ("complete_system_integrator.py", "parallel capital/integration path — authority surface"),
    ("elite_integration.py", "parallel capital/integration path — authority surface"),
    ("master_integration.py", "parallel capital/integration path — authority surface"),
    ("mega_integration.py", "parallel capital/integration path — authority surface"),
    ("optimized_integration.py", "parallel capital/integration path — authority surface"),
    ("position_manager.py", "parallel capital/integration path — authority surface"),
    ("realtime_dependency_manager.py", "parallel capital/integration path — authority surface"),
    ("realtime_system_validator.py", "parallel capital/integration path — authority surface"),
    ("system_interfaces.py", "parallel capital/integration path — authority surface"),
    ("trading_engine.py", "parallel capital/integration path — authority surface"),
    ("ultimate_integration.py", "parallel capital/integration path — authority surface"),
    ("ultimate_module_integrator.py", "parallel capital/integration path — authority surface"),
    ("unified_main.py", "parallel capital/integration path — authority surface"),
    ("unified_master_integrator.py", "parallel capital/integration path — authority surface"),
    ("universal_action_layer.py", "parallel capital/integration path — authority surface"),
    # --- utilities ---
    ("constants.py", "utility module — not a market analyzer"),
    ("core_types.py", "utility module — not a market analyzer"),
    ("safe_imports.py", "utility module — not a market analyzer"),
    ("system_config.py", "utility module — not a market analyzer"),
    ("unicode_fix.py", "utility module — not a market analyzer"),
    # --- test-only fixtures ---
    ("autonomous_engineer.py", "test-only fixture — no production reach"),
    ("yourtradingbot.py", "test-only fixture — no production reach"),
    # --- non-AI-named orphan dirs never imported by the canonical path
    #     (the 140 other non-manifest dirs ARE live imports — telemetry,
    #     brokers, monitoring etc. — and stay outside this manifest) ---
    ("adversarial_verification", "orphan parallel verification stack; "
     "RedTeam.analyze_strategy needs strategy source code — operates on "
     "candidates, not observations"),
    ("alpha_evolve", "alpha_evolve_regime attached; evolution/fitness "
     "remainder is an offline backtest loop, not obs-callable — "
     "deprecated RSI duplicate per AGENTS.md"),
    ("apex_fi", "apex_regime_surveillance + apex_transaction_cost "
     "attached; model parliament/execution layers need trained models "
     "and order-book depth"),
    ("cos", "DecisionSupportSystem requires cognition_store + "
     "simulation_engine ctor collaborators — not constructible "
     "standalone"),
    ("decision_governance", "dg_volatility_regime attached; governance "
     "gates/arbiters are authority surfaces, not evidence"),
    ("deepseek_engineer", "offline engineering assistant; not a runtime "
     "advisor"),
    ("deepseek_engineer_pkg_tmp", "temporary packaging dir"),
    ("events", "orphan event plumbing; canonical path uses "
     "core/unified_event_bus"),
    ("feedback", "feedback_performance attached; remaining plumbing is "
     "superseded by record_outcome/decision sink"),
    ("gets", "gets_market_structure attached; promotion/evolution "
     "remainder is authority surface"),
    ("golden_path", "orphan scripted demo path"),
    ("hivemind", "hivemind_collective + hivemind_threat_assessment "
     "attached; GovernedHivemindEngine evolution remainder is an "
     "authority surface"),
    ("master_system", "orphan parallel master orchestrator"),
    ("meta_governance", "orphan parallel governance layer"),
    ("metrics", "orphan metrics shim; canonical path uses telemetry/"),
    ("neuros_evolution", "MicrostructureExpert fabricates analysis via "
     "np.random — quarantined like aads aip_agents; remainder needs "
     "ctor collaborators (network, codebase_path)"),
    ("orchestration", "orphan parallel orchestrator"),
    ("perplexity_trading", "QuantAgent needs an AgentContext task graph; "
     "orchestrator calls the external Perplexity API — external dep"),
    ("realtime_trading_core", "orphan parallel realtime engine; "
     "canonical path is unified_bot -> CSC"),
    ("registry", "orphan registry shim; canonical path uses "
     "core/unified_registry"),
    ("services", "AAMISService delegates to a started orchestrator; "
     "IntelligenceDirectorateService.evaluate_signal needs a Signal "
     "object — no obs-dict surface"),
    ("tests", "in-repo test package, not a runtime module"),
    # --- dirs proven orphan by the Tier-1 audit (imported only by
    #     legacy_main/main_v1 or nothing at all) ---
    ("analysis", "analysis_* technical analyzers attached (18 "
     "capabilities incl. wyckoff, market_structure, mtf_intelligence, "
     "vpin, liquidity_gravity); external-data remainder (sec_13f, cot, "
     "dark_pool, options, news, sentiment, cross_asset, sector) needs "
     "feeds the bot doesn't ingest"),
    ("innovations", "fourier_price attached; chrono_arbitrage needs "
     "multi-asset/multi-timezone prices the single-symbol obs can't "
     "supply; biological/cosmic/mythological are speculative"),
    ("advanced_features", "black_swan, fractal_divergence, "
     "volatility_impulse, liquidity_holography attached (last three "
     "need scipy/sklearn, env-gated); institutional/footprint "
     "remainder needs order-flow feeds"),
    ("improvements", "pullback_detector, session_awareness, "
     "signal_enhancement_mtf attached; spread_slippage needs live "
     "collaborators; rest is offline enhancement tooling"),
    ("analytics", "alpha_decay attached; emotional/psychological "
     "trackers need trade-action history, not observations"),
    ("indicators", "iceberg_detector + adv_technical + liquidity (cvd/absorption) attached; advanced_ml remainder "
     "ships unfitted models"),
    ("market_teacher", "momentum_specialist attached; teacher/learning "
     "framework remainder is pedagogy, not market analysis"),
    ("alphaalgo_v2", "intelligence_brain_v2 attached; models/forecasting "
     "remainder overlaps the brain service"),
    # ml is live-imported canonical (confidence_calibration/
    # data_leakage_guard) - see LIVE_IMPORTED_NON_ADVISORY; the
    # ml_statistical adapter attaches its obs-callable surface.

    ("elite_system", "elite_price_action attached; equal_levels, "
     "swing_points, patterns env-gated on scipy/sklearn; LSTMPredictor "
     "and siblings need trained weights"),
    ("brain", "tier3_structure, tier2_orderflow, adaptive_integration "
     "attached (env-gated on scipy); deep-model remainder needs "
     "trained tensors"),
    ("market_intelligence", "mi_absorption, mi_manipulation, "
     "mi_wyckoff_accumulation attached; mi_market_structure, "
     "mi_time_price env-gated on sklearn/pytz; regulatory/technological "
     "remainder needs external feeds"),
    ("msos", "vendor-bias detection needs vendor/reference data feeds"),
    ("opportunity_scanner", "spread analyzer needs two symbols; "
     "observation is single-symbol"),
    ("hedge_fund_safety", "hf_model_decay attached "
     "(ModelDecayDetector fed real settled predictions via self_state); "
     "kill-switches/oversight/leverage limits are authority surfaces"),
    ("deepchart", "time_to_move + sr_memory attached (price/volume "
     "analyzers); friction/liquidity/intent engines need bid/ask or "
     "orderflow the observation cannot supply"),
    ("dashboard", "read-only UI surface"),
    ("decision_layer", "parallel decision authority — never advisory"),
    ("exit_strategies", "exit authority surface — canonical path owns "
     "exits via risk + governance"),
    ("adversarial_curriculum", "training curriculum generator, not an "
     "obs analyzer"),
    ("autonomous", "self-healing monitors analyze system metrics, not "
     "markets"),
    ("strategy", "A/B promotion framework — authority surface"),
    ("self_improvement", "code-mutation surface — RSI is canonical per "
     "AGENTS.md"),
    ("unified_architecture", "parallel architecture scaffold"),
    ("ultimate_production", "parallel production scaffold — authority "
     "surface"),
    ("orchestrator", "opportunity prediction needs opportunity objects, "
     "not observations"),
    ("upgrades", "upgrades_price_structure + upgrades_regime_divergence "
     "+ hft_orderbook_imbalance (LiquidityAnalyzer) attached; the "
     "remaining ~40 upgrade classes are portfolio/execution tooling and "
     "status facades - unverified members stay unwired"),
    ("institutional_entry", "institutional_entry_footprint attached "
     "(AbsorptionDetector + InstitutionalFootprint + WyckoffICTFusion); "
     "EntrySignalGenerator needs upstream EntryTrigger objects that the "
     "observation channel never produces"),
    ("analysis_unified", "analysis_unified_analyzer attached"),
    ("advanced_analysis", "hypernetwork_regime + marl_strategists + "
     "tda_topology + ricci_momentum + fractal_momentum_div attached; "
     "ConsensusDecision/learning machinery is decision-layer plumbing; "
     "hawkes_event_intensity attached (bars->event stream); "
     "lob_cnn/options_hedging need orderflow/options flow the "
     "observation cannot supply"),
    ("realtime", "realtime_ensemble attached (online models, evidence "
     "only); RealTimeMLEngine's deployment loop is not wired"),
    ("research", "feature_discovery + quant_regime_microstructure "
     "attached; pipeline orchestration is research-time, not runtime"),
    ("skills", "concept_drift + counterfactual_outcomes attached "
     "(fed real settled action/outcome pairs via self_state); RL "
     "trainer remainder is offline tooling"),
    ("profit_maximizer", "profit_max_market_regime + confluence_session "
     "attached; position-management remainder is a sizing/authority "
     "surface"),
    ("ultimate_system", "deep_agent_market attached; "
     "AlphaDiscoveryEngine.get_signals emits np.random noise (stub) - "
     "never wire a generator that fabricates evidence"),
    ("psychology", "psychology_bias_tilt attached (fed the real "
     "settled-outcome journal via self_state); EmotionalStateTracker "
     "needs a live emotional-state feed the controller doesn't "
     "produce"),
    ("position", "position_state_monitor attached "
     "(CorrelationExposure + PositionAging on real CSC open positions "
     "via self_state); sizing/pyramid/scale-out tools are authority "
     "surfaces"),
    ("hft", "hft_orderbook_imbalance attached (conditional - only emits "
     "when the observation carries a real order book); feed handlers "
     "are broker plumbing"),
    ("hedge_fund", "MultiStrategyEngine starts with an empty strategy "
     "registry - no live registration path exists, so it would emit "
     "vacuous evidence"),
    ("unified_system", "layer4/layer5 impls are literal stubs "
     "(constant predictions, empty signal lists) - orchestrator is a "
     "parallel pipeline regardless"),
    ("production", "parallel production strategy lane - Signal objects "
     "carry entry/stop/sizing; authority-adjacent and requires "
     "StrategyConfig plumbing the obs channel lacks"),
)


_DISCOVERY_METHODS = ("analyze", "detect", "classify", "predict",
                      "assess", "estimate", "evaluate")
_DISCOVERY_TIMEOUT_S = 0.5
_DISCOVERY_CAP = 40
# Confirmed live-failures: classes that pass the synthetic probe but
# crash on real observations (type errors on string/sequence fields).
# Circuit breaker already silences them in-session; skip attaching.
_DISCOVERY_BLOCKLIST = frozenset({
    "DataAgent",   # cognitive_architecture layer3: '<' on str vs float
})


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
    # Realistic context: real observations carry string/sequence fields
    # alongside numerics — advisors that assume all-numeric inputs must
    # fail here, not mid-pipeline.
    probe_ctx = {
        "symbol": "EURUSD", "price": 1.09, "close": 1.09,
        "volatility": 0.01, "trend": "FLAT", "trend_strength": 0.1,
        "sentiment": 0.0, "momentum": 0.0, "timeframe": "M15",
        "timestamp": "2026-01-01T00:00:00", "volume_ratio": 1.0,
        "raw_market_data": {"note": "nested"}, "key_levels": [],
    }

    async def _probe(svc):
        res = svc.analyze(probe_ctx)
        if _inspect.isawaitable(res):
            res = await asyncio.wait_for(res, _DISCOVERY_TIMEOUT_S)
        return res

    def _probe_sync(svc) -> None:
        _run_coro_sync(_probe(svc))

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
                if cls.__name__ in _DISCOVERY_BLOCKLIST:
                    skipped.append(f"discovered:{cls.__name__}(blocklisted)")
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

    ``TB_MEASURED_ADVISORS=1`` restricts the set to services measured
    substantive on real bars (``advisor_degeneracy_report.py``) - the
    degenerate tail consumes the cycle budget without producing evidence;
    orphan discovery is disabled in measured mode.
    """
    import asyncio
    import os

    measured_only = os.environ.get("TB_MEASURED_ADVISORS", "") == "1"
    selected = factories or DEFAULT_ADVISORY_FACTORIES
    if measured_only:
        selected = tuple(f for f in selected
                         if f[0] in MEASURED_ACTIVE_SET)
        logger.info("advisory attach: measured-only mode - %d/%d "
                    "services selected", len(selected),
                    len(DEFAULT_ADVISORY_FACTORIES))

    attached: List[str] = []
    skipped: List[str] = []
    for capability_id, factory in selected:
        try:
            service = factory()
            if probe:
                probe_ctx = {
                    "symbol": "EURUSD", "price": 1.09, "close": 1.09,
                    "volatility": 0.01, "trend": "FLAT", "sentiment": 0.0,
                }
                result = service.analyze(probe_ctx)
                if inspect.isawaitable(result):
                    _run_coro_sync(result)
            csc.configure_cognition(service)
            attached.append(capability_id)
            logger.info("advisory module attached: %s", capability_id)
        except Exception as exc:
            skipped.append(capability_id)
            logger.warning("advisory module skipped: %s (%s)",
                           capability_id, exc)

    if discover and not measured_only:
        # Only package names — root .py manifest entries resolve to dead
        # stubs or side-effect modules (installers, stdout patchers) that
        # must never be imported by discovery.
        orphan_pkgs = tuple(
            name.split("(")[0]
            for name, _ in UNWIRED_ORPHAN_MODULES
            if not name.endswith(".py"))
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

    csc._advisory_attach_report = {
        "attached": list(attached),
        "skipped": list(skipped),
        "discover": bool(discover),
    }
    return attached, skipped

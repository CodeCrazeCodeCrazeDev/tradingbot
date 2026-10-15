"""Trading-knowledge curriculum — books, traders, institutional practice
distilled into testable candidate specs for the model-engineering gate.

The architecture stays honest: a lesson from a book is a *hypothesis*,
not authority. Every entry is expressed only in derivable features —
specs that need sentiment, order book, or macro data we don't have are
excluded by construction, not trusted. Each lesson must survive the same
gate as generated alpha: OOS holdout, bootstrap significance, FDR
control, human approval, trust-ramp attach.

Sources are attributed in provenance so the audit trail says WHERE a
candidate's idea came from.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Each entry: name, source, lesson, spec (model-engineering spec).
# Specs only use DERIVABLE_FEATURES / the alpha grammar — real data only.
TRADING_CURRICULUM: List[Dict[str, Any]] = [
    # --- Trend following (Turtle/Covel, Jegadeesh momentum) ---
    {"name": "turtle_breakout_20", "source": "Covel — Trend Following / Turtle rules",
     "lesson": "Buy 20-period highs; trend persists past breakout",
     "mechanism": "breakout triggers stop-runs and trend-following flow",
     "data_required": "OHLCV bars; faithful rank-over-20-bars window",
     "disprover": "post-breakout forward return <= 0 net of costs OOS",
     "spec": {"kind": "ga_expression",
              "expression": "ts_rank(close, 20)"}},
    {"name": "momentum_10bar", "source": "Jegadeesh & Titman — momentum",
     "lesson": "Positive 10-bar momentum continues",
     "mechanism": "underreaction: order flow persistence past 10 bars",
     "data_required": "close series; derivable momentum feature",
     "disprover": "momentum>0 trades show <=0 mean net bps OOS",
     "spec": {"kind": "threshold_rule", "feature": "momentum", "op": ">",
              "direction": "BUY"}},
    {"name": "trend_strength_up", "source": "Turtle/Covel — only trade strong trends",
     "lesson": "Strong trend regime + up-trend → long",
     "mechanism": "regime persistence: strong trends continue",
     "data_required": "derivable trend regime feature",
     "disprover": "BULLISH-regime longs show <=0 mean net bps OOS",
     "spec": {"kind": "threshold_rule", "feature": "trend", "equals": "BULLISH",
              "direction": "BUY"}},
    # --- Mean reversion (Connors RSI-2, Bollinger reversion) ---
    {"name": "rsi_oversold_revert", "source": "Connors — RSI(2) mean reversion",
     "lesson": "Deep oversold RSI reverts upward short-term",
     "mechanism": "short-horizon liquidity provision: oversold fades",
     "data_required": "derivable RSI feature (RSI-2 approx via rsi)",
     "disprover": "low-RSI buys show <=0 mean net bps OOS",
     "spec": {"kind": "threshold_rule", "feature": "rsi", "op": "<",
              "direction": "BUY"}},
    {"name": "zscore_reversion", "source": "Bollinger/stat-arb — price reverts to mean",
     "lesson": "Extreme negative z-score → bounce",
     "mechanism": "deviation from local mean attracts reversion flow",
     "data_required": "returns series for rolling z-score",
     "disprover": "extreme-zscore entries show <=0 mean net bps OOS",
     "spec": {"kind": "ga_expression",
              "expression": "zscore(returns)"}},
    {"name": "down_move_fade", "source": "Trader lore — fade sharp single-bar drops",
     "lesson": "Immediate strong negative bar reverts next bar",
     "mechanism": "one-bar overreaction corrects on the next bar",
     "data_required": "per-bar delta of close",
     "disprover": "post-drop bars show <=0 mean net bps OOS",
     "spec": {"kind": "ga_expression", "expression": "delta(close)"}},
    # --- Volatility regime (ATR expansion → continuation) ---
    {"name": "vol_expansion_trend", "source": "ATR doctrine — volatility expansion = trend birth",
     "lesson": "High volatility + bullish trend → continuation",
     "mechanism": "vol expansion marks regime transitions to trends",
     "data_required": "volatility, momentum, trend_strength features",
     "disprover": "high-vol longs show <=0 mean net bps OOS",
     "spec": {"kind": "logistic",
              "features": ["volatility", "momentum", "trend_strength"]}},
    {"name": "low_vol_skip", "source": "Institutional risk desks — don't trade dead vol",
     "lesson": "Low volatility predicts no edge — abstention evidence",
     "mechanism": "dead-vol regimes lack the flow that creates edge",
     "data_required": "volatility feature",
     "disprover": "low-vol trades match or beat high-vol trades OOS",
     "spec": {"kind": "threshold_rule", "feature": "volatility", "op": ">",
              "direction": "SELL"}},
    # --- Volume (OBV doctrine, institutional footprint) ---
    {"name": "volume_confirms_move", "source": "Granville OBV — volume precedes price",
     "lesson": "Rising volume + up move = real demand",
     "mechanism": "participation validates the price move",
     "data_required": "volume_ratio + momentum features",
     "disprover": "high-volume-ratio longs show <=0 net bps OOS",
     "spec": {"kind": "logistic",
              "features": ["volume_ratio", "momentum"]}},
    {"name": "vol_price_corr", "source": "Wyckoff — effort vs result",
     "lesson": "volume×price co-movement signals accumulation",
     "mechanism": "institutional accumulation prints effort/result correlation",
     "data_required": "volume + returns series, 20-bar correlation window",
     "disprover": "corr-conditioned trades show <=0 net bps OOS",
     "spec": {"kind": "ga_expression",
              "expression": "correlation(volume, returns, 20)"}},
    # --- Range/wick rejection (price-action lore) ---
    {"name": "range_compression_break", "source": "Squeeze doctrine — compression precedes expansion",
     "lesson": "Low range volatility resolves into a directional break",
     "mechanism": "volatility clustering: compression stores energy",
     "data_required": "returns series, 20-bar std window",
     "disprover": "post-compression moves show no directional edge OOS",
     "spec": {"kind": "ga_expression",
              "expression": "ts_std(returns, 20)"}},
    # --- Multi-timeframe (Elder triple screen) ---
    {"name": "htf_alignment", "source": "Elder — trade with the higher timeframe",
     "lesson": "M15 longs only when H1 trend is bullish",
     "mechanism": "higher-timeframe flow dominates lower-TF noise",
     "data_required": "htf_trend + trend + momentum features",
     "disprover": "aligned-TF longs show <=0 net bps OOS",
     "spec": {"kind": "logistic",
              "features": ["momentum", "htf_trend", "trend"]}},
    # --- Crowd/disagreement (contrarian signal) ---
    {"name": "disagreement_fade", "source": "Contrarian doctrine — consensus is late",
     "lesson": "High advisory disagreement marks turning points",
     "mechanism": "crowd conviction peaks near inflections",
     "data_required": "advisory_disagreement + momentum features",
     "disprover": "high-disagreement fades show <=0 net bps OOS",
     "spec": {"kind": "logistic",
              "features": ["advisory_disagreement", "momentum"]}},
    # --- Peer/cross-market (pairs/sector lore) ---
    {"name": "peer_confirmation", "source": "Institutional cross-asset desks",
     "lesson": "Correlated peer confirms the move",
     "mechanism": "correlated instruments share order-flow drivers",
     "data_required": "peer_return feature (synchronized second symbol)",
     "disprover": "peer-confirmed trades show <=0 net bps OOS",
     "spec": {"kind": "logistic",
              "features": ["peer_return", "momentum"]}},
    # --- Regime-conditional (Mandelbrot persistence) ---
    {"name": "regime_up_buy", "source": "Regime doctrine — UP regime → buy dips",
     "lesson": "Long in UP regimes, mean-revert there",
     "mechanism": "regime autocorrelation: UP regimes persist",
     "data_required": "derivable regime feature",
     "disprover": "UP-regime longs show <=0 net bps OOS",
     "spec": {"kind": "threshold_rule", "feature": "regime", "equals": "UP",
              "direction": "BUY"}},
    {"name": "regime_down_sell", "source": "Regime doctrine — DOWN regime → sell rallies",
     "lesson": "Short in DOWN regimes",
     "mechanism": "regime autocorrelation: DOWN regimes persist",
     "data_required": "derivable regime feature",
     "disprover": "DOWN-regime shorts show <=0 net bps OOS",
     "spec": {"kind": "threshold_rule", "feature": "regime", "equals": "DOWN",
              "direction": "SELL"}},
    # --- Livermore pivotal points (recover after pullback) ---
    {"name": "pullback_resume", "source": "Livermore — pivotal points resume trend",
     "lesson": "Pullback in uptrend → resume",
     "mechanism": "trend resumes after healthy retracement",
     "data_required": "returns series, 10-bar rank window",
     "disprover": "pullback-resume entries show <=0 net bps OOS",
     "spec": {"kind": "ga_expression",
              "expression": "ts_rank(returns, 10)"}},
    # --- Institutional calendar ---
    {"name": "trend_up_inst", "source": "Institutional flow windows",
     "lesson": "Month-end/quarter-end flow distorts — reduced-conviction trades",
     "mechanism": "rebalancing flow creates non-fundamental price pressure",
     "data_required": "trend_strength + volume_ratio features",
     "disprover": "flow-window trades show <=0 net bps OOS",
     "spec": {"kind": "logistic",
              "features": ["trend_strength", "volume_ratio"]}},
    # --- Composite multi-feature learned specs ---
    {"name": "classic_trend_composite", "source": "Composite — trend + momentum + vol",
     "lesson": "Aligned trend, momentum and volatility outperform",
     "mechanism": "joint signal alignment filters noise",
     "data_required": "4 derivable features; logistic fit",
     "disprover": "composite-signal trades show <=0 net bps OOS",
     "spec": {"kind": "logistic",
              "features": ["momentum", "trend_strength", "volatility",
                           "volume_ratio"]}},
    {"name": "calm_reversion_composite", "source": "Composite — calm markets revert",
     "lesson": "Low vol + flat trend → fade extremes",
     "mechanism": "calm regimes lack flow to sustain breakouts",
     "data_required": "volatility + momentum + rsi features",
     "disprover": "calm-regime fades show <=0 net bps OOS",
     "spec": {"kind": "logistic",
              "features": ["volatility", "momentum", "rsi"]}},
]


async def learn_from_curriculum(
    csc: Any,
    bars: List[Dict[str, Any]],
    limit: int = 0,
) -> Dict[str, Any]:
    """Run the whole curriculum through the gated pipeline: propose every
    lesson, batch-validate with FDR control, return the survivors for
    human review. Nothing attaches — approval stays human."""
    from .model_engineering import validate_alpha_generation
    proposed: List[str] = []
    for entry in TRADING_CURRICULUM[:limit or len(TRADING_CURRICULUM)]:
        spec = dict(entry["spec"])
        spec["name"] = entry["name"]
        # Full provenance rides the spec — the audit trail keeps WHERE
        # the idea came from, the claimed mechanism, what data it needs,
        # and what observation would disprove it.
        spec["provenance"] = {
            "source": entry.get("source"),
            "lesson": entry.get("lesson"),
            "mechanism": entry.get("mechanism"),
            "data_required": entry.get("data_required"),
            "disprover": entry.get("disprover"),
        }
        r = await csc.propose_model(
            spec, proposed_by=f"curriculum:{entry['source']}")
        if r.get("status") == "proposed":
            proposed.append(r["candidate_id"])
    verdict = await validate_alpha_generation(csc, proposed, bars)
    survivors = [x["candidate_id"] for x in verdict["candidates"]
                 if x.get("fdr_survived")]
    return {"proposed": len(proposed), "validated": verdict["validated"],
            "survivors": survivors, "candidates": verdict["candidates"],
            "note": "survivors await operator_cli approve-model — the "
                    "gate decided; the human decides whether to adopt"}

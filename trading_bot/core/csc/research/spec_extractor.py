"""Distillate -> MethodSpec extraction (M1 component a).

Mechanical, bounded, honest: maps free text (scout descriptions,
paper abstracts, operator notes) onto the allow-listed parametric
families in method_spec.FAMILIES. It NEVER invents a family — text
that matches no template yields no spec. Numeric hints are extracted
only when explicitly stated ("20-period", "z-score 2", "1.5%");
anything outside declared bounds is clamped to the bound and the
clamp is recorded in provenance, never silently applied.

This is the constrained-template-DSL half of the doc's extraction
options — no model call, works in .venv, deterministic. An LLM
extractor can sit upstream later and emit the same MethodSpec dicts;
this module is the floor, not the ceiling.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .method_spec import FAMILIES, MethodSpec, spec_from_dict

# keyword -> (family, param hints). Order matters: first match wins
# per family block; a text can emit at most one spec per family.
_TEMPLATES = [
    ("stat_arb",
     ("pairs trading", "pairs trade", "cointegration", "co-integrated",
      "spread trading", "statistical arbitrage", "stat arb",
      "pairs arbitrage")),
    ("vol_regime_momentum",
     ("volatility regime", "vol expansion", "volatility expansion",
      "realized vol", "vol ratio", "volatility contraction",
      "regime-switching momentum")),
    ("funding_fade",
     ("funding rate", "funding carry", "perp funding",
      "perpetual funding", "funding yield", "funding arbitrage",
      "funding fade")),
    ("meanrev",
     ("mean reversion", "mean-reversion", "oversold", "overbought",
      "bollinger", "z-score", "z score", "revert to the mean",
      "range-bound", "rsi fade", "counter-trend")),
    ("donchian",
     ("breakout", "donchian", "channel breakout", "new high",
      "new low", "turtle", "range expansion")),
    ("momentum",
     ("momentum", "trend following", "trend-following", "trend",
      "time series momentum", "tsmom", "carry")),
]

# "20-period" / "20 day" / "20-bar" -> int hint for lookback-ish params
_PERIOD_RE = re.compile(
    r"(\d{1,3})\s*[- ]?(?:period|day|bar|week)s?", re.I)
# "z-score of 2" / "2 sigma" / "1.5%" style magnitude hints
_Z_RE = re.compile(r"(?:z[- ]?score|sigma)[^0-9]{0,10}(\d+(?:\.\d+)?)",
                   re.I)
_PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def _clamp_to_bounds(family: str, params: Dict[str, float],
                     provenance: Dict[str, Any]) -> Dict[str, float]:
    """Clamp hinted params into declared bounds; record every clamp."""
    bounds = FAMILIES[family]["bounds"]
    out = {}
    for k, v in params.items():
        if k not in bounds:
            continue
        lo, hi = bounds[k]
        cv = float(v)
        if cv < lo or cv > hi:
            provenance.setdefault("param_clamps", {})[k] = {
                "requested": cv, "clamped_to": [lo, hi]}
            cv = min(max(cv, lo), hi)
        out[k] = cv
    return out


def _hint_params(family: str, text: str) -> Dict[str, float]:
    """Pull numeric hints from text, mapped onto the family's params."""
    hints: Dict[str, float] = {}
    periods = [int(m) for m in _PERIOD_RE.findall(text)]
    if family == "momentum":
        if periods:
            hints["lookback"] = float(periods[0])
        pcts = [float(m) for m in _PCT_RE.findall(text)]
        if pcts:
            hints["threshold_bps"] = pcts[0] * 100.0  # % -> bps
    elif family == "meanrev":
        if periods:
            hints["window"] = float(periods[0])
        zs = [float(m) for m in _Z_RE.findall(text)]
        if zs:
            hints["z"] = zs[0]
    elif family == "donchian":
        if periods:
            hints["channel"] = float(periods[0])
    elif family == "stat_arb":
        if periods:
            hints["window"] = float(periods[0])
        zs = [float(m) for m in _Z_RE.findall(text)]
        if zs:
            hints["z"] = zs[0]
        # hedge ratio is NOT guessed from text — it stays at the
        # declared default unless the spec is hand-authored
    elif family == "vol_regime_momentum":
        if len(periods) >= 2:
            hints["vol_short"], hints["vol_long"] = \
                float(min(periods[:2])), float(max(periods[:2]))
        elif periods:
            hints["vol_long"] = float(periods[0])
        zs = [float(m) for m in _Z_RE.findall(text)]
        if zs:
            hints["vr_min"] = 1.0 + min(zs[0], 2.0)
    return hints


# Context gate. An ANCHOR term is required before template matching:
# either an unambiguous market/instrument reference (stocks, forex,
# futures, treasury, VIX, FOMC, ...) or a finance-specific method
# term (bollinger, donchian, z-score, cointegration, "volatility
# regime", ...). Domain-shared words — "momentum", "trend",
# "volatility", "breakout", "reversion", "regime", "forecast",
# "price", "return", "volume", "spread" — do NOT admit text alone:
# they appear throughout physics, climate, software, and medicine
# writing. Observed live failures this gate prevents: a Minecraft
# crash log ("Ticking entity") and a climate abstract ("atmospheric
# momentum and volatility of storm systems") both emitted specs
# under the old permissive regex.
_ANCHOR_RE = re.compile(
    r"\b(?:prices?|markets?|trading|trades?|stocks?|forex|fx|"
    r"crypto\w*|bitcoin|assets?|equity|equities|bonds?|futures?|"
    r"options?|portfolio|invest\w*|financial|financing|currency|"
    r"currencies|hedg\w+|swaps?|treasur\w+|yield curve|vix|fomc|"
    r"cpi|nfp|pce|risk premium|cross[- ]?sectional|term structure|"
    r"order flow|limit orders?|open interest|funding rate|"
    r"basis trade|pairs trading|mean[- ]?reversion|lookback|"
    r"backtest\w*|sharpe|sortino|drawdown|contango|backwardation|"
    r"bollinger|donchian|z[- ]?score|stochastic|rsi|ema|sma|adx|"
    r"macd|candlestick|ichimoku|elliott|wyckoff|cointegration|"
    r"co[- ]?integration|arbitrage|volatility regime|vol regime|"
    r"volatility expansion|volatility contraction|vol expansion|"
    r"realized vol\w*|vol ratio|regime[- ]?switching momentum|"
    r"eurodollar|sofr)\b", re.I)

# Document-type denylist: crash logs, recipes, and similar are never
# tradeable claims even if an anchor term appears incidentally.
_NON_MARKET_RE = re.compile(
    r"crash report|stack ?trace|heap space|outofmemory|"
    r"null ?pointer|segmentation fault|kernel panic|minecraft|"
    r"sourdough", re.I)


def _has_finance_context(text: str) -> bool:
    return bool(_ANCHOR_RE.search(text)) \
        and not _NON_MARKET_RE.search(text)


def extract_specs(text: str, *, provenance: Optional[Dict[str, Any]] = None,
                  spec_prefix: str = "ext") -> List[MethodSpec]:
    """Map free text onto allow-listed families -> MethodSpecs.

    Returns [] when nothing matches — honest empty, never a
    fabricated spec. At most one spec per matched family; families
    are tried in template order (most specific first). Text without
    ANY finance-market vocabulary emits nothing: "momentum" in a
    climate or physics abstract is not a tradeable claim, and the
    eval budget is better spent on plausible candidates.
    """
    if not text or not _has_finance_context(text):
        return []
    low = text.lower()
    prov = dict(provenance or {})
    specs: List[MethodSpec] = []
    emitted = set()
    for fam, keywords in _TEMPLATES:
        if fam in emitted:
            continue
        if not any(kw in low for kw in keywords):
            continue
        params = _clamp_to_bounds(
            fam, _hint_params(fam, text), prov)
        slug = re.sub(r"[^a-z0-9]+", "_", fam)[:24]
        spec = spec_from_dict({
            "spec_id": f"{spec_prefix}_{slug}_{len(specs)}",
            "hypothesis": text.strip()[:200],
            "family": fam,
            "params": params,
            "provenance": {**prov, "extracted_by": "spec_extractor",
                           "matched_family": fam},
            "falsification": "rejected if any eval segment LCB5 <= 0 "
                             "or mean net <= 0 under declared cost",
            "required_data": FAMILIES[fam].get("data", "close"),
        })
        specs.append(spec)
        emitted.add(fam)
    return specs

"""CSC-owned model engineering surface.

The AI may engineer models; it may not grant them authority. Every
engineered candidate must pass through a fixed lifecycle:

    PROPOSED -> VALIDATING -> VALIDATED | REJECTED
             -> APPROVED (human operator writes the durable control flag)
             -> ATTACHED (advisory-only: votes flow through the same
                trust ramp, regime eligibility and reliability weighting
                as every other advisor)

The objective that decides VALIDATED vs REJECTED is out-of-sample net
expectancy after the cost model — not accuracy. A candidate that is
"right" half the time but loses money to spread is rejected. A candidate
that wins money only on the training slice is rejected: parameters are
fit on the first 70% of the window and scored on the held-out remainder.

Nothing here can create execution authority. The attach path produces an
AdvisoryModuleAdapter whose only output surface is direction/evidence —
risk, governance, shield and the execution service are untouched.
"""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

import numpy as np

ALLOWED_KINDS = ("threshold_rule", "logistic")
# Features derivable honestly from bar history — the enriched obs set
# plus raw fields. Anything else is not a valid engineered input.
DERIVABLE_FEATURES = {
    "close", "open", "high", "low", "volume", "price",
    "volatility", "trend", "rsi", "rsi14", "momentum",
    "trend_strength", "regime", "volume_ratio",
    "htf_close", "htf_trend", "htf_rsi14",
    "peer_close", "peer_return", "peer_corr", "bid", "ask",
    "spread_bps",
}
_DIRECTION_NUM = {"BUY": 1.0, "SELL": -1.0}

# Cost model matching the paper runner's measured frictions.
COST_BPS = 3.25
HOLDOUT_FRACTION = 0.30
MIN_HOLDOUT_SIGNALS = 10
MIN_EXPECTANCY_BPS = 0.0


@dataclass
class ModelCandidate:
    candidate_id: str
    name: str
    spec: Dict[str, Any]
    proposed_by: str
    status: str = "PROPOSED"
    created_at: float = field(default_factory=time.time)
    fitted_params: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    verdict: Optional[str] = None


def _forward_return(obs_window: List[Dict[str, Any]], i: int,
                    horizon: int = 8) -> Optional[float]:
    """Realized direction payoff: close[i+horizon]/close[i] - 1, costed."""
    if i + horizon >= len(obs_window):
        return None
    a = obs_window[i].get("close") or obs_window[i].get("price")
    b = obs_window[i + horizon].get("close") or obs_window[i + horizon].get(
        "price")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) \
            or a <= 0:
        return None
    return (b - a) / a


def _predict_threshold(obs: Mapping[str, Any], params: Dict[str, Any]
                       ) -> Optional[str]:
    feat = params.get("feature")
    val = obs.get(feat)
    if isinstance(val, str) and feat in ("trend", "regime", "htf_trend"):
        target = params.get("equals")
        if target is not None:
            return params["direction"] if val == target else None
    if not isinstance(val, (int, float)):
        return None
    thr = float(params["threshold"])
    op = params.get("op", ">")
    hit = val > thr if op == ">" else val < thr
    return params["direction"] if hit else None


def _fit_threshold(train: List[Dict[str, Any]], feature: str,
                   direction: str) -> Optional[Dict[str, Any]]:
    """Sweep the in-sample quantiles of `feature`; keep the threshold with
    the best in-sample net expectancy. Returns None if nothing qualifies —
    validation decides honestly on the holdout regardless."""
    vals = [o.get(feature) for o in train]
    vals = [v for v in vals if isinstance(v, (int, float))]
    if len(vals) < 30:
        return None
    qs = np.quantile(np.asarray(vals, dtype=float),
                     [0.6, 0.7, 0.8, 0.9, 0.95])
    best = None
    for op in (">", "<"):
        for q in qs:
            hits = 0
            ret = 0.0
            for i, o in enumerate(train):
                r = _forward_return(train, i)
                if r is None:
                    continue
                pred = _predict_threshold(
                    o, {"feature": feature, "op": op, "threshold": float(q),
                        "direction": direction})
                if pred is None:
                    continue
                hits += 1
                ret += (r if direction == "BUY" else -r) - COST_BPS * 1e-4
            if hits >= MIN_HOLDOUT_SIGNALS and (best is None or ret > best[1]):
                best = (float(q), ret, hits, op)
    if best is None:
        return None
    return {"feature": feature, "op": best[3], "threshold": best[0],
            "direction": direction,
            "insample_net_return": best[1], "insample_n": best[2]}


def _fit_logistic(train: List[Dict[str, Any]], features: List[str],
                  horizon: int = 8) -> Optional[Dict[str, Any]]:
    """sklearn logistic regression on the derived feature vector; labels are
    forward-return sign. Honest fail if sklearn is absent."""
    try:
        from sklearn.linear_model import LogisticRegression
    except ImportError:
        return None
    X, y = [], []
    for i, o in enumerate(train):
        r = _forward_return(train, i, horizon)
        row = [o.get(f) for f in features]
        if r is None or any(not isinstance(v, (int, float)) for v in row):
            continue
        X.append(row)
        y.append(1 if r > 0 else -1)
    if len(X) < 40 or len(set(y)) < 2:
        return None
    model = LogisticRegression(max_iter=500)
    model.fit(np.asarray(X, dtype=float), np.asarray(y))
    return {"features": list(features),
            "coef": model.coef_[0].tolist(),
            "intercept": float(model.intercept_[0])}


def _predict_logistic(obs: Mapping[str, Any], params: Dict[str, Any]
                      ) -> Optional[tuple]:
    row = [obs.get(f) for f in params["features"]]
    if any(not isinstance(v, (int, float)) for v in row):
        return None
    x = np.asarray(row, dtype=float)
    coef = np.asarray(params["coef"], dtype=float)
    z = float(x @ coef + params["intercept"])
    p = 1.0 / (1.0 + math.exp(-z))
    if p > 0.55:
        return ("BUY", float(p))
    if p < 0.45:
        return ("SELL", float(1 - p))
    return None


def evaluate_holdout(spec: Dict[str, Any], params: Dict[str, Any],
                     holdout: List[Dict[str, Any]],
                     horizon: int = 8) -> Dict[str, Any]:
    """Score a fitted candidate on bars it never saw. Objective is net
    expectancy after the cost model — accuracy alone is not success."""
    n_calls = wins = 0
    ret = 0.0
    for i, o in enumerate(holdout):
        r = _forward_return(holdout, i, horizon)
        if r is None:
            continue
        if spec["kind"] == "threshold_rule":
            pred = _predict_threshold(o, params)
            conf = 0.6
        else:
            pred = _predict_logistic(o, params)
            conf = pred[1] if pred else 0.5
            pred = pred[0] if pred else None
        if pred is None:
            continue
        n_calls += 1
        signed = r if pred == "BUY" else -r
        net = signed - COST_BPS * 1e-4
        ret += net
        if signed > 0:
            wins += 1
    return {
        "holdout_signals": n_calls,
        "accuracy": (wins / n_calls) if n_calls else None,
        "net_return": ret,
        "mean_net_bps": (ret / n_calls * 1e4) if n_calls else None,
        "horizon": horizon,
    }


def fit_candidate(spec: Dict[str, Any], train: List[Dict[str, Any]]
                  ) -> Optional[Dict[str, Any]]:
    if spec["kind"] == "threshold_rule":
        return _fit_threshold(train, spec["feature"], spec["direction"])
    if spec["kind"] == "logistic":
        return _fit_logistic(train, list(spec["features"]))
    return None


def validate_spec(spec: Mapping[str, Any]) -> List[str]:
    """Fail fast on specs that can't be honestly engineered or evaluated."""
    errs: List[str] = []
    kind = spec.get("kind")
    if kind not in ALLOWED_KINDS:
        errs.append(f"kind must be one of {ALLOWED_KINDS}")
        return errs
    if kind == "threshold_rule":
        feat = spec.get("feature")
        if feat not in DERIVABLE_FEATURES:
            errs.append(f"feature {feat!r} is not derivable from real data")
        if spec.get("direction") not in ("BUY", "SELL"):
            errs.append("direction must be BUY or SELL")
        if spec.get("op", ">") not in (">", "<") and feat not in (
                "trend", "regime", "htf_trend"):
            errs.append("numeric features need op > or <")
        if feat in ("trend", "regime", "htf_trend") and \
                spec.get("equals") is None:
            errs.append("categorical feature needs 'equals'")
    if kind == "logistic":
        feats = spec.get("features") or []
        if not feats or any(f not in DERIVABLE_FEATURES for f in feats):
            errs.append("logistic needs 1+ derivable features")
        if len(feats) > 8:
            errs.append("logistic limited to 8 features")
    return errs


def candidate_adapter(candidate: ModelCandidate) -> Any:
    """Wrap an approved candidate as an advisory-only service. It votes
    like every other advisor — trust ramp, regime eligibility and
    measured reliability weighting all apply from day one."""
    from trading_bot.core.csc.advisory import AdvisoryModuleAdapter

    spec = dict(candidate.spec)
    params = dict(candidate.fitted_params)
    horizon = 8

    async def analyze(ctx: Mapping[str, Any]) -> Dict[str, Any]:
        if spec["kind"] == "threshold_rule":
            direction = _predict_threshold(ctx, params)
            confidence = 0.6
        else:
            pred = _predict_logistic(ctx, params)
            direction = pred[0] if pred else None
            confidence = pred[1] if pred else None
        evidence: Dict[str, Any] = {
            "status": "ok" if direction else "no_signal",
            "engineered_model": candidate.name,
            "validation": candidate.validation,
        }
        return {"capability_id": f"engineered:{candidate.name}",
                "direction": direction, "confidence": confidence,
                "evidence": evidence, "advisory_only": True}

    return AdvisoryModuleAdapter(f"engineered:{candidate.name}", analyze)

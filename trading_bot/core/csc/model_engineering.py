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

ALLOWED_KINDS = ("threshold_rule", "logistic", "ga_expression")

# --- alpha-grammar evaluator (subset of apex_fi GeneticAlphaSearch's
# vocabulary, evaluated over rolling obs series — the bridge between the
# quarantined generator and the gated candidate pipeline) ---
GA_FIELDS = ("close", "volume", "high", "low", "vwap", "returns",
             "log_returns", "volatility")


def _expr_series(series: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Derived fields the grammar expects, from raw obs series."""
    out = dict(series)
    c = out.get("close")
    h, l, v = out.get("high"), out.get("low"), out.get("volume")
    if c is not None:
        out["returns"] = np.diff(c, prepend=c[0]) / np.where(c == 0, 1, c)
        with np.errstate(divide="ignore", invalid="ignore"):
            out["log_returns"] = np.diff(
                np.log(np.where(c > 0, c, np.nan)), prepend=np.nan)
        if h is not None and l is not None:
            out["vwap"] = (h + l + c) / 3.0
        if len(c) >= 10:
            out["volatility"] = np.array([
                float(np.std(out["returns"][max(0, i - 9):i + 1]))
                for i in range(len(c))])
    return out


def _parse_expr(expr: str):
    """Tiny recursive parser for the alpha grammar: op(...) chains or a
    bare field name. Returns nested tuples: ('op', arg...) | ('field', n)."""
    expr = expr.strip()
    if expr in GA_FIELDS:
        return ("field", expr)
    if "(" not in expr:
        return ("field", expr)
    op, rest = expr.split("(", 1)
    inner = rest.rsplit(")", 1)[0]
    args, depth, cur = [], 0, ""
    for ch in inner:
        if ch == "," and depth == 0:
            args.append(cur.strip()); cur = ""; continue
        depth += (ch == "(") - (ch == ")")
        cur += ch
    if cur.strip():
        args.append(cur.strip())
    parsed = [a if a.lstrip("-").replace(".", "", 1).isdigit()
              else _parse_expr(a) for a in args]
    return (op.strip(), *parsed)


def _eval_expr(ast, series: Dict[str, np.ndarray]) -> np.ndarray:
    """Evaluate the expression AST elementwise over the series dict.
    Unknown ops/fields produce NaN arrays — honest failure, not zeros."""
    n = len(next(iter(series.values()))) if series else 1
    if isinstance(ast, float) or isinstance(ast, int) or (
            isinstance(ast, str) and ast.lstrip("-").replace(
                ".", "", 1).isdigit()):
        return np.full(n, float(ast))
    tag = ast[0]
    if tag == "field":
        return np.asarray(series.get(ast[1], np.full(n, np.nan)),
                          dtype=float)
    args = [_eval_expr(a, series) for a in ast[1:]
            if not (isinstance(a, str) and a.lstrip("-").replace(
                ".", "", 1).isdigit())]
    nums = [float(a) for a in ast[1:]
            if isinstance(a, (int, float)) or (isinstance(a, str)
                and a.lstrip("-").replace(".", "", 1).isdigit())]
    w = int(nums[0]) if nums else 10
    x = args[0]
    nan = np.full(n, np.nan)
    try:
        if tag == "delta":
            d = np.diff(x, prepend=np.nan)
            return d
        if tag == "zscore":
            mu, sd = np.nanmean(x), np.nanstd(x)
            return (x - mu) / sd if sd > 0 else nan
        if tag == "rank":
            valid = x[~np.isnan(x)]
            if not len(valid):
                return nan
            order = np.argsort(np.argsort(valid))
            ranks = np.full(n, np.nan)
            ranks[~np.isnan(x)] = order / max(1, len(valid) - 1)
            return ranks
        if tag in ("ts_mean", "ts_std", "ts_min", "ts_max", "ts_rank",
                   "decay_linear", "ts_argmax", "ts_argmin"):
            fn = {"ts_mean": np.nanmean, "ts_std": np.nanstd,
                  "ts_min": np.nanmin, "ts_max": np.nanmax}.get(tag)
            out = np.full(n, np.nan)
            for i in range(n):
                win = x[max(0, i - w + 1):i + 1]
                win = win[~np.isnan(win)]
                if not len(win):
                    continue
                if tag == "ts_rank":
                    out[i] = float(np.mean(win <= x[i]))
                elif tag == "decay_linear":
                    weights = np.arange(1, len(win) + 1)
                    out[i] = float(np.average(win, weights=weights))
                elif tag == "ts_argmax":
                    out[i] = float(len(win) - 1 - np.argmax(win[::-1]))
                elif tag == "ts_argmin":
                    out[i] = float(len(win) - 1 - np.argmin(win[::-1]))
                else:
                    out[i] = float(fn(win))
            return out
        if tag in ("correlation", "covariance") and len(args) >= 2:
            y = args[1]
            out = np.full(n, np.nan)
            for i in range(n):
                xs, ys = x[max(0, i - w + 1):i + 1], y[max(0, i - w + 1):i + 1]
                m = ~(np.isnan(xs) | np.isnan(ys))
                if m.sum() < 3:
                    continue
                out[i] = float(np.corrcoef(xs[m], ys[m])[0, 1]) \
                    if tag == "correlation" \
                    else float(np.cov(xs[m], ys[m])[0, 1])
            return out
    except (ValueError, FloatingPointError, IndexError):
        return nan
    return nan


def _obs_to_series(obs_list: List[Dict[str, Any]]
                   ) -> Dict[str, np.ndarray]:
    fields = ("close", "volume", "high", "low")
    return {f: np.array([
        float(o[f]) if isinstance(o.get(f), (int, float)) else np.nan
        for o in obs_list]) for f in fields}
# Features derivable honestly from bar history — the enriched obs set
# plus raw fields. Anything else is not a valid engineered input.
DERIVABLE_FEATURES = {
    "close", "open", "high", "low", "volume", "price",
    "volatility", "trend", "rsi", "rsi14", "momentum",
    "trend_strength", "regime", "volume_ratio",
    "htf_close", "htf_trend", "htf_rsi14",
    "peer_close", "peer_return", "peer_corr", "bid", "ask",
    "spread_bps", "advisory_disagreement",
    "system_health_score", "system_health_flags",
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


def _ga_signal(obs_list: List[Dict[str, Any]], expr: str) -> np.ndarray:
    """Evaluate an alpha expression over a bar sequence → signal per bar."""
    series = _expr_series(_obs_to_series(obs_list))
    return _eval_expr(_parse_expr(expr), series)


def _fit_ga_expression(train: List[Dict[str, Any]], expr: str
                       ) -> Optional[Dict[str, Any]]:
    """Fit direction + activation threshold for a fixed alpha expression
    on the training slice: sweep both directions and signal-magnitude
    quantiles, keep the best in-sample net expectancy."""
    sig = _ga_signal(train, expr)
    best = None
    for direction in ("BUY", "SELL"):
        side = sig if direction == "BUY" else -sig
        valid = side[~np.isnan(side)]
        if len(valid) < 40:
            continue
        for q in np.quantile(valid, [0.5, 0.6, 0.7, 0.8, 0.9]):
            hits = 0
            ret = 0.0
            for i, o in enumerate(train):
                if i >= len(side) or np.isnan(side[i]) or side[i] <= q:
                    continue
                r = _forward_return(train, i)
                if r is None:
                    continue
                hits += 1
                ret += r - COST_BPS * 1e-4
            if hits >= MIN_HOLDOUT_SIGNALS and (best is None or ret > best[1]):
                best = (float(q), ret, hits, direction)
    if best is None:
        return None
    return {"expression": expr, "threshold": best[0],
            "direction": best[3],
            "insample_net_return": best[1], "insample_n": best[2]}


def _predict_ga(history: List[Dict[str, Any]], params: Dict[str, Any]
                ) -> Optional[str]:
    """Live prediction: evaluate the expression on the rolling window and
    emit the fitted direction when the signal exceeds the fitted
    threshold."""
    if len(history) < 10:
        return None
    sig = _ga_signal(history, params["expression"])
    s = sig[-1] if len(sig) else np.nan
    if np.isnan(s):
        return None
    side = s if params["direction"] == "BUY" else -s
    return params["direction"] if side > params["threshold"] else None


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


def _bootstrap_significance(signal_returns: List[float], n_boot: int = 5000,
                            seed: int = 7) -> Dict[str, Any]:
    """ASRS Promotion Gate standard: paired bootstrap on the out-of-sample
    net-return series. Returns P(mean_return > 0) and the 95% CI — the
    gate requires significance, not just a positive sample mean."""
    arr = np.asarray(signal_returns, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) < 5:
        return {"p_gt_0": 0.0, "ci95": [0.0, 0.0], "n": int(len(arr))}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(n_boot, len(arr)))
    means = arr[idx].mean(axis=1)
    return {"p_gt_0": float(np.mean(means > 0)),
            "ci95": [float(np.quantile(means, 0.025)),
                     float(np.quantile(means, 0.975))],
            "n": int(len(arr))}


def evaluate_holdout(spec: Dict[str, Any], params: Dict[str, Any],
                     holdout: List[Dict[str, Any]],
                     horizon: int = 8) -> Dict[str, Any]:
    """Score a fitted candidate on bars it never saw. Objective is net
    expectancy after the cost model — accuracy alone is not success."""
    n_calls = wins = 0
    ret = 0.0
    signal_returns: List[float] = []
    for i, o in enumerate(holdout):
        r = _forward_return(holdout, i, horizon)
        if r is None:
            continue
        if spec["kind"] == "threshold_rule":
            pred = _predict_threshold(o, params)
            conf = 0.6
        elif spec["kind"] == "ga_expression":
            hist = holdout[max(0, i - 63):i + 1]
            pred = _predict_ga(hist, params)
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
        signal_returns.append(net)
        if signed > 0:
            wins += 1
    result = {
        "holdout_signals": n_calls,
        "accuracy": (wins / n_calls) if n_calls else None,
        "net_return": ret,
        "mean_net_bps": (ret / n_calls * 1e4) if n_calls else None,
        "horizon": horizon,
    }
    result["significance"] = _bootstrap_significance(signal_returns)
    return result


# Promotion-gate significance bar for advisory candidates (ASRS asks
# P(Δ>0) >= 0.95 for production promotion; advisory candidates earn only
# trust-ramp influence, so 0.90 is the honest bar for a voting slot).
SIGNIFICANCE_THRESHOLD = 0.90


def fit_candidate(spec: Dict[str, Any], train: List[Dict[str, Any]]
                  ) -> Optional[Dict[str, Any]]:
    if spec["kind"] == "threshold_rule":
        return _fit_threshold(train, spec["feature"], spec["direction"])
    if spec["kind"] == "ga_expression":
        return _fit_ga_expression(train, str(spec["expression"]))
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
    if kind == "ga_expression":
        expr = str(spec.get("expression") or "")
        if not expr:
            errs.append("ga_expression needs an expression")
        else:
            try:
                ast = _parse_expr(expr)
                # Evaluate on a small synthetic series — parses is not
                # enough; unknown ops (all-NaN output) must die here,
                # not at validation.
                probe = 1.0 + np.linspace(0, 0.1, 160) + np.random.RandomState(3).normal(0, 0.001, 160)
                sig = _eval_expr(ast, {
                    "close": probe, "high": probe, "low": probe,
                    "volume": probe, "returns": probe,
                    "log_returns": probe, "volatility": probe,
                    "vwap": probe})
                if not np.isfinite(np.asarray(sig)).any():
                    errs.append("expression evaluates to no signal "
                                "(all-NaN on a probe series)")
            except Exception as exc:  # noqa: BLE001
                errs.append(f"expression does not evaluate: {exc}")
    return errs


def candidate_adapter(candidate: ModelCandidate) -> Any:
    """Wrap an approved candidate as an advisory-only service. It votes
    like every other advisor — trust ramp, regime eligibility and
    measured reliability weighting all apply from day one."""
    from trading_bot.core.csc.advisory import AdvisoryModuleAdapter

    spec = dict(candidate.spec)
    params = dict(candidate.fitted_params)
    horizon = 8
    # Rolling raw-bar history for expression evaluation — the adapter
    # accumulates it itself, so it benefits from the same startup
    # warm-up seeding every other advisor gets.
    history: List[Dict[str, Any]] = []

    async def analyze(ctx: Mapping[str, Any]) -> Dict[str, Any]:
        if spec["kind"] == "ga_expression":
            if isinstance(ctx.get("close"), (int, float)):
                history.append({k: ctx.get(k) for k in
                                ("close", "volume", "high", "low")})
                if len(history) > 64:
                    del history[:-64]
            direction = _predict_ga(history, params)
            confidence = 0.6
        elif spec["kind"] == "threshold_rule":
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


class SprtMonitor:
    """Wald SPRT on an attached model's live outcomes (ASRS continuous
    monitoring). H0: win rate >= p0 (edge persists); H1: win rate <= p1
    (edge degraded). Crossing the lower bound => accept H1 => the caller
    rolls the model back. Bounds use Wald approximations
    A=(1-beta)/alpha, B=beta/(1-alpha) on the log-likelihood ratio."""

    def __init__(self, p0: float = 0.50, p1: float = 0.42,
                 alpha: float = 0.05, beta: float = 0.10):
        self.p0, self.p1 = p0, p1
        self.upper = math.log((1 - beta) / alpha)   # ~ln18 ≈ 2.89
        self.lower = math.log(beta / (1 - alpha))   # ~ln(0.105) ≈ -2.25
        self.llr = 0.0
        self.n = 0
        self.verdict = "monitoring"  # | "degraded" | "confirms_edge"

    def update(self, win: bool) -> str:
        # LLR = log(f(x|H1)/f(x|H0)) — losses push toward the upper bound
        # (accept H1: edge degraded); wins pull toward the lower bound
        # (accept H0: edge persists).
        self.n += 1
        p_win = self.p1 if win else (1 - self.p1)
        p_null = self.p0 if win else (1 - self.p0)
        self.llr += math.log(p_win / p_null)
        if self.llr >= self.upper:
            self.verdict = "degraded"
        elif self.llr <= self.lower and self.n >= 20:
            self.verdict = "confirms_edge"
        return self.verdict


def benjamini_hochberg(p_values: List[float], q: float = 0.05
                       ) -> List[bool]:
    """BH procedure (ASRS FDR standard): when m candidates are validated
    in parallel, only the ones surviving FDR control may be promoted —
    the rest are multiple-comparison luck, not edge."""
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    passed = [False] * m
    k_max = -1
    for k, i in enumerate(order, start=1):
        if p_values[i] <= (k / m) * q:
            k_max = k
    for k, i in enumerate(order, start=1):
        if k <= k_max:
            passed[i] = True
    return passed


async def validate_alpha_generation(
    csc: Any,
    candidate_ids: List[str],
    bars: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Batch validation with FDR control (ASRS Promotion Gate): validate
    every candidate on the same bars, then apply Benjamini-Hochberg on
    the per-candidate p(Δ≤0). Survivors stay VALIDATED; the rest are
    re-verdicted FDR_REJECTED — statistically, most 'wins' in a
    generation sweep are luck."""
    results: List[Dict[str, Any]] = []
    p_values: List[float] = []
    for cid in candidate_ids:
        r = await csc.validate_model(cid, bars)
        sig = (r.get("validation") or {}).get("significance") or {}
        p = 1.0 - float(sig.get("p_gt_0") or 0.0)
        p_values.append(p)
        results.append({"candidate_id": cid, "status": r.get("status"),
                        "p_le_0": p})
    survivors = benjamini_hochberg(p_values)
    n_survived = 0
    for res, survived in zip(results, survivors):
        res["fdr_survived"] = bool(survived)
        c = csc._engineered_models.get(res["candidate_id"])
        if c is not None and c.status == "VALIDATED" and not survived:
            c.status = "REJECTED"
            c.verdict = "FDR_REJECTED"
            await csc._persist_audit_event(
                event_type="MODEL_VALIDATION", action="fdr_gate",
                outcome="FDR_REJECTED", correlation_id=res["candidate_id"],
                details={"name": c.name, "p_le_0": res["p_le_0"]})
        elif c is not None and survived:
            n_survived += 1
    return {"validated": n_survived, "tested": len(candidate_ids),
            "candidates": results}


async def evolve_alpha_generation(
    csc: Any,
    parent_candidate_ids: List[str],
    bars: List[Dict[str, Any]],
    n_offspring: int = 8,
) -> Dict[str, Any]:
    """Generational self-training (ASRS Evolution Engine): breed new
    candidates from FDR survivors via the alpha grammar's own mutation/
    crossover, propose each offspring through the same gated pipeline,
    batch-validate with FDR control. The AI evolves its own attached
    models — every generation still faces the gate."""
    from trading_bot.apex_fi.alpha_mining import GeneticAlphaSearch
    search = GeneticAlphaSearch(population_size=20, mutation_rate=0.4)
    parents: List[str] = []
    for cid in parent_candidate_ids:
        c = csc._engineered_models.get(cid)
        if c is not None and c.spec.get("kind") == "ga_expression":
            parents.append(str(c.spec.get("expression") or ""))
    parents = [p for p in parents if p]
    if not parents:
        return {"status": "no_parents",
                "reason": "no ga_expression parents to breed from"}
    import random as _rnd
    rng = _rnd.Random(13)
    offspring: List[str] = []
    while len(offspring) < n_offspring:
        if len(parents) >= 2 and rng.random() < 0.5:
            expr = search._crossover(
                rng.choice(parents), rng.choice(parents))
        else:
            expr = rng.choice(parents)
        if rng.random() < 0.6:
            expr = search._mutate(expr)
        if expr and expr not in offspring:
            offspring.append(expr)
    proposed: List[str] = []
    for i, expr in enumerate(offspring):
        r = await csc.propose_model(
            {"kind": "ga_expression", "expression": expr,
             "name": f"gen2:{expr[:28]}"},
            proposed_by="self_training:evolve")
        if r.get("status") == "proposed":
            proposed.append(r["candidate_id"])
    verdict = await validate_alpha_generation(csc, proposed, bars)
    return {"parents": len(parents), "offspring": len(proposed),
            "validated": verdict["validated"],
            "candidates": verdict["candidates"]}


async def propose_alpha_generation(
    csc: Any,
    n_proposals: int = 20,
    population_size: int = 200,
) -> List[str]:
    """Bridge: the quarantined apex_fi GeneticAlphaSearch generates
    candidate alpha expressions; the ones our safe evaluator can actually
    compute become ``ga_expression`` proposals. Everything still faces
    the full gate — OOS validation, then human approval — before any
    voice is earned."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from trading_bot.apex_fi.alpha_mining import GeneticAlphaSearch
        gen = GeneticAlphaSearch(population_size=population_size)
        gen.initialize_population()
    probe_series = _expr_series({
        f: (np.arange(1, 65, dtype=float) * 0.01) + 1.1
        for f in ("close", "volume", "high", "low")})
    proposed: List[str] = []
    seen = set()
    for cand in list(getattr(gen, "_population", ())):
        expr = str(getattr(cand, "expression", "") or "")
        if not expr or expr in seen:
            continue
        try:
            sig = _eval_expr(_parse_expr(expr), probe_series)
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(sig, np.ndarray) or np.isnan(sig).all():
            continue
        seen.add(expr)
        r = await csc.propose_model(
            {"kind": "ga_expression", "expression": expr,
             "name": f"ga:{expr[:32]}"},
            proposed_by="alpha_mining")
        if r.get("status") == "proposed":
            proposed.append(r["candidate_id"])
        if len(proposed) >= n_proposals:
            break
    return proposed

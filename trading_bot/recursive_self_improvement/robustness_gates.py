"""Robustness gates inspired by production strategy breeders (Algory audit).

Three cheap falsifiers layered on top of the signed paired-replay report,
all computed *inside* the existing evidence boundary so no protected
evaluator file needs new statistical machinery:

- ``order_shuffle_gate`` — path-fragility check. The candidate's per-bar net
  series is resampled as contiguous blocks (preserving local dependence,
  unlike iid shuffling) and its drawdown re-measured. A candidate whose edge
  depends on a lucky ordering of returns fails when too many reorderings
  breach the drawdown regression budget.
- ``perturbation_gate`` — local-stability check. The verifier replays K
  parameter perturbations of the candidate; at least half must stay
  net-positive and the probe count must clear a minimum, mirroring the
  "nudge the parameters" gate.
- ``random_field_gate`` — the candidate's holdout net return must beat at
  least half of a field of uniformly-random parameter vectors replayed on
  the same data, mirroring the "beat random" gate.

Everything is deterministic: every stochastic step is seeded from the
contract hash + trial id, so a verdict replays bit-identically.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


def _finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _seed(*parts: Any) -> int:
    payload = json.dumps(parts, sort_keys=True, default=str).encode("utf-8")
    return int(hashlib.sha256(payload).hexdigest()[:16], 16)


def equity_max_drawdown(returns: Sequence[float]) -> float:
    """Max drawdown of the compounded equity path built from per-bar nets."""
    equity = peak = 1.0
    worst = 0.0
    for r in returns:
        if not _finite(r) or r <= -1.0:
            return float("inf")
        equity *= 1.0 + r
        peak = max(peak, equity)
        worst = max(worst, 1.0 - equity / peak)
    return worst


def net_return_of(returns: Sequence[float]) -> float:
    equity = 1.0
    for r in returns:
        equity *= 1.0 + r
        if not _finite(equity):
            return float("-inf")
    return equity - 1.0


def candidate_series(report: Mapping[str, Any]) -> Tuple[List[Any], List[float]]:
    """Reconstruct the cross-sectional mean candidate net series per
    timestamp — the same alignment ``MultiObjectiveEvaluator`` uses."""
    grouped: Dict[str, Dict[Any, float]] = {}
    for row in report.get("bars") or []:
        if not isinstance(row, dict):
            continue
        sym, ts = row.get("symbol"), row.get("timestamp")
        net = row.get("candidate_net")
        if isinstance(sym, str) and _finite(ts) and _finite(net):
            grouped.setdefault(sym, {})[ts] = float(net)
    if not grouped:
        return [], []
    timeline = sorted(next(iter(grouped.values())))
    series = [
        sum(grouped[s][t] for s in grouped if t in grouped[s]) / len(grouped)
        for t in timeline
    ]
    return timeline, series


def order_shuffle_gate(
    returns: Sequence[float],
    *,
    observed_max_dd: Optional[float] = None,
    max_drawdown: float = 0.5,
    drawdown_regression: float = 0.05,
    max_bad_frac: float = 0.4,
    shuffles: int = 1000,
    block: int = 8,
    seed: int = 0,
) -> Tuple[bool, str, Dict[str, float]]:
    """Block-permutation fragility check on the candidate equity path.

    Contiguous blocks of ``block`` bars are permuted (local dependence is
    preserved inside a block; long-range ordering is destroyed). A shuffle
    is "bad" when its max drawdown exceeds the observed drawdown inflated
    by the contract's drawdown-regression budget, or breaches the absolute
    contract drawdown cap outright. Fails when the bad fraction exceeds
    ``max_bad_frac`` (Algory's documented 40% bar).
    """
    rets = [float(r) for r in returns]
    n = len(rets)
    if n < 4 * block or shuffles < 1:
        return True, "insufficient path length for order-shuffle gate", {
            "order_shuffle_bad_frac": 0.0, "order_shuffle_shuffles": 0.0}
    observed = (equity_max_drawdown(rets) if observed_max_dd is None
                else float(observed_max_dd))
    bad_threshold = max(observed * (1.0 + max(0.0, drawdown_regression)),
                        observed + 1e-12)
    rng = random.Random(seed)
    n_blocks = math.ceil(n / block)
    bad = 0
    evaluated = 0
    for _ in range(shuffles):
        order = list(range(n_blocks))
        rng.shuffle(order)
        shuffled: List[float] = []
        for b in order:
            start = b * block
            shuffled.extend(rets[start:start + block])
        shuffled = shuffled[:n]
        dd = equity_max_drawdown(shuffled)
        evaluated += 1
        if dd > max_drawdown or dd > bad_threshold:
            bad += 1
    bad_frac = bad / evaluated if evaluated else 1.0
    metrics = {
        "order_shuffle_bad_frac": bad_frac,
        "order_shuffle_shuffles": float(evaluated),
        "order_shuffle_observed_dd": observed,
    }
    if bad_frac > max_bad_frac:
        return False, (
            f"order-fragile path: {bad_frac:.1%} of {evaluated} block "
            f"orderings breach the drawdown budget"), metrics
    return True, "", metrics


def perturbation_gate(
    perturbation_results: Sequence[Mapping[str, Any]],
    *,
    min_perturbations: int = 4,
    min_profitable_frac: float = 0.5,
) -> Tuple[bool, str, Dict[str, float]]:
    """Local parameter-stability check over verifier-supplied probes.

    Each entry needs a finite ``net_return`` for the perturbed candidate.
    Fails when fewer than half the probes stay profitable, or when the
    probe count is too small to mean anything (Algory refuses <15
    held-out trades; here the analog is too few completed probes).
    """
    nets = [float(p["net_return"]) for p in perturbation_results
            if isinstance(p, Mapping) and _finite(p.get("net_return"))]
    n = len(nets)
    if n < min_perturbations:
        return False, (
            f"insufficient perturbation probes: {n} < {min_perturbations}"), {
            "perturbation_profitable_frac": 0.0,
            "perturbation_probes": float(n)}
    profitable = sum(1 for x in nets if x > 0.0)
    frac = profitable / n
    metrics = {
        "perturbation_profitable_frac": frac,
        "perturbation_probes": float(n),
    }
    if frac < min_profitable_frac:
        return False, (
            f"parameter-fragile candidate: only {frac:.0%} of {n} "
            f"perturbations stay profitable"), metrics
    return True, "", metrics


def random_field_gate(
    candidate_net: float,
    field_nets: Sequence[float],
    *,
    min_field: int = 8,
    min_percentile: float = 0.5,
) -> Tuple[bool, str, Dict[str, float]]:
    """Candidate must beat at least half the random-parameter field.

    ``field_nets`` are holdout net returns of uniformly random parameter
    draws replayed on the same frames. The bar rises implicitly with field
    size; a thin field is refused outright.
    """
    field = [float(x) for x in field_nets if _finite(x)]
    if len(field) < min_field or not _finite(candidate_net):
        return False, (
            f"insufficient random-field sample: {len(field)} < {min_field}"), {
            "random_field_percentile": 0.0,
            "random_field_size": float(len(field))}
    beaten = sum(1 for x in field if candidate_net > x)
    percentile = beaten / len(field)
    metrics = {
        "random_field_percentile": percentile,
        "random_field_size": float(len(field)),
        "random_field_candidate_net": float(candidate_net),
    }
    if percentile < min_percentile:
        return False, (
            f"candidate does not beat the random field: percentile "
            f"{percentile:.0%} < {min_percentile:.0%}"), metrics
    return True, "", metrics


def gate_report(
    report: Mapping[str, Any],
    contract: Mapping[str, Any],
    cfg: Optional[Mapping[str, Any]] = None,
) -> Tuple[bool, str, Dict[str, float]]:
    """Apply whichever robustness gates the cycle config enables.

    ``cfg`` keys (all default off / permissive):
      order_shuffles (int, 0=off), perturbations (int, 0=off),
      random_field (int, 0=off), order_block (int, default 8),
      order_max_bad_frac (float, default 0.4),
      perturbation_min (int, default 4),
      random_field_min (int, default 8).

    Order-shuffle always runs on the report's own bars when enabled — no
    extra replay needed. Perturbation/random-field results must already be
    present under ``report["robustness"]`` (produced inside the sandboxed
    verifier replay); a missing block is fail-closed.
    """
    cfg = dict(cfg or {})
    metrics: Dict[str, float] = {}
    n_shuffle = int(cfg.get("order_shuffles", 0) or 0)
    n_perturb = int(cfg.get("perturbations", 0) or 0)
    n_field = int(cfg.get("random_field", 0) or 0)
    if n_shuffle <= 0 and n_perturb <= 0 and n_field <= 0:
        return True, "", metrics

    if n_shuffle > 0:
        _, series = candidate_series(report)
        ok, reason, m = order_shuffle_gate(
            series,
            max_drawdown=float(contract.get("max_drawdown", 0.5)),
            drawdown_regression=float(contract.get("max_drawdown_regression", 0.05)),
            max_bad_frac=float(cfg.get("order_max_bad_frac", 0.4)),
            shuffles=n_shuffle,
            block=int(cfg.get("order_block", 8)),
            seed=_seed(contract.get("contract_id"), report.get("trial_id"),
                       "order_shuffle"),
        )
        metrics.update(m)
        if not ok:
            return False, reason, metrics

    robustness = report.get("robustness")
    if n_perturb > 0:
        probes = (robustness or {}).get("perturbations") or []
        ok, reason, m = perturbation_gate(
            probes,
            min_perturbations=int(cfg.get("perturbation_min", 4)))
        metrics.update(m)
        if not ok:
            return False, reason, metrics

    if n_field > 0:
        field_nets = (robustness or {}).get("random_field", [])
        cand_net = float((robustness or {}).get("candidate_net_return", float("nan")))
        ok, reason, m = random_field_gate(
            cand_net, field_nets,
            min_field=int(cfg.get("random_field_min", 8)))
        metrics.update(m)
        if not ok:
            return False, reason, metrics

    return True, "", metrics


# ---------------------------------------------------------------------------
# Verifier-side evidence production (runs inside the sandboxed replay)
# ---------------------------------------------------------------------------

_PERTURB_FACTORS = (0.8, 0.9, 1.1, 1.25)


def _holdout_net_return(out: Mapping[str, Any], contract: Mapping[str, Any]
                        ) -> float:
    """Compounded candidate net return restricted to the contract holdout."""
    hs = float(contract.get("holdout_start", 0))
    he = float(contract.get("holdout_end", float("inf")))
    timeline, series = candidate_series({"bars": out.get("bars") or []})
    rets = [r for t, r in zip(timeline, series) if hs <= float(t) < he]
    return net_return_of(rets) if rets else float("nan")


def build_robustness_evidence(
    *,
    adapter: Any,
    frames: Mapping[str, Any],
    contract: Mapping[str, Any],
    incumbent_params: Mapping[str, Any],
    candidate_params: Mapping[str, Any],
    genome: Any,
    trial_id: str,
    cfg: Mapping[str, Any],
) -> Dict[str, Any]:
    """Replay perturbation + random-field probes for ``gate_report``.

    Called inside ``IndependentVerifier.replay_and_build_report`` so the
    extra evidence is produced keyless inside the sandbox and covered by
    the parent signature like every other report field. Deterministic:
    perturbations are fixed multiplicative factors; the random field is
    seeded from contract + trial id.
    """
    from trading_bot.evaluation.runner import PairedFamilyReplay

    runner = PairedFamilyReplay(
        adapter, cost_bps=float(contract["max_cost_bps"]), fraction=0.01)
    frames_d = dict(frames)

    def replay(params: Mapping[str, Any]) -> float:
        out = runner.run(frames_d, baseline_params=dict(incumbent_params),
                         candidate_params=dict(params))
        return _holdout_net_return(out, contract)

    candidate_net = replay(candidate_params)

    change = dict(getattr(genome, "change_set", {}) or {})
    param = next(iter(change), None)
    bounds = (contract.get("allowed_parameters") or {}).get(param) \
        if param else None
    perturbations: List[Dict[str, Any]] = []
    if param and bounds:
        lo, hi = float(bounds[0]), float(bounds[1])
        base = float(candidate_params.get(param, change[param]))
        for f in _PERTURB_FACTORS:
            v = max(lo, min(hi, base * f))
            if v == base:
                continue
            p = dict(candidate_params)
            p[param] = v
            perturbations.append({"params": {param: v},
                                  "net_return": replay(p)})

    field_nets: List[float] = []
    n_field = int(cfg.get("random_field", 0) or 0)
    allowed = contract.get("allowed_parameters") or {}
    validate = getattr(adapter, "validate", None)
    if n_field > 0 and allowed:
        rng = random.Random(_seed(contract.get("contract_id"), trial_id,
                                  "random_field"))
        for _ in range(n_field):
            drawn: Dict[str, float] = {}
            for name, (lo, hi) in allowed.items():
                drawn[name] = rng.uniform(float(lo), float(hi))
            ok = True
            if validate is not None:
                for _try in range(8):
                    if validate(drawn):
                        break
                    for name, (lo, hi) in allowed.items():
                        drawn[name] = rng.uniform(float(lo), float(hi))
                else:
                    ok = False
            if ok:
                field_nets.append(replay(drawn))

    return {
        "candidate_net_return": candidate_net,
        "perturbations": perturbations,
        "random_field": field_nets,
    }

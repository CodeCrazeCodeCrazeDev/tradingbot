"""Versioned, diagnostic rewards owned by CSC; never execution authority.

Objectives retain their units. There is deliberately no weighted sum through
which profit can compensate for a failed safety/evidence gate. Missing values
remain None. Callers persist these records in their existing evidence ledgers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Optional, Tuple

POLICY_VERSION = "csc-rewards-v1"
ORIGINS = frozenset({"paper", "live", "historical", "synthetic", "simulated",
                     "unknown"})


def finite(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


@dataclass(frozen=True)
class Objective:
    name: str
    value: Optional[float]
    unit: str
    direction: str = "max"


@dataclass(frozen=True)
class RewardRecord:
    domain: str
    evidence_id: str
    origin: str
    objectives: Tuple[Objective, ...]
    blockers: Tuple[str, ...] = ()
    sample_weight: float = 1.0
    policy_version: str = POLICY_VERSION

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["reward_id"] = hashlib.sha256(json.dumps(
            payload, sort_keys=True, allow_nan=False).encode()).hexdigest()
        payload.update(advisory_only=True, promotion_eligible=False,
                       evidence_class="diagnostic")
        return payload


def provenance(evidence_id: str, origin: str) -> Tuple[str, ...]:
    problems = []
    if not evidence_id:
        problems.append("missing_evidence_id")
    if origin not in ORIGINS or origin == "unknown":
        problems.append("unknown_origin")
    if origin in {"simulated", "synthetic"}:
        problems.append("sandbox_only")
    return tuple(problems)


def prediction_reward(evidence_id: str, probability: Any, outcome: Any,
                      *, origin: str = "unknown",
                      sample_weight: float = 1.0) -> RewardRecord:
    """Proper binary score; certainty about a wrong outcome is penalized.

    A 0.5 constant forecast has skill zero. This is per-outcome Brier skill,
    not a claim that the predictor is calibrated.
    """
    blockers = list(provenance(evidence_id, origin))
    valid = (finite(probability) and 0 <= probability <= 1
             and isinstance(outcome, bool))
    if not valid:
        blockers.append("missing_or_invalid_prediction_pair")
    brier = (float(probability) - int(outcome)) ** 2 if valid else None
    if not finite(sample_weight) or not 0 < sample_weight <= 1:
        blockers.append("invalid_sample_weight")
        sample_weight = 0.0
    return RewardRecord("prediction", evidence_id, origin, (
        Objective("brier", brier, "fraction", "min"),
        Objective("skill_vs_half", 0.25 - brier if valid else None, "fraction"),
    ), tuple(blockers), sample_weight)


def trading_reward(evidence_id: str, gross_return: Any, *,
                   cost_return: Any = None, baseline_net_return: Any = None,
                   origin: str = "unknown", shared_settlement: int = 1,
                   constraints_satisfied: Optional[bool] = None) -> RewardRecord:
    """Returns/costs are fractions on the SAME notional and horizon.

    Raw price moves are gross, not net PnL. No payout is fabricated from
    approval, a BUY/SELL label, confidence, or absence of trades.
    """
    blockers = list(provenance(evidence_id, origin))
    gross = float(gross_return) if finite(gross_return) else None
    cost = (float(cost_return) if finite(cost_return)
            and cost_return >= 0 else None)
    base = float(baseline_net_return) if finite(baseline_net_return) else None
    if gross is None:
        blockers.append("missing_settled_return")
    if cost is None:
        blockers.append("missing_costs")
    if base is None:
        blockers.append("missing_paired_baseline")
    if constraints_satisfied is not True:
        blockers.append("constraint_breach" if constraints_satisfied is False
                        else "constraints_unverified")
    valid_count = type(shared_settlement) is int and shared_settlement > 0
    if not valid_count:
        blockers.append("invalid_shared_settlement")
    net = gross - cost if gross is not None and cost is not None else None
    alpha = net - base if net is not None and base is not None else None
    if net is not None and (not finite(net) or (alpha is not None and not finite(alpha))):
        net = alpha = None
        blockers.append("invalid_return_arithmetic")
    return RewardRecord("trading", evidence_id, origin, (
        Objective("gross_return", gross, "fraction"),
        Objective("cost_return", cost, "fraction", "min"),
        Objective("net_return", net, "fraction"),
        Objective("alpha_vs_baseline", alpha, "fraction"),
    ), tuple(blockers), 1.0 / shared_settlement if valid_count else 0.0)


def research_reward(evidence_id: str, verdict: str, *, origin: str,
                    protocol_verified: bool, comparison_complete: bool,
                    compute_seconds: Any = None) -> RewardRecord:
    """Reward resolving a precommitted question, including falsification.

    A seal alone is not protocol verification. That flag must come from the
    experiment runner verifying the pre-execution contract, not the model.
    """
    blockers = list(provenance(evidence_id, origin))
    if protocol_verified is not True:
        blockers.append("protocol_unverified")
    if comparison_complete is not True:
        blockers.append("incomplete_comparison")
    resolved = verdict in {"CONFIRMED", "FALSIFIED"}
    credit = float(resolved and not blockers)
    seconds = (float(compute_seconds) if finite(compute_seconds)
               and compute_seconds >= 0 else None)
    return RewardRecord("research", evidence_id, origin, (
        Objective("resolved_question", credit, "fraction"),
        Objective("compute_seconds", seconds, "seconds", "min"),
    ), tuple(blockers))


def forecast_reward(evidence_id: str, predicted: Any, observed: Any,
                    baseline: Any, *, origin: str) -> RewardRecord:
    """World-model error on an observed target in fixed, declared units.

    Learned latent cosine is not market reward. This function requires a
    decoded target and the matching persistence/baseline prediction.
    """
    blockers = list(provenance(evidence_id, origin))
    valid = all(finite(x) for x in (predicted, observed, baseline))
    try:
        error = (predicted - observed) ** 2 if valid else None
        base_error = (baseline - observed) ** 2 if valid else None
    except OverflowError:
        error = base_error = None
    if not valid or not finite(error) or not finite(base_error):
        error = base_error = None
        blockers.append("missing_or_invalid_observed_target")
    return RewardRecord("world_model", evidence_id, origin, (
        Objective("squared_error", error, "target_units_squared", "min"),
        Objective("error_reduction_vs_baseline",
                  base_error - error if error is not None else None,
                  "target_units_squared"),
    ), tuple(blockers))

"""Versioned multi-objective improvement contract (schema_version 2).

The contract is the operator-owned, signed, hash-locked definition of what
counts as "improvement". A candidate can never change its own acceptance
criteria mid-experiment: the hash recorded at proposal time must equal the
hash at evaluation time (`assert_frozen`).

Schema 2 extends the 26 keys enforced by `evaluation.evaluate_verified`
with metric directions, Pareto objectives, regression budgets, economic
materiality, a regime/seed/cost transfer panel, a holdout query budget,
a recursion-depth bound and the protected-path list.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from cryptography.exceptions import InvalidSignature

from .metric_registry import METRIC_REGISTRY, direction

SCHEMA_VERSION = 2


class ContractError(ValueError):
    """Contract missing, malformed, unsigned or semantically invalid."""


# Keys inherited from the schema-1 evaluator plus schema-2 additions.
REQUIRED_KEYS = (
    "schema_version", "contract_id", "baseline_hash", "dataset_hash",
    "allowed_parameters", "min_bars", "min_instruments", "block_size",
    "max_trials", "minimum_net_gain", "max_drawdown",
    "max_drawdown_regression", "confidence", "max_cost_bps", "max_latency_ms",
    "train_end", "validation_start", "validation_end", "holdout_start",
    "holdout_end", "cost_model_id", "max_exposure", "max_cvar_95",
    "code_hash", "dependencies_hash", "max_turnover",
    # schema-2 additions
    "strategy_family", "metric_directions", "pareto_objectives",
    "regression_budgets", "economic_materiality_min", "regime_panel",
    "holdout_query_budget", "max_recursion_depth", "protected_paths",
    "seeds", "cost_multipliers", "min_cost_bps", "expiry",
)

NUMERIC_KEYS = (
    "min_bars", "min_instruments", "block_size", "max_trials",
    "minimum_net_gain", "max_drawdown", "max_drawdown_regression",
    "confidence", "max_cost_bps", "min_cost_bps", "max_latency_ms",
    "train_end", "validation_start", "validation_end", "holdout_start",
    "holdout_end", "max_exposure", "max_cvar_95", "max_turnover",
    "economic_materiality_min", "holdout_query_budget", "max_recursion_depth",
    "expiry",
)

KNOWN_REGIMES = ("trend", "mean_revert", "high_vol", "crash", "flat")


def canonical(data: Mapping[str, Any]) -> bytes:
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str
    ).encode("utf-8")


def contract_hash(contract: Mapping[str, Any]) -> str:
    """Hash of the canonical contract body, excluding signature metadata."""
    body = {k: v for k, v in contract.items() if k not in ("signature", "contract_hash")}
    return hashlib.sha256(canonical(body)).hexdigest()


def signable_document(contract: Mapping[str, Any]) -> Dict[str, Any]:
    """The exact object an operator signs."""
    return {k: v for k, v in contract.items() if k != "signature"}


def _finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def validate_contract(contract: Any) -> Dict[str, Any]:
    """Structural + semantic validation. Returns the contract dict or raises."""
    if not isinstance(contract, dict):
        raise ContractError("contract is not an object")
    missing = [k for k in REQUIRED_KEYS if k not in contract]
    if missing:
        raise ContractError(f"missing required keys: {missing}")
    if contract["schema_version"] != SCHEMA_VERSION:
        raise ContractError("unsupported contract schema")
    for k in NUMERIC_KEYS:
        if not _finite(contract[k]):
            raise ContractError(f"non-numeric or nonfinite threshold {k}")
    if not (contract["train_end"] < contract["validation_start"]
            <= contract["validation_end"] < contract["holdout_start"]
            < contract["holdout_end"]):
        raise ContractError("chronological split/embargo invalid")
    if not (0 < contract["confidence"] < 1 and contract["block_size"] >= 1
            and contract["min_bars"] >= 2 and contract["min_instruments"] >= 1
            and contract["max_trials"] >= 1 and contract["minimum_net_gain"] > 0
            and contract["economic_materiality_min"] > 0
            and contract["min_cost_bps"] >= 0
            and contract["max_cost_bps"] > contract["min_cost_bps"]
            and contract["max_drawdown"] >= 0
            and contract["max_drawdown_regression"] >= 0
            and contract["max_exposure"] > 0 and contract["max_cvar_95"] >= 0
            and contract["max_turnover"] >= 0
            and contract["holdout_query_budget"] >= 1
            and contract["max_recursion_depth"] >= 1
            and contract["expiry"] > 0):
        raise ContractError("invalid operator-calibrated thresholds")
    allowed = contract["allowed_parameters"]
    if not isinstance(allowed, dict) or not allowed:
        raise ContractError("allowed_parameters must be a non-empty map")
    for name, bounds in allowed.items():
        if (not isinstance(name, str) or not isinstance(bounds, (list, tuple))
                or len(bounds) != 2 or not all(_finite(b) for b in bounds)
                or bounds[0] >= bounds[1]):
            raise ContractError(f"invalid parameter bounds for {name!r}")
    dirs = contract["metric_directions"]
    if not isinstance(dirs, dict):
        raise ContractError("metric_directions must be a map")
    for metric, d in dirs.items():
        if metric not in METRIC_REGISTRY:
            raise ContractError(f"unregistered metric {metric!r}")
        if d != direction(metric) and direction(metric) != "info":
            raise ContractError(
                f"contract redefines direction of {metric!r}: registry is authoritative"
            )
    objectives = contract["pareto_objectives"]
    if (not isinstance(objectives, (list, tuple)) or not objectives
            or any(o not in METRIC_REGISTRY for o in objectives)
            or any(direction(o) == "info" for o in objectives)):
        raise ContractError("pareto_objectives must be registered non-info metrics")
    budgets = contract["regression_budgets"]
    if not isinstance(budgets, dict) or any(
        m not in METRIC_REGISTRY or not _finite(v) or v < 0
        for m, v in budgets.items()
    ):
        raise ContractError("regression_budgets must map registered metrics to >=0 tolerances")
    panel = contract["regime_panel"]
    if (not isinstance(panel, (list, tuple)) or not panel
            or any(r not in KNOWN_REGIMES for r in panel)):
        raise ContractError("regime_panel must use known regime names")
    seeds = contract["seeds"]
    if (not isinstance(seeds, (list, tuple)) or not seeds
            or any(not isinstance(s, int) or isinstance(s, bool) or s < 0 for s in seeds)):
        raise ContractError("seeds must be non-negative ints")
    mults = contract["cost_multipliers"]
    if (not isinstance(mults, (list, tuple)) or not mults
            or any(not _finite(m) or m <= 0 for m in mults)
            or min(mults) < 1.0):
        raise ContractError("cost_multipliers must be >=1 (1.0 = observed cost)")
    paths = contract["protected_paths"]
    if (not isinstance(paths, (list, tuple)) or not paths
            or any(not isinstance(p, str) or not p for p in paths)):
        raise ContractError("protected_paths must be non-empty strings")
    for key in ("contract_id", "baseline_hash", "dataset_hash", "strategy_family",
                "cost_model_id", "code_hash", "dependencies_hash"):
        if not isinstance(contract[key], str) or not contract[key]:
            raise ContractError(f"{key} must be a non-empty string")
    return contract


def verify_signature(contract: Mapping[str, Any], signature_hex: str,
                     operator_public_key: Any) -> None:
    try:
        operator_public_key.verify(
            bytes.fromhex(signature_hex), canonical(signable_document(contract))
        )
    except (ValueError, TypeError, AttributeError, InvalidSignature, OverflowError) as exc:
        raise ContractError("invalid or missing operator signature") from exc


def load_signed_contract(path: str | Path, operator_public_key: Any) -> Dict[str, Any]:
    """Load `{"contract": {...}, "signature": "<hex>"}`; verify + validate."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read contract file: {exc}") from exc
    if not isinstance(payload, dict) or "contract" not in payload or "signature" not in payload:
        raise ContractError("contract file must contain contract and signature")
    verify_signature(payload["contract"], payload["signature"], operator_public_key)
    contract = validate_contract(payload["contract"])
    return dict(contract)


def assert_frozen(expected_hash: str, contract: Mapping[str, Any]) -> None:
    """A candidate may not alter its own acceptance criteria mid-experiment."""
    if not expected_hash or contract_hash(contract) != expected_hash:
        raise ContractError("evaluation contract changed between proposal and evaluation")

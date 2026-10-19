"""MSOS survival diagnostics under CSC; no capital governor or trade authority."""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

from trading_bot.core.csc.rewards import Objective, RewardRecord, finite


class MSOSRewardAdvisor:
    """Score the supplied settlement window, without re-counting observations.

    No model, randomness, venue calls, constraint edits, sizing or execution.
    The current CSC provides gross price returns: these diagnostics must not
    be mistaken for account drawdown or cost-adjusted strategy performance.
    """
    capability_id = "msos_survival_reward"

    def analyze(self, context: Mapping[str, Any]) -> dict:
        state = context.get("self_state") or {}
        rows = state.get("settled_outcomes") or []
        returns = [row.get("realized_return") for row in rows
                   if isinstance(row, Mapping)]
        if (not returns or len(returns) != len(rows)
                or any(not finite(r) or r <= -1 for r in returns)):
            return {"capability_id": self.capability_id, "direction": "HOLD",
                    "confidence": 0.0, "advisory_only": True,
                    "evidence": {"status": "missing_data",
                                 "reason": "valid settlements required"}}
        equity = peak = 1.0
        drawdown = 0.0
        for value in returns:
            equity *= 1 + value
            peak = max(peak, equity)
            drawdown = max(drawdown, 1 - equity / peak)
        if not math.isfinite(equity):
            return {"advisory_only": True, "direction": "HOLD",
                    "evidence": {"status": "missing_data",
                                 "reason": "invalid equity path"}}
        n_tail = max(1, math.ceil(len(returns) * 0.05))
        tail_loss = max(0.0, -sum(sorted(returns)[:n_tail]) / n_tail)
        # Includes settlement identity where supplied. Same window => same ID.
        identity = hashlib.sha256(json.dumps(
            rows, sort_keys=True, default=str, allow_nan=False).encode()).hexdigest()
        reward = RewardRecord("survival", identity, "unknown", (
            Objective("window_gross_drawdown", drawdown, "fraction", "min"),
            Objective("window_gross_tail_loss_95", tail_loss, "fraction", "min"),
            Objective("settlements", float(len(returns)), "count", "info"),
        ), ("gross_returns_only", "window_not_account_risk", "unknown_origin"))
        return {"capability_id": self.capability_id, "direction": "HOLD",
                "confidence": 0.0, "advisory_only": True,
                "evidence": {"status": "measured",
                             "reward": reward.to_dict()}}


def firewall_reward(evidence_id: str, firewall_result: Mapping[str, Any],
                    *, update_attempted: bool, origin: str = "unknown") -> RewardRecord:
    """Audit compliance with an existing MSOS firewall result.

    Freezing learning never deletes adverse observations or creates positive
    alpha. This is feedback only, not a replacement for the firewall.
    """
    from trading_bot.core.csc.rewards import provenance
    blockers = list(provenance(evidence_id, origin))
    known = all(type(firewall_result.get(k)) is bool
                for k in ("can_learn", "data_allowed"))
    if not known:
        blockers.append("missing_firewall_evidence")
    violation = bool(known and update_attempted and not (
        firewall_result["can_learn"] and firewall_result["data_allowed"]))
    if violation:
        blockers.append("learning_firewall_violation")
    return RewardRecord("learning_safety", evidence_id, origin, (
        Objective("firewall_violation", float(violation) if known else None,
                  "count", "min"),
    ), tuple(blockers))

"""Agent foundry — builds new advisory agents through the real gated
model-engineering pipeline, and prices each as a strategy product.

Claims covered:

- #8 builds new agents: a generation is a bounded batch of candidate
  specs proposed through ``csc.propose_model`` and fitted/evaluated on
  real bars through ``csc.validate_model``. Survivors become VALIDATED
  candidates eligible for the operator-approval attach gate — the same
  trust ramp every other advisor faces. The foundry does not bypass
  that gate; agents it "builds" earn voice only through measurement.
- #14 designs companies: honestly reframed — a *strategy product* is
  the trading-bot analogue of a company: a named entity with a cost
  model, expected net expectancy, signal rate, and a capital envelope.
  The product case is derived from the sealed holdout evaluation, never
  invented.

Everything persisted is a record of something that actually ran.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

# Bounded spec pool: only kinds and features the safe evaluator can
# honestly derive from real bars (model_engineering.DERIVABLE_FEATURES).
DEFAULT_SPEC_POOL = (
    {"kind": "threshold_rule", "feature": "momentum", "op": ">",
     "direction": "BUY", "name": "foundry_momentum_buy"},
    {"kind": "threshold_rule", "feature": "momentum", "op": "<",
     "direction": "SELL", "name": "foundry_momentum_sell"},
    {"kind": "threshold_rule", "feature": "rsi14", "op": "<",
     "direction": "BUY", "name": "foundry_rsi_oversold_buy"},
    {"kind": "threshold_rule", "feature": "rsi14", "op": ">",
     "direction": "SELL", "name": "foundry_rsi_overbought_sell"},
    {"kind": "logistic",
     "features": ["momentum", "volatility", "ret_autocorr"],
     "name": "foundry_logistic_core"},
)


class AgentFoundry:
    """Proposes and validates new advisory candidates on real bars."""

    def __init__(self, state_path: Any) -> None:
        self.state_path = Path(state_path)
        self.generations: List[Dict[str, Any]] = self._load()

    async def run_generation(
        self,
        csc: Any,
        bars: List[Dict[str, Any]],
        specs: Optional[Iterable[Dict[str, Any]]] = None,
        dataset_label: str = "unknown",
    ) -> Dict[str, Any]:
        """Run one bounded generation: propose each spec through the real
        gate, validate on the supplied bars, record every verdict.

        ``bars`` must be real observations (timestamp/open/high/low/
        close/volume/symbol). The foundry never fabricates the market."""
        if len(bars) < 120:
            return {"status": "rejected",
                    "reason": "insufficient real bars for a generation"}
        specs = list(specs or DEFAULT_SPEC_POOL)
        record: Dict[str, Any] = {
            "generation": len(self.generations) + 1,
            "at": time.time(),
            "dataset": dataset_label,
            "bars": len(bars),
            "candidates": [],
            "status": "completed",
        }
        for spec in specs:
            entry: Dict[str, Any] = {"spec": dict(spec)}
            try:
                prop = await csc.propose_model(
                    dict(spec), proposed_by="expansion.foundry")
            except Exception as exc:  # noqa: BLE001
                entry.update(status="error", reason=str(exc)[:160])
                record["candidates"].append(entry)
                continue
            entry["propose_status"] = prop.get("status")
            cid = prop.get("candidate_id")
            if prop.get("status") != "proposed" or not cid:
                entry.update(status="rejected",
                             reason=prop.get("errors") or prop.get(
                                 "status"))
                record["candidates"].append(entry)
                continue
            entry["candidate_id"] = cid
            try:
                res = await csc.validate_model(cid, bars)
            except Exception as exc:  # noqa: BLE001
                entry.update(status="error", reason=str(exc)[:160])
                record["candidates"].append(entry)
                continue
            entry["status"] = res.get("status")
            entry["verdict"] = res.get("verdict")
            val = res.get("validation") or {}
            entry["reason"] = res.get("reason") or val.get("error")
            entry["mean_net_bps"] = val.get("mean_net_bps")
            entry["holdout_signals"] = val.get("holdout_signals")
            entry["p_gt_0"] = (val.get("significance") or {}).get(
                "p_gt_0")
            if res.get("status") == "validated":
                entry["product"] = self._product_case(
                    cid, spec, val, dataset_label)
            record["candidates"].append(entry)
        record["validated"] = sum(
            1 for c in record["candidates"]
            if c.get("status") == "validated")
        record["rejected"] = sum(
            1 for c in record["candidates"]
            if c.get("status") == "rejected")
        self.generations.append(record)
        self._save()
        return record

    @staticmethod
    def _product_case(candidate_id: str, spec: Dict[str, Any],
                      validation: Dict[str, Any],
                      dataset_label: str) -> Dict[str, Any]:
        """The honest 'company': a strategy product with a costed
        business case — what it trades on, what it is expected to earn
        net of costs on unseen data, and the risk envelope it must stay
        inside. Derived entirely from the sealed evaluation."""
        sig = validation.get("significance") or {}
        return {
            "product_kind": "strategy_product",
            "label": ("a deployable signal strategy with a measured "
                      "business case — not a legal entity"),
            "candidate_id": candidate_id,
            "name": spec.get("name"),
            "spec": dict(spec),
            "dataset": dataset_label,
            "expected_net_bps_per_signal": validation.get(
                "mean_net_bps"),
            "holdout_signals": validation.get("holdout_signals"),
            "p_gt_0": sig.get("p_gt_0"),
            "p_gt_baseline": sig.get("p_gt_baseline"),
            "seal": validation.get("seal"),
            "status": ("VALIDATED — awaiting the durable operator "
                       "approval gate before any advisory voice"),
        }

    def summary(self) -> Dict[str, Any]:
        """Artifact payload: what the foundry has actually produced."""
        validated = [
            {"candidate_id": c["candidate_id"], "name": c["spec"].get(
                "name"), "verdict": c.get("verdict")}
            for g in self.generations for c in g["candidates"]
            if c.get("status") == "validated"]
        return {
            "generations_run": len(self.generations),
            "candidates_total": sum(len(g["candidates"])
                                    for g in self.generations),
            "validated_products": validated[-10:],
            "products_count": len(validated),
            "note": ("validated candidates await the operator approval "
                     "gate — none hold authority yet"),
        }

    def _load(self) -> List[Dict[str, Any]]:
        if self.state_path.exists():
            try:
                return list(json.loads(
                    self.state_path.read_text()).get("generations", []))
            except Exception:  # noqa: BLE001
                return []
        return []

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(
            {"generations": self.generations[-50:]}, indent=2))
        tmp.replace(self.state_path)

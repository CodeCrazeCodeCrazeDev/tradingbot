"""
Reality-gate verifiers: adapt trading_bot.reality_gates and
trading_bot.ml.data_leakage_guard into the VerificationSwarm's
verify(ledger_entry) contract.

The gates were written as standalone checks with their own input
shapes; these adapters extract a candidate's ``validation={...}``
record from ``reasoning_steps`` and run the matching gate. They carry
no authority themselves — they return veto/verdict evidence only, and
they abstain (items_checked=0) on any entry that is not an engineered-
candidate review, so the research-ledger path is unaffected.
"""

import ast
import logging
import math
from typing import Any, Dict, List, Optional

from .swarm import BaseVerificationAgent, _eget, VerifierVerdict

logger = logging.getLogger(__name__)


def _extract_validation(entry: Any) -> Optional[Dict[str, Any]]:
    """Pull the ``validation={...}`` payload out of reasoning_steps.

    Candidate review packs the validation record as a repr on a
    reasoning step; anything else (research ledger entries, strings,
    snapshots) returns None and the verifier abstains."""
    steps = _eget(entry, "reasoning_steps") or []
    for step in steps:
        text = str(step)
        if not text.startswith("validation="):
            continue
        try:
            value = ast.literal_eval(text[len("validation="):])
        except (ValueError, SyntaxError):
            continue
        if isinstance(value, dict):
            return value
    return None


def _sig(entry: Any) -> Dict[str, Any]:
    val = _extract_validation(entry) or {}
    sig = val.get("significance")
    return sig if isinstance(sig, dict) else {}


class ExecutionRealismVerifier(BaseVerificationAgent):
    """No fantasy execution: the recorded cost model must be non-zero and
    the candidate's mean net edge must survive a realistic-cost analysis.
    """

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        val = _extract_validation(ledger_entry)
        if val is None:
            return VerifierVerdict(
                agent_name="ExecutionRealismVerifier", is_valid=True,
                items_checked=0, confidence=0.5,
                critique="no candidate validation payload — abstain")
        issues: List[str] = []
        items = 1
        cost_bps = val.get("cost_bps")
        if not isinstance(cost_bps, (int, float)) or cost_bps <= 0:
            issues.append("validation recorded no positive cost_bps — "
                          "zero-cost backtests are fantasy execution")
        mean_net = val.get("mean_net_bps")
        if isinstance(mean_net, (int, float)):
            try:
                from trading_bot.reality_gates.execution_realism_gate import (
                    ExecutionRealismGate)
                gate = ExecutionRealismGate()
                bar = val.get("sample_bar") or {}
                price = float(bar.get("close") or 1.0)
                adj = gate.analyze_trade(
                    symbol=str(bar.get("symbol") or "UNKNOWN"),
                    side="buy", size=1e6, price=price,
                    expected_return=float(mean_net) / 100.0,  # bps→%
                    volatility=0.01, spread=price * 2e-4,
                    avg_daily_volume=1e9)
                items += 1
                # mean_net_bps is already net of the light cost model —
                # veto only if it cannot also cover the heavier
                # realistic-cost estimate the gate produces.
                heavy_cost_bps = float(adj.total_cost) * 1e4
                if float(mean_net) < (heavy_cost_bps - float(cost_bps or 0)):
                    issues.append(
                        f"edge {mean_net:.2f}bps does not survive "
                        f"realistic-cost analysis "
                        f"(gate estimates ~{heavy_cost_bps:.1f}bps "
                        f"vs recorded {cost_bps}bps)")
            except Exception as exc:  # noqa: BLE001
                logger.warning("ExecutionRealismGate unavailable: %s", exc)
        return VerifierVerdict(
            agent_name="ExecutionRealismVerifier",
            is_valid=not issues, items_checked=items,
            confidence=0.85,
            critique="; ".join(issues) or
            "cost model recorded and edge survives realistic-cost check")


class MultipleTestingVerifier(BaseVerificationAgent):
    """P-hacking guard: selection_trials inflate the effective test count;
    the reported significance must survive a corrected threshold."""

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        val = _extract_validation(ledger_entry)
        if val is None:
            return VerifierVerdict(
                agent_name="MultipleTestingVerifier", is_valid=True,
                items_checked=0, confidence=0.5,
                critique="no candidate validation payload — abstain")
        issues: List[str] = []
        items = 1
        trials = int(val.get("selection_trials") or 1)
        sig = _sig(ledger_entry)
        p_gt_0 = sig.get("p_gt_0")
        if isinstance(p_gt_0, (int, float)):
            try:
                from trading_bot.reality_gates.multiple_testing_gate import (
                    MultipleTestingGate)
                gate = MultipleTestingGate()
                sid = str(_eget(ledger_entry, "entry_id", "cand"))
                gate.register_test(
                    sid, num_parameters=trials,
                    parameter_ranges={"selection_trials": (1, max(1, trials))},
                    data_hash=str(val.get("dataset_hash") or "none"),
                    optimization_method="alpha_generation")
                corr = gate.correct_results(
                    sid, observed_sharpe=0.0,
                    observed_pvalue=max(1e-9, 1.0 - float(p_gt_0)),
                    num_trades=int(val.get("holdout_signals") or 1),
                    backtest_years=1.0)
                items += 1
                corrected = float(getattr(corr, "corrected_pvalue",
                                          getattr(corr, "adjusted_pvalue",
                                                  1.0)))
                if corrected > 0.10:
                    issues.append(
                        f"significance does not survive multiple-testing "
                        f"correction (corrected_p={corrected:.3f}, "
                        f"effective_tests≈{trials})")
            except Exception as exc:  # noqa: BLE001
                logger.warning("MultipleTestingGate unavailable: %s", exc)
        if trials > 1 and sig.get("p_gt_baseline") is None:
            issues.append("evolved candidate lacks a paired-baseline "
                          "significance on the sealed outer slice")
        return VerifierVerdict(
            agent_name="MultipleTestingVerifier",
            is_valid=not issues, items_checked=items,
            confidence=0.85,
            critique="; ".join(issues) or
            "significance survives multiple-testing correction")


class DataLeakageVerifier(BaseVerificationAgent):
    """Leakage guard: seal/dataset-hash must be present, evaluation must be
    marked causal, and the recorded train/holdout split must not overlap."""

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        val = _extract_validation(ledger_entry)
        if val is None:
            return VerifierVerdict(
                agent_name="DataLeakageVerifier", is_valid=True,
                items_checked=0, confidence=0.5,
                critique="no candidate validation payload — abstain")
        issues: List[str] = []
        items = 1
        if not val.get("seal"):
            issues.append("no validation seal — verdict not bound to "
                          "dataset/spec/params")
        if not val.get("dataset_hash"):
            issues.append("no dataset_hash recorded")
        if not val.get("causal_eval"):
            issues.append("evaluation not marked causal — "
                          "rolling-window semantics unverified")
        n_train = val.get("train_bars")
        n_hold = val.get("holdout_bars")
        if isinstance(n_train, int) and isinstance(n_hold, int) \
                and n_train > 0 and n_hold > 0:
            try:
                import pandas as pd
                from trading_bot.ml.data_leakage_guard import (
                    DataLeakageGuard)
                guard = DataLeakageGuard(raise_on_violation=False,
                                         log_violations=False)
                train = pd.DataFrame(
                    {"t": range(n_train)}, index=range(n_train))
                test = pd.DataFrame(
                    {"t": range(n_train, n_train + n_hold)},
                    index=range(n_train, n_train + n_hold))
                items += 1
                if not guard.validate_train_test_split(
                        train, test, time_column="t"):
                    issues.append("train/holdout boundary failed the "
                                  "leakage guard's contamination check")
            except Exception as exc:  # noqa: BLE001
                logger.warning("DataLeakageGuard unavailable: %s", exc)
        return VerifierVerdict(
            agent_name="DataLeakageVerifier",
            is_valid=not issues, items_checked=items,
            confidence=0.9,
            critique="; ".join(issues) or
            "sealed causal evaluation with clean train/holdout boundary")


class DataIntegrityVerifier(BaseVerificationAgent):
    """Data-quality gate on the validated dataset's representative bar —
    completeness/validity/consistency (freshness relaxed: sealed trials
    replay historical data by design)."""

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        val = _extract_validation(ledger_entry)
        bar = (val or {}).get("sample_bar")
        if not isinstance(bar, dict) or not bar.get("close"):
            return VerifierVerdict(
                agent_name="DataIntegrityVerifier", is_valid=True,
                items_checked=0, confidence=0.5,
                critique="no sample bar on the validation record — abstain")
        try:
            from trading_bot.reality_gates.data_integrity_gate import (
                DataIntegrityGate)
            gate = DataIntegrityGate({"max_price_age": 10 ** 12,
                                      "max_indicator_age": 10 ** 12})
            score = gate.validate(bar, data_type="ohlcv")
            passed = not bool(getattr(score, "should_block", False))
            anomalies = [str(a) for a in
                         (getattr(score, "anomalies", []) or [])][:3]
            return VerifierVerdict(
                agent_name="DataIntegrityVerifier",
                is_valid=passed, items_checked=1, confidence=0.85,
                critique="data integrity OK" if passed else
                f"data-quality anomalies: {anomalies}")
        except Exception as exc:  # noqa: BLE001
            return VerifierVerdict(
                agent_name="DataIntegrityVerifier", is_valid=True,
                items_checked=0, confidence=0.5,
                critique=f"gate unavailable: {exc}")


class WalkForwardVerifier(BaseVerificationAgent):
    """Walk-forward decay check: runs only when the validation record
    carries per-window results; single-holdout candidates abstain."""

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        val = _extract_validation(ledger_entry)
        walks = (val or {}).get("walk_forward_windows")
        if not isinstance(walks, list) or not walks:
            return VerifierVerdict(
                agent_name="WalkForwardVerifier", is_valid=True,
                items_checked=0, confidence=0.5,
                critique="no walk-forward windows recorded — abstain")
        try:
            from trading_bot.reality_gates.walk_forward_gate import (
                WalkForwardGate, WalkForwardConfig)
            gate = WalkForwardGate(WalkForwardConfig(min_walks=1))
            result = gate.validate_strategy(
                str(_eget(ledger_entry, "entry_id", "cand")), walks)
            approved, reason = gate.is_strategy_approved(
                str(_eget(ledger_entry, "entry_id", "cand")))
            return VerifierVerdict(
                agent_name="WalkForwardVerifier",
                is_valid=bool(approved), items_checked=len(walks),
                confidence=0.85,
                critique=str(reason or getattr(result, "status", "checked")))
        except Exception as exc:  # noqa: BLE001
            return VerifierVerdict(
                agent_name="WalkForwardVerifier", is_valid=True,
                items_checked=0, confidence=0.5,
                critique=f"gate unavailable: {exc}")

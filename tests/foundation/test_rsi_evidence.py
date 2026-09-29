import asyncio
import copy
import json
import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from trading_bot.recursive_self_improvement.engine import RecursiveSelfImprovementEngine
from trading_bot.recursive_self_improvement.evaluation import EvaluationEngine
from trading_bot.recursive_self_improvement.memory import ImprovementMemory
from trading_bot.recursive_self_improvement import HumanGuidedRecursiveImprovementLoop, ImprovementDomain, ImprovementGenome, ImprovementPolicy


def signed(key, payload):
    return key.sign(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=True).encode()).hex()


def evidence_pair():
    operator = Ed25519PrivateKey.generate()
    verifier = Ed25519PrivateKey.generate()
    contract = {
        "schema_version": 1, "contract_id": "c1", "baseline_hash": "baseline-hash",
        "dataset_hash": "dataset-hash", "allowed_parameters": {"lookback": [2, 50]},
        "min_bars": 32, "min_instruments": 2, "block_size": 4, "max_trials": 2,
        "minimum_net_gain": 0.00001, "max_drawdown": 0.1,
        "max_drawdown_regression": 0.01, "confidence": 0.95,
        "max_cost_bps": 20, "max_latency_ms": 100, "max_exposure": 0.02,
        "max_cvar_95": 0.02, "train_end": -30, "validation_start": -20,
        "validation_end": -10, "holdout_start": 0, "holdout_end": 40,
        "cost_model_id": "independent-costs-v1", "code_hash": "unchanged-strategy-code",
        "dependencies_hash": "unchanged-dependencies", "max_turnover": 0.2,
        "expires_at": time.time() + 3600,
    }
    genome = ImprovementGenome(
        domain=ImprovementDomain.ALPHA_STRATEGY_DISCOVERY,
        objective="Higher cost-adjusted return without more drawdown",
        change_set={"lookback": 12}, evaluation_plan={"contract_id": "c1"},
        safety_constraints={}, parent_id="baseline-hash",
    )
    rows = []
    for symbol in ("EURUSD", "GBPUSD"):
        for i in range(40):
            rows.append({"symbol": symbol, "timestamp": i, "baseline_net": 0.0001,
                         "candidate_net": 0.0003, "baseline_gross": 0.00012,
                         "candidate_gross": 0.00032, "baseline_turnover": 0.1,
                         "candidate_turnover": 0.1, "cost_bps": 2, "baseline_exposure": 0.01,
                         "candidate_exposure": 0.01})
    report = {"schema_version": 1, "contract_id": "c1", "baseline_hash": "baseline-hash",
              "dataset_hash": "dataset-hash", "candidate_hash": genome.fingerprint,
              "trial_id": "trial-1", "trial_count": 1, "latency_ms": 5,
              "candidate_parameters": {"lookback": 12}, "bars": rows,
              "holdout_attested": True, "verifier_id": "external-reviewer",
              "cost_model_id": "independent-costs-v1", "code_hash": "unchanged-strategy-code",
              "dependencies_hash": "unchanged-dependencies", "risk_invariants_passed": True,
              "parameter_effect_verified": True, "issued_at": time.time(),
              "expires_at": contract["expires_at"], "nonce": "nonce-trial-1"}
    return operator, verifier, contract, genome, report


def evaluate(operator, verifier, contract, genome, report):
    return EvaluationEngine().evaluate_verified(
        genome, contract, signed(operator, contract), operator.public_key(),
        report, signed(verifier, report), verifier.public_key(),
    )


def test_missing_signatures_and_thresholds_fail_closed():
    operator, verifier, contract, genome, report = evidence_pair()
    assert EvaluationEngine().evaluate_verified(genome, contract, "", operator.public_key(),
                                                 report, signed(verifier, report), verifier.public_key())["status"] == "insufficient_evidence"
    del contract["minimum_net_gain"]
    assert evaluate(operator, verifier, contract, genome, report)["status"] == "insufficient_evidence"


def test_wrong_hash_and_replayed_trial_fail_closed():
    operator, verifier, contract, genome, report = evidence_pair()
    report["candidate_hash"] = "another-candidate"
    assert evaluate(operator, verifier, contract, genome, report)["status"] != "eligible_for_operator_review"
    report["candidate_hash"] = genome.fingerprint
    report["trial_count"] = 3
    assert evaluate(operator, verifier, contract, genome, report)["status"] != "eligible_for_operator_review"


def test_incomplete_transfer_costs_nan_and_protected_mutations_rejected():
    operator, verifier, contract, genome, report = evidence_pair()
    report["bars"] = [r for r in report["bars"] if r["symbol"] == "EURUSD"]
    assert evaluate(operator, verifier, contract, genome, report)["status"] == "insufficient_evidence"
    report["bars"][0]["cost_bps"] = float("nan")
    assert evaluate(operator, verifier, contract, genome, report)["status"] == "insufficient_evidence"
    report["bars"][0]["cost_bps"] = 2
    forbidden = copy.deepcopy(genome)
    object.__setattr__(forbidden, "change_set", {"max_exposure": 999})
    assert evaluate(operator, verifier, contract, forbidden, report)["status"] == "rejected"


def test_paired_verified_evidence_reports_full_vector_but_never_deploys():
    operator, verifier, contract, genome, report = evidence_pair()
    result = evaluate(operator, verifier, contract, genome, report)
    assert result["status"] == "eligible_for_operator_review"
    assert result["metrics"]["candidate_net_return"] > result["metrics"]["baseline_net_return"]
    assert result["metrics"]["candidate_max_drawdown"] == 0
    assert result["delta"]["net_return"] > 0
    report["bars"][0]["candidate_net"] = -0.5
    assert evaluate(operator, verifier, contract, genome, report)["status"] == "rejected"


@pytest.mark.asyncio
async def test_old_deployment_and_callback_promotion_disabled():
    engine = RecursiveSelfImprovementEngine(None, None, None, None)
    assert not await engine.deploy_improvement("strategy", {"name": "test", "parameters": {}, "hypothesis": "x"},
                                               {"experiment_id": "fake"})
    operator, verifier, contract, genome, report = evidence_pair()
    called = []
    loop = HumanGuidedRecursiveImprovementLoop(
        observer=lambda _: {}, proposer=lambda *_: [genome],
        evaluator=lambda *_: {"candidate_metrics": {"score": 900}, "safety_passed": True},
        approver=lambda *_: True, promoter=lambda *_: called.append(True),
        policy=ImprovementPolicy(dry_run=False),
    )
    decisions = await loop.run_cycle([genome.domain])
    assert decisions[0].status != "approved"
    assert not called


@pytest.mark.asyncio
async def test_signed_report_is_logged_once_and_never_invokes_promoter(tmp_path):
    operator, verifier, contract, genome, report = evidence_pair()
    promoted = []
    memory = ImprovementMemory(str(tmp_path / "experiments.db"))
    loop = HumanGuidedRecursiveImprovementLoop(
        observer=lambda _: {}, proposer=lambda *_: [genome],
        evaluator=lambda *_: {"report": report, "signature": signed(verifier, report)},
        approver=lambda *_: True, promoter=lambda *_: promoted.append(True),
        policy=ImprovementPolicy(dry_run=False), memory=memory,
        contract=contract, contract_signature=signed(operator, contract),
        operator_public_key=operator.public_key(), verifier_public_key=verifier.public_key(),
    )
    decision = (await loop.run_cycle([genome.domain]))[0]
    assert decision.status == "eligible_for_operator_review"
    assert not decision.approved
    assert promoted == []
    assert memory.get_recent_experiments()[0]["status"] == "eligible_for_operator_review"
    repeated = (await loop.run_cycle([genome.domain]))[0]
    assert repeated.status == "insufficient_evidence"
    assert promoted == []


def test_cost_arithmetic_and_zero_trade_cannot_game_evidence():
    operator, verifier, contract, genome, report = evidence_pair()
    report["bars"][0]["candidate_net"] += 0.01
    assert evaluate(operator, verifier, contract, genome, report)["status"] == "rejected"
    report["bars"][0]["candidate_net"] -= 0.01
    for row in report["bars"]:
        row["candidate_exposure"] = row["candidate_gross"] = row["candidate_net"] = 0
        row["candidate_turnover"] = 0
    assert evaluate(operator, verifier, contract, genome, report)["status"] != "eligible_for_operator_review"


@pytest.mark.asyncio
async def test_candidate_budget_applies_across_domains():
    evaluated = []
    loop = HumanGuidedRecursiveImprovementLoop(
        observer=lambda _: {},
        proposer=lambda domain, _: [ImprovementGenome(domain=domain, objective="bounded",
                                                        change_set={"lookback": 12},
                                                        evaluation_plan={}, safety_constraints={})],
        evaluator=lambda genome, _: evaluated.append(genome.genome_id) or {},
        policy=ImprovementPolicy(max_candidates_per_cycle=1),
    )
    await loop.run_cycle([ImprovementDomain.ALPHA_STRATEGY_DISCOVERY, ImprovementDomain.TRADING_POLICY])
    assert len(evaluated) == 1


def test_invalid_verifier_signature_and_contaminated_holdout_denied():
    operator, verifier, contract, genome, report = evidence_pair()
    impostor = Ed25519PrivateKey.generate()
    result = EvaluationEngine().evaluate_verified(
        genome, contract, signed(operator, contract), operator.public_key(),
        report, signed(impostor, report), verifier.public_key(),
    )
    assert result["status"] == "insufficient_evidence"
    result = EvaluationEngine().evaluate_verified(
        genome, contract, signed(operator, contract), operator.public_key(),
        report, signed(operator, report), operator.public_key(),
    )
    assert result["status"] == "insufficient_evidence"
    contract["holdout_start"] = contract["validation_end"]
    assert evaluate(operator, verifier, contract, genome, report)["status"] == "insufficient_evidence"


def test_protected_code_risk_failure_and_wrong_cost_model_denied():
    operator, verifier, contract, genome, report = evidence_pair()
    report["code_hash"] = "modified"
    assert evaluate(operator, verifier, contract, genome, report)["status"] == "rejected"
    report["code_hash"] = contract["code_hash"]
    report["risk_invariants_passed"] = False
    assert evaluate(operator, verifier, contract, genome, report)["status"] == "rejected"
    report["risk_invariants_passed"] = True
    report["cost_model_id"] = "untrusted"
    assert evaluate(operator, verifier, contract, genome, report)["status"] == "insufficient_evidence"
    report["cost_model_id"] = contract["cost_model_id"]
    report["expires_at"] = time.time() - 1
    assert evaluate(operator, verifier, contract, genome, report)["status"] == "insufficient_evidence"

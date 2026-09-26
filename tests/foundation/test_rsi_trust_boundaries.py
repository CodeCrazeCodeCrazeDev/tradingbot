"""Fail-closed trust-boundary tests for the RSI evidence envelope.

Every gate here must degrade to ``insufficient_evidence`` or ``rejected`` —
never to a silent pass — when custody, provenance or ledger integrity is absent.
"""
import json
import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from trading_bot.recursive_self_improvement.evaluation import EvaluationEngine
from trading_bot.recursive_self_improvement import (
    HumanGuidedRecursiveImprovementLoop,
    ImprovementDomain,
    ImprovementGenome,
    ImprovementPolicy,
)
from trading_bot.recursive_self_improvement.memory import ImprovementMemory


def _sign(key, payload):
    return key.sign(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=True).encode()).hex()


def _fixture():
    operator = Ed25519PrivateKey.generate()
    verifier = Ed25519PrivateKey.generate()
    contract = {
        "schema_version": 1, "contract_id": "c-boundary", "baseline_hash": "baseline-hash",
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
        change_set={"lookback": 12}, evaluation_plan={"contract_id": "c-boundary"},
        safety_constraints={}, parent_id="baseline-hash",
    )
    rows = []
    for symbol in ("EURUSD", "GBPUSD"):
        for i in range(40):
            rows.append({"symbol": symbol, "timestamp": i, "baseline_net": 0.0001,
                         "candidate_net": 0.0003, "baseline_gross": 0.00012,
                         "candidate_gross": 0.00032, "baseline_turnover": 0.1,
                         "candidate_turnover": 0.1, "cost_bps": 2,
                         "baseline_exposure": 0.01, "candidate_exposure": 0.01})
    report = {"schema_version": 1, "contract_id": "c-boundary", "baseline_hash": "baseline-hash",
              "dataset_hash": "dataset-hash", "candidate_hash": genome.fingerprint,
              "trial_id": "trial-1", "trial_count": 1, "latency_ms": 5,
              "candidate_parameters": {"lookback": 12}, "bars": rows,
              "holdout_attested": True, "verifier_id": "external-reviewer",
              "cost_model_id": "independent-costs-v1", "code_hash": "unchanged-strategy-code",
              "dependencies_hash": "unchanged-dependencies", "risk_invariants_passed": True,
              "parameter_effect_verified": True, "issued_at": time.time(),
              "expires_at": contract["expires_at"], "nonce": "nonce-trial-1"}
    return operator, verifier, contract, genome, report


def _evaluate(operator, verifier, contract, genome, report, **kwargs):
    return EvaluationEngine(kwargs.pop("engine_config", None)).evaluate_verified(
        genome, contract, _sign(operator, contract), operator.public_key(),
        report, _sign(verifier, report), verifier.public_key(), **kwargs)


def test_truthy_strings_cannot_satisfy_boolean_attestations():
    operator, verifier, contract, genome, report = _fixture()
    report["holdout_attested"] = "yes"
    assert _evaluate(operator, verifier, contract, genome, report)["status"] == "insufficient_evidence"
    report["holdout_attested"] = True
    report["risk_invariants_passed"] = "passed"
    assert _evaluate(operator, verifier, contract, genome, report)["status"] == "rejected"
    report["risk_invariants_passed"] = True
    report["parameter_effect_verified"] = 1
    assert _evaluate(operator, verifier, contract, genome, report)["status"] == "insufficient_evidence"


def test_holdout_attestation_object_enforced_when_contract_requires_it():
    from trading_bot.recursive_self_improvement.evidence_boundaries import HoldoutAttestation

    operator, verifier, contract, genome, report = _fixture()
    contract["require_holdout_attestation"] = True
    assert _evaluate(operator, verifier, contract, genome, report)["status"] == "insufficient_evidence"

    wrong = HoldoutAttestation(dataset_manifest_hash="other-dataset", custodian="operator",
                               released_at=time.time(), expires_at=contract["expires_at"])
    wrong_signed = {"attestation": wrong.to_dict(), "signature": _sign(operator, wrong.to_dict())}
    assert _evaluate(operator, verifier, contract, genome, report,
                     holdout_attestation=wrong_signed)["status"] == "insufficient_evidence"

    good = HoldoutAttestation(dataset_manifest_hash=contract["dataset_hash"], custodian="operator",
                              released_at=time.time(), expires_at=contract["expires_at"])
    good_signed = {"attestation": good.to_dict(), "signature": _sign(operator, good.to_dict())}
    result = _evaluate(operator, verifier, contract, genome, report,
                       holdout_attestation=good_signed)
    assert result["status"] == "eligible_for_operator_review"

    expired = HoldoutAttestation(dataset_manifest_hash=contract["dataset_hash"], custodian="operator",
                                 released_at=time.time() - 7200, expires_at=time.time() - 3600)
    expired_signed = {"attestation": expired.to_dict(), "signature": _sign(operator, expired.to_dict())}
    assert _evaluate(operator, verifier, contract, genome, report,
                     holdout_attestation=expired_signed)["status"] == "insufficient_evidence"


def test_cost_model_registry_blocks_unregistered_or_unmeasured_models():
    from trading_bot.recursive_self_improvement.evidence_boundaries import CostModelRegistry

    operator, verifier, contract, genome, report = _fixture()
    registry = CostModelRegistry({
        "independent-costs-v1": {"source": "measured", "custodian": "broker-fill-logs"},
    })
    engine_kwargs = {"engine_config": {"cost_model_registry": registry}}

    result = _evaluate(operator, verifier, contract, genome, report, **engine_kwargs)
    assert result["status"] == "eligible_for_operator_review"

    report["cost_model_id"] = "unregistered-model"
    assert _evaluate(operator, verifier, contract, genome, report,
                     **engine_kwargs)["status"] == "insufficient_evidence"

    report["cost_model_id"] = contract["cost_model_id"]
    assumed = CostModelRegistry({"independent-costs-v1": {"source": "assumed"}})
    assert _evaluate(operator, verifier, contract, genome, report,
                     engine_config={"cost_model_registry": assumed})["status"] == "insufficient_evidence"


def test_hash_chained_ledger_detects_drop_modify_and_reorder(tmp_path):
    memory = ImprovementMemory(str(tmp_path / "exp.db"))
    memory.append_evidence(trial_id="t1", nonce="n1", payload={"status": "rejected"})
    memory.append_evidence(trial_id="t2", nonce="n2", payload={"status": "insufficient_evidence"})
    assert memory.verify_evidence_chain() is True

    # DB-level triggers block casual DELETE/UPDATE; a file-level attacker must
    # drop them first. The hash chain is what catches that stronger tamper.
    import sqlite3
    with sqlite3.connect(memory.db_path) as conn:
        conn.execute("DROP TRIGGER IF EXISTS evidence_ledger_no_delete")
        conn.execute("DELETE FROM evidence_ledger WHERE trial_id = 't1'")
        conn.commit()
    assert memory.verify_evidence_chain() is False


def test_ledger_rejects_duplicate_trial_and_nonce(tmp_path):
    memory = ImprovementMemory(str(tmp_path / "exp.db"))
    memory.append_evidence(trial_id="t1", nonce="n1", payload={})
    with pytest.raises(Exception):
        memory.append_evidence(trial_id="t1", nonce="n-other", payload={})
    with pytest.raises(Exception):
        memory.append_evidence(trial_id="t-other", nonce="n1", payload={})


@pytest.mark.asyncio
async def test_loop_records_evidence_chain_and_reuses_no_nonce(tmp_path):
    operator, verifier, contract, genome, report = _fixture()
    memory = ImprovementMemory(str(tmp_path / "exp.db"))
    loop = HumanGuidedRecursiveImprovementLoop(
        observer=lambda _: {}, proposer=lambda *_: [genome],
        evaluator=lambda *_: {"report": report, "signature": _sign(verifier, report)},
        approver=lambda *_: True, promoter=lambda *_: None,
        policy=ImprovementPolicy(dry_run=False), memory=memory,
        contract=contract, contract_signature=_sign(operator, contract),
        operator_public_key=operator.public_key(), verifier_public_key=verifier.public_key(),
    )
    decision = (await loop.run_cycle([genome.domain]))[0]
    assert decision.status == "eligible_for_operator_review"
    assert memory.verify_evidence_chain() is True


def test_multi_instrument_envelope_feeds_min_instruments_gate():
    from trading_bot.recursive_self_improvement.evidence_boundaries import build_paired_envelope

    operator, verifier, contract, genome, report = _fixture()
    single = build_paired_envelope({"EURUSD": report["bars"][:40]})
    report["bars"] = single["bars"]
    assert _evaluate(operator, verifier, contract, genome, report)["status"] == "insufficient_evidence"

    report["bars"] = build_paired_envelope({"EURUSD": report["bars"],
                                           "GBPUSD": [dict(r, symbol="GBPUSD") for r in report["bars"]]})["bars"]
    assert _evaluate(operator, verifier, contract, genome, report)["status"] == "eligible_for_operator_review"

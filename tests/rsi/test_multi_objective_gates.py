"""Mission §17 gate tests: the v2 multi-objective evaluator accepts genuine
Pareto improvement and rejects the enumerated failure classes."""

from __future__ import annotations

import pytest

from trading_bot.recursive_self_improvement.contracts import (
    ContractError, contract_hash, validate_contract)
from trading_bot.recursive_self_improvement.multi_objective import (
    MultiObjectiveEvaluator, metric_vector, pareto_relation)

from tests.rsi.helpers import (  # noqa: E402  (tests/rsi on sys.path via rootdir config)
    fixture_bars, make_contract, make_frames, make_genome, make_report)


@pytest.fixture(scope="module")
def frames():
    return make_frames()


@pytest.fixture()
def contract(frames):
    return make_contract(frames)


def _eval(contract, genome, report, **kw):
    return MultiObjectiveEvaluator(contract).evaluate(
        genome, report, expected_contract_hash=contract_hash(contract), **kw)


# -- §17: a Pareto improvement can be promoted --------------------------------
def test_pareto_improvement_eligible_for_operator_review(contract, frames):
    genome = make_genome(contract)
    report = make_report(contract, genome, fixture_bars())
    verdict = _eval(contract, genome, report)
    assert verdict["status"] == "eligible_for_operator_review"
    assert verdict["promotion_eligible"] is False
    assert verdict["metrics"]["pareto_relation"] == "dominates"


# -- §17: profitable but catastrophically riskier candidate is rejected -------
def test_profitable_but_riskier_rejected(contract):
    # net-positive (+0.005/bar) but with -0.04 tail losses -> risk bound breach
    pattern = [0.02 if i % 4 else -0.04 for i in range(64)]
    tight = dict(contract, max_cvar_95=0.01, max_drawdown=0.03)
    bars = fixture_bars(candidate_net=0.001, candidate_pattern=pattern)
    genome = make_genome(tight)
    report = make_report(tight, genome, bars)
    verdict = _eval(tight, genome, report)
    assert verdict["status"] == "rejected"
    assert "risk" in verdict["reason"] or "drawdown" in verdict["reason"] \
        or "gaming" in verdict["reason"] or "exposure" in verdict["reason"]


# -- §17: statistically insignificant improvement is rejected -----------------
def test_insignificant_improvement_insufficient(contract):
    # near-zero mean difference with high per-bar variance -> CI lower <= 0
    # (period-3 diffs so block bootstrap sees genuine spread)
    base = [0.0001 if i % 4 else -0.0002 for i in range(64)]
    diffs = [[0.003, -0.003, 0.0002][i % 3] for i in range(64)]
    pattern = [b + d for b, d in zip(base, diffs)]
    pattern = [b + d for b, d in zip(base, diffs)]
    bars = fixture_bars(baseline_pattern=base, candidate_pattern=pattern)
    genome = make_genome(contract)
    verdict = _eval(contract, genome, make_report(contract, genome, bars))
    assert verdict["status"] in ("insufficient_evidence", "rejected")


# -- §17: candidate with no effect is rejected ---------------------------------
def test_no_change_rejected(contract):
    shared = [0.0002 if i % 4 else -0.0001 for i in range(64)]
    bars = fixture_bars(baseline_pattern=shared, candidate_pattern=shared)
    genome = make_genome(contract)
    verdict = _eval(contract, genome, make_report(contract, genome, bars))
    assert verdict["status"] == "rejected"
    assert "no change" in verdict["reason"]


# -- §17: Pareto-dominated candidate is rejected --------------------------------
def test_pareto_dominated_rejected(contract):
    # candidate wins net but loses every risk objective
    pattern = [0.004 if i % 3 else -0.05 for i in range(64)]
    bars = fixture_bars(candidate_pattern=pattern, turnover=0.02)
    genome = make_genome(contract)
    verdict = _eval(contract, genome, make_report(contract, genome, bars))
    assert verdict["status"] == "rejected"


# -- §17: missing attestation -> insufficient evidence -------------------------
def test_missing_attestation_insufficient(contract):
    genome = make_genome(contract)
    report = make_report(contract, genome, fixture_bars(), holdout_attested=False)
    verdict = _eval(contract, genome, report)
    assert verdict["status"] == "insufficient_evidence"


# -- §17: regression budget breach rejected ------------------------------------
def test_regression_budget_breach_rejected():
    frames = make_frames()
    contract = make_contract(frames, regression_budgets={"sharpe": 0.0, "net_return": 0.0})
    # candidate net improves but sharpe regresses massively
    pattern = [0.02 if i % 2 == 0 else -0.017 for i in range(64)]
    bars = fixture_bars(candidate_pattern=pattern)
    genome = make_genome(contract)
    verdict = _eval(contract, genome, make_report(contract, genome, bars))
    assert verdict["status"] == "rejected"


# -- §17: contract mutation mid-experiment rejected -----------------------------
def test_contract_mutation_rejected(contract):
    genome = make_genome(contract)
    report = make_report(contract, genome, fixture_bars())
    verdict = MultiObjectiveEvaluator(contract).evaluate(
        genome, report, expected_contract_hash="deadbeef")
    assert verdict["status"] == "rejected"
    assert "mutated" in verdict["reason"]


# -- §17: trial budget enforced -------------------------------------------------
def test_trial_budget_rejected(contract):
    genome = make_genome(contract)
    report = make_report(contract, genome, fixture_bars(), trial_count=99)
    verdict = _eval(contract, genome, report)
    assert verdict["status"] == "rejected"
    assert "trial" in verdict["reason"]


def test_holdout_query_budget_rejected(contract):
    genome = make_genome(contract)
    report = make_report(contract, genome, fixture_bars())
    verdict = _eval(contract, genome, report, holdout_queries_used=999)
    assert verdict["status"] == "rejected"


# -- §17: risk parameter cannot be self-modified --------------------------------
def test_risk_parameter_change_rejected(contract):
    genome = make_genome(contract, param="max_cvar_95", value=0.9)
    report = make_report(contract, genome, fixture_bars(),
                         candidate_parameters={"max_cvar_95": 0.9})
    verdict = _eval(contract, genome, report)
    assert verdict["status"] == "rejected"


# -- schema-2 contract validation ----------------------------------------------
def test_contract_requires_all_keys(frames):
    c = make_contract(frames)
    del c["pareto_objectives"]
    with pytest.raises(ContractError):
        validate_contract(c)


def test_contract_rejects_unregistered_pareto_metric(frames):
    c = make_contract(frames, pareto_objectives=["vibes"])
    with pytest.raises(ContractError):
        validate_contract(c)


def test_metric_vector_and_pareto_relation():
    mv = metric_vector([0.001] * 50, turnover=1.0, exposures=[0.01] * 50,
                       directions=[1] * 50)
    assert mv["net_return"] > 0 and mv["max_drawdown"] == 0.0
    assert mv["n_trades"] == 1.0
    mb = metric_vector([0.0005] * 50, turnover=1.0, exposures=[0.01] * 50,
                       directions=[1] * 50)
    assert pareto_relation(mv, mb, ["net_return", "max_drawdown"]) == "dominates"
    assert pareto_relation(mb, mv, ["net_return", "max_drawdown"]) == "dominated"

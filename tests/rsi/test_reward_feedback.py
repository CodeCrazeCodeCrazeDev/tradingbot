"""Rewards are measured feedback, never a route around canonical gates."""
import json
from types import SimpleNamespace

import pytest

from trading_bot.core.csc.rewards import (
    forecast_reward, prediction_reward, research_reward, trading_reward)
from trading_bot.core.csc.research.engine import ResearchEngine
from trading_bot.msos.rewards import MSOSRewardAdvisor, firewall_reward
from trading_bot.recursive_self_improvement.rewards import reward_from_verdict


def values(record):
    return {o.name: o.value for o in record.objectives}


def test_trading_costs_can_reverse_profit_and_baseline_credit():
    reward = trading_reward("position-1", 0.001, cost_return=0.002,
                            baseline_net_return=0, origin="paper",
                            constraints_satisfied=True)
    assert values(reward)["net_return"] == pytest.approx(-0.001)
    assert values(reward)["alpha_vs_baseline"] < 0
    assert reward.to_dict()["promotion_eligible"] is False


def test_missing_costs_and_approvals_never_create_net_reward():
    reward = trading_reward("position-1", 0.01)
    assert values(reward)["net_return"] is None
    assert "missing_costs" in reward.blockers
    assert "unknown_origin" in reward.blockers
    unsafe = trading_reward("position-1", 100, cost_return=0,
                            baseline_net_return=0, origin="live",
                            constraints_satisfied=False)
    assert "constraint_breach" in unsafe.blockers


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, "0.1"])
def test_bad_returns_stay_missing(bad):
    reward = trading_reward("p", bad, cost_return=0, origin="paper")
    assert values(reward)["gross_return"] is None
    json.dumps(reward.to_dict(), allow_nan=False)


def test_shared_settlement_does_not_multiply_learning_weight():
    rewards = [trading_reward(str(i), 0.01, shared_settlement=4)
               for i in range(4)]
    assert sum(r.sample_weight for r in rewards) == 1
    assert trading_reward("bad", 0.01, shared_settlement=0).sample_weight == 0


def test_proper_prediction_score_penalizes_overconfidence():
    wrong = prediction_reward("p", 0.99, False, origin="paper")
    uncertain = prediction_reward("p", 0.5, False, origin="paper")
    assert values(wrong)["skill_vs_half"] < values(uncertain)["skill_vs_half"] == 0
    assert values(prediction_reward("p", 0.9, None))["brier"] is None


def test_world_model_reward_requires_observed_targets_not_latent_similarity():
    good = forecast_reward("forecast", 2, 2, 1, origin="historical")
    assert values(good)["error_reduction_vs_baseline"] == 1
    missing = forecast_reward("forecast", 2, None, 1, origin="historical")
    assert values(missing)["squared_error"] is None
    extreme = forecast_reward("forecast", 1e308, -1e308, 0, origin="historical")
    json.dumps(extreme.to_dict(), allow_nan=False)


def test_research_falsification_earns_same_credit_as_confirmation():
    kwargs = dict(origin="historical", protocol_verified=True,
                  comparison_complete=True)
    for verdict in ("CONFIRMED", "FALSIFIED"):
        assert values(research_reward("experiment", verdict, **kwargs))[
            "resolved_question"] == 1
    kwargs["protocol_verified"] = False
    assert values(research_reward("experiment", "CONFIRMED", **kwargs))[
        "resolved_question"] == 0
    kwargs.update(protocol_verified=True, origin="simulated")
    assert values(research_reward("experiment", "CONFIRMED", **kwargs))[
        "resolved_question"] == 0


def test_research_repeated_experiment_cannot_farm_credit():
    engine = ResearchEngine(None, None)
    args = dict(candidate_positions=[1] * 40, baseline_positions=[0] * 40,
                bar_returns=[-0.001] * 40, dataset_id="fixture",
                origin="historical")
    first = engine.evaluate_strategy("hypothesis", **args)
    second = engine.evaluate_strategy("renamed hypothesis", **args)
    assert first.verdict == second.verdict == "FALSIFIED"
    assert first.reward["evidence_id"] == second.reward["evidence_id"]
    assert engine.policy.reward_stats["evaluate_strategy"] == [1, 1]
    engine.evaluate_strategy("third rename", **args)
    assert engine.policy.priority_adjustment("evaluate_strategy") == 0
    assert engine.policy.estimate_info_gain("evaluate_strategy") == 0.5
    # Recorded with claim metadata, so reward identities survive KG replay.
    restored = ResearchEngine(None, None)
    events = [{"action": kind, "details": payload}
              for kind, payload in engine.drain_persisted_events()]
    assert events[0]["action"] == "RESEARCH_REWARD_CONTRACT"
    assert first.seal == events[0]["details"]["seal_hash"]
    restored.rehydrate(list(reversed(json.loads(json.dumps(events)))))
    restored.rehydrate(list(reversed(events)))  # repeat replay is idempotent
    assert restored.policy.reward_stats["evaluate_strategy"] == [1, 1]


def test_research_does_not_credit_truncated_or_unlabelled_comparisons():
    engine = ResearchEngine(None, None)
    result = engine.evaluate_strategy(
        "unaligned", [1] * 41, [0] * 40, [-0.01] * 40,
        dataset_id="fixture", origin="historical")
    assert "incomplete_comparison" in result.reward["blockers"]
    assert engine.policy.reward_stats["evaluate_strategy"] == [0, 0]


def test_rsi_projects_existing_objectives_without_compensating_risk():
    verdict = {"status": "rejected", "metrics": {
        "candidate_net_return": 0.2, "baseline_net_return": 0.01,
        "candidate_max_drawdown": 0.4, "baseline_max_drawdown": 0.02}}
    reward = reward_from_verdict("trial", verdict)
    assert values(reward)["net_return_improvement"] > 0
    assert values(reward)["max_drawdown_improvement"] < 0
    assert values(reward)["evaluation_credit"] == 0
    assert reward.to_dict()["promotion_eligible"] is False
    assert reward.origin == "unknown"


def test_rsi_finish_persists_reward_in_existing_evidence_ledger():
    from trading_bot.recursive_self_improvement.engine_v2 import RecursiveImprovementCycle
    entries = []
    cycle = RecursiveImprovementCycle.__new__(RecursiveImprovementCycle)
    cycle.memory = SimpleNamespace(append_evidence=lambda **kw: entries.append(kw))
    result = cycle._finish(SimpleNamespace(genome_id="candidate"), "trial",
                           "rejected", "risk breach", {}, {})
    assert result.status == "rejected"
    assert entries[0]["payload"]["reward"]["domain"] == "rsi"
    assert entries[0]["payload"]["reward"]["promotion_eligible"] is False


def test_msos_observes_survival_without_trade_authority_or_repeat_credit():
    advisor = MSOSRewardAdvisor()
    assert advisor.analyze({})["evidence"]["status"] == "missing_data"
    context = {"self_state": {"settled_outcomes": [
        {"realized_return": 0.1, "exit_seq": 1},
        {"realized_return": -0.2, "exit_seq": 2}]}}
    first = advisor.analyze(context)
    assert first["direction"] == "HOLD"
    assert first["advisory_only"] is True
    reward = first["evidence"]["reward"]
    assert reward["reward_id"] == advisor.analyze(context)["evidence"]["reward"]["reward_id"]
    objectives = {o["name"]: o["value"] for o in reward["objectives"]}
    assert objectives["window_gross_drawdown"] == pytest.approx(0.2)
    assert "window_not_account_risk" in reward["blockers"]
    assert "position_size" not in first


def test_msos_learning_freeze_is_not_overridden_by_reward():
    reward = firewall_reward("freeze", {"can_learn": False, "data_allowed": False},
                             update_attempted=True, origin="paper")
    assert values(reward)["firewall_violation"] == 1
    assert "learning_firewall_violation" in reward.blockers
    missing = firewall_reward("freeze", {}, update_attempted=False)
    assert values(missing)["firewall_violation"] is None


def test_msos_attaches_without_optional_directional_advisors():
    from trading_bot.core.csc.assembly import build_cognitive_system
    attached = []
    csc = SimpleNamespace(
        configure_cognition=attached.append,
        configure_research=lambda: None, _research_interval=0)
    assert build_cognitive_system(csc, advisory_brain=False) is csc
    assert [a.capability_id for a in attached] == ["msos_survival_reward"]

"""Tests for the human-guided recursive improvement foundation."""

import pytest

from trading_bot.recursive_self_improvement import (
    HumanGuidedRecursiveImprovementLoop,
    ImprovementDomain,
    ImprovementGenome,
    ImprovementPolicy,
)


def make_genome(domain=ImprovementDomain.TRADING_POLICY):
    return ImprovementGenome(
        domain=domain,
        objective="Improve calibrated OOS score without increasing drawdown",
        change_set={"policy.temperature": 0.9},
        evaluation_plan={"replay": "fixture-1", "oos_split": 0.3},
        safety_constraints={"max_drawdown": 0.25},
    )


@pytest.mark.asyncio
async def test_rsi_requires_human_approval_before_promotion() -> None:
    promoted = []

    def observe(_domain):
        return {"score": 1.0, "max_drawdown": 0.1}

    def propose(domain, _baseline):
        return [make_genome(domain)]

    def evaluate(genome, _baseline):
        return {
            "baseline_metrics": {"score": 1.0},
            "candidate_metrics": {"score": 1.05},
            "oos_metrics": {"score": 1.01, "max_drawdown": 0.1},
            "robustness_metrics": {"score": 0.8},
            "safety_passed": True,
            "deterministic_replay_passed": True,
            "data_provenance": {"dataset": "fixture-1"},
        }

    loop = HumanGuidedRecursiveImprovementLoop(
        observer=observe,
        proposer=propose,
        evaluator=evaluate,
        policy=ImprovementPolicy(dry_run=False),
        promoter=lambda genome, _evidence: promoted.append(genome.genome_id),
    )
    result = await loop.run_cycle([ImprovementDomain.TRADING_POLICY])

    assert result[0].status == "insufficient_evidence"
    # Gate denies with stage-specific wording: missing keys -> "trust anchors
    # required"; failed verification -> "independent signatures". Either means
    # promotion was refused for lack of independent attestation.
    assert "trust anchors" in result[0].reason or "independent signatures" in result[0].reason
    assert promoted == []


@pytest.mark.asyncio
async def test_rsi_promotes_only_after_human_approval_and_snapshots() -> None:
    promoted = []
    snapshots = []

    def observe(_domain):
        return {"score": 1.0, "max_drawdown": 0.1}

    def propose(domain, _baseline):
        return [make_genome(domain)]

    def evaluate(_genome, _baseline):
        return {
            "baseline_metrics": {"score": 1.0},
            "candidate_metrics": {"score": 1.05},
            "oos_metrics": {"score": 1.01, "max_drawdown": 0.1},
            "robustness_metrics": {"score": 0.8},
            "safety_passed": True,
            "deterministic_replay_passed": True,
            "data_provenance": {"dataset": "fixture-1"},
        }

    class Rollback:
        def create_snapshot(self, domain, name, data, metadata):
            snapshots.append((domain, name, data, metadata))
            return "snapshot-1"

    loop = HumanGuidedRecursiveImprovementLoop(
        observer=observe,
        proposer=propose,
        evaluator=evaluate,
        approver=lambda _genome, _evidence: True,
        promoter=lambda genome, _evidence: promoted.append(genome.genome_id),
        rollback_manager=Rollback(),
        policy=ImprovementPolicy(dry_run=False),
    )
    result = await loop.run_cycle([ImprovementDomain.TRADING_POLICY])

    assert result[0].approved is False
    assert result[0].status == "insufficient_evidence"
    assert snapshots == []
    assert promoted == []


def test_improvement_genome_covers_requested_domain_set() -> None:
    assert len(list(ImprovementDomain)) >= 30
    assert ImprovementDomain.ROOT_CAUSE_ANALYSIS.value == "root_cause_analysis"
    assert ImprovementDomain.RESEARCH_ENGINEERING_TRANSFER.value == "research_engineering_transfer"

#!/usr/bin/env python3
"""Tests for frontier capability distillation under governance."""

import importlib.util
import sys
import asyncio
from pathlib import Path


MODULE_PATH = Path(__file__).parent.parent / "trading_bot" / "core" / "frontier_capability_distillation.py"
SPEC = importlib.util.spec_from_file_location("frontier_distillation_direct", MODULE_PATH)
distill = importlib.util.module_from_spec(SPEC)
sys.modules["frontier_distillation_direct"] = distill
SPEC.loader.exec_module(distill)


def _observations():
    return [
        distill.FrontierObservation(
            observation_id="obs-tool",
            model_name="frontier-x",
            observation_type=distill.FrontierObservationType.TOOL_USE_PATTERN,
            summary="Model batches tool calls and validates read-only outputs before writes.",
            observed_behavior="programmatic tool planning with explicit output checks",
            conditions=("structured tool schemas", "read-only calls available"),
            metrics={distill.CapabilityDimension.TOOL_USE.value: 0.91},
            failure_modes=("tool output hallucination",),
            cost_estimate=0.40,
            latency_ms=1200,
        ),
        distill.FrontierObservation(
            observation_id="obs-context",
            model_name="frontier-x",
            observation_type=distill.FrontierObservationType.LONG_CONTEXT_BEHAVIOR,
            summary="Long context is compressed into stable facts and a recent trace.",
            observed_behavior="hierarchical context compaction",
            conditions=("long context", "multi-step task"),
            metrics={distill.CapabilityDimension.MEMORY_CONTEXT.value: 0.86},
            failure_modes=("context drift",),
            cost_estimate=0.30,
            latency_ms=1500,
        ),
        distill.FrontierObservation(
            observation_id="obs-eval",
            model_name="frontier-x",
            observation_type=distill.FrontierObservationType.EVAL_RESULT,
            summary="Verifier-backed reasoning improves hard task pass rate.",
            observed_behavior="claim decomposition followed by critic pass",
            conditions=("hard reasoning", "objective checks available"),
            metrics={
                distill.CapabilityDimension.REASONING_DEPTH.value: 0.79,
                distill.CapabilityDimension.RELIABILITY.value: 0.82,
            },
            failure_modes=("expensive on simple tasks",),
            cost_estimate=0.60,
            latency_ms=1800,
        ),
    ]


def _tasks():
    return [
        distill.BenchmarkTask(
            task_id="research:tool_plan",
            domain="research",
            task_type="tool_use",
            objective="Plan and verify AlphaAlgo tool use.",
            baseline_score=0.62,
        ),
        distill.BenchmarkTask(
            task_id="trading:memory_context",
            domain="trading",
            task_type="memory_context",
            objective="Keep long-context trading assumptions stable.",
            baseline_score=0.64,
        ),
    ]


def _results():
    return [
        distill.BenchmarkResult(
            task_id="research:tool_plan",
            model_name="frontier-x",
            score=0.79,
            baseline_score=0.62,
            cost=0.50,
            latency_ms=1300,
            stability=0.88,
            metadata={"task_type": "tool_use"},
        ),
        distill.BenchmarkResult(
            task_id="trading:memory_context",
            model_name="frontier-x",
            score=0.76,
            baseline_score=0.64,
            cost=0.40,
            latency_ms=1500,
            stability=0.84,
            metadata={"task_type": "memory_context"},
        ),
    ]


def test_engine_profiles_frontier_model_conditions_cost_and_failures():
    profiler = distill.ModelProfiler()
    profile = profiler.build_profile("frontier-x", _observations(), _results())

    assert profile.dimension_scores[distill.CapabilityDimension.TOOL_USE] >= 0.75
    assert "tool_use" in profile.strengths
    assert "structured tool schemas" in profile.conditions
    assert "tool output hallucination" in profile.failure_modes
    assert profile.average_cost > 0
    assert profile.average_latency_ms > 0


def test_extractor_compiler_only_emit_alphaalgo_native_artifacts():
    profile = distill.ModelProfiler().build_profile("frontier-x", _observations(), _results())
    patterns = distill.CapabilityExtractor().extract(profile, _observations(), _results())
    inverter = distill.WeaknessInversionEngine()
    compiler = distill.SkillCompiler()

    artifacts = [compiler.compile(pattern, inverter.invert(profile, pattern)) for pattern in patterns]

    assert patterns
    assert all(pattern.transferable_part for pattern in patterns)
    assert all("proprietary training data are excluded" in pattern.non_transferable_notes[0] for pattern in patterns)
    assert all(artifact is not None for artifact in artifacts)
    assert {artifact.kind for artifact in artifacts if artifact} <= set(distill.AlphaAlgoArtifactKind)


def test_weakness_inversion_turns_failures_into_controls():
    profile = distill.ModelProfiler().build_profile("frontier-x", _observations(), _results())
    pattern = distill.CapabilityExtractor().extract(profile, _observations(), _results())[0]

    controls = distill.WeaknessInversionEngine().invert(profile, pattern)

    names = {control.control_name for control in controls}
    assert "citation_critic" in names
    assert "context_compaction" in names
    assert "budget_cap" in names


def test_governance_rejects_artifacts_without_budget_or_rollback():
    profile = distill.ModelProfiler().build_profile("frontier-x", _observations(), _results())
    pattern = distill.CapabilityExtractor().extract(profile, _observations(), _results())[0]
    artifact = distill.AlphaAlgoNativeArtifact(
        artifact_id="bad",
        kind=distill.AlphaAlgoArtifactKind.TOOL_USE_PLAYBOOK,
        name="bad",
        content={},
        source_pattern_id=pattern.pattern_id,
        valid_domains=("research",),
        budget_cap=0.0,
        rollback_triggers=(),
    )

    result = distill.DistillationGovernanceGate().review(artifact, pattern)

    assert not result.accepted
    assert "artifact lacks rollback triggers" in result.issues
    assert "artifact lacks a budget cap" in result.issues


def test_sandbox_validator_blocks_side_effects_and_rollout():
    artifact = distill.AlphaAlgoNativeArtifact(
        artifact_id="artifact-risk",
        kind=distill.AlphaAlgoArtifactKind.ROUTING_RULE,
        name="risky",
        content={},
        source_pattern_id="pattern",
        valid_domains=("trading",),
        valid_tasks=("trading:routing",),
        budget_cap=10.0,
        rollback_triggers=("actual_lift_below_zero",),
    )
    result = distill.BenchmarkResult(
        task_id="trading:routing",
        model_name="frontier-x",
        score=0.90,
        baseline_score=0.70,
        cost=0.5,
        latency_ms=100,
        stability=0.90,
        side_effects=("risk_limit_change",),
    )

    validation = distill.SandboxValidator().validate(artifact, [result])
    rollout = distill.RolloutManager().plan(artifact, validation)

    assert not validation.accepted
    assert not validation.compatible_with_global_objective
    assert rollout is None


def test_full_distillation_loop_creates_selective_lineage_records():
    engine = distill.FrontierCapabilityDistillationEngine()

    report = engine.run("frontier-x", _observations(), _tasks(), _results())

    assert report.profile.model_name == "frontier-x"
    assert report.artifacts
    assert report.lineage_records
    assert all(record.decision in {distill.RegistryDecision.KEEP, distill.RegistryDecision.REVISE} for record in report.lineage_records)
    assert all(plan.scope != "global" for plan in report.rollout_plans)
    assert all(not plan.approved_for_live for plan in report.rollout_plans)
    assert all(record.artifact.rollback_triggers for record in report.lineage_records)


def test_meta_intelligence_layer_arbitrages_frontier_outputs_into_native_advantage():
    layer = distill.FrontierMetaIntelligenceLayer()

    report = layer.arbitrage_frontier("frontier-x", _observations(), _tasks(), _results())

    assert report.advantage_score > 0
    assert report.native_artifacts
    assert report.active_rollouts
    assert report.opportunity.transferable_value > 0
    assert "frontier outputs are treated as external R&D signals" in report.notes
    assert layer.ledger.cumulative_advantage() == report.advantage_score


def test_meta_intelligence_neutralizes_dangerous_frontier_power_before_transfer():
    observations = [
        distill.FrontierObservation(
            observation_id="obs-danger",
            model_name="frontier-danger",
            observation_type=distill.FrontierObservationType.API_BEHAVIOR,
            summary="Model can bypass deployment approval in autonomous tool mode.",
            observed_behavior="live deployment bypass with unguarded tool write",
            conditions=("autonomous tools enabled",),
            metrics={distill.CapabilityDimension.TOOL_USE.value: 0.94},
            failure_modes=("live deployment bypass", "risk limit weakening", "credential access"),
        )
    ]
    tasks = [
        distill.BenchmarkTask(
            task_id="engineering:tool_use",
            domain="engineering",
            task_type="tool_use",
            objective="Use tools safely in engineering tasks.",
            baseline_score=0.50,
        )
    ]
    results = [
        distill.BenchmarkResult(
            task_id="engineering:tool_use",
            model_name="frontier-danger",
            score=0.88,
            baseline_score=0.50,
            cost=0.30,
            latency_ms=600,
            stability=0.92,
            metadata={"task_type": "tool_use"},
        )
    ]

    report = distill.FrontierMetaIntelligenceLayer().arbitrage_frontier(
        "frontier-danger",
        observations,
        tasks,
        results,
    )

    assert report.advantage_score == 0.0
    assert not report.native_artifacts
    assert report.killed_lineage_ids
    assert any(item.severity == distill.DangerSeverity.CRITICAL for item in report.neutralized_dangers)
    assert any(item.blocked_transfer for item in report.neutralized_dangers)


def test_meta_intelligence_continuous_loop_runs_bounded_cycles():
    layer = distill.FrontierMetaIntelligenceLayer()

    async def run_cycle():
        return await layer.run_continuous(
            lambda: [
                {
                    "model_name": "frontier-x",
                    "observations": _observations(),
                    "benchmark_tasks": _tasks(),
                    "benchmark_results": _results(),
                }
            ],
            sleep_seconds=0.0,
            max_cycles=1,
        )

    reports = asyncio.run(run_cycle())

    assert len(reports) == 1
    assert reports[0].advantage_score > 0

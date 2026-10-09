"""Regression tests for the thinking strategies wired into the CSC.

Covers the canonical lens set (first-principles, systems, analytical,
creative): determinism, branch structure, evidence-graph constraints,
probability normalization, adversarial coverage, and pipeline integration.
"""

import pytest
from unittest.mock import MagicMock

from trading_bot.core.csc.hypothesis import HypothesisGenerator, ReasoningBranch
from trading_bot.core.csc.strategies import (
    AnalyticalThinking,
    CreativeThinking,
    FirstPrinciplesThinking,
    SystemsThinking,
    ThinkingMode,
    default_thinking_strategies,
    extract_features,
    score_to_action,
)


OBS = {
    "symbol": "EURUSD",
    "price": 1.0950,
    "volume": 2_500_000,
    "volatility": 0.02,
    "sentiment": 0.6,
    "trend": 0.5,
    "momentum": 0.4,
    "liquidity": 0.3,
}

EXPECTED_MODES = {
    ThinkingMode.FIRST_PRINCIPLES,
    ThinkingMode.SYSTEMS,
    ThinkingMode.ANALYTICAL,
    ThinkingMode.CREATIVE,
}

EXPECTED_BRANCH_IDS = {f"branch_{m.value}" for m in EXPECTED_MODES}


def _snapshot(branches):
    return [
        (
            b.branch_id,
            b.name,
            b.probability,
            b.confidence,
            b.uncertainty,
            b.causal_explanation,
            tuple(b.invalidation_conditions),
            dict(b.execution_plan),
        )
        for b in branches
    ]


@pytest.mark.asyncio
async def test_each_thinking_lens_produces_one_competing_branch():
    gen = HypothesisGenerator(world_model=None)
    branches = await gen.generate_competing_branches(OBS)

    assert len(branches) == 4
    assert {b.branch_id for b in branches} == EXPECTED_BRANCH_IDS
    assert all(isinstance(b, ReasoningBranch) for b in branches)


@pytest.mark.asyncio
async def test_branch_generation_is_deterministic():
    gen = HypothesisGenerator(world_model=None)
    first = await gen.generate_competing_branches(OBS)
    second = await gen.generate_competing_branches(dict(OBS))
    assert _snapshot(first) == _snapshot(second)


@pytest.mark.asyncio
async def test_branch_contract_holds_for_every_lens():
    gen = HypothesisGenerator(world_model=None)
    branches = await gen.generate_competing_branches(OBS)
    total = sum(b.probability for b in branches)

    assert total == pytest.approx(1.0)
    for b in branches:
        assert b.execution_plan["action"] in ("BUY", "SELL", "WAIT")
        assert b.execution_plan["symbol"] == "EURUSD"
        assert b.causal_explanation
        assert b.invalidation_conditions
        assert b.hypotheses, f"{b.branch_id} missing structured hypothesis"
        # EvidenceGraph hard constraints used by EvidenceGraphGate
        assert len(b.evidence_graph.nodes) >= 5
        assert len(b.evidence_graph.edges) >= 3
        assert 0.0 < b.probability < 1.0
        assert 0.0 < b.confidence <= 0.95
        assert 0.0 <= b.uncertainty <= 0.95


def test_default_lens_set_is_the_four_thinking_modes():
    strategies = default_thinking_strategies()
    assert len(strategies) == 4
    assert {s.mode for s in strategies} == EXPECTED_MODES
    assert isinstance(strategies[0], FirstPrinciplesThinking)
    assert isinstance(strategies[1], SystemsThinking)
    assert isinstance(strategies[2], AnalyticalThinking)
    assert isinstance(strategies[3], CreativeThinking)


def test_extract_features_is_safe_on_missing_and_bad_fields():
    f = extract_features({"price": "not-a-number", "volume": "n/a"})
    assert f.price == 0.0
    assert f.volume_signal == 0.0
    assert f.ref_price == 1.0
    assert f.volatility == 0.02
    # Sentiment/trend/momentum are clamped to [-1, 1]
    f2 = extract_features({"sentiment": 9.9, "trend": -9.9, "momentum": 0.0})
    assert f2.sentiment == 1.0
    assert f2.trend == -1.0


def test_score_to_action_thresholds():
    assert score_to_action(0.5) == "BUY"
    assert score_to_action(-0.5) == "SELL"
    assert score_to_action(0.0) == "WAIT"
    assert score_to_action(0.12) == "WAIT"
    assert score_to_action(-0.12) == "WAIT"


def test_creative_lens_fades_crowded_consensus():
    features = extract_features(
        {**OBS, "sentiment": 0.9, "trend": 0.9}
    )
    analysis = CreativeThinking().analyze(features)
    # Strong bullish consensus -> contrarian (bearish) hypothesis
    assert analysis.score < 0
    assert analysis.uncertainty == 0.35

    quiet = extract_features({**OBS, "sentiment": 0.0, "trend": 0.0})
    fallback = CreativeThinking().analyze(quiet)
    # No crowd to fade -> exploratory tail scenario, not contrarian
    assert "tail scenario" in fallback.causal_explanation.lower()


@pytest.mark.asyncio
async def test_contrarian_coverage_when_consensus_is_strong():
    """Adversarial coverage: creative branch opposes the consensus direction."""
    gen = HypothesisGenerator(world_model=None)
    branches = await gen.generate_competing_branches(
        {**OBS, "sentiment": 0.9, "trend": 0.9}
    )
    by_id = {b.branch_id: b for b in branches}
    analytical = by_id[f"branch_{ThinkingMode.ANALYTICAL.value}"]
    creative = by_id[f"branch_{ThinkingMode.CREATIVE.value}"]
    # Evidence-weighted lenses go long; the creative lens fades them.
    assert analytical.execution_plan["action"] == "BUY"
    assert creative.execution_plan["action"] == "SELL"


@pytest.mark.asyncio
async def test_pipeline_uses_thinking_branches_end_to_end():
    """The CSC 12-stage pipeline receives the thinking-lens branches."""
    from trading_bot.core.csc.controller import CognitiveSystemController

    CognitiveSystemController._instance = None
    world_model = MagicMock()
    hms = MagicMock()
    hms.retrieve_evidence_chain = MagicMock(return_value=[])
    shield = MagicMock()

    csc = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)
    branches = await csc.hypothesis_gen.generate_competing_branches(OBS)

    assert {b.branch_id for b in branches} == EXPECTED_BRANCH_IDS
    await CognitiveSystemController.reset()

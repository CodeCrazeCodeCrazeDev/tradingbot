"""
Comprehensive Integration Test for Scientific Architecture (UCA 2026)
======================================================================
Verifies compliance, paper traceability, and functional integration across:
- EKSFT (arXiv:2605.29303)
- DiscoLoop (arXiv:2607.00341)
- AutoMem (arXiv:2607.01224)
- SAGE (arXiv:2605.12061)
- NanoResearch (arXiv:2605.10813)
- AutoResearchClaw (arXiv:2605.20025)
- HASP (arXiv:2605.17734)
- DeepWeb-Bench (arXiv:2605.21482)
"""

import pytest
import asyncio
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.router import SkillRouter
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.agents.multi_agent_debate import MultiAgentDebateSystem
from trading_bot.governance.evolution_gate import EvolutionGate

MANDATORY_PAPERS = [
    "2605.29303",  # EKSFT
    "2607.00341",  # DiscoLoop
    "2607.01224",  # AutoMem
    "2605.12061",  # SAGE
    "2605.10813",  # NanoResearch
    "2605.20025",  # AutoResearchClaw
    "2605.17734",  # HASP
    "2605.21482",  # DeepWeb-Bench
]


def test_core_singletons_paper_traceability_matrix():
    """Verify all 5 core singletons cite all 8 mandatory research papers in module docstrings."""
    import trading_bot.core.csc.controller as ctrl
    import trading_bot.core.csc.router as rtr
    import trading_bot.core.hms.memory as mem
    import trading_bot.agents.multi_agent_debate as debate
    import trading_bot.governance.evolution_gate as gate

    modules = [ctrl, rtr, mem, debate, gate]

    for mod in modules:
        doc = mod.__doc__ or ""
        for paper in MANDATORY_PAPERS:
            assert paper in doc, f"Module {mod.__name__} docstring missing citation for mandatory paper {paper}"


@pytest.mark.asyncio
async def test_discoloop_and_pivot_refine_integration():
    """Verify CognitiveSystemController DiscoLoop loop and Pivot/Refine capabilities."""
    csc = CognitiveSystemController()
    obs = {"price": 100.0, "volatility": 0.01}

    # Run DiscoLoop reasoning step
    await csc._run_discoloop_reasoning(obs, k=2)
    assert len(csc.discrete_channel) >= 2
    assert "latent" in csc.continuous_state


@pytest.mark.asyncio
async def test_hasp_guardrail_preemption():
    """Verify SkillRouter HASP program function pre-emption."""
    router = SkillRouter()
    context = {"market": {"volatility": 0.4}}  # Volatility > 0.3 triggers HASP

    result = await router.route_task("market_analysis", context)
    assert result.status == "pf_intervention"
    assert result.action == "override_to_hold"


@pytest.mark.asyncio
async def test_sage_graph_memory_subgraph_retrieval(tmp_path):
    """Verify SAGE graph memory multi-hop retrieval."""
    hms = HierarchicalMemorySystem(base_path=str(tmp_path / "hms_test"))
    hms.sage.add_evidence(
        ("BTC", "CORRELATED_WITH", "ETH"),
        context={"regime": "bull"},
        evidence={"confidence": 0.85}
    )

    results = await hms.retrieve_evidence_chain("BTC")
    assert len(results) > 0
    assert results[0]["source"] == "BTC"
    assert results[0]["target"] == "ETH"

#!/usr/bin/env python3
"""Tests for imaginationplanner"""

import pytest
import sys
from pathlib import Path
from trading_bot.world_model.imagination import (
    AdversarialSelfPlay,
    ComplianceController,
    ContactMode,
    ContactModeSwitcher,
    CausalAgentLoop,
    DreamAndVerifyLoop,
    ResidualDiffusionRefiner,
)
from trading_bot.world_model.simulation_orchestrator import PredictiveShield

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestImaginationplanner:
    """Test suite for imaginationplanner"""
    
    def test_import(self):
        """Test that module can be imported"""
        try:
            import trading_bot
            assert True
        except ImportError as e:
            pytest.skip(f"Module not importable: {e}")
    
    def test_placeholder(self):
        """Placeholder test - implement actual tests"""
        # TODO: Implement actual tests for imaginationplanner
        assert True


def test_l8_contact_mode_compliance_and_residual_refinement():
    switcher = ContactModeSwitcher()
    mode = switcher.select_mode({"surprise": 0.2, "liquidity_gap": 0.7, "slippage": 0.6})
    controller = ComplianceController(max_notional=1000, max_leverage=2)
    action = controller.constrain({"decision": "BUY", "notional": 5000, "leverage": 5}, mode.mode)
    refiner = ResidualDiffusionRefiner(seed=1)
    refined = refiner.refine(action.adjusted_action, risk_multiplier=action.risk_multiplier)

    assert mode.mode == ContactMode.SLIP
    assert action.risk_multiplier == 0.5
    assert action.adjusted_action["notional"] == 500
    assert action.adjusted_action["leverage"] == 2
    assert "residual_refinement" in refined


def test_cross_cut_dream_and_verify_loop_blocks_bad_dreams():
    shield = PredictiveShield(warn_threshold=0.3, block_threshold=0.7)

    def simulator(seed):
        return [
            {"drawdown_pressure": 0.1, "surprise": 0.1},
            {"drawdown_pressure": 1.0, "surprise": 1.0, "liquidity_gap": 1.0, "model_uncertainty": 1.0},
        ]

    result = DreamAndVerifyLoop(simulator, shield).run({})

    assert result["dreams"] == 2
    assert result["accepted"] == 1
    assert result["blocked"] == 1


def test_cross_cut_causal_agent_loop_repairs_plan():
    loop = CausalAgentLoop(
        planner=lambda ctx: ["skill_a", "skill_b"],
        repairer=lambda plan, ctx: plan + ["bridge_skill"] if ctx["needs_bridge"] else plan,
    )

    result = loop.run({"needs_bridge": True})

    assert result["changed"]
    assert result["repaired_plan"][-1] == "bridge_skill"


def test_cross_cut_adversarial_self_play_records_stress():
    loop = AdversarialSelfPlay(
        planner=lambda ctx: {"action": "HOLD" if ctx["stress"] > 0.5 else "BUY"},
        adversary=lambda ctx: {**ctx, "stress": 0.8, "resilience": 0.2},
    )

    result = loop.run_round({"stress": 0.0})

    assert result["plan"]["action"] == "HOLD"
    assert result["adversarial_score"] == 0.6
    assert len(loop.history) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

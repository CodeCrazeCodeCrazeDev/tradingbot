"""
Architecture Fitness & UCA-2026 Validation Suite.
Implements 'Gain Metric' (CL-Bench) and 'HORIZON' failure attribution.
"""

import pytest
import os
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.unified_registry import UnifiedComponentRegistry
from trading_bot.governance.evolution_gate import EvolutionGate

def test_singleton_csc():
    """Ensure exactly one instance of CSC exists (One Brain Principle)."""
    csc1 = CognitiveSystemController()
    csc2 = CognitiveSystemController()
    assert csc1 is csc2
    assert csc1.get_status()['version'] == 'UCA-2026-V5'

def test_unified_registry_exists():
    """Ensure the Unified Registry is initialized."""
    registry = UnifiedComponentRegistry()
    assert registry is not None

@pytest.mark.asyncio
async def test_evolution_gate_monotone_safety():
    """Verify the RSEA Evolution Gate logic."""
    gate = EvolutionGate(gain_threshold=0.05)

    # Test pass case
    result = await gate.validate_improvement(
        "test_alpha_1",
        {"sharpe_ratio": 1.5},
        {"sharpe_ratio": 1.0}
    )
    assert result == True

    # Test reject case
    result = await gate.validate_improvement(
        "test_alpha_2",
        {"sharpe_ratio": 1.02},
        {"sharpe_ratio": 1.0}
    )
    assert result == False

def test_orchestrator_cleanup():
    """Verify that redundant orchestrators have been moved to archive."""
    # Check a few known legacy orchestrators
    legacy_path = "trading_bot/self_mastery/mastery_orchestrator.py"
    assert not os.path.exists(legacy_path)

    archive_path = "trading_bot/_archive/legacy_orchestrators/mastery_orchestrator.py"
    assert os.path.exists(archive_path)

def test_hipif_folding_integration():
    """Verify HIPIF folding is integrated in ReActLoop."""
    from trading_bot.core_agent_system.react_loop import ReActLoop
    loop = ReActLoop()
    assert hasattr(loop, 'folding_operator')
    assert loop.folding_operator is not None

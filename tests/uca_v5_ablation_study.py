
import asyncio
import time
import numpy as np
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome

async def run_ablation_study():
    print("\n--- UCA V5 SCIENTIFIC ABLATION STUDY ---\n")

    hms = HierarchicalMemorySystem(base_path="ablation_hms")
    from trading_bot.core.immutable_shield import shield
    from trading_bot.core.unified_event_bus import decision_bus
    await decision_bus.start()

    # --- 1. DiscoLoop Ablation (Reasoning Depth) ---
    print("Ablation 1: DiscoLoop (Multi-hop vs One-shot)")
    csc = CognitiveSystemController(world_model=MagicMock(), hms=hms, shield=shield)
    obs = {"price": 100}

    # Multi-hop (K=3)
    csc._max_loops = 3
    csc.discrete_channel = []
    await csc._run_discoloop_reasoning(obs)
    depth_multi = len(csc.discrete_channel)

    # One-shot (K=0) - Simulation
    csc._max_loops = 0
    csc.discrete_channel = []
    await csc._run_discoloop_reasoning(obs)
    depth_single = len(csc.discrete_channel)

    print(f"  [RESULT] Multi-hop tokens: {depth_multi}, One-shot tokens: {depth_single}")
    assert depth_multi > depth_single
    print("  [PASS] DiscoLoop increases reasoning depth.")

    # --- 2. HASP Ablation (Safety Invariants) ---
    print("\nAblation 2: HASP (Executable Guardrails)")
    high_vol_obs = {"price": 100, "volatility": 0.4} # Above 0.3 threshold

    # With HASP
    intervention = csc._apply_hasp_guardrails(high_vol_obs)
    print(f"  [RESULT] HASP Intervention: {intervention.get('action')}")
    assert intervention.get('status') == "pf_intervention"
    print("  [PASS] HASP correctly enforces state invariants.")

    # --- 3. SAGE Ablation (Graph Retrieval) ---
    print("\nAblation 3: SAGE (Context-Aware Evidence)")
    # Add evidence
    hms.sage.add_evidence(("BTC", "INVERSE_CORRELATED", "DXY"), {"regime": "risk_off"}, {"conf": 0.9})

    # Retrieval
    results = await hms.retrieve_evidence_chain("BTC")
    print(f"  [RESULT] SAGE retrieved {len(results)} evidence chains.")
    assert len(results) > 0
    assert any(r['relation'] == "INVERSE_CORRELATED" for r in results)
    print("  [PASS] SAGE provides structured evidence retrieval.")

    await decision_bus.stop()
    import shutil
    shutil.rmtree("ablation_hms", ignore_errors=True)
    print("\n--- ABLATION STUDY COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(run_ablation_study())

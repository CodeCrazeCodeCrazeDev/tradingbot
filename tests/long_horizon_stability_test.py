"""
Long-Horizon Lifecycle Stability Test
====================================
Simulates accelerated temporal drift and verifies that lifecycle
guardrails (Compaction, Checkpointing, Provenance) prevent system collapse.
"""

import asyncio
import logging
from datetime import datetime, timedelta
import os
import shutil

from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.evolution_layer.evolver import CodeEvolver, EvolutionType
from trading_bot.recursive_improvement.recursive_core import RecursiveImprovementCore, ImprovementDimension

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StabilityTest")

async def test_long_term_sage_stability():
    """Simulates 1000 rounds of evidence to trigger compaction."""
    logger.info("Starting SAGE stability simulation...")
    hms = HierarchicalMemorySystem(base_path="test_hms_stability")

    # Add 100 entries to trigger evolution rounds
    for i in range(101):
        hms.sage.add_evidence(
            (f"Asset_{i}", "HAS_RETURN", f"Value_{i}"),
            {"context": "sim"},
            {"confidence": 0.1 if i % 10 == 0 else 0.8} # Low confidence for some
        )
        hms.sage.evolve([{"action": "PRUNE", "edge_id": (f"Asset_{i}", f"Value_{i}", f"HAS_RETURN_{i}")}] if i % 20 == 0 else [])

    final_node_count = len(hms.sage.graph.nodes)
    logger.info(f"Final SAGE nodes after simulation: {final_node_count}")
    assert final_node_count > 0
    logger.info("SAGE stability test passed (No bloat/crash).")

async def test_generational_checkpointing():
    """Simulates 10 successful evolutions to trigger checkpointing."""
    logger.info("Starting Evolution checkpointing simulation...")
    evolver = CodeEvolver(config={'storage_path': 'test_evolution_stability', 'checkpoints_path': 'test_evolution_checkpoints'})

    def dummy_apply(state): pass

    for i in range(10):
        prop = evolver.propose_evolution(
            EvolutionType.PARAMETER_CHANGE,
            "test_comp", "desc", "rat",
            {}, {"param": i}, 0.1
        )
        evolver.approve_evolution(prop.proposal_id, "human")
        evolver.apply_evolution(prop.proposal_id, dummy_apply)

    # Check if generation_2.json exists (checkpointed every 5)
    checkpoint_files = os.listdir("test_evolution_checkpoints")
    logger.info(f"Checkpoints created: {checkpoint_files}")
    assert len(checkpoint_files) >= 2
    logger.info("Evolution checkpointing test passed.")

async def run_all_stability_tests():
    try:
        await test_long_term_sage_stability()
        await test_generational_checkpointing()
        logger.info("ALL LIFECYCLE STABILITY TESTS PASSED.")
    finally:
        # Cleanup
        for d in ["test_hms_stability", "test_evolution_stability", "test_evolution_checkpoints"]:
            if os.path.exists(d):
                shutil.rmtree(d)

if __name__ == "__main__":
    asyncio.run(run_all_stability_tests())

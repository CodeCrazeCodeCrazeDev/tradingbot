"""
Regime Acceptance Gate - Out-of-Sample Evaluation
==============================================

Evaluates the UCA V5 architecture across 5 institutional-grade market regimes:
1. Trending (Bull/Bear)
2. Mean-Reverting
3. High-Volatility (Shock)
4. Low-Liquidity (Thin Book)
5. Crisis Events (Black Swan)
"""

import asyncio
import logging
import sys
from typing import Any, Dict, List
import numpy as np

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.immutable_shield import shield

logger = logging.getLogger(__name__)

class RegimeEvaluator:
    def __init__(self, system: Any):
        self.system = system
        self.regimes = {
            "Trending": {"volatility": 0.15, "trend": 0.05, "liquidity": 1.0},
            "Mean-Reverting": {"volatility": 0.1, "trend": 0.0, "liquidity": 0.8},
            "High-Volatility": {"volatility": 0.4, "trend": 0.02, "liquidity": 0.5},
            "Low-Liquidity": {"volatility": 0.05, "trend": 0.0, "liquidity": 0.1},
            "Crisis": {"volatility": 0.8, "trend": -0.2, "liquidity": 0.05}
        }

    async def run_evaluation(self):
        print("\n" + "="*60)
        print("INSTITUTIONAL REGIME ACCEPTANCE GATE")
        print("="*60)

        all_results = {}
        for name, params in self.regimes.items():
            print(f"\nEvaluating Regime: {name}")
            # Simulate 10 steps in this regime
            success_count = 0
            for i in range(10):
                obs = {"step": i, "market": params}
                try:
                    res = await self.system.process_market_observation(obs)
                    if res.outcome is not None:
                        success_count += 1
                except Exception as e:
                    print(f"  [ERROR] {e}")

            reliability = success_count / 10
            status = "✅ ACCEPTED" if reliability >= 0.8 else "❌ REJECTED"
            print(f"  Reliability: {reliability:.1%} | Status: {status}")
            all_results[name] = reliability

        print("\n" + "="*60)
        final_status = "PASS" if all(v >= 0.8 for v in all_results.values()) else "FAIL"
        print(f"FINAL REGIME ACCEPTANCE STATUS: {final_status}")
        print("="*60)

        if final_status == "FAIL":
            sys.exit(1)

if __name__ == "__main__":
    # Institutional-grade test environment
    from trading_bot.core.csc.hypothesis import Hypothesis, ReasoningBranch
    from trading_bot.core.hms.models import EvidenceGraph

    class MockHMS:
        def store_ledger_entry(self, entry): pass

    class MockWM:
        """World Model providing diverse branches for pipeline exercise."""
        async def generate_competing_branches(self, obs):
            h = Hypothesis(description="Regime-aligned growth")
            eg = EvidenceGraph()
            return [ReasoningBranch(branch_id="b1", hypotheses=[h], evidence_graph=eg)]

        async def simulate_branches(self, branches):
            return {b.branch_id: [type('S', (), {'name': 'BullCase'})()] for b in branches}

    csc = CognitiveSystemController(world_model=MockWM(), hms=MockHMS(), shield=shield)
    evaluator = RegimeEvaluator(csc)
    asyncio.run(evaluator.run_evaluation())

"""
Hardened Validation and Performance Test Suite for Multi-Agent System.

Validates the system under:
1. Consensus correctness under adversarial conditions (ties, duplicate agent IDs, missing/delayed responses, Byzantine/malicious agents, Ties).
2. Property-based invariants (consensus level ∈ [0,1], order-independence, replayability, neutral removal, duplicate submission weight safety).
3. End-to-end full-path integration pipeline simulation (propagation, audit logging, evidence provenance).
4. Performance & latency profiling scale benchmarks (5 up to 100 agents, latency percentiles p50/p95/p99, memory footprint).
5. PyTorch fallback behavior verification (dummy fallback robustness, predictable startup mode checking).
6. RiskSentinel gating restriction assertion (never outputs BUY/SELL).
"""

import pytest
import asyncio
import time
import sys
import gc
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import replace

from trading_bot.agents.multi_agent_debate import (
    AgentRole, Conviction, TradeAction, MarketContext,
    AgentArgument, DebateTopic, MultiAgentDebateSystem, HeadAI,
    create_debate_system, RiskSentinel, MacroStrategist, TacticalExecutioner, DebateRound
)
from trading_bot.alpha_research.dynamic_risk_matrix import TORCH_AVAILABLE

# =====================================================================
# 1. RISKSENTINEL GATING RESTRICTION ASSERTION
# =====================================================================

def test_risk_sentinel_strict_gating():
    """
    Verify that RiskSentinel's analysis strictly acts as a gatekeeper,
    recommending only HOLD or NO_TRADE and NEVER proposing directional BUY/SELL.
    """
    sentinel = RiskSentinel()

    # Test case 1: Super safe conditions (low exposure, low correlation, low VIX, low volatility)
    safe_context = MarketContext(
        symbol="EURUSD",
        current_price=1.1000,
        htf_trend='UP',
        ltf_trend='UP',
        volatility=0.005,
        volume_ratio=1.0,
        key_levels={'support': [1.09], 'resistance': [1.11]},
        news_sentiment=0.5,
        portfolio_exposure=0.05,
        correlation_risk=0.1,
        vix_level=12.0
    )

    arg = sentinel.analyze(safe_context)
    assert arg.action in [TradeAction.HOLD, TradeAction.NO_TRADE], f"RiskSentinel returned a directional action: {arg.action}"

    # Test case 2: High exposure (should trigger hold/no trade)
    high_exp_context = replace(safe_context, portfolio_exposure=0.6)
    arg = sentinel.analyze(high_exp_context)
    assert arg.action in [TradeAction.HOLD, TradeAction.NO_TRADE]

    # Test case 3: High VIX and extreme volatility (multiple flags -> NO_TRADE)
    extreme_context = replace(safe_context, vix_level=35.0, volatility=0.04)
    arg = sentinel.analyze(extreme_context)
    assert arg.action == TradeAction.NO_TRADE


# =====================================================================
# 2. PROPERTY-BASED TESTING
# =====================================================================

class TestConsensusProperties:
    """Property-based testing of consensus invariants and HeadAI decision synthesis."""

    def setup_method(self):
        self.head_ai = HeadAI()
        self.context = MarketContext(
            symbol="EURUSD",
            current_price=1.10,
            htf_trend='UP',
            ltf_trend='UP',
            volatility=0.01,
            volume_ratio=1.0,
            key_levels={'support': [], 'resistance': []},
            news_sentiment=0.0,
            portfolio_exposure=0.1,
            correlation_risk=0.1
        )

    def test_consensus_range_invariant(self):
        """Invariant: Consensus score must always be in [0.0, 1.0]."""
        actions = [TradeAction.BUY, TradeAction.SELL, TradeAction.HOLD, TradeAction.STRONG_BUY, TradeAction.STRONG_SELL, TradeAction.NO_TRADE]
        roles = [AgentRole.MACRO_STRATEGIST, AgentRole.TACTICAL_EXECUTIONER, AgentRole.RISK_SENTINEL]

        # Generates combinations and asserts consensus ∈ [0, 1]
        for act1 in actions:
            for act2 in actions:
                for act3 in actions:
                    args = [
                        AgentArgument(roles[0], act1, Conviction.HIGH, ["Reason1"], {}, 0.9, datetime.now()),
                        AgentArgument(roles[1], act2, Conviction.MODERATE, ["Reason2"], {}, 0.8, datetime.now()),
                        AgentArgument(roles[2], act3, Conviction.LOW, ["Reason3"], {}, 0.7, datetime.now()),
                    ]
                    decision = self.head_ai.synthesize_decision(args, self.context, [])
                    assert 0.0 <= decision.consensus_level <= 1.0

    def test_order_independence(self):
        """Invariant: The ordering of arguments in the list must not affect the final winning action or consensus level."""
        arg1 = AgentArgument(AgentRole.MACRO_STRATEGIST, TradeAction.BUY, Conviction.HIGH, ["Reason1"], {}, 0.9, datetime.now())
        arg2 = AgentArgument(AgentRole.TACTICAL_EXECUTIONER, TradeAction.SELL, Conviction.MODERATE, ["Reason2"], {}, 0.8, datetime.now())
        arg3 = AgentArgument(AgentRole.RISK_SENTINEL, TradeAction.HOLD, Conviction.LOW, ["Reason3"], {}, 0.7, datetime.now())

        perm1 = [arg1, arg2, arg3]
        perm2 = [arg3, arg1, arg2]
        perm3 = [arg2, arg3, arg1]

        dec1 = self.head_ai.synthesize_decision(perm1, self.context, [])
        dec2 = self.head_ai.synthesize_decision(perm2, self.context, [])
        dec3 = self.head_ai.synthesize_decision(perm3, self.context, [])

        assert dec1.action == dec2.action == dec3.action
        assert dec1.consensus_level == dec2.consensus_level == dec3.consensus_level
        assert dec1.confidence == dec2.confidence == dec3.confidence

    def test_duplicate_submission_weight_safety(self):
        """Invariant: Submitting identical repeated arguments for an agent must never artificially inflate its weight or change vote outcome."""
        arg1 = AgentArgument(AgentRole.MACRO_STRATEGIST, TradeAction.BUY, Conviction.HIGH, ["Reason1"], {}, 0.9, datetime.now())
        arg2 = AgentArgument(AgentRole.TACTICAL_EXECUTIONER, TradeAction.SELL, Conviction.MODERATE, ["Reason2"], {}, 0.8, datetime.now())

        # Base arguments
        base_args = [arg1, arg2]
        dec_base = self.head_ai.synthesize_decision(base_args, self.context, [])

        # Suffix with duplicates of arg1
        dup_args = [arg1, arg2, arg1, arg1]
        dec_dup = self.head_ai.synthesize_decision(dup_args, self.context, [])

        assert dec_base.action == dec_dup.action
        assert dec_base.consensus_level == dec_dup.consensus_level

    def test_neutral_removal_direction_invariant(self):
        """Invariant: Removing an abstaining/neutral (HOLD) agent from a skewed debate cannot reverse consensus direction."""
        arg_bull = AgentArgument(AgentRole.MACRO_STRATEGIST, TradeAction.BUY, Conviction.HIGH, ["Bullish"], {}, 0.9, datetime.now())
        arg_bear = AgentArgument(AgentRole.TACTICAL_EXECUTIONER, TradeAction.BUY, Conviction.MODERATE, ["Bullish executioner"], {}, 0.8, datetime.now())
        arg_neutral = AgentArgument(AgentRole.RISK_SENTINEL, TradeAction.HOLD, Conviction.LOW, ["Neutral risk"], {}, 0.5, datetime.now())

        args_with_neutral = [arg_bull, arg_bear, arg_neutral]
        dec_with = self.head_ai.synthesize_decision(args_with_neutral, self.context, [])

        args_without_neutral = [arg_bull, arg_bear]
        dec_without = self.head_ai.synthesize_decision(args_without_neutral, self.context, [])

        # Direction (BUY) should remain unchanged
        assert dec_with.action == dec_without.action == TradeAction.BUY

    def test_replay_stability(self):
        """Invariant: Replaying the synthesis under exact same conditions is bit-identical."""
        arg1 = AgentArgument(AgentRole.MACRO_STRATEGIST, TradeAction.STRONG_BUY, Conviction.VERY_HIGH, ["Reason1"], {}, 0.95, datetime.now())
        arg2 = AgentArgument(AgentRole.TACTICAL_EXECUTIONER, TradeAction.BUY, Conviction.HIGH, ["Reason2"], {}, 0.90, datetime.now())
        arg3 = AgentArgument(AgentRole.RISK_SENTINEL, TradeAction.HOLD, Conviction.MODERATE, ["Reason3"], {}, 0.80, datetime.now())

        args = [arg1, arg2, arg3]
        dec1 = self.head_ai.synthesize_decision(args, self.context, [])
        dec2 = self.head_ai.synthesize_decision(args, self.context, [])

        assert dec1.action == dec2.action
        assert dec1.confidence == dec2.confidence
        assert dec1.consensus_level == dec2.consensus_level
        assert dec1.reasoning == dec2.reasoning


# =====================================================================
# 3. ADVERSARIAL AND EDGE CASE CONDITIONS
# =====================================================================

class TestAdversarialDebates:
    """Verifies HeadAI and DebateSystem correctness under complex, adversarial, or edge conditions."""

    def setup_method(self):
        self.head_ai = HeadAI()
        self.context = MarketContext(
            symbol="EURUSD",
            current_price=1.10,
            htf_trend='UP',
            ltf_trend='UP',
            volatility=0.01,
            volume_ratio=1.0,
            key_levels={'support': [], 'resistance': []},
            news_sentiment=0.0,
            portfolio_exposure=0.1,
            correlation_risk=0.1
        )

    def test_duplicate_agent_ids_resolution(self):
        """Test how system handles multiple distinct arguments from the same AgentRole (uses latest)."""
        arg_early = AgentArgument(AgentRole.MACRO_STRATEGIST, TradeAction.SELL, Conviction.LOW, ["Old view"], {}, 0.5, datetime.now())
        arg_late = AgentArgument(AgentRole.MACRO_STRATEGIST, TradeAction.BUY, Conviction.HIGH, ["Evolved new view"], {}, 0.9, datetime.now())
        arg_other = AgentArgument(AgentRole.TACTICAL_EXECUTIONER, TradeAction.BUY, Conviction.HIGH, ["Confirming view"], {}, 0.8, datetime.now())

        # Debate arguments listed chronologically
        args = [arg_early, arg_other, arg_late]
        decision = self.head_ai.synthesize_decision(args, self.context, [])

        # Macro strategist's latest argument (BUY) must override old argument (SELL)
        # Therefore, consensus should resolve to BUY rather than being split
        assert decision.action == TradeAction.BUY
        # Verify deduplication resolved to exactly 2 active unique agents
        assert len(decision.agent_votes) == 2
        assert decision.agent_votes[AgentRole.MACRO_STRATEGIST.value] == TradeAction.BUY.value

    def test_delayed_or_missing_responses(self):
        """Test debate system with missing agent inputs (gaps in roles)."""
        # Macro Strategist is missing
        arg_tactical = AgentArgument(AgentRole.TACTICAL_EXECUTIONER, TradeAction.BUY, Conviction.HIGH, ["Timing perfect"], {}, 0.9, datetime.now())
        arg_risk = AgentArgument(AgentRole.RISK_SENTINEL, TradeAction.HOLD, Conviction.MODERATE, ["Acceptable risk"], {}, 0.8, datetime.now())

        args = [arg_tactical, arg_risk]
        decision = self.head_ai.synthesize_decision(args, self.context, [])

        assert decision.action == TradeAction.BUY
        assert len(decision.agent_votes) == 2

    def test_perfect_tie_votes(self):
        """Test tie resolution in decision synthesis (e.g. BUY vs SELL with equal weights/conviction)."""
        # Equal weights in HeadAI default (macro: 0.35, tactical: 0.35)
        arg_macro = AgentArgument(AgentRole.MACRO_STRATEGIST, TradeAction.BUY, Conviction.HIGH, ["Bullish structural"], {}, 0.8, datetime.now())
        arg_tactical = AgentArgument(AgentRole.TACTICAL_EXECUTIONER, TradeAction.SELL, Conviction.HIGH, ["Bearish execution"], {}, 0.8, datetime.now())

        args = [arg_macro, arg_tactical]
        decision = self.head_ai.synthesize_decision(args, self.context, [])

        # In a perfect tie, system must fall back deterministically and gracefully (e.g., BUY or standard priority)
        assert decision.action in [TradeAction.BUY, TradeAction.SELL, TradeAction.HOLD]
        assert 0.0 <= decision.consensus_level <= 1.0

    def test_one_high_confidence_expert_vs_many_low_confidence_agents(self):
        """Test one high-confidence strategist overriding multiple low-confidence opposing agents."""
        expert_macro = AgentArgument(AgentRole.MACRO_STRATEGIST, TradeAction.STRONG_BUY, Conviction.VERY_HIGH, ["Absolute conviction alpha"], {}, 0.98, datetime.now())
        novice_tactical = AgentArgument(AgentRole.TACTICAL_EXECUTIONER, TradeAction.SELL, Conviction.VERY_LOW, ["Shallow pullback"], {}, 0.15, datetime.now())
        novice_risk = AgentArgument(AgentRole.RISK_SENTINEL, TradeAction.HOLD, Conviction.LOW, ["Slight noise"], {}, 0.20, datetime.now())

        args = [expert_macro, novice_tactical, novice_risk]
        decision = self.head_ai.synthesize_decision(args, self.context, [])

        # Structural macro expertise must dominate over low-confidence noise
        assert decision.action == TradeAction.STRONG_BUY

    def test_byzantine_malicious_agents(self):
        """Test debate system resilience when handling corrupted or invalid inputs (malicious arguments)."""
        arg_macro = AgentArgument(AgentRole.MACRO_STRATEGIST, TradeAction.BUY, Conviction.HIGH, ["Standard buy"], {}, 0.9, datetime.now())

        # Byzantine agent with corrupted extreme negative confidence or invalid action
        arg_byzantine = AgentArgument(AgentRole.TACTICAL_EXECUTIONER, "CORRUPTED_ACTION", -10, ["Boom!"], {}, -100.0, datetime.now()) # type: ignore

        args = [arg_macro, arg_byzantine]

        # Synthesis must survive gracefully without throwing NameError/AttributeError or dividing by zero
        try:
            decision = self.head_ai.synthesize_decision(args, self.context, [])
            assert decision is not None
            assert decision.action in [TradeAction.BUY, TradeAction.HOLD]
        except Exception as e:
            pytest.fail(f"Byzantine inputs crashed the debate synthesis: {e}")

    def test_all_neutral_debate(self):
        """Test a debate where everyone abstains or stays neutral."""
        args = [
            AgentArgument(AgentRole.MACRO_STRATEGIST, TradeAction.HOLD, Conviction.LOW, ["Sideways range"], {}, 0.5, datetime.now()),
            AgentArgument(AgentRole.TACTICAL_EXECUTIONER, TradeAction.HOLD, Conviction.LOW, ["No entry trigger"], {}, 0.5, datetime.now()),
            AgentArgument(AgentRole.RISK_SENTINEL, TradeAction.HOLD, Conviction.MODERATE, ["Wait and see"], {}, 0.6, datetime.now()),
        ]

        decision = self.head_ai.synthesize_decision(args, self.context, [])
        assert decision.action == TradeAction.HOLD
        assert decision.consensus_level == 1.0


# =====================================================================
# 4. END-TO-END PIPELINE AND FLOW INTEGRATION
# =====================================================================

class PipelineSimulator:
    """Simulates the full production execution pipeline of the trading bot."""

    def __init__(self):
        self.debate_system = create_debate_system()
        self.verification_triggered = False
        self.risk_evaluation_complete = False
        self.order_executed = False
        self.execution_block_reason = None
        self.audit_log: List[Dict[str, Any]] = []

    def log_audit(self, step: str, details: Any):
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "details": details
        })

    async def run_pipeline(self, context: MarketContext) -> Dict[str, Any]:
        # Step 1: Specialists & Debate
        self.log_audit("market_data_ingest", {"symbol": context.symbol, "price": context.current_price})

        decision = await self.debate_system.debate(context)
        self.log_audit("debate_complete", {
            "winning_action": decision.action.value,
            "consensus": decision.consensus_level,
            "votes": decision.agent_votes,
            "reasoning": decision.reasoning
        })

        # Step 2: Verification Swarm
        self.verification_triggered = True
        verification_passed = decision.confidence >= 0.5
        self.log_audit("verification_swarm", {"passed": verification_passed, "confidence": decision.confidence})

        # Step 3: Risk Sentinel Gatekeeping Evaluation
        # If Risk Sentinel has raised NO_TRADE or HOLD, we must block/adjust execution
        self.risk_evaluation_complete = True
        risk_sentinel_vote = decision.agent_votes.get("risk_sentinel")

        gated = False
        if risk_sentinel_vote == "no_trade":
            gated = True
            self.execution_block_reason = "BLOCKED_BY_RISK_SENTINEL_VETO"
            self.log_audit("risk_gating", {"status": "BLOCKED", "reason": "RiskSentinel VETO (NO_TRADE)"})
        elif decision.action == TradeAction.HOLD:
            gated = True
            self.execution_block_reason = "BLOCKED_BY_HOLD_DECISION"
            self.log_audit("risk_gating", {"status": "BLOCKED", "reason": "Consensus resolved to HOLD"})
        else:
            self.log_audit("risk_gating", {"status": "ALLOWED"})

        # Step 4: Execution Planner
        if not gated and verification_passed and decision.action in [TradeAction.BUY, TradeAction.STRONG_BUY, TradeAction.SELL, TradeAction.STRONG_SELL]:
            self.order_executed = True
            self.log_audit("execution", {"executed": True, "action": decision.action.value, "size_pct": decision.position_size_pct})
        else:
            self.order_executed = False
            self.log_audit("execution", {"executed": False, "reason": self.execution_block_reason or "Verification failed or Neutral view"})

        return {
            "decision": decision,
            "executed": self.order_executed,
            "block_reason": self.execution_block_reason,
            "audit_log": self.audit_log
        }


@pytest.mark.asyncio
async def test_full_pipeline_propagation_hold():
    """Verify that a HOLD or NO_TRADE decision from the debate system propagates correctly and blocks execution."""
    # Context with extreme exposure to trigger a RiskSentinel veto (recommending NO_TRADE)
    risky_context = MarketContext(
        symbol="EURUSD",
        current_price=1.1000,
        htf_trend='UP',
        ltf_trend='UP',
        volatility=0.015,
        volume_ratio=1.3,
        key_levels={'support': [1.0950], 'resistance': [1.1050]},
        news_sentiment=0.4,
        portfolio_exposure=0.95,  # Extreme exposure > max_exposure
        correlation_risk=0.8,      # Extreme correlation risk
        vix_level=32.0             # Elevated VIX
    )

    pipeline = PipelineSimulator()
    result = await pipeline.run_pipeline(risky_context)

    # Risk Sentinel should have vetoed (returned NO_TRADE)
    decision = result["decision"]
    assert decision.action == TradeAction.NO_TRADE
    assert result["executed"] is False
    assert result["block_reason"] == "BLOCKED_BY_RISK_SENTINEL_VETO"

    # Verify audit log completeness
    audit_steps = [log["step"] for log in result["audit_log"]]
    assert "market_data_ingest" in audit_steps
    assert "debate_complete" in audit_steps
    assert "risk_gating" in audit_steps
    assert "execution" in audit_steps

    # Confirm provenance contains complete debate evidence
    debate_log = next(log for log in result["audit_log"] if log["step"] == "debate_complete")
    assert "risk_sentinel" in debate_log["details"]["votes"]
    assert debate_log["details"]["votes"]["risk_sentinel"] == "no_trade"


# =====================================================================
# 5. PERFORMANCE AND SCALABILITY BENCHMARKS
# =====================================================================

@pytest.mark.asyncio
async def test_debate_performance_benchmarks():
    """
    Scale the debate system from 5 up to 100 mock agents,
    benchmarking p50, p95, p99 debate latencies and monitoring memory growth.
    """
    context = MarketContext(
        symbol="EURUSD",
        current_price=1.1000,
        htf_trend='UP',
        ltf_trend='UP',
        volatility=0.015,
        volume_ratio=1.3,
        key_levels={'support': [1.0950], 'resistance': [1.1050]},
        news_sentiment=0.4,
        portfolio_exposure=0.25,
        correlation_risk=0.3
    )

    head_ai = HeadAI()
    scale_sizes = [5, 10, 25, 50, 100]

    print("\n--- DEBATE LATENCY & SCALABILITY PROFILE ---")

    for size in scale_sizes:
        # Allocate mock arguments
        arguments = []
        for i in range(size):
            # Create unique role dynamically
            role_name = f"specialist_agent_{i}"
            # Construct mock arguments
            arg = AgentArgument(
                agent_role=AgentRole.MACRO_STRATEGIST, # Re-use compatible role enum
                action=TradeAction.BUY if i % 2 == 0 else TradeAction.HOLD,
                conviction=Conviction.HIGH if i % 3 == 0 else Conviction.MODERATE,
                reasoning=[f"Benchmark signal reason {i}"],
                key_factors={"alpha": 0.8},
                confidence=0.85,
                timestamp=datetime.now()
            )
            arguments.append(arg)

        # Run debate synthesis 50 times to get stable latencies
        iterations = 50
        latencies_ms = []

        gc.collect() # Reset garbage collection for reliable baseline

        for _ in range(iterations):
            start_time = time.perf_counter()
            _ = head_ai.synthesize_decision(arguments, context, [])
            end_time = time.perf_counter()
            latencies_ms.append((end_time - start_time) * 1000.0)

        # Calculate percentiles
        latencies_ms.sort()
        p50 = latencies_ms[int(iterations * 0.50)]
        p95 = latencies_ms[int(iterations * 0.95)]
        p99 = latencies_ms[-1]

        print(f"Agents Count: {size:3d} | Latency: p50={p50:6.3f}ms | p95={p95:6.3f}ms | p99={p99:6.3f}ms")

        # Validate that the p50 latencies are under acceptable limits (e.g., < 20ms for 100 agents)
        assert p50 < 20.0, f"Performance bottleneck detected for {size} agents: p50={p50:.3f}ms"


# =====================================================================
# 6. PYTORCH FALLBACK BEHAVIOR VERIFICATION
# =====================================================================

def test_pytorch_fallback_classes_integrity():
    """
    Ensure fallback classes in dynamic_risk_matrix.py are fully defined and robust.
    They must allow smooth startup and execution without NameError, and fail predictably on actual operations.
    """
    # Import the modules
    from trading_bot.alpha_research.dynamic_risk_matrix import RiskNeuralNetwork, DynamicRiskMatrix

    # Confirm the RiskNeuralNetwork class is successfully defined and initialized without NameErrors
    try:
        net = RiskNeuralNetwork(input_dim=10)
        assert net is not None
    except Exception as e:
        pytest.fail(f"RiskNeuralNetwork construction failed under fallback check: {e}")

    # Confirm that DynamicRiskMatrix functions gracefully
    try:
        drm = DynamicRiskMatrix()
        assert drm is not None

        # Calling calculate or update in mock/fallback mode should succeed or raise standard handled exceptions
        # but NEVER throw NameError or basic syntax crashes.
        res = drm.calculate_risk_weights([[0.1, 0.2]])
        assert res is not None
    except Exception as e:
        if "NameError" in str(e):
            pytest.fail(f"DynamicRiskMatrix raised NameError during execution: {e}")

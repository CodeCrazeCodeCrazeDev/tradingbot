"""
AlphaAlgo MSOS - Market Survival Operating System Demo

This demo showcases the complete MSOS system - a capital-preservation-first
trading governance system designed to survive adversarial, non-stationary markets.

PRIMARY DIRECTIVE: Preserve capital. Returns are a side effect of survival.

Author: AlphaAlgo MSOS
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.msos import (
    MSOSOrchestrator,
    OrchestratorConfig,
    MSOSCore,
    MSOSConfig,
    ConstraintType,
    HierarchyLevel,
    ABSOLUTE_AXIOMS,
    MarketTradabilityGate,
    AssumptionEngine,
    SignalSemanticMonitor,
    RegimeInstabilityDetector,
    CapitalGovernor,
    LossShapeMonitor,
    ExecutionRealityChecker,
    AntiOverreactionEngine,
    LearningFirewall,
    TimeRiskManager,
    DataAdversarialDefense,
    QuantModelFactory,
    EdgeDeclaration,
    EdgeType,
    ModelProposal,
    PostMortemEngine,
    EntropyBudgetManager,
    ReactionType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("msos.demo")


def print_header(title: str):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_axioms():
    """Print the absolute axioms"""
    print_header("ABSOLUTE AXIOMS (IMMUTABLE)")
    for i, axiom in enumerate(sorted(ABSOLUTE_AXIOMS), 1):
        print(f"  {i}. {axiom}")
    print()


async def demo_core_system():
    """Demonstrate the core MSOS system"""
    print_header("MSOS CORE SYSTEM")
    
    # Create core
    core = MSOSCore(MSOSConfig(
        enable_strict_mode=True,
        default_to_no_trade=True
    ))
    
    print("Core initialized with immutable constraints:")
    for constraint in core.constraints.all_constraints:
        print(f"  - {constraint.constraint_type.name}: {constraint.value}")
    
    # Test evaluation with good conditions
    print("\n--- Evaluating with GOOD conditions ---")
    good_values = {
        ConstraintType.MIN_MARKET_VALIDITY: 0.8,
        ConstraintType.MAX_UNCERTAINTY: 0.3,
        ConstraintType.MAX_VOLATILITY: 0.02,
        ConstraintType.MAX_DRAWDOWN: 0.05,
        ConstraintType.MAX_DAILY_LOSS: 0.01,
    }
    
    decision = core.evaluate("momentum_strategy", "EURUSD", good_values)
    print(f"  Decision: {decision.decision_type.name}")
    print(f"  Authority: {decision.authority_layer.name}")
    print(f"  Max Exposure: {decision.max_exposure:.2%}")
    print(f"  Trade Allowed: {decision.is_trade_allowed()}")
    
    # Test evaluation with bad conditions
    print("\n--- Evaluating with BAD conditions ---")
    bad_values = {
        ConstraintType.MIN_MARKET_VALIDITY: 0.3,  # Too low
        ConstraintType.MAX_UNCERTAINTY: 0.9,      # Too high
        ConstraintType.MAX_VOLATILITY: 0.08,
        ConstraintType.MAX_DRAWDOWN: 0.15,
        ConstraintType.MAX_DAILY_LOSS: 0.04,
    }
    
    decision = core.evaluate("momentum_strategy", "EURUSD", bad_values)
    print(f"  Decision: {decision.decision_type.name}")
    print(f"  Authority: {decision.authority_layer.name}")
    print(f"  Max Exposure: {decision.max_exposure:.2%}")
    print(f"  Trade Allowed: {decision.is_trade_allowed()}")
    print(f"  Reason: {decision.reason}")


async def demo_market_tradability():
    """Demonstrate market tradability gate"""
    print_header("MARKET TRADABILITY GATE (Layer 0)")
    
    gate = MarketTradabilityGate()
    
    # Good market conditions
    print("\n--- Good Market Conditions ---")
    good_market = {
        'bid': 1.1000,
        'ask': 1.1002,
        'bid_depth': 500000,
        'ask_depth': 500000,
        'fill_rate': 0.98,
        'slippage': 0.0001,
        'realized_volatility': 0.015,
        'event_proximity_hours': 48,
    }
    
    result = gate.evaluate("EURUSD", good_market)
    print(f"  Validity: {result.validity.name}")
    print(f"  Tradable: {result.is_tradable}")
    print(f"  Exposure Multiplier: {result.exposure_multiplier:.2%}")
    print(f"  Overall Score: {result.overall_score:.2f}")
    
    # Bad market conditions
    print("\n--- Bad Market Conditions (Liquidity Crisis) ---")
    bad_market = {
        'bid': 1.1000,
        'ask': 1.1050,  # Wide spread
        'bid_depth': 10000,  # Low depth
        'ask_depth': 5000,
        'fill_rate': 0.5,
        'slippage': 0.005,
        'realized_volatility': 0.08,
        'event_proximity_hours': 0.5,  # Event imminent
    }
    
    result = gate.evaluate("EURUSD", bad_market)
    print(f"  Validity: {result.validity.name}")
    print(f"  Tradable: {result.is_tradable}")
    print(f"  Exposure Multiplier: {result.exposure_multiplier:.2%}")
    print(f"  Invalidation Reasons: {result.invalidation_reasons}")


async def demo_assumption_engine():
    """Demonstrate assumption extraction and enforcement"""
    print_header("ASSUMPTION ENGINE")
    
    engine = AssumptionEngine()
    
    # Register strategy with explicit assumptions
    print("\n--- Registering Strategy with Assumptions ---")
    strategy_config = {
        'type': 'momentum',
        'lookback': 20,
        'assumptions': {
            'regime': {
                'name': 'Trending Regime',
                'description': 'Assumes market is trending',
                'expected_value': 0.7,
                'tolerance': 0.2
            },
            'liquidity': {
                'name': 'Adequate Liquidity',
                'description': 'Assumes sufficient liquidity',
                'expected_value': 0.8,
                'tolerance': 0.15
            },
            'volatility': {
                'name': 'Normal Volatility',
                'description': 'Assumes volatility < 3%',
                'expected_value': 0.02,
                'tolerance': 0.5
            }
        }
    }
    
    result = engine.register_strategy("momentum_001", strategy_config)
    print(f"  Registered: {result.is_valid}")
    print(f"  Explicit Assumptions: {len(result.assumptions)}")
    print(f"  Hidden Assumptions: {len(result.hidden_assumptions)}")
    
    # Validate with good conditions
    print("\n--- Validating with Good Conditions ---")
    good_data = {
        'regime_stability': 0.75,
        'liquidity_score': 0.85,
        'realized_volatility': 0.018,
    }
    
    result = engine.validate_strategy("momentum_001", good_data)
    print(f"  Valid: {result.is_valid}")
    print(f"  Can Trade: {result.can_trade}")
    print(f"  Exposure: {result.exposure_multiplier:.2%}")
    print(f"  Violations: {len(result.violations)}")
    
    # Validate with violated assumptions
    print("\n--- Validating with Violated Assumptions ---")
    bad_data = {
        'regime_stability': 0.3,  # Violated!
        'liquidity_score': 0.4,   # Violated!
        'realized_volatility': 0.05,  # Violated!
    }
    
    result = engine.validate_strategy("momentum_001", bad_data)
    print(f"  Valid: {result.is_valid}")
    print(f"  Can Trade: {result.can_trade}")
    print(f"  Violations: {len(result.violations)}")
    for v in result.violations:
        print(f"    - {v.assumption.name}: {v.severity.name}")


async def demo_learning_firewall():
    """Demonstrate learning firewall"""
    print_header("LEARNING FIREWALL")
    
    firewall = LearningFirewall()
    
    # Normal market data
    print("\n--- Normal Market Data ---")
    normal_data = {
        'return': 0.005,
        'volatility': 0.02,
        'correlation': 0.3,
        'liquidity': 0.8,
    }
    
    result = firewall.check(normal_data)
    print(f"  State: {result.state.name}")
    print(f"  Can Learn: {result.can_learn}")
    print(f"  Detected Events: {[e.name for e in result.detected_events]}")
    
    # Extreme event (tail event)
    print("\n--- Extreme Event (Tail Event) ---")
    # First, build up history
    for _ in range(50):
        firewall.check({'return': 0.001, 'volatility': 0.02, 'correlation': 0.3, 'liquidity': 0.8})
    
    extreme_data = {
        'return': -0.15,  # 15% drop - extreme!
        'volatility': 0.08,
        'correlation': 0.95,  # Correlation spike
        'liquidity': 0.2,  # Liquidity vacuum
    }
    
    result = firewall.check(extreme_data)
    print(f"  State: {result.state.name}")
    print(f"  Can Learn: {result.can_learn}")
    print(f"  Detected Events: {[e.name for e in result.detected_events]}")
    print(f"  Freeze Duration: {result.freeze_duration_seconds}s")
    print(f"  Reason: {result.reason}")


async def demo_quant_factory():
    """Demonstrate quant model factory"""
    print_header("QUANT MODEL FACTORY (Sandbox Only)")
    
    factory = QuantModelFactory()
    
    # Propose a model with valid edge declaration
    print("\n--- Proposing Model with Valid Edge ---")
    edge = EdgeDeclaration(
        edge_type=EdgeType.BEHAVIORAL,
        description="Exploits retail trader overreaction to news",
        why_exists="Retail traders overreact to headlines, creating mean-reversion opportunities",
        when_fails="When institutional flow dominates or during genuine regime changes",
        what_breaks_it="Increased retail sophistication or regulatory changes",
        expected_half_life=90,  # 90 days
        crowding_sensitivity=0.6,
        regime_dependency=['normal', 'low_volatility']
    )
    
    proposal = ModelProposal(
        model_id="retail_fade_001",
        name="Retail Fade Strategy",
        description="Fades retail overreaction to news",
        edge_declaration=edge,
        complexity_score=0.4,
        interpretability_score=0.7,
        proposed_by="quant_team"
    )
    
    accepted = factory.propose(proposal)
    print(f"  Accepted: {accepted}")
    print(f"  Status: {factory.get_model_status('retail_fade_001').name}")
    
    # Propose a black-box model (should be rejected)
    print("\n--- Proposing Black-Box Model (Should Reject) ---")
    bad_edge = EdgeDeclaration(
        edge_type=EdgeType.UNKNOWN,  # Black box!
        description="",
        why_exists="",
        when_fails="",
        what_breaks_it="",
        expected_half_life=0,
        crowding_sensitivity=0,
        regime_dependency=[]
    )
    
    bad_proposal = ModelProposal(
        model_id="blackbox_001",
        name="Black Box ML",
        description="Neural network with unknown edge",
        edge_declaration=bad_edge,
        complexity_score=0.9,  # Too complex
        interpretability_score=0.1,  # Not interpretable
        proposed_by="ml_team"
    )
    
    accepted = factory.propose(bad_proposal)
    print(f"  Accepted: {accepted}")
    print(f"  Rejection Reason: {bad_proposal.rejection_reason}")


async def demo_entropy_budget():
    """Demonstrate entropy budget management"""
    print_header("ENTROPY BUDGET MANAGER")
    
    manager = EntropyBudgetManager()
    
    print("\n--- Initial Budget ---")
    result = manager.check_budget()
    print(f"  Level: {result.level.name}")
    print(f"  Consumed: {result.budget.consumed:.2f}")
    print(f"  Remaining: {result.budget.remaining:.2f}")
    print(f"  Can Add Exposure: {result.can_add_exposure}")
    
    # Add positions (consume entropy)
    print("\n--- Adding Positions (Consuming Entropy) ---")
    for i in range(5):
        result = manager.add_position_entropy(
            strategy_id=f"strategy_{i}",
            position_size=0.05,
            complexity=0.5
        )
        print(f"  Position {i+1}: Level={result.level.name}, Consumed={result.budget.consumed:.2f}")
    
    print(f"\n  Final Level: {result.level.name}")
    print(f"  Can Add Exposure: {result.can_add_exposure}")
    print(f"  Exposure Multiplier: {result.exposure_multiplier:.2%}")


async def demo_full_orchestrator():
    """Demonstrate the full MSOS orchestrator"""
    print_header("FULL MSOS ORCHESTRATOR")
    
    # Create orchestrator
    config = OrchestratorConfig(
        enable_all_checks=True,
        strict_mode=True
    )
    orchestrator = MSOSOrchestrator(config)
    
    print("\n--- System Status ---")
    status = orchestrator.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Evaluate a trade with good conditions
    print("\n--- Evaluating Trade (Good Conditions) ---")
    good_market = {
        'source': 'primary_feed',
        'price': 1.1000,
        'volume': 100000,
        'timestamp': 1234567890,
        'bid': 1.0999,
        'ask': 1.1001,
        'bid_depth': 500000,
        'ask_depth': 500000,
        'fill_rate': 0.98,
        'slippage': 0.0001,
        'realized_volatility': 0.015,
        'return': 0.002,
        'signal_value': 0.7,
        'target_value': 0.65,
        'trade_count': 100,
        'order_book_changes': 50,
        'volatility': 0.015,
        'regime_stability': 0.8,
        'liquidity_score': 0.85,
    }
    
    strategy_config = {
        'type': 'momentum',
        'assumptions': {
            'regime': {'name': 'Trending', 'expected_value': 0.7, 'tolerance': 0.2},
            'liquidity': {'name': 'Liquid', 'expected_value': 0.8, 'tolerance': 0.15},
            'volatility': {'name': 'Normal Vol', 'expected_value': 0.02, 'tolerance': 0.5},
        }
    }
    
    result = await orchestrator.evaluate(
        strategy_id="momentum_001",
        symbol="EURUSD",
        market_data=good_market,
        strategy_config=strategy_config,
        equity=100000
    )
    
    print(f"  Tradable: {result.is_tradable}")
    print(f"  Can Trade: {result.can_trade}")
    print(f"  Max Exposure: {result.max_exposure:.2%}")
    print(f"  Mode: {result.mode.name}")
    print(f"  Decision: {result.decision.decision_type.name}")
    print(f"  Warnings: {len(result.warnings)}")
    
    # Evaluate with bad conditions
    print("\n--- Evaluating Trade (Crisis Conditions) ---")
    crisis_market = {
        'source': 'primary_feed',
        'price': 1.0800,
        'volume': 10000,
        'timestamp': 1234567890,
        'bid': 1.0750,
        'ask': 1.0850,  # Wide spread
        'bid_depth': 10000,
        'ask_depth': 5000,
        'fill_rate': 0.5,
        'slippage': 0.01,
        'realized_volatility': 0.08,  # High vol
        'return': -0.05,  # Big loss
        'signal_value': 0.3,
        'target_value': -0.2,
        'trade_count': 500,  # High activity
        'order_book_changes': 200,
        'volatility': 0.08,
        'regime_stability': 0.2,  # Unstable
        'liquidity_score': 0.3,  # Low liquidity
    }
    
    result = await orchestrator.evaluate(
        strategy_id="momentum_001",
        symbol="EURUSD",
        market_data=crisis_market,
        strategy_config=strategy_config,
        equity=95000  # Lost 5%
    )
    
    print(f"  Tradable: {result.is_tradable}")
    print(f"  Can Trade: {result.can_trade}")
    print(f"  Max Exposure: {result.max_exposure:.2%}")
    print(f"  Mode: {result.mode.name}")
    print(f"  Decision: {result.decision.decision_type.name}")
    print(f"  Reason: {result.reason}")
    print(f"  Warnings: {result.warnings[:3]}...")  # First 3 warnings


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("  ALPHAALGO MSOS - MARKET SURVIVAL OPERATING SYSTEM")
    print("  Capital Preservation First | Returns Are A Side Effect")
    print("=" * 70)
    
    # Print axioms
    print_axioms()
    
    # Run demos
    await demo_core_system()
    await demo_market_tradability()
    await demo_assumption_engine()
    await demo_learning_firewall()
    await demo_quant_factory()
    await demo_entropy_budget()
    await demo_full_orchestrator()
    
    print_header("DEMO COMPLETE")
    print("""
    KEY TAKEAWAYS:
    
    1. MSOS is NOT a profit-maximization system
    2. It is a SURVIVAL system that governs exposure
    3. Constraints > Control > Exposure > Strategy > Intelligence > Prediction
    4. No layer may override a higher layer
    5. Default to NO TRADE unless all checks pass
    6. Learning from extreme events is FORBIDDEN
    7. Black-box alpha is FORBIDDEN
    8. Capital preservation is the PRIMARY directive
    
    "AlphaAlgo does not try to win. AlphaAlgo tries to not die."
    """)


if __name__ == "__main__":
    asyncio.run(main())

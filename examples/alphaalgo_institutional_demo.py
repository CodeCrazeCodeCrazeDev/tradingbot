"""
AlphaAlgo Institutional System Demo
===================================

This demo showcases the complete AlphaAlgo Institutional quantitative research system.

The system operates as:
- Hedge fund research desk
- Proprietary trading firm
- Quantitative asset manager
- Risk committee
- Portfolio manager
- Systems engineer

Primary objective: Long-term capital compounding under uncertainty.
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.alphaalgo_institutional import (
    AlphaAlgoInstitutional,
    MarketSelectionLayer,
    RegimeDetectionLayer,
    QuantitativeResearchLayer,
    PortfolioAllocationLayer,
    RiskGovernanceLayer,
    ExecutionLayer,
    MonitoringEvolutionLayer,
    IdeaVectorConstraints,
    SelfEvolvingResearchLoop
)
from trading_bot.alphaalgo_institutional.orchestrator import (
    create_alphaalgo_institutional,
    SystemConfig,
    TradingMode
)
from trading_bot.alphaalgo_institutional.core_types import MarketRegime


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_section(title: str):
    """Print a section header."""
    print(f"\n--- {title} ---")


async def demo_layer1_market_selection():
    """Demonstrate Layer 1: Market Selection."""
    print_header("LAYER 1: MARKET SELECTION")
    
    layer = MarketSelectionLayer()
    
    # Define candidate markets
    candidate_markets = [
        {'symbol': 'EURUSD', 'type': 'forex', 'avg_spread': 0.0001, 'daily_volume': 5e9},
        {'symbol': 'BTCUSD', 'type': 'crypto', 'avg_spread': 0.001, 'daily_volume': 50e9},
        {'symbol': 'SPY', 'type': 'equity', 'avg_spread': 0.01, 'daily_volume': 100e6},
        {'symbol': 'GC', 'type': 'commodity', 'avg_spread': 0.1, 'daily_volume': 200000},
        {'symbol': 'ILLIQUID', 'type': 'equity', 'avg_spread': 0.5, 'daily_volume': 1000},
    ]
    
    print_section("Analyzing Markets")
    selected = layer.select_markets(candidate_markets)
    
    print(f"\nCandidates analyzed: {len(candidate_markets)}")
    print(f"Markets selected: {len(selected)}")
    
    for market in selected:
        print(f"  - {market.get('symbol', 'Unknown')}: Score {market.get('score', 0):.2f}")
    
    print_section("Layer State")
    state = layer.get_layer_state()
    print(f"Total markets analyzed: {state['total_markets_analyzed']}")
    print(f"Markets selected: {state['markets_selected']}")


async def demo_layer2_regime_detection():
    """Demonstrate Layer 2: Regime Detection."""
    print_header("LAYER 2: REGIME DETECTION")
    
    layer = RegimeDetectionLayer()
    
    # Generate sample returns for different regimes
    print_section("Detecting Regimes")
    
    # Normal market
    normal_returns = np.random.normal(0.0005, 0.01, 100)
    regime = layer.detect_regime(normal_returns, volatility=0.15)
    print(f"\nNormal market regime: {regime.primary_regime.value}")
    print(f"  Confidence: {regime.confidence:.2f}")
    print(f"  Volatility regime: {regime.volatility_regime.value}")
    
    # High volatility market
    volatile_returns = np.random.normal(0, 0.03, 100)
    regime = layer.detect_regime(volatile_returns, volatility=0.45)
    print(f"\nVolatile market regime: {regime.primary_regime.value}")
    print(f"  Confidence: {regime.confidence:.2f}")
    print(f"  Volatility regime: {regime.volatility_regime.value}")
    
    # Trending market
    trend_returns = np.linspace(0.001, 0.003, 100) + np.random.normal(0, 0.005, 100)
    regime = layer.detect_regime(trend_returns, volatility=0.12)
    print(f"\nTrending market regime: {regime.primary_regime.value}")
    print(f"  Confidence: {regime.confidence:.2f}")
    print(f"  Trend regime: {regime.trend_regime.value}")


async def demo_layer3_research():
    """Demonstrate Layer 3: Quantitative Research."""
    print_header("LAYER 3: QUANTITATIVE RESEARCH")
    
    layer = QuantitativeResearchLayer()
    
    print_section("Generating Research Hypotheses")
    
    market_conditions = {
        'regime': MarketRegime.NORMAL,
        'volatility': 0.15,
        'trend_strength': 0.3
    }
    
    hypotheses = layer.run_research_cycle(market_conditions)
    
    print(f"\nHypotheses generated: {len(hypotheses)}")
    
    for i, hyp in enumerate(hypotheses[:5]):  # Show first 5
        print(f"\n{i+1}. {hyp.name}")
        print(f"   Family: {hyp.model_family.value}")
        print(f"   Expected edge: {hyp.expected_edge:.2f}")
        print(f"   Confidence: {hyp.confidence:.2f}")
    
    print_section("Model Families Used")
    families = set(h.model_family.value for h in hypotheses)
    for family in sorted(families):
        count = sum(1 for h in hypotheses if h.model_family.value == family)
        print(f"  - {family}: {count} hypotheses")


async def demo_layer4_allocation():
    """Demonstrate Layer 4: Portfolio Allocation."""
    print_header("LAYER 4: STRATEGIC PORTFOLIO ALLOCATION")
    
    layer = PortfolioAllocationLayer()
    
    print_section("Initializing Portfolio")
    
    strategy_ids = ['momentum_1', 'mean_reversion_1', 'volatility_1', 'trend_1']
    portfolio = layer.initialize(1000000, strategy_ids)
    
    print(f"\nTotal capital: ${portfolio.total_capital:,.2f}")
    print(f"Allocated capital: ${portfolio.allocated_capital:,.2f}")
    print(f"Cash reserve: ${portfolio.cash_reserve:,.2f}")
    
    print_section("Strategy Allocations")
    for alloc in portfolio.strategy_allocations:
        print(f"  - {alloc.strategy_id}: {alloc.weight:.2%} (${alloc.capital:,.2f})")
    
    print_section("Computing Optimal Allocation")
    
    expected_returns = {
        'momentum_1': 0.12,
        'mean_reversion_1': 0.08,
        'volatility_1': 0.15,
        'trend_1': 0.10
    }
    
    # Simple covariance matrix
    cov_matrix = np.array([
        [0.04, 0.01, 0.02, 0.015],
        [0.01, 0.03, 0.01, 0.01],
        [0.02, 0.01, 0.05, 0.02],
        [0.015, 0.01, 0.02, 0.035]
    ])
    
    optimal = layer.compute_allocation(expected_returns, cov_matrix, strategy_ids)
    
    print("\nOptimal allocation:")
    for strategy, weight in optimal.items():
        print(f"  - {strategy}: {weight:.2%}")


async def demo_layer5_risk():
    """Demonstrate Layer 5: Risk Governance."""
    print_header("LAYER 5: RISK GOVERNANCE")
    
    layer = RiskGovernanceLayer()
    
    print_section("Risk Limits")
    limits = layer.get_risk_limits()
    print(f"\nMax drawdown: {limits['max_drawdown']:.0%}")
    print(f"Max position size: {limits['max_position_size']:.0%}")
    print(f"Max leverage: {limits['max_leverage']:.1f}x")
    print(f"Max correlation: {limits['max_correlation']:.1f}")
    
    print_section("Validating Trade")
    
    trade = {
        'symbol': 'EURUSD',
        'direction': 'buy',
        'size': 50000,
        'portfolio_value': 1000000,
        'current_positions': {}
    }
    
    is_valid, reason = layer.validate_trade(trade)
    print(f"\nTrade validation: {'APPROVED' if is_valid else 'REJECTED'}")
    print(f"Reason: {reason}")
    
    print_section("Running Stress Tests")
    
    stress_results = layer.run_stress_tests(
        portfolio_value=1000000,
        portfolio_beta=1.2,
        leverage=1.5,
        liquidity_buffer=100000
    )
    
    for result in stress_results:
        print(f"\n{result.scenario.name}:")
        print(f"  Portfolio loss: {result.portfolio_loss:.2%}")
        print(f"  Survival probability: {result.survival_probability:.2%}")
        print(f"  Passes: {'Yes' if result.passes_limits else 'No'}")


async def demo_layer6_execution():
    """Demonstrate Layer 6: Execution."""
    print_header("LAYER 6: EXECUTION & MICROSTRUCTURE")
    
    layer = ExecutionLayer()
    
    print_section("Creating Execution Plan")
    
    from trading_bot.alphaalgo_institutional.layer6_execution import ExecutionUrgency
    
    plan = layer.create_execution_plan(
        symbol='EURUSD',
        direction='buy',
        quantity=100000,
        urgency=ExecutionUrgency.MEDIUM,
        regime=MarketRegime.NORMAL
    )
    
    print(f"\nSymbol: {plan.symbol}")
    print(f"Direction: {plan.direction}")
    print(f"Quantity: {plan.quantity:,}")
    print(f"Algorithm: {plan.algorithm}")
    print(f"Expected slippage: {plan.expected_slippage:.1f} bps")
    print(f"Max participation: {plan.max_participation_rate:.0%}")
    
    print_section("Submitting Order")
    
    order = layer.submit_order(plan)
    print(f"\nOrder ID: {order.id}")
    print(f"Status: {order.status.value}")
    print(f"Algorithm: {order.algorithm.value}")
    
    print_section("Transaction Cost Analysis")
    state = layer.get_layer_state()
    print(f"\nOrders submitted: {state['orders_submitted']}")
    print(f"Orders filled: {state['orders_filled']}")


async def demo_layer7_monitoring():
    """Demonstrate Layer 7: Monitoring & Evolution."""
    print_header("LAYER 7: MONITORING, AUDIT & EVOLUTION")
    
    layer = MonitoringEvolutionLayer()
    
    print_section("Logging Audit Entry")
    
    entry = layer.log_audit(
        event_type="trade",
        component="demo",
        action="executed",
        details={'symbol': 'EURUSD', 'quantity': 100000}
    )
    
    print(f"\nAudit entry ID: {entry.id}")
    print(f"Hash: {entry.hash[:16]}...")
    
    print_section("Verifying Audit Chain")
    
    is_valid, invalid_idx = layer.verify_audit_chain()
    print(f"\nAudit chain valid: {is_valid}")
    
    print_section("Analyzing Strategy for Decay")
    
    returns = np.random.normal(0.0003, 0.015, 100)
    signal_accuracy = [0.52 + np.random.normal(0, 0.02) for _ in range(100)]
    
    analysis = layer.analyze_strategy(
        strategy_id='test_strategy',
        returns=returns,
        signal_accuracy=signal_accuracy,
        current_regime=MarketRegime.NORMAL,
        strategy_regime=MarketRegime.NORMAL,
        regime_performance={MarketRegime.NORMAL: 0.5}
    )
    
    print(f"\nStrategy: {analysis['strategy_id']}")
    print(f"Decay signals: {len(analysis['decay_signals'])}")
    print(f"Needs attention: {analysis['needs_attention']}")


async def demo_idea_vectors():
    """Demonstrate Idea Vectors."""
    print_header("IDEA VECTORS (150+ CONSTRAINTS)")
    
    vectors = IdeaVectorConstraints()
    
    summary = vectors.get_summary()
    
    print_section("Vector Summary")
    print(f"\nTotal vectors: {summary['total_vectors']}")
    
    print("\nBy Category:")
    for category, count in summary['by_category'].items():
        print(f"  - {category}: {count}")
    
    print("\nBy Priority:")
    for priority, count in summary['by_priority'].items():
        print(f"  - {priority}: {count}")
    
    print_section("Critical Vectors (Must Always Consider)")
    critical = vectors.get_critical_vectors()
    for v in critical[:10]:  # Show first 10
        print(f"\n  [{v.id}] {v.name}")
        print(f"      {v.description}")


async def demo_research_loop():
    """Demonstrate Self-Evolving Research Loop."""
    print_header("SELF-EVOLVING RESEARCH LOOP")
    
    loop = SelfEvolvingResearchLoop()
    
    print_section("Pipeline Status")
    status = loop.get_pipeline_status()
    print(f"\nCandidates in pipeline: {status['candidates_in_pipeline']}")
    print(f"Live models: {status['live_models']}")
    print(f"Retired models: {status['retired_models']}")
    
    print_section("Running Research Iteration")
    
    market_conditions = {
        'regime': MarketRegime.NORMAL,
        'volatility': 0.15
    }
    
    # Register a simple hypothesis generator
    def generate_hypotheses(conditions):
        from trading_bot.alphaalgo_institutional.core_types import ModelHypothesis, ModelFamily
        return [
            ModelHypothesis(
                name="Test Momentum Model",
                model_family=ModelFamily.STOCHASTIC,
                expected_edge=0.8,
                confidence=0.6,
                mathematical_basis="Mean reversion",
                failure_modes=["Trending markets", "Low volatility"],
                data_requirements=["price", "volume"]
            )
        ]
    
    loop.register_hypothesis_generator(generate_hypotheses)
    
    iteration = await loop.run_iteration(market_conditions)
    
    print(f"\nIteration completed")
    print(f"Candidates processed: {iteration.candidates_processed}")
    print(f"Candidates advanced: {iteration.candidates_advanced}")
    print(f"Candidates rejected: {iteration.candidates_rejected}")
    
    print_section("Loop Metrics")
    metrics = loop.get_metrics()
    print(f"\nTotal iterations: {metrics['total_iterations']}")
    print(f"Hypotheses generated: {metrics['total_hypotheses_generated']}")
    print(f"Models validated: {metrics['total_models_validated']}")
    print(f"Models deployed: {metrics['total_models_deployed']}")


async def demo_full_system():
    """Demonstrate the full integrated system."""
    print_header("FULL SYSTEM INTEGRATION")
    
    print_section("Creating AlphaAlgo Institutional System")
    
    system = create_alphaalgo_institutional(
        trading_mode="paper",
        initial_capital=1000000.0
    )
    
    print(f"\nSystem created successfully")
    print(f"Trading mode: {system.trading_mode.value}")
    print(f"Initial capital: ${system.total_capital:,.2f}")
    
    print_section("Starting System")
    await system.start()
    print(f"System state: {system.state.value}")
    
    print_section("Running Health Check")
    health = system.run_health_check()
    print(f"\nOverall status: {health['overall_status']}")
    for component, status in health['components'].items():
        print(f"  - {component}: {status}")
    
    print_section("Analyzing Market")
    
    market_data = {
        'available_markets': [
            {'symbol': 'EURUSD', 'type': 'forex', 'avg_spread': 0.0001, 'daily_volume': 5e9},
            {'symbol': 'BTCUSD', 'type': 'crypto', 'avg_spread': 0.001, 'daily_volume': 50e9},
        ],
        'returns': np.random.normal(0.0005, 0.01, 100),
        'volatility': 0.15
    }
    
    analysis = system.analyze_market(market_data)
    print(f"\nCurrent regime: {analysis['regime']['primary']}")
    print(f"Regime confidence: {analysis['regime']['confidence']:.2f}")
    
    print_section("Running Risk Check")
    
    portfolio_data = {
        'value': 1000000,
        'returns': np.random.normal(0.0003, 0.01, 60),
        'positions': {'EURUSD': 50000},
        'leverage': 1.2,
        'beta': 1.1,
        'liquidity_buffer': 100000
    }
    
    risk_check = await system.run_risk_check(portfolio_data)
    print(f"\nRisk level: {risk_check['risk_level']}")
    print(f"Current drawdown: {risk_check['current_drawdown']:.2%}")
    print(f"Alerts: {risk_check['alerts']}")
    
    print_section("Making Trading Decision")
    
    signal = {
        'direction': 'buy',
        'quantity': 10000,
        'confidence': 0.7
    }
    
    decision = await system.make_trading_decision('EURUSD', signal, 'momentum_1')
    print(f"\nDecision ID: {decision.id}")
    print(f"Direction: {decision.direction}")
    print(f"Approved: {decision.approved}")
    print(f"Rationale: {decision.rationale}")
    print(f"Committee votes: {len(decision.committee_votes)}")
    
    print_section("System Explanation")
    print(system.explain_system()[:2000] + "...")  # First 2000 chars
    
    print_section("Comprehensive Report")
    report = system.get_comprehensive_report()
    print(f"\nSystem state: {report['system']['state']}")
    print(f"Trading mode: {report['system']['trading_mode']}")
    print(f"Market regime: {report['market']['regime']}")
    print(f"Risk level: {report['market']['risk_level']}")
    print(f"Active strategies: {report['portfolio']['active_strategies']}")
    print(f"Audit chain valid: {report['audit_chain_valid']}")
    
    print_section("Stopping System")
    await system.stop()
    print(f"System state: {system.state.value}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print(" ALPHAALGO INSTITUTIONAL SYSTEM DEMONSTRATION")
    print(" A Multi-Disciplinary Institutional Quantitative Research Platform")
    print("=" * 80)
    
    print("\nThis demo showcases the complete 7-layer architecture:")
    print("  1. Market Selection Layer")
    print("  2. Regime Detection Layer")
    print("  3. Quantitative Research Layer")
    print("  4. Strategic Portfolio Allocation Layer")
    print("  5. Risk Governance Layer")
    print("  6. Execution & Microstructure Layer")
    print("  7. Monitoring, Audit & Evolution Layer")
    print("\nPlus: Idea Vectors, Self-Evolving Research Loop, and Master Orchestrator")
    
    # Run individual layer demos
    await demo_layer1_market_selection()
    await demo_layer2_regime_detection()
    await demo_layer3_research()
    await demo_layer4_allocation()
    await demo_layer5_risk()
    await demo_layer6_execution()
    await demo_layer7_monitoring()
    await demo_idea_vectors()
    await demo_research_loop()
    
    # Run full system demo
    await demo_full_system()
    
    print_header("DEMO COMPLETE")
    print("\nThe AlphaAlgo Institutional system is fully operational.")
    print("\nCore Philosophy:")
    print("  - Markets are non-stationary, adversarial, and partially efficient")
    print("  - Prediction is unreliable; distribution control is superior")
    print("  - Capital preservation has veto power over opportunity")
    print("  - All models decay; systems must adapt or delete them")
    print("  - Risk is global, not local")
    print("  - No single model is ever trusted")
    print("  - Evolution is mostly subtraction, not addition")
    print("\nPrimary Objective: Long-term capital compounding under uncertainty.")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

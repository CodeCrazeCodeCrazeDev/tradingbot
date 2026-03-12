"""
Recursive Self-Evolution System Demo
=====================================

Demonstrates the comprehensive recursive self-evolution system that continuously
improves all aspects of the trading bot to achieve elite-level performance.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.recursive_evolution import (
    RecursiveEvolutionOrchestrator,
    EvolutionDimension,
    ParadigmType,
    DecisionType
)
import numpy as np
from datetime import datetime


async def demo_recursive_evolution():
    """Demonstrate recursive self-evolution system"""
    
    print("=" * 80)
    print("RECURSIVE SELF-EVOLUTION SYSTEM DEMO")
    print("=" * 80)
    print()
    
    # Initialize orchestrator
    print("1. Initializing Recursive Evolution Orchestrator...")
    config = {
        'meta_learning': {
            'base_learning_rate': 0.01,
            'exploration_rate': 0.2,
            'enable_meta_meta_learning': True
        },
        'reasoning': {
            'min_confidence': 0.7,
            'reasoning_depth': 5,
            'multi_perspective': True
        },
        'intelligence': {
            'timeframes': ['1m', '5m', '15m', '1h', '4h'],
            'min_liquidity': 0.3
        },
        'orderflow': {
            'min_block_size': 100000,
            'iceberg_window': 60
        },
        'fusion': {
            'min_consensus': 0.6,
            'adaptive_weighting': True
        }
    }
    
    orchestrator = await RecursiveEvolutionOrchestrator(config)
    print("✓ Orchestrator initialized with all components")
    print()
    
    # Demo 1: Run single evolution cycle
    print("2. Running Single Evolution Cycle...")
    print("-" * 80)
    
    context = {
        'market_conditions': 'volatile',
        'regime': 'trending',
        'volatility': 0.6
    }
    
    cycle_results = await orchestrator.run_evolution_cycle(context)
    
    print(f"Cycle #{cycle_results['cycle_number']} completed in {cycle_results['duration_seconds']:.2f}s")
    print()
    
    # Show phase results
    for phase_name, phase_results in cycle_results['phases'].items():
        print(f"  Phase: {phase_name}")
        if isinstance(phase_results, dict):
            if 'scores' in phase_results:
                print(f"    Scores: {phase_results['scores']}")
        elif isinstance(phase_results, list):
            print(f"    Results: {len(phase_results)} items")
        print()
    
    # Demo 2: Generate trading signal with evolved system
    print("3. Generating Trading Signal with Evolved System...")
    print("-" * 80)
    
    # Simulate market data
    symbol = "EURUSD"
    market_data = {
        'symbol': symbol,
        'price': 1.1000,
        'prices': np.random.randn(100).cumsum() + 1.1000,
        'volumes': np.random.randint(1000, 10000, 100),
        'bid_ask_spread': 0.0001,
        'volatility': 0.015,
        'indicators': {
            'rsi': 55,
            'macd': 0.0005,
            'macd_signal': 0.0003
        },
        'order_book': {
            'bids': [(1.0999, 50000), (1.0998, 75000), (1.0997, 100000)],
            'asks': [(1.1001, 60000), (1.1002, 80000), (1.1003, 90000)]
        },
        'trades': [
            {'price': 1.1000, 'size': 10000, 'side': 'buy'},
            {'price': 1.1000, 'size': 15000, 'side': 'buy'},
            {'price': 1.1001, 'size': 8000, 'side': 'sell'}
        ]
    }
    
    signal_context = {
        'regime': 'trending_bull',
        'volatility': 0.015,
        'news_sentiment': 0.3,
        'social_sentiment': 0.2,
        'institutional_activity': True
    }
    
    fused_decision = await orchestrator.generate_trading_signal(symbol, market_data, signal_context)
    
    print(f"Symbol: {fused_decision.symbol}")
    print(f"Decision: {fused_decision.final_decision.value}")
    print(f"Confidence: {fused_decision.confidence.overall_confidence:.2%}")
    print(f"Consensus: {fused_decision.consensus_level:.2%}")
    print(f"Risk/Reward: {fused_decision.risk_reward_ratio:.2f}")
    print()
    print(f"Recommendation: {fused_decision.recommended_action}")
    print(f"Position Size: {fused_decision.position_size_multiplier:.1%}")
    print()
    print("Primary Reasoning:")
    print(f"  {fused_decision.primary_reasoning}")
    print()
    print("Supporting Factors:")
    for i, factor in enumerate(fused_decision.supporting_factors[:3], 1):
        print(f"  {i}. {factor}")
    print()
    print("Risk Factors:")
    for i, risk in enumerate(fused_decision.risk_factors[:3], 1):
        print(f"  {i}. {risk}")
    print()
    
    # Show paradigm contributions
    print("Paradigm Contributions:")
    for paradigm_decision in fused_decision.paradigm_decisions:
        weight = fused_decision.paradigm_weights.get(paradigm_decision.paradigm, 0)
        print(f"  {paradigm_decision.paradigm.value:20s}: {paradigm_decision.decision.value:15s} "
              f"(confidence: {paradigm_decision.confidence:.2%}, weight: {weight:.2%})")
    print()
    
    # Demo 3: Show evolution metrics
    print("4. Evolution Metrics...")
    print("-" * 80)
    
    status = orchestrator.get_evolution_status()
    metrics = status['metrics']
    
    print(f"Total Cycles: {metrics['total_cycles']}")
    print(f"Total Proposals: {metrics['total_proposals']}")
    print(f"Successful Improvements: {metrics['successful_improvements']}")
    print(f"Failed Improvements: {metrics['failed_improvements']}")
    print(f"Success Rate: {metrics['success_rate']:.1%}")
    print(f"Learning Efficiency: {metrics['learning_efficiency']:.2%}")
    print(f"Overall Improvement: {metrics['overall_improvement']:.2%}")
    print()
    
    # Demo 4: Component statistics
    print("5. Component Statistics...")
    print("-" * 80)
    
    component_stats = status['component_stats']
    
    print("Reasoning Engine:")
    reasoning_stats = component_stats['reasoning']
    print(f"  Total Reasonings: {reasoning_stats.get('total_reasonings', 0)}")
    print(f"  Average Confidence: {reasoning_stats.get('average_confidence', 0):.2%}")
    print(f"  Average Time: {reasoning_stats.get('average_reasoning_time_ms', 0):.0f}ms")
    print()
    
    print("Market Intelligence:")
    intel_stats = component_stats['intelligence']
    print(f"  Total Reports: {intel_stats.get('total_reports', 0)}")
    print(f"  Average Tradability: {intel_stats.get('average_tradability', 0):.2%}")
    print(f"  Average Confidence: {intel_stats.get('average_confidence', 0):.2%}")
    print()
    
    print("Multi-Paradigm Fusion:")
    fusion_stats = component_stats['fusion']
    print(f"  Total Decisions: {fusion_stats.get('total_decisions', 0)}")
    print(f"  Average Confidence: {fusion_stats.get('average_confidence', 0):.2%}")
    print(f"  Average Consensus: {fusion_stats.get('average_consensus', 0):.2%}")
    print(f"  Average Risk/Reward: {fusion_stats.get('average_risk_reward', 0):.2f}")
    print()
    
    # Demo 5: Start continuous evolution (optional)
    print("6. Continuous Evolution (Optional)...")
    print("-" * 80)
    print("The system can run continuous evolution in the background.")
    print("To start: await orchestrator.start_continuous_evolution(interval_seconds=3600)")
    print("To stop: await orchestrator.stop_continuous_evolution()")
    print()
    
    # Demo 6: Export evolution report
    print("7. Exporting Evolution Report...")
    print("-" * 80)
    
    report_path = "recursive_evolution_report.json"
    orchestrator.export_evolution_report(report_path)
    print(f"✓ Evolution report exported to: {report_path}")
    print()
    
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("KEY FEATURES DEMONSTRATED:")
    print("✓ Recursive meta-learning that improves the improvement process")
    print("✓ Elite step-by-step reasoning with verification")
    print("✓ Deep market intelligence and regime classification")
    print("✓ Institutional order flow detection (blocks, icebergs, spoofing)")
    print("✓ Multi-paradigm decision fusion with adaptive weighting")
    print("✓ Continuous evolution cycles with 7 phases")
    print("✓ Comprehensive metrics and reporting")
    print()
    print("The system continuously discovers better ways to:")
    print("  • Reason about trades like an elite professional")
    print("  • Spot liquidity zones and institutional activity")
    print("  • Read order flow and detect manipulation")
    print("  • Classify market regimes and conditions")
    print("  • Generate profitable trading opportunities")
    print("  • Make disciplined, high-confidence decisions")
    print("  • Reject bad trades by default")
    print("  • Adapt to changing market conditions")
    print()


async def demo_specific_capabilities():
    """Demonstrate specific capabilities in detail"""
    
    print("\n" + "=" * 80)
    print("DETAILED CAPABILITY DEMONSTRATIONS")
    print("=" * 80)
    print()
    
    orchestrator = RecursiveEvolutionOrchestrator()
    
    # Demo: Elite Reasoning
    print("A. Elite Step-by-Step Reasoning")
    print("-" * 80)
    
    symbol = "BTCUSD"
    market_data = {
        'symbol': symbol,
        'price': 45000,
        'prices': [44000, 44200, 44500, 44800, 45000],
        'volumes': [100, 120, 150, 180, 200],
        'indicators': {'rsi': 65, 'macd': 50, 'macd_signal': 45}
    }
    
    reasoning = orchestrator.reasoning_engine.reason_about_trade(symbol, market_data)
    
    print(f"Reasoning Quality: {reasoning.reasoning_quality.value}")
    print(f"Quality Score: {reasoning.quality_score:.2%}")
    print(f"Decision: {reasoning.direction}")
    print(f"Confidence: {reasoning.decision_confidence:.2%}")
    print()
    print("Reasoning Steps:")
    for step in reasoning.steps:
        print(f"  Step {step.step_number}: {step.step_type.value}")
        print(f"    {step.description}")
        print(f"    Confidence: {step.confidence:.2%}, Verified: {step.verified}")
    print()
    
    # Demo: Market Intelligence
    print("B. Deep Market Intelligence")
    print("-" * 80)
    
    intel_report = orchestrator.intelligence.generate_intelligence_report(symbol, market_data)
    
    print(f"Current Regime: {intel_report.current_regime.value}")
    print(f"Regime Confidence: {intel_report.regime_confidence:.2%}")
    print(f"Tradability Score: {intel_report.tradability_score:.2%}")
    print(f"Sentiment: {intel_report.sentiment.value} ({intel_report.sentiment_score:.2f})")
    print(f"Liquidity: {intel_report.liquidity_map.overall_liquidity:.2%}")
    print(f"Opportunities Found: {len(intel_report.identified_opportunities)}")
    print()
    
    # Demo: Order Flow Analysis
    print("C. Institutional Order Flow Detection")
    print("-" * 80)
    
    market_data['trades'] = [
        {'price': 45000, 'size': 150000, 'side': 'buy'},  # Block trade
        {'price': 45001, 'size': 5000, 'side': 'buy'},
        {'price': 45001, 'size': 5000, 'side': 'buy'},  # Iceberg pattern
        {'price': 45001, 'size': 5000, 'side': 'buy'},
    ]
    
    orderflow_signals = orchestrator.orderflow.analyze_order_flow(symbol, market_data)
    
    print(f"Signals Detected: {len(orderflow_signals)}")
    for signal in orderflow_signals:
        print(f"  {signal.flow_type.value}:")
        print(f"    Strength: {signal.strength:.2%}")
        print(f"    Confidence: {signal.confidence:.2%}")
        print(f"    Expected Impact: {signal.expected_impact}")
        print(f"    Evidence: {signal.evidence[0] if signal.evidence else 'N/A'}")
    print()
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    print("\nStarting Recursive Self-Evolution System Demo...\n")
    
    # Run main demo
    asyncio.run(demo_recursive_evolution())
    
    # Run detailed capability demos
    asyncio.run(demo_specific_capabilities())
    
    print("\nDemo completed successfully!")
    print("\nTo use in your trading bot:")
    print("  from trading_bot.recursive_evolution import quick_start")
    print("  orchestrator = await quick_start({'auto_start': True})")
    print("  signal = await orchestrator.generate_trading_signal(symbol, market_data)")

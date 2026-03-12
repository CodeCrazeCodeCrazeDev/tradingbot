"""
Decision Layer Demo - Complete Usage Examples

Demonstrates the enhanced decision layer with integration, persistence, and analytics.

Author: AlphaAlgo Integration Team
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

logger = logging.getLogger(__name__)


async def demo_basic_usage():
    """Demo 1: Basic decision making"""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Decision Making")
    print("=" * 80)
    
    from trading_bot.decision_layer import (
        create_decision_bridge,
        DecisionPersistence,
        DecisionAnalytics
    )
    
    # Create decision bridge
    bridge = create_decision_bridge(parallel=True)
    
    # Create market data
    market_data = {
        'price': 1.0850,
        'volume': 1000000,
        'volatility': 0.15,
        'trend': 0.3,
        'momentum': 0.5,
        'sentiment': 0.2,
        'regime': 'trending',
        'timeframe': '1h'
    }
    
    # Create portfolio state
    portfolio_state = {
        'value': 100000.0,
        'position': 0.0,
        'drawdown': 0.05,
        'win_rate': 0.55,
        'recent_trades': []
    }
    
    # Analyze and get decision
    signal = await bridge.analyze_and_decide('EURUSD', market_data, portfolio_state)
    
    if signal:
        print(f"\n✓ Signal Generated:")
        print(f"  Symbol: {signal.symbol}")
        print(f"  Action: {signal.action.value}")
        print(f"  Confidence: {signal.confidence:.2%}")
        print(f"  Position Size: {signal.position_size:.2f}x")
        print(f"  Reasoning: {signal.reasoning}")
    else:
        print("\n✗ No signal generated (below thresholds)")
    
    # Get performance stats
    stats = bridge.get_performance_stats()
    print(f"\nPerformance Stats:")
    print(f"  Decisions Made: {stats['decisions_made']}")
    print(f"  Enabled Concepts: {stats['enabled_concepts']}/{stats['total_concepts']}")


async def demo_quick_analyze():
    """Demo 2: Quick analysis API"""
    print("\n" + "=" * 80)
    print("DEMO 2: Quick Analysis API")
    print("=" * 80)
    
    from trading_bot.decision_layer import quick_analyze
    
    # Quick analysis with minimal inputs
    signal = await quick_analyze(
        symbol='BTCUSD',
        price=45000,
        trend=0.5,
        momentum=0.3,
        volatility=0.2
    )
    
    if signal:
        print(f"\n✓ Quick Signal:")
        print(f"  {signal.symbol}: {signal.action.value}")
        print(f"  Confidence: {signal.confidence:.2%}")
        print(f"  Size: {signal.position_size:.2f}x")


async def demo_persistence():
    """Demo 3: Persistence and history"""
    print("\n" + "=" * 80)
    print("DEMO 3: Persistence and History")
    print("=" * 80)
    
    from trading_bot.decision_layer import (
        create_decision_bridge,
        DecisionPersistence
    )
    
    # Create bridge and persistence
    bridge = create_decision_bridge()
    persistence = DecisionPersistence()
    
    # Make a decision
    market_data = {
        'price': 1.0850,
        'trend': 0.4,
        'momentum': 0.3,
        'volatility': 0.15
    }
    
    portfolio_state = {
        'value': 100000.0,
        'position': 0.0,
        'drawdown': 0.0,
        'win_rate': 0.6,
        'recent_trades': []
    }
    
    signal = await bridge.analyze_and_decide('EURUSD', market_data, portfolio_state)
    
    if signal:
        # Get the decision from engine history
        if bridge.engine.decision_history:
            decision = bridge.engine.decision_history[-1]
            
            # Save to database
            decision_id = persistence.save_decision(decision, symbol='EURUSD')
            print(f"\n✓ Decision saved with ID: {decision_id}")
            
            # Save concept weights
            persistence.save_concept_weights(bridge.engine.concepts)
            print(f"✓ Saved weights for {len(bridge.engine.concepts)} concepts")
    
    # Get decision history
    history = persistence.get_decision_history(limit=10)
    print(f"\n✓ Retrieved {len(history)} decisions from history")
    
    if history:
        latest = history[0]
        print(f"\nLatest Decision:")
        print(f"  Timestamp: {latest['timestamp']}")
        print(f"  Action: {latest['action']}")
        print(f"  Confidence: {latest['confidence']:.2%}")
        print(f"  Consensus: {latest['consensus_level']:.2%}")


async def demo_analytics():
    """Demo 4: Analytics and performance monitoring"""
    print("\n" + "=" * 80)
    print("DEMO 4: Analytics and Performance Monitoring")
    print("=" * 80)
    
    from trading_bot.decision_layer import (
        DecisionPersistence,
        DecisionAnalytics,
        ConceptPerformanceTracker
    )
    
    # Create analytics
    persistence = DecisionPersistence()
    analytics = DecisionAnalytics(persistence)
    tracker = ConceptPerformanceTracker(persistence)
    
    # Get performance summary
    summary = persistence.get_performance_summary()
    print(f"\nPerformance Summary:")
    print(f"  Total Decisions: {summary['total_decisions']}")
    print(f"  Avg Confidence: {summary['avg_confidence']:.2%}")
    print(f"  Avg Consensus: {summary['avg_consensus']:.2%}")
    
    # Get concept rankings
    rankings = analytics.get_concept_rankings(min_samples=5)
    if rankings:
        print(f"\nTop 5 Concepts:")
        for i, concept in enumerate(rankings[:5], 1):
            print(f"  {i}. Concept #{concept['concept_id']}: "
                  f"{concept['accuracy']:.2%} accuracy "
                  f"({concept['total_decisions']} decisions)")
    
    # Get decision quality metrics
    quality = analytics.get_decision_quality_metrics(days=7)
    print(f"\nDecision Quality (Last 7 days):")
    print(f"  Total: {quality['total_decisions']}")
    print(f"  High Quality: {quality['high_quality_decisions']}")
    print(f"  Low Quality: {quality['low_quality_decisions']}")
    print(f"  Avg Confidence: {quality['avg_confidence']:.2%}")
    
    # Get real-time metrics
    metrics = analytics.get_real_time_metrics()
    print(f"\nReal-Time Metrics:")
    print(f"  Total Decisions: {metrics['total_decisions']}")
    print(f"  Today's Decisions: {metrics['today_decisions']}")


async def demo_performance_tracking():
    """Demo 5: Performance tracking and concept updates"""
    print("\n" + "=" * 80)
    print("DEMO 5: Performance Tracking")
    print("=" * 80)
    
    from trading_bot.decision_layer import create_decision_bridge
    
    bridge = create_decision_bridge()
    
    # Simulate making decisions and tracking performance
    market_scenarios = [
        {'price': 1.0850, 'trend': 0.5, 'momentum': 0.4, 'success': True},
        {'price': 1.0860, 'trend': 0.3, 'momentum': 0.2, 'success': True},
        {'price': 1.0840, 'trend': -0.2, 'momentum': -0.3, 'success': False},
        {'price': 1.0870, 'trend': 0.6, 'momentum': 0.5, 'success': True},
    ]
    
    for i, scenario in enumerate(market_scenarios, 1):
        market_data = {
            'price': scenario['price'],
            'trend': scenario['trend'],
            'momentum': scenario['momentum'],
            'volatility': 0.15
        }
        
        portfolio_state = {
            'value': 100000.0,
            'position': 0.0,
            'drawdown': 0.0,
            'win_rate': 0.5,
            'recent_trades': []
        }
        
        signal = await bridge.analyze_and_decide('EURUSD', market_data, portfolio_state)
        
        if signal and bridge.engine.decision_history:
            decision = bridge.engine.decision_history[-1]
            
            # Update concept performance
            bridge.update_concept_performance(decision, scenario['success'])
            
            print(f"\nScenario {i}: {signal.action.value} "
                  f"(Success: {scenario['success']})")
    
    # Show updated stats
    stats = bridge.get_performance_stats()
    print(f"\nUpdated Stats:")
    print(f"  Successful Trades: {stats['successful_trades']}")
    print(f"  Failed Trades: {stats['failed_trades']}")
    print(f"  Win Rate: {stats['win_rate']:.2%}")


async def demo_parallel_execution():
    """Demo 6: Parallel vs Sequential execution"""
    print("\n" + "=" * 80)
    print("DEMO 6: Parallel vs Sequential Execution")
    print("=" * 80)
    
    from trading_bot.decision_layer import create_decision_bridge
    import time
    
    market_data = {
        'price': 1.0850,
        'trend': 0.3,
        'momentum': 0.5,
        'volatility': 0.15
    }
    
    portfolio_state = {
        'value': 100000.0,
        'position': 0.0,
        'drawdown': 0.0,
        'win_rate': 0.5,
        'recent_trades': []
    }
    
    # Sequential execution
    print("\nSequential Execution:")
    bridge_seq = create_decision_bridge(parallel=False)
    start = time.time()
    signal_seq = await bridge_seq.analyze_and_decide('EURUSD', market_data, portfolio_state)
    duration_seq = time.time() - start
    print(f"  Duration: {duration_seq*1000:.1f}ms")
    if signal_seq:
        print(f"  Action: {signal_seq.action.value}")
    
    # Parallel execution
    print("\nParallel Execution:")
    bridge_par = create_decision_bridge(parallel=True)
    start = time.time()
    signal_par = await bridge_par.analyze_and_decide('EURUSD', market_data, portfolio_state)
    duration_par = time.time() - start
    print(f"  Duration: {duration_par*1000:.1f}ms")
    if signal_par:
        print(f"  Action: {signal_par.action.value}")
    
    speedup = duration_seq / duration_par if duration_par > 0 else 1.0
    print(f"\nSpeedup: {speedup:.2f}x")


async def demo_generate_report():
    """Demo 7: Generate analytics report"""
    print("\n" + "=" * 80)
    print("DEMO 7: Generate Analytics Report")
    print("=" * 80)
    
    from trading_bot.decision_layer import DecisionAnalytics, DecisionPersistence
    
    persistence = DecisionPersistence()
    analytics = DecisionAnalytics(persistence)
    
    # Generate report
    report = analytics.generate_performance_report(days=7)
    
    print("\n" + report)
    
    # Export to file
    output_path = "decision_layer_data/analytics_report.txt"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    analytics.export_analytics_report(output_path, days=7)
    print(f"\n✓ Report exported to: {output_path}")


async def demo_anomaly_detection():
    """Demo 8: Anomaly detection"""
    print("\n" + "=" * 80)
    print("DEMO 8: Anomaly Detection")
    print("=" * 80)
    
    from trading_bot.decision_layer import DecisionAnalytics, DecisionPersistence
    
    persistence = DecisionPersistence()
    analytics = DecisionAnalytics(persistence)
    
    # Detect anomalies
    anomalies = analytics.detect_anomalies(threshold=2.0)
    
    if anomalies:
        print(f"\n⚠ Found {len(anomalies)} anomalies:")
        for anomaly in anomalies[:5]:
            print(f"\n  Decision ID: {anomaly['decision_id']}")
            print(f"  Timestamp: {anomaly['timestamp']}")
            print(f"  Confidence: {anomaly['confidence']:.2%}")
            print(f"  Consensus: {anomaly['consensus']:.2%}")
            print(f"  Anomaly Type: {anomaly['anomaly_type']}")
            print(f"  Z-Score: {anomaly.get('confidence_zscore', 0):.2f}")
    else:
        print("\n✓ No anomalies detected")


async def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("DECISION LAYER - COMPLETE DEMO")
    print("=" * 80)
    print("\nDemonstrating enhanced decision layer with:")
    print("  - 100 decision concepts across 10 categories")
    print("  - Integration bridge for trading systems")
    print("  - Persistence layer for decisions and weights")
    print("  - Analytics and performance monitoring")
    print("  - Parallel execution optimization")
    
    try:
        await demo_basic_usage()
        await demo_quick_analyze()
        await demo_persistence()
        await demo_analytics()
        await demo_performance_tracking()
        await demo_parallel_execution()
        await demo_generate_report()
        await demo_anomaly_detection()
        
        print("\n" + "=" * 80)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

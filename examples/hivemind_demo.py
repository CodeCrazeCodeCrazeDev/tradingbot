"""
Trading Bot Hivemind Demo
============================================================

Demonstrates the collective intelligence system where multiple
specialized AI nodes work together to make trading decisions.

This demo shows:
1. Swarm initialization with multiple node types
2. Parallel analysis across all swarms
3. Consensus voting mechanisms
4. Emergent signal detection
5. Collective learning from outcomes
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.hivemind import (
    TradingHiveMind,
    HiveMindConfig,
    quick_start,
    NodeType,
    SwarmType,
    ConsensusMethod,
    SignalDirection,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def generate_mock_market_data(symbol: str, trend: str = "neutral") -> dict:
    """Generate mock market data for testing"""
    base_price = {
        'EURUSD': 1.0850,
        'GBPUSD': 1.2650,
        'USDJPY': 149.50,
        'BTCUSD': 65000.0,
    }.get(symbol, 1.0)
    
    # Generate OHLCV bars
    ohlcv = []
    price = base_price
    
    for i in range(100):
        if trend == "bullish":
            change = random.uniform(-0.001, 0.002)
        elif trend == "bearish":
            change = random.uniform(-0.002, 0.001)
        else:
            change = random.uniform(-0.0015, 0.0015)
        
        price *= (1 + change)
        
        ohlcv.append({
            'time': datetime.utcnow() - timedelta(hours=100-i),
            'open': price * (1 + random.uniform(-0.0005, 0.0005)),
            'high': price * (1 + random.uniform(0, 0.001)),
            'low': price * (1 - random.uniform(0, 0.001)),
            'close': price,
            'volume': random.randint(1000, 5000),
        })
    
    return {
        'ohlcv': ohlcv,
        'current_price': price,
        'atr': price * 0.005,
        'account_equity': 10000,
        'fundamentals': {
            'interest_rate_differential': random.uniform(-1, 2),
            'economic_outlook': random.choice(['bullish', 'neutral', 'bearish']),
            'central_bank_stance': random.choice(['hawkish', 'neutral', 'dovish']),
            'gdp_growth': random.uniform(1, 3),
        },
        'sentiment': {
            'overall_score': random.uniform(-0.5, 0.5),
            'fear_greed_index': random.randint(30, 70),
            'positioning': {
                'retail': {'long_percent': random.randint(40, 60)},
                'institutional': {'long_percent': random.randint(45, 55)},
            },
        },
        'macro': {
            'risk_appetite': random.choice(['risk_on', 'neutral', 'risk_off']),
            'dxy_trend': random.choice(['bullish', 'neutral', 'bearish']),
            'high_impact_events_24h': random.randint(0, 3),
            'yield_differential': random.uniform(-0.5, 1.5),
        },
        'microstructure': {
            'order_flow': {
                'imbalance': random.uniform(-0.3, 0.3),
            },
            'toxicity': random.uniform(0, 0.5),
            'large_orders': {
                'buy_count': random.randint(5, 20),
                'sell_count': random.randint(5, 20),
            },
        },
        'execution': {
            'spread': 0.0002,
            'avg_spread': 0.00018,
            'liquidity_score': random.uniform(0.5, 0.9),
            'session': random.choice(['london', 'new_york', 'asian']),
        },
        'risk': {
            'current_drawdown': random.uniform(0, 0.05),
            'daily_loss': random.uniform(0, 0.02),
            'potential_risk_reward': random.uniform(1.0, 3.0),
        },
    }


async def demo_basic_analysis():
    """Demo 1: Basic Hivemind Analysis"""
    print("\n" + "=" * 60)
    print("DEMO 1: BASIC HIVEMIND ANALYSIS")
    print("=" * 60)
    
    hivemind = await quick_start()
    
    # Analyze EURUSD
    symbol = "EURUSD"
    market_data = generate_mock_market_data(symbol, trend="bullish")
    
    print(f"\n🐝 Analyzing {symbol} with {hivemind._count_nodes()} nodes...")
    print("-" * 50)
    
    decision = await hivemind.analyze(symbol, market_data)
    
    print(decision.get_summary())
    
    return decision


async def demo_swarm_details():
    """Demo 2: Swarm-Level Analysis"""
    print("\n" + "=" * 60)
    print("DEMO 2: SWARM-LEVEL ANALYSIS")
    print("=" * 60)
    
    hivemind = await quick_start()
    
    symbol = "GBPUSD"
    market_data = generate_mock_market_data(symbol, trend="bearish")
    
    decision = await hivemind.analyze(symbol, market_data)
    
    print(f"\n🐝 Swarm Analysis for {symbol}")
    print("-" * 50)
    
    # Group votes by swarm/node type
    votes_by_type = {}
    for vote in decision.node_votes:
        node_type = vote.node_type.value
        if node_type not in votes_by_type:
            votes_by_type[node_type] = []
        votes_by_type[node_type].append(vote)
    
    for node_type, votes in votes_by_type.items():
        avg_signal = sum(v.direction.to_numeric() for v in votes) / len(votes)
        avg_conf = sum(v.confidence for v in votes) / len(votes)
        direction = "BULLISH" if avg_signal > 0.1 else ("BEARISH" if avg_signal < -0.1 else "NEUTRAL")
        
        print(f"\n   {node_type.upper()} SWARM ({len(votes)} nodes):")
        print(f"   Direction: {direction} (signal: {avg_signal:.2f})")
        print(f"   Avg Confidence: {avg_conf:.0%}")
        
        for vote in votes:
            print(f"     - {vote.node_id}: {vote.direction.value} ({vote.confidence:.0%})")


async def demo_consensus_methods():
    """Demo 3: Different Consensus Methods"""
    print("\n" + "=" * 60)
    print("DEMO 3: CONSENSUS METHODS COMPARISON")
    print("=" * 60)
    
    symbol = "USDJPY"
    market_data = generate_mock_market_data(symbol)
    
    methods = [
        ConsensusMethod.MAJORITY_VOTE,
        ConsensusMethod.WEIGHTED_VOTE,
        ConsensusMethod.BAYESIAN,
        ConsensusMethod.BORDA_COUNT,
    ]
    
    print(f"\n🐝 Comparing consensus methods for {symbol}")
    print("-" * 50)
    
    for method in methods:
        config = {'consensus_method': method}
        hivemind = await quick_start(config)
        
        decision = await hivemind.analyze(symbol, market_data)
        
        print(f"\n   {method.value.upper()}:")
        print(f"   Action: {decision.action}")
        print(f"   Direction: {decision.direction.value}")
        print(f"   Consensus: {decision.consensus_score:.0%}")
        print(f"   Confidence: {decision.confidence:.0%}")


async def demo_emergent_signals():
    """Demo 4: Emergent Signal Detection"""
    print("\n" + "=" * 60)
    print("DEMO 4: EMERGENT SIGNAL DETECTION")
    print("=" * 60)
    
    hivemind = await quick_start()
    
    # Create strongly trending market data
    symbol = "BTCUSD"
    market_data = generate_mock_market_data(symbol, trend="bullish")
    
    # Boost sentiment to create strong agreement
    market_data['sentiment']['overall_score'] = 0.6
    market_data['fundamentals']['economic_outlook'] = 'bullish'
    market_data['macro']['risk_appetite'] = 'risk_on'
    
    print(f"\n🐝 Detecting emergent signals for {symbol}")
    print("-" * 50)
    
    decision = await hivemind.analyze(symbol, market_data)
    
    print(f"\n   Emergent Signals Detected: {len(decision.emergent_signals)}")
    
    for signal in decision.emergent_signals:
        print(f"\n   📡 {signal.signal_type}")
        print(f"      Direction: {signal.direction.value}")
        print(f"      Strength: {signal.strength:.0%}")
        print(f"      Description: {signal.description}")
        print(f"      Source Nodes: {len(signal.source_nodes)}")


async def demo_collective_learning():
    """Demo 5: Collective Learning"""
    print("\n" + "=" * 60)
    print("DEMO 5: COLLECTIVE LEARNING")
    print("=" * 60)
    
    hivemind = await quick_start({'enable_learning': True})
    
    print("\n🐝 Simulating trading decisions and outcomes...")
    print("-" * 50)
    
    # Simulate multiple decisions
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    
    for i, symbol in enumerate(symbols):
        market_data = generate_mock_market_data(symbol)
        decision = await hivemind.analyze(symbol, market_data)
        
        # Simulate outcome
        was_correct = random.random() > 0.4  # 60% win rate
        profit = random.uniform(50, 200) if was_correct else random.uniform(-100, -30)
        
        hivemind.record_outcome(was_correct, profit)
        
        print(f"\n   Trade {i+1}: {symbol}")
        print(f"   Decision: {decision.action}")
        print(f"   Outcome: {'WIN' if was_correct else 'LOSS'} (${profit:.2f})")
    
    # Show learning results
    print("\n   📊 Collective Memory Stats:")
    stats = hivemind.collective_memory.get_stats()
    print(f"   Knowledge Items: {stats['knowledge_count']}")
    print(f"   Patterns: {stats['pattern_count']}")
    print(f"   Recent Decisions: {stats['recent_decisions']}")


async def demo_node_rankings():
    """Demo 6: Node Performance Rankings"""
    print("\n" + "=" * 60)
    print("DEMO 6: NODE PERFORMANCE RANKINGS")
    print("=" * 60)
    
    hivemind = await quick_start()
    
    # Run several analyses to build performance data
    for _ in range(5):
        symbol = random.choice(["EURUSD", "GBPUSD", "USDJPY"])
        market_data = generate_mock_market_data(symbol)
        await hivemind.analyze(symbol, market_data)
        
        # Record random outcomes
        hivemind.record_outcome(random.random() > 0.4, random.uniform(-100, 200))
    
    print("\n🐝 Node Performance Rankings")
    print("-" * 50)
    
    rankings = hivemind.get_node_rankings()
    
    print(f"\n   {'Rank':<6} {'Node ID':<25} {'Type':<15} {'Weight':<8} {'Accuracy':<10}")
    print("   " + "-" * 70)
    
    for i, node in enumerate(rankings[:10], 1):
        print(f"   {i:<6} {node['node_id']:<25} {node['node_type']:<15} {node['weight']:.2f}    {node['accuracy']:.0%}")


async def demo_full_workflow():
    """Demo 7: Full Trading Workflow"""
    print("\n" + "=" * 60)
    print("DEMO 7: FULL TRADING WORKFLOW")
    print("=" * 60)
    
    # Initialize with custom config
    config = {
        'consensus_method': ConsensusMethod.WEIGHTED_VOTE,
        'min_consensus': 0.5,
        'min_confidence': 0.4,
        'enable_learning': True,
        'require_risk_approval': True,
    }
    
    hivemind = await quick_start(config)
    
    print("\n🐝 Full Trading Workflow Simulation")
    print("-" * 50)
    
    symbol = "EURUSD"
    
    # Step 1: Market Analysis
    print("\n   Step 1: Market Analysis")
    market_data = generate_mock_market_data(symbol, trend="bullish")
    decision = await hivemind.analyze(symbol, market_data)
    
    print(f"   Action: {decision.action}")
    print(f"   Consensus: {decision.consensus_score:.0%}")
    print(f"   Confidence: {decision.confidence:.0%}")
    
    # Step 2: Trade Parameters
    if decision.action in ['BUY', 'SELL']:
        print("\n   Step 2: Trade Parameters")
        print(f"   Entry: {decision.entry_price:.5f}")
        print(f"   Stop Loss: {decision.stop_loss:.5f}")
        print(f"   Take Profit: {decision.take_profit:.5f}")
        print(f"   Position Size: {decision.position_size:.2f}")
    
    # Step 3: Node Votes Summary
    print("\n   Step 3: Node Votes Summary")
    bullish = sum(1 for v in decision.node_votes if v.direction.to_numeric() > 0.1)
    bearish = sum(1 for v in decision.node_votes if v.direction.to_numeric() < -0.1)
    neutral = len(decision.node_votes) - bullish - bearish
    print(f"   Bullish: {bullish}, Bearish: {bearish}, Neutral: {neutral}")
    
    # Step 4: Emergent Signals
    print("\n   Step 4: Emergent Signals")
    for signal in decision.emergent_signals[:3]:
        print(f"   - {signal.signal_type}: {signal.direction.value} ({signal.strength:.0%})")
    
    # Step 5: Record Outcome
    print("\n   Step 5: Simulated Outcome")
    was_correct = random.random() > 0.4
    profit = random.uniform(50, 150) if was_correct else random.uniform(-80, -20)
    hivemind.record_outcome(was_correct, profit)
    print(f"   Result: {'WIN' if was_correct else 'LOSS'} (${profit:.2f})")
    
    # Final Status
    print("\n   📊 Final Hivemind Status:")
    status = hivemind.get_status()
    print(f"   Total Analyses: {status['total_analyses']}")
    print(f"   Success Rate: {status['success_rate']:.0%}")
    print(f"   Avg Processing Time: {status['avg_processing_time_ms']:.0f}ms")


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("TRADING BOT HIVEMIND DEMO")
    print("Collective Intelligence for Trading Decisions")
    print("=" * 60)
    print("""
The Hivemind is a swarm intelligence system where multiple
specialized AI nodes work together to make trading decisions.

Key Features:
- 7 specialized swarms (Technical, Fundamental, Sentiment, etc.)
- 15+ individual nodes with unique expertise
- Multiple consensus mechanisms (Majority, Weighted, Bayesian)
- Emergent signal detection from collective behavior
- Collective learning from outcomes
    """)
    
    try:
        await demo_basic_analysis()
        await demo_swarm_details()
        await demo_consensus_methods()
        await demo_emergent_signals()
        await demo_collective_learning()
        await demo_node_rankings()
        await demo_full_workflow()
        
        print("\n" + "=" * 60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())

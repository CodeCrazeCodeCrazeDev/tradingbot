"""
Innovative Decision Layer Demo

Demonstrates the 100 decision-making concepts in action.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.decision_layer import (
    InnovativeDecisionEngine,
    DecisionContext,
    DecisionCategory,
    DecisionAction,
    create_decision_engine,
    quick_decide,
    ALL_CONCEPTS,
)


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def demo_basic_usage():
    """Basic usage of the decision engine"""
    print_header("BASIC USAGE")
    
    # Create engine
    engine = create_decision_engine()
    print(f"[OK] Created engine with {len(engine.concepts)} concepts")
    
    # Create context
    context = DecisionContext(
        symbol="EURUSD",
        price=1.0850,
        volume=1500000,
        volatility=0.25,
        trend=0.3,
        momentum=0.2,
        sentiment=0.1,
        regime="trending",
        timeframe="1H",
        portfolio_value=100000,
        current_position=0,
        drawdown=0.02,
        win_rate=0.55,
    )
    
    # Get decision
    decision = engine.decide(context)
    
    print(f"\n[DECISION RESULT]")
    print(f"   Action: {decision.final_action.value}")
    print(f"   Confidence: {decision.final_confidence:.2%}")
    print(f"   Consensus: {decision.consensus_level:.2%}")
    print(f"   Risk-Adjusted: {decision.risk_adjusted_action.value}")
    print(f"   Position Size: {decision.position_size_multiplier:.2f}x")
    
    print(f"\n[REASONING CHAIN]")
    for line in decision.reasoning_chain[:8]:
        print(f"   {line}")
    
    print(f"\n[+] Contributing Concepts: {len(decision.contributing_concepts)}")
    print(f"[-] Dissenting Concepts: {len(decision.dissenting_concepts)}")


def demo_different_scenarios():
    """Test different market scenarios"""
    print_header("DIFFERENT MARKET SCENARIOS")
    
    engine = create_decision_engine()
    
    scenarios = [
        {
            "name": "Strong Bullish Trend",
            "trend": 0.7, "momentum": 0.6, "sentiment": 0.5,
            "volatility": 0.2, "drawdown": 0.01
        },
        {
            "name": "Strong Bearish Trend",
            "trend": -0.7, "momentum": -0.6, "sentiment": -0.4,
            "volatility": 0.3, "drawdown": 0.05
        },
        {
            "name": "High Volatility Crisis",
            "trend": -0.3, "momentum": -0.5, "sentiment": -0.6,
            "volatility": 0.7, "drawdown": 0.15
        },
        {
            "name": "Ranging Market",
            "trend": 0.05, "momentum": -0.05, "sentiment": 0.1,
            "volatility": 0.15, "drawdown": 0.02
        },
        {
            "name": "Reversal Setup",
            "trend": -0.4, "momentum": 0.3, "sentiment": 0.2,
            "volatility": 0.25, "drawdown": 0.08
        },
    ]
    
    for scenario in scenarios:
        context = DecisionContext(
            symbol="EURUSD",
            price=1.0850,
            volume=1000000,
            volatility=scenario["volatility"],
            trend=scenario["trend"],
            momentum=scenario["momentum"],
            sentiment=scenario["sentiment"],
            regime="normal",
            timeframe="1H",
            portfolio_value=100000,
            current_position=0,
            drawdown=scenario["drawdown"],
            win_rate=0.5,
        )
        
        decision = engine.decide(context)
        
        print(f"\n>>> {scenario['name']}:")
        print(f"   Trend={scenario['trend']:.1f}, Mom={scenario['momentum']:.1f}, "
              f"Vol={scenario['volatility']:.1f}, DD={scenario['drawdown']:.1%}")
        print(f"   -> {decision.final_action.value} (conf={decision.final_confidence:.2f}, "
              f"consensus={decision.consensus_level:.2f})")


def demo_category_analysis():
    """Analyze decisions by category"""
    print_header("CATEGORY ANALYSIS")
    
    engine = create_decision_engine()
    
    context = DecisionContext(
        symbol="BTCUSD",
        price=45000,
        volume=5000000,
        volatility=0.4,
        trend=0.25,
        momentum=0.15,
        sentiment=0.3,
        regime="volatile",
        timeframe="4H",
        portfolio_value=50000,
        current_position=0,
        drawdown=0.03,
        win_rate=0.52,
    )
    
    decision = engine.decide(context)
    
    # Analyze by category
    category_results = {}
    for result in decision.contributing_concepts + decision.dissenting_concepts:
        cat = result.category.value
        if cat not in category_results:
            category_results[cat] = {'buy': 0, 'sell': 0, 'hold': 0}
        
        if 'buy' in result.action.value:
            category_results[cat]['buy'] += 1
        elif 'sell' in result.action.value:
            category_results[cat]['sell'] += 1
        else:
            category_results[cat]['hold'] += 1
    
    print("\n[DECISIONS BY CATEGORY]")
    for cat, counts in sorted(category_results.items()):
        total = sum(counts.values())
        print(f"   {cat:20s}: Buy={counts['buy']:2d} Sell={counts['sell']:2d} Hold={counts['hold']:2d} (Total: {total})")


def demo_quick_decide():
    """Quick decision function"""
    print_header("QUICK DECIDE")
    
    decision = quick_decide(
        symbol="GBPUSD",
        price=1.2650,
        trend=0.4,
        momentum=0.35,
        volatility=0.22,
        sentiment=0.25,
        volume=2000000,
        drawdown=0.01,
        win_rate=0.58,
    )
    
    print(f"Quick Decision: {decision.final_action.value}")
    print(f"Confidence: {decision.final_confidence:.2%}")
    print(f"Position Size: {decision.position_size_multiplier:.2f}x")


def demo_concept_list():
    """List all 100 concepts"""
    print_header("ALL 100 DECISION CONCEPTS")
    
    print(f"\nTotal Concepts: {len(ALL_CONCEPTS)}")
    
    categories = {}
    for ConceptClass in ALL_CONCEPTS:
        concept = ConceptClass()
        cat = concept.category.value
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((concept.concept_id, concept.name))
    
    for cat in sorted(categories.keys()):
        concepts = categories[cat]
        print(f"\n[{cat.upper()}] ({len(concepts)} concepts):")
        for cid, name in sorted(concepts):
            print(f"   {cid:3d}. {name}")


def demo_engine_stats():
    """Engine statistics"""
    print_header("ENGINE STATISTICS")
    
    engine = create_decision_engine()
    
    # Make some decisions to generate stats
    for i in range(5):
        context = DecisionContext(
            symbol="EURUSD",
            price=1.0850 + i * 0.001,
            volume=1000000,
            volatility=0.2 + i * 0.05,
            trend=0.3 - i * 0.1,
            momentum=0.2,
            sentiment=0.1,
            regime="normal",
            timeframe="1H",
            portfolio_value=100000,
            current_position=0,
            drawdown=0.02,
            win_rate=0.5,
        )
        engine.decide(context)
    
    stats = engine.get_concept_stats()
    
    print(f"\n[ENGINE STATISTICS]")
    print(f"   Total Concepts: {stats['total_concepts']}")
    print(f"   Enabled Concepts: {stats['enabled_concepts']}")
    print(f"   Decisions Made: {stats['decisions_made']}")
    
    print(f"\n[CONCEPTS PER CATEGORY]")
    for cat, count in sorted(stats['category_counts'].items()):
        print(f"   {cat:20s}: {count}")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print(" INNOVATIVE DECISION LAYER - 100 CONCEPTS DEMO")
    print(" AlphaAlgo Trading Bot")
    print("=" * 60)
    
    try:
        demo_basic_usage()
        demo_different_scenarios()
        demo_category_analysis()
        demo_quick_decide()
        demo_concept_list()
        demo_engine_stats()
        
        print_header("DEMO COMPLETE")
        print("\n[SUCCESS] All demos completed successfully!")
        print("\nThe Innovative Decision Layer provides:")
        print("  • 100 unique decision-making concepts")
        print("  • 10 categories of decision approaches")
        print("  • Weighted aggregation of all concepts")
        print("  • Confidence and consensus metrics")
        print("  • Risk-adjusted final decisions")
        print("  • Comprehensive reasoning chains")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

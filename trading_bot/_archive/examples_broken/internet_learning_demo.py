"""
Internet Learning System Demo
Demonstrates how the bot learns from verified internet sources
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.learning import (
    InternetLearningSystem,
    AdaptiveLearningAgent,
    SourceType,
    VerificationStatus
)


async def demo_internet_learning():
    pass
    """Demonstrate internet learning capabilities"""
    
    print("="*80)
    print("INTERNET LEARNING SYSTEM DEMO")
    print("="*80)
    
    # Initialize learning system
    config = {
        'verification_threshold': 0.7,
        'min_sources': 2,
        'storage_path': 'data/learned_knowledge'
    }
    
    learning_system = InternetLearningSystem(config)
    agent = AdaptiveLearningAgent(learning_system)
    
    # Demo 1: Learn about forex strategies
    print("\n" + "="*80)
    print("DEMO 1: Learning Forex Trading Strategies")
    print("="*80)
    
    knowledge = await learning_system.learn_from_internet(
        topic="forex trading strategies",
        max_sources=5
    )
    
    print(f"\n✅ Learned {len(knowledge)} items from internet sources")
    
    # Show verified knowledge
    verified = [k for k in knowledge if k.verification_status == VerificationStatus.VERIFIED]
    print(f"✅ Verified items: {len(verified)}")
    
    for item in verified[:3]:  # Show first 3
        print(f"\n📚 Knowledge Item:")
        print(f"   Title: {item.metadata.get('title', 'N/A')}")
        print(f"   Source: {item.verification_sources}")
        print(f"   Confidence: {item.confidence_score:.2%}")
        print(f"   Extracted Data: {list(item.extracted_data.keys())}")
    
    # Demo 2: Learn strategy for specific market condition
    print("\n" + "="*80)
    print("DEMO 2: Learning Strategy for High Volatility Market")
    print("="*80)
    
    strategy = await agent.learn_new_strategy("high volatility")
    
    if strategy:
    pass
        print(f"\n✅ Learned Strategy: {strategy['name']}")
        print(f"   Market Condition: {strategy['market_condition']}")
        print(f"   Techniques: {', '.join(strategy['techniques'][:5])}")
        print(f"   Confidence: {strategy['confidence']:.2%}")
        print(f"   Sources: {len(strategy['sources'])} verified sources")
    
    # Demo 3: Update market knowledge
    print("\n" + "="*80)
    print("DEMO 3: Updating Market Knowledge")
    print("="*80)
    
    print("\n🔄 Fetching latest market information...")
    await agent.update_market_knowledge()
    
    # Demo 4: Get strategy recommendations
    print("\n" + "="*80)
    print("DEMO 4: Strategy Recommendations")
    print("="*80)
    
    recommendations = agent.get_strategy_recommendations("volatility")
    
    print(f"\n✅ Found {len(recommendations)} strategy recommendations")
    for i, rec in enumerate(recommendations[:3], 1):
    pass
        print(f"\n{i}. {rec['name']}")
        print(f"   Confidence: {rec['confidence']:.2%}")
        print(f"   Techniques: {', '.join(rec['techniques'][:3])}")
    
    # Demo 5: Learning statistics
    print("\n" + "="*80)
    print("DEMO 5: Learning Statistics")
    print("="*80)
    
    stats = learning_system.get_learning_stats()
    
    print(f"\n📊 Learning System Statistics:")
    print(f"   Total Knowledge Items: {stats['total_items']}")
    print(f"   Verified Items: {stats['verified']}")
    print(f"   Pending Verification: {stats['pending']}")
    print(f"   Rejected Items: {stats['rejected']}")
    print(f"   Verification Rate: {stats['verification_rate']:.2%}")
    print(f"   Trusted Sources: {stats['trusted_sources']}")
    print(f"   Average Confidence: {stats['avg_confidence']:.2%}")
    
    # Demo 6: Show trusted sources
    print("\n" + "="*80)
    print("DEMO 6: Trusted Learning Sources")
    print("="*80)
    
    print(f"\n📡 {len(learning_system.trusted_sources)} Trusted Sources:")
    
    for source in learning_system.trusted_sources[:10]:
    pass
        print(f"\n   • {source.name}")
        print(f"     Type: {source.source_type.value}")
        print(f"     Reliability: {source.reliability_score:.2%}")
        print(f"     URL: {source.url[:60]}...")
    
    # Demo 7: Search specific knowledge
    print("\n" + "="*80)
    print("DEMO 7: Search Verified Knowledge")
    print("="*80)
    
    search_topics = ["momentum", "trend", "support"]
    
    for topic in search_topics:
    pass
        results = learning_system.get_verified_knowledge(topic)
        print(f"\n🔍 '{topic}': {len(results)} verified items found")
        
        if results:
    pass
            print(f"   Latest: {results[0].metadata.get('title', 'N/A')[:60]}...")
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    
    print("\n✅ Internet Learning System is ready to:")
    print("   • Learn from verified internet sources")
    print("   • Cross-verify information from multiple sources")
    print("   • Extract trading strategies and insights")
    print("   • Adapt to new market conditions")
    print("   • Maintain knowledge base with confidence scores")
    
    print("\n🚀 The bot can now learn and adapt from the internet safely!")


if __name__ == '__main__':
    pass
    asyncio.run(demo_internet_learning())

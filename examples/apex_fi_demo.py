"""
APEX-FI Demonstration
=====================

Demonstrates the Adaptive Financial Intelligence Infrastructure.

Genetic Parentage: Palantir × Two Sigma × Citadel
Architecture Class: Self-Improving · Self-Discovering · Self-Evolving
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def demo_constitutional_layer():
    """Demonstrate Constitutional Layer - Immutable Governance."""
    print("\n" + "=" * 60)
    print("DEMO 1: CONSTITUTIONAL LAYER")
    print("=" * 60)
    
    from trading_bot.apex_fi.constitutional_layer import get_constitutional_layer
    
    const = get_constitutional_layer()
    
    # Show constitutional constraints
    print("\nConstitutional Constraints (IMMUTABLE):")
    status = const.get_status()
    for key, value in status['constraints'].items():
        if isinstance(value, float) and value < 1:
            print(f"  - {key}: {value:.1%}")
        else:
            print(f"  - {key}: {value}")
    
    # Test drawdown constraint
    print("\nTesting Drawdown Constraint:")
    is_valid, msg = const.check_drawdown_constraint(
        current_nav=92000,
        high_water_mark=100000,
        level="book"
    )
    print("  Current NAV: $92,000")
    print("  High Water Mark: $100,000")
    print("  Drawdown: 8.0%")
    print(f"  [OK] Valid: {is_valid}" if is_valid else f"  [BREACH] {msg}")
    
    # Test concentration constraint
    print("\nTesting Concentration Constraint:")
    is_valid, msg = const.check_concentration_constraint(
        position_value=2500,
        portfolio_nav=100000
    )
    print("  Position Value: $2,500")
    print("  Portfolio NAV: $100,000")
    print("  Concentration: 2.5%")
    print(f"  [OK] Valid: {is_valid}" if is_valid else f"  [BREACH] {msg}")
    
    # Test validation gate
    print("\nTesting Validation Gate:")
    is_valid, msg = const.check_validation_gate(
        t_statistic=2.5,
        sandbox_days=35
    )
    print("  T-Statistic: 2.5")
    print("  Sandbox Days: 35")
    print(f"  [OK] Valid: {is_valid}" if is_valid else f"  [FAILED] {msg}")


async def demo_data_fabric():
    """Demonstrate Data Fabric - Palantir Bloodline."""
    print("\n" + "=" * 60)
    print("DEMO 2: DATA FABRIC & KNOWLEDGE GRAPH")
    print("=" * 60)
    
    from trading_bot.apex_fi.data_fabric import (
        get_data_fabric,
        Entity,
        EntityType,
        Relationship,
        RelationType,
        DataAtom
    )
    
    fabric = get_data_fabric()
    
    # Register data sources
    print("\n📡 Registering Data Sources:")
    fabric.register_data_source(
        source_id="bloomberg",
        source_type="market_data",
        freshness_threshold_seconds=1,
        quality_threshold=0.95
    )
    fabric.register_data_source(
        source_id="satellite_imagery",
        source_type="alternative_data",
        freshness_threshold_seconds=3600,
        quality_threshold=0.8
    )
    print("  ✅ Bloomberg (market data)")
    print("  ✅ Satellite Imagery (alternative data)")
    
    # Create entities
    print("\n🏢 Creating Knowledge Graph Entities:")
    
    # Apple Inc.
    apple = Entity(
        entity_id="AAPL",
        entity_type=EntityType.COMPANY
    )
    apple.set_attribute("name", DataAtom(
        value="Apple Inc.",
        source="bloomberg",
        timestamp=datetime.now()
    ))
    apple.set_attribute("market_cap", DataAtom(
        value=3000000000000,
        source="bloomberg",
        timestamp=datetime.now(),
        quality_score=0.98
    ))
    fabric.knowledge_graph.add_entity(apple)
    print("  ✅ Apple Inc. (AAPL)")
    
    # AAPL Stock
    aapl_stock = Entity(
        entity_id="AAPL_EQUITY",
        entity_type=EntityType.SECURITY
    )
    aapl_stock.set_attribute("ticker", DataAtom(
        value="AAPL",
        source="bloomberg",
        timestamp=datetime.now()
    ))
    aapl_stock.set_attribute("price", DataAtom(
        value=175.50,
        source="bloomberg",
        timestamp=datetime.now(),
        quality_score=0.99
    ))
    fabric.knowledge_graph.add_entity(aapl_stock)
    print("  ✅ AAPL Stock (Security)")
    
    # Tim Cook
    tim_cook = Entity(
        entity_id="TIM_COOK",
        entity_type=EntityType.EXECUTIVE
    )
    tim_cook.set_attribute("name", DataAtom(
        value="Tim Cook",
        source="bloomberg",
        timestamp=datetime.now()
    ))
    tim_cook.set_attribute("title", DataAtom(
        value="CEO",
        source="bloomberg",
        timestamp=datetime.now()
    ))
    fabric.knowledge_graph.add_entity(tim_cook)
    print("  ✅ Tim Cook (Executive)")
    
    # Create relationships
    print("\n🔗 Creating Relationships:")
    
    # Apple issues AAPL stock
    issues_rel = Relationship(
        source_id="AAPL",
        target_id="AAPL_EQUITY",
        relation_type=RelationType.ISSUES,
        valid_from=datetime(2020, 1, 1)
    )
    fabric.knowledge_graph.add_relationship(issues_rel)
    print("  ✅ AAPL → ISSUES → AAPL_EQUITY")
    
    # Apple employs Tim Cook
    employs_rel = Relationship(
        source_id="AAPL",
        target_id="TIM_COOK",
        relation_type=RelationType.EMPLOYS,
        valid_from=datetime(2011, 8, 24)
    )
    fabric.knowledge_graph.add_relationship(employs_rel)
    print("  ✅ AAPL → EMPLOYS → TIM_COOK")
    
    # Show graph stats
    print("\n📊 Knowledge Graph Statistics:")
    stats = fabric.knowledge_graph.get_stats()
    print(f"  • Total Entities: {stats['total_entities']}")
    print(f"  • Total Relationships: {stats['total_relationships']}")
    print(f"  • Graph Version: {stats['current_version']}")


async def demo_alpha_mining():
    """Demonstrate Alpha Mining Engine - Two Sigma Bloodline."""
    print("\n" + "=" * 60)
    print("DEMO 3: ALPHA MINING ENGINE")
    print("=" * 60)
    
    from trading_bot.apex_fi.alpha_mining import (
        get_alpha_mining_engine,
        FactorMetadata
    )
    
    engine = get_alpha_mining_engine()
    
    # Initialize genetic search
    print("\n🧬 Initializing Genetic Alpha Search:")
    engine.genetic_search.initialize_population()
    print(f"  ✅ Population Size: {engine.genetic_search.population_size}")
    print(f"  ✅ Mutation Rate: {engine.genetic_search.mutation_rate}")
    print(f"  ✅ Crossover Rate: {engine.genetic_search.crossover_rate}")
    
    # Show sample candidates
    print("\n📋 Sample Alpha Candidates:")
    for i, candidate in enumerate(engine.genetic_search._population[:5]):
        print(f"  {i+1}. {candidate.expression}")
        print(f"     Type: {candidate.expression_type.value}")
    
    # Add some factors to library
    print("\n📚 Adding Factors to Living Library:")
    
    factor1 = FactorMetadata(
        factor_id="momentum_20d",
        expression="rank(delta(close, 20))",
        discovery_timestamp=datetime.now(),
        current_sharpe=2.1,
        peak_sharpe=2.1
    )
    engine.factor_library.add_factor(factor1)
    print("  ✅ momentum_20d (Sharpe: 2.1)")
    
    factor2 = FactorMetadata(
        factor_id="mean_reversion_5d",
        expression="rank(-1 * ts_mean(returns, 5))",
        discovery_timestamp=datetime.now(),
        current_sharpe=1.8,
        peak_sharpe=1.8
    )
    engine.factor_library.add_factor(factor2)
    print("  ✅ mean_reversion_5d (Sharpe: 1.8)")
    
    factor3 = FactorMetadata(
        factor_id="volatility_breakout",
        expression="rank(close / ts_std(close, 20))",
        discovery_timestamp=datetime.now(),
        current_sharpe=1.5,
        peak_sharpe=1.5
    )
    engine.factor_library.add_factor(factor3)
    print("  ✅ volatility_breakout (Sharpe: 1.5)")
    
    # Show library stats
    print("\n📊 Factor Library Statistics:")
    stats = engine.factor_library.get_stats()
    print(f"  • Active Factors: {stats['total_active_factors']}")
    print(f"  • Retired Factors: {stats['total_retired_factors']}")
    print(f"  • Decay Threshold: {stats['decay_threshold']:.1%}")


async def demo_apex_orchestrator():
    """Demonstrate APEX Orchestrator."""
    print("\n" + "=" * 60)
    print("DEMO 4: APEX ORCHESTRATOR")
    print("=" * 60)
    
    from trading_bot.apex_fi.apex_orchestrator import get_apex_orchestrator
    
    apex = get_apex_orchestrator()
    
    # Initialize
    print("\n🚀 Initializing APEX-FI...")
    init_success = await apex.initialize()
    
    if init_success:
        print("  ✅ Initialization Complete")
        
        # Show status
        print("\n📊 System Status:")
        status = apex.get_status()
        print(f"  • State: {status['state']}")
        print(f"  • Initialization Complete: {status['initialization_complete']}")
        
        # Start system
        print("\n▶️  Starting APEX-FI...")
        start_success = await apex.start()
        
        if start_success:
            print("  ✅ System Running")
            
            # Wait a moment for metrics to update
            await asyncio.sleep(2)
            
            # Show performance report
            print("\n📈 Performance Report:")
            report = apex.get_performance_report()
            
            print("\n  North Star Targets:")
            targets = report['north_star_targets']
            print(f"    • Sharpe Ratio: {targets['sharpe_ratio_actual']:.2f} / {targets['sharpe_ratio_target']:.2f}")
            print(f"    • Max Drawdown: {targets['max_drawdown_actual']:.1%} / {targets['max_drawdown_limit']:.1%}")
            print(f"    • Alpha Hypotheses/Day: {targets['alpha_hypotheses_actual']} / {targets['alpha_hypotheses_target_per_day']}")
            print(f"    • Active Factors: {targets['active_factors_actual']:,} / {targets['active_factors_target']:,}")
            
            # Stop system
            print("\n⏹️  Stopping APEX-FI...")
            await apex.stop()
            print("  ✅ System Stopped")
    else:
        print("  ❌ Initialization Failed")


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("APEX-FI DEMONSTRATION")
    print("=" * 60)
    print("Genetic Parentage: Palantir × Two Sigma × Citadel")
    print("Architecture Class: Self-Improving · Self-Discovering · Self-Evolving")
    print("Constitutional Version: 4.0")
    print("=" * 60)
    
    # Run demos
    await demo_constitutional_layer()
    await demo_data_fabric()
    await demo_alpha_mining()
    await demo_apex_orchestrator()
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nAPEX-FI is operational with:")
    print("  ✅ Layer 1: Data Fabric & Ontology Engine")
    print("  ✅ Layer 2: Alpha Mining Engine")
    print("  ✅ Constitutional Layer: Immutable Governance")
    print("  ✅ APEX Orchestrator: System Coordination")
    print("\nRemaining layers (3-7) are ready for implementation.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

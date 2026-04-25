"""
AADS Demo Script

Demonstrates the core capabilities of the Autonomous Alpha Discovery System.

Usage:
    python -m trading_bot.aads.examples.demo

This script showcases:
1. Strategy genome creation and evolution
2. MicroFish swarm consensus
3. Causal world model interventions
4. Visual signal analysis
5. Multi-agent decision making
6. Maven decision briefs
7. Self-improvement cycles
"""

import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_strategy_genome():
    """Demonstrate strategy genome creation and Sakana-style merging"""
    print("\n" + "=" * 60)
    print("DEMO 1: Strategy Genome & Sakana Evolution")
    print("=" * 60)
    
    from trading_bot.aads.core.strategy_genome import (
        AADSStrategyGenome, StrategyGene, SignalGeneType,
        create_random_genome, merge_strategies
    )
    
    # Create two parent genomes
    parent_a = create_random_genome(num_signals=5)
    parent_a.sharpe_ratio = 1.8
    parent_a.max_drawdown = 0.12
    parent_a.win_rate = 0.58
    parent_a.compute_fitness()
    
    parent_b = create_random_genome(num_signals=4)
    parent_b.sharpe_ratio = 2.1
    parent_b.max_drawdown = 0.15
    parent_b.win_rate = 0.55
    parent_b.compute_fitness()
    
    print(f"\nParent A: {parent_a.genome_id[:8]}")
    print(f"  Signals: {len(parent_a.signal_genes)}")
    print(f"  Fitness: {parent_a.fitness_score:.4f}")
    
    print(f"\nParent B: {parent_b.genome_id[:8]}")
    print(f"  Signals: {len(parent_b.signal_genes)}")
    print(f"  Fitness: {parent_b.fitness_score:.4f}")
    
    # Sakana-style merge
    child = merge_strategies(parent_a, parent_b, merge_ratio=0.5)
    
    print(f"\nMerged Child: {child.genome_id[:8]}")
    print(f"  Generation: {child.generation}")
    print(f"  Parents: {child.parent_ids}")
    print(f"  Signals: {len(child.signal_genes)}")
    
    return child


def demo_microfish_swarm():
    """Demonstrate MicroFish swarm intelligence"""
    print("\n" + "=" * 60)
    print("DEMO 2: MicroFish Swarm Intelligence")
    print("=" * 60)
    
    from trading_bot.aads.core.microfish_swarm import MicroFishSwarm
    import numpy as np
    
    swarm = MicroFishSwarm()
    
    print(f"\nSwarm initialized with {len(swarm.fish)} fish")
    stats = swarm.get_swarm_stats()
    print(f"Category distribution: {stats['category_counts']}")
    
    # Generate market state
    market_state = {
        'prices': [100 + np.cumsum(np.random.randn(100) * 0.5).tolist()[-1] for _ in range(100)],
        'volumes': [1e6 + np.random.randn() * 1e5 for _ in range(100)],
        'vix': 22.5,
        'regime': 'normal',
        'sentiment_score': 0.3,
        'yields': {'2y': 4.5, '10y': 4.2},
        'options': {'call_volume': 50000, 'put_volume': 45000}
    }
    
    # Get swarm consensus
    signal = swarm.get_consensus('AAPL', market_state)
    
    print(f"\nSwarm Consensus for AAPL:")
    print(f"  Direction: {signal.direction:+.2f}")
    print(f"  Strength: {signal.strength:.2%}")
    print(f"  Dissent Ratio: {signal.dissent_ratio:.2%}")
    print(f"  Bulls: {signal.bull_count}, Bears: {signal.bear_count}, Neutral: {signal.neutral_count}")
    print(f"  Dominant Fish: {signal.dominant_fish}")
    
    return signal


def demo_causal_model():
    """Demonstrate causal world model and do-calculus"""
    print("\n" + "=" * 60)
    print("DEMO 3: Causal World Model (do-calculus)")
    print("=" * 60)
    
    from trading_bot.aads.core.causal_world_model import CausalWorldModel
    
    model = CausalWorldModel()
    
    print(f"\nCausal graph: {len(model.nodes)} nodes, {len(model.edges)} edges")
    
    # Set current values
    model.set_node_value("Fed_Rate", 5.25)
    model.set_node_value("VIX", 20.0)
    model.set_node_value("Oil_Price", 75.0)
    
    # Run intervention: What if Fed raises rates +50bp?
    print("\n--- Intervention: Fed Rate +50bp ---")
    result = model.intervene(
        variable="Fed_Rate",
        value=5.75,
        observe=["Bond_Yields", "USD_Strength", "Equity_Valuations", "Credit_Spreads"]
    )
    
    print("Counterfactual effects:")
    for var, effect in result.causal_effects.items():
        print(f"  {var}: {effect:+.4f}")
    
    # Run full trade analysis
    print("\n--- Counterfactual Trade Analysis ---")
    scenarios = model.counterfactual_trade_analysis(
        trade_asset="SPY",
        trade_direction="long",
        current_exposure=0.02
    )
    
    for scenario_name, scenario_result in scenarios.items():
        print(f"\n{scenario_name}:")
        for var, effect in list(scenario_result.causal_effects.items())[:3]:
            print(f"  {var}: {effect:+.4f}")
    
    return result


def demo_vision_pipeline():
    """Demonstrate OpenCLIP visual intelligence"""
    print("\n" + "=" * 60)
    print("DEMO 4: OpenCLIP Visual Intelligence")
    print("=" * 60)
    
    from trading_bot.aads.core.openclip_vision import OpenCLIPPipeline
    
    pipeline = OpenCLIPPipeline()
    
    print(f"\nVisual categories: {len(pipeline.FINANCIAL_CATEGORIES)}")
    
    # Analyze a hypothetical chart image
    signal = pipeline.analyze("charts/AAPL_daily.png")
    
    print(f"\nVisual Signal Analysis:")
    print(f"  Category: {signal.category.value}")
    print(f"  Classification: {signal.top_classification[:50]}...")
    print(f"  Confidence: {signal.confidence:.2%}")
    print(f"  Sentiment: {signal.sentiment.value}")
    print(f"  Sentiment Score: {signal.sentiment_score:+.2f}")
    
    # Analyze satellite imagery
    sat_result = pipeline.analyze_satellite_imagery(
        image_path="satellite/walmart_parking.png",
        target_type="parking_lot"
    )
    
    print(f"\nSatellite Analysis (Parking Lot):")
    print(f"  Activity Level: {sat_result['activity_level']:.2%}")
    print(f"  Alpha Signal: {sat_result['alpha_signal']:+.2f}")
    print(f"  Affected Sectors: {sat_result['affected_sectors']}")
    
    return signal


def demo_multi_agent():
    """Demonstrate multi-agent decision making"""
    print("\n" + "=" * 60)
    print("DEMO 5: Multi-Agent Decision Making")
    print("=" * 60)
    
    from trading_bot.aads.core.aip_agents import (
        ResearchAgent, BullAgent, BearAgent, RiskAgent, SimulationAgent
    )
    
    # Initialize agents
    research = ResearchAgent()
    bull = BullAgent()
    bear = BearAgent()
    risk = RiskAgent()
    simulation = SimulationAgent()
    
    asset = "NVDA"
    current_price = 875.0
    
    # Research phase
    print(f"\n--- Research Agent ---")
    research_output = research.execute({
        'asset': asset,
        'market_state': {'regime': 'bull', 'vix': 18}
    })
    print(f"Hypothesis: {research_output.data.get('hypothesis', {}).get('thesis', 'N/A')[:80]}...")
    print(f"Confidence: {research_output.confidence:.2%}")
    
    # Bull case
    print(f"\n--- Bull Agent ---")
    bull_output = bull.execute({
        'hypothesis': research_output.data,
        'asset': asset,
        'current_price': current_price
    })
    print(f"Thesis: {bull_output.data.get('thesis', 'N/A')[:80]}...")
    print(f"Price Targets: ${bull_output.data.get('price_target_1', 0):.2f} / ${bull_output.data.get('price_target_2', 0):.2f}")
    
    # Bear case
    print(f"\n--- Bear Agent ---")
    bear_output = bear.execute({
        'bull_case': bull_output.data,
        'asset': asset,
        'current_price': current_price
    })
    print(f"Counter-thesis: {bear_output.data.get('counter_thesis', 'N/A')[:80]}...")
    print(f"Tail Risks: {len(bear_output.data.get('tail_risks', []))}")
    
    # Simulation
    print(f"\n--- Simulation Agent ---")
    sim_output = simulation.execute({
        'asset': asset,
        'position_size': 0.02,
        'current_price': current_price
    })
    mc = sim_output.data.get('simulations', {}).get('monte_carlo', {})
    print(f"Monte Carlo P10/P50/P90: ${mc.get('p10', 0):.2f} / ${mc.get('p50', 0):.2f} / ${mc.get('p90', 0):.2f}")
    print(f"VaR 95: {mc.get('var_95', 0):.2%}")
    
    # Risk check
    print(f"\n--- Risk Agent ---")
    risk_output = risk.execute({
        'trade': {'position_size': 0.02, 'sector': 'Technology'},
        'portfolio': {'sector_exposures': {'Technology': 0.05}, 'current_drawdown': 0.03},
        'simulation_results': sim_output.data
    })
    print(f"Approved: {risk_output.data.get('approved', False)}")
    print(f"Recommended Size: {risk_output.data.get('recommended_position_size', 0):.2%}")
    
    return {
        'research': research_output,
        'bull': bull_output,
        'bear': bear_output,
        'simulation': sim_output,
        'risk': risk_output
    }


def demo_decision_brief():
    """Demonstrate Maven decision brief generation"""
    print("\n" + "=" * 60)
    print("DEMO 6: Maven Decision Brief")
    print("=" * 60)
    
    from trading_bot.aads.orchestrator import create_aads
    
    aads = create_aads(mode="research", initial_capital=1_000_000.0)
    
    # Generate decision brief
    brief = aads.generate_decision_brief(
        asset="MSFT",
        current_price=415.0
    )
    
    # Print formatted brief
    print(brief.to_formatted_string())
    
    return brief


def demo_self_improvement():
    """Demonstrate self-improvement engine"""
    print("\n" + "=" * 60)
    print("DEMO 7: Self-Improvement Engine")
    print("=" * 60)
    
    from trading_bot.aads.core.self_improvement import SelfImprovementEngine, ComponentRegistry
    
    registry = ComponentRegistry()
    engine = SelfImprovementEngine(registry=registry)
    
    print(f"\nComponents registered: {len(registry.components)}")
    
    # Simulate some metrics
    for component_name in list(registry.components.keys())[:5]:
        for _ in range(30):
            import numpy as np
            value = registry.components[component_name].threshold * np.random.uniform(0.8, 1.2)
            registry.record_metric(component_name, value)
    
    # Get health report
    health = engine.get_component_health_report()
    
    print(f"\nComponent Health Report:")
    print(f"  Total Components: {health['total_components']}")
    print(f"  Healthy: {health['healthy_components']}")
    print(f"  Unhealthy: {health['unhealthy_components']}")
    print(f"  Health Rate: {health['health_rate']:.2%}")
    
    # Run improvement cycle
    print("\n--- Running Self-Improvement Cycle ---")
    cycle = engine.run_weekly_improvement_cycle()
    
    if cycle:
        print(f"Improvement cycle: {cycle.cycle_id}")
        print(f"  Component: {cycle.component_name}")
        print(f"  Status: {cycle.status.value}")
        print(f"  Improvement: {cycle.improvement_pct:.2%}")
    else:
        print("No improvement needed - all components above threshold")
    
    return health


async def demo_discovery_loop():
    """Demonstrate the autonomous discovery loop"""
    print("\n" + "=" * 60)
    print("DEMO 8: Autonomous Alpha Discovery Loop")
    print("=" * 60)
    
    from trading_bot.aads.core.alpha_discovery_loop import AutonomousAlphaDiscoveryLoop
    
    loop = AutonomousAlphaDiscoveryLoop(initial_capital=1_000_000.0)
    
    print("\nRunning 5 discovery iterations...")
    
    for i in range(5):
        await loop._run_iteration()
        
        status = loop.get_loop_status()
        print(f"\nIteration {i+1}:")
        print(f"  Phase: {status['current_phase']}")
        print(f"  Discoveries: {status['total_discoveries']}")
        print(f"  Deployed: {status['deployed_count']}")
        print(f"  Evolution Gen: {status['evolution_generation']}")
    
    # Get performance report
    report = loop.get_performance_report()
    print(f"\nPerformance Report:")
    print(f"  Deployed Strategies: {report.get('deployed_strategies', 0)}")
    print(f"  Total Allocation: {report.get('total_allocation', 0):.2%}")
    print(f"  Portfolio Drawdown: {report.get('portfolio_drawdown', 0):.2%}")
    
    return report


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("AADS - Autonomous Alpha Discovery System")
    print("Level 6 Financial AI Infrastructure Demo")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    
    try:
        # Run synchronous demos
        demo_strategy_genome()
        demo_microfish_swarm()
        demo_causal_model()
        demo_vision_pipeline()
        demo_multi_agent()
        demo_decision_brief()
        demo_self_improvement()
        
        # Run async demo
        asyncio.run(demo_discovery_loop())
        
        print("\n" + "=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    main()

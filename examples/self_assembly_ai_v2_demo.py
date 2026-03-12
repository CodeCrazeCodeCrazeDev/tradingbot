"""
Self-Assembly AI V2 Demo
========================

Demonstrates the complete self-assembly AI system with:
- Code Genetics (DNA-like strategy evolution)
- Swarm Intelligence (collective optimization)
- Neural Architecture Search (auto-designing networks)
- Emergent Behavior (complex patterns from simple rules)
- Strategy Factory (self-replicating strategies)
- Component Auto-Wiring (self-configuring system)
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.self_assembly_ai import (
    # V2 Components
    CodeGenetics,
    create_code_genetics,
    SwarmIntelligence,
    create_swarm_intelligence,
    NeuralArchitectureSearch,
    create_nas_engine,
    EmergentBehaviorEngine,
    create_emergent_behavior_engine,
    StrategyFactory,
    create_strategy_factory,
    AutoWiringContainer,
    create_autowiring_container,
    SelfAssemblyOrchestratorV2,
    create_self_assembly_v2,
    AssemblyConfig,
    # Types
    Chromosome,
    Position,
    Architecture,
    Strategy,
    StrategyType,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title: str) -> None:
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


async def demo_code_genetics():
    """Demonstrate Code Genetics - DNA-like strategy evolution"""
    print_header("CODE GENETICS - DNA-Like Strategy Evolution")
    
    print("Creating genetic code system...")
    genetics = create_code_genetics({
        'population_size': 20,
        'mutation_rate': 0.15,
        'crossover_rate': 0.7,
    })
    
    print(f"Initial population: {len(genetics.gene_pool.population)} chromosomes")
    
    # Define fitness function
    def fitness_func(chromosome: Chromosome) -> float:
        config = chromosome.express()
        fitness = 0.5
        
        # Evaluate parameters
        if 'rsi_period' in config:
            if 10 <= config['rsi_period'] <= 20:
                fitness += 0.15
        
        if 'risk' in config:
            risk = config['risk'].get('risk_per_trade', 0.02)
            if 0.01 <= risk <= 0.025:
                fitness += 0.15
        
        if 'exits' in config:
            tp = config['exits'].get('take_profit_atr', 2)
            sl = config['exits'].get('stop_loss_atr', 1)
            if tp > sl * 1.5:
                fitness += 0.2
        
        return min(1.0, fitness)
    
    # Evolve for several generations
    print("\nEvolving strategies through genetic algorithms...")
    for gen in range(5):
        report = genetics.evolve_generation(fitness_func)
        print(f"  Generation {gen + 1}: Best fitness = {report['best_fitness']:.4f}, "
              f"Diversity = {report['diversity_score']:.2f}")
    
    # Get best strategy
    best = genetics.get_best_strategy()
    print(f"\nBest evolved strategy configuration:")
    for key, value in best.items():
        print(f"  {key}: {value}")
    
    # Export DNA
    best_chromosome = genetics.gene_pool.get_best_chromosome()
    dna_hash = best_chromosome.get_dna_hash()
    print(f"\nDNA Hash: {dna_hash}")
    print(f"Generation: {best_chromosome.generation}")
    print(f"Mutations applied: {best_chromosome.mutations_applied}")


async def demo_swarm_intelligence():
    """Demonstrate Swarm Intelligence - Collective optimization"""
    print_header("SWARM INTELLIGENCE - Collective Optimization")
    
    # Define parameter bounds
    bounds = [
        (5, 50),    # RSI period
        (60, 90),   # RSI overbought
        (10, 40),   # RSI oversold
        (5, 50),    # MA fast
        (20, 200),  # MA slow
    ]
    
    print("Creating hybrid swarm (PSO + ACO + ABC)...")
    swarm = create_swarm_intelligence(
        swarm_type="hybrid",
        dimensions=len(bounds),
        bounds=bounds,
        config={'max_iterations': 100}
    )
    
    report = swarm.get_report()
    print(f"Total agents: {report['total_agents']}")
    print(f"Agent types: {report['agent_types']}")
    
    # Define fitness function
    def position_fitness(position: Position) -> float:
        dims = position.dimensions
        fitness = 0.5
        
        # RSI period in optimal range
        if 10 <= dims[0] <= 20:
            fitness += 0.2
        
        # RSI levels properly separated
        if dims[1] > dims[2] + 30:
            fitness += 0.15
        
        # MA crossover valid
        if dims[3] < dims[4]:
            fitness += 0.15
        
        return fitness
    
    # Run optimization
    print("\nRunning swarm optimization...")
    for i in range(20):
        result = swarm.step(position_fitness)
        if (i + 1) % 5 == 0:
            print(f"  Iteration {i + 1}: Best = {result['global_best_fitness']:.4f}, "
                  f"Diversity = {result['diversity']:.4f}")
    
    # Get best solution
    best = swarm.get_best_solution()
    print(f"\nBest parameters found:")
    param_names = ['RSI Period', 'RSI Overbought', 'RSI Oversold', 'MA Fast', 'MA Slow']
    for name, value in zip(param_names, best.dimensions):
        print(f"  {name}: {value:.2f}")
    print(f"Fitness: {best.fitness:.4f}")


async def demo_neural_architecture_search():
    """Demonstrate Neural Architecture Search"""
    print_header("NEURAL ARCHITECTURE SEARCH - Auto-Designing Networks")
    
    print("Creating NAS engine...")
    nas = create_nas_engine(
        input_shape=(100, 10),  # 100 timesteps, 10 features
        output_shape=(3,),      # Buy, Hold, Sell
        config={
            'population_size': 15,
            'elite_size': 3,
        }
    )
    
    # Initialize population
    nas.initialize_population()
    print(f"Initial population: {len(nas.population)} architectures")
    
    # Define fitness function (simulated)
    import random
    def arch_fitness(arch: Architecture) -> float:
        fitness = 0.3
        
        # Prefer architectures with LSTM
        has_lstm = any(l.layer_type.value == 'lstm' for l in arch.layers)
        if has_lstm:
            fitness += 0.2
        
        # Prefer moderate depth
        if 3 <= len(arch.layers) <= 6:
            fitness += 0.15
        
        # Prefer dropout
        has_dropout = any(l.dropout_rate > 0 for l in arch.layers)
        if has_dropout:
            fitness += 0.1
        
        # Penalize too many parameters
        params = arch.estimate_total_params()
        if params < 1_000_000:
            fitness += 0.15
        
        fitness += random.uniform(-0.1, 0.1)
        return max(0, min(1, fitness))
    
    # Search for best architecture
    print("\nSearching for optimal architecture...")
    for gen in range(10):
        nas.evaluate_population(arch_fitness, use_predictor=True)
        nas.evolve()
        
        report = nas.get_report()
        print(f"  Generation {gen + 1}: Best = {report['best_fitness']:.4f}, "
              f"Avg params = {report['avg_params']:,.0f}")
    
    # Get best architecture
    best = nas.get_best_architecture()
    print(f"\nBest architecture found:")
    print(f"  Layers: {len(best.layers)}")
    print(f"  Total parameters: {best.estimate_total_params():,}")
    print(f"  Fitness: {best.fitness:.4f}")
    print(f"  Architecture:")
    for layer in best.layers:
        print(f"    - {layer.layer_type.value}: units={layer.units}, "
              f"activation={layer.activation.value}")


async def demo_emergent_behavior():
    """Demonstrate Emergent Behavior Engine"""
    print_header("EMERGENT BEHAVIOR - Complex Patterns from Simple Rules")
    
    print("Creating emergent behavior engine...")
    emergent = create_emergent_behavior_engine({
        'ca_width': 20,
        'ca_height': 20,
    })
    
    # Run cellular automata
    print("\nRunning cellular automata (Game of Life variant)...")
    for i in range(20):
        result = emergent.step()
        if (i + 1) % 5 == 0:
            ca = result['ca']
            print(f"  Step {i + 1}: Alive cells = {ca['alive_count']}, "
                  f"Pattern = {ca['pattern_type']}")
    
    # Get emergent signal
    signal = emergent.get_emergent_signal()
    print(f"\nEmergent trading signal:")
    print(f"  Pattern type: {signal['pattern_type']}")
    print(f"  System health: {signal['system_health']:.2f}")
    print(f"  Is stable: {signal['is_stable']}")
    print(f"  Direction: {signal['direction']}")
    print(f"  Confidence: {signal['confidence']:.2f}")
    
    # Autopoiesis status
    report = emergent.get_report()
    print(f"\nAutopoiesis (self-maintaining organisms):")
    print(f"  Population: {report['autopoiesis']['population']}")
    print(f"  Total births: {report['autopoiesis']['total_births']}")
    print(f"  Total deaths: {report['autopoiesis']['total_deaths']}")


async def demo_strategy_factory():
    """Demonstrate Strategy Factory - Self-replicating strategies"""
    print_header("STRATEGY FACTORY - Self-Replicating Strategies")
    
    print("Creating strategy factory...")
    factory = create_strategy_factory({
        'max_population': 30,
        'min_population': 5,
    })
    
    report = factory.get_report()
    print(f"Initial population: {report['current_population']} strategies")
    print(f"Strategy types: {report['strategies_by_type']}")
    
    # Simulate trading results
    print("\nSimulating trading for strategies...")
    import random
    
    for _ in range(50):
        # Pick a random strategy
        active = factory.get_active_strategies()
        if not active:
            break
        
        strategy = random.choice(active)
        
        # Simulate trade result
        pnl = random.gauss(10, 50)  # Mean $10, std $50
        trade_result = {
            'pnl': pnl,
            'drawdown': abs(min(0, pnl)) / 1000,
        }
        
        factory.update_strategy_state(strategy.strategy_id, trade_result)
    
    # Natural selection
    print("\nApplying natural selection...")
    factory.natural_selection()
    
    report = factory.get_report()
    print(f"\nAfter evolution:")
    print(f"  Population: {report['current_population']}")
    print(f"  Total created: {report['total_created']}")
    print(f"  Total died: {report['total_died']}")
    print(f"  Best fitness: {report['best_fitness']:.2f}")
    print(f"  Average fitness: {report['avg_fitness']:.2f}")
    print(f"  Strategies by state: {report['strategies_by_state']}")
    
    # Get best strategy
    best = factory.get_best_strategy()
    if best:
        print(f"\nBest strategy:")
        print(f"  ID: {best.strategy_id}")
        print(f"  Type: {best.dna.strategy_type.value}")
        print(f"  State: {best.state.value}")
        print(f"  Fitness: {best.fitness:.2f}")
        print(f"  Win rate: {best.get_win_rate():.1%}")
        print(f"  Total P&L: ${best.total_pnl:.2f}")


async def demo_full_self_assembly():
    """Demonstrate the complete Self-Assembly AI V2 system"""
    print_header("FULL SELF-ASSEMBLY AI V2 - Ultimate Self-Assembling System")
    
    print("Creating Self-Assembly AI V2 orchestrator...")
    config = AssemblyConfig(
        evolution_interval_seconds=5,  # Fast for demo
        optimization_interval_seconds=10,
        genetics_population_size=20,
        swarm_population_size=20,
        strategy_population_size=15,
    )
    
    orchestrator = create_self_assembly_v2(".", config)
    
    # Set callbacks
    def on_evolution(report):
        print(f"  [Evolution] Best fitness: {report['best_fitness']:.4f}")
    
    def on_strategy(strategy):
        print(f"  [Strategy] Created: {strategy.strategy_id}")
    
    orchestrator.on_evolution_complete = on_evolution
    orchestrator.on_strategy_created = on_strategy
    
    # Start the system
    print("\nStarting self-assembly system...")
    await orchestrator.start()
    
    print("\nRunning for 15 seconds...")
    await asyncio.sleep(15)
    
    # Get comprehensive report
    report = orchestrator.get_comprehensive_report()
    
    print("\n" + "-" * 50)
    print("SYSTEM STATUS REPORT")
    print("-" * 50)
    print(f"Mode: {report['state']['mode']}")
    print(f"Health: {report['state']['health']}")
    print(f"Total evolutions: {report['metrics']['total_evolutions']}")
    print(f"Total optimizations: {report['metrics']['total_optimizations']}")
    print(f"Strategies created: {report['metrics']['total_strategies_created']}")
    print(f"Best fitness: {report['metrics']['best_fitness']:.4f}")
    
    print("\nSubsystems active:")
    for name, active in report['subsystems'].items():
        status = "✓" if active else "✗"
        print(f"  {status} {name}")
    
    # Human override demo
    print("\n" + "-" * 50)
    print("HUMAN OVERRIDE DEMO")
    print("-" * 50)
    
    result = orchestrator.human_override("CREATE_STRATEGY", {'blueprint': 'momentum'})
    print(f"Create strategy: {result['message']}")
    
    result = orchestrator.human_override("GET_STATUS")
    print(f"Get status: {result['message']}")
    
    # Stop the system
    print("\nStopping self-assembly system...")
    await orchestrator.stop()
    
    print("\nSelf-Assembly AI V2 demo complete!")


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("  SELF-ASSEMBLY AI V2 - COMPREHENSIVE DEMO")
    print("  The AI that builds and evolves itself")
    print("=" * 70)
    
    demos = [
        ("Code Genetics", demo_code_genetics),
        ("Swarm Intelligence", demo_swarm_intelligence),
        ("Neural Architecture Search", demo_neural_architecture_search),
        ("Emergent Behavior", demo_emergent_behavior),
        ("Strategy Factory", demo_strategy_factory),
        ("Full Self-Assembly", demo_full_self_assembly),
    ]
    
    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos) + 1}. Run ALL demos")
    print("  0. Exit")
    
    try:
        choice = input("\nSelect demo (0-7): ").strip()
        
        if choice == "0":
            print("Exiting...")
            return
        
        choice = int(choice)
        
        if choice == len(demos) + 1:
            # Run all demos
            for name, demo_func in demos:
                await demo_func()
                print("\n" + "-" * 70 + "\n")
        elif 1 <= choice <= len(demos):
            await demos[choice - 1][1]()
        else:
            print("Invalid choice")
            
    except ValueError:
        print("Invalid input")
    except KeyboardInterrupt:
        print("\nInterrupted by user")


if __name__ == "__main__":
    asyncio.run(main())

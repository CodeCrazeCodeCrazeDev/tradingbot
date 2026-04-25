# AlphaEvolve: Complete Implementation Guide

## System Overview

You now have a **complete self-evolving edge discovery and capital allocation engine** that implements:

✅ **Formal Search Space**: Strategy genomes with evolvable components  
✅ **Genetic Operators**: Real mutation, crossover, and recombination  
✅ **Leakage-Free Backtesting**: No lookahead bias, realistic costs  
✅ **Multi-Objective Fitness**: Sharpe, drawdown, regime stability, tail risk  
✅ **Walk-Forward Validation**: Rigorous out-of-sample testing  
✅ **Evolutionary Loop**: Generate → Mutate → Evaluate → Select → Repeat  
✅ **Edge Decay Detection**: Automated monitoring and alerts  
✅ **Distributed Compute**: Massive parallel search capability  

## Quick Start (3 Steps)

### 1. Run Basic Evolution

```bash
python RUN_ALPHA_EVOLVE.py
```

This will:
- Load your market data (or generate sample data)
- Initialize population of 100 random strategies
- Evolve for 50 generations with walk-forward validation
- Save best strategies to `alpha_evolve_results/`

### 2. Review Results

```python
import json

# Load best strategy
with open('alpha_evolve_results/best_genome.json', 'r') as f:
    best_genome = json.load(f)

# Load evolution history
with open('alpha_evolve_results/final_results.json', 'r') as f:
    results = json.load(f)

print(f"Best Fitness: {results['best_fitness']}")
print(f"Best Sharpe: {results['best_sharpe']}")
print(f"Generations: {results['total_generations']}")
```

### 3. Deploy and Monitor

```python
from trading_bot.alpha_evolve import EdgeDecayMonitor

monitor = EdgeDecayMonitor()

# Monitor deployed strategy
edge_status = monitor.monitor_strategy(
    genome_id=deployed_strategy_id,
    recent_performance=recent_data
)

if "RETIRE" in edge_status.recommendation:
    print("Edge decay detected - re-evolving...")
    # Trigger new evolution cycle
```

## Architecture Components

### 1. Strategy Genome (`strategy_genome.py`)

**What it does**: Represents trading strategies as evolvable genomes

**Key classes**:
- `StrategyGenome`: Complete strategy specification
- `Signal`: Individual trading signal
- `SearchSpace`: Valid parameter ranges
- `RiskControl`: Risk management parameters
- `ExecutionParams`: Transaction cost modeling

**Usage**:
```python
from trading_bot.alpha_evolve import SearchSpace

search_space = SearchSpace()
genome = search_space.random_genome()

print(f"Signals: {len(genome.signals)}")
print(f"Genome ID: {genome.get_genome_id()}")
```

### 2. Genetic Operators (`genetic_operators.py`)

**What it does**: Implements mutation, crossover, and selection

**Key operations**:
- `mutate()`: Add/remove signals, alter parameters
- `crossover()`: Recombine two parent strategies
- `tournament_selection()`: Select best from random subset
- `elitism_selection()`: Keep top performers
- `diversity_selection()`: Maintain population diversity

**Usage**:
```python
from trading_bot.alpha_evolve import GeneticOperators

genetic_ops = GeneticOperators(search_space, mutation_rate=0.15)

# Mutate a strategy
mutated = genetic_ops.mutate(genome)

# Crossover two strategies
offspring1, offspring2 = genetic_ops.crossover(parent1, parent2)
```

### 3. Backtesting Engine (`backtesting_engine.py`)

**What it does**: Rigorous backtesting with no data leakage

**Key features**:
- Point-in-time data access only
- Realistic execution delays
- Commission, slippage, market impact
- Proper trade execution simulation

**Usage**:
```python
from trading_bot.alpha_evolve import LeakageFreeBacktester

backtester = LeakageFreeBacktester(
    data=market_data,
    initial_capital=100000
)

result = backtester.backtest(genome)

print(f"Sharpe: {result.sharpe_ratio:.2f}")
print(f"Drawdown: {result.max_drawdown:.2%}")
print(f"Trades: {result.num_trades}")
print(f"Total Costs: ${result.total_costs:.2f}")
```

### 4. Fitness Evaluator (`fitness_evaluator.py`)

**What it does**: Multi-objective strategy evaluation

**Objectives** (weighted):
- Sharpe Ratio (35%): Risk-adjusted returns
- Max Drawdown (25%): Tail risk control
- Regime Stability (20%): Consistency across conditions
- Tail Risk (15%): VaR, CVaR, skewness
- Complexity (5%): Prefer simpler strategies

**Usage**:
```python
from trading_bot.alpha_evolve import MultiObjectiveFitness

fitness_evaluator = MultiObjectiveFitness()

fitness = fitness_evaluator.evaluate(
    backtest_result=result,
    genome_complexity=genome.get_complexity(),
    market_data=market_data
)

print(f"Total Fitness: {fitness.total_fitness:.4f}")
```

### 5. Walk-Forward Validator (`walk_forward.py`)

**What it does**: Out-of-sample validation to prevent overfitting

**Validation types**:
- Rolling: Fixed-size windows
- Anchored: Fixed start, expanding train
- Expanding: Growing training set

**Usage**:
```python
from trading_bot.alpha_evolve import WalkForwardValidator

validator = WalkForwardValidator(
    train_period_days=252,
    test_period_days=63,
    step_days=21,
    validation_type='rolling'
)

wf_result = validator.validate(genome, market_data, fitness_evaluator)

print(f"Test Sharpe: {wf_result.test_sharpe:.2f}")
print(f"Overfitting: {wf_result.overfitting_score:.2f}")
print(f"Significant: {wf_result.is_statistically_significant}")
```

### 6. Evolution Engine (`evolution_engine.py`)

**What it does**: Main evolutionary loop orchestration

**Process**:
1. Initialize random population
2. Evaluate fitness of all individuals
3. Select best performers (elitism)
4. Breed next generation (crossover + mutation)
5. Repeat until convergence

**Usage**:
```python
from trading_bot.alpha_evolve import EvolutionEngine, EvolutionConfig

config = EvolutionConfig(
    population_size=100,
    elite_size=10,
    max_generations=50,
    use_walkforward=True,
    parallel_workers=8
)

engine = EvolutionEngine(config, search_space, market_data)
best_strategy = engine.evolve()
```

### 7. Edge Monitor (`edge_monitor.py`)

**What it does**: Detect when strategies stop working

**Decay signals**:
- Sharpe degradation
- Win rate decline
- Statistical significance loss
- Regime instability
- Opportunity decline

**Usage**:
```python
from trading_bot.alpha_evolve import EdgeDecayMonitor

monitor = EdgeDecayMonitor(
    lookback_days=90,
    decay_threshold=0.3
)

edge_status = monitor.monitor_strategy(
    genome_id=genome.get_genome_id(),
    recent_performance=recent_data,
    baseline_performance=baseline_data
)

print(f"Recommendation: {edge_status.recommendation}")
print(f"Decay Signals: {len(edge_status.decay_signals)}")
```

### 8. Distributed Compute (`distributed_compute.py`)

**What it does**: Scale evolution across multiple workers

**Features**:
- Process pool for CPU-bound tasks
- Task queue management
- Load balancing
- Fault tolerance

**Usage**:
```python
from trading_bot.alpha_evolve import DistributedComputeOrchestrator

orchestrator = DistributedComputeOrchestrator(num_workers=16)

results = orchestrator.execute_parallel(
    genomes=genome_list,
    evaluation_func=evaluate_strategy,
    market_data=market_data
)

cluster_status = orchestrator.get_cluster_status()
print(f"Throughput: {cluster_status.throughput:.2f} evals/hour")
```

## Configuration Options

### EvolutionConfig

```python
config = EvolutionConfig(
    # Population settings
    population_size=100,          # Number of strategies per generation
    elite_size=10,                # Top performers to keep
    tournament_size=3,            # Selection tournament size
    
    # Genetic operator rates
    mutation_rate=0.15,           # Probability of mutation
    crossover_rate=0.7,           # Probability of crossover
    
    # Evolution control
    max_generations=100,          # Maximum generations
    convergence_threshold=0.001,  # Fitness change for convergence
    convergence_generations=10,   # Generations to check convergence
    
    # Validation
    use_walkforward=True,         # Enable walk-forward validation
    walkforward_frequency=5,      # Validate every N generations
    
    # Compute
    parallel_workers=8,           # Number of parallel workers
    
    # Persistence
    save_frequency=5,             # Save checkpoint every N generations
    save_directory="results"      # Results directory
)
```

### SearchSpace

```python
search_space = SearchSpace()

# Customize ranges
search_space.lookback_range = (10, 200)
search_space.threshold_range = (-2.0, 2.0)
search_space.max_signals = 15
search_space.position_size_range = (0.02, 0.20)
```

## Production Workflow

### Phase 1: Discovery (Weekly/Monthly)

```python
# Run evolution to discover new strategies
config = EvolutionConfig(
    population_size=200,
    max_generations=100,
    use_walkforward=True,
    parallel_workers=16
)

engine = EvolutionEngine(config, search_space, market_data)
best_strategies = engine.evolve()

# Get Pareto frontier (multiple good strategies)
pareto_strategies = engine.pareto_frontier
```

### Phase 2: Validation (Before Deployment)

```python
# Rigorous walk-forward validation
validator = WalkForwardValidator(
    train_period_days=252,
    test_period_days=63,
    validation_type='rolling'
)

for strategy in pareto_strategies:
    wf_result = validator.validate(
        strategy.genome,
        market_data,
        fitness_evaluator
    )
    
    # Only deploy if passes validation
    if (wf_result.is_statistically_significant and 
        wf_result.overfitting_score < 0.3 and
        wf_result.test_sharpe > 1.0):
        deploy_to_production(strategy)
```

### Phase 3: Monitoring (Daily)

```python
# Monitor deployed strategies
monitor = EdgeDecayMonitor()

for deployed_strategy in get_deployed_strategies():
    recent_perf = get_recent_performance(deployed_strategy)
    
    edge_status = monitor.monitor_strategy(
        genome_id=deployed_strategy.get_id(),
        recent_performance=recent_perf
    )
    
    # Take action based on recommendation
    if "RETIRE" in edge_status.recommendation:
        retire_strategy(deployed_strategy)
        trigger_new_evolution()
    
    elif "REDUCE" in edge_status.recommendation:
        reduce_allocation(deployed_strategy, factor=0.5)
    
    elif "MAINTAIN" in edge_status.recommendation:
        continue  # All good
```

### Phase 4: Re-Evolution (When Needed)

```python
# Trigger re-evolution when edges decay
if portfolio_health_score < 0.6:
    logger.info("Portfolio health declining - starting re-evolution")
    
    # Use recent data for evolution
    recent_data = market_data.iloc[-1000:]
    
    # Run new evolution cycle
    new_best = engine.evolve()
    
    # Gradually transition to new strategies
    transition_to_new_strategies(new_best)
```

## Performance Tuning

### For Speed

```python
config = EvolutionConfig(
    population_size=50,           # Smaller population
    max_generations=20,           # Fewer generations
    use_walkforward=False,        # Skip walk-forward initially
    parallel_workers=16           # More workers
)
```

### For Quality

```python
config = EvolutionConfig(
    population_size=200,          # Larger population
    max_generations=100,          # More generations
    use_walkforward=True,         # Always validate
    walkforward_frequency=3,      # Validate more often
    elite_size=20,                # Keep more elites
    parallel_workers=32           # Maximum parallelism
)
```

### For Diversity

```python
config = EvolutionConfig(
    mutation_rate=0.25,           # Higher mutation
    crossover_rate=0.5,           # Lower crossover
    tournament_size=5             # Larger tournaments
)

# Use diversity selection
genetic_ops = GeneticOperators(search_space)
diverse_population = genetic_ops.diversity_selection(
    population_with_fitness,
    num_select=50
)
```

## Troubleshooting

### Low Fitness Scores

**Problem**: All strategies have fitness < 0.5

**Solutions**:
- Increase population size
- Increase max generations
- Expand search space ranges
- Check data quality
- Verify transaction costs aren't too high

### Overfitting

**Problem**: High train fitness, low test fitness

**Solutions**:
- Enable walk-forward validation
- Increase complexity penalty weight
- Reduce max_signals in search space
- Use longer test periods
- Add more validation periods

### Slow Evolution

**Problem**: Evolution takes too long

**Solutions**:
- Increase parallel_workers
- Reduce population_size
- Reduce max_generations
- Disable walk-forward initially
- Use simpler fitness evaluation

### No Convergence

**Problem**: Fitness keeps improving, never converges

**Solutions**:
- This is actually good! Let it run longer
- Increase convergence_threshold
- Reduce convergence_generations
- Check if you're finding genuinely better strategies

## Integration Examples

### With Existing Trading Bot

```python
# In your main trading system
from trading_bot.alpha_evolve import EvolutionEngine, EdgeDecayMonitor

class AlphaEvolveIntegration:
    def __init__(self, trading_bot):
        self.bot = trading_bot
        self.monitor = EdgeDecayMonitor()
        self.deployed_strategies = []
    
    def discover_strategies(self):
        """Run evolution to find new strategies"""
        market_data = self.bot.get_historical_data()
        
        config = EvolutionConfig(population_size=100, max_generations=50)
        engine = EvolutionEngine(config, SearchSpace(), market_data)
        
        best = engine.evolve()
        return best
    
    def monitor_strategies(self):
        """Monitor deployed strategies for decay"""
        for strategy in self.deployed_strategies:
            recent_perf = self.bot.get_strategy_performance(strategy)
            
            status = self.monitor.monitor_strategy(
                genome_id=strategy.get_id(),
                recent_performance=recent_perf
            )
            
            if "RETIRE" in status.recommendation:
                self.bot.retire_strategy(strategy)
                self.deployed_strategies.remove(strategy)
```

## Next Steps

1. **Run first evolution**: `python RUN_ALPHA_EVOLVE.py`
2. **Review results**: Check `alpha_evolve_results/` directory
3. **Validate strategies**: Use walk-forward on additional data
4. **Paper trade**: Test in simulation before live deployment
5. **Monitor continuously**: Set up daily edge decay monitoring
6. **Re-evolve regularly**: Run new cycles quarterly or when edges decay

## Support & Documentation

- **Full API docs**: See `trading_bot/alpha_evolve/README.md`
- **Examples**: See `trading_bot/alpha_evolve/example_usage.py`
- **Main trading bot**: See main README.md

---

**You now have a complete, production-ready self-evolving edge discovery engine!**

# AlphaEvolve: Self-Evolving Edge Discovery Engine

A rigorous, statistically-grounded evolutionary search system for discovering, validating, and exploiting decaying market edges faster than competitors.

## Overview

AlphaEvolve implements a complete genetic algorithm framework for automated trading strategy discovery with:

- **No Data Leakage**: Strict point-in-time backtesting
- **Realistic Costs**: Commission, slippage, market impact modeling
- **Statistical Rigor**: Walk-forward validation, significance testing
- **Massive Search**: Distributed parallel evaluation
- **Multi-Objective Optimization**: Sharpe, drawdown, regime stability, tail risk
- **Edge Decay Detection**: Automated monitoring and re-evolution

## Architecture

```
AlphaEvolve/
├── strategy_genome.py       # Strategy representation & search space
├── genetic_operators.py     # Mutation, crossover, selection
├── backtesting_engine.py    # Leakage-free backtesting
├── fitness_evaluator.py     # Multi-objective fitness
├── walk_forward.py          # Out-of-sample validation
├── evolution_engine.py      # Main evolutionary loop
├── edge_monitor.py          # Edge decay detection
├── distributed_compute.py   # Parallel execution
└── example_usage.py         # Complete examples
```

## Core Concepts

### 1. Strategy Genome

Strategies are represented as evolvable genomes containing:

- **Signals**: Individual trading signals (momentum, mean reversion, etc.)
- **Aggregation**: How signals are combined (linear, rank, ensemble)
- **Position Sizing**: Kelly, volatility-scaled, risk parity
- **Risk Controls**: Stop loss, position limits, drawdown limits
- **Execution Parameters**: Slippage, commission, market impact

```python
from alpha_evolve import StrategyGenome, SearchSpace

search_space = SearchSpace()
genome = search_space.random_genome()

print(f"Signals: {len(genome.signals)}")
print(f"Aggregation: {genome.aggregation_type}")
print(f"Position Sizing: {genome.position_sizing}")
```

### 2. Genetic Operators

Real operators that modify strategies:

- **Add/Remove Signals**: Grow or prune strategy complexity
- **Mutate Parameters**: Adjust lookback periods, thresholds, weights
- **Swap Components**: Change aggregation or position sizing methods
- **Crossover**: Recombine successful strategies

```python
from alpha_evolve import GeneticOperators

genetic_ops = GeneticOperators(search_space)

# Mutation
mutated = genetic_ops.mutate(genome)

# Crossover
offspring1, offspring2 = genetic_ops.crossover(parent1, parent2)

# Selection
winner = genetic_ops.tournament_selection(population, tournament_size=3)
```

### 3. Leakage-Free Backtesting

Rigorous backtesting with no lookahead bias:

- **Point-in-time data access only**
- **Realistic execution delays**
- **Transaction cost modeling**
- **Slippage simulation**
- **Market impact estimation**

```python
from alpha_evolve import LeakageFreeBacktester

backtester = LeakageFreeBacktester(
    data=market_data,
    initial_capital=100000
)

result = backtester.backtest(genome)

print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
print(f"Total Costs: ${result.total_costs:.2f}")
```

### 4. Multi-Objective Fitness

Evaluates strategies across multiple dimensions:

- **Sharpe Ratio** (35%): Risk-adjusted returns
- **Max Drawdown** (25%): Tail risk control
- **Regime Stability** (20%): Performance across market conditions
- **Tail Risk** (15%): VaR, CVaR, skewness
- **Complexity Penalty** (5%): Occam's razor

```python
from alpha_evolve import MultiObjectiveFitness

fitness_evaluator = MultiObjectiveFitness()

fitness = fitness_evaluator.evaluate(
    backtest_result=result,
    genome_complexity=genome.get_complexity(),
    market_data=market_data
)

print(f"Total Fitness: {fitness.total_fitness:.4f}")
print(f"Sharpe Score: {fitness.sharpe_ratio:.4f}")
print(f"Regime Stability: {fitness.regime_stability:.4f}")
```

### 5. Walk-Forward Validation

Prevents overfitting through rigorous out-of-sample testing:

- **Rolling Windows**: Fixed-size train/test periods
- **Anchored Windows**: Fixed start date, expanding training
- **Expanding Windows**: Growing training set
- **Statistical Significance**: T-tests on out-of-sample results

```python
from alpha_evolve import WalkForwardValidator

validator = WalkForwardValidator(
    train_period_days=252,
    test_period_days=63,
    step_days=21,
    validation_type='rolling'
)

wf_result = validator.validate(genome, market_data, fitness_evaluator)

print(f"Train Sharpe: {wf_result.train_sharpe:.2f}")
print(f"Test Sharpe: {wf_result.test_sharpe:.2f}")
print(f"Overfitting Score: {wf_result.overfitting_score:.2f}")
print(f"Statistically Significant: {wf_result.is_statistically_significant}")
```

### 6. Evolution Engine

Main evolutionary loop: **Generate → Mutate → Evaluate → Select → Repeat**

```python
from alpha_evolve import EvolutionEngine, EvolutionConfig

config = EvolutionConfig(
    population_size=100,
    elite_size=10,
    tournament_size=3,
    mutation_rate=0.15,
    crossover_rate=0.7,
    max_generations=100,
    use_walkforward=True,
    parallel_workers=8
)

engine = EvolutionEngine(config, search_space, market_data)

best_strategy = engine.evolve()

print(f"Best Fitness: {best_strategy.fitness.total_fitness:.4f}")
print(f"Generation: {best_strategy.generation}")
```

### 7. Edge Decay Monitoring

Detect when strategies stop working:

- **Performance Degradation**: Sharpe decline, win rate drop
- **Statistical Significance Loss**: P-value > 0.05
- **Regime Instability**: Inconsistent across market conditions
- **Opportunity Decline**: Fewer trading signals

```python
from alpha_evolve import EdgeDecayMonitor

monitor = EdgeDecayMonitor(
    lookback_days=90,
    decay_threshold=0.3,
    significance_level=0.05
)

edge_status = monitor.monitor_strategy(
    genome_id=genome.get_genome_id(),
    recent_performance=recent_data,
    baseline_performance=baseline_data
)

print(f"Recommendation: {edge_status.recommendation}")
print(f"Decay Signals: {len(edge_status.decay_signals)}")

for signal in edge_status.decay_signals:
    print(f"  - {signal.signal_type}: {signal.description}")
```

### 8. Distributed Compute

Scale evolution across multiple workers:

```python
from alpha_evolve import DistributedComputeOrchestrator

orchestrator = DistributedComputeOrchestrator(num_workers=16)

results = orchestrator.execute_parallel(
    genomes=genome_list,
    evaluation_func=evaluate_strategy,
    market_data=market_data
)

cluster_status = orchestrator.get_cluster_status()
print(f"Throughput: {cluster_status.throughput:.2f} evals/hour")
```

## Quick Start

### Basic Evolution

```python
import pandas as pd
from alpha_evolve import (
    SearchSpace, EvolutionEngine, EvolutionConfig
)

# Load your market data
market_data = pd.read_csv('market_data.csv', index_col='date', parse_dates=True)

# Configure evolution
config = EvolutionConfig(
    population_size=50,
    max_generations=20,
    parallel_workers=4
)

# Run evolution
search_space = SearchSpace()
engine = EvolutionEngine(config, search_space, market_data)
best_strategy = engine.evolve()

print(f"Best Strategy Sharpe: {best_strategy.fitness.sharpe_ratio:.2f}")
```

### Production Deployment

```python
from alpha_evolve import EdgeDecayMonitor

# Deploy strategy
deployed_genome = best_strategy.genome

# Monitor for decay
monitor = EdgeDecayMonitor()

# Daily monitoring loop
while True:
    recent_performance = get_recent_performance()  # Your implementation
    
    edge_status = monitor.monitor_strategy(
        genome_id=deployed_genome.get_genome_id(),
        recent_performance=recent_performance
    )
    
    if "RETIRE" in edge_status.recommendation:
        print("Edge decay detected - triggering re-evolution")
        # Start new evolution cycle
        new_best = engine.evolve()
        deployed_genome = new_best.genome
```

## Hard Constraints (Enforced)

✅ **No Data Leakage**: All signals use only past data  
✅ **Realistic Costs**: Commission, slippage, market impact included  
✅ **Statistical Rigor**: Walk-forward validation, significance tests  
✅ **Massive Search**: Parallel evaluation across multiple workers  

## Key Features

### Genetic Operators

- **Add/Remove Signals**: Dynamic strategy complexity
- **Parameter Mutation**: Continuous optimization
- **Component Swapping**: Discrete choices (aggregation, position sizing)
- **Crossover**: Multi-point recombination

### Fitness Components

- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Worst peak-to-trough decline
- **Regime Stability**: Performance consistency across market conditions
- **Tail Risk**: VaR, CVaR, skewness, kurtosis
- **Complexity Penalty**: Prefer simpler strategies

### Validation Methods

- **Walk-Forward**: Out-of-sample testing
- **Statistical Tests**: T-tests for significance
- **Regime Analysis**: Bull/bear/high-vol/low-vol performance
- **Overfitting Detection**: Train vs test degradation

## Performance Metrics

The system tracks comprehensive metrics:

- **Returns**: Total, annual, risk-adjusted
- **Risk**: Volatility, drawdown, VaR, CVaR
- **Trading**: Win rate, profit factor, trade frequency
- **Costs**: Commission, slippage, market impact
- **Statistical**: Sharpe, information ratio, significance

## Best Practices

1. **Start Small**: Begin with small population (50-100) for testing
2. **Use Walk-Forward**: Always validate out-of-sample
3. **Monitor Decay**: Check strategies weekly for edge degradation
4. **Re-Evolve Regularly**: Run new evolution cycles quarterly
5. **Diversify**: Deploy multiple uncorrelated strategies
6. **Control Costs**: Model realistic transaction costs
7. **Test Regimes**: Ensure strategies work in different market conditions

## Advanced Usage

See `example_usage.py` for complete examples including:

- Basic evolution
- Advanced evolution with walk-forward
- Edge decay monitoring
- Distributed parallel search
- Complete production workflow

## Integration with Existing System

```python
# In your main trading bot
from trading_bot.alpha_evolve import (
    EvolutionEngine, EdgeDecayMonitor, EvolutionConfig
)

# Initialize
config = EvolutionConfig(population_size=100, max_generations=50)
engine = EvolutionEngine(config, search_space, market_data)
monitor = EdgeDecayMonitor()

# Discover strategies
best_strategies = engine.evolve()

# Deploy and monitor
for strategy in best_strategies:
    deploy_to_production(strategy)
    monitor.monitor_strategy(strategy.get_id(), live_performance)
```

## Performance Expectations

- **Population Size 100**: ~10-30 minutes per generation (8 workers)
- **Walk-Forward Validation**: 2-5x slower than simple backtest
- **Distributed (16 workers)**: ~500-1000 evaluations/hour
- **Convergence**: Typically 20-50 generations

## Limitations & Considerations

- **Computational Cost**: Evolution is CPU-intensive
- **Data Requirements**: Need sufficient history (2+ years recommended)
- **Market Regime Changes**: Edges decay over time
- **Transaction Costs**: Critical for high-frequency strategies
- **Overfitting Risk**: Always use walk-forward validation

## Future Enhancements

- [ ] Multi-asset portfolio optimization
- [ ] Reinforcement learning integration
- [ ] Neural architecture search
- [ ] Adaptive mutation rates
- [ ] Online learning / continuous evolution
- [ ] Cloud-native distributed execution

## License

Part of the AlphaAlgo Trading Bot system.

## Support

For questions or issues, see the main trading bot documentation.

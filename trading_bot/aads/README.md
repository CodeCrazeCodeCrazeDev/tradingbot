# AADS - Autonomous Alpha Discovery System

## Level 6 Financial AI Infrastructure

AADS is a fully autonomous financial intelligence infrastructure modeled after:

- **Palantir's Stack**: Foundry (data ops) + Gotham (intelligence graph) + AIP (agent orchestration) + Maven (decision intelligence)
- **Sakana AI**: Evolutionary model merging - strategies as genomes, fitness selection across generations
- **AlphaEvolve**: LLM-driven code evolution of signal logic
- **OmniFlow**: Agentic workflow orchestration - autonomous multi-agent pipelines
- **MicroFish**: Swarm intelligence - hundreds of micro-agents operating as a decentralized school
- **OpenClaw**: Extensible tool system - dynamic runtime tool discovery and use
- **OpenCLIP**: Visual intelligence - chart, satellite, and image-based alpha
- **Causal Inference**: Structural causal models with do-calculus interventions

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AADS ORCHESTRATOR                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │   FOUNDRY   │ │   GOTHAM    │ │   SAKANA    │ │ SIMULATION │ │
│  │  Data Ops   │ │  Intel Graph│ │  Evolution  │ │   Engine   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │ ALPHAEVOLVE │ │  MICROFISH  │ │  OPENCLAW   │ │  OPENCLIP  │ │
│  │ Code Evolve │ │   Swarm     │ │   Tools     │ │   Vision   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │   CAUSAL    │ │     AIP     │ │    MAVEN    │ │SELF-IMPROVE│ │
│  │ World Model │ │Multi-Agent  │ │  Decision   │ │  Recursive │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
│                                                                  │
│              AUTONOMOUS ALPHA DISCOVERY LOOP                     │
│     DISCOVER → VALIDATE → DEPLOY → MONITOR → RETIRE → EVOLVE    │
└─────────────────────────────────────────────────────────────────┘
```

## Modules

### 1. Strategy Genome (`core/strategy_genome.py`)
- **AADSStrategyGenome**: Complete genome representation of trading strategies
- **Sakana-style merging**: SLERP interpolation for weight blending
- **Fitness function**: `Sharpe * (1 - max_dd) * win_rate`

### 2. Sakana Evolution Engine (`core/sakana_engine.py`)
- Population-based evolution with fitness selection
- Elitism + tournament selection
- Crossover via model merging
- Extinction events to escape local optima

### 3. MicroFish Swarm (`core/microfish_swarm.py`)
- 20+ specialized micro-agents (momentum, mean reversion, sentiment, etc.)
- Emergent consensus via weighted voting
- Fish lifecycle: spawn, grow, decline, death
- Dissent detection reduces confidence

### 4. OpenClaw Tool Registry (`core/openclaw_registry.py`)
- Dynamic tool registration at runtime
- Semantic search for tool discovery
- 25+ built-in tools across categories

### 5. Causal World Model (`core/causal_world_model.py`)
- Structural Causal Model of financial markets
- do-calculus interventions (graph surgery)
- Counterfactual scenario analysis
- Agent-based microstructure simulation

### 6. OpenCLIP Vision (`core/openclip_vision.py`)
- Zero-shot visual classification
- 30+ financial-specific categories
- Chart pattern recognition
- Satellite imagery analysis

### 7. AIP Multi-Agent Core (`core/aip_agents.py`)
- **ResearchAgent**: Hypothesis generation
- **BullAgent**: Adversarial bull case
- **BearAgent**: Counter-thesis builder
- **RiskAgent**: Portfolio constraints (veto power)
- **SimulationAgent**: Monte Carlo, stress tests
- **ExecutionAgent**: Multi-venue routing
- **AuditAgent**: Immutable logging

### 8. Maven Decision Engine (`core/maven_decision.py`)
- Situational awareness
- Wargame (Bull vs Bear)
- Simulation synthesis
- Decision brief generation
- Approval gate (auto-execute / human review / reject)

### 9. Self-Improvement Engine (`core/self_improvement.py`)
- Component benchmarking
- Weakest link identification
- Improvement generation
- Shadow mode validation
- Blue-green deployment with rollback

### 10. Alpha Discovery Loop (`core/alpha_discovery_loop.py`)
- Continuous 24/7 operation
- DISCOVER → VALIDATE → DEPLOY → MONITOR → RETIRE → EVOLVE
- Non-negotiable operational constraints

## Quick Start

```python
from trading_bot.aads import create_aads

# Create AADS instance
aads = create_aads(
    mode="paper_trading",
    initial_capital=1_000_000.0
)

# Start autonomous operation
import asyncio
asyncio.run(aads.start())
```

## Generate a Decision Brief

```python
from trading_bot.aads import create_aads

aads = create_aads(mode="research")

# Generate decision brief for an asset
brief = aads.generate_decision_brief(
    asset="AAPL",
    current_price=175.0
)

# Print formatted brief
print(brief.to_formatted_string())
```

## Run Causal Analysis

```python
from trading_bot.aads.core.causal_world_model import CausalWorldModel

model = CausalWorldModel()

# What if Fed raises rates +50bp?
result = model.intervene(
    variable="Fed_Rate",
    value=5.75,
    observe=["Bond_Yields", "Equity_Valuations", "USD_Strength"]
)

print(result.causal_effects)
```

## Swarm Consensus

```python
from trading_bot.aads.core.microfish_swarm import MicroFishSwarm

swarm = MicroFishSwarm()

market_state = {
    'prices': [...],
    'volumes': [...],
    'vix': 22.5
}

signal = swarm.get_consensus("NVDA", market_state)
print(f"Direction: {signal.direction}, Strength: {signal.strength}")
```

## Operational Constraints (Non-Negotiable)

| Constraint | Limit |
|------------|-------|
| Max single position | 2.0% of portfolio |
| Max single sector | 10.0% of portfolio |
| Max correlated book | 15.0% (correlation > 0.6) |
| Circuit breaker | 10.0% rolling 30-day drawdown |
| Max market impact | 50 bps |
| Max order as % ADV | 5% |

## Decision Approval Thresholds

| Confidence | Action |
|------------|--------|
| ≥ 75 | Auto-execute |
| 50-74 | Human review required |
| < 50 | Rejected |

## Running the Demo

```bash
python -m trading_bot.aads.examples.demo
```

## Directory Structure

```
aads/
├── __init__.py              # Main exports
├── orchestrator.py          # AADSOrchestrator
├── README.md                # This file
├── core/
│   ├── __init__.py
│   ├── strategy_genome.py   # Strategy genomes
│   ├── sakana_engine.py     # Evolution engine
│   ├── microfish_swarm.py   # Swarm intelligence
│   ├── openclaw_registry.py # Tool registry
│   ├── causal_world_model.py# Causal reasoning
│   ├── openclip_vision.py   # Visual intelligence
│   ├── aip_agents.py        # Multi-agent core
│   ├── maven_decision.py    # Decision engine
│   ├── self_improvement.py  # Self-improvement
│   └── alpha_discovery_loop.py # Discovery loop
└── examples/
    ├── __init__.py
    └── demo.py              # Demo script
```

## License

Proprietary - All rights reserved.

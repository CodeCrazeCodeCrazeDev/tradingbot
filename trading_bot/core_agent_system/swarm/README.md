# Unified Swarm Intelligence System (USIS)

The Unified Swarm Intelligence System (USIS) is a production-grade Hierarchical Swarm Intelligence Architecture that unifies lightweight exploration with expert reasoning.

## Architecture

```
                    IntegratedAgentSystem
                             |
                  Meta-Intelligence Layer
                             |
               UnifiedSwarmIntelligenceSystem (USIS)
                             |
                    ┌────────┴────────┐
                    │ Swarm Controller │
                    └────────┬────────┘
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐
    │ Micro Layer  │   │ Expert Layer │   │ Evolution Layer│
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
    Hundreds of small  Specialized      Strategy mutation
    specialized fish   expert agents    & learning
```

## Layers

### 1. Micro-Agent Layer (MicroLayer)
Inspired by `MicroFishSwarm`, this layer consists of hundreds of lightweight "observers" with localized objectives.
- **Pattern Detector**: Identifies technical price patterns.
- **Anomaly Detector**: Flags statistical outliers.
- **Momentum Observer**: Measures velocity of price movement.
- **Volatility Observer**: Monitors regime shifts in variance.
- **Liquidity Observer**: Analyzes order book depth and slippage.
- **Sentiment Observer**: Processes news and social signals.
- **Regime Observer**: Classifies macro and market states.

### 2. Expert Agent Layer (ExpertLayer)
Inspired by `AgentSwarm`, this layer consists of high-reasoning specialized agents.
- **Market Scientist**: Deep market structure and regime analysis.
- **Quant Analyst**: Mathematical modeling and statistical verification.
- **Risk Manager**: Exposure control and downside protection.
- **Execution Agent**: Order optimization and execution strategy.
- **Research Agent**: Autonomous strategy discovery.

### 3. Swarm Controller
The central brain that:
- Activates specific layers/agents based on context.
- Aggregates outputs using multi-factor weighting (Confidence, Accuracy, Context).
- Detects disagreement (dissent) and requests deeper analysis.
- Facilitates the "Multi-Agent Debate" before final decision.

### 4. Evolution & Memory
- **Performance Memory**: Tracks every prediction against market outcomes.
- **Evolution Layer**: Prunes weak micro-agents and mutates successful strategies.

## Integration
USIS is integrated into the `IntegratedAgentSystem` and serves as a specialized execution engine for complex research and trading tasks.

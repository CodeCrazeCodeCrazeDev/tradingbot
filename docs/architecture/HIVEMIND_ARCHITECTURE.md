# Trading Bot Hivemind - Collective Intelligence Architecture

## Overview

The **Hivemind** is a swarm intelligence system where multiple specialized AI nodes work together to make trading decisions through consensus. Inspired by biological swarm behavior, the system exhibits emergent intelligence that exceeds any individual node's capabilities.

## Architecture Diagram

```
                    ┌─────────────────────────────────────┐
                    │         HIVEMIND COORDINATOR        │
                    │   (Consensus, Aggregation, Memory)  │
                    └─────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
    ┌───────▼───────┐         ┌───────▼───────┐         ┌───────▼───────┐
    │  TECHNICAL    │         │ FUNDAMENTAL   │         │  SENTIMENT    │
    │    SWARM      │         │    SWARM      │         │    SWARM      │
    │  (3 nodes)    │         │  (2 nodes)    │         │  (2 nodes)    │
    └───────────────┘         └───────────────┘         └───────────────┘
            │                         │                         │
    ┌───────▼───────┐         ┌───────▼───────┐         ┌───────▼───────┐
    │    RISK       │         │  EXECUTION    │         │   MACRO       │
    │    SWARM      │         │    SWARM      │         │    SWARM      │
    │  (2 nodes)    │         │  (2 nodes)    │         │  (2 nodes)    │
    └───────────────┘         └───────────────┘         └───────────────┘
                                      │
                              ┌───────▼───────┐
                              │    QUANT      │
                              │    SWARM      │
                              │  (2 nodes)    │
                              └───────────────┘
```

## Key Concepts

### 1. HiveNode
Individual AI agent with specific expertise. Each node:
- Analyzes market data from its unique perspective
- Casts votes on trading decisions
- Has a weight based on historical performance
- Communicates with other nodes
- Learns from outcomes

### 2. Swarm
Group of related nodes that collaborate:
- Technical Swarm: Price action, patterns, indicators
- Fundamental Swarm: Economic data, interest rates
- Sentiment Swarm: Social media, news, positioning
- Risk Swarm: Volatility, drawdown, position sizing
- Execution Swarm: Liquidity, spread, timing
- Macro Swarm: Global factors, correlations
- Quant Swarm: Statistical analysis, mean reversion

### 3. Consensus
Voting mechanisms for collective decisions:
- **Majority Vote**: Simple majority wins
- **Weighted Vote**: Performance-weighted voting
- **Bayesian**: Probabilistic aggregation
- **Borda Count**: Ranked preference voting

### 4. Emergent Signals
Complex signals that emerge from node interactions:
- Cross-domain agreement (multiple swarms align)
- High-confidence clusters
- Swarm alignment patterns

### 5. Collective Memory
Shared knowledge base across all nodes:
- Learned patterns
- Historical performance
- Market regimes
- Successful strategies

## Components

### Core (`core.py`)
- `HiveNode`: Base class for all nodes
- `NodeVote`: Individual node's vote
- `SwarmSignal`: Emergent signal from swarm
- `CollectiveDecision`: Final hivemind decision
- `SignalDirection`: STRONG_BUY to STRONG_SELL

### Specialized Nodes (`nodes.py`)
| Node Type | Specialization |
|-----------|---------------|
| `TechnicalNode` | RSI, MACD, MA, patterns |
| `FundamentalNode` | Interest rates, GDP, central banks |
| `SentimentNode` | Social media, fear/greed, positioning |
| `RiskNode` | Volatility, drawdown, position sizing |
| `ExecutionNode` | Spread, liquidity, timing |
| `MacroNode` | Global risk, correlations, yields |
| `MicrostructureNode` | Order flow, toxicity, large orders |
| `QuantNode` | Z-score, momentum, volatility regime |

### Swarm Management (`swarm.py`)
- `Swarm`: Group of related nodes
- `SwarmManager`: Manages all swarms
- `SwarmConfig`: Configuration for swarms

### Consensus Engine (`consensus.py`)
- `MajorityVoting`: Simple majority
- `WeightedVoting`: Performance-weighted
- `BayesianAggregation`: Probabilistic
- `BordaCount`: Ranked preference
- `ConflictResolver`: Handles low consensus

### Collective Memory (`collective_memory.py`)
- `SharedKnowledge`: Shared information
- `EmergentPattern`: Discovered patterns
- Pattern matching and learning

### Coordinator (`coordinator.py`)
- `TradingHiveMind`: Main orchestrator
- `HiveMindConfig`: Configuration
- `quick_start()`: Helper function

## Usage

### Basic Usage

```python
from trading_bot.hivemind import TradingHiveMind, quick_start

# Quick start
hivemind = await quick_start()

# Analyze a symbol
decision = await hivemind.analyze("EURUSD", market_data)

print(decision.action)           # BUY, SELL, HOLD
print(decision.consensus_score)  # 0.0 - 1.0 (agreement level)
print(decision.confidence)       # 0.0 - 1.0
print(decision.node_votes)       # Individual node opinions
print(decision.emergent_signals) # Emergent patterns
```

### With Custom Configuration

```python
from trading_bot.hivemind import TradingHiveMind, HiveMindConfig, ConsensusMethod

config = {
    'consensus_method': ConsensusMethod.BAYESIAN,
    'min_consensus': 0.6,
    'min_confidence': 0.5,
    'enable_learning': True,
    'require_risk_approval': True,
}

hivemind = TradingHiveMind(config)
await hivemind.initialize()

decision = await hivemind.analyze("GBPUSD", market_data)
```

### Recording Outcomes for Learning

```python
# After trade closes
was_correct = True  # Trade was profitable
profit = 150.0      # Profit in account currency

hivemind.record_outcome(was_correct, profit)

# Nodes will update their weights based on performance
```

### Accessing Node Rankings

```python
rankings = hivemind.get_node_rankings()

for node in rankings[:5]:
    print(f"{node['node_id']}: weight={node['weight']:.2f}, accuracy={node['accuracy']:.0%}")
```

## Market Data Format

```python
market_data = {
    # Required: OHLCV data
    'ohlcv': [
        {'time': datetime, 'open': 1.0850, 'high': 1.0860, 'low': 1.0840, 'close': 1.0855, 'volume': 1000},
        # ... more bars
    ],
    
    # Optional: Current price
    'current_price': 1.0855,
    
    # Optional: Account info
    'account_equity': 10000,
    'atr': 0.0050,
    
    # Optional: Fundamental data
    'fundamentals': {
        'interest_rate_differential': 1.5,
        'economic_outlook': 'bullish',  # bullish, neutral, bearish
        'central_bank_stance': 'hawkish',  # hawkish, neutral, dovish
        'gdp_growth': 2.5,
    },
    
    # Optional: Sentiment data
    'sentiment': {
        'overall_score': 0.3,  # -1 to 1
        'fear_greed_index': 55,  # 0-100
        'positioning': {
            'retail': {'long_percent': 60},
            'institutional': {'long_percent': 52},
        },
    },
    
    # Optional: Macro data
    'macro': {
        'risk_appetite': 'risk_on',  # risk_on, neutral, risk_off
        'dxy_trend': 'bearish',
        'high_impact_events_24h': 2,
        'yield_differential': 1.2,
    },
    
    # Optional: Microstructure data
    'microstructure': {
        'order_flow': {'imbalance': 0.15},
        'toxicity': 0.2,
        'large_orders': {'buy_count': 15, 'sell_count': 10},
    },
    
    # Optional: Execution data
    'execution': {
        'spread': 0.0002,
        'avg_spread': 0.00018,
        'liquidity_score': 0.8,
        'session': 'london',  # london, new_york, asian, overlap
    },
    
    # Optional: Risk data
    'risk': {
        'current_drawdown': 0.03,
        'daily_loss': 0.01,
        'potential_risk_reward': 2.5,
    },
}
```

## Collective Decision Output

```python
@dataclass
class CollectiveDecision:
    id: str                              # Unique decision ID
    symbol: str                          # Trading symbol
    action: str                          # BUY, SELL, HOLD
    direction: SignalDirection           # Detailed direction
    
    # Consensus metrics
    consensus_score: float               # 0-1, agreement level
    confidence: float                    # 0-1, overall confidence
    
    # Voting details
    node_votes: List[NodeVote]           # All individual votes
    total_nodes: int                     # Total nodes that voted
    agreeing_nodes: int                  # Nodes that agree with decision
    dissenting_nodes: int                # Nodes that disagree
    
    # Emergent signals
    emergent_signals: List[SwarmSignal]  # Detected emergent patterns
    
    # Trade parameters (if action is BUY/SELL)
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    position_size: Optional[float]
    
    # Metadata
    timestamp: datetime
    processing_time_ms: float
    consensus_method: ConsensusMethod
```

## Emergent Signal Types

| Signal Type | Description |
|-------------|-------------|
| `cross_domain_bullish` | 4+ different node types agree bullish |
| `cross_domain_bearish` | 4+ different node types agree bearish |
| `high_confidence_cluster` | 3+ nodes with >80% confidence agree |
| `swarm_alignment_bullish` | 5+ swarms are bullish |
| `swarm_alignment_bearish` | 5+ swarms are bearish |

## Files

| File | Lines | Description |
|------|-------|-------------|
| `__init__.py` | ~150 | Module exports |
| `core.py` | ~300 | Core types and base classes |
| `nodes.py` | ~700 | 8 specialized node types |
| `swarm.py` | ~300 | Swarm management |
| `consensus.py` | ~400 | Consensus mechanisms |
| `collective_memory.py` | ~450 | Shared memory system |
| `coordinator.py` | ~500 | Main orchestrator |

**Total: ~2,800 lines**

## Running the Demo

```bash
cd "c:\Users\peterson\trading bot"
python examples/hivemind_demo.py
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `consensus_method` | `WEIGHTED_VOTE` | Voting method |
| `min_consensus` | `0.5` | Minimum agreement for trade |
| `min_confidence` | `0.4` | Minimum confidence for trade |
| `enable_learning` | `True` | Learn from outcomes |
| `require_risk_approval` | `True` | Risk swarm must approve |
| `memory_db_path` | `hivemind_memory.db` | SQLite database path |
| `parallel_analysis` | `True` | Analyze swarms in parallel |
| `analysis_timeout_seconds` | `30.0` | Max analysis time |

## Performance Characteristics

- **Total Nodes**: 15+ specialized nodes
- **Swarms**: 7 domain-specific swarms
- **Analysis Time**: ~100-500ms (parallel)
- **Memory**: SQLite-backed collective memory
- **Learning**: Adaptive node weights based on performance

## Integration with AlphaAlgo

The Hivemind can be integrated with existing AlphaAlgo systems:

```python
# In main trading loop
from trading_bot.hivemind import quick_start

hivemind = await quick_start()

# Get collective decision
decision = await hivemind.analyze(symbol, market_data)

# Use decision in trading logic
if decision.action == "BUY" and decision.consensus_score > 0.7:
    # Execute trade with hivemind parameters
    execute_trade(
        symbol=decision.symbol,
        direction="BUY",
        entry=decision.entry_price,
        stop_loss=decision.stop_loss,
        take_profit=decision.take_profit,
        size=decision.position_size,
    )
```

## Conclusion

The Hivemind architecture provides:
- **Collective Intelligence**: Multiple perspectives combined
- **Adaptive Learning**: Nodes improve over time
- **Emergent Behavior**: Complex signals from simple interactions
- **Robust Decisions**: Consensus reduces individual errors
- **Transparency**: Full visibility into node reasoning

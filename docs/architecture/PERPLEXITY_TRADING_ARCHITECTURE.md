# Perplexity Trading Architecture for AlphaAlgo

## Overview

This document describes the **Perplexity Computer-style architecture** specifically designed for AlphaAlgo trading decisions. Like Perplexity Computer, this system uses multi-model orchestration, task decomposition, retrieval-augmented generation, and human-in-the-loop approval for high-stakes actions.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PERPLEXITY TRADING ORCHESTRATOR                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     TASK DECOMPOSITION LAYER                        │ │
│  │  "Analyze EURUSD for entry" → [Research, Technical, Risk, Execute] │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     MULTI-MODEL ROUTER                              │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │ │
│  │  │ RESEARCH │ │TECHNICAL │ │   RISK   │ │EXECUTION │ │ REASONING│ │ │
│  │  │  AGENT   │ │  AGENT   │ │  AGENT   │ │  AGENT   │ │  AGENT   │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                           │ │
│  │  │SENTIMENT │ │  MACRO   │ │MICROSTRUC│                           │ │
│  │  │  AGENT   │ │  AGENT   │ │  AGENT   │                           │ │
│  │  └──────────┘ └──────────┘ └──────────┘                           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     RETRIEVAL PIPELINE                              │ │
│  │  Market Data → News → Sentiment → Fundamentals → Alternative Data  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     PERSISTENT MEMORY                               │ │
│  │  Short-term (session) │ Medium-term (7d) │ Long-term (forever)     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     ASSEMBLY & QA LAYER                             │ │
│  │  Cross-reference │ Verification │ Citation │ Confidence Scoring    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     HUMAN-IN-THE-LOOP                               │ │
│  │  High-stakes actions require explicit approval                      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Principles (from Perplexity Computer)

| Principle | Description | Trading Application |
|-----------|-------------|---------------------|
| **Multi-Model Routing** | Different models for different subtasks | 8 specialized trading agents |
| **Task Decomposition** | Break complex queries into discrete subtasks | DAG-based task graphs |
| **Retrieval-Augmented** | Real-time data retrieval with citation | Market data, news, sentiment |
| **Persistent Memory** | Context across sessions | User preferences, trade history |
| **Orchestration Graph** | Dependency management between subtasks | Parallel batch execution |
| **QA Verification** | Cross-reference outputs against sources | Consistency and reasonableness checks |
| **Human-in-the-Loop** | High-stakes actions require approval | Trade execution approval |

## Components

### 1. Task Decomposer (`task_decomposer.py`)

Decomposes natural language trading queries into task graphs:

```python
from trading_bot.perplexity_trading import TaskDecomposer

decomposer = TaskDecomposer()
graph = decomposer.decompose_simple("Should I buy EURUSD?")

# Result: Task graph with subtasks for:
# - Memory context retrieval
# - Fundamental research
# - Sentiment analysis
# - Market data fetch
# - Technical analysis
# - Risk calculation
# - Synthesis/reasoning
# - Verification
# - Summary generation
```

**Query Intents Detected:**
- RESEARCH: Information gathering
- ANALYZE: Technical/fundamental analysis
- TRADE: Execute a trade
- POSITION_SIZE: Calculate position size
- RISK_CHECK: Check risk parameters
- FORECAST: Predict future movement

### 2. Model Router (`model_router.py`)

Routes subtasks to specialized agents based on task type, complexity, and load:

```python
from trading_bot.perplexity_trading import ModelRouter

router = ModelRouter()
decision = router.route(subtask)

print(decision.selected_agent)      # AgentType.TECHNICAL
print(decision.confidence)          # 0.92
print(decision.estimated_latency_ms) # 500
```

**Routing Strategies:**
- `TASK_TYPE`: Route based on task type
- `QUALITY`: Route to highest quality agent
- `LATENCY`: Route to fastest agent
- `BALANCED`: Balance quality and latency
- `SPECIALIZED`: Prioritize specialization match

### 3. Specialized Agents (`trading_agents.py`)

8 specialized agents, each optimized for specific tasks:

| Agent | Specialization | Avg Latency |
|-------|---------------|-------------|
| **Research** | News, fundamentals, economic data | 2000ms |
| **Technical** | Patterns, indicators, S/R levels | 500ms |
| **Risk** | Position sizing, stop loss, R:R | 300ms |
| **Execution** | Order routing, timing, slippage | 100ms |
| **Reasoning** | Chain-of-thought, synthesis | 3000ms |
| **Sentiment** | Social media, news sentiment | 1500ms |
| **Macro** | Economic indicators, policy | 2500ms |
| **Microstructure** | Order flow, liquidity, depth | 200ms |

### 4. Retrieval Pipeline (`retrieval_pipeline.py`)

Multi-source data retrieval with caching and citation tracking:

```python
from trading_bot.perplexity_trading import RetrievalPipeline, RetrievalSource

pipeline = RetrievalPipeline()

# Retrieve from all sources in parallel
results = await pipeline.retrieve_all({'symbol': 'EURUSD'})

# Generate citations
citations = pipeline.generate_citations(results)
```

**Data Sources:**
- `MARKET_DATA`: Price, volume, OHLCV (5s cache)
- `NEWS`: Financial news (5min cache)
- `SENTIMENT`: Social media sentiment (10min cache)
- `FUNDAMENTALS`: Economic data (1hr cache)
- `ALTERNATIVE`: Alternative data (30min cache)

### 5. Persistent Memory (`persistent_memory.py`)

Three-tier memory system like Perplexity Computer:

```python
from trading_bot.perplexity_trading import PersistentMemory, MemoryLevel

memory = PersistentMemory()

# Store user preference (long-term)
memory.store_user_preference('risk_tolerance', 'moderate')

# Store trade (medium-term, 7 days)
memory.store_trade({'symbol': 'EURUSD', 'action': 'BUY', ...})

# Store market context (short-term, session only)
memory.store_market_context('current_regime', 'trending')

# Query memory
context = memory.get_context()
```

**Memory Levels:**
- `SHORT_TERM`: In-memory only, cleared on restart
- `MEDIUM_TERM`: SQLite storage, 7-day retention
- `LONG_TERM`: SQLite storage, permanent

### 6. Assembly & QA (`assembly_qa.py`)

Assembles subtask results with quality assurance:

```python
from trading_bot.perplexity_trading import AssemblyEngine

engine = AssemblyEngine()
decision = engine.assemble(query_id, subtask_results, symbol='EURUSD')

# QA checks performed:
# - Cross-reference: Data matches sources
# - Consistency: No conflicting signals
# - Completeness: All required data present
# - Reasonableness: Values within expected ranges
```

### 7. Human Approval (`human_approval.py`)

Human-in-the-loop for high-stakes actions:

```python
from trading_bot.perplexity_trading import HumanApprovalGate

gate = HumanApprovalGate()

# Check if approval needed
needs_approval, reason = gate.requires_approval(decision)

# Request approval
approval = await gate.request_approval(decision, timeout_seconds=300)

if approval.approved:
    # Execute trade
    pass
```

**Risk Levels:**
- `LOW`: Auto-approve possible
- `MEDIUM`: Requires review
- `HIGH`: Requires explicit approval
- `CRITICAL`: Requires multiple approvals

### 8. Main Orchestrator (`orchestrator.py`)

Coordinates all components:

```python
from trading_bot.perplexity_trading import PerplexityTradingOrchestrator, quick_start

# Quick start
orchestrator = await quick_start()

# Analyze a query
decision = await orchestrator.analyze(
    query="Should I buy EURUSD?",
    symbol="EURUSD",
    timeframe="H4",
)

# Access results
print(decision.action)           # BUY, SELL, HOLD
print(decision.confidence)       # 0.0 - 1.0
print(decision.reasoning_chain)  # Step-by-step reasoning
print(decision.citations)        # Data sources used
print(decision.get_summary())    # Human-readable summary
```

## Usage Examples

### Basic Analysis

```python
import asyncio
from trading_bot.perplexity_trading import quick_start

async def main():
    orchestrator = await quick_start()
    
    decision = await orchestrator.analyze(
        query="Should I buy EURUSD?",
        symbol="EURUSD",
    )
    
    print(decision.get_summary())

asyncio.run(main())
```

### Complex Multi-Step Query

```python
decision = await orchestrator.analyze(
    query="""
    Research the current macroeconomic outlook for EUR and USD.
    Analyze the EURUSD 4H chart for technical signals.
    Check market sentiment and positioning data.
    Calculate optimal position size for 1.5% risk.
    Provide a trading recommendation with entry, stop loss, and take profit.
    """,
    symbol="EURUSD",
    timeframe="H4",
)
```

### With User Preferences

```python
# Store preferences (persisted across sessions)
orchestrator.store_user_preference('risk_tolerance', 'conservative')
orchestrator.store_user_preference('max_risk_per_trade', 0.01)
orchestrator.store_user_preference('preferred_timeframe', 'D1')

# Analysis will use these preferences
decision = await orchestrator.analyze("Should I trade GBPJPY?")
```

### Manual Approval Workflow

```python
# Enable approval requirement
orchestrator = await quick_start({'require_approval_for_trades': True})

# Start analysis
decision = await orchestrator.analyze("Buy EURUSD at market")

# Check pending approvals
pending = orchestrator.get_pending_approvals()
for request in pending:
    print(orchestrator.approval_gate.format_request_for_display(request))
    
    # Approve or reject
    orchestrator.approve_request(request.id, "Approved after review")
    # or: orchestrator.reject_request(request.id, "Risk too high")
```

## Configuration

```python
from trading_bot.perplexity_trading import OrchestratorConfig

config = OrchestratorConfig(
    # Execution settings
    max_parallel_tasks=5,
    task_timeout_seconds=30.0,
    total_timeout_seconds=120.0,
    
    # Retry settings
    max_retries=3,
    retry_delay_seconds=1.0,
    
    # Memory settings
    memory_db_path="perplexity_trading_memory.db",
    
    # Approval settings
    require_approval_for_trades=True,
    approval_timeout_seconds=300.0,
)

orchestrator = PerplexityTradingOrchestrator(config.__dict__)
```

## Files

| File | Lines | Description |
|------|-------|-------------|
| `__init__.py` | ~250 | Module exports and documentation |
| `core_types.py` | ~300 | Data structures and enums |
| `task_decomposer.py` | ~400 | Query decomposition |
| `model_router.py` | ~350 | Multi-model routing |
| `trading_agents.py` | ~700 | 8 specialized agents |
| `retrieval_pipeline.py` | ~400 | Data retrieval |
| `persistent_memory.py` | ~450 | Three-tier memory |
| `assembly_qa.py` | ~400 | Result assembly and QA |
| `human_approval.py` | ~350 | Human-in-the-loop |
| `orchestrator.py` | ~400 | Main orchestrator |

**Total: ~4,000 lines of production-ready code**

## Running the Demo

```bash
cd "c:\Users\peterson\trading bot"
python examples/perplexity_trading_demo.py
```

## Integration with Existing AlphaAlgo Systems

The Perplexity Trading Architecture integrates with existing AlphaAlgo components:

- **Cognitive Architecture**: Can use as Layer 3 (Multi-Agent) replacement
- **Intelligent Delegation**: Compatible task decomposition
- **Elite AI System**: Can use as analysis backend
- **MSOS**: Respects safety constraints
- **Hedge Fund Safety**: Integrates with approval workflow

## Key Differences from Perplexity Computer

| Perplexity Computer | AlphaAlgo Perplexity Trading |
|---------------------|------------------------------|
| 19 general AI models | 8 specialized trading agents |
| Web browsing | Market data retrieval |
| File manipulation | Trade execution |
| General research | Financial research |
| Document analysis | Chart analysis |
| Code execution | Risk calculation |

## Conclusion

The Perplexity Trading Architecture brings the power of multi-model orchestration to algorithmic trading, enabling:

- **Natural language queries** for trading analysis
- **Specialized agents** for different aspects of trading
- **Citation-backed decisions** with full provenance
- **Human oversight** for high-stakes actions
- **Persistent learning** across sessions

This architecture represents a significant step toward AGI-level trading intelligence while maintaining safety and explainability.

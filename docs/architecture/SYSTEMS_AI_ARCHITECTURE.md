# AlphaAlgo Systems AI Architecture

## Core Philosophy (Non-Negotiable)

| Principle | Implementation |
|-----------|----------------|
| Models are opaque | Systems provide attribution |
| Behavior changes via retraining | Not code patching |
| Intelligence = training + memory + feedback | Not parameters |
| Agents assist discovery | Never act without governance |
| Text → system action | Allowed |
| Text → live trading | **FORBIDDEN** |

---

## 1. System Architecture (Text Diagram)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ALPHAALGO SYSTEMS AI                                   │
│                    "Intelligence from Architecture, Not Parameters"              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
┌───────────────┐              ┌───────────────┐              ┌───────────────┐
│  DATA LAYER   │              │ COMPUTE LAYER │              │ CONTROL LAYER │
│  (Ingestion)  │              │  (Processing) │              │ (Governance)  │
└───────────────┘              └───────────────┘              └───────────────┘
        │                               │                               │
        ▼                               ▼                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA INGESTION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ L1 Quotes   │  │ L2 Order    │  │ Trade Tape  │  │ News/       │            │
│  │ (BBO)       │  │ Book        │  │ (Prints)    │  │ Sentiment   │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                │                    │
│         └────────────────┴────────────────┴────────────────┘                    │
│                                   │                                              │
│                                   ▼                                              │
│                        ┌─────────────────────┐                                   │
│                        │   NORMALIZER        │                                   │
│                        │   - Timestamp align │                                   │
│                        │   - Sequence valid  │                                   │
│                        │   - Quality flags   │                                   │
│                        └──────────┬──────────┘                                   │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EVENT STORE & REPLAY                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         IMMUTABLE EVENT LOG                              │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │
│  │  │ Event 1  │→ │ Event 2  │→ │ Event 3  │→ │ Event N  │→ │ HEAD     │  │    │
│  │  │ t=0.001  │  │ t=0.002  │  │ t=0.003  │  │ t=N.xxx  │  │ (live)   │  │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                   │                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         REPLAY ENGINE                                    │    │
│  │  - Deterministic replay from any point                                   │    │
│  │  - Speed: REALTIME | FAST | STEPPED                                      │    │
│  │  - Bookmarks for key events                                              │    │
│  │  - Reproducible training                                                 │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FEATURE PIPELINES                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Microstruc- │  │ Technical   │  │ Regime      │  │ Sentiment   │            │
│  │ ture        │  │ Indicators  │  │ Features    │  │ Features    │            │
│  │ ─────────── │  │ ─────────── │  │ ─────────── │  │ ─────────── │            │
│  │ - Imbalance │  │ - Momentum  │  │ - Volatility│  │ - News NLP  │            │
│  │ - Spread    │  │ - Mean Rev  │  │ - Liquidity │  │ - Social    │            │
│  │ - Toxicity  │  │ - Trend     │  │ - Regime ID │  │ - Macro     │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                │                    │
│         └────────────────┴────────────────┴────────────────┘                    │
│                                   │                                              │
│                                   ▼                                              │
│                        ┌─────────────────────┐                                   │
│                        │   FEATURE STORE     │                                   │
│                        │   - Versioned       │                                   │
│                        │   - Point-in-time   │                                   │
│                        │   - Decay tracking  │                                   │
│                        └──────────┬──────────┘                                   │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MODEL ENSEMBLE                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    REGIME-AWARE MODEL ROUTER                             │    │
│  │                                                                          │    │
│  │    Regime: TRENDING    Regime: RANGING    Regime: VOLATILE               │    │
│  │    ┌─────────────┐     ┌─────────────┐    ┌─────────────┐               │    │
│  │    │ Trend Model │     │ MeanRev Mdl │    │ Vol Model   │               │    │
│  │    │ w=0.7       │     │ w=0.8       │    │ w=0.6       │               │    │
│  │    └─────────────┘     └─────────────┘    └─────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                   │                                              │
│                                   ▼                                              │
│                        ┌─────────────────────┐                                   │
│                        │   CONFIDENCE-       │                                   │
│                        │   WEIGHTED          │                                   │
│                        │   AGGREGATOR        │                                   │
│                        └──────────┬──────────┘                                   │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DECISION ATTRIBUTION LAYER                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Every signal MUST output:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  {                                                                       │    │
│  │    "signal_id": "uuid",                                                  │    │
│  │    "feature_snapshot_hash": "sha256:abc123...",                          │    │
│  │    "contributing_models": [                                              │    │
│  │      {"model_id": "trend_v3", "weight": 0.4, "confidence": 0.85}         │    │
│  │    ],                                                                    │    │
│  │    "latent_regime_id": "regime_cluster_7",                               │    │
│  │    "historical_analogs": ["2023-03-15", "2022-11-08"],                   │    │
│  │    "expected_outcome": {"direction": "LONG", "magnitude": 0.02},         │    │
│  │    "confidence_score": 0.78,                                             │    │
│  │    "reasoning_chain": ["high_imbalance", "trend_confirmed"]              │    │
│  │  }                                                                       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MEMORY HIERARCHY                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐     │
│  │   SHORT-TERM        │  │   MID-TERM          │  │   LONG-TERM         │     │
│  │   (Seconds-Minutes) │  │   (Hours-Days)      │  │   (Weeks-Forever)   │     │
│  │   ───────────────── │  │   ───────────────── │  │   ───────────────── │     │
│  │   - Microstructure  │  │   - Session regime  │  │   - Archived events │     │
│  │   - Execution ctx   │  │   - Volatility      │  │   - Training data   │     │
│  │   - Order book      │  │   - Liquidity       │  │   - Model versions  │     │
│  │   - Recent trades   │  │   - Correlations    │  │   - Outcomes        │     │
│  │                     │  │                     │  │   - Shock signatures│     │
│  │   TTL: 5 minutes    │  │   TTL: 7 days       │  │   TTL: Forever      │     │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘     │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RESEARCH AGENTS                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    SCIENTIFIC LOOP (NON-TRADING)                         │    │
│  │                                                                          │    │
│  │    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │    │
│  │    │ OBSERVE  │ →  │ HYPOTHE- │ →  │ TEST     │ →  │ VALIDATE │        │    │
│  │    │ Data     │    │ SIZE     │    │ Replay   │    │ Robustness│        │    │
│  │    └──────────┘    └──────────┘    └──────────┘    └──────────┘        │    │
│  │         │                                               │               │    │
│  │         └───────────────────────────────────────────────┘               │    │
│  │                              │                                          │    │
│  │                              ▼                                          │    │
│  │                    ┌──────────────────┐                                 │    │
│  │                    │ PROMOTE (if pass)│                                 │    │
│  │                    │ to Governance    │                                 │    │
│  │                    └──────────────────┘                                 │    │
│  │                                                                          │    │
│  │    CONSTRAINTS:                                                          │    │
│  │    ✗ CANNOT deploy live                                                  │    │
│  │    ✗ CANNOT modify risk rules                                            │    │
│  │    ✗ CANNOT bypass governance                                            │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         TEXT-TO-SYSTEM COMMAND LAYER                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ALLOWED:                           FORBIDDEN:                                   │
│  ┌─────────────────────────┐       ┌─────────────────────────┐                  │
│  │ "Analyze slippage..."   │       │ ✗ "Execute trade..."    │                  │
│  │ "Find failing features" │       │ ✗ "Override risk..."    │                  │
│  │ "Retrain model..."      │       │ ✗ "Deploy to prod..."   │                  │
│  │ "Simulate sizing..."    │       │ ✗ "Disable safety..."   │                  │
│  └─────────────────────────┘       └─────────────────────────┘                  │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         GOVERNANCE & APPROVAL GATES                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  G0: HUMAN AUTHORITY (Ultimate control)                                          │
│  ├── Approves: Model deployment, Risk changes, System config                     │
│  │                                                                               │
│  G1: SYSTEM CONTROLLER (Automated gates)                                         │
│  ├── Validates: Signal quality, Risk limits, Data integrity                      │
│  │                                                                               │
│  G2: AGENT LAYER (Research & discovery)                                          │
│  └── Proposes: Features, Hypotheses, Improvements                                │
│                                                                                  │
│  FLOW: G2 proposes → G1 validates → G0 approves → Deploy                         │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SELF-IMPROVEMENT LOOP                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│    │ OUTCOME  │ →  │ DRIFT    │ →  │ DECAY    │ →  │ RETRAIN  │                 │
│    │ LABELING │    │ DETECT   │    │ DETECT   │    │ TRIGGER  │                 │
│    └──────────┘    └──────────┘    └──────────┘    └──────────┘                 │
│         │                                               │                        │
│         │         ┌──────────┐    ┌──────────┐         │                        │
│         └────────→│ VALIDATE │ →  │ DEPLOY   │←────────┘                        │
│                   │ GATE     │    │ GATE     │                                  │
│                   └──────────┘    └──────────┘                                  │
│                                                                                  │
│    ALL IMPROVEMENTS: Measured | Reversible | Auditable                           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Memory Hierarchy Design

### Tier 1: Short-Term Memory (Seconds to Minutes)

| Attribute | Value |
|-----------|-------|
| **TTL** | 5 minutes |
| **Storage** | In-memory (fast access) |
| **Max Entries** | 100,000 |

**Data Stored:**
- Market microstructure (imbalance, spread, toxicity)
- Execution context (pending orders, recent fills)
- Order book state
- Recent trades and quotes

**Access Rules:**
| Agent Type | Access Level |
|------------|--------------|
| Live Trading | READ, WRITE |
| Research | READ |
| Training | None |
| Governance | READ, ADMIN |

### Tier 2: Mid-Term Memory (Hours to Days)

| Attribute | Value |
|-----------|-------|
| **TTL** | 7 days |
| **Storage** | Disk-backed with memory cache |
| **Cache Size** | 10,000 entries |

**Data Stored:**
- Session regime classification
- Volatility states (realized, implied, regime)
- Liquidity conditions
- Correlation snapshots

**Access Rules:**
| Agent Type | Access Level |
|------------|--------------|
| Live Trading | READ |
| Research | READ |
| Training | READ |
| Governance | READ, ADMIN |

### Tier 3: Long-Term Memory (Weeks to Forever)

| Attribute | Value |
|-----------|-------|
| **TTL** | Forever (immutable) |
| **Storage** | Persistent database |
| **Retention** | Append-only |

**Data Stored:**
- Archived events (market shocks, anomalies)
- Training datasets (versioned)
- Model versions (with metadata)
- Historical outcomes
- Market shock signatures

**Access Rules:**
| Agent Type | Access Level |
|------------|--------------|
| Live Trading | None |
| Research | READ |
| Training | READ, WRITE |
| Governance | READ, ADMIN |

---

## 3. Decision Attribution Engine

### Schema

```json
{
  "signal_id": "uuid",
  "timestamp": "ISO8601",
  "symbol": "BTCUSDT",
  "feature_snapshot_hash": "sha256:abc123...",
  "contributing_models": [
    {
      "model_id": "trend_v3",
      "version": "1.2.0",
      "weight": 0.4,
      "confidence": 0.85,
      "features_used": ["momentum", "trend", "volatility"]
    }
  ],
  "latent_regime_id": "regime_cluster_7",
  "historical_analogs": [
    {
      "date": "2023-03-15",
      "similarity": 0.92,
      "outcome": 0.015
    }
  ],
  "expected_outcome": {
    "direction": "LONG",
    "magnitude": 0.02,
    "horizon": "1h",
    "probability": 0.78
  },
  "realized_outcome": {
    "status": "win",
    "pnl": 0.018,
    "slippage": 0.0002
  },
  "confidence_score": 0.78,
  "reasoning_chain": [
    "high_imbalance",
    "trend_confirmed",
    "vol_low"
  ]
}
```

### Storage

| Store | Retention | Purpose |
|-------|-----------|---------|
| Hot | 7 days | Fast query |
| Cold | Forever | Compressed, indexed |

### Query Interface

```python
# By signal ID
attribution = engine.store.get(signal_id)

# By time range
records = engine.store.query(AttributionQuery(
    time_range=(start, end),
    limit=100
))

# By regime
records = engine.store.query(AttributionQuery(
    regime_ids=["regime_trending"],
    outcome_status=[OutcomeStatus.WIN]
))
```

### Debug Workflows

```python
# "Why did signal X fail?"
analysis = engine.debug_signal_failure(signal_id)

# "What features drove signal Y?"
drivers = engine.debug_feature_drivers(signal_id)

# "Compare attribution across regime Z"
comparison = engine.compare_regime_attribution("regime_volatile")
```

---

## 4. Training-First Architecture

### Core Principles

1. **Logic is immutable** - Code defines structure, not behavior
2. **Behavior changes via retraining** - Not code patches
3. **Models are hot-swappable** - No downtime for updates
4. **All training is reproducible** - Same data + config = same results

### Dataset Versioning

```python
DatasetVersion(
    dataset_id="market_data_v1",
    version="2024.01.15",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2024, 1, 15),
    symbols=["BTCUSDT", "ETHUSDT"],
    features=["price", "volume", "imbalance"],
    row_count=1_000_000,
    data_hash="sha256:...",
    quality_score=0.98
)
```

### Training Config Versioning

```python
TrainingConfig(
    config_id="trend_model_v3",
    version="1.0",
    model_type="transformer",
    hyperparameters={
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 100
    },
    dataset_version="market_data_v1:2024.01.15",
    random_seed=42,
    deterministic=True
)
```

### Deployment Pipeline

```
Shadow Testing (0% traffic)
    ↓
Canary 1% (1% traffic)
    ↓
Canary 5% (5% traffic)
    ↓
Canary 25% (25% traffic)
    ↓
Production (100% traffic)
```

### Auto-Rollback Rules

| Condition | Action |
|-----------|--------|
| Error rate > 1% | Rollback |
| P99 latency > 100ms | Rollback |
| Signal accuracy < 50% | Rollback |
| PnL contribution negative | Rollback |

---

## 5. Research Agent (Scientific Loop)

### Workflow

```
OBSERVE → HYPOTHESIZE → TEST → VALIDATE → PROMOTE
   ↑                                          │
   └──────────────────────────────────────────┘
```

### Constraints (IMMUTABLE)

| Constraint | Enforced |
|------------|----------|
| Cannot deploy live | ✓ |
| Cannot modify risk rules | ✓ |
| Cannot bypass governance | ✓ |
| Cannot execute trades | ✓ |
| Cannot access production | ✓ |

### Validation Criteria

| Criterion | Threshold |
|-----------|-----------|
| P-value | < 0.05 |
| Sharpe ratio | > 0.5 |
| Win rate | > 45% |
| Max drawdown | > -20% |
| Profit factor | > 1.1 |
| Regime coverage | > 80% |
| Decay rate | < 10%/month |

### Hypothesis Types

- **SIGNAL**: New trading signal logic
- **FEATURE**: New feature transformation
- **REGIME**: New regime classification
- **ENSEMBLE**: New model combination
- **EXECUTION**: New execution strategy

---

## 6. Text-to-System Action Layer

### Allowed Commands

| Category | Examples |
|----------|----------|
| ANALYZE | "Analyze why slippage exceeded forecast last week" |
| FIND | "Find features that fail in low-volatility regimes" |
| RETRAIN | "Retrain execution model excluding high-spread periods" |
| SIMULATE | "Simulate alternative sizing under current regime" |
| SHOW | "Show attribution for signal XYZ" |
| COMPARE | "Compare model performance across regimes" |

### Forbidden Commands (IMMUTABLE)

| Pattern | Blocked |
|---------|---------|
| Execute/place/submit trade | ✓ |
| Buy/sell/long/short | ✓ |
| Override/disable risk | ✓ |
| Deploy to production | ✓ |
| Disable safety/checks | ✓ |
| Show credentials/keys | ✓ |

---

## 7. Governance & Safety Boundaries

### Governance Hierarchy

```
G0: HUMAN AUTHORITY (Ultimate control)
├── Approves: Model deployment, Risk changes, System config
│
G1: SYSTEM CONTROLLER (Automated gates)
├── Validates: Signal quality, Risk limits, Data integrity
│
G2: AGENT LAYER (Research & discovery)
└── Proposes: Features, Hypotheses, Improvements

FLOW: G2 proposes → G1 validates → G0 approves → Deploy
```

### Safety Boundaries (IMMUTABLE)

| Boundary | Limit | Enforcement |
|----------|-------|-------------|
| Max position size | 10% | Hard |
| Max daily loss | 5% | Hard |
| Max drawdown | 20% | Hard |
| Max leverage | 3x | Hard |

### Audit Log

Every action logged with:
- **Who**: Actor and level
- **What**: Action type
- **When**: Timestamp
- **Why**: Reasoning
- **Outcome**: Result

---

## 8. Self-Improvement Loop

### Loop Stages

```
OUTCOME LABELING → DRIFT DETECTION → DECAY DETECTION → RETRAINING TRIGGER
        ↑                                                      │
        │         VALIDATION GATE ← DEPLOYMENT GATE ←──────────┘
        │                │                 │
        └────────────────┴─────────────────┘
```

### Drift Types

| Type | Description |
|------|-------------|
| Data drift | Input distribution changes |
| Concept drift | Input-output relationship changes |
| Label drift | Target distribution changes |
| Performance drift | Metrics degradation |

### Retraining Triggers

| Trigger | Condition |
|---------|-----------|
| Performance decay | Sharpe < 0.5 |
| Drift detected | Severity HIGH or CRITICAL |
| Scheduled | Time-based |
| Manual | Human request |

### Improvement Requirements

All improvements MUST be:
- **Measured**: Quantified impact
- **Reversible**: Rollback available
- **Auditable**: Full trace

---

## 9. Advanced Features

### Implemented Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | Adaptive Signal Orchestration | Dynamic agent weighting by regime/confidence |
| 2 | Market-Driven Curriculum Learning | Progressive exposure to market complexity |
| 3 | Feature Evolution Sandbox | Automatic feature discovery and validation |
| 4 | Latent Regime Mapper | Unsupervised regime classification |
| 5 | Confidence-Weighted Ensemble | Dynamic model routing |
| 6 | Predictive Feature Decay | Track and retire stale features |
| 7 | Temporal Attention for Execution | Focus on impactful patterns |
| 8 | Anomaly-Driven Feedback Loop | Prioritize rare events in training |
| 9 | Meta-Reward Layer | Multi-objective reward (not just PnL) |
| 10 | Synthetic Market Stress Simulation | Edge-case generation |
| 11 | Self-Documenting Model Logs | Automatic provenance |
| 12 | Cross-Domain Knowledge Transfer | External data integration |
| 13 | Autonomous Strategy Discovery | Automated strategy exploration |
| 14 | Feedback-Aware Risk Management | Risk in reward function |
| 15 | Real-Time What-If Sandbox | Safe online experimentation |

---

## Usage

### Quick Start

```python
from trading_bot.systems_ai import SystemsAIOrchestrator, quick_start

# Quick start
orchestrator = await quick_start(mode="paper")

# Generate signal
from trading_bot.systems_ai import SignalRequest
request = SignalRequest(
    request_id="req_001",
    symbol="BTCUSDT",
    timestamp=datetime.utcnow(),
    features={"trend": 0.5, "momentum": 0.3, "volatility": 0.2}
)
response = orchestrator.generate_signal(request)

# Process command
result = orchestrator.process_command("Analyze slippage for last 7 days")

# Get status
status = orchestrator.get_system_status()
```

### Files Created

| File | Lines | Description |
|------|-------|-------------|
| `architecture.py` | ~400 | System architecture |
| `memory_hierarchy.py` | ~700 | 3-tier memory |
| `attribution_engine.py` | ~650 | Decision attribution |
| `training_first.py` | ~800 | Training architecture |
| `research_agent.py` | ~600 | Scientific loop |
| `text_to_system.py` | ~600 | NL command layer |
| `governance.py` | ~650 | Governance engine |
| `self_improvement.py` | ~750 | Self-improvement loop |
| `orchestrator.py` | ~700 | Master orchestrator |
| **TOTAL** | **~5,850** | Production-ready |

---

## Final Constraint

**You are building Systems AI, not a model demo.**

If any component increases autonomy without increasing control, reject it and propose a safer alternative.

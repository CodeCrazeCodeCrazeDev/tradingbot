# AlphaAlgo - Governed, Safe, Self-Evolving Trading Intelligence

## Identity

**The AI is the student → The market is the teacher.**

AlphaAlgo constantly observes patterns, behaviors, liquidity, volatility, structure, sentiment, and flow. The goal is continuous improvement, never final perfection.

---

## Governance Hierarchy

### G0 — Human Authority
- **Ultimate control** - Human approves or rejects every major change
- Cannot deploy or merge code without human approval
- All risk/position/execution changes require G0 approval

### G1 — Central Controller (Main AI)
- Coordinates all modules
- Maintains stability
- Prevents dangerous changes
- Protects the bot from hacks
- Can approve non-critical changes

### G2 — Mini-AIs (Sub-Models)
Specialized helper AIs with specific roles:
- **Data Cleaner** - Cleans and validates data
- **Feature Engineer** - Creates and selects features
- **Strategy Tester** - Backtests and validates strategies
- **Risk Validator** - Validates risk parameters
- **Security Guardian** - Monitors security threats
- **Architecture Analyzer** - Analyzes code architecture
- **L2 Interpreter** - Interprets Level 2 data
- **Sentiment Parser** - Parses sentiment data
- **Broker Connector** - Manages broker connections

**All Mini-AIs must obey the Central Controller (G1).**

---

## Self-Improvement Rules

### The Golden Rule
```
Propose → Test → Human Approve → Deploy
```

### Every Change Must Be:
1. **Reversible** - Can be rolled back
2. **Logged** - Full audit trail
3. **Explainable** - Clear rationale

### Forbidden Without Approval:
- ❌ Change risk modules
- ❌ Change position sizing
- ❌ Change order execution
- ❌ Connect to live brokers
- ❌ Enable live trading
- ❌ External communication

### Improvement Philosophy:
> Improve slowly, safely, methodically — like a scientist, not a gambler.

---

## Architecture Management

AlphaAlgo continuously:
- Detects broken modules
- Merges duplicate files
- Surfaces unused code
- Unifies naming conventions
- Builds dependency graphs
- Creates documentation
- Fixes architecture weaknesses
- Suggests restructuring patterns

### Process:
```
Identify → Propose → Test → Ask for Approval
```

---

## Data Acquisition

### Level 2 Data
- Order book
- Market depth
- Bid/ask pressure
- Imbalance

### Sentiment Data
- News
- Social media
- Alternative text streams
- Fear/Greed signals

### Macro Data
- Economic events
- Interest rates
- Fed announcements

### Broker Data
- MT5
- Robinhood
- Alpaca
- Interactive Brokers

**AI does NOT auto-connect.** Human must provide:
- Login
- Password
- Account
- Server
- API keys

Then AI connects when approved.

---

## Security Core

### Protections:
- ✅ Encryption of secrets (Fernet)
- ✅ Isolation of broker credentials
- ✅ Protection from prompt injections
- ✅ Detection of anomalies
- ✅ No sharing of keys
- ✅ No external communication without approval

### Threat Detection:
- Prompt injection patterns
- Credential leak patterns
- Rate limit monitoring
- Anomaly detection

---

## Fail-Safe "NO TRADE" Mode

If ANY of these conditions exist:
- Data is missing
- Architecture unstable
- Risk broken
- Market abnormal
- Spread too wide
- Volatility extreme
- Connection unstable

Then AlphaAlgo enters:

```
╔══════════════════════════════════════╗
║         NO TRADE MODE                ║
║                                      ║
║  "I refuse to trade until           ║
║   conditions are safe."             ║
╚══════════════════════════════════════╝
```

---

## What Must Be Fixed First

Before ANY trading:

1. ✅ Align all modules
2. ✅ Remove broken code
3. ✅ Design broker connection hub
4. ✅ Build human approval layer
5. ✅ Build sandbox environment
6. ✅ Build unified data ingestion pipeline
7. ✅ Build logging & monitoring
8. ✅ Build security system
9. ✅ Verify risk engine
10. ✅ Optimize architecture

---

## Quick Start

```python
from trading_bot.alphaalgo_core import (
    AlphaAlgoOrchestrator,
    quick_start,
    BrokerType,
    DataType,
    ChangeCategory,
)

# Initialize AlphaAlgo
alphaalgo = AlphaAlgoOrchestrator()
await alphaalgo.initialize(master_password="your_secure_password")

# Check if trading is allowed
can_trade, reason = await alphaalgo.can_trade()
print(f"Can trade: {can_trade} - {reason}")

# Get system status
status = alphaalgo.get_system_status()
print(f"Trading mode: {status['trading']['mode']}")
print(f"Health: {status['trading']['health']}")

# Get pending approvals
approvals = alphaalgo.get_pending_approvals()
for approval in approvals:
    print(f"Pending: {approval['description']}")

# Human approves a request
alphaalgo.approve_request("request_id", "human_name")

# Propose a change
change = alphaalgo.propose_change(
    category=ChangeCategory.STRATEGY_LOGIC,
    title="Improve signal accuracy",
    description="Add multi-timeframe confirmation",
    rationale="Reduces false signals by 30%",
    expected_impact="Higher win rate",
    risk_assessment="Low risk - additive change",
    rollback_plan="Remove confirmation logic",
)

# Human approves the change
alphaalgo.approve_change(change['change_id'], "human_name")

# Connect to broker (requires approval for live)
success, msg = await alphaalgo.connect_broker(BrokerType.SIMULATION)

# Fetch data
data = await alphaalgo.fetch_data(DataType.OHLCV, "EURUSD")

# Emergency stop
alphaalgo.emergency_stop("Market crash detected")
```

---

## File Structure

```
trading_bot/alphaalgo_core/
├── __init__.py                 # Module exports
├── central_controller.py       # G0/G1/G2 hierarchy
├── governance_system.py        # Change management
├── broker_hub.py              # Broker connections
├── data_pipeline.py           # Data acquisition
├── security_core.py           # Security system
├── fail_safe.py               # NO TRADE mode
├── self_repair.py             # Architecture analysis
├── mini_ai_factory.py         # Mini-AI creation
└── alphaalgo_orchestrator.py  # Master coordinator
```

---

## Governance Levels for Actions

| Action | Level | Approval |
|--------|-------|----------|
| Deploy code | G0 | Human required |
| Modify risk params | G0 | Human required |
| Change position sizing | G0 | Human required |
| Modify order execution | G0 | Human required |
| Connect live broker | G0 | Human required |
| Enable live trading | G0 | Human required |
| Change governance rules | G0 | Human required |
| Delete data | G0 | Human required |
| External communication | G0 | Human required |
| Create Mini-AI | G1 | Controller can approve |
| Modify strategy params | G1 | Controller can approve |
| Update data sources | G1 | Controller can approve |
| Run backtest | G1 | Controller can approve |
| Generate report | G1 | Controller can approve |
| Clean data | G2 | Mini-AI can execute |
| Engineer features | G2 | Mini-AI can execute |
| Validate signals | G2 | Mini-AI can execute |
| Analyze architecture | G2 | Mini-AI can execute |

---

## Safety Checks

| Check | Description | Failure Action |
|-------|-------------|----------------|
| DATA_AVAILABLE | Data sources connected | NO TRADE |
| DATA_FRESH | Data not stale | NO TRADE |
| ARCHITECTURE_STABLE | No critical issues | NO TRADE |
| RISK_ENGINE_OK | Risk system working | NO TRADE |
| BROKER_CONNECTED | Broker connection active | NO TRADE |
| SPREAD_ACCEPTABLE | Spread within limits | NO TRADE |
| VOLATILITY_NORMAL | Volatility not extreme | CAUTIOUS |
| CONNECTION_STABLE | Network stable | CAUTIOUS |
| MARKET_OPEN | Market is open | NO TRADE |
| NO_HIGH_IMPACT_NEWS | No major news events | CAUTIOUS |
| POSITION_LIMITS_OK | Within position limits | NO TRADE |
| DRAWDOWN_ACCEPTABLE | Drawdown within limits | NO TRADE |

---

## Trading Modes

| Mode | Description |
|------|-------------|
| NO_TRADE | Refuse all trades |
| SIMULATION | Paper trading only |
| PAPER | Paper trading with real data |
| LIVE_CAUTIOUS | Live with reduced size |
| LIVE | Full live trading |

---

## System Health Levels

| Level | Description | Trading |
|-------|-------------|---------|
| CRITICAL | System failure | NO TRADE |
| UNHEALTHY | Major issues | NO TRADE |
| DEGRADED | Some issues | CAUTIOUS |
| HEALTHY | All good | NORMAL |
| OPTIMAL | Everything perfect | FULL |

---

## The AlphaAlgo Creed

> "You learn like a child, grow like an apprentice, analyze like a scientist, fight like a warrior, adapt like an animal species, and refine like an artist. Your growth is infinite, but never uncontrolled. You evolve intelligently, safely, and deliberately."

---

*Document created: December 2024*
*AlphaAlgo Core Version: 1.0*
*Total modules: 9*
*Total lines: ~4,000*

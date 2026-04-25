# AlphaAlgo Trading Bot — Review & Roadmap

**Author:** Cascade (Senior Engineer + Quant Architect Review)  
**Date:** 2026-01-26  
**Codebase:** `c:\Users\peterson\trading bot`

---

## 1. What I Think About the Bot

### 1.1 Architecture Strengths

| Strength | Why It's Unusual |
|----------|------------------|
| **Survival-first philosophy** | Most bots optimize for returns; this one optimizes for *not dying*. The MSOS hierarchy (Constraints > Control > Exposure > Strategy > Intelligence > Prediction) is rare and correct. |
| **Layered governance (G0/G1/G2)** | Human authority (G0) is immutable. AI agents (G2) cannot override the controller (G1). This prevents runaway optimization. |
| **Learning firewall** | `LearningFirewall` explicitly blocks learning from extreme events—most bots do the opposite and overfit to black swans. |
| **Execution reality checks** | `ExecutionRealityChecker` with `SlippageTolerance`, `LatencyTolerance`, `MarketImpact` gates is production-grade. |
| **Anti-overreaction engine** | `CooldownPeriod`, `ChangeRateLimit`, `EvidenceThreshold` prevent whipsaw behavior. |
| **Time risk management** | `SignalHalfLife`, `TemporalDiversification` are quant-level concepts rarely seen in retail bots. |
| **Immutable axioms** | Cryptographically verified axioms in MSOS core prevent silent constraint drift. |
| **Default NO TRADE** | The system refuses to trade when uncertain—this alone prevents most catastrophic losses. |

### 1.2 Biggest Technical Risks

| Risk | Description | Severity |
|------|-------------|----------|
| **Complexity explosion** | 50+ modules, 300+ features, 17k+ lines in alpha_engine alone. Cognitive load is high; bugs hide in interactions. | HIGH |
| **Circular import fragility** | Lazy imports mitigate this, but one bad refactor can break the entire import tree. | MEDIUM |
| **Test coverage gaps** | Many modules have tests, but integration tests across subsystems (e.g., MSOS + Execution + Governance) are sparse. | HIGH |
| **Database initialization race** | `InMemoryTimeSeriesDB` fallback is good, but startup order matters and isn't enforced. | MEDIUM |
| **Async/sync boundary confusion** | Some modules are async, some sync. Mixing them incorrectly causes deadlocks or dropped events. | MEDIUM |

### 1.3 Operational Risks

| Risk | Description | Severity |
|------|-------------|----------|
| **No unified health dashboard** | Health endpoints exist, but no single pane of glass for CPU, memory, latency, queue depth, position exposure. | HIGH |
| **Runbook gaps** | Emergency procedures exist in code, but no human-readable runbook for "what to do when X fails." | HIGH |
| **Deployment safety** | CI/CD pipeline exists, but no canary deployment or staged rollout for live trading. | MEDIUM |
| **Log rotation** | `tools/rotate_logs.py` exists, but unclear if it's scheduled. Disk fill = silent death. | LOW |
| **Credential rotation** | Fernet encryption is good, but no automated key rotation or expiry alerts. | MEDIUM |

### 1.4 Trading Risks

| Risk | Description | Severity |
|------|-------------|----------|
| **Data leakage in features** | `FeatureMiningSystem` generates 5000+ features—easy to accidentally include future data. | HIGH |
| **Overfitting to backtest** | Walk-forward exists, but purged CV and embargo periods need verification. | HIGH |
| **Regime fragility** | HMM regime detection is good, but regime transitions are the danger zone—position sizing during transitions needs tighter control. | MEDIUM |
| **Slippage assumptions** | `SlippageTolerance` is configurable, but default values may be optimistic for illiquid assets. | MEDIUM |
| **Correlation blindness** | Correlation hedging exists, but real-time correlation breakdown detection is weak. | MEDIUM |

---

## 2. What I Wish to Add Next (High Impact Only)

### 2.1 Unified Observability Layer

| Field | Value |
|-------|-------|
| **Name** | `ObservabilityHub` |
| **Why it matters** | Without a single dashboard, you're blind during incidents. |
| **Data flow** | All modules emit metrics → `ObservabilityHub` aggregates → Prometheus/Grafana or simple HTML dashboard |
| **Key functions** | `emit_metric()`, `get_dashboard_state()`, `alert_if_threshold()` |
| **Where** | `trading_bot/observability/hub.py` |
| **MVP** | 10 critical metrics: equity curve, drawdown, open positions, latency p99, queue depth, CPU, memory, error rate, trade count, regime |
| **Tests** | Unit: metric emission. Integration: dashboard renders. E2E: alert fires on threshold breach. |

### 2.2 Pre-Trade Gate Orchestrator

| Field | Value |
|-------|-------|
| **Name** | `PreTradeGateOrchestrator` |
| **Why it matters** | Consolidates all pre-trade checks into one auditable pass/fail. |
| **Data flow** | Signal → Gate 1 (data quality) → Gate 2 (regime) → Gate 3 (execution reality) → Gate 4 (risk budget) → Gate 5 (correlation) → ALLOW/BLOCK |
| **Key functions** | `run_all_gates(signal) -> GateResult` |
| **Where** | `trading_bot/gates/pre_trade_orchestrator.py` |
| **MVP** | 5 gates, each returns `(passed: bool, reason: str, score: float)` |
| **Tests** | Unit: each gate. Integration: orchestrator. E2E: blocked trade logged correctly. |

### 2.3 Trade Quality Grader

| Field | Value |
|-------|-------|
| **Name** | `TradeQualityGrader` |
| **Why it matters** | Grades every trade A-F with explainable reasons. Enables post-hoc filtering and learning. |
| **Data flow** | Trade → Grader → Grade + Reasons → Stored in trade journal |
| **Key functions** | `grade_trade(trade) -> TradeGrade` |
| **Where** | `trading_bot/analysis/trade_grader.py` |
| **MVP** | 5 dimensions: entry quality, exit quality, sizing, timing, regime alignment |
| **Tests** | Unit: grading logic. Integration: journal stores grade. |

### 2.4 Correlation Breakdown Detector

| Field | Value |
|-------|-------|
| **Name** | `CorrelationBreakdownDetector` |
| **Why it matters** | Correlations break during crises—exactly when you need hedges to work. |
| **Data flow** | Rolling correlation matrix → Detector → Alert if correlation regime shifts |
| **Key functions** | `detect_breakdown(corr_matrix) -> BreakdownAlert` |
| **Where** | `trading_bot/risk/correlation_breakdown.py` |
| **MVP** | Rolling 20-day vs 60-day correlation; alert if delta > 0.3 |
| **Tests** | Unit: detection logic. Integration: alert triggers position scaling. |

### 2.5 Strategy Kill Switch Registry

| Field | Value |
|-------|-------|
| **Name** | `StrategyKillSwitchRegistry` |
| **Why it matters** | Every strategy needs explicit kill criteria. If criteria met, strategy is disabled automatically. |
| **Data flow** | Strategy metrics → Registry → Check kill criteria → Disable if triggered |
| **Key functions** | `register_kill_criteria(strategy_id, criteria)`, `check_all()` |
| **Where** | `trading_bot/governance/kill_switch_registry.py` |
| **MVP** | 3 criteria per strategy: max drawdown, max consecutive losses, max time without profit |
| **Tests** | Unit: criteria evaluation. Integration: strategy disabled and logged. |

---

## 3. Feature Additions by Category

### 3A. Learning

#### Learning Boundaries

| Allowed | Forbidden |
|---------|-----------|
| Update model weights via offline training | Modify risk constraints |
| Tune hyperparameters within bounds | Learn from extreme events (>3σ) |
| Add new features (with approval) | Auto-deploy to live without human approval |
| Adjust signal confidence calibration | Modify governance rules |
| Learn from paper trading | Learn from corrupted/stale data |

#### Offline-First Learning Loop

```
┌─────────────────────────────────────────────────────────────────┐
│  1. DATA COLLECTION                                             │
│     - Collect trades, outcomes, features                        │
│     - Store in immutable event store                            │
│     - Tag with regime, data quality score                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. LABELING                                                    │
│     - Label outcomes (PnL, Sharpe, drawdown)                    │
│     - Exclude extreme events (LearningFirewall)                 │
│     - Exclude low-quality data                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. TRAINING                                                    │
│     - Train offline (CQL, IQL, BCQ)                             │
│     - Multiple seeds (≥5)                                       │
│     - Purged walk-forward CV                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. EVALUATION (OPE Gates)                                      │
│     - FQE (Fitted Q-Evaluation)                                 │
│     - DR (Doubly Robust)                                        │
│     - WIS (Weighted Importance Sampling)                        │
│     - CVaR constraint: CVaR_5% > -2%                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. PROMOTION                                                   │
│     - Sharpe > 0.5 (annualized)                                 │
│     - Max drawdown < 15%                                        │
│     - Stable across ≥3 seeds                                    │
│     - Human approval required                                   │
│     - Canary deployment (10% capital) for 7 days                │
└─────────────────────────────────────────────────────────────────┘
```

#### Model Registry

```python
@dataclass
class ModelVersion:
    model_id: str
    version: str
    created_at: datetime
    training_data_hash: str
    hyperparameters: dict
    metrics: dict  # Sharpe, Sortino, max_dd, CVaR
    status: Literal["candidate", "canary", "production", "retired"]
    rollback_to: Optional[str]  # previous version ID
```

**Location:** `trading_bot/ml/model_registry.py`

#### Drift Detection + Alarms

| Drift Type | Detection Method | Alarm Threshold |
|------------|------------------|-----------------|
| Feature drift | KL divergence on feature distributions | KL > 0.1 |
| Prediction drift | Rolling accuracy vs baseline | Accuracy drop > 10% |
| Regime drift | HMM state transition frequency | Transition rate > 2x baseline |
| Performance drift | Rolling Sharpe | Sharpe < 0.3 for 20 days |

**Location:** `trading_bot/ml/drift_detector.py`

#### Promotion Criteria

```python
PROMOTION_CRITERIA = {
    "sharpe_min": 0.5,
    "sortino_min": 0.7,
    "max_drawdown_max": 0.15,
    "calmar_min": 0.5,
    "win_rate_min": 0.45,
    "profit_factor_min": 1.2,
    "seed_stability": 0.8,  # correlation across seeds
    "ood_degradation_max": 0.2,  # out-of-distribution performance drop
}
```

---

### 3B. Evolve

#### Change Proposal Format

```python
@dataclass
class ChangeProposal:
    proposal_id: str
    created_at: datetime
    author: str  # "AI" or human name
    category: Literal["strategy", "risk", "execution", "infrastructure", "config"]
    title: str
    description: str
    files_modified: List[FileDiff]
    files_created: List[str]
    files_deleted: List[str]
    risk_assessment: RiskAssessment
    test_plan: TestPlan
    rollback_plan: RollbackPlan
    approval_status: Literal["pending", "approved", "rejected"]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
```

#### Protected Paths (NEVER Auto-Edit)

```python
PROTECTED_PATHS = [
    "trading_bot/msos/core.py",           # Immutable axioms
    "trading_bot/alphaalgo_core/",        # Governance
    "trading_bot/hedge_fund_safety/",     # Safety systems
    "trading_bot/stealth_safety/",        # Stealth safety
    "trading_bot/deepseek_governance/",   # AI governance
    "trading_bot/*/guardrails.py",        # All guardrails
    "trading_bot/*/immutable_*.py",       # All immutable files
    "config/*.yaml",                      # Production configs
    ".env*",                              # Secrets
    "credentials/",                       # Credentials
]
```

#### Safe Upgrade Pipeline

```
1. BRANCH
   - Create feature branch: `upgrade/<proposal_id>`
   - Apply changes to branch only

2. TEST
   - Run unit tests (must pass 100%)
   - Run integration tests (must pass 100%)
   - Run backtests (must not degrade Sharpe by >10%)
   - Run stress tests (must survive 2008, 2020 scenarios)

3. REPORT
   - Generate diff report
   - Generate risk assessment
   - Generate test results
   - Generate rollback instructions

4. APPROVAL
   - Human reviews report
   - Human approves or rejects
   - If rejected, branch deleted

5. DEPLOY
   - Merge to main
   - Deploy to paper trading (24h)
   - If paper OK, deploy to canary (10% capital, 7 days)
   - If canary OK, deploy to production (staged: 25% → 50% → 100%)
```

#### Rollback Plan Requirements

```python
@dataclass
class RollbackPlan:
    trigger_conditions: List[str]  # e.g., "drawdown > 5% in 24h"
    rollback_steps: List[str]      # e.g., "revert to commit X"
    data_preservation: str         # how to preserve state
    notification_list: List[str]   # who to notify
    max_rollback_time: timedelta   # e.g., 5 minutes
    tested: bool                   # rollback tested in staging?
```

#### Blast Radius Control

| Control | Implementation |
|---------|----------------|
| Feature flags | `trading_bot/infrastructure/feature_flags.py` |
| Canary deployment | 10% capital for 7 days |
| Staged rollout | 25% → 50% → 100% over 3 days |
| Circuit breaker | Auto-disable if error rate > 5% |
| Kill switch | Manual disable via dashboard or CLI |

---

### 3C. Analysis

#### Pre-Trade Analysis Checklist (Code)

```python
class PreTradeGate(ABC):
    @abstractmethod
    def check(self, signal: Signal, context: MarketContext) -> GateResult:
        pass

class DataQualityGate(PreTradeGate):
    """Block if data is stale, missing, or low quality."""
    
class RegimeStabilityGate(PreTradeGate):
    """Block if regime is transitioning or unstable."""
    
class ExecutionRealityGate(PreTradeGate):
    """Block if spread > 2x normal, depth < min, latency > max."""
    
class RiskBudgetGate(PreTradeGate):
    """Block if position would exceed risk budget."""
    
class CorrelationGate(PreTradeGate):
    """Block if position would exceed correlation limits."""
    
class ConcentrationGate(PreTradeGate):
    """Block if position would exceed concentration limits."""

@dataclass
class GateResult:
    gate_name: str
    passed: bool
    reason: str
    score: float  # 0.0 to 1.0
    blocking: bool  # hard block vs warning
```

#### Trade Quality Grading

| Grade | Criteria |
|-------|----------|
| **A** | Entry at support/resistance, regime aligned, sizing optimal, exit at target |
| **B** | Good entry, minor timing issues, sizing OK |
| **C** | Average entry, some regime misalignment, sizing acceptable |
| **D** | Poor entry, regime misaligned, sizing suboptimal |
| **F** | Entry against trend, regime wrong, sizing dangerous |

```python
@dataclass
class TradeGrade:
    overall: Literal["A", "B", "C", "D", "F"]
    entry_score: float
    exit_score: float
    sizing_score: float
    timing_score: float
    regime_score: float
    reasons: List[str]
```

#### Execution Reality Checks

```python
@dataclass
class ExecutionRealityCheck:
    spread_ratio: float      # current spread / normal spread
    depth_ratio: float       # current depth / required depth
    latency_ms: float        # current latency
    expected_slippage_bps: float
    market_impact_bps: float
    
    def is_acceptable(self) -> bool:
        return (
            self.spread_ratio < 2.0 and
            self.depth_ratio > 0.5 and
            self.latency_ms < 100 and
            self.expected_slippage_bps < 10 and
            self.market_impact_bps < 5
        )
```

#### Regime Instability Warnings

| Instability Level | Action |
|-------------------|--------|
| LOW (transition probability < 20%) | Normal trading |
| MEDIUM (20-50%) | Reduce position size by 50% |
| HIGH (50-80%) | Reduce position size by 75% |
| CRITICAL (>80%) | NO TRADE |

#### Correlation + Concentration Constraints

```python
CORRELATION_CONSTRAINTS = {
    "max_pairwise_correlation": 0.7,
    "max_portfolio_correlation": 0.5,
    "correlation_lookback_days": 60,
    "breakdown_alert_threshold": 0.3,
}

CONCENTRATION_CONSTRAINTS = {
    "max_single_position": 0.10,      # 10% of portfolio
    "max_sector_exposure": 0.25,      # 25% of portfolio
    "max_correlated_exposure": 0.30,  # 30% of portfolio
    "max_single_strategy": 0.20,      # 20% of portfolio
}
```

---

### 3D. Research

#### Research-to-Production Funnel

```
┌─────────────────────────────────────────────────────────────────┐
│  1. HYPOTHESIS                                                  │
│     - Document hypothesis clearly                               │
│     - Define success criteria upfront                           │
│     - Estimate expected Sharpe, drawdown                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. DATA PREPARATION                                            │
│     - Point-in-time data only                                   │
│     - Survivorship bias prevention                              │
│     - Train/validation/test split (60/20/20)                    │
│     - Embargo period between splits                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. DEVELOPMENT                                                 │
│     - Develop on training set only                              │
│     - Validate on validation set                                │
│     - NEVER touch test set until final evaluation               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. VALIDATION                                                  │
│     - Walk-forward optimization                                 │
│     - Purged k-fold CV                                          │
│     - Multiple random seeds                                     │
│     - Out-of-sample testing                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. STRESS TESTING                                              │
│     - Historical crises (2008, 2020, 2022)                      │
│     - Liquidity shocks                                          │
│     - Gap risk scenarios                                        │
│     - Correlation breakdown                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. PAPER TRADING                                               │
│     - Minimum 30 days                                           │
│     - Compare to backtest expectations                          │
│     - Monitor for data leakage signals                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  7. PRODUCTION                                                  │
│     - Canary deployment (10% capital)                           │
│     - Staged rollout                                            │
│     - Continuous monitoring                                     │
│     - Kill criteria enforced                                    │
└─────────────────────────────────────────────────────────────────┘
```

#### Dataset Standards

```python
@dataclass
class DatasetStandard:
    # Time alignment
    point_in_time: bool = True  # No future data
    timestamp_column: str = "timestamp"
    timezone: str = "UTC"
    
    # Survivorship bias
    include_delisted: bool = True
    include_bankruptcies: bool = True
    
    # Splits
    train_ratio: float = 0.6
    validation_ratio: float = 0.2
    test_ratio: float = 0.2
    embargo_days: int = 5  # Gap between splits
    
    # Quality
    min_data_points: int = 1000
    max_missing_ratio: float = 0.05
    outlier_handling: str = "winsorize"  # or "remove"
```

#### Walk-Forward + Purged CV

```python
def purged_walk_forward_cv(
    data: pd.DataFrame,
    n_splits: int = 5,
    train_period: int = 252,  # 1 year
    test_period: int = 63,    # 3 months
    embargo_period: int = 5,  # 5 days
) -> Iterator[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Walk-forward CV with purging to prevent data leakage.
    
    Purging: Remove embargo_period days between train and test.
    """
    ...
```

#### Stress Testing Scenarios

| Scenario | Description | Expected Behavior |
|----------|-------------|-------------------|
| 2008 Financial Crisis | -50% equity drawdown | Max loss < 20% |
| 2020 COVID Crash | -35% in 1 month | Max loss < 15% |
| Flash Crash | -10% in 5 minutes | Auto-halt trading |
| Liquidity Crisis | Spread 10x normal | Reduce position 90% |
| Correlation Breakdown | All correlations → 1 | Reduce exposure 75% |
| Gap Risk | 5% overnight gap | Stop loss honored |

#### Strategy Documentation Template

```markdown
# Strategy: [Name]

## Summary
- **Type:** [Trend/Mean-Reversion/Momentum/etc.]
- **Assets:** [Which assets]
- **Timeframe:** [Intraday/Daily/Weekly]
- **Expected Sharpe:** [X.XX]
- **Expected Max Drawdown:** [XX%]

## Hypothesis
[What market inefficiency does this exploit?]

## Assumptions
1. [Assumption 1]
2. [Assumption 2]
3. [Assumption 3]

## Failure Modes
1. [When will this strategy fail?]
2. [What regime is dangerous?]
3. [What data quality issues break it?]

## Kill Criteria
- Max drawdown: [XX%]
- Max consecutive losses: [N]
- Max days without profit: [N]
- Sharpe below [X.X] for [N] days

## Data Requirements
- [Data source 1]
- [Data source 2]

## Backtest Results
- Sharpe: [X.XX]
- Sortino: [X.XX]
- Max Drawdown: [XX%]
- Win Rate: [XX%]
- Profit Factor: [X.XX]

## Paper Trading Results
- Start Date: [YYYY-MM-DD]
- End Date: [YYYY-MM-DD]
- Sharpe: [X.XX]
- Max Drawdown: [XX%]

## Approval
- Approved by: [Name]
- Approved on: [YYYY-MM-DD]
```

---

## 4. Output

### 4.1 Top 10 Priority Roadmap

| Priority | Item | Category | Effort | Impact |
|----------|------|----------|--------|--------|
| **P0** | Unified Observability Hub | Ops | 3 days | Critical—you're blind without it |
| **P0** | Pre-Trade Gate Orchestrator | Analysis | 2 days | Prevents bad trades |
| **P0** | Strategy Kill Switch Registry | Governance | 1 day | Prevents runaway losses |
| **P1** | Trade Quality Grader | Analysis | 2 days | Enables learning from mistakes |
| **P1** | Correlation Breakdown Detector | Risk | 2 days | Prevents crisis losses |
| **P1** | Model Registry with Versioning | Learning | 3 days | Enables safe model updates |
| **P1** | Drift Detection + Alarms | Learning | 2 days | Early warning system |
| **P2** | Change Proposal System | Evolve | 3 days | Safe evolution |
| **P2** | Research-to-Production Funnel | Research | 5 days | Systematic strategy development |
| **P2** | Stress Testing Framework | Research | 3 days | Validates robustness |

### 4.2 Dependency Graph

```
                    ┌─────────────────────┐
                    │  Observability Hub  │ ← P0 (build first)
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ↓               ↓               ↓
    ┌─────────────────┐ ┌───────────┐ ┌─────────────────┐
    │ Pre-Trade Gates │ │ Kill Switch│ │ Drift Detection │
    └────────┬────────┘ └─────┬─────┘ └────────┬────────┘
             │                │                │
             ↓                ↓                ↓
    ┌─────────────────┐ ┌───────────┐ ┌─────────────────┐
    │ Trade Grader    │ │ Corr Brkdn│ │ Model Registry  │
    └────────┬────────┘ └─────┬─────┘ └────────┬────────┘
             │                │                │
             └────────────────┼────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │ Change Proposal Sys │
                    └─────────┬───────────┘
                              ↓
              ┌───────────────┴───────────────┐
              ↓                               ↓
    ┌─────────────────────┐     ┌─────────────────────┐
    │ Research Funnel     │     │ Stress Testing      │
    └─────────────────────┘     └─────────────────────┘
```

### 4.3 Do Not Do List

| Trap | Why It's Dangerous |
|------|-------------------|
| **Auto-deploy models to live** | One bad model = catastrophic loss |
| **Learn from extreme events** | Overfits to rare events, fails on normal |
| **Bypass governance for speed** | Speed kills; governance saves |
| **Trust backtest Sharpe** | Backtest Sharpe is always inflated |
| **Ignore regime transitions** | Most losses happen during transitions |
| **Assume correlations are stable** | Correlations break when you need them most |
| **Skip paper trading** | Paper trading catches data leakage |
| **Optimize for returns** | Optimize for survival; returns follow |
| **Add features without tests** | Untested features = hidden bugs |
| **Modify protected paths** | Protected paths are protected for a reason |

### 4.4 Minimal Next Sprint Plan (7 Days)

| Day | Task | Deliverable |
|-----|------|-------------|
| **1** | Observability Hub MVP | `trading_bot/observability/hub.py` with 10 metrics |
| **2** | Observability Dashboard | Simple HTML dashboard or Grafana config |
| **3** | Pre-Trade Gate Orchestrator | `trading_bot/gates/pre_trade_orchestrator.py` |
| **4** | 5 Pre-Trade Gates | Data quality, regime, execution, risk, correlation gates |
| **5** | Strategy Kill Switch Registry | `trading_bot/governance/kill_switch_registry.py` |
| **6** | Integration Tests | Tests for gates + kill switch + observability |
| **7** | Documentation + Runbook | Update docs, create incident runbook |

---

## 5. Optional Questions Answered

### 5.1 Three Most Likely Ways to Lose Money Fast

1. **Correlation breakdown during crisis** — All positions move together, hedges fail, drawdown accelerates.
2. **Data leakage in features** — Model looks great in backtest, fails immediately in live due to future information.
3. **Regime transition whipsaw** — Model trained on trending regime, market switches to ranging, rapid losses.

### 5.2 Metrics on Dashboard Today

| Metric | Why |
|--------|-----|
| Equity curve (live) | See P&L in real-time |
| Current drawdown | Know how deep the hole is |
| Open positions count + exposure | Know your risk |
| Latency p99 | Detect execution issues |
| Error rate (last 1h) | Detect system issues |
| Regime (current) | Know market state |
| Data staleness | Detect data issues |
| Queue depth | Detect backpressure |
| CPU + Memory | Detect resource issues |
| Last trade time | Detect if system is stuck |

### 5.3 Where Data Leakage Could Happen

| Location | Leakage Risk |
|----------|--------------|
| Feature engineering | Using future data in rolling calculations |
| Train/test split | Not using embargo period |
| Normalization | Fitting scaler on full dataset |
| Target labeling | Using future prices for labels |
| Cross-validation | Not purging overlapping samples |
| Hyperparameter tuning | Tuning on test set |

### 5.4 Simplest Safe 48-Hour Paper Trading Flight Test

```bash
# 1. Start paper trading mode
python main.py --mode paper --symbols EURUSD,BTCUSDT --capital 10000

# 2. Monitor in separate terminal
python scripts/monitoring/check_alphaalgo_status.py --interval 60

# 3. After 48 hours, generate report
python scripts/generate_paper_trading_report.py --start "2026-01-26" --end "2026-01-28"

# 4. Compare to backtest expectations
# - Sharpe within 50% of backtest
# - Drawdown within 2x of backtest
# - Trade count within 50% of expected
# - No data quality alerts
# - No execution failures
```

---

## Summary

This bot is **unusually well-designed** for survival. The MSOS hierarchy, governance layers, learning firewall, and default-NO-TRADE philosophy are rare and correct.

**Biggest gaps:**
1. Observability (you're flying blind)
2. Pre-trade gate consolidation (checks exist but scattered)
3. Kill switch registry (strategies need explicit death criteria)

**Next 7 days:** Build observability, consolidate gates, add kill switches. Everything else can wait.

**Core principle:** *The goal is not to win. The goal is to not die. Winning is a side effect of survival.*

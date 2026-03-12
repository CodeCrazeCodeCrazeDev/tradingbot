# 🧠 P1: HIGH PRIORITY - Core RL/ML Improvements

**Priority**: HIGH  
**Timeline**: Week 3-8  
**Expected Impact**: 30-50% improvement in risk-adjusted returns

---

## Quick Implementation Checklist

### Week 3-4: Offline RL
- [ ] Prepare dataset from historical trades
- [ ] Implement CQL (Conservative Q-Learning)
- [ ] Implement BCQ (Batch-Constrained Q)
- [ ] Deploy offline policy evaluation

### Week 5-6: Forecasting
- [ ] Implement Temporal Fusion Transformer
- [ ] Train on 2 years of data
- [ ] Integrate with risk manager
- [ ] Deploy N-BEATS baseline

### Week 7-8: Agent Orchestration
- [ ] Refactor to planner-verifier-executor
- [ ] Implement Almgren-Chriss execution
- [ ] Add CVaR optimization
- [ ] Deploy Kelly criterion sizing

---

## 1. Offline RL for Safe Policy Learning 🎯

### Problem
Training RL agents live is risky. Offline RL learns from historical data without live risk.

### Research Papers
1. **Conservative Q-Learning (CQL)** - Kumar et al. (NeurIPS 2020)
   - arXiv: https://arxiv.org/abs/2006.04779
   - Core offline RL algorithm to avoid over-optimistic policies

2. **Batch-Constrained Q-Learning (BCQ)** - Fujimoto et al.
   - Restricts actions to dataset support
   - More conservative than CQL

3. **BEAR (Bootstrapping Error Accumulation Reduction)**
   - Another conservative offline method

4. **Offline RL Survey** - Prudencio et al.
   - arXiv: https://arxiv.org/abs/2005.01643
   - Taxonomy, evaluation pitfalls, best practices

### Implementation Files

#### `trading_bot/ml/offline_rl/dataset_builder.py`
**Purpose**: Export historical trades to RL dataset format

**Dataset Format**:
```python
{
  "state": [rsi, macd, volume, ...],  # 50-dim feature vector
  "action": 0,  # 0=hold, 1=long, 2=short
  "reward": 15.50,  # PnL in USD
  "next_state": [rsi_next, macd_next, ...],
  "done": True,  # Trade closed
  "info": {"ticket": 12345, "slippage": 0.5}
}
```

**Data Sources**:
- Last 6 months of paper trades
- Last 12 months of demo trades
- Backtest results (if available)

**Splits**: 70% train, 15% validation, 15% test (temporal split)

#### `trading_bot/ml/offline_rl/cql_agent.py`
**Purpose**: Train conservative Q-learning agent

**Library**: Use `d3rlpy` (offline RL toolkit)

**Hyperparameters**:
- alpha=1.0 (CQL penalty weight)
- tau=0.005 (soft update)
- batch_size=256
- learning_rate=3e-4
- n_epochs=100

**Training**:
```python
from d3rlpy.algos import CQL

cql = CQL(
    actor_learning_rate=3e-4,
    critic_learning_rate=3e-4,
    temp_learning_rate=3e-4,
    alpha_learning_rate=3e-4,
    use_gpu=True
)

cql.fit(
    dataset,
    n_epochs=100,
    eval_episodes=validation_dataset
)
```

#### `trading_bot/ml/offline_rl/bcq_agent.py`
**Purpose**: Train batch-constrained Q-learning agent

**Key Difference**: Trains VAE to model action distribution, constrains policy

#### `trading_bot/ml/offline_rl/ope.py`
**Purpose**: Offline Policy Evaluation - estimate policy value without deployment

**Methods**:
1. **Weighted Importance Sampling (WIS)**: Reweight historical data
2. **Doubly Robust (DR)**: Combine model-based + importance sampling
3. **FQE (Fitted Q Evaluation)**: Fit Q-function for policy

**Usage**: Compare 5 candidate policies, deploy best one

### Success Metrics
- ✅ CQL policy achieves 20%+ higher Sharpe than baseline
- ✅ Zero catastrophic trades in offline evaluation
- ✅ OPE estimates within 10% of live performance

---

## 2. Temporal Fusion Transformer (TFT) for Forecasting 📈

### Problem
Current forecasting is basic. TFT provides interpretable, probabilistic multi-horizon forecasts.

### Research Papers
1. **Temporal Fusion Transformer** - Lim et al. (2021)
   - arXiv: https://arxiv.org/abs/1912.09363
   - Interpretable attention-based forecasting

2. **N-BEATS** - Oreshkin et al.
   - OpenReview: https://openreview.net/forum?id=r1ecqn4YwB
   - Strong baseline for comparison

3. **Informer** - Zhou et al. (AAAI 2021)
   - Efficient long-sequence transformer

### Implementation Files

#### `trading_bot/ml/forecasting/tft_model.py`
**Purpose**: Multi-horizon probabilistic price forecasting

**Library**: `pytorch-forecasting`

**Architecture**:
- Input: 168 hours (1 week) of OHLCV + indicators
- Output: Probabilistic forecasts for 1h, 6h, 24h horizons
- Quantiles: 10th, 50th, 90th percentiles

**Features**:
- **Static**: symbol, day_of_week
- **Known covariates**: time_idx, hour, is_market_open
- **Observed covariates**: price, volume, RSI, MACD, ATR
- **Target**: future returns

**Training**:
```python
from pytorch_forecasting import TemporalFusionTransformer

tft = TemporalFusionTransformer.from_dataset(
    training_data,
    learning_rate=0.03,
    hidden_size=64,
    attention_head_size=4,
    dropout=0.1,
    hidden_continuous_size=16,
    loss=QuantileLoss()
)

trainer = pl.Trainer(max_epochs=50, gpus=1)
trainer.fit(tft, train_dataloader, val_dataloader)
```

#### `trading_bot/ml/forecasting/train_tft.py`
**Purpose**: Training pipeline for TFT

**Dataset**: 2 years of 1-hour bars (17,520 samples)

**Validation**: Walk-forward (last 3 months)

**Metrics**: MAPE, RMSE, calibration score

#### `trading_bot/risk/forecast_based_sizing.py`
**Purpose**: Use forecast uncertainty for position sizing

**Logic**:
- Wide prediction interval (90th - 10th > 50 pips) → reduce size by 50%
- Narrow interval (< 20 pips) → increase size up to Kelly limit
- High confidence (50th percentile favorable) → larger position

**Integration**: Call before every trade

#### `trading_bot/ml/forecasting/nbeats_model.py`
**Purpose**: Simple baseline for comparison

### Success Metrics
- ✅ TFT MAPE < 2% on 1h forecasts
- ✅ Calibrated prediction intervals (90% coverage)
- ✅ 15%+ improvement in risk-adjusted returns

---

## 3. AgentFlow: Multi-Agent Orchestration 🤖

### Problem
Current orchestrator is monolithic. Need planner-verifier-executor separation.

### Research Papers
1. **AgentFlow** - Stanford (2024)
   - HuggingFace: https://huggingface.co/papers/2402.01927
   - In-the-flow agentic system optimization

2. **Multi-Agent RL: A Selective Overview**
   - Survey of MARL techniques

3. **Hierarchical RL: Options Framework**
   - Decomposing decisions (strategy → execution)

### Implementation Files

#### `trading_bot/agents/planner_agent.py`
**Purpose**: Analyze market and propose trades

**Inputs**: Market data, news, sentiment, forecasts

**Outputs**: Trade proposals with reasoning

**Example**:
```python
{
  "action": "long",
  "symbol": "EURUSD",
  "lots": 0.10,
  "reasoning": "TFT forecast bullish, RSI oversold, positive news sentiment",
  "confidence": 0.78,
  "expected_return": 25.0,
  "risk": 10.0
}
```

#### `trading_bot/agents/verifier_agent.py`
**Purpose**: Independent safety checks (can veto trades)

**Runs in**: Separate process for independence

**Checks**:
- Position size within limits
- Correlation exposure acceptable
- Total portfolio risk < 5%
- Forecast confidence > threshold
- No conflicting positions

**Veto Power**: Can reject planner proposals and close existing positions

#### `trading_bot/agents/executor_agent.py`
**Purpose**: Smart order execution

**Algorithms**:
- VWAP (Volume-Weighted Average Price)
- TWAP (Time-Weighted Average Price)
- Adaptive (adjust to market conditions)
- Sniper (wait for favorable liquidity)

**Goal**: Minimize slippage and market impact

#### `trading_bot/orchestrator/agent_orchestrator.py`
**Purpose**: Coordinate planner → verifier → executor pipeline

**Communication**: Redis message queue for async coordination

**Flow**:
1. Planner proposes trade
2. Verifier checks safety
3. If approved → Executor executes
4. If rejected → Log reason, return to planner

### Success Metrics
- ✅ Verifier blocks 100% of limit-violating trades
- ✅ Executor reduces slippage by 30%
- ✅ Modular agents enable A/B testing

---

## 4. Almgren-Chriss Optimal Execution 📊

### Problem
Market orders cause slippage. Need optimal execution scheduling.

### Research Papers
1. **Almgren & Chriss (2000)** - Optimal execution of portfolio transactions
   - Link: https://www.math.nyu.edu/faculty/chriss/optliq_f.pdf
   - Classic model for execution scheduling

2. **Gatheral (2010)** - Market impact models
   - Temporary vs permanent impact

3. **RL for Optimal Execution** - Recent papers
   - Learn adaptive schedules from LOB features

### Implementation Files

#### `trading_bot/execution/almgren_chriss.py`
**Purpose**: Compute optimal execution schedule

**Inputs**:
- Order size (lots)
- Time horizon (minutes)
- Volatility (ATR)
- Market impact parameters (alpha, beta)

**Output**: Execution trajectory (how much to trade each minute)

**Objective**: Minimize cost = market impact + timing risk

#### `trading_bot/execution/impact_calibration.py`
**Purpose**: Estimate market impact from historical fills

**Method**: Fit regression model
```
slippage = alpha * order_size + beta * volatility + gamma * spread
```

**Data**: Last 1000 fills from demo account

#### `trading_bot/execution/execution_scheduler.py`
**Purpose**: Split large orders using Almgren-Chriss

**Example**: 1.0 lot order over 10 minutes
- Minute 1: 0.15 lots
- Minute 2: 0.13 lots
- ...
- Minute 10: 0.08 lots

### Success Metrics
- ✅ 40% reduction in slippage vs market orders
- ✅ Execution cost < 0.5 pips per trade

---

## 5. CVaR Optimization & Kelly Criterion 💰

### Research Papers
1. **CVaR optimization for tail risk** - Downside protection
2. **Kelly criterion modern treatments** - Position sizing
3. **Risk-aware RL** - Enforce exposure constraints

### Implementation Files

#### `trading_bot/risk/cvar_calculator.py`
**Purpose**: Compute 95% CVaR (expected loss in worst 5% scenarios)

**Method**: Historical simulation + Monte Carlo

#### `trading_bot/risk/cvar_optimizer.py`
**Purpose**: Portfolio optimization with CVaR constraint

**Objective**: Maximize expected return

**Constraint**: CVaR < 3% of equity

**Solver**: CVXPY (convex optimization)

#### `trading_bot/risk/kelly_calculator.py`
**Purpose**: Optimal position sizing

**Formula**: f = (p * b - q) / b
- p = win probability
- q = 1-p
- b = win/loss ratio

**Safety**: Use 25% Kelly (fractional Kelly)

#### `trading_bot/risk/dynamic_kelly.py`
**Purpose**: Adjust Kelly fraction based on conditions

**Rules**:
- High confidence → 50% Kelly
- Normal → 25% Kelly
- High volatility → 10% Kelly

### Success Metrics
- ✅ Tail risk (CVaR) reduced by 40%
- ✅ Optimal growth rate without excessive risk
- ✅ Max drawdown < 15%

---

## Dependencies to Install

```bash
pip install d3rlpy pytorch-forecasting pytorch-lightning cvxpy river
```

---

## Implementation Timeline

### Week 3: Offline RL Setup
- Export historical data
- Implement CQL
- Train first model

### Week 4: Offline RL Deployment
- Implement OPE
- Compare policies
- Deploy best policy

### Week 5: TFT Implementation
- Prepare time-series dataset
- Train TFT model
- Validate forecasts

### Week 6: TFT Integration
- Integrate with risk manager
- Deploy forecast-based sizing
- Monitor performance

### Week 7: Agent Refactoring
- Split orchestrator into agents
- Implement verifier
- Add Almgren-Chriss execution

### Week 8: Risk Optimization
- Deploy CVaR optimization
- Implement dynamic Kelly
- Full system testing

---

## Success Criteria

✅ **30%+ improvement in Sharpe ratio**  
✅ **40% reduction in tail risk (CVaR)**  
✅ **20% reduction in slippage**  
✅ **Zero limit violations** (verifier working)  
✅ **Forecast MAPE < 2%**  
✅ **Offline policy matches live within 10%**  

---

## Next Steps

After completing P1, proceed to:
- [RESEARCH_ROADMAP_P2_ADVANCED.md](RESEARCH_ROADMAP_P2_ADVANCED.md) - Advanced ML features

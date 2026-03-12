# Self-Improvement Engine - Complete Guide

## Overview

The Self-Improvement Engine is an automated system that learns from every losing trade, diagnoses root causes, proposes conservative fixes, validates them in canary mode, and applies only low-risk improvements. The system is designed to be **conservative, auditable, and reversible**.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   LOSING TRADE DETECTED                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: TRIAGE                                              │
│  - Classify loss severity (small/medium/large/critical)      │
│  - Collect trade data, signals, market data, system metrics  │
│  - Detect immediate anomalies                                │
│  - Generate diagnostic report                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: ROOT CAUSE ANALYSIS                                 │
│  - Run comprehensive diagnostic checks:                      │
│    A. Signal Quality (confidence, MTF agreement, drift)      │
│    B. Execution Issues (slippage, fills, latency)            │
│    C. Risk Sizing (SL placement, position size)              │
│    D. Market/External (volatility, news, regime)             │
│    E. Software/Data (errors, NaNs, cache issues)             │
│  - Generate ranked hypotheses with confidence scores         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  CONFIDENCE CHECK                                            │
│  If top hypothesis confidence < CONF_THRESHOLD (0.6):        │
│    → ESCALATE TO HUMAN REVIEW                                │
│  Else: Continue                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: CONSERVATIVE FIX GENERATION                         │
│  - Generate safe fixes for each hypothesis                   │
│  - ONLY risk-reducing fixes allowed:                         │
│    ✓ Increase confidence thresholds                          │
│    ✓ Add filters (MTF agreement, time-based)                 │
│    ✓ Reduce position size                                    │
│    ✓ Widen stop losses (ATR-based)                           │
│    ✓ Disable trading in illiquid periods                     │
│    ✓ Clear cache, rollback models                            │
│    ✗ NEVER increase risk, remove SL, or raise lot size       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: BACKUP & BRANCH                                     │
│  - Create git branch: autolearn/<timestamp>_<trade_id>       │
│  - Backup config files to backups/autolearn/                 │
│  - Record all changes in audit trail                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: CANARY VALIDATION                                   │
│  - Run fix in paper/canary mode for configured duration      │
│  - Collect metrics: win rate, drawdown, slippage, signals    │
│  - Compare vs baseline with strict thresholds:               │
│    • Max 10% win rate degradation                            │
│    • Max 5% drawdown increase                                │
│    • Max 0.2% slippage increase                              │
│  - Decision: PASS → promote, FAIL → rollback                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 6: APPLY OR ESCALATE                                   │
│  If AUTO_PROMOTE=true AND canary PASSED:                     │
│    → Apply fix to live config                                │
│  Else:                                                       │
│    → Create PR for human approval                            │
│  If canary FAILED:                                           │
│    → Automatic rollback + log failure                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 7: CONTINUOUS LEARNING                                 │
│  - Add labeled example: (trade features, root cause, fix)    │
│  - Accumulate examples in training database                  │
│  - When threshold reached (500 examples):                    │
│    → Retrain models in sandbox                               │
│    → Validate new model performance                          │
│    → Deploy if improved                                      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. TradeTriage

**Purpose**: Immediate classification and data collection for losing trades.

**Inputs**:
- `trade`: Trade object with entry/exit prices, PnL, fees, slippage
- `signal_data`: Indicators, confidence, timeframe, regime
- `market_data`: Historical candles, ATR, spread, news events
- `system_data`: CPU, memory, latency, errors
- `equity`: Current account equity

**Outputs**:
- `TriageDiagnostic`: Complete diagnostic with:
  - Loss category (SMALL/MEDIUM/LARGE/CRITICAL)
  - PnL and percentage of equity
  - List of detected anomalies
  - Full context for analysis

**Example**:
```python
from trading_bot.self_improvement import TradeTriage

triage = TradeTriage(config={
    'loss_small_threshold': 0.005,  # 0.5%
    'loss_medium_threshold': 0.02,  # 2%
    'max_drawdown': 0.20,  # 20%
    'candles_lookback': 200
})

diagnostic = triage.triage_trade(
    trade=trade_dict,
    signal_data=signal_dict,
    market_data=market_dict,
    system_data=system_dict,
    equity=10000.0
)

print(f"Loss Category: {diagnostic.loss_category}")
print(f"Anomalies: {diagnostic.anomalies}")
```

### 2. RootCauseAnalyzer

**Purpose**: Automated diagnosis of why trades lost money.

**Checks Performed**:

**A. Signal Quality**
- Low model confidence (< 0.5)
- Multi-timeframe disagreement
- High signal drift (post-entry vs pre-entry)

**B. Execution Issues**
- High slippage (> 0.5%)
- Partial fills or rejections
- High execution latency (> 1000ms)

**C. Risk Sizing**
- Stop loss too tight relative to ATR (< 1.5x ATR)
- Position size exceeds limits
- Risk per trade too high

**D. Market & External**
- Sudden volatility spike
- News events during trade
- Market regime mismatch
- Illiquidity (wide spreads, low volume)

**E. Software & Data**
- Missing data or NaN values
- Errors in logs
- Cache corruption
- Model returning invalid values

**Outputs**:
- List of `RootCauseHypothesis` ranked by confidence
- Each hypothesis includes:
  - Description of the problem
  - Confidence score (0.0 to 1.0)
  - Estimated PnL impact
  - Evidence from checks
  - Suggested fixes

**Example**:
```python
from trading_bot.self_improvement import RootCauseAnalyzer

analyzer = RootCauseAnalyzer(config={
    'low_confidence_threshold': 0.5,
    'high_slippage_threshold': 0.005,
    'tight_sl_atr_ratio': 1.5
})

hypotheses = analyzer.analyze(diagnostic)

for i, hyp in enumerate(hypotheses, 1):
    print(f"{i}. {hyp.description}")
    print(f"   Confidence: {hyp.confidence:.2f}")
    print(f"   Suggested fixes: {hyp.suggested_fixes}")
```

### 3. FixGenerator

**Purpose**: Proposes conservative, safe fixes for identified root causes.

**Safety Rules** (CRITICAL):
1. **NEVER** increase `MAX_LOT_SIZE` automatically
2. **NEVER** increase `RISK_PER_TRADE` automatically
3. **NEVER** remove or disable stop losses
4. **NEVER** apply untested changes to live trading
5. **ONLY** propose fixes that reduce risk or maintain current risk

**Allowed Fix Types**:

| Fix Type | Description | Risk Level | Auto-Approvable |
|----------|-------------|------------|-----------------|
| Increase confidence threshold | Filter weak signals | SAFE | Yes |
| Add MTF agreement filter | Require multi-TF confirmation | SAFE | Yes |
| Reduce position size | Lower exposure in risky conditions | SAFE | Yes |
| Widen stop loss (ATR-based) | Avoid noise-induced stops | LOW | Yes |
| Disable illiquid hours | Avoid high-slippage periods | SAFE | Yes |
| Add signal debounce | Require N consecutive candles | SAFE | Yes |
| Clear cache | Fix data corruption | SAFE | Yes |
| Rollback model | Revert to stable checkpoint | LOW | Yes |

**Prohibited Fixes** (require manual approval):
- Increase max lot size
- Increase risk per trade
- Remove stop loss
- Disable risk checks
- Modify core trading logic without testing

**Example**:
```python
from trading_bot.self_improvement import FixGenerator

generator = FixGenerator(config={
    'max_lot_size': 1.0,
    'risk_per_trade': 0.01,
    'min_stop_loss_pips': 10
})

fixes = generator.generate_fixes(hypotheses)

for fix in fixes:
    print(f"Fix: {fix.description}")
    print(f"Risk Level: {fix.risk_level.value}")
    print(f"Auto-approvable: {fix.auto_approvable}")
    print(f"Implementation: {fix.implementation}")
```

### 4. CanaryValidator

**Purpose**: Tests fixes in paper/canary mode before live deployment.

**Canary Configuration**:
- **Duration**: 60 minutes (configurable)
- **Min Trades**: 100 trades (configurable)
- **Instruments**: Subset of symbols (e.g., EURUSD, GBPUSD)
- **Mode**: Paper trading or small live size

**Validation Thresholds**:
```python
{
    'max_win_rate_degradation': 0.10,  # Max 10% drop in win rate
    'max_drawdown_increase': 0.05,     # Max 5% increase in drawdown
    'min_trade_count': 30,              # Minimum trades for validation
    'max_slippage_increase': 0.002     # Max 0.2% slippage increase
}
```

**Metrics Collected**:
- Win rate, losing rate
- Total PnL, average PnL
- Maximum drawdown
- Sharpe ratio
- Average slippage
- Average latency
- Fill rate
- Signal count and rate
- Average confidence

**Decision Logic**:
```
IF all criteria PASSED:
    IF AUTO_PROMOTE = true:
        → Apply fix to live config
    ELSE:
        → Create PR for human approval
ELIF any criteria FAILED:
    → Automatic rollback
    → Log failure reason
    → Add to failures database
ELSE:
    → Extend testing period
```

**Example**:
```python
from trading_bot.self_improvement import CanaryValidator

validator = CanaryValidator(config={
    'canary_duration_minutes': 60,
    'canary_min_trades': 100,
    'canary_instruments': ['EURUSD', 'GBPUSD'],
    'max_win_rate_degradation': 0.10
})

# Start canary
canary_id = validator.start_canary(fix, baseline_metrics)

# ... canary runs for configured duration ...

# Finalize and get result
result = validator.finalize_canary(canary_id)

if result.status == ValidationStatus.PASSED:
    print("✓ Canary passed, ready for promotion")
else:
    print(f"✗ Canary failed: {result.failed_criteria}")
```

### 5. AuditLogger

**Purpose**: Maintains complete audit trail of all decisions and actions.

**Logged Events**:
- Triage diagnostics
- Root cause hypotheses
- Proposed fixes
- Canary start/results
- Fix applications
- Rollbacks
- Model updates
- Escalations to human review

**Output Structure**:
```
diagnostics/self_improve/
├── <trade_id>/
│   ├── triage_<timestamp>.json
│   ├── hypotheses_<timestamp>.json
│   ├── fixes_<timestamp>.json
│   ├── canary_<canary_id>.json
│   └── decision_<timestamp>.json
├── failures.json
└── changes-log.txt
```

**Changes Log Format**:
```
[2025-01-09 12:30:45] TRADE_001 | TRIAGE | LOSS_MEDIUM | 2 anomalies
[2025-01-09 12:30:46] TRADE_001 | HYPOTHESIS | Low confidence | conf=0.78
[2025-01-09 12:30:47] TRADE_001 | FIX_PROPOSED | Increase threshold | SAFE
[2025-01-09 12:30:48] TRADE_001 | CANARY_START | canary_fix_001_1234567890
[2025-01-09 13:30:48] TRADE_001 | CANARY_PASSED | win_rate +5%, drawdown -2%
[2025-01-09 13:30:49] TRADE_001 | FIX_APPLIED | config.yaml updated
```

### 6. ContinuousLearner

**Purpose**: Accumulates labeled examples and retrains models.

**Learning Process**:
1. **Collect Examples**: Each losing trade becomes a labeled training example
   - Features: Indicators, market conditions, system state
   - Label: Root cause type
   - Metadata: Fix applied, outcome

2. **Accumulate**: Store in training database until threshold reached (default: 500 examples)

3. **Retrain in Sandbox**:
   - Train new model on accumulated examples
   - Use cross-validation
   - Evaluate on held-out test set

4. **Validate**:
   - Compare new model vs current model
   - Metrics: Accuracy, precision, recall, F1
   - Must show improvement to deploy

5. **Deploy**:
   - Version new model
   - Gradual rollout (canary → full)
   - Monitor performance
   - Rollback if degradation detected

**Example**:
```python
from trading_bot.self_improvement import ContinuousLearner

learner = ContinuousLearner(config={
    'model_dir': 'models/self_improvement',
    'retrain_threshold': 500,
    'validation_split': 0.2
})

# Add training example
learner.add_training_example(
    features=feature_dict,
    label='signal_quality',
    metadata={'fix_applied': 'increase_threshold', 'outcome': 'success'}
)

# Check if retraining needed
if learner.should_retrain():
    result = learner.retrain_model_in_sandbox()
    if result['status'] == 'success':
        print(f"New model version: {result['version']}")
        print(f"Metrics: {result['metrics']}")
```

## Configuration

### Complete Configuration Example

```yaml
self_improvement:
  # Master switches
  AUTO_LEARN: true              # Enable/disable self-improvement
  CONF_THRESHOLD: 0.6           # Confidence threshold for escalation
  AUTO_PROMOTE: false           # Auto-apply fixes (false = require approval)
  
  # Paths
  repo_path: "."
  backup_dir: "diagnostics/self_improve/backups"
  
  # Triage settings
  triage:
    loss_small_threshold: 0.005    # 0.5% of equity
    loss_medium_threshold: 0.02    # 2% of equity
    max_drawdown: 0.20             # 20% max drawdown
    candles_lookback: 200          # Historical candles to collect
    news_window_minutes: 30        # News event window
  
  # Root cause analysis
  root_cause:
    low_confidence_threshold: 0.5
    high_slippage_threshold: 0.005    # 0.5%
    high_latency_threshold: 1000      # milliseconds
    tight_sl_atr_ratio: 1.5           # SL should be >= 1.5x ATR
    volatility_spike_threshold: 2.0   # 2x normal volatility
  
  # Fix generation
  fix_generator:
    max_lot_size: 1.0                 # NEVER increase automatically
    risk_per_trade: 0.01              # NEVER increase automatically
    min_stop_loss_pips: 10            # Minimum SL distance
  
  # Canary validation
  canary:
    canary_duration_minutes: 60
    canary_min_trades: 100
    canary_instruments: ["EURUSD", "GBPUSD"]
    max_win_rate_degradation: 0.10   # 10%
    max_drawdown_increase: 0.05      # 5%
    min_trade_count: 30
    max_slippage_increase: 0.002     # 0.2%
  
  # Audit logging
  audit:
    log_dir: "diagnostics/self_improve"
    changes_log: "diagnostics/changes-log.txt"
  
  # Continuous learning
  learning:
    model_dir: "models/self_improvement"
    retrain_threshold: 500           # Retrain after N examples
    validation_split: 0.2            # 20% for validation
```

## Usage Examples

### Basic Usage

```python
from trading_bot.self_improvement import SelfImprovementEngine

# Initialize engine
config = {
    'AUTO_LEARN': True,
    'CONF_THRESHOLD': 0.6,
    'AUTO_PROMOTE': False,
    # ... other config ...
}

engine = SelfImprovementEngine(config)

# Process a losing trade
result = engine.process_losing_trade(
    trade=trade_dict,
    signal_data=signal_dict,
    market_data=market_dict,
    system_data=system_dict,
    equity=10000.0
)

# Check result
if result['status'] == 'processed':
    print(f"Fixes proposed: {result['fixes_proposed']}")
    print(f"Canary validations started: {len(result['canary_results'])}")
elif result['status'] == 'escalated':
    print(f"Escalated to human review: {result['reason']}")
```

### Integration with Trading Loop

```python
class TradingBot:
    def __init__(self):
        self.engine = SelfImprovementEngine(config)
        # ... other initialization ...
    
    async def on_trade_closed(self, trade):
        """Called when a trade closes."""
        # Check if trade was a loss
        if trade['pnl'] < 0:
            # Collect all required data
            signal_data = self._get_signal_context(trade)
            market_data = self._get_market_snapshot(trade)
            system_data = self._get_system_metrics()
            equity = self.get_account_equity()
            
            # Process the loss
            result = self.engine.process_losing_trade(
                trade, signal_data, market_data, system_data, equity
            )
            
            # Log result
            logger.info(f"Self-improvement result: {result['status']}")
```

### Manual Canary Finalization

```python
# After canary has run for configured duration
canary_id = "canary_fix_001_1234567890"

result = engine.finalize_canary(canary_id)

if result['status'] == 'applied':
    print("✓ Fix applied successfully")
elif result['status'] == 'rollback':
    print(f"✗ Fix rolled back: {result['reason']}")
elif result['status'] == 'awaiting_approval':
    print("⏳ Awaiting human approval")
    # Show approval UI to user
```

## Safety Protocols

### 1. Never Increase Risk Automatically

The engine is **hardcoded** to never:
- Increase `MAX_LOT_SIZE`
- Increase `RISK_PER_TRADE`
- Remove stop losses
- Disable risk management checks

Any attempt to do so will be **rejected** at the fix generation stage.

### 2. Confidence-Based Escalation

If the top hypothesis has confidence < `CONF_THRESHOLD` (default 0.6), the system:
1. Does NOT apply any fixes automatically
2. Creates a pause request file: `diagnostics/PAUSE-REQUEST-<timestamp>.md`
3. Logs the escalation with full context
4. Waits for human review

### 3. Automatic Rollback

If a canary validation fails:
1. Immediately revert all changes
2. Checkout previous git commit
3. Restore backup config files
4. Log failure with detailed metrics
5. Add to failures database for future reference

### 4. Git Branching

Every fix attempt creates a new git branch:
```
autolearn/<timestamp>_<trade_id>
```

This allows:
- Easy rollback
- Code review before merge
- Tracking of all attempted changes
- Isolation of experiments

### 5. Complete Audit Trail

Every action is logged with:
- Timestamp
- Trade ID
- Action type
- Parameters
- Result
- Metrics

This enables:
- Full traceability
- Regulatory compliance
- Post-mortem analysis
- Performance tracking

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Self-Improvement Activity**
   - Losing trades processed per day
   - Hypotheses generated
   - Fixes proposed
   - Canaries started
   - Fixes applied

2. **Escalations**
   - Number of escalations to human review
   - Reasons for escalation
   - Average confidence of escalated cases

3. **Canary Performance**
   - Canary pass rate
   - Canary fail rate
   - Average improvement in metrics
   - Rollback frequency

4. **Model Performance**
   - Root cause prediction accuracy
   - False positive rate
   - False negative rate
   - Model version history

### Alert Conditions

Set up alerts for:
- ⚠️ High escalation rate (> 50% of losses)
- ⚠️ Low canary pass rate (< 30%)
- ⚠️ Frequent rollbacks (> 3 per day)
- ⚠️ Model accuracy drop (< 70%)
- 🚨 Any attempt to increase risk parameters
- 🚨 System errors in self-improvement pipeline

## Troubleshooting

### Issue: Too Many Escalations

**Symptom**: Most losing trades are escalated to human review.

**Possible Causes**:
- `CONF_THRESHOLD` too high
- Insufficient training data for root cause models
- Complex/novel failure modes

**Solutions**:
1. Lower `CONF_THRESHOLD` to 0.5 (from 0.6)
2. Add more labeled training examples
3. Review escalated cases and add to training data
4. Improve feature engineering for root cause detection

### Issue: Canaries Keep Failing

**Symptom**: Most canary validations fail.

**Possible Causes**:
- Validation thresholds too strict
- Fixes not addressing root cause
- Market conditions changed during canary

**Solutions**:
1. Review failed canary metrics
2. Adjust validation thresholds if too strict
3. Improve hypothesis generation
4. Extend canary duration for more data

### Issue: No Fixes Generated

**Symptom**: Root causes identified but no fixes proposed.

**Possible Causes**:
- All potential fixes are high-risk
- Fix generator too conservative
- Missing fix templates for identified causes

**Solutions**:
1. Review hypothesis types
2. Add new safe fix templates
3. Check fix generator configuration
4. Consider manual fixes for complex cases

## Best Practices

### 1. Start Conservative

- Set `AUTO_PROMOTE = false` initially
- Review all proposed fixes manually
- Build confidence in the system gradually
- Enable `AUTO_PROMOTE` only for SAFE risk level fixes

### 2. Monitor Continuously

- Review audit logs daily
- Track key metrics
- Investigate anomalies
- Adjust thresholds based on performance

### 3. Maintain Training Data Quality

- Review and validate labeled examples
- Remove outliers and errors
- Balance dataset across root cause types
- Regularly retrain models

### 4. Test in Staging First

- Run self-improvement in staging environment
- Validate all fixes before production
- Use paper trading for initial canaries
- Gradual rollout to live trading

### 5. Document Everything

- Keep detailed notes on manual interventions
- Document why certain fixes were rejected
- Track long-term impact of applied fixes
- Share learnings with team

## Advanced Topics

### Custom Fix Templates

Add custom fix templates for your specific strategies:

```python
class CustomFixGenerator(FixGenerator):
    def _fixes_for_custom_cause(self, hypothesis):
        """Generate fixes for custom root cause."""
        fixes = []
        
        if "custom condition" in hypothesis.description:
            fixes.append(ProposedFix(
                fix_id=f"{hypothesis.hypothesis_id}_custom",
                hypothesis_id=hypothesis.hypothesis_id,
                fix_type=FixType.PARAMETER_ADJUSTMENT,
                risk_level=RiskLevel.SAFE,
                description="Custom fix description",
                implementation={
                    'config_file': 'config/custom.yaml',
                    'parameter': 'custom.parameter',
                    'current_value': 0.5,
                    'new_value': 0.7
                },
                expected_impact="Expected improvement",
                rollback_plan="Revert parameter",
                validation_criteria={'metric': 0.1},
                auto_approvable=True
            ))
        
        return fixes
```

### Multi-Stage Canary

Implement progressive rollout:

```python
# Stage 1: Paper trading (0% live)
canary_1 = validator.start_canary(fix, stage='paper')

# Stage 2: 10% live traffic
if canary_1.passed:
    canary_2 = validator.start_canary(fix, stage='10pct')

# Stage 3: 50% live traffic
if canary_2.passed:
    canary_3 = validator.start_canary(fix, stage='50pct')

# Stage 4: 100% rollout
if canary_3.passed:
    apply_fix(fix)
```

### A/B Testing Framework

Compare multiple fixes simultaneously:

```python
# Create multiple fix variants
fix_a = generator.generate_fix(hypothesis, variant='A')
fix_b = generator.generate_fix(hypothesis, variant='B')

# Run parallel canaries
canary_a = validator.start_canary(fix_a)
canary_b = validator.start_canary(fix_b)

# Compare results
if canary_a.metrics.win_rate > canary_b.metrics.win_rate:
    apply_fix(fix_a)
else:
    apply_fix(fix_b)
```

## FAQ

**Q: Will this system trade automatically without my approval?**

A: Only if you set `AUTO_PROMOTE = true` AND the fix is classified as SAFE or LOW risk. Medium and HIGH risk fixes always require human approval.

**Q: Can the system increase my risk exposure?**

A: No. The system is hardcoded to never increase `MAX_LOT_SIZE`, `RISK_PER_TRADE`, or remove stop losses automatically.

**Q: What happens if a fix makes things worse?**

A: The canary validation will detect degraded performance and automatically rollback the fix. All changes are reversible.

**Q: How long does a canary run?**

A: Default is 60 minutes or 100 trades, whichever comes first. This is configurable.

**Q: Can I disable the self-improvement system?**

A: Yes, set `AUTO_LEARN = false` in the configuration.

**Q: Where are all the logs stored?**

A: In `diagnostics/self_improve/` with subdirectories for each trade and a master `changes-log.txt`.

**Q: How do I review proposed fixes before they're applied?**

A: Set `AUTO_PROMOTE = false`. The system will create detailed reports in the audit logs and wait for your approval.

**Q: Can I add my own root cause checks?**

A: Yes, extend the `RootCauseAnalyzer` class and add custom check methods.

**Q: How often should models be retrained?**

A: Default is every 500 new labeled examples. Adjust based on your trading frequency.

**Q: What if I want to manually trigger a fix?**

A: Use the `FixGenerator` directly to create a fix, then use `CanaryValidator` to test it before applying.

## Conclusion

The Self-Improvement Engine provides a robust, safe, and auditable way for your trading bot to learn from losses automatically. By following the guidelines in this document and starting conservatively, you can gradually enable more automation while maintaining full control and visibility.

Remember the core principles:
- **Conservative**: Never increase risk automatically
- **Auditable**: Complete trail of all decisions
- **Reversible**: All changes can be rolled back
- **Validated**: Canary testing before deployment
- **Monitored**: Continuous performance tracking

For support or questions, refer to the audit logs and escalation reports, or consult with your development team.

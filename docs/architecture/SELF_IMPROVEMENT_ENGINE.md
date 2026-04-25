# Self-Improvement Engine Documentation
## Automated Learning from Losing Trades

**Version:** 1.0  
**Status:** Production Ready  
**Safety Level:** Conservative with Human Oversight

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Safety Principles](#safety-principles)
4. [Workflow](#workflow)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Audit Trail](#audit-trail)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Self-Improvement Engine is an autonomous system that automatically analyzes losing trades, diagnoses root causes, generates safe corrective actions, validates fixes in canary mode, and applies only low-risk improvements.

### Key Features

✅ **Conservative by Design** - Never increases risk automatically  
✅ **Fully Auditable** - Complete audit trail of all decisions  
✅ **Reversible** - All changes backed up and can be rolled back  
✅ **Human Oversight** - Escalates ambiguous cases for review  
✅ **Canary Testing** - Validates fixes before live deployment  
✅ **Continuous Learning** - Accumulates labeled examples for model improvement

### Safety Guarantees

**NEVER Automatically:**
- Increase MAX_LOT_SIZE
- Increase RISK_PER_TRADE
- Remove stop-loss or take-profit
- Bypass validation checks
- Apply untested changes to live trading

**ONLY Automatically:**
- Reduce risk or maintain current levels
- Add protective filters
- Improve signal quality
- Fix data/software issues
- Throttle trading frequency

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                  Self-Improvement Engine                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Triage     │→ │ Root Cause   │→ │     Fix      │      │
│  │   Module     │  │   Analyzer   │  │  Generator   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         ↓                  ↓                  ↓              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Audit     │  │    Canary    │  │  Continuous  │      │
│  │    Logger    │  │  Validator   │  │   Learner    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Module Descriptions

#### 1. Triage Module
**Purpose:** Immediate classification and data collection  
**Inputs:** Trade data, signal context, market snapshot, system metrics  
**Outputs:** TriageDiagnostic with loss category and anomalies

**Loss Categories:**
- `LOSS_SMALL`: <0.5% of equity
- `LOSS_MEDIUM`: 0.5-2% of equity
- `LOSS_LARGE`: >2% of equity
- `LOSS_CRITICAL`: Exceeds MAX_DRAWDOWN

#### 2. Root Cause Analyzer
**Purpose:** Automated diagnosis of why trades lost  
**Method:** Runs 5 categories of checks with evidence collection

**Check Categories:**
- **A. Signal Quality:** Confidence, multi-TF agreement, drift
- **B. Execution Issues:** Slippage, fills, latency
- **C. Risk Sizing:** Stop loss placement, position size
- **D. Market/External:** Volatility, news, liquidity
- **E. Software/Data:** Errors, resource usage, data quality

**Output:** Ranked hypotheses with confidence scores

#### 3. Fix Generator
**Purpose:** Propose conservative, safe fixes  
**Safety:** Only generates risk-reducing or risk-neutral fixes

**Fix Types:**
- `CONFIG_CHANGE`: Modify configuration parameters
- `PARAMETER_ADJUSTMENT`: Adjust thresholds/multipliers
- `FILTER_ADD`: Add protective filters
- `THRESHOLD_CHANGE`: Increase quality thresholds
- `DISABLE_FEATURE`: Temporarily disable problematic features
- `MODEL_ROLLBACK`: Revert to previous model version
- `CACHE_CLEAR`: Clear stale data

**Risk Levels:**
- `SAFE`: No risk increase, auto-approvable
- `LOW`: Minimal risk, auto-approvable with monitoring
- `MEDIUM`: Requires human approval
- `HIGH`: Requires human approval and testing
- `PROHIBITED`: Never auto-apply

#### 4. Canary Validator
**Purpose:** Test fixes in paper/canary mode before live deployment  
**Duration:** 60 minutes or 100 trades (configurable)  
**Instruments:** Subset of symbols for testing

**Validation Criteria:**
- Win rate degradation < 10%
- Drawdown increase < 5%
- Slippage increase < 0.2%
- Minimum 30 trades for statistical significance

#### 5. Audit Logger
**Purpose:** Maintain comprehensive audit trail  
**Logs:** All diagnostics, hypotheses, fixes, validations, decisions

**Log Files:**
- `{timestamp}_triage_{trade_id}.json`
- `{timestamp}_root_cause_{trade_id}.json`
- `{timestamp}_fixes_{trade_id}.json`
- `{timestamp}_canary_result_{fix_id}.json`
- `{timestamp}_apply_{fix_id}.json`
- `PAUSE-REQUEST-{timestamp}.md` (escalations)
- `changes-log.txt` (chronological log)

#### 6. Continuous Learner
**Purpose:** Accumulate labeled examples and retrain models  
**Trigger:** After 500 labeled examples (configurable)  
**Process:** Train in sandbox → Validate → Promote if passing

---

## Safety Principles

### 1. Never Increase Risk Automatically

**Prohibited Actions:**
```python
# NEVER automatically:
MAX_LOT_SIZE += x  # ❌
RISK_PER_TRADE += x  # ❌
stop_loss = None  # ❌
take_profit = None  # ❌
```

**Allowed Actions:**
```python
# ONLY automatically:
confidence_threshold += x  # ✅ (reduces false signals)
position_size *= 0.5  # ✅ (reduces risk)
stop_loss_atr_multiplier += x  # ✅ (wider stops, safer)
# (with compensating position size reduction)
```

### 2. Backup Before Changes

Every change creates:
- Git branch: `autolearn/{timestamp}_{trade_id}`
- Backup snapshot in `backups/autolearn/`
- Audit log entry

### 3. Canary First

**No fix goes live without:**
1. Passing safety validation
2. Running in canary mode
3. Meeting performance criteria
4. Human approval (if AUTO_PROMOTE=false)

### 4. Fail-Safe & Rollback

**Automatic rollback if:**
- Canary validation fails
- Performance degrades >15%
- System errors increase
- Drawdown exceeds threshold

### 5. Audit Trail

**Every action logged:**
- What was changed
- Why it was changed
- Who/what approved it
- Results of the change
- Rollback procedure

### 6. Escalate for Ambiguity

**Escalate to human if:**
- Confidence < CONF_THRESHOLD (default 0.6)
- Multiple similar losses in short period
- Critical loss (>MAX_DRAWDOWN)
- System errors detected
- Ambiguous root cause

---

## Workflow

### Complete Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. LOSING TRADE OCCURS                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. TRIAGE                                                    │
│    - Classify loss severity                                  │
│    - Collect trade data, signals, market data, system metrics│
│    - Detect immediate anomalies                              │
│    - Output: TriageDiagnostic                                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. ROOT CAUSE ANALYSIS                                       │
│    - Run 5 categories of checks (A-E)                        │
│    - Generate 1-3 ranked hypotheses                          │
│    - Include confidence scores and evidence                  │
│    - Output: List[RootCauseHypothesis]                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. CONFIDENCE CHECK                                          │
│    - If confidence < CONF_THRESHOLD → ESCALATE               │
│    - Create PAUSE-REQUEST-{timestamp}.md                     │
│    - Wait for human review                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. FIX GENERATION                                            │
│    - Map hypotheses → safe fixes                             │
│    - Validate safety (no risk increase)                      │
│    - Filter by risk level                                    │
│    - Output: List[ProposedFix]                               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. BACKUP & BRANCH                                           │
│    - Create git branch: autolearn/{timestamp}_{trade_id}    │
│    - Create backup snapshot                                  │
│    - Log to audit trail                                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. CANARY VALIDATION                                         │
│    - Start canary run (60 min or 100 trades)                │
│    - Collect metrics: win rate, drawdown, slippage, etc.    │
│    - Compare vs baseline                                     │
│    - Output: ValidationResult                                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. DECISION                                                  │
│    - If PASSED + AUTO_PROMOTE=true → APPLY                  │
│    - If PASSED + AUTO_PROMOTE=false → CREATE PR              │
│    - If FAILED → ROLLBACK                                    │
│    - Log decision to audit trail                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. CONTINUOUS LEARNING                                       │
│    - Add labeled example to training set                     │
│    - If 500+ examples → Retrain model in sandbox             │
│    - Validate sandbox model                                  │
│    - Promote if passing thresholds                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Main Configuration File

**Location:** `config/loss_learning_config.yaml`

**Key Settings:**

```yaml
# Global settings
AUTO_LEARN: true  # Enable/disable system
CONF_THRESHOLD: 0.6  # Confidence threshold for auto-action
AUTO_PROMOTE: false  # Require human approval

# Safety limits (NEVER increase automatically)
fix_generator:
  max_lot_size: 1.0
  risk_per_trade: 0.01
  min_stop_loss_pips: 10

# Canary settings
canary:
  canary_duration_minutes: 60
  canary_min_trades: 100
  max_win_rate_degradation: 0.10
  max_drawdown_increase: 0.05

# Learning settings
learning:
  min_examples_for_retrain: 500
  rolling_window_size: 10000
  min_model_accuracy: 0.6
```

### Environment Variables

```bash
# Optional overrides
export AUTO_LEARN=true
export CONF_THRESHOLD=0.7
export AUTO_PROMOTE=false
```

---

## Usage

### Basic Integration

```python
from trading_bot.self_improvement import SelfImprovementEngine
import yaml

# Load configuration
with open('config/loss_learning_config.yaml') as f:
    config = yaml.safe_load(f)

# Initialize engine
engine = SelfImprovementEngine(config)

# Process losing trade
result = engine.process_losing_trade(
    trade=trade_dict,
    signal_data=signal_dict,
    market_data=market_dict,
    system_data=system_dict,
    equity=current_equity
)

# Check result
if result['status'] == 'processed':
    print(f"Fixes proposed: {result['fixes_proposed']}")
elif result['status'] == 'escalated':
    print(f"Escalated: {result['reason']}")
```

### Integration with Trading Loop

```python
async def trading_loop():
    engine = SelfImprovementEngine(config)
    
    while trading:
        # Execute trade
        trade_result = await execute_trade()
        
        # If loss, trigger self-improvement
        if trade_result['pnl'] < 0:
            improvement_result = engine.process_losing_trade(
                trade=trade_result,
                signal_data=get_signal_context(),
                market_data=get_market_snapshot(),
                system_data=get_system_metrics(),
                equity=get_current_equity()
            )
            
            # Log result
            logger.info(f"Self-improvement: {improvement_result['status']}")
```

### Manual Canary Finalization

```python
# After canary duration elapses
canary_id = "canary_fix_12345_1234567890"

# Finalize and get decision
result = engine.finalize_canary(canary_id)

if result['status'] == 'applied':
    print("Fix applied successfully")
elif result['status'] == 'rollback':
    print(f"Rolled back: {result['reason']}")
```

### Check System Status

```python
status = engine.get_status()

print(f"Labeled examples: {status['labeled_examples']}")
print(f"Ready for retrain: {status['ready_for_retrain']}")
print(f"Active canaries: {status['active_canaries']}")
print(f"Audit summary: {status['audit_summary']}")
```

---

## Audit Trail

### Log Files

All logs stored in: `diagnostics/self_improve/`

**File Naming Convention:**
```
{YYYYMMDD_HHMMSS}_{type}_{identifier}.json
```

**Examples:**
```
20251009_103045_triage_DEMO_12345.json
20251009_103046_root_cause_DEMO_12345.json
20251009_103047_fixes_DEMO_12345.json
20251009_103100_canary_start_canary_fix_001.json
20251009_110100_canary_result_fix_001.json
20251009_110101_apply_fix_001.json
```

### Changes Log

**Location:** `diagnostics/changes-log.txt`

**Format:**
```
[20251009_103045] CANARY_START: canary_fix_001 for fix fix_001
[20251009_110100] CANARY_RESULT: fix_001 - passed - promote
[20251009_110101] FIX_APPLY_SUCCESS: fix_001 - Applied successfully
[20251009_120000] MODEL_UPDATE: v2 - accuracy: 0.650
```

### Escalation Requests

**Location:** `diagnostics/self_improve/PAUSE-REQUEST-{timestamp}.md`

**Contents:**
- Trade ID and timestamp
- Reason for escalation
- Confidence level
- Review checklist
- Files to review

---

## Troubleshooting

### Common Issues

#### 1. Low Confidence Escalations

**Symptom:** Many trades escalated for human review

**Solutions:**
- Lower `CONF_THRESHOLD` (e.g., 0.5 instead of 0.6)
- Improve signal quality
- Add more training examples
- Retrain models

#### 2. Canary Validations Failing

**Symptom:** Fixes consistently fail canary validation

**Solutions:**
- Review validation thresholds (may be too strict)
- Increase `canary_duration_minutes` for more data
- Check if baseline metrics are accurate
- Review fix implementation

#### 3. No Fixes Generated

**Symptom:** Root causes identified but no fixes proposed

**Solutions:**
- Check if fixes are being filtered by safety validation
- Review `fix_generator` configuration
- Check logs for prohibited actions
- May need to add new fix types

#### 4. Model Not Retraining

**Symptom:** Accumulated examples but no retraining

**Solutions:**
- Check `min_examples_for_retrain` threshold
- Verify sandbox directory permissions
- Check model training logs
- Ensure sufficient compute resources

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('trading_bot.self_improvement')
logger.setLevel(logging.DEBUG)
```

### Audit Log Review

```bash
# View recent changes
tail -n 50 diagnostics/changes-log.txt

# Count diagnostics
ls diagnostics/self_improve/*_triage_*.json | wc -l

# Find escalations
ls diagnostics/self_improve/PAUSE-REQUEST-*.md

# View specific diagnostic
cat diagnostics/self_improve/20251009_103045_triage_DEMO_12345.json | jq .
```

---

## Best Practices

### 1. Start Conservative

- Set `AUTO_PROMOTE=false` initially
- Use `CONF_THRESHOLD=0.7` or higher
- Monitor for 1-2 weeks before enabling auto-promotion

### 2. Regular Review

- Review audit logs weekly
- Check escalation requests daily
- Monitor canary success rates
- Review applied fixes monthly

### 3. Gradual Automation

**Phase 1:** Manual approval for all fixes  
**Phase 2:** Auto-approve SAFE risk level only  
**Phase 3:** Auto-approve SAFE and LOW risk levels  
**Phase 4:** Full automation with monitoring

### 4. Backup Strategy

- Keep 30 days of audit logs
- Maintain git history of all branches
- Regular backups of training data
- Document all manual interventions

### 5. Performance Monitoring

- Track fix effectiveness over time
- Monitor for regression after fixes
- Compare pre/post fix metrics
- Maintain performance dashboard

---

## Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- Check for escalation requests
- Monitor active canaries
- Review changes log

**Weekly:**
- Review audit summary
- Check model retraining status
- Analyze fix success rates
- Update documentation

**Monthly:**
- Full audit log review
- Performance analysis
- Configuration tuning
- Model performance evaluation

### Getting Help

**Documentation:**
- This file: `docs/SELF_IMPROVEMENT_ENGINE.md`
- Configuration: `config/loss_learning_config.yaml`
- Examples: `examples/loss_learning_demo.py`

**Logs:**
- Audit logs: `diagnostics/self_improve/`
- Changes log: `diagnostics/changes-log.txt`
- System logs: `logs/`

---

## Appendix

### A. Example Fixes by Root Cause

| Root Cause | Example Fix | Risk Level |
|------------|-------------|------------|
| Low confidence | Increase confidence threshold | SAFE |
| MTF disagreement | Require MTF agreement | SAFE |
| High slippage | Reduce position size 50% | SAFE |
| Tight stop loss | Increase SL to 1.5x ATR | SAFE |
| Volatility spike | Add volatility filter | SAFE |
| News events | Add news filter | SAFE |
| System errors | Clear cache, rebuild | SAFE |

### B. Validation Metrics

| Metric | Threshold | Action if Exceeded |
|--------|-----------|-------------------|
| Win rate degradation | 10% | Fail canary |
| Drawdown increase | 5% | Fail canary |
| Slippage increase | 0.2% | Fail canary |
| Trade count | 30 minimum | Extend testing |

### C. Safety Checklist

Before enabling AUTO_PROMOTE:

- [ ] Tested in paper trading for 2+ weeks
- [ ] Reviewed 10+ successful canary validations
- [ ] No escalations in last week
- [ ] Audit logs reviewed and understood
- [ ] Rollback procedure tested
- [ ] Monitoring dashboard configured
- [ ] Team trained on system operation

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-09  
**Next Review:** 2025-11-09

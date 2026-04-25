# AlphaAlgo Decision Verification System

## Overview

A comprehensive **fact-checking and hallucination prevention** system that verifies the bot's own outputs before execution. This ensures decision integrity and prevents errors caused by fabricated data, logical contradictions, or overconfident predictions.

**Location:** `trading_bot/verification/`  
**Total Modules:** 5  
**Total Lines:** ~3,500  

---

## Architecture

```
                    ┌─────────────────────────────────────┐
                    │     VERIFICATION ORCHESTRATOR       │
                    │   (Unified Verification Pipeline)   │
                    └─────────────────┬───────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌─────────────────┐           ┌─────────────────┐
│   DECISION    │           │     CROSS       │           │   ADVERSARIAL   │
│ VERIFICATION  │           │   VALIDATOR     │           │    CHECKER      │
│    CHAIN      │           │                 │           │                 │
│  (8 Stages)   │           │ (Multi-Source)  │           │ (Self-Question) │
└───────────────┘           └─────────────────┘           └─────────────────┘
        │                             │                             │
        └─────────────────────────────┼─────────────────────────────┘
                                      │
                                      ▼
                          ┌─────────────────────┐
                          │    CONFIDENCE       │
                          │    CALIBRATOR       │
                          │                     │
                          │ (Uncertainty Quant) │
                          └─────────────────────┘
```

---

## Modules

### 1. Decision Verification Chain (`decision_verification_chain.py`)

**8-stage verification pipeline:**

| Stage | Name | Purpose |
|-------|------|---------|
| 1 | **Data Grounding** | Verify claims against actual market data |
| 2 | **Logical Consistency** | Detect contradictions in reasoning |
| 3 | **Cross-Source** | Validate against multiple sources |
| 4 | **Historical Accuracy** | Compare with past prediction accuracy |
| 5 | **Adversarial Questioning** | Challenge conclusions |
| 6 | **Confidence Calibration** | Ensure calibrated confidence |
| 7 | **Reality Anchor** | Verify values are physically possible |
| 8 | **Audit Trail** | Create immutable verification records |

**Hallucination Types Detected:**
- `FABRICATED_DATA` - Prices/volumes that don't exist
- `INVENTED_PATTERN` - Patterns not present in data
- `FALSE_CORRELATION` - Correlations that don't exist
- `OVERCONFIDENT` - Confidence exceeding historical accuracy
- `LOGICAL_CONTRADICTION` - Mutually exclusive claims
- `TEMPORAL_IMPOSSIBILITY` - Future data in past analysis
- `MAGNITUDE_ERROR` - Values outside reasonable bounds
- `UNSUPPORTED_CLAIM` - Claims without evidence
- `CIRCULAR_REASONING` - Self-referential logic
- `CHERRY_PICKING` - Selective evidence

---

### 2. Cross-Validator (`cross_validator.py`)

Validates decisions against multiple independent sources.

**Source Types:**
- Technical Analysis (indicators, patterns)
- Sentiment Analysis (social, news)
- Fundamental Data (if available)
- Historical Patterns (backtested)
- Expert Systems (strategies)
- ML Models (predictions)

**Agreement Levels:**
- `UNANIMOUS` - 100% agree
- `STRONG` - 80%+ agree
- `MODERATE` - 60%+ agree
- `WEAK` - 40%+ agree
- `CONFLICTING` - <40% agree

---

### 3. Confidence Calibrator (`confidence_calibrator.py`)

Ensures confidence levels match historical accuracy.

**Calibration Methods:**
- **Platt Scaling** - Logistic regression calibration
- **Isotonic Regression** - Non-parametric calibration
- **Temperature Scaling** - Simple scalar calibration
- **Bayesian Calibration** - Prior-based adjustment
- **Historical Binning** - Bucket-based calibration

**Outputs:**
- Calibrated confidence value
- Uncertainty bounds (95% CI)
- Calibration status (well-calibrated, overconfident, underconfident)
- Recommendations

---

### 4. Adversarial Checker (`adversarial_checker.py`)

Challenges decisions using adversarial techniques.

**Techniques:**
| Technique | Description |
|-----------|-------------|
| **Devil's Advocate** | Argue against the decision |
| **Pre-Mortem** | Imagine failure, explain why |
| **Red Team** | Attack from all angles |
| **Assumption Challenge** | Question every assumption |
| **Contrarian** | What would a contrarian do? |
| **Black Swan** | What rare events could invalidate? |
| **Bias Detection** | Check for cognitive biases |

**Cognitive Biases Detected:**
- Confirmation Bias
- Recency Bias
- Anchoring
- Overconfidence
- Loss Aversion
- Gambler's Fallacy
- Availability Heuristic
- Herding

---

### 5. Verification Orchestrator (`verification_orchestrator.py`)

Unified entry point that coordinates all verification components.

**Final Verdicts:**
- `APPROVED` - Proceed with trade
- `APPROVED_WITH_MODIFICATIONS` - Proceed with adjustments
- `NEEDS_REVIEW` - Manual review recommended
- `REJECTED` - Do not execute
- `ESCALATE_TO_HUMAN` - Requires human decision

---

## Quick Start

### Basic Usage

```python
from trading_bot.verification import VerificationOrchestrator, FinalVerdict

# Create orchestrator
orchestrator = VerificationOrchestrator()

# Decision to verify
decision = {
    'symbol': 'BTCUSDT',
    'direction': 'BUY',
    'confidence': 0.85,
    'current_price': 45000.0,
    'stop_loss': 44000.0,
    'take_profit': 48000.0,
    'reasoning': 'Bullish pattern with volume confirmation',
}

# Market data for grounding
market_data = {
    'price': 45050.0,
    'volume': 1000000,
    'timestamp': '2026-01-28T12:00:00Z',
}

# Run verification
result = await orchestrator.verify(decision, market_data)

# Check verdict
if result.final_verdict == FinalVerdict.APPROVED:
    execute_trade(decision)
elif result.final_verdict == FinalVerdict.APPROVED_WITH_MODIFICATIONS:
    execute_trade(result.modified_decision)
elif result.final_verdict == FinalVerdict.REJECTED:
    log_rejection(result.critical_issues)
else:
    escalate_to_human(result)
```

### Using Individual Components

```python
from trading_bot.verification import (
    DecisionVerificationChain,
    CrossValidator,
    ConfidenceCalibrator,
    AdversarialChecker,
)

# 1. Verification Chain
chain = DecisionVerificationChain()
chain_result = await chain.verify_decision(decision, market_data)
print(f"Status: {chain_result.overall_status.value}")
print(f"Hallucinations: {len(chain_result.hallucinations_detected)}")

# 2. Cross-Validation
validator = CrossValidator()
cross_result = await validator.validate(decision, source_opinions)
print(f"Agreement: {cross_result.source_agreement.agreement_level.value}")

# 3. Confidence Calibration
calibrator = ConfidenceCalibrator()
calibrator.record_outcome(0.8, was_correct=True)  # Record outcomes
cal_result = calibrator.calibrate(0.85)
print(f"Calibrated: {cal_result.calibrated_confidence:.1%}")

# 4. Adversarial Analysis
checker = AdversarialChecker()
adv_result = checker.analyze(decision)
print(f"Robustness: {adv_result.overall_robustness:.1%}")
print(f"Should Proceed: {adv_result.should_proceed}")
```

---

## Integration with Trading Loop

```python
async def execute_with_verification(signal, market_data):
    """Execute trade only after verification passes"""
    
    # Create decision from signal
    decision = {
        'symbol': signal.symbol,
        'direction': signal.direction,
        'confidence': signal.confidence,
        'current_price': market_data['price'],
        'stop_loss': signal.stop_loss,
        'take_profit': signal.take_profit,
        'reasoning': signal.reasoning,
    }
    
    # Verify decision
    orchestrator = VerificationOrchestrator()
    result = await orchestrator.verify(decision, market_data)
    
    # Log verification
    logger.info(f"Verification: {result.final_verdict.value}")
    logger.info(f"Confidence: {result.final_confidence:.1%}")
    
    # Act based on verdict
    if result.final_verdict in [FinalVerdict.APPROVED, FinalVerdict.APPROVED_WITH_MODIFICATIONS]:
        # Use modified decision if available
        final_decision = result.modified_decision or decision
        
        # Execute trade
        order = await broker.place_order(
            symbol=final_decision['symbol'],
            direction=final_decision['direction'],
            stop_loss=final_decision['stop_loss'],
            take_profit=final_decision['take_profit'],
        )
        
        return order
    
    elif result.final_verdict == FinalVerdict.REJECTED:
        logger.warning(f"Trade rejected: {result.critical_issues}")
        return None
    
    else:
        # Escalate or defer
        await notify_human(result)
        return None
```

---

## Configuration

```python
config = {
    'chain': {
        'min_confidence_threshold': 0.7,
        'hallucination_severity_threshold': 0.5,
        'min_sources_for_verification': 2,
    },
    'cross_validator': {
        'min_sources': 3,
        'min_agreement_ratio': 0.6,
        'strong_agreement_ratio': 0.8,
    },
    'calibrator': {
        'min_samples': 30,
        'bucket_size': 0.1,
        'prior_strength': 0.3,
    },
    'adversarial': {
        'min_robustness': 0.6,
        'max_critical_challenges': 1,
    },
    'min_confidence_for_approval': 0.7,
    'max_hallucinations_for_approval': 0,
    'min_robustness_for_approval': 0.6,
}

orchestrator = VerificationOrchestrator(config)
```

---

## Demo

Run the demo to see all components in action:

```bash
python examples/verification_chain_demo.py
```

---

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| `decision_verification_chain.py` | ~1,350 | 8-stage verification chain |
| `cross_validator.py` | ~500 | Multi-source validation |
| `confidence_calibrator.py` | ~450 | Confidence calibration |
| `adversarial_checker.py` | ~550 | Adversarial self-questioning |
| `verification_orchestrator.py` | ~400 | Unified orchestrator |
| `__init__.py` | ~140 | Package exports |
| `examples/verification_chain_demo.py` | ~400 | Demo script |

**Total:** ~3,800 lines

---

## Key Principles

1. **Trust but Verify** - Every decision is verified before execution
2. **Multiple Perspectives** - Cross-validate against independent sources
3. **Historical Grounding** - Calibrate confidence to match past accuracy
4. **Adversarial Thinking** - Challenge every conclusion
5. **Audit Trail** - Immutable records for all verifications
6. **Fail-Safe** - Default to rejection when uncertain

---

## Version

- **Version:** 1.0
- **Date:** 2026-01-28
- **Author:** AlphaAlgo Team

# ALPHAALGO QUICK REFERENCE CARD

**Version**: 1.0.0  
**Date**: October 19, 2025  
**Status**: Production-Ready  

---

## QUICK START (3 COMMANDS)

```bash
# 1. Run demo to see system in action
py DEMO_COGNITIVE_CORE.py --quick

# 2. Test with paper trading
py main.py --symbol EURUSD --mode paper --adaptive-integration

# 3. Activate full system
RUN_ADAPTIVE_INTEGRATION.bat
```

---

## PYTHON USAGE (1 MINUTE)

```python
from trading_bot.cognitive_architecture import AlphaAlgoCognitiveCore

# Initialize
core = AlphaAlgoCognitiveCore()

# Make decision
decision = core.make_decision(market_data)

# Use result
if decision.confidence >= 0.6:
    execute_trade(
        action=decision.action,
        size=decision.position_size,
        stop_loss=decision.stop_loss,
        take_profit=decision.take_profit
    )
```

---

## 10 LAYERS AT A GLANCE

1. **Market State** - Detects regime (6 types)
2. **Integration** - Selects mode (6 options)
3. **Multi-Agent** - Coordinates 5 agents
4. **Neuro-Symbolic** - Neural + Logic
5. **Advanced RL** - CQL/IQL/BCQ learning
6. **Multi-Modal** - Fuses 5 data types
7. **Self-Healing** - Auto-repair + optimize
8. **Quantum** - Enhanced forecasting
9. **Explainability** - Natural language
10. **Evolution** - Continuous improvement

---

## KEY FILES

| File | Purpose |
|------|---------|
| `DEMO_COGNITIVE_CORE.py` | Demo all features |
| `RUN_ADAPTIVE_INTEGRATION.bat` | Quick launcher |
| `ALPHAALGO_COMPLETE_SYSTEM_SUMMARY.md` | Full documentation |
| `trading_bot/cognitive_architecture/cognitive_core.py` | Main system |

---

## DECISION OUTPUT

```python
decision.action           # BUY/SELL/HOLD
decision.confidence       # 0.0-1.0
decision.position_size    # Calculated size
decision.stop_loss        # Stop loss price
decision.take_profit      # Take profit price
decision.reasoning        # Full explanation
decision.cognitive_state  # Complete state
```

---

## SAFETY THRESHOLDS

- **Min Confidence**: 0.6 (60%)
- **Max Position**: 2% of capital
- **System Health**: Must be >90%
- **Auto-Rollback**: If performance drops >5%

---

## SUPPORT

- **Full Docs**: `ALPHAALGO_COMPLETE_SYSTEM_SUMMARY.md`
- **Architecture**: `ALPHAALGO_10_LAYER_ARCHITECTURE.md`
- **Validation**: `ALPHAALGO_FINAL_REPORT.md`
- **Diagnostics**: `ALPHAALGO_ADAPTIVE_INTEGRATION_DIAGNOSTIC.py`

---

**Status**: READY  
**Action**: RUN DEMO

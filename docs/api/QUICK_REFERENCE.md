# 🤖 Thinking Bot - Quick Reference Card

## 🚀 Quick Start (3 Steps)

```bash
# 1. Validate
python validate_thinking_bot.py

# 2. Configure (optional)
# Edit config/config.yaml

# 3. Run
python thinking_bot.py
# or
RUN_THINKING_BOT.bat
```

## 📊 Trading Loop (Every 60 Seconds)

```
┌─────────────────────────────────────────┐
│  1. ANALYZE → 2. VALIDATE → 3. EXECUTE │
│            ↓                            │
│  6. LEARN ← 5. UPDATE ← 4. MONITOR     │
└─────────────────────────────────────────┘
```

## 🎯 Signal Generation (BUY Example)

**Minimum 5 points required:**

| Factor | Points | Condition |
|--------|--------|-----------|
| Trend | 2 | Bullish across timeframes |
| RSI | 1-2 | < 50 (1pt) or < 30 (2pts) |
| MACD | 2 | Bullish crossover |
| EMA | 1 | Price > EMA20 > EMA50 |
| Momentum | 1 | Positive > 1% |

**Example:** Trend(2) + RSI(1) + MACD(2) + EMA(1) = **6 points** → STRONG BUY

## ⚖️ Risk Rules (The Guardian)

| Rule | Limit | Action |
|------|-------|--------|
| Position Size | 0.01 - 1.0 lot | Cap/reject |
| Risk per Trade | 1-2% balance | Adjust lots |
| Total Exposure | ≤ 10% equity | Reject |
| Max Positions | 5 | Reject |
| Balance | ≥ $100 | Reject |
| Margin | Sufficient | Reject |

**Formula:**
```
Lot Size = Risk Amount / (Stop Loss Pips × Pip Value)
Risk Amount = Balance × Risk %
```

## 🚀 Execution Modes

### Paper Trading (Safe)
```yaml
trading:
  mode: "paper"
```
- Simulates execution
- No real money
- Perfect for testing

### Live Trading (Real)
```yaml
trading:
  mode: "live"
```
- Real orders to MT5
- Real money at risk
- Use with caution

## 📈 Key Metrics

| Metric | Good | Excellent |
|--------|------|-----------|
| Win Rate | 50-60% | 60-70%+ |
| Profit Factor | 1.5-2.0 | 2.0-3.0+ |
| Max Drawdown | <15% | <10% |
| Risk/Reward | 1:2 | 1:3+ |

## 🔧 Configuration Quick Edit

```yaml
# config/config.yaml

# Symbols to trade
mt5:
  symbols: [EURUSD, GBPUSD, USDJPY]

# Risk settings
trading:
  risk_per_trade: 0.01  # 1%
  max_positions: 5
  
risk:
  max_position_size: 1.0
  min_position_size: 0.01
```

## 📊 Indicator Cheat Sheet

| Indicator | Bullish | Bearish |
|-----------|---------|---------|
| RSI | < 30 (oversold) | > 70 (overbought) |
| MACD | > Signal line | < Signal line |
| EMA | Price > EMA20 > EMA50 | Price < EMA20 < EMA50 |
| Trend | Multiple TF bullish | Multiple TF bearish |
| Momentum | > +1% | < -1% |

## 🎛️ Command Reference

```bash
# Validate system
python validate_thinking_bot.py

# Run bot
python thinking_bot.py

# Run tests
pytest tests/test_thinking_bot.py -v

# Check logs
tail -f logs/thinking_bot_*.log  # Linux/Mac
type logs\thinking_bot_*.log     # Windows
```

## 🐛 Troubleshooting Quick Fix

| Problem | Solution |
|---------|----------|
| Bot won't start | Run `validate_thinking_bot.py` |
| No signals | Check market conditions, review logs |
| Trades rejected | Check risk limits, balance, margin |
| MT5 error | Restart MT5, check login |
| Import error | `pip install -r requirements.txt` |

## 📁 Important Files

| File | Purpose |
|------|---------|
| `thinking_bot.py` | Main bot code |
| `config/config.yaml` | Configuration |
| `logs/thinking_bot_*.log` | Runtime logs |
| `THINKING_BOT_GUIDE.md` | Full documentation |
| `validate_thinking_bot.py` | Pre-flight checks |

## 🔔 Signal Example

```
✓ Analysis complete: EURUSD - BULLISH trend, RSI=45.2, MACD=0.00012
✓ Signal generated: BUY EURUSD @ 1.09500, SL=1.09300, TP=1.09950, Confidence=0.75
✓ Signal validated: EURUSD, Approved lots=0.10, Risk=1.00%
✓ Trade executed: Ticket=123456, Price=1.09500, Slippage=0.00001
```

## 📊 Performance Report Example

```
================================================================================
PERFORMANCE SUMMARY
================================================================================
Total Trades: 50        Win Rate: 70.00%
Winning: 35             Profit Factor: 2.33
Losing: 15              Net P&L: $1000.00
================================================================================
```

## ⚡ Hot Keys

| Action | Command |
|--------|---------|
| Stop bot | `Ctrl+C` |
| View logs | Check `logs/` folder |
| Edit config | Open `config/config.yaml` |
| Validate | `python validate_thinking_bot.py` |

## 🎯 Best Practices

1. ✅ **Always start with paper trading**
2. ✅ **Validate before running** (`validate_thinking_bot.py`)
3. ✅ **Monitor logs regularly**
4. ✅ **Start with conservative risk** (0.5-1%)
5. ✅ **Test on demo account first**
6. ✅ **Review performance weekly**
7. ✅ **Keep MT5 running and logged in**
8. ✅ **Ensure stable internet connection**

## 🔒 Safety Checklist

- [ ] Paper trading mode enabled
- [ ] Risk per trade ≤ 1%
- [ ] Max position size ≤ 1.0 lot
- [ ] Max positions ≤ 5
- [ ] Stop-loss always set
- [ ] Take-profit always set
- [ ] Sufficient balance
- [ ] MT5 connected
- [ ] Logs being written
- [ ] Validation passed

## 📞 Emergency Actions

**If something goes wrong:**

1. **Stop the bot:** Press `Ctrl+C`
2. **Close positions manually:** Use MT5 interface
3. **Check logs:** Review `logs/thinking_bot_*.log`
4. **Run validation:** `python validate_thinking_bot.py`
5. **Fix issues:** Address errors found
6. **Restart:** Run bot again

## 🎓 Learning Path

1. **Read:** `THINKING_BOT_GUIDE.md`
2. **Validate:** `python validate_thinking_bot.py`
3. **Test:** Run in paper mode for 1 week
4. **Analyze:** Review performance metrics
5. **Optimize:** Adjust config if needed
6. **Deploy:** Switch to live (with caution)

## 📚 Documentation Index

- **Complete Guide:** `THINKING_BOT_GUIDE.md`
- **Implementation:** `THINKING_BOT_COMPLETE.md`
- **Quick Reference:** `QUICK_REFERENCE.md` (this file)
- **Code:** `thinking_bot.py`
- **Tests:** `tests/test_thinking_bot.py`
- **Validation:** `validate_thinking_bot.py`

---

## 🚀 Ready to Trade?

```bash
python thinking_bot.py
```

**Remember:** Start with paper trading! 📝

---

**Quick Help:** See `THINKING_BOT_GUIDE.md` for detailed documentation.

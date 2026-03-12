# 🚀 AlphaAlgo Internet System - Quick Start Guide

## ⚡ 3-Minute Setup

### Step 1: Install Dependencies (30 seconds)

```bash
pip install -r requirements_internet.txt
```

### Step 2: Configure API Keys (1 minute)

```bash
# Copy the example file
cp config/api_keys.json.example config/api_keys.json
```

Edit `config/api_keys.json`:
```json
{
  "market_data": "YOUR_MARKET_DATA_API_KEY",
  "news": "YOUR_NEWS_API_KEY",
  "sentiment": "YOUR_SENTIMENT_API_KEY",
  "macro": "YOUR_MACRO_API_KEY"
}
```

**Don't have API keys yet?** The system will use mock data for testing.

### Step 3: Run the System (30 seconds)

**Option A - Autonomous Mode (recommended)**
```bash
```

**Option B - Demo Mode (for testing)**
```bash
python examples/alphaalgo_internet_demo.py
```

---

## 🎮 Demo Options

When running the demo, you'll see:

```
1. Single Trading Cycle (quick demo)
2. Autonomous Operation (5 minutes)
3. Phase-by-Phase Walkthrough (educational)
4. Run All Demos
```

**Recommended**: Start with option 3 to understand each phase.

---

## 📊 What You'll See

### Connection Validation
```
🌐 PHASE 1: Connection Validation
✅ broker_feed     : healthy    (latency: 45.2ms)
✅ economic_api    : healthy    (latency: 120.5ms)
✅ sentiment_api   : healthy    (latency: 95.8ms)
✅ model_repo      : healthy    (latency: 150.0ms)
```

### Data Acquisition
```
📊 PHASE 2: Data Acquisition
✓ Market data: 6 timeframes
✓ News: 50 articles
✓ Sentiment: 3 symbols
✓ Macro: 5 indicators
```

### Trading Decision
```
📋 TRADING DECISION
Symbol:     EURUSD
Action:     BUY
Confidence: 78.50%
Strength:   +1.25
Risk Score: 21.50%
```

---

## 🔧 Configuration (Optional)

Edit `config/internet_config.yaml` to customize:

```yaml
# Trading symbols
symbols:
  - EURUSD
  - GBPUSD
  - USDJPY

# Trading interval
trading_interval_minutes: 5

# Fusion weights (must sum to 1.0)
fusion:
  fusion_weights:
    technical: 0.60    # 60% technical analysis
    sentiment: 0.25    # 25% sentiment
    news: 0.10         # 10% news
    volatility: 0.05   # 5% volatility filter
  min_confidence: 0.60 # Minimum confidence to trade
```

---

## 📁 Where to Find Things

| What | Where |
|------|-------|
| Logs | `alphaalgo_internet.log` |
| Status | `alphaalgo_final_status.json` |
| Update Log | `update_report.log` |
| Security Log | `secure/security_audit.log` |
| Data Cache | `data_cache/` |
| Models | `models/` |
| Dashboard | `dashboard_data.json` |

---

## 🆘 Troubleshooting

### "Trading disabled due to connection failures"
**Fix**: Check your internet connection and endpoint URLs in `config/internet_config.yaml`

### "API authentication failed"
**Fix**: Verify your API keys in `config/api_keys.json`

### "Module not found"
**Fix**: Run `pip install -r requirements_internet.txt`

---

## 📚 Next Steps

1. ✅ Run the demo to understand the system
2. ✅ Configure your real API keys
3. ✅ Adjust fusion weights if needed
4. ✅ Test with paper trading
5. ✅ Monitor performance for 1-2 weeks
6. ✅ Go live with small positions

---

## 📖 Full Documentation

- **Complete Guide**: `ALPHAALGO_INTERNET_GUIDE.md`
- **Implementation Details**: `ALPHAALGO_INTERNET_COMPLETE.md`
- **Executive Summary**: `INTERNET_SYSTEM_SUMMARY.md`

---

## ✅ You're Ready!

The system is now configured and ready to run. Start with the demo to see it in action!

```bash
python examples/alphaalgo_internet_demo.py
```

**Happy Trading! 🚀**

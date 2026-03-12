# ⏰ Bot Timeframes - Complete Analysis

## 📊 Current Timeframe Configuration

---

## 🤖 Demo Trading Bot

### **Data Timeframe:**
```
Timeframe: TICK-BY-TICK (Simulated)
Update Frequency: Every 15 seconds
Data Source: Random price generation
```

### **Analysis Cycle:**
```python
await asyncio.sleep(15)  # Check every 15 seconds
```

**What this means:**
- Bot analyzes markets **every 15 seconds**
- Generates new price data each cycle
- Fast-paced for demonstration purposes
- Not based on candle timeframes (uses tick data)

### **Indicator Calculation:**
```
RSI: Calculated from simulated price movements
MACD: Calculated from simulated EMAs
SMA(20): 20-period simple moving average
SMA(50): 50-period simple moving average
```

**Note:** Since data is simulated tick-by-tick, the "periods" are based on the number of price updates, not traditional candles.

---

## 📡 Real Data Trading Bot

### **Data Timeframe:**
```
Timeframe: 1-MINUTE CANDLES
Period: 1 Day (Last 24 hours)
Update Frequency: Every 60 seconds
Data Source: Yahoo Finance
```

### **Code Configuration:**
```python
# Line 134 in real_data_trading_bot.py
data = yf.download(ticker, period='1d', interval='1m', progress=False)
```

**Breakdown:**
- `period='1d'` = Fetches **1 day** of historical data
- `interval='1m'` = Uses **1-minute candles**
- Updates every **60 seconds**

### **Analysis Cycle:**
```python
await asyncio.sleep(60)  # Check every 60 seconds
```

**What this means:**
- Bot fetches fresh data **every 60 seconds**
- Analyzes **1-minute candles**
- Calculates indicators from **up to 390 candles** (1 trading day)
- Real market data, real timeframes

### **Indicator Calculation:**
```
RSI(14): Based on last 14 one-minute candles
MACD: Based on EMA(12) and EMA(26) of 1-min candles
SMA(20): Average of last 20 one-minute candles
SMA(50): Average of last 50 one-minute candles
```

---

## 📈 Timeframe Breakdown

### **Demo Bot Timeline:**
```
00:00 - Cycle 1: Analyze, signal, trade
00:15 - Cycle 2: Analyze, signal, trade
00:30 - Cycle 3: Analyze, signal, trade
00:45 - Cycle 4: Analyze, signal, trade
01:00 - Cycle 5: Display statistics
...continues every 15 seconds
```

**Trades per hour:** Up to 240 analysis cycles (4 per minute)

### **Real Data Bot Timeline:**
```
00:00 - Cycle 1: Fetch 1-min data, analyze, signal, trade
01:00 - Cycle 2: Fetch 1-min data, analyze, signal, trade
02:00 - Cycle 3: Fetch 1-min data, analyze, signal, trade
03:00 - Cycle 4: Fetch 1-min data, analyze, signal, trade
04:00 - Cycle 5: Display statistics
...continues every 60 seconds
```

**Trades per hour:** Up to 60 analysis cycles (1 per minute)

---

## 🎯 Position Monitoring Timeframes

### **Demo Bot Monitoring:**
```
Frequency: Every 15 seconds
Method: Real-time tick monitoring
Check: Price vs TP/SL on every cycle
```

**Example:**
```
00:00 - Trade opened at 1.0850
00:15 - Check: Price 1.0852 (still open)
00:30 - Check: Price 1.0855 (still open)
00:45 - Check: Price 1.0865 (still open)
01:00 - Check: Price 1.0900 (TP hit! Close trade)
```

### **Real Data Bot Monitoring:**
```
Frequency: Every 60 seconds
Method: 1-minute candle close monitoring
Check: Price vs TP/SL on every cycle
```

**Example:**
```
10:00 - Trade opened at 1.0850
10:01 - Check: Price 1.0852 (still open)
10:02 - Check: Price 1.0855 (still open)
10:03 - Check: Price 1.0865 (still open)
10:04 - Check: Price 1.0900 (TP hit! Close trade)
```

---

## 📊 Indicator Timeframe Details

### **RSI (Relative Strength Index)**

**Demo Bot:**
```
Period: 14 (last 14 price updates)
Timeframe: ~3.5 minutes of data (14 × 15 seconds)
Calculation: Based on simulated price changes
```

**Real Data Bot:**
```
Period: 14 (last 14 one-minute candles)
Timeframe: 14 minutes of real market data
Calculation: Based on actual price movements
```

### **MACD (Moving Average Convergence Divergence)**

**Demo Bot:**
```
Fast EMA: 12 periods (~3 minutes)
Slow EMA: 26 periods (~6.5 minutes)
Timeframe: Simulated tick data
```

**Real Data Bot:**
```
Fast EMA: 12 periods (12 minutes)
Slow EMA: 26 periods (26 minutes)
Timeframe: 1-minute candles
```

### **SMA (Simple Moving Averages)**

**Demo Bot:**
```
SMA(20): Last 20 price updates (~5 minutes)
SMA(50): Last 50 price updates (~12.5 minutes)
Timeframe: Simulated data
```

**Real Data Bot:**
```
SMA(20): Last 20 one-minute candles (20 minutes)
SMA(50): Last 50 one-minute candles (50 minutes)
Timeframe: Real 1-minute candles
```

---

## 🔄 Data Refresh Rates

### **Demo Bot:**
```
Price Updates: Every 15 seconds (new simulated price)
Indicator Recalculation: Every 15 seconds
Signal Generation: Every 15 seconds
Position Monitoring: Every 15 seconds
Statistics Display: Every 75 seconds (5 cycles)
```

### **Real Data Bot:**
```
Price Updates: Every 60 seconds (new 1-min candle)
Indicator Recalculation: Every 60 seconds
Signal Generation: Every 60 seconds
Position Monitoring: Every 60 seconds
Statistics Display: Every 300 seconds (5 cycles)
```

---

## 📅 Trading Session Coverage

### **Demo Bot:**
```
Trading Hours: 24/7 (continuous)
Market: Simulated (always open)
Weekends: Trades on weekends (simulated)
Holidays: Trades on holidays (simulated)
```

### **Real Data Bot:**
```
Trading Hours: Forex market hours (24/5)
Market: Real forex markets
Weekends: No data (markets closed)
Holidays: Limited data (depends on market)
Data Availability: Monday 00:00 - Friday 23:59 GMT
```

---

## 🎯 Timeframe Comparison

| Feature | Demo Bot | Real Data Bot |
|---------|----------|---------------|
| **Primary Timeframe** | Tick (15s) | 1-minute candles |
| **Update Frequency** | 15 seconds | 60 seconds |
| **Historical Data** | Simulated | 1 day (390 candles) |
| **RSI Period** | 14 ticks (~3.5 min) | 14 candles (14 min) |
| **SMA(20)** | 20 ticks (~5 min) | 20 candles (20 min) |
| **SMA(50)** | 50 ticks (~12.5 min) | 50 candles (50 min) |
| **MACD Fast** | 12 ticks (~3 min) | 12 candles (12 min) |
| **MACD Slow** | 26 ticks (~6.5 min) | 26 candles (26 min) |
| **Monitoring** | Every 15s | Every 60s |
| **Trading Style** | Scalping | Intraday |

---

## 🚀 How to Change Timeframes

### **Option 1: Change Real Data Bot to 5-Minute Candles**

**Current:**
```python
data = yf.download(ticker, period='1d', interval='1m', progress=False)
```

**Modified:**
```python
data = yf.download(ticker, period='5d', interval='5m', progress=False)
```

**Effect:**
- Uses 5-minute candles instead of 1-minute
- RSI(14) = 70 minutes of data (14 × 5 min)
- SMA(50) = 250 minutes of data (50 × 5 min)
- Less frequent signals, more stable

### **Option 2: Change to 15-Minute Candles**

```python
data = yf.download(ticker, period='5d', interval='15m', progress=False)
```

**Effect:**
- Uses 15-minute candles
- RSI(14) = 3.5 hours of data
- SMA(50) = 12.5 hours of data
- Swing trading style

### **Option 3: Change to 1-Hour Candles**

```python
data = yf.download(ticker, period='30d', interval='1h', progress=False)
```

**Effect:**
- Uses 1-hour candles
- RSI(14) = 14 hours of data
- SMA(50) = 50 hours of data
- Position trading style

### **Option 4: Change Demo Bot Speed**

**Current:**
```python
await asyncio.sleep(15)  # Every 15 seconds
```

**Slower:**
```python
await asyncio.sleep(60)  # Every 60 seconds
```

**Faster:**
```python
await asyncio.sleep(5)  # Every 5 seconds
```

---

## 📊 Available Yahoo Finance Timeframes

### **Valid Intervals:**
```
1m  = 1 minute
2m  = 2 minutes
5m  = 5 minutes
15m = 15 minutes
30m = 30 minutes
60m = 60 minutes (1 hour)
90m = 90 minutes
1h  = 1 hour
1d  = 1 day
5d  = 5 days
1wk = 1 week
1mo = 1 month
3mo = 3 months
```

### **Valid Periods:**
```
1d   = 1 day
5d   = 5 days
1mo  = 1 month
3mo  = 3 months
6mo  = 6 months
1y   = 1 year
2y   = 2 years
5y   = 5 years
10y  = 10 years
ytd  = Year to date
max  = All available data
```

### **Restrictions:**
- `1m` interval: Max 7 days period
- `2m` interval: Max 60 days period
- `5m` interval: Max 60 days period
- `15m` interval: Max 60 days period
- `1h` interval: Max 730 days period

---

## 🎯 Recommended Timeframes by Trading Style

### **Scalping (Very Short-Term):**
```
Timeframe: 1-minute candles
Update: Every 30-60 seconds
Indicators: RSI(14), MACD(12,26,9)
Holding Time: Minutes to hours
Bot: Demo Bot (fast cycles)
```

### **Day Trading (Short-Term):**
```
Timeframe: 5-minute or 15-minute candles
Update: Every 1-5 minutes
Indicators: RSI(14), SMA(20,50), MACD
Holding Time: Hours to 1 day
Bot: Real Data Bot (current setup)
```

### **Swing Trading (Medium-Term):**
```
Timeframe: 1-hour or 4-hour candles
Update: Every 15-60 minutes
Indicators: RSI(14), SMA(50,200), MACD
Holding Time: Days to weeks
Bot: Real Data Bot (modified)
```

### **Position Trading (Long-Term):**
```
Timeframe: Daily candles
Update: Once per day
Indicators: SMA(50,200), Weekly trends
Holding Time: Weeks to months
Bot: Real Data Bot (heavily modified)
```

---

## ✅ Current Bot Configuration Summary

### **Demo Bot:**
- **Timeframe:** Tick-by-tick (simulated)
- **Update:** Every 15 seconds
- **Style:** Ultra-fast scalping (demo purposes)
- **Indicators:** Based on last ~50 ticks
- **Best For:** Testing logic, seeing activity

### **Real Data Bot:**
- **Timeframe:** 1-minute candles
- **Update:** Every 60 seconds
- **Style:** Scalping to day trading
- **Indicators:** Based on last 50-390 minutes
- **Best For:** Real trading, intraday strategies

---

## 🔧 How to Optimize Timeframes

### **For More Trades:**
- Use shorter timeframes (1m, 5m)
- Faster update cycles
- Lower indicator periods

### **For Better Quality:**
- Use longer timeframes (15m, 1h)
- Slower update cycles
- Higher indicator periods

### **For Real Trading:**
- Start with 5m or 15m candles
- Update every 1-5 minutes
- Use standard indicator periods (14, 20, 50)

---

## 📝 Summary

**Your bots currently use:**

1. **Demo Bot:** Tick data (15-second updates) - Fast demo trading
2. **Real Data Bot:** 1-minute candles (60-second updates) - Real scalping

**Monitoring:** Both bots check positions on every cycle
- Demo: Every 15 seconds
- Real: Every 60 seconds

**Indicators calculated from:**
- Demo: Last 50 simulated ticks (~12.5 minutes)
- Real: Last 50 one-minute candles (50 minutes)

**To change timeframes:** Modify the `interval` parameter in `yf.download()` and adjust the `asyncio.sleep()` duration.

---

**Your bots are optimized for SHORT-TERM trading with FREQUENT monitoring!** ⏰

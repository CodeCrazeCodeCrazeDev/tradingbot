# 🤖 AlphaAlgo Autonomous Operator Guide

## Overview

The **Autonomous Operator** is a fully automated system that runs, validates, monitors, and maintains your AlphaAlgo trading bot without manual intervention.

---

## 🚀 Quick Start

### Start the Operator

```bash
py autonomous_operator.py
```

That's it! The operator will:
- ✅ Validate all prerequisites
- ✅ Auto-install missing dependencies
- ✅ Start the trading bot
- ✅ Monitor continuously
- ✅ Auto-recover from errors
- ✅ Save logs and backups

---

## 📋 What It Does

### Phase 1: Pre-Run Validation

The operator performs comprehensive checks before starting:

#### 1️⃣ Python Environment
- ✅ Checks Python is installed and accessible
- ✅ Verifies Python 3.8+ is available
- ❌ Logs error if Python not found

#### 2️⃣ Dependencies
- ✅ Checks all required packages:
  - yfinance, ta, vaderSentiment, fredapi
  - tensorflow, stable-baselines3, shap, gym
  - aiohttp, psutil, pyyaml, numpy, pandas, scikit-learn
- ✅ **Auto-installs** missing packages
- ✅ Uses requirements.txt or requirements_internet.txt

#### 3️⃣ Configuration Files
- ✅ Validates `config/alphaalgo_config.yaml`
- ✅ Checks for API keys in `api_keys.env`
- ✅ Verifies essential config sections

#### 4️⃣ System Health
- ✅ CPU usage < 90%
- ✅ Available memory > 500MB
- ✅ Disk space check
- ⚠️ Enters Safe Mode if unhealthy

#### 5️⃣ Model Files
- ✅ Checks for ML models in `/models`
- ⚠️ Uses fallback strategy if missing

#### 6️⃣ Network Stability
- ✅ Measures ping latency
- ✅ Checks packet loss
- ✅ Starts network monitor
- ⚠️ Enters Safe Mode if unstable (>150ms)

---

### Phase 2: Bot Execution

Once validation passes, the operator starts the bot:

#### Core Modules Loaded:
1. **Data Collector** - Market data acquisition
2. **Signal Generator** - Trading signals
3. **Risk Manager** - Position sizing and risk control
4. **Trade Executor** - Order execution
5. **Monitor** - System health monitoring

#### Broker Connection:
- ✅ Validates broker API connection
- ✅ Falls back to paper trading if unavailable

#### Trading Loop:
- ✅ Starts continuous trading loop
- ✅ Logs: "INFO – Trading loop started successfully."

---

### Phase 3: Continuous Monitoring

The operator monitors the bot in real-time:

#### Real-Time Checks (Every 10 seconds):
- 🌐 **Network Stability** - Latency and packet loss
- 🔌 **Broker Connection** - API heartbeat
- 💻 **System Resources** - CPU, memory, disk
- 📊 **Trade Limits** - Max positions, position size
- 🔍 **API Responses** - Response times and errors

#### Status Display (Every 30 seconds):
```
==================================================
✅ AlphaAlgo Running Successfully
==================================================
Mode: Paper Trading
Network: Stable
Active Modules: 5 loaded
Last Ping: 45ms
Current Timeframe: 5min-1h
Trades Executed: 12
Uptime: 1:23:45
CPU: 15.2% | Memory: 42.3%
==================================================
```

#### Auto-Recovery:
If errors occur:
1. 🔍 **Detect Issue** - Identify what's broken
2. 🔧 **Attempt Fix** - Restart affected module
3. ⏱️ **Wait & Retry** - Give time to stabilize
4. ✅ **Resume** - Continue if fixed
5. ⚠️ **Safe Mode** - Pause trading if unrecoverable

#### Safe Mode Triggers:
- ⚠️ Network unstable (latency >150ms)
- ⚠️ High CPU usage (>90%)
- ⚠️ Low memory (<500MB)
- ⚠️ Broker connection lost
- ⚠️ Critical module failure

**In Safe Mode:**
- ⛔ New trades blocked
- ✅ Existing positions monitored
- 🔔 Alert sent: "⚠️ AlphaAlgo paused due to unstable environment."
- ⏳ Waits for conditions to improve
- ✅ Auto-resumes when stable

---

### Phase 4: Post-Run Operations

When the bot stops (gracefully or emergency):

#### Automatic Actions:
1. 💾 **Save Logs** - All trading logs preserved
2. 📊 **Save Metrics** - Session performance summary
   - Session start/end time
   - Trades executed
   - Restart count
   - Component status
3. 🗄️ **Backup Trade History** - To `/backup/trades_{timestamp}.json`
4. 🛑 **Graceful Shutdown** - Stop all modules cleanly

---

## 🔁 Auto-Restart & Continuous Mode

### Automatic Restart:
If the bot crashes unexpectedly:
1. ⏱️ Wait 30 seconds
2. ♻️ Auto-restart core script
3. 📝 Log: "♻️ Auto-restarted AlphaAlgo after failure."
4. 🔢 Track restart count (max 10 restarts)

### Continuous Operation:
- ✅ Runs indefinitely until stopped
- ✅ Self-heals from transient errors
- ✅ Adapts to changing conditions
- ✅ Maintains logs and backups

---

## 🕒 Timeframe Analysis

The bot analyzes multiple timeframes simultaneously:

### Supported Timeframes:
- **1 min** - Ultra-short term signals
- **5 min** - Short-term entry signals
- **15 min** - Intraday trends
- **1 hour** - Medium-term trends
- **4 hour** - Swing trading
- **1 day** - Long-term trends
- **1 week** - Major trend confirmation

### Intelligent Selection:
- ✅ Lower timeframes for entry signals
- ✅ Higher timeframes for trend confirmation
- ✅ Auto-selects best combination based on volatility
- ✅ Adapts to market conditions

---

## 📊 Monitoring & Logs

### Log Files:

#### 1. Autonomous Operator Log
```
logs/autonomous_operator.log
```
Contains:
- Validation results
- Module status
- Real-time checks
- Error messages
- Recovery attempts

#### 2. Network Monitor Log
```
logs/network_monitor.log
```
Contains:
- Latency measurements
- Packet loss data
- Mode transitions
- Network alerts

#### 3. Session Metrics
```
logs/session_metrics_YYYYMMDD_HHMMSS.json
```
Contains:
- Session duration
- Trades executed
- Component status
- Restart count

#### 4. Trade History Backup
```
backup/trades_YYYYMMDD_HHMMSS.json
```
Contains:
- All executed trades
- Entry/exit prices
- P/L data
- Timestamps

---

## 🎛️ Control Commands

### Start Operator
```bash
py autonomous_operator.py
```

### Stop Operator
Press `Ctrl+C` for graceful shutdown

### View Real-Time Logs
```bash
# Windows
type logs\autonomous_operator.log

# Or tail equivalent
Get-Content logs\autonomous_operator.log -Wait -Tail 50
```

### Check Status
The operator displays status every 30 seconds automatically.

---

## 🔧 Configuration

### Main Config File
`config/alphaalgo_config.yaml`

Key sections:
- `trading` - Trading parameters
- `risk` - Risk management settings
- `network` - Network monitoring config
- `monitoring` - Alert settings

### API Keys (Optional)
`api_keys.env`

Example:
```env
FRED_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
ALPHA_VANTAGE_KEY=your_key_here
```

---

## 🚨 Alerts & Notifications

### Alert Triggers:
- ⚠️ Network unstable
- ⚠️ Broker connection lost
- ⚠️ High CPU/memory usage
- ⚠️ Safe Mode activated
- ⚠️ Critical error occurred
- ⚠️ Auto-restart triggered

### Alert Message Example:
```
⚠️ ALERT: AlphaAlgo paused due to unstable environment.

Reason: Network latency exceeded 300ms
Status: Safe Mode Active
Time: 2025-10-09 18:00:00

Action: Monitoring network stability...
Will resume when latency < 100ms for 60 seconds.
```

---

## 📈 Performance Metrics

### Tracked Metrics:
- ✅ Uptime
- ✅ Trades executed
- ✅ Win rate
- ✅ P/L
- ✅ Drawdown
- ✅ CPU usage
- ✅ Memory usage
- ✅ Network latency
- ✅ Restart count

### Session Summary Example:
```json
{
  "session_start": "2025-10-09T18:00:00",
  "session_end": "2025-10-09T20:30:00",
  "duration": "2:30:00",
  "trades_executed": 24,
  "win_rate": 0.67,
  "profit_loss": 450.25,
  "max_drawdown": 0.05,
  "restart_count": 0,
  "components": {
    "python": true,
    "dependencies": true,
    "config": true,
    "health": true,
    "models": true,
    "network": true,
    "broker": true
  }
}
```

---

## 🛠️ Troubleshooting

### Issue: Operator won't start

**Check:**
```bash
# Verify Python is installed
py --version

# Check if config exists
dir config\alphaalgo_config.yaml

# View logs
type logs\autonomous_operator.log
```

### Issue: Dependencies won't install

**Solution:**
```bash
# Manual install
py -m pip install -r requirements.txt

# Or specific package
py -m pip install tensorflow
```

### Issue: Bot enters Safe Mode immediately

**Check:**
1. Network latency: `ping 8.8.8.8`
2. CPU usage: Task Manager
3. Memory available: Task Manager
4. Config file: `config/alphaalgo_config.yaml`

**Adjust thresholds:**
```yaml
network:
  latency_warning_ms: 200  # Increase if needed
  latency_critical_ms: 400
```

### Issue: Broker connection fails

**Check:**
1. API credentials in `api_keys.env`
2. Broker API status
3. Network connectivity
4. Firewall settings

**Fallback:**
- Operator automatically uses paper trading mode

---

## 🎯 Best Practices

### 1. Monitor Logs Regularly
```bash
# Check for errors
Get-Content logs\autonomous_operator.log | Select-String "ERROR"

# Check for warnings
Get-Content logs\autonomous_operator.log | Select-String "WARNING"
```

### 2. Review Session Metrics
- Check daily performance
- Analyze restart patterns
- Monitor resource usage

### 3. Keep Dependencies Updated
```bash
py -m pip install --upgrade -r requirements.txt
```

### 4. Backup Configuration
```bash
# Backup config before changes
copy config\alphaalgo_config.yaml config\alphaalgo_config.yaml.backup
```

### 5. Test in Paper Trading First
- Verify all systems work
- Check performance
- Validate strategies
- Then switch to live trading

---

## 🔒 Safety Features

### Built-in Protection:
1. ✅ **Pre-flight checks** - Won't start if unsafe
2. ✅ **Safe Mode** - Pauses trading on issues
3. ✅ **Auto-recovery** - Fixes transient errors
4. ✅ **Emergency shutdown** - Stops on critical errors
5. ✅ **State persistence** - Saves state for recovery
6. ✅ **Trade limits** - Enforces position limits
7. ✅ **Network monitoring** - Detects connectivity issues
8. ✅ **Resource monitoring** - Prevents system overload

---

## 📚 Related Documentation

- **Network Monitoring:** `docs/NETWORK_STABILITY_GUIDE.md`
- **Quick Start:** `NETWORK_MONITOR_README.md`
- **Configuration:** `config/network_config.yaml`
- **Main Config:** `config/alphaalgo_config.yaml`

---

## ✅ Success Criteria

Your autonomous operator is working correctly if:

- ✅ Starts without errors
- ✅ Completes all validation checks
- ✅ Displays status every 30 seconds
- ✅ Creates log files
- ✅ Auto-installs missing dependencies
- ✅ Monitors network continuously
- ✅ Enters Safe Mode when needed
- ✅ Auto-recovers from errors
- ✅ Saves backups on shutdown

---

## 🎊 You're All Set!

The Autonomous Operator will:
- ✅ **Validate** everything before starting
- ✅ **Start** the bot automatically
- ✅ **Monitor** continuously
- ✅ **Protect** your capital
- ✅ **Recover** from errors
- ✅ **Alert** you of issues
- ✅ **Save** all data
- ✅ **Never leave it hanging**

**Status: RUNNING OK ✅**

---

## 🆘 Support

If you encounter issues:
1. Check logs: `logs/autonomous_operator.log`
2. Review config: `config/alphaalgo_config.yaml`
3. Test network: `py run_network_monitor.py`
4. Manual validation: Check each component individually

---

**🚀 Your AlphaAlgo bot is now fully autonomous!**

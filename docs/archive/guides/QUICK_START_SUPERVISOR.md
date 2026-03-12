# 🚀 AlphaAlgo AI System Supervisor - Quick Start

## ⚡ 2-Minute Setup

### Step 1: Install (30 seconds)
```bash
pip install -r requirements_internet.txt
mkdir -p logs bot_backups reports
```

### Step 2: Run (30 seconds)

**Production Mode:**
```bash
python run_system_supervisor.py
```

**Demo Mode:**
```bash
python examples/system_supervisor_demo.py
```

---

## 🎮 What It Does

### 🌐 Phase 1: Internet Health
- Monitors latency (< 150ms)
- Detects packet loss (< 5%)
- Auto-failover on issues
- Disables trading if unstable

### 📡 Phase 2: Module Monitoring
- Watches 5 critical modules
- Auto-restarts on failure
- Enters degraded mode if needed
- Uses backup data sources

### 🔧 Phase 3: Auto-Repair
- Diagnoses failures automatically
- Clears cache
- Refreshes API tokens
- Restores from backups
- Switches to alternate sources

### 📊 Phase 4: Data Validation
- Validates all incoming data
- Quarantines bad data
- Gets replacement data
- Ensures data quality

### 🔄 Phase 5: Auto-Update
- 24-hour update cycles
- Retrains if performance < 70%
- Archives old models
- Tracks performance

### 🔒 Phase 6: Security
- Protects API keys
- Enforces SSL/TLS
- Scans for malware
- Detects DDoS

### ✅ Phase 7: Stability
- Scores system health (0-100%)
- Selects trading mode
- Validates recovery
- Confirms stability

---

## 📊 Trading Modes

| Mode | Health | Description |
|------|--------|-------------|
| **LIVE** | > 85% | Real money trading |
| **PAPER** | 70-85% | Simulated trading |
| **SAFE_PAPER** | 50-70% | Degraded mode, cached data |
| **OFFLINE** | - | No internet, cached only |
| **DISABLED** | < 50% | Trading stopped |

---

## 🔍 Check Status

### View Logs
```bash
tail -f logs/system_supervisor.log
```

### View Report
```bash
cat system_supervisor_report.json
```

### Programmatic Check
```python
from trading_bot.system_supervisor import SystemSupervisor

supervisor = SystemSupervisor(config)
await supervisor.start()

status = await supervisor.get_system_status()
print(f"Health: {status.health.value}")
print(f"Mode: {status.trading_mode.value}")
```

---

## 🆘 Troubleshooting

### Trading Disabled?
1. Check internet: `logs/network_recovery.log`
2. Check modules: `logs/system_supervisor.log`
3. Wait 15 minutes for auto-recovery

### Module Failing?
1. Check error logs
2. System will auto-restart (3 attempts)
3. Will use backup data if needed

### Data Issues?
1. Check validation stats in report
2. System quarantines bad data
3. Gets replacement automatically

---

## 📁 File Locations

| What | Where |
|------|-------|
| Main Log | `logs/system_supervisor.log` |
| Errors | `logs/system_supervisor_errors.log` |
| Network | `logs/network_recovery.log` |
| Status | `logs/system_status.log` |
| Reports | `system_supervisor_report.json` |
| Backups | `bot_backups/` |

---

## ✅ System Ready When

- ✅ Internet health > 95%
- ✅ All modules = OK
- ✅ No warnings for 15 minutes
- ✅ Data validity > 90%

---

## 🎯 Key Features

✅ **Self-Healing**: Fixes itself automatically  
✅ **Autonomous**: Runs without supervision  
✅ **Adaptive**: Adjusts to conditions  
✅ **Safe**: Disables trading if unsafe  
✅ **Smart**: Learns and improves  

---

## 📚 Full Documentation

- **Complete Guide**: `AI_SYSTEM_SUPERVISOR_GUIDE.md`
- **Implementation**: `AI_SUPERVISOR_COMPLETE.md`
- **Demo**: `examples/system_supervisor_demo.py`

---

**AlphaAlgo AI System Supervisor is ready! 🚀**

# ⚡ AlphaAlgo Quick Commands Reference

## 🎯 Essential Commands

### View Live Status
```powershell
# Real-time main log (updates automatically)
Get-Content logs\autonomous_operator.log -Wait -Tail 50

# Real-time network log
Get-Content logs\network_monitor.log -Wait -Tail 50

# Last 20 lines (quick check)
Get-Content logs\autonomous_operator.log -Tail 20

# View live dashboard
Get-Content LIVE_STATUS_DASHBOARD.md
```

### Check System Status
```powershell
# Quick status check
Get-Content logs\autonomous_operator.log -Tail 5

# Network status
Get-Content logs\network_monitor.log -Tail 10

# View session metrics
Get-Content logs\session_metrics_*.json | ConvertFrom-Json
```

### Test Network
```powershell
# Test DNS (should be fast)
ping 8.8.8.8

# Test Cloudflare
ping 1.1.1.1

# Test connection
Test-NetConnection google.com
```

### Start/Stop Operator
```powershell
# Start (if not running)
py autonomous_operator.py

# Stop (press in terminal)
Ctrl+C

# Check if running
Get-Process python
```

---

## 📊 Monitoring Commands

### Real-Time Monitoring
```powershell
# Watch logs live (best for monitoring)
Get-Content logs\autonomous_operator.log -Wait -Tail 50

# Watch network live
Get-Content logs\network_monitor.log -Wait -Tail 30

# Watch both (in separate terminals)
# Terminal 1:
Get-Content logs\autonomous_operator.log -Wait -Tail 30
# Terminal 2:
Get-Content logs\network_monitor.log -Wait -Tail 30
```

### Search Logs
```powershell
# Find errors
Get-Content logs\autonomous_operator.log | Select-String "ERROR"

# Find warnings
Get-Content logs\autonomous_operator.log | Select-String "WARNING"

# Find Safe Mode events
Get-Content logs\autonomous_operator.log | Select-String "Safe Mode"

# Find status updates
Get-Content logs\autonomous_operator.log | Select-String "AlphaAlgo Running"
```

### Performance Checks
```powershell
# CPU usage
Get-Process python | Select-Object CPU, WorkingSet

# Memory usage
Get-Process python | Select-Object WS -ExpandProperty WS

# System resources
Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory, TotalVisibleMemorySize
```

---

## 🔍 Diagnostic Commands

### Check Components
```powershell
# Check if Python is running
Get-Process python

# Check log files exist
dir logs\*.log

# Check state files
dir state\*.json

# Check backups
dir backup\*.json
```

### Verify Configuration
```powershell
# View main config
Get-Content config\alphaalgo_config.yaml

# View network config
Get-Content config\network_config.yaml

# Check for API keys
Test-Path api_keys.env
```

### Test Network Endpoints
```powershell
# Test Google DNS
ping 8.8.8.8 -n 4

# Test Cloudflare DNS
ping 1.1.1.1 -n 4

# Test broker API (if configured)
Test-NetConnection api.oanda.com -Port 443

# Test general connectivity
Test-NetConnection google.com
```

---

## 📁 File Management

### View Important Files
```powershell
# Main operator log
Get-Content logs\autonomous_operator.log

# Network monitor log
Get-Content logs\network_monitor.log

# Recovery state
Get-Content state\recovery.json | ConvertFrom-Json

# Latest session metrics
Get-ChildItem logs\session_metrics_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content | ConvertFrom-Json
```

### Clean Up (if needed)
```powershell
# Remove old logs (keep last 10)
Get-ChildItem logs\session_metrics_*.json | Sort-Object LastWriteTime -Descending | Select-Object -Skip 10 | Remove-Item

# Remove old backups (keep last 10)
Get-ChildItem backup\trades_*.json | Sort-Object LastWriteTime -Descending | Select-Object -Skip 10 | Remove-Item

# Clear old network logs (if very large)
# WARNING: Only do this if log file is huge
# Clear-Content logs\network_monitor.log
```

---

## 🚀 Quick Actions

### Restart System
```powershell
# Stop current (Ctrl+C in terminal)
# Then start fresh:
py autonomous_operator.py
```

### Run Tests
```powershell
# Test network monitor
py tests\test_network_monitor.py

# Run network monitor standalone
py run_network_monitor.py
```

### View Documentation
```powershell
# Quick start
Get-Content NETWORK_MONITOR_README.md

# Full guide
Get-Content docs\NETWORK_STABILITY_GUIDE.md

# Operator guide
Get-Content AUTONOMOUS_OPERATOR_GUIDE.md

# Live status
Get-Content LIVE_STATUS_DASHBOARD.md

# This file
Get-Content QUICK_COMMANDS.md
```

---

## 🎯 Common Scenarios

### Scenario 1: Check if everything is OK
```powershell
# Quick check
Get-Content logs\autonomous_operator.log -Tail 10

# Look for:
# ✅ "AlphaAlgo Running Successfully"
# ✅ Status updates every 30 seconds
# ✅ No ERROR messages
```

### Scenario 2: System in Safe Mode
```powershell
# Check why
Get-Content logs\network_monitor.log -Tail 20

# Test network
ping 8.8.8.8

# Wait for auto-recovery (system will resume automatically)
```

### Scenario 3: Want to see real-time activity
```powershell
# Open terminal and run:
Get-Content logs\autonomous_operator.log -Wait -Tail 50

# Leave it running - you'll see updates every 10-30 seconds
```

### Scenario 4: Check performance
```powershell
# View latest metrics
Get-ChildItem logs\session_metrics_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content | ConvertFrom-Json

# Check CPU/Memory
Get-Process python | Select-Object CPU, WS
```

### Scenario 5: System stopped unexpectedly
```powershell
# Check last log entries
Get-Content logs\autonomous_operator.log -Tail 50

# Look for errors
Get-Content logs\autonomous_operator.log | Select-String "ERROR" | Select-Object -Last 10

# Restart
py autonomous_operator.py
```

---

## 📊 Status Interpretation

### Good Signs:
```
✅ "Trading loop started successfully"
✅ "AlphaAlgo Running Successfully"
✅ Status updates every 30 seconds
✅ "Network: Stable" or "Network: Unstable" (both OK)
✅ "Safe Mode" (protecting capital - good!)
✅ No ERROR messages
✅ Uptime increasing
```

### Warning Signs (Usually OK):
```
⚠️ "Safe Mode activated" - System protecting capital
⚠️ "Network unstable" - System monitoring, will auto-recover
⚠️ "High CPU usage" - Normal during startup
⚠️ "Missing packages" - System auto-installing
```

### Concerning Signs:
```
❌ "CRITICAL" or "EMERGENCY"
❌ No log updates for >5 minutes
❌ Process not running
❌ Repeated ERROR messages
```

---

## 🔧 Troubleshooting Commands

### If logs aren't updating:
```powershell
# Check if process is running
Get-Process python

# If not running, start it:
py autonomous_operator.py
```

### If Safe Mode won't exit:
```powershell
# Check network
ping 8.8.8.8

# View network log
Get-Content logs\network_monitor.log -Tail 20

# System will auto-exit when stable for 60 seconds
# Just wait - it's protecting your capital!
```

### If you see errors:
```powershell
# View recent errors
Get-Content logs\autonomous_operator.log | Select-String "ERROR" | Select-Object -Last 10

# Check full context
Get-Content logs\autonomous_operator.log -Tail 50

# Usually system auto-recovers, but you can restart if needed:
# Ctrl+C then: py autonomous_operator.py
```

---

## 💡 Pro Tips

### Best Monitoring Setup:
```powershell
# Open 2 PowerShell windows:

# Window 1 - Main log
Get-Content logs\autonomous_operator.log -Wait -Tail 30

# Window 2 - Network log
Get-Content logs\network_monitor.log -Wait -Tail 20

# Now you can see everything in real-time!
```

### Quick Health Check:
```powershell
# One-liner to check everything
Get-Content logs\autonomous_operator.log -Tail 5; Write-Host "`n---`n"; Get-Content logs\network_monitor.log -Tail 5
```

### Performance Monitoring:
```powershell
# Watch resources
while ($true) { 
    Clear-Host
    Get-Process python | Select-Object CPU, WS, StartTime
    Start-Sleep -Seconds 5
}
```

### Log Analysis:
```powershell
# Count errors
(Get-Content logs\autonomous_operator.log | Select-String "ERROR").Count

# Count warnings
(Get-Content logs\autonomous_operator.log | Select-String "WARNING").Count

# Count Safe Mode activations
(Get-Content logs\autonomous_operator.log | Select-String "Safe Mode activated").Count
```

---

## 🎓 Understanding Output

### Status Display Format:
```
==================================================
✅ AlphaAlgo Running Successfully
==================================================
Mode: Paper Trading              <- Trading mode
Network: Stable                  <- Network status
Active Modules: 2 loaded         <- Components running
Last Ping: 39ms                  <- Network latency
Current Timeframe: 5min-1h       <- Analysis timeframes
Trades Executed: 0               <- Trade count
Uptime: 0:11:41                  <- How long running
CPU: 82.1% | Memory: 90.8%       <- Resource usage
==================================================
```

### Network Log Format:
```json
{
  "timestamp": "2025-10-09T18:16:11",
  "endpoint": "8.8.8.8",
  "latency_ms": 13.0,           <- Lower is better
  "packet_loss": 0.0,           <- 0 is perfect
  "status": "online",           <- online/unstable/offline
  "mode": "safe_mode"           <- Current trading mode
}
```

---

## ✅ Quick Reference Card

```
ESSENTIAL COMMANDS:
==================
View Live:    Get-Content logs\autonomous_operator.log -Wait -Tail 50
Quick Check:  Get-Content logs\autonomous_operator.log -Tail 20
Test Network: ping 8.8.8.8
Start Bot:    py autonomous_operator.py
Stop Bot:     Ctrl+C

STATUS CHECKS:
=============
Main Log:     logs\autonomous_operator.log
Network Log:  logs\network_monitor.log
Metrics:      logs\session_metrics_*.json
State:        state\recovery.json
Dashboard:    LIVE_STATUS_DASHBOARD.md

NORMAL BEHAVIOR:
===============
✅ Status updates every 30 seconds
✅ Network checks every 10 seconds
✅ Safe Mode during instability (GOOD!)
✅ Auto-recovery when stable
✅ Continuous logging

WHEN TO ACT:
===========
❌ Process stopped - Restart with: py autonomous_operator.py
❌ No logs for 5+ min - Check process, restart if needed
❌ Repeated CRITICAL errors - Review logs, may need config fix

OTHERWISE: System handles everything automatically!
```

---

**🚀 Keep this file handy for quick reference!**

**Most Common Command:**
```powershell
Get-Content logs\autonomous_operator.log -Wait -Tail 50
```

**This shows you everything in real-time!**

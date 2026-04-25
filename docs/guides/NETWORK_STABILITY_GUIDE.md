# AlphaAlgo Internet Stability & Safety Module
## Complete Network Monitoring & Protection System

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Operating Modes](#operating-modes)
8. [Alert System](#alert-system)
9. [Testing & Validation](#testing--validation)
10. [Integration](#integration)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)

---

## Overview

The Internet Stability & Safety Module provides comprehensive network monitoring and protection for AlphaAlgo, ensuring the bot can detect, handle, and recover from network issues without losing trades or causing errors.

### Key Capabilities

- **Continuous Monitoring**: Real-time latency and packet loss tracking
- **Safe Mode**: Automatic protection during network degradation
- **Offline Mode**: Complete pause during connection loss
- **Auto-Recovery**: Seamless resumption when network stabilizes
- **Fallback Systems**: Redundant endpoints and retry logic
- **Alert System**: Multi-channel notifications (Email, SMS, Telegram)
- **State Persistence**: Recovery state saved for crash protection

---

## Features

### 1. Network Monitoring

```python
✅ Ping latency measurement (every 10 seconds)
✅ Packet loss detection
✅ Multiple endpoint monitoring (primary + fallback)
✅ Async operations for performance
✅ Comprehensive logging
```

**Thresholds:**
- Latency Warning: >150 ms
- Latency Critical: >300 ms
- Packet Loss: >10%
- Timeout: 5 seconds

### 2. Safe Mode Activation

**Triggers:**
- Latency exceeds 300ms
- Packet loss exceeds 10%
- Network becomes unstable

**Actions:**
- ⛔ Stop all new trades
- ✅ Continue managing existing positions (SL/TP)
- 📝 Log: "⚠️ Network unstable – entering Safe Mode"
- 🔔 Send alerts

### 3. Offline Mode

**Triggers:**
- Complete connection loss (ping timeout > 5s)
- All endpoints unreachable

**Actions:**
- ⏸️ Pause all trading activity
- 💾 Save system state to `state/recovery.json`
- 📝 Log: "🌐 Connection lost – trading paused"
- 🚨 Send critical alerts

### 4. Auto-Recovery

**Requirements:**
- Latency < 100ms for 60 consecutive seconds
- All primary endpoints responding

**Actions:**
- 🔄 Re-sync open positions and balances
- ✅ Validate data consistency
- ▶️ Resume trading operations
- 📝 Log: "✅ Internet stable – resuming operations"

### 5. Fallback & Redundancy

```python
Primary Endpoints:
  - Broker API (e.g., api.oanda.com)
  - Google DNS (8.8.8.8)
  - Cloudflare DNS (1.1.1.1)

Fallback Endpoints:
  - Backup API
  - Secondary DNS (8.8.4.4)
```

**Retry Logic:**
- Exponential backoff: 1s, 2s, 4s, 8s, 16s
- Automatic fallback after 2 failures
- Maximum 5 retry attempts

### 6. Alert System

**Channels:**
- 📧 Email (SMTP)
- 📱 SMS (Twilio)
- 💬 Telegram
- 🔗 Webhook

**Alert Levels:**
- INFO: Normal operations, recovery
- WARNING: Network degradation, Safe Mode
- CRITICAL: Connection lost, Offline Mode

### 7. Emergency Shutdown

**Trigger:**
- Network offline for >15 minutes

**Actions:**
- 💾 Save final state
- 🚨 Send critical alert
- 🛑 Graceful shutdown

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AlphaAlgo Trading Bot                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Network Monitor (Core)                      │  │
│  │  - Continuous endpoint monitoring                     │  │
│  │  - Latency & packet loss tracking                     │  │
│  │  - Mode management (Normal/Safe/Offline/Recovery)     │  │
│  │  - State persistence                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                   │
│           ┌───────────────┼───────────────┐                  │
│           │               │               │                  │
│  ┌────────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐           │
│  │ Alert System  │ │ Integration│ │ API Retry  │           │
│  │ - Email       │ │ - Health   │ │ - Backoff  │           │
│  │ - SMS         │ │ - Risk Mgr │ │ - Fallback │           │
│  │ - Telegram    │ │ - Trading  │ │ - Recovery │           │
│  └───────────────┘ └────────────┘ └────────────┘           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

### 1. Install Dependencies

```bash
pip install aiohttp asyncio psutil
```

### 2. Configure Endpoints

Edit `config/alphaalgo_config.yaml`:

```yaml
network:
  enabled: true
  primary_endpoints:
    - "https://api.your-broker.com/health"  # Replace with your broker
    - "8.8.8.8"
    - "1.1.1.1"
  fallback_endpoints:
    - "https://backup-api.your-broker.com"
    - "8.8.4.4"
```

### 3. Configure Alerts (Optional)

Edit `config/network_config.yaml`:

```yaml
alerts:
  enabled: true
  channels:
    - email
    - telegram
```

---

## Configuration

### Basic Configuration

```yaml
network:
  # Enable network monitoring
  enabled: true
  
  # Endpoints to monitor
  primary_endpoints:
    - "https://api.oanda.com/v3/accounts"
    - "8.8.8.8"
  
  # Thresholds
  latency_warning_ms: 150
  latency_critical_ms: 300
  packet_loss_threshold: 10
  
  # Recovery
  stable_latency_ms: 100
  stable_duration_seconds: 60
  max_offline_minutes: 15
  
  # Monitoring
  check_interval_seconds: 10
```

### Advanced Configuration

See `config/network_config.yaml` for full options:
- Retry delays
- Safe mode settings
- Offline mode settings
- Alert templates
- Performance optimization
- Testing scenarios

---

## Usage

### Basic Usage

```python
import asyncio
from trading_bot.connectivity import get_network_monitor

# Initialize
config = {
    'primary_endpoints': ['8.8.8.8'],
    'latency_warning_ms': 150,
    'latency_critical_ms': 300,
    'check_interval_seconds': 10,
    'log_dir': 'logs',
    'state_dir': 'state'
}

monitor = get_network_monitor(config)

# Start monitoring
await monitor.start()

# Check status
status = monitor.get_current_status()
print(f"Network: {status['network_status']}")
print(f"Mode: {status['trading_mode']}")
print(f"Latency: {status['average_latency_ms']:.1f}ms")

# Check if trading allowed
if monitor.is_trading_allowed():
    print("✅ Trading allowed")
else:
    print("⛔ Trading blocked")

# Stop monitoring
await monitor.stop()
```

### With Integration

```python
from trading_bot.connectivity import NetworkIntegration

# Initialize integration
integration = NetworkIntegration(config)
await integration.initialize()

# Check trading status
if integration.is_trading_allowed():
    # Execute trade
    pass

# Get network status
status = integration.get_network_status()

# Shutdown
await integration.shutdown()
```

### Network-Aware Trading

```python
from trading_bot.connectivity import NetworkAwareTrading

# Create network-aware wrapper
trading = NetworkAwareTrading(integration)

# Execute trade with network protection
success = await trading.execute_trade({
    'symbol': 'EURUSD',
    'volume': 0.1,
    'type': 'buy'
})

# Modify position (allowed in Safe Mode)
await trading.modify_position('12345', {
    'stop_loss': 1.0950,
    'take_profit': 1.1050
})

# API call with retry
result = await trading.api_call_with_retry(
    broker_api.get_account_info
)
```

### Register Alert Callbacks

```python
# Custom alert handler
async def my_alert_handler(alert):
    print(f"Alert: {alert['level']} - {alert['message']}")
    # Send to custom notification system

# Register callback
monitor.register_alert_callback(my_alert_handler)
```

---

## Operating Modes

### 1. Normal Mode

**Status:** ✅ ONLINE  
**Trading:** Fully operational  
**New Trades:** ✅ Allowed  
**Modify Positions:** ✅ Allowed  
**Close Positions:** ✅ Allowed  

### 2. Safe Mode

**Status:** ⚠️ DEGRADED / UNSTABLE  
**Trading:** Limited operations  
**New Trades:** ⛔ Blocked  
**Modify Positions:** ✅ Allowed  
**Close Positions:** ✅ Allowed  

**Entry Conditions:**
- Latency > 300ms
- Packet loss > 10%
- Network unstable

**Exit Conditions:**
- Latency < 100ms for 60 seconds
- Network stable

### 3. Offline Mode

**Status:** 🌐 OFFLINE  
**Trading:** All operations paused  
**New Trades:** ⛔ Blocked  
**Modify Positions:** ⛔ Blocked  
**Close Positions:** ⛔ Blocked  

**Entry Conditions:**
- Connection lost (timeout > 5s)
- All endpoints unreachable

**Exit Conditions:**
- Connection restored
- Latency < 100ms for 60 seconds

### 4. Recovery Mode

**Status:** 🔄 RECOVERING  
**Trading:** Validation in progress  
**New Trades:** ⛔ Blocked  
**Modify Positions:** ⚠️ Limited  
**Close Positions:** ✅ Allowed  

**Actions:**
1. Re-sync positions with broker
2. Validate account balance
3. Check for orphaned orders
4. Verify data consistency
5. Transition to Normal Mode

---

## Alert System

### Email Alerts

```yaml
alerts:
  email:
    enabled: true
    from_address: "bot@yourdomain.com"
    to_address: "peterkiragu68@outlook.com"
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    smtp_user: "your-email@gmail.com"
    smtp_password: "your-app-password"
```

### Telegram Alerts

```yaml
alerts:
  telegram:
    enabled: true
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"
```

### SMS Alerts (Twilio)

```yaml
alerts:
  sms:
    enabled: true
    account_sid: "YOUR_ACCOUNT_SID"
    auth_token: "YOUR_AUTH_TOKEN"
    from_number: "+1234567890"
    to_number: "+1234567890"
```

### Alert Messages

**Safe Mode:**
```
⚠️ WARNING
ALERT: AlphaAlgo network unstable (ping: 482ms). 
Entered Safe Mode to protect trades.
```

**Offline Mode:**
```
🚨 CRITICAL
ALERT: AlphaAlgo connection lost. 
All trading paused.
```

**Recovery:**
```
✅ INFO
AlphaAlgo network stable. 
Resuming operations.
```

---

## Testing & Validation

### Run Tests

```bash
# Run comprehensive tests
python tests/test_network_monitor.py

# View results
cat logs/network_test_results.log
```

### Test Scenarios

1. **Normal Operation** - Verify monitoring works
2. **High Latency** - Test Safe Mode activation
3. **Packet Loss** - Test degradation handling
4. **Connection Loss** - Test Offline Mode
5. **Auto-Recovery** - Test resumption
6. **Fallback Endpoints** - Test redundancy
7. **Retry Logic** - Test exponential backoff
8. **State Persistence** - Test recovery state
9. **Alert System** - Test notifications
10. **Emergency Shutdown** - Test prolonged offline

### Manual Testing

```python
# Simulate high latency
# Block primary endpoints in firewall

# Simulate connection loss
# Disconnect internet

# Verify logs
tail -f logs/network_monitor.log

# Check state file
cat state/recovery.json
```

---

## Integration

### With Health Monitor

```python
from trading_bot.system_health import SystemHealthMonitor

# Network status included in health diagnostics
health = SystemHealthMonitor(config)
diagnostics = await health.run_full_diagnostics()

# Network component health
network_health = diagnostics['components']['network']
```

### With Risk Manager

```python
from trading_bot.risk import AdvancedRiskManager

# Risk automatically reduced in Safe Mode
risk_mgr = AdvancedRiskManager(config)

# Position sizing adjusted based on network status
position_size = risk_mgr.calculate_position_size(
    network_stable=monitor.is_trading_allowed()
)
```

### With Trading Engine

```python
# Trading engine checks network before executing
if not monitor.is_trading_allowed():
    logger.warning("Trade blocked - network unstable")
    return False

# Execute trade
await execute_trade(params)
```

---

## Troubleshooting

### Issue: Monitor not starting

**Solution:**
```python
# Check logs
tail -f logs/network_monitor.log

# Verify endpoints are reachable
ping 8.8.8.8

# Check configuration
cat config/alphaalgo_config.yaml
```

### Issue: False positives (Safe Mode triggered incorrectly)

**Solution:**
```yaml
# Adjust thresholds in config
network:
  latency_warning_ms: 200  # Increase from 150
  latency_critical_ms: 400  # Increase from 300
  packet_loss_threshold: 15  # Increase from 10
```

### Issue: Alerts not sending

**Solution:**
```python
# Test alert system
from trading_bot.connectivity import NetworkAlertSystem

alert_system = NetworkAlertSystem(config)
await alert_system.send_alert({
    'level': 'INFO',
    'message': 'Test alert',
    'timestamp': datetime.now().isoformat()
})

# Check SMTP credentials
# Verify Telegram bot token
# Check Twilio credentials
```

### Issue: Not recovering after connection restored

**Solution:**
```yaml
# Reduce recovery requirements
network:
  stable_latency_ms: 150  # Increase from 100
  stable_duration_seconds: 30  # Decrease from 60
```

---

## Best Practices

### 1. Endpoint Selection

✅ **DO:**
- Use your actual broker API as primary endpoint
- Include reliable DNS servers (8.8.8.8, 1.1.1.1)
- Configure fallback endpoints
- Test all endpoints before production

❌ **DON'T:**
- Use only DNS servers
- Skip fallback configuration
- Use unreliable endpoints

### 2. Threshold Configuration

✅ **DO:**
- Test thresholds with your actual network
- Adjust based on your broker's typical latency
- Consider your trading strategy requirements
- Monitor false positives

❌ **DON'T:**
- Use default values without testing
- Set thresholds too sensitive
- Ignore network conditions

### 3. Alert Configuration

✅ **DO:**
- Enable multiple alert channels
- Test alerts before production
- Configure alert throttling
- Use secure credentials

❌ **DON'T:**
- Rely on single alert channel
- Skip alert testing
- Hardcode credentials
- Ignore alert failures

### 4. Recovery Strategy

✅ **DO:**
- Verify positions after recovery
- Check account balance
- Validate data consistency
- Log all recovery actions

❌ **DON'T:**
- Resume trading immediately
- Skip validation
- Ignore state files
- Delete recovery logs

### 5. Monitoring

✅ **DO:**
- Review logs regularly
- Monitor false positives
- Track recovery times
- Analyze network patterns

❌ **DON'T:**
- Ignore warning logs
- Skip log rotation
- Disable monitoring
- Delete historical data

---

## Log Files

### Network Monitor Log
```
logs/network_monitor.log
```

Contains:
- Latency measurements
- Packet loss data
- Mode transitions
- Alert triggers
- Recovery events

### Test Results Log
```
logs/network_test_results.log
```

Contains:
- Test execution results
- Pass/fail status
- Error messages
- Timestamps

### Recovery State
```
state/recovery.json
```

Contains:
- Current trading mode
- Open positions
- Pending orders
- Account balance
- Last sync time

---

## Performance Impact

- **CPU Usage:** <1% (async operations)
- **Memory Usage:** ~10MB
- **Network Overhead:** ~1KB per check (every 10 seconds)
- **Latency Added:** <1ms to trading operations

---

## Support

For issues or questions:
1. Check logs: `logs/network_monitor.log`
2. Review configuration: `config/network_config.yaml`
3. Run tests: `python tests/test_network_monitor.py`
4. Check documentation: This file

---

## Version History

- **v1.0.0** - Initial release
  - Network monitoring
  - Safe/Offline modes
  - Auto-recovery
  - Alert system
  - Full integration

---

**🎉 Your AlphaAlgo bot is now protected from network instability!**

# Unified Trading System - Deployment Guide

## Prerequisites

### System Requirements
- **Python:** 3.10 or higher
- **Memory:** 8GB RAM minimum (16GB recommended)
- **Storage:** 10GB free space
- **OS:** Windows 10/11, Linux, macOS

### Dependencies
```bash
pip install -r requirements.txt
```

Key dependencies:
- `asyncio` - Async operations
- `psutil` - System monitoring
- `pyyaml` - Configuration
- `numpy`, `pandas` - Data processing
- `torch` - ML models (optional)

## Quick Start

### 1. Run Demo
```bash
python main_unified_system.py --demo
```

### 2. Run in Paper Mode
```bash
python main_unified_system.py --mode paper --symbols BTCUSDT,ETHUSDT
```

### 3. Windows Launcher
```bash
RUN_UNIFIED_SYSTEM.bat
```

## Configuration

### Environment Variables
```bash
export TRADING_MODE=paper
export TRADING_SYMBOLS=BTCUSDT,ETHUSDT
export INITIAL_CAPITAL=10000
export MAX_RISK_PER_TRADE=0.02
export MAX_DAILY_LOSS=0.05
export LOG_LEVEL=INFO
```

### Configuration File
Create `config/unified_config.yaml`:

```yaml
system_name: AlphaAlgo
system_version: "3.0.0"
environment: production

trading_mode: paper

symbols:
  - BTCUSDT
  - ETHUSDT
  - BNBUSDT

timeframes:
  - 1m
  - 5m
  - 15m
  - 1h

initial_capital: 10000.0
currency: USD

broker: binance
broker_config:
  api_key: ${BINANCE_API_KEY}
  api_secret: ${BINANCE_API_SECRET}
  testnet: true

risk:
  max_position_size: 0.10
  max_total_exposure: 0.50
  max_risk_per_trade: 0.02
  max_daily_loss: 0.05
  max_weekly_loss: 0.10
  max_drawdown: 0.20
  max_leverage: 5.0
  circuit_breaker_threshold: 0.03

execution:
  default_order_type: limit
  default_algorithm: adaptive
  max_slippage: 0.001
  slippage_protection: true

signal:
  min_confidence: 0.6
  min_strength: 0.5
  verification_enabled: true
  min_verification_score: 0.7
  signal_blending: weighted
  signal_ttl_seconds: 300

intelligence:
  ensemble_enabled: true
  num_experts: 10
  regime_detection_enabled: true
  online_learning_enabled: true

governance:
  operation_mode: semi_autonomous
  require_human_approval: false
  auto_approve_threshold: 0.9
  audit_enabled: true
  kill_switch_enabled: true

log_level: INFO
log_to_file: true
log_dir: logs

max_workers: 4
use_gpu: false
memory_limit_mb: 4096
```

## Deployment Options

### Option 1: Local Development
```bash
# Clone and setup
cd trading_bot
pip install -e .

# Run
python main_unified_system.py --mode paper
```

### Option 2: Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV TRADING_MODE=paper
ENV LOG_LEVEL=INFO

CMD ["python", "main_unified_system.py"]
```

```bash
docker build -t unified-trading-system .
docker run -e TRADING_MODE=paper unified-trading-system
```

### Option 3: Docker Compose
```yaml
version: '3.8'
services:
  trading-bot:
    build: .
    environment:
      - TRADING_MODE=paper
      - TRADING_SYMBOLS=BTCUSDT,ETHUSDT
      - INITIAL_CAPITAL=10000
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
```

### Option 4: Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: trading-bot
  template:
    metadata:
      labels:
        app: trading-bot
    spec:
      containers:
      - name: trading-bot
        image: unified-trading-system:latest
        env:
        - name: TRADING_MODE
          value: "paper"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
```

## Production Checklist

### Pre-Deployment
- [ ] Configuration validated
- [ ] API keys secured (not in code)
- [ ] Risk limits configured
- [ ] Circuit breakers enabled
- [ ] Kill switch tested
- [ ] Logging configured
- [ ] Monitoring setup

### Security
- [ ] API keys in environment variables or secrets manager
- [ ] Network firewall configured
- [ ] TLS/SSL enabled for connections
- [ ] Audit logging enabled
- [ ] Access controls configured

### Monitoring
- [ ] Prometheus metrics exposed
- [ ] Grafana dashboards configured
- [ ] Alerting rules defined
- [ ] Log aggregation setup

### Backup
- [ ] Database backups scheduled
- [ ] Configuration backed up
- [ ] Model checkpoints saved

## Monitoring

### Health Endpoint
```python
from trading_bot.unified_system import get_master_system

system = get_master_system()
health = await system.get_health()

print(f"Status: {health.status}")
print(f"Uptime: {health.uptime_seconds}s")
print(f"Errors: {health.error_count}")
```

### Metrics
Key metrics to monitor:
- `system_status` - Overall system status
- `layer_status` - Individual layer status
- `signals_generated` - Total signals
- `trades_executed` - Total trades
- `error_count` - Error count
- `cpu_usage` - CPU utilization
- `memory_usage` - Memory utilization
- `latency_ms` - Processing latency

## Troubleshooting

### Common Issues

**System won't start:**
```bash
# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip install -r requirements.txt

# Check configuration
python main_unified_system.py --status
```

**Layer initialization fails:**
```bash
# Enable verbose logging
python main_unified_system.py --verbose

# Check specific layer
python -c "from trading_bot.unified_system.layers import *; print('OK')"
```

**Connection issues:**
- Verify API keys
- Check network connectivity
- Verify exchange status

**Memory issues:**
```bash
# Reduce workers
export MAX_WORKERS=2

# Limit memory
export MEMORY_LIMIT_MB=2048
```

### Emergency Procedures

**Emergency Stop:**
```python
await system.emergency_stop()
```

**Manual Kill Switch:**
```bash
# Send SIGTERM
kill -TERM <pid>

# Or SIGINT
Ctrl+C
```

## Support

- **Documentation:** `docs/UNIFIED_SYSTEM_ARCHITECTURE.md`
- **Demo:** `python main_unified_system.py --demo`
- **Examples:** `examples/unified_system_demo.py`

---

**Version:** 3.0.0  
**Last Updated:** 2026-02-06

# Local Baseline + Smoke Runbook (Single-Symbol, Paper Mode)

## Scope
Repeatable local startup with conservative risk defaults, then smoke-check:
1. analysis signal generation,
2. order routing path,
3. monitoring metrics/alerts.

Background services (Market Student, Eternal Evolution, Sentiment-related stack) are attempted **only after baseline smoke checks pass**.

## Environment assumptions
- Python 3.10+
- Run from repo root: `cd /workspace/tradingbot`
- If launching scripts under `scripts/runners`, use `PYTHONPATH=.` to expose local package imports.

## Conservative startup config
Use `elite_config.yaml` (repo root) with conservative risk:
- `max_risk_per_trade: 0.005`
- `max_portfolio_risk: 0.02`
- `max_positions: 2`
- `kelly_fraction_limit: 0.1`

## Baseline startup command (paper, single symbol)
```bash
python main.py --mode paper --symbol EURUSD --timeframe M15 --bars 50 --log-level INFO
```

### Expected startup log indicators
- No fatal import/config traceback during CLI boot.
- CLI help runs successfully:
```bash
python main.py --help
```
- Typical non-fatal warnings in constrained envs:
  - missing optional ML libs (torch, transformers)
  - missing observability libs (prometheus_client)
  - missing MT5 runtime integration modules

## Smoke test checklist

### 1) Analysis signal generation
Run:
```bash
python analyze_market.py
```
Expected output shape:
- `Direction: ...`
- `Strength: ...`
- `Confidence: ...`

### 2) Order routing path
Run:
```bash
python - <<'PY'
from trading_bot.execution.algorithms import SmartOrderRouter
router = SmartOrderRouter()
route = router.route_order(symbol='EURUSD', direction='buy', volume=60, current_price=1.1050, urgency='normal')
print(route.get('algorithm'))
print(router.get_stats().get('total_orders'))
PY
```
Expected:
- Algorithm selected (e.g., `twap`)
- Total orders increments to `1`

### 3) Monitoring metrics + alerts
Run:
```bash
python - <<'PY'
import asyncio
from trading_bot.monitoring.prometheus_metrics import PrometheusMetrics
from trading_bot.monitoring.alerting_system import AlertingSystem, AlertSeverity

metrics = PrometheusMetrics(port=9101)
print('metrics_enabled:', metrics.enabled)

async def main():
    alerts = AlertingSystem()
    alert = await alerts.send_alert(
        severity=AlertSeverity.WARNING,
        title='Smoke test alert',
        message='Baseline monitoring path check',
        source='local_smoke',
    )
    print('alert_id:', alert.alert_id)

asyncio.run(main())
PY
```
Expected:
- metrics object initializes (may be disabled if `prometheus_client` missing)
- alert object is created and persisted in recent alerts

---

## Background services (only after baseline pass)

### Market Student
```bash
PYTHONPATH=. python scripts/runners/run_market_student.py --mode demo --symbol EURUSD
```
Observed status: fails on missing export (`quick_start`) in `trading_bot.market_student`.

### Eternal Evolution
```bash
PYTHONPATH=. python scripts/runners/run_eternal_evolution.py --help
```
Observed status: fails on missing export (`EternalEvolutionOrchestrator`) in `trading_bot.eternal_evolution`.

### Sentiment service stack
```bash
PYTHONPATH=. python -m trading_bot.services.sentiment_service --help
```
Observed status: fails early due deep import chain requiring unavailable ML stack (`torch`/`nn.Module`).

## Common failure fixes
- `ModuleNotFoundError: loguru`
  - Use local fallback shim (`loguru.py`) already added in repo root.
- `SyntaxError` in reporting module on startup
  - Ensure `trading_bot/reporting/reporter.py` f-strings use non-conflicting quote styles.
- `ModuleNotFoundError: trading_bot` from runner scripts
  - Prefix commands with `PYTHONPATH=.` when running from repo root.
- Missing optional dependencies (offline/proxy environment)
  - Treat as non-fatal for smoke baseline; avoid enabling modules that hard-require unavailable packages.

## This week’s hardening objective (chosen)
**Risk-control validation over new features.**
- Goal: add integration checks that prove conservative risk settings are honored before execution.
- Immediate first step in this run: stabilize startup path (fallback logging + syntax fix) so risk-validation tests can run consistently.

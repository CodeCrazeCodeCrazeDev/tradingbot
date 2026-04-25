# AI System Operational Guide

This guide makes the repository runnable through a single orchestrator script.

## 1) Repository structure + main entry points

Primary runnable entry points discovered and validated:

- `main.py` → core integrated CLI (`--mode smoke|paper|live`).
- `scripts/launchers/run_integrated_system.py` → integrated orchestration launcher.
- `scripts/launchers/run_production_system.py` → production-style launcher.
- `scripts/launchers/run_ai_system.py` (**new**) → single startup orchestrator that checks env + launches selected entrypoint.

## 2) Single orchestrator (new)

Use:

```bash
python scripts/launchers/run_ai_system.py --mode check --entrypoint main
```

What it does:
- creates required runtime dirs (`logs`, `data`, `models`, `cache`, `reports`),
- verifies critical config files are present,
- checks critical imports (`numpy`, `pandas`, `trading_bot`) and optional imports,
- validates target entrypoint with `--help`,
- writes JSON report to `diagnostics/startup_orchestrator_report.json`.

Run mode:

```bash
python scripts/launchers/run_ai_system.py --mode run --entrypoint main
```

Pass-through args to selected entrypoint:

```bash
python scripts/launchers/run_ai_system.py --mode run --entrypoint main -- --mode paper --symbol EURUSD --timeframe M15 --bars 300
```

## 3) Required environment setup

### Option A (recommended minimal runtime)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-runtime.txt
```

### Option B (full project dependencies)

```bash
pip install -r requirements.txt
```

> Note: In restricted/offline environments, some packages may fail to install (e.g., MT5, deep ML stack). The orchestrator reports those as optional misses where possible.

## 4) Dependency list

- Minimal runtime: `requirements-runtime.txt`
- Full stack: `requirements.txt`
- Optional extras: `requirements-optional.txt`, `trading_bot/requirements.txt`, `trading_bot/dashboard/requirements.txt`

## 5) Configuration prerequisites

Expected files:
- `config/alphaalgo_config.yaml`
- `config/survival_config.yaml`
- `elite_config.yaml`

If they exist, orchestrator proceeds. If missing, check mode fails with explicit diagnostics.

## 6) System architecture (operational view)

At runtime, system components are organized as:

1. **Data layer**
   - data feeds, ingestion, connectivity, storage adapters.
2. **Models/analysis layer**
   - technical analysis, ML modules, sentiment, regime detection.
3. **Agents/orchestration layer**
   - orchestrators and decision engines coordinating signals and strategies.
4. **Execution layer**
   - paper/live execution paths, routing algorithms, broker adapters.
5. **Risk & validation layer**
   - risk controls, safety checks, validation gates.
6. **Monitoring/ops layer**
   - telemetry, alerting, dashboards, diagnostics reports.

The new orchestrator acts as the top control plane for startup validation and launch handoff.

## 7) Quick start commands

Health check:

```bash
python scripts/launchers/run_ai_system.py --mode check --entrypoint main
```

Launch smoke mode:

```bash
python scripts/launchers/run_ai_system.py --mode run --entrypoint main -- --mode smoke --symbol EURUSD --timeframe M15 --bars 50
```

Launch paper mode:

```bash
python scripts/launchers/run_ai_system.py --mode run --entrypoint main -- --mode paper --symbol EURUSD --timeframe M15 --bars 300
```

Try integrated launcher:

```bash
python scripts/launchers/run_ai_system.py --mode check --entrypoint integrated
```

If integrated/production check fails, use `main` entrypoint first and resolve missing packages from the report.

# Working notes for agents

## RSI (recursive self-improvement) subsystem

Canonical research package: `trading_bot/recursive_self_improvement/`.
Legacy duplicates (`recursive_improvement/`, `eternal_evolution/`,
`alpha_evolve/`, `autonomous_learner/`, `adaptive_systems/`,
`meta_learning/`, root `code_evolver.py`, `auto_optimizer.py`,
`auto_rollback.py`, `continual_learner.py`, `self_learning.py`,
`ai_learner.py`, `experiment_tracker.py`, `optimization.py`,
`performance_optimizer.py`) emit DeprecationWarnings and carry no
improvement authority — do not extend them for RSI work.

Rules:
- Never modify `trading_bot/risk/service.py`,
  `trading_bot/core/immutable_shield.py`, `trading_bot/execution/service.py`,
  `trading_bot/unified_bot.py`, `main.py`, or the RSI
  contracts/evaluator/anti-gaming/archive modules as part of a candidate
  change — `ProtectedPathGuard` hashes them and rejects on drift.
- `trading_bot/__init__.py` import costs ~1-3 min. Tests should import
  only needed submodules; keep test files free of heavy top-level work.
- Only bounded numeric parameters on allow-listed strategy families
  (`mean_reversion`, `momentum`, `stat_arb`) are valid Level-1 candidates.
- Real market data: only `market_data.db` EURUSD 1,000 bars. Use
  `trading_bot/evaluation/synthetic_market.py` for tests.

## Test commands

```bash
python -m pytest tests/rsi -q --no-cov -p no:cacheprovider     # v2 suite
python -m pytest tests/foundation/test_rsi_evidence.py \
  tests/foundation/test_rsi_loop.py \
  tests/foundation/test_rsi_replay_causality.py \
  tests/foundation/test_walk_forward_runner.py \
  tests/recursive_self_improvement -q --no-cov                  # v1 regression
python scripts/rsi_synthetic_benchmark.py --seeds 20            # ablation
python scripts/rsi_reachability_inventory.py                   # audit refresh
```

## Environments

Two interpreters, different roles:

- `.venv/` — lightweight dedicated env (no torch). Runs every pytest suite
  listed above plus foundation/execution/interfaces/brokers/strategies
  tests. Cannot `start()` the full bot — `UnifiedTradingBot.start()`
  imports `world_model` which requires torch.
- Hermes env (`%LOCALAPPDATA%\hermes\hermes-agent\venv`) — carries
  torch/transformers; required for the live runner scripts and any test
  importing `trading_bot/__init__.py`.

## Operational commands

```bash
# Offline paper runner (canonical runtime, paper fills only, localhost)
python scripts/paper_runner.py --source synthetic --cycles 40 \
  --state-dir var/paper_run --interval 0

# Operator controls against a running bot (audited, no order entry)
python scripts/operator_cli.py --state-dir var/paper_run pause
python scripts/operator_cli.py --state-dir var/paper_run resume
python scripts/operator_cli.py --state-dir var/paper_run flatten
python scripts/operator_cli.py --state-dir var/paper_run cancel-all
python scripts/operator_cli.py --state-dir var/paper_run estop
python scripts/operator_cli.py --state-dir var/paper_run reset-emergency
python scripts/operator_cli.py --state-dir var/paper_run status

# Read-only dashboard snapshot published to <state-dir>/snapshot.json;
# optional GET-only server via --dashboard-port (binds localhost only)

# Execution idempotency fault gate (restart + duplicate + UNKNOWN faults)
python scripts/fault_gate.py --events 10000 --state-dir <tmp>  # suite gate
python -m pytest tests/execution/test_fault_gate.py            # small scale

# MT5 demo preflight — READ-ONLY, requires rotated demo-only credentials.
# Runs under the hermes env (MetaTrader5 SDK); never sends an order.
python scripts/mt5_preflight.py --authorize-connect
```

## Credential status

The previously committed MT5 demo credential (the MetaQuotes-Demo account
login/password + investor password) was hardcoded in `scripts/` and is in
git history — **it is burned and must not be reused**. Literal secrets have
been scrubbed from executable files; `DOCS/` retains the exposure records.
`scripts/mt5_preflight.py --authorize-connect` asserts rotated demo-only
credentials are provisioned before any terminal connection is attempted.

Pause/emergency flags persist under `control:*` keys in the repository's
`account_state` table and are re-applied on runner start — a restart does
not silently resume trading.

Disk space is tight (~2 GB free). Run pytest with `-p no:cacheprovider`;
avoid large artifacts; keep `.merge_backup/` (pre-merge untracked files).

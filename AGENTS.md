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

Disk space is tight (~2 GB free). Run pytest with `-p no:cacheprovider`;
avoid large artifacts; keep `.merge_backup/` (pre-merge untracked files).

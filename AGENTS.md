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

# MT5 demo runner — live M15 bars, demo-only execution through the
# canonical CSC→risk→shield→governance→bus→execution pipeline.
# --replay N validates on the last N closed bars; --follow polls for each
# new closed M15 bar (soak). --auto-approve opts in to autonomous demo
# trading (audited); omit it to require per-trade operator decision files.
python scripts/mt5_demo_runner.py --replay 30 --auto-approve \
  --state-dir var/mt5_demo
python scripts/mt5_demo_runner.py --follow --cycles 8 --dashboard-port 8080
# Replay produces paper fills with measured-cost frictions
# (--paper-spread-bps/--paper-slippage-bps/--paper-commission). When MT5
# creds aren't provisioned, --current-session attaches to the terminal's
# open session (explicit opt-in; DEMO validation still enforced).
```

### MT5 venue quirks (observed on MetaQuotes-Demo, 2026-10-07)

- `common.ini` `[Experts] Enabled=1` is the AutoTrading toggle — edit it and
  restart `terminal64.exe` to enable algo trading headlessly. `Api=0` is
  correct; setting it to 1 *disables* API trading (inverted semantics).
- The Python SDK rejects order `comment` strings ≥30 bytes despite the
  documented 31-char limit — the adapter caps comments at 29.
- `SYMBOL_FILLING_*` is a bitmask where bit `1 << ORDER_FILLING_*` marks
  support; MetaQuotes-Demo EURUSD is FOK-only (`filling_mode=1`). The
  adapter probes the mask rather than hardcoding IOC.
- Hedging accounts return one row per ticket from `positions_get`;
  reconciliation aggregates signed quantity per symbol before comparing
  to the ledger.
- `quantity` on a proposal is unit intent — the risk service is the
  sizing authority and clamps to the venue volume grid (`volume_step`/
  `volume_min` fields on the observation).

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

## Concurrent editing hazard (observed 2026-10-09)

Multiple agent sessions rewrote `trading_bot/core/csc/advisory.py` in
parallel; it was truncated to 0 bytes three times and uncommitted work was
lost repeatedly. Do NOT run concurrent agent sessions against this repo,
and never against the same file. If a parallel session is unavoidable:
commit work immediately after each change, use atomic temp-file
replacement for large writes (plain `open(w)` truncates on ENOSPC), and
verify `git status` before and after edits.

## Trading bot diagnosis and recovery

When asked why the bot is not running or behaving like an AI trading system,
follow `DOCS/DEVIN_TRADING_BOT_RECOVERY_PLAN.md`. Start with offline evidence
and its safety/authorization gates; treat findings there as scoped to its
review date and verify them against the current code before changing anything.

## Reasoning and sandbox policy (operator-directed)

- Use strong reasoning models for defensive security review, code
  hardening, trading research, and post-trade analysis — not for
  autonomous live execution decisions.
- Prefer real-world validation and regression tests over
  benchmark-only confidence claims.
- Untrusted strategy code, generated patches, unknown files, and
  external-repo experiments run in ephemeral sandbox sessions with no
  persistent secrets and no production access (`SandboxManager`
  subprocess backend with kernel Job Object limits (memory cap,
  child-spawn ban, kill-on-close, network bandwidth strangle),
  secret env scrubbing, dead-proxy injection, and LOW-integrity
  FS confinement — sandbox children are kernel-blocked from
  writing to medium-integrity objects (profile, repo) and are
  confined to a per-eval low-labeled scratch dir. Still not a
  container: no FS virtualization for reads, bandwidth strangle
  is not a socket wall (true blocking needs OS firewall rules).
- Verifier keys provisioned outside the repo tree
  (`key_custody`); on Windows they are DPAPI-encrypted at rest
  (bound to the user account). External HSM/KMS custody remains
  the declared residual.
- Live deployment, broker credential changes, risk-limit changes,
  capital scaling, production patching, strategy promotion, and
  kill-switch overrides require signed operator approval
  (`OperatorAuthorization`, Ed25519).
- Keep vulnerability details private until patched or maintainers
  approve coordinated disclosure.
- Specialist-agent routing already exists: verifier swarm
  (market-structure/cost/risk), advisory electorate, RSI evaluators.
  Route new risky work through them rather than new parallel brains.
- Risky decisions use sealed provenance traces and append-only audit
  (decision-bus jsonl, hash-chained archive, evidence_ledger triggers).

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
# NOTE: tests/recursive_self_improvement needs the Hermes env (imports
# torch via governance_bridge); run it there, the rest in .venv.
python scripts/rsi_synthetic_benchmark.py --seeds 20            # ablation
python scripts/rsi_reachability_inventory.py                   # audit refresh
```

## Sleep phase (arXiv:2606.03979 transfer)

`trading_bot/recursive_self_improvement/sleep_cycle.py` implements an
offline "sleep" phase on top of `RecursiveImprovementCycle`:
consolidation distills archive records into memory `lessons` and prunes
the `experiments` buffer (the hash-chained `evidence_ledger` is never
touched); "dreaming" generates regime-shifted synthetic scenarios, keeps
those with discriminative power across bounded parameter probes, and
rehearses cross-regime recombinations of archived specialist parameters.
Dream output is ledger-recorded as `dream_diagnostic` with
`promotion_eligible: false` — only the gated paired-replay cycle can
produce `eligible_for_operator_review` verdicts, and deployment still
requires signed `OperatorAuthorization`. `run_cycle(selector=...)` is the
diversity-selection seam (`select_diverse_hypotheses` spends the
per-cycle budget across distinct parameters). `SleepPhaseRunner` is
fail-closed: an awake runtime without a wired `pause_fn` refuses to run.
`channel_sleep_controller(state_dir)` wires pause/resume through the
operator `ControlChannel`.

`rsi_sleep_cycle.py` also schedules periodic windows
(`--every-cycles N` polls the runner's `snapshot.json` cycle count,
`--every-seconds N` is the wall-clock fallback, `--max-sleeps` bounds
the loop) and `--quiesce-timeout` must outlast one runner cycle —
mid-cycle control drains starve when `run_cycle` is CPU-bound, so the
pause effectively lands at the next cycle boundary.

```bash
python scripts/rsi_sleep_cycle.py --work-dir var/rsi_sleep            # standalone
python scripts/rsi_sleep_cycle.py --state-dir var/paper_run           # pauses a live runner
python scripts/rsi_sleep_cycle.py --state-dir var/paper_run \
  --every-cycles 100 --quiesce-timeout 1800                           # scheduled window
python scripts/rsi_sleep_cycle.py --db market_data.db --instruments EURUSD
python scripts/rsi_synthetic_benchmark.py --sleep --seeds 5           # sleep ablation
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

## World-model V2 evaluation + market_data.db quality

- `scripts/eval_world_model.py` (hermes env — needs torch) evaluates
  `var/world_model_v2.pt`: per-block latent skill vs persistence and
  random-init control, plus ridge probes latent-vs-raw-features on
  observable next-bar targets (return, |return|, range), chronological
  fit/test, off-grid bars excluded. Artifact: `var/world_model_eval.json`.
- `market_data.db` EURUSD M15 contains 1,000 off-grid spliced rows
  (fractional-second timestamps, ~:09:51.890219), 2026-06-04→2026-06-14,
  interleaved with real bars producing ±6.7% alternating fake returns.
  Detect with minute%15!=0 or fractional seconds (see `off_grid_mask` in
  eval script). ~1,274 contaminated the v2 checkpoint's training split.
  ~26 other |ret|>0.5% bars over 2024-2026 look like genuine news/gap moves.
- Eval result 2026-11-07: checkpoint beats persistence on held-out latent
  cosine only +0.0026 (metric saturates: consecutive-bar cos ~0.99).
  Observable probes: trained latent ≈ random-init latent on every target;
  raw features predict next range R² +0.32 / |ret| +0.26 over naive
  baselines, latent probes negative R² at any ridge λ. The latent is not
  currently a usable predictive representation.
- 2026-11-07 retrain (filtered data + joint observable decoder head +
  strengthened gate in `train_world_model.py`): 600 steps -> latent skill
  -0.001, decoder range R2 -1.26 vs raw-ridge -0.17 -> gate REJECTED, no
  checkpoint written (old Oct-19 ckpt untouched). Metrics +
  provenance in `var/world_model_v2.train_meta.json`. Even clean data +
  decoder-shaped encoder did not transfer across the train/held-out
  regime boundary; the JEPA-latent objective at this scale is not
  producing observable-predictive structure. Save gate is now: latent
  skill > 0 AND decoder range R2 >= raw-feature ridge R2.
- `scripts/train_vol_forecaster.py` (GRU 25k params, raw features ->
  next range + |ret|, same split/gate protocol): 1000 steps ->
  range R2 -1.00, |ret| R2 -0.21 vs persistence -> REJECTED, worse than
  the per-bar ridge (-0.11 / +0.08). Verdict: on this M15 EURUSD
  series, next-bar vol has no transferable predictability past the
  70/30 regime boundary for anything tried (WM latents, joint decoder,
  direct GRU). Persistence is near-optimal here; only the +0.32 figure
  seen earlier was an adjacent-regime probe fit, not a transferable one.
- `scripts/train_rv_forecaster.py --ratio --blend` (GRU+ridge 50/50,
  log(rv_H/roll21|ret|) targets, H in {4,8,16}): rv16 blend R2 +0.43 /
  corr 0.67 — first artifact to pass its gate
  (`var/rv_blend_forecaster.pt`). Next-BAR vol is unpredictable (above),
  but multi-bar forward vol is not. paper_runner `--rv-forecast` emits
  `rvf_*` obs fields + `rv_forecast_log.jsonl`; the CSC consumes
  `rvf_mult_rv16` as a bounded down-only sizing scalar.
- `scripts/rv_walkforward_eval.py` (hermes env) re-judges RV claims on
  contiguous expanding-window folds with an S+H embargo — single 70/30
  splits kept producing adjacent-regime mirages. 2026-11-07 result:
  blend holds on all 5 EURUSD folds (rv16 mean +0.45, fully-OOS folds
  +0.42..+0.49) and transfers ZERO-SHOT to GBPUSD (+0.49, 5/5). USDJPY
  fails — per-fold ridge positive only 3/5 at rv8/rv16, EURUSD weights
  don't transfer (mean -0.02); in-pair retrain
  (`var/rv_blend_forecaster_jpy.pt`) fixes it: 5/5 folds positive, rv16
  mean +0.19. Vol-ratio skill is the first verified transferable signal;
  JPY needs its own weights, EURUSD covers both EURUSD and GBPUSD.
  Reports: `var/rv_walkforward.json`, `var/rv_walkforward_jpy.json`.
- Quantile extension (`scripts/train_rv_quantile.py`, GBM pinball
  P50/P80/P95 on the same ratio target): 5/5 folds positive pinball
  skill at every tau on EURUSD (rv16 q80 +0.22, q95 +0.13) with
  near-target coverage. Artifact `var/rv_quantile_forecaster.joblib`;
  runtime `RVBlendForecaster(quantile_path=...)` emits
  `rvf_q{50,80,95}mult_rv*` obs fields via `--rv-quantile`. USDJPY
  in-pair artifact: `var/rv_quantile_jpy.joblib` (coverage 0.81/0.94,
  better calibrated than EURUSD's conservative tail). Soak 2026-11-08
  (`--source db --skip 2000 --seed-bars 48 --rv-forecast
  --rv-quantile`): 60/60 cycles forecast-ready from bar 1 — seed rows
  now warm the forecaster's 32-bar window (prior_seed_rows carries
  OHLCV+ts); rv16 mult ranged 0.63-1.75, q95 1.55-2.72. Soak 2
  (TB_CSC_EXPLORE_BUDGET=80): the abstention trap is the cold-start
  loop — u=1.0 zeroes every qty, and every directional branch arrives
  with plan qty=0 anyway (planner emits no measured size), so only
  explore-promoted qty=0.1 trades exist. 80 directional proposals,
  50 approved, 8 settled; u moved 1.0->0.23->0.93 on real outcomes.
  rv_vol_size_factor computed live on all proposals (0.41-0.60,
  tracking q95 mult ~2.2). Fix: scalar now applies AFTER explore
  promotion — pre-promotion it could only multiply zero. Sizing
  consumption: `_select_optimal_action` applies a bounded, down-only
  `rv_vol_size_factor = clip(1/mult, 0.25, 1.0)` — P95 mult when
  quantiles are armed, mean mult otherwise. The forecast never raises
  size; risk service stays the sizing authority.
- Direction note (2026-11-07): the JEPA-latent world model produced no
  observable-predictive structure after two honest attempts; the
  verified local-model channel is multi-bar RV ratio + quantiles.
  Any "V3-lite" spine should build on that channel, not latents.
- Off-grid splice contamination is EURUSD-M15-only; GBPUSD/USDJPY M15
  and EURUSD/GBPUSD H1/H4 are clean (verified 2026-11-07). market_data.db
  now carries ~65k M15 bars x3 pairs + H1 (2016+) + H4 (2007+).
- `load_features` in train script now drops off-grid rows
  (`on_grid`); eval imports the same loader, so both paths are clean.
- torch on this box needs `torch.set_num_threads(1)` + OMP/MKL env
  caps: multi-threaded runs deadlock with ~0 CPU (seen twice).

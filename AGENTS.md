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

# Multi-instrument replay: --symbols merges per-symbol db streams by bar
# timestamp (aligned to common start); --universe adds multi-db +
# per-source skip; --universe auto lets the OpportunityScanner pick the
# top-N series by measured structure_score itself.
python scripts/paper_runner.py --source db \
  --symbols EURUSD,GBPUSD,USDJPY --skip 64000 --state-dir var/paper_multi
python scripts/paper_runner.py --source db --universe \
  'market_data.db:EURUSD,GBPUSD:M15:64000;binance_data.db:BTC,ETH:15m:15900' \
  --state-dir var/paper_multi
python scripts/paper_runner.py --source db --universe auto \
  --universe-top 6 --universe-tail 4000 --state-dir var/paper_auto

# US equities + fresh FX: scripts/stock_sync.py pulls keyless Yahoo v8
# chart data into market_data-schema dbs (auto-discovered by scanner).
# FX: EURUSD=X/GBPUSD=X/JPY=X -> fx_data.db (JPY=X maps to USDJPY).
python scripts/stock_sync.py --symbols AAPL,MSFT,NVDA,TSLA,SPY --timeframe 15m
python scripts/stock_sync.py --symbols EURUSD=X,GBPUSD=X,JPY=X \
  --timeframe 15m --db-path fx_data.db
python scripts/paper_runner.py --source db \
  --universe 'us_stocks.db:AAPL,MSFT,NVDA,TSLA,SPY:M15' \
  --state-dir var/paper_stocks

# Rotating universe: --universe-refresh N re-ranks all onboarded series
# every N bars on closes strictly BEFORE the tape clock (no lookahead);
# entries join at the clock, drops stop emitting. Watch
# 'universe re-rank @<ts>' + 'feed mix' log lines.
python scripts/paper_runner.py --source db --universe auto \
  --universe-refresh 500 --cycles 1000 --state-dir var/paper_rotate

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
  tracking q95 mult ~2.2). Mechanics (soak 2/3): plans DO carry
  qty=1.0 unit intent (hypothesis.py) but the electorate verdict is
  nondirectional every cycle (won_by_branch_range) — all directional
  trades are _explore_probe promotions capped at min(qty, 0.1), and
  the u=1.0 floor zeroes the rest. Scalar applies AFTER explore
  promotion — pre-promotion it could only multiply zero. Soak 3
  (`--explore-budget 40`, 22 cycles in): approved exploratory qty is
  now 0.037-0.051 = 0.1 x vol_factor — the forecast observably moves
  real executed size. `--explore-budget N` on paper_runner sets
  TB_CSC_EXPLORE_BUDGET before bot start; without it every qty is
  zeroed by the u=1.0 floor and nothing ever trades. For the scalar
  to bind at full unit intent (~0.3-0.7 after unc x vol) a bull/bear
  branch must win the electorate on merit — a data/alpha question,
  not wiring. Policy (2026-11-09): explore probes stay capped at 0.1
  forever — they buy information, not conviction. Promotion to real
  size is a capital-scaling decision: signed OperatorAuthorization,
  never an automatic graduation rule or an env-var knob. A branch
  that wins on merit needs no graduation machinery. Sizing
  consumption: `_select_optimal_action` applies a bounded, down-only
  `rv_vol_size_factor = clip(1/mult, 0.25, 1.0)` — P95 mult when
  quantiles are armed, mean mult otherwise. The forecast never raises
  size; risk service stays the sizing authority.
- Direction note (2026-11-07): the JEPA-latent world model produced no
  observable-predictive structure after two honest attempts; the
  verified local-model channel is multi-bar RV ratio + quantiles.
- Alpha verdict (2026-11-09, measured): ~20 rule classes gated on
  M15 h=4/h=16 and H1 h=4 across EURUSD/GBPUSD/USDJPY — including
  vol-regime-conditioned variants (vol_exp_mom / vol_con_fade /
  regime_switch added to edge_hypotheses.py) — ALL net ≈ -cost_bps
  on every walk-forward segment. Gross directional edge ≈ 0 on this
  data at every tested horizon; the electorate's abstention is the
  correct answer, not a pipeline failure. Directional exposure only
  exists via bounded explore probes (by design), and any future
  directional claim must arrive through the edge_gate as a killable
  hypothesis with venue-level evidence. The verified contribution
  of local models is vol/risk information for sizing, not direction.
- Macro channel check (2026-11-09, macro_data.db — real daily UST/EU
  yields + spot, published_at same-day = lookahead-free): ΔUST2y→
  EURUSD OOS r=-0.215 (correct sign, stable); daily-PnL eval of
  threshold rules (|Δ|>10-15bp, cost 5bps): OOS mean +0.5..+1.2bps/d
  in 3/4 variants but LCB5<0 on all — real relationship, sub-gate
  strength. COT lev_money positioning: OOS r -0.15..-0.27, sign
  flips vs train — rejected. Closest lead yet is rates-momentum on
  DAILY horizon; it does not promote.
- `scripts/macro_rates_gate.py` (proper gate eval, 2026-11-09):
  daily-horizon rates-momentum on macro_data.db — 39 variants x 3
  pairs, point-in-time clean, cost 5bps/change, 60/40 + 3-segment
  OOS. THREE variants cleared all-segment LCB5>0 — the first
  directional candidates in the repo:
  dUST2y_10d>0.15@USDJPY (mean +4.56bps/d, LCB +0.87..+1.88, 24%
  expo), dUST2y_10d>0.15@EURUSD (+3.74, LCB +0.25..+1.58, 25%),
  dUST2y_10d>0.2@EURUSD (+2.54, LCB +0.07..+0.87, 14% — thin).
  Caveats: single data source (no cross-venue), ~160d segments,
  daily not M15 — promotion would still need the edge_gate's
  venue-level protocol, but the signal is real, sign-consistent,
  and theory-correct (USDJPY = strongest, as rates-sensitivity
  predicts). Report: var/macro_rates_gate.json.
  Any "V3-lite" spine should build on that channel, not latents.
- Venue replication FALSIFIED the rates channel (2026-11-12,
  `scripts/macro_rates_venue_gate.py`): same signals re-judged on
  tradeable D1 bars (fx_data.db, Yahoo composite, 2012->2026) with
  yields reindexed lookahead-safe (`--yield-lag`). lag=1 (yields
  strictly before bar date): EVERY variant rejected on all 3 pairs —
  best mean +0.79bps, LCB<0. lag=0 (original same-day convention):
  USDJPY dust_2y_10d|>0.15 mean +2.07/LCB +0.38 but recent-third
  segment -1.46 — fails all-segments; all else rejected. Verdict:
  rates↔FX is a coincident daily relationship, not a leading one —
  the fixing-series "edge" needed the day-t+1 yield print before the
  day-t+1 fixing completed (suspected lookahead in
  macro_rates_gate.py's pos/ret alignment: pos[t] consumes yield
  index t+1 to earn spot[t]->spot[t+1]). Treat the 3 "candidates" as
  FALSIFIED at venue level; the channel stays open only as a
  coincident risk indicator, not a signal. Reports:
  var/macro_rates_venue_gate_lag{0,1}.json.
- `trading_bot/autonomous_financial_intelligence/` audited
  (2026-11-12, `DOCS/AFI_PACKAGE_AUDIT.md`): legacy/quarantined —
  only live import is LogicalVerifier types via
  chainofthoughtreasoner (try/except); data_canonicalizer +
  fact_checker FABRICATE canonical prices (random.gauss/hardcoded);
  README documents methods that don't exist; package now emits
  DeprecationWarning. Disposition: extract logical_verifier, then
  archive; destination remains DOCS/AUTONOMOUS_FI_INFRASTRUCTURE.md.
- M1 method->candidate loop built (2026-11-12):
  `trading_bot/core/csc/research/method_spec.py` — MethodSpec
  (spec_id/hypothesis/family/bounded params/provenance/falsification)
  compiles through allow-listed parametric families
  (momentum/meanrev/donchian/vol_regime_momentum; RSI Level-1
  spirit: numeric params only, no free code) into
  `fn(closes,i)->-1/0/+1` for the edge gate, and
  `positions_triple` emits the (candidate, flat-baseline, next-bar
  returns) contract for `ResearchEngine.evaluate_strategy`.
  `scripts/method_candidate.py --spec|--family --param k=v --db --symbol
  --timeframe [--csc-eval]` runs segmented all-LCB gate eval and
  writes var/method_candidates/<id>_<hash>.json (advisory only).
  Smoke: momentum(10,15bps)@EURUSD M15 h=4 -> rejected, mean -5.3bps
  (consistent with the no-directional-edge verdict). Tests:
  tests/foundation/test_method_candidate.py (9 tests, ~55s — pays
  the trading_bot/__init__ import once).
- M1 extraction + M2 cycle (2026-11-12):
  `core/csc/research/spec_extractor.py` — mechanical text->MethodSpec
  mapper (keyword->allow-listed family, numeric hints clamped into
  declared bounds with clamps recorded in provenance; honest [] on
  no match, never fabricates). Wired into `scripts/internet_scout.py`:
  governance-passed candidates now carry `method_specs` in the ledger
  record (guarded import — extraction failure can't sink a scout).
  `scripts/autonomous_cycle.py` — M2 runner: rotating query ->
  optional bounded scout subprocess -> harvest specs from ledger ->
  segmented gate eval per dataset -> var/reports/YYYYMMDD.md +
  var/autonomous_cycle/cycles/*.json. Zero authority; --once or
  --interval-hours N --max-cycles M. `--replication-datasets` adds
  the DIFFERENT_DATASET rung: any spec with a candidate verdict is
  re-judged there; survivors keep "candidate", failures are marked
  "candidate_unreplicated" and excluded from the candidate count.
  Tests: tests/foundation/test_spec_extractor.py (7 tests).
- M3+M4 (2026-11-12): `scripts/data_catalog.py` -> var/data_catalog.json
  (20 dbs / 85 series / 659k rows; macro_data.db cataloged at
  series level, others at symbol/timeframe). `scripts/intel_report.py`
  merges scout ledgers + cycle reports + method candidates + catalog
  into var/intel_report.md. `autonomous_cycle.py --interval-hours 24
  --max-cycles 7 --scout` runs unattended (var/autonomous_cycle).
- Cross-venue lead-lag FALSIFIED (2026-11-12, `scripts/cross_venue_gate.py`):
  Binance taker_imb (2*buy/vol-1, 15m) -> Kraken/HL same-index next-bar
  returns, lookahead-safe. BTC/ETH x hl+kraken all rejected, best means
  -0.59..-2.94bps at 5bps cost (imb coverage 33-96%). Report:
  var/cross_venue_gate.json.
- Event-study FALSIFIED (2026-11-12, `scripts/event_study_gate.py`):
  news_events (339 rows, FOMC/NFP/ALFRED vintages) -> M15 continuation
  of event-bar direction, horizons 1/2/4/8 bars. High-impact n~106/pair:
  ALL rejected (means -3..-8bps net of 5bps; EURUSD h1 -61bps outlier).
  Medium-impact n=20 -> insufficient_evidence. Scheduled-release
  continuation has no net edge at retail cost. Report:
  var/event_study_gate.json. NOTE: impacts stored title-case
  ('High'/'Medium') — normalize before filtering.
- Vol-regime monetization FALSIFIED (2026-10-16 data, hermes env,
  `scripts/vol_regime_gate.py`): rv16 blend ckpt forecasts -> tercile
  regimes on EURUSD M15 (29k bars, 11.6k eval). ALL 7 structures
  rejected at 5bps turnover: mom_flat -0.31, mom_highvol -0.12,
  mom_lowvol -0.11, mr_lowvol -0.11, mr_highvol -0.32,
  regime_switch -0.23, invvol_size -0.34 (mean bps/bar, LCB<0).
  Nuance: regime conditioning DOES shift means ~3x (forecast carries
  real regime info) but nothing crosses zero net of cost — vol skill
  is a sizing/risk input, not alpha. Report: var/vol_regime_gate.json.
  EDGE SCOREBOARD COMPLETE: every directional channel falsified;
  verified skills = vol forecasting (sizing) + safety spine only.
- PAIR family added to method->candidate compiler (2026-11-12):
  `stat_arb` (RSI allow-listed but was missing) — spec.pair declares
  hedge leg {db,symbol,timeframe}; align_pair inner-joins timestamps;
  rule2(a,b,i) fades log-spread z-score; pair_pnl_bps charges cost
  PER LEG (x2); pair_triple feeds evaluate_strategy spread returns.
  method_candidate `--pair db:sym:tf`; autonomous_cycle marks
  pair-less extracted specs `needs_pair` (not rejected). Smoke:
  EURUSD~GBPUSD D1 z2.0 -> rejected -4.06bps (honest null).
  Tests: +6 in test_method_candidate.py (21 total pass).
- Off-grid splice contamination is EURUSD-M15-only; GBPUSD/USDJPY M15
  and EURUSD/GBPUSD H1/H4 are clean (verified 2026-11-07). market_data.db
  now carries ~65k M15 bars x3 pairs + H1 (2016+) + H4 (2007+).
- `load_features` in train script now drops off-grid rows
  (`on_grid`); eval imports the same loader, so both paths are clean.
- torch on this box needs `torch.set_num_threads(1)` + OMP/MKL env
  caps: multi-threaded runs deadlock with ~0 CPU (seen twice).

## CSC capability matrix

`trading_bot/core/csc/capabilities.py` — `CSCCapabilities(csc, ctx=ExpansionContext(...))`
binds every advertised "autonomous superintelligence" capability to a real
bounded mechanism instead of the fabricated `autonomous_superintelligence/`
implementations. Everything is measured or honestly refused:

- analyze/optimize/train/tune/discover/experiment -> sealed
  `propose_model`/`validate_model` (+ `benjamini_hochberg` FDR); sweeps carry a
  selection-bias warning, "useful" means CONFIRMED only.
- builds+deploys agents -> foundry + real `approve_model` ->
  `attach_engineered_model`; stalls at `awaiting_human` without the
  durable `control:model_approval:<id>` flag, never self-attaches.
- tests+rollback -> byte snapshot + real pytest subprocess + byte restore,
  refuses all `ProtectedPathGuard.PROTECTED_PATHS` (asserted equal in test).
- scan/opportunities/arbitrage -> measured `series_stats`/`scan_all` and a
  cross-source same-series close-discrepancy probe (stale-data evidence,
  not tradeable arbitrage without synced quotes).
- industries/products -> correlation sectors + sealed-eval product cases.
- infrastructure/resource balance -> verified data onboarding + local-host
  psutil throttle. No servers/regions/global fleet.
- measurable self-model (honest "consciousness") -> introspection coverage
  over real CSC surfaces; knowledge graph edges require shared measured
  basis; capital deployment -> read-only accounting of the real
  fills/positions ledger (order authority stays canonical).

`capability_report()` gives per-claim mechanism+scope+probe (never VERIFIED
by fiat). `attach_capability_services(csc)` registers 7 read-only probes as
advisory services — work-performing methods stay operator-invoked — and is
wired into `expansion.service.attach_expansion_services` so the canonical
assembly actually attaches them to the running CSC (key `capability_services`
in the attach report).

Known-honest bounds after the 2026-11-09 hardening pass: protected-path
comparison happens on RESOLVED paths (aliases/case/dirs refused); rollback
restores bytes on ANY pytest outcome incl. launch failure; the threshold
sweep is fixed-parameter `evaluate_holdout` (the fitter can't override the
swept value); `discover_methods` requires verdict CONFIRMED AND fdr_survivor;
agent attach requires the durable operator flag AND a present verifier
swarm (reviewer_absent -> gate 'reviewer_unavailable'); sector discovery
correlates on shared timestamps only; `deployment_performance` reports
average-cost realized + last-fill-mark unrealized P&L; `balance_resources`
actuates via bounded advisory `timeout_s` scaling when `apply=True`.
`capability_verification.py` reports honest statuses
(VERIFIED / VERIFIED_BOUNDED / UNPROVEN / RETIRED_BY_DESIGN) — no more
24/24 VERIFIED. `autonomous_superintelligence/` emits a package-level
DeprecationWarning. `detect_executable_arbitrage(dbs, symbol)` measures
top-of-book cross-venue net spread (depth-capped, fee/gap bounded; honest
insufficient_data under 2 venues) and `search_architecture_space(bars)`
enumerates the honest spec space (threshold grid + logistic subsets + GA
grammar) through the sealed gate with FDR.

```bash
python -m pytest tests/foundation/test_csc_capabilities.py -q --no-cov -p no:cacheprovider
```

## Evolution supervisor (CSC self-mastery loop)

`trading_bot/core/csc/evolution_supervisor.py` — `EvolutionSupervisor`
wired into `CognitiveSystemController` (`evolution_supervisor=` kwarg;
`None` disables). Per-observation tick runs in the
`process_market_observation` finally block, so it fires on every
terminal path.

- Every terminal decision (executed/abstained/rejected) is ingested
  into `self_mastery.ExperienceMemory` with decision context;
  `record_outcome`/`record_paper_settlement` attach measured outcomes
  (deduped by settlement_id).
- `MasteryOrchestrator` reflect/learn passes run on ONE daemon worker
  thread (never blocks the pipeline). CodeEvolver output is journaled
  to `evolution_journal.jsonl` — proposals only; `apply_modification`
  is never called. Promotion stays behind RSI gates + OperatorAuthorization.
- `NetworkSentinel` + `SelfDefender` are legacy/quarantined components
  used READ-ONLY (no registered systems, no mode switching). Defender
  state lives under `var/self_mastery/self_defense/`; its credential
  store is NOT the canonical provider.
- Intel sweeps = real browsing + research. `csc/web_browser.py`
  (`WebBrowser`, stdlib-only urllib — works in .venv, no aiohttp/bs4)
  gives web_search (DuckDuckGo HTML, no key), webfetch (page -> text),
  and RSS/Atom news reads, plus arxiv/github via
  `_fetch_internet_evidence`. SSRF guard refuses private/loopback/
  reserved IPs; byte caps, timeouts, per-request min-interval; honest
  `unavailable`/`refused` on failure. Sweeps persist to
  `var/self_mastery/intel/sweep_*.json`. Operator-visible:
  `await csc._evolution.browse(url)` / `.search(q)` — connectivity-gated.
  `internet_access/` deliberately unused: fabricates mock feeds on
  fetch failure.
- Env: `TB_INTEL_FEEDS` (comma-separated RSS URLs; defaults: Google
  News forex, DailyFX, FXStreet).
- AI peer teacher (`csc/ai_peer.py`, `AIPeer`, stdlib urllib): after
  each learn cycle the worker asks a local inference server (Ollama
  `/api/generate` or OpenAI-compatible `/v1/chat/completions`;
  `TB_AI_PEER_ENDPOINT`/`TB_AI_PEER_MODEL`, default qwen3:8b) to
  critique the learning report. 1s TCP probe per consult — zero cost
  when no server runs. Critiques persist as `ai_peer`-tagged
  LESSON_LEARNED experiences + journal entries; untrusted evidence,
  never instructions. `TB_AI_PEER=0` disables. `qwen_codemender`/
  `deepseek_engineer` already model this pattern via aiohttp
  (hermes env only); the peer is the .venv-safe equivalent.
  Backend router `make_peer` (`TB_AI_PEER_BACKEND=auto|ollama|hf`):
  auto probes Ollama (1s) then falls back to `HuggingFacePeer` —
  in-process transformers text-gen (`TB_HF_MODEL`, default
  Qwen/Qwen2.5-0.5B-Instruct; torch/transformers = hermes env).
  Peer critique runs on the worker thread; lessons stay untrusted.
- Advisory wiring (2026-11-09): `golden_path_trap_scan`
  (golden_path AgentTrapScanner over the obs payload — injection/
  memory-poisoning/manipulation markers), `jurisdiction_session`
  (global_expansion venue session state from obs timestamp),
  `mi_smc_structure` (SMC break-of-structure/CoC/premium-discount +
  liquidity pools/voids on real bars) attach in .venv;
  `mi_liquidity_gaps` + `mi_vol_regime_change` are env-gated on scipy
  (hermes env only). `expansion_*` services attach via
  `expansion.service.attach_expansion_services` in assembly —
  already canonical, not orphan. core_api/market_feeds/
  market_student audited with no obs-callable surface — cataloged.
- Self-innovation engine (`csc/self_innovation.py`,
  arXiv:2504.01990): each learn worker synthesizes bounded
  threshold_rule candidates from weakest-skills + failure-kinds +
  frontier hints over DERIVABLE_FEATURES only, runs them through
  csc.propose_model -> validate_model (70/30 holdout, net-of-cost).
  VALIDATED candidates wait for OperatorAuthorization — never
  auto-approved. `TB_INNOVATE_MAX_CANDIDATES` (4).
- Frontier-distillation feed: intel sweeps also extract structured
  `FrontierObservation`s when fetched text names a watched model
  (`TB_FRONTIER_WATCH`, default
  gpt/claude/gemini/deepseek/qwen/llama/mistral/grok). Buffer persists
  to `frontier_observations.jsonl` (50/model cap); once a model holds
  `TB_FRONTIER_MIN_OBS` (5) the learn worker runs
  `csc.distill_frontier(model, obs, [], [])` — the full
  observe->profile->patterns->weakness-inversion->compile->governance
  ->validate->selective-rollout->lineage pipeline in
  `core/frontier_capability_distillation.py`. Honest boundary stands:
  artifacts are playbook/policy/invariant kinds, never model specs,
  nothing auto-enters propose_model. `observe_frontier(...)` is the
  operator feed API. Weakness inversion on fetched docs already runs
  live via `research/institutional.py` + `weakness_inversion.py`.
- Pre-existing bug fixed: `mastery_orchestrator.verify_skill_mastery`
  called `application_success_rate`/`needs_review` (they are
  @property) — `run_continuous_learning` was dead code until then.

Env: `TB_SELF_MASTERY_DIR` (default `var/self_mastery`),
`TB_SELF_MASTERY=0` (kill learning), `TB_AUTONOMY_EXTERNAL=0`
(no monitors/intel — set in sandboxes), `TB_EVO_{REFLECT,LEARN,INTEL,SEC,AUDIT}_EVERY`
cycle cadences (defaults 250/1000/150/50/25).

```bash
python -m pytest tests/core/test_evolution_supervisor.py -q --no-cov
```

## Alt-data ingestion + feature edge evaluation (2026-11-09)

`DOCS/DATA_SOURCES.md` is the registry: every evaluated source mapped
to wired / keyless-planned / licensed. New collectors:

```bash
# macro_data.db: FRED (DGS2/10, SOFR, DEX* fx refs), ECB ref rates +
# euro 10y, CFTC COT managed-money (TFF FX + disagg gold), calendar
python scripts/collect_macro.py                       # all sources
python scripts/collect_macro.py --sources cot --cot-years 3
python scripts/collect_macro.py --sources calendar    # weekly accrual

# second FX venue: Dukascopy ticks -> mid candles + measured spread
python scripts/dsc_candles.py --symbol EURUSD --days 30 \
  --timeframes M15,H1                                 # ~1s/req, feed 429s faster

# feature-conditioned edge eval (news blackout delta, london sweep
# with measured spread, COT fade, US-EU rate-diff trend) ->
# var/edge_features.json
python scripts/edge_features.py --symbol EURUSD \
  --m15-db market_data.db --d1-db market_data.db
```

Facts that will bite you:

- `market_data.db` is deeper than this file used to say: 66,718 EURUSD
  M15 + 30k H4 (2007->). The 1,000 off-grid splice rows are still in
  EURUSD M15; `edge_features.py` drops them automatically.
- fred.stlouisfed.org Akamai-blocks custom User-Agents and stalls
  python/OpenSSL TLS reads; collectors fall back to Git-for-Windows
  curl with its DEFAULT UA (System32 curl also fails).
- `collect_fx_ticks.py` used to stamp .bi5 ticks with LOCAL-time base
  ms (machine is UTC+3 — ticks were shifted -3h); fixed to UTC but
  `var/orderflow/fx_ticks.db` predates the fix.
- COT `XRATE` cross contracts are excluded — they're not the pair's
  own positioning. Positions join on `published_at` (+3d), never as-of.
- Calendar coverage: `--sources calendar` is the forward-only weekly
  mirror; `--sources official` adds REAL FOMC statement+minutes dates
  2021-2027 (parsed federalreserve.gov page, 14:00 ET) and
  `rule_seed:nfp_1st_friday` NFP dates (rule-derived, honest label —
  holiday shifts can be off a week). `--sources releases` discovers
  REAL release dates keylessly via ALFRED `vintage_date=` (binary-
  search first vintage containing each obs; revisions = GDP 2nd/3rd
  estimates; ~5-15 req/release, opt-in). BLS/BEA ICS and Wayback are
  IP-blocked here; `--sources ics` reports them, never fakes.
  Measured blackout A/B (2025-09→2026-10 M15): 199 events, 250 bars
  removed, LCB delta ±0.03bps — filter is neutral on baseline rules.
- First real result: `london_sweep` on clean M15 -> 203 trades,
  lcb5 -6.1bps, no_edge. `rate_diff_trend` on H4-rollup D1 -> 966
  trades, lcb5 -40bps (negative systematic — worth inverting as a
  hypothesis before declaring it dead).

Network-heavy verification commands are slow; the unit tests are not:
`python -m pytest tests/foundation/test_altdata_ingest.py -q --no-cov -p no:cacheprovider`

## CSC modular architecture (2026-11-10)

`trading_bot/core/csc/discovery.py` — AST-scans source for top-level
`CSC_MANIFEST` dicts (`id/kind/provides/requires/factory/status`),
builds the provides/requires dep graph, topo-orders wiring, reports
blocked/cycles/conflicts. Never imports scanned code (trading_bot
init is heavy + concurrent-edit hazard). INVARIANT_IDS + protected
prefixes rejected at plan time.

`trading_bot/core/csc/self_update.py` — composes the existing gates
into a declared loop: scan -> wire advisory factories (SHADOW) ->
propose/validate/operator-flag/attach stays with the controller.
Plan is reported before execution; authority chain unreachable by
construction. "Self-update" = the electorate + candidate pool
improves under measured evidence; the control plane never rewrites.

Docs: `DOCS/CSC_MODULAR_ARCHITECTURE.md` (design), `DOCS/DATA_SOURCES.md`
(source registry), `DOCS/100_REALISTIC_IDEAS.md` (grounded backlog).

Tests: `tests/foundation/test_csc_discovery.py`,
`tests/foundation/test_altdata_ingest.py` (15 tests).

## Research lab (2026-11-10)

`trading_bot/core/csc/research_lab.py` — manifest-declared advisory
service with specialist agents (ResearcherAgent, MLResearchAgent,
RiskEngineerAgent, SystemsEngineerAgent, OpportunityRadarAgent)
behind `AdaptiveRouter`: task kind -> agent `provides` interface,
ordered by EMA health score updated on measured outcomes only.
Artifacts carry confidence: measured|partial|unprovisioned. Advisory
only — `build()` is the CSC_MANIFEST factory; discovery.py wires it
to the CSC at SHADOW. Tests: tests/foundation/test_research_lab.py.
Doc: DOCS/CSC_RESEARCH_LAB.md.

## Neuro-symbolic reasoning layer (2026-11-10)

`trading_bot/core/csc/neuro_symbolic.py` — advisory NSR layer over the
SRE. Policy enforced as data (POLICY dict): live_execution -> refused
by construction; risky_change (deploy/creds/limits/capital/patch/
promote/kill_switch) -> requires_signed_approval; untrusted ->
sandbox_only; vulnerability findings -> sealed pending patch or
disclosure approval; benchmark-only channel can never confirm.
Six persistent specialists (risk/execution/macro/backtest/
code_review/security) review every hypothesis; decisions append to a
hash-chained `var/nsr_ledger.jsonl`. Optional injected model callable
for the neural channel; pattern templates otherwise.
Tests: tests/foundation/test_neuro_symbolic.py (9 tests).

## SRE x neuro-symbolic gate (2026-11-10)

`sre_bridge.SREAdvisoryService` now routes every hypothesis's declared
`target_action` through `neuro_symbolic.route()` before it lands as
evidence: live_exec/order/trade -> refused, _RISKY_OPS actions ->
pending_approval, unknown classes normalize to the safest matching
ActionClass. Artifacts carry `policy: {status, gate, verdict, sealed}`
— "ungated"/"not_applicable" markers are honest, never implied pass.
Tests: tests/foundation/test_sre_bridge_gate.py.

## Expansion capabilities (2026-11-10)

`trading_bot/core/csc/expansion_capabilities.py` — 12 advisory
capabilities through `ExpansionCapabilities.run(name, ctx)` /
`analyze()`: multi_modal_fusion, seven_dim_awareness, temporal_mesh
(reads provisioned forecasters), geopolitical_intel, red_team
(injection/degenerate checks on emits), options_greeks (real BSM),
portfolio_mpt (risk-parity from real closes), tca (fills ledger),
voice_interface (text->operator_cli), federated_learning, 
regulatory_compliance (real ledger reads + nsr chain verify),
energy_optimization (measured cycle cost). Every capability returns
confidence: measured|partial|unprovisioned — honest bounds, never
simulated. CSC_MANIFEST advisory; discovery wires at SHADOW.
Tests: tests/foundation/test_expansion_capabilities.py (7 tests).

## Autonomous FI loop + L2 order-book eval (2026-11-12)

M1-M5 infrastructure (live, advisory-only): `scripts/method_eval.py`
(spec -> bounded candidate -> net-of-cost verdict -> `var/methods/ledger.jsonl`),
`scripts/autonomous_cycle.py` (6h unattended loop: catalog -> data probes ->
internet scout -> method evals -> edge_research -> `var/reports/*.md`),
`scripts/build_catalog.py` -> `var/data_catalog.json` (consumed by
`paper_runner --universe auto` when <24h fresh), `scripts/intel_report.py`
(one-command status across all ledgers), `scripts/edge_research.py`
(bounded hypothesis queue, all results ledgered).

M6 — Binance Futures UM L2 suite (`data.binance.vision` keyless archives;
spot has NO bookDepth, UM does: bookDepth/bookTicker/metrics/liqSnapshot;
filename `BTCUSDT-<kind>-YYYY-MM-DD.zip`). Bounded week 2024-01-01..07 in
`var/l2data/` (~13MB total after deleting the 50MB aggTrades csv — klines
cover price; retention policy is pull-analyze-keep-small-derived).
Schemas: bookDepth = `timestamp,percentage,depth,notional` (depth by
%-band, bids negative, snapshots ~30s, NOT top-of-book L2); metrics =
5min OI + toptrader/retail long-short ratios + taker vol ratio.
H5 depth_imbalance and H6 positioning_metrics are in edge_research.py
(--only works). Verdicts on the week: both FAIL.

CRITICAL eval lesson (third time this pattern appeared): pooled
edge stats on overlapping forward windows are inflated mirages —
pooled top-decile depth-imbalance edge looked like +21.6bps net
(+16.6bps over ~5bps UM taker RT), per-day split showed
+36.9/+34.6/+31.6/-4.4/-51.5/-9.1/-6.8 = mean +4.5bps, 3/7 days.
Same for positioning fade: pooled -31..-36bps spread -> per-day
-11.3/-5.5bps. The honest unit is the per-day edge; ~300 extreme
"samples"/day are really 2-12 clusters. Never verdict on pooled
overlapping-window means.

HF dataset `venvoo/china-a-share-l2-*` is GATED (401, no token) —
catalog listing is public but files need credentials; recorded, not faked.

M7 additions (same protocol): H7 bookticker_microprice streams the
128MB/day UM bookTicker zip -> 1s resample (~4MB kept). Measured real
BTCUSDT-perp quoted spread = 0.02bps median (1 tick); microprice imb
edge +0.7bps@60s vs fees+spread ~5.02bps -> FAIL. H8 premium_basis on
premiumIndexKlines: the STRONGEST anomaly found — premium mean-
reversion corr -0.37..-0.70 all 7 days, fade edges positive 7/7, but
mean +2.69bps < cost -> FAIL (structural funding-pull, sub-cost).
liquidationSnapshot is NOT in Vision archives (API-only) — recorded.

H8 extended to full month x 3 perps (2024-01, ~3MB total): the
premium fade is positive 93/93 days (BTC +3.02, ETH +2.89, SOL
+4.55bps, agg +3.49) — most stable anomaly found, but harvesting is
the 2-leg basis trade (short perp + long spot); std-tier cost ~30bps
RT, maker+BNB ~18bps — still sub-cost. This IS the textbook funding
arb; it lives at VIP fee tiers, not here. Robust FAIL.

## Multi-symbol buffer poisoning — recurring bug class (2026-11-12)

Second instance (first was `_price_window`): `RVBlendForecaster` kept
ONE shared `rows`/`feats` deque while `merged_symbol_observations`
interleaves EURUSD/GBPUSD obs. Returns computed across symbol
boundaries (~15% price jumps) poisoned every feature: GRU stayed
plausible (-0.53) but the ridge head emitted -191, blend -> vol_mult
~1e-42 -> sizing silently zeroed. Fixed: rows/feats are now dicts
keyed by obs['symbol'] (verified: interleaved feed gives ridge
+0.54/+0.45, mult ~1.65). RULE: any rolling buffer fed by a merged
multi-symbol stream MUST be keyed by symbol — check for this first
whenever an advisory model emits degenerate values on multi-symbol
runs but tests fine single-symbol.

## Maker paper execution mode (2026-11-12)

Every hypothesis verdict bottomed out at "sub-taker-cost" — the paper
venue only modeled market orders. Maker mode exists now:
`paper_runner --paper-order-style maker --maker-offset-bps 3
--maker-ttl-bars 4 --maker-fee-bps 2`. Entry TRADE_EXECUTIONs become
passive LIMITs (bridge, `order_style`/`maker_offset_bps`; position_close
stays MARKET — flattening must not wait). `MakerPaperAdapter`
(brokers/maker_paper_adapter.py) subclasses the protected
PaperBrokerAdapter: mark-TTL expiry (stale limits die, not fill later),
bps-of-notional maker fee. paper_runner feeds on_mark low->high->close
per bar so limits fill on intra-bar touches; `_sync_maker_reports`
pushes resting->filled/expired transitions into the repository
(service.submit only persists submit-time reports — without the sync,
maker fills never reach the ledger). Verified: buy limit rests ->
fills at exact limit on touch, fee=qty*px*fee_bps, TTL->expired.

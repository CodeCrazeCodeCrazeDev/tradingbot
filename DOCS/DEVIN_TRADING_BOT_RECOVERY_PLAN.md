# Devin runbook: make the canonical trading bot observable, reliable, and evidence-driven

Status: investigation and execution plan, **not a claim of profitability or a live-trading authorization**. Reviewed 2026-10-09 against the current worktree. Read `AGENTS.md` first. The phrase "run like other AI" is not a testable target: use the acceptance criteria below instead. This is not an exhaustive diagnosis of every module in the repository; classify new discoveries as *verified by code/test/runtime evidence*, *historical evidence*, or *hypothesis to test*.

## Rules for the next Devin session

- Work only in `C:\Users\peterson\trading bot-merge-six`. Preserve existing uncommitted changes; inspect `git status` and diff before editing. In particular, `trading_bot/ai_stack.py`, `trading_bot/core/hms/*`, `trading_bot/foundation/runtime.py`, `trading_bot/cognition/advisory_adapter.py`, and `DOCS/CANONICAL_RUNTIME_DATAFLOW.md` were already modified at review time. Never overwrite these blindly.
- Use **one** capital path: `UnifiedTradingBot` -> CSC -> canonical risk -> shield -> human governance -> LogAct -> canonical execution. Respect the `ProtectedPathGuard` restrictions in `AGENTS.md` for RSI candidates. Do not route legacy bots, research agents, or advisors directly to execution.
- Do not disable guardrails, reduce costs, inflate confidence, auto-reset emergency stops, forge market data, or force trades merely to increase activity. **Do not connect to MT5, run `mt5_demo_runner.py`, or send demo/live orders without the operator's explicit authorization for that action.** Never use the previously exposed MT5 credentials; do not print secrets.
- Start with read-only inspection and isolated **offline** paper runs in a fresh state directory, after checking disk space. Read old logs and reports as clues, not as current proof. Put each finding, reproduction, change, test result, and remaining blocker in a final report. If a safety check fails, stop and request operator action rather than bypass it.

## Verified findings and likely causes of the perceived behavior

| Priority | Finding (evidence) | Consequence / action |
|---|---|---|
| P0 | `main.py:91-113` starts `ModularMonolithRuntime` but does **not** call `build_cognitive_system`; `scripts/mt5_demo_runner.py:70-103` likewise does not. The paper runner explicitly assembles advisors and research at `scripts/paper_runner.py:140-155`. `foundation/runtime.py:70-95` only adds `AdvisoryCognitiveBrain` when `enable_cognitive_advisory` is set. | Different entrypoints run different AI stacks. Verify at runtime using the read-only advisory report; design a single idempotent assembly seam for the canonical entrypoints, test before/after, and avoid double registration or demo side effects. Do not equate additional attached modules with better trading. |
| P0 | The repo `.venv` has `pytest` but **no `torch`** (checked with `importlib.util.find_spec`); `unified_bot.py:97-128` imports/constructs `WorldModelV2` on start. `AGENTS.md:40-50` documents the separate Hermes environment. | A full run using `.venv` cannot start as configured. Use `.venv` for lightweight tests; verify the required dependencies in the documented Hermes environment before attempting an authorized full paper run. Do not change dependency/security policy to paper over errors. |
| P0 | `scripts/paper_runner.py:4-13,179-183` is offline paper-only, synthetic or database replay; `main.py:8-16,107-110` also replays history or synthetic data. `scripts/mt5_demo_runner.py:9-17,97-153` consumes live terminal M15 data. | An offline replay is not a continuously market-connected trading AI. First establish a reproducible paper run; distinguish *bot is running*, *a decision was made*, *an order filled*, and *a positive net edge was demonstrated*. Do not switch to demo execution to disguise a paper issue. |
| P1 | Only EURUSD ~1,000 real historical bars are documented in `AGENTS.md:24-25` and `RSI_CURRENT_STATE_AUDIT.md:72-76`. `main.py:41-54` raises if the requested symbol has no rows. Synthetic prices are labeled synthetic. | Other instruments or robust generalization cannot be inferred from this dataset. Inventory quality, timestamp interval, duplication, spread/cost data, and lookahead before training or claiming AI performance; acquire authorized multi-regime data if needed. |
| P1 | `unified_bot.py:426-475` rejects invalid observations, needs ~15 closes for RSI, and returns before CSC when the human layer is absent/paused. `controller.py:2301-2358` has guardrails and optional cadence abstentions. `controller.py:1806-1855,255-273` downgrades unprofitable-after-cost proposals to HOLD and caps churn. `foundation/runtime.py:162-208` emergency-stops on reconciliation failure. | No orders can be the *correct* outcome. Inspect per-cycle counts and exact rejection reasons before changing strategy or infrastructure. Preserve safety controls. Do not assume the historical `-4.4%`/443-fill note in controller comments is a measurement from this session. |
| P1 | `mt5_demo_runner.py:193-197` requires explicit `--auto-approve` for unattended demo approval; otherwise an operator decision is required. `mt5_preflight.py:190` defaults to `var/paper/trading_state.db`, while the demo runner defaults to `var/mt5_demo` (`mt5_demo_runner.py:39,74-83`). | Preflight may compare against the **wrong ledger** unless `--state-db` targets the matching demo state. Correct the default/explicit operational guidance and test that mismatch is detected; never reset an emergency flag to hide a reconciliation difference. |
| P1 | `mt5_preflight.py:194-199` uses a self-attested `--authorize-connect` flag; `brokers/mt5_demo.py:190-206` can attach to an existing demo terminal session if credentials are absent. Demo-only account validation still exists at `mt5_demo.py:243-269`. | The flag does not cryptographically prove credential rotation. Operator must independently verify account identity and rotation before any authorized connection. Do not treat a successful preflight as proof of profitability or credential provenance. |
| P1 | `mt5_demo_runner.py:112-123` replays *historical* bars through `run_cycle` using a demo execution adapter; `:125-138` also runs follow-mode warmup bars through the same path. | **Never use `--replay` as an offline dry-run.** Historical bars in either mode can reach the order path if approvals are granted. Move warmup/replay validation to a non-executing path and add tests proving they cannot send orders before using them operationally. |
| P2 | `advisory.py:5288-5322` constructs and probes individual services, logging skipped factories; `controller.py:1196-1246` times out failing advisors and disables one after five consecutive failures. Advisors only tilt selection (`controller.py:1286-1321`); they cannot authorize orders. `DOCS/CSC_WIRING_AUDIT.md:119-176` reports optional analyzers that skip without dependencies. | Many AI-named modules need not be running, and some may be warming, skipped, or emitting nondirectional evidence. Record actual attached/skipped/disabled counts, directional contributions, and measured accuracy by regime; fix proven dependency/input bugs only. |
| P2 | `controller.py:1008-1102` scores approved predictions at position settlement; research is scheduled periodically at `controller.py:2231-2263`. `foundation/runtime.py:107-145` wires RSI memory but **does not auto-run or promote** the RSI cycle. `RSI_EXPERIMENT_LEDGER.md:16` says no real candidate has cleared promotion. | "Self-improvement" does not mean autonomous parameter deployment. Keep promotion operator-authorized and evaluate on sealed out-of-sample data with realistic costs and fills. |
| P2 | `controller.py:1262-1264` seeds its recurrence projection with Python `hash(...)`, which is process-randomized by default. | *Potential* replay nondeterminism across processes: test identical observations under different `PYTHONHASHSEED` values and compare decisions/state before changing the seed derivation. |

Historical audit documents may describe obsolete architectures (`IMPLEMENTATION_GAP_AUDIT.md:3-27` contains a later status addendum contradicting its older `:29-44` verdict). Prefer the live code, fresh test output, and the new per-run audit data. There is **no verified evidence here** that current trading has a durable positive net edge.

## Execute in order (do not skip the evidence gates)

### 1. Define and reproduce the actual symptom (offline)

- Ask which command/interpreter/state directory/symbol/mode the operator uses and whether the symptom is a startup error, no decisions, no fills, missing advisors, losses, or missing learning. If unspecified, use the canonical paper runner with synthetic EURUSD in a **new** state directory; do not modify or reuse existing `var/mt5_demo` or `var/paper_run` state.
- Capture environment identity (`python --version`, interpreter path, import availability, disk space), `git status`, current logs, and read-only snapshot. Avoid dumping `.env`, MT5 account identifiers, credentials, or full order payloads. For tests from `.venv`: `.venv/Scripts/python.exe -m pytest tests/foundation/test_runtime_data_boundary.py tests/foundation/test_runtime_reconciliation_gate.py -q --no-cov -p no:cacheprovider`. On review these passed **10/10**; that proves the isolated gates, not full startup.
- Under the authorized full-runtime interpreter, run a small offline paper sample, e.g. `python scripts/paper_runner.py --source synthetic --cycles 40 --interval 0 --state-dir var/paper_diagnostic_new`. Check `snapshot.json`, `decision_log.jsonl`, and read-only `audit_events`/orders/fills/positions in that same state directory. Save cycle counts, `ABSTAIN` / `TRADE_REJECTED` / `TRADE_APPROVED`, top `dominant_rejection_reason` or audit `details.reason`, attached/skipped/disabled advisors, execution and reconciliation results. Use `scripts/operator_cli.py --state-dir <same-dir> status` for controls. If startup fails, record the first exception and fix that root cause before tuning decisions.

### 2. Reconcile entrypoints, data, and observability

- Add focused failing tests for assembly behavior in `main.py`, paper runner, and demo runner **with a fake adapter** (no terminal, no orders). Move assembly to a single lifecycle point if tests show inconsistent advisor/research registration, while retaining exactly one CSC, shield voter, risk authority, and executor. Expose attached/skipped/disabled counts and per-cycle advisory contribution in a read-only snapshot for **each** entrypoint. Keep user-modified `runtime.py`/AI-stack work intact.
- Test restart with an isolated paper state: persisted pause/estop, durable order recovery, position restoration, decision log, advisor outcome scoring, and reconciliation must survive. `scripts/paper_runner.py:132-174,237-255` has custom history/position restore and flush; verify ledger agreement rather than assuming it.
- Add fixture-based tests that malformed/stale/out-of-order/duplicate bars are rejected or handled explicitly, feature warmup is visible, and timestamps/features are causal. Test seeded synthetic replay repeatability across subprocesses if the recurrence hash is relevant. Do not claim synthetic runs are real-world evidence.

### 3. Explain activity and establish a real edge

- Produce a stage funnel: observations -> normalized -> guardrails -> directional advisor calls -> candidate branches -> verified proposals -> net-cost eligible -> risk-sized -> shield/governance/bus approved -> orders -> fills -> settled outcomes. Quantify latency and failures at each stage. Investigate top abstain/rejection reasons, warmup, market-data quality, missing dependencies, optional advisor probe skips, cadence, cost calibration, churn, approval state, and venue minimums **one at a time**. Do not turn off any gate merely to raise the trade count.
- Compare a simple baseline to CSC and to selective advisory ablations on chronological, embargoed walk-forward splits; include spread, fees, slippage, FX notional/volume grid, position holding, and failed/unknown orders. Report net return, drawdown, turnover, calibration (ECE/Brier), advisor precision per regime, and uncertainty/confidence intervals. Use multiple independent market regimes/instruments before any generalization claim; mark 1,000-bar EURUSD results as exploratory only. Do not promote RSI candidates or retrain on the holdout.

### 4. MT5 demo readiness — requires a separate operator decision

- First implement tests using a fake MT5 client. Make preflight explicitly compare the same `--state-db` as the selected demo state dir and report session mode/ledger mismatch without modifying the ledger. Test that neither `--replay` nor `--follow` warmup can issue demo orders, that follow mode uses only closed bars and receives approvals correctly, and that denied/missing credentials, a non-demo account, market closed, unavailable symbol, failed reconciliation, and persisted estop all fail safely.
- Only after the operator confirms **rotated demo credentials, account identity, and explicit permission to connect**, run the read-only `scripts/mt5_preflight.py --authorize-connect --state-db <matching-demo-state-dir>/trading_state.db` in the Hermes environment. The script currently can attach to an existing demo session; inspect `session_mode`. Never run the demo runner or `--auto-approve` as part of this runbook without a separate explicit approval. Live funded trading is out of scope.

## Completion criteria for Devin

1. A documented, reproducible offline paper run reaches CSC and writes a snapshot plus durable audit rows; no startup exceptions or unexplained silent skips.
2. Entry-point comparisons prove which advisory/research features are attached in each mode; missing features are deliberately unified or explicitly documented with passing tests.
3. Every observed "no trade" interval has an auditable cause; any trade and fill match the ledger and remain subject to risk, shield, human controls, consensus, and reconciliation.
4. Out-of-sample net-of-cost results are reported honestly; if evidence is insufficient or negative, say so and **do not** declare the bot ready or loosen gates.
5. Demo execution remains disabled until separate operator authorization and successful read-only, matching-ledger preflight. Publish remaining blockers and exact test commands/results; don't claim production readiness on paper tests alone.

## Implementation pass — 2026-10-09

### Changes implemented

- Canonical cognitive assembly is now requested through `cognitive_assembly` runtime config by `main.py`, `scripts/paper_runner.py`, and `scripts/mt5_demo_runner.py`. `ModularMonolithRuntime` invokes `build_cognitive_system` once, using the public `discover_advisors` option; `attach_advisory_modules` records attached/skipped assembly results and `advisory_report()` exposes them under `assembly`.
- CSC advisory registration is idempotent by `capability_id`. Advisor outputs remain advisory evidence only; the CSC remains the sole decision authority.
- `CognitiveSystemController.process_market_observation` now persists every terminal pipeline decision through the configured decision sink as `DECISION_TERMINAL`, including `TRADE_REJECTED` outcomes, rejection reasons, symbol, and advisory evidence IDs. Rejections are also recorded as reflective failures when HMS reflection is available.
- The DiscoLoop projection seed now uses deterministic SHA-256 material instead of process-randomized `hash()`.
- The runtime wires an HMS/RSI reflective bridge and exposes a read-only `reflection` plane through the AI-stack projection. This is evidence plumbing only; it does not promote RSI candidates or bypass operator authorization.
- `mt5_demo_runner --replay` now uses a non-executing `analysis` runtime and connects MT5 separately as a data feed. Follow-mode warmup seeds closed-bar history instead of sending historical bars through live decision/execution paths. Snapshots report replay boundary, advisory assembly, and AI-stack summaries.
- `mt5_preflight.py` defaults its ledger to `var/mt5_demo/trading_state.db` so the default ledger matches the demo runner's default `--state-dir`. The explicit `--state-db` override remains available.
- `MT5DemoAdapter` now fails closed when credentials are missing unless `current_session` is explicitly selected. This removes the accidental "attach to whatever terminal session is open" fallback; DEMO-only account validation still applies to explicit current-session mode.
- Added focused regression coverage in `tests/foundation/test_recovery_plan.py` for assembly reporting/idempotence, terminal audit persistence, canonical runtime config, replay non-execution, warmup seeding, snapshot observability, and deterministic projection.

### Verified commands and results

```bash
.venv/Scripts/python.exe -m pytest \
  tests/foundation/test_runtime_data_boundary.py \
  tests/foundation/test_runtime_reconciliation_gate.py \
  tests/foundation/test_recovery_plan.py \
  -q --no-cov -p no:cacheprovider
# 17 passed

.venv/Scripts/python.exe -m pytest \
  tests/brokers/test_mt5_demo.py \
  tests/foundation/test_recovery_plan.py \
  -q --no-cov -p no:cacheprovider
# 34 passed — fake-client checks cover demo-only enforcement, missing
# credentials, unavailable/closed symbols, stale ticks, volume grid,
# reject/UNKNOWN mapping, idempotent resubmission, positions, and drift.

.venv/Scripts/python.exe -m pytest \
  tests/foundation/test_execution_recovery.py \
  tests/foundation/test_wave3_execution_persistence.py \
  tests/foundation/test_runtime_reconciliation_gate.py \
  -q --no-cov -p no:cacheprovider
# 28 passed — durable order recovery, ledger snapshots, audit-failure veto,
# and reconciliation-driven emergency stop remain green.

"$LOCALAPPDATA/hermes/hermes-agent/venv/Scripts/python.exe" \
  scripts/paper_runner.py --source synthetic --cycles 12 --interval 0 \
  --research-interval 0 --state-dir var/devin_recovery_postfix \
  --log-level WARNING
# exit 0; no MT5 connection; no broker orders

"$LOCALAPPDATA/hermes/hermes-agent/venv/Scripts/python.exe" \
  scripts/paper_runner.py --source synthetic --cycles 6 --interval 0 \
  --research-interval 0 --state-dir var/devin_recovery_postfix \
  --log-level WARNING
# restart pass on the same state: exit 0; persisted history recovered
```

The first Hermes paper diagnostic completed 12 synthetic cycles and published `var/devin_recovery_postfix/snapshot.json`. The snapshot reported `cycles=12`, `advisor_attached=157`, `assembly_attached=156`, `assembly_skipped=0`, and AI-stack planes `state`, `evidence`, `selection`, and `reflection`. A 6-cycle restart pass on the same state recovered `market_history.json` (18 closes), ran 6 more cycles, and left durable totals of 18 `DECISION_TERMINAL` rows (14 `TRADE_REJECTED`, 4 `ABSTAIN`), 4 additional `DECISION/ABSTAIN` rows, 4 matched `execution_recovery` rows, and 4 reconciliation runs. Orders, fills, and positions remain zero. Terminal rows carry auditable reasons: 14 `Failed Pivot/Refine loop: High-confidence VETO by MarketStructureVerifier: FALSIFIED: no measured volatility/trend/regime feature evidence.` and 4 `Abstain: verified WAIT decision, quantity=0.0.`

### Remaining blockers / non-claims

- This pass does **not** prove profitability, production readiness, or a live edge. The only verified runtime result is a safe synthetic paper run with auditable rejections.
- Several optional advisory components still emit runtime errors after attachment (for example `volatility_impulse`, `market_intelligence`, and unfitted adaptive-learning models). These should be triaged individually as advisory evidence-quality issues; do not remove safety gates to hide them.
- The rejection reason is currently evidence-driven, but the missing measured feature evidence and early-window behavior still need a dedicated funnel report before changing strategy logic.
- A short same-state restart is verified, but a longer paper soak, broad walk-forward performance evidence, and operator-authorized read-only MT5 preflight remain pending. Fake-client adapter and replay boundary coverage is green, but it is not a substitute for the authorized terminal preflight.
- No MT5 terminal was connected by this implementation pass, no demo/live order was sent, and no credential was used or printed.

## Implementation pass 2 — stage funnel + advisory input fixes (2026-10-09)

### Changes implemented

- `CognitiveSystemController` now maintains an ordered per-process stage funnel (`self._funnel`) counted at every pipeline boundary: observations, cadence, perception, evidence items, guardrails, advisory artifacts, directional advisor calls, hypothesis branches, pivot/refine terminals, verification (+terminals), synthesis, net-cost downgrades, directional proposals, risk/shield/governance checks (+terminals), consensus rejections, churn/nondirectional abstentions, terminal outcomes, and settled positions. `funnel_report()` exposes it; `paper_runner` and `mt5_demo_runner` snapshots publish it under `funnel`.
- Fixed proven advisory input bugs (evidence-quality only; no gate changed):
  - `volatility_impulse`: wrapper passed a `list` where `detect_volume_surge` requires `pd.Series` — now passes a Series and reports last/max surge ratio.
  - `_BarHistory`: bars now carry a numeric `time` field (observation timestamp when numeric, else bar index) so analyzers computing time-deltas (`price_action`) work.
  - `analysis/market_intelligence.py`: `_run_*` sub-analyzers now return quiet `{}`/`[]` when the underlying module is absent or lacks the called method; `MarketRegimeDetector`/`OrderFlowAnalyzer` are constructed with their real ctor signatures (a config dict was being passed into positional numeric args — `lookback_period`/`imbalance_threshold` became `None` and every call raised `TypeError`); `detect_regime` is now fed via `update()` then called no-arg; `analyze_flow` -> `analyze_delta` with summarized output; the wrapper now passes a DataFrame (the documented input type), not a dict.
  - `adaptive_learning_predict`: checks `check_is_fitted` before calling `predict` — untrained models now report `"untrained"` instead of logging ERROR every cycle.
  - `analysis/anomaly_detection.py`: `fillna(method='ffill')` -> `.ffill()` (removed in pandas 2).
  - `institutional_entry/wyckoff_ict_fusion.py`: volume-profile dict is keyed by bin index — float-midpoint keys (`low + size/2` vs `(bins[:-1]+bins[1:])/2`) rounded differently and raised `KeyError(np.float64)`.
- `EvidenceGate` rejections in `verification/swarm.py` demoted ERROR -> WARNING: a veto is a normal decision outcome, not a system fault. No gate semantics changed.

### Verified commands and results

```bash
.venv/Scripts/python.exe -m pytest \
  tests/foundation/test_runtime_data_boundary.py \
  tests/foundation/test_runtime_reconciliation_gate.py \
  tests/foundation/test_recovery_plan.py \
  tests/foundation/test_execution_recovery.py \
  tests/foundation/test_wave3_execution_persistence.py \
  tests/brokers/test_mt5_demo.py \
  -q --no-cov -p no:cacheprovider
# 70 passed

# 60-cycle soak (pre-fix baseline)
hermes-python scripts/paper_runner.py --source synthetic --cycles 60 \
  --interval 0 --research-interval 0 --state-dir var/devin_soak_funnel \
  --log-level WARNING

# 25-cycle verification (post-fix)
hermes-python scripts/paper_runner.py --source synthetic --cycles 25 \
  --interval 0 --research-interval 0 --state-dir var/devin_funnel_verify3 \
  --log-level WARNING
```

Post-fix 25-cycle funnel (`var/devin_funnel_verify3/snapshot.json`):

| Stage | Count |
|---|---|
| observations / perception / guardrails / verification | 25 |
| evidence_items | 250 |
| advisory_artifacts | 3,999 |
| advisor_directional_calls (BUY/SELL only) | 57 |
| hypothesis_branches | 100 |
| verification_terminal (warmup vetoes) | 14 |
| synthesis | 11 |
| **directional_proposals** | **0** |
| risk_check / shield / governance | 0 |
| nondirectional_abstain (verified WAIT) | 11 |
| orders / fills / settled positions | 0 |

Advisory-channel error lines dropped from **152 → 28** per comparable run, and the remaining 28 are legitimate EvidenceGate vetoes (now WARNING, not ERROR). Zero unhandled advisor crashes after the input fixes.

### What the funnel answers about "no trades"

The no-trade outcome is **not** an infrastructure failure: every observation reaches verification, ~14 warmup cycles are vetoed for missing measured feature evidence, and every cycle after warmup synthesizes a **verified WAIT** (`directional_proposals: 0`). Advisors do emit directional calls (57 in 25 cycles), but the hypothesis/simulation layer does not promote any to a directional proposal on this mean-reverting synthetic series — so the net-cost gate, risk service, shield, governance, and the execution bus are never reached. This is consistent with correct abstention on directionless data; it does NOT establish that the same boundary would hold on trending real data.

### Remaining blockers / non-claims (updated)

- Verified bottleneck is now measured, not guessed: decisions terminate at warmup verification or verified-WAIT synthesis. Whether directional proposals ever emerge requires trending/multi-regime input (real `market_data.db` replay or a regime-mixed synthetic spec) — a legitimate next diagnostic, not a gate to loosen.
- `adaptive_systems.market_regime` reports "Insufficient data for regime detection" through 60+ accumulated bars — likely an internal lookback larger than the window or a separate warmup contract; low priority since it degrades to warning-only evidence.
- `order_flow.analyze_delta` still logs a handled error path when no bid/ask footprint exists (estimates from price action internally); evidence is degraded but not fabricated.
- Broad walk-forward net-of-cost evaluation, multi-instrument/multi-regime data, and operator-authorized MT5 preflight remain pending. Nothing here claims profitability or live readiness.

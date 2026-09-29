# MEGAPLAN — AlphaAlgo First-Principles Unfinished-Work Inventory & Roadmap

**Snapshot:** commit `e9efee2b9fe63b2105e1ef5d51a241b2c1a54693` + working-tree
edits of 2026-09-28 (Wave A+B implemented), Python 3.11.15 (win32). Disk freed
to ~6 GB. Rows marked **FIXED 2026-09-28** are verified by the tests/runs
listed; re-run §1 before quoting.

**Update 2026-09-28:** Wave B landed — two capital-path fail-open defects are
now closed (MP-041, MP-042) with regression tests, and every launcher/deploy
file was repaired to the canonical `main.py` paper entry (MP-001..MP-009
partially resolved — see table). New P0 rows added: tracked credentials
(MP-040, **operator action required: rotate first**), divergent legacy API
stacks (MP-043), production-compose missing mounts (MP-044).

**Authority:** this document supersedes the status claims of all prior audit
docs where they conflict. Prior docs are treated as *claims to re-verify*,
not evidence. A finding is `CONFIRMED` only when it was reproduced or the
code path was read at this commit; `DOC-REPORTED` means cited but not
independently re-proven here; `BLOCKED` means an external input is missing.

---

## 1. Verified state of the world (what actually works today)

| Check | Result | Evidence |
|---|---|---|
| `import trading_bot` | **OK** (~seconds, lazy exports) | ran 2026-09-27 |
| `main.py --cycles 2` | **OK** — CSC → VerificationSwarm → LogAct APPROVED → `PaperExecutionBridge` fills, clean shutdown | ran; `uca_brain.log` |
| `tests/rsi` | **70/70 pass** in 65 s | ran |
| v1 RSI regression (`tests/foundation/test_rsi_*` + `tests/recursive_self_improvement`) | **19/19 pass** in 34 s | ran |
| `find_spec` on `foundation.runtime`, `unified_bot`, `csc.controller`, `risk.service`, `execution.service`, `immutable_shield`, `recursive_self_improvement`, `evaluation`, `self_awareness` | **all FOUND** | ran |
| `main.py --timeframe M15` | **FAILS** — `unrecognized arguments` | ran (argparse exit 2) |
| Full `pytest` suite (3,510 test files) | **UNVERIFIED** — disk too small, last logged run timed out | `suite_run2.log` ends in Timeout |
| `rsi_synthetic_benchmark.py --seeds 20` | **NOT RUN** | planned Wave 1 gate |

| `main.py --synthetic --cycles 2` post-fix | **OK** — human layer wired, shield APPROVED, paper fills, clean shutdown | ran 2026-09-28 |
| `tests/core/test_unified_decision_bus.py` + `tests/foundation/test_runtime_data_boundary.py` | **13/13 pass** (incl. new fail-closed regressions) | ran 2026-09-28 |
| `python -m trading_bot.main --help` | **OK** — delegates to root `main.py` argparse | ran 2026-09-28 |
| `tests/core/test_architectural_verification.py` | **3/3 pass** after health-endpoint `_archive` import fix | ran 2026-09-28 |
| `tests/core`+`foundation`+`rsi` broad run | 1,753 collected; all completed groups green EXCEPT `test_dependency_manager` hit the 180 s pytest timeout inside a slow `transformers` import (environmental, pre-existing) | ran 2026-09-28 |

**First-principles verdict (revised):** the *research/paper core* is alive and
the RSI machinery is genuinely fail-closed where tested. But the audit found
the *capital boundary itself* had two fail-open holes (voter timeout →
APPROVED; missing/throwing human override → trade allowed) that the prior
"0 open weaknesses" registers never detected — both now closed and
regression-tested. Deployment surfaces were all broken as documented and are
now repaired to the single verified path; container build still unverified
(docker unavailable here) and credentials rotation remains an operator task.

---

## 2. First-principles requirements this system must satisfy

Derived from the code's own architecture (one brain, veto chain, evidence
ladder) — not from README claims:

1. **One decision authority** per live path: `UnifiedTradingBot` → CSC → shield
   → bus → execution. Parallel brains/orchestrators must be advisory-only or
   dead. *(Mostly true on the main path; ~172 `*Orchestrator` classes were
   inventoried in `IMPLEMENTATION_GAP_AUDIT.md` — doc-reported; disconnected
   classes remain — classify, don't claim they're wired.)*
2. **Fail-closed capital path:** execution modes outside `paper`/`analysis`
   are already refused (`unified_bot.py:90-94`). Any live path must route
   through `CanonicalRiskService` + `ImmutableShield` + human approval.
3. **Reproducible entry points:** every command in README/Procfile/Docker/
   railway/render must resolve to an existing file and valid args.
   *Currently broken everywhere — see P0.*
4. **Evidence honesty:** no promotion, release "GO", or Sharpe claim without
   paired point-in-time replay, measured costs, multi-instrument data, and an
   operator-signed holdout. *The RSI machinery enforces this; the legacy
   release reports violate it in text only.*
5. **Data grounding:** 1,000 EURUSD bars is the entire real dataset —
   synthetic fixtures are engineering evidence, never alpha.
6. **Preservation:** archived/generated code is triaged, not silently deleted;
   protected paths (`risk/service.py`, `immutable_shield.py`,
   `execution/service.py`, `unified_bot.py`, `main.py`, RSI
   contracts/evaluator/archive) are never relaxed.

---

## 3. Issue registry

### P0 — deploy/entry surface repairs (status as of 2026-09-28)

| ID | Surface | Breakage | Status |
|---|---|---|---|
| MP-001 | `Procfile` worker, `railway.json`, `render.yaml` | `--timeframe M15` → argparse reject | **FIXED** — all now use `python main.py --mode paper --symbol EURUSD` |
| MP-002 | `Procfile` web, `render.yaml` web | `trading_bot.api.api_server` does not exist | **FIXED (by removal)** — web services dropped/disabled; do NOT re-add without a vetted read-only API (MP-043) |
| MP-003 | `Dockerfile` | `COPY run_unified_bot.py` → wrong path; CMD pointed at legacy launcher | **FIXED** — copies real files only, CMD = `main.py --mode paper` |
| MP-004 | `Dockerfile.production` | `COPY main_production.py` absent; healthcheck curled a nonexistent HTTP server; dev stage ran tests that weren't copied | **FIXED** — CMD = `main.py`; psutil process healthcheck; dev stage now COPYs `tests/` + `pytest.ini` |
| MP-005 | `docker-compose.yml` test service | `test_bot_comprehensive.py` absent | **FIXED** — runs `main.py --synthetic --cycles 3` smoke; trading-bot mounts `market_data.db` read-only |
| MP-006 | `pyproject.toml` console script | `trading_bot.main:main` absent | **FIXED** — new thin `trading_bot/main.py` delegates to root `main.py` (single source of truth) |
| MP-007 | Root `api/` package | `api/__init__.py` imports nonexistent `APIServer` → import-dead | **OPEN (by design)** — left dead; exposing it would resurrect a default-secret JWT + placeholder order path (MP-043) |
| MP-008 | `README.md` quickstart | thinking-bot files/flags missing; bogus `--timeframe/--bars/--use-ml` flags | **FIXED** — hero + Quick Start rewritten to verified commands |
| MP-009 | `START_HERE.md` | Option 4 → missing `run_full_autonomous_system.py` | **FIXED (annotated)** — Option 4 marked BROKEN; status banner added. *Correction:* `RUN_DEMO.bat`→`examples/autonomous_superintelligence_demo.py` and `RUN_AUTONOMOUS_*.bat`→`autonomous_superintelligence_launcher.py` DO exist (earlier row was wrong); launchers unverified at runtime |

*Remaining gap: `config/docker-compose.yml` credentials (MP-040) and any
container image build are not yet executed — docker build is the Wave-1 gate.*

### P0 — capital-path fail-closed defects (FOUND 2026-09-28, FIXED)

| ID | Defect | Root cause | Status |
|---|---|---|---|
| MP-041 | `UnifiedDecisionBus` voter timeout → `{"decision": "ERROR"}` was not in the veto set, so `TRADE_EXECUTION` could reach `APPROVED` + dispatch with its mandatory shield voter dead. Dispatch also swallowed handler exceptions (`gather(return_exceptions=True)`) leaving phantoms APPROVED | consensus = "no veto seen" instead of "affirmative shield report received" | **FIXED** — `_check_consensus` now requires an affirmative shield decision for `TRADE_PROPOSAL/TRADE_EXECUTION/ORDER/EXECUTE` (ERROR/abstain/malformed → VETOED); subscriber crashes/rejections mark shielded actions `FAILED` (EXECUTED fills stay EXECUTED). Non-capital timeout-approve semantics preserved. Tests: `test_shielded_action_*` ×4 |
| MP-042 | `UnifiedTradingBot.trading_allowed()` returned `True` when the human layer (manual pause / emergency stop) was absent or threw — the override boundary could silently vanish | optional-layer wiring treated absence as consent | **FIXED** — missing layer or raising check now denies the cycle (fail-closed). Exits/cancels route through `ManualOverride` service, not this gate. Tests: `test_runtime_denies_entries_when_*` ×3 |

### P0 — security incident (operator action required FIRST)

| ID | Item | State |
|---|---|---|
| MP-040 | `config/docker-compose.yml` lines ~10-15,42-47 contained **tracked hard-coded broker credentials** (login/password/investor/server), introduced in initial commit `95721498` — values not reproduced here | **WORKING TREE CLEANED 2026-09-28; ROTATION PENDING**: file rewritten without any `MT5_*` or credential values; root compose no longer forwards `MT5_*` to the paper worker; production compose no longer injects `.env` into the worker. Regression tests `test_paper_compose_services_carry_no_broker_credentials` / `test_legacy_config_compose_resolves_repo_root` guard all three files. **Still required — operator, not code**: (1) rotate/revoke trading+investor credentials via the broker NOW (deleting the file does NOT purge git history `95721498` or old image layers — `Dockerfile` copies `config/`); (2) inventory prior images/clones/registry pulls; (3) history rewrite/remote coordination — separate explicit approval; (4) secret scanning (gitleaks/detect-secrets) as a commit gate |

### P0 — divergent API/launcher stacks (NEW)

| ID | Item | State |
|---|---|---|
| MP-043 | Two incompatible API implementations exist and deploy configs referenced a third, nonexistent one: root `api/api_server.py` (default `JWT_SECRET_KEY="supersecretkey"`, in-memory users, `allow_origins=["*"]`, placeholder order execution) and `trading_bot/api/rest_api.py` (broker-direct `/orders` route bypassing CSC/shield; `OrderType` members sit under a `try:` block — verify). Neither routes capital through the canonical CSC→shield→bus path | **OPEN** — deploy configs no longer reference them; a safe API needs an authority model (read-only first) before re-exposure |
| MP-044 | `docker-compose.production.yml` mounted 4 missing files (`deploy/init-db.sql`, `deploy/nginx/nginx.conf`, `deploy/alertmanager/alertmanager.yml`, `docs/api/openapi.json`); trading-bot service had an unservable HTTP healthcheck and published ports with no listener | **PARTIALLY FIXED** — missing mounts removed/disabled, healthcheck→psutil, bot ports dropped; prometheus/grafana/postgres/redis/timescaledb kept as scaffolding but several scrape targets are dead by construction |
| MP-045 | Production module `trading_bot/infrastructure/health_endpoints.py` re-exported `HealthCheckManager` et al. from `trading_bot._archive` — production importing archived code (caught by `test_no_archive_imports_in_production`, **pre-existing failure at HEAD**) | **FIXED** — 300-line implementation restored in-tree verbatim; architecture + health-endpoint tests pass |

### P1 — evidence/scientific-validity gaps (CONFIRMED via docs + code)

| ID | Item | State |
|---|---|---|
| MP-010 | Real market data | `market_data.db` = 1,000 EURUSD bars, 10 days only (TD-05). `CsvDirSource` exists; no datasets acquired. **BLOCKED** on data governance/licensing |
| MP-011 | RSI verifier key custody | in-process/file-based key; `ExternalVerifierClient` contract exists but unprovisioned (TD-07). **BLOCKED** on ops/HSM or operator key service |
| MP-012 | Sealed holdout + measured costs | `HoldoutAttestation`/`CostModelRegistry` enforce the interface; no real holdout or broker-measured cost model exists. **BLOCKED** on external custody + live/paper fill data |
| MP-013 | `self_play_loop.py` random-walk prices | DOC-REPORTED still present (`np.random.randn()` paths ~lines 672/800); partially remediated. Verify + eliminate remaining ungrounded evaluation paths |
| MP-014 | Gap-matrix algorithms (EKSFT, DiscoLoop, AutoMem, SAGE, HASP, NanoResearch) | DOC-REPORTED standalone files in `SCIENTIFIC_FOUNDATION_V5/ALGORITHMS/`; not integrated into CSC/ACPE. DiscoLoop in CSC is a toy (`tanh`+argmax) |
| MP-015 | Divergent release gates | `release_verification.py` tests `trading_bot.ai.hub` (a different stack than `main.py`); the "GO" reports' Sharpe +30% / ECE / latency numbers have no reproducible harness in-repo |

### P2 — test/infra hygiene (CONFIRMED)

| ID | Item | State |
|---|---|---|
| MP-020 | Syntax-broken tracked files | 60 files, **all under `trading_bot/_archive/`** (`examples_broken/*` ×59 + `integrations/intelligence_layer.py`) | `ast.parse` pass over all 8,906 tracked `.py` |
| MP-021 | Excluded tests | `tests/_quarantine/` = 4 files (`test_additional_coverage`, `test_integration_thinking_bot`, `test_multi_symbol`, `test_mutation_quality`); manifest entries: `auto_fix_backups`, `self_mastery/test_mastery_orchestrator.py`, `test_infrastructure.py`. `TECHNICAL_DEBT_REGISTER.md` says "2 files" — stale |
| MP-022 | pytest config divergence | `pytest.ini` and `pyproject.toml [tool.pytest.ini_options]` disagree; runtime warns "ignoring pytest config in pyproject.toml". `--continue-on-collection-errors` can mask collection failure |
| MP-023 | Test-suite health unknown | `suite_run2.log` ends in pytest Timeout; 3,510 test files never fully verified post-merge. Conftest builtins/import shims mean collection ≠ product import health |
| MP-024 | Marker debt | 57 TODO/FIXME in `trading_bot/`; 16 `NotImplementedError` sites (mostly abstract contracts — verify individually, don't fake-implement); ~1,048 S5 weakness-register rows pattern-classified, not line-audited |
| MP-025 | Dependency manifests | `requirements.txt` (178 lines) vs `requirements-runtime.txt`, `requirements-optional.txt`, `requirements_no_mt5.txt`, `pyproject.toml` — overlapping, unverified mutually; Dockerfile installs which one? Audit |

### P3 — structural/legacy mass (classified, not bugs)

| ID | Item | State |
|---|---|---|
| MP-030 | Archive mass | 1,587 tracked files under `trading_bot/_archive/`; keep (preservation), parse-fix optional under "restore viable behavior" |
| MP-031 | Disconnected subsystems | ~225 top-level `trading_bot` packages; RSI duplicates (`recursive_improvement`, `eternal_evolution`, `alpha_evolve`, etc.) DISCONNECTED with DeprecationWarnings — by design, do not extend |
| MP-032 | Merge residue | 446 remote branches, 22 unmerged into HEAD; `merge_progress.txt` shows 5 prior dirty-worktree failures (later entries RESOLVED). `agents 2/` root dir untracked |
| MP-033 | Doc contradiction (Gap #0) | ~209 root `.md` + large `docs/`; five docs still declare five different canonical stacks. `CANONICAL_COMPONENTS.md` vs CSC reality never fully reconciled |
| MP-034 | Untracked runtime state | `*.db`, `*_data/` dirs, `orders.json`, logs — local state, excluded from evidence claims |

---

## 4. Dependency-ordered roadmap

Each wave is separately approvable. Nothing here authorizes live trading.

### Wave 0 — Environment & measurement baseline (unblocks everything)
- W0.1 User frees disk (≥5 GB target); record `df` in repo notes.
- W0.2 Full tracked-file AST/compile inventory → `tools/` artifact; baseline
  `python -m pytest --collect-only -q` (no-cov, no-cacheprovider) to enumerate
  collection failures as ground truth.
- W0.3 Decide test-config source of truth (`pytest.ini` vs `pyproject.toml`)
  — consolidate to one.
- **Gate:** collection completes; failure list published. Any code fix in
  later waves re-runs the affected collection set.

### Wave 1 — Entry-point & deploy repair (P0 — PARTIALLY DONE 2026-09-28)
- W1.1 API: **deferred by design** — both existing APIs bypass canonical
  authority (MP-043); deploy configs no longer reference any API. A safe
  read-only `foundation.runtime`-backed API is a separate design task.
- W1.2 Launchers aligned: Procfile/railway/render/Dockerfile(s)/compose all
  point at `python main.py --mode paper --symbol EURUSD`; missing-file
  mounts removed; compose `test` service runs a synthetic smoke.
- W1.3 Console script: `trading_bot/main.py` created; delegates to root
  `main.py` so CLI and source launcher cannot diverge.
- W1.4 README/START_HERE quickstarts rewritten to verified commands;
  dead references annotated.
- **Remaining gates:** `docker build` unexecuted (no docker here);
  `python -m trading_bot.main --help` verified; `config/docker-compose.yml`
  sanitized 2026-09-28 but **MP-040 stays open until operator rotation**;
  `bot_cli.py` and the surviving `RUN_*.bat` launchers still unverified
  at runtime.

### Wave 2 — Test-suite restoration & quarantine triage
- W2.1 Fix `test_infrastructure.py` (`import infrastructure` resolves to
  tests package), `self_mastery/test_mastery_orchestrator.py` (shim target).
- W2.2 Quarantined files: `test_additional_coverage.py` (27 API-drift
  failures — update to current APIs or mark expected-fail documented),
  `test_integration_thinking_bot.py` (lazy import), the 2 structurally
  unfixable ones → move to `_archive` with a note, unquarantine dir.
- W2.3 `auto_fix_backups` — not a maintained suite; exclude by norecursedirs
  or archive.
- W2.4 Full suite run in partitions (per top-level test dir), publish
  pass/fail baseline; `--continue-on-collection-errors` off for the gate run.
- **Gate:** zero collection errors; baseline failure count documented and
  shrinking.

### Wave 3 — Data & evidence custody (external blockers)
- W3.1 Acquire multi-instrument/regime data through `CsvDirSource`
  governance path (licensing is external). BLOCKED until data lands.
- W3.2 Provision verifier key custody (`RSI_VERIFIER_KEY_FILE` or
  `ExternalVerifierClient` service). BLOCKED on ops.
- W3.3 Operator-signed holdout attestation + measured cost model from real
  fills/LOB. BLOCKED on the same custody work.
- W3.4 Eliminate remaining `np.random` eval paths in `self_play_loop.py`;
  integrate or honestly archive `SCIENTIFIC_FOUNDATION_V5` algorithms.
- **Gate:** `rsi_synthetic_benchmark --seeds 20` + a *real-data* sealed
  evaluation produces `insufficient_evidence` or better only via signed
  evidence — never a promotion claim.

### Wave 4 — Paper/shadow hardening
- W4.1 `main.py` long-run stability (memory, file descriptors, restart).
- W4.2 Order integrity: idempotency, partial fills, reconciliation between
  `PaperExecutionBridge` positions and `CanonicalExecutionService` reports.
- W4.3 Failure injection (bus restart, shield veto storm, feed stall) per
  `FAILURE_INJECTION_PLAN.md`; observability via existing `telemetry` layer.
- **Gate:** soak run + chaos suite green; zero unlogged rejections.

### Wave 5 — Live-readiness review (go/no-go doc only, never executed here)
- W5.1 Broker adapter behind `CanonicalExecutionService` (MT5 first per
  README intent); fill-vs-expected slippage measured via `SlippageRecorder`.
- W5.2 Deployment repair validated in Wave 1 becomes a real deployment:
  image builds, health endpoints live, config as code.
- W5.3 Compliance/legal for market data and broker terms; credential
  custody (no keys in repo/env); human approval UI path exercised.
- W5.4 Reconcile CANONICAL_COMPONENTS/docs; retire or amend the 200+
  contradicting reports with VERIFIED_AT stamps.
- **Gate:** a signed go/no-go checklist requiring operator authorization.
  Trading-live is **outside** this plan's execution authority.

---

## 5. What was deliberately not done

- No full-suite test run (last logged attempt timed out; focused suites and
  an end-to-end smoke were run instead).
- No line-level audit of ~9,800 files; weakness register is a flagged-
  candidate list, not confirmed defects — and this audit proved the
  "0 open reachable" registers had blind spots (MP-041/042 escaped them).
- No archive deletions, no secret-value output persisted, no external
  network calls, no deploys, no Git-history rewriting.
- `config/docker-compose.yml` credentials were **removed from the working
  tree** (MP-040 gate A done); rotation/revocation, history rewrite, and
  old-image cleanup are still operator-side (gate B, pending).
- The 60 syntax-broken `_archive` files were catalogued, not repaired
  (Wave 2/3 decision: repair only where a demo's original intent is clear).
- `unified_bot.py` and `unified_event_bus.py` were modified by human
  engineering (fail-closed hardening) — these are ProtectedPathGuard files;
  the hash drift is expected and reviewed, NOT an RSI candidate change.

## 6. How to keep this honest

- Every row above carries a snapshot hash; re-run the §1 verification block
  before quoting it. If a fix lands, move the row to "resolved" with the
  fixing commit — do not delete history.
- New audit docs must carry `VERIFIED_AT: <commit>` headers (prior docs
  asserting states that were already false when written caused the P0
  confusion).

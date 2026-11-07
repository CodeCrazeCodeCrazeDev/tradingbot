# Architecture Execution Plan — consolidated 36-doc reconciliation

Generated: 2026-11-03 by reconciling the 36 root-level audit/architecture
documents against the current worktree. Scope: reconcile claims vs live
code, produce ONE prioritized plan. Not a profitability or readiness claim.

Binding references: `AGENTS.md`, `DOCS/DEVIN_TRADING_BOT_RECOVERY_PLAN.md`.

## 1. Document inventory (classified)

| Doc | Date | Verdict class | Notes |
|---|---|---|---|
| TARGET_FOUNDATION | 2026-09-29 | verified-by-code (contract) | Explicitly does *not* claim runtime matches design; canonical path confirmed in `foundation/runtime.py`, `unified_bot.py`. |
| CONSISTENCY_AND_OBJECTIVES | — | spec | UCA-2026 authoritative table; matches current path (CSC, HMS, GWM-V2, Shield, UnifiedDecisionBus). |
| DEPENDENCY_AND_COMPLEXITY | — | spec | Startup-order graph matches `unified_bot.start()`. |
| PRINCIPLE_EXTRACTION | — | spec | HIPIF folding, evaluator-optimizer, WMR loop — partially in CSC/SRE. |
| VALIDATION_AND_FITNESS | — | spec | Acceptance criteria (ECE<0.1, depth≥10); not yet met/measured — untestable claims remain aspirational. |
| VERIFICATION_MATRIX_1/2 | — | spec | Paper-compat matrix (HIPIF, RSEA monotone-safe → matches `EvolutionGate`). |
| VERIFICATION_REPORT | 2026-03-16 | **CONTRADICTED** | Claims `trading_bot.ai.hub.MTASH` is authoritative CSC — current code makes `CognitiveSystemController` sole authority; MTASH is legacy. |
| WAVE_INVENTORY | generated | verified | Wave table consistent with quarantine structure. |
| AUTHORITY_BOUNDARY_MAP / CONSOLIDATION | 2026-03-30 | spec+partial | Authority table matches post-merge consolidation intent; UnifiedDecisionBus/HMS/Shield verified. |
| AUTONOMOUS_CHANGE_SURFACE | — | spec | Autonomy boundary matches RSI promotion-gate (operator-signed). |
| CDS_BOTTLENECK | — | historical | References `VerdictEngine` mock reviewers — legacy CDS path, not canonical. |
| CHAMPION_CHALLENGER_SPEC | — | spec | Dual-track promotion matches RSI champion/challenger gate. |
| CODEBASE_AUDIT_REPORT | **2024-05-22** | **historical-only** | Pre-canonical fragmented state; "delusion loop" complaints largely remediated by canonical pipeline. |
| CODEBASE_MAPPING_2026 | — | spec | Paper-to-module map (HIPIF folding, SocraticPO, Skill-to-LoRA — mostly still Missing). |
| COGNITIVE_ARCHITECTURE_SPEC | — | spec | Closed-loop cognitive processor spec. |
| BRAIN_HOSTILE_AUDIT | 2026-03 | verified-by-code (verdict) | "UNKNOWN/partially demonstrated, unproven live" — still accurate; no live edge claim exists. |
| COGNITIVE_CAPABILITY_MAP | — | spec | 15-capability registry. |
| COGNITIVE_EVOLUTION | — | spec | Governed evolution objective — matches RSI gate design. |
| CONCURRENCY_AUDIT | — | **partially STALE** | `validation.py` time.sleep claim contradicted (`:71` uses `await asyncio.sleep`); task-cancellation concerns remain untested. |
| DELUSION_LOOP_ELIMINATION | 2026-07 | verified-by-code (scope) | Random-simulation removal in `foundation_agents/*` — legacy path; canonical path unaffected. |
| EVALUATOR_SECURITY_AUDIT | 2026-03-30 | spec+partial | Held-out/test-hashing design matches `ProtectedPathGuard` + sealed RSI evaluator. |
| EVOLUTION_ENGINE_SPEC | — | spec | Async evolution pipeline topology. |
| EVOLUTION_EXPERIMENTS | 2026 | ledger | EXP-2026-* records; historical claims not runtime-verified. |
| EVOLUTION_POLICY | — | spec | Promotion policy — enforced via signed operator approval. |
| EVOLUTION_VALIDATION | — | spec | Validation protocol — mirrors RSI OOS gate. |
| FAILURE_INJECTION_PLAN | — | spec | Fault-injection plan; `scripts/fault_gate.py` exists (execution idempotency gate). |
| FINAL_ACCEPTANCE_REPORT | — | report | Acceptance summary — read as historical claim, not current proof. |
| FIRST_PRINCIPLES_AUDIT | — | spec | First-principles checklist. |
| FIX_IMPLEMENTATION_LOG | — | ledger | Historical fix log. |
| GOVERNANCE_SECURITY_AUDIT | — | spec | Governance hardening checklist — matches shield/governance layer intent. |
| GAP_MATRIX | — | spec | Paper-gap table (see §3). |
| IMPROVEMENTS | 2026 | report | Sandbox AST-validation + architecture invariants (`tests/architecture/test_architecture_invariants.py` exists). |
| REVIEW | — | spec | MTASH meta-intelligence review — superseded by canonical consolidation. |

## 2. Contradiction table (resolved by live code)

| Claim | Doc(s) | Resolution |
|---|---|---|
| "MTASH hub is the authoritative CSC" | VERIFICATION_REPORT (2026-03-16) | **STALE** — `CognitiveSystemController` is sole authority (`unified_bot.py`); MTASH is legacy/quarantined. |
| "blocking time.sleep starves the event loop in validation.py" | CONCURRENCY_AUDIT | **STALE** — `trading_bot/core/validation.py:71` already uses `await asyncio.sleep`. |
| "alpha_evolve modules are unwired" | GAP_MATRIX / WAVE notes | **STALE as of 2026-11-03** — `alpha_evolve_lab` advisory (evidence-only) now wires the 8-module stack in `advisory.py`. |
| "advisors route to execution" | several older docs | **CONTRADICTED** — advisory services are authority-stripped cognition services; capital path is CSC→risk→shield→governance→bus→execution only. |

## 3. Gap matrix (prioritized)

### P0 — correctness/safety (verified now)
| Item | Evidence | Fix shape | Test |
|---|---|---|---|
| `paper_runner.py` synthetic feed crashes for `--cycles < 53`: tail regime `n_bars - q*6 - max(4,q//2)` goes negative → `rng.normal(size<0)` | `scripts/paper_runner.py:241-257`, `trading_bot/evaluation/synthetic_market.py:89`; reproduced 2026-11-02 | Scale regime sizes to fit any n_bars ≥ 8 (fall back to 2-regime spec for tiny windows) | generate() succeeds for n∈{10,40,52,200} |
| Demo-runner `--replay` can reach order path when approvals granted (historical bars through executing runtime) | RECOVERY_PLAN finding; `mt5_demo_runner.py` replay mode already runs analysis/paper boundary — same construction applied to new `ctrader_demo_runner.py` | Keep replay on non-executing boundary (already done); add regression test proving replay cannot send orders | fake-adapter test asserting no venue submit during replay |

### P1 — authority/trust-boundary
| Item | Evidence | Fix shape | Test |
|---|---|---|---|
| Advisory `analyze()` exceptions/timeouts can stall or disable services unevenly | `controller.py` advisory timeout/disable logic | Keep 5-failure disable; log per-service latency to snapshot | latency fields in advisory_report |
| cTrader venue adapter has no operator-authorized market-data soak yet | new `ctrader_demo.py` | run `scripts/ctrader_preflight.py --authorize-connect` with rotated demo creds; then `--replay` validation | preflight report JSON |
| `alpha_evolve_lab` outputs are advisory-only but land in same evidence stream as measured advisors | `advisory.py` factory | weight/tag `authority:"evidence_only"` downstream in reliability scoring | funnel shows lab marked non-directional |

### P2 — capability (spec gaps still real)
| Item | Source | Status |
|---|---|---|
| ~~ECE calibration in EvolutionGate~~ | GAP_MATRIX / VALIDATION | DONE `9a5079fe` — absolute `calibration_error ≤ 0.1` hard reject in `EvolutionGate` |
| DiscoLoop coupled discrete-continuous trackers | GAP_MATRIX | Partial — `ai_stack` shows `discoloop tokens`; coupled trackers not implemented |
| ~~AutoMem schema-versioned memory~~ | GAP_MATRIX | STALE-claim — `migrate_to_version` + `_run_migration_step` implement real sequential ±0.1 up/down migrations with `migration_history` (`hms/memory.py:458`). No auto-trigger on load by design — migrations stay explicit. |
| ~~SAGE online edge-weight updates from outcomes~~ | GAP_MATRIX | DONE `3003e60a` — advisor→signal edges at decision time; `tanh`-scaled realized utility feeds `evolve_weights` at settlement (dissent gets inverse delta); ids persist via position export/import |
| ~~HIPIF information folding~~ | PRINCIPLE_EXTRACTION / MAPPING | DONE — settled-outcome journal folds every 16 settlements into durable `lesson` records in HMS self-improvement memory (regime stats, win-rate, exit reasons); re-enters evidence plane via `recall_lessons`/reflective context |
| NanoResearch skill-bank DPO | GAP_MATRIX | Missing |

### P3 — hygiene
| Item | Note |
|---|---|
| Requirements file does not include `ctrader-open-api` pin | add `ctrader-open-api==0.9.3` to runtime requirements comment section (installed `--no-deps` in hermes) |
| advisory.py concurrent-edit hazard | keep single-session + atomic writes + prompt commits (protocol already in AGENTS.md) |

## 4. Sequenced plan

1. **P0-a** `paper_runner` regime-spec scaling (this session — implemented below). ✅
2. **P0-b** replay-cannot-order regression test for both demo runners — done: `tests/test_demo_runner_replay_isolation.py` (6/6 pass; pins replay→analysis, follow→venue, paper-only service, feed-adapter seam). ✅
3. **P1-a** advisory latency/skip telemetry in snapshot `advisory_report`.
4. **P1-b** cTrader demo preflight run when rotated creds provisioned.
5. **P2** capability items each get their own failing-test-first cycle under RSI governance; do NOT batch.

## 5. P0 fix status (this session)

The `paper_runner.py` negative-dimension crash was **already fixed in the
worktree** (uncommitted change from another session): the regime list now
truncates blocks (`take = min(block.n_bars, n_bars - used)`) so no
`RegimeSpec` can carry a negative size. Verified fixed for every window
≥3 bars. Contribution added here: regression coverage in
`tests/test_paper_runner_synthetic.py` — 8/8 pass (n ∈ {4,8,10,40,52,53,
100,200} generate cleanly; n=2 raises the generator's documented
minimum). The `paper_runner.py` diff itself belongs to the other session's
uncommitted work and was deliberately left uncommitted here.

## 6. What remains untestable / honest limits

- No document provides verified out-of-sample net-edge evidence; the
  hostile audit's "unproven in live capital" verdict still stands.
- Docs dated pre-canonical (2024–early-2026) describe obsolete layers;
  treated as historical unless code-verified.
- Acceptance criteria in VALIDATION_AND_FITNESS are targets, not measured
  results; no ECE<0.1 or >80% rollout-fidelity evidence exists yet.

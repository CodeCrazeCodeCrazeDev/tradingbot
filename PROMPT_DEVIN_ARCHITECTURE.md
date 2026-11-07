# Devin task prompt — consolidate architecture/audit corpus into a verified execution plan

Paste the text below (everything inside the fence) into a Devin session.
It references the 36 audit/architecture documents at the repo root and is
written to respect `AGENTS.md` and `DOCS/DEVIN_TRADING_BOT_RECOVERY_PLAN.md`.

```text
You are working in C:\Users\peterson\trading bot-merge-six. Read AGENTS.md
and DOCS/DEVIN_TRADING_BOT_RECOVERY_PLAN.md first — they are binding.

GOAL
Turn the 36 audit/architecture documents at the repo root into ONE verified,
prioritized execution plan for this codebase. These documents describe a
target architecture, gap analyses, hostile audits, and evolution policy.
Your job is not to summarize them — it is to reconcile them against the
current code and produce a plan that is executable now.

INPUT DOCUMENTS (repo root, read all of them — classify each as
verified-by-code / historical-only / hypothesis):
  ARCHITECTURE_CONSISTENCY_AND_OBJECTIVES.md
  ARCHITECTURE_DEPENDENCY_AND_COMPLEXITY.md
  ARCHITECTURE_GAP_MATRIX.md
  ARCHITECTURE_IMPROVEMENTS.md
  ARCHITECTURE_PRINCIPLE_EXTRACTION.md
  ARCHITECTURE_REVIEW.md
  ARCHITECTURE_TARGET_FOUNDATION.md
  ARCHITECTURE_VALIDATION_AND_FITNESS.md
  ARCHITECTURE_VERIFICATION_MATRIX_PART1.md
  ARCHITECTURE_VERIFICATION_MATRIX_PART2.md
  ARCHITECTURE_VERIFICATION_REPORT.md
  ARCHITECTURE_WAVE_INVENTORY.md
  AUTHORITY_AND_TRUST_BOUNDARY_MAP.md
  AUTHORITY_CONSOLIDATION_REPORT.md
  AUTONOMOUS_CHANGE_SURFACE.md
  CDS_BOTTLENECK_REPORT.md
  CHAMPION_CHALLENGER_SPEC.md
  CODEBASE_AUDIT_REPORT.md
  CODEBASE_MAPPING_AUDIT_2026.md
  COGNITIVE_ARCHITECTURE_SPEC.md
  COGNITIVE_BRAIN_HOSTILE_AUDIT_REPORT.md
  COGNITIVE_CAPABILITY_MAP.md
  COGNITIVE_EVOLUTION_ARCHITECTURE.md
  CONCURRENCY_AUDIT.md
  DELUSION_LOOP_ELIMINATION_REPORT.md
  EVALUATOR_SECURITY_AUDIT.md
  EVOLUTION_ENGINE_SPECIFICATION.md
  EVOLUTION_EXPERIMENTS.md
  EVOLUTION_POLICY.md
  EVOLUTION_VALIDATION.md
  FAILURE_INJECTION_PLAN.md
  FINAL_ACCEPTANCE_REPORT.md
  FIRST_PRINCIPLES_AUDIT.md
  FIX_IMPLEMENTATION_LOG.md
  GOVERNANCE_SECURITY_AUDIT.md

HARD CONSTRAINTS (violating any of these fails the task)
- One capital path only: UnifiedTradingBot -> CSC -> CanonicalRiskService ->
  immutable shield -> human governance -> LogAct -> CanonicalExecutionService.
  Never route advisors, research agents, or evolution output directly to
  execution.
- Never modify trading_bot/risk/service.py,
  trading_bot/core/immutable_shield.py, trading_bot/execution/service.py,
  trading_bot/unified_bot.py, main.py, or the RSI contracts/evaluator/
  anti-gaming/archive modules (ProtectedPathGuard enforces this for
  candidates). Other canonical files may be edited for operator-directed
  work — preserve existing uncommitted changes; check `git status` first.
- Do NOT connect to MT5, run scripts/mt5_demo_runner.py or
  scripts/ctrader_demo_runner.py, or place demo/live orders without a
  separate explicit authorization for that action. Never reuse the burned
  MetaQuotes-Demo credential. Offline paper runs and tests are fine.
- Legacy quarantined packages (recursive_improvement/, eternal_evolution/,
  alpha_evolve/, autonomous_learner/, adaptive_systems/, meta_learning/,
  root legacy singles) carry no improvement authority — wire them
  evidence-only through advisory services, never as promotion paths.
  AlphaEvolve is already wired evidence-only as `alpha_evolve_lab` in
  trading_bot/core/csc/advisory.py.
- Do not disable guardrails, loosen cost models, inflate confidence,
  auto-reset emergency stops, or force trades to raise activity.
- advisory.py has a documented concurrent-edit hazard: single session,
  atomic temp-file replacement, `git status` before/after, commit promptly.

METHOD — do these in order, write findings as you go
1. Inventory: for each document, record date, verdict, top-level claims, and
   which claims are still testable. Dedupe overlapping findings.
2. Reconcile vs live code: for each *actionable* claim (gap, vulnerability,
   missing capability, bottleneck), verify it against the CURRENT worktree —
   cite file:line evidence. Mark each VERIFIED / STALE / CONTRADICTED /
   UNTESTABLE. Historical reports describe obsolete states; live code wins.
3. Contradiction table: where documents disagree (e.g., an audit saying
   "unwired" vs code that is wired), resolve by code evidence and list the
   resolution explicitly.
4. Gap matrix: produce a single prioritized table —
   P0 correctness/safety, P1 authority/trust-boundary, P2 capability,
   P3 hygiene. Each row: item, source doc(s), code evidence, blast radius,
   suggested fix shape, verification test.
5. Execution plan: sequence P0/P1 items into independently-landable steps,
   each with failing-test-first, the exact files to touch (respecting the
   protected list above), and the test command that proves it
   (.venv for lightweight suites, hermes env for trading_bot/__init__ work;
   pytest -q --no-cov -p no:cacheprovider).
6. Implement ONLY the first P0 item end-to-end (test -> fix -> green), then
   stop and report. Do not batch-implement.

DELIVERABLES
- DOCS/ARCHITECTURE_EXECUTION_PLAN.md containing the inventory,
  contradiction table, gap matrix, and sequenced plan (or update an
  existing canonical plan doc if one exists).
- One implemented-and-tested P0 fix with its test diff.
- A final report: what was verified, what was contradicted, what remains
  untestable, and the exact next step.

ACCEPTANCE
- Every plan row cites doc + code evidence; no "the audit says" without a
  file:line check.
- No new execution paths, promotion paths, or live connections appear in
  the diff.
- All touched test suites pass; nothing protected was modified.
```

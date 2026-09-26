# RSI implementation roadmap

Source of truth: `RSI_CURRENT_STATE_AUDIT.md`, `RSI_RESEARCH_REVIEW.md`, `RSI_EVALUATION_CONTRACT.md`. This is a **plan**, not a claim of completed scientific validation. Operator-controlled dataset custody and cost calibration are required before positive approval.

## Slice 0 — prerequisites (complete before production edits)

Verify executable import/call graph; publish all ten required artifacts; reconcile competing RSI authorities, synthetic paths and existing governance claims. Pre-register an operator-controlled evaluation contract/parameter allowlist, minimum effect and hard risk/cost limits; if unavailable use fail-closed research-only testing. Review existing tests expecting mock deployment. No deletion of legacy subsystems during discovery.

## Slice 1 — offline bounded strategy-parameter evaluation (this milestone)

1. Failing tests in `tests/foundation/` and `tests/recursive_self_improvement/`: unsafe fake approvals, missing/tampered contract or attestation, wrong baseline/parameter that changes nothing, test-outcome leakage, fill timing, overlapping labels, no costs, insufficient effective sample, hidden multiple trials, dominated tradeoffs, protected writes, disabled deployment and failed-experiment retention.
2. Extend existing `recursive_self_improvement/improvement_genome.py` with contract binding and full candidate provenance while keeping import API; validate no candidate can modify protected evaluation/risk/authorization files. Implement operator-owned contract/evidence parsing adjacent to existing RSI package rather than a new framework. Typed strict data, explicit unknown/insufficient results and no permissive defaults.
3. Adapt `evaluation/walk_forward.py` and `evaluation/runner.py` for point-in-time paired incumbent/candidate *same* per-bar series, actual bounded strategy parameter adapter, frozen OOS calibration, realistic cost assumptions, identical sizing, OHLCV fill bounds and finite metric outputs. Existing summary runner retained as diagnostic only; remove false Sharpe and unconditional promotion eligibility.
4. Replace `recursive_self_improvement/evaluation.py` ad hoc approval with vector metrics, hard-constraint checks, predeclared Pareto rules, paired dependence-aware inference and explicit multiplicity/sample gate. Never claim DSR/PBO when unsupported. All trial results and rejects persisted via `experiment_manager.py`/`memory.py` with dataset/contracts/baseline IDs and errors.
5. Connect bounded `rsi_loop.py` only to independent verified evidence, emit `rejected`, `insufficient_evidence` or `eligible_for_operator_review`, never invoke promoter/apply. Disable `engine.py`'s callable old deployment path while retaining imports; adjust `test_rsi_system.py` to deny mock deployment. Accept external signed verifier attestation only with operator-supplied trust anchor and no fabricated local holdout.
6. Verify targeted and broader tests under normal conftest; no runtime risk/shield/execution edits or capital-moving actions. Verify failure behavior is deterministic and positive fixture outcomes do not escape to production.

## First-slice delivery status

The local diagnostic `BoundedMeanReversionReplay` in `evaluation/runner.py` compares an actual lookback intervention over identical bars, but has no independently measured broker costs, no real holdout and no cross-asset coverage in `market_data.db`. `evaluation/walk_forward.py` remains diagnostic only; training feedback is delayed by the trade horizon and test outcomes no longer update calibration. `EvaluationEngine.evaluate_verified` accepts only signed operator/verifier-bound evidence envelopes and enforces finite net-return/cost arithmetic, bounded scope, two-instrument paired timelines, sample/trial/expiry and DD/CVaR checks; the bounded loop records attempts and never invokes its promoter. Tests generate ephemeral keys and artificial bars to validate *interfaces*, not economic claims. Full transferable effect measurement, prior-regime retention, trustworthy custodied trial counts and signed production authorization are still pending; no candidate has been accepted.

## Trust-boundary layer (landed after first slice)

`recursive_self_improvement/evidence_boundaries.py` adds the custody interfaces the next gated slices consume: `HoldoutAttestation` (operator-signed dataset-manifest binding, enforced when a contract sets `require_holdout_attestation`), `CostModelRegistry` (only `source="measured"` models may carry an eligible verdict), `build_paired_envelope` (per-instrument provenance validation; single-instrument input still fails `min_instruments`), and `load_key_file` (filesystem-only key custody, never inlined secrets). `memory.py` adds a hash-chained `evidence_ledger` with UNIQUE `trial_id`/`nonce` and `verify_evidence_chain()` tamper detection; `rsi_loop.py` appends every signed verdict to it — replay or ledger-write failure degrades to `insufficient_evidence`. `evaluate_verified` now requires strict boolean (`is True`) attestations so truthy strings cannot satisfy holdout/risk/parameter-effect claims. Both replay classes share `_paired_bar`/`_net_of_cost` arithmetic and the `PAIRED_BAR_KEYS` schema while keeping their public names. All gates fail closed; none authorize deployment.

## Next gated slices (not built or claimed)

- Operator-held sealed holdout service, budgets and rotation; audited experiment store/append-only signatures; real multi-instrument chronological histories and cost/impact calibration from fills/LOB where available.
- Regime/instrument/seed/cost stress, crisis and broker rejection/partial-fill and order integrity, shadow/paper monitoring parity and rollback rehearsal.
- Isolated code/model/prompt candidate execution, higher-level verifier upgrades under stricter out-of-band approval, slow meta-loop, complexity-adjusted improvement-rate tracking and plateau termination.
- Human-signed constrained canary and monitored live rollout with existing canonical risk/shield/execution vetoes, only after external infrastructure and empirical evidence exist.

## Acceptance

A verified first slice can reject all candidates when trusted evidence is unavailable. Required: no unsafe legacy deploy, no fake Sharpe or free cost, no OOS fit/update, paired chronology, full net metric/regression vector, auditable failed attempts and tested protected boundary. No test run alone demonstrates economically meaningful improvement. Parallel unrelated work remains untouched; recheck git status before every edit.

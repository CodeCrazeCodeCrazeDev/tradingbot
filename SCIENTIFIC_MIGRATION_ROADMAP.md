# Scientific Migration Roadmap - UCA 2026

The transition from the current fragmented architecture to the Unified Scientific Reasoning Engine (SRE) will follow a 4-phase institutional roadmap.

## Phase 1: Structural Foundation (Weeks 1-2)
- **Centralize SRE Registry**: Deploy the unified `ScientificHypothesis` data model in `trading_bot/core_agent_system/scientific_reasoning/core.py`.
- **Alias Bridging**: Implement compatibility wrappers for `PHCE-D`, `AlphaMining`, and `CuriosityEngine` to map their internal "hypotheses" to the SRE standard.
- **Audit Logging**: Initialize the `LogAct` decision ledger to track all hypothesis state transitions.

## Phase 2: Pipeline Integration (Weeks 3-5)
- **Unified 19-Step Cycle**: Wire existing modules into the SRE lifecycle.
  - Curiosity Engine -> Steps 2-4
  - HMS/GWM -> Steps 5-7
  - Verification Swarm -> Step 8
  - Backtest/Paper -> Steps 9-11
- **Bayesian Layer**: Activate the central `bayesian_update` and `calibrate_confidence` modules.

## Phase 3: Advanced Reasoning (Weeks 6-8)
- **Counterfactual Engine**: Integrate the Mamba-based GWM for Step 7 (Do-calculus).
- **Adversarial Hardening**: Deploy the full `VerificationSwarm` with 80% consensus gate for Step 8.
- **HMS Optimization**: Implement `AutoMem` for automated memory consolidation (Step 15).

## Phase 4: Full Autonomy (Weeks 9+)
- **Meta-Discovery**: Activate Step 19 for automatic discovery of new research paths.
- **Legacy Decommissioning**: Gradually archive fragmented logic (e.g., `trading_bot/ai_core/`, `trading_bot/agents2/`) once SRE parity is verified.
- **Institutional Certification**: Final audit of the Gain Metric and ECE targets.

## Risk Mitigation
- **Fail-Closed Gate**: The `ImmutableShield` remains active throughout the migration to prevent unverified SRE decisions from controlling capital.
- **Parallel Run**: The SRE will run in "Shadow Mode" (logging only) for the first 4 weeks to calibrate against existing production strategies.

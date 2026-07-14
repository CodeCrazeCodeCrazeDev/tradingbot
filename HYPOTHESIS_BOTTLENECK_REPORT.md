# Hypothesis Ecosystem Bottleneck Report

## 1. Fragmentation of Logic (Critical)
- **Bottleneck**: PHCE-D, AlphaMining, and CuriosityEngine maintain independent hypothesis states.
- **Downstream Effect**: Duplicate effort and inconsistent evaluation criteria.
- **Recommendation**: Unify under the SRE 19-stage lifecycle.

## 2. Lack of Unified Causal/Bayesian Loop (High)
- **Bottleneck**: PHCE-D uses deterministic gates; AlphaMining uses genetic fitness. SRE has the blueprint but isn't integrated.
- **Downstream Effect**: Inability to perform cross-domain evidence synthesis.
- **Recommendation**: Integrate SRE's Bayesian update and Counterfactual stages into the main decision flow.

## 3. Insufficient Adversarial Testing (High)
- **Bottleneck**: AlphaMining lacks explicit adversarial debate (Step 8 of SRE).
- **Downstream Effect**: High risk of discovering spurious correlations (alpha decay).
- **Recommendation**: Hook VerificationSwarm into the SRE evaluation pipeline.

### 4. Poor Memory Integration of Historical Failures
- **Why it exists**: `FailureMemory` is currently a passive log rather than an active constraint on hypothesis generation.
- **Downstream effects**: The system "re-discovers" and re-tests failed hypotheses in similar market regimes.
- **Priority**: MEDIUM
- **Recommended Redesign**: Implement a "Semantic Negative Filter" in the `HypothesisGenerator` that queries HMS for similar rejected lineages before instantiation.

## 5. Poor Failure Reuse
- **Cause**: Rejected hypotheses are often simply discarded or forgotten in tournament selection.
- **Downstream Effect**: Repeating historical mistakes and losing the "Negative Knowledge" of why something failed.
- **Priority**: MEDIUM
- **Redesign**: Implement a mandatory `Rejected` or `Dormant` end-state with a "Reason for Failure" metadata field persisted in HMS.

## 6. Knowledge Fragmentation
- **Cause**: At least 3 different `ConfidenceCalibrator` implementations exist in the codebase.
- **Downstream Effect**: Signal confidence is not comparable across modules; high confidence in one module might be low in another.
- **Priority**: HIGH
- **Redesign**: Single authoritative `ConfidenceCalibrator` integrated into SRE Step 13.

## 7. Reward Hacking in Self-Play
- **Cause**: Self-play loops optimizing for win-rate without institutional risk constraints (CVaR, Max Drawdown).
- **Downstream Effect**: Policies that "win" games but are too risky for production deployment.
- **Priority**: HIGH
- **Redesign**: Inject the `UnifiedRiskEngine` into the self-play reward function.

## 8. Missing Counterfactual Verification in Discovery
- **Cause**: `AlphaMining` and `EvolutionaryEngine` find predictors but don't ask "What if the lead indicator is manipulated?".
- **Downstream Effect**: Fragile alphas that break under distribution shift or adversarial conditions.
- **Priority**: HIGH
- **Redesign**: Mandatory Step 7 (Counterfactual Generation) before hypothesis promotion.

## 9. Lack of Experiment Design Formalism
- **Cause**: Most "experiments" are just backtests; no formal design for A/B tests, stress tests, or regime-switching sensitivity.
- **Downstream Effect**: Incomplete validation leads to unexpected production failures.
- **Priority**: MEDIUM
- **Redesign**: Implement Step 9 (Experiment Design) using a formal experiment DSL.

## 10. Survivorship Bias in HMS
- **Cause**: Only successful strategies are well-documented in some memory modules.
- **Downstream Effect**: The system overestimates its competence and doesn't learn from the "graveyard" of failed ideas.
- **Priority**: MEDIUM
- **Redesign**: Enforce mandatory persistence of the full hypothesis lineage, including all rejected branches.

## 11. Core System Instability (NameErrors/Missing Imports)
- **Cause**: Incomplete refactoring of core modules like `HMS` (`memory.py`).
- **Downstream Effect**: Validation tests and the SRE cannot run due to basic Python `NameError` (e.g., missing `Tuple`, `json` imports).
- **Priority**: CRITICAL
- **Redesign**: Immediate "Scientific-First Refactoring" to fix core imports and satisfy static analysis.

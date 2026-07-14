# AlphaAlgo Hypothesis Ecosystem Migration Roadmap

## Phase 1: Foundation (Weeks 1-2)
- [ ] Deploy the unified `ScientificHypothesis` data model in `trading_bot/core/hms/models.py`.
- [ ] Initialize the `ScientificReasoningEngine` (SRE) singleton.
- [ ] Implement the 10 authoritative end-states in the `ResearchLedger`.

## Phase 2: Interception (Weeks 3-4)
- [ ] Wrap existing `TradingSignal` generation in Step 4 (Hypothesis Generation) of the SRE.
- [ ] Route all `WalkForwardValidator` calls through Step 10 (Execution).
- [ ] Connect `ConfidenceCalibrator` to Step 13.

## Phase 3: Causal Integration (Weeks 5-6)
- [ ] Integrate `CausalWorldModel` into Step 3 (Question Generation).
- [ ] Activate `CounterfactualEngine` in Step 7.
- [ ] Enforce "Causal Justification" as a blocking requirement for Level 3 promotion.

## Phase 4: Adversarial Hardening (Weeks 7-8)
- [ ] Expand the `VerificationSwarm` to include "Risk Falsifiers" and "Regime Stressors."
- [ ] Implement Step 8 (Adversarial Debate) as a mandatory gate for all production strategies.
- [ ] Automate "Hypothesis Retirement" based on real-time alpha decay monitoring (Step 17).

## Phase 5: Decommissioning (Weeks 9-12)
- [ ] Migrate all "Live" legacy strategies into the SRE.
- [ ] Decommission redundant `Validator` and `Calibrator` classes.
- [ ] Archive fragmented research modules into `_legacy/`.

## Phase 6: Full Autonomy (Ongoing)
- [ ] Enable Step 19 (Automatic Discovery) for self-directed research.
- [ ] Implement Meta-SRE loops where the system redesigns its own `HypothesisTemplate` library based on success rates.

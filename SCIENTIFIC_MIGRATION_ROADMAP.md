# Scientific Migration Roadmap: Phase 6 Transition

## Phase 1: Foundation (Weeks 1-2)
- [ ] **Consolidate Base Types**: Create `trading_bot/core/base_types.py` and move the `ScientificHypothesis` and `ScientificEvidence` classes there as the single source of truth.
- [ ] **Implement Adapters**: Create adapter layers for `phce_d`, `csc`, and `hms` to interface with the new base types.
- [ ] **Unified Registry**: Instantiate the `ScientificReasoningEngine` as a singleton in the `SystemRegistry`.

## Phase 2: Lifecycle Enforcement (Weeks 3-4)
- [ ] **Step Implementation**: Gradually implement the missing logic for the 19 steps (Question Gen, Adversarial Debate, etc.).
- [ ] **Gateway Integration**: Modify `ValidationGateway` to require `CausalIntervention` and `AdversarialDebate` proofs before promotion.
- [ ] **Bayesian Core**: Replace threshold-based promotion logic with the Bayesian posterior update core.

## Phase 3: Memory and Self-Improvement (Weeks 5-6)
- [ ] **HMS Integration**: Map `ScientificHypothesis` end-states to HMS tiers (Tier 5 for Institutionalized).
- [ ] **Failure Memory Loop**: Implement the "Negative Filter" to prevent redundant hypothesis generation.
- [ ] **Meta-Discovery**: Implement Step 19 (`discover_new_hypotheses`) based on high-VFE regions of the market.

## Phase 4: Productionization (Weeks 7-8)
- [ ] **Continuity Audit**: Run the SRE in "Shadow Mode" alongside the legacy system to verify alignment.
- [ ] **Full Switchover**: Redirect all signal generation and validation to the SRE core.
- [ ] **Self-Optimization**: Activate the meta-learner to optimize hypothesis generation parameters.

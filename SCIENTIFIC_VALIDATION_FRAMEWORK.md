# Scientific Reasoning Engine: Validation Framework

## 1. Quality Metrics (KPIs)

To measure the success of the SRE, we track the following metrics:

### Scientific KPIs
- **Hypothesis Survival Rate:** % of hypotheses that graduate to Institutionalized vs. total generated.
- **Falsification Velocity:** Average time from hypothesis creation to first falsification attempt.
- **Evidence Density:** Average number of unique evidence sources per hypothesis.
- **Reasoning Depth:** Average number of steps in the provenance/lineage chain.
- **Information Gain:** Cumulative reduction in entropy across the hypothesis ecosystem.

### Economic KPIs
- **Alpha Decay Rate:** Time taken for a "Confirmed" hypothesis to lose its predictive edge.
- **Research Efficiency:** Cost (compute/time) per Institutionalized hypothesis.
- **Regime Robustness:** Performance of hypotheses in out-of-sample (unseen) regimes.

## 2. Validation Gates

### G1: Static Falsification Gate
- Every hypothesis MUST have at least 3 defined `falsification_triggers` before investigation.
- **Test:** `assert len(hypothesis.falsification_triggers) >= 3`

### G2: Adversarial Verification Gate
- Requires at least 2 independent verifiers to "approve" the evidence graph.
- **Test:** `assert len([r for r in reports if r.is_valid]) >= 2`

### G3: Counterfactual Consistency Gate
- The hypothesis must yield consistent results in at least 5 different counterfactual simulations.

## 3. Continuous Self-Improvement

The SRE monitors its own failures:
- If a "Confirmed" hypothesis is later "Rejected" with high loss, a **Post-Mortem Hypothesis** is automatically generated to explain the failure in the validation process itself.

# UCA-2026: Scientific Reasoning Engine (SRE) Redesign

## 1. The 18-Step Scientific Loop

The SRE unifies all autonomous intelligence into a single, continuous reasoning loop.

1.  **Observation:** Continuous multi-modal market ingestion.
2.  **Anomaly Detection:** Identify deviations from World Model predictions.
3.  **Question Generation:** Formulate "Why?" based on the anomaly (e.g., "Why did liquidity drop despite high volume?").
4.  **Hypothesis Generation:** Generate multiple competing falsifiable explanations.
5.  **Evidence Collection:** Proactive search for supporting and contradicting data across all sources.
6.  **World Model Simulation:** Predict future states under each hypothesis.
7.  **Counterfactual Generation:** Test "What if?" scenarios to isolate causal variables.
8.  **Adversarial Debate:** Peer agents attempt to falsify the hypothesis.
9.  **Experiment Design:** Define specific market conditions or "synthetic tests" to validate.
10. **Execution:** Deploy the hypothesis into a simulated or live (low-risk) environment.
11. **Evaluation:** Measure predictive accuracy vs. actual outcome.
12. **Bayesian Update:** Update the posterior probability and reduce uncertainty.
13. **Confidence Calibration:** Adjust confidence based on sample size and regime stability.
14. **Knowledge Integration:** Abstract successful patterns into Institutional Knowledge.
15. **Memory Consolidation:** Store the full reasoning trace and lineage in the Research Ledger.
16. **Policy Improvement:** Update the global Decision Bus and Agent policies.
17. **Continuous Monitoring:** Monitor for "Hypothesis Drift" or invalidation triggers.
18. **Hypothesis Retirement:** Gracefully retire, merge, or supersede hypotheses.

## 2. Authoritative Hypothesis States (10)

Every hypothesis must exist in exactly one of these states:

1.  **PROPOSED:** Initial idea after anomaly detection.
2.  **CONFIRMED:** Statistically validated with high posterior probability.
3.  **REJECTED:** Falsified by evidence or simulation.
4.  **INCONCLUSIVE:** Insufficient evidence to validate or reject.
5.  **MERGED:** Combined with another hypothesis into a more general model.
6.  **SPLIT:** Divided into specialized hypotheses (e.g., different regimes).
7.  **DORMANT:** Inactive due to current market regime but remains valid.
8.  **REACTIVATED:** Moved from Dormant to active investigation.
9.  **DEPRECATED:** No longer useful due to market structural changes.
10. **SUPERSEDED:** Replaced by a more accurate or efficient hypothesis.
11. **INSTITUTIONALIZED:** Promoted to core system logic/policy.

## 3. Implementation Requirements

- **Immutable Lineage:** Every hypothesis must carry a `parent_ids` list to ensure full provenance.
- **No Disappearance:** Even "Rejected" hypotheses are stored in the `ScientificMemory` to prevent re-generation.
- **Evidence-First:** Transitions to `CONFIRMED` or `INSTITUTIONALIZED` require a minimum Evidence Graph density.

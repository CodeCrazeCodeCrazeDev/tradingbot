# Hypothesis Bottleneck Report (Institutional Audit 2026)

## 1. Knowledge Fragmentation
- **Why it exists**: Hypotheses are created in silos (CSC, Alpha Mining, PHCE-D, Extraction Engine) with different data structures and local "registries".
- **Downstream Effects**: Redundant testing of the same idea across different modules; inability to aggregate evidence for a single causal claim globally.
- **Priority**: CRITICAL
- **Recommended Redesign**: Enforce the SRE `ScientificHypothesis` as the single global data model with a unified registry in `core.py`.

## 2. Incomplete Bayesian Lifecycle
- **Why it exists**: While `ScientificReasoningEngine` defines 19 steps, many steps (Anomaly Detection, Counterfactual Generation, Meta-Discovery) are currently stubs or loosely coupled.
- **Downstream Effects**: Premature promotion of signals based on correlations without causal (do-calculus) verification; poor adaptation to regime shifts.
- **Priority**: HIGH
- **Recommended Redesign**: Implement concrete implementations for `detect_anomalies` and `generate_counterfactuals` using the Global World Model (GWM).

## 3. Poor Uncertainty & Confidence Calibration
- **Why it exists**: Confidence scores are often hardcoded (e.g., in `specialists.py`) or use simple averages in the Verdict Engine.
- **Downstream Effects**: Overconfidence in high-risk regimes (Reward Hacking); "Confidence Drift" where nominal scores stay high while real-world accuracy drops.
- **Priority**: HIGH
- **Recommended Redesign**: Implement formal Expected Calibration Error (ECE) tracking and force Bayesian Credal Bounds ([P_lower, P_upper]) for all active hypotheses.

## 4. Lack of Adversarial Falsification
- **Why it exists**: The `VerificationSwarm` is tactical (checks current decisions) but doesn't systematically attempt to "break" long-term research hypotheses.
- **Downstream Effects**: Survivorship bias; strategies appear robust in backtests but fail in tail-risk events.
- **Priority**: MEDIUM
- **Recommended Redesign**: Integrate `AdversarialAnalyzer` into the SRE `execute_experiment` stage to simulate "hostile" market conditions for every Level 3+ hypothesis.

## 5. Poor Reuse of Historical Failures (Scientific Amnesia)
- **Why it exists**: Rejected hypotheses are often deleted or moved to an `_archive` without structured "Lessons Learned" that the generator can read.
- **Downstream Effects**: The system keeps generating "zombie" hypotheses that have failed before in similar conditions.
- **Priority**: HIGH
- **Recommended Redesign**: Implement a "Failure Memory" in HMS that the `HypothesisGenerator` must query to avoid previously rejected causal structures.

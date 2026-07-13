# Engineering Decomposition: DeepWeb-Bench (arXiv:2605.21482)

## Core Hypothesis
Retrieval is not the bottleneck in deep research; derivation and calibration (self-evaluation of certainty) are the primary failure points.

## Mathematical Formulation
- **Performance Families**: $\{Ret, Der, Rea, Cal\}$.
- **Error Attribution**: $E = \alpha \cdot E_{Ret} + \beta \cdot E_{Der} + \gamma \cdot E_{Rea} + \delta \cdot E_{Cal}$ where $\beta, \delta$ are typically large.

## Training Methodology
- Focus on multi-step derivation and cross-source reconciliation.
- Calibration training to improve the model's awareness of its own knowledge limits.

## Learning Algorithm
N/A (Benchmark).

## Memory Architecture
Demands "Massive Cross-Source Evidence" management.

## Planning Architecture
Requires "Long-Horizon Derivation" planning, moving beyond simple one-step reasoning.

## Agent Architecture
Evaluates agents on their ability to reconcile conflicting information and derive complex answers.

## World Model Contribution
Highlights the need for better "calibration" in the world model's predictions.

## Self-improvement Contribution
Provides a metric for measuring improvements in derivation and calibration.

## Failure Modes
- Hallucinated precision (weak models).
- Incomplete derivation (strong models).

## Scalability Limits
Benchmark complexity.

## Computational Complexity
N/A.

## Engineering Tradeoffs
N/A.

## Financial Applicability
Institutional-grade research where being "vaguely right" is often worse than being "precisely wrong."

## Production Readiness
N/A (Benchmark/Evaluation framework).

## Reusable Algorithms
- **DerivationValidator**: Logic for checking multi-step reasoning consistency.
- **CalibrationMonitor**: Metric (e.g., ECE) for evaluating confidence vs. accuracy.
